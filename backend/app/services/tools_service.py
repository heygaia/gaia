"""
Service for managing and retrieving tool information.
"""

from typing import Dict

from app.langchain.tools.core.registry import tool_registry
from app.models.tools_models import ToolInfo, ToolsCategoryResponse, ToolsListResponse


async def get_available_tools() -> ToolsListResponse:
    """Get list of all available tools with their metadata."""
    all_tools = tool_registry.get_all_tools()
    tool_infos = []
    categories = set()

    for tool in all_tools:
        # Extract basic info
        name = tool.name
        category = tool_registry.get_tool_category(name) or "general"
        categories.add(category)

        # Check if this category requires an integration
        required_integration = tool_registry.get_category_integration_requirement(
            category
        )

        tool_info = ToolInfo(
            name=name,
            category=category,
            required_integration=required_integration,
        )
        tool_infos.append(tool_info)

    return ToolsListResponse(
        tools=tool_infos,
        total_count=len(tool_infos),
        categories=sorted(list(categories)),
    )


async def get_tools_by_category(category: str) -> ToolsCategoryResponse:
    """Get tools filtered by category."""
    category_tools = tool_registry.get_tools_by_category(category)

    tool_infos = []
    for tool in category_tools:
        name = tool.name
        required_integration = tool_registry.get_category_integration_requirement(
            category
        )

        tool_info = ToolInfo(
            name=name,
            category=category,
            required_integration=required_integration,
        )
        tool_infos.append(tool_info)

    return ToolsCategoryResponse(
        category=category, tools=tool_infos, count=len(tool_infos)
    )


async def get_tool_categories() -> Dict[str, int]:
    """Get all tool categories with their counts."""
    category_counts: Dict[str, int] = {}

    for category in tool_registry.get_all_categories():
        category_tools = tool_registry.get_tools_by_category(category)
        category_counts[category] = len(category_tools)

    return category_counts
