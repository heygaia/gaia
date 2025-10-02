import asyncio
from contextlib import asynccontextmanager

from app.config.loggers import app_logger as logger
from app.core.provider_registration import (
    register_all_providers,
    initialize_auto_providers,
    setup_warnings,
)
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
)
from fastapi import FastAPI

setup_warnings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager with lazy providers.
    Handles startup and shutdown events.
    """
    try:
        logger.info("Starting up the API with lazy providers...")

        # LAZY LOADING SETUP: Register all lazy providers with the registry
        # This is synchronous and fast - just sets up provider factory functions
        # Add new lazy providers by calling their registration functions here
        # Example: init_new_lazy_service() - this registers but doesn't initialize
        register_all_providers("main_app")

        # EAGER INITIALIZATION: Services that MUST be ready before app starts
        # Add services here that need to be fully initialized before serving requests
        # These run in parallel for faster startup
        startup_tasks = [
            # Database connections that need to be ready immediately
            init_mongodb_async(),
            # Background services that need to start with the app
            init_reminder_service(),
            init_workflow_service(),
            init_websocket_consumer(),
            # AUTO-INIT LAZY PROVIDERS: Providers marked with auto_initialize=True
            # This initializes global configs, DB connections, etc. that are marked for auto-init
            # DO NOT add regular services here - only the auto-init lazy providers call
            initialize_auto_providers("main_app"),
        ]

        # Run remaining initialization tasks in parallel
        results = await asyncio.gather(*startup_tasks, return_exceptions=True)

        # RESULT PROCESSING: Check startup results and log any failures
        # The service names array MUST match the startup_tasks order exactly
        # Each name corresponds to its respective task in startup_tasks for error reporting
        # Add new service names here when adding new startup_tasks above
        _process_results(
            results,
            [
                "mongodb",  # matches init_mongodb_async()
                "reminder_service",  # matches init_reminder_service()
                "workflow_service",  # matches init_workflow_service()
                "websocket_consumer",  # matches init_websocket_consumer()
                "lazy_providers_auto_initializer",  # matches initialize_auto_providers()
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

        # SHUTDOWN CLEANUP: Close all connections and cleanup resources
        # Add cleanup functions here for services that need graceful shutdown
        # These run in parallel for faster shutdown
        shutdown_tasks = [
            # Database connection cleanup
            close_postgresql_async(),
            # Background service cleanup
            close_reminder_scheduler(),
            close_websocket_async(),
            # Message queue cleanup
            close_publisher_async(),
            # Add new cleanup functions here:
            # close_new_service_async(),
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
