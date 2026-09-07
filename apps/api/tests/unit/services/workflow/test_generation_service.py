"""Unit tests for the pure helpers behind workflow step generation.

These pin the four helpers extracted out of ``WorkflowGenerationService`` in
``app/services/workflow/generation_service.py``: the user-facing failure
summary, the structured one-shot's call shape, and the two category collectors
that decide what the generator is allowed to reach for. Each is a pure function
over a seam (an exception, the LLM lane, the tool registry, the OAuth catalog),
so every branch is provable without touching a model.
"""

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import pytest

from app.constants.integrations import MANAGED_BY_INTERNAL
from app.services.workflow.generation_service import (
    _MAX_REASON_CHARS,
    _collect_registry_categories,
    _collect_subagent_categories,
    _failure_reason,
    _structured_one_shot,
)

MODULE = "app.services.workflow.generation_service"


# ---------------------------------------------------------------------------
# _failure_reason
# ---------------------------------------------------------------------------


class TestFailureReason:
    """The one line the workflow modal shows when generation dies."""

    def test_it_names_the_exception_type_and_its_message(self):
        """A bare "This request requires more credits" reads as if the user's own
        account is at fault; the type is what says the provider refused."""
        assert _failure_reason(ValueError("no route to model")) == ("ValueError: no route to model")

    def test_the_type_is_the_concrete_subclass_not_its_base(self):
        class ProviderRefused(RuntimeError):
            pass

        assert _failure_reason(ProviderRefused("402")) == "ProviderRefused: 402"

    def test_a_multi_line_provider_body_is_collapsed_to_one_line(self):
        """The modal renders this inline — a raw JSON body would break it."""
        assert _failure_reason(RuntimeError("credits\n  low\tnow")) == (
            "RuntimeError: credits low now"
        )

    def test_an_empty_message_falls_back_to_the_class_name(self):
        """``raise TimeoutError`` carries no message at all; "TimeoutError: "
        with nothing after it tells the user nothing."""
        assert _failure_reason(TimeoutError()) == "TimeoutError: TimeoutError"
        assert _failure_reason(TimeoutError("   ")) == "TimeoutError: TimeoutError"

    def test_a_message_exactly_at_the_limit_is_kept_whole(self):
        """The cut is for messages LONGER than the limit — truncating one that
        already fits would drop a character for nothing."""
        message = "a" * _MAX_REASON_CHARS

        assert _failure_reason(ValueError(message)) == f"ValueError: {message}"

    def test_a_longer_message_is_cut_to_the_limit_with_an_ellipsis(self):
        reason = _failure_reason(ValueError("a" * (_MAX_REASON_CHARS + 50)))

        assert reason == "ValueError: " + "a" * (_MAX_REASON_CHARS - 1) + "…"
        assert len(reason.removeprefix("ValueError: ")) == _MAX_REASON_CHARS

    def test_the_cut_never_leaves_a_space_before_the_ellipsis(self):
        """Cutting mid-sentence lands on a space as often as not; " …" reads as
        a typo rather than as elision."""
        message = "a" * (_MAX_REASON_CHARS - 2) + " " + "b" * 50

        assert _failure_reason(ValueError(message)) == (
            "ValueError: " + "a" * (_MAX_REASON_CHARS - 2) + "…"
        )


# ---------------------------------------------------------------------------
# _structured_one_shot
# ---------------------------------------------------------------------------


class _Draft(BaseModel):
    title: str = ""


