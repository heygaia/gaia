"""The single executor-facing browser-automation tool.

The only place the browser host + Browser-Use are wired together. The executor
sees one tool, not the internals. The "do you want me to use a browser?"
confirmation is handled by the shared HIL system (``browser_task`` is registered
destructive). This tool composes the runner's seams: progress emission (SSE +
bots), cancellation (stream flag), and the mid-run live-view handoff. The
session context manager owns capacity limits, saved-login persistence, live-view
registration, and always releasing the browser context.
"""

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from functools import partial
from time import perf_counter
from typing import Annotated, Any
import uuid

from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import tool
from langgraph.config import get_stream_writer
from langgraph.types import StreamWriter

from app.config.settings import settings
from app.constants.browser import (
    BROWSER_TASK_EVENT,
    BROWSER_TOOL_CATEGORY,
    BrowserSessionStatus,
    HandoffStatus,
    SensitiveCategory,
)
from app.constants.log_tags import LogTag
from app.core.stream_manager import stream_manager
from app.decorators import with_doc, with_rate_limiting
from app.models.chat_models import ConversationSource, SourceCategory
from app.models.stream_events import ToolOutputPayload
from app.schemas.browser import (
    BrowserActionOutput,
    BrowserCardSnapshot,
    BrowserHandoffSnapshot,
    BrowserResultSnapshot,
    BrowserSessionSnapshot,
    BrowserStepSnapshot,
    HandoffOutcome,
    HandoffRequest,
)
from app.services.analytics_service import AnalyticsEvents, capture_event
from app.services.browser.bot_delivery import BotProgressDelivery
from app.services.browser.exceptions import BrowserConcurrencyLimit, BrowserUnavailableError
from app.services.browser.fingerprint import reset_fingerprint_seed, set_fingerprint_seed
from app.services.browser.handoff import await_handoff, create_pending_handoff
from app.services.browser.llm import build_browser_llm, resolve_use_vision
from app.services.browser.runner import (
    BrowserRunConfig,
    BrowserRunnerCallbacks,
    BrowserTaskRunner,
)
from app.services.browser.session import (
    BrowserHostSession,
    auto_resolve_handoff_on_navigation,
    browser_session,
    keep_session_alive,
)
from app.services.browser.tasks import BrowserTaskRecord, record_browser_task
from app.templates.docstrings.browser_tool_docs import BROWSER_TASK
from app.utils.agent_utils import (
    SubagentStartDetails,
    format_browser_action_entry,
    format_subagent_end_event,
    format_subagent_start_event,
)
from app.utils.background_tasks import spawn_background_task
from shared.py.wide_events import log

# Screenshots stream into the chat live, so the reply must never narrate them.
_NO_META = (
    "The step-by-step screenshots were already shown to the user in this chat, so do "
    "NOT mention screenshots, tools, steps, or 'browser vision' — speak only to the outcome."
)


def _agent_result_message(result: BrowserResultSnapshot) -> str:
    """Outcome-specific guidance for the assistant's reply — so it confirms a real
    result, owns a stop, or reports a failure, but never claims success it didn't get."""
    summary = result.summary.strip()
    if result.status == BrowserSessionStatus.COMPLETED and result.success:
        return (
            f"BROWSER TASK COMPLETED. What was accomplished: {summary or 'the task finished'}.\n\n"
            f"Reply with a short, natural confirmation of what you found or did. {_NO_META}"
        )
    if result.status == BrowserSessionStatus.CANCELLED:
        return (
            "BROWSER TASK STOPPED BY THE USER before it finished — it did NOT complete, so "
            "there is no result and you must not claim one.\n\n"
            f"Briefly acknowledge you've stopped and ask if they'd like you to try again or "
            f"do something else. {_NO_META}"
        )
    return (
        f"BROWSER TASK DID NOT COMPLETE. Last state: {summary or 'the task could not be finished'}.\n\n"
        f"Tell the user honestly and briefly that it couldn't be finished, and why if it's clear. "
        f"Do not fabricate a result. {_NO_META}"
    )


