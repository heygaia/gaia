"""Everything a run reads before it decides or writes anything.

Split from the task so the gathering is one pass with one shape: the policy gets
:class:`~app.services.activation.policy.Facts` and the prompt gets the same data
formatted for a model. Nothing here writes, and nothing here calls a model.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.agents.context.fetchers import build_connected_integrations_manifest
from app.agents.prompts.new_user_prompts import NEED_PLAYBOOKS
from app.db.repositories.conversations import conversation_repository
from app.decorators.entitlements import is_subscription_active
from app.models.activation_models import ActivationSequenceState
from app.models.conversation_models import ConversationMessageHit
from app.models.user_models import OnboardingNeed, OnboardingPreferences, UserDocument
from app.services.activation.policy import Facts
from app.services.delivery.chat_channel import resolve_chat_channel
from app.services.integrations.user_integrations import get_connected_integrations_named

#: The window "what actually happened" and "did they already talk to us" share.
LOOKBACK_HOURS = 24
#: Messages carried into the prompt. A heavy day is not more signal than a light
#: one, and past this the onboarding answers stop competing for attention.
MAX_YESTERDAY_MESSAGES = 20
#: Characters kept per message: enough to know what it was about, not a transcript.
MAX_MESSAGE_CHARS = 200
#: Message role marking a turn the user typed (vs. a turn GAIA sent).
USER_MESSAGE_TYPE = "user"


@dataclass(frozen=True, slots=True)
class RunContext:
    """The gathered world for one day of one user's sequence."""

    facts: Facts
    state: ActivationSequenceState
    platform: str | None
    who_block: str
    integrations_block: str
    yesterday_block: str
    already_sent_block: str


def _preferences(user: UserDocument) -> OnboardingPreferences:
    raw = (user.onboarding or {}).get("preferences") or {}
    return OnboardingPreferences.model_validate(raw)


def format_who_block(preferences: OnboardingPreferences) -> str:
    """Their role and the jobs they picked, with each pick's playbook.

    The playbook is what turns a pick into something to offer: "inbox" alone is
    a tag, while its playbook says what GAIA would actually do about it.
    """
    lines = [f"Role: {preferences.profession or 'unknown'}"]
    needs: list[OnboardingNeed] = preferences.needs or []
    if needs:
        lines.append("They picked these, with what you can offer for each:")
        lines.extend(f"- {NEED_PLAYBOOKS[need]}" for need in needs if need in NEED_PLAYBOOKS)
    if preferences.other_need:
        lines.append(f'In their own words, they also said: "{preferences.other_need}"')
    if not needs and not preferences.other_need:
        lines.append("They picked nothing in onboarding, so you know only the role.")
    return "\n".join(lines)


def format_yesterday_block(hits: list[ConversationMessageHit]) -> str:
    """The last day's turns, oldest first, marked by who said them."""
    if not hits:
        return f"Nothing in the last {LOOKBACK_HOURS} hours. They have not written to you."
    lines = []
    for hit in hits:
        text = " ".join((hit.message.response or "").split())
        if not text:
            continue
        if len(text) > MAX_MESSAGE_CHARS:
            text = text[:MAX_MESSAGE_CHARS] + "..."
        speaker = "them" if hit.message.type == USER_MESSAGE_TYPE else "you"
        lines.append(f"- [{speaker}] {text}")
    return "\n".join(lines) if lines else f"Nothing in the last {LOOKBACK_HOURS} hours."


def format_already_sent_block(state: ActivationSequenceState) -> str:
    """Every earlier day, verbatim. The model must not reuse any of it."""
    if not state.messages:
        return "Nothing yet. This is the first message."
    return "\n\n".join(
        f"Day {message.day} ({message.direction}):\n"
        + "\n".join(message.bubbles)
        + f"\n(suggestion: {message.suggestion})"
        for message in state.messages
    )


async def gather(user: UserDocument, now: datetime) -> RunContext:
    """Read everything today's decision needs, without deciding anything."""
    user_id = user.id
    since = now - timedelta(hours=LOOKBACK_HOURS)
    state = ActivationSequenceState.of(user.activation_sequence)
    preferences = _preferences(user)

    platform = await resolve_chat_channel(user_id, user.chat_channel_priority)
    hits = await conversation_repository.list_messages_since(
        user_id, since, limit=MAX_YESTERDAY_MESSAGES
    )
    user_hits = [hit for hit in hits if hit.message.type == USER_MESSAGE_TYPE]
    integrations = await get_connected_integrations_named(user_id)
    subscription_active = await is_subscription_active(user_id)

    created_at = user.created_at or now
    # A handover is a turn the user typed at GAIA since signing up. That is the
    # honest signal available here: conversations record turns, not "GAIA did a
    # job for them", and a turn they typed is the moment they handed something
    # over. It over-counts a one-word reply and under-counts nothing.
    ever_handed_over = await conversation_repository.has_activity_since(user_id, created_at)
    facts = Facts(
        opted_out=state.opted_out,
        days_sent=state.day_sent,
        account_age_days=(now - created_at).days,
        subscription_active=subscription_active,
        has_channel=platform is not None,
        user_messaged_last_24h=bool(user_hits),
        replied_to_sequence_last_24h=_replied_to_sequence(state, user_hits, since),
        connected_integrations=len(integrations),
        handovers=int(ever_handed_over),
    )
    return RunContext(
        facts=facts,
        state=state,
        platform=platform,
        who_block=format_who_block(preferences),
        integrations_block=await build_connected_integrations_manifest(
            user_id, header="Connected:"
        ),
        yesterday_block=format_yesterday_block(hits),
        already_sent_block=format_already_sent_block(state),
    )


def _replied_to_sequence(
    state: ActivationSequenceState, user_hits: list[ConversationMessageHit], since: datetime
) -> bool:
    """Whether the user wrote AFTER the last sequence message, inside the window.

    A message they sent before yesterday's nudge landed is not a reply to it;
    treating it as one is how day 2 answers a question nobody asked.
    """
    if not user_hits or state.last_sent_at is None:
        return False
    boundary = max(state.last_sent_at, since)
    return any((hit.message.date or "") > boundary.astimezone(UTC).isoformat() for hit in user_hits)
