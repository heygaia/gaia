# rabbitmq_utils.py
import aio_pika
from aio_pika import Message

from app.config.settings import settings


class RabbitMQPublisher:
    def __init__(self, amqp_url=settings.RABBITMQ_URL):
        self.amqp_url = amqp_url
        self.connection = None
        self.channel = None
        self.declared_queues = set()

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.amqp_url)
        self.channel = await self.connection.channel()

    async def declare_queue(self, queue_name: str):
        if queue_name not in self.declared_queues and self.channel:
            await self.channel.declare_queue(queue_name, durable=True)
            self.declared_queues.add(queue_name)

    async def publish(self, queue_name: str, body: bytes):
        if not self.channel:
            raise RuntimeError("Channel is not connected. Call connect() first.")
        await self.declare_queue(queue_name)
        message = Message(body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT)

        await self.channel.default_exchange.publish(message, routing_key=queue_name)

    async def close(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()


publisher = RabbitMQPublisher()
