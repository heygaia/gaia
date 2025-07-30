"""
Profiling decorators and middleware for performance monitoring.

This module provides decorators and middleware for profiling function execution and HTTP requests.
"""

import cProfile
import io
import pstats
import time
from functools import wraps
from typing import Any, Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config.loggers import profiler_logger as logger
from app.config.settings import settings
from app.utils.profiler_utils import profile_block


def profile_celery_task(print_lines=7):
    """Decorator to profile Celery tasks with configurable print stats."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()

            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()

                # Collect profiling stats
                s = io.StringIO()
                ps = pstats.Stats(profiler, stream=s).sort_stats(
                    pstats.SortKey.CUMULATIVE
                )
                ps.print_stats(print_lines)

            return result

        return wrapper

    return decorator


def profile_time(func_name: Optional[str] = None):
    """
    Decorator to profile function execution time.

    Args:
        func_name: Optional custom name for the function in logs
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            name = func_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Profile: {name} completed in {execution_time:.4f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Profile: {name} failed after {execution_time:.4f}s - {str(e)}"
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            name = func_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Profile: {name} completed in {execution_time:.4f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Profile: {name} failed after {execution_time:.4f}s - {str(e)}"
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class ProfilingMiddleware(BaseHTTPMiddleware):
    """Middleware to profile API request execution time."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only profile in development or when explicitly enabled
        if not settings.ENABLE_PROFILING:
            return await call_next(request)

        # Skip profiling for static assets, health checks, etc.
        path = request.url.path
        if path.startswith(("/static/", "/docs/", "/openapi.json")) or path in {
            "/health",
            "/ping",
            "/api/v1/ping",
            "/api/v1/",
            "/api/v1",
            "/api/v1/oauth/me",
            "/api/v1/conversations",
            "/",
        }:
            return await call_next(request)

        try:
            with profile_block(name=f"Request: {request.method} {path}"):
                response = await call_next(request)
            return response
        except Exception as e:
            # Ensure the application continues even if profiling fails
            logger.exception(f"Profiling error: {str(e)}")
            return await call_next(request)
