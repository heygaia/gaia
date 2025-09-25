"""
Decorators package for GAIA backend.

This package provides various decorators for common functionality:
- Documentation: with_doc
- Rate limiting: with_rate_limiting, tiered_rate_limit
- Integration checking: require_integration
- Caching: Cacheable, CacheInvalidator
- Profiling: ProfilingMiddleware
"""

from .caching import Cacheable, CacheInvalidator
from .documentation import with_doc
from .integration import require_integration
from .profiling import ProfilingMiddleware
from .logging import LoggingMiddleware, log_function_call
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
    "ProfilingMiddleware",
    # Logging
    "LoggingMiddleware",
    "log_function_call",
]
