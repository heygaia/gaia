"""The day's draft: what the model is asked, and who pays for the answer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.activation_models import ActivationDraft
from app.services.activation import copy
from app.services.activation.copy import ActivationCopyError, draft_message
from app.services.activation.policy import ActivationBrief, Direction, PromptBlocks

USER_ID = "6acc0dac0cc0a00000000001"
BRIEF = ActivationBrief(
    day=1,
    direction=Direction.CONNECT,
    blocks=PromptBlocks(
        who="Role: founder", integrations="Nothing", yesterday="-", already_sent="-"
    ),
)
DRAFT = ActivationDraft(bubbles=["Morning."], suggestion="connect gmail", connect_target="gmail")


@pytest.fixture
def model():
    runnable = MagicMock(name="runnable")
    with (
        patch.object(copy, "background_structured_runnable", return_value=runnable) as build,
        patch.object(copy, "ainvoke_llm", AsyncMock(return_value=DRAFT)) as invoke,
    ):
        yield {"build": build, "invoke": invoke, "runnable": runnable}


@pytest.mark.unit
class TestDraftMessage:
    async def test_the_spend_is_attributed_to_the_user_on_both_the_model_and_the_call(
        self, model
    ) -> None:
        draft = await draft_message(BRIEF, earlier=[], user_id=USER_ID)

        assert draft is DRAFT
        expected = {"configurable": {"user_id": USER_ID}}
        assert model["build"].call_args.kwargs["config"] == expected
        assert model["invoke"].await_args.kwargs["config"] == expected
        assert model["invoke"].await_args.kwargs["label"] == "activation_sequence"
        assert model["invoke"].await_args.args[0] is model["runnable"]

    async def test_the_simulator_writes_for_nobody(self, model) -> None:
        await draft_message(BRIEF, earlier=[], user_id=None)

        assert model["build"].call_args.kwargs["config"] is None
        assert model["invoke"].await_args.kwargs["config"] is None

    async def test_a_draft_that_repeats_an_earlier_day_is_retried_with_the_reason(
        self, model
    ) -> None:
        fresh = ActivationDraft(bubbles=["Different."], suggestion="book the dentist")
        model["invoke"].side_effect = [DRAFT, fresh]

        draft = await draft_message(BRIEF, earlier=[("Morning.", "connect gmail")], user_id=USER_ID)

        assert draft is fresh
        second_prompt = model["invoke"].await_args_list[1].args[1]
        assert "Your last draft was rejected" in second_prompt

    async def test_no_unique_draft_raises_instead_of_sending_a_repeat(self, model) -> None:
        with pytest.raises(ActivationCopyError, match="no unique draft for day 1"):
            await draft_message(BRIEF, earlier=[("Morning.", "connect gmail")], user_id=USER_ID)
