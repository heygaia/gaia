import asyncio
from contextlib import asynccontextmanager

from app.config.cloudinary import init_cloudinary
from app.config.loggers import app_logger as logger
from app.db.chromadb import init_chroma
from app.db.postgresql import close_postgresql_db, init_postgresql_db
from app.db.rabbitmq import publisher
from app.langchain.core.graph_builder.build_graph import build_graph
from app.langchain.core.graph_manager import GraphManager
from app.langchain.tools.core.store import initialize_tools_store
from app.utils.websocket_consumer import (
    start_websocket_consumer,
    stop_websocket_consumer,
)
from fastapi import FastAPI


async def init_chroma_async(app):
    """Initialize Chroma database."""
    try:
        await init_chroma(app)
        logger.info("Chroma initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Chroma: {e}")
        raise


async def init_postgresql_async():
    """Initialize PostgreSQL database."""
    try:
        await init_postgresql_db()
        logger.info("PostgreSQL initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL database: {e}")
        raise RuntimeError("PostgreSQL initialization failed") from e


async def setup_checkpointer_manager():
    """Setup checkpointer manager for LangGraph."""
    try:
        from app.langchain.core.graph_builder.checkpointer_manager import (
            checkpointer_manager,
            checkpointer_manager_shallow,
        )

        await checkpointer_manager.setup()
        await checkpointer_manager_shallow.setup()
    except Exception as e:
        logger.error(f"Failed to setup checkpointer manager: {e}")
        raise RuntimeError("Checkpointer manager setup failed") from e


async def init_cloudinary_async():
    """Initialize Cloudinary service."""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, init_cloudinary)
        logger.info("Cloudinary initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Cloudinary: {e}")
        raise


async def init_reminder_service():
    """Initialize reminder scheduler and scan for pending reminders."""
    try:
        from app.services.reminder_service import reminder_scheduler

        await reminder_scheduler.initialize()
        await reminder_scheduler.scan_and_schedule_pending_tasks()
        logger.info("Reminder scheduler initialized and pending reminders scheduled")
    except Exception as e:
        logger.error(f"Failed to initialize reminder scheduler: {e}")
        raise


async def init_workflow_service():
    """Initialize workflow service."""
    try:
        from app.services.workflow.scheduler_service import workflow_scheduler_service

        await workflow_scheduler_service.initialize()
        await workflow_scheduler_service.scheduler.scan_and_schedule_pending_tasks()
        logger.info("Workflow service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize workflow service: {e}")
        raise


async def init_rabbitmq():
    """Initialize RabbitMQ connection."""
    try:
        await publisher.connect()
        logger.info("RabbitMQ connection established")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise


async def init_websocket_consumer():
    """Initialize WebSocket event consumer."""
    try:
        await start_websocket_consumer()
        logger.info("WebSocket event consumer started")
    except Exception as e:
        logger.error(f"Failed to start WebSocket consumer: {e}")
        raise


async def init_default_graph():
    """Initialize default graph and store in GraphManager."""
    try:
        async with build_graph() as built_graph:
            await GraphManager.set_graph(built_graph)
            logger.info("Default graph initialized")
    except Exception as e:
        logger.error(f"Failed to initialize default graph: {e}")
        raise


async def init_tools_store_async():
    """Initialize tools store."""
    try:
        await initialize_tools_store()
        logger.info("Tools store initialized")
    except Exception as e:
        logger.error(f"Failed to initialize tools store: {e}")
        raise


async def init_mongodb_async():
    """Initialize MongoDB and create database indexes."""
    try:
        from app.db.mongodb.mongodb import init_mongodb

        mongo_client = init_mongodb()
        await mongo_client._initialize_indexes()
        logger.info("MongoDB initialized and indexes created")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB and create indexes: {e}")
        raise


# Shutdown methods
async def close_postgresql_async():
    """Close PostgreSQL database connection."""
    try:
        await close_postgresql_db()
        logger.info("PostgreSQL database closed")
    except Exception as e:
        logger.error(f"Error closing PostgreSQL database: {e}")


async def close_reminder_scheduler():
    """Close reminder scheduler."""
    try:
        from app.services.reminder_service import reminder_scheduler

        await reminder_scheduler.close()
        logger.info("Reminder scheduler closed")
    except Exception as e:
        logger.error(f"Error closing reminder scheduler: {e}")


async def close_websocket_async():
    """Close WebSocket event consumer."""
    try:
        await stop_websocket_consumer()
        logger.info("WebSocket event consumer stopped")
    except Exception as e:
        logger.error(f"Error stopping WebSocket consumer: {e}")


async def close_publisher_async():
    """Close publisher connection."""
    try:
        await publisher.close()
        logger.info("Publisher closed")
    except Exception as e:
        logger.error(f"Error closing publisher: {e}")


def _process_results(results, service_names):
    failed_services = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed_services.append(service_names[i])
            logger.error(f"Failed to initialize {service_names[i]}: {result}")

        if failed_services:
            error_msg = f"Failed to initialize services: {failed_services}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    try:
        logger.info("Starting up the API...")

        core_tasks = [
            init_postgresql_async(),
            setup_checkpointer_manager(),
        ]

        results = await asyncio.gather(*core_tasks, return_exceptions=True)

        _process_results(results, ["postgresql", "checkpointer_manager"])

        # Initialize all services in parallel
        startup_tasks = [
            init_chroma_async(app),
            init_mongodb_async(),
            init_cloudinary_async(),
            init_reminder_service(),
            init_workflow_service(),
            init_rabbitmq(),
            init_websocket_consumer(),
            init_default_graph(),
            init_tools_store_async(),
        ]

        # Run all initialization tasks in parallel
        results = await asyncio.gather(*startup_tasks, return_exceptions=True)

        _process_results(
            results,
            [
                "chroma",
                "cloudinary",
                "mongodb",
                "reminder_service",
                "workflow_service",
                "rabbitmq",
                "websocket_consumer",
                "default_graph",
                "tools_store",
            ],
        )

        logger.info("All services initialized successfully")
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
