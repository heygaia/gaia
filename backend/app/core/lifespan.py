from contextlib import asynccontextmanager

from app.config.cloudinary import init_cloudinary
from app.config.loggers import app_logger as logger
from app.db.chromadb import init_chroma
from app.db.postgresql import close_postgresql_db, init_postgresql_db
from app.db.rabbitmq import publisher
from app.langchain.core.graph_builder.build_graph import build_graph
from app.langchain.core.graph_manager import GraphManager
from app.utils.nltk_utils import download_nltk_resources
from app.utils.text_utils import get_zero_shot_classifier
from app.utils.websocket_consumer import (
    start_websocket_consumer,
    stop_websocket_consumer,
)
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    try:
        logger.info("Starting up the API...")

        await init_chroma(app)
        download_nltk_resources()
        get_zero_shot_classifier()
        init_cloudinary()

        try:
            await init_postgresql_db()
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL database: {e}")
            raise RuntimeError("PostgreSQL initialization failed") from e

        # Create all database indexes
        try:
            from app.db.mongodb.mongodb import init_mongodb

            mongo_client = init_mongodb()

            await mongo_client._initialize_indexes()
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")

        # Initialize reminder scheduler and scan for pending reminders
        try:
            from app.services.reminder_service import initialize_scheduler

            scheduler = await initialize_scheduler()
            await scheduler.scan_and_schedule_pending_reminders()
            logger.info(
                "Reminder scheduler initialized and pending reminders scheduled"
            )
        except Exception as e:
            logger.error(f"Failed to initialize reminder scheduler: {e}")

        try:
            await publisher.connect()
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")

        try:
            await start_websocket_consumer()
            logger.info("WebSocket event consumer started")
        except Exception as e:
            logger.error(f"Failed to start WebSocket consumer: {e}")

        # Initialize the graph and store in GraphManager
        async with build_graph() as built_graph:
            GraphManager.set_graph(built_graph)
            yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise RuntimeError("Startup failed") from e
    finally:
        logger.info("Shutting down the API...")

        try:
            await close_postgresql_db()
        except Exception as e:
            logger.error(f"Error closing PostgreSQL database: {e}")

        # Close reminder scheduler
        try:
            from app.services.reminder_service import close_scheduler

            await close_scheduler()
            logger.info("Reminder scheduler closed")
        except Exception as e:
            logger.error(f"Error closing reminder scheduler: {e}")

        # Stop WebSocket consumer if running in main app
        try:
            await stop_websocket_consumer()
            logger.info("WebSocket event consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping WebSocket consumer: {e}")

        await publisher.close()
