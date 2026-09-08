"""Exact-string tests for GAIA's deterministic first contact after one-tap linking.

No model runs on this path, so the copy IS the feature: every bubble here is a
message a real user reads seconds after signing up. A mutation that reorders the
bubbles, drops a pick, or changes a promise must go red.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.user_models import OnboardingNeed, OnboardingPreferences
from app.services.onboarding.first_contact import (
    NEED_INTEGRATIONS,
    NEED_PROMISES,
    build_first_contact,
    compose_first_contact,
    compose_link_greeting,
    needed_integration_ids,
)

CONNECTED_PATCH = "app.services.onboarding.first_contact.user_integration_repository.is_connected"
LINK_PATCH = "app.services.onboarding.first_contact.build_connect_link_url"


def _prefs(
    needs: list[OnboardingNeed] | None = None,
    other_need: str | None = None,
) -> OnboardingPreferences:
    return OnboardingPreferences(profession="founder", needs=needs, other_need=other_need)


@pytest.mark.unit
class TestNeedPromises:
    def test_every_need_has_a_promise(self) -> None:
        """A pick with no promise is a pick GAIA silently ignores — the exact
        failure the deterministic bundle exists to stop."""
        assert set(NEED_PROMISES) == set(OnboardingNeed)

    def test_every_need_declares_its_integrations(self) -> None:
        """An absent key and an empty tuple mean different things only if every
        need is present: a missing key is a forgotten need, not "connects
        nothing"."""
        assert set(NEED_INTEGRATIONS) == set(OnboardingNeed)

    @pytest.mark.parametrize("promise", NEED_PROMISES.values())
    def test_no_promise_shouts_or_uses_an_emoji(self, promise: str) -> None:
        assert "!" not in promise
        assert promise.isascii()

    @pytest.mark.parametrize("promise", NEED_PROMISES.values())
    def test_every_promise_is_a_problem_sentence_then_a_promise_sentence(
        self, promise: str
    ) -> None:
        """The shape Aryan asked for. One sentence is either a complaint with no
        offer or an offer with no reason, and both read as a slogan."""
        problem, _, rest = promise.partition(". ")
        assert problem and rest.endswith(".")


@pytest.mark.unit
class TestNeededIntegrationIds:
    def test_picks_dedupe_and_keep_tap_order(self) -> None:
        """Mornings needs Gmail too; the founder who tapped the inbox first sees
        the Gmail link first, and never twice."""
        assert needed_integration_ids(_prefs([OnboardingNeed.INBOX, OnboardingNeed.MORNINGS])) == [
            "gmail",
            "googlecalendar",
        ]

    def test_picks_that_connect_nothing_contribute_nothing(self) -> None:
        assert needed_integration_ids(_prefs([OnboardingNeed.GRUNT_WORK])) == []

    def test_no_picks_is_no_links(self) -> None:
        assert needed_integration_ids(_prefs(None)) == []


@pytest.mark.unit
class TestComposeFirstContact:
    def test_the_founder_bundle_reads_end_to_end(self) -> None:
        assert compose_first_contact(
            "telegram",
            "Aryan Randeriya",
            _prefs([OnboardingNeed.INBOX, OnboardingNeed.CALENDAR, OnboardingNeed.GRUNT_WORK]),
            [
                ("gmail", "https://gaia.test/connect/aaa"),
                ("googlecalendar", "https://gaia.test/connect/bbb"),
            ],
        ) == [
            "Hey Aryan. I'm with you on Telegram now.",
            "Your inbox is out of control. Every morning I'll have it sorted and "
            "the replies drafted.",
            "You walk into meetings cold. I'll brief you before each one.",
            "Grunt work eats your week. Hand it to me and it's done.",
            "Two taps and those switch on. Links are live for the next hour:",
            "Gmail: https://gaia.test/connect/aaa",
            "Google Calendar: https://gaia.test/connect/bbb",
        ]

    def test_the_promises_follow_the_order_the_user_tapped(self) -> None:
        """Their first pick is what they came for, so it leads."""
        bubbles = compose_first_contact(
            "telegram", None, _prefs([OnboardingNeed.CALENDAR, OnboardingNeed.INBOX]), []
        )
        assert bubbles[1] == NEED_PROMISES[OnboardingNeed.CALENDAR]
        assert bubbles[2] == NEED_PROMISES[OnboardingNeed.INBOX]

    def test_one_link_is_one_tap(self) -> None:
        bubbles = compose_first_contact(
            "telegram",
            None,
            _prefs([OnboardingNeed.INBOX]),
            [("gmail", "https://gaia.test/connect/aaa")],
        )
        assert bubbles[-2] == "One tap and that switches on. The link is live for the next hour:"
        assert bubbles[-1] == "Gmail: https://gaia.test/connect/aaa"

    def test_each_link_is_its_own_bubble_under_its_real_name(self) -> None:
        """One link per message: a wall of URLs is a wall nobody taps, and the
        name comes from the OAuth config so it matches the connect page."""
        bubbles = compose_first_contact(
            "whatsapp",
            None,
            _prefs([OnboardingNeed.MORNINGS]),
            [("gmail", "https://a"), ("googlecalendar", "https://b")],
        )
        assert bubbles[-2:] == ["Gmail: https://a", "Google Calendar: https://b"]

    def test_nothing_to_connect_still_offers_a_first_move(self) -> None:
        """Ending on the promises alone ends on nothing the user can say yes to."""
        bubbles = compose_first_contact("telegram", None, _prefs([OnboardingNeed.REMINDERS]), [])
        assert bubbles[-1] == "Say the word and I'll start."

    def test_their_own_words_are_quoted_back_and_taken_on(self) -> None:
        bubbles = compose_first_contact(
            "telegram", None, _prefs([OnboardingNeed.INBOX], other_need="chasing invoices."), []
        )
        assert bubbles[-2] == 'You said: "chasing invoices". I\'ll take that on too.'

    def test_a_blank_other_need_adds_no_bubble(self) -> None:
        bubbles = compose_first_contact(
            "telegram", None, _prefs([OnboardingNeed.INBOX], other_need="   "), []
        )
        assert bubbles == [
            "Hey. I'm with you on Telegram now.",
            NEED_PROMISES[OnboardingNeed.INBOX],
            "Say the word and I'll start.",
        ]

    def test_a_user_who_picked_nothing_still_gets_a_hello_and_an_offer(self) -> None:
        assert compose_first_contact("telegram", "Aryan", _prefs(None), []) == [
            "Hey Aryan. I'm with you on Telegram now.",
            "Say the word and I'll start.",
        ]

    def test_output_is_stable_across_calls(self) -> None:
        prefs = _prefs([OnboardingNeed.INBOX])
        assert compose_first_contact("telegram", "Aryan", prefs, []) == compose_first_contact(
            "telegram", "Aryan", prefs, []
        )


