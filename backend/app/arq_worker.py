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
from app.workers.workflow_worker import (
    execute_workflow_by_id,
    generate_workflow_steps,
)

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
    ctx["startup_time"] = asyncio.get_event_loop().time()

    llm = init_llm()

    # Build the workflow processing graph excluding reminder tools
    # Reminder tools are excluded since AI agent reminders were removed
    # STATIC reminders still work via direct reminder service
    async with build_graph(
        chat_llm=llm,  # type: ignore[call-arg]
        exclude_tools=[
            create_reminder_tool.name,
            update_reminder_tool.name,
            delete_reminder_tool.name,
        ],
        in_memory_checkpointer=True,
    ) as workflow_graph:
        GraphManager.set_graph(workflow_graph, graph_name="workflow_processing")

    logger.info(
        "ARQ worker startup complete with workflow processing graph initialized"
    )


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

        # Convert to naive datetime for comparison with potentially naive database values
        seven_days_ago_naive = seven_days_ago.replace(tzinfo=None)

        # Find users inactive for 7+ days who haven't gotten email recently
        inactive_users = await users_collection.find(
            {
                "last_active_at": {"$lt": seven_days_ago_naive},
                "is_active": {"$ne": False},
                "$or": [
                    {"last_inactive_email_sent": {"$exists": False}},
                    {"last_inactive_email_sent": {"$lt": seven_days_ago_naive}},
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


async def process_email_task(ctx: dict, history_id: str, user_email: str) -> str:
    """
    Simple email processing task that uses the workflow processing graph.
    """
    from app.langchain.core.graph_manager import GraphManager

    try:
        logger.info(f"Processing email task for history_id: {history_id}")

        # Use the standard workflow processing graph for email tasks too
        graph = await GraphManager.get_graph("workflow_processing")
        if not graph:
            raise ValueError("Workflow processing graph not available")

        # Simple email processing logic here
        # TODO: Implement actual email processing logic
        result = f"Processed email {history_id} for {user_email}"

        logger.info(f"Email processing completed for {history_id}: {result}")
        return f"Email processed successfully: {result}"

    except Exception as e:
        error_msg = f"Failed to process email {history_id}: {str(e)}"
        logger.error(error_msg)
        raise


async def process_workflow_generation_task(
    ctx: dict, todo_id: str, user_id: str, title: str, description: str = ""
) -> str:
    """
    Process workflow generation task for todos.
    Migrated from RabbitMQ to ARQ for unified task processing.

    Args:
        ctx: ARQ context
        todo_id: Todo ID to generate workflow for
        user_id: User ID who owns the todo
        title: Todo title
        description: Todo description

    Returns:
        Processing result message
    """
    from datetime import datetime, timezone
    from bson import ObjectId
    from app.db.mongodb.collections import todos_collection
    from app.services.todo_service import TodoService
    from app.models.workflow_models import (
        CreateWorkflowRequest,
        TriggerConfig,
        TriggerType,
    )
    from app.services.workflow.service import WorkflowService

    logger.info(f"Processing workflow generation for todo {todo_id}: {title}")

    try:
        # Create standalone workflow using the new workflow system
        workflow_request = CreateWorkflowRequest(
            title=f"Todo: {title}",
            description=description or f"Workflow for todo: {title}",
            trigger_config=TriggerConfig(type=TriggerType.MANUAL, enabled=True),
            generate_immediately=True,  # Generate steps immediately
        )

        workflow = await WorkflowService.create_workflow(workflow_request, user_id)

        if workflow and workflow.id:
            # Update the todo with the workflow_id for linking
            update_data = {
                "workflow_id": workflow.id,
                "updated_at": datetime.now(timezone.utc),
            }

            result = await todos_collection.update_one(
                {"_id": ObjectId(todo_id), "user_id": user_id}, {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(
                    f"Successfully generated and linked standalone workflow {workflow.id} for todo {todo_id} with {len(workflow.steps)} steps"
                )

                # Invalidate cache for this todo
                await TodoService._invalidate_cache(user_id, None, todo_id, "update")

                return f"Successfully generated standalone workflow {workflow.id} for todo {todo_id}"
            else:
                raise ValueError(f"Todo {todo_id} not found or not updated")

        else:
            # Mark workflow generation as failed
            logger.error(
                f"Failed to generate workflow for todo {todo_id}: No workflow created"
            )
            raise ValueError("Workflow generation failed: No workflow created")

    except Exception as e:
        # Log the error but don't try to update legacy workflow fields
        error_msg = (
            f"Failed to process workflow generation for todo {todo_id}: {str(e)}"
        )
        logger.error(error_msg)
        raise


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
        process_email_task,
        process_workflow_generation_task,
        execute_workflow_by_id,
        generate_workflow_steps,
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
