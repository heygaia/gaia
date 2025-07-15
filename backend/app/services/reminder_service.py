from datetime import datetime, timezone
from typing import List, Optional

from app.db.mongodb.collections import reminders_collection
from app.models.arq_event_models import EventStatus, EventType
from app.models.reminder_models import (
    CreateReminderRequest,
    ReminderModel,
    UpdateReminderRequest,
)
from app.utils.arq_event import scheduler
from bson import ObjectId


async def create_reminder(reminder_data: CreateReminderRequest, user_id: str) -> str:
    """Create a reminder, store it, and schedule it."""
    reminder = ReminderModel(**reminder_data.model_dump(), user_id=user_id)
    reminder_dict = reminder.model_dump(by_alias=True)

    # Removing _id to let mongodb auto assign it in ObjectId format
    reminder_dict.pop("_id")

    result = await reminders_collection.insert_one(reminder_dict)
    reminder_id = str(result.inserted_id)

    await scheduler.schedule_event(
        reminder_id, reminder.scheduled_at, type=EventType.REMINDER
    )
    return reminder_id


async def get_reminder(
    reminder_id: str, user_id: Optional[str]
) -> Optional[ReminderModel]:
    """Retrieve a reminder from the database."""
    filters = {"_id": ObjectId(reminder_id)}
    if user_id:
        filters["user_id"] = user_id  # type: ignore

    doc = await reminders_collection.find_one(filters)
    if doc:
        doc["_id"] = str(doc["_id"])
        return ReminderModel(**doc)
    return None


async def list_user_reminders(
    user_id: str,
    status: Optional[EventStatus] = None,
    limit: int = 100,
    skip: int = 0,
) -> List[ReminderModel]:
    """List all reminders for a user."""
    query = {"user_id": user_id}
    if status:
        query["status"] = status

    cursor = reminders_collection.find(query).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    return [ReminderModel(**{**doc, "_id": str(doc["_id"])}) for doc in docs]


async def update_reminder(
    reminder_id: str, update_data: dict, user_id: str, reschedule: bool = False
) -> ReminderModel:
    """Update reminder in DB and reschedule if applicable."""
    update_data_model = UpdateReminderRequest(**update_data)
    update_data = update_data_model.model_dump(by_alias=True)

    filters = {"_id": ObjectId(reminder_id), "user_id": user_id}
    result = await reminders_collection.update_one(filters, {"$set": update_data})

    reminder = await get_reminder(reminder_id, user_id)
    if not reminder:
        raise ValueError(f"Reminder with ID {reminder_id} not found for user {user_id}")

    if result.modified_count == 0:
        # No changes made, return existing reminder
        return reminder

    if reschedule:
        await scheduler.update_event_schedule(
            reminder_id, update_data_model, reminder, EventType.REMINDER
        )

    return reminder


async def cancel_reminder(reminder_id: str, user_id: str) -> bool:
    """Cancel a reminder by setting its status."""
    filters = {"_id": ObjectId(reminder_id), "user_id": user_id}
    result = await reminders_collection.update_one(
        filters,
        {
            "$set": {
                "status": EventStatus.CANCELLED,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return result.modified_count > 0


async def process_reminder_task(reminder_id: str):
    """Execute and possibly reschedule a reminder task."""
    reminder = await get_reminder(reminder_id, user_id=None)
    if not reminder:
        return

    result = await scheduler.process_event(reminder)
    await update_reminder(
        reminder_id,
        {
            "status": result.status,
            "current_execution_count": result.current_execution_count,
            "scheduled_at": result.scheduled_at if result.scheduled_at else None,
        },
        reminder.user_id,
    )

    if result.reschedule and result.scheduled_at:
        await scheduler.schedule_event(
            reminder_id, result.scheduled_at, type=EventType.REMINDER
        )
