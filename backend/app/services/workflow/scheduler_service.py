"""
Workflow scheduling service - thin wrapper around WorkflowScheduler.

This maintains the existing API while leveraging the robust BaseSchedulerService
foundation for enhanced scheduling capabilities.
"""

from datetime import datetime
from typing import Optional

from app.config.loggers import general_logger as logger
from app.models.scheduler_models import ScheduleConfig, ScheduledTaskStatus
from app.services.workflow.scheduler import WorkflowScheduler


class WorkflowSchedulerService:
    """
    Service for scheduling workflow executions.

    Now powered by BaseSchedulerService with support for:
    - Recurring workflows with cron expressions
    - Occurrence counting and limits
    - Stop dates and advanced scheduling
    - Robust error handling and status management
    """

    def __init__(self):
        """Initialize with WorkflowScheduler instance."""
        self.scheduler = WorkflowScheduler()

    async def initialize(self):
        """Initialize the underlying scheduler."""
        await self.scheduler.initialize()

    async def close(self):
        """Close the underlying scheduler."""
        await self.scheduler.close()

    async def schedule_workflow_execution(
        self,
        workflow_id: str,
        user_id: str,
        scheduled_at: datetime,
        repeat: Optional[str] = None,
        max_occurrences: Optional[int] = None,
        stop_after: Optional[datetime] = None,
    ) -> bool:
        """
        Schedule workflow execution using BaseSchedulerService.

        Args:
            workflow_id: Workflow ID to schedule
            user_id: User ID (for validation)
            scheduled_at: When to execute
            repeat: Cron expression for recurring workflows
            max_occurrences: Limit number of executions
            stop_after: Stop executing after this date

        Returns:
            True if scheduled successfully
        """
        try:
            # Create schedule configuration
            schedule_config = ScheduleConfig(
                scheduled_at=scheduled_at,
                repeat=repeat,
                max_occurrences=max_occurrences,
                stop_after=stop_after,
                base_time=scheduled_at,  # Use scheduled_at as base for timezone calculations
            )

            # Use the robust BaseSchedulerService scheduling
            success = await self.scheduler.schedule_task(workflow_id, schedule_config)

            if success:
                logger.info(
                    f"Scheduled workflow {workflow_id} for execution at {scheduled_at}"
                    + (f" with repeat '{repeat}'" if repeat else "")
                )
            else:
                logger.error(f"Failed to schedule workflow {workflow_id}")

            return success

        except Exception as e:
            logger.error(f"Error scheduling workflow {workflow_id}: {str(e)}")
            return False

    async def cancel_scheduled_workflow_execution(self, workflow_id: str) -> bool:
        """
        Cancel scheduled workflow execution.

        Args:
            workflow_id: Workflow ID to cancel

        Returns:
            True if cancelled successfully
        """
        try:
            # Update workflow status to cancelled in database
            db_success = await self.scheduler.update_task_status(
                workflow_id, ScheduledTaskStatus.CANCELLED
            )

            # Cancel ARQ job
            arq_success = await self.scheduler.cancel_task(workflow_id, "")

            if db_success and arq_success:
                logger.info(f"Cancelled scheduled execution for workflow {workflow_id}")
            elif db_success:
                logger.warning(
                    f"Cancelled workflow {workflow_id} in DB but ARQ cancellation failed"
                )
            else:
                logger.warning(
                    f"Could not cancel workflow {workflow_id} - may not exist or already executed"
                )

            return db_success

        except Exception as e:
            logger.error(f"Error cancelling workflow {workflow_id}: {str(e)}")
            return False

    async def reschedule_workflow(
        self, workflow_id: str, new_scheduled_at: datetime, repeat: Optional[str] = None
    ) -> bool:
        """
        Reschedule an existing workflow.

        Args:
            workflow_id: Workflow ID to reschedule
            new_scheduled_at: New execution time
            repeat: New cron expression (optional)

        Returns:
            True if rescheduled successfully
        """
        try:
            # Update the workflow's scheduling fields in database
            update_data = {
                "scheduled_at": new_scheduled_at,
                "status": ScheduledTaskStatus.SCHEDULED.value,
            }

            if repeat is not None:
                update_data["repeat"] = repeat

            # Update database status
            db_success = await self.scheduler.update_task_status(
                workflow_id, ScheduledTaskStatus.SCHEDULED, update_data
            )

            if not db_success:
                logger.error(f"Failed to update workflow {workflow_id} in database")
                return False

            # Actually reschedule in ARQ queue
            arq_success = await self.scheduler.reschedule_task(
                workflow_id, new_scheduled_at
            )

            if arq_success:
                logger.info(
                    f"Rescheduled workflow {workflow_id} for {new_scheduled_at}"
                )
            else:
                logger.error(
                    f"Failed to reschedule workflow {workflow_id} in ARQ queue"
                )

            return arq_success

        except Exception as e:
            logger.error(f"Error rescheduling workflow {workflow_id}: {str(e)}")
            return False

    async def get_workflow_status(self, workflow_id: str) -> Optional[str]:
        """
        Get the current status of a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Status string or None if not found
        """
        try:
            workflow = await self.scheduler.get_task(workflow_id)
            return workflow.status.value if workflow else None
        except Exception as e:
            logger.error(f"Error getting workflow status for {workflow_id}: {str(e)}")
            return None


# Global instance for backward compatibility
workflow_scheduler_service = WorkflowSchedulerService()
