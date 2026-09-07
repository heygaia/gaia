"""Which channels one briefing actually delivers to.

A briefing goes to a SINGLE chat platform picked by walking the priority order,
so a linked, enabled platform that is missing from that order is not merely
deprioritised — it never receives a brief at all. That is how an iMessage-only
user got nothing.
"""

import pytest

from app.constants.notifications import NotificationChannel
from app.services.briefing import delivery_channels


@pytest.fixture
def linked_and_enabled(monkeypatch):
    """Route the two lookups the resolver makes to per-test fakes."""

    def _configure(linked: set[str], prefs: dict[str, bool] | None = None) -> None:
        async def fake_linked(user_id: str) -> set[str]:
            return linked

        async def fake_prefs(user_id: str) -> dict[str, bool]:
            return prefs or {}

        monkeypatch.setattr(
            delivery_channels.PlatformLinkService,
            "get_linked_platforms",
            staticmethod(fake_linked),
        )
        monkeypatch.setattr(delivery_channels, "fetch_channel_preferences", fake_prefs)

    return _configure


class TestResolveBriefingChannels:
    async def test_imessage_only_user_gets_their_brief(self, linked_and_enabled):
        linked_and_enabled({NotificationChannel.IMESSAGE.value})

        channels = await delivery_channels.resolve_briefing_channels("u1", {})

        assert NotificationChannel.IMESSAGE.value in channels

    async def test_highest_linked_platform_in_the_order_wins(self, linked_and_enabled):
        linked_and_enabled(
            {
                NotificationChannel.IMESSAGE.value,
                NotificationChannel.DISCORD.value,
                NotificationChannel.WHATSAPP.value,
            }
        )

        channels = await delivery_channels.resolve_briefing_channels("u1", {})

        chat = [c for c in channels if c != NotificationChannel.INAPP.value]
        assert chat == [NotificationChannel.WHATSAPP.value]

    async def test_disabled_platform_is_skipped_for_the_next_one(self, linked_and_enabled):
        linked_and_enabled(
            {
                NotificationChannel.WHATSAPP.value,
                NotificationChannel.IMESSAGE.value,
            },
            prefs={NotificationChannel.WHATSAPP.value: False},
        )

        channels = await delivery_channels.resolve_briefing_channels("u1", {})

        assert NotificationChannel.IMESSAGE.value in channels
        assert NotificationChannel.WHATSAPP.value not in channels


class TestResolveChannelPriority:
    def test_imessage_survives_the_stored_order_filter(self):
        assert delivery_channels.resolve_channel_priority([NotificationChannel.IMESSAGE.value]) == [
            NotificationChannel.IMESSAGE.value
        ]
