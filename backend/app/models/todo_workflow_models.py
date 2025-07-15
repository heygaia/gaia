"""Structured models for workflow generation using Pydantic."""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import uuid


class WorkflowStep(BaseModel):
    """A single step in a workflow."""

    id: str = Field(description="Unique identifier for the step")
    title: str = Field(description="Clear, actionable title for the step")
    tool_name: str = Field(
        description="Specific tool to be used (e.g., 'web_search_tool', 'create_todo')"
    )
    tool_category: str = Field(
        description="Category of the tool (mail, calendar, search, productivity, documents, weather, goal_tracking)"
    )
    description: str = Field(
        description="Detailed description of what this step accomplishes"
    )
    tool_inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Expected inputs for the tool"
    )

    @classmethod
    def create_step(
        cls,
        step_number: int,
        title: str,
        tool_name: str,
        tool_category: str,
        description: str,
        tool_inputs: Optional[Dict[str, Any]] = None,
    ):
        """Create a workflow step with auto-generated ID."""
        return cls(
            id=f"step_{step_number}",
            title=title,
            tool_name=tool_name,
            tool_category=tool_category,
            description=description,
            tool_inputs=tool_inputs or {},
        )


class WorkflowPlan(BaseModel):
    """Complete workflow plan for a TODO item."""

    workflow_id: str = Field(
        default_factory=lambda: f"wf_{uuid.uuid4().hex[:8]}",
        description="Unique identifier for the workflow",
    )
    title: str = Field(description="Title of the workflow")
    steps: List[WorkflowStep] = Field(
        description="List of workflow steps to complete the todo",
        min_length=2,
        max_length=4,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "wf_abc12345",
                "title": "Workflow for: Plan vacation",
                "steps": [
                    {
                        "id": "step_1",
                        "title": "Research vacation destinations",
                        "tool_name": "web_search_tool",
                        "tool_category": "search",
                        "description": "Search for popular vacation destinations and travel guides",
                        "tool_inputs": {"query": "best vacation destinations 2025"},
                    },
                    {
                        "id": "step_2",
                        "title": "Check weather forecast",
                        "tool_name": "get_weather",
                        "tool_category": "weather",
                        "description": "Get weather information for potential destinations",
                        "tool_inputs": {"location": "destination_city"},
                    },
                ],
            }
        }
