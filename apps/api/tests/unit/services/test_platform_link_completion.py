"""Link completion's side effects: whatever GAIA says after a link is sent
from here. A one-tap onboarding link hands over its composed first contact;
any other new link gets the generic connected text."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.outbound import OUTBOUND_TTL_SECONDS_GREETING
from app.models.chat_models import ConversationSource
from app.models.platform_models import PlatformLinkResult
from app.services.outbound_delivery import OutboundResult
from app.services.platform_link_completion import complete_platform_link
from app.services.platform_link_service import AccountHasDifferentPlatformError
from app.utils.errors import AppError

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
        publish.assert_awaited_once_with(
            ConversationSource.WHATSAPP, "u1", BUBBLES, ttl_seconds=OUTBOUND_TTL_SECONDS_GREETING
        )
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


class TestLinkConflicts:
    """The two 409s are not interchangeable.

    ``PlatformAccountTakenError`` is proved end to end through the route in
    ``tests/unit/api/test_platform_links_endpoint.py::test_link_conflict``; this
    is its sibling, where the conflict is on the GAIA side and the fix is the
    opposite one. The bots pick the message they show from ``code`` alone
    (``libs/shared/ts/src/bots/link-codes.ts::classifyLinkFailure``), so the
    exact body is a cross-language contract, not a message anyone may reword.
    """

    async def test_a_second_account_on_the_same_platform_names_the_conflict_the_user_owns(
        self, side_effects
    ) -> None:
        _, _, link = side_effects
        conflict = AccountHasDifferentPlatformError(
            "Your account already has a different whatsapp account linked"
        )
        link.side_effect = conflict

        with patch(f"{MODULE}.log") as mock_log, pytest.raises(AppError) as excinfo:
            await complete_platform_link("u1", "whatsapp", "wa-2")

        error = excinfo.value
        assert error.status_code == 409
        assert error.to_dict() == {
            "message": "Your account already has a different whatsapp account linked",
            "why": "this GAIA account already has a different account on this platform",
            "fix": "disconnect the one you already have in settings, then link this one",
            # Not "platform_account_taken": telling this person to free the
            # account on the other GAIA account sends them after one that does
            # not exist.
            "code": "account_has_other_platform_account",
        }
        assert error.__cause__ is conflict
        # The audit line has to say WHICH conflict fired; both 409s share this
        # call site, and a bare ValueError name cannot tell them apart.
        mock_log.audit.assert_called_once_with(
            "platform account link rejected",
            actor="u1",
            resource="wa-2",
            provider="whatsapp",
            error_type="AccountHasDifferentPlatformError",
            error="Your account already has a different whatsapp account linked",
        )
