"""Background tasks for paired bridge devices."""

from typing import Any

from app.constants.log_tags import LogTag
from app.services.device.device_service import (
    get_active_device,
    list_device_servers,
    record_device_server_sync,
)
from app.services.mcp.mcp_client import get_mcp_client
from shared.py.wide_events import log


async def warm_device_servers(
    ctx: dict[str, Any],  # noqa: ARG001 -- ARQ injects ctx positionally into every task
    device_id: str,
    server_keys: list[str] | None = None,
) -> str:
    """Connect a device's MCP servers so their tools are indexed and discoverable.

    Registration only records a server; nothing indexes its tools until a session
    opens. This runs that connect off the request path (the device spawn can take
    the full open timeout), recording each outcome on the server row so the UI can
    show a tool count or an error instead of an optimistic "connected".
    """
    device = await get_active_device(device_id)
    if device is None:
        return "device inactive"

    servers = (await list_device_servers([device_id])).get(device_id, [])
    if server_keys is not None:
        wanted = set(server_keys)
        servers = [s for s in servers if s.server_key in wanted]

    client = await get_mcp_client(device.user_id)
    warmed = 0
    failed = 0
    for server in servers:
        try:
            await client.ensure_connected(server.integration_id)
            await record_device_server_sync(server.integration_id, error=None)
            warmed += 1
        except Exception as e:
            # One server failing must not stop the others; the failure is recorded
            # on its row, not swallowed.
            failed += 1
            await record_device_server_sync(server.integration_id, error=f"{type(e).__name__}: {e}")
            log.warning(
                f"{LogTag.MCP} Device server warm-connect failed",
                device_id=device_id,
                server_key=server.server_key,
                error=str(e),
                error_type=type(e).__name__,
            )

    log.set(
        device={"operation": "warm_servers", "device_id": device_id},
        warmed=warmed,
        failed=failed,
    )
    return f"warmed={warmed} failed={failed}"
