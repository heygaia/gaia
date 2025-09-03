"""
Cron utilities for reminder scheduling.
"""

from datetime import datetime, timezone
from typing import Optional

from croniter import croniter


class CronError(Exception):
    """Exception raised for cron-related errors."""

    pass


def validate_cron_expression(cron_expr: str) -> bool:
    """
    Validate a cron expression.

    Args:
        cron_expr: Cron expression to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        croniter(cron_expr)
        return True
    except (ValueError, TypeError):
        return False


def get_next_run_time(
    cron_expr: str,
    base_time: Optional[datetime] = None,
    user_timezone: Optional[str] = None,
) -> datetime:
    """
    Get the next scheduled run time based on cron expression.

    Args:
        cron_expr: Cron expression (e.g., "0 8 * * *" for daily at 8AM)
        base_time: Base time to calculate from (defaults to current UTC time)
        user_timezone: User's timezone for cron calculation (e.g., "America/New_York")

    Returns:
        Next scheduled datetime in UTC

    Raises:
        CronError: If cron expression is invalid
    """
    if not validate_cron_expression(cron_expr):
        raise CronError(f"Invalid cron expression: {cron_expr}")

    # Handle timezone-aware calculation
    if user_timezone and user_timezone != "UTC":
        try:
            import pytz

            tz = pytz.timezone(user_timezone)

            # Get base time in user's timezone
            if base_time is None:
                base_time = datetime.now(tz)
            elif base_time.tzinfo is None:
                base_time = base_time.replace(tzinfo=timezone.utc).astimezone(tz)
            else:
                base_time = base_time.astimezone(tz)

            # Calculate next run in user's timezone
            cron = croniter(cron_expr, base_time)
            next_time = cron.get_next(datetime)

            # Convert to UTC for storage
            return next_time.astimezone(timezone.utc)

        except Exception:
            # Fallback to UTC if timezone conversion fails
            pass

    # Default UTC calculation
    if base_time is None:
        base_time = datetime.now(timezone.utc)
    elif base_time.tzinfo is None:
        # Assume UTC if no timezone info
        base_time = base_time.replace(tzinfo=timezone.utc)

    try:
        cron = croniter(cron_expr, base_time)
        next_time = cron.get_next(datetime)

        # Ensure we return UTC timezone-aware datetime
        if next_time.tzinfo is None:  # type: ignore
            next_time = next_time.replace(tzinfo=timezone.utc)  # type: ignore

        return next_time  # type: ignore
    except Exception as e:
        raise CronError(f"Failed to calculate next run time: {str(e)}")


def get_previous_run_time(
    cron_expr: str, base_time: Optional[datetime] = None
) -> datetime:
    """
    Get the previous scheduled run time based on cron expression.

    Args:
        cron_expr: Cron expression
        base_time: Base time to calculate from (defaults to current UTC time)

    Returns:
        Previous scheduled datetime in UTC

    Raises:
        CronError: If cron expression is invalid
    """
    if not validate_cron_expression(cron_expr):
        raise CronError(f"Invalid cron expression: {cron_expr}")

    if base_time is None:
        base_time = datetime.now(timezone.utc)
    elif base_time.tzinfo is None:
        base_time = base_time.replace(tzinfo=timezone.utc)

    try:
        cron = croniter(cron_expr, base_time)
        prev_time = cron.get_prev(datetime)

        if prev_time.tzinfo is None:
            prev_time = prev_time.replace(tzinfo=timezone.utc)

        return prev_time
    except Exception as e:
        raise CronError(f"Failed to calculate previous run time: {str(e)}")


def calculate_next_occurrences(
    cron_expr: str, count: int, base_time: Optional[datetime] = None
) -> list[datetime]:
    """
    Calculate the next N occurrences of a cron expression.

    Args:
        cron_expr: Cron expression
        count: Number of occurrences to calculate
        base_time: Base time to calculate from (defaults to current UTC time)

    Returns:
        List of next scheduled datetimes in UTC

    Raises:
        CronError: If cron expression is invalid
    """
    if not validate_cron_expression(cron_expr):
        raise CronError(f"Invalid cron expression: {cron_expr}")

    if count <= 0:
        return []

    if base_time is None:
        base_time = datetime.now(timezone.utc)
    elif base_time.tzinfo is None:
        base_time = base_time.replace(tzinfo=timezone.utc)

    try:
        cron = croniter(cron_expr, base_time)
        occurrences = []

        for _ in range(count):
            next_time = cron.get_next(datetime)
            if next_time.tzinfo is None:  # type: ignore
                next_time = next_time.replace(tzinfo=timezone.utc)  # type: ignore
            occurrences.append(next_time)

        return occurrences
    except Exception as e:
        raise CronError(f"Failed to calculate next occurrences: {str(e)}")


def is_time_in_future(
    target_time: datetime, reference_time: Optional[datetime] = None
) -> bool:
    """
    Check if a target time is in the future relative to a reference time.

    Args:
        target_time: Time to check
        reference_time: Reference time (defaults to current UTC time)

    Returns:
        True if target_time is in the future
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)

    # Ensure both times are timezone-aware
    if target_time.tzinfo is None:
        target_time = target_time.replace(tzinfo=timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    return target_time > reference_time


# Common cron expressions for easy reference
COMMON_CRON_EXPRESSIONS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "hourly": "0 * * * *",
    "daily_8am": "0 8 * * *",
    "daily_noon": "0 12 * * *",
    "daily_6pm": "0 18 * * *",
    "weekly_monday_9am": "0 9 * * 1",
    "monthly_first_day": "0 9 1 * *",
    "yearly_jan_1st": "0 9 1 1 *",
}
