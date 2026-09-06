"""One fan-out for turn telemetry across Agnost, Latitude, and Laminar.

Both agent entry points (streaming chat, silent background) open the three
vendor scopes together and close them with one shared outcome mapping, so a
turn reads identically in every dashboard: cancelled counts as failure
everywhere, errors carry the same exception, properties match.
"""

from typing import TypedDict

from agnost import Interaction
from latitude_telemetry.sdk.context import CaptureScope

from app.constants.agents import COMMS_AGENT_NAME
from app.services import agnost_service, laminar_service, latitude_service
from app.services.laminar_service import TurnScope


class TurnCancelled(Exception):
    """A user-cancelled turn, reported as failure to every vendor."""


class TurnHandles(TypedDict):
    """One vendor scope per telemetry backend; any may be None when disabled."""

    agnost: Interaction | None
    latitude: CaptureScope | None
    laminar: TurnScope | None


def begin_turn_all(
    *,
    user_id: str,
    conversation_id: str,
    user_input: str,
    properties: dict[str, str | bool | None] | None = None,
) -> TurnHandles:
    """Open all three vendor scopes. Never raises (each service guards)."""
    props = dict(properties or {})
    return {
        "agnost": agnost_service.begin_turn(
            user_id=user_id,
            conversation_id=conversation_id,
            user_input=user_input,
            agent_name=COMMS_AGENT_NAME,
            properties=props,
        ),
        "latitude": latitude_service.begin_turn(
            user_id=user_id,
            conversation_id=conversation_id,
            agent_name=COMMS_AGENT_NAME,
            properties=props,
        ),
        "laminar": laminar_service.begin_turn(
            user_id=user_id,
            conversation_id=conversation_id,
            agent_name=COMMS_AGENT_NAME,
            properties=props,
        ),
    }


def end_turn_all(
    handles: TurnHandles | None,
    *,
    output: str,
    error: Exception | None = None,
    cancelled: bool = False,
) -> None:
    """Close all three scopes with one outcome. None handles is a no-op. Never raises."""
    if handles is None:
        return
    success = error is None and not cancelled
    trace_error = error if error is not None else (TurnCancelled() if cancelled else None)
    properties: dict[str, str | bool | None] = {
        "cancelled": cancelled,
        "has_error": error is not None,
    }
    agnost_service.end_turn(
        handles["agnost"], output=output, success=success, properties=properties
    )
    latitude_service.end_turn(handles["latitude"], error=trace_error)
    laminar_service.end_turn(handles["laminar"], error=trace_error)
