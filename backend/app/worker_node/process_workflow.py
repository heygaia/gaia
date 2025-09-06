"""
Background task processor for workflow generation.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId

from app.config.loggers import worker_logger as logger
from app.db.mongodb.collections import todos_collection
from app.services.todo_service import TodoService


async def process_workflow_generation(task_data: Dict[str, Any]) -> None:
    """
    Process workflow generation task in the background.

    Args:
        task_data: Dictionary containing todo_id, user_id, title, and description
    """
    try:
        todo_id = task_data.get("todo_id")
        user_id = task_data.get("user_id")
        title = task_data.get("title")
        description = task_data.get("description")

        if not all([todo_id, user_id, title]):
            logger.error(f"Missing required fields in workflow task data: {task_data}")
            return

        logger.info(f"Starting workflow generation for todo {todo_id}: {title}")

        # Create standalone workflow using the new workflow system
        from app.models.workflow_models import (
            CreateWorkflowRequest,
            TriggerConfig,
            TriggerType,
        )
        from app.services.workflow.service import WorkflowService

        workflow_request = CreateWorkflowRequest(
            title=f"Todo: {title}",
            description=description or f"Workflow for todo: {title}",
            trigger_config=TriggerConfig(type=TriggerType.MANUAL, enabled=True),
            generate_immediately=True,  # Generate steps immediately
        )

        workflow = await WorkflowService.create_workflow(workflow_request, str(user_id))

        if workflow and workflow.id:
            # Update the todo with the workflow_id for linking
            update_data = {
                "workflow_id": workflow.id,
                "updated_at": datetime.now(timezone.utc),
            }

            result = await todos_collection.update_one(
                {"_id": ObjectId(todo_id), "user_id": user_id}, {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(
                    f"Successfully generated and linked standalone workflow {workflow.id} for todo {todo_id} with {len(workflow.steps)} steps"
                )

                if not user_id:
                    logger.warning(
                        f"User ID is missing for todo {todo_id}. Cannot invalidate cache."
                    )
                    return

                # Invalidate cache for this todo
                await TodoService._invalidate_cache(user_id, None, todo_id, "update")
            else:
                logger.warning(f"Todo {todo_id} not found or not updated with workflow")

        else:
            logger.error(
                f"Failed to generate workflow for todo {todo_id}: No workflow created"
            )

    except Exception as e:
        # Mark workflow generation as failed on exception
        try:
            todo_id = task_data.get("todo_id")
            user_id = task_data.get("user_id")
            if todo_id and user_id:
                # Just log the failure, don't update legacy fields
                logger.error(f"Failed to generate workflow for todo {todo_id}")
        except Exception as update_error:
            logger.error(
                f"Failed to update workflow status to failed: {str(update_error)}"
            )

        logger.error(
            f"Error processing workflow generation task: {str(e)}", exc_info=True
        )
