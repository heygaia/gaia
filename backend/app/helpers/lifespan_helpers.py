from app.agents.tools.core.store import initialize_tools_store
from app.config.loggers import app_logger as logger
from app.core.websocket_consumer import (
    start_websocket_consumer,
    stop_websocket_consumer,
)
from app.db.postgresql import close_postgresql_db
from app.db.rabbitmq import get_rabbitmq_publisher
from app.services.reminder_service import reminder_scheduler
from app.services.workflow.scheduler import workflow_scheduler


async def init_reminder_service():
    """Initialize reminder scheduler and scan for pending reminders."""
    try:
        await reminder_scheduler.initialize()
        await reminder_scheduler.scan_and_schedule_pending_tasks()
        logger.info("Reminder scheduler initialized and pending reminders scheduled")
    except Exception as e:
        logger.error(f"Failed to initialize reminder scheduler: {e}")
        raise


async def init_workflow_service():
    """Initialize workflow service."""
    try:
        await workflow_scheduler.initialize()
        await workflow_scheduler.scan_and_schedule_pending_tasks()
        logger.info("Workflow service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize workflow service: {e}")
        raise


async def init_websocket_consumer():
    """Initialize WebSocket event consumer."""
    try:
        await start_websocket_consumer()
        logger.info("WebSocket event consumer started")
    except Exception as e:
        logger.error(f"Failed to start WebSocket consumer: {e}")
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
        publisher = await get_rabbitmq_publisher()

        if publisher:
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
