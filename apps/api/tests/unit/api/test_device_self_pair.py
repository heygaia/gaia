"""Unit tests for POST /device/self-pair (app/api/v1/endpoints/device.py).

The route runs for real against a mocked DB session (the seam one layer down),
so the shared device-creation path — cap, client stamping, token minting —
actually executes. Only the Postgres session and PostHog client are faked.
"""

import contextlib
from unittest.mock import patch

from httpx import AsyncClient
import pytest

from app.constants.device_bridge import MAX_ACTIVE_DEVICES_PER_USER
from app.models.device import DeviceStatus
from app.services.analytics_service import AnalyticsEvents
from app.services.device.device_auth import hash_refresh_token
from shared.py.wide_events import log as wide_log

pytestmark = pytest.mark.unit

BASE = "/api/v1/device"
_DB_SESSION = "app.services.device.device_service.get_db_session"
_CAPTURE = "app.api.v1.endpoints.device.capture_event"

_BODY = {
    "name": "My Mac",
    "platform": "macos",
    "client": "desktop",
    "daemon_version": "1.2.3",
}


class _FakeResult:
    def __init__(self, value: int) -> None:
        self._value = value

    def scalar_one(self) -> int:
        return self._value


class _FakeSession:
    """Captures the added Device and answers the active-device count query."""

    def __init__(self, active_count: int) -> None:
        self._active_count = active_count
        self.added: list[object] = []

    async def execute(self, _stmt: object) -> _FakeResult:
        return _FakeResult(self._active_count)

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        return None


def _fake_session_factory(session: _FakeSession):
    @contextlib.asynccontextmanager
    async def _cm():
        yield session

    return _cm


class TestSelfPairEndpoint:
    async def test_authenticated_creates_device_and_returns_token(
        self, client: AsyncClient, fake_user: dict
    ) -> None:
        session = _FakeSession(active_count=0)
        with (
            patch(_DB_SESSION, _fake_session_factory(session)),
            patch(_CAPTURE) as mock_capture,
            patch.object(wide_log, "audit") as mock_audit,
        ):
            resp = await client.post(f"{BASE}/self-pair", json=_BODY)

        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "My Mac"
        assert body["device_id"]
        assert body["refresh_token"]
        assert "user_code" not in body

        # The service really ran: exactly one Device row was created, stamped
        # with the request's client, owned by the authenticated user, active.
        assert len(session.added) == 1
        device = session.added[0]
        assert device.client == "desktop"
        assert device.user_id == fake_user["user_id"]
        assert device.status == DeviceStatus.ACTIVE
        # The returned plaintext token is the credential minted for this row.
        assert hash_refresh_token(body["refresh_token"]) == device.refresh_token_hash

        # Attributed to the resolved user id — not an anonymous context profile.
        mock_capture.assert_called_once_with(
            fake_user["user_id"],
            AnalyticsEvents.DEVICE_SELF_PAIRED,
            {"client": "desktop", "platform": "macos"},
        )

        credential_audits = [
            c
            for c in mock_audit.call_args_list
            if c.args and c.args[0] == "device credential issued"
        ]
        assert len(credential_audits) == 1
        audit_kwargs = credential_audits[0].kwargs
        assert audit_kwargs["actor"] == fake_user["user_id"]
        assert audit_kwargs["resource"] == body["device_id"]
        assert audit_kwargs["flow"] == "self_pair"

    async def test_unauthenticated_returns_401(self, unauthed_client: AsyncClient) -> None:
        resp = await unauthed_client.post(f"{BASE}/self-pair", json=_BODY)
        assert resp.status_code == 401

    async def test_over_active_device_cap_returns_409(self, client: AsyncClient) -> None:
        session = _FakeSession(active_count=MAX_ACTIVE_DEVICES_PER_USER)
        with (
            patch(_DB_SESSION, _fake_session_factory(session)),
            patch(_CAPTURE) as mock_capture,
        ):
            resp = await client.post(f"{BASE}/self-pair", json=_BODY)

        assert resp.status_code == 409
        # Rejected before the row was inserted; no analytics on a failed pair.
        assert session.added == []
        mock_capture.assert_not_called()
