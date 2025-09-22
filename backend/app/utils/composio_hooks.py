"""
Unified hook system for Composio tool param and output modification.

This module provides a plug-and-play architecture for registering before_execute
and after_execute hooks for any Composio tool. The system allows centralized
registration and execution of param modifiers and output processors.
"""

from typing import Any, Callable, Dict, List

from composio.types import ToolExecuteParams

from app.config.loggers import app_logger as logger


class ComposioHookRegistry:
    """
    Registry for managing before_execute and after_execute hooks for Composio tools.

    This class provides a centralized way to register and execute param modifiers
    and output processors for specific tools, enabling a plug-and-play architecture.
    """

    def __init__(self):
        # Registry for before_execute hooks (param modifiers)
        self._before_hooks: Dict[
            str, List[Callable[[str, str, ToolExecuteParams], ToolExecuteParams]]
        ] = {}

        # Registry for after_execute hooks (output processors)
        self._after_hooks: Dict[str, List[Callable[[str, str, Any], Any]]] = {}

        # Tools that have registered hooks
        self._registered_tools: set = set()

    def register_before_hook(
        self,
        tool_name: str,
        hook_func: Callable[[str, str, ToolExecuteParams], ToolExecuteParams],
    ) -> None:
        """
        Register a before_execute hook for a specific tool.

        Args:
            tool_name: Name of the tool to register the hook for
            hook_func: Function that takes (tool, toolkit, params) and returns modified params
        """
        if tool_name not in self._before_hooks:
            self._before_hooks[tool_name] = []

        self._before_hooks[tool_name].append(hook_func)
        self._registered_tools.add(tool_name)
        logger.debug(f"Registered before_execute hook for tool: {tool_name}")

    def register_after_hook(
        self, tool_name: str, hook_func: Callable[[str, str, Any], Any]
    ) -> None:
        """
        Register an after_execute hook for a specific tool.

        Args:
            tool_name: Name of the tool to register the hook for
            hook_func: Function that takes (tool, toolkit, response) and returns modified response
        """
        if tool_name not in self._after_hooks:
            self._after_hooks[tool_name] = []

        self._after_hooks[tool_name].append(hook_func)
        self._registered_tools.add(tool_name)
        logger.debug(f"Registered after_execute hook for tool: {tool_name}")

    def get_registered_tools(self) -> List[str]:
        """Get list of all tools that have registered hooks."""
        return list(self._registered_tools)

    def execute_before_hooks(
        self, tool: str, toolkit: str, params: ToolExecuteParams
    ) -> ToolExecuteParams:
        """
        Execute all registered before_execute hooks for a tool.

        Args:
            tool: Tool name
            toolkit: Toolkit name
            params: Original tool execution parameters

        Returns:
            Modified parameters after applying all hooks
        """
        if tool not in self._before_hooks:
            return params

        modified_params = params
        for hook_func in self._before_hooks[tool]:
            try:
                modified_params = hook_func(tool, toolkit, modified_params)
            except Exception as e:
                logger.error(f"Error executing before_execute hook for {tool}: {e}")
                # Continue with other hooks even if one fails

        return modified_params

    def execute_after_hooks(self, tool: str, toolkit: str, response: Any) -> Any:
        """
        Execute all registered after_execute hooks for a tool.

        Args:
            tool: Tool name
            toolkit: Toolkit name
            response: Original tool execution response

        Returns:
            Modified response after applying all hooks
        """
        if tool not in self._after_hooks:
            return response

        modified_response = response
        for hook_func in self._after_hooks[tool]:
            try:
                modified_response = hook_func(tool, toolkit, modified_response)
            except Exception as e:
                logger.error(f"Error executing after_execute hook for {tool}: {e}")
                # Continue with other hooks even if one fails

        return modified_response


# Global registry instance
hook_registry = ComposioHookRegistry()


def master_before_execute_hook(
    tool: str, toolkit: str, params: ToolExecuteParams
) -> ToolExecuteParams:
    """
    Master before_execute hook that executes all registered param modifiers.

    This function serves as the single entry point for all before_execute hooks
    and delegates to the appropriate registered hooks based on the tool name.
    """
    return hook_registry.execute_before_hooks(tool, toolkit, params)


def master_after_execute_hook(tool: str, toolkit: str, response: Any) -> Any:
    """
    Master after_execute hook that executes all registered output processors.

    This function serves as the single entry point for all after_execute hooks
    and delegates to the appropriate registered hooks based on the tool name.
    """
    return hook_registry.execute_after_hooks(tool, toolkit, response)


def register_before_hook(tool_name: str):
    """
    Decorator for registering before_execute hooks.

    Usage:
        @register_before_hook("GMAIL_FETCH_EMAILS")
        def modify_gmail_fetch_params(tool, toolkit, params):
            # Modify params
            return params
    """

    def decorator(func: Callable[[str, str, ToolExecuteParams], ToolExecuteParams]):
        hook_registry.register_before_hook(tool_name, func)
        return func

    return decorator


def register_after_hook(tool_name: str):
    """
    Decorator for registering after_execute hooks.

    Usage:
        @register_after_hook("GMAIL_FETCH_EMAILS")
        def process_gmail_fetch_output(tool, toolkit, response):
            # Process response
            return response
    """

    def decorator(func: Callable[[str, str, Any], Any]):
        hook_registry.register_after_hook(tool_name, func)
        return func

    return decorator
