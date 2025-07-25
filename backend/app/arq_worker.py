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
from app.models.arq_event_models import EventType


async def startup(ctx: dict):
    """ARQ worker startup function."""
    from app.langchain.core.graph_builder.build_graph import build_graph
    from app.langchain.core.graph_builder.build_workflow_processing_graph import (
        build_workflow_processing_graph,
    )
    from app.langchain.core.graph_manager import GraphManager
    from app.langchain.tools.workflow_tool import (
        create_workflow_tool,
        delete_workflow_tool,
        update_workflow_tool,
    )

    logger.info("ARQ worker starting up...")

    # Initialize any resources needed by worker
    # For example, database connections, external service clients, etc.
    ctx["startup_time"] = asyncio.get_event_loop().time()
    logger.info("ARQ worker startup complete")

    llm = init_llm()

    # Register and Build the general processing graph
    async with build_graph(
        chat_llm=llm,  # type: ignore[call-arg]
        exclude_tools=[
            create_workflow_tool.name,
            delete_workflow_tool.name,
            update_workflow_tool.name,
        ],
        in_memory_checkpointer=True,
    ) as built_graph:
        GraphManager.set_graph(built_graph, graph_name="default")

    # Register and Build the workflow processing graph with runtime conditional edges
    async with build_workflow_processing_graph() as workflow_graph:
        GraphManager.set_graph(workflow_graph, graph_name="workflow_processing")


async def shutdown(ctx: dict):
    """ARQ worker shutdown function."""
    logger.info("ARQ worker shutting down...")

    # Clean up any resources
    startup_time = ctx.get("startup_time", 0)
    runtime = asyncio.get_event_loop().time() - startup_time
    logger.info(f"ARQ worker ran for {runtime:.2f} seconds")


async def process_event(ctx: dict, event_id: str) -> str:
    """
    Process an event task (reminder or workflow).

    Args:
        ctx: ARQ context
        event_id: ID of the event to process in format "type:id"

    Returns:
        Processing result message
    """
    logger.info(f"Processing event task: {event_id}")

    try:
        [event_type, event_id] = event_id.split(":")

        if event_type == EventType.REMINDER:
            from app.services.reminder_service import process_reminder_task

            await process_reminder_task(event_id)
            result = f"Successfully processed reminder {event_id}"
        elif event_type == EventType.WORKFLOW:
            from app.services.workflow_service import process_workflow_task

            await process_workflow_task(event_id)
            result = f"Successfully processed workflow {event_id}"
        else:
            result = f"Unknown event type: {event_type}"
            logger.error(result)

        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Error processing event {event_id}: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def check_inactive_users(ctx: dict) -> str:
    """
    Check for inactive users and send emails to those inactive for more than 7 days.

    Args:
        ctx: ARQ context

    Returns:
        Processing result message
    """
    from app.db.mongodb.collections import users_collection
    from app.utils.email_utils import send_inactive_user_email

    logger.info("Checking for inactive users")

    try:
        # Find users inactive for more than 7 days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        inactive_users = await users_collection.find(
            {
                "last_active_at": {"$lt": seven_days_ago},
                "is_active": {"$ne": False},  # Only active users
            }
        ).to_list(length=None)

        email_count = 0
        for user in inactive_users:
            try:
                await send_inactive_user_email(
                    user_email=user["email"], user_name=user.get("name")
                )
                email_count += 1
                logger.info(f"Sent inactive user email to {user['email']}")
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


class WorkerSettings:
    """
    ARQ worker settings configuration.
    This class defines the settings for the ARQ worker, including Redis connection,
    task functions, scheduled jobs, and performance settings.
    """

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions = [
        process_event,
        check_inactive_users,
        renew_gmail_watch_subscriptions,
    ]
    cron_jobs = [
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