class _BrowserThreadMirror:
    """Mirrors the browser agent's own actions into the chat's tool thread.

    The card shows *what the browser is doing*; this shows *what it called* —
    every action with its arguments, grouped under one "Browser" row exactly
    like a subagent's tool calls. Before this the thread carried a single
    opaque ``browser_task`` row and the agent's real work was invisible.

    Stateful because only the session snapshot carries the session id, and the
    group id has to outlive it for the steps and the result that follow.
    """

    def __init__(self, writer: StreamWriter) -> None:
        self._writer = writer
        self._group_id: str | None = None
        self._started_at = perf_counter()
        # tool_call_ids of the action rows emitted, so an output only ever
        # lands on a row that exists (an errored step emits no rows).
        self._emitted_ids: set[str] = set()
        # Outputs can arrive before their row: the runner emits step rows through
        # a background task that first uploads the screenshot (~1s), while the
        # action results arrive synchronously on the very next Browser-Use hook.
        # Buffer an early output and flush it when its row lands, so ordering
        # between the two paths never drops a result.
        self._pending_outputs: dict[str, str] = {}

    def mirror(self, snapshot: BrowserCardSnapshot) -> None:
        if isinstance(snapshot, BrowserSessionSnapshot):
            self._open(snapshot)
        elif isinstance(snapshot, BrowserStepSnapshot):
            self._actions(snapshot)
        elif isinstance(snapshot, BrowserResultSnapshot):
            self._close()

    def _open(self, snapshot: BrowserSessionSnapshot) -> None:
        if self._group_id or not snapshot.session_id:
            return
        self._group_id = f"browser:{snapshot.session_id}"
        self._started_at = perf_counter()
        self._writer(
            {
                "subagent_start": format_subagent_start_event(
                    subagent_name="Browser",
                    agent_type="spawned",
                    subagent_id=self._group_id,
                    details=SubagentStartDetails(tool_category=BROWSER_TOOL_CATEGORY),
                )
            }
        )

    def _actions(self, snapshot: BrowserStepSnapshot) -> None:
        if not self._group_id:
            return
        for position, action in enumerate(snapshot.actions):
            tool_call_id = f"{self._group_id}:{snapshot.index}:{position}"
            self._emitted_ids.add(tool_call_id)
            self._writer(
                {
                    "tool_data": format_browser_action_entry(
                        name=action.name,
                        inputs=action.inputs,
                        target=action.target,
                        subagent_id=self._group_id,
                        tool_call_id=tool_call_id,
                    )
                }
            )
            buffered = self._pending_outputs.pop(tool_call_id, None)
            if buffered is not None:
                self._emit_output(tool_call_id, buffered)

    def results(self, step_index: int, outputs: list[BrowserActionOutput]) -> None:
        """Attach each executed action's result to its row, or buffer it until the
        row is emitted (the row's background task may still be uploading)."""
        if not self._group_id:
            return
        for output in outputs:
            tool_call_id = f"{self._group_id}:{step_index}:{output.position}"
            if tool_call_id in self._emitted_ids:
                self._emit_output(tool_call_id, output.output)
            else:
                self._pending_outputs[tool_call_id] = output.output

    def _emit_output(self, tool_call_id: str, output: str) -> None:
        payload = ToolOutputPayload(
            tool_call_id=tool_call_id,
            output=output,
            subagent_id=self._group_id,
        )
        self._writer({"tool_output": payload.model_dump(mode="json", exclude_none=True)})

    def _close(self) -> None:
        if not self._group_id:
            return
        self._writer(
            {
                "subagent_end": format_subagent_end_event(
                    subagent_id=self._group_id,
                    duration_ms=int((perf_counter() - self._started_at) * 1000),
                )
            }
        )
        self._group_id = None


