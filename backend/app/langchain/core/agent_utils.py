import json
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4

from langchain_core.messages import ToolCall

from app.config.loggers import llm_logger as logger
from app.langchain.tools.core.registry import tool_registry
from app.models.chat_models import MessageModel, UpdateMessagesRequest
from app.services.conversation_service import update_messages


def format_tool_progress(tool_call: ToolCall) -> Optional[dict]:
    """Format tool execution progress data for streaming UI updates.

    Transforms a LangChain ToolCall object into a structured progress update
    that can be displayed in the frontend. Extracts tool name, formats it for
    display, and retrieves the tool category from the registry.

    Args:
        tool_call: LangChain ToolCall object containing tool execution details

    Returns:
        Dictionary with progress information including formatted message,
        tool name, and category, or None if tool name is missing
    """
    tool_name_raw = tool_call.get("name")
    if not tool_name_raw:
        return None

    tool_name = tool_name_raw.replace("_", " ").title()
    tool_category = tool_registry.get_category_of_tool(tool_name_raw)

    return {
        "progress": {
            "message": f"Executing {tool_name}...",
            "tool_name": tool_name_raw,
            "tool_category": tool_category,
        }
    }


def format_sse_response(content: str) -> str:
    """Format text content as Server-Sent Events (SSE) response.

    Wraps content in the standard SSE data format with JSON encoding
    for transmission to frontend clients via EventSource connections.

    Args:
        content: Text content to be streamed to the client

    Returns:
        SSE-formatted string with 'data:' prefix and proper line endings
    """
    return f"data: {json.dumps({'response': content})}\n\n"


def format_sse_data(data: dict) -> str:
    """Format structured data as Server-Sent Events (SSE) response.

    Converts dictionary data to JSON and wraps it in SSE format for
    streaming structured information like tool progress, errors, or
    custom events to frontend clients.

    Args:
        data: Dictionary containing structured data to stream

    Returns:
        SSE-formatted string with JSON-encoded data and proper line endings
    """
    return f"data: {json.dumps(data)}\n\n"


def process_custom_event_for_tools(payload) -> dict:
    """Extract and process tool execution data from custom LangGraph events.

    Safely processes custom event payloads from LangGraph streams to extract
    tool execution results and data. Handles serialization and delegates to
    the chat service for tool-specific data extraction.

    Args:
        payload: Raw event payload from LangGraph custom events

    Returns:
        Dictionary containing extracted tool data, or empty dict if
        extraction fails or no data is available
    """
    try:
        # Import inside function to avoid circular imports
        from app.services.chat_service import extract_tool_data

        serialized = json.dumps(payload) if payload else "{}"
        new_data = extract_tool_data(serialized)
        return new_data if new_data else {}
    except Exception as e:
        logger.error(f"Error extracting tool data: {e}")
        return {}


async def store_agent_progress(
    conversation_id: str, user_id: str, current_message: str, current_tool_data: dict
) -> None:
    """Store agent execution progress in real-time.

    Generic function for storing bot messages during agent execution.
    Works for any agent execution - workflows, normal chat, etc.
    Only stores messages that have meaningful content (message text or tool data).

    Args:
        conversation_id: Conversation ID for storage
        user_id: User ID for authorization
        current_message: Current accumulated LLM response
        current_tool_data: Current accumulated tool outputs
    """
    try:
        # Only store if there's meaningful content
        has_content = (
            current_message.strip() or any(current_tool_data.values())
            if current_tool_data
            else False
        )

        if not has_content:
            return  # Skip storing empty messages

        # Create bot message using same pattern as chat_service.py
        bot_message = MessageModel(
            type="bot",
            response=current_message,
            date=datetime.now(timezone.utc).isoformat(),
            message_id=str(uuid4()),
        )

        # Apply tool data to message (same as chat_service.py)
        if current_tool_data:
            for key, value in current_tool_data.items():
                setattr(bot_message, key, value)

        # Store immediately using existing service
        await update_messages(
            UpdateMessagesRequest(
                conversation_id=conversation_id,
                messages=[bot_message],
            ),
            user={"user_id": user_id},
        )

    except Exception as e:
        # Don't break agent execution for storage failures
        logger.error(f"Failed to store agent progress: {str(e)}")
