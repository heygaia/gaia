"""Resia voice-call and SMS client (server-held org credential).

One org balance covers all users; per-call attribution travels in
``client_reference`` (opaque ids only, never PII). All functions are
module-level async — no service classes.
"""

import re
from typing import TypeVar, cast
import uuid

import httpx
from pydantic import BaseModel, ValidationError

from app.config.settings import settings
from app.constants.resia import (
    E164_RE,
    MAX_SMS_RECIPIENTS,
    RESIA_BASE_URL,
    RESIA_TIMEOUT_SECONDS,
    SMS_MAX_CHARS,
    US_CA_PREFIX,
)
from app.schemas.resia_schemas import (
    CallOutcome,
    CallPlaced,
    CallRead,
    TextBatchPlaced,
    TextBatchRead,
    TextMessagePlaced,
    TranscriptTurn,
)
from shared.py.wide_events import log

_E164 = re.compile(E164_RE)

M = TypeVar("M", bound=BaseModel)

# The only outcomes our call agent's analysis_schema can produce.
_KNOWN_OUTCOMES: tuple[str, ...] = ("achieved", "partial", "not_achieved", "unclear")


class ResiaError(Exception):
    """A refused Resia request: machine-readable code plus request id."""

    def __init__(
        self,
        code: str,
        message: str,
        request_id: str | None = None,
        status: int = 0,
        retry_after_seconds: int | None = None,
    ):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.request_id = request_id
        self.status = status
        self.retry_after_seconds = retry_after_seconds


def _parse(model: type[M], data: object, what: str) -> M:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ResiaError("bad_response", f"Unparseable {what}: {exc}") from exc


def validate_us_ca_number(number: str) -> str:
    """Return the stripped number, or raise ValueError (Resia dials US/CA only)."""
    cleaned = number.strip().replace(" ", "").replace("-", "")
    if not _E164.match(cleaned):
        raise ValueError(f"Not E.164 (use +countrycode, e.g. +14155550123): {number}")
    if not cleaned.startswith(US_CA_PREFIX):
        raise ValueError(f"Resia dials US/Canada (+1) only: {number}")
    return cleaned


def _require_key() -> str:
    key: str | None = settings.RESIA_API_KEY
    if not key:
        raise RuntimeError("RESIA_API_KEY is not set — add it via Infisical/env")
    return key


def _require_agent() -> str:
    agent: str | None = settings.RESIA_DEFAULT_CALL_AGENT_ID
    if not agent:
        raise RuntimeError(
            "RESIA_DEFAULT_CALL_AGENT_ID is not set — provision one via POST /v1/call-agents"
        )
    return agent


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_require_key()}"}


async def _request(
    method: str, path: str, payload: dict[str, object] | None = None
) -> dict[str, object]:
    url = f"{RESIA_BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=RESIA_TIMEOUT_SECONDS) as client:
            response = await client.request(method, url, headers=_headers(), json=payload)
    except httpx.HTTPError as exc:
        raise ResiaError("unreachable", str(exc), None, 0) from exc
    request_id = response.headers.get("X-Request-ID")
    if response.status_code >= 400:
        code, message = "request_failed", response.text[:500]
        try:
            body = response.json()
            err = body.get("error", body) if isinstance(body, dict) else {}
            if not isinstance(err, dict):
                err = {}
            code = str(err.get("code", code))
            message = str(err.get("message", message))
        except ValueError:
            pass
        retry_after_seconds: int | None = None
        raw_retry = response.headers.get("Retry-After")
        if raw_retry is not None:
            try:
                retry_after_seconds = int(raw_retry)
            except ValueError:
                retry_after_seconds = None
        log.set(resia={"path": path, "status": response.status_code, "code": code})
        raise ResiaError(code, message, request_id, response.status_code, retry_after_seconds)
    data = response.json()
    if not isinstance(data, dict):
        raise ResiaError("bad_response", "Non-object response", request_id, 200)
    return data


def new_client_reference(user_id: str) -> str:
    return f"gaia-{user_id}-{uuid.uuid4().hex[:8]}"


