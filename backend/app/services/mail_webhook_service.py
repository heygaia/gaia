from app.config.loggers import mail_webhook_logger as logger
from app.config.settings import settings
from arq import create_pool
from arq.connections import RedisSettings


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

    try:
        # Create ARQ connection pool
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        pool = await create_pool(redis_settings)

        # Enqueue the email processing task
        job = await pool.enqueue_job(
            "process_email_task",
            user_id,
            email_data,
        )

        await pool.close()

        if job:
            logger.info(
                f"Successfully queued email processing task with job ID: {job.job_id}"
            )
            return {
                "message": "Email processing started successfully.",
                "job_id": job.job_id,
            }
        else:
            logger.error("Failed to enqueue email processing task")
            return {"message": "Failed to start email processing."}

    except Exception as e:
        logger.error(f"Error queuing email processing: {str(e)}")
        return {"message": f"Error starting email processing: {str(e)}"}
