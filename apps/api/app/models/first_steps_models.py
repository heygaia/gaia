from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FirstStepKey(StrEnum):
    """The activation checklist, in display order. Mirrored by the web."""

    SAY_HI = "say_hi"
    CONNECT_INTEGRATION = "connect_integration"
    LINK_PLATFORM = "link_platform"
    CREATE_WORKFLOW = "create_workflow"
    PUBLISH_WORKFLOW = "publish_workflow"


class FirstStep(BaseModel):
    key: FirstStepKey
    done: bool = Field(description="Derived server-side from a real signal at read time")


class FirstStepsResponse(BaseModel):
    steps: list[FirstStep] = Field(description="Every step, in checklist order")
    dismissed: bool = Field(description="Whether the user hid the checklist")


class FirstStepsState(BaseModel):
    """The ``users.first_steps`` subdocument — only the dismissal is persisted."""

    dismissed: bool = False
    dismissed_at: datetime | None = None
