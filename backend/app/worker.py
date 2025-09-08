import asyncio

# import json
import signal

from aio_pika import connect_robust

# from aio_pika.abc import AbstractIncomingMessage
from aiolimiter import AsyncLimiter

from app.config.loggers import worker_logger as logger
from app.config.settings import settings

# TODO: Analyze the rate limit and adjust based on actual LLM performance
llm_limiter = AsyncLimiter(10, 1)  # 10 tasks per second

stop_event = asyncio.Event()


# async def on_workflow_message(message: AbstractIncomingMessage):
#     import app.worker_node.process_workflow as process_workflow

#     async with message.process():
#         async with llm_limiter:
#             try:
#                 data = json.loads(message.body.decode())
#                 await process_workflow.process_workflow_generation(data)
#                 logger.info(
#                     f"Processing workflow message for todo: {data.get('todo_id')}"
#                 )
#             except Exception as e:
#                 logger.error(f"Failed to process workflow message: {e}")


async def shutdown(signal_name):
    logger.info(f"Received exit signal {signal_name}. Shutting down...")
    stop_event.set()


async def start_worker():
    connection = await connect_robust(settings.RABBITMQ_URL, timeout=10)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    # Set up workflow generation queue (email processing now handled by ARQ)
    # workflow_queue = await channel.declare_queue("workflow-generation", durable=True)
    # await workflow_queue.consume(on_workflow_message)

    logger.info(
        "Worker started on queue: workflow-generation (email processing via ARQ)"
    )

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
