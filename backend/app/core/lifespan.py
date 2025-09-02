from contextlib import asynccontextmanager

from app.config.cloudinary import init_cloudinary
from app.db.chromadb import init_chroma
from app.db.postgresql import close_postgresql_db, init_postgresql_db
from app.db.rabbitmq import publisher
from app.langchain.core.graph_builder.build_graph import build_graph
from app.langchain.core.graph_manager import GraphManager
from app.utils.websocket_consumer import (
    start_websocket_consumer,
    stop_websocket_consumer,
)
from app.config.settings import get_settings

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    try:
        # Load secrets first before other initializations
        get_settings()

        # ChromaDB initialization
        await init_chroma(app)

        # Cloudinary initialization
        init_cloudinary()

        # PostgreSQL initialization
        try:
            await init_postgresql_db()
        except Exception as e:
            raise RuntimeError("PostgreSQL initialization failed") from e

        # MongoDB indexes creation
        try:
            from app.db.mongodb.mongodb import init_mongodb

            mongo_client = init_mongodb()
            await mongo_client._initialize_indexes()
        except Exception as e:
            pass

        # Reminder scheduler initialization
        try:
            from app.services.reminder_service import initialize_scheduler

            scheduler = await initialize_scheduler()
            await scheduler.scan_and_schedule_pending_reminders()
        except Exception as e:
            pass

        # RabbitMQ connection
        try:
            await publisher.connect()
        except Exception as e:
            pass

        # WebSocket consumer startup
        try:
            await start_websocket_consumer()
        except Exception as e:
            pass

        # Graph initialization
        async with build_graph() as built_graph:
            GraphManager.set_graph(built_graph)

            # This is where the app runs - yield control back to FastAPI
            yield

    except Exception as e:
        raise RuntimeError("Startup failed") from e
    finally:
        # Shutdown sequence
        try:
            await close_postgresql_db()
        except Exception as e:
            pass

        # Close reminder scheduler
        try:
            from app.services.reminder_service import close_scheduler

            await close_scheduler()
        except Exception as e:
            pass

        # Stop WebSocket consumer if running in main app
        try:
            await stop_websocket_consumer()
        except Exception as e:
            pass

        await publisher.close()
