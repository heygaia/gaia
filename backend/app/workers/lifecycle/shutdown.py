"""
ARQ worker shutdown functionality.
"""

import asyncio

from app.config.loggers import arq_worker_logger as logger


async def shutdown(ctx: dict):
    """ARQ worker shutdown function."""
    logger.info("ARQ worker shutting down...")

    # Clean up any resources if needed
    startup_time = ctx.get("startup_time", 0)
    if startup_time:
        runtime = asyncio.get_event_loop().time() - startup_time
        logger.info(f"ARQ worker ran for {runtime:.2f} seconds")
