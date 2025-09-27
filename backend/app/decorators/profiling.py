"""
Universal profiling decorator for both async and sync functions using pyinstrument.

This module provides a single decorator that can profile both synchronous and
asynchronous functions with detailed call stack analysis. Profiling is completely
optional and must be explicitly enabled via environment variables.

Features:
- Works with both async and sync functions
- Environment-based configuration
- Optional profiling with sampling
- Detailed call stack analysis
- Configurable output formats
- Graceful fallback when pyinstrument is not available

Environment Variables:
    ENABLE_PROFILING: bool = False (must be explicitly enabled)
    PROFILING_SAMPLE_RATE: float = 1.0 (100% sampling rate)
    PROFILING_MAX_DEPTH: int = 20 (max call stack depth)
    PROFILING_ASYNC_MODE: str = "enabled" (enabled, disabled, strict)

Usage:
    @profile_function
    async def my_async_function():
        # Your async code here
        pass

    @profile_function
    def my_sync_function():
        # Your sync code here
        pass

    @profile_function(sample_rate=0.1)  # 10% sampling
    def expensive_function():
        # Your code here
        pass
"""

import functools
import inspect
import random
from typing import Any, Callable, Optional, Union

from pyinstrument import Profiler

from app.config.loggers import profiler_logger as logger
from app.config.settings import settings


def profile_function(
    func: Optional[Callable] = None,
    *,
    sample_rate: Optional[float] = None,
    max_depth: Optional[int] = None,
    async_mode: Optional[str] = None,
    output_format: str = "text",
    log_results: bool = True,
    **profiler_kwargs,
) -> Union[Callable, Any]:
    """
    Universal profiling decorator for both async and sync functions.

    Args:
        func: The function to profile (when used as decorator)
        sample_rate: Override global sampling rate (0.0 to 1.0)
        max_depth: Override global max call stack depth
        async_mode: Override global async mode setting
        output_format: Output format ("text", "html", "json")
        log_results: Whether to log profiling results
        **profiler_kwargs: Additional arguments passed to Profiler

    Returns:
        Decorated function or decorator function
    """

    def decorator(f: Callable) -> Callable:
        # Check if profiling is available and enabled
        if not settings.ENABLE_PROFILING:
            logger.debug(f"Profiling disabled for {f.__name__}")
            return f

        # Determine if function is async
        is_async = inspect.iscoroutinefunction(f)

        # Get configuration
        effective_sample_rate = (
            sample_rate if sample_rate is not None else settings.PROFILING_SAMPLE_RATE
        )
        effective_max_depth = (
            max_depth if max_depth is not None else settings.PROFILING_MAX_DEPTH
        )

        # Apply sampling
        if effective_sample_rate < 1.0 and random.random() >= effective_sample_rate:
            logger.debug(f"Profiling skipped for {f.__name__} due to sampling")
            return f

        if is_async:

            @functools.wraps(f)
            async def async_wrapper(*args, **kwargs):
                profiler = Profiler(**profiler_kwargs)

                try:
                    profiler.start()
                    result = await f(*args, **kwargs)
                    profiler.stop()

                    if log_results:
                        _log_profiling_results(f.__name__, profiler, output_format)

                    return result

                except Exception as e:
                    profiler.stop()
                    logger.exception(
                        f"Profiling error in async function {f.__name__}: {str(e)}"
                    )
                    raise

            return async_wrapper
        else:

            @functools.wraps(f)
            def sync_wrapper(*args, **kwargs):
                profiler = Profiler(**profiler_kwargs)

                try:
                    profiler.start()
                    result = f(*args, **kwargs)
                    profiler.stop()

                    if log_results:
                        _log_profiling_results(f.__name__, profiler, output_format)

                    return result

                except Exception as e:
                    profiler.stop()
                    logger.exception(
                        f"Profiling error in sync function {f.__name__}: {str(e)}"
                    )
                    raise

            return sync_wrapper

    # Handle both @profile_function and @profile_function() usage
    if func is None:
        return decorator
    else:
        return decorator(func)


def _log_profiling_results(
    func_name: str, profiler: Profiler, output_format: str
) -> None:
    """
    Log profiling results in the specified format.

    Args:
        func_name: Name of the profiled function
        profiler: PyInstrument profiler instance
        output_format: Desired output format
    """
    try:
        if output_format == "html":
            output = profiler.output_html()
            logger.info(f"Profiling HTML report for {func_name}:\n{output}")
        elif output_format == "json":
            output = profiler.output_json()
            logger.info(f"Profiling JSON report for {func_name}:\n{output}")
        else:  # text format
            output = profiler.output_text()
            logger.info(f"Profiling results for {func_name}:\n{output}")
    except Exception as e:
        logger.warning(f"Could not generate profiling output for {func_name}: {e}")


def profile_class_methods(
    sample_rate: Optional[float] = None,
    max_depth: Optional[int] = None,
    async_mode: Optional[str] = None,
    output_format: str = "text",
    log_results: bool = True,
    **profiler_kwargs,
):
    """
    Class decorator to profile all methods of a class.

    Args:
        sample_rate: Override global sampling rate
        max_depth: Override global max call stack depth
        async_mode: Override global async mode setting
        output_format: Output format for results
        log_results: Whether to log profiling results
        **profiler_kwargs: Additional profiler arguments

    Usage:
        @profile_class_methods(sample_rate=0.1)
        class MyClass:
            def method1(self):
                pass

            async def method2(self):
                pass
    """

    def decorator(cls):
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if callable(attr) and not attr_name.startswith("_"):
                setattr(
                    cls,
                    attr_name,
                    profile_function(
                        attr,
                        sample_rate=sample_rate,
                        max_depth=max_depth,
                        async_mode=async_mode,
                        output_format=output_format,
                        log_results=log_results,
                        **profiler_kwargs,
                    ),
                )
        return cls

    return decorator


# Convenience decorators for common use cases
def profile_sync(sample_rate: Optional[float] = None, **kwargs):
    """Decorator specifically for synchronous functions."""
    return profile_function(sample_rate=sample_rate, **kwargs)


def profile_async(sample_rate: Optional[float] = None, **kwargs):
    """Decorator specifically for asynchronous functions."""
    return profile_function(sample_rate=sample_rate, **kwargs)


def profile_heavy_operations(sample_rate: float = 0.1, **kwargs):
    """Decorator for heavy operations with low sampling rate."""
    return profile_function(sample_rate=sample_rate, **kwargs)


def profile_critical_path(sample_rate: float = 1.0, **kwargs):
    """Decorator for critical path functions with full sampling."""
    return profile_function(sample_rate=sample_rate, **kwargs)
