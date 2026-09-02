"""Unit tests for tracked_todo_service (GAIA working-memory todo lifecycle).

Covers the facet persistence (deliverable / notes / log) + ChromaDB indexing
pipeline, the creation gate's staging invariant, completion/archival, and the
context-summary renderers the agent sees.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.todos import (
    ASSIGNEE_GAIA,
    DELIVERABLE_TEMPLATE,
    FACET_LOG,
    NOTES_TEMPLATE,
)
from app.models.todo_models import (
    ExecutionStatus,
    Priority,
    TodoDocument,
    TodoModel,
    TodoResponse,
    TrackedTodoDraft,
)
from app.services.todos.gaia_todo_lifecycle import TraceabilityError
from app.services.tracked_todo_service import (
    TrackedTodoService,
    tracked_todo_service,
)

_MOD = "app.services.tracked_todo_service"
USER_ID = "507f1f77bcf86cd799439011"
TODO_ID = "todo-1"
SERVES = "the user asked for the Q3 report"
WORKSPACE_LABEL = f"/workspace/gaia-tasks/{TODO_ID}"


def _todo_doc(**overrides: object) -> TodoDocument:
    now = datetime.now(UTC)
    data: dict[str, object] = {
        "id": TODO_ID,
        "user_id": USER_ID,
        "title": "Prepare Q3 report",
        "labels": ["work"],
        "assignee": ASSIGNEE_GAIA,
        "vfs_path": WORKSPACE_LABEL,
        "notes_content": "# Prepare Q3 report\n\n## Key Details\nthread: abc123\n",
        "deliverable_content": "## Output\nthe report",
        "log_content": "# System Log\n",
        "completed": False,
        "created_at": now - timedelta(days=2),
        "updated_at": now - timedelta(hours=1),
        "due_date": None,
    }
    data.update(overrides)
    return TodoDocument(**data)


def _todo_response(**overrides: object) -> TodoResponse:
    now = datetime.now(UTC)
    data: dict[str, object] = {
        "id": TODO_ID,
        "user_id": USER_ID,
        "title": "Prepare Q3 report",
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return TodoResponse(**data)


@pytest.fixture
def mock_repo():
    with patch(f"{_MOD}.todo_repository") as m:
        m.get = AsyncMock(return_value=None)
        m.update = AsyncMock(return_value=None)
        m.list_active_gaia_for_summary = AsyncMock(return_value=[])
        yield m


@pytest.fixture
def mock_deps():
    """Every seam the service writes through, with the creation gate open."""
    with (
        patch(f"{_MOD}.TodoService.create_todo", new_callable=AsyncMock) as m_create,
        patch(f"{_MOD}.store_canvas_embedding", new_callable=AsyncMock) as m_store,
        patch(f"{_MOD}.mark_canvas_completed", new_callable=AsyncMock) as m_mark,
        patch(f"{_MOD}.update_canvas_embedding", new_callable=AsyncMock) as m_update_emb,
        patch(f"{_MOD}.schedule_gaia_tasks_sync", new_callable=MagicMock) as m_sync,
        patch(f"{_MOD}.append_facet", new_callable=AsyncMock) as m_append,
        patch(f"{_MOD}.track", new_callable=MagicMock) as m_track,
        patch(f"{_MOD}.lifecycle.gate_creation", new_callable=AsyncMock) as m_gate,
        patch(f"{_MOD}.lifecycle.enforce_budget_post_insert", new_callable=AsyncMock) as m_budget,
        patch(f"{_MOD}.lifecycle.mark_execution_status", new_callable=AsyncMock) as m_status,
        patch(f"{_MOD}.lifecycle.schedule_execution", new_callable=AsyncMock) as m_schedule,
        patch(f"{_MOD}.lifecycle.reschedule_execution", new_callable=AsyncMock) as m_reschedule,
        patch(f"{_MOD}.lifecycle.system_log", new_callable=AsyncMock) as m_system_log,
        patch(
            f"{_MOD}.lifecycle.get_rejection_strikes_summary",
            new_callable=AsyncMock,
            return_value="",
        ) as m_strikes,
        patch(f"{_MOD}.teardown_subscriptions", new_callable=AsyncMock) as m_teardown,
    ):
        m_gate.return_value = (SERVES, ExecutionStatus.QUEUED)
        yield SimpleNamespace(
            create=m_create,
            store=m_store,
            mark=m_mark,
            update_emb=m_update_emb,
            sync=m_sync,
            append=m_append,
            track=m_track,
            gate=m_gate,
            budget=m_budget,
            status=m_status,
            schedule=m_schedule,
            reschedule=m_reschedule,
            system_log=m_system_log,
            strikes=m_strikes,
            teardown=m_teardown,
        )


async def _create(**kwargs: object) -> TodoResponse:
    """Create with the required gate arguments filled in."""
    params: dict[str, object] = {
        "title": "Prepare Q3 report",
        "serves": SERVES,
        "requires_approval": False,
    }
    params.update(kwargs)
    return await TrackedTodoService.create_tracked_todo(USER_ID, TrackedTodoDraft(**params))


class TestCreateTrackedTodo:
    async def test_creates_with_template_facets_and_indexes(self, mock_repo, mock_deps):
        mock_deps.create.return_value = _todo_response()

        result = await _create()

        assert result.id == TODO_ID
        assert result.vfs_path == WORKSPACE_LABEL

        todo_model: TodoModel = mock_deps.create.call_args.args[0]
        assert todo_model.assignee == ASSIGNEE_GAIA
        assert todo_model.execution_status is ExecutionStatus.QUEUED
        assert todo_model.serves == SERVES

        update = mock_repo.update.await_args_list[0].kwargs["update"]
        assert update.vfs_path == WORKSPACE_LABEL
        assert update.deliverable_content == DELIVERABLE_TEMPLATE.format(title="Prepare Q3 report")
        assert update.notes_content == NOTES_TEMPLATE.format(title="Prepare Q3 report")
        assert "[CREATED]" in update.log_content
        assert "Source: agent" in update.log_content

        mock_deps.store.assert_awaited_once()
        store_kwargs = mock_deps.store.call_args.kwargs
        assert store_kwargs["todo_id"] == TODO_ID
        assert store_kwargs["user_id"] == USER_ID
        assert store_kwargs["title"] == "Prepare Q3 report"
        mock_deps.sync.assert_called_once_with(USER_ID)

    async def test_indexes_notes_and_deliverable_but_never_the_log(self, mock_repo, mock_deps):
        """The log facet is audit noise — indexing it would match signals on
        timestamps instead of on the work."""
        mock_deps.create.return_value = _todo_response()

        await _create(initial_notes="notes body", initial_deliverable="deliverable body")

        content = mock_deps.store.call_args.kwargs["content"]
        assert "notes body" in content
        assert "deliverable body" in content
        assert "[CREATED]" not in content

    async def test_uses_provided_initial_facets(self, mock_repo, mock_deps):
        mock_deps.create.return_value = _todo_response()

        await _create(initial_notes="custom notes", initial_deliverable="custom deliverable")

        update = mock_repo.update.await_args_list[0].kwargs["update"]
        assert update.notes_content == "custom notes"
        assert update.deliverable_content == "custom deliverable"

    async def test_persists_the_originating_conversation(self, mock_repo, mock_deps):
        """The run's result is delivered back into the chat the todo came from,
        so the originating conversation id has to reach the doc."""
        mock_deps.create.return_value = _todo_response()

        await _create(source_conversation_id="conv-9")

        update = mock_repo.update.await_args_list[0].kwargs["update"]
        assert update.source_conversation_id == "conv-9"

    async def test_preserves_caller_labels_without_stamping_a_tracked_label(
        self, mock_repo, mock_deps
    ):
        """`assignee == "gaia"` is the discriminator now; a stamped label would
        show as a stray chip on the user's todo."""
        mock_deps.create.return_value = _todo_response()

        await _create(labels=["work", "finance"])

        todo_model: TodoModel = mock_deps.create.call_args.args[0]
        assert todo_model.labels == ["work", "finance"]

    async def test_budget_is_re_enforced_after_the_insert(self, mock_repo, mock_deps):
        mock_deps.create.return_value = _todo_response()

        await _create()

        mock_deps.budget.assert_awaited_once_with(USER_ID, TODO_ID, ExecutionStatus.QUEUED)

    async def test_gate_rejection_propagates_and_creates_nothing(self, mock_repo, mock_deps):
        mock_deps.gate.side_effect = TraceabilityError("no goal named")

        with pytest.raises(TraceabilityError, match="no goal named"):
            await _create(serves="")

        mock_deps.create.assert_not_awaited()

    async def test_queued_todo_executes_immediately(self, mock_repo, mock_deps):
        """Internal work needs no permission: it is scheduled on creation, not
        only when a schedule happens to be attached."""
        mock_deps.create.return_value = _todo_response()

        await _create()

        mock_deps.schedule.assert_awaited_once()
        assert mock_deps.schedule.await_args.args[0] == TODO_ID

    async def test_auto_execute_false_leaves_the_schedule_to_the_caller(self, mock_repo, mock_deps):
        mock_deps.create.return_value = _todo_response()

        await _create(auto_execute=False)

        mock_deps.schedule.assert_not_awaited()


