"""Today's message: one structured model call, checked for repetition.

The call is schema-bound, so there is no prose to parse and no way to half-fail
into a generic greeting. A draft that repeats an earlier day is rejected and
retried once with the reason; a second repeat, or a failed call, means the day
is skipped. Sending nothing is strictly better than sending yesterday again.
"""

from app.agents.llm.client import LLMInvokeOptions, ainvoke_llm, background_structured_runnable
from app.agents.prompts.activation_prompts import build_activation_prompt
from app.models.activation_models import MAX_WORDS_PER_BUBBLE, ActivationDraft
from app.services.activation.policy import Direction
from app.services.activation.uniqueness import repeats_earlier
from shared.py.wide_events import log

#: Wall-clock ceiling for one draft. A morning message that arrives at noon is
#: not the feature, so a slow provider is a skipped day, not a late send.
DRAFT_TIMEOUT_SECONDS = 45
#: Drafts per day: the first, plus one rewrite when the first repeats an earlier
#: day. A third attempt buys nothing — a model that has repeated itself twice
#: with the reason in front of it is not going to find a new idea on try three.
MAX_DRAFTS = 2


class ActivationCopyError(Exception):
    """No sendable draft today. The caller skips the day; it never sends a fallback."""


def _too_long(draft: ActivationDraft) -> bool:
    return any(len(bubble.split()) > MAX_WORDS_PER_BUBBLE for bubble in draft.bubbles)


async def draft_message(
    *,
    day: int,
    direction: Direction,
    who_block: str,
    integrations_block: str,
    yesterday_block: str,
    already_sent_block: str,
    earlier: list[tuple[str, str]],
) -> ActivationDraft:
    """One day's message, or raise :class:`ActivationCopyError`.

    ``earlier`` is ``(first bubble, suggestion)`` per earlier day; it is both
    shown to the model and used to reject the answer, because the second is what
    actually holds.
    """
    reason: str | None = None
    for attempt in range(MAX_DRAFTS):
        prompt = build_activation_prompt(
            day=day,
            direction=direction,
            who_block=who_block,
            integrations_block=integrations_block,
            yesterday_block=yesterday_block,
            already_sent_block=already_sent_block,
            retry_reason=reason,
        )
        draft: ActivationDraft = await ainvoke_llm(
            background_structured_runnable(ActivationDraft),
            prompt,
            label="activation_sequence",
            options=LLMInvokeOptions(max_attempts=2, timeout=DRAFT_TIMEOUT_SECONDS),
        )
        reason = repeats_earlier(draft.bubbles[0], draft.suggestion, earlier)
        if reason is None and _too_long(draft):
            reason = "too_long"
        if reason is None:
            log.set(draft_attempts=attempt + 1)
            return draft
        log.set(draft_rejected=reason)
    raise ActivationCopyError(
        f"no unique draft for day {day} after {MAX_DRAFTS} attempts: {reason}"
    )
