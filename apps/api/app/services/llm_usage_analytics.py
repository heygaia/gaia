"""The dimensions PostHog's LLM analytics cannot work out for itself.

``posthog.ai.langchain.CallbackHandler`` already emits ``$ai_generation`` for
every call inside an agent graph, with its own token counts and cost. It does
not know what the spend was *for*, where it came *from*, or which workflow
asked for it, and it never sees the auxiliary one-shots that run outside a
graph. This module fills exactly those two gaps and nothing else:

- :func:`graph_call_properties` — extra properties for that existing handler,
  so the graph route stays ONE event.
- :func:`capture_auxiliary_llm_call` — the only new event, for background spend
  the handler is never attached to.

Deliberately not a second event for graph calls: two events over the same calls
would double-count cost, and PostHog already prices that half.
"""

from app.config.model_pricing import has_rate_card
from app.models.chat_models import SourceCategory
from app.services.analytics_service import AIFeature, AnalyticsEvents, capture_event
from app.services.llm_metering import TokenUsage
from shared.py.wide_events import log

#: The two graph tiers. Any other ``agent_name`` is a per-integration subagent,
#: which is what makes integration spend separable.
TIER_AGENT_NAMES = frozenset({"comms_agent", "executor_agent"})

#: Which capability each auxiliary ``label`` belongs to.
#:
#: Keyed on the label every one-shot already passes for its log line, rather
#: than a second argument at each call site: one table is the whole taxonomy,
#: readable at a glance, and adding a helper never means editing a service file
#: for an analytics reason. An unmapped label is not silent — it books to
#: ``UNATTRIBUTED`` and logs an error naming itself.
LABEL_FEATURES: dict[str, AIFeature] = {
    "chatbot": AIFeature.TITLE_GENERATION,
    "file_image_summary": AIFeature.FILE_EXTRACTION,
    "file_text_summary": AIFeature.FILE_EXTRACTION,
    "follow_up_actions": AIFeature.FOLLOW_UPS,
    "hil_conversational_resolve": AIFeature.HIL,
    "hil_conversational_resolve_batch": AIFeature.HIL,
    "hil_intent_judge": AIFeature.HIL,
    "hil_tool_classification": AIFeature.HIL,
    "holo_card": AIFeature.PROFILE,
    "image_to_text": AIFeature.VISION,
    "integration_category": AIFeature.INTEGRATION_INFERENCE,
    "integration_content": AIFeature.INTEGRATION_INFERENCE,
    "mail_compose": AIFeature.MAIL,
    "onboarding_clarify": AIFeature.ONBOARDING,
    "onboarding_first_message": AIFeature.ONBOARDING,
    "onboarding_focus_todos": AIFeature.ONBOARDING,
    "onboarding_inbox_triage": AIFeature.ONBOARDING,
    "onboarding_social_profile": AIFeature.ONBOARDING,
    "onboarding_todos_from_emails": AIFeature.ONBOARDING,
    "onboarding_workflow_suggestions": AIFeature.ONBOARDING,
    "onboarding_writing_style": AIFeature.ONBOARDING,
    "onboarding_writing_style_example": AIFeature.ONBOARDING,
    "playbook_ask_fill": AIFeature.WORKFLOW,
    "playbook_narration": AIFeature.WORKFLOW,
    "profanity": AIFeature.MODERATION,
    "profile_extraction": AIFeature.MEMORY,
    "research_queries": AIFeature.RESEARCH,
    "tool_media_vision": AIFeature.VISION,
    "vision_fallback": AIFeature.VISION,
    "workflow_generation": AIFeature.WORKFLOW_GENERATION,
    "workflow_prompt": AIFeature.WORKFLOW_GENERATION,
}

#: The one label built at runtime rather than written as a literal
#: (``f"memory:{operation}"``), so it cannot be an exact key.
_MEMORY_LABEL_PREFIX = "memory:"


def llm_feature(agent_name: str, workflow_id: str | None) -> AIFeature:
    """Which capability an agent-graph call served.

    ``workflow_id`` wins over the subagent check on purpose: a Gmail subagent
    running inside a workflow is workflow spend that Gmail happens to execute,
    and ``agent_name`` still carries the second half.
    """
    if workflow_id:
        return AIFeature.WORKFLOW
    if agent_name in TIER_AGENT_NAMES:
        return AIFeature.CHAT
    return AIFeature.INTEGRATION


def feature_for_label(label: str) -> AIFeature:
    """Which capability an auxiliary call served, from the label it already carries."""
    if label.startswith(_MEMORY_LABEL_PREFIX):
        return AIFeature.MEMORY
    return LABEL_FEATURES.get(label, AIFeature.UNATTRIBUTED)


def graph_call_properties(
    agent_name: str,
    source: str | None,
    workflow_id: str | None,
) -> dict[str, str]:
    """The feature/surface/workflow properties to stamp onto ``$ai_generation``."""
    properties = {
        "feature": str(llm_feature(agent_name, workflow_id)),
        "surface": SourceCategory.from_source(source).value,
    }
    if workflow_id:
        properties["workflow_id"] = workflow_id
    return properties


def capture_auxiliary_llm_call(
    *,
    user_id: str | None,
    label: str,
    model_name: str,
    usage: TokenUsage,
    cost_usd: float,
) -> None:
    """Emit ``ai:llm_call_completed`` for one background call.

    Auxiliary one-shots (memory, onboarding, follow-ups, title generation) run
    outside any agent graph, so PostHog's own LLM analytics never sees them and
    their spend is invisible. ``user_id`` is explicit because these run outside
    a request context, where the contextvar identity would attribute the event
    to nobody; a call with no user is skipped rather than left anonymous.
    """
    if user_id is None:
        log.warning("llm_call_unattributed", label=label, model=model_name)
        return

    feature = feature_for_label(label)
    if feature is AIFeature.UNATTRIBUTED:
        # A helper was added without a LABEL_FEATURES entry. Loud, and greppable
        # by the label, rather than quietly pooling into another bucket.
        log.error("llm_call_unmapped_label", label=label, model=model_name)

    capture_event(
        user_id,
        AnalyticsEvents.AI_LLM_CALL_COMPLETED,
        {
            "feature": str(feature),
            "surface": SourceCategory.BG.value,
            "label": label,
            "model": model_name,
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "cached_tokens": usage["cached_tokens"],
            "reasoning_tokens": usage["reasoning_tokens"],
            "total_tokens": usage["input_tokens"] + usage["output_tokens"],
            "cost_usd": cost_usd,
            "charged": False,
            # A model missing from the rate card is priced at DEFAULT_PRICING
            # rather than raising, so the dollar figure is plausible and wrong.
            "cost_estimated": not has_rate_card(model_name),
        },
    )