class TestCreateProposalStagingInvariant:
    """Approving a proposal releases its deliverable verbatim, so the gate
    rejects a proposal that has no finished content to release."""

    async def test_proposal_without_a_deliverable_is_rejected(self, mock_repo, mock_deps):
        mock_deps.gate.return_value = (SERVES, ExecutionStatus.PROPOSED)

        with pytest.raises(TraceabilityError, match="initial_deliverable"):
            await _create(requires_approval=True)

        mock_deps.create.assert_not_awaited()

    async def test_proposal_with_unfilled_placeholders_is_rejected(self, mock_repo, mock_deps):
        mock_deps.gate.return_value = (SERVES, ExecutionStatus.PROPOSED)

        with pytest.raises(TraceabilityError, match="placeholders"):
            await _create(requires_approval=True, initial_deliverable="Hi [Name], we should talk.")

        mock_deps.create.assert_not_awaited()

    async def test_markdown_links_and_checkboxes_are_not_placeholders(self, mock_repo, mock_deps):
        mock_deps.gate.return_value = (SERVES, ExecutionStatus.PROPOSED)
        mock_deps.create.return_value = _todo_response()

        await _create(
            requires_approval=True,
            initial_deliverable="- [x] done\nSee [the docs](https://example.com).",
        )

        mock_deps.create.assert_awaited_once()

    async def test_a_staged_proposal_is_tracked_and_not_auto_executed(self, mock_repo, mock_deps):
        mock_deps.gate.return_value = (SERVES, ExecutionStatus.PROPOSED)
        mock_deps.create.return_value = _todo_response()

        await _create(requires_approval=True, initial_deliverable="Ready to send.")

        mock_deps.schedule.assert_not_awaited()
        mock_deps.track.assert_called_once()
        assert mock_deps.track.call_args.args[1] == "todo_proposed"


