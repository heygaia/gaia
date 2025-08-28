from functools import cache
from typing import Dict, List, Optional

from app.langchain.core.subagents.handoff_tools import get_handoff_tools
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
)
from app.services.composio_service import composio_service
from langchain_core.tools import BaseTool


class Tool:
    """Simplified tool object that holds individual tool metadata."""

    def __init__(
        self,
        tool: BaseTool,
        name: Optional[str] = None,
        is_core: bool = False,
    ):
        self.tool = tool
        self.name = name or tool.name
        self.is_core = is_core


class ToolCategory:
    """Category that holds tools and category-level metadata."""

    def __init__(
        self,
        name: str,
        space: str = "general",
        require_integration: bool = False,
        integration_name: Optional[str] = None,
        is_delegated: bool = False,
        delegation_target: Optional[str] = None,
    ):
        self.name = name
        self.space = space
        self.require_integration = require_integration
        self.integration_name = integration_name
        self.is_delegated = is_delegated
        self.delegation_target = delegation_target
        self.tools: List[Tool] = []

    def add_tool(
        self, tool: BaseTool, is_core: bool = False, name: Optional[str] = None
    ):
        """Add a tool to this category."""
        self.tools.append(Tool(tool=tool, name=name, is_core=is_core))

    def add_tools(self, tools: List[BaseTool], is_core: bool = False):
        """Add multiple tools to this category."""
        for tool in tools:
            self.add_tool(tool, is_core=is_core)

    def get_tool_objects(self) -> List[BaseTool]:
        """Get the actual tool objects for binding."""
        return [tool.tool for tool in self.tools]

    def get_core_tools(self) -> List[Tool]:
        """Get only core tools from this category."""
        return [tool for tool in self.tools if tool.is_core]


class ToolInfo:
    """Metadata for a tool."""

    def __init__(self, tool: BaseTool, space: str):
        self.tool = tool
        self.space = space

    tool: BaseTool
    space: str


