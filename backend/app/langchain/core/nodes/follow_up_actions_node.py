"""
Follow-up Actions Node for the conversational graph.

This module provides functionality to suggest contextual follow-up actions
to users based on the conversation context and tool usage patterns.
"""

import asyncio
from typing import List

from app.config.loggers import chat_logger as logger
from app.docstrings.langchain.tools.follow_up_actions_tool_docs import (
    SUGGEST_FOLLOW_UP_ACTIONS,
)
from app.langchain.llm.client import init_llm
from app.langchain.prompts.agent_prompts import AGENT_SYSTEM_PROMPT
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from langgraph.store.base import BaseStore
from langgraph_bigtool.graph import State
from pydantic import BaseModel, Field


class FollowUpActions(BaseModel):
    """Data structure for follow-up action suggestions."""

    actions: List[str] = Field(
        description="Array of 3-4 follow-up action suggestions for the user. Each action should be clear, actionable, contextually relevant, and under 50 characters."
    )


llm = init_llm()


async def follow_up_actions_node(
    state: State, config: RunnableConfig, store: BaseStore
) -> State:
    """
    Analyze conversation context and suggest relevant follow-up actions.

    PROBLEM SOLVED:
    ==============
    LangGraph was automatically streaming our follow-up actions LLM call along with
    the main agent response, causing unwanted mixed output. We needed the follow-up
    actions to be generated silently and streamed separately with controlled timing.

    THREADING SOLUTION:
    ==================
    Using run_in_executor() executes the LLM call in an isolated thread where
    LangGraph cannot detect it. This prevents automatic streaming while allowing
    us to manually stream the results when we want using get_stream_writer().

    The key insight: LangGraph only monitors LLM calls in the main async thread context.
    Thread pool workers are invisible to this monitoring system.

    Args:
        state: The current state of the conversation

    Returns:
        Empty dict indicating successful completion (follow-up actions are streamed, not stored in state)
    """
    try:
        messages = state.get("messages", [])

        # Skip if insufficient conversation history for meaningful suggestions
        if not messages or len(messages) < 2:
            return state

        # Set up structured output parsing
        parser = PydanticOutputParser(pydantic_object=FollowUpActions)
        prompt = PromptTemplate(
            template=SUGGEST_FOLLOW_UP_ACTIONS,
            input_variables=["conversation_summary", "agent_prompt", "tool_names"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = (prompt | llm | parser).with_config({"run_name": "Follow-up actions"})
        recent_messages = messages[-4:] if len(messages) > 4 else messages

        # THREADING SOLUTION TO PREVENT AUTO-STREAMING:
        # Problem: LangGraph automatically detects and streams any LLM calls within the graph context,
        # causing our follow-up actions to be mixed with the main agent response output.
        # Solution: run_in_executor() executes the LLM call in an isolated thread where LangGraph
        # cannot detect it, allowing us to control streaming manually with get_stream_writer().

        # Lazy import to avoid circular dependency
        from app.langchain.tools.core.registry import tool_registry

        result = await asyncio.get_event_loop().run_in_executor(
            None,  # Use default thread pool
            lambda: chain.invoke(
                {  # Synchronous call in isolated thread
                    "conversation_summary": recent_messages,
                    "agent_prompt": AGENT_SYSTEM_PROMPT,
                    "tool_names": tool_registry.get_tool_names(),
                }
            ),
        )

        # CONTROLLED STREAMING:
        # Now we explicitly stream the follow-up actions when and how we want
        writer = get_stream_writer()
        writer({"follow_up_actions": result.actions})

        logger.info(
            f"Follow-up actions generated and streamed: {len(result.actions)} actions"
        )
        return state

    except Exception as e:
        logger.error(f"Error in follow-up actions node: {e}")
        return state
