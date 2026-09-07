"""Unit tests for warm_device_servers — the warm-connect that makes a device's
MCP tools discoverable after registration."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.workers.tasks.device_tasks import warm_device_servers

_MODULE = "app.workers.tasks.device_tasks"


def _server(integration_id: str, server_key: str) -> SimpleNamespace:
    return SimpleNamespace(integration_id=integration_id, server_key=server_key)


@pytest.mark.asyncio
async def test_warms_each_server_and_records_success():
    device = SimpleNamespace(user_id="u1")
    client = AsyncMock()
    client.ensure_connected = AsyncMock(return_value=["t1", "t2"])
    with (
        patch(f"{_MODULE}.get_active_device", AsyncMock(return_value=device)),
        patch(
            f"{_MODULE}.list_device_servers",
            AsyncMock(return_value={"dev": [_server("int-a", "a"), _server("int-b", "b")]}),
        ),
        patch(f"{_MODULE}.get_mcp_client", AsyncMock(return_value=client)),
        patch(f"{_MODULE}.record_device_server_sync", new=AsyncMock()) as record,
    ):
        result = await warm_device_servers({}, "dev")

    assert result == "warmed=2 failed=0"
    assert client.ensure_connected.await_count == 2
    recorded = {c.args[0]: c.kwargs["error"] for c in record.await_args_list}
    assert recorded == {"int-a": None, "int-b": None}


@pytest.mark.asyncio
async def test_one_server_failing_does_not_stop_the_rest():
    device = SimpleNamespace(user_id="u1")
    client = AsyncMock()
    client.ensure_connected = AsyncMock(side_effect=[RuntimeError("boom"), ["t1"]])
    with (
        patch(f"{_MODULE}.get_active_device", AsyncMock(return_value=device)),
        patch(
            f"{_MODULE}.list_device_servers",
            AsyncMock(return_value={"dev": [_server("int-bad", "bad"), _server("int-ok", "ok")]}),
        ),
        patch(f"{_MODULE}.get_mcp_client", AsyncMock(return_value=client)),
        patch(f"{_MODULE}.record_device_server_sync", new=AsyncMock()) as record,
    ):
        result = await warm_device_servers({}, "dev")

    assert result == "warmed=1 failed=1"
    recorded = {c.args[0]: c.kwargs["error"] for c in record.await_args_list}
    assert recorded["int-ok"] is None
    assert "boom" in recorded["int-bad"]


@pytest.mark.asyncio
async def test_inactive_device_is_a_noop():
    with patch(f"{_MODULE}.get_active_device", AsyncMock(return_value=None)):
        result = await warm_device_servers({}, "dev")
    assert result == "device inactive"


@pytest.mark.asyncio
async def test_server_keys_filter_limits_the_warmup():
    device = SimpleNamespace(user_id="u1")
    client = AsyncMock()
    client.ensure_connected = AsyncMock(return_value=[])
    with (
        patch(f"{_MODULE}.get_active_device", AsyncMock(return_value=device)),
        patch(
            f"{_MODULE}.list_device_servers",
            AsyncMock(return_value={"dev": [_server("int-a", "a"), _server("int-b", "b")]}),
        ),
        patch(f"{_MODULE}.get_mcp_client", AsyncMock(return_value=client)),
        patch(f"{_MODULE}.record_device_server_sync", new=AsyncMock()) as record,
    ):
        await warm_device_servers({}, "dev", ["b"])

    recorded = [c.args[0] for c in record.await_args_list]
    assert recorded == ["int-b"]
