"""
ARQ worker startup functionality.
"""

import asyncio

from app.config.loggers import arq_worker_logger as logger
from app.langchain.llm.client import init_llm


async def startup(ctx: dict):
    """ARQ worker startup function."""
    from app.langchain.core.graph_builder.build_graph import build_graph
    from app.langchain.core.graph_manager import GraphManager

    logger.info("ARQ worker starting up...")

    # Initialize any resources needed by worker
    ctx["startup_time"] = asyncio.get_event_loop().time()

    llm = init_llm()

    # Build the normal graph (same as main app) but with in-memory checkpointer for ARQ worker
    async with (
        build_graph(
            chat_llm=llm,  # type: ignore[call-arg]
            in_memory_checkpointer=True,  # Use in-memory for ARQ worker to avoid DB connection issues
        ) as normal_graph
    ):
        GraphManager.set_graph(normal_graph)  # Set as default graph

    logger.info(
        "ARQ worker startup complete with workflow processing graph initialized"
    )
