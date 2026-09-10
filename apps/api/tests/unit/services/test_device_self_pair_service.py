"""Unit tests for the shared device-creation path (device_service._create_device).

Proves the per-user active-device cap fires identically from BOTH entry points
(self_pair_device and approve_pairing), and that the browser-approval path leaves
``client`` NULL while self-pair stamps it. The Postgres session and Redis are the
only fakes — the real service logic runs.
"""

import contextlib
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.device_bridge import MAX_ACTIVE_DEVICES_PER_USER
from app.models.device import DeviceStatus
from app.services.device import device_service
from app.services.device.device_auth import hash_refresh_token
from app.utils.errors import AppError

pytestmark = pytest.mark.unit

_DB_SESSION = "app.services.device.device_service.get_db_session"
_USER = "507f1f77bcf86cd799439011"


class _FakeResult:
    def __init__(self, value: int) -> None:
        self._value = value

    def scalar_one(self) -> int:
        return self._value


class _FakeSession:
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


class TestSelfPairDevice:
    async def test_stamps_client_and_mints_matching_token(self) -> None:
        session = _FakeSession(active_count=0)
        with patch(_DB_SESSION, _fake_session_factory(session)):
            device_id, refresh_token = await device_service.self_pair_device(
                _USER, "My Mac", "macos", "desktop", "1.2.3"
            )

        assert device_id
        assert len(session.added) == 1
        device = session.added[0]
        assert device.user_id == _USER
        assert device.client == "desktop"
        assert device.platform == "macos"
        assert device.status == DeviceStatus.ACTIVE
        # The returned plaintext token is exactly the credential stored (hashed).
        assert hash_refresh_token(refresh_token) == device.refresh_token_hash

    async def test_cap_rejects_self_pair(self) -> None:
        session = _FakeSession(active_count=MAX_ACTIVE_DEVICES_PER_USER)
        with patch(_DB_SESSION, _fake_session_factory(session)):
            with pytest.raises(AppError) as exc:
                await device_service.self_pair_device(_USER, "My Mac", "macos", "desktop", None)
        assert exc.value.status_code == 409
        assert session.added == []


class TestApprovePairingSharedCap:
    async def test_stamps_null_client(self) -> None:
        session = _FakeSession(active_count=0)
        pending = {
            "device_code": "dc",
            "name": "CLI box",
            "platform": "linux",
            "daemon_version": "0.1",
        }
        with (
            patch(_DB_SESSION, _fake_session_factory(session)),
            patch.object(
                device_service, "lookup_pending_by_user_code", AsyncMock(return_value=pending)
            ),
            patch.object(device_service, "set_cache", AsyncMock(return_value=True)),
            patch.object(device_service, "get_and_delete_cache", AsyncMock(return_value=None)),
        ):
            device_id, name = await device_service.approve_pairing(_USER, "GAIA-7F3K")

        assert device_id
        assert name == "CLI box"
        assert len(session.added) == 1
        # CLI-paired devices keep client NULL for now.
        assert session.added[0].client is None

    async def test_same_cap_rejects_approve_pairing(self) -> None:
        session = _FakeSession(active_count=MAX_ACTIVE_DEVICES_PER_USER)
        pending = {"device_code": "dc", "name": "CLI box", "platform": "linux"}
        with (
            patch(_DB_SESSION, _fake_session_factory(session)),
            patch.object(
                device_service, "lookup_pending_by_user_code", AsyncMock(return_value=pending)
            ),
            patch.object(device_service, "set_cache", AsyncMock(return_value=True)),
            patch.object(device_service, "get_and_delete_cache", AsyncMock(return_value=None)),
        ):
            with pytest.raises(AppError) as exc:
                await device_service.approve_pairing(_USER, "GAIA-7F3K")

        assert exc.value.status_code == 409
        assert session.added == []
