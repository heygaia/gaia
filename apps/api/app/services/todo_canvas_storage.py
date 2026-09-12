"""MongoDB-backed canvas/activity/log storage for tracked todos.

Canvas (`canvas.md`), activity (`activity.md`) and log (`log.md`) content live
as fields on the todo document itself: ``canvas_content``, ``activity_content``
and ``log_content``. Reading, writing, and appending go through the todos
repository — no FUSE mount or JuiceFS required, so tracked todos work in every
dev mode.

Every successful canvas/activity write re-embeds the todo in ChromaDB here, so
all writers (agent file tools, code-written run markers) keep search fresh.

The legacy ``vfs_path`` field on the todo doc is retained as a stable
display label (``/workspace/gaia-tasks/{todo_id}``) but is no longer a
real filesystem path. It never carries the host-side ``/users/<uid>``
prefix — the LLM only ever sees the sandbox-visible workspace path.
"""

from app.db.repositories.todos import todo_repository
from app.models.todo_models import TodoDocument, TodoUpdate
from app.services.gaia_tasks_fs import schedule_gaia_tasks_sync
from app.utils.canvas_vector_utils import update_canvas_embedding
from shared.py.wide_events import log, spawn_logged_task


def build_vfs_label(todo_id: str, *, archived: bool = False) -> str:
    """Stable label used wherever the old VFS path was surfaced for display."""
    if archived:
        return f"/workspace/gaia-tasks/archive/{todo_id}"
    return f"/workspace/gaia-tasks/{todo_id}"


def embedding_text(doc: TodoDocument) -> str:
    """The text embedded for canvas search: canvas + activity, skipping empties."""
    parts = [p for p in (doc.canvas_content, doc.activity_content) if p]
    return "\n\n".join(parts)


def _schedule_reindex(doc: TodoDocument) -> None:
    text = embedding_text(doc)
    if not text:
        return
    spawn_logged_task(
        "canvas_reindex",
        update_canvas_embedding(
            todo_id=doc.id,
            canvas_content=text,
            user_id=doc.user_id,
            title=doc.title,
            labels=doc.labels,
        ),
    )


async def read_canvas(todo_id: str, user_id: str) -> str | None:
    """Return the todo's canvas body, or None when the todo does not exist."""
    doc = await todo_repository.get(todo_id, user_id=user_id)
    if not doc:
        return None
    return doc.canvas_content or ""


async def write_canvas(todo_id: str, user_id: str, content: str) -> bool:
    """Replace the canvas body; schedules VFS sync + Chroma reindex on success."""
    updated = await todo_repository.update(
        todo_id, user_id=user_id, update=TodoUpdate(canvas_content=content)
    )
    if updated is not None:
        schedule_gaia_tasks_sync(user_id)
        _schedule_reindex(updated)
        return True
    return False


async def read_activity(todo_id: str, user_id: str) -> str | None:
    """Return the todo's activity body, or None when the todo does not exist."""
    doc = await todo_repository.get(todo_id, user_id=user_id)
    if not doc:
        return None
    return doc.activity_content or ""


async def write_activity(todo_id: str, user_id: str, content: str) -> bool:
    """Replace the activity body; schedules VFS sync + Chroma reindex on success."""
    updated = await todo_repository.update(
        todo_id, user_id=user_id, update=TodoUpdate(activity_content=content)
    )
    if updated is not None:
        schedule_gaia_tasks_sync(user_id)
        _schedule_reindex(updated)
        return True
    return False


async def append_activity(todo_id: str, user_id: str, entry: str) -> bool:
    """Append an entry at the end of the activity log (chronological order)."""
    current = await read_activity(todo_id, user_id)
    if current is None:
        log.warning("todo_canvas.activity_append_missing_todo", todo_id=todo_id)
        return False
    suffix = entry if entry.startswith("\n") else f"\n{entry}"
    return await write_activity(todo_id, user_id, (current + suffix).lstrip("\n"))


async def read_log(todo_id: str, user_id: str) -> str | None:
    """Return the todo's system-log body, or None when the todo does not exist."""
    doc = await todo_repository.get(todo_id, user_id=user_id)
    if not doc:
        return None
    return doc.log_content or ""


async def write_log(todo_id: str, user_id: str, content: str) -> bool:
    """Replace the system-log body; schedules the gaia-tasks VFS sync on success."""
    updated = await todo_repository.update(
        todo_id, user_id=user_id, update=TodoUpdate(log_content=content)
    )
    if updated is not None:
        schedule_gaia_tasks_sync(user_id)
        return True
    return False


async def append_log(todo_id: str, user_id: str, content: str) -> bool:
    """Append to the system-log body, ensuring a leading newline separator."""
    current = await read_log(todo_id, user_id)
    if current is None:
        log.warning("todo_canvas.log_append_missing_todo", todo_id=todo_id)
        return False
    suffix = content if content.startswith("\n") else f"\n{content}"
    return await write_log(todo_id, user_id, current + suffix)
