"""What the stored sequence hands back to the next day's prompt."""

from datetime import UTC, datetime

import pytest

from app.models.activation_models import ActivationMessage, ActivationSequenceState
from app.services.activation.policy import Direction

SENT = datetime(2026, 5, 4, 8, 0, tzinfo=UTC)


def _message(bubbles: list[str], suggestion: str) -> ActivationMessage:
    return ActivationMessage(
        day=1,
        direction=Direction.CONNECT,
        platform="telegram",
        sent_at=SENT,
        bubbles=bubbles,
        suggestion=suggestion,
    )


@pytest.mark.unit
class TestEarlierDrafts:
    def test_each_day_contributes_its_opening_bubble_and_its_suggestion(self) -> None:
        state = ActivationSequenceState(
            day_sent=2,
            messages=[
                _message(["Morning.", "Gmail?"], "connect gmail"),
                _message(["Still here.", "Calendar?"], "connect calendar"),
            ],
        )

        assert state.earlier_drafts() == [
            ("Morning.", "connect gmail"),
            ("Still here.", "connect calendar"),
        ]

    def test_a_day_with_no_bubbles_contributes_an_empty_opening(self) -> None:
        state = ActivationSequenceState(day_sent=1, messages=[_message([], "connect gmail")])

        assert state.earlier_drafts() == [("", "connect gmail")]

    def test_of_none_is_a_fresh_sequence(self) -> None:
        assert ActivationSequenceState.of(None) == ActivationSequenceState()

    def test_of_a_stored_subdoc_reads_its_fields(self) -> None:
        assert ActivationSequenceState.of({"opted_out": True, "day_sent": 2}).opted_out is True
