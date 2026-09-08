"""Unit tests for the Resia service: validation, parsing, error mapping.

HTTP is faked at the transport seam (httpx.MockTransport) — the service's own
logic always runs. No network, no credentials.
"""

from collections.abc import Callable
import json
from unittest.mock import patch

import httpx
import pytest

from app.services import resia_service
from app.services.resia_service import ResiaError, validate_us_ca_number


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
    async def test_extracts_outcome_and_filters_transcript(self):
        def handler(request: httpx.Request):
            return _json_response(
                200,
                {
                    "id": "call-1",
                    "status": "completed",
                    "created_at": "2026-09-08T17:57:38.921+00:00",
                    "call_agent_version_id": "v1",
                    "analysis": {"outcome": "achieved", "summary": "Booked."},
                    "transcript": [
                        {"role": "assistant", "content": "Hi"},
                        {"role": "user", "content": "Yes"},
                        {"role": "event", "content": "keypad"},
                    ],
                },
            )

        with _patched(handler):
            call = await resia_service.get_call("call-1")
        assert call.outcome == "achieved"
        assert call.summary == "Booked."
        assert [(t.role, t.content) for t in call.transcript] == [
            ("assistant", "Hi"),
            ("user", "Yes"),
        ]

    async def test_missing_analysis_stays_unresolved(self):
        def handler(request: httpx.Request):
            return _json_response(
                200,
                {
                    "id": "call-1",
                    "status": "in_progress",
                    "created_at": "2026-09-08T17:57:38.921+00:00",
                    "call_agent_version_id": "v1",
                },
            )

        with _patched(handler):
            call = await resia_service.get_call("call-1")
        assert call.outcome is None
        assert call.transcript == []

    async def test_failure_code_surfaces(self):
        def handler(request: httpx.Request):
            return _json_response(
                200,
                {
                    "id": "call-1",
                    "status": "error",
                    "created_at": "2026-09-08T17:57:38.921+00:00",
                    "call_agent_version_id": "v1",
                    "failure": {"code": "busy", "message": "Busy"},
                },
            )

        with _patched(handler):
            call = await resia_service.get_call("call-1")
        assert call.failure_code == "busy"

    async def test_malformed_turn_fails_loud(self):
        def handler(request: httpx.Request):
            return _json_response(
                200,
                {
                    "id": "call-1",
                    "status": "completed",
                    "created_at": "2026-09-08T17:57:38.921+00:00",
                    "call_agent_version_id": "v1",
                    "transcript": ["garbage"],
                },
            )

        with _patched(handler):
            with pytest.raises(ResiaError, match="bad_response"):
                await resia_service.get_call("call-1")


class TestPlaceCall:
    async def test_builds_agent_inputs_and_reference(self):
        bodies: list[object] = []

        def handler(request: httpx.Request):
            bodies.append(request.content)
            return _json_response(
                202,
                {
                    "id": "call-1",
                    "status": "queued",
                    "created_at": "2026-09-08T17:57:38.921+00:00",
                    "call_agent_version_id": "v1",
                },
            )

        with _patched(handler):
            placed = await resia_service.place_call(
                "+1 415-555-0123", "Book a table", "Alex", "user-1"
            )
        assert placed.call_id == "call-1"
        assert placed.status == "queued"
        assert isinstance(bodies[0], bytes)
        body = json.loads(bodies[0].decode())
        assert body["to_phone_number"] == "+14155550123"
        assert body["call_agent_id"] == "agent-1"
        assert body["inputs"] == {"objective": "Book a table", "on_behalf_of": "Alex"}
        assert str(body["client_reference"]).startswith("gaia-user-1-")

    async def test_blank_objective_rejected_before_network(self):
        bodies: list[object] = []

        def handler(request: httpx.Request):
            bodies.append(request.content)
            raise AssertionError("no request should fire")

        with _patched(handler):
            with pytest.raises(ValueError, match="objective is required"):
                await resia_service.place_call("+14155550123", "  ", "Alex", "user-1")
        assert bodies == []


class TestSendBatch:
    async def test_rejects_bad_counts_before_network(self):
        bodies: list[object] = []

        def handler(request: httpx.Request):
            bodies.append(request.content)
            raise AssertionError("no request should fire")

        with _patched(handler):
            with pytest.raises(ValueError, match="1-100"):
                await resia_service.send_text_batch([], "hi", "user-1")
            with pytest.raises(ValueError, match="1-1600"):
                await resia_service.send_text_batch(["+14155550123"], "", "user-1")
        assert bodies == []


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


class TestUnknownOutcome:
    async def test_unlisted_outcome_maps_to_none(self):
        def handler(request: httpx.Request):
            return _json_response(
                200,
                {
                    "id": "call-1",
                    "status": "completed",
                    "created_at": "2026-09-08T17:57:38.921+00:00",
                    "call_agent_version_id": "v1",
                    "analysis": {"outcome": "transcended", "summary": "Huh."},
                },
            )

        with _patched(handler):
            call = await resia_service.get_call("call-1")
        assert call.outcome is None
        assert call.summary == "Huh."
