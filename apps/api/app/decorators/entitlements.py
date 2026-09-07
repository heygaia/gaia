"""Paywall gate: blocks non-PRO users from spend-incurring endpoints.

Distinct from ``app.decorators.rate_limiting`` — that caps HOW MUCH a plan may
use; this blocks access outright for a plan with none at all. Mirrors the
``tiered_rate_limit`` decorator / ``enforce_tiered_limit`` imperative-helper
split so callers that resolve their own user (bots) can still gate.
"""

from typing import ParamSpec, TypedDict, TypeVar

from fastapi import HTTPException

from app.config.settings import settings
from app.models.payment_models import PlanType
from app.services.analytics_service import AnalyticsEvents, capture_event
from app.services.payments.payment_service import payment_service
from app.services.payments.plan_cache import invalidate_plan_cache
from shared.py.wide_events import log

P = ParamSpec("P")
R = TypeVar("R")

PAYWALL_MESSAGE = "GAIA is paid only. Subscribe to GAIA Pro to keep chatting."


class SubscriptionRequiredDetail(TypedDict):
    """The 402 body the web app and bots parse. Changing a key breaks them."""

    code: str
    message: str
    checkout_url: str | None
    discount_code: str | None


class SubscriptionRequiredException(HTTPException):
    """402 raised when a non-PRO user hits a paid-only surface.

    Wire contract is fixed (the frontend is built against it): ``detail`` is
    ``{code, message, checkout_url, discount_code}``. No dedicated exception
    handler is registered for this — like ``RateLimitExceededException``, it
    rides the app's generic ``StarletteHTTPException`` handler, which emits
    ``{"detail": exc.detail}`` unchanged.
    """

    def __init__(self, checkout_url: str | None) -> None:
        detail: SubscriptionRequiredDetail = {
            "code": "subscription_required",
            "message": PAYWALL_MESSAGE,
            "checkout_url": checkout_url,
            "discount_code": settings.PAYWALL_DISCOUNT_CODE,
        }
        super().__init__(status_code=402, detail=detail)


async def is_subscription_active(user_id: str) -> bool:
    """Whether ``user_id`` currently has paid chat access."""
    plan = await payment_service.get_cached_plan_type(user_id)
    return plan == PlanType.PRO


async def confirm_subscription_active(user_id: str) -> bool:
    """A fresh read of the subscription, for a decision the cache must not make.

    The cached tier lags a payment by up to its TTL. Refusing one request on a
    stale FREE is fine; skipping a scheduled workflow run on it is not, so the
    worker asks the database once before it skips. A live subscription found
    here also drops the stale key, so the next gate read is right.
    """
    status = await payment_service.get_user_subscription_status(user_id)
    if status.plan_type == PlanType.PRO:
        await invalidate_plan_cache(user_id)
        return True
    return False


async def get_checkout_url(user_id: str) -> str | None:
    """A personal Dodo checkout link for ``user_id``, or ``None`` if Dodo is unreachable.

    A paywall response must never itself fail because the checkout provider
    is down — the block still stands, just without a one-tap link.
    """
    try:
        pro = await payment_service.create_pro_checkout(user_id)
    except Exception as e:
        log.warning(
            "Could not mint checkout link for paywall response",
            user={"id": user_id},
            payment={"operation": "paywall_checkout_link"},
            error_type=type(e).__name__,
        )
        return None
    return pro.checkout.payment_link


async def require_active_subscription(user_id: str, feature: str) -> None:
    """Raise ``SubscriptionRequiredException`` unless ``user_id`` is on PRO.

    ``feature`` names the surface that turned the caller away; it is required
    so every block is attributable in the funnel rather than anonymous.
    """
    if await is_subscription_active(user_id):
        return
    checkout_url = await get_checkout_url(user_id)
    log.warning(
        "Subscription required, blocking request",
        user={"id": user_id},
        payment={"operation": "paywall_gate", "feature": feature},
    )
    # capture_event, not capture_context_event: bot routes and worker paths
    # reach this with no authenticated request context to attribute to, and an
    # anonymous paywall block never joins the user's funnel.
    capture_event(
        user_id,
        AnalyticsEvents.PAYWALL_BLOCKED,
        {"feature": feature, "has_checkout_url": checkout_url is not None},
    )
    raise SubscriptionRequiredException(checkout_url=checkout_url)
