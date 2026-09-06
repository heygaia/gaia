"""The repetition guard: what counts as "we already said that"."""

import pytest

from app.services.activation.uniqueness import (
    MAX_SUGGESTION_OVERLAP,
    opener,
    repeats_earlier,
    suggestion_overlap,
)


class TestOpener:
    def test_takes_the_first_six_words(self) -> None:
        assert opener("one two three four five six seven eight") == "one two three four five six"

    def test_ignores_case_and_punctuation(self) -> None:
        assert opener("Morning! Your inbox, again?") == opener("morning your inbox again")

    def test_shorter_text_is_its_whole_self(self) -> None:
        assert opener("hey there") == "hey there"


class TestSuggestionOverlap:
    def test_identical_suggestions_overlap_fully(self) -> None:
        assert suggestion_overlap("draft the investor update", "draft the investor update") == 1.0

    def test_unrelated_suggestions_do_not_overlap(self) -> None:
        assert suggestion_overlap("connect gmail", "book the dentist") == 0.0

    def test_stopwords_do_not_manufacture_overlap(self) -> None:
        # Two different ideas that share only filler words must read as different.
        assert suggestion_overlap("i want you to connect gmail", "i want you to call sam") < 0.5

    def test_two_empty_suggestions_are_not_a_new_idea(self) -> None:
        assert suggestion_overlap("", "") == 1.0

    def test_one_empty_suggestion_does_not_collide(self) -> None:
        assert suggestion_overlap("", "connect gmail") == 0.0


class TestRepeatsEarlier:
    def test_no_history_never_repeats(self) -> None:
        assert repeats_earlier("Morning, ready?", "connect gmail", []) is None

    def test_same_opener_is_rejected(self) -> None:
        earlier = [("Morning, want me to take the inbox?", "clear the inbox")]
        assert (
            repeats_earlier("Morning, want me to take the calendar?", "prep tomorrow", earlier)
            == "same_opener"
        )

    def test_same_suggestion_under_a_new_opener_is_rejected(self) -> None:
        earlier = [("Morning.", "connect gmail so i can triage your inbox")]
        assert (
            repeats_earlier(
                "Quick one before your day starts.",
                "connect gmail so i can triage your inbox",
                earlier,
            )
            == "same_suggestion"
        )

    def test_a_genuinely_new_message_passes(self) -> None:
        earlier = [
            ("Morning.", "connect gmail so i can triage your inbox"),
            ("Yesterday you asked about specs.", "turn the notes into a spec draft"),
        ]
        assert (
            repeats_earlier(
                "That competitor page changed.",
                "watch their pricing and ping you on changes",
                earlier,
            )
            is None
        )

    def test_the_threshold_is_exclusive(self) -> None:
        # A draft sitting exactly at the limit is allowed; only "more similar
        # than the limit" is a repeat, so the constant reads as documented.
        assert pytest.approx(0.6) == MAX_SUGGESTION_OVERLAP
        earlier = [("A.", "alpha beta gamma")]
        # 3 shared of 5 union = 0.6 exactly.
        assert repeats_earlier("B.", "alpha beta gamma delta epsilon", earlier) is None
