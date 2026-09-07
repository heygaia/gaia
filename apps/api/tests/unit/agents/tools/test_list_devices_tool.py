"""Unit tests for the list_devices executor tool."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.agents.tools.integration_tool import list_devices

_MODULE = "app.agents.tools.integration_tool"
_CONFIG = {"configurable": {"user_id": "u1"}}


def _device(device_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=device_id,
        name="MacBook",
        platform="darwin",
        last_seen_at=datetime(2026, 9, 6, tzinfo=UTC),
    )


def _server(synced: bool) -> SimpleNamespace:
    return SimpleNamespace(
        server_key="github",
        display_name="GitHub",
        integration_id="int-gh",
        kind="stdio",
        status=SimpleNamespace(value="connected"),
        tools_synced_at=datetime(2026, 9, 6, tzinfo=UTC) if synced else None,
    )


async def _run(config=_CONFIG):
    return await list_devices.ainvoke({}, config=config)


async def test_lists_devices_with_online_and_server_mapping():
    with (
        patch(f"{_MODULE}.list_devices_service", AsyncMock(return_value=[_device("dev-1")])),
        patch(f"{_MODULE}.online_device_ids", AsyncMock(return_value={"dev-1"})),
        patch(
            f"{_MODULE}.list_device_servers",
            AsyncMock(return_value={"dev-1": [_server(synced=True)]}),
        ),
    ):
        result = await _run()

    assert result["devices"][0]["online"] is True
    assert result["devices"][0]["last_seen_at"] == "2026-09-06T00:00:00+00:00"
    server = result["devices"][0]["servers"][0]
    assert server["integration_id"] == "int-gh"
    assert server["kind"] == "stdio"
    assert server["status"] == "connected"
    assert server["tools_synced_at"] == "2026-09-06T00:00:00+00:00"


async def test_offline_device_and_unsynced_server_render():
    with (
        patch(f"{_MODULE}.list_devices_service", AsyncMock(return_value=[_device("dev-1")])),
        patch(f"{_MODULE}.online_device_ids", AsyncMock(return_value=set())),
        patch(
            f"{_MODULE}.list_device_servers",
            AsyncMock(return_value={"dev-1": [_server(synced=False)]}),
        ),
    ):
        result = await _run()

    assert result["devices"][0]["online"] is False
    # never-synced server surfaces null so the agent can warn the user
    assert result["devices"][0]["servers"][0]["tools_synced_at"] is None


async def test_missing_user_id_fails_loud():
    result = await _run(config={"configurable": {}})
    assert "User ID not found" in result
