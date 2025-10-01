"""ARQ worker task for Gmail email memory processing."""

from app.config.loggers import app_logger as logger
from app.agents.memory.email_processor import process_gmail_to_memory


async def process_gmail_emails_to_memory(ctx, user_id: str) -> str:
    """
    ARQ background task to process Gmail emails into memories.

    Args:
        ctx: ARQ context (unused but required)
        user_id: User ID to process emails for

    Returns:
        Processing result message
    """
    try:
        logger.info(f"Starting Gmail email processing task for user {user_id}")

        # Use the existing service function
        await process_gmail_to_memory(user_id)

        success_message = f"Gmail email processing completed for user {user_id}"
        logger.info(success_message)
        return success_message

    except Exception as e:
        error_message = f"Fatal error in Gmail email processing for user {user_id}: {e}"
        logger.error(error_message, exc_info=True)
        return error_message
