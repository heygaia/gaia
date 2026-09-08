"""Resia voice-call and SMS client (server-held org credential).

One org balance covers all users; per-call attribution travels in
``client_reference`` (opaque ids only, never PII). All functions are
module-level async — no service classes.
"""

import re
import uuid

import httpx
from pydantic import ValidationError

from app.config.settings import settings
from app.constants.resia import (
    E164_RE,
    RESIA_BASE_URL,
    RESIA_TIMEOUT_SECONDS,
    TERMINAL_CALL_STATUSES,
    US_CA_PREFIX,
)
from app.schemas.resia_schemas import (
    CallPlaced,
    CallRead,
    TextBatchPlaced,
    TextBatchRead,
    TextMessagePlaced,
    TranscriptTurn,
)
from shared.py.wide_events import log

_E164 = re.compile(E164_RE)


class ResiaError(Exception):
    """A refused Resia request: machine-readable code plus request id."""

    def __init__(self, code: str, message: str, request_id: str | None = None, status: int = 0):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.request_id = request_id
        self.status = status


def validate_us_ca_number(number: str) -> str:
    """Return the stripped number, or raise ValueError (Resia dials US/CA only)."""
    cleaned = number.strip().replace(" ", "").replace("-", "")
    if not _E164.match(cleaned):
        raise ValueError(f"Not E.164 (use +countrycode, e.g. +14155550123): {number}")
    if not cleaned.startswith(US_CA_PREFIX):
        raise ValueError(f"Resia dials US/Canada (+1) only: {number}")
    return cleaned


def is_configured() -> bool:
    return bool(settings.RESIA_API_KEY and settings.RESIA_DEFAULT_CALL_AGENT_ID)


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
            code = str(err.get("code", code))
            message = str(err.get("message", message))
        except ValueError:
            pass
        log.set(resia={"path": path, "status": response.status_code, "code": code})
        raise ResiaError(code, message, request_id, response.status_code)
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
    placed = CallPlaced.model_validate(data)
    log.set(resia={"call_id": placed.call_id, "status": placed.status})
    return placed


def _read_call(data: dict[str, object]) -> CallRead:
    analysis = data.get("analysis")
    outcome: str | None = None
    summary: str | None = None
    if isinstance(analysis, dict):
        raw_outcome = analysis.get("outcome")
        raw_summary = analysis.get("summary")
        outcome = str(raw_outcome) if raw_outcome is not None else None
        summary = str(raw_summary) if raw_summary is not None else None
    failure = data.get("failure")
    failure_code: str | None = None
    if isinstance(failure, dict) and failure.get("code") is not None:
        failure_code = str(failure["code"])
    raw_transcript = data.get("transcript")
    turns = (
        [TranscriptTurn.model_validate(t) for t in raw_transcript]
        if isinstance(raw_transcript, list)
        else []
    )
    spoken = [t for t in turns if t.role in ("assistant", "user")]
    return CallRead.model_validate(
        {
            **data,
            "outcome": outcome,
            "summary": summary,
            "failure_code": failure_code,
            "transcript": spoken,
        }
    )


async def get_call(call_id: str) -> CallRead:
    """Read one call. Terminal when status is completed/error/canceled."""
    return _read_call(await _request("GET", f"/v1/calls/{call_id}"))


def is_terminal(status: str) -> bool:
    return status in TERMINAL_CALL_STATUSES


async def send_text_batch(
    to_phone_numbers: list[str],
    text: str,
    user_id: str,
    from_phone_number: str | None = None,
) -> TextBatchPlaced:
    """Queue one SMS body to 1..N recipients from a single owned sender."""
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
    batch = TextBatchPlaced.model_validate(data)
    log.set(resia={"batch_id": batch.batch_id, "total": len(batch.messages)})
    return batch


async def get_text_batch(batch_id: str) -> TextBatchRead:
    """Read one SMS batch's derived status, counts and total."""
    try:
        data = await _request("GET", f"/v1/text-message-batches/{batch_id}")
        return TextBatchRead.model_validate(data)
    except ValidationError as exc:
        raise ResiaError("bad_response", f"Unparseable batch payload: {exc}") from exc


async def list_text_batch_messages(
    batch_id: str, cursor: str | None = None
) -> tuple[list[TextMessagePlaced], str | None]:
    """Return (page of messages, next_cursor) for one SMS batch."""
    path = f"/v1/text-message-batches/{batch_id}/text-messages"
    if cursor:
        path += f"?cursor={cursor}"
    data = await _request("GET", path)
    raw = data.get("items", [])
    messages = [TextMessagePlaced.model_validate(m) for m in raw] if isinstance(raw, list) else []
    next_cursor = data.get("next_cursor")
    return messages, str(next_cursor) if next_cursor else None


async def list_phone_numbers() -> list[str]:
    data = await _request("GET", "/v1/phone-numbers")
    raw = data.get("items", [])
    if not isinstance(raw, list):
        return []
    return [str(item["phone_number"]) for item in raw if isinstance(item, dict)]
