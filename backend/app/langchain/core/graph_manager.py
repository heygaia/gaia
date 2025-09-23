"""
Graph manager module to handle LangGraph initialization and hold multiple graph instances.

This module helps avoid circular imports between app.api.v1 and app.langchain.agent.
"""

from typing import Any

from app.config.loggers import langchain_logger as logger
from app.core.lazy_loader import providers


class GraphManager:
    @classmethod
    def set_graph(cls, graph_instance: Any, graph_name: str = "default_graph"):
        """Set a graph instance with the given name."""
        providers.register(graph_name, loader_func=lambda: graph_instance)

    @classmethod
    async def get_graph(cls, graph_name: str = "default_graph") -> Any:
        """Get the graph instance by name."""
        graph = await providers.aget(graph_name)
        if graph is not None:
            logger.debug("Retrieved graph from lazy provider")
            return graph
