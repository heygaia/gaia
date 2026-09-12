"""Unit tests for todo_canvas_storage (Mongo-backed canvas/log read/write/append).

The storage primitives funnel every read and write through the todos
repository — atomicity here means: each append reads the current value, then
writes back the full concatenated content in one update (no partial writes),
and a write only succeeds when the repository confirms the update matched.
"""

from collections.abc import Coroutine
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.todo_models import TodoDocument
from app.services.todo_canvas_storage import (
    append_activity,
    append_log,
    build_vfs_label,
    read_activity,
    read_canvas,
    read_log,
    write_activity,
    write_canvas,
    write_canvas_and_activity,
    write_log,
)

_MOD = "app.services.todo_canvas_storage"
USER_ID = "507f1f77bcf86cd799439011"
TODO_ID = "todo-1"


def _todo_doc(**overrides: object) -> TodoDocument:
    data: dict[str, object] = {
        "user_id": USER_ID,
        "title": "Ship the thing",
        "canvas_content": "canvas-v1",
        "activity_content": "activity-v1",
        "log_content": "log-v1",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    data.update(overrides)
    return TodoDocument(**data)


@pytest.fixture
def mock_repo():
    with patch(f"{_MOD}.todo_repository") as m:
        m.get = AsyncMock(return_value=None)
        m.update = AsyncMock(return_value=None)
        yield m


@pytest.fixture
def mock_sync():
    with patch(f"{_MOD}.schedule_gaia_tasks_sync", new_callable=MagicMock) as m:
        yield m


@pytest.fixture
def captured_reindex():
    """Capture the fire-and-forget reindex: patched spawn collects coroutines so
    tests can await them deterministically; the embedding call itself is mocked."""
    scheduled: list[tuple[str, Coroutine[Any, Any, Any]]] = []

    def fake_spawn(name: str, coro: Coroutine[Any, Any, Any]) -> None:
        scheduled.append((name, coro))

    with (
        patch(f"{_MOD}.spawn_logged_task", side_effect=fake_spawn),
        patch(f"{_MOD}.update_canvas_embedding", new_callable=AsyncMock) as embed,
    ):
        yield scheduled, embed
        for _, coro in scheduled:
            coro.close()


class TestBuildVfsLabel:
    def test_label_format(self):
        assert build_vfs_label(TODO_ID) == f"/workspace/gaia-tasks/{TODO_ID}"

    def test_label_never_contains_user_id(self) -> None:
        assert USER_ID not in build_vfs_label(TODO_ID)

    def test_archive_label_format(self) -> None:
        assert build_vfs_label(TODO_ID, archived=True) == (
            f"/workspace/gaia-tasks/archive/{TODO_ID}"
        )


class TestReadCanvas:
    async def test_none_for_missing_todo(self, mock_repo):
        assert await read_canvas(TODO_ID, USER_ID) is None

    async def test_returns_content(self, mock_repo):
        mock_repo.get.return_value = _todo_doc(canvas_content="hello")

        assert await read_canvas(TODO_ID, USER_ID) == "hello"

    async def test_empty_string_when_unset(self, mock_repo):
        mock_repo.get.return_value = _todo_doc(canvas_content=None)

        assert await read_canvas(TODO_ID, USER_ID) == ""


class TestWriteCanvas:
    async def test_writes_and_triggers_sync(self, mock_repo, mock_sync):
        mock_repo.update.return_value = _todo_doc()

        ok = await write_canvas(TODO_ID, USER_ID, "new content")

        assert ok is True
        update = mock_repo.update.await_args.kwargs["update"]
        assert update.canvas_content == "new content"
        mock_sync.assert_called_once_with(USER_ID)

    async def test_false_when_update_matches_nothing(self, mock_repo, mock_sync):
        mock_repo.update.return_value = None

        assert await write_canvas(TODO_ID, USER_ID, "new content") is False
        mock_sync.assert_not_called()


class TestActivity:
    async def test_read_none_for_missing_todo(self, mock_repo):
        assert await read_activity(TODO_ID, USER_ID) is None

    async def test_read_empty_string_when_unset(self, mock_repo):
        mock_repo.get.return_value = _todo_doc(activity_content=None)

        assert await read_activity(TODO_ID, USER_ID) == ""

    async def test_write_and_triggers_sync(self, mock_repo, mock_sync, captured_reindex):
        mock_repo.update.return_value = _todo_doc()

        ok = await write_activity(TODO_ID, USER_ID, "- 2026-09-02 did a thing")

        assert ok is True
        update = mock_repo.update.await_args.kwargs["update"]
        assert update.activity_content == "- 2026-09-02 did a thing"
        mock_sync.assert_called_once_with(USER_ID)

    async def test_write_false_when_update_matches_nothing(self, mock_repo, mock_sync):
        mock_repo.update.return_value = None

        assert await write_activity(TODO_ID, USER_ID, "entry") is False
        mock_sync.assert_not_called()

    async def test_append_false_for_missing_todo(self, mock_repo):
        assert await append_activity(TODO_ID, USER_ID, "entry") is False

    async def test_append_lands_at_end(self, mock_repo, mock_sync, captured_reindex):
        """Chronological log: a new entry always goes after existing ones."""
        mock_repo.get.return_value = _todo_doc(activity_content="- old entry")
        mock_repo.update.return_value = _todo_doc()

        ok = await append_activity(TODO_ID, USER_ID, "- new entry")

        assert ok is True
        update = mock_repo.update.await_args.kwargs["update"]
        assert update.activity_content == "- old entry\n- new entry"

    async def test_append_round_trip_accumulates(self, mock_repo, mock_sync, captured_reindex):
        activity = "- a"
        mock_repo.update.return_value = _todo_doc()

        async def fake_get(todo_id: str, **kwargs: object) -> TodoDocument | None:
            return _todo_doc(activity_content=activity)

        async def fake_update(todo_id: str, **kwargs: object) -> TodoDocument:
            nonlocal activity
            activity = kwargs["update"].activity_content
            return _todo_doc(activity_content=activity)

        mock_repo.get = fake_get
        mock_repo.update = fake_update

        await append_activity(TODO_ID, USER_ID, "- b")
        await append_activity(TODO_ID, USER_ID, "- c")

        assert activity == "- a\n- b\n- c"


class TestWriteCanvasAndActivity:
    async def test_sets_both_fields_in_one_update(self, mock_repo, mock_sync, captured_reindex):
        scheduled, embed = captured_reindex
        mock_repo.update.return_value = _todo_doc(canvas_content="c", activity_content="a")

        ok = await write_canvas_and_activity(TODO_ID, USER_ID, canvas="c", activity="a")

        assert ok is True
        mock_repo.update.assert_awaited_once()
        update = mock_repo.update.await_args.kwargs["update"]
        assert (update.canvas_content, update.activity_content) == ("c", "a")
        mock_sync.assert_called_once_with(USER_ID)
        assert [name for name, _ in scheduled] == ["canvas_reindex"]

    async def test_false_when_update_matches_nothing(self, mock_repo, mock_sync):
        mock_repo.update.return_value = None

        assert await write_canvas_and_activity(TODO_ID, USER_ID, canvas="c", activity="a") is False
        mock_sync.assert_not_called()


class TestReindexOnWrite:
    async def test_write_canvas_reindexes_with_combined_text(
        self, mock_repo, mock_sync, captured_reindex
    ):
        scheduled, embed = captured_reindex
        mock_repo.update.return_value = _todo_doc(
            canvas_content="canvas body", activity_content="activity body"
        )

        await write_canvas(TODO_ID, USER_ID, "canvas body")

        assert [name for name, _ in scheduled] == ["canvas_reindex"]
        await scheduled.pop()[1]
        embed.assert_awaited_once()
        assert embed.await_args.kwargs["canvas_content"] == "canvas body\n\nactivity body"

    async def test_write_activity_reindexes(self, mock_repo, mock_sync, captured_reindex):
        scheduled, embed = captured_reindex
        mock_repo.update.return_value = _todo_doc(
            canvas_content="canvas body", activity_content="- entry"
        )

        await write_activity(TODO_ID, USER_ID, "- entry")

        assert [name for name, _ in scheduled] == ["canvas_reindex"]
        await scheduled.pop()[1]
        assert embed.await_args.kwargs["canvas_content"] == "canvas body\n\n- entry"

    async def test_no_reindex_when_update_matches_nothing(
        self, mock_repo, mock_sync, captured_reindex
    ):
        scheduled, embed = captured_reindex
        mock_repo.update.return_value = None

        await write_canvas(TODO_ID, USER_ID, "content")

        assert scheduled == []
        embed.assert_not_awaited()

    async def test_write_log_does_not_reindex(self, mock_repo, mock_sync, captured_reindex):
        """log.md is the system audit trail — it is not part of the embedding."""
        scheduled, embed = captured_reindex
        mock_repo.update.return_value = _todo_doc()

        await write_log(TODO_ID, USER_ID, "audit")

        assert scheduled == []
        embed.assert_not_awaited()


class TestReadLog:
    async def test_none_for_missing_todo(self, mock_repo):
        assert await read_log(TODO_ID, USER_ID) is None

    async def test_returns_content(self, mock_repo):
        mock_repo.get.return_value = _todo_doc(log_content="audit")

        assert await read_log(TODO_ID, USER_ID) == "audit"


class TestWriteLog:
    async def test_writes_and_triggers_sync(self, mock_repo, mock_sync):
        mock_repo.update.return_value = _todo_doc()

        assert await write_log(TODO_ID, USER_ID, "audit v2") is True
        assert mock_repo.update.await_args.kwargs["update"].log_content == "audit v2"
        mock_sync.assert_called_once_with(USER_ID)

    async def test_false_when_update_matches_nothing(self, mock_repo, mock_sync):
        mock_repo.update.return_value = None

        assert await write_log(TODO_ID, USER_ID, "audit v2") is False
        mock_sync.assert_not_called()


class TestAppendLog:
    async def test_false_for_missing_todo(self, mock_repo):
        assert await append_log(TODO_ID, USER_ID, "entry") is False

    async def test_appends_with_newline_separator(self, mock_repo, mock_sync):
        mock_repo.get.return_value = _todo_doc(log_content="audit v1")
        mock_repo.update.return_value = _todo_doc()

        assert await append_log(TODO_ID, USER_ID, "audit v2") is True
        assert mock_repo.update.await_args.kwargs["update"].log_content == "audit v1\naudit v2"
