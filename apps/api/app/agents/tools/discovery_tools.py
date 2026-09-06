"""Discovery tools the comms agent runs itself, without the executor.

Three questions used to cost a round trip through ``call_executor``: "is there a
Notion integration?", "is there a ready-made workflow for X?" and "connect my
Gmail". The first two are read-only catalogue lookups with no side effects, and
the third has to land its card in the SAME reply as the sentence that offers it
-- which the executor path cannot do, because its card arrives on a later
message once the background run reports back.

None of these do work on the user's data, so putting them on the front door does
not breach the "delegate every real ask" rule: they read catalogues, and
``show_connect_card`` renders UI.

``show_connect_card`` deliberately owns no card-building logic. It validates an
id and defers to :func:`request_integration_connection`, the one place that
knows about expired grants, UI vs bot wording and the stream frame. A second
implementation is how the card and its copy drift apart.
"""

from typing import Annotated, Any, TypedDict, cast

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.config.oauth_config import OAUTH_INTEGRATIONS, get_integration_by_id
from app.config.settings import settings
from app.constants.log_tags import LogTag
from app.decorators import with_doc
from app.helpers.integration_helpers import build_search_matcher
from app.models.agent_models import agent_configurable
from app.models.workflow_models import PublicWorkflowsResponse
from app.services.integrations.community_service import list_community_integrations
from app.services.oauth.oauth_service import check_multiple_integrations_status
from app.services.workflow.service import WorkflowService
from app.templates.docstrings.discovery_tool_docs import (
    FIND_INTEGRATION,
    SEARCH_PUBLIC_WORKFLOWS,
    SHOW_CONNECT_CARD,
)
from app.utils.integration_checker import request_integration_connection
from shared.py.wide_events import log

# Five is what a chat reply can carry without turning into a catalogue dump; the
# model picks one and shows its card rather than listing everything it found.
MAX_DISCOVERY_RESULTS = 5

# Over-fetch before filtering: neither public-workflow list takes a query, so the
# match happens here and a small page would hide the one template that matches.
PUBLIC_WORKFLOW_FETCH_LIMIT = 50


class IntegrationMatch(TypedDict):
    """One integration the user could use, and whether they already can."""

    id: str
    name: str
    description: str
    connected: bool
    source: str


class PublicWorkflowMatch(TypedDict):
    """One public workflow template the user could add from the explore page."""

    title: str
    description: str
    source_integration: str | None
    slug: str | None


def _user_id_from(config: RunnableConfig) -> str | None:
    configurable = agent_configurable(config)
    return configurable.get("user_id") if configurable else None


def _one_line(text: str | None) -> str:
    """First sentence-ish line of a catalogue description, never a paragraph."""
    collapsed = " ".join((text or "").split())
    return collapsed[:160]


@tool
@with_doc(FIND_INTEGRATION)
async def find_integration(
    config: RunnableConfig,
    query: Annotated[
        str,
        "What the user is looking for: a product name ('notion', 'slack') or a "
        "capability ('email', 'crm', 'project management').",
    ],
) -> dict[str, Any]:
    """Search GAIA's built-in integrations and the public marketplace."""
    try:
        log.set(tool={"name": "find_integration", "action": "search"})
        user_id = _user_id_from(config)
        if not user_id:
            return {"error": "User ID not found in configuration.", "query": query}

        matcher = build_search_matcher(query)

        # Platform integrations first: these are the only ones show_connect_card
        # can render, so a platform hit is always more useful than a community one.
        available = [i for i in OAUTH_INTEGRATIONS if i.available]
        status_map = await check_multiple_integrations_status([i.id for i in available], user_id)

        matches: list[IntegrationMatch] = [
            {
                "id": integration.id,
                "name": integration.name,
                "description": _one_line(integration.description),
                "connected": status_map.get(integration.id, False),
                "source": "platform",
            }
            for integration in available
            if matcher(
                f"{integration.name} {integration.description} {integration.category}".lower()
            )
        ]

        if len(matches) < MAX_DISCOVERY_RESULTS:
            # Same call the marketplace search endpoint makes; no second search.
            community = await list_community_integrations(search=query, limit=MAX_DISCOVERY_RESULTS)
            seen = {m["id"].lower() for m in matches}
            matches.extend(
                {
                    "id": item.integration_id,
                    "name": item.name,
                    "description": _one_line(item.description),
                    "connected": False,
                    "source": "community",
                }
                for item in community.integrations
                if item.integration_id.lower() not in seen
            )

        capped = matches[:MAX_DISCOVERY_RESULTS]
        log.set_ns("tool", result_count=len(capped))
        return {"integrations": capped, "query": query}

    except Exception as e:
        log.error(f"{LogTag.TOOL} Error finding integrations", error_type=type(e).__name__)
        return {"error": f"Could not search integrations: {e!s}", "query": query}


