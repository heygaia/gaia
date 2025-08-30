"""
Tool categorization system with dynamic extraction from file names
and configurable overrides.
"""

from typing import Dict

from app.langchain.tools.core.registry import TOOLS_BY_CATEGORY


# Category overrides - allows custom mapping for specific tools
CATEGORY_OVERRIDES: Dict[str, str] = {
    # Example overrides:
    # "google_docs_tool": "documents",
    # "code_exec_tool": "development",
    # Add custom overrides here as needed
}


def get_tool_category(tool_name: str) -> str:
    """
    Get the category for a tool with the following priority:
    1. Check registry categories first
    2. Check CATEGORY_OVERRIDES for specific tool name
    3. Extract from file name dynamically
    4. Return extracted category or 'general' as fallback
    """

    # Priority 1: Check registry categories first
    # Find the tool in categorized registry
    for category, category_tools in TOOLS_BY_CATEGORY.items():
        for tool in category_tools:
            if hasattr(tool, "name") and tool.name == tool_name:
                return category

    # Priority 2: Check for explicit overrides
    if tool_name in CATEGORY_OVERRIDES:
        return CATEGORY_OVERRIDES[tool_name]

    return "general"
