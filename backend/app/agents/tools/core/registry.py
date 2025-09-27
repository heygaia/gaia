import asyncio
import time
from functools import cache
from typing import Dict, List, Optional

from app.agents.core.subagents.handoff_tools import get_handoff_tools
from app.agents.tools import (
    calendar_tool,
    code_exec_tool,
    document_tool,
    file_tools,
    flowchart_tool,
    goal_tool,
    google_docs_tool,
    image_tool,
    memory_tools,
    notification_tool,
    reminder_tool,
    search_tool,
    support_tool,
    todo_tool,
    weather_tool,
    webpage_tool,
)
from app.config.loggers import langchain_logger as logger
from app.services.composio.composio_service import composio_service
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
    ):
        self.name = name
        self.space = space
        self.require_integration = require_integration
        self.integration_name = integration_name
        self.is_delegated = is_delegated
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

        # Helper function to create and register categories
        def add_category(
            name: str,
            tools: Optional[List[BaseTool]] = None,
            core_tools: Optional[List[BaseTool]] = None,
            space: str = "general",
            require_integration: bool = False,
            integration_name: Optional[str] = None,
            is_delegated: bool = False,
        ):
            category = ToolCategory(
                name=name,
                space=space,
                require_integration=require_integration,
                integration_name=integration_name,
                is_delegated=is_delegated,
            )
            if core_tools:
                category.add_tools(core_tools, is_core=True)
            if tools:
                category.add_tools(tools)
            self._categories[name] = category

        # Core categories (no integration required)
        add_category(
            "search",
            core_tools=[
                search_tool.web_search_tool,
                search_tool.deep_research_tool,
                webpage_tool.fetch_webpages,
            ],
        )

        add_category(
            "documents",
            core_tools=[file_tools.query_file],
            tools=[document_tool.generate_document],
        )

        add_category(
            "delegation",
            core_tools=get_handoff_tools(["gmail", "notion", "twitter", "linkedin"]),
        )

        add_category("notifications", tools=[*notification_tool.tools])
        add_category("productivity", tools=[*todo_tool.tools, *reminder_tool.tools])
        add_category("goal_tracking", tools=goal_tool.tools)
        add_category("support", tools=[support_tool.create_support_ticket])
        add_category("memory", tools=memory_tools.tools)
        add_category(
            "development",
            tools=[code_exec_tool.execute_code, flowchart_tool.create_flowchart],
        )
        add_category("creative", tools=[image_tool.generate_image])
        add_category("weather", tools=[weather_tool.get_weather])

        # Integration-required categories
        add_category(
            "calendar",
            tools=calendar_tool.tools,
            require_integration=True,
            integration_name="google_calendar",
        )

        add_category(
            "google_docs",
            tools=google_docs_tool.tools,
            require_integration=True,
            integration_name="google_docs",
        )

        # Provider categories (integration required + delegated) - Load async
        self._initialize_provider_categories_async()

    def _initialize_provider_categories_async(self):
        """Initialize provider categories asynchronously for better startup performance."""

        async def load_provider_tools():
            """Load all provider tools concurrently using asyncio.gather."""
            logger.info("Loading provider tools concurrently...")
            start_time = time.time()

            provider_configs = [
                ("twitter", "TWITTER"),
                ("notion", "NOTION"),
                ("linkedin", "LINKEDIN"),
                ("google_sheets", "GOOGLE_SHEETS"),
                ("gmail", "GMAIL"),
            ]

            async def load_single_provider(name: str, toolkit: str):
                """Load tools for a single provider."""
                provider_start = time.time()
                try:
                    # Use the cached async method
                    tools = await composio_service.get_tools(toolkit)
                    provider_time = time.time() - provider_start

                    if tools:
                        logger.info(
                            f"{name} provider: {len(tools)} tools loaded in {provider_time:.3f}s"
                        )
                    else:
                        logger.warning(
                            f"{name} provider: no tools found ({provider_time:.3f}s)"
                        )

                    return name, toolkit, tools
                except Exception as e:
                    provider_time = time.time() - provider_start
                    logger.error(
                        f"{name} provider failed in {provider_time:.3f}s: {str(e)}"
                    )
                    return name, toolkit, []

            # Create tasks for all providers
            tasks = [
                load_single_provider(name, toolkit)
                for name, toolkit in provider_configs
            ]

            # Execute all provider loading tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and add categories
            successful_providers = []
            failed_providers = []
            total_tools_loaded = 0

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Provider task exception: {result}")
                    failed_providers.append("unknown")
                    continue

                name, toolkit, tools = result
                if tools:
                    category = ToolCategory(
                        name=name,
                        space=name,
                        require_integration=True,
                        integration_name=name,
                        is_delegated=True,
                    )
                    category.add_tools(tools)
                    self._categories[name] = category
                    successful_providers.append(name)
                    total_tools_loaded += len(tools)
                else:
                    failed_providers.append(name)

            total_time = time.time() - start_time
            logger.info(
                f"Provider tools loaded: {len(successful_providers)}/{len(provider_configs)} successful, {total_tools_loaded} total tools in {total_time:.3f}s"
            )

        # Run the async function in the event loop
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, schedule as a task
                import concurrent.futures

                logger.info("Scheduling provider tools loading in background...")
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, load_provider_tools())
                    # Don't wait for completion to avoid blocking startup
            else:
                # If no loop is running, run directly
                asyncio.run(load_provider_tools())
        except RuntimeError as e:
            # Fallback to synchronous loading if async fails
            logger.warning(
                f"Async loading failed - falling back to synchronous mode: {str(e)}"
            )
            self._initialize_provider_categories_sync()
        except Exception as e:
            # Unexpected error - still fallback to sync
            logger.error(
                f"Unexpected error in async setup - falling back to sync: {str(e)}"
            )
            self._initialize_provider_categories_sync()

    def _initialize_provider_categories_sync(self):
        """Fallback synchronous provider initialization."""
        import time

        from app.config.loggers import app_logger as logger

        logger.info("Loading provider tools synchronously...")
        start_time = time.time()

        provider_configs = [
            ("twitter", "TWITTER"),
            ("notion", "NOTION"),
            ("linkedin", "LINKEDIN"),
            ("google_sheets", "GOOGLE_SHEETS"),
            ("gmail", "GMAIL"),
        ]

        successful_providers = []
        failed_providers = []
        total_tools_loaded = 0

        for name, toolkit in provider_configs:
            provider_start = time.time()
            try:
                tools = composio_service.get_tools(tool_kit=toolkit)
                provider_time = time.time() - provider_start

                if tools:
                    logger.info(
                        f"{name} provider: {len(tools)} tools loaded in {provider_time:.3f}s"
                    )
                    successful_providers.append(name)
                    total_tools_loaded += len(tools)
                else:
                    logger.warning(
                        f"{name} provider: no tools found ({provider_time:.3f}s)"
                    )
                    failed_providers.append(name)

                category = ToolCategory(
                    name=name,
                    space=name,
                    require_integration=True,
                    integration_name=name,
                    is_delegated=True,
                )
                if tools:
                    category.add_tools(tools)
                self._categories[name] = category

            except Exception as e:
                provider_time = time.time() - provider_start
                logger.error(
                    f"{name} provider failed in {provider_time:.3f}s: {str(e)}"
                )
                failed_providers.append(name)

        total_time = time.time() - start_time
        logger.info(
            f"Provider tools loaded synchronously: {len(successful_providers)}/{len(provider_configs)} successful, {total_tools_loaded} total tools in {total_time:.3f}s"
        )

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
