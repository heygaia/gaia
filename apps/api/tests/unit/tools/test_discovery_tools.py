"""Unit tests for the comms-tier discovery tools.

The services are mocked at their seams (the shared integration search, the
workflow repository, the stream writer); the tools themselves always run for
real, so a dropped field or a broken cap goes red here.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.tools.discovery_tools import (
    MAX_DISCOVERY_RESULTS,
    _one_line,
    find_integration,
    search_public_workflows,
    show_connect_card,
)
from app.config.oauth_config import OAUTH_INTEGRATIONS
from app.db.repositories.user_integrations import user_integration_repository
from app.models.workflow_models import PublicWorkflowRow
from app.schemas.integrations.responses import CommunityIntegrationItem, MyIntegrationItem

_USER = "user1"
_CONFIG: dict[str, Any] = {"configurable": {"user_id": _USER}}
_FRONTEND = "https://app.example.com"


def _mine(
    integration_id: str,
    name: str,
    description: str,
    *,
    connected: bool = False,
    source: str = "platform",
) -> MyIntegrationItem:
    return MyIntegrationItem(
        id=integration_id,
        name=name,
        description=description,
        category="productivity",
        source=source,  # type: ignore[arg-type] -- the literal is what the test varies
        managed_by="composio",
        status="connected" if connected else "not_connected",
    )


def _community(integration_id: str, name: str, description: str) -> CommunityIntegrationItem:
    return CommunityIntegrationItem(
        integration_id=integration_id,
        slug=integration_id,
        name=name,
        description=description,
        category="productivity",
    )


@contextmanager
def _catalogue(
    mine: list[MyIntegrationItem] | None = None,
    community: list[CommunityIntegrationItem] | None = None,
) -> Iterator[tuple[AsyncMock, AsyncMock]]:
    """Patch the shared integration search at both of its questions."""
    match_mine = AsyncMock(return_value=mine or [])
    match_public = AsyncMock(return_value=community or [])
    with (
        patch("app.agents.tools.discovery_tools.match_my_integrations", match_mine),
        patch("app.agents.tools.discovery_tools.match_public_integrations", match_public),
    ):
        yield match_mine, match_public


class TestFindIntegration:
    """The user's catalogue first, then the marketplace, capped for a chat reply."""

    async def test_asks_the_shared_search_for_this_users_matches(self) -> None:
        with _catalogue(mine=[_mine("notion", "Notion", "Pages and notes")]) as (mine, _):
            result = await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        mine.assert_awaited_once_with(_USER, "notion")
        row = result["integrations"][0]
        assert row == {
            "id": "notion",
            "name": "Notion",
            "description": "Pages and notes",
            "connected": False,
            "source": "platform",
        }

    async def test_reports_the_users_real_connected_status_and_source(self) -> None:
        with _catalogue(mine=[_mine("crm", "My CRM", "custom", connected=True, source="custom")]):
            result = await find_integration.ainvoke({"query": "crm"}, _CONFIG)

        assert result["integrations"][0]["connected"] is True
        assert result["integrations"][0]["source"] == "custom"

    async def test_tops_up_from_the_marketplace_excluding_what_was_already_listed(self) -> None:
        with _catalogue(
            mine=[_mine("notion", "Notion", "notes")],
            community=[_community("stripe-mcp", "Stripe", "Payments and invoices")],
        ) as (_, public):
            result = await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        public.assert_awaited_once_with(
            "notion", exclude_ids={"notion"}, limit=MAX_DISCOVERY_RESULTS - 1
        )
        sources = {i["id"]: i["source"] for i in result["integrations"]}
        assert sources == {"notion": "platform", "stripe-mcp": "community"}

    async def test_no_match_anywhere_is_an_empty_list_not_the_whole_catalogue(self) -> None:
        with _catalogue():
            result = await find_integration.ainvoke({"query": "quickbooks"}, _CONFIG)

        assert result["integrations"] == []

    async def test_a_full_page_of_own_hits_skips_the_marketplace(self) -> None:
        many = [_mine(f"crm{n}", f"CRM {n}", "crm") for n in range(MAX_DISCOVERY_RESULTS + 2)]
        with _catalogue(mine=many) as (_, public):
            result = await find_integration.ainvoke({"query": "crm"}, _CONFIG)

        public.assert_not_awaited()
        assert [m["id"] for m in result["integrations"]] == [f"crm{n}" for n in range(5)]

    async def test_one_short_of_the_cap_still_asks_the_marketplace_for_one(self) -> None:
        crms = [_mine(f"crm{n}", f"CRM {n}", "crm") for n in range(MAX_DISCOVERY_RESULTS - 1)]
        with _catalogue(mine=crms) as (_, public):
            await find_integration.ainvoke({"query": "crm"}, _CONFIG)

        assert public.await_args.kwargs["limit"] == 1

    async def test_descriptions_are_collapsed_to_one_line(self) -> None:
        crm = _community("hubspot", "HubSpot", "  Sales \n  CRM   for teams ")
        with _catalogue(community=[crm]):
            result = await find_integration.ainvoke({"query": "crm"}, _CONFIG)

        assert result["integrations"][0]["description"] == "Sales CRM for teams"

    async def test_missing_user_id_is_an_error_not_an_empty_result(self) -> None:
        with _catalogue():
            result = await find_integration.ainvoke({"query": "notion"}, {"configurable": {}})

        # An empty list would read as "GAIA has no Notion" and the model would
        # tell the user so; the error branch has to stay distinguishable.
        assert result == {"error": "User ID not found in configuration.", "query": "notion"}

    async def test_the_wide_event_names_the_tool_and_counts_the_results(self) -> None:
        many = [_community(f"c{n}", f"C{n}", "desc") for n in range(3)]
        with _catalogue(community=many), patch("app.agents.tools.discovery_tools.log") as log:
            await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        log.set.assert_any_call(tool={"name": "find_integration", "action": "search"})
        log.set_ns.assert_called_once_with("tool", result_count=3)

    async def test_a_failure_is_logged_by_type_and_returned_with_the_query(self) -> None:
        with (
            patch(
                "app.agents.tools.discovery_tools.match_my_integrations",
                AsyncMock(side_effect=RuntimeError("composio down")),
            ),
            patch("app.agents.tools.discovery_tools.log") as log,
        ):
            result = await find_integration.ainvoke({"query": "gmail"}, _CONFIG)

        assert result == {"error": "Could not search integrations: composio down", "query": "gmail"}
        log.error.assert_called_once()
        assert "Error finding integrations" in log.error.call_args.args[0]
        assert log.error.call_args.kwargs == {"error_type": "RuntimeError"}


