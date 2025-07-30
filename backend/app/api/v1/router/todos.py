from typing import List, Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body

from app.api.v1.dependencies.oauth_dependencies import get_current_user
from app.decorators import tiered_rate_limit
from app.models.todo_models import (
    TodoCreate,
    TodoResponse,
    UpdateTodoRequest,
    ProjectCreate,
    ProjectResponse,
    UpdateProjectRequest,
    TodoListResponse,
    TodoSearchParams,
    Priority,
    SearchMode,
    BulkUpdateRequest,
    BulkMoveRequest,
    BulkOperationResponse,
    SubtaskCreateRequest,
    SubtaskUpdateRequest,
    SubTask,
    WorkflowStatus,
)
from app.services.todo_service import TodoService, ProjectService

router = APIRouter()


# Main Todo CRUD Endpoints
@router.get("/todos", response_model=TodoListResponse)
async def list_todos(
    # Search parameters
    q: Optional[str] = Query(None, description="Search query"),
    mode: SearchMode = Query(
        SearchMode.HYBRID, description="Search mode: text, semantic, or hybrid"
    ),
    # Filter parameters
    project_id: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
    priority: Optional[Priority] = Query(None),
    has_due_date: Optional[bool] = Query(None),
    overdue: Optional[bool] = Query(None),
    labels: Optional[List[str]] = Query(None),
    # Date range filters
    due_after: Optional[datetime] = Query(None, description="Due date after this date"),
    due_before: Optional[datetime] = Query(
        None, description="Due date before this date"
    ),
    # Special date filters
    due_today: bool = Query(False, description="Only todos due today"),
    due_this_week: bool = Query(False, description="Only todos due this week"),
    # Pagination
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    # Options
    include_stats: bool = Query(False, description="Include statistics in response"),
    user: dict = Depends(get_current_user),
):
    """
    List todos with comprehensive filtering and search options.

    This endpoint consolidates all todo retrieval operations:
    - Search (text, semantic, or hybrid)
    - Filtering by various criteria
    - Date-based queries (today, this week, custom range)
    - Pagination with metadata
    - Optional statistics
    """
    # Handle special date filters
    if due_today:
        today = datetime.now(timezone.utc).date()
        due_after = datetime.combine(today, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        due_before = datetime.combine(today, datetime.max.time()).replace(
            tzinfo=timezone.utc
        )
    elif due_this_week:
        today = datetime.now(timezone.utc)
        due_after = today
        due_before = today + timedelta(days=7)

    params = TodoSearchParams(
        q=q,
        mode=mode,
        project_id=project_id,
        completed=completed,
        priority=priority,
        has_due_date=has_due_date,
        overdue=overdue,
        due_date_start=due_after,
        due_date_end=due_before,
        labels=labels,
        page=page,
        per_page=per_page,
        include_stats=include_stats,
    )

    try:
        return await TodoService.list_todos(user["user_id"], params)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve todos",
        )


@router.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
@tiered_rate_limit("todo_operations")
async def create_todo(todo: TodoCreate, user: dict = Depends(get_current_user)):
    """Create a new todo. If no project is specified, it will be added to Inbox."""
    try:
        return await TodoService.create_todo(todo, user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create todo",
        )


@router.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: str, user: dict = Depends(get_current_user)):
    """Get a specific todo by ID."""
    try:
        return await TodoService.get_todo(todo_id, user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve todo",
        )


@router.put("/todos/{todo_id}", response_model=TodoResponse)
@tiered_rate_limit("todo_operations")
async def update_todo(
    todo_id: str, updates: UpdateTodoRequest, user: dict = Depends(get_current_user)
):
    """Update a todo."""
    try:
        return await TodoService.update_todo(todo_id, updates, user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update todo",
        )


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
@tiered_rate_limit("todo_operations")
async def delete_todo(todo_id: str, user: dict = Depends(get_current_user)):
    """Delete a todo."""
    try:
        await TodoService.delete_todo(todo_id, user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete todo",
        )


# Workflow Generation Endpoint
@router.post("/todos/{todo_id}/workflow", response_model=TodoResponse)
@tiered_rate_limit("todo_operations")
async def generate_workflow(todo_id: str, user: dict = Depends(get_current_user)):
    """Generate a workflow plan for a specific todo and update the todo with it."""
    try:
        todo = await TodoService.get_todo(todo_id, user["user_id"])
        workflow_result = await TodoService._generate_workflow_for_todo(
            todo.title, todo.description
        )

        if not workflow_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=workflow_result.get("error", "Failed to generate workflow"),
            )

        # Update the todo with the generated workflow
        update_request = UpdateTodoRequest(
            title=None,
            description=None,
            labels=None,
            due_date=None,
            due_date_timezone=None,
            priority=None,
            project_id=None,
            completed=None,
            subtasks=None,
            workflow=workflow_result["workflow"],
            workflow_status=None,
        )
        updated_todo = await TodoService.update_todo(
            todo_id, update_request, user["user_id"]
        )

        return updated_todo
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate workflow",
        )


