"""
Clean and lean workflow models for GAIA workflow system.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class WorkflowStatus(str, Enum):
    """Status of workflow processing and execution."""

    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    ACTIVE = "active"
    INACTIVE = "inactive"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TriggerType(str, Enum):
    """Type of workflow trigger."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    EMAIL = "email"
    CALENDAR = "calendar"


class WorkflowStep(BaseModel):
    """A single step in a workflow."""

    id: str = Field(description="Unique identifier for the step")
    title: str = Field(description="Clear, actionable title for the step")
    tool_name: str = Field(description="Specific tool to be used")
    tool_category: str = Field(default="general", description="Category of the tool")
    description: str = Field(
        description="Detailed description of what this step accomplishes"
    )
    tool_inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Expected inputs for the tool"
    )
    order: int = Field(description="Order of execution (0-based)")
    status: WorkflowStatus = Field(default=WorkflowStatus.READY)
    executed_at: Optional[datetime] = Field(default=None)
    result: Optional[Dict[str, Any]] = Field(default=None)

    @classmethod
    def create_step(
        cls,
        step_number: int,
        title: str,
        tool_name: str,
        description: str,
        tool_inputs: Optional[Dict[str, Any]] = None,
    ):
        """Create a workflow step with auto-generated ID."""
        return cls(
            id=f"step_{step_number}",
            title=title,
            tool_name=tool_name,
            description=description,
            tool_inputs=tool_inputs or {},
            order=step_number,
        )


class TriggerConfig(BaseModel):
    """Configuration for workflow triggers."""

    type: TriggerType = Field(description="Type of trigger")
    enabled: bool = Field(default=True, description="Whether the trigger is enabled")

    # Schedule configuration
    cron_expression: Optional[str] = Field(
        default=None, description="Cron expression for scheduled workflows"
    )
    timezone: Optional[str] = Field(
        default="UTC", description="Timezone for scheduled execution"
    )
    next_run: Optional[datetime] = Field(
        default=None, description="Next scheduled execution time"
    )

    # Email trigger configuration
    email_patterns: Optional[List[str]] = Field(
        default=None, description="Email patterns to match"
    )

    # Calendar trigger configuration
    calendar_patterns: Optional[List[str]] = Field(
        default=None, description="Calendar event patterns"
    )


class Workflow(BaseModel):
    """Main workflow model."""

    id: str = Field(
        default_factory=lambda: f"wf_{uuid.uuid4().hex[:12]}",
        description="Unique identifier",
    )
    title: str = Field(min_length=1, description="Title of the workflow")
    description: str = Field(
        min_length=1, description="Description of what this workflow aims to accomplish"
    )
    steps: List[WorkflowStep] = Field(
        description="List of workflow steps to execute", min_length=1, max_length=10
    )

    # Configuration
    trigger_config: TriggerConfig = Field(description="Trigger configuration")

    # Status and tracking
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    user_id: str = Field(description="ID of the user who owns this workflow")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_executed_at: Optional[datetime] = Field(default=None)

    # Execution tracking
    current_step_index: int = Field(
        default=0, description="Index of currently executing step"
    )
    execution_logs: List[str] = Field(
        default_factory=list, description="Execution logs"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if workflow failed"
    )

    # Statistics
    total_executions: int = Field(default=0, description="Total number of executions")
    successful_executions: int = Field(
        default=0, description="Number of successful executions"
    )


# Request/Response models for API


class CreateWorkflowRequest(BaseModel):
    """Request model for creating a new workflow."""

    title: str = Field(min_length=1, description="Title of the workflow")
    description: str = Field(
        min_length=1, description="Description of what the workflow should accomplish"
    )
    trigger_config: TriggerConfig = Field(description="Trigger configuration")
    generate_immediately: bool = Field(
        default=False, description="Generate steps immediately vs background"
    )

    @field_validator("title", "description")
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or contain only whitespace")
        return v.strip()


class UpdateWorkflowRequest(BaseModel):
    """Request model for updating an existing workflow."""

    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    steps: Optional[List[WorkflowStep]] = Field(default=None)
    trigger_config: Optional[TriggerConfig] = Field(default=None)
    status: Optional[WorkflowStatus] = Field(default=None)


class WorkflowResponse(BaseModel):
    """Response model for workflow operations."""

    workflow: Workflow
    message: str = Field(description="Success or status message")


class WorkflowListResponse(BaseModel):
    """Response model for listing workflows."""

    workflows: List[Workflow]


class WorkflowExecutionRequest(BaseModel):
    """Request model for executing a workflow."""

    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context for execution"
    )


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""

    execution_id: str = Field(description="Unique ID for this execution")
    status: WorkflowStatus
    message: str


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status checks."""

    workflow_id: str
    status: WorkflowStatus
    current_step_index: int
    total_steps: int
    progress_percentage: float
    last_updated: datetime
    error_message: Optional[str] = Field(default=None)
    logs: List[str] = Field(default_factory=list)
