"""The always-live connected-device context: names the user's machines + servers
so the agent routes local-file work to the device instead of the cloud sandbox."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.context import fetchers as mod


def _device(did: str, name: str, platform: str) -> SimpleNamespace:
    return SimpleNamespace(id=did, name=name, platform=platform)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lists_each_device_with_its_servers():
    devices = [_device("d1", "MacBook", "macOS")]
    servers = {
        "d1": [
            SimpleNamespace(display_name="Local Files"),
            SimpleNamespace(display_name="Everything"),
        ]
    }
    with (
        patch.object(mod, "list_devices_service", AsyncMock(return_value=devices)),
        patch.object(mod, "list_device_servers", AsyncMock(return_value=servers)),
    ):
        out = await mod.build_connected_devices_manifest("u1", "HEADER:")

    assert out.startswith("HEADER:")
    # The id is in the line verbatim: it's what run_on_device / the device tools
    # take, and the model invents a wrong one from the name without it.
    assert "- MacBook (macOS, id: d1) exposing: Local Files, Everything" in out


@pytest.mark.unit
@pytest.mark.asyncio
async def test_device_with_no_servers_still_listed():
    with (
        patch.object(
            mod, "list_devices_service", AsyncMock(return_value=[_device("d1", "Box", "linux")])
        ),
        patch.object(mod, "list_device_servers", AsyncMock(return_value={})),
    ):
        out = await mod.build_connected_devices_manifest("u1", "HEADER:")
    assert out == "HEADER:\n- Box (linux, id: d1)"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_when_no_devices():
    with patch.object(mod, "list_devices_service", AsyncMock(return_value=[])):
        out = await mod.build_connected_devices_manifest("u1", "HEADER:")
    assert out == ""


@pytest.mark.unit
@pytest.mark.asyncio
async def test_swallows_errors_to_empty_block():
    # A context section is enrichment; a lookup failure degrades to "" (byte-stable),
    # never fails the user's turn.
    with patch.object(mod, "list_devices_service", AsyncMock(side_effect=RuntimeError("boom"))):
        out = await mod.build_connected_devices_manifest("u1", "HEADER:")
    assert out == ""
