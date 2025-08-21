"""
Tiered rate limiting middleware for API endpoints.

Enforces daily and monthly rate limits based on user subscription plans.
Automatically checks both time periods and rejects requests that exceed any limit.

Usage:
    @tiered_rate_limit("file_analysis", count_tokens=True)
    async def analyze_file(user: dict = Depends(get_current_user)):
        # Also validates token usage limits per request
        return await analyze()
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Callable, Optional
from functools import wraps

import redis.asyncio as redis
from fastapi import HTTPException
from pydantic import BaseModel

from app.db.redis import redis_cache
from app.models.payment_models import PlanType
from app.services.payment_service import payment_service
from app.config.rate_limits import (
    RateLimitPeriod,
    get_limits_for_plan,
    get_reset_time,
    get_time_window_key,
    get_feature_info,
    FEATURE_LIMITS,
)
from app.models.usage_models import UserUsageSnapshot, FeatureUsage, UsagePeriod
from app.db.mongodb.collections import usage_snapshots_collection


class UsageInfo(BaseModel):
    used: int
    limit: int
    reset_time: datetime


class RateLimitExceededException(HTTPException):
    def __init__(
        self,
        feature: str,
        plan_required: Optional[str] = None,
        reset_time: Optional[datetime] = None,
    ):
        detail = {
            "error": "rate_limit_exceeded",
            "feature": feature,
            "message": f"Rate limit exceeded for {feature}",
        }
        if plan_required:
            detail["plan_required"] = plan_required
            detail["message"] = (
                f"{feature} is not available in your current plan. Upgrade to {plan_required.upper()} to access this feature."
            )
        if reset_time:
            detail["reset_time"] = reset_time.isoformat()

        super().__init__(status_code=429, detail=detail)


class TieredRateLimiter:
    def __init__(self):
        self.redis = redis_cache

    def _get_redis_key(
        self, user_id: str, feature: str, period: RateLimitPeriod
    ) -> str:
        time_window = get_time_window_key(period)
        return f"rate_limit:{user_id}:{feature}:{period}:{time_window}"

    def _get_ttl(self, period: RateLimitPeriod) -> int:
        reset_time = get_reset_time(period)
        return int((reset_time - datetime.now(timezone.utc)).total_seconds())

    async def check_and_increment(
        self, user_id: str, feature_key: str, user_plan: PlanType, tokens_used: int = 0
    ) -> Dict[str, UsageInfo]:
        current_limits = get_limits_for_plan(feature_key, user_plan)
        usage_info = {}

        for period in [RateLimitPeriod.DAY, RateLimitPeriod.MONTH]:
            limit = getattr(current_limits, period.value)
            if limit <= 0:
                continue

            redis_key = self._get_redis_key(user_id, feature_key, period)
            current_usage = await self.redis.get(redis_key)
            current_usage = int(current_usage) if current_usage else 0
            reset_time = get_reset_time(period)

            usage_info[period.value] = UsageInfo(
                used=current_usage, limit=limit, reset_time=reset_time
            )

            if current_usage >= limit:
                plan_required = "pro" if user_plan == PlanType.FREE else None
                raise RateLimitExceededException(feature_key, plan_required, reset_time)

        # Token usage check
        if tokens_used > 0:
            token_limit = current_limits.tokens_per_request
            if token_limit > 0 and tokens_used > token_limit:
                plan_required = "pro" if user_plan == PlanType.FREE else None
                raise RateLimitExceededException(
                    f"{feature_key} (token limit)", plan_required, None
                )

        # Increment usage atomically
        for period in [RateLimitPeriod.DAY, RateLimitPeriod.MONTH]:
            limit = getattr(current_limits, period.value)
            if limit <= 0:
                continue

            redis_key = self._get_redis_key(user_id, feature_key, period)
            ttl = self._get_ttl(period)

            # Use Redis pipeline with WATCH for atomic check-and-increment
            async with self.redis.redis.pipeline() as pipe:
                while True:
                    try:
                        # Watch the key for changes
                        await pipe.watch(redis_key)

                        # Get current value
                        current_val = await self.redis.get(redis_key)
                        current_val = int(current_val) if current_val else 0

                        # Double-check limit hasn't been exceeded by concurrent requests
                        if current_val >= limit:
                            await pipe.unwatch()
                            plan_required = (
                                "pro" if user_plan == PlanType.FREE else None
                            )
                            raise RateLimitExceededException(
                                feature_key, plan_required, get_reset_time(period)
                            )

                        # Execute atomic increment
                        pipe.multi()
                        await pipe.incr(redis_key)
                        await pipe.expire(redis_key, ttl)
                        await pipe.execute()
                        break  # Success, exit retry loop

                    except redis.WatchError:
                        # Key was modified, retry the transaction
                        continue

        # Real-time usage sync after rate limit usage
        asyncio.create_task(self._sync_usage_real_time(user_id, feature_key, user_plan))

        return usage_info

    async def get_usage_info(
        self, user_id: str, feature_key: str, user_plan: PlanType
    ) -> Dict[str, UsageInfo]:
        current_limits = get_limits_for_plan(feature_key, user_plan)
        usage_info = {}

        for period in [RateLimitPeriod.DAY, RateLimitPeriod.MONTH]:
            limit = getattr(current_limits, period.value)
            if limit <= 0:
                continue

            redis_key = self._get_redis_key(user_id, feature_key, period)
            current_usage = await self.redis.get(redis_key)
            current_usage = int(current_usage) if current_usage else 0
            reset_time = get_reset_time(period)

            usage_info[period.value] = UsageInfo(
                used=current_usage, limit=limit, reset_time=reset_time
            )

        return usage_info

    async def _sync_usage_real_time(
        self, user_id: str, feature_key: str, user_plan: PlanType
    ) -> None:
        """
        Sync usage data to database in real-time after rate limit usage.
        Runs asynchronously to avoid blocking the main request.
        Creates comprehensive snapshot with ALL features that have usage data.
        """
        try:
            # Get current usage for ALL features that have been used
            all_feature_usage = []

            # Iterate through all possible features to build comprehensive snapshot
            for check_feature_key in FEATURE_LIMITS:
                current_limits = get_limits_for_plan(check_feature_key, user_plan)
                feature_has_usage = False
                feature_usage_list = []

                for period in [RateLimitPeriod.DAY, RateLimitPeriod.MONTH]:
                    limit = getattr(current_limits, period.value)
                    if limit <= 0:
                        continue

                    redis_key = self._get_redis_key(user_id, check_feature_key, period)
                    current_usage = await self.redis.get(redis_key)
                    current_usage = int(current_usage) if current_usage else 0

                    # Only include features that have been used (current_usage > 0)
                    if current_usage > 0:
                        feature_has_usage = True
                        reset_time = get_reset_time(period)

                        feature_info = get_feature_info(check_feature_key)
                        feature_usage = FeatureUsage(
                            feature_key=check_feature_key,
                            feature_title=feature_info["title"],
                            period=UsagePeriod(period.value),
                            used=current_usage,
                            limit=limit,
                            reset_time=reset_time,
                        )
                        feature_usage_list.append(feature_usage)

                # Add this feature's usage if it has any
                if feature_has_usage:
                    all_feature_usage.extend(feature_usage_list)

            if all_feature_usage:
                # Create and save comprehensive usage snapshot
                snapshot = UserUsageSnapshot(
                    user_id=user_id,
                    plan_type=(
                        user_plan.value
                        if hasattr(user_plan, "value")
                        else str(user_plan)
                    ),
                    features=all_feature_usage,
                )

                snapshot_dict = snapshot.model_dump()
                await usage_snapshots_collection.insert_one(snapshot_dict)

        except Exception as e:
            # Log error but don't raise - this shouldn't break the main request
            from app.config.loggers import app_logger

            app_logger.error(
                f"Real-time usage sync failed for user {user_id}, feature {feature_key}: {str(e)}"
            )


# Global rate limiter instance
tiered_limiter = TieredRateLimiter()


def tiered_rate_limit(feature_key: str, count_tokens: bool = False):
    """Rate limiting decorator for API endpoints."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user from dependencies
            user = None

            for arg in args:
                if isinstance(arg, dict) and "user_id" in arg:
                    user = arg

            if not user:
                user = kwargs.get("user")
                if not user:
                    # If no user found, skip rate limiting (for public endpoints)
                    return await func(*args, **kwargs)

            user_id = user.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found")

            # Get user subscription
            subscription = await payment_service.get_user_subscription_status(user_id)
            user_plan = subscription.plan_type or PlanType.FREE

            # Check rate limits before executing function
            await tiered_limiter.check_and_increment(
                user_id=user_id,
                feature_key=feature_key,
                user_plan=user_plan,
                tokens_used=0,  # Will be handled post-execution if count_tokens=True
            )

            # Execute the original function
            result = await func(*args, **kwargs)

            # Handle token counting post-execution
            if count_tokens and isinstance(result, dict):
                tokens_used = result.get("tokens_used", 0)
                if tokens_used > 0:
                    # Validate token limits
                    current_limits = get_limits_for_plan(feature_key, user_plan)
                    if (
                        current_limits.tokens_per_request > 0
                        and tokens_used > current_limits.tokens_per_request
                    ):
                        plan_required = "pro" if user_plan == PlanType.FREE else None
                        raise RateLimitExceededException(
                            f"{feature_key} (token limit)", plan_required
                        )

            return result

        # Store metadata for usage tracking
        setattr(wrapper, "_rate_limit_metadata", {"feature_key": feature_key})

        return wrapper

    return decorator
