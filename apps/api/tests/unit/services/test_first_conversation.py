"""The two bubbles GAIA opens with after onboarding, and the chips merged in.

Post-onboarding, not a pitch: bubble one opens the door and sells the two
routines, bubble two hands over addressed by the job they gave. The only
model-written part is the starting jobs, merged by ``with_starting_jobs``; with
no jobs the escape hatch is the only chip, never invented ones.
"""

from app.models.user_models import OnboardingPreferences
from app.services.onboarding.first_conversation import (
    CALENDAR_INTEGRATION_ID,
    CONNECT_OPTIONS,
    CONNECT_OPTIONS_TOOL_NAME,
    GMAIL_INTEGRATION_ID,
    INTEGRATIONS_PATH,
    ROUTINES_LINE,
    SOMETHING_ELSE_CHIP,
    WELCOME,
    compose_first_conversation,
    connect_link,
    with_starting_jobs,
)

JOBS = ["Find investors", "Fix my marketing", "Hire someone", "Write my pitch"]


def _prefs(profession: str | None = "founder") -> OnboardingPreferences:
    return OnboardingPreferences(profession=profession, needs=[], other_need=None)


class TestOpeningBubble:
    def test_a_linked_platform_is_named_in_the_welcome_then_the_routines(self) -> None:
        composed = compose_first_conversation(_prefs("founder"), "telegram")
        assert composed.opening == [
            f"{WELCOME} I'm on your Telegram too, text me there anytime.",
            ROUTINES_LINE,
        ]

    def test_no_platform_opens_the_door_and_moves_on(self) -> None:
        composed = compose_first_conversation(_prefs("founder"), None)
        assert composed.opening == [WELCOME, ROUTINES_LINE]
        assert composed.lines == [WELCOME, ROUTINES_LINE, composed.question]

    def test_the_welcome_hands_the_work_over_in_one_line(self) -> None:
        assert WELCOME == (
            "Okay, you're in. From here on, anything you'd rather not do yourself, hand it to me."
        )

    def test_imessage_keeps_its_capitalisation_and_unknown_platforms_are_capitalised(self) -> None:
        assert (
            "I'm on your iMessage too," in compose_first_conversation(_prefs(), "imessage").lines[0]
        )
        assert "I'm on your Signal too," in compose_first_conversation(_prefs(), "signal").lines[0]

    def test_the_routines_line_sells_exactly_the_two_built_ins(self) -> None:
        assert ROUTINES_LINE == (
            "Two things worth switching on now: connect Gmail and every morning your mail "
            "comes back sorted, replies drafted. Add Calendar and I brief you before every meeting."
        )

    def test_the_buttons_open_each_app_and_the_full_page(self) -> None:
        """Rendered by the web as a row of buttons outside the bubble, same tab."""
        tool = compose_first_conversation(_prefs("founder"), None).connect_tool_data()
        assert tool["tool_name"] == CONNECT_OPTIONS_TOOL_NAME == "connect_options"
        assert tool["data"] == {"options": CONNECT_OPTIONS}
        assert [o["href"] for o in CONNECT_OPTIONS] == [
            connect_link(GMAIL_INTEGRATION_ID),
            connect_link(CALENDAR_INTEGRATION_ID),
            INTEGRATIONS_PATH,
        ]
        assert [o.get("integration_id") for o in CONNECT_OPTIONS] == [
            GMAIL_INTEGRATION_ID,
            CALENDAR_INTEGRATION_ID,
            None,
        ]


