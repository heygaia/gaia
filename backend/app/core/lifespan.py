from contextlib import asynccontextmanager

from app.config.cloudinary import init_cloudinary
from app.config.loggers import app_logger as logger
from app.db.chromadb import init_chroma
from app.db.rabbitmq import publisher
from app.langchain.core.graph_builder.build_graph import build_graph
from app.langchain.core.graph_manager import GraphManager
from app.utils.nltk_utils import download_nltk_resources
from app.utils.text_utils import get_zero_shot_classifier
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

        # Create all database indexes
        try:
            from app.db.mongodb.mongodb import init_mongodb

            mongo_client = init_mongodb()

            await mongo_client._initialize_indexes()
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")

        # Initialize reminder scheduler and scan for pending reminders
        try:
            from app.utils.arq_event import scheduler

            await scheduler.initialize()
            await scheduler.scan_and_schedule_pending_events()
            logger.info("Reminder scheduler initialized and pending events scheduled")
        except Exception as e:
            logger.error(f"Failed to initialize reminder scheduler: {e}")

        try:
            await publisher.connect()
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")

        # Initialize the graph and store in GraphManager
        async with build_graph() as built_graph:
            GraphManager.set_graph(built_graph)
            yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise RuntimeError("Startup failed") from e
    finally:
        logger.info("Shutting down the API...")

        # Close reminder scheduler
        try:
            from app.utils.arq_event import scheduler

            await scheduler.close()
            logger.info("Reminder scheduler closed")
        except Exception as e:
            logger.error(f"Error closing reminder scheduler: {e}")

        await publisher.close()
