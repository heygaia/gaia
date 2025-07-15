from datetime import datetime, timezone
from typing import List, Optional

from app.db.mongodb.collections import workflow_collection
from app.models.arq_event_models import EventStatus, EventType
from app.models.workflow_models import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    WorkflowModel,
)
from app.utils.arq_event import scheduler
from bson import ObjectId


async def create_workflow(workflow_data: CreateWorkflowRequest, user_id: str) -> str:
    """Create a workflow, store it, and schedule it."""
    workflow = WorkflowModel(**workflow_data.model_dump(), user_id=user_id)

    workflow_dict = workflow.model_dump(by_alias=True)

    result = await workflow_collection.insert_one(workflow_dict)
    workflow_id = str(result.inserted_id)

    await scheduler.schedule_event(
        workflow_id, workflow.scheduled_at, type=EventType.WORKFLOW
    )
    return workflow_id


async def get_workflow(
    workflow_id: str, user_id: Optional[str]
) -> Optional[WorkflowModel]:
    """Retrieve a workflow from the database."""
    filters = {"_id": ObjectId(workflow_id)}
    if user_id:
        filters["user_id"] = user_id  # type: ignore

    doc = await workflow_collection.find_one(filters)
    if doc:
        doc["_id"] = str(doc["_id"])
        return WorkflowModel(**doc)
    return None


async def list_user_workflows(
    user_id: str,
    status: Optional[EventStatus] = None,
    limit: int = 100,
    skip: int = 0,
) -> List[WorkflowModel]:
    """List all workflows for a user."""
    query = {"user_id": user_id}
    if status:
        query["status"] = status

    cursor = workflow_collection.find(query).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    return [WorkflowModel(**{**doc, "_id": str(doc["_id"])}) for doc in docs]


async def update_workflow(
    workflow_id: str, update_data: dict, user_id: str, reschedule: bool = False
) -> WorkflowModel:
    """Update workflow in DB and reschedule if applicable."""
    update_data_model = UpdateWorkflowRequest(**update_data)
    update_data = update_data_model.model_dump(by_alias=True)

    filters = {"_id": ObjectId(workflow_id), "user_id": user_id}
    result = await workflow_collection.update_one(filters, {"$set": update_data})

    workflow = await get_workflow(workflow_id, user_id)
    if not workflow:
        raise ValueError(f"Workflow with ID {workflow_id} not found for user {user_id}")

    if result.modified_count == 0:
        # No changes made, return existing workflow
        return workflow

    if reschedule:
        await scheduler.update_event_schedule(
            workflow_id, update_data_model, workflow, EventType.WORKFLOW
        )

    return workflow


async def cancel_workflow(workflow_id: str, user_id: str) -> bool:
    """Cancel a workflow by setting its status."""
    filters = {"_id": ObjectId(workflow_id), "user_id": user_id}
    result = await workflow_collection.update_one(
        filters,
        {
            "$set": {
                "status": EventStatus.CANCELLED,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return result.modified_count > 0


async def process_workflow_task(workflow_id: str):
    """Execute and possibly reschedule a workflow task."""
    workflow = await get_workflow(workflow_id, user_id=None)
    if not workflow:
        return

    result = await scheduler.process_event(workflow)
    await update_workflow(
        workflow_id,
        {
            "status": result.status,
            "current_execution_count": result.current_execution_count,
            "scheduled_at": result.scheduled_at if result.scheduled_at else None,
        },
        workflow.user_id,
    )

    if result.reschedule and result.scheduled_at:
        await scheduler.schedule_event(
            workflow_id, result.scheduled_at, type=EventType.WORKFLOW
        )
