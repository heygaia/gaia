"""
Delete System Messages Node for the conversational graph.

This module provides functionality to remove system messages from the conversation
state while preserving all other message types in their original order.
"""

from app.config.loggers import chat_logger as logger
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from langgraph_bigtool.graph import State


def create_filter_messages_node(
    agent_name: str = "main_agent",
    allow_empty_agent_name: bool = False,
):
    """Create a node that filters out system messages from the conversation state.
    Args:
        agent_name: Name of the agent whose system messages should be included.
        allow_empty_agent_name: If True, allows empty agent_name to skip filtering.
            If False, It filters out all the messages having empty names.
    Returns:
        A callable node that filters messages in the conversation state.
    """

    async def filter_messages(
        state: State, config: RunnableConfig, store: BaseStore
    ) -> State:
        """
        Filters out system messages from the conversation state.
        Args:
            state: The current state containing messages.
            config: Configuration for the runnable.
            store: The store for any required data persistence.
        Returns:
            The updated state with system messages removed.
        """
        try:
            allowed_tool_messages_ids = set()
            filtered_messages = []
            # Separate system messages for removal and keep others
            for msg in state["messages"]:
                # Checking for content match because we don't want to remove memories in SystemMessage
                if (
                    msg.name == agent_name
                    or ((msg.name == "" or msg.name is None) and allow_empty_agent_name)
                    or (
                        isinstance(msg, ToolMessage)
                        and msg.tool_call_id in allowed_tool_messages_ids
                    )
                ):
                    filtered_messages.append(msg)

                    if isinstance(msg, AIMessage):
                        for tool_call in msg.tool_calls:
                            allowed_tool_messages_ids.add(tool_call.get("id"))

            return {**state, "messages": filtered_messages}

        except Exception as e:
            logger.error(f"Error in delete system messages node: {e}")
            return state

    return filter_messages
