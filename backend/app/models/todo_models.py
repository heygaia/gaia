from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    HIGH = "high"  # red
    MEDIUM = "medium"  # yellow
    LOW = "low"  # blue
    NONE = "none"  # no color


class SubTask(BaseModel):
    id: str = Field(default="", description="Unique identifier for the subtask")
    title: str = Field(..., description="Title of the subtask")
    completed: bool = Field(
        default=False, description="Whether the subtask is completed"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TodoModel(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=200, description="Title of the todo item"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Description of the todo item"
    )
    labels: List[str] = Field(
        default_factory=list, max_length=10, description="Labels for categorization"
    )
    due_date: Optional[datetime] = Field(None, description="Due date for the todo item")
    due_date_timezone: Optional[str] = Field(
        None, description="Timezone for the due date (e.g., 'America/New_York')"
    )
    priority: Priority = Field(default=Priority.NONE, description="Priority level")
    project_id: Optional[str] = Field(
        None, description="Project ID the todo belongs to"
    )
    completed: bool = Field(default=False, description="Whether the todo is completed")
    subtasks: List[SubTask] = Field(
        default_factory=list, max_length=50, description="List of subtasks"
    )
    workflow_id: Optional[str] = Field(
        None, description="ID of the associated workflow"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TodoCreate(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=200, description="Title of the todo item"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Description of the todo item"
    )
    labels: List[str] = Field(
        default_factory=list, max_length=10, description="Labels for categorization"
    )
    due_date: Optional[datetime] = Field(None, description="Due date for the todo item")
    due_date_timezone: Optional[str] = Field(
        None, description="Timezone for the due date (e.g., 'America/New_York')"
    )
    priority: Priority = Field(default=Priority.NONE, description="Priority level")
    project_id: Optional[str] = Field(
        None, description="Project ID the todo belongs to"
    )


class UpdateTodoRequest(BaseModel):
    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Title of the todo item"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Description of the todo item"
    )
    labels: Optional[List[str]] = Field(
        None, max_length=10, description="Labels for categorization"
    )
    due_date: Optional[datetime] = Field(None, description="Due date for the todo item")
    due_date_timezone: Optional[str] = Field(
        None, description="Timezone for the due date (e.g., 'America/New_York')"
    )
    priority: Optional[Priority] = Field(None, description="Priority level")
    project_id: Optional[str] = Field(
        None, description="Project ID the todo belongs to"
    )
    completed: Optional[bool] = Field(None, description="Whether the todo is completed")
    subtasks: Optional[List[SubTask]] = Field(
        None, max_length=50, description="List of subtasks"
    )
    workflow_id: Optional[str] = Field(
        None, description="ID of the associated workflow"
    )


class TodoResponse(BaseModel):
    id: str = Field(..., description="Unique identifier")
    user_id: str = Field(..., description="User ID who owns the todo")
    title: str = Field(..., description="Title of the todo item")
    description: Optional[str] = Field(None, description="Description of the todo item")
    labels: List[str] = Field(
        default_factory=list, description="Labels for categorization"
    )
    due_date: Optional[datetime] = Field(None, description="Due date for the todo item")
    due_date_timezone: Optional[str] = Field(
        None, description="Timezone for the due date (e.g., 'America/New_York')"
    )
    priority: Priority = Field(default=Priority.NONE, description="Priority level")
    project_id: str = Field(..., description="Project ID the todo belongs to")
    completed: bool = Field(default=False, description="Whether the todo is completed")
    subtasks: List[SubTask] = Field(
        default_factory=list, description="List of subtasks"
    )
    workflow_id: Optional[str] = Field(
        None, description="ID of the associated workflow"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ProjectModel(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the project"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Description of the project"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9A-Fa-f]{6}$",
        description="Color code for the project in hex format",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectCreate(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the project"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Description of the project"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9A-Fa-f]{6}$",
        description="Color code for the project in hex format",
    )


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Name of the project"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Description of the project"
    )
    color: Optional[str] = Field(
        None,
        pattern="^#[0-9A-Fa-f]{6}$",
        description="Color code for the project in hex format",
    )


class ProjectResponse(BaseModel):
    id: str = Field(..., description="Unique identifier")
    user_id: str = Field(..., description="User ID who owns the project")
    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")
    color: Optional[str] = Field(None, description="Color code for the project")
    is_default: bool = Field(
        default=False, description="Whether this is the default Inbox project"
    )
    todo_count: int = Field(default=0, description="Number of todos in this project")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SubtaskCreateRequest(BaseModel):
    title: str


class SubtaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None


class PaginationMeta(BaseModel):
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page (1-based)")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")


class TodoStats(BaseModel):
    total: int = Field(default=0)
    completed: int = Field(default=0)
    pending: int = Field(default=0)
    overdue: int = Field(default=0)
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_project: dict[str, int] = Field(default_factory=dict)
    completion_rate: float = Field(default=0.0)
    labels: Optional[List[dict]] = Field(default=None)


class TodoListResponse(BaseModel):
    data: List[TodoResponse]
    meta: PaginationMeta
    stats: Optional[TodoStats] = None


class SearchMode(str, Enum):
    TEXT = "text"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class TodoSearchParams(BaseModel):
    q: Optional[str] = Field(None, description="Search query")
    mode: SearchMode = Field(default=SearchMode.HYBRID, description="Search mode")
    project_id: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[Priority] = None
    has_due_date: Optional[bool] = None
    overdue: Optional[bool] = None
    due_date_start: Optional[datetime] = None
    due_date_end: Optional[datetime] = None
    labels: Optional[List[str]] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=100)
    include_stats: bool = Field(default=False)


class BulkOperationRequest(BaseModel):
    todo_ids: List[str] = Field(..., min_length=1, max_length=100)


class BulkUpdateRequest(BulkOperationRequest):
    updates: UpdateTodoRequest


class BulkMoveRequest(BulkOperationRequest):
    project_id: str


class BulkOperationResponse(BaseModel):
    success: List[str] = Field(default_factory=list)
    failed: List[dict] = Field(default_factory=list)
    total: int
    message: str
