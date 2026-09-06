"""What the stored sequence says about the streak of unanswered days."""

from datetime import UTC, datetime

import pytest

from app.models.activation_models import ActivationMessage, ActivationSequenceState
from app.services.activation.policy import Direction

pytestmark = pytest.mark.unit

_NOW = datetime(2026, 9, 7, 8, 0, tzinfo=UTC)


def _msg(day: int, direction: Direction, target: str | None = None) -> ActivationMessage:
    return ActivationMessage(
        day=day,
        direction=direction,
        platform="telegram",
        sent_at=_NOW,
        bubbles=["hi"],
        suggestion="s",
        connect_target=target,
    )


class TestStreaks:
    def test_fresh_state_has_no_streak(self) -> None:
        state = ActivationSequenceState()
        assert state.unanswered_days() == 0
        assert state.handover_asks() == 0
        assert state.connect_asks() == 0
        assert state.connect_targets_asked() == set()

    def test_the_streak_counts_back_to_the_last_reply(self) -> None:
        state = ActivationSequenceState(
            messages=[
                _msg(0, Direction.CONNECT, "gmail"),
                _msg(1, Direction.CONTINUE_THREAD),
                _msg(2, Direction.HANDOVER),
                _msg(3, Direction.HANDOVER),
            ]
        )
        assert state.unanswered_days() == 2
        assert state.handover_asks() == 2
        assert state.connect_asks() == 1
        assert state.connect_targets_asked() == {"gmail"}

    def test_a_handover_before_the_reply_is_not_in_the_streak(self) -> None:
        state = ActivationSequenceState(
            messages=[_msg(0, Direction.HANDOVER), _msg(1, Direction.CONTINUE_THREAD)]
        )
        assert state.unanswered_days() == 0
        assert state.handover_asks() == 0
