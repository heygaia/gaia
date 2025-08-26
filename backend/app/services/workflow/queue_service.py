"""Workflow queue service for background job management."""

from typing import Optional

from app.config.loggers import general_logger as logger
from app.utils.redis_utils import RedisPoolManager


class WorkflowQueueService:
    """Service for managing workflow job queues."""

    @staticmethod
    async def queue_workflow_generation(workflow_id: str, user_id: str) -> None:
        """Queue workflow generation as a background task."""
        try:
            pool = await RedisPoolManager.get_pool()

            job = await pool.enqueue_job(
                "generate_workflow_steps", workflow_id, user_id
            )

            if job:
                logger.info(
                    f"Queued workflow generation for {workflow_id} with job ID {job.job_id}"
                )
            else:
                logger.error(f"Failed to queue workflow generation for {workflow_id}")

        except Exception as e:
            logger.error(
                f"Error queuing workflow generation for {workflow_id}: {str(e)}"
            )
            # Note: Fallback to direct execution would need to be handled at the service level
            # to avoid circular imports

    @staticmethod
    async def queue_workflow_execution(
        workflow_id: str, user_id: str, context: Optional[dict] = None
    ) -> None:
        """Queue workflow execution as a background task."""
        try:
            pool = await RedisPoolManager.get_pool()

            job = await pool.enqueue_job(
                "execute_workflow_by_id", workflow_id, context or {}
            )

            if job:
                logger.info(
                    f"Queued workflow execution for {workflow_id} with job ID {job.job_id}"
                )
            else:
                logger.error(f"Failed to queue workflow execution for {workflow_id}")

        except Exception as e:
            logger.error(
                f"Error queuing workflow execution for {workflow_id}: {str(e)}"
            )
