"""
Workflow models for task scheduling system.
"""

from typing import Optional

from app.models.arq_event_models import (
    CreateEventRequestModel,
    EventModel,
    UpdateEventRequestModel,
)
from pydantic import BaseModel, Field


class WorkflowPayload(BaseModel):
    """Payload for STATIC agent workflows."""

    instructions: str = Field(
        ...,
        description="Detailed instructions for the workflow task",
    )
    context: Optional[str] = Field(
        None,
        description="Optional context or additional information for the workflow",
    )


class WorkflowModel(EventModel):
    """
    Workflow document model for MongoDB.

    Represents a scheduled task that can be one-time or recurring.
    """

    payload: WorkflowPayload = Field(
        ..., description="Task-specific data based on agent type"
    )


class CreateWorkflowRequest(CreateEventRequestModel):
    """Request model for creating a new workflow."""

    payload: WorkflowPayload = Field(
        ..., description="Task-specific data based on agent type"
    )


class UpdateWorkflowRequest(UpdateEventRequestModel):
    """Request model for updating an existing workflow."""

    payload: Optional[WorkflowPayload] = Field(
        None, description="Task-specific data (optional)"
    )


class WorkflowResponse(EventModel):
    """Response model for workflow operations."""

    payload: WorkflowPayload = Field(..., description="Task-specific data")


class WorkflowProcessingAgentResult(BaseModel):
    """Result model for workflow processing by AI agents."""

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
            "It should contain the actual output or summary of the workflow task. "
            "Be professional and helpful—avoid filler phrases like 'Sure, here's the thing' or conversational fluff."
        ),
    )