@router.get("/todos/{todo_id}/workflow-status")
@tiered_rate_limit("todo_operations")
async def get_workflow_status(todo_id: str, user: dict = Depends(get_current_user)):
    """
    Get the workflow generation status for a todo.
    Returns whether the workflow has been generated or is still being processed.
    """
    try:
        todo = await TodoService.get_todo(todo_id, user["user_id"])

        # Check if workflow exists
        has_workflow = hasattr(todo, "workflow") and todo.workflow is not None

        # Get workflow status - if not present, assume not started for old todos
        workflow_status = getattr(todo, "workflow_status", WorkflowStatus.NOT_STARTED)

        # Determine if currently generating (status is generating and no workflow yet)
        is_generating = workflow_status == WorkflowStatus.GENERATING

        return {
            "todo_id": todo_id,
            "has_workflow": has_workflow,
            "is_generating": is_generating,
            "workflow_status": workflow_status,
            "workflow": todo.workflow if has_workflow else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow status",
        )


# Bulk Operations
@router.put("/todos/bulk", response_model=BulkOperationResponse)
@tiered_rate_limit("todo_operations")
async def bulk_update_todos(
    request: BulkUpdateRequest, user: dict = Depends(get_current_user)
):
    """
    Bulk update multiple todos with the same changes.

    Example:
    ```json
    {
        "todo_ids": ["id1", "id2", "id3"],
        "updates": {
            "completed": true,
            "priority": "high"
        }
    }
    ```
    """
    try:
        return await TodoService.bulk_update_todos(request, user["user_id"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk update failed",
        )


@router.post("/todos/bulk/move", response_model=BulkOperationResponse)
@tiered_rate_limit("todo_operations")
async def bulk_move_todos(
    request: BulkMoveRequest, user: dict = Depends(get_current_user)
):
    """Move multiple todos to a different project."""
    try:
        return await TodoService.bulk_move_todos(request, user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Bulk move failed"
        )


@router.delete("/todos/bulk", response_model=BulkOperationResponse)
@tiered_rate_limit("todo_operations")
async def bulk_delete_todos(
    todo_ids: List[str] = Body(..., min_length=1, max_length=100),
    user: dict = Depends(get_current_user),
):
    """Delete multiple todos."""
    try:
        return await TodoService.bulk_delete_todos(todo_ids, user["user_id"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk delete failed",
        )


# Special mark complete endpoint for convenience
@router.post("/todos/bulk/complete", response_model=BulkOperationResponse)
@tiered_rate_limit("todo_operations")
async def bulk_complete_todos(
    todo_ids: List[str] = Body(..., min_length=1, max_length=100),
    user: dict = Depends(get_current_user),
):
    """Mark multiple todos as completed (convenience endpoint)."""
    request = BulkUpdateRequest(
        todo_ids=todo_ids,
        updates=UpdateTodoRequest(
            title=None,
            description=None,
            labels=None,
            due_date=None,
            due_date_timezone=None,
            priority=None,
            project_id=None,
            completed=True,
            subtasks=None,
            workflow=None,
            workflow_status=None,
        ),
    )
    try:
        return await TodoService.bulk_update_todos(request, user["user_id"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk complete failed",
        )


# Project Endpoints
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(user: dict = Depends(get_current_user)):
    """List all projects with todo counts."""
    try:
        return await ProjectService.list_projects(user["user_id"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects",
        )


@router.post(
    "/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
@tiered_rate_limit("todo_operations")
async def create_project(
    project: ProjectCreate, user: dict = Depends(get_current_user)
):
    """Create a new project."""
    try:
        return await ProjectService.create_project(project, user["user_id"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project",
        )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
@tiered_rate_limit("todo_operations")
async def update_project(
    project_id: str,
    updates: UpdateProjectRequest,
    user: dict = Depends(get_current_user),
):
    """Update a project. Cannot update the default Inbox project."""
    try:
        return await ProjectService.update_project(project_id, updates, user["user_id"])
    except ValueError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
                if "Cannot update" in str(e)
                else status.HTTP_404_NOT_FOUND
            ),
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project",
        )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
@tiered_rate_limit("todo_operations")
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    """Delete a project. All todos will be moved to Inbox. Cannot delete Inbox."""
    try:
        await ProjectService.delete_project(project_id, user["user_id"])
    except ValueError as e:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
                if "Cannot delete" in str(e)
                else status.HTTP_404_NOT_FOUND
            ),
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project",
        )


# Subtask Management Endpoints
@router.post(
    "/todos/{todo_id}/subtasks",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
)
@tiered_rate_limit("todo_operations")
async def create_subtask(
    todo_id: str, subtask: SubtaskCreateRequest, user: dict = Depends(get_current_user)
):
    """Add a new subtask to a todo."""
    try:
        # Get the current todo
        current_todo = await TodoService.get_todo(todo_id, user["user_id"])

        # Create new subtask with unique ID
        import uuid

        new_subtask = SubTask(
            id=str(uuid.uuid4()), title=subtask.title, completed=False
        )

        # Add to existing subtasks
        updated_subtasks = list(current_todo.subtasks) + [new_subtask]

        # Update the todo
        return await TodoService.update_todo(
            todo_id,
            UpdateTodoRequest(
                title=None,
                description=None,
                labels=None,
                due_date=None,
                due_date_timezone=None,
                priority=None,
                project_id=None,
                completed=None,
                subtasks=updated_subtasks,
                workflow=None,
                workflow_status=None,
            ),
            user["user_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subtask",
        )


@router.put("/todos/{todo_id}/subtasks/{subtask_id}", response_model=TodoResponse)
@tiered_rate_limit("todo_operations")
async def update_subtask(
    todo_id: str,
    subtask_id: str,
    updates: SubtaskUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """Update a specific subtask."""
    try:
        # Get the current todo
        current_todo = await TodoService.get_todo(todo_id, user["user_id"])

        # Find and update the subtask
        updated_subtasks = []
        subtask_found = False

        for subtask in current_todo.subtasks:
            if subtask.id == subtask_id:
                subtask_found = True
                # Update fields if provided
                if updates.title is not None:
                    subtask.title = updates.title
                if updates.completed is not None:
                    subtask.completed = updates.completed
            updated_subtasks.append(subtask)

        if not subtask_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subtask not found"
            )

        # Update the todo
        return await TodoService.update_todo(
            todo_id,
            UpdateTodoRequest(
                title=None,
                description=None,
                labels=None,
                due_date=None,
                due_date_timezone=None,
                priority=None,
                project_id=None,
                completed=None,
                subtasks=updated_subtasks,
                workflow=None,
                workflow_status=None,
            ),
            user["user_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subtask",
        )


@router.delete("/todos/{todo_id}/subtasks/{subtask_id}", response_model=TodoResponse)
@tiered_rate_limit("todo_operations")
async def delete_subtask(
    todo_id: str, subtask_id: str, user: dict = Depends(get_current_user)
):
    """Delete a specific subtask."""
    try:
        # Get the current todo
        current_todo = await TodoService.get_todo(todo_id, user["user_id"])

        # Remove the subtask
        updated_subtasks = [s for s in current_todo.subtasks if s.id != subtask_id]

        if len(updated_subtasks) == len(current_todo.subtasks):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subtask not found"
            )

        # Update the todo
        return await TodoService.update_todo(
            todo_id,
            UpdateTodoRequest(
                title=None,
                description=None,
                labels=None,
                due_date=None,
                due_date_timezone=None,
                priority=None,
                project_id=None,
                completed=None,
                subtasks=updated_subtasks,
                workflow=None,
                workflow_status=None,
            ),
            user["user_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete subtask",
        )


@router.post(
    "/todos/{todo_id}/subtasks/{subtask_id}/toggle", response_model=TodoResponse
)
@tiered_rate_limit("todo_operations")
async def toggle_subtask_completion(
    todo_id: str, subtask_id: str, user: dict = Depends(get_current_user)
):
    """Toggle the completion status of a subtask (convenience endpoint)."""
    try:
        # Get the current todo
        current_todo = await TodoService.get_todo(todo_id, user["user_id"])

        # Find and toggle the subtask
        updated_subtasks = []
        subtask_found = False

        for subtask in current_todo.subtasks:
            if subtask.id == subtask_id:
                subtask_found = True
                subtask.completed = not subtask.completed
            updated_subtasks.append(subtask)

        if not subtask_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subtask not found"
            )

        # Update the todo
        return await TodoService.update_todo(
            todo_id,
            UpdateTodoRequest(
                title=None,
                description=None,
                labels=None,
                due_date=None,
                due_date_timezone=None,
                priority=None,
                project_id=None,
                completed=None,
                subtasks=updated_subtasks,
                workflow=None,
                workflow_status=None,
            ),
            user["user_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle subtask",
        )
