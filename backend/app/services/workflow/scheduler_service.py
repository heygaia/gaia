"""Workflow scheduling service for time-based execution."""

from datetime import datetime, timezone

from app.config.loggers import general_logger as logger
from app.db.mongodb.collections import workflows_collection
from app.utils.redis_utils import RedisPoolManager


class WorkflowSchedulerService:
    """Service for scheduling workflow executions."""

    @staticmethod
    async def schedule_workflow_execution(
        workflow_id: str, user_id: str, scheduled_at: datetime
    ) -> None:
        """Schedule workflow execution at a specific time using ARQ."""
        try:
            pool = await RedisPoolManager.get_pool()

            job = await pool.enqueue_job(
                "process_workflow",
                workflow_id,
                user_id,
                {},  # context
                _defer_until=scheduled_at,
            )

            if job:
                # Store job ID in workflow document for cancellation
                await workflows_collection.update_one(
                    {"_id": workflow_id, "user_id": user_id},
                    {
                        "$set": {
                            "scheduled_job_id": job.job_id,
                            "scheduled_at": scheduled_at,
                            "updated_at": datetime.now(timezone.utc),
                        }
                    },
                )
                logger.info(
                    f"Scheduled workflow {workflow_id} for execution at {scheduled_at} with job ID {job.job_id}"
                )
            else:
                logger.error(f"Failed to schedule workflow execution for {workflow_id}")

        except Exception as e:
            logger.error(
                f"Error scheduling workflow execution for {workflow_id}: {str(e)}"
            )

    @staticmethod
    async def cancel_scheduled_workflow_execution(workflow_id: str) -> None:
        """Cancel any pending scheduled executions for a workflow."""
        try:
            # Get the workflow to retrieve the scheduled job ID
            workflow_doc = await workflows_collection.find_one(
                {"_id": workflow_id}, {"scheduled_job_id": 1, "scheduled_at": 1}
            )

            if not workflow_doc:
                logger.warning(f"Workflow {workflow_id} not found for cancellation")
                return

            scheduled_job_id = workflow_doc.get("scheduled_job_id")

            if scheduled_job_id:
                try:
                    pool = await RedisPoolManager.get_pool()

                    # Get job info and try to cancel it
                    # ARQ uses Redis keys for job storage, we can try to delete the job
                    job_key = f"arq:job:{scheduled_job_id}"
                    redis_client = pool  # ARQ pool is a Redis connection

                    # Delete the job from Redis if it exists
                    deleted = await redis_client.delete(job_key)

                    if deleted:
                        logger.info(
                            f"Successfully cancelled job {scheduled_job_id} for workflow {workflow_id}"
                        )
                    else:
                        logger.info(
                            f"Job {scheduled_job_id} for workflow {workflow_id} may have already started or completed"
                        )

                except Exception as abort_error:
                    logger.warning(
                        f"Could not cancel job {scheduled_job_id}: {abort_error}"
                    )
                    # Continue to clear the job ID even if cancellation failed

                # Clear the job ID from the workflow document regardless of abort success
                await workflows_collection.update_one(
                    {"_id": workflow_id},
                    {
                        "$unset": {"scheduled_job_id": "", "scheduled_at": ""},
                        "$set": {"updated_at": datetime.now(timezone.utc)},
                    },
                )
                logger.info(f"Cleared scheduled job data for workflow {workflow_id}")
            else:
                logger.info(f"No scheduled job found for workflow {workflow_id}")

        except Exception as e:
            logger.error(
                f"Error cancelling scheduled execution for {workflow_id}: {str(e)}"
            )
