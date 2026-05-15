import json
import asyncio
from app.core.queue import QueueService
from app.services.email_service import EmailService
from app.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class QueueConsumer:
    _running = False
    
    @classmethod
    async def start(cls):
        """Запуск фонового потребителя"""
        cls._running = True
        queue = QueueService.get_queue()
        
        async def on_message(message):
            body = json.loads(message.body.decode())
            event_id = body.get('eventId')
            
            # Проверяем идемпотентность
            cache_key = f"testing:email:sent:{event_id}"
            if cache.get(cache_key):
                logger.info(f"Event {event_id} already processed, skipping")
                await message.ack()
                return
            
            payload = body.get('payload', {})
            email = payload.get('email')
            display_name = payload.get('displayName', email.split('@')[0] if email else 'User')
            
            try:
                await EmailService.send_welcome_email(email, display_name)
                cache.set(cache_key, "sent", ttl=86400)
                logger.info(f"Event {event_id} processed successfully")
                await message.ack()
            except Exception as e:
                metadata = body.get('metadata', {})
                attempt = metadata.get('attempt', 1)
                if attempt >= 3:
                    logger.error(f"Event {event_id} failed after 3 attempts: {e}")
                    await message.nack(requeue=False)
                else:
                    logger.warning(f"Event {event_id} attempt {attempt} failed: {e}")
                    body['metadata']['attempt'] = attempt + 1
                    await QueueService.publish('user.registered', payload)
                    await message.ack()
        
        await queue.consume(on_message)
        logger.info("Consumer started, waiting for messages...")
        
        while cls._running:
            await asyncio.sleep(1)
    
    @classmethod
    async def stop(cls):
        cls._running = False