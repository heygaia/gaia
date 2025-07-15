"""
Central event scheduler using ARQ.
Does NOT perform any database operations.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from arq import create_pool
from arq.connections import RedisSettings
from arq.jobs import Job

from app.config.loggers import general_logger as logger
from app.config.settings import settings
from app.models.arq_event_models import (
    EventModel,
    EventProcessResponseModel,
    EventStatus,
    EventType,
    UpdateEventRequestModel,
)
from app.utils.cron_utils import get_next_run_time


class EventScheduler:
    """
    Central scheduler responsible for timed execution of events.
    Upper layer is responsible for persistence and event resolution.
    """

    def __init__(self, redis_settings: Optional[RedisSettings] = None):
        self.redis_settings = redis_settings or RedisSettings.from_dsn(
            settings.REDIS_URL
        )
        self.arq_pool = None

    async def initialize(self):
        self.arq_pool = await create_pool(self.redis_settings)
        logger.info("Central Scheduler initialized")

    async def close(self):
        if self.arq_pool:
            await self.arq_pool.close()
        logger.info("Central Scheduler closed")

    async def schedule_event(
        self, event_id: str, scheduled_at: datetime, type: EventType
    ):
        """
        Schedule a new event to run via ARQ.

        Args:
            event_id (str): Unique ID of the event
            scheduled_at (datetime): When to execute the event
        """
        if not self.arq_pool:
            logger.error("ARQ pool not initialized")
            return

        job = await self.arq_pool.enqueue_job(
            "process_event", f"{type}:{event_id}", _defer_until=scheduled_at
        )

        if not job:
            logger.error(f"Failed to enqueue event {event_id}")
        else:
            logger.debug(
                f"Enqueued event {event_id} at {scheduled_at} (Job ID: {job.job_id})"
            )

    async def process_event(self, event: EventModel) -> EventProcessResponseModel:
        """
        Process a scheduled event. Determines whether to reschedule or mark complete.

        Args:
            event (Event): Event object (from external source)

        Returns:
            dict: {
                "status": EventStatus,
                "reschedule": bool,
                "occurrence_count": int,
                "scheduled_at": datetime (optional)
            }
        """
        logger.info(f"Processing event {event.id}")

        if event.status != EventStatus.SCHEDULED:
            logger.warning(
                f"Event {event.id} is not scheduled (status: {event.status})"
            )
            raise ValueError(
                f"Cannot process event {event.id} with status {event.status}"
            )

        try:
            from app.tasks.event_tasks import execute_event

            await execute_event(event)

            occurrence_count = event.current_execution_count + 1

            if event.repeat:
                next_run = get_next_run_time(event.repeat, event.scheduled_at)
                should_continue = True

                if event.max_occurrences and occurrence_count >= event.max_occurrences:
                    should_continue = False
                    logger.info(f"Event {event.id} reached max occurrences")

                if event.stop_after and next_run >= event.stop_after:
                    should_continue = False
                    logger.info(f"Event {event.id} reached stop_after")

                if should_continue:
                    return EventProcessResponseModel(
                        scheduled_at=next_run,
                        status=EventStatus.SCHEDULED,
                        current_execution_count=occurrence_count,
                        reschedule=True,
                    )

                return EventProcessResponseModel(
                    reschedule=False,
                    current_execution_count=occurrence_count,
                    status=EventStatus.COMPLETED,
                )

            # One-time event
            return EventProcessResponseModel(
                reschedule=False,
                current_execution_count=occurrence_count,
                status=EventStatus.COMPLETED,
            )

        except Exception as e:
            logger.error(f"Error processing event {event.id}: {str(e)}")
            return EventProcessResponseModel(
                reschedule=False,
                status=EventStatus.FAILED,
                current_execution_count=event.current_execution_count,
            )

    async def update_event_schedule(
        self,
        event_id: str,
        update_data: UpdateEventRequestModel,
        event: EventModel,
        type: EventType,
    ):
        """
        Reschedule an existing event with new attributes.

        Args:
            event_id (str): Unique ID of the event
            update_data (dict): Attributes to update
        """
        if not self.arq_pool:
            logger.error("ARQ pool not initialized")
            return

        job_key = f"{type}:{event_id}"
        job = Job(job_key, self.arq_pool)

        # Handle cancellation
        if update_data.status == EventStatus.CANCELLED:
            if job:
                await job.abort()
                logger.info(f"Cancelled event {event_id}")
            else:
                logger.warning(f"Event {event_id} not found in queue")
            return

        # Handle terminal states
        if update_data.status in {
            EventStatus.COMPLETED,
            EventStatus.FAILED,
            EventStatus.PAUSED,
        }:
            if job:
                await job.abort()
                logger.info(f"Cancelled event {event_id} as it is no longer needed")
            else:
                logger.warning(f"Event {event_id} not found in queue")
            return

        elif (
            update_data.status == EventStatus.SCHEDULED
            or update_data.repeat != event.repeat
        ):
            repeat = update_data.repeat or event.repeat
            if not repeat:
                raise ValueError("Repeat schedule must be specified for rescheduling")

            if event.status == EventStatus.SCHEDULED and event.repeat == repeat:
                logger.info(f"Event {event_id} already scheduled with same repeat")
                return

            next_run = get_next_run_time(repeat, event.base_time)

            await self.schedule_event(event_id, next_run, type)
            logger.info(f"Rescheduled event {event_id} to {next_run}")

        # Determine if rescheduling is required
        reschedule = False
        new_repeat = update_data.repeat or event.repeat
        new_status = update_data.status or event.status

        if new_repeat != event.repeat:
            reschedule = True
        if new_status != event.status and new_status == EventStatus.SCHEDULED:
            reschedule = True

        if not reschedule:
            logger.info(f"Event {event_id} does not require rescheduling")
            return

        if not new_repeat:
            raise ValueError("Repeat schedule must be specified for rescheduling")

        next_run = get_next_run_time(new_repeat, event.base_time)

        await self.schedule_event(event_id, next_run, type)
        logger.info(f"Rescheduled event {event_id} to {next_run}")

    async def cancel_event(self, event_id: str):
        """
        Cancel a scheduled event by removing it from the queue.

        Args:
            event_id (str): Unique ID of the event
        """
        if not self.arq_pool:
            logger.error("ARQ pool not initialized")
            return

        job = Job(event_id, self.arq_pool)
        if job:
            await job.abort()
            logger.info(f"Cancelled event {event_id}")
        else:
            logger.warning(f"Event {event_id} not found in queue")

    async def scan_and_schedule_pending_events(self):
        from app.db.mongodb.collections import reminders_collection, workflow_collection

        now = datetime.now(timezone.utc)

        # Find all scheduled reminders that should run in the future
        cursor_reminder = reminders_collection.find(
            {"status": EventStatus.SCHEDULED, "scheduled_at": {"$gte": now}}
        )
        cursor_workflow = workflow_collection.find(
            {"status": EventStatus.SCHEDULED, "scheduled_at": {"$gte": now}}
        )

        tasks = []
        async for doc in cursor_reminder:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            tasks.append(
                self.schedule_event(
                    event_id=doc["_id"],
                    scheduled_at=doc["scheduled_at"],
                    type=EventType.REMINDER,
                )
            )
        async for doc in cursor_workflow:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            tasks.append(
                self.schedule_event(
                    event_id=doc["_id"],
                    scheduled_at=doc["scheduled_at"],
                    type=EventType.WORKFLOW,
                )
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = 0
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Reminder scheduling failed: {repr(result)}")
            else:
                success_count += 1

        logger.info(f"Scheduled {success_count} pending workflows or reminders")


scheduler = EventScheduler()
