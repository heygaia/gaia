"""Did anyone answer?

The only number that says whether the sequence works. Sends are easy to count
and prove nothing; a reply within a day of a message is the user saying the
message was worth something.
"""

from datetime import UTC, datetime, timedelta

from app.db.repositories.users import user_repository
from app.models.activation_models import ActivationSequenceState
from app.services.analytics_service import AnalyticsEvents, capture_event

#: A reply after this long is a new conversation, not an answer to yesterday.
REPLY_WINDOW_HOURS = 24


async def record_reply(user_id: str) -> None:
    """Count this inbound bot message as a reply, when it answers a recent day.

    Joined to the day it answers so the funnel reads per day rather than as one
    undifferentiated "someone replied at some point".
    """
    user = await user_repository.get(user_id)
    if user is None:
        return
    state = ActivationSequenceState.of(user.activation_sequence)
    if state.last_sent_at is None or not state.messages:
        return
    age = datetime.now(UTC) - state.last_sent_at.astimezone(UTC)
    if age > timedelta(hours=REPLY_WINDOW_HOURS):
        return
    last = state.messages[-1]
    capture_event(
        user_id,
        AnalyticsEvents.ACTIVATION_REPLIED,
        {"day": last.day, "platform": last.platform, "direction": last.direction},
    )
