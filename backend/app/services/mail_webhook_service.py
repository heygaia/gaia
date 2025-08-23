import json

from app.config.loggers import mail_webhook_logger as logger
from app.db.rabbitmq import publisher


async def queue_composio_email_processing(user_id: str, email_data: dict) -> dict:
    """
    Queue a Composio email for background processing.

    Args:
        user_id (str): The user ID from the webhook
        email_data (dict): The email data from Composio webhook

    Returns:
        dict: Response message indicating success
    """
    logger.info(
        f"Queueing Composio email processing: user_id={user_id}, message_id={email_data.get('message_id', 'unknown')}"
    )

    await publisher.publish(
        queue_name="composio-email-events",
        body=json.dumps(
            {
                "user_id": user_id,
                "email_data": email_data,
            }
        ).encode("utf-8"),
    )

    return {"message": "Composio email processing started successfully."}
