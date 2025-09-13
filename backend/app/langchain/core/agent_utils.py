import json
from typing import Optional

from langchain_core.messages import ToolCall

from app.config.loggers import llm_logger as logger
from app.langchain.tools.core.registry import tool_registry


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
