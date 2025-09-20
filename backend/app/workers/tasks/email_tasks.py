"""
Email-related ARQ tasks.
"""

from datetime import datetime, timezone

from app.config.loggers import arq_worker_logger as logger
from app.db.mongodb.collections import workflows_collection, mail_collection
from app.middleware.tiered_rate_limiter import RateLimitExceededException
from app.services.email_workflow_filter_service import filter_workflows_for_email
from app.services.email_importance_service import process_email_comprehensive_analysis
from app.services.trigger_matching_service import find_matching_workflows
from app.utils.email_utils import (
    extract_string_content,
    extract_subject,
    extract_sender,
    extract_date,
    extract_labels,
    convert_composio_to_gmail_format,
)
from app.utils.session_logger.email_session_logger import (
    create_session,
    end_session,
)
from app.workers.tasks.workflow_tasks import execute_workflow_as_chat


async def perform_email_analysis(email_data: dict, user_id: str, session) -> None:
    """
    Perform email importance analysis and store results in database.
    Moved from process_email.py to unify email processing flow.

    Args:
        email_data: Email data from webhook
        user_id: User ID
        session: Email processing session for logging
    """
    try:
        # Convert Composio format to Gmail format for consistent parsing
        gmail_message = convert_composio_to_gmail_format(email_data)

        # Extract email information using robust parsing utilities
        content = extract_string_content(gmail_message)
        subject = extract_subject(gmail_message) or email_data.get("subject", "")
        sender = extract_sender(gmail_message) or email_data.get("sender", "")
        date = extract_date(gmail_message) or email_data.get("message_timestamp", "")
        labels = extract_labels(gmail_message)
        message_id = email_data.get("message_id", "")

        session.log_milestone(
            f"Starting email analysis for {message_id}",
            {
                "subject": subject[:50] + "..." if len(subject) > 50 else subject,
                "sender": sender,
                "has_content": bool(content),
            },
        )

        # Process email with comprehensive analysis (importance + semantic labels)
        analysis_result = await process_email_comprehensive_analysis(
            subject=subject, sender=sender, date=date, content=content
        )

        if analysis_result:
            session.log_milestone(
                f"Email analysis completed for {message_id}",
                {
                    "is_important": analysis_result.is_important,
                    "importance_level": analysis_result.importance_level,
                    "has_summary": bool(analysis_result.summary),
                    "labels_count": len(analysis_result.semantic_labels),
                },
            )

            # Store analysis in database
            email_doc = {
                "user_id": user_id,
                "message_id": message_id,
                "subject": subject,
                "sender": sender,
                "date": date,
                "labels": labels,  # Include Gmail labels
                "analyzed_at": datetime.now(timezone.utc),
                "content_preview": (content[:500] if content else ""),
                "is_important": analysis_result.is_important,
                "importance_level": analysis_result.importance_level,
                "summary": analysis_result.summary,
                "semantic_labels": analysis_result.semantic_labels,
            }

            await mail_collection.update_one(
                {"user_id": user_id, "message_id": message_id},
                {"$set": email_doc},
                upsert=True,
            )

            session.log_milestone(
                f"Email analysis stored in database for {message_id}",
                {
                    "user_id": user_id,
                    "message_id": message_id,
                    "is_important": analysis_result.is_important,
                    "importance_level": analysis_result.importance_level,
                },
            )
        else:
            session.log_error(
                "EMAIL_ANALYSIS_FAILED",
                f"Failed to analyze email {message_id}",
                {"message_id": message_id, "user_id": user_id},
            )

    except Exception as e:
        session.log_error(
            "EMAIL_ANALYSIS_ERROR",
            f"Error analyzing email {email_data.get('message_id', 'unknown')}: {str(e)}",
            {"user_id": user_id, "error": str(e)},
        )


async def renew_gmail_watch_subscriptions(ctx: dict) -> str:
    """
    Renew Gmail watch API subscriptions for active users.
    Uses the optimized function from user_utils with controlled concurrency.

    Args:
        ctx: ARQ context

    Returns:
        Processing result message
    """
    from app.utils.watch_mail import renew_gmail_watch_subscriptions as renew_function

    # Use the optimized function with controlled concurrency
    return await renew_function(ctx, max_concurrent=15)


