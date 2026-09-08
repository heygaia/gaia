import asyncio
from typing import Annotated, NotRequired, TypedDict

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

from app.constants.log_tags import LogTag
from app.constants.resia import MAX_SMS_RECIPIENTS, SMS_MAX_CHARS
from app.decorators import with_doc, with_rate_limiting
from app.services import resia_service
from app.services.analytics_service import AnalyticsEvents
from app.templates.docstrings.resia_tool_docs import (
    GET_PHONE_CALL_STATUS,
    GET_SMS_STATUS,
    PLACE_PHONE_CALL,
    SEND_SMS,
)
from app.utils.analytics import track
from app.utils.chat_utils import get_user_id_from_config
from shared.py.wide_events import log


class PhoneCallResult(TypedDict):
    """``place_phone_call`` / ``get_phone_call_status``."""

    call_id: str
    status: str
    to_phone_number: NotRequired[str | None]
    outcome: NotRequired[str | None]
    summary: NotRequired[str | None]
    duration_secs: NotRequired[float | None]
    charged_cents: NotRequired[int | None]
    failure_code: NotRequired[str | None]
    transcript: NotRequired[list[dict[str, str]]]
    error: NotRequired[str]


class SmsResult(TypedDict):
    """``send_sms`` / ``get_sms_status``."""

    batch_id: str
    status: NotRequired[str]
    recipient_count: NotRequired[int]
    messages: NotRequired[list[dict[str, str]]]
    rejected: NotRequired[list[dict[str, str]]]
    counts: NotRequired[dict[str, int]]
    total: NotRequired[int]
    error: NotRequired[str]


def _resia_hint(error: resia_service.ResiaError) -> str:
    if error.code == "sender_not_registered":
        return (
            "SMS sender is not 10DLC-registered: register the 10DLC brand, "
            "activate a campaign, and attach the sender number first."
        )
    return f"{error.code}: {error.message}"


@tool
@with_rate_limiting("phone_call_operations")
@with_doc(PLACE_PHONE_CALL)
async def place_phone_call(
    config: RunnableConfig,
    to_phone_number: Annotated[str, "Destination in E.164, e.g. +14155550123 (US/CA only)"],
    objective: Annotated[str, "What the call should accomplish, in plain language"],
    on_behalf_of: Annotated[str, "Person the agent says it is calling for"],
    from_phone_number: Annotated[str | None, "Owned sender override"] = None,
    client_reference: Annotated[str | None, "Opaque dedupe label"] = None,
) -> PhoneCallResult:
    """Place a real outbound phone call."""
    try:
        log.set(tool={"name": "place_phone_call", "action": "place"})
        user_id = get_user_id_from_config(config)
        if not user_id:
            return {"error": "User authentication required", "call_id": "", "status": "error"}
        if not objective.strip() or not on_behalf_of.strip():
            return {
                "error": "objective and on_behalf_of are required",
                "call_id": "",
                "status": "error",
            }

        placed = await resia_service.place_call(
            to_phone_number,
            objective,
            on_behalf_of,
            user_id,
            client_reference,
            from_phone_number,
        )
        card: PhoneCallResult = {
            "call_id": placed.call_id,
            "status": placed.status,
            "to_phone_number": to_phone_number,
        }
        writer = get_stream_writer()
        writer({"phone_call_data": card})
        track(
            user_id,
            AnalyticsEvents.PHONE_CALL_PLACED,
            {"call_id": placed.call_id, "status": placed.status},
        )
        log.set(tool={"name": "place_phone_call", "call_id": placed.call_id})
        return card
    except (resia_service.ResiaError, ValueError, RuntimeError) as e:
        log.error(f"{LogTag.TOOL} Error placing phone call", error_type=type(e).__name__)
        hint = _resia_hint(e) if isinstance(e, resia_service.ResiaError) else str(e)
        return {"error": hint, "call_id": "", "status": "error"}


