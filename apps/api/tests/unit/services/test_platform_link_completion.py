"""Link completion's side effects: whatever GAIA says after a link is sent
from here. A one-tap onboarding link hands over its composed first contact;
any other new link gets the generic connected text."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.chat_models import ConversationSource
from app.models.platform_models import PlatformLinkResult
from app.services.outbound_delivery import OutboundResult
from app.services.platform_link_completion import complete_platform_link

MODULE = "app.services.platform_link_completion"
BUBBLES = ["Hey Aryan, I'm with you on WhatsApp now.", "Tell me one thing off your plate."]


def _linked(is_new_link: bool = True) -> PlatformLinkResult:
    return PlatformLinkResult(
        status="linked",
        platform="whatsapp",
        platform_user_id="wa-1",
        connected_at="2026-09-08T00:00:00Z",
        is_new_link=is_new_link,
    )


@pytest.fixture
def side_effects():
    notify = AsyncMock()
    publish = AsyncMock(return_value=OutboundResult.PUBLISHED)
    link = AsyncMock(return_value=_linked())
    with (
        patch(f"{MODULE}.PlatformLinkService.link_account", link),
        patch(f"{MODULE}.notify_account_linked", notify),
        patch(f"{MODULE}.publish_outbound_message", publish),
        patch(f"{MODULE}.schedule_account_sync", MagicMock()),
        patch(f"{MODULE}.capture_event", MagicMock()),
    ):
        yield notify, publish, link


class TestPostLinkMessage:
    async def test_a_new_link_without_a_first_contact_gets_the_generic_text(
        self, side_effects
    ) -> None:
        notify, publish, _ = side_effects
        await complete_platform_link("u1", "whatsapp", "wa-1")
        notify.assert_awaited_once_with("whatsapp", "u1")
        publish.assert_not_awaited()

    async def test_a_repeat_link_without_a_first_contact_says_nothing(self, side_effects) -> None:
        notify, publish, link = side_effects
        link.return_value = _linked(is_new_link=False)
        await complete_platform_link("u1", "whatsapp", "wa-1")
        notify.assert_not_awaited()
        publish.assert_not_awaited()

    async def test_a_first_contact_is_delivered_on_the_outbound_queue_instead(
        self, side_effects
    ) -> None:
        notify, publish, _ = side_effects
        await complete_platform_link("u1", "whatsapp", "wa-1", first_contact=BUBBLES)
        publish.assert_awaited_once_with(ConversationSource.WHATSAPP, "u1", BUBBLES)
        notify.assert_not_awaited()

    async def test_a_first_contact_is_delivered_even_when_the_link_already_existed(
        self, side_effects
    ) -> None:
        """Tapping the link twice still answers the tap."""
        _, publish, link = side_effects
        link.return_value = _linked(is_new_link=False)
        await complete_platform_link("u1", "whatsapp", "wa-1", first_contact=BUBBLES)
        publish.assert_awaited_once()

    async def test_an_undelivered_first_contact_is_logged_loudly_but_keeps_the_link(
        self, side_effects
    ) -> None:
        _, publish, _ = side_effects
        publish.return_value = OutboundResult.FAILED
        with patch(f"{MODULE}.log") as mock_log:
            result = await complete_platform_link("u1", "whatsapp", "wa-1", first_contact=BUBBLES)
        assert result.is_new_link is True
        mock_log.warning.assert_called_once_with(
            "first contact was not delivered after a one-tap link",
            platform="whatsapp",
            user_id="u1",
            outcome="failed",
        )