@dataclass(frozen=True)
class _RunParams:
    """The run's identity and provenance, read once from the tool's config."""

    user_id: str
    conversation_id: str
    stream_id: str | None
    root_request_id: str | None
    source_category: str | None
    is_bot: bool
    conversation_source: ConversationSource | None
    task_source: str


def _run_params(configurable: Mapping[str, Any]) -> _RunParams:
    source_category = configurable.get("source_category")
    conv_source = ConversationSource.coerce(configurable.get("conversation_source"))
    return _RunParams(
        user_id=configurable.get("user_id") or "",
        # The USER-facing conversation, never the executor's derived `thread_id`
        # (`executor_<conv>`). A handoff registered here is resolved by a chat
        # reply ("done"/"stop") that arrives on the comms conversation id —
        # keying it by the prefixed thread_id would make that lookup miss and
        # the handoff never resume.
        conversation_id=(
            configurable.get("conversation_id") or configurable.get("thread_id") or ""
        ),
        stream_id=configurable.get("stream_id"),
        root_request_id=configurable.get("root_request_id"),
        source_category=source_category,
        is_bot=source_category == SourceCategory.BOT.value,
        conversation_source=conv_source,
        task_source=conv_source.value if conv_source else "",
    )


def _build_bot_delivery(params: _RunParams) -> BotProgressDelivery | None:
    if not (params.is_bot and params.user_id and params.conversation_id):
        return None
    if params.conversation_source is None:
        return None
    return BotProgressDelivery(
        platform=params.conversation_source,
        user_id=params.user_id,
        conversation_id=params.conversation_id,
        stream_screenshots=settings.BROWSER_USE_STREAM_SCREENSHOTS,
    )


async def _deliver_snapshot_to_bot(
    bot_delivery: BotProgressDelivery, snapshot: BrowserCardSnapshot
) -> None:
    """Best-effort mirror of a card to the bot platform. The card has already
    been written to the chat, so a messaging/queue outage is logged and
    swallowed — never a reason to abort the in-flight browser run."""
    try:
        if isinstance(snapshot, BrowserStepSnapshot):
            await bot_delivery.step(snapshot)
        elif isinstance(snapshot, BrowserResultSnapshot):
            await bot_delivery.result(snapshot)
        elif isinstance(snapshot, BrowserHandoffSnapshot):
            await bot_delivery.handoff(snapshot)
        elif isinstance(snapshot, BrowserSessionSnapshot):
            await bot_delivery.session(snapshot)
    except Exception as exc:
        log.error(
            f"{LogTag.BROWSER} Bot delivery failed; continuing browser task",
            error_type=type(exc).__name__,
            browser={"snapshot_type": type(snapshot).__name__},
        )


class _ProgressEmitter:
    """Streams each card snapshot into the chat and mirrors it to the bot
    platform, recording the CDN screenshots and captions the history recap
    reads back once the run finishes."""

    def __init__(
        self,
        writer: StreamWriter,
        thread_mirror: _BrowserThreadMirror,
        bot_delivery: BotProgressDelivery | None,
    ) -> None:
        self._writer = writer
        self._thread_mirror = thread_mirror
        self._bot_delivery = bot_delivery
        # Captions for the recap ("what's going on" per step), keyed by step index.
        self.step_goals: dict[int, str] = {}
        # Only the screenshots that actually reached the CDN. A step whose upload
        # failed falls back to an inline data URL, which must not be stored as a
        # history frame — it would render as a permanently broken image.
        self.step_shots: dict[int, str] = {}

    async def emit(self, snapshot: BrowserCardSnapshot) -> None:
        self._writer({BROWSER_TASK_EVENT: snapshot.model_dump(mode="json")})
        self._thread_mirror.mirror(snapshot)
        if isinstance(snapshot, BrowserStepSnapshot):
            if snapshot.goal:
                self.step_goals[snapshot.index] = snapshot.goal
            if snapshot.screenshot and snapshot.screenshot.startswith("http"):
                self.step_shots[snapshot.index] = snapshot.screenshot
        if self._bot_delivery is not None:
            await _deliver_snapshot_to_bot(self._bot_delivery, snapshot)


