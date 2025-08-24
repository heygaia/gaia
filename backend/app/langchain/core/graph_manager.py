"""
Graph manager module to handle LangGraph initialization and hold multiple graph instances.

This module helps avoid circular imports between app.api.v1 and app.langchain.agent.
"""

import asyncio
from typing import Any, Dict

from app.config.loggers import langchain_logger as logger


class GraphManager:
    _instance = None
    _graphs: Dict[str, Any] = {}
    _initialization_locks: Dict[str, asyncio.Lock] = {}
    _initialization_events: Dict[str, asyncio.Event] = {}
    _main_lock = asyncio.Lock()

    def __init__(self):
        # Initialize with default graph placeholders
        self._graphs = {}
        self._initialization_locks = {}
        self._initialization_events = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GraphManager()
        return cls._instance

    @classmethod
    async def _ensure_graph_tracking(cls, graph_name: str):
        """Ensure tracking structures exist for the given graph name."""
        async with cls._main_lock:
            if graph_name not in cls._initialization_locks:
                cls._initialization_locks[graph_name] = asyncio.Lock()
                cls._initialization_events[graph_name] = asyncio.Event()

    @classmethod
    async def set_graph(cls, graph_instance: Any, graph_name: str = "default"):
        """Set a graph instance with the given name (async version)."""
        # Ensure tracking structures exist
        await cls._ensure_graph_tracking(graph_name)

        if graph_name in cls._graphs and cls._graphs[graph_name] is not None:
            logger.info(f"LANGGRAPH: Graph '{graph_name}' already set, skipping")
            return

        cls._graphs[graph_name] = graph_instance
        cls._initialization_events[graph_name].set()
        logger.info(
            f"LANGGRAPH: Graph instance '{graph_name}' has been set successfully"
        )

    @classmethod
    def set_graph_sync(cls, graph_instance: Any, graph_name: str = "default"):
        """
        Synchronous version of set_graph for backward compatibility.
        Use this only when you're sure the tracking structures already exist.
        """
        if graph_name not in cls._initialization_locks:
            # Create basic structures synchronously - this should only be used
            # when we know we're in a safe context (like app startup)
            cls._initialization_locks[graph_name] = asyncio.Lock()
            cls._initialization_events[graph_name] = asyncio.Event()

        if graph_name in cls._graphs and cls._graphs[graph_name] is not None:
            logger.info(f"LANGGRAPH: Graph '{graph_name}' already set, skipping")
            return

        cls._graphs[graph_name] = graph_instance
        cls._initialization_events[graph_name].set()
        logger.info(
            f"LANGGRAPH: Graph instance '{graph_name}' has been set successfully"
        )

    @classmethod
    async def get_graph(cls, graph_name: str = "default") -> Any:
        """Get the graph instance by name, waiting for it to be initialized if necessary."""
        await cls._ensure_graph_tracking(graph_name)

        if graph_name not in cls._graphs or cls._graphs[graph_name] is None:
            logger.info(
                f"LANGGRAPH: Waiting for graph '{graph_name}' to be initialized..."
            )
            await cls._initialization_events[graph_name].wait()
            logger.info(
                f"LANGGRAPH: Graph '{graph_name}' initialization complete, proceeding"
            )

        return cls._graphs[graph_name]

    @classmethod
    def has_graph(cls, graph_name: str = "default") -> bool:
        """Check if a graph with the given name exists and is initialized."""
        return graph_name in cls._graphs and cls._graphs[graph_name] is not None

    @classmethod
    def list_graphs(cls) -> list[str]:
        """List all available graph names."""
        return [name for name, graph in cls._graphs.items() if graph is not None]

    @classmethod
    async def remove_graph(cls, graph_name: str):
        """Remove a graph instance (useful for cleanup or testing)."""
        await cls._ensure_graph_tracking(graph_name)

        if graph_name in cls._graphs:
            cls._graphs[graph_name] = None
            # Reset the event for potential re-initialization
            if graph_name in cls._initialization_events:
                cls._initialization_events[graph_name].clear()
            logger.info(f"LANGGRAPH: Graph '{graph_name}' has been removed")
        else:
            logger.warning(
                f"LANGGRAPH: Attempted to remove non-existent graph '{graph_name}'"
            )
