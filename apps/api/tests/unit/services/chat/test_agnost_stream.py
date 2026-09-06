"""Turn telemetry on the streaming chat path.

Every surface (web, desktop, mobile, bots, voice) funnels through
``run_chat_stream_background``, so the fan-out opened there must carry the
real user id, conversation id, and input, and close with the real output and
one coherent outcome — and a telemetry failure must never break the turn.
"""

from collections.abc import AsyncGenerator, Iterator
import contextlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.message_models import MessageRequestWithHistory
from app.services.chat.stream import run_chat_stream_background


@pytest.fixture
def test_user() -> dict:
    return {"user_id": "user_abc", "email": "tester@example.com"}


@pytest.fixture
def existing_conv_body() -> MessageRequestWithHistory:
    return MessageRequestWithHistory(
        message="Follow-up",
        messages=[{"role": "user", "content": "Follow-up"}],
        conversation_id="conv_existing_123",
    )


async def _done_only_stream() -> AsyncGenerator[str, None]:
    yield "data: [DONE]\n\n"


async def _text_then_nostream(text: str, complete: str) -> AsyncGenerator[str, None]:
    yield f"data: {json.dumps({'response': text})}\n\n"
    yield f"nostream: {json.dumps({'complete_message': complete})}"
    yield "data: [DONE]\n\n"


def _make_stream_manager_mock(is_cancelled: bool = False) -> MagicMock:
    m = MagicMock()
    m.publish_chunk = AsyncMock()
    m.is_cancelled = AsyncMock(return_value=is_cancelled)
    m.update_progress = AsyncMock()
    m.complete_stream = AsyncMock()
    m.set_error = AsyncMock()
    m.cleanup = AsyncMock()
    m.get_progress = AsyncMock(return_value=None)
    return m


@contextlib.contextmanager
def _patch_stream_manager(sm: MagicMock) -> Iterator[MagicMock]:
    with contextlib.ExitStack() as stack:
        for path in (
            "app.services.chat.stream.stream_manager",
            "app.services.chat.chunks.stream_manager",
            "app.services.chat.state.stream_manager",
            "app.services.chat.artifact_forwarder.stream_manager",
            "app.utils.stream_publishers.stream_manager",
        ):
            stack.enter_context(patch(path, sm))
        yield sm


def _usage_callback_class() -> MagicMock:
    return MagicMock(return_value=MagicMock(usage_metadata={}))


@pytest.fixture(autouse=True)
def _quiet_turn() -> Iterator[None]:
    """Stub the turn's side channels so tests exercise telemetry only."""
    with (
        patch(
            "app.services.chat.stream.resolve_pending_from_message",
            new=AsyncMock(return_value=None),
        ),
        patch("app.services.chat.artifact_forwarder.redis_cache.redis", None),
        # PostHog capture is a separate seam with its own tests; the provider
        # registry is ambient process state, so a real call here would couple
        # these tests to whatever registered "posthog" first (or raise when
        # nothing did). The telemetry assertions below are what this file owns.
        patch("app.services.chat.stream.capture_event", new=MagicMock()),
    ):
        yield


async def _run_turn(
    sm: MagicMock,
    body: MessageRequestWithHistory,
    user: dict,
    conversation_id: str,
    agent_stream: AsyncGenerator[str, None],
) -> None:
    with (
        _patch_stream_manager(sm),
        patch(
            "app.services.chat.stream.call_agent",
            new=AsyncMock(return_value=agent_stream),
        ),
        patch(
            "app.services.chat.stream.save_conversation_async",
            new=AsyncMock(),
        ),
        patch("app.services.chat.stream.UsageMetadataCallbackHandler", _usage_callback_class()),
    ):
        await run_chat_stream_background(
            stream_id="stream_agnost",
            body=body,
            user=user,
            conversation_id=conversation_id,
        )


