"""
Decorators package for GAIA backend.

This package provides various decorators for common functionality:
- Documentation: with_doc
- Rate limiting: with_rate_limiting, tiered_rate_limit
- Integration checking: require_integration
- Caching: Cacheable, CacheInvalidator
- Profiling: profile_celery_task
"""

from .caching import Cacheable, CacheInvalidator
from .documentation import with_doc
from .integration import require_integration
from .profiling import profile_celery_task, profile_time, ProfilingMiddleware
from .logging import LoggingMiddleware
from .rate_limiting import (
    with_rate_limiting,
    tiered_rate_limit,
    LangChainRateLimitException,
    set_user_context,
    clear_user_context,
    get_current_rate_limit_info,
)

__all__ = [
    # Documentation
    "with_doc",
    # Rate limiting
    "with_rate_limiting",
    "tiered_rate_limit",
    "LangChainRateLimitException",
    "set_user_context",
    "clear_user_context",
    "get_current_rate_limit_info",
    # Integration
    "require_integration",
    # Caching
    "Cacheable",
    "CacheInvalidator",
    # Profiling
    "profile_celery_task",
    "profile_time",
    "ProfilingMiddleware",
    # Logging
    "LoggingMiddleware",
]
