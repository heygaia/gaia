from typing import Annotated

from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore


def get_retrieve_tools_function(
    tool_space: str = "general",
    include_core_tools: bool = True,
):
    """
    Get a function to retrieve tools based on a search query.

    Args:
        tool_space: Namespace prefix for the tools.
        exclude_tools: List of tool names to exclude from results.
        include_core_tools: Whether to include core tools in the results.

    Returns:
        A function that retrieves tools based on the provided parameters.
    """

    def retrieve_tools(
        query: str,
        store: Annotated[BaseStore, InjectedStore],
        exclude_tools: list[str] = [],
    ) -> list[str]:
        """Retrieve a tool to use, given a search query."""

        # Lazy import to avoid circular dependency
        from app.langchain.tools.core.registry import tool_registry

        # Search for matching tools based on query
        results = store.search((tool_space,), query=query, limit=5)
        tool_ids = [result.key for result in results]

        if include_core_tools:
            # Filter core tools based on exclusions
            filtered_core_tools = [
                tool
                for tool in tool_registry.get_core_tools()
                if tool.name not in exclude_tools
            ]

            # Core tools are essential tools that should be accessible regardless of semantic search results
            core_tool_ids = [tool.name for tool in filtered_core_tools]

            tool_ids.extend(core_tool_ids)

        return tool_ids

    return retrieve_tools
