"""Laminar parent span for real agent turns.

``start_as_current_span`` (not the bare ``set_trace_*`` setters, which no-op
without an already-active span) nests the whole turn under one attributed
parent. Never raises; missing key is a silent no-op.
"""

from collections.abc import Sequence
from contextlib import AbstractContextManager

from lmnr import Laminar, LaminarSpan

from app.config.settings import settings
from app.constants.agents import COMMS_AGENT_NAME
from shared.py.wide_events import log

TurnScope = AbstractContextManager[LaminarSpan]
LaminarMetadata = dict[
    str, str | bool | int | float | Sequence[str] | Sequence[bool] | Sequence[int] | Sequence[float]
]


def _configured() -> bool:
    return bool((settings.LMNR_PROJECT_API_KEY or "").strip())


def begin_turn(
    *,
    user_id: str,
    conversation_id: str,
    agent_name: str = COMMS_AGENT_NAME,
    properties: dict[str, str | bool | None] | None = None,
) -> TurnScope | None:
    """Open a Laminar turn scope, or None when disabled/failing."""
    if not user_id or not _configured():
        return None
    try:
        # Filtered, not just annotated: the SDK's metadata type excludes None
        # while ours arrives nullable, so only real values are passed.
        metadata: LaminarMetadata = {k: v for k, v in (properties or {}).items() if v is not None}
        scope: TurnScope = Laminar.start_as_current_span(
            agent_name,
            user_id=user_id,
            session_id=conversation_id,
            metadata=metadata,
        )
        scope.__enter__()
        return scope
    except Exception as exc:
        log.warning(
            "laminar_begin_failed",
            error=str(exc),
            error_type=type(exc).__name__,
            conversation_id=conversation_id,
        )
        return None


def end_turn(scope: TurnScope | None, *, error: Exception | None = None) -> None:
    """Close a Laminar turn scope. No-op when scope is None. Never raises."""
    if scope is None:
        return
    try:
        if error is None:
            scope.__exit__(None, None, None)
        else:
            scope.__exit__(type(error), error, error.__traceback__)
    except Exception as exc:
        # A re-raise of the turn's own error means the scope surfaced it
        # instead of absorbing it — that error is already reported by the
        # caller, so only a *different* failure is worth logging here.
        if exc is not error:
            log.warning(
                "laminar_end_failed",
                error=str(exc),
                error_type=type(exc).__name__,
            )
