"""
Caching decorators for Redis-based caching functionality.

This module provides decorators for caching function results and cache invalidation.
"""

import asyncio
import functools
import inspect
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, TypeVar

from app.config.loggers import redis_logger as logger
from app.db.redis import ONE_YEAR_TTL, delete_cache, get_cache, set_cache

T = TypeVar("T")


class Cacheable(Generic[T]):
    """
    A decorator class that provides caching functionality with
    support for template-based keys and custom key generators.
    """

    def __init__(
        self,
        key_pattern: Optional[str] = None,
        key_generator: Optional[Callable] = None,
        key: Optional[str] = None,
        ttl: int = ONE_YEAR_TTL,
        serializer: Optional[Callable[[T], Any]] = None,
        deserializer: Optional[Callable[[Any], T]] = None,
    ):
        """
        Initialize the cache decorator.

        Args:
            key_pattern: Optional string template for the cache key (e.g. "{arg1}:{arg2}")
            key_generator: Optional custom function to generate cache keys
            ttl: Time-to-live for cache entries in seconds. None means no expiration
            key: Optional static key for caching
            serializer: Optional function to serialize the value before caching
            deserializer: Optional function to deserialize the value after retrieving from cache
        """
        self.key_pattern = key_pattern
        self.key_generator = key_generator
        self.key = key
        if not key and not key_pattern and not key_generator:
            raise ValueError(
                "Either key, key_pattern, or key_generator must be provided."
            )
        self.ttl = ttl
        self.serializer = serializer
        self.deserializer = deserializer

    def __call__(
        self, func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        """
        Apply the cache decorator to a function.

        Args:
            func: The function to be cached

        Returns:
            Wrapped function with caching behavior
        """

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate the cache key
            if self.key:
                cache_key = self.key
            elif self.key_generator:
                cache_key = await self.key_generator(func.__name__, *args, **kwargs)
            else:
                if not self.key_pattern:
                    raise ValueError(
                        "key_pattern must be provided if key_generator is not used."
                    )

                func_signature = inspect.signature(func)
                bound_args = func_signature.bind(*args, **kwargs)
                bound_args.apply_defaults()

                cache_key = _pattern_to_key(
                    self.key_pattern, arguments=bound_args.arguments
                )

            # Check if the value is already cached
            cached_value = await get_cache(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                if self.deserializer:
                    cached_value = self.deserializer(cached_value)
                return cached_value

            # Call the original function and cache the result
            result = await func(*args, **kwargs)

            serialized_result = result
            if self.serializer:
                serialized_result = self.serializer(result)

            logger.debug(f"Cache miss for key: {cache_key}")
            logger.debug(f"Setting cache for key: {cache_key}")

            # Let set_cache handle Pydantic serialization
            await set_cache(key=cache_key, value=serialized_result, ttl=self.ttl)

            return result

        return wrapper


class CacheInvalidator:
    """
    A decorator class that provides cache invalidation functionality.
    """

    def __init__(
        self,
        key_patterns: Optional[List[str]] = None,
        key_generator: Optional[Callable] = None,
        key: Optional[str] = None,
    ):
        """
        Initialize the cache decorator.

        Args:
            key_pattern: Optional string template for the cache key (e.g. "{arg1}:{arg2}")
            key_generator: Optional custom function to generate cache keys
            ttl: Time-to-live for cache entries in seconds. None means no expiration
            key: Optional static key for caching
        """
        self.key_patterns = key_patterns
        self.key_generator = key_generator
        self.key = key
        if not key and not key_patterns and not key_generator:
            raise ValueError(
                "Either key, key_patterns, or key_generator must be provided."
            )

    def __call__(
        self, func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        """
        Apply the cache invalidator to a function.

        Args:
            func: The function to be invalidated

        Returns:
            Wrapped function with cache invalidation behavior
        """

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate the cache key
            cache_keys: List[str] = []
            if self.key:
                cache_keys = [self.key]
            elif self.key_generator:
                cache_keys = [await self.key_generator(func.__name__, *args, **kwargs)]
            else:
                if not self.key_patterns:
                    raise ValueError(
                        "key_pattern must be provided if key_generator is not used."
                    )

                func_signature = inspect.signature(func)
                bound_args = func_signature.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Generate the cache key
                cache_keys = [
                    _pattern_to_key(pattern, arguments=bound_args.arguments)
                    for pattern in self.key_patterns
                ]

            logger.debug(f"Cache invalidation for keys: {cache_keys}")

            # Invalidate the cache
            await asyncio.gather(*[delete_cache(key) for key in cache_keys])

            return await func(*args, **kwargs)

        return wrapper


def _pattern_to_key(pattern: str, arguments: Dict[str, Any]) -> str:
    """
    Convert a pattern string to a cache key by replacing placeholders with actual values.

    Args:
        pattern: The pattern string with placeholders
        arguments: Keyword arguments to replace placeholders

    Returns:
        The generated cache key
    """
    try:
        return pattern.format(**arguments)
    except KeyError as e:
        raise ValueError(f"Missing key in pattern: {e}")
    except Exception as e:
        raise ValueError(f"Error generating key from pattern: {e}")