class TestOneLine:
    def test_none_is_empty(self) -> None:
        assert _one_line(None) == ""

    def test_whitespace_runs_and_newlines_collapse_to_single_spaces(self) -> None:
        assert _one_line("  Pages,\n  databases   and notes ") == "Pages, databases and notes"

    def test_a_paragraph_is_cut_at_exactly_160_characters(self) -> None:
        text = "x" * 200
        assert _one_line(text) == "x" * 160


def _row(title: str, description: str, **extra: Any) -> PublicWorkflowRow:
    return PublicWorkflowRow.model_validate(
        {
            "user_id": "creator",
            "title": title,
            "description": description,
            "slug": title,
            "is_public": True,
            "prompt": "do the thing",
            "steps": [{"title": "step", "category": "gmail", "description": "d"}],
            "trigger_config": {"type": "manual"},
            **extra,
        }
    )


@contextmanager
def _public_workflows(rows: list[PublicWorkflowRow]) -> Iterator[AsyncMock]:
    find = AsyncMock(return_value=rows)
    with (
        patch(
            "app.agents.tools.discovery_tools.workflow_repository.find_public_matching",
            find,
        ),
        patch("app.agents.tools.discovery_tools.settings") as mock_settings,
    ):
        mock_settings.FRONTEND_URL = _FRONTEND
        yield find