def _handoff_snapshot(
    handoff_id: str,
    req: HandoffRequest,
    session: BrowserHostSession,
    status: HandoffStatus,
) -> BrowserHandoffSnapshot:
    return BrowserHandoffSnapshot(
        handoff_id=handoff_id,
        category=req.category,
        reason=req.reason,
        session_id=session.session_id,
        live_view_url=session.live_view_url,
        status=status,
    )


def _spawn_handoff_watchers(
    handoff_id: str, req: HandoffRequest, session_id: str, user_id: str
) -> list[asyncio.Task[Any]]:
    # The paused session produces no CDP/live-view traffic, so keep its idle
    # clock fresh until the user decides — otherwise the host reaps the browser
    # they were asked to come back to.
    watchers = [
        spawn_background_task(keep_session_alive(session_id), name="browser_handoff_keepalive")
    ]
    # A login handoff can auto-complete when the page navigates off the sign-in
    # URL — the user just signs in, no extra tap. Only for credentials; a
    # payment/confirmation has no such signal.
    if req.category == SensitiveCategory.CREDENTIALS:
        watchers.append(
            spawn_background_task(
                auto_resolve_handoff_on_navigation(handoff_id, session_id, user_id),
                name="browser_handoff_autoresolve",
            )
        )
    return watchers


async def _run_handoff(
    req: HandoffRequest,
    *,
    emit: Callable[[BrowserCardSnapshot], Awaitable[None]],
    session: BrowserHostSession,
    user_id: str,
    conversation_id: str,
) -> HandoffOutcome:
    """Pause the run and hand the user a live view to complete the step
    themselves. Returns the outcome (completed with optional note, cancelled,
    or timed out) so the loop resumes natively."""
    handoff_id = uuid.uuid4().hex
    await create_pending_handoff(handoff_id, user_id, conversation_id, req.reason)
    await emit(_handoff_snapshot(handoff_id, req, session, HandoffStatus.PENDING))
    watchers = _spawn_handoff_watchers(handoff_id, req, session.session_id, user_id)
    try:
        outcome = await await_handoff(handoff_id, settings.BROWSER_USE_HANDOFF_TIMEOUT_SECONDS)
    finally:
        for watcher in watchers:
            watcher.cancel()
    await emit(_handoff_snapshot(handoff_id, req, session, outcome.status))
    return outcome


def _persist_run_outcome(
    params: _RunParams,
    *,
    task: str,
    session_id: str,
    result: BrowserResultSnapshot,
    run_t0: float,
    emitter: _ProgressEmitter,
) -> None:
    """Record analytics + the browser-history row for a finished run.

    Graph-background execution has no authenticated request context, so the id
    must be explicit or the event lands on an anonymous profile (see analytics
    conventions in CLAUDE.md).
    """
    if not params.user_id:
        return
    capture_event(
        params.user_id,
        AnalyticsEvents.BROWSER_TASK_FINISHED,
        {
            "status": result.status.value,
            "success": result.success,
            "steps": result.steps,
            "duration_ms": round((perf_counter() - run_t0) * 1000),
            "source": params.source_category or "web",
        },
    )
    # Best-effort background write: a completed task must still return its result
    # even if history persistence hiccups.
    spawn_background_task(
        record_browser_task(
            BrowserTaskRecord(
                user_id=params.user_id,
                conversation_id=params.conversation_id,
                task=task,
                session_id=session_id,
                source=params.task_source,
            ),
            result,
            step_goals=[emitter.step_goals.get(i, "") for i in range(1, result.steps + 1)],
            step_screenshots=[emitter.step_shots.get(i, "") for i in range(1, result.steps + 1)],
        ),
        name="record_browser_task",
    )


