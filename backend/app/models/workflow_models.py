"""
Clean and lean workflow models for GAIA workflow system.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.config.loggers import general_logger as logger
from app.models.scheduler_models import BaseScheduledTask
from pydantic import BaseModel, Field, field_validator


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

    def calculate_next_run(
        self, base_time: Optional[datetime] = None, user_timezone: Optional[str] = None
    ) -> Optional[datetime]:
        """
        Calculate the next run time based on cron expression with timezone awareness.

        Args:
            base_time: Base time for calculation (defaults to current UTC)
            user_timezone: User's timezone for cron calculation (defaults to trigger config timezone)

        Returns:
            Next run time in UTC
        """
        if self.type != TriggerType.SCHEDULE or not self.cron_expression:
            return None

        from app.utils.cron_utils import get_next_run_time
        from datetime import timezone as dt_timezone
        import pytz
        from typing import Union

        try:
            # Use user_timezone parameter, fallback to trigger config timezone, then UTC
            tz_name = user_timezone or self.timezone or "UTC"

            # Convert timezone name to timezone object
            tz: Union[dt_timezone, pytz.BaseTzInfo]
            if tz_name == "UTC":
                tz = dt_timezone.utc
            else:
                tz = pytz.timezone(tz_name)

            # If base_time is provided, convert it to the user's timezone for cron calculation
            if base_time:
                if base_time.tzinfo is None:
                    base_time = base_time.replace(tzinfo=dt_timezone.utc)
                # Convert to user timezone for cron calculation
                if tz_name != "UTC":
                    base_time = base_time.astimezone(tz)
            else:
                # Current time in user's timezone
                if tz_name == "UTC":
                    base_time = datetime.now(dt_timezone.utc)
                else:
                    base_time = datetime.now(tz)

            # Calculate next run time using timezone-aware base_time
            next_run = get_next_run_time(self.cron_expression, base_time, tz_name)

            # Ensure result is in UTC for storage
            if next_run.tzinfo != dt_timezone.utc:
                next_run = next_run.astimezone(dt_timezone.utc)

            return next_run
        except Exception as e:
            logger.error(f"Error calculating next run time: {e}")
            return None

    def update_next_run(
        self, base_time: Optional[datetime] = None, user_timezone: Optional[str] = None
    ) -> bool:
        """
        Update the next_run field with timezone awareness and return True if changed.

        Args:
            base_time: Base time for calculation
            user_timezone: User's timezone for cron calculation

        Returns:
            True if next_run was updated
        """
        old_next_run = self.next_run
        self.next_run = self.calculate_next_run(base_time, user_timezone)
        return old_next_run != self.next_run

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, v):
        """Validate cron expression if provided."""
        if v is not None:
            from app.utils.cron_utils import validate_cron_expression

            if not validate_cron_expression(v):
                raise ValueError(f"Invalid cron expression: {v}")
        return v


class Workflow(BaseScheduledTask):
    """Main workflow model extending BaseScheduledTask for scheduling capabilities."""

    # Override ID generation for workflows - always generate ID
    id: Optional[str] = Field(
        default_factory=lambda: f"wf_{uuid.uuid4().hex[:12]}",
        description="Unique identifier",
    )

    user_id: str = Field(..., description="User ID who owns this workflow")

    title: str = Field(min_length=1, description="Title of the workflow")
    description: str = Field(
        min_length=1, description="Description of what this workflow aims to accomplish"
    )
    steps: List[WorkflowStep] = Field(
        description="List of workflow steps to execute", max_length=10
    )

    # Configuration
    trigger_config: TriggerConfig = Field(description="Trigger configuration")

    # Workflow-specific fields
    activated: bool = Field(
        default=True,
        description="Whether the workflow is activated and can be executed",
    )
    last_executed_at: Optional[datetime] = Field(default=None)

    # Community features
    is_public: bool = Field(
        default=False,
        description="Whether this workflow is published to the community marketplace",
    )
    created_by: Optional[str] = Field(
        default=None,
        description="User ID of the original creator (for public workflows)",
    )
    upvotes: int = Field(
        default=0, description="Number of upvotes from community users"
    )
    upvoted_by: List[str] = Field(
        default_factory=list,
        description="List of user IDs who have upvoted this workflow",
    )

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

    def __init__(self, **data):
        """Initialize workflow with mapping from trigger_config to BaseScheduledTask fields."""
        # Ensure user_id is provided (it's required by BaseScheduledTask)
        if "user_id" not in data:
            raise ValueError("user_id is required for workflow creation")

        # Map trigger_config fields to BaseScheduledTask fields if not provided
        if "trigger_config" in data:
            trigger_config = data["trigger_config"]

            # Handle both dict and TriggerConfig object
            if isinstance(trigger_config, dict):
                # Map scheduled_at from trigger_config.next_run if not provided
                if "scheduled_at" not in data and trigger_config.get("next_run"):
                    data["scheduled_at"] = trigger_config["next_run"]

                # Map repeat from trigger_config.cron_expression if not provided
                if "repeat" not in data and trigger_config.get("cron_expression"):
                    data["repeat"] = trigger_config["cron_expression"]
            else:
                # TriggerConfig is already a Pydantic model
                # Map scheduled_at from trigger_config.next_run if not provided
                if (
                    "scheduled_at" not in data
                    and hasattr(trigger_config, "next_run")
                    and trigger_config.next_run
                ):
                    data["scheduled_at"] = trigger_config.next_run

                # Map repeat from trigger_config.cron_expression if not provided
                if (
                    "repeat" not in data
                    and hasattr(trigger_config, "cron_expression")
                    and trigger_config.cron_expression
                ):
                    data["repeat"] = trigger_config.cron_expression

        # Set default scheduled_at if still not provided
        if "scheduled_at" not in data:
            data["scheduled_at"] = datetime.now(timezone.utc)

        super().__init__(**data)


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
    activated: Optional[bool] = Field(default=None)


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
    message: str


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status checks."""

    workflow_id: str
    activated: bool
    current_step_index: int
    total_steps: int
    progress_percentage: float
    last_updated: datetime
    error_message: Optional[str] = Field(default=None)
    logs: List[str] = Field(default_factory=list)


class RegenerateStepsRequest(BaseModel):
    """Request model for regenerating workflow steps."""

    instruction: str = Field(
        min_length=1, description="Instruction for how to modify the workflow"
    )
    reason: Optional[str] = Field(default=None, description="Reason for regeneration")
    force_different_tools: bool = Field(
        default=False, description="Force the use of different tools"
    )


class PublishWorkflowRequest(BaseModel):
    """Request model for publishing a workflow to the community."""

    workflow_id: str = Field(description="ID of the workflow to publish")


class UnpublishWorkflowRequest(BaseModel):
    """Request model for unpublishing a workflow from the community."""

    workflow_id: str = Field(description="ID of the workflow to unpublish")


class UpvoteWorkflowRequest(BaseModel):
    """Request model for upvoting a community workflow."""

    workflow_id: str = Field(description="ID of the workflow to upvote")


class PublicWorkflowsResponse(BaseModel):
    """Response model for listing public workflows."""

    workflows: List[Dict[str, Any]] = Field(
        description="List of public workflows with creator info"
    )
    total: int = Field(description="Total number of public workflows")


class PublishWorkflowResponse(BaseModel):
    """Response model for publishing a workflow."""

    message: str = Field(description="Success message")
    workflow_id: str = Field(description="ID of the published workflow")