class TestSearchPublicWorkflows:
    """The repository does the matching; the tool shapes the reply."""

    async def test_the_query_is_split_into_search_words_for_the_repository(self) -> None:
        with _public_workflows([]) as find:
            await search_public_workflows.ainvoke({"query": "the investor update"}, _CONFIG)

        find.assert_awaited_once_with(["investor", "update"], limit=MAX_DISCOVERY_RESULTS)

    async def test_the_result_is_exactly_what_the_model_reads(self) -> None:
        rows = [
            _row("Weekly investor update", "  Summarise \n the week ", source_integration="gmail")
        ]
        with _public_workflows(rows):
            result = await search_public_workflows.ainvoke({"query": "investor"}, _CONFIG)

        assert result == {
            "workflows": [
                {
                    "title": "Weekly investor update",
                    "description": "Summarise the week",
                    "source_integration": "gmail",
                    "slug": "Weekly investor update",
                }
            ],
            "query": "investor",
            "explore_url": f"{_FRONTEND}/workflows",
        }

    async def test_always_returns_the_explore_url_because_there_is_no_chat_add(self) -> None:
        with _public_workflows([]):
            result = await search_public_workflows.ainvoke({"query": "investor"}, _CONFIG)

        assert result["workflows"] == []
        assert result["explore_url"] == f"{_FRONTEND}/workflows"

    async def test_only_slashes_are_trimmed_from_the_frontend_url(self) -> None:
        with (
            _public_workflows([]),
            patch("app.agents.tools.discovery_tools.settings") as mock_settings,
        ):
            mock_settings.FRONTEND_URL = "https://app.example.com/preX/"
            result = await search_public_workflows.ainvoke({"query": "x"}, _CONFIG)

        assert result["explore_url"] == "https://app.example.com/preX/workflows"

    async def test_the_wide_event_names_the_tool_and_counts_the_matches(self) -> None:
        rows = [_row("Digest", "inbox"), _row("Sorter", "inbox")]
        with _public_workflows(rows), patch("app.agents.tools.discovery_tools.log") as log:
            await search_public_workflows.ainvoke({"query": "inbox"}, _CONFIG)

        log.set.assert_any_call(tool={"name": "search_public_workflows", "action": "search"})
        log.set_ns.assert_called_once_with("tool", result_count=2)

    async def test_a_failure_is_logged_by_type_and_returned_as_an_error_with_the_url(
        self,
    ) -> None:
        with (
            _public_workflows([]) as find,
            patch("app.agents.tools.discovery_tools.log") as log,
        ):
            find.side_effect = RuntimeError("db gone")
            result = await search_public_workflows.ainvoke({"query": "inbox"}, _CONFIG)

        assert result == {
            "error": "Could not search public workflows: db gone",
            "query": "inbox",
            "explore_url": f"{_FRONTEND}/workflows",
        }
        log.error.assert_called_once()
        assert "Error searching public workflows" in log.error.call_args.args[0]
        assert log.error.call_args.kwargs == {"error_type": "RuntimeError"}


@contextmanager
def _ui_graph_run(*, expired: bool = False) -> Iterator[MagicMock]:
    """A UI graph run, yielding the stream writer the card is emitted on."""
    writer = MagicMock()
    with (
        patch(
            "app.utils.integration_checker.get_config",
            return_value={"configurable": {"source_category": "ui"}},
        ),
        patch("app.utils.integration_checker.get_stream_writer", return_value=writer),
        patch(
            "app.utils.integration_checker.build_connect_link_url",
            AsyncMock(return_value=None),
        ),
        patch.object(user_integration_repository, "is_expired", AsyncMock(return_value=expired)),
    ):
        yield writer