class ToolRegistry:
    """Modern tool registry with category-based organization."""

    def __init__(self):
        self._categories: Dict[str, ToolCategory] = {}
        self._initialize_categories()

    def _initialize_categories(self):
        """Initialize all tool categories with their metadata and tools."""

        # Core categories (no integration required)
        search_category = ToolCategory(
            name="search", space="general", require_integration=False
        )
        search_category.add_tools(
            [
                search_tool.web_search_tool,
                search_tool.deep_research_tool,
                webpage_tool.fetch_webpages,
            ],
            is_core=True,
        )
        self._categories["search"] = search_category

        documents_category = ToolCategory(
            name="documents", space="general", require_integration=False
        )
        documents_category.add_tool(file_tools.query_file, is_core=True)
        documents_category.add_tool(document_tool.generate_document)
        self._categories["documents"] = documents_category

        delegation_category = ToolCategory(
            name="delegation", space="general", require_integration=False
        )
        delegation_category.add_tools(get_handoff_tools(["gmail", "notion", "twitter", "linkedin"]))
        self._categories["delegation"] = delegation_category

        productivity_category = ToolCategory(
            name="productivity", space="general", require_integration=False
        )
        productivity_category.add_tools([*todo_tool.tools, *reminder_tool.tools])
        self._categories["productivity"] = productivity_category

        goal_tracking_category = ToolCategory(
            name="goal_tracking", space="general", require_integration=False
        )
        goal_tracking_category.add_tools(goal_tool.tools)
        self._categories["goal_tracking"] = goal_tracking_category

        support_category = ToolCategory(
            name="support", space="general", require_integration=False
        )
        support_category.add_tool(support_tool.create_support_ticket)
        self._categories["support"] = support_category

        memory_category = ToolCategory(
            name="memory", space="general", require_integration=False
        )
        memory_category.add_tools(memory_tools.tools)
        self._categories["memory"] = memory_category

        development_category = ToolCategory(
            name="development", space="general", require_integration=False
        )
        development_category.add_tools(
            [
                code_exec_tool.execute_code,
                flowchart_tool.create_flowchart,
            ]
        )
        self._categories["development"] = development_category

        creative_category = ToolCategory(
            name="creative", space="general", require_integration=False
        )
        creative_category.add_tool(image_tool.generate_image)
        self._categories["creative"] = creative_category

        weather_category = ToolCategory(
            name="weather", space="general", require_integration=False
        )
        weather_category.add_tool(weather_tool.get_weather)
        self._categories["weather"] = weather_category

        # Integration-required categories
        calendar_category = ToolCategory(
            name="calendar",
            space="general",
            require_integration=True,
            integration_name="google_calendar",
        )
        calendar_category.add_tools(calendar_tool.tools)
        self._categories["calendar"] = calendar_category

        google_docs_category = ToolCategory(
            name="google_docs",
            space="general",
            require_integration=True,
            integration_name="google_docs",
        )
        google_docs_category.add_tools(google_docs_tool.tools)
        self._categories["google_docs"] = google_docs_category

        # Provider categories (integration required)
        twitter_category = ToolCategory(
            name="twitter",
            space="general",
            is_delegated=True,
            require_integration=True,
            integration_name="twitter",
        )
        twitter_category.add_tools(composio_service.get_tools(tool_kit="TWITTER"))
        self._categories["twitter"] = twitter_category

        notion_category = ToolCategory(
            name="notion",
            space="general",
            is_delegated=True,
            require_integration=True,
            integration_name="notion",
        )
        notion_category.add_tools(composio_service.get_tools(tool_kit="NOTION"))
        self._categories["notion"] = notion_category

        linkedin_category = ToolCategory(
            name="linkedin",
            space="general",
            is_delegated=True,
            require_integration=True,
            integration_name="linkedin",
        )
        linkedin_category.add_tools(composio_service.get_tools(tool_kit="LINKEDIN"))
        self._categories["linkedin"] = linkedin_category

        google_sheets_category = ToolCategory(
            name="google_sheets",
            space="general",
            is_delegated=True,
            require_integration=True,
            integration_name="google_sheets",
        )
        google_sheets_category.add_tools(
            composio_service.get_tools(tool_kit="GOOGLE_SHEETS")
        )
        self._categories["google_sheets"] = google_sheets_category

        # Delegated categories
        gmail_category = ToolCategory(
            name="gmail",
            space="gmail",
            require_integration=True,
            integration_name="gmail",
            is_delegated=True,
            delegation_target="gmail",
        )
        gmail_category.add_tools(
            composio_service.get_tools(tool_kit="GMAIL", exclude_tools=[])
        )
        self._categories["gmail"] = gmail_category

    def get_category(self, name: str) -> Optional[ToolCategory]:
        """Get a specific category by name."""
        return self._categories.get(name)

    def get_all_category_objects(
        self, ignore_categories: List[str] = []
    ) -> Dict[str, ToolCategory]:
        """Get all categories as ToolCategory objects."""
        return {
            name: category
            for name, category in self._categories.items()
            if name not in ignore_categories
        }

    @cache
    def get_category_of_tool(self, tool_name: str) -> str:
        """Get the category of a specific tool by name."""
        for category in self._categories.values():
            for tool in category.tools:
                if tool.name == tool_name:
                    return category.name
        return "unknown"

    def get_all_tools_for_search(self, include_delegated: bool = True) -> List[Tool]:
        """
        Get all tool objects for semantic search (includes delegated tools).

        Returns:
            List of Tool objects for semantic search.
        """
        tools: List[Tool] = []
        for category in self._categories.values():
            if category.is_delegated and not include_delegated:
                continue
            tools.extend(category.tools)
        return tools

    def get_core_tools(self) -> List[Tool]:
        """
        Get all core tools across all categories.

        Returns:
            List of core Tool objects.
        """
        core_tools = []
        for category in self._categories.values():
            core_tools.extend(category.get_core_tools())
        return core_tools

    def get_tool_registry(self) -> Dict[str, BaseTool]:
        """Get a dictionary mapping tool names to tool instances for agent binding.

        This excludes delegated tools that should only be available via sub-agents.
        """
        all_tools = self.get_all_tools_for_search()
        return {tool.name: tool.tool for tool in all_tools}

    def get_tool_names(self) -> List[str]:
        """Get list of all tool names including delegated ones."""
        tools = self.get_all_tools_for_search()
        return [tool.name for tool in tools]


tool_registry = ToolRegistry()
