import asyncio
import warnings
from contextlib import asynccontextmanager

from app.agents.core.graph_builder.build_graph import build_default_graph
from app.agents.core.graph_builder.checkpointer_manager import init_checkpointer_manager
from app.agents.llm.client import register_llm_providers
from app.agents.tools.core.registry import init_tool_registry
from app.agents.tools.core.store import init_embeddings, initialize_tools_store
from app.config.cloudinary import init_cloudinary
from app.config.loggers import app_logger as logger
from app.core.lazy_loader import providers
from app.db.chromadb import init_chroma
from app.db.postgresql import init_postgresql_engine
from app.db.rabbitmq import init_rabbitmq_publisher
from app.helpers.lifespan_helpers import (
    _process_results,
    close_postgresql_async,
    close_publisher_async,
    close_reminder_scheduler,
    close_websocket_async,
    init_mongodb_async,
    init_reminder_service,
    init_websocket_consumer,
    init_workflow_service,
    setup_event_loop_policy,
)
from app.services.composio.composio_service import init_composio_service
from app.services.startup_validation import validate_startup_requirements
from fastapi import FastAPI
from pydantic import PydanticDeprecatedSince20

# Ignore specific deprecation warnings from pydantic in langchain_core
warnings.filterwarnings(
    "ignore", category=PydanticDeprecatedSince20, module="langchain_core.tools.base"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager with lazy providers.
    Handles startup and shutdown events.
    """
    try:
        logger.info("Starting up the API with lazy providers...")

        # Register all lazy providers
        logger.info("Registering lazy providers...")
        # Register all providers
        init_postgresql_engine()
        init_rabbitmq_publisher()
        register_llm_providers()
        build_default_graph()
        init_chroma()
        init_cloudinary()
        init_checkpointer_manager()
        init_tool_registry()
        init_composio_service()
        init_embeddings()
        initialize_tools_store()
        validate_startup_requirements()
        setup_event_loop_policy()

        logger.info("All lazy providers registered successfully")

        # Initialize services that still require eager initialization
        startup_tasks = [
            init_mongodb_async(),
            init_reminder_service(),
            init_workflow_service(),
            init_websocket_consumer(),
            providers.initialize_auto_providers(),
        ]

        # Run remaining initialization tasks in parallel
        results = await asyncio.gather(*startup_tasks, return_exceptions=True)

        _process_results(
            results,
            [
                "mongodb",
                "reminder_service",
                "workflow_service",
                "websocket_consumer",
                "tools_store",
                "lazy_providers_auto_initializer",
            ],
        )

        logger.info("All services initialized successfully")
        logger.info("Application startup complete")
        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise RuntimeError("Startup failed") from e

    finally:
        logger.info("Shutting down the API...")

        # Run all shutdown tasks in parallel
        shutdown_tasks = [
            close_postgresql_async(),
            close_reminder_scheduler(),
            close_websocket_async(),
            close_publisher_async(),
        ]

        # Use return_exceptions=True so one failure doesn't stop others during shutdown
        shutdown_results = await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        # Log any shutdown failures
        shutdown_service_names = [
            "postgresql",
            "reminder_scheduler",
            "websocket",
            "publisher",
        ]
        for i, result in enumerate(shutdown_results):
            if isinstance(result, Exception):
                logger.error(
                    f"Error during {shutdown_service_names[i]} shutdown: {result}"
                )

        logger.info("Application shutdown completed")
