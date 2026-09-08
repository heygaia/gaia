"""Pydantic schemas for Resia voice-call and SMS responses."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CallOutcome = Literal["achieved", "partial", "not_achieved", "unclear"]


class TranscriptTurn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: str
    content: str = ""


class CallPlaced(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    call_id: str = Field(alias="id")
    status: str = "queued"


class CallRead(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    call_id: str = Field(alias="id")
    status: str
    to_phone_number: str | None = None
    outcome: CallOutcome | None = None
    summary: str | None = None
    duration_secs: float | None = None
    charged_cents: int | None = Field(alias="charge_amount_in_cents", default=None)
    failure_code: str | None = None
    transcript: list[TranscriptTurn] = Field(default_factory=list)


class TextMessagePlaced(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text_message_id: str
    to_phone_number: str
    status: str


class RejectedEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    position: int = 0
    to_phone_number: str = ""
    reason: str = ""


class TextBatchPlaced(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    batch_id: str = Field(alias="id")
    status: str = "in_progress"
    messages: list[TextMessagePlaced] = Field(alias="text_messages", default_factory=list)
    rejected: list[RejectedEntry] = Field(alias="rejected_text_messages", default_factory=list)


class TextBatchCounts(BaseModel):
    model_config = ConfigDict(extra="ignore")

    queued: int = 0
    canceled: int = 0
    sent: int = 0
    delivered: int = 0
    delivery_unconfirmed: int = 0
    failed: int = 0


class TextBatchRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = "unknown"
    counts: TextBatchCounts = Field(default_factory=TextBatchCounts)
    total: int = 0
