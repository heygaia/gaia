"""How the bot opener strings the user's picks together."""

import pytest

from app.services.onboarding.first_message import _join


@pytest.mark.unit
class TestJoin:
    def test_one_phrase_is_itself(self) -> None:
        assert _join(["a"]) == "a"

    def test_two_phrases_take_a_bare_and(self) -> None:
        assert _join(["a", "b"]) == "a and b"

    def test_three_or_more_take_commas_and_an_oxford_and(self) -> None:
        assert _join(["a", "b", "c"]) == "a, b, and c"
        assert _join(["a", "b", "c", "d"]) == "a, b, c, and d"
