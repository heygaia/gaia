"""Agent execution module providing streaming and silent execution modes.

This module handles the core agent execution logic with two distinct pa        graph, initial_state, config = await _core_agent_logic(
            request,
            conversation_id,
            user,
            user_time,
            user_model_config,
            trigger_context,
        )

        # Create token tracking callback
        from langchain_core.callbacks import UsageMetadataCallbackHandler

        user_id = user.get("user_id")
        token_callback = UsageMetadataCallbackHandler()

        return execute_graph_streaming(graph, initial_state, config, token_callback). Streaming Mode (call_agent)* Returns AsyncGenerator for real-time SSE streaming
   - Required for interactive chat where users need immediate feedback
   - Cannot return awaited results directly due to AsyncGenerator yield semantics
   - Must yield SSE-formatted strings as they're produced

2. Silent Mode (call_agent_silent): Returns awaited tuple for background processing
   - Used for workflow triggers and batch processing where streaming isn't needed
   - Can return complete results after full execution
   - More efficient for automation and server-to-server communication

The separation exists because Python async functions cannot both yield values
(AsyncGenerator) and return awaited results simultaneously. Each pattern serves
different use cases in the agent architecture.
"""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Optional

from app.config.loggers import llm_logger as logger
from app.langchain.core.agent_helpers import (
    build_agent_config,
    build_initial_state,
    execute_graph_silent,
    execute_graph_streaming,
)
from app.langchain.core.graph_manager import GraphManager
from app.langchain.core.messages import construct_langchain_messages
from app.models.message_models import MessageRequestWithHistory
from app.models.models_models import ModelConfig
from app.utils.memory_utils import store_user_message_memory
from langchain_core.callbacks import UsageMetadataCallbackHandler


async def _core_agent_logic(
    request: MessageRequestWithHistory,
    conversation_id: str,
    user: dict,
    user_time: datetime,
    user_model_config: Optional[ModelConfig] = None,
    trigger_context: Optional[dict] = None,
    usage_metadata_callback: Optional[UsageMetadataCallbackHandler] = None,
):
    """Core agent initialization logic shared between streaming and silent execution modes.

    Handles the common setup required for both streaming and silent agent execution
    including message construction, graph initialization, state building, and
    background memory storage. Centralizes the preparation logic to avoid duplication.

    Args:
        request: Message request with conversation history and file data
        conversation_id: Unique identifier for the conversation thread
        user: User information dictionary with ID, email, and name
        user_time: Current datetime in user's timezone
        user_model_config: Optional model configuration for inference
        access_token: Optional OAuth access token for authenticated requests
        refresh_token: Optional OAuth refresh token for token renewal
        trigger_context: Optional context data from workflow triggers

    Returns:
        Tuple containing:
        - graph: Initialized LangGraph instance ready for execution
        - initial_state: Prepared state dictionary with all context
        - config: Configuration dictionary with user settings and tokens
    """
    user_id = user.get("user_id")

    # Build langchain messages and get graph concurrently
    history, graph = await asyncio.gather(
        construct_langchain_messages(
            messages=request.messages,
            files_data=request.fileData,
            currently_uploaded_file_ids=request.fileIds,
            user_id=user_id,
            query=request.message,
            user_name=user.get("name"),
            selected_tool=request.selectedTool,
            selected_workflow=request.selectedWorkflow,
            trigger_context=trigger_context,
        ),
        GraphManager.get_graph(),
    )
    initial_state = build_initial_state(
        request, user_id or "", conversation_id, history, trigger_context
    )

    # Start memory storage in background (fire and forget)
    if user_id and request.message:
        asyncio.create_task(
            store_user_message_memory(user_id, request.message, conversation_id)
        )

    # Build config with optional tokens
    config = build_agent_config(
        conversation_id,
        user,
        user_time,
        user_model_config,
        usage_metadata_callback,
    )

    return graph, initial_state, config


async def call_agent(
    request: MessageRequestWithHistory,
    conversation_id: str,
    user: dict,
    user_time: datetime,
    user_model_config: Optional[ModelConfig] = None,
    usage_metadata_callback: Optional[UsageMetadataCallbackHandler] = None,
) -> AsyncGenerator[str, None]:
    """
    Execute agent in streaming mode for interactive chat.

    Returns an AsyncGenerator that yields SSE-formatted streaming data.
    """
    try:
        graph, initial_state, config = await _core_agent_logic(
            request,
            conversation_id,
            user,
            user_time,
            user_model_config,
            usage_metadata_callback=usage_metadata_callback,
        )

        return execute_graph_streaming(graph, initial_state, config)

    except Exception as exc:
        logger.error(f"Error when calling agent: {exc}")
        error_message = f"Error when calling agent: {str(exc)}"

        async def error_generator():
            error_dict = {"error": error_message}
            yield f"data: {json.dumps(error_dict)}\n\n"
            yield "data: [DONE]\n\n"

        return error_generator()


async def call_agent_silent(
    request: MessageRequestWithHistory,
    conversation_id: str,
    user: dict,
    user_time: datetime,
    usage_metadata_callback: Optional[UsageMetadataCallbackHandler] = None,
    user_model_config: Optional[ModelConfig] = None,
    trigger_context: Optional[dict] = None,
) -> tuple[str, dict, dict]:
    """
    Execute agent in silent mode for background processing.

    Returns a tuple of (complete_message, tool_data_dict, token_metadata).
    """
    try:
        graph, initial_state, config = await _core_agent_logic(
            request,
            conversation_id,
            user,
            user_time,
            user_model_config,
            trigger_context,
            usage_metadata_callback,
        )

        return await execute_graph_silent(
            graph, initial_state, config, usage_metadata_callback
        )

    except Exception as exc:
        logger.error(f"Error when calling silent agent: {exc}")
        return f"Error when calling silent agent: {str(exc)}", {}, {}
