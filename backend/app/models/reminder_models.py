"""
Reminder models for task scheduling system.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_serializer, field_validator


class ReminderStatus(str, Enum):
    """Status of a reminder."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class AgentType(str, Enum):
    """Agent type handling the reminder task."""

    STATIC = "static"
    AI_AGENT = "ai_agent"
    EMAIL_SUMMARY = "email_summary"


class StaticReminderPayload(BaseModel):
    """Payload for STATIC agent reminders."""

    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")


class AIAgentReminderPayload(BaseModel):
    """Payload for AI_AGENT reminders."""

    instructions: str = Field(
        ..., description="Special instructions for reminder generation"
    )


class EmailSummaryReminderPayload(BaseModel):
    """Payload for EMAIL_SUMMARY agent reminders."""

    important_only: bool = Field(
        default=True, description="Whether to include only important emails"
    )


class ReminderModel(BaseModel):
    """
    Reminder document model for MongoDB.

    Represents a scheduled task that can be one-time or recurring.
    """

    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="User ID who owns this reminder")
    agent: AgentType = Field(
        ..., description="Agent responsible for this reminder task"
    )
    repeat: Optional[str] = Field(
        None, description="Cron expression for recurring tasks"
    )
    scheduled_at: datetime = Field(..., description="Next scheduled execution time")
    status: ReminderStatus = Field(
        default=ReminderStatus.SCHEDULED, description="Current status"
    )
    occurrence_count: int = Field(
        default=0, description="Number of times this reminder has been executed"
    )
    max_occurrences: Optional[int] = Field(
        None, description="Maximum number of executions (optional)"
    )
    stop_after: Optional[datetime] = Field(
        default=datetime.now(timezone.utc) + timedelta(days=180),
        description="Stop executing after this date (optional), defaults to 6 months from now",
    )
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for AI agent reminders to track outputs"
    )
    payload: Union[
        StaticReminderPayload,
        AIAgentReminderPayload,
        EmailSummaryReminderPayload,
        Dict[str, Any],
    ] = Field(..., description="Task-specific data based on agent type")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    @field_validator("scheduled_at", "stop_after", "created_at", "updated_at")
    @classmethod
    def ensure_timezone_aware(cls, v):
        """Ensure datetime fields are timezone-aware (UTC if no timezone)."""
        if v is not None and v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @field_serializer("scheduled_at", "stop_after", "created_at", "updated_at")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format strings."""
        if value is not None:
            return value.isoformat()
        return None

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class CreateReminderRequest(BaseModel):
    """Request model for creating a new reminder."""

    agent: AgentType = Field(
        ..., description="Agent handling the reminder task (static or ai_agent)"
    )
    repeat: Optional[str] = Field(
        None, description="Cron expression for recurring tasks (optional)"
    )
    scheduled_at: Optional[datetime] = Field(
        None, description="First execution time (optional, defaults to None)"
    )
    max_occurrences: Optional[int] = Field(
        None, description="Maximum number of executions (optional)"
    )
    stop_after: Optional[datetime] = Field(
        None, description="Stop executing after this date (optional)"
    )
    payload: Union[
        StaticReminderPayload, AIAgentReminderPayload, EmailSummaryReminderPayload
    ] = Field(..., description="Task-specific data based on agent type")
    base_time: Optional[datetime] = Field(
        None,
        description="Base time for handling time zones and scheduling (optional, defaults to None)",
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID for AI agent reminders (optional, auto-generated if not provided)",
    )

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

    @field_serializer("scheduled_at", "stop_after", "base_time")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format strings."""
        if value is not None:
            return value.isoformat()
        return None


class UpdateReminderRequest(BaseModel):
    """Request model for updating an existing reminder."""

    agent: Optional[AgentType] = Field(
        None, description="Agent handling the reminder task (optional)"
    )
    repeat: Optional[str] = Field(
        None, description="Cron expression for recurring tasks"
    )
    scheduled_at: Optional[datetime] = Field(None, description="Next execution time")
    status: Optional[ReminderStatus] = Field(None, description="Current status")
    max_occurrences: Optional[int] = Field(
        None, description="Maximum number of executions"
    )
    stop_after: Optional[datetime] = Field(
        None, description="Stop executing after this date"
    )
    payload: Optional[Union[StaticReminderPayload, AIAgentReminderPayload]] = Field(
        None, description="Task-specific data (optional)"
    )
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for AI agent reminders (optional)"
    )

    @field_validator("repeat")
    @classmethod
    def check_repeat_cron(cls, v):
        from app.utils.cron_utils import validate_cron_expression

        if v is not None and not validate_cron_expression(v):
            raise ValueError(f"Invalid cron expression: {v}")
        return v

    @field_validator("scheduled_at", "stop_after")
    @classmethod
    def ensure_timezone_aware(cls, v):
        """Ensure datetime fields are timezone-aware (UTC if no timezone)."""
        if v is not None and v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("max_occurrences")
    @classmethod
    def check_max_occurrences(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_occurrences must be greater than 0")
        return v

    @field_validator("stop_after")
    @classmethod
    def check_stop_after_future(cls, v):
        from datetime import datetime

        if v is not None:
            # Ensure timezone-aware datetime
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)

            if v <= datetime.now(timezone.utc):
                raise ValueError("stop_after must be in the future")
        return v

    @field_serializer("scheduled_at", "stop_after")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format strings."""
        if value is not None:
            return value.isoformat()
        return None


class ReminderResponse(BaseModel):
    """Response model for reminder operations."""

    id: str = Field(..., description="Reminder ID")
    user_id: str = Field(..., description="User ID who owns this reminder")
    agent: AgentType = Field(
        ..., description="Agent responsible for this reminder task"
    )
    repeat: Optional[str] = Field(
        None, description="Cron expression for recurring tasks"
    )
    scheduled_at: datetime = Field(..., description="Next scheduled execution time")
    status: ReminderStatus = Field(..., description="Current status")
    occurrence_count: int = Field(
        ..., description="Number of times this reminder has been executed"
    )
    max_occurrences: Optional[int] = Field(
        None, description="Maximum number of executions"
    )
    stop_after: Optional[datetime] = Field(
        None, description="Stop executing after this date"
    )
    payload: Union[
        StaticReminderPayload,
        AIAgentReminderPayload,
        EmailSummaryReminderPayload,
        Dict[str, Any],
    ] = Field(..., description="Task-specific data")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for AI agent reminders"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @field_serializer("scheduled_at", "stop_after", "created_at", "updated_at")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format strings."""
        if value is not None:
            return value.isoformat()
        return None


class ReminderProcessingAgentResult(BaseModel):
    """Result model for reminder processing by AI agents."""

    title: str = Field(
        ...,
        description="Short, clear title for the user-facing notification. No filler—just the key point.",
    )
    body: str = Field(
        ...,
        description="Notification body shown to the user. Keep it direct, informative, and useful. Avoid fluff like 'Here's what you asked for.'",
    )
    message: str = Field(
        ...,
        description=(
            "The complete message that will be added to the user’s conversation thread. "
            "It should contain the actual output or summary of the reminder task. "
            "Be professional and helpful—avoid filler phrases like 'Sure, here's the thing' or conversational fluff."
        ),
    )