class TestStructuredOneShot:
    """The lane a workflow draft is actually asked for."""

    async def test_it_meters_the_user_and_runs_the_schema_on_this_deployments_lane(self):
        """``metered_config`` is what bills the request to the user, and the SAME
        config has to reach both the runnable and the invoke: a deployment on a
        custom endpoint has no OpenRouter route, and a lost config sends the
        call back to the lane that does not exist here."""
        prompt = [HumanMessage(content="make me a workflow")]
        config = {"metadata": {"user_id": "user-1"}}
        runnable = MagicMock(name="structured_runnable")
        drafted = _Draft(title="Daily digest")

        with (
            patch(f"{MODULE}.metered_config", return_value=config) as mock_metered,
            patch(
                f"{MODULE}.background_structured_runnable", return_value=runnable
            ) as mock_runnable,
            patch(
                f"{MODULE}.ainvoke_llm", new_callable=AsyncMock, return_value=drafted
            ) as mock_llm,
        ):
            result = await _structured_one_shot(
                _Draft, prompt, label="workflow_steps", user_id="user-1"
            )

        assert result is drafted
        mock_metered.assert_called_once_with("user-1")
        mock_runnable.assert_called_once_with(_Draft, config=config)
        mock_llm.assert_awaited_once_with(runnable, prompt, label="workflow_steps", config=config)

    async def test_the_label_reaches_the_call_verbatim(self):
        """The label is how a generation shows up in the model-cost ledger; two
        call sites sharing one label make the spend unattributable."""
        with (
            patch(f"{MODULE}.metered_config", return_value={}),
            patch(f"{MODULE}.background_structured_runnable", return_value=MagicMock()),
            patch(
                f"{MODULE}.ainvoke_llm", new_callable=AsyncMock, return_value=_Draft()
            ) as mock_llm,
        ):
            await _structured_one_shot(
                _Draft, [HumanMessage(content="x")], label="workflow_prompt", user_id="user-1"
            )

        assert mock_llm.await_args.kwargs["label"] == "workflow_prompt"

    async def test_an_empty_draft_is_returned_as_is_rather_than_repaired(self):
        """The one-shot does not validate or substitute — the caller's retry loop
        owns the empty draft, so a silent fallback here would hide it."""
        empty = _Draft()

        with (
            patch(f"{MODULE}.metered_config", return_value={}),
            patch(f"{MODULE}.background_structured_runnable", return_value=MagicMock()),
            patch(f"{MODULE}.ainvoke_llm", new_callable=AsyncMock, return_value=empty),
        ):
            result = await _structured_one_shot(
                _Draft, [HumanMessage(content="x")], label="workflow_steps", user_id="user-1"
            )

        assert result is empty
        assert result.title == ""

    async def test_a_provider_error_propagates_instead_of_becoming_a_blank_draft(self):
        with (
            patch(f"{MODULE}.metered_config", return_value={}),
            patch(f"{MODULE}.background_structured_runnable", return_value=MagicMock()),
            patch(
                f"{MODULE}.ainvoke_llm",
                new_callable=AsyncMock,
                side_effect=RuntimeError("402 credits"),
            ),
        ):
            with pytest.raises(RuntimeError, match="402 credits"):
                await _structured_one_shot(
                    _Draft, [HumanMessage(content="x")], label="workflow_steps", user_id="user-1"
                )


# ---------------------------------------------------------------------------
# _collect_registry_categories
# ---------------------------------------------------------------------------


