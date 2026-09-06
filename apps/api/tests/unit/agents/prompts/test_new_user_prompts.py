"""The playbooks are one prose source rendered for two surfaces: the comms tier,
which can draw a connect card, and a bot message, which can only carry a link."""

import pytest

from app.agents.prompts.new_user_prompts import (
    NEED_CONNECT_IDS,
    NEED_PLAYBOOKS,
    playbook_for_message,
)
from app.config.oauth_config import get_integration_by_id
from app.models.user_models import OnboardingNeed

pytestmark = pytest.mark.unit


class TestPlaybookForMessage:
    def test_the_card_call_becomes_a_named_link(self) -> None:
        rendered = playbook_for_message(OnboardingNeed.INBOX)
        assert "show_connect_card" not in rendered
        assert "a Gmail connect link" in rendered
        assert rendered.startswith("inbox out of control")

    def test_a_choice_of_cards_keeps_its_ids(self) -> None:
        rendered = playbook_for_message(OnboardingNeed.TOOLS)
        assert "show_connect_card" not in rendered
        assert "a connect link for it ('slack', 'notion', 'github' or 'linear')" in rendered

    def test_a_playbook_without_a_card_is_unchanged(self) -> None:
        assert (
            playbook_for_message(OnboardingNeed.REMINDERS)
            == NEED_PLAYBOOKS[OnboardingNeed.REMINDERS]
        )

    def test_no_surface_ever_sees_a_tool_name_in_a_bot_message(self) -> None:
        for need in OnboardingNeed:
            assert "show_connect_card" not in playbook_for_message(need), need


class TestConnectIds:
    def test_every_id_is_a_real_integration(self) -> None:
        for need, ids in NEED_CONNECT_IDS.items():
            for integration_id in ids:
                assert get_integration_by_id(integration_id) is not None, (need, integration_id)

    def test_ids_match_the_prose(self) -> None:
        """The prose is the source; the id table must not drift from it."""
        for need in OnboardingNeed:
            for integration_id in NEED_CONNECT_IDS.get(need, ()):
                assert f"'{integration_id}'" in NEED_PLAYBOOKS[need], (need, integration_id)
        assert NEED_CONNECT_IDS[OnboardingNeed.INBOX] == ("gmail",)
        assert OnboardingNeed.REMINDERS not in NEED_CONNECT_IDS
