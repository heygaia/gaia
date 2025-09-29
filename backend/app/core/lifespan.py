import asyncio
from contextlib import asynccontextmanager

import uvloop
from app.agents.core.graph_builder.build_graph import build_default_graph
from app.agents.core.graph_builder.checkpointer_manager import (
    init_checkpointer_managers,
)
from app.agents.llm.client import register_llm_providers
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
    init_tools_store_async,
    init_websocket_consumer,
    init_workflow_service,
)
from app.services.startup_validation import validate_startup_requirements
from fastapi import FastAPI


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
        init_checkpointer_managers()
        validate_startup_requirements()

        # Use uvloop for better performance if available instead of asyncio
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        logger.info("All lazy providers registered successfully")

        # Initialize services that still require eager initialization
        startup_tasks = [
            init_mongodb_async(),
            init_reminder_service(),
            init_workflow_service(),
            init_websocket_consumer(),
            init_tools_store_async(),
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
