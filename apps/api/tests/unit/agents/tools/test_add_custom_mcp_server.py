"""Unit tests for the add_custom_mcp_server executor tool.

The tool must never leak a secret or an OAuth URL into its return value (the
ToolMessage the LLM reads): OAuth/bearer flows are delivered through the
capability-free connect card (request_integration_connection), and a token is
never accepted as an argument.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.tools.core.registry import ToolRegistry
from app.agents.tools.integration_tool import add_custom_mcp_server

_MODULE = "app.agents.tools.integration_tool"
_CONFIG = {"configurable": {"user_id": "u1"}}
_URL = "https://mcp.sentry.dev/mcp"


def _integration(integration_id: str = "int-1", name: str = "Sentry") -> SimpleNamespace:
    return SimpleNamespace(integration_id=integration_id, name=name)


@pytest.fixture
def seams():
    """Patch every external seam of the tool; each test drives the mocks it needs."""
    mcp_client = AsyncMock()
    mcp_client.probe_connection = AsyncMock(return_value={})
    repo = MagicMock()
    repo.find_custom_by_server_url = AsyncMock(return_value=None)
    user_repo = MagicMock()
    user_repo.is_connected = AsyncMock(return_value=False)
    with (
        patch(f"{_MODULE}.OAUTH_INTEGRATIONS", []),
        patch(f"{_MODULE}.get_mcp_client", AsyncMock(return_value=mcp_client)),
        patch(f"{_MODULE}.integration_repository", repo),
        patch(f"{_MODULE}.user_integration_repository", user_repo),
        patch(
            f"{_MODULE}.create_and_connect_custom_integration", new=AsyncMock()
        ) as create_connect,
        patch(f"{_MODULE}.create_custom_integration", new=AsyncMock()) as create,
        patch(
            f"{_MODULE}.request_integration_connection",
            new=AsyncMock(return_value="A connect button has been shown to the user."),
        ) as request_card,
    ):
        yield SimpleNamespace(
            mcp_client=mcp_client,
            repo=repo,
            user_repo=user_repo,
            create_connect=create_connect,
            create=create,
            request_card=request_card,
        )


async def _run(server_url: str = _URL, name: str = "Sentry", config=_CONFIG) -> str:
    return await add_custom_mcp_server.ainvoke(
        {"server_url": server_url, "name": name}, config=config
    )


async def test_no_auth_server_connects_and_reports_tool_count(seams):
    seams.mcp_client.probe_connection.return_value = {}
    seams.create_connect.return_value = (
        _integration(),
        {"status": "connected", "tools_count": 3},
    )

    result = await _run()

    assert "connected" in result.lower()
    assert "3 tools" in result
    seams.request_card.assert_not_awaited()
    # the resolved URL is normalized before it reaches the service
    passed_request = seams.create_connect.await_args.args[1]
    assert passed_request.server_url == _URL


async def test_oauth_server_shows_card_and_never_leaks_the_oauth_url(seams):
    seams.mcp_client.probe_connection.return_value = {"requires_auth": True, "auth_type": "oauth"}
    seams.create_connect.return_value = (
        _integration(integration_id="int-oauth"),
        {"status": "requires_oauth", "oauth_url": "https://evil.example/secret-state-token"},
    )

    result = await _run()

    assert result == "A connect button has been shown to the user."
    assert "secret-state-token" not in result
    assert "http" not in result  # the tool return carries no URL at all
    seams.request_card.assert_awaited_once()
    assert seams.request_card.await_args.args[0] == "int-oauth"


async def test_bearer_server_hands_off_to_ui_without_taking_a_token(seams):
    seams.mcp_client.probe_connection.return_value = {"requires_auth": True, "auth_type": "bearer"}
    seams.create.return_value = _integration(integration_id="int-bearer")

    result = await _run()

    # created (so the UI has a target for the token) but never auto-connected,
    # and the connect+token flow is delegated to the secure card.
    seams.create.assert_awaited_once()
    seams.create_connect.assert_not_awaited()
    created_request = seams.create.await_args.args[1]
    assert created_request.auth_type == "bearer"
    assert created_request.bearer_token is None
    seams.request_card.assert_awaited_once()
    assert result == "A connect button has been shown to the user."


async def test_duplicate_already_connected_short_circuits(seams):
    seams.repo.find_custom_by_server_url.return_value = _integration(name="Sentry")
    seams.user_repo.is_connected.return_value = True

    result = await _run()

    assert "already added" in result.lower()
    seams.mcp_client.probe_connection.assert_not_awaited()
    seams.create_connect.assert_not_awaited()
    seams.create.assert_not_awaited()


async def test_duplicate_not_connected_shows_connect_card(seams):
    seams.repo.find_custom_by_server_url.return_value = _integration(
        integration_id="int-dup", name="Sentry"
    )
    seams.user_repo.is_connected.return_value = False

    result = await _run()

    assert result == "A connect button has been shown to the user."
    seams.request_card.assert_awaited_once()
    assert seams.request_card.await_args.args[0] == "int-dup"
    seams.mcp_client.probe_connection.assert_not_awaited()


async def test_catalog_app_redirects_to_connect_integration(seams):
    with patch(
        f"{_MODULE}.OAUTH_INTEGRATIONS",
        [SimpleNamespace(id="github", name="GitHub", short_name=None)],
    ):
        result = await _run(name="GitHub")

    assert "connect_integration" in result
    assert "github" in result
    seams.create_connect.assert_not_awaited()
    seams.create.assert_not_awaited()


async def test_disallowed_url_is_rejected_before_any_write(seams):
    result = await _run(server_url="ftp://evil.example/mcp")

    assert result.startswith("❌")
    seams.create_connect.assert_not_awaited()
    seams.create.assert_not_awaited()
    seams.mcp_client.probe_connection.assert_not_awaited()


async def test_missing_user_id_fails_loud(seams):
    result = await _run(config={"configurable": {}})

    assert "User ID not found" in result


async def test_failed_connect_keeps_record_and_surfaces_id(seams):
    seams.mcp_client.probe_connection.return_value = {}
    seams.create_connect.return_value = (
        _integration(integration_id="int-9"),
        {"status": "failed", "error": "boom"},
    )

    result = await _run()

    assert "couldn't connect" in result.lower()
    assert "int-9" in result
    assert "boom" in result


def test_add_custom_mcp_server_is_force_gated():
    """HIL is globally 'always_allow' pre-launch, so only always_gate_tools produce
    a confirmation card. Without the stamp the tool would connect an LLM-resolved
    server with no user approval."""
    registry = ToolRegistry()
    registry._initialize_categories()

    add_meta = registry.get_tool_meta("add_custom_mcp_server")
    assert add_meta is not None
    assert add_meta.always_gate is True

    # Control: connect_integration is destructive but not force-gated, so the
    # assertion above proves the stamp is selective, not blanket-true.
    connect_meta = registry.get_tool_meta("connect_integration")
    assert connect_meta is not None
    assert connect_meta.always_gate is False
