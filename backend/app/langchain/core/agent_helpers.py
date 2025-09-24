"""Core agent helper functions for LangGraph execution and configuration.

Provides essential building blocks for agent execution including configuration
building, state initialization, and graph execution in both streaming and silent modes.

These functions are tightly coupled to agent-specific logic and LangGraph execution.
"""

import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from app.langchain.core.agent_utils import (
    format_sse_data,
    format_sse_response,
    format_tool_progress,
    process_custom_event_for_tools,
    store_agent_progress,
)
from app.models.models_models import ModelConfig
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import AIMessageChunk
from langsmith import traceable


def build_agent_config(
    conversation_id: str,
    user: dict,
    user_time: datetime,
    user_model_config: Optional[ModelConfig] = None,
    usage_metadata_callback: Optional[UsageMetadataCallbackHandler] = None,
) -> dict:
    """Build configuration for graph execution with optional authentication tokens.

    Creates a comprehensive configuration object for LangGraph execution that includes
    user context, model settings, authentication tokens, and execution parameters.

    Args:
        conversation_id: Unique identifier for the conversation thread
        user: User information dictionary containing user_id and email
        user_time: Current datetime for the user's timezone
        user_model_config: Optional model configuration with provider and token limits

    Returns:
        Tuple containing:
        - Configuration dictionary formatted for LangGraph execution with configurable
            parameters, metadata, and recursion limits
        - UsageMetadataCallbackHandler instance for tracking token usage during execution
    """
    model_configuration = {
        "provider": (
            user_model_config.inference_provider.value if user_model_config else None
        ),
        "max_tokens": user_model_config.max_tokens if user_model_config else None,
        "model_name": (
            user_model_config.provider_model_name if user_model_config else None
        ),
    }

    config = {
        "configurable": {
            "thread_id": conversation_id,
            "user_id": user.get("user_id"),
            "email": user.get("email"),
            "user_time": user_time.isoformat(),
            "model_configurations": model_configuration,
        },
        "recursion_limit": 25,
        "metadata": {"user_id": user.get("user_id")},
        "callbacks": [usage_metadata_callback],
    }

    return config


def build_initial_state(
    request,
    user_id: str,
    conversation_id: str,
    history,
    trigger_context: Optional[dict] = None,
) -> dict:
    """Construct initial state dictionary for LangGraph execution.

    Builds the starting state containing all necessary context for the agent
    including user query, conversation history, tool selections, and optional
    workflow trigger context.

    Args:
        request: Message request object containing user message and selections
        user_id: Unique identifier for the user
        conversation_id: Unique identifier for the conversation thread
        history: List of previous messages in LangChain format
        trigger_context: Optional context data from workflow triggers

    Returns:
        State dictionary with query, messages, datetime, user context, and
        selected tools/workflows for graph processing
    """
    state = {
        "query": request.message,
        "messages": history,
        "current_datetime": datetime.now(timezone.utc).isoformat(),
        "mem0_user_id": user_id,
        "conversation_id": conversation_id,
        "selected_tool": request.selectedTool,
        "selected_workflow": request.selectedWorkflow,
    }

    if trigger_context:
        state["trigger_context"] = trigger_context

    return state


@traceable(run_type="llm", name="Call Agent Silent")
async def execute_graph_silent(
    graph,
    initial_state: dict,
    config: dict,
    usage_metadata_callback: UsageMetadataCallbackHandler,
) -> tuple[str, dict, dict]:
    """Execute LangGraph in silent mode with real-time progress storage.

    Runs the agent graph asynchronously and accumulates all results including
    the complete message content and extracted tool data. Used for background
    processing and workflow triggers where real-time streaming is not needed.

    Stores intermediate messages and tool outputs as they happen during execution,
    using the same storage patterns as normal chat.

    Args:
        graph: LangGraph instance to execute
        initial_state: Starting state dictionary with query and context
        config: Configuration dictionary with user context and settings

    Returns:
        Tuple containing:
        - complete_message: Full response text accumulated from all chunks
        - tool_data: Dictionary of extracted tool execution data and results
        - token_metadata: Dictionary containing token usage information
    """
    complete_message = ""
    tool_data = {}

    # Get storage context from config
    conversation_id = config.get("configurable", {}).get("thread_id")
    user_id = config.get("configurable", {}).get("user_id")

    async for event in graph.astream(
        initial_state,
        stream_mode=["messages", "custom"],
        config=config,
        subgraphs=True,
    ):
        ns, stream_mode, payload = event

        if stream_mode == "messages":
            chunk, metadata = payload

            if metadata.get("silent"):
                continue  # Skip silent chunks (e.g. follow-up actions generation)

            if chunk and isinstance(chunk, AIMessageChunk):
                content = str(chunk.content)
                if content:
                    complete_message += content

        elif stream_mode == "custom":
            new_data = process_custom_event_for_tools(payload)
            if new_data:
                tool_data.update(new_data)

                # Store progress immediately when tool completes (same pattern as chat)
                if conversation_id and user_id:
                    await store_agent_progress(
                        conversation_id, user_id, complete_message, tool_data
                    )

    # Get token usage metadata from callback
    token_metadata = usage_metadata_callback.usage_metadata

    return complete_message, tool_data, token_metadata


@traceable(run_type="llm", name="Call Agent")
async def execute_graph_streaming(
    graph,
    initial_state: dict,
    config: dict,
) -> AsyncGenerator[str, None]:
    """Execute LangGraph in streaming mode with real-time output.

    Runs the agent graph and yields Server-Sent Events (SSE) formatted updates
    as they occur. Handles both message content streaming and tool execution
    progress updates. Only yields content from the main agent to avoid duplication
    from subgraphs.

    Args:
        graph: LangGraph instance to execute
        initial_state: Starting state dictionary with query and context
        config: Configuration dictionary with user context and settings

    Yields:
        SSE-formatted strings containing:
        - Real-time message content as it's generated
        - Tool execution progress updates
        - Custom events from tool executions
        - Final completion marker and accumulated message
    """
    complete_message = ""

    async for event in graph.astream(
        initial_state,
        stream_mode=["messages", "custom"],
        config=config,
        subgraphs=True,
    ):
        ns, stream_mode, payload = event
        is_main_agent = len(ns) == 0  # Main agent when namespace is empty

        if stream_mode == "messages":
            chunk, metadata = payload
            if chunk and isinstance(chunk, AIMessageChunk):
                # Skip silent chunks (e.g. follow-up actions generation)
                if metadata.get("silence"):
                    continue

                content = str(chunk.content)
                tool_calls = chunk.tool_calls

                # Show tool execution progress
                if tool_calls:
                    for tool_call in tool_calls:
                        progress_data = format_tool_progress(tool_call)
                        if progress_data:
                            yield format_sse_data(progress_data)

                # Only yield content from main agent to avoid duplication
                if content and is_main_agent:
                    yield format_sse_response(content)
                    complete_message += content

        elif stream_mode == "custom":
            # Forward custom events as-is
            yield f"data: {json.dumps(payload)}\n\n"

    # Get token metadata after streaming completes and yield complete message for DB storage
    message_data = {"complete_message": complete_message}

    message_data = {**message_data}

    yield f"nostream: {json.dumps(message_data)}"
    yield "data: [DONE]\n\n"
