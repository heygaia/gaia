"""Unit tests for the device tunnel WebSocket connect ordering.

The online handler must hold the down-channel subscription before enqueueing
warmup: Redis drops pub/sub frames with no subscriber, which surfaces as a
warmup open-timeout and leaves the server's tools undiscoverable until the
next reconnect.
"""

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import WebSocketDisconnect
import pytest

from app.api.v1.endpoints import device_ws as ws_module

_MODULE = "app.api.v1.endpoints.device_ws"


def _socket() -> MagicMock:
    ws = MagicMock()
    ws.headers = {"authorization": "Bearer device-token"}
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


def _manager() -> MagicMock:
    manager = MagicMock()
    manager.owns = MagicMock(return_value=False)
    return manager


async def _run_handler(ws: MagicMock, relay, enqueue) -> None:
    with (
        patch.object(
            ws_module, "verify_device_token", return_value={"device_id": "d1", "user_id": "u1"}
        ),
        patch.object(ws_module, "get_active_device", AsyncMock(return_value=object())),
        patch.object(ws_module, "mark_online", AsyncMock()),
        patch.object(ws_module, "mark_offline", AsyncMock()),
        patch.object(ws_module, "device_connection_manager", _manager()),
        patch.object(ws_module, "enqueue_device_server_warmup", enqueue),
        patch.object(ws_module, "_down_relay", relay),
        patch.object(ws_module, "_heartbeat", AsyncMock()),
        patch.object(
            ws_module,
            "_receive_loop",
            AsyncMock(side_effect=WebSocketDisconnect()),
        ),
    ):
        await ws_module.device_ws(ws)


@pytest.mark.asyncio
async def test_warmup_enqueued_only_after_relay_subscribes():
    """The relay task is created first and the enqueue waits for its
    subscribe-ready signal — reversing that order drops the open frame."""
    order: list[str] = []

    async def fake_relay(websocket, device_id, ready=None):
        order.append("relay-start")
        await asyncio.sleep(0)
        ready.set()
        order.append("relay-subscribed")

    async def fake_enqueue(device_id, server_keys=None):
        order.append("enqueue")

    await _run_handler(_socket(), fake_relay, fake_enqueue)

    assert order.index("relay-subscribed") < order.index("enqueue")


@pytest.mark.asyncio
async def test_stalled_relay_does_not_block_the_socket():
    """A subscribe that never lands still lets the socket connect: the wait is
    bounded and the enqueue proceeds (a socket must never fail on warmup)."""
    enqueued = asyncio.Event()

    async def stalled_relay(websocket, device_id, ready=None):
        await asyncio.sleep(60)

    async def fake_enqueue(device_id, server_keys=None):
        enqueued.set()

    with patch.object(ws_module, "DEVICE_RELAY_READY_TIMEOUT_SECONDS", 0.01):
        await asyncio.wait_for(_run_handler(_socket(), stalled_relay, fake_enqueue), 10)

    assert enqueued.is_set()


@pytest.mark.asyncio
async def test_relay_signals_only_after_subscribe_returns():
    """The readiness signal fires after subscribe() resolves — not before."""
    events: list[str] = []
    pubsub = MagicMock()

    async def fake_get_message(**kwargs):
        # Yield like real Redis I/O: a bare AsyncMock never suspends, and the
        # tight poll loop would starve the event loop (and its timers).
        await asyncio.sleep(0.01)

    pubsub.get_message = AsyncMock(side_effect=fake_get_message)

    async def fake_subscribe(channel):
        events.append("subscribe")

    pubsub.subscribe = AsyncMock(side_effect=fake_subscribe)
    pubsub.unsubscribe = AsyncMock()
    pubsub.aclose = AsyncMock()
    redis = MagicMock()
    redis.pubsub = MagicMock(return_value=pubsub)
    ws = _socket()
    ready = asyncio.Event()

    with patch.object(ws_module.redis_cache, "redis", redis):
        task = asyncio.create_task(ws_module._down_relay(ws, "d1", ready))
        await asyncio.wait_for(ready.wait(), 5)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    assert events == ["subscribe"]
    pubsub.subscribe.assert_awaited_once_with("device:down:d1")


@pytest.mark.asyncio
async def test_relay_without_redis_still_signals_ready():
    """No Redis means no subscription is possible — signal anyway so the
    handler's bounded wait never stalls on the early return."""
    ready = asyncio.Event()
    with patch.object(ws_module.redis_cache, "redis", None):
        await ws_module._down_relay(_socket(), "d1", ready)
    assert ready.is_set()
