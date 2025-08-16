"""
ARQ worker for processing reminder tasks.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from arq import cron
from arq.connections import RedisSettings

from app.config.loggers import arq_worker_logger as logger
from app.config.settings import settings
from app.langchain.llm.client import init_llm
from app.services.reminder_service import reminder_scheduler

# from app.tasks.subscription_cleanup import (
#     cleanup_abandoned_subscriptions,
#     reconcile_subscription_payments,
# )


async def startup(ctx: dict):
    from app.langchain.core.graph_builder.build_graph import build_graph
    from app.langchain.core.graph_manager import GraphManager
    from app.langchain.tools.reminder_tool import (
        create_reminder_tool,
        delete_reminder_tool,
        update_reminder_tool,
    )

    """ARQ worker startup function."""
    logger.info("ARQ worker starting up...")

    # Initialize any resources needed by worker
    # For example, database connections, external service clients, etc.
    ctx["startup_time"] = asyncio.get_event_loop().time()
    logger.info("ARQ worker startup complete")

    llm = init_llm()

    # Register and Build the processing graph
    async with build_graph(
        chat_llm=llm,  # type: ignore[call-arg]
        exclude_tools=[
            create_reminder_tool.name,
            update_reminder_tool.name,
            delete_reminder_tool.name,
        ],
        in_memory_checkpointer=True,
    ) as built_graph:
        GraphManager.set_graph(built_graph, graph_name="reminder_processing")


# async def cleanup_abandoned_subscriptions_task(ctx: dict) -> str:
#     """ARQ task wrapper for cleaning up abandoned subscriptions."""
#     try:
#         result = await cleanup_abandoned_subscriptions()
#         message = f"Subscription cleanup completed. Status: {result['status']}, Cleaned: {result.get('cleaned_up_count', 0)}"
#         logger.info(message)
#         return message
#     except Exception as e:
#         error_msg = f"Failed to cleanup abandoned subscriptions: {str(e)}"
#         logger.error(error_msg)
#         raise


# async def reconcile_subscription_payments_task(ctx: dict) -> str:
#     """ARQ task wrapper for reconciling subscription payments."""
#     try:
#         result = await reconcile_subscription_payments()
#         message = f"Payment reconciliation completed. Status: {result['status']}, Reconciled: {result.get('reconciled_count', 0)}, Deactivated: {result.get('deactivated_count', 0)}"
#         logger.info(message)
#         return message
#     except Exception as e:
#         error_msg = f"Failed to reconcile subscription payments: {str(e)}"
#         logger.error(error_msg)
#         raise
#     """ARQ worker shutdown function."""
#     logger.info("ARQ worker shutting down...")

#     # Clean up any resources
#     startup_time = ctx.get("startup_time", 0)
#     runtime = asyncio.get_event_loop().time() - startup_time
#     logger.info(f"ARQ worker ran for {runtime:.2f} seconds")


async def process_reminder(ctx: dict, reminder_id: str) -> str:
    """
    Process a reminder task.

    Args:
        ctx: ARQ context
        reminder_id: ID of the reminder to process

    Returns:
        Processing result message
    """
    logger.info(f"Processing reminder task: {reminder_id}")

    try:
        # Process the reminder
        await reminder_scheduler.process_task_execution(reminder_id)

        result = f"Successfully processed reminder {reminder_id}"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Failed to process reminder {reminder_id}: {str(e)}"
        logger.error(error_msg)
        raise


async def cleanup_expired_reminders(ctx: dict) -> str:
    """
    Cleanup expired or completed reminders (scheduled task).

    Args:
        ctx: ARQ context

    Returns:
        Cleanup result message
    """
    from app.db.mongodb.collections import reminders_collection

    logger.info("Running cleanup of expired reminders")

    try:
        # Remove completed reminders older than 30 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        result = await reminders_collection.delete_many(
            {
                "status": {"$in": ["completed", "cancelled"]},
                "updated_at": {"$lt": cutoff_date},
            }
        )

        message = f"Cleaned up {result.deleted_count} expired reminders"
        logger.info(message)
        return message

    except Exception as e:
        error_msg = f"Failed to cleanup expired reminders: {str(e)}"
        logger.error(error_msg)
        raise


async def check_inactive_users(ctx: dict) -> str:
    """
    Check for inactive users and send emails to those inactive for more than 7 days.
    Emails are sent only once after 7 days and once more after 14 days to avoid spam.

    Args:
        ctx: ARQ context

    Returns:
        Processing result message
    """
    from app.db.mongodb.collections import users_collection
    from app.utils.email_utils import send_inactive_user_email

    logger.info("Checking for inactive users")

    try:
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        # Find users inactive for 7+ days who haven't gotten email recently
        inactive_users = await users_collection.find(
            {
                "last_active_at": {"$lt": seven_days_ago},
                "is_active": {"$ne": False},
                "$or": [
                    {"last_inactive_email_sent": {"$exists": False}},
                    {"last_inactive_email_sent": {"$lt": seven_days_ago}},
                ],
            }
        ).to_list(length=None)

        email_count = 0
        for user in inactive_users:
            try:
                sent = await send_inactive_user_email(
                    user_email=user["email"],
                    user_name=user.get("name"),
                    user_id=str(user["_id"]),
                )

                if sent:
                    email_count += 1
                    logger.info(f"Sent inactive email to {user['email']}")

            except Exception as e:
                logger.error(f"Failed to send email to {user['email']}: {str(e)}")

        message = (
            f"Processed {len(inactive_users)} inactive users, sent {email_count} emails"
        )
        logger.info(message)
        return message

    except Exception as e:
        error_msg = f"Failed to check inactive users: {str(e)}"
        logger.error(error_msg)
        raise


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


async def process_workflow(
    ctx: dict, workflow_id: str, user_id: str, context: dict
) -> str:
    """
    Process a workflow execution task.
    Executes workflow steps sequentially via the existing LangChain graph.

    Args:
        ctx: ARQ context
        workflow_id: ID of the workflow to execute
        user_id: ID of the user who owns the workflow
        context: Optional execution context

    Returns:
        Processing result message
    """
    logger.info(f"Processing workflow execution: {workflow_id} for user {user_id}")

    try:
        # Import here to avoid circular imports
        from app.services.workflow_service import WorkflowService
        from app.models.workflow_models import UpdateWorkflowRequest, WorkflowStatus
        from app.langchain.core.graph_manager import GraphManager

        # Get the workflow
        workflow = await WorkflowService.get_workflow(workflow_id, user_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not workflow.steps:
            raise ValueError(f"Workflow {workflow_id} has no steps to execute")

        # Update workflow status to running
        await WorkflowService.update_workflow(
            workflow_id,
            UpdateWorkflowRequest(status=WorkflowStatus.RUNNING),
            user_id,
        )

        # Get the processing graph
        graph = GraphManager.get_graph("reminder_processing")
        if not graph:
            raise ValueError("Processing graph not available")

        # Execute workflow steps sequentially
        execution_results = []
        accumulated_context = context or {}

        for step_index, step in enumerate(workflow.steps):
            try:
                logger.info(
                    f"Executing step {step_index + 1}/{len(workflow.steps)}: {step.title}"
                )

                # Update current step status
                step.status = WorkflowStatus.RUNNING
                step.executed_at = datetime.now(timezone.utc)

                # Update workflow with current step progress
                await WorkflowService.update_workflow(
                    workflow_id,
                    UpdateWorkflowRequest(steps=workflow.steps),
                    user_id,
                )

                # Execute the tool directly via graph
                graph_config = {
                    "configurable": {
                        "user_id": user_id,
                        "conversation_id": f"workflow_{workflow_id}",
                        "thread_id": f"workflow_{workflow_id}_step_{step_index}",
                    }
                }

                # Create a tool execution message
                tool_message = f"Use {step.tool_name} tool"
                if step.tool_inputs:
                    tool_message += f" with inputs: {step.tool_inputs}"

                # Execute via graph
                result = await graph.ainvoke(
                    {"messages": [{"role": "user", "content": tool_message}]},
                    config=graph_config,
                )

                # Extract result from graph response
                step_result = {
                    "step_id": step.id,
                    "tool_name": step.tool_name,
                    "status": "completed",
                    "result": result.get("messages", [])[-1].get("content", "")
                    if result.get("messages")
                    else "",
                    "executed_at": step.executed_at.isoformat(),
                }

                # Update step with results
                step.status = WorkflowStatus.COMPLETED
                step.result = step_result
                execution_results.append(step_result)

                # Add to accumulated context for next steps
                accumulated_context[f"step_{step_index + 1}_result"] = step_result[
                    "result"
                ]

                logger.info(f"Completed step {step_index + 1}: {step.title}")

            except Exception as step_error:
                logger.error(
                    f"Failed to execute step {step_index + 1}: {str(step_error)}"
                )

                # Mark step as failed
                step.status = WorkflowStatus.FAILED
                step.result = {"error": str(step_error)}

                # Update workflow with failed step
                await WorkflowService.update_workflow(
                    workflow_id,
                    UpdateWorkflowRequest(
                        status=WorkflowStatus.FAILED,
                        steps=workflow.steps,
                    ),
                    user_id,
                )

                raise step_error

        # All steps completed successfully
        workflow.total_executions += 1
        workflow.successful_executions += 1
        workflow.last_executed_at = datetime.now(timezone.utc)

        await WorkflowService.update_workflow(
            workflow_id,
            UpdateWorkflowRequest(
                status=WorkflowStatus.COMPLETED,
                steps=workflow.steps,
            ),
            user_id,
        )

        # Create result summary and notification
        await _create_workflow_completion_notification(
            workflow, execution_results, user_id
        )

        result = f"Successfully executed workflow {workflow_id} with {len(workflow.steps)} steps"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Failed to process workflow {workflow_id}: {str(e)}"
        logger.error(error_msg)

        # Mark workflow as failed
        try:
            from app.services.workflow_service import WorkflowService
            from app.models.workflow_models import UpdateWorkflowRequest, WorkflowStatus

            workflow = await WorkflowService.get_workflow(workflow_id, user_id)
            if workflow:
                workflow.total_executions += 1

            await WorkflowService.update_workflow(
                workflow_id,
                UpdateWorkflowRequest(
                    status=WorkflowStatus.FAILED,
                ),
                user_id,
            )
        except Exception as update_e:
            logger.error(
                f"Failed to mark workflow {workflow_id} as failed: {str(update_e)}"
            )

        raise


async def generate_workflow_steps(ctx: dict, workflow_id: str, user_id: str) -> str:
    """
    Generate workflow steps for a workflow.

    Args:
        ctx: ARQ context
        workflow_id: ID of the workflow to generate steps for
        user_id: ID of the user who owns the workflow

    Returns:
        Processing result message
    """
    logger.info(f"Generating workflow steps: {workflow_id} for user {user_id}")

    try:
        # Import here to avoid circular imports
        from app.services.workflow_service import WorkflowService

        # Generate steps using the service method
        await WorkflowService._generate_workflow_steps(workflow_id, user_id)

        result = f"Successfully generated steps for workflow {workflow_id}"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Failed to generate workflow steps {workflow_id}: {str(e)}"
        logger.error(error_msg)
        raise


async def check_scheduled_workflows(ctx: dict) -> str:
    """
    Check for scheduled workflows that need to be executed.

    Args:
        ctx: ARQ context

    Returns:
        Processing result message
    """
    logger.info("Checking for scheduled workflows")

    try:
        from app.db.mongodb.collections import workflows_collection
        from app.models.workflow_models import WorkflowStatus
        from datetime import datetime, timezone

        # Find workflows that are scheduled and enabled
        cursor = workflows_collection.find(
            {
                "status": WorkflowStatus.ACTIVE,
                "trigger_config.type": "schedule",
                "trigger_config.enabled": True,
                "trigger_config.next_run": {"$lte": datetime.now(timezone.utc)},
            }
        )

        executed_count = 0
        async for workflow_doc in cursor:
            try:
                # Queue workflow execution
                from arq import create_pool
                from arq.connections import RedisSettings
                from app.config.settings import settings

                redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
                pool = await create_pool(redis_settings)

                job = await pool.enqueue_job(
                    "process_workflow", workflow_doc["_id"], workflow_doc["user_id"]
                )

                if job:
                    executed_count += 1
                    logger.info(f"Queued scheduled workflow {workflow_doc['_id']}")

                await pool.close()

            except Exception as e:
                logger.error(
                    f"Failed to queue scheduled workflow {workflow_doc['_id']}: {str(e)}"
                )

        result = f"Checked scheduled workflows, queued {executed_count} for execution"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Failed to check scheduled workflows: {str(e)}"
        logger.error(error_msg)
        raise


async def _create_workflow_completion_notification(
    workflow, execution_results, user_id: str
):
    """Create a new conversation with workflow results and send notification."""
    try:
        # Import here to avoid circular imports
        from app.db.mongodb.collections import conversations_collection
        from app.services.notification_service import notification_service
        from app.models.notification.notification_models import NotificationRequest
        from datetime import datetime, timezone
        import uuid

        # Create conversation content
        content = f"""🎯 **Workflow Completed: {workflow.title}**

