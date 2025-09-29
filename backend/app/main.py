"""
Main module for the GAIA FastAPI application.

This module initializes and runs the FastAPI application.
"""

import time
import warnings

from pydantic import PydanticDeprecatedSince20

from app.config.loggers import app_logger as logger
from app.config.sentry import init_sentry
from app.core.app_factory import create_app

warnings.filterwarnings(
    "ignore", category=PydanticDeprecatedSince20, module="langchain_core.tools.base"
)

# Create the FastAPI application
logger.info("Starting application initialization...")
app_creation_start = time.time()
app = create_app()
init_sentry()

logger.info(f"Application setup completed in {(time.time() - app_creation_start):.3f}s")