class TestCompleteTrackedTodo:
    async def test_false_for_missing_todo(self, mock_repo, mock_deps):
        assert await TrackedTodoService.complete_tracked_todo(TODO_ID, USER_ID, "done") is False
        mock_deps.append.assert_not_awaited()

    async def test_idempotent_for_already_completed(self, mock_repo, mock_deps):
        mock_repo.get.return_value = _todo_doc(completed=True)

        assert await TrackedTodoService.complete_tracked_todo(TODO_ID, USER_ID, "done") is True
        mock_deps.append.assert_not_awaited()
        mock_repo.update.assert_not_awaited()

    async def test_appends_log_marks_completed_and_archives_path(self, mock_repo, mock_deps):
        mock_repo.get.return_value = _todo_doc()

        ok = await TrackedTodoService.complete_tracked_todo(TODO_ID, USER_ID, "Wrapped it up")

        assert ok is True
        todo_id, user_id, facet, entry = mock_deps.append.await_args.args
        assert (todo_id, user_id, facet) == (TODO_ID, USER_ID, FACET_LOG)
        assert "[COMPLETED]" in entry
        assert "Wrapped it up" in entry

        update = mock_repo.update.await_args.kwargs["update"]
        assert update.completed is True
        assert update.completed_at is not None
        assert update.vfs_path == f"/workspace/gaia-tasks/archive/{TODO_ID}"
        mock_deps.status.assert_awaited_once_with(TODO_ID, USER_ID, ExecutionStatus.DONE)
        mock_deps.mark.assert_awaited_once_with(TODO_ID)
        mock_deps.sync.assert_called_once_with(USER_ID)

    async def test_completion_stops_the_todo_watching(self, mock_repo, mock_deps):
        # Teardown lives inside completion rather than at its callers (tool, sweep,
        # worker) so no completion path can forget it and strand a live trigger.
        mock_repo.get.return_value = _todo_doc()

        await TrackedTodoService.complete_tracked_todo(TODO_ID, USER_ID, "done")

        mock_deps.teardown.assert_awaited_once_with(TODO_ID, USER_ID, reason="completed")

    async def test_an_already_completed_todo_does_not_tear_down_again(self, mock_repo, mock_deps):
        mock_repo.get.return_value = _todo_doc(completed=True)

        await TrackedTodoService.complete_tracked_todo(TODO_ID, USER_ID, "done")

        mock_deps.teardown.assert_not_awaited()

    async def test_missing_vfs_path_falls_back_to_derived_workspace_label(
        self, mock_repo: MagicMock, mock_deps: SimpleNamespace
    ) -> None:
        """A doc with no stored label must get the derived /workspace-scoped one —
        never None, and never a label derived from the wrong id."""
        mock_repo.get.return_value = _todo_doc(vfs_path=None)

        ok = await TrackedTodoService.complete_tracked_todo(TODO_ID, USER_ID, "done")

        assert ok is True
        update = mock_repo.update.await_args.kwargs["update"]
        assert update.vfs_path == f"/workspace/gaia-tasks/archive/{TODO_ID}"

    async def test_legacy_user_scoped_label_is_healed_on_completion(
        self, mock_repo: MagicMock, mock_deps: SimpleNamespace
    ) -> None:
        """A doc still storing the host-side /users/<uid> label must not have it
        persisted back on completion — the derived archive label replaces it."""
        mock_repo.get.return_value = _todo_doc(vfs_path=f"/users/{USER_ID}/todos/{TODO_ID}")

        ok = await TrackedTodoService.complete_tracked_todo(TODO_ID, USER_ID, "done")

        assert ok is True
        update = mock_repo.update.await_args.kwargs["update"]
        assert update.vfs_path == f"/workspace/gaia-tasks/archive/{TODO_ID}"


