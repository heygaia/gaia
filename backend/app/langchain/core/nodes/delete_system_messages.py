"""
Delete System Messages Node for the conversational graph.

This module provides functionality to remove system messages from the conversation
state while preserving all other message types in their original order.
"""

from typing import Any, Dict

from app.config.loggers import chat_logger as logger
from app.langchain.prompts.agent_prompts import AGENT_SYSTEM_PROMPT
from langchain_core.messages import AIMessage, RemoveMessage


async def delete_system_messages(state: Dict[str, Any]):
    """
    Remove all system messages from the conversation state.

    This function processes the message history and creates RemoveMessage instances
    for all system-type messages while preserving the order and content of all
    other message types (human, AI, tool, etc.).

    TECHNICAL IMPLEMENTATION:
    ========================
    - Iterates through all messages in the conversation state
    - Identifies messages with type "system"
    - Creates RemoveMessage instances to mark them for deletion
    - Returns updated message list with removal markers followed by kept messages

    Args:
        state: The current state of the conversation containing a "messages" key
               with a list of message objects

    Returns:
        Dict containing updated "messages" list with RemoveMessage instances
        for system messages followed by all non-system messages, or empty dict
        if insufficient messages or on error
    """
    try:
        messages = state.get("messages", [])

        # Skip if no messages to process
        if not messages or len(messages) < 2:
            return {}

        last_message = messages[-1]
        # Skip processing if last message is AI with tool calls
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return {}

        messages_to_remove = []
        messages_to_keep = []

        # Separate system messages for removal and keep others
        for msg in state["messages"]:
            # Checking for content match because we don't want to remove memories in SystemMessage
            if msg.type == "system" and msg.content.startswith(
                AGENT_SYSTEM_PROMPT[:50]
            ):
                messages_to_remove.append(RemoveMessage(id=msg.id))
            else:
                messages_to_keep.append(msg)

        return {"messages": messages_to_remove + messages_to_keep}

    except Exception as e:
        logger.error(f"Error in delete system messages node: {e}")
        return {}
