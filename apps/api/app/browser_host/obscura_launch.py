"""Shared Obscura process-launch primitives.

Obscura is a CDP *server* (``obscura serve``), not a chrome-with-a-debug-flag, so
both the interactive browser host and the crawl4ai engine start it the same way:
one argv, then poll ``/json/version`` for the websocket endpoint. Defined once
here so the spawn stays identical across both callers.
"""

from __future__ import annotations

import asyncio
import time

import httpx

from app.config.settings import settings

# Poll budget for Obscura to publish its DevTools endpoint after launch.
_CDP_READY_TIMEOUT_SECONDS = 30.0
_CDP_READY_POLL_SECONDS = 0.2


def obscura_serve_argv(port: int) -> list[str]:
    """The ``obscura serve`` argv for ``port``, stealthed and private-network-permitted.

    Raises when ``OBSCURA_BIN`` is unset — fail loud, never silently fall back to
    another engine.
    """
    obscura_bin = settings.OBSCURA_BIN
    if not obscura_bin:
        raise RuntimeError("Obscura requires OBSCURA_BIN to be set")
    return [
        obscura_bin,
        "serve",
        "--port",
        str(port),
        "--stealth",
        "--allow-private-network",
    ]


async def poll_obscura_endpoint(port: int) -> str:
    """Poll ``/json/version`` until Obscura yields its root ``webSocketDebuggerUrl``."""
    deadline = time.monotonic() + _CDP_READY_TIMEOUT_SECONDS
    async with httpx.AsyncClient() as client:
        while time.monotonic() < deadline:
            try:
                resp = await client.get(f"http://127.0.0.1:{port}/json/version", timeout=2.0)
                resp.raise_for_status()
                return str(resp.json()["webSocketDebuggerUrl"])
            except (httpx.HTTPError, KeyError):
                await asyncio.sleep(_CDP_READY_POLL_SECONDS)
    raise RuntimeError(f"Obscura did not expose its CDP endpoint on port {port} in time")
