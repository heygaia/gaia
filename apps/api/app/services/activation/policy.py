"""Whether today's activation message is sent, and what it is about.

Pure decisions over facts the task gathers first, so every rule here is a unit
test away from proof and none of them needs a database. The task evaluates
:func:`skip_reason` BEFORE any model call: a skipped day costs a few reads.
"""

from dataclasses import dataclass
from enum import StrEnum

#: Messages in the sequence after which it is complete.
SEQUENCE_LENGTH = 5
#: An account older than this is past activation; the sequence ends.
MAX_ACCOUNT_AGE_DAYS = 14
#: Redis key holding the once-per-day send claim (SET NX), by user and day index.
CLAIM_KEY_PREFIX = "activation:sent:"


class SkipReason(StrEnum):
    OPTED_OUT = "opted_out"
    SEQUENCE_COMPLETE = "sequence_complete"
    ACCOUNT_TOO_OLD = "account_too_old"
    NOT_SUBSCRIBED = "not_subscribed"
    NO_CHANNEL = "no_channel"
    USER_ACTIVE_TODAY = "user_active_today"


class Direction(StrEnum):
    """What today's message points at, chosen from what actually happened."""

    CONNECT = "connect"  # nothing connected yet: the one connection that unlocks most
    HANDOVER = "handover"  # connected, nothing handed over: one starting job for today
    FOLLOW_THROUGH = "follow_through"  # a handover happened: its next step
    CONTINUE_THREAD = "continue_thread"  # they replied yesterday: pick that up


@dataclass(frozen=True, slots=True)
class Facts:
    """Everything the policy needs, gathered by the task before deciding."""

    opted_out: bool
    days_sent: int
    account_age_days: int
    subscription_active: bool
    has_channel: bool
    user_messaged_last_24h: bool
    replied_to_sequence_last_24h: bool
    connected_integrations: int
    handovers: int


def skip_reason(facts: Facts) -> SkipReason | None:
    """The first rule that stops today's send, or ``None`` to send.

    Terminal reasons come before the daily one on purpose: a user who is active
    today AND done with the sequence is done, not merely "active today".
    """
    if facts.opted_out:
        return SkipReason.OPTED_OUT
    if facts.days_sent >= SEQUENCE_LENGTH:
        return SkipReason.SEQUENCE_COMPLETE
    if facts.account_age_days > MAX_ACCOUNT_AGE_DAYS:
        return SkipReason.ACCOUNT_TOO_OLD
    if not facts.subscription_active:
        return SkipReason.NOT_SUBSCRIBED
    if not facts.has_channel:
        return SkipReason.NO_CHANNEL
    if facts.user_messaged_last_24h and not facts.replied_to_sequence_last_24h:
        return SkipReason.USER_ACTIVE_TODAY
    return None


def direction(facts: Facts) -> Direction:
    """Today's direction. A reply to yesterday's message always wins: continuing a
    conversation the user started beats any fresh suggestion."""
    if facts.replied_to_sequence_last_24h:
        return Direction.CONTINUE_THREAD
    if facts.handovers > 0:
        return Direction.FOLLOW_THROUGH
    if facts.connected_integrations > 0:
        return Direction.HANDOVER
    return Direction.CONNECT


def claim_key(user_id: str, day: int) -> str:
    return f"{CLAIM_KEY_PREFIX}{user_id}:{day}"
