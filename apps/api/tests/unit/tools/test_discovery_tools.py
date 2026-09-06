"""Unit tests for the comms-tier discovery tools.

The services are mocked at their seams (catalogue lookups, the marketplace
search, the workflow service, the stream writer); the tools themselves always
run for real, so a broken filter or a dropped field goes red here.
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
from app.db.repositories.user_integrations import user_integration_repository

_USER = "user1"
_CONFIG: dict[str, Any] = {"configurable": {"user_id": _USER}}
_FRONTEND = "https://app.example.com"


def _integration(
    integration_id: str, name: str, description: str, category: str = "productivity"
) -> MagicMock:
    stub = MagicMock()
    stub.id = integration_id
    stub.name = name
    stub.description = description
    stub.category = category
    stub.available = True
    return stub


_CATALOGUE = [
    _integration("gmail", "Gmail", "Read and send email from your inbox", "communication"),
    _integration("notion", "Notion", "Pages, databases and notes in Notion"),
    _integration("linear", "Linear", "Issue tracking for software teams"),
]


def _community(integration_id: str, name: str, description: str) -> MagicMock:
    stub = MagicMock()
    stub.integration_id = integration_id
    stub.name = name
    stub.description = description
    return stub


@contextmanager
def _catalogue(
    connected: dict[str, bool] | None = None,
    community: list[MagicMock] | None = None,
) -> Iterator[AsyncMock]:
    """Patch both catalogues find_integration reads, yielding the marketplace call."""
    community_response = MagicMock()
    community_response.integrations = community or []
    search = AsyncMock(return_value=community_response)
    with (
        patch("app.agents.tools.discovery_tools.OAUTH_INTEGRATIONS", _CATALOGUE),
        patch(
            "app.agents.tools.discovery_tools.check_multiple_integrations_status",
            AsyncMock(return_value=connected or {}),
        ),
        patch("app.agents.tools.discovery_tools.list_community_integrations", search),
    ):
        yield search


class TestFindIntegration:
    """Finds a platform integration by name or capability, with real connected status."""

    async def test_matches_a_platform_integration_by_name(self) -> None:
        with _catalogue():
            result = await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        assert [i["id"] for i in result["integrations"]] == ["notion"]
        row = result["integrations"][0]
        assert row["name"] == "Notion"
        assert row["source"] == "platform"
        assert row["connected"] is False

    async def test_matches_by_capability_not_just_product_name(self) -> None:
        with _catalogue():
            result = await find_integration.ainvoke({"query": "email"}, _CONFIG)

        assert [i["id"] for i in result["integrations"]] == ["gmail"]

    async def test_reports_the_users_real_connected_status(self) -> None:
        with _catalogue(connected={"gmail": True}):
            result = await find_integration.ainvoke({"query": "gmail"}, _CONFIG)

        assert result["integrations"][0]["connected"] is True

    async def test_tops_up_from_the_marketplace_using_the_same_search_call(self) -> None:
        extra = _community("stripe-mcp", "Stripe", "Payments and invoices")
        with _catalogue(community=[extra]) as search:
            result = await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        # The marketplace search service is called with the user's query, not a
        # browse listing: passing no `search` silently returns the popular list.
        assert search.await_args.kwargs["search"] == "notion"
        sources = {i["id"]: i["source"] for i in result["integrations"]}
        assert sources == {"notion": "platform", "stripe-mcp": "community"}

    async def test_marketplace_duplicates_of_a_platform_hit_are_dropped(self) -> None:
        with _catalogue(community=[_community("NOTION", "Notion", "dupe")]):
            result = await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        assert [i["id"] for i in result["integrations"]] == ["notion"]

    async def test_no_match_returns_an_empty_list_not_the_whole_catalogue(self) -> None:
        with _catalogue():
            result = await find_integration.ainvoke({"query": "quickbooks"}, _CONFIG)

        assert result["integrations"] == []

    async def test_caps_results_so_a_reply_never_becomes_a_catalogue_dump(self) -> None:
        many = [_community(f"c{n}", f"C{n}", "desc") for n in range(20)]
        with _catalogue(community=many):
            result = await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        assert len(result["integrations"]) == 5

    async def test_missing_user_id_is_an_error_not_an_empty_result(self) -> None:
        with _catalogue():
            result = await find_integration.ainvoke({"query": "notion"}, {"configurable": {}})

        # An empty list would read as "GAIA has no Notion" and the model would
        # tell the user so; the error branch has to stay distinguishable.
        assert "integrations" not in result
        assert "User ID" in result["error"]

    async def test_service_failure_degrades_to_an_error_not_an_exception(self) -> None:
        with (
            patch("app.agents.tools.discovery_tools.OAUTH_INTEGRATIONS", _CATALOGUE),
            patch(
                "app.agents.tools.discovery_tools.check_multiple_integrations_status",
                AsyncMock(side_effect=RuntimeError("composio down")),
            ),
        ):
            result = await find_integration.ainvoke({"query": "gmail"}, _CONFIG)

        assert "composio down" in result["error"]

    async def test_the_result_is_exactly_what_the_model_reads(self) -> None:
        """Every key is read by the model or by show_connect_card; a renamed or
        dropped one is a silent blank in the reply."""
        crm = _community("hubspot", "HubSpot", "  Sales \n  CRM   for teams ")
        with _catalogue(connected={"gmail": True}, community=[crm]):
            result = await find_integration.ainvoke({"query": "email"}, _CONFIG)

        assert result == {
            "integrations": [
                {
                    "id": "gmail",
                    "name": "Gmail",
                    "description": "Read and send email from your inbox",
                    "connected": True,
                    "source": "platform",
                },
                {
                    "id": "hubspot",
                    "name": "HubSpot",
                    "description": "Sales CRM for teams",
                    "connected": False,
                    "source": "community",
                },
            ],
            "query": "email",
        }

    async def test_the_status_lookup_covers_every_available_integration_for_this_user(
        self,
    ) -> None:
        status = AsyncMock(return_value={})
        with (
            _catalogue(),
            patch("app.agents.tools.discovery_tools.check_multiple_integrations_status", status),
        ):
            await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        status.assert_awaited_once_with(["gmail", "notion", "linear"], _USER)

    async def test_the_marketplace_is_asked_with_the_users_query_and_the_cap(self) -> None:
        with _catalogue() as search:
            await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        search.assert_awaited_once_with(search="notion", limit=MAX_DISCOVERY_RESULTS)

    async def test_a_full_page_of_platform_hits_skips_the_marketplace(self) -> None:
        """Exactly the cap: the marketplace can add nothing, so it is not asked."""
        crms = [
            _integration(f"crm{n}", f"CRM {n}", "customer crm")
            for n in range(MAX_DISCOVERY_RESULTS)
        ]
        with (
            _catalogue() as search,
            patch("app.agents.tools.discovery_tools.OAUTH_INTEGRATIONS", crms),
        ):
            result = await find_integration.ainvoke({"query": "crm"}, _CONFIG)

        search.assert_not_awaited()
        assert [m["id"] for m in result["integrations"]] == [f"crm{n}" for n in range(5)]

    async def test_one_short_of_the_cap_still_asks_the_marketplace(self) -> None:
        crms = [
            _integration(f"crm{n}", f"CRM {n}", "customer crm")
            for n in range(MAX_DISCOVERY_RESULTS - 1)
        ]
        with (
            _catalogue() as search,
            patch("app.agents.tools.discovery_tools.OAUTH_INTEGRATIONS", crms),
        ):
            await find_integration.ainvoke({"query": "crm"}, _CONFIG)

        search.assert_awaited_once()

    async def test_the_missing_user_error_is_exactly_the_shape_the_model_reads(self) -> None:
        with _catalogue():
            result = await find_integration.ainvoke({"query": "notion"}, {"configurable": {}})

        assert result == {"error": "User ID not found in configuration.", "query": "notion"}

    async def test_the_wide_event_names_the_tool_and_counts_the_capped_results(self) -> None:
        many = [_community(f"c{n}", f"C{n}", "desc") for n in range(20)]
        with _catalogue(community=many), patch("app.agents.tools.discovery_tools.log") as log:
            await find_integration.ainvoke({"query": "notion"}, _CONFIG)

        log.set.assert_any_call(tool={"name": "find_integration", "action": "search"})
        log.set_ns.assert_called_once_with("tool", result_count=MAX_DISCOVERY_RESULTS)


class TestOneLine:
    def test_none_is_empty(self) -> None:
        assert _one_line(None) == ""

    def test_whitespace_runs_and_newlines_collapse_to_single_spaces(self) -> None:
        assert _one_line("  Pages,\n  databases   and notes ") == "Pages, databases and notes"

    def test_a_paragraph_is_cut_at_exactly_160_characters(self) -> None:
        text = "x" * 200
        assert _one_line(text) == "x" * 160


def _workflow(title: str, description: str, **extra: Any) -> dict[str, Any]:
    return {"id": title, "title": title, "description": description, "slug": title, **extra}


@contextmanager
def _public_workflows(
    explore: list[dict[str, Any]], community: list[dict[str, Any]]
) -> Iterator[None]:
    explore_response = MagicMock(workflows=explore)
    community_response = MagicMock(workflows=community)
    with (
        patch("app.agents.tools.discovery_tools.WorkflowService") as service,
        patch("app.agents.tools.discovery_tools.settings") as mock_settings,
    ):
        mock_settings.FRONTEND_URL = _FRONTEND
        service.get_explore_workflows = AsyncMock(return_value=explore_response)
        service.get_community_workflows = AsyncMock(return_value=community_response)
        yield


class TestSearchPublicWorkflows:
    """Filters the two public lists, which take no query of their own."""

    async def test_matches_a_template_by_title_and_description(self) -> None:
        rows = [
            _workflow("Weekly investor update", "Summarise the week for investors"),
            _workflow("Morning briefing", "Your calendar and inbox at 8am"),
        ]
        with _public_workflows(rows, []):
            result = await search_public_workflows.ainvoke({"query": "investor update"}, _CONFIG)

        assert [w["title"] for w in result["workflows"]] == ["Weekly investor update"]

    async def test_searches_the_community_list_as_well_as_explore(self) -> None:
        with _public_workflows([], [_workflow("Investor digest", "for investors")]):
            result = await search_public_workflows.ainvoke({"query": "investor"}, _CONFIG)

        assert [w["title"] for w in result["workflows"]] == ["Investor digest"]

    async def test_returns_what_the_template_needs_connected(self) -> None:
        rows = [_workflow("Investor update", "weekly", source_integration="gmail")]
        with _public_workflows(rows, []):
            result = await search_public_workflows.ainvoke({"query": "investor"}, _CONFIG)

        assert result["workflows"][0]["source_integration"] == "gmail"
        assert result["workflows"][0]["slug"] == "Investor update"

    async def test_a_template_in_both_lists_is_returned_once(self) -> None:
        row = _workflow("Investor update", "weekly")
        with _public_workflows([row], [dict(row)]):
            result = await search_public_workflows.ainvoke({"query": "investor"}, _CONFIG)

        assert len(result["workflows"]) == 1

    async def test_always_returns_the_explore_url_because_there_is_no_chat_add(self) -> None:
        with _public_workflows([], []):
            result = await search_public_workflows.ainvoke({"query": "investor"}, _CONFIG)

        assert result["workflows"] == []
        assert result["explore_url"] == f"{_FRONTEND}/workflows"

    async def test_failure_still_carries_the_explore_url(self) -> None:
        with (
            patch("app.agents.tools.discovery_tools.WorkflowService") as service,
            patch("app.agents.tools.discovery_tools.settings") as mock_settings,
        ):
            mock_settings.FRONTEND_URL = _FRONTEND
            service.get_explore_workflows = AsyncMock(side_effect=RuntimeError("mongo down"))
            result = await search_public_workflows.ainvoke({"query": "investor"}, _CONFIG)

        assert "mongo down" in result["error"]
        assert result["explore_url"] == f"{_FRONTEND}/workflows"


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
        assert "User ID" in result


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
