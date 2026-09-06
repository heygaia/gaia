"""When the next activation message goes out: the next local wall-clock hour,
returned as a UTC instant for ARQ's ``_defer_until``.

Evaluated in the user's home timezone so "8am" is their 8am across DST changes;
an unparseable or missing timezone falls back to UTC the way every other
user-local schedule in this codebase does.
"""

from datetime import UTC, datetime, timedelta

from app.utils.timezone import Timezone

#: Local hour the daily activation message is sent at.
SEND_HOUR_LOCAL = 8


def next_send_at(timezone_raw: str | None, now: datetime, hour: int = SEND_HOUR_LOCAL) -> datetime:
    """The next ``hour``:00 in the user's timezone strictly after ``now``, in UTC.

    ``now`` must be timezone-aware. A wall-clock hour that does not exist on a
    DST-forward day resolves the way ``zoneinfo`` resolves it (the instant after
    the gap), which is what a person expects from "8am tomorrow".
    """
    if now.tzinfo is None:
        raise ValueError("next_send_at needs an aware datetime")
    tz = Timezone.parse(timezone_raw).tzinfo
    local_now = now.astimezone(tz)
    candidate = local_now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if candidate <= local_now:
        # Advance one calendar day in local time, then re-pin the wall clock so a
        # DST change between the two days cannot shift the hour.
        candidate = (candidate + timedelta(days=1)).replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
    return candidate.astimezone(UTC)
