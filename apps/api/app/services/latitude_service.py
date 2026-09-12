"""Latitude span scope for real agent turns. Never raises; missing key is a silent no-op."""

from latitude_telemetry import capture
from latitude_telemetry.sdk.context import CaptureScope
from latitude_telemetry.sdk.types import ContextOptions

from app.config.settings import settings
from app.constants.agents import COMMS_AGENT_NAME
from shared.py.wide_events import log


def _configured() -> bool:
    return bool((settings.LATITUDE_API_KEY or "").strip())


def begin_turn(
    *,
    user_id: str,
    conversation_id: str,
    agent_name: str = COMMS_AGENT_NAME,
    properties: dict[str, str | bool | None] | None = None,
) -> CaptureScope | None:
    """Open a Latitude capture scope for this turn, or None when disabled/failing."""
    if not user_id or not _configured():
        return None
    try:
        metadata: dict[str, object] = {k: v for k, v in (properties or {}).items() if v is not None}
        options: ContextOptions = {
            "user_id": user_id,
            "session_id": conversation_id,
            "project": settings.LATITUDE_PROJECT,
            "metadata": metadata,
        }
        return capture.start(agent_name, options)
    except Exception as exc:
        log.warning(
            "latitude_begin_failed",
            error=str(exc),
            error_type=type(exc).__name__,
            conversation_id=conversation_id,
        )
        return None


def end_turn(scope: CaptureScope | None, *, error: Exception | None = None) -> None:
    """Close a Latitude capture scope. No-op when scope is None. Never raises."""
    if scope is None:
        return
    try:
        capture.end(scope, error)
    except Exception as exc:
        log.warning(
            "latitude_end_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )
