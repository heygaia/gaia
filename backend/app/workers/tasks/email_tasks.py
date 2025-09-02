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
