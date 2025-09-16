"""
Workflow scheduler extending BaseSchedulerService for robust scheduling.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config.loggers import general_logger as logger
from app.db.mongodb.collections import workflows_collection
from app.models.scheduler_models import (
    BaseScheduledTask,
    ScheduledTaskStatus,
    TaskExecutionResult,
)
from app.models.workflow_models import Workflow
from app.services.scheduler_service import BaseSchedulerService
from arq.connections import RedisSettings


class WorkflowScheduler(BaseSchedulerService):
    """
    Workflow scheduler using BaseSchedulerService foundation.

    Inherits all robust scheduling capabilities:
    - Recurring task logic with occurrence counting
    - Status management (SCHEDULED → EXECUTING → COMPLETED)
    - ARQ integration for reliable job queuing
    - Cron expression handling
    - stop_after and max_occurrences support
    """

    def __init__(self, redis_settings: Optional[RedisSettings] = None):
        """Initialize the workflow scheduler."""
        super().__init__(redis_settings)

    def get_job_name(self) -> str:
        """Get the ARQ job name for workflow processing."""
        return "execute_workflow_by_id"

    async def get_task(
        self, task_id: str, user_id: Optional[str] = None
    ) -> Optional[Workflow]:
        """
        Get a workflow by ID.

        Args:
            task_id: Workflow ID
            user_id: Optional user ID for additional validation

        Returns:
            Workflow object or None if not found
        """
        try:
            query = {"_id": task_id}
            if user_id:
                query["user_id"] = user_id

            workflow_doc = await workflows_collection.find_one(query)
            if not workflow_doc:
                logger.warning(f"Workflow {task_id} not found")
                return None

            # Transform MongoDB document to Workflow object
            workflow_doc["id"] = workflow_doc.get("_id")
            if "_id" in workflow_doc:
                del workflow_doc["_id"]

            return Workflow(**workflow_doc)
        except Exception as e:
            logger.error(f"Error fetching workflow {task_id}: {e}")
            return None

    async def execute_task(self, task: BaseScheduledTask) -> TaskExecutionResult:
        """
        Execute a workflow task.

        This delegates to the existing workflow worker logic
        while providing the BaseSchedulerService interface.

        Args:
            task: Workflow to execute (extending BaseScheduledTask)

        Returns:
            Task execution result
        """
        try:
            # Cast to Workflow since we know it's a workflow
            workflow: Optional[Workflow] = task if isinstance(task, Workflow) else None
            print(workflow)
            if not workflow:
                raise ValueError("Task must be a Workflow instance")

            # Import here to avoid circular imports
            from app.workers.tasks import execute_workflow_as_chat

            logger.info(f"Executing workflow {workflow.id}")

            # Ensure task.id is not None
            if not workflow.id:
                raise ValueError("Workflow ID is required for execution")

            # Execute the workflow using the chat execution function directly
            await execute_workflow_as_chat(workflow, {"user_id": workflow.user_id}, {})

            return TaskExecutionResult(
                success=True,
                message="Workflow executed via scheduler",
            )
        except Exception as e:
            logger.error(f"Error executing workflow {task.id}: {e}")
            return TaskExecutionResult(
                success=False, message=f"Workflow execution failed: {str(e)}"
            )

    async def update_task_status(
        self,
        task_id: str,
        status: ScheduledTaskStatus,
        update_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Update workflow status and other fields.

        Args:
            task_id: Workflow ID
            status: New status
            update_data: Additional fields to update
            user_id: User ID for authorization (optional)

        Returns:
            True if update was successful
        """
        try:
            update_fields = {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc),
            }

            if update_data:
                update_fields.update(update_data)

            # Build query with optional user_id filter
            query = {"_id": task_id}
            if user_id:
                query["user_id"] = user_id

            result = await workflows_collection.update_one(
                query, {"$set": update_fields}
            )

            if result.modified_count > 0:
                logger.info(f"Updated workflow {task_id} status to {status.value}")
                return True
            else:
                logger.warning(f"No workflow updated for {task_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating workflow {task_id}: {e}")
            return False

    async def get_pending_task(self, current_time: datetime) -> List[BaseScheduledTask]:
        """
        Get workflows that should be scheduled for execution.

        Args:
            current_time: Current time to check against

        Returns:
            List of workflows ready for execution (as BaseScheduledTask)
        """
        try:
            # Find workflows that are:
            # 1. In SCHEDULED status
            # 2. Have scheduled_at <= current_time
            # 3. Are activated
            query = {
                "status": ScheduledTaskStatus.SCHEDULED.value,
                "scheduled_at": {"$lte": current_time},
                "activated": True,
            }

            cursor = workflows_collection.find(query)
            workflows: List[BaseScheduledTask] = []

            async for workflow_doc in cursor:
                try:
                    # Transform MongoDB document to Workflow object
                    workflow_doc["id"] = workflow_doc.get("_id")
                    if "_id" in workflow_doc:
                        del workflow_doc["_id"]

                    workflow = Workflow(**workflow_doc)
                    workflows.append(workflow)  # Workflow extends BaseScheduledTask
                except Exception as e:
                    logger.error(f"Error creating workflow object: {e}")
                    continue

            logger.info(f"Found {len(workflows)} pending workflows")
            return workflows

        except Exception as e:
            logger.error(f"Error fetching pending workflows: {e}")
            return []

    async def create_workflow_with_scheduling(
        self, workflow_data: Dict[str, Any], user_id: str
    ) -> Optional[str]:
        """
        Create a workflow and handle its initial scheduling.

        Args:
            workflow_data: Workflow data dictionary
            user_id: User ID

        Returns:
            Workflow ID if successful, None otherwise
        """
        try:
            # Create the workflow
            workflow = Workflow(user_id=user_id, **workflow_data)

            # Insert into database
            workflow_dict = workflow.model_dump()
            workflow_dict["_id"] = workflow_dict["id"]

            result = await workflows_collection.insert_one(workflow_dict)
            if not result.inserted_id:
                raise ValueError("Failed to create workflow in database")

            # Schedule if it's a scheduled workflow
            if workflow.trigger_config.type == "schedule" and workflow.repeat:
                from app.models.scheduler_models import ScheduleConfig

                # Ensure workflow.id is not None
                if not workflow.id:
                    raise ValueError("Workflow ID is required for scheduling")

                schedule_config = ScheduleConfig(
                    repeat=workflow.repeat,
                    scheduled_at=workflow.scheduled_at,
                    max_occurrences=workflow.max_occurrences,
                    stop_after=workflow.stop_after,
                    base_time=datetime.now(timezone.utc),  # Add required base_time
                )

                await self.schedule_task(workflow.id, schedule_config)
                logger.info(f"Scheduled workflow {workflow.id} for recurring execution")

            return workflow.id

        except Exception as e:
            logger.error(f"Error creating and scheduling workflow: {e}")
            return None
