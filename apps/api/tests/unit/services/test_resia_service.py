"""Unit tests for the Resia service: validation, parsing, error mapping.

HTTP is faked at the transport seam (httpx.MockTransport) — the service's own
logic always runs. No network, no credentials.
"""

from collections.abc import Callable
from unittest.mock import patch

import httpx
import pytest

from app.services import resia_service
from app.services.resia_service import ResiaError, validate_us_ca_number

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _fake_resia_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(resia_service.settings, "RESIA_API_KEY", "test-key")
    monkeypatch.setattr(resia_service.settings, "RESIA_DEFAULT_CALL_AGENT_ID", "agent-1")


def _patched(handler: Callable[[httpx.Request], httpx.Response]):
    """Patch the HTTP seam: real service code, fake transport."""
    fake = httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=5)
    return patch.object(resia_service.httpx, "AsyncClient", lambda **kw: fake)


def _json_response(status: int, payload: object, headers: dict[str, str] | None = None):
    return httpx.Response(status, json=payload, headers=headers or {})


class TestValidateNumber:
    def test_accepts_us_number_with_separators(self):
        assert validate_us_ca_number("+1 415-555-0123") == "+14155550123"

    def test_rejects_non_e164(self):
        with pytest.raises(ValueError, match="E.164"):
            validate_us_ca_number("4155550123")

    def test_rejects_non_us_ca(self):
        with pytest.raises(ValueError, match=r"\+1.*only"):
            validate_us_ca_number("+918980112000")


class TestReadCall:
    def test_extracts_outcome_and_filters_transcript(self):
        call = resia_service._read_call(
            {
                "id": "call-1",
                "status": "completed",
                "analysis": {"outcome": "achieved", "summary": "Booked."},
                "transcript": [
                    {"role": "assistant", "content": "Hi"},
                    {"role": "user", "content": "Yes"},
                    {"role": "event", "content": "keypad"},
                ],
            }
        )
        assert call.outcome == "achieved"
        assert call.summary == "Booked."
        assert [(t.role, t.content) for t in call.transcript] == [
            ("assistant", "Hi"),
            ("user", "Yes"),
        ]

    def test_missing_analysis_stays_unresolved(self):
        call = resia_service._read_call({"id": "call-1", "status": "in_progress"})
        assert call.outcome is None
        assert call.transcript == []

    def test_failure_code_surfaces(self):
        call = resia_service._read_call(
            {"id": "call-1", "status": "error", "failure": {"code": "busy", "message": "Busy"}}
        )
        assert call.failure_code == "busy"

    def test_malformed_turn_fails_loud(self):
        with pytest.raises(ResiaError, match="bad_response"):
            resia_service._read_call(
                {"id": "call-1", "status": "completed", "transcript": ["garbage"]}
            )


class TestRequestErrors:
    async def test_rate_limit_carries_retry_after(self):
        def handler(request: httpx.Request):
            return _json_response(
                429,
                {"error": {"code": "rate_limited", "message": "Slow down"}},
                {"Retry-After": "7", "X-Request-ID": "req-1"},
            )

        with _patched(handler):
            with pytest.raises(ResiaError) as exc_info:
                await resia_service.get_call("call-1")
        assert exc_info.value.code == "rate_limited"
        assert exc_info.value.status == 429
        assert exc_info.value.retry_after_seconds == 7
        assert exc_info.value.request_id == "req-1"

    async def test_string_error_envelope_does_not_crash(self):
        def handler(request: httpx.Request):
            return _json_response(400, {"error": "oops"})

        with _patched(handler):
            with pytest.raises(ResiaError) as exc_info:
                await resia_service.get_call("call-1")
        assert exc_info.value.code == "request_failed"

    async def test_non_json_error_falls_back(self):
        def handler(request: httpx.Request):
            return httpx.Response(503, text="<html>down</html>")

        with _patched(handler):
            with pytest.raises(ResiaError) as exc_info:
                await resia_service.get_call("call-1")
        assert exc_info.value.code == "request_failed"
        assert exc_info.value.status == 503
