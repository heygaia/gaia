"""Link completion's side effects: the connected text is announced by default
and skipped for the one-tap onboarding link, whose composed first contact is
the confirmation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.platform_models import PlatformLinkResult
from app.services.platform_link_completion import complete_platform_link

MODULE = "app.services.platform_link_completion"


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
    with (
        patch(f"{MODULE}.PlatformLinkService.link_account", AsyncMock(return_value=_linked())),
        patch(f"{MODULE}.notify_account_linked", notify),
        patch(f"{MODULE}.schedule_account_sync", MagicMock()),
        patch(f"{MODULE}.capture_event", MagicMock()),
    ):
        yield notify


class TestAnnounce:
    async def test_a_new_link_is_announced_by_default(self, side_effects: AsyncMock) -> None:
        await complete_platform_link("u1", "whatsapp", "wa-1")
        side_effects.assert_awaited_once_with("whatsapp", "u1")

    async def test_the_one_tap_link_stays_quiet(self, side_effects: AsyncMock) -> None:
        await complete_platform_link("u1", "whatsapp", "wa-1", announce=False)
        side_effects.assert_not_awaited()
