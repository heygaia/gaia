"""Event models for the event system."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from app.utils.cron_utils import get_next_run_time
from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


class EventType(str, Enum):
    """Enumeration for different event types."""

    REMINDER = "reminder"
    WORKFLOW = "workflow"


class EventStatus(str, Enum):
    """Event status enumeration."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    FAILED = "failed"


class CreateEventRequestModel(BaseModel):
    repeat: Optional[str] = Field(
        None, description="Cron expression for recurring events"
    )
    scheduled_at: Optional[datetime] = Field(
        None, description="Time when the event should first execute"
    )
    max_occurrences: Optional[int] = Field(
        None, description="Maximum number of event executions"
    )
    stop_after: Optional[datetime] = Field(
        None, description="Do not execute after this date"
    )
    base_time: datetime = Field(
        ..., description="Reference time for scheduling calculations"
    )
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for AI agent reminders (optional)"
    )

    @model_validator(mode="after")
    @classmethod
    def calculate_scheduled_at(cls, values):
        """Calculate scheduled_at if not provided."""
        if values.scheduled_at is None and values.repeat:
            values.scheduled_at = get_next_run_time(
                cron_expr=values.repeat, base_time=values.base_time
            )
        elif values.scheduled_at is None:
            raise ValueError("Either scheduled_at or repeat must be specified")
        return values

    @field_validator("repeat")
    @classmethod
    def check_repeat_cron(cls, v):
        from app.utils.cron_utils import validate_cron_expression

        if v is not None and not validate_cron_expression(v):
            raise ValueError(f"Invalid cron expression: {v}")
        return v

    @field_validator("max_occurrences")
    @classmethod
    def check_max_occurrences(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_occurrences must be greater than 0")
        return v

    @field_validator("stop_after", "scheduled_at")
    @classmethod
    def check_after_future(cls, v):
        if v is not None:
            # Ensure timezone-aware datetime
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)

            if v <= datetime.now(timezone.utc):
                raise ValueError("stop_after and scheduled_at must be in the future")
        return v

    @field_validator("scheduled_at", "stop_after", "base_time")
    @classmethod
    def ensure_timezone_aware(cls, v):
        """Ensure datetime fields are timezone-aware (UTC if no timezone)."""
        if v is not None and v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @field_serializer("scheduled_at", "stop_after", "base_time")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format strings."""
        if value is not None:
            return value.isoformat()
        return None

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class UpdateEventRequestModel(BaseModel):
    """Request model for updating an event."""

    repeat: Optional[str] = Field(
        None, description="Cron expression for recurring events"
    )
    max_occurrences: Optional[int] = Field(
        None, description="Maximum number of event executions"
    )
    stop_after: Optional[datetime] = Field(
        None, description="Do not execute after this date"
    )
    status: Optional[EventStatus] = Field(None, description="Updated event status")

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last event update",
    )

    @field_validator("repeat")
    @classmethod
    def check_repeat_cron(cls, v):
        from app.utils.cron_utils import validate_cron_expression

        if v is not None and not validate_cron_expression(v):
            raise ValueError(f"Invalid cron expression: {v}")
        return v

    @field_validator("stop_after")
    @classmethod
    def check_stop_after_future(cls, v):
        if v is not None:
            # Ensure timezone-aware datetime
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)

            if v <= datetime.now(timezone.utc):
                raise ValueError("stop_after must be in the future")
        return v

    @field_validator("max_occurrences")
    @classmethod
    def check_max_occurrences(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_occurrences must be greater than 0")
        return v

    @field_validator("stop_after")
    @classmethod
    def ensure_timezone_aware(cls, v):
        """Ensure datetime fields are timezone-aware (UTC if no timezone)."""
        if v is not None and v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @field_serializer("stop_after")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format strings."""
        if value is not None:
            return value.isoformat()
        return None

    class Config:
        extra = "ignore"


class EventModel(BaseModel):
    """Main event model."""

    id: Optional[str] = Field(
        default=None, description="Unique event identifier", alias="_id"
    )
    user_id: str = Field(..., description="ID of the user who owns this event")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for AI agent reminders to track outputs"
    )
    payload: Any = Field(..., description="Task-specific data based on agent type")
    status: EventStatus = Field(
        EventStatus.SCHEDULED, description="Current event status"
    )

    # Scheduling fields
    repeat: Optional[str] = Field(
        None, description="Cron expression for recurring events"
    )
    scheduled_at: datetime = Field(description="Time the event should execute")
    max_occurrences: Optional[int] = Field(
        None, description="Maximum number of executions"
    )
    stop_after: Optional[datetime] = Field(
        None, description="Do not execute after this date"
    )
    base_time: datetime = Field(
        ..., description="Reference time for scheduling calculations"
    )

    # Execution tracking
    current_execution_count: int = Field(
        0, description="Number of times this event has executed"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of event creation",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last event update",
    )

    @field_serializer(
        "scheduled_at", "stop_after", "created_at", "updated_at", "base_time"
    )
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format strings."""
        if value is not None:
            return value.isoformat()
        return None

    class Config:
        extra = "allow"
        use_enum_values = True
        populate_by_name = True


class EventListResponseModel(BaseModel):
    """Response model for listing events."""

    events: List[EventModel]
    total: int
    skip: int
    limit: int

    class Config:
        extra = "allow"


class EventProcessResponseModel(BaseModel):
    """Response model for processing an event."""

    status: EventStatus
    reschedule: bool
    current_execution_count: int
    scheduled_at: Optional[datetime] = None

    @model_validator(mode="after")
    @classmethod
    def validate_reschedule(cls, values):
        """Ensure reschedule is True if scheduled_at is provided."""
        if values.get("reschedule") and not values.get("scheduled_at"):
            raise ValueError("scheduled_at must be provided if reschedule is True")
        return values

    @field_serializer("scheduled_at")
    def serialize_scheduled_at(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize scheduled_at to ISO format string."""
        if value is not None:
            return value.isoformat()
        return None
