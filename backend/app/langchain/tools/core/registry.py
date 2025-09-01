from typing import Dict, List, Optional

from app.langchain.tools import (
    calendar_tool,
    code_exec_tool,
    document_tool,
    file_tools,
    flowchart_tool,
    goal_tool,
    google_docs_tool,
    image_tool,
    memory_tools,
    reminder_tool,
    search_tool,
    support_tool,
    todo_tool,
    weather_tool,
    webpage_tool,
    workflow_tool,
)
from app.services.composio_service import composio_service
from langchain_core.tools import BaseTool


class ToolInfo:
    """Metadata for a tool."""

    def __init__(self, tool: BaseTool, space: str):
        self.tool = tool
        self.space = space

    tool: BaseTool
    space: str


class ToolRegistry:
    """Centralized repository for managing and retrieving tool information."""

    def __init__(self):
        # Define which categories require special integration handling
        self._categories_requiring_integrations = {
            "mail",
            "calendar",
            "google_docs",
            "twitter",
            "notion",
            "linkedin",
            "google_sheets",
        }

        # Define integration requirements for each category
        self._category_integration_map = {
            "mail": "gmail",
            "calendar": "google_calendar",
            "google_docs": "google_docs",
            "twitter": "twitter",
            "notion": "notion",
            "linkedin": "linkedin",
            "google_sheets": "google_sheets",
        }

        # All tools organized by category
        self._tools_by_category = {
            "productivity": [
                *todo_tool.tools,
                *reminder_tool.tools,
            ],
            "calendar": [
                *calendar_tool.tools,
            ],
            "goal_tracking": [
                *goal_tool.tools,
            ],
            "google_docs": [
                *google_docs_tool.tools,
            ],
            "documents": [
                document_tool.generate_document,
                file_tools.query_file,
            ],
            "search": [
                search_tool.web_search_tool,
                search_tool.deep_research_tool,
                webpage_tool.fetch_webpages,
            ],
            "support": [
                support_tool.create_support_ticket,
            ],
            "memory": [
                *memory_tools.tools,
            ],
            "development": [
                code_exec_tool.execute_code,
                flowchart_tool.create_flowchart,
            ],
            "creative": [
                image_tool.generate_image,
            ],
            "weather": [
                weather_tool.get_weather,
            ],
            "workflow": [
                *workflow_tool.tools,
            ],
            # Only handler tools in main categories - sub-agents get their own tools separately
            "twitter": composio_service.get_tools(tool_kit="TWITTER"),
            "notion": composio_service.get_tools(tool_kit="NOTION"),
            "linkedin": composio_service.get_tools(tool_kit="LINKEDIN"),
            "mail": composio_service.get_tools(
                tool_kit="GMAIL", exclude_tools=["GMAIL_SEND_EMAIL"]
            ),
            "google_sheets": [*composio_service.get_tools(tool_kit="GOOGLE_SHEETS")],
        }

        # Core tools that should always be available
        self._core_tools = [
            search_tool.web_search_tool,
            search_tool.deep_research_tool,
            webpage_tool.fetch_webpages,
            file_tools.query_file,
        ]

    def get_tools_by_category(self, category: str):
        """Get all tools for a specific category."""
        return self._tools_by_category.get(category.lower(), [])

    def get_all_categories(self) -> List[str]:
        """Get list of all available categories."""
        return list(self._tools_by_category.keys())

    def category_requires_integration(self, category: str) -> bool:
        """Check if a category requires special integration treatment."""
        return category.lower() in self._categories_requiring_integrations

    def get_category_integration_requirement(self, category: str) -> Optional[str]:
        """Get the integration requirement for a category."""
        return self._category_integration_map.get(category.lower())

    def get_core_tools(self):
        """Get tools that should always be accessible."""
        return self._core_tools.copy()

    def get_all_tools(self) -> List[BaseTool]:
        """Get all tools from all categories."""
        all_tools = []
        for category_tools in self._tools_by_category.values():
            all_tools.extend(category_tools)
        return all_tools

    def get_tool_registry(self) -> Dict[str, BaseTool]:
        """Get a dictionary mapping tool names to tool instances."""
        all_tools = self.get_all_tools()
        return {tool.name: tool for tool in all_tools}

    def get_tool_names(self) -> List[str]:
        """Get list of all tool names."""
        tools = self.get_all_tools()
        return [tool.name for tool in tools]

    def get_tool_dictionary(self) -> Dict[str, ToolInfo]:
        """Get a dictionary mapping tool names to tool instances."""
        all_tools = self.get_all_tools()
        tool_dict = {
            tool.name: ToolInfo(tool=tool, space="general") for tool in all_tools
        }

        return tool_dict

    def get_tool_category(self, tool_name: str) -> Optional[str]:
        """Get the category of a specific tool by its name."""
        for category, tools in self._tools_by_category.items():
            if any(tool.name == tool_name for tool in tools):
                return category
        return None


tool_registry = ToolRegistry()