class TestGetActiveTrackedSummary:
    async def test_empty_string_without_docs(self, mock_repo, mock_deps):
        assert await TrackedTodoService.get_active_tracked_summary(USER_ID) == ""

    async def test_strikes_are_surfaced_even_with_no_active_todos(self, mock_repo, mock_deps):
        mock_deps.strikes.return_value = "Rejected work: outreach (3x, BLOCKED)"

        summary = await TrackedTodoService.get_active_tracked_summary(USER_ID)

        assert summary == "\nRejected work: outreach (3x, BLOCKED)"

    async def test_strikes_are_appended_after_the_todo_lines(self, mock_repo, mock_deps):
        mock_repo.list_active_gaia_for_summary.return_value = [_todo_doc()]
        mock_deps.strikes.return_value = "Rejected work: outreach (3x, BLOCKED)"

        summary = await TrackedTodoService.get_active_tracked_summary(USER_ID)

        assert summary.split("\n")[-1] == "Rejected work: outreach (3x, BLOCKED)"

    @pytest.mark.regression
    async def test_stored_user_scoped_vfs_path_never_leaks_into_agent_context(
        self, mock_repo: MagicMock, mock_deps: SimpleNamespace
    ) -> None:
        """Old docs store vfs_path as /users/<uid>/todos/<id> — that host-side
        path must never reach the LLM, which only knows /workspace-scoped paths."""
        stale_doc = _todo_doc(vfs_path=f"/users/{USER_ID}/todos/{TODO_ID}")
        mock_repo.list_active_gaia_for_summary.return_value = [stale_doc]

        summary = await TrackedTodoService.get_active_tracked_summary(USER_ID)

        assert USER_ID not in summary
        assert "/users/" not in summary

    async def test_renders_summary_lines(self, mock_repo, mock_deps):
        mock_repo.list_active_gaia_for_summary.return_value = [
            _todo_doc(execution_status=ExecutionStatus.QUEUED)
        ]

        summary = await TrackedTodoService.get_active_tracked_summary(USER_ID)

        lines = summary.split("\n")
        assert lines[0] == "ACTIVE TRACKED TODOS:"
        assert '"Prepare Q3 report" [work]' in lines[1]
        assert "state: queued" in lines[1]
        assert "ID: todo-1" in lines[1]
        assert f"VFS: {WORKSPACE_LABEL}" in lines[1]
        assert "d old" in lines[1]

    async def test_a_blocked_todo_shows_the_question_it_is_waiting_on(self, mock_repo, mock_deps):
        """A chat reply like "yes, use the second one" is only actionable if the
        agent can see which question it answers."""
        mock_repo.list_active_gaia_for_summary.return_value = [
            _todo_doc(
                execution_status=ExecutionStatus.NEEDS_YOU,
                blocker_question="Which vendor should I book?",
            )
        ]

        summary = await TrackedTodoService.get_active_tracked_summary(USER_ID)

        assert 'waiting on user: "Which vendor should I book?"' in summary

    async def test_active_todo_pinned_with_star(self, mock_repo, mock_deps):
        docs = [
            _todo_doc(id="todo-2", title="Second"),
            _todo_doc(id="todo-3", title="Third"),
        ]
        mock_repo.list_active_gaia_for_summary.return_value = docs

        summary = await TrackedTodoService.get_active_tracked_summary(
            USER_ID, active_todo_id="todo-3"
        )

        lines = summary.split("\n")
        assert lines[1].startswith('  ⭐ ACTIVE "Third"')
        assert lines[2].startswith('  "Second"')

    async def test_due_and_overdue_suffixes(self, mock_repo, mock_deps):
        now = datetime.now(UTC)
        docs = [
            _todo_doc(id="todo-due", title="Due soon", due_date=now + timedelta(days=3, hours=1)),
            _todo_doc(id="todo-late", title="Late", due_date=now - timedelta(days=3, hours=23)),
        ]
        mock_repo.list_active_gaia_for_summary.return_value = docs

        summary = await TrackedTodoService.get_active_tracked_summary(USER_ID)

        assert " due(3d)" in summary.split("\n")[1]
        assert " OVERDUE(4d)" in summary.split("\n")[2]


