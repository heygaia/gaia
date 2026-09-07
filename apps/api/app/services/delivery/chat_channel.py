"""The ONE chat platform a proactive message goes to.

A message GAIA sends on its own initiative (an activation nudge, a briefing)
belongs on one platform, not on every platform the user ever linked: fanning it
out is the triple-delivery bug, and the user reads it once anyway. This module
owns that single choice — the first platform in the user's priority order that
is both linked and preference-enabled — and nothing else. It is deliberately
free of any feature coupling so the activation sequence and the briefing can
share it.
"""

from app.constants.notifications import DEFAULT_CHAT_CHANNEL_PRIORITY
from app.db.repositories.users import user_repository
from app.models.chat_channel_models import CHAT_CHANNEL_VALUES
from app.services.analytics_service import AnalyticsEvents, capture_event

#: The chat platforms a priority list may contain. A stored document that names
#: anything else (hand-edited, or a platform we dropped) can never route a
#: message somewhere unsupported because every entry is filtered through this.
#: Every bot platform, not just the ones in the default order — a user who puts
#: iMessage first has chosen a platform GAIA can genuinely text on.
VALID_CHAT_PLATFORMS: frozenset[str] = CHAT_CHANNEL_VALUES


def resolve_channel_priority(stored: list[str] | None) -> list[str]:
    """The user's stored chat-channel priority, or the default order.

    Unknown entries are dropped; a list that is empty after cleaning falls back
    to the default rather than resolving to "no channel", because an unusable
    stored value is a data problem, not a user preference for silence.
    """
    if isinstance(stored, list):
        cleaned = [p for p in stored if p in VALID_CHAT_PLATFORMS]
        if cleaned:
            return cleaned
    return list(DEFAULT_CHAT_CHANNEL_PRIORITY)


async def get_chat_channel_priority(user_id: str) -> list[str]:
    """The order the settings UI shows: the user's own, or the default."""
    user = await user_repository.get(user_id)
    return resolve_channel_priority(user.chat_channel_priority if user else None)


async def set_chat_channel_priority(user_id: str, priority: list[str]) -> None:
    """Store a new order and report the change (platform names only, no content)."""
    await user_repository.set_chat_channel_priority(user_id, priority)
    capture_event(
        user_id,
        AnalyticsEvents.SETTINGS_CHAT_CHANNEL_PRIORITY_UPDATED,
        {"first": priority[0], "count": len(priority)},
    )