class TestHandoverBubble:
    def test_a_picked_job_is_addressed_by_its_phrase(self) -> None:
        assert compose_first_conversation(_prefs("founder"), None).question == (
            "Since you're a founder, what are we starting with?"
        )
        assert compose_first_conversation(_prefs("sales"), None).question == (
            "Since you're in sales, what are we starting with?"
        )
        assert compose_first_conversation(_prefs("engineering"), None).question == (
            "Since you're an engineer, what are we starting with?"
        )

    def test_a_typed_sentence_is_turned_to_the_second_person(self) -> None:
        assert compose_first_conversation(_prefs("I run a bakery."), None).question == (
            "Since you run a bakery, what are we starting with?"
        )
        assert compose_first_conversation(_prefs("I'm a plumber"), None).question == (
            "Since you're a plumber, what are we starting with?"
        )

    def test_a_typed_title_gets_an_article_and_loses_its_capital(self) -> None:
        assert compose_first_conversation(_prefs("Plumber"), None).question == (
            "Since you're a plumber, what are we starting with?"
        )
        assert compose_first_conversation(_prefs("An Architect"), None).question == (
            "Since you're an architect, what are we starting with?"
        )

    def test_every_first_person_opener_is_turned(self) -> None:
        cases = {
            "I am a nurse": "Since you are a nurse, what are we starting with?",
            "We run a shop": "Since you run a shop, what are we starting with?",
            "We're a two person studio": "Since you're a two person studio, what are we starting with?",
        }
        for typed, expected in cases.items():
            assert compose_first_conversation(_prefs(typed), None).question == expected

    def test_trailing_punctuation_and_articles_are_dropped_and_vowels_get_an(self) -> None:
        assert compose_first_conversation(_prefs("Engineer!"), None).question == (
            "Since you're an engineer, what are we starting with?"
        )
        assert compose_first_conversation(_prefs("The Baker."), None).question == (
            "Since you're a baker, what are we starting with?"
        )
        assert compose_first_conversation(_prefs("a Barista"), None).question == (
            "Since you're a barista, what are we starting with?"
        )
        # Only the article goes; a multi-word title keeps every other word.
        assert compose_first_conversation(_prefs("The head baker"), None).question == (
            "Since you're a head baker, what are we starting with?"
        )
        # Only end punctuation is dropped, never a trailing letter of the job.
        assert compose_first_conversation(_prefs("Founder at SpaceX"), None).question == (
            "Since you're a founder at SpaceX, what are we starting with?"
        )
        # Every vowel earns "an"; anything else, including x, gets "a".
        for typed, expected in {
            "Illustrator": "an illustrator",
            "Optometrist": "an optometrist",
            "Urban planner": "an urban planner",
        }.items():
            assert compose_first_conversation(_prefs(typed), None).question == (
                f"Since you're {expected}, what are we starting with?"
            )
        assert compose_first_conversation(_prefs("X-ray technician"), None).question == (
            "Since you're a x-ray technician, what are we starting with?"
        )

    def test_other_or_skipped_gets_the_plain_question(self) -> None:
        for profession in ("other", "Other", None):
            assert compose_first_conversation(_prefs(profession), None).question == (
                "So, what are we starting with?"
            )

    def test_nothing_in_the_thread_recites_the_answers(self) -> None:
        for line in compose_first_conversation(_prefs(), "telegram").lines:
            assert "So:" not in line
            assert "You said" not in line


class TestChips:
    def test_without_jobs_the_only_chip_is_the_escape_hatch(self) -> None:
        assert compose_first_conversation(_prefs(), None).follow_ups == [SOMETHING_ELSE_CHIP]

    def test_the_jobs_lead_and_the_escape_hatch_closes(self) -> None:
        composed = compose_first_conversation(_prefs(), None)
        updated = with_starting_jobs(composed, JOBS)
        assert updated.lines == composed.lines
        assert updated.follow_ups == [*JOBS, SOMETHING_ELSE_CHIP]
        assert composed.follow_ups == [SOMETHING_ELSE_CHIP]

    def test_the_chips_are_copied_not_shared(self) -> None:
        jobs = list(JOBS)
        updated = with_starting_jobs(compose_first_conversation(_prefs(), None), jobs)
        jobs.append("Ship it")
        assert updated.follow_ups == [*JOBS, SOMETHING_ELSE_CHIP]