class TestAppendActivityMarker:
    async def test_appends_to_the_log_facet(self, mock_repo, mock_deps):
        mock_deps.append.return_value = True

        assert await TrackedTodoService.append_activity_marker(TODO_ID, USER_ID, "step") is True
        todo_id, user_id, facet, line = mock_deps.append.await_args.args
        assert (todo_id, user_id, facet, line) == (TODO_ID, USER_ID, FACET_LOG, "- step")

    async def test_keeps_an_already_bulleted_entry_as_is(self, mock_repo, mock_deps):
        mock_deps.append.return_value = True

        await TrackedTodoService.append_activity_marker(TODO_ID, USER_ID, "- step")

        assert mock_deps.append.await_args.args[3] == "- step"

    async def test_false_when_the_write_fails(self, mock_repo, mock_deps):
        mock_deps.append.side_effect = RuntimeError("mongo down")

        assert await TrackedTodoService.append_activity_marker(TODO_ID, USER_ID, "step") is False


class TestSystemLog:
    async def test_delegates_to_the_lifecycle_audit_writer(self, mock_repo, mock_deps):
        await TrackedTodoService.system_log(TODO_ID, USER_ID, "rescheduled", "Retry at 9am")

        mock_deps.system_log.assert_awaited_once_with(
            TODO_ID, USER_ID, "rescheduled", "Retry at 9am"
        )


