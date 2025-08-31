from arq import create_pool
from arq.connections import RedisSettings

from app.config.loggers import mail_webhook_logger as logger
from app.config.settings import settings


async def queue_email_processing(email_address: str, history_id: int) -> dict:
    """
    Queue an email for background processing using ARQ.

    Args:
        email_address (str): The email address associated with the webhook
        history_id (int): The history ID from the webhook

    Returns:
        dict: Response message indicating success
    """
    logger.info(
        f"Queueing email processing: email={email_address}, historyId={history_id}"
    )

    try:
        # Create ARQ connection pool
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        pool = await create_pool(redis_settings)

        # Enqueue the email processing task
        job = await pool.enqueue_job(
            "process_email_task",
            history_id,
            email_address,
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