@pytest.mark.unit
class TestComposeLinkGreeting:
    @pytest.mark.parametrize(
        ("platform", "expected"),
        [
            ("telegram", "Hey Aryan. I'm with you on Telegram now."),
            ("whatsapp", "Hey Aryan. I'm with you on WhatsApp now."),
            ("imessage", "Hey Aryan. I'm with you on iMessage now."),
        ],
    )
    def test_each_platform_is_named_the_way_the_user_calls_it(
        self, platform: str, expected: str
    ) -> None:
        assert compose_link_greeting(platform, "Aryan Randeriya") == expected

    @pytest.mark.parametrize("name", [None, "", "   "])
    def test_an_unknown_name_drops_the_clause_rather_than_greeting_a_blank(
        self, name: str | None
    ) -> None:
        assert compose_link_greeting("telegram", name) == "Hey. I'm with you on Telegram now."


@pytest.mark.unit
class TestBuildFirstContact:
    async def test_an_already_connected_integration_is_not_re_offered(self) -> None:
        """A link to something already on is a tap that does nothing, and it
        makes the whole first move look like GAIA is not paying attention."""
        with (
            patch(CONNECTED_PATCH, new=AsyncMock(side_effect=lambda _u, i: i == "gmail")),
            patch(LINK_PATCH, new=AsyncMock(return_value="https://gaia.test/connect/x")) as mint,
        ):
            bubbles = await build_first_contact(
                "user1", "telegram", "Aryan", _prefs([OnboardingNeed.MORNINGS])
            )

        mint.assert_awaited_once_with("user1", "googlecalendar")
        assert bubbles[-1] == "Google Calendar: https://gaia.test/connect/x"
        assert not any("Gmail" in b for b in bubbles)

    async def test_a_link_that_could_not_be_minted_is_dropped_not_shipped_dead(self) -> None:
        """Redis down means no binding exists — a URL that resolves to nothing is
        worse in a first message than one fewer link."""
        with (
            patch(CONNECTED_PATCH, new=AsyncMock(return_value=False)),
            patch(LINK_PATCH, new=AsyncMock(return_value=None)),
        ):
            bubbles = await build_first_contact(
                "user1", "telegram", None, _prefs([OnboardingNeed.INBOX])
            )

        assert bubbles[-1] == "Say the word and I'll start."

    async def test_every_unconnected_integration_gets_its_own_minted_link(self) -> None:
        with (
            patch(CONNECTED_PATCH, new=AsyncMock(return_value=False)),
            patch(LINK_PATCH, new=AsyncMock(side_effect=lambda _u, i: f"https://gaia.test/{i}")),
        ):
            bubbles = await build_first_contact(
                "user1", "telegram", None, _prefs([OnboardingNeed.INBOX, OnboardingNeed.CALENDAR])
            )

        assert bubbles[-2:] == [
            "Gmail: https://gaia.test/gmail",
            "Google Calendar: https://gaia.test/googlecalendar",
        ]
