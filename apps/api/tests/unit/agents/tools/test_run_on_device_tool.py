"""Unit tests for the run_on_device executor tool.

The tool runs a shell command on a paired machine. The behavior that must hold:
it refuses a device the requesting user does not own (authz), it surfaces the
device's exit code + stdout + stderr, and it turns a transport failure into a
readable message instead of raising.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.agents.tools.integration_tool import run_on_device
from app.services.mcp.device_exec import DeviceExecError
from tests.helpers import captured_wide_event

_MODULE = "app.agents.tools.integration_tool"
_CONFIG = {"configurable": {"user_id": "u1"}}


def _device(device_id: str) -> SimpleNamespace:
    return SimpleNamespace(id=device_id)


def _result(exit_code=0, stdout="", stderr="", truncated=False) -> SimpleNamespace:
    return SimpleNamespace(exit_code=exit_code, stdout=stdout, stderr=stderr, truncated=truncated)


async def _run(device_id="dev-1", command="ls", config=_CONFIG):
    return await run_on_device.ainvoke({"device_id": device_id, "command": command}, config=config)


async def test_runs_command_and_formats_output():
    exec_mock = AsyncMock(return_value=_result(exit_code=0, stdout="a.txt\nb.txt\n"))
    with (
        patch(f"{_MODULE}.list_devices_service", AsyncMock(return_value=[_device("dev-1")])),
        patch(f"{_MODULE}.run_device_command", exec_mock),
    ):
        async with captured_wide_event() as event:
            result = await _run(command="ls ~")

    assert event["tool"] == {"name": "run_on_device", "action": "exec"}
    exec_mock.assert_awaited_once_with("dev-1", "ls ~")
    assert "exit code: 0" in result
    assert "a.txt\nb.txt" in result


async def test_refuses_a_device_the_user_does_not_own():
    exec_mock = AsyncMock()
    with (
        patch(f"{_MODULE}.list_devices_service", AsyncMock(return_value=[_device("dev-1")])),
        patch(f"{_MODULE}.run_device_command", exec_mock),
    ):
        result = await _run(device_id="someone-elses-device")

    # Authz is the whole point: an id the user doesn't own must never reach the
    # bridge, so the command is not dispatched at all.
    exec_mock.assert_not_awaited()
    assert "someone-elses-device" in result
    assert "list_devices" in result


async def test_nonzero_exit_surfaces_stderr():
    with (
        patch(f"{_MODULE}.list_devices_service", AsyncMock(return_value=[_device("dev-1")])),
        patch(
            f"{_MODULE}.run_device_command",
            AsyncMock(return_value=_result(exit_code=2, stderr="no such file")),
        ),
    ):
        result = await _run(command="cat missing")

    assert "exit code: 2" in result
    assert "no such file" in result


async def test_offline_device_error_is_reported_not_raised():
    with (
        patch(f"{_MODULE}.list_devices_service", AsyncMock(return_value=[_device("dev-1")])),
        patch(
            f"{_MODULE}.run_device_command",
            AsyncMock(side_effect=DeviceExecError("Your device is offline.")),
        ),
    ):
        result = await _run()

    assert "Could not run the command" in result
    assert "offline" in result


async def test_macos_permission_denied_surfaces_full_disk_access_hint():
    with (
        patch(f"{_MODULE}.list_devices_service", AsyncMock(return_value=[_device("dev-1")])),
        patch(
            f"{_MODULE}.run_device_command",
            AsyncMock(
                return_value=_result(
                    exit_code=1, stderr="ls: /Users/x/Downloads: Operation not permitted"
                )
            ),
        ),
    ):
        result = await _run(command="ls ~/Downloads")

    # A raw errno is useless to the user; the tool must explain the macOS TCC
    # grant so the model can relay an actionable fix.
    assert "Full Disk Access" in result
    assert "gaia bridge down" in result


async def test_missing_user_id_fails_loud():
    result = await _run(config={"configurable": {}})
    assert result == "Error: User ID not found in configuration."
