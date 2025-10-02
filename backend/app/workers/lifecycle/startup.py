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
    # Store startup time for monitoring/debugging
    ctx["startup_time"] = asyncio.get_event_loop().time()

    # LAZY LOADING SETUP: Register all lazy providers with the registry
    # This is synchronous and fast - just sets up provider factory functions
    # Add new lazy providers by calling their registration functions here
    # Example: init_new_lazy_service() - this registers but doesn't initialize
    register_all_providers("arq_worker")

    # AUTO-INIT LAZY PROVIDERS: Initialize providers marked with auto_initialize=True
    # This initializes global configs, DB connections, etc. that workers need immediately
    # DO NOT add regular worker services here - only the auto-init lazy providers call
    await initialize_auto_providers("arq_worker")

    # WORKER-SPECIFIC EAGER INITIALIZATION: Services that workers need ready immediately
    # Add worker-specific services that must be initialized before processing tasks
    # Example: await init_worker_specific_service()

    # Build and set the workflow processing graph for this worker
    async with build_graph() as normal_graph:
        GraphManager.set_graph(
            normal_graph
        )  # Set as default graph for workflow processing

    logger.info(
        "ARQ worker startup complete with workflow processing graph initialized"
    )