async def process_email_task(ctx: dict, user_id: str, email_data: dict) -> str:
    """
    Email processing task - handles workflow triggers and basic email processing.

    Args:
        ctx: ARQ context
        user_id: User ID from webhook
        email_data: Email data from webhook

    Returns:
        Processing result message
    """
    try:
        # Create processing session
        message_id = email_data.get("message_id", "unknown")
        session = create_session(message_id, user_id)
        workflow_executions = []

        try:
            session.log_milestone(
                "Email processing started",
                {
                    "user_id": user_id,
                    "email_message_id": message_id,
                    "processing_type": "unified_flow",
                },
            )

            # Step 1: Perform email analysis and store in database
            await perform_email_analysis(email_data, user_id, session)

            # Step 2: Find workflow matches
            matching_workflows = await find_matching_workflows(user_id)
            workflows_to_execute = []  # Initialize to ensure it's always defined

            # Apply intelligent LLM-based filtering before execution
            if matching_workflows:
                session.log_milestone(
                    f"Found {len(matching_workflows)} potential workflows, applying intelligent filtering"
                )

                filtered_results = await filter_workflows_for_email(
                    email_data, matching_workflows, user_id
                )

                # Extract workflows that should be executed
                workflows_to_execute = [
                    result["workflow"]
                    for result in filtered_results
                    if result["should_execute"]
                ]

                session.log_milestone(
                    f"LLM filtering complete: {len(workflows_to_execute)}/{len(matching_workflows)} workflows will execute"
                )

                # Log filtering decisions for monitoring
                for result in filtered_results:
                    decision = result["decision"]
                    logger.info(
                        f"Workflow {result['workflow'].id} filter decision: "
                        f"should_execute={decision.should_process}, "
                        f"confidence={decision.confidence}, "
                        f"reason={decision.reasoning[:100]}..."
                    )
            else:
                session.log_milestone("No email-triggered workflows found for user")

            # Execute filtered workflows with rate limiting
            if workflows_to_execute:
                trigger_context = {
                    "type": "gmail",
                    "email_data": email_data,
                    "triggered_at": datetime.now(timezone.utc).isoformat(),
                }

                for workflow in workflows_to_execute:
                    try:
                        execution_messages = await execute_workflow_as_chat(
                            workflow, {"user_id": user_id}, trigger_context
                        )

                        # Update workflow statistics
                        await workflows_collection.update_one(
                            {"_id": workflow.id, "user_id": user_id},
                            {
                                "$inc": {
                                    "total_executions": 1,
                                    "successful_executions": 1,
                                },
                                "$set": {
                                    "last_executed_at": datetime.now(timezone.utc)
                                },
                            },
                        )

                        workflow_executions.append(
                            {
                                "workflow_id": workflow.id,
                                "status": "success",
                                "messages_count": len(execution_messages),
                            }
                        )

                    except RateLimitExceededException as rate_error:
                        logger.warning(
                            f"Rate limit exceeded for user {user_id} executing workflow {workflow.id}: {rate_error}"
                        )
                        workflow_executions.append(
                            {
                                "workflow_id": workflow.id,
                                "status": "rate_limited",
                                "error": f"Rate limit exceeded: {str(rate_error)}",
                            }
                        )

                    except Exception as workflow_error:
                        logger.error(f"Workflow {workflow.id} failed: {workflow_error}")

                        workflow_executions.append(
                            {
                                "workflow_id": workflow.id,
                                "status": "error",
                                "error": str(workflow_error),
                            }
                        )

                        # Update failure statistics
                        try:
                            await workflows_collection.update_one(
                                {"_id": workflow.id, "user_id": user_id},
                                {"$inc": {"total_executions": 1}},
                            )
                        except Exception as stats_error:
                            logger.error(f"Failed to update stats: {stats_error}")
            # Basic email processing
            email_result = "Email processed successfully"

            session.log_session_summary(
                {
                    "status": "success",
                    "workflows_found": len(matching_workflows)
                    if matching_workflows
                    else 0,
                    "workflows_filtered": len(workflows_to_execute),
                    "workflows_executed": len(workflow_executions),
                    "workflow_executions": workflow_executions,
                    "email_processing": email_result,
                }
            )

            successful_executions = len(
                [w for w in workflow_executions if w["status"] == "success"]
            )
            failed_executions = len(
                [w for w in workflow_executions if w["status"] == "error"]
            )
            rate_limited_executions = len(
                [w for w in workflow_executions if w["status"] == "rate_limited"]
            )

            return f"Email processed successfully: {len(matching_workflows) if matching_workflows else 0} workflows found, {len(workflows_to_execute)} passed filtering, {len(workflow_executions)} executed (✅ {successful_executions} success, ❌ {failed_executions} failed, ⚠️ {rate_limited_executions} rate limited)"

        finally:
            if session:
                end_session(session.session_id)

    except Exception as e:
        error_msg = f"Failed to process email for user {user_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise
