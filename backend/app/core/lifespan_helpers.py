"""
Lifespan helper functions for application startup and shutdown.
"""

import asyncio
import sys

from app.config.loggers import app_logger as logger


def setup_event_loop_policy() -> None:
    """
    Set up the optimal event loop policy for the current platform.

    Uses uvloop on Unix-like systems for better performance,
    falls back to default event loop policy on Windows or if uvloop is unavailable.
    """
    if sys.platform != "win32":
        try:
            import uvloop

            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            logger.info("Using uvloop event loop policy")
        except ImportError:
            logger.warning("uvloop not available, using default event loop policy")
    else:
        logger.info("Windows detected, using default event loop policy")
