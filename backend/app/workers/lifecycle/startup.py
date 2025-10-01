"""
ARQ worker startup functionality.
"""

import asyncio

from app.agents.core.graph_builder.build_graph import build_graph
from app.agents.core.graph_manager import GraphManager
from app.config.loggers import arq_worker_logger as logger
from app.core.provider_registration import (
    initialize_auto_providers,
    register_all_providers,
    setup_warnings,
)

# Set up common warning filters
setup_warnings()


async def startup(ctx: dict):
    """ARQ worker startup function."""

    logger.info("ARQ worker starting up...")

    # Initialize any resources needed by worker
    ctx["startup_time"] = asyncio.get_event_loop().time()

    # Register all lazy providers using common function
    register_all_providers("arq_worker")

    # Initialize auto providers using common function
    await initialize_auto_providers("arq_worker")

    async with build_graph() as normal_graph:
        GraphManager.set_graph(normal_graph)  # Set as default graph

    logger.info(
        "ARQ worker startup complete with workflow processing graph initialized"
    )
