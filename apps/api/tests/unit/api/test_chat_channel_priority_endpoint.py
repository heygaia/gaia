"""The settings surface for "where GAIA texts you first"."""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
import pytest

API = "/api/v1"


@pytest.mark.unit
class TestGetChatChannelPriority:
    async def test_returns_the_resolved_order(self, client: AsyncClient) -> None:
        with patch(
            "app.api.v1.endpoints.user.get_chat_channel_priority",
            new_callable=AsyncMock,
            return_value=["slack", "telegram"],
        ):
            resp = await client.get(f"{API}/user/chat-channel-priority")
        assert resp.status_code == 200
        assert resp.json() == {"priority": ["slack", "telegram"]}


@pytest.mark.unit
class TestUpdateChatChannelPriority:
    async def test_persists_and_echoes_the_order(self, client: AsyncClient) -> None:
        with patch(
            "app.api.v1.endpoints.user.set_chat_channel_priority",
            new_callable=AsyncMock,
        ) as save:
            resp = await client.patch(
                f"{API}/user/chat-channel-priority",
                json={"priority": ["discord", "telegram"]},
            )
        assert resp.status_code == 200
        assert resp.json() == {"priority": ["discord", "telegram"]}
        save.assert_awaited_once()
        assert save.await_args.args[1] == ["discord", "telegram"]

    async def test_rejects_an_unknown_platform(self, client: AsyncClient) -> None:
        resp = await client.patch(
            f"{API}/user/chat-channel-priority", json={"priority": ["telegram", "carrier-pigeon"]}
        )
        assert resp.status_code == 422

    async def test_rejects_a_non_bot_platform(self, client: AsyncClient) -> None:
        resp = await client.patch(f"{API}/user/chat-channel-priority", json={"priority": ["web"]})
        assert resp.status_code == 422

    async def test_rejects_an_empty_order(self, client: AsyncClient) -> None:
        resp = await client.patch(f"{API}/user/chat-channel-priority", json={"priority": []})
        assert resp.status_code == 422

    async def test_collapses_duplicates(self, client: AsyncClient) -> None:
        with patch(
            "app.api.v1.endpoints.user.set_chat_channel_priority",
            new_callable=AsyncMock,
        ) as save:
            resp = await client.patch(
                f"{API}/user/chat-channel-priority",
                json={"priority": ["telegram", "slack", "telegram"]},
            )
        assert resp.status_code == 200
        assert resp.json() == {"priority": ["telegram", "slack"]}
        assert save.await_args.args[1] == ["telegram", "slack"]


@pytest.mark.unit
class TestReadActivationSequence:
    async def test_reports_the_current_opt_out(self, client: AsyncClient) -> None:
        with patch(
            "app.api.v1.endpoints.user.get_opted_out",
            new_callable=AsyncMock,
            return_value=True,
        ):
            resp = await client.get(f"{API}/user/activation-sequence")
        assert resp.status_code == 200
        assert resp.json() == {"opted_out": True}
