import asyncio
import json
import signal

from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from aiolimiter import AsyncLimiter

from app.config.loggers import worker_logger as logger
from app.config.settings import settings
from app.utils.session_logger.email_session_logger import create_session, end_session

# TODO: Analyze the rate limit and adjust based on actual LLM performance
llm_limiter = AsyncLimiter(10, 1)  # 10 tasks per second

stop_event = asyncio.Event()


async def on_email_message(message: AbstractIncomingMessage):
    import app.worker_node.process_email as process_emails

    async with message.process():
        async with llm_limiter:
            session = None
            try:
                # Parse message data
                data = json.loads(message.body.decode())
                history_id = data.get("history_id")
                email_address = data.get("email_address")

                # Create processing session
                session = create_session(history_id, email_address)

                session.log_milestone(
                    "Message received",
                    {
                        "queue_message_id": getattr(message, "message_id", "unknown"),
                        "routing_key": getattr(message, "routing_key", "unknown"),
                    },
                )

                # Process emails with session
                result = await process_emails.process_emails(
                    history_id=history_id, email=email_address, session=session
                )

                session.log_session_summary(result)
                logger.info(f"Session {session.session_id} completed successfully")

            except json.JSONDecodeError as e:
                error_msg = f"Failed to decode message JSON: {e}"
                if session:
                    session.log_error("JSON_DECODE_ERROR", error_msg)
                    session.log_session_summary(
                        {"status": "failed", "error": error_msg}
                    )
                logger.error(error_msg)

            except Exception as e:
                error_msg = f"Failed to process message: {e}"
                if session:
                    session.log_error("PROCESSING_ERROR", error_msg)
                    session.log_session_summary(
                        {"status": "failed", "error": error_msg}
                    )
                logger.error(error_msg)

            finally:
                # Clean up session
                if session:
                    end_session(session.session_id)


async def on_workflow_message(message: AbstractIncomingMessage):
    import app.worker_node.process_workflow as process_workflow

    async with message.process():
        async with llm_limiter:
            try:
                data = json.loads(message.body.decode())
                await process_workflow.process_workflow_generation(data)
                logger.info(
                    f"Processing workflow message for todo: {data.get('todo_id')}"
                )
            except Exception as e:
                logger.error(f"Failed to process workflow message: {e}")


async def shutdown(signal_name):
    logger.info(f"Received exit signal {signal_name}. Shutting down...")
    stop_event.set()


async def start_worker():
    from app.langchain.core.graph_builder.build_mail_processing_graph import (
        build_mail_processing_graph,
    )
    from app.langchain.core.graph_manager import GraphManager

    connection = await connect_robust(settings.RABBITMQ_URL, timeout=10)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    # Set up email processing queue
    email_queue = await channel.declare_queue("email-events", durable=True)
    await email_queue.consume(on_email_message)

    # Set up workflow generation queue
    workflow_queue = await channel.declare_queue("workflow-generation", durable=True)
    await workflow_queue.consume(on_workflow_message)

    # Build the processing graph
    async with build_mail_processing_graph() as built_graph:
        await GraphManager.set_graph(built_graph, graph_name="mail_processing")

    logger.info("Worker started on queues: email-events, workflow-generation")

    # Handle shutdown signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s.name))
        )

    await stop_event.wait()

    logger.info("Closing connection...")
    await connection.close()


if __name__ == "__main__":
    try:
        asyncio.run(start_worker())
    except Exception as e:
        logger.error(f"Worker encountered an error: {e}", exc_info=True)
