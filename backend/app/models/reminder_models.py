"""
Reminder models for task scheduling system.
"""

from typing import Optional

from app.models.arq_event_models import (
    CreateEventRequestModel,
    EventModel,
    UpdateEventRequestModel,
)
from pydantic import BaseModel, Field


class ReminderPayload(BaseModel):
    """Payload for STATIC agent reminders."""

    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")


class ReminderModel(EventModel):
    """
    Reminder document model for MongoDB.

    Represents a scheduled task that can be one-time or recurring.
    """

    payload: ReminderPayload = Field(
        ..., description="Task-specific data based on agent type"
    )


class CreateReminderRequest(CreateEventRequestModel):
    """Request model for creating a new reminder."""

    payload: ReminderPayload = Field(
        ..., description="Task-specific data based on agent type"
    )


class UpdateReminderRequest(UpdateEventRequestModel):
    """Request model for updating an existing reminder."""

    payload: Optional[ReminderPayload] = Field(
        None, description="Task-specific data (optional)"
    )


class ReminderResponse(EventModel):
    """Response model for reminder operations."""

    payload: ReminderPayload = Field(..., description="Task-specific data")


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
