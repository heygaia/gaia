"""
Rate limiting configuration for all features.
Single source of truth for rate limits.

Rate limits are enforced across two time periods:
- Daily: Medium-term usage control
- Monthly: Long-term subscription limits

Both limits are checked on each request. If any limit is exceeded,
the request is rejected with a 429 status code.

Usage:
    @tiered_rate_limit("generate_image")
    async def generate_image(user: dict = Depends(get_current_user)):
        # This endpoint will be limited by daily (50/1000) and monthly (1000/25000)
        # limits based on user's plan
        pass
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict

from app.models.payment_models import PlanType
from pydantic import BaseModel


class RateLimitPeriod(str, Enum):
    DAY = "day"
    MONTH = "month"


class RateLimitConfig(BaseModel):
    day: int = 0
    month: int = 0
    tokens_per_request: int = 0


class FeatureInfo(BaseModel):
    title: str
    description: str


class TieredRateLimits(BaseModel):
    free: RateLimitConfig = RateLimitConfig()
    pro: RateLimitConfig = RateLimitConfig()
    info: FeatureInfo


# All feature rate limits in one place
FEATURE_LIMITS: Dict[str, TieredRateLimits] = {
    "file_upload": TieredRateLimits(
        free=RateLimitConfig(day=5, month=20),
        pro=RateLimitConfig(day=500, month=10000),
        info=FeatureInfo(title="File Upload", description="Upload and process files"),
    ),
    "calendar_management": TieredRateLimits(
        free=RateLimitConfig(day=3, month=10),
        pro=RateLimitConfig(day=1000, month=25000),
        info=FeatureInfo(
            title="Calendar Management",
            description="Create, update, and manage calendar events",
        ),
    ),
    "mail_actions": TieredRateLimits(
        free=RateLimitConfig(day=3, month=10),
        pro=RateLimitConfig(day=500, month=12000),
        info=FeatureInfo(
            title="Mail Actions", description="Send emails and manage mail operations"
        ),
    ),
    "generate_image": TieredRateLimits(
        free=RateLimitConfig(day=2, month=5),
        pro=RateLimitConfig(day=200, month=5000),
        info=FeatureInfo(
            title="AI Image Generation", description="Generate images using AI models"
        ),
    ),
    "goal_tracking": TieredRateLimits(
        free=RateLimitConfig(day=1, month=3),
        pro=RateLimitConfig(day=100, month=2500),
        info=FeatureInfo(
            title="Goal Tracking", description="Create and track personal goals"
        ),
    ),
    "deep_research": TieredRateLimits(
        free=RateLimitConfig(day=1, month=3),
        pro=RateLimitConfig(day=50, month=1200),
        info=FeatureInfo(
            title="Deep Research", description="Perform comprehensive research analysis"
        ),
    ),
    "todo_operations": TieredRateLimits(
        free=RateLimitConfig(day=50, month=500),
        pro=RateLimitConfig(day=1000, month=25000),
        info=FeatureInfo(
            title="Todo Operations", description="Create, update, and manage todo items"
        ),
    ),
    "workflow_operations": TieredRateLimits(
        free=RateLimitConfig(day=1, month=30),
        pro=RateLimitConfig(day=200, month=2000),
        info=FeatureInfo(
            title="Workflow Operations",
            description="Create, execute, and manage AI workflows",
        ),
    ),
    "web_search": TieredRateLimits(
        free=RateLimitConfig(day=50, month=500),
        pro=RateLimitConfig(day=1000, month=25000),
        info=FeatureInfo(
            title="Web Search", description="Search the web for information"
        ),
    ),
    "reminder_operations": TieredRateLimits(
        free=RateLimitConfig(day=5, month=30),
        pro=RateLimitConfig(day=200, month=5000),
        info=FeatureInfo(
            title="Reminder Operations", description="Create and manage reminders"
        ),
    ),
    "weather_checks": TieredRateLimits(
        free=RateLimitConfig(day=10, month=100),
        pro=RateLimitConfig(day=500, month=10000),
        info=FeatureInfo(
            title="Weather Checks", description="Check weather information"
        ),
    ),
    "webpage_fetch": TieredRateLimits(
        free=RateLimitConfig(day=5, month=50),
        pro=RateLimitConfig(day=200, month=5000),
        info=FeatureInfo(
            title="Webpage Fetch", description="Fetch and analyze web pages"
        ),
    ),
    "document_generation": TieredRateLimits(
        free=RateLimitConfig(day=2, month=10),
        pro=RateLimitConfig(day=100, month=2500),
        info=FeatureInfo(
            title="Document Generation", description="Generate documents and reports"
        ),
    ),
    "flowchart_creation": TieredRateLimits(
        free=RateLimitConfig(day=2, month=10),
        pro=RateLimitConfig(day=50, month=1000),
        info=FeatureInfo(
            title="Flowchart Creation", description="Create flowcharts and diagrams"
        ),
    ),
    "code_execution": TieredRateLimits(
        free=RateLimitConfig(day=5, month=50),
        pro=RateLimitConfig(day=200, month=5000),
        info=FeatureInfo(title="Code Execution", description="Execute code snippets"),
    ),
    "google_docs_operations": TieredRateLimits(
        free=RateLimitConfig(day=3, month=20),
        pro=RateLimitConfig(day=100, month=2500),
        info=FeatureInfo(
            title="Google Docs Operations", description="Create and manage Google Docs"
        ),
    ),
    "file_analysis": TieredRateLimits(
        free=RateLimitConfig(day=10, month=50),
        pro=RateLimitConfig(day=500, month=10000),
        info=FeatureInfo(
            title="File Analysis", description="Analyze and process uploaded files"
        ),
    ),
    "memory": TieredRateLimits(
        free=RateLimitConfig(day=50, month=500),
        pro=RateLimitConfig(day=1000, month=25000),
        info=FeatureInfo(
            title="Memory Operations", description="Store and retrieve memories"
        ),
    ),
    "notes": TieredRateLimits(
        free=RateLimitConfig(day=100, month=1000),
        pro=RateLimitConfig(day=2000, month=50000),
        info=FeatureInfo(
            title="Notes Management", description="Create and manage notes"
        ),
    ),
    "chat_messages": TieredRateLimits(
        free=RateLimitConfig(day=200, month=5000),
        pro=RateLimitConfig(day=5000, month=125000),
        info=FeatureInfo(
            title="Chat Messages", description="Send messages to AI assistants"
        ),
    ),
}


def get_feature_limits(feature_key: str) -> TieredRateLimits:
    """Get rate limits for a specific feature."""
    if feature_key not in FEATURE_LIMITS:
        raise ValueError(f"Unknown feature key: {feature_key}")
    return FEATURE_LIMITS[feature_key]


def get_limits_for_plan(feature_key: str, plan_type: PlanType) -> RateLimitConfig:
    """Get rate limits for a specific feature and plan."""
    limits = get_feature_limits(feature_key)
    return limits.free if plan_type == PlanType.FREE else limits.pro


def get_reset_time(period: RateLimitPeriod) -> datetime:
    """Calculate reset time for a given period."""
    now = datetime.now(timezone.utc)
    if period == RateLimitPeriod.DAY:
        return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=1
        )
    else:  # MONTH
        if now.month == 12:
            return now.replace(
                year=now.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            return now.replace(
                month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0
            )


def get_time_window_key(period: RateLimitPeriod) -> str:
    """Get Redis time window key for a period."""
    now = datetime.now(timezone.utc)
    if period == RateLimitPeriod.DAY:
        return now.strftime("%Y%m%d")
    else:  # MONTH
        return now.strftime("%Y%m")


def get_feature_info(feature_key: str) -> Dict[str, str]:
    """Get user-friendly feature information."""
    if feature_key in FEATURE_LIMITS:
        info = FEATURE_LIMITS[feature_key].info
        return {"title": info.title, "description": info.description}
    return {
        "title": feature_key.replace("_", " ").title(),
        "description": f"Usage for {feature_key}",
    }


def list_all_features() -> list[str]:
    """Get a list of all available feature keys."""
    return list(FEATURE_LIMITS.keys())
