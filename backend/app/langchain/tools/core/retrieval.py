from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore
from typing import Annotated

from app.langchain.tools.core.registry import ALWAYS_AVAILABLE_TOOLS


def retrieve_tools(
    query: str,
    store: Annotated[BaseStore, InjectedStore],
    exclude_tools: list[str] = [],
) -> list[str]:
    """Retrieve a tool to use, given a search query."""
    # Search for matching tools based on query
    results = store.search(("tools",), query=query, limit=5)
    tool_ids = [
        result.key for result in results
    ]  # Filter out any tools that should be excluded
    filtered_always_available_tools = [
        tool for tool in ALWAYS_AVAILABLE_TOOLS if tool.name not in exclude_tools
    ]

    # Always available tools are essential core tools that should be accessible regardless of semantic search results. These tools provide fundamental capabilities like web search, memory management, and basic functionality that the agent may need even if they don't match the current query semantically.
    always_available_tool_ids = [tool.name for tool in filtered_always_available_tools]

    # Combine both sets of tools (semantic search + always available)
    combined_tools = tool_ids + always_available_tool_ids

    return combined_tools
