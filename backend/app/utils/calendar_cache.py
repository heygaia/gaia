"""
Simple calendar caching utilities for improved performance.
"""

from typing import Any, Dict, Optional

from app.config.loggers import calendar_logger as logger
from app.db.redis import get_cache, set_cache, delete_cache_by_pattern


class CalendarCache:
    """Simple calendar caching implementation using Redis."""

    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.default_ttl = default_ttl

    def _make_key(self, key_type: str, user_id: str, **kwargs) -> str:
        """Generate cache key with consistent format."""
        base_key = f"calendar:{key_type}:{user_id}"
        if kwargs:
            suffix = ":".join([f"{k}={v}" for k, v in sorted(kwargs.items())])
            return f"{base_key}:{suffix}"
        return base_key

    async def get_events(
        self,
        user_id: str,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get cached calendar events."""
        try:
            key = self._make_key(
                "events",
                user_id,
                calendar_id=calendar_id,
                time_min=time_min or "",
                time_max=time_max or "",
            )

            cached_data = await get_cache(key)
            if cached_data:
                logger.info(f"Cache hit for events: {key}")
                return cached_data

            logger.debug(f"Cache miss for events: {key}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving cached events: {e}")
            return None

    async def set_events(
        self,
        user_id: str,
        events_data: Dict[str, Any],
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache calendar events."""
        try:
            key = self._make_key(
                "events",
                user_id,
                calendar_id=calendar_id,
                time_min=time_min or "",
                time_max=time_max or "",
            )

            cache_ttl = ttl or self.default_ttl
            await set_cache(key, events_data, cache_ttl)

            logger.info(f"Cached events for {cache_ttl}s: {key}")

        except Exception as e:
            logger.error(f"Error caching events: {e}")

    async def get_calendars(self, user_id: str) -> Optional[list]:
        """Get cached calendar list."""
        try:
            key = self._make_key("calendars", user_id)
            cached_data = await get_cache(key)

            if cached_data:
                logger.info(f"Cache hit for calendars: {key}")
                return cached_data

            logger.debug(f"Cache miss for calendars: {key}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving cached calendars: {e}")
            return None

    async def set_calendars(
        self, user_id: str, calendars_data: list, ttl: Optional[int] = None
    ) -> None:
        """Cache calendar list."""
        try:
            key = self._make_key("calendars", user_id)
            cache_ttl = ttl or (self.default_ttl * 12)  # Longer TTL for calendar list

            await set_cache(key, calendars_data, cache_ttl)
            logger.info(f"Cached calendars for {cache_ttl}s: {key}")

        except Exception as e:
            logger.error(f"Error caching calendars: {e}")

    async def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate all cache entries for a user."""
        try:
            pattern = f"calendar:*:{user_id}*"
            await delete_cache_by_pattern(pattern)
            logger.info(f"Invalidated cache entries for user {user_id}")

        except Exception as e:
            logger.error(f"Error invalidating user cache: {e}")

    async def invalidate_events_cache(
        self, user_id: str, calendar_id: Optional[str] = None
    ) -> None:
        """Invalidate events cache for user/calendar."""
        try:
            if calendar_id:
                pattern = f"calendar:events:{user_id}:calendar_id={calendar_id}*"
            else:
                pattern = f"calendar:events:{user_id}*"

            await delete_cache_by_pattern(pattern)
            logger.info("Invalidated events cache entries")

        except Exception as e:
            logger.error(f"Error invalidating events cache: {e}")


# Global cache instance
calendar_cache = CalendarCache()
