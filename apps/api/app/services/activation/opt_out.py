"""Making it stop, from either surface.

Two ways in — replying "stop" on the bot and a settings toggle — and one place
that does the work, so the bot path can never drift into a different meaning of
opted out than the API path.
"""

from app.db.repositories.users import user_repository
from app.models.activation_models import ActivationSequenceState
from app.services.analytics_service import AnalyticsEvents, capture_event

#: What the user replies to end the sequence. Whole message only: "stop" inside
#: a sentence ("stop booking that for me") is a request, not an unsubscribe, and
#: silently muting GAIA there would be the worst possible reading.
STOP_WORD = "stop"
#: The one line back. Any more is arguing with someone who asked you to stop.
STOP_ACKNOWLEDGEMENT = "Got it, no more daily messages. I'm still here if you need me."


def is_stop_message(text: str) -> bool:
    """Whether ``text`` is the opt-out word and nothing else."""
    return text.strip().strip(".!").casefold() == STOP_WORD


async def set_opted_out(user_id: str, opted_out: bool, *, source: str) -> None:
    """Record the user's choice and report where it came from."""
    await user_repository.set_activation_opted_out(user_id, opted_out)
    capture_event(
        user_id, AnalyticsEvents.ACTIVATION_OPTED_OUT, {"opted_out": opted_out, "source": source}
    )


async def get_opted_out(user_id: str) -> bool:
    """Whether the daily sequence is currently off for this user."""
    user = await user_repository.get(user_id)
    return ActivationSequenceState.of(user.activation_sequence if user else None).opted_out