@tool
@with_doc(SEARCH_PUBLIC_WORKFLOWS)
async def search_public_workflows(
    config: RunnableConfig,  # noqa: ARG001 -- tool contract; the catalogue is public
    query: Annotated[
        str,
        "The outcome the user wants a template for, e.g. 'weekly investor "
        "update', 'morning briefing', 'triage my inbox'.",
    ],
) -> dict[str, Any]:
    """Search the featured and community public workflow templates."""
    explore_url = f"{settings.FRONTEND_URL.rstrip('/')}/workflows"
    try:
        log.set(tool={"name": "search_public_workflows", "action": "search"})
        matcher = build_search_matcher(query)

        # Cacheable erases the wrapped return type; both are declared
        # -> PublicWorkflowsResponse, so this is correct by construction.
        explore = cast(
            PublicWorkflowsResponse,
            await WorkflowService.get_explore_workflows(limit=PUBLIC_WORKFLOW_FETCH_LIMIT),
        )
        community = cast(
            PublicWorkflowsResponse,
            await WorkflowService.get_community_workflows(limit=PUBLIC_WORKFLOW_FETCH_LIMIT),
        )

        matches: list[PublicWorkflowMatch] = []
        seen: set[str] = set()
        for row in [*explore.workflows, *community.workflows]:
            identity = str(row.get("id") or row.get("slug") or row.get("title"))
            if identity in seen:
                continue
            haystack = " ".join(
                str(row.get(field) or "")
                for field in ("title", "description", "source_integration")
            ).lower()
            if not matcher(haystack):
                continue
            seen.add(identity)
            matches.append(
                {
                    "title": str(row.get("title") or ""),
                    "description": _one_line(row.get("description")),
                    "source_integration": row.get("source_integration"),
                    "slug": row.get("slug"),
                }
            )
            if len(matches) == MAX_DISCOVERY_RESULTS:
                break

        log.set_ns("tool", result_count=len(matches))
        return {"workflows": matches, "query": query, "explore_url": explore_url}

    except Exception as e:
        log.error(f"{LogTag.TOOL} Error searching public workflows", error_type=type(e).__name__)
        return {
            "error": f"Could not search public workflows: {e!s}",
            "query": query,
            "explore_url": explore_url,
        }


@tool
@with_doc(SHOW_CONNECT_CARD)
async def show_connect_card(
    config: RunnableConfig,
    integration_id: Annotated[
        str,
        "Exact integration id, e.g. 'gmail', 'notion', 'googlecalendar'. Use "
        "find_integration when unsure; a wrong id shows the user nothing.",
    ],
) -> str:
    """Render the connect card for an integration in this reply."""
    try:
        log.set(tool={"name": "show_connect_card", "action": "show"})
        user_id = _user_id_from(config)
        if not user_id:
            return "Error: User ID not found in configuration."

        normalized = integration_id.lower().strip()
        integration = get_integration_by_id(normalized)
        if integration is None or not integration.available:
            # Naming the alternatives keeps the model from retrying the same
            # wrong id, which is what it does when told only "not found".
            available = ", ".join(i.id for i in OAUTH_INTEGRATIONS if i.available)
            return (
                f"No connectable integration with id '{integration_id}'. No card was shown, so "
                f"do NOT tell the user to connect anything. Valid ids: {available}"
            )

        instruction = await request_integration_connection(
            integration.id, integration.name, str(user_id)
        )
        return (
            f"The connect card for {integration.name} is now in this reply; do not describe it "
            f"as coming, do not ask whether to send it. {instruction}"
        )

    except Exception as e:
        log.error(
            f"{LogTag.TOOL} Error showing connect card",
            integration_id=integration_id,
            error_type=type(e).__name__,
        )
        return (
            f"Could not show the connect card ({e!s}). No card was shown, so do NOT tell the "
            f"user to connect anything this turn."
        )