@pytest.mark.unit
class TestTurnTelemetry:
    async def test_success_opens_and_closes_with_real_ids_and_text(
        self, test_user, existing_conv_body
    ):
        sm = _make_stream_manager_mock()
        with (
            patch("app.services.agnost_service.begin_turn") as mock_begin,
            patch("app.services.agnost_service.end_turn") as mock_agnost_end,
            patch("app.services.latitude_service.end_turn") as mock_lat_end,
            patch("app.services.laminar_service.end_turn") as mock_lam_end,
        ):
            await _run_turn(
                sm,
                existing_conv_body,
                test_user,
                "conv_existing_123",
                _text_then_nostream("Follow", "Follow-up complete"),
            )

        mock_begin.assert_called_once()
        begin_kwargs = mock_begin.call_args.kwargs
        assert begin_kwargs["user_id"] == "user_abc"
        assert begin_kwargs["conversation_id"] == "conv_existing_123"
        assert begin_kwargs["user_input"] == "Follow-up"

        mock_agnost_end.assert_called_once()
        end_kwargs = mock_agnost_end.call_args.kwargs
        assert end_kwargs["output"] == "Follow-up complete"
        assert end_kwargs["success"] is True
        assert end_kwargs["properties"]["cancelled"] is False
        # One outcome everywhere: no error reaches any vendor on success.
        assert mock_lat_end.call_args.kwargs["error"] is None
        assert mock_lam_end.call_args.kwargs["error"] is None

    async def test_agent_error_closes_with_error(self, test_user, existing_conv_body):
        sm = _make_stream_manager_mock()

        async def _failing_stream() -> AsyncGenerator[str, None]:
            if False:  # pragma: no cover
                yield ""
            raise RuntimeError("provider down")

        with (
            patch("app.services.agnost_service.end_turn") as mock_agnost_end,
            patch("app.services.latitude_service.end_turn") as mock_lat_end,
            patch("app.services.laminar_service.end_turn") as mock_lam_end,
        ):
            await _run_turn(
                sm, existing_conv_body, test_user, "conv_existing_123", _failing_stream()
            )

        assert mock_agnost_end.call_args.kwargs["success"] is False
        assert mock_agnost_end.call_args.kwargs["output"], "the failure must carry a message"
        lat_error = mock_lat_end.call_args.kwargs["error"]
        assert isinstance(lat_error, RuntimeError) and str(lat_error) == "provider down"
        assert mock_lam_end.call_args.kwargs["error"] is lat_error

    async def test_cancelled_turn_marks_cancelled(self, test_user, existing_conv_body):
        sm = _make_stream_manager_mock(is_cancelled=True)
        with (
            patch("app.services.agnost_service.end_turn") as mock_agnost_end,
            patch("app.services.latitude_service.end_turn") as mock_lat_end,
            patch("app.services.laminar_service.end_turn") as mock_lam_end,
        ):
            await _run_turn(
                sm,
                existing_conv_body,
                test_user,
                "conv_existing_123",
                _text_then_nostream("partial", "partial"),
            )

        assert mock_agnost_end.call_args.kwargs["success"] is False
        assert mock_agnost_end.call_args.kwargs["properties"]["cancelled"] is True
        lat_error = mock_lat_end.call_args.kwargs["error"]
        assert type(lat_error).__name__ == "TurnCancelled"
        assert mock_lam_end.call_args.kwargs["error"] is lat_error

    async def test_telemetry_explosion_never_breaks_the_turn(self, test_user, existing_conv_body):
        """Sabotage below the services: the real fan-out must still not break the turn."""
        sm = _make_stream_manager_mock()
        settings = SimpleNamespace(AGNOST_ORG_ID="org-1", AGNOST_ENDPOINT="https://api.agnost.ai")
        with (
            patch("app.services.agnost_service.settings", settings),
            patch(
                "app.services.agnost_service.agnost.begin",
                side_effect=RuntimeError("telemetry down"),
            ),
        ):
            await _run_turn(
                sm,
                existing_conv_body,
                test_user,
                "conv_existing_123",
                _text_then_nostream("Follow", "Follow-up complete"),
            )

        published = [call.args[1] for call in sm.publish_chunk.call_args_list]
        assert "data: [DONE]\n\n" in published