class TestShowConnectCard:
    """A thin wrapper over the one card builder, with id validation."""

    async def test_emits_the_connect_card_frame(self) -> None:
        with _ui_graph_run() as writer:
            await show_connect_card.ainvoke({"integration_id": "gmail"}, _CONFIG)

        writer.assert_called_once_with(
            {
                "integration_connection_required": {
                    "integration_id": "gmail",
                    "expired": False,
                    "message": "To use Gmail features, please connect your account first.",
                }
            }
        )

    async def test_an_expired_grant_asks_the_user_to_sign_in_again(self) -> None:
        with _ui_graph_run(expired=True) as writer:
            await show_connect_card.ainvoke({"integration_id": "gmail"}, _CONFIG)

        assert writer.call_args[0][0]["integration_connection_required"]["expired"] is True

    async def test_tells_the_model_the_card_is_already_in_this_reply(self) -> None:
        with _ui_graph_run():
            result = await show_connect_card.ainvoke({"integration_id": "gmail"}, _CONFIG)

        # The failure this pins: the model narrating "I'll send you a link" and
        # the card sitting unmentioned in the same message.
        assert "is now in this reply" in result
        assert "do not ask whether to send it" in result

    async def test_an_unknown_id_shows_no_card_and_says_so(self) -> None:
        with _ui_graph_run() as writer:
            result = await show_connect_card.ainvoke({"integration_id": "quickbooks"}, _CONFIG)

        writer.assert_not_called()
        assert "No card was shown" in result
        assert "do NOT tell the user to connect" in result

    async def test_the_id_is_matched_case_insensitively(self) -> None:
        with _ui_graph_run() as writer:
            await show_connect_card.ainvoke({"integration_id": "  Gmail "}, _CONFIG)

        assert writer.call_args[0][0]["integration_connection_required"]["integration_id"] == (
            "gmail"
        )

    async def test_missing_user_id_shows_no_card(self) -> None:
        with _ui_graph_run() as writer:
            result = await show_connect_card.ainvoke(
                {"integration_id": "gmail"}, {"configurable": {}}
            )

        writer.assert_not_called()
        assert result == "Error: User ID not found in configuration."

    async def test_an_unknown_id_names_every_valid_one(self) -> None:
        with _ui_graph_run():
            result = await show_connect_card.ainvoke({"integration_id": "quickbooks"}, _CONFIG)

        valid = ", ".join(i.id for i in OAUTH_INTEGRATIONS if i.available)
        assert result == (
            "No connectable integration with id 'quickbooks'. No card was shown, so do NOT tell "
            f"the user to connect anything. Valid ids: {valid}"
        )

    async def test_the_card_is_requested_for_this_user_by_id_and_name(self) -> None:
        request = AsyncMock(return_value="Ask them to tap it.")
        with (
            patch("app.agents.tools.discovery_tools.request_integration_connection", request),
            patch("app.agents.tools.discovery_tools.log") as log,
        ):
            result = await show_connect_card.ainvoke({"integration_id": "gmail"}, _CONFIG)

        request.assert_awaited_once_with("gmail", "Gmail", _USER)
        assert result.endswith("do not ask whether to send it. Ask them to tap it.")
        log.set.assert_any_call(tool={"name": "show_connect_card", "action": "show"})

    async def test_a_failure_is_logged_with_the_id_and_type_and_the_model_is_told(self) -> None:
        with (
            patch(
                "app.agents.tools.discovery_tools.request_integration_connection",
                AsyncMock(side_effect=RuntimeError("stream gone")),
            ),
            patch("app.agents.tools.discovery_tools.log") as log,
        ):
            result = await show_connect_card.ainvoke({"integration_id": "gmail"}, _CONFIG)

        assert result.startswith("Could not show the connect card (stream gone). No card was shown")
        log.error.assert_called_once()
        assert "Error showing connect card" in log.error.call_args.args[0]
        assert log.error.call_args.kwargs == {
            "integration_id": "gmail",
            "error_type": "RuntimeError",
        }


class TestCardPayloadMatchesTheExecutorPath:
    """The comms card and the executor card must be the same frame.

    Two builders would drift and the web/bot clients would render two different
    cards for the same ask, which is the whole reason show_connect_card wraps
    request_integration_connection instead of writing its own frame.
    """

    async def test_payload_is_identical_to_the_executor_tools_payload(self) -> None:
        from app.agents.tools.integration_tool import connect_integration

        with _ui_graph_run() as comms_writer:
            await show_connect_card.ainvoke({"integration_id": "gmail"}, _CONFIG)
        comms_payload = comms_writer.call_args[0][0]

        with _ui_graph_run() as executor_writer:
            with (
                patch(
                    "app.agents.tools.integration_tool.check_single_integration_status",
                    AsyncMock(return_value=False),
                ),
                patch(
                    "app.agents.tools.integration_tool.get_stream_writer",
                    return_value=MagicMock(),
                ),
            ):
                await connect_integration.ainvoke({"integration_ids": ["gmail"]}, _CONFIG)
        executor_payload = next(
            call[0][0]
            for call in executor_writer.call_args_list
            if "integration_connection_required" in call[0][0]
        )

        assert comms_payload == executor_payload
