import json
from datetime import datetime
from typing import Any

import redis.asyncio as redis
from app.config.loggers import redis_logger as logger
from app.config.settings import settings
from pydantic import BaseModel

ONE_YEAR_TTL = 31_536_000
ONE_HOUR_TTL = 3600
CACHE_TTL = ONE_HOUR_TTL  # Default cache TTL for todos
STATS_CACHE_TTL = 30 * 60  # 30 minutes for stats (increased from 5)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class RedisCache:
    def __init__(self, redis_url="redis://localhost:6379", default_ttl=3600):
        self.redis_url = settings.REDIS_URL or redis_url
        self.default_ttl = default_ttl
        self.redis = None

        if self.redis_url:
            try:
                self.redis = redis.from_url(self.redis_url, decode_responses=True)
                logger.info("Redis connection initialized.")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
        else:
            logger.warning("REDIS_URL is not set. Caching will be disabled.")

    async def get(self, key: str):
        """
        Get a cached value by key.
        """
        if not self.redis:
            logger.warning("Redis is not initialized. Skipping get operation.")
            return None

        try:
            value = await self.redis.get(name=key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error accessing Redis for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set a cached value with an optional TTL.
        """
        if not self.redis:
            logger.warning("Redis is not initialized. Skipping set operation.")
            return

        try:
            ttl = ttl or self.default_ttl

            # Handle Pydantic models
            if isinstance(value, BaseModel):
                # Use Pydantic's JSON encoder to handle datetime and other special types
                json_str = value.model_dump_json()
                await self.redis.setex(key, ttl, json_str)
            else:
                await self.redis.setex(key, ttl, json.dumps(value, cls=DateTimeEncoder))
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")

    async def delete(self, key: str):
        """
        Delete a cached key.
        """
        if not self.redis:
            logger.warning("Redis is not initialized. Skipping delete operation.")
            return

        try:
            await self.redis.delete(key)
            logger.info(f"Cache deleted for key: {key}")
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}")

    @property
    def client(self):
        """
        Get the Redis client instance.
        """
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            logger.info("Re-initialized Redis connection.")

        return self.redis


# Initialize the Redis cache
redis_cache = RedisCache()


# Wrappers for RedisCache instance methods
async def get_cache(key: str):
    """
    Get a cached value by key.
    """
    return await redis_cache.get(key)


async def set_cache(key: str, value: Any, ttl: int = ONE_YEAR_TTL):
    """
    Set a cached value with an optional TTL.
    """
    await redis_cache.set(key, value, ttl)


async def delete_cache(key: str):
    """
    Delete a cached key.
    """
    # TODO: Optimize this
    if key.endswith("*"):
        await delete_cache_by_pattern(key)
        return

    await redis_cache.delete(key)


async def delete_cache_by_pattern(pattern: str):
    """
    Delete cached keys by pattern.
    """
    if not redis_cache.redis:
        logger.warning("Redis is not initialized. Skipping delete operation.")
        return

    try:
        keys = await redis_cache.redis.keys(pattern)
        if not keys:
            logger.info(f"No keys found for pattern: {pattern}")
            return
        for key in keys:
            await redis_cache.delete(key)
            logger.info(f"Cache deleted for key: {key}")
    except Exception as e:
        logger.error(f"Error deleting Redis keys by pattern {pattern}: {e}")


# Caching decorators have been moved to app.decorators.caching
# Import them from there: from app.decorators.caching import Cacheable, CacheInvalidator
