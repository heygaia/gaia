"""
Email-related ARQ tasks.
"""

from app.config.loggers import arq_worker_logger as logger


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
        logger.info(f"Processing email for user {user_id}")

        from app.services.trigger_matching_service import GmailTriggerMatchingService
        from app.utils.session_logger.email_session_logger import (
            create_session,
            end_session,
        )
        from app.db.mongodb.collections import workflows_collection

        # Create processing session for the entire email processing pipeline
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

            # Step 1: Find workflow matches (doesn't queue them)
            trigger_service = GmailTriggerMatchingService()
            trigger_result = await trigger_service.process_gmail_event(
                user_id, email_data
            )

            matching_workflows = trigger_result.get("matching_workflows", [])
            logger.info(f"Found {len(matching_workflows)} matching workflows")

            # Step 2: Execute matched workflows directly in this context
            if matching_workflows:
                from datetime import datetime, timezone
                from app.workers.tasks.workflow_tasks import execute_workflow_as_chat

                trigger_context = {
                    "type": "gmail",
                    "email_data": email_data,
                    "triggered_at": datetime.now(timezone.utc).isoformat(),
                }

                for workflow in matching_workflows:
                    try:
                        logger.info(f"Executing triggered workflow {workflow.id}")

                        # Execute workflow directly
                        execution_messages = await execute_workflow_as_chat(
                            workflow, user_id, trigger_context
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

                    except Exception as workflow_error:
                        error_msg = (
                            f"Error executing workflow {workflow.id}: {workflow_error}"
                        )
                        logger.error(error_msg, exc_info=True)  # Include stack trace

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
                            logger.error(
                                f"Failed to update workflow failure stats: {stats_error}"
                            )
                            # Don't fail the entire email processing for stats errors

            # Step 3: Basic email processing (placeholder for future features)
            email_result = "Email processed successfully"

            session.log_session_summary(
                {
                    "status": "success",
                    "workflows_matched": len(matching_workflows),
                    "workflows_executed": len(
                        [w for w in workflow_executions if w["status"] == "success"]
                    ),
                    "workflow_executions": workflow_executions,
                    "email_processing": email_result,
                }
            )

            logger.info(
                f"Email processing completed for user {user_id}: {len(matching_workflows)} workflows triggered"
            )

            return f"Email processed successfully: {len(matching_workflows)} workflows triggered, {len(workflow_executions)} executed"

        finally:
            if session:
                end_session(session.session_id)

    except Exception as e:
        error_msg = f"Failed to process email for user {user_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)  # Include stack trace for debugging
        raise