async def place_call(
    to_phone_number: str,
    objective: str,
    on_behalf_of: str,
    user_id: str,
    client_reference: str | None = None,
    from_phone_number: str | None = None,
) -> CallPlaced:
    """Queue one outbound call; the call has NOT been dialled when this returns."""
    if not objective.strip():
        raise ValueError("objective is required")
    if not on_behalf_of.strip():
        raise ValueError("on_behalf_of is required")
    to_number = validate_us_ca_number(to_phone_number)
    sender = from_phone_number or settings.RESIA_DEFAULT_FROM_NUMBER
    if sender:
        sender = validate_us_ca_number(sender)
    payload: dict[str, object] = {
        "call_agent_id": _require_agent(),
        "to_phone_number": to_number,
        "inputs": {"objective": objective.strip(), "on_behalf_of": on_behalf_of.strip()},
        "client_reference": client_reference or new_client_reference(user_id),
    }
    if sender:
        payload["from_phone_number"] = sender
    data = await _request("POST", "/v1/calls", payload)
    placed = _parse(CallPlaced, data, "call acceptance")
    log.set(resia={"call_id": placed.call_id, "status": placed.status})
    return placed


def _read_call(data: dict[str, object]) -> CallRead:
    analysis = data.get("analysis")
    outcome: CallOutcome | None = None
    summary: str | None = None
    if isinstance(analysis, dict):
        raw_outcome = analysis.get("outcome")
        raw_summary = analysis.get("summary")
        if isinstance(raw_outcome, str) and raw_outcome in _KNOWN_OUTCOMES:
            outcome = cast(CallOutcome, raw_outcome)
        summary = str(raw_summary) if raw_summary is not None else None
    failure = data.get("failure")
    failure_code: str | None = None
    if isinstance(failure, dict) and failure.get("code") is not None:
        failure_code = str(failure["code"])
    raw_transcript = data.get("transcript")
    turns = (
        [_parse(TranscriptTurn, t, "transcript turn") for t in raw_transcript]
        if isinstance(raw_transcript, list)
        else []
    )
    spoken = [t for t in turns if t.role in ("assistant", "user")]
    return _parse(
        CallRead,
        {
            **data,
            "outcome": outcome,
            "summary": summary,
            "failure_code": failure_code,
            "transcript": spoken,
        },
        "call",
    )


async def get_call(call_id: str) -> CallRead:
    """Read one call. Terminal when status is completed/error/canceled."""
    return _read_call(await _request("GET", f"/v1/calls/{call_id}"))


async def send_text_batch(
    to_phone_numbers: list[str],
    text: str,
    user_id: str,
    from_phone_number: str | None = None,
) -> TextBatchPlaced:
    """Queue one SMS body to 1..N recipients from a single owned sender."""
    if not 1 <= len(to_phone_numbers) <= MAX_SMS_RECIPIENTS:
        raise ValueError(f"Send 1-{MAX_SMS_RECIPIENTS} recipients per call")
    if not 1 <= len(text) <= SMS_MAX_CHARS:
        raise ValueError(f"Message must be 1-{SMS_MAX_CHARS} chars")
    sender_raw = from_phone_number or settings.RESIA_DEFAULT_FROM_NUMBER
    if not sender_raw:
        raise ValueError(
            "No SMS sender: set RESIA_DEFAULT_FROM_NUMBER to an owned number, "
            "or pass from_phone_number. SMS also needs 10DLC brand+campaign."
        )
    sender = validate_us_ca_number(sender_raw)
    entries = [
        {
            "to_phone_number": validate_us_ca_number(n),
            "client_reference": new_client_reference(user_id),
        }
        for n in to_phone_numbers
    ]
    data = await _request(
        "POST",
        "/v1/text-message-batches",
        {"from_phone_number": sender, "text": text, "text_messages": entries},
    )
    batch = _parse(TextBatchPlaced, data, "text batch acceptance")
    log.set(resia={"batch_id": batch.batch_id, "total": len(batch.messages)})
    return batch


async def get_text_batch(batch_id: str) -> TextBatchRead:
    """Read one SMS batch's derived status, counts and total."""
    data = await _request("GET", f"/v1/text-message-batches/{batch_id}")
    return _parse(TextBatchRead, data, "text batch")


async def list_text_batch_messages(
    batch_id: str, cursor: str | None = None
) -> tuple[list[TextMessagePlaced], str | None]:
    """Return (page of messages, next_cursor) for one SMS batch."""
    path = f"/v1/text-message-batches/{batch_id}/text-messages"
    if cursor:
        path += f"?cursor={cursor}"
    data = await _request("GET", path)
    raw = data.get("items", [])
    messages = (
        [_parse(TextMessagePlaced, m, "text message") for m in raw] if isinstance(raw, list) else []
    )
    next_cursor = data.get("next_cursor")
    return messages, str(next_cursor) if next_cursor else None