class TestReindexCanvas:
    async def test_false_for_missing_todo(self, mock_repo, mock_deps):
        assert await TrackedTodoService.reindex_canvas(TODO_ID, USER_ID) is False
        mock_deps.update_emb.assert_not_awaited()

    async def test_false_without_any_indexable_facet(self, mock_repo, mock_deps):
        mock_repo.get.return_value = _todo_doc(notes_content=None, deliverable_content=None)

        assert await TrackedTodoService.reindex_canvas(TODO_ID, USER_ID) is False

    async def test_reindexes_notes_and_deliverable(self, mock_repo, mock_deps):
        mock_repo.get.return_value = _todo_doc()
        mock_deps.update_emb.return_value = True

        ok = await TrackedTodoService.reindex_canvas(TODO_ID, USER_ID)

        assert ok is True
        kwargs = mock_deps.update_emb.call_args.kwargs
        assert kwargs["todo_id"] == TODO_ID
        assert kwargs["user_id"] == USER_ID
        assert kwargs["title"] == "Prepare Q3 report"
        assert kwargs["labels"] == ["work"]
        assert "thread: abc123" in kwargs["content"]
        assert "the report" in kwargs["content"]

    async def test_the_log_facet_is_never_indexed(self, mock_repo, mock_deps):
        mock_repo.get.return_value = _todo_doc(log_content="## 2026 [CREATED]\n- audit line\n")
        mock_deps.update_emb.return_value = True

        await TrackedTodoService.reindex_canvas(TODO_ID, USER_ID)

        assert "audit line" not in mock_deps.update_emb.call_args.kwargs["content"]

    async def test_propagates_embedding_failure(self, mock_repo, mock_deps):
        mock_repo.get.return_value = _todo_doc()
        mock_deps.update_emb.return_value = False

        assert await TrackedTodoService.reindex_canvas(TODO_ID, USER_ID) is False


class TestScheduleExecution:
    async def test_delegates_to_the_lifecycle_scheduler(self, mock_repo, mock_deps):
        mock_deps.schedule.return_value = True
        when = datetime.now(UTC) + timedelta(hours=1)

        assert await TrackedTodoService.schedule_execution(TODO_ID, when) is True
        mock_deps.schedule.assert_awaited_once_with(TODO_ID, when)

    async def test_propagates_a_scheduling_failure(self, mock_repo, mock_deps):
        mock_deps.schedule.return_value = False

        assert await TrackedTodoService.schedule_execution(TODO_ID, datetime.now(UTC)) is False

    async def test_reschedule_delegates_to_the_lifecycle_rescheduler(self, mock_repo, mock_deps):
        mock_deps.reschedule.return_value = True
        when = datetime.now(UTC) + timedelta(hours=2)

        assert await TrackedTodoService.reschedule_execution(TODO_ID, when) is True
        mock_deps.reschedule.assert_awaited_once_with(TODO_ID, when)


class TestArchiveTrackedTodo:
    async def test_logs_reason_and_completes(self, mock_repo, mock_deps):
        mock_repo.get.return_value = _todo_doc()

        ok = await TrackedTodoService.archive_tracked_todo(TODO_ID, USER_ID, "expired")

        assert ok is True
        assert mock_deps.system_log.await_args.args[2] == "auto_archived"
        assert "expired" in mock_deps.system_log.await_args.args[3]

    async def test_false_when_completion_fails(self, mock_repo, mock_deps):
        mock_repo.get.return_value = None

        assert await TrackedTodoService.archive_tracked_todo(TODO_ID, USER_ID, "expired") is False

    async def test_false_when_unexpected_error(self, mock_repo, mock_deps):
        mock_deps.system_log.side_effect = RuntimeError("boom")

        assert await TrackedTodoService.archive_tracked_todo(TODO_ID, USER_ID, "expired") is False


class TestSingleton:
    def test_module_singleton_is_an_instance(self):
        assert isinstance(tracked_todo_service, TrackedTodoService)

    def test_priority_default_is_none(self):
        assert Priority.NONE.value == "none"