class _FakeTool:
    """A tool object carrying a name, whose ``str()`` is deliberately different."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"<tool object {self.name}>"


class _FakeCategory:
    def __init__(
        self,
        tools: list[object],
        require_integration: bool = False,
        integration_name: str | None = None,
    ) -> None:
        self.require_integration = require_integration
        self.integration_name = integration_name
        self._tools = tools

    def get_tool_objects(self) -> list[object]:
        return self._tools


def _registry(categories: dict[str, _FakeCategory]) -> MagicMock:
    registry = MagicMock()
    registry.get_all_category_objects.return_value = categories
    return registry


class TestCollectRegistryCategories:
    """What the generator is told it may build steps out of."""

    def test_core_categories_are_always_offered_with_their_tool_names(self):
        """A tool is named to the model by ``.name``; its repr would be a string
        the model cannot call."""
        registry = _registry(
            {"productivity": _FakeCategory([_FakeTool("create_todo"), _FakeTool("list_todos")])}
        )

        names, lines = _collect_registry_categories(registry, set())

        assert names == ["productivity"]
        assert lines == ["productivity: create_todo, list_todos"]

    def test_a_tool_without_a_name_falls_back_to_its_string_form(self):
        registry = _registry({"misc": _FakeCategory([_FakeTool("named"), "raw_tool"])})

        names, lines = _collect_registry_categories(registry, set())

        assert names == ["misc"]
        assert lines == ["misc: named, raw_tool"]

    def test_a_provider_category_is_offered_only_when_its_integration_is_active(self):
        """Offering an unconnected provider produces a workflow that fails on its
        first run, so the active set is the whole gate."""
        registry = _registry(
            {
                "gh_tools": _FakeCategory(
                    [_FakeTool("open_pr")], require_integration=True, integration_name="GitHub"
                )
            }
        )

        assert _collect_registry_categories(registry, {"github"}) == (
            ["gh_tools"],
            ["gh_tools: open_pr"],
        )
        assert _collect_registry_categories(registry, {"notion"}) == ([], [])

    def test_the_active_set_is_matched_on_the_integration_name_not_the_category(self):
        """The category key and the integration slug differ (``gh_tools`` vs
        ``github``); matching on the wrong one hides every connected provider."""
        registry = _registry(
            {
                "gh_tools": _FakeCategory(
                    [_FakeTool("open_pr")], require_integration=True, integration_name="GitHub"
                )
            }
        )

        assert _collect_registry_categories(registry, {"gh_tools"}) == ([], [])

    def test_a_provider_category_with_no_integration_name_falls_back_to_its_key(self):
        registry = _registry(
            {"notion": _FakeCategory([_FakeTool("search")], require_integration=True)}
        )

        assert _collect_registry_categories(registry, {"notion"}) == (
            ["notion"],
            ["notion: search"],
        )
        assert _collect_registry_categories(registry, set()) == ([], [])

    def test_one_skipped_provider_does_not_hide_the_categories_after_it(self):
        """The skip is a `continue`, not a `break`: a single unconnected provider
        early in the registry must not cost the model every category behind it."""
        registry = _registry(
            {
                "notion_tools": _FakeCategory(
                    [_FakeTool("search")], require_integration=True, integration_name="notion"
                ),
                "productivity": _FakeCategory([_FakeTool("create_todo")]),
            }
        )

        names, lines = _collect_registry_categories(registry, set())

        assert names == ["productivity"]
        assert lines == ["productivity: create_todo"]


# ---------------------------------------------------------------------------
# _collect_subagent_categories
# ---------------------------------------------------------------------------


@dataclass
class _FakeSubagentConfig:
    has_subagent: bool
    capabilities: str = ""


@dataclass
class _FakeIntegration:
    id: str
    managed_by: str
    subagent_config: _FakeSubagentConfig | None


def _catalog(*integrations: _FakeIntegration):
    return patch(f"{MODULE}.OAUTH_INTEGRATIONS", list(integrations))


class TestCollectSubagentCategories:
    """Which subagents the generator may delegate a step to."""

    def test_an_internal_subagent_is_offered_even_with_nothing_connected(self):
        """Todos/reminders/skills are core capabilities — gating them behind the
        active set would leave a brand-new user unable to generate anything."""
        with _catalog(
            _FakeIntegration(
                "todos", MANAGED_BY_INTERNAL, _FakeSubagentConfig(True, "creating todos")
            )
        ):
            assert _collect_subagent_categories(set()) == (
                ["todos"],
                ["todos (subagent): creating todos"],
            )

    def test_a_provider_subagent_is_offered_only_once_its_integration_is_active(self):
        gmail = _FakeIntegration("gmail", "composio", _FakeSubagentConfig(True, "sending mail"))

        with _catalog(gmail):
            assert _collect_subagent_categories({"gmail"}) == (
                ["gmail"],
                ["gmail (subagent): sending mail"],
            )
            assert _collect_subagent_categories(set()) == ([], [])
            assert _collect_subagent_categories({"notion"}) == ([], [])

    def test_the_active_set_is_matched_in_lower_case(self):
        """Integration ids arrive lower-cased in the active set; upper-casing the
        lookup would hide every connected provider subagent."""
        with _catalog(
            _FakeIntegration("GitHub", "composio", _FakeSubagentConfig(True, "opening PRs"))
        ):
            assert _collect_subagent_categories({"github"}) == (
                ["GitHub"],
                ["GitHub (subagent): opening PRs"],
            )

    def test_an_integration_with_no_subagent_is_skipped_without_reading_its_config(self):
        """Most of the catalog has no subagent at all — reaching into a missing
        config is an AttributeError on every generation."""
        with _catalog(
            _FakeIntegration("dropbox", "composio", None),
            _FakeIntegration("figma", "composio", _FakeSubagentConfig(has_subagent=False)),
            _FakeIntegration("gmail", "composio", _FakeSubagentConfig(True, "sending mail")),
        ):
            assert _collect_subagent_categories({"dropbox", "figma", "gmail"}) == (
                ["gmail"],
                ["gmail (subagent): sending mail"],
            )

    def test_one_unconnected_provider_does_not_hide_the_subagents_after_it(self):
        """The skip is a `continue`, not a `break`: the catalog is mostly
        unconnected providers, so stopping at the first one would leave the
        generator with nothing — including the internal capabilities."""
        with _catalog(
            _FakeIntegration("notion", "composio", _FakeSubagentConfig(True, "pages")),
            _FakeIntegration("todos", MANAGED_BY_INTERNAL, _FakeSubagentConfig(True, "todos")),
        ):
            assert _collect_subagent_categories(set()) == (
                ["todos"],
                ["todos (subagent): todos"],
            )

    def test_the_catalog_order_is_preserved(self):
        with _catalog(
            _FakeIntegration("todos", MANAGED_BY_INTERNAL, _FakeSubagentConfig(True, "a")),
            _FakeIntegration("gmail", "composio", _FakeSubagentConfig(True, "b")),
            _FakeIntegration("skills", MANAGED_BY_INTERNAL, _FakeSubagentConfig(True, "c")),
        ):
            names, lines = _collect_subagent_categories({"gmail"})

        assert names == ["todos", "gmail", "skills"]
        assert lines == [
            "todos (subagent): a",
            "gmail (subagent): b",
            "skills (subagent): c",
        ]