📝 **Original Goal:** {workflow.goal}

✅ **Execution Summary:**
• Total Steps: {len(workflow.steps)}
• Completed: {len(execution_results)}
• Duration: {(datetime.now(timezone.utc) - workflow.last_executed_at).total_seconds():.1f}s

🔧 **Step Results:**
"""

        for i, result in enumerate(execution_results, 1):
            content += f"\n{i}. **{result['step_id']}** - {result['status'].title()}"
            if result.get("result"):
                # Truncate long results
                result_text = (
                    str(result["result"])[:200] + "..."
                    if len(str(result["result"])) > 200
                    else str(result["result"])
                )
                content += f"\n   📄 {result_text}"

        content += f"\n\n🕒 **Completed:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"

        # Create new conversation
        conversation_doc = {
            "_id": f"conv_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "title": f"Workflow Results: {workflow.title}",
            "messages": [
                {
                    "role": "assistant",
                    "content": content,
                    "timestamp": datetime.now(timezone.utc),
                    "metadata": {
                        "type": "workflow_completion",
                        "workflow_id": workflow.id,
                        "created_by": "GAIA",
                    },
                }
            ],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_pinned": False,
            "metadata": {
                "created_by": "workflow_system",
                "workflow_id": workflow.id,
                "workflow_title": workflow.title,
            },
        }

        # Insert conversation
        await conversations_collection.insert_one(conversation_doc)
        logger.info(
            f"Created workflow completion conversation for workflow {workflow.id}"
        )

        # Send notification
        notification_request = NotificationRequest(
            user_id=user_id,
            title=f"Workflow Completed: {workflow.title}",
            message=f"Your workflow '{workflow.title}' has completed successfully with {len(execution_results)} steps.",
            type="workflow_completion",
            metadata={
                "workflow_id": workflow.id,
                "conversation_id": conversation_doc["_id"],
            },
        )

        await notification_service.create_notification(notification_request)
        logger.info(f"Sent workflow completion notification for workflow {workflow.id}")

    except Exception as e:
        logger.error(f"Failed to create workflow completion notification: {str(e)}")
        # Don't raise - this shouldn't fail the workflow execution


async def shutdown(ctx: dict):
    """ARQ worker shutdown function."""
    logger.info("ARQ worker shutting down...")
    # Clean up any resources if needed


class WorkerSettings:
    """
    ARQ worker settings configuration.
    This class defines the settings for the ARQ worker, including Redis connection,
    task functions, scheduled jobs, and performance settings.
    """

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions = [
        process_reminder,
        cleanup_expired_reminders,
        check_inactive_users,
        renew_gmail_watch_subscriptions,
        process_workflow,
        generate_workflow_steps,
        check_scheduled_workflows,
        # cleanup_abandoned_subscriptions_task,
        # reconcile_subscription_payments_task,
    ]
    cron_jobs = [
        cron(
            cleanup_expired_reminders,
            hour=0,  # At midnight
            minute=0,  # At the start of the hour
            second=0,  # At the start of the minute
        ),
        cron(
            check_inactive_users,
            hour=9,  # At 9 AM
            minute=0,  # At the start of the hour
            second=0,  # At the start of the minute
        ),
        cron(
            renew_gmail_watch_subscriptions,
            hour=2,  # At 2 AM (different from other jobs to spread load)
            minute=0,  # At the start of the hour
            second=0,  # At the start of the minute
        ),
        cron(
            check_scheduled_workflows,
            minute={0, 15, 30, 45},  # Every 15 minutes
            second=0,
        ),
        # cron(
        #     cleanup_abandoned_subscriptions_task,
        #     minute={0, 30},  # Every 30 minutes
        #     second=0,
        # ),
        # cron(
        #     reconcile_subscription_payments_task,
        #     hour=1,  # At 1 AM daily
        #     minute=0,
        #     second=0,
        # ),
    ]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300  # 5 minutes
    keep_result = 0  # Don't keep results in Redis
    log_results = True
    health_check_interval = 30  # seconds
    health_check_key = "arq:health"
    allow_abort_jobs = True
