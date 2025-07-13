"""
Service for creating and managing email summary reminders.
"""

from datetime import datetime, timedelta
from typing import Optional

from pytz import timezone as pytz_timezone

from app.config.loggers import general_logger as logger
from app.models.reminder_models import (
    AgentType,
    CreateReminderRequest,
    EmailSummaryReminderPayload,
)
from app.services.reminder_service import create_reminder


async def create_email_summary_reminder(
    user_id: str, user_timezone: str = "UTC"
) -> Optional[str]:
    """
    Create a daily email summary reminder for a user.

    Args:
        user_id: The user's ID
        user_timezone: The user's timezone (default: UTC)

    Returns:
        The ID of the created reminder, or None if creation failed
    """
    try:
        # Get timezone-aware datetime
        user_tz = pytz_timezone(user_timezone)
        now = datetime.now(user_tz)

        # Set to run at 9:00 AM in user's timezone
        scheduled_time = now.replace(hour=9, minute=0, second=0, microsecond=0)

        # If it's already past 9 AM, schedule for tomorrow
        if now.hour >= 9:
            scheduled_time = scheduled_time + timedelta(days=1)

        # Create payload
        payload = EmailSummaryReminderPayload(
            important_only=True,
        )

        # Define cron expression for daily execution at 9:00 AM
        cron_expr = "0 9 * * *"  # Daily at 9:00 AM

        # Create reminder request
        reminder_request = CreateReminderRequest(
            agent=AgentType.EMAIL_SUMMARY,
            scheduled_at=scheduled_time,
            repeat=cron_expr,
            payload=payload,
            stop_after=None,
            max_occurrences=None,
            conversation_id=None,
            base_time=scheduled_time,
        )

        # Create the reminder
        reminder_id = await create_reminder(
            reminder_data=reminder_request, user_id=user_id
        )

        logger.info(f"Created email summary reminder {reminder_id} for user {user_id}")
        return reminder_id

    except Exception as e:
        logger.error(
            f"Failed to create email summary reminder for user {user_id}: {str(e)}"
        )
        raise e
