"""Shapes the activation sequence writes down and reads back.

One module because the drafted message, the persisted record and the state
subdoc are the same object at three moments: the model produces
:class:`ActivationDraft`, the task stamps it into :class:`ActivationMessage`,
and tomorrow's run reads the list of those back out of
:class:`ActivationSequenceState` to avoid repeating itself.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.services.activation.policy import Direction

#: Bubbles per message. One is the norm; two is the ceiling, because a third
#: bubble is where a text stops being a text and becomes a newsletter.
MAX_BUBBLES = 2
#: Words per bubble. Above this the message gets scrolled past, not read.
MAX_WORDS_PER_BUBBLE = 60


class ActivationDraft(BaseModel):
    """What the model is asked to return: a text, and the one thing it suggests.

    ``suggestion`` is not shown to the user — it is the same idea in a plain
    sentence, so the repetition check can compare ideas across days instead of
    comparing prose that has been deliberately varied.
    """

    bubbles: list[str] = Field(
        ..., min_length=1, max_length=MAX_BUBBLES, description="The chat bubbles to send, in order"
    )
    suggestion: str = Field(
        ...,
        min_length=1,
        description="The single concrete thing this message suggests, in one plain sentence",
    )
    connect_target: str | None = Field(
        None,
        description="The integration id this message asked them to connect, or null",
    )


class ActivationMessage(BaseModel):
    """One delivered day of the sequence, as stored on the user document."""

    day: int
    direction: Direction
    platform: str
    sent_at: datetime
    bubbles: list[str]
    suggestion: str
    connect_target: str | None = None


class ActivationSequenceState(BaseModel):
    """The ``users.activation_sequence`` subdoc, read back at the start of a run."""

    day_sent: int = 0
    last_sent_at: datetime | None = None
    platform: str | None = None
    opted_out: bool = False
    messages: list[ActivationMessage] = Field(default_factory=list)

    @classmethod
    def of(cls, raw: dict[str, Any] | None) -> "ActivationSequenceState":
        """The state on a user document, or a fresh one when the field is unset."""
        return cls.model_validate(raw) if raw else cls()

    def earlier_drafts(self) -> list[tuple[str, str]]:
        """``(first bubble, suggestion)`` per earlier day, oldest first."""
        return [(m.bubbles[0] if m.bubbles else "", m.suggestion) for m in self.messages]

    def connect_targets_asked(self) -> set[str]:
        """Integrations an earlier day already asked them to connect."""
        return {m.connect_target for m in self.messages if m.connect_target}

    def connect_asks(self) -> int:
        """Earlier days that asked for a connection."""
        return sum(1 for m in self.messages if m.direction is Direction.CONNECT)

    def unanswered_days(self) -> int:
        """Trailing days the user never replied to. A reply shows up as the next
        day being CONTINUE_THREAD, so the streak is counted back from the end."""
        streak = 0
        for message in reversed(self.messages):
            if message.direction is Direction.CONTINUE_THREAD:
                break
            streak += 1
        return streak

    def handover_asks(self) -> int:
        """Trailing HANDOVER days inside the unanswered streak."""
        streak = self.messages[len(self.messages) - self.unanswered_days() :]
        return sum(1 for m in streak if m.direction is Direction.HANDOVER)


class ActivationSequenceUpdate(BaseModel):
    """The settings toggle's request body."""

    opted_out: bool = Field(..., description="Whether to stop the daily activation messages")


class ActivationSequenceResponse(BaseModel):
    """The state after the toggle, echoed so the UI does not re-fetch."""

    opted_out: bool
