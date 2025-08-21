"""
Usage tracking API endpoints.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.dependencies.oauth_dependencies import get_current_user
from app.services.usage_service import UsageService
from app.services.token_service import token_service
from app.config.rate_limits import get_feature_info
from app.config.rate_limits import (
    FEATURE_LIMITS,
    get_limits_for_plan,
    get_reset_time,
    RateLimitPeriod,
)
from app.services.payment_service import payment_service
from app.models.payment_models import PlanType
from app.decorators.rate_limiting import tiered_limiter


router = APIRouter(prefix="/usage", tags=["usage"])
usage_service = UsageService()


@router.get("/summary")
async def get_usage_summary(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get real-time usage summary for the current user."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    # Get user subscription
    subscription = await payment_service.get_user_subscription_status(user_id)
    user_plan = subscription.plan_type or PlanType.FREE

    # Get real-time usage data directly from Redis
    features_formatted = await _get_realtime_usage(user_id, user_plan)
    token_summary = await token_service.get_token_usage_summary(user_id, user_plan)

    return {
        "user_id": user_id,
        "plan_type": user_plan.value if hasattr(user_plan, "value") else str(user_plan),
        "features": features_formatted,
        "token_usage": token_summary,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/history")
async def get_usage_history(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to retrieve"),
    feature_key: Optional[str] = Query(
        default=None, description="Specific feature to filter by"
    ),
    user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get usage history for the current user."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    # Validate feature_key if provided
    if feature_key and feature_key not in FEATURE_LIMITS:
        raise HTTPException(status_code=400, detail=f"Unknown feature: {feature_key}")

    history = await usage_service.get_usage_history(user_id, feature_key, days)

    formatted_history = []
    for snapshot in history:
        features_formatted: Dict[str, Dict[str, Any]] = {}
        for feature in snapshot.features:
            key = feature.feature_key
            if key not in features_formatted:
                feature_info = get_feature_info(key)
                features_formatted[key] = {
                    "title": feature_info["title"],
                    "periods": {},
                }

            features_formatted[key]["periods"][feature.period] = {
                "used": feature.used,
                "limit": feature.limit,
                "percentage": (
                    (feature.used / feature.limit * 100) if feature.limit > 0 else 0
                ),
            }

        formatted_history.append(
            {
                "date": snapshot.created_at.isoformat(),
                "plan_type": snapshot.plan_type,
                "features": features_formatted,
            }
        )

    return formatted_history


def _format_empty_features(user_plan: PlanType) -> Dict[str, Any]:
    """Format empty features with zero usage."""
    features_formatted: Dict[str, Dict[str, Any]] = {}

    for feature_key in FEATURE_LIMITS:
        feature_info = get_feature_info(feature_key)
        features_formatted[feature_key] = {
            "title": feature_info["title"],
            "description": feature_info["description"],
            "periods": {},
        }

        current_limits = get_limits_for_plan(feature_key, user_plan)

        for period in ["day", "month"]:
            limit = getattr(current_limits, period, 0)
            if limit > 0:
                reset_time = get_reset_time(getattr(RateLimitPeriod, period.upper()))
                features_formatted[feature_key]["periods"][period] = {
                    "used": 0,
                    "limit": limit,
                    "percentage": 0,
                    "reset_time": reset_time.isoformat(),
                    "remaining": limit,
                }

    return features_formatted


def _format_features_with_usage(snapshot, user_plan: PlanType) -> Dict[str, Any]:
    """Format features with actual usage data."""
    # Create mapping of actual usage data
    usage_data: Dict[str, Dict[str, Any]] = {}
    for feature in snapshot.features:
        if feature.feature_key not in usage_data:
            usage_data[feature.feature_key] = {}
        usage_data[feature.feature_key][feature.period] = {
            "used": feature.used,
            "limit": feature.limit,
            "percentage": (
                (feature.used / feature.limit * 100) if feature.limit > 0 else 0
            ),
            "reset_time": feature.reset_time.isoformat(),
            "remaining": max(0, feature.limit - feature.used),
        }

    # Format ALL configured features
    features_formatted: Dict[str, Dict[str, Any]] = {}
    for feature_key in FEATURE_LIMITS:
        feature_info = get_feature_info(feature_key)
        features_formatted[feature_key] = {
            "title": feature_info["title"],
            "description": feature_info["description"],
            "periods": {},
        }

        current_limits = get_limits_for_plan(feature_key, user_plan)

        for period in ["day", "month"]:
            limit = getattr(current_limits, period, 0)
            if limit > 0:
                if feature_key in usage_data and period in usage_data[feature_key]:
                    # Use actual usage data but with CURRENT limit configuration
                    stored_data = usage_data[feature_key][period]
                    features_formatted[feature_key]["periods"][period] = {
                        "used": stored_data["used"],
                        "limit": limit,  # Use current config limit, not stored limit
                        "percentage": (
                            (stored_data["used"] / limit * 100) if limit > 0 else 0
                        ),
                        "reset_time": stored_data["reset_time"],
                        "remaining": max(0, limit - stored_data["used"]),
                    }
                else:
                    # Show unused feature with zero usage
                    reset_time = get_reset_time(
                        getattr(RateLimitPeriod, period.upper())
                    )
                    features_formatted[feature_key]["periods"][period] = {
                        "used": 0,
                        "limit": limit,
                        "percentage": 0,
                        "reset_time": reset_time.isoformat(),
                        "remaining": limit,
                    }

    return features_formatted


async def _get_realtime_usage(user_id: str, user_plan: PlanType) -> Dict[str, Any]:
    """Get real-time usage data directly from Redis for all features."""
    features_formatted: Dict[str, Dict[str, Any]] = {}

    for feature_key in FEATURE_LIMITS:
        feature_info = get_feature_info(feature_key)
        features_formatted[feature_key] = {
            "title": feature_info["title"],
            "description": feature_info["description"],
            "periods": {},
        }

        current_limits = get_limits_for_plan(feature_key, user_plan)

        for period in ["day", "month"]:
            limit = getattr(current_limits, period, 0)
            if limit > 0:
                # Get real-time usage from Redis
                redis_key = tiered_limiter._get_redis_key(
                    user_id, feature_key, getattr(RateLimitPeriod, period.upper())
                )
                current_usage = await tiered_limiter.redis.get(redis_key)
                current_usage = int(current_usage) if current_usage else 0

                reset_time = get_reset_time(getattr(RateLimitPeriod, period.upper()))
                percentage = (current_usage / limit * 100) if limit > 0 else 0
                remaining = max(0, limit - current_usage)

                features_formatted[feature_key]["periods"][period] = {
                    "used": current_usage,
                    "limit": limit,
                    "percentage": percentage,
                    "reset_time": reset_time.isoformat(),
                    "remaining": remaining,
                }

    return features_formatted