@tool
@with_rate_limiting("phone_call_operations")
@with_doc(GET_PHONE_CALL_STATUS)
async def get_phone_call_status(
    config: RunnableConfig,  # noqa: ARG001 -- framework contract
    call_id: Annotated[str, "The call_id place_phone_call returned"],
) -> PhoneCallResult:
    """Read one call's status and, when done, its result."""
    try:
        log.set(tool={"name": "get_phone_call_status", "action": "read"})
        call = await resia_service.get_call(call_id)
        result: PhoneCallResult = {
            "call_id": call.call_id,
            "status": call.status,
            "to_phone_number": call.to_phone_number,
            "outcome": call.outcome,
            "summary": call.summary,
            "duration_secs": call.duration_secs,
            "charged_cents": call.charged_cents,
            "failure_code": call.failure_code,
            "transcript": [t.model_dump(mode="json") for t in call.transcript],
        }
        return result
    except (resia_service.ResiaError, RuntimeError) as e:
        log.error(f"{LogTag.TOOL} Error reading phone call", error_type=type(e).__name__)
        return {"error": str(e), "call_id": call_id, "status": "error"}


@tool
@with_rate_limiting("sms_operations")
@with_doc(SEND_SMS)
async def send_sms(
    config: RunnableConfig,
    to_phone_numbers: Annotated[list[str], "Destinations in E.164 (max 100)"],
    message: Annotated[str, "The one body every recipient gets"],
    from_phone_number: Annotated[str | None, "Owned sender override"] = None,
) -> SmsResult:
    """Send a real SMS to 1-100 recipients."""
    try:
        log.set(tool={"name": "send_sms", "action": "send"})
        user_id = get_user_id_from_config(config)
        if not user_id:
            return {"error": "User authentication required", "batch_id": ""}
        if not 1 <= len(to_phone_numbers) <= MAX_SMS_RECIPIENTS:
            return {
                "error": f"Send 1-{MAX_SMS_RECIPIENTS} recipients per call",
                "batch_id": "",
            }
        if not 1 <= len(message) <= SMS_MAX_CHARS:
            return {
                "error": f"Message must be 1-{SMS_MAX_CHARS} chars",
                "batch_id": "",
            }

        batch = await resia_service.send_text_batch(
            to_phone_numbers, message, user_id, from_phone_number
        )
        result: SmsResult = {
            "batch_id": batch.batch_id,
            "status": batch.status,
            "recipient_count": len(batch.messages),
            "messages": [
                {
                    "text_message_id": m.text_message_id,
                    "to_phone_number": m.to_phone_number,
                    "status": m.status,
                }
                for m in batch.messages
            ],
            "rejected": [
                {"to_phone_number": r.to_phone_number, "reason": r.reason} for r in batch.rejected
            ],
        }
        writer = get_stream_writer()
        writer({"sms_data": result})
        track(
            user_id,
            AnalyticsEvents.SMS_SENT,
            {
                "batch_id": batch.batch_id,
                "recipient_count": len(batch.messages),
                "rejected_count": len(batch.rejected),
            },
        )
        log.set(tool={"name": "send_sms", "batch_id": batch.batch_id})
        return result
    except (resia_service.ResiaError, ValueError, RuntimeError) as e:
        log.error(f"{LogTag.TOOL} Error sending SMS", error_type=type(e).__name__)
        hint = _resia_hint(e) if isinstance(e, resia_service.ResiaError) else str(e)
        return {"error": hint, "batch_id": ""}


@tool
@with_rate_limiting("sms_operations")
@with_doc(GET_SMS_STATUS)
async def get_sms_status(
    config: RunnableConfig,  # noqa: ARG001 -- framework contract
    batch_id: Annotated[str, "The batch_id send_sms returned"],
) -> SmsResult:
    """Read one SMS batch's delivery progress."""
    try:
        log.set(tool={"name": "get_sms_status", "action": "read"})
        batch, (messages, _) = await asyncio.gather(
            resia_service.get_text_batch(batch_id),
            resia_service.list_text_batch_messages(batch_id),
        )
        return {
            "batch_id": batch_id,
            "status": batch.status,
            "counts": batch.counts.model_dump(mode="json"),
            "total": batch.total,
            "messages": [
                {
                    "text_message_id": m.text_message_id,
                    "to_phone_number": m.to_phone_number,
                    "status": m.status,
                }
                for m in messages
            ],
        }
    except (resia_service.ResiaError, RuntimeError) as e:
        log.error(f"{LogTag.TOOL} Error reading SMS status", error_type=type(e).__name__)
        return {"error": str(e), "batch_id": batch_id}


tools = [place_phone_call, get_phone_call_status, send_sms, get_sms_status]
