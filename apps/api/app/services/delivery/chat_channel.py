"""The ONE chat platform a proactive message goes to.

A message GAIA sends on its own initiative (an activation nudge, a briefing)
belongs on one platform, not on every platform the user ever linked: fanning it
out is the triple-delivery bug, and the user reads it once anyway. This module
owns that single choice — the first platform in the user's priority order that
is both linked and preference-enabled — and nothing else. It is deliberately
free of any feature coupling so the activation sequence and the briefing can
share it.
"""

from collections.abc import Mapping

from app.constants.notifications import DEFAULT_CHAT_CHANNEL_PRIORITY
from app.services.platform_link_service import PlatformLinkService
from app.utils.notification.channel_preferences import fetch_channel_preferences

#: The chat platforms a priority list may contain. A stored document that names
#: anything else (hand-edited, or a platform we dropped) can never route a
#: message somewhere unsupported because every entry is filtered through this.
VALID_CHAT_PLATFORMS: frozenset[str] = frozenset(DEFAULT_CHAT_CHANNEL_PRIORITY)


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


def pick_chat_channel(
    priority: list[str], linked: Mapping[str, object], preferences: Mapping[str, bool]
) -> str | None:
    """The first platform in ``priority`` that is linked AND enabled, else ``None``.

    Pure so the ordering rules are provable without a database. ``None`` means
    the user has no usable bot platform; callers decide what that implies (the
    activation sequence stops, it never falls back to the web).
    """
    for platform in priority:
        if platform in linked and preferences.get(platform, True):
            return platform
    return None


async def resolve_chat_channel(user_id: str, stored_priority: list[str] | None) -> str | None:
    """The one chat platform for ``user_id``, or ``None`` when none is usable."""
    linked = await PlatformLinkService.get_linked_platforms(user_id)
    preferences = await fetch_channel_preferences(user_id)
    return pick_chat_channel(resolve_channel_priority(stored_priority), linked, preferences)
