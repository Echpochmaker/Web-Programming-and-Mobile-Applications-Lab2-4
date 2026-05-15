import aio_pika
import json
import uuid
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class QueueService:
    _connection = None
    _channel = None
    
    @classmethod
    async def connect(cls):
        """Подключение к RabbitMQ"""
        cls._connection = await aio_pika.connect_robust(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            login=settings.RABBITMQ_USER,
            password=settings.RABBITMQ_PASS,
        )
        cls._channel = await cls._connection.channel()
        
        # Объявляем exchange (долговечный)
        cls.exchange = await cls._channel.declare_exchange(
            'app.events',
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        # Объявляем Dead Letter Exchange
        cls.dlx_exchange = await cls._channel.declare_exchange(
            'app.dlx',
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        # Объявляем очередь
        cls.queue = await cls._channel.declare_queue(
            settings.QUEUE_USER_REGISTERED if hasattr(settings, 'QUEUE_USER_REGISTERED') else 'wp.auth.user.registered',
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'app.dlx',
                'x-dead-letter-routing-key': 'user.registered'
            }
        )
        
        # Привязываем очередь к exchange
        await cls.queue.bind(cls.exchange, routing_key='user.registered')
        
        # Объявляем DLQ
        cls.dlq = await cls._channel.declare_queue(
            'wp.auth.user.registered.dlq',
            durable=True
        )
        await cls.dlq.bind(cls.dlx_exchange, routing_key='user.registered')
        
        logger.info("RabbitMQ connected and queues declared")
    
    @classmethod
    async def publish(cls, routing_key: str, payload: dict):
        """Публикация сообщения"""
        message_body = {
            "eventId": str(uuid.uuid4()),
            "eventType": "user.registered",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
            "metadata": {
                "attempt": 1,
                "sourceService": "auth-service"
            }
        }
        
        message = aio_pika.Message(
            body=json.dumps(message_body, default=str).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type='application/json'
        )
        
        await cls.exchange.publish(message, routing_key=routing_key)
        logger.info(f"Event published: {message_body['eventId']}")
    
    @classmethod
    async def close(cls):
        if cls._connection:
            await cls._connection.close()
    
    @classmethod
    def get_channel(cls):
        return cls._channel
    
    @classmethod
    def get_queue(cls):
        return cls.queue