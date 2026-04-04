import json
import redis
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.client = None
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")

    def get(self, key: str):
        if not self.client:
            return None
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, key: str, value, ttl: int = None):
        if not self.client:
            return
        ttl = ttl or settings.CACHE_TTL_DEFAULT
        self.client.setex(key, ttl, json.dumps(value, default=str))

    def delete(self, key: str):
        if not self.client:
            return
        self.client.delete(key)

    def delete_pattern(self, pattern: str):
        if not self.client:
            return
        for key in self.client.scan_iter(match=pattern):
            self.client.delete(key)

# Глобальный экземпляр
cache = RedisCache()