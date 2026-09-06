"""A reply counts only when it answers a day that was actually sent, recently."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.models.activation_models import ActivationMessage, ActivationSequenceState
from app.services.activation import engagement
from app.services.activation.engagement import REPLY_WINDOW_HOURS, record_reply
from app.services.activation.policy import Direction
from app.services.analytics_service import AnalyticsEvents

USER_ID = "6acc0dac0cc0a00000000001"
NOW = datetime(2026, 5, 4, 8, 0, tzinfo=UTC)


class _Clock:
    """``datetime`` as the module sees it, pinned so the window edge is exact."""

    @staticmethod
    def now(tz: object = None) -> datetime:
        assert tz is UTC
        return NOW


def _message(day: int, direction: Direction, sent_at: datetime) -> ActivationMessage:
    return ActivationMessage(
        day=day,
        direction=direction,
        platform="telegram",
        sent_at=sent_at,
        bubbles=["hi"],
        suggestion="connect gmail",
    )


def _state(age: timedelta, *, days: int = 2) -> ActivationSequenceState:
    sent_at = NOW - age
    return ActivationSequenceState(
        day_sent=days,
        last_sent_at=sent_at,
        messages=[
            _message(day, Direction.CONNECT if day == 1 else Direction.HANDOVER, sent_at)
            for day in range(1, days + 1)
        ],
    )


@pytest.fixture
def capture():
    with (
        patch.object(engagement, "datetime", _Clock),
        patch.object(engagement, "capture_event") as captured,
    ):
        yield captured


@pytest.mark.unit
class TestRecordReply:
    def test_a_reply_to_yesterdays_message_is_joined_to_that_day(self, capture) -> None:
        record_reply(USER_ID, _state(timedelta(hours=23)))

        capture.assert_called_once_with(
            USER_ID,
            AnalyticsEvents.ACTIVATION_REPLIED,
            {"day": 2, "platform": "telegram", "direction": Direction.HANDOVER},
        )

    def test_the_day_answered_is_the_last_one_sent_not_the_first(self, capture) -> None:
        record_reply(USER_ID, _state(timedelta(hours=1), days=3))

        assert capture.call_args.args[2]["day"] == 3

    def test_exactly_the_window_still_counts(self, capture) -> None:
        record_reply(USER_ID, _state(timedelta(hours=REPLY_WINDOW_HOURS)))

        capture.assert_called_once()

    def test_a_second_past_the_window_is_a_new_conversation(self, capture) -> None:
        record_reply(USER_ID, _state(timedelta(hours=REPLY_WINDOW_HOURS, seconds=1)))

        capture.assert_not_called()

    def test_a_user_who_was_never_messaged_produces_no_event(self, capture) -> None:
        record_reply(USER_ID, ActivationSequenceState())

        capture.assert_not_called()

    def test_a_send_time_without_messages_is_not_a_reply(self, capture) -> None:
        record_reply(USER_ID, ActivationSequenceState(day_sent=1, last_sent_at=NOW))

        capture.assert_not_called()

    def test_messages_without_a_send_time_are_not_a_reply(self, capture) -> None:
        state = ActivationSequenceState(day_sent=1, messages=[_message(1, Direction.CONNECT, NOW)])

        record_reply(USER_ID, state)

        capture.assert_not_called()
