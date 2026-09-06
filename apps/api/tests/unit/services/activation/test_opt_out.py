"""The one word that ends the sequence, and the one place both surfaces record it."""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.user_models import UserDocument
from app.services.activation import opt_out
from app.services.activation.opt_out import get_opted_out, is_stop_message, set_opted_out
from app.services.analytics_service import AnalyticsEvents

USER_ID = "6acc0dac0cc0a00000000001"


@pytest.mark.unit
class TestIsStopMessage:
    @pytest.mark.parametrize("text", ["stop", "STOP", " Stop ", "stop.", "stop!", "Stop!!"])
    def test_the_word_alone_in_any_dress_is_a_stop(self, text: str) -> None:
        assert is_stop_message(text) is True

    @pytest.mark.parametrize("text", ["stop booking that", "please stop", "stop?", "stopped", ""])
    def test_the_word_inside_a_request_is_not(self, text: str) -> None:
        assert is_stop_message(text) is False


@pytest.mark.unit
class TestSetOptedOut:
    async def test_stores_the_choice_and_reports_where_it_came_from(self) -> None:
        with (
            patch.object(opt_out.user_repository, "set_activation_opted_out", AsyncMock()) as save,
            patch.object(opt_out, "capture_event") as capture,
        ):
            await set_opted_out(USER_ID, True, source="telegram")

        save.assert_awaited_once_with(USER_ID, True)
        capture.assert_called_once_with(
            USER_ID, AnalyticsEvents.ACTIVATION_OPTED_OUT, {"opted_out": True, "source": "telegram"}
        )


@pytest.mark.unit
class TestGetOptedOut:
    async def test_reads_the_flag_off_this_users_sequence(self) -> None:
        user = UserDocument(_id=USER_ID, activation_sequence={"opted_out": True})
        with patch.object(opt_out.user_repository, "get", AsyncMock(return_value=user)) as read:
            assert await get_opted_out(USER_ID) is True
        read.assert_awaited_once_with(USER_ID)

    async def test_a_user_who_never_chose_is_still_on(self) -> None:
        with patch.object(opt_out.user_repository, "get", AsyncMock(return_value=None)):
            assert await get_opted_out(USER_ID) is False