@tool
@with_rate_limiting("browser_task")
@with_doc(BROWSER_TASK)
async def browser_task(
    config: RunnableConfig,
    task: Annotated[str, "Clear, self-contained description of what to do in the browser."],
    start_url: Annotated[str | None, "Optional URL to open first."] = None,
) -> str:
    """Drive a browser task end to end: allocate a session, run the agent loop,
    and stream progress/result cards. Returns the outcome guidance message the
    executor surfaces to the user (never a fabricated success).
    """
    params = _run_params(config.get("configurable", {}))
    log.set(browser={"operation": "task", "source_category": params.source_category})

    if not settings.BROWSER_USE_ENABLED:
        return "Browser automation is currently disabled."

    writer = get_stream_writer()
    thread_mirror = _BrowserThreadMirror(writer)
    emitter = _ProgressEmitter(writer, thread_mirror, _build_bot_delivery(params))

    async def is_cancelled() -> bool:
        """Check whether the user cancelled this task mid-run (via the card or
        chat), so the agent loop can stop early instead of finishing unprompted.
        """
        return bool(params.stream_id) and await stream_manager.is_cancelled(params.stream_id)

    try:
        llm = build_browser_llm()
    except BrowserUnavailableError as exc:
        log.warning(f"{LogTag.BROWSER} Browser LLM unavailable", error_type=type(exc).__name__)
        return f"I can't use the browser right now: {exc}"

    # Pin this run's canvas/audio fingerprint to the user, so the same person
    # always presents the same device rather than a new one per task.
    seed_token = set_fingerprint_seed(params.user_id)

    full_task = task if not start_url else f"{task}\n\nStart at: {start_url}"
    use_vision = await resolve_use_vision()

    try:
        async with browser_session(user_id=params.user_id, start_url=start_url) as session:
            log.set(browser={"session_id": session.session_id})

            runner = BrowserTaskRunner(
                session=session,
                llm=llm,
                callbacks=BrowserRunnerCallbacks(
                    emit=emitter.emit,
                    request_handoff=partial(
                        _run_handoff,
                        emit=emitter.emit,
                        session=session,
                        user_id=params.user_id,
                        conversation_id=params.conversation_id,
                    ),
                    is_cancelled=is_cancelled,
                    action_results=thread_mirror.results,
                ),
                config=BrowserRunConfig(
                    max_steps=settings.BROWSER_USE_MAX_STEPS,
                    max_actions_per_step=settings.BROWSER_USE_MAX_ACTIONS_PER_STEP,
                    task_timeout_seconds=settings.BROWSER_USE_TASK_TIMEOUT_SECONDS,
                    step_timeout_seconds=settings.BROWSER_USE_STEP_TIMEOUT_SECONDS,
                    handoff_timeout_seconds=settings.BROWSER_USE_HANDOFF_TIMEOUT_SECONDS,
                    stream_screenshots=settings.BROWSER_USE_STREAM_SCREENSHOTS,
                    use_vision=use_vision,
                    solve_captcha=settings.BROWSER_USE_SOLVE_CAPTCHA,
                    flash_mode=settings.BROWSER_USE_FLASH_MODE,
                ),
                user_id=params.user_id or None,
                root_request_id=params.root_request_id,
            )
            run_t0 = perf_counter()
            result = await runner.run(full_task)
            _persist_run_outcome(
                params,
                task=task,
                session_id=session.session_id,
                result=result,
                run_t0=run_t0,
                emitter=emitter,
            )
            return _agent_result_message(result)
    except BrowserConcurrencyLimit as exc:
        return str(exc)
    except BrowserUnavailableError as exc:
        log.warning(f"{LogTag.BROWSER} Browser session unavailable", error_type=type(exc).__name__)
        await emitter.emit(
            BrowserResultSnapshot(
                status=BrowserSessionStatus.FAILED, success=False, summary=str(exc)
            )
        )
        return f"I couldn't start the browser: {exc}"
    finally:
        reset_fingerprint_seed(seed_token)
