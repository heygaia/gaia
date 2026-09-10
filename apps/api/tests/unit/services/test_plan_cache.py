"""The one place the cached plan tier is dropped, and its Dodo-id front door."""

from unittest.mock import AsyncMock, patch

from app.constants.cache import SUBSCRIPTION_PLAN_CACHE_PREFIX
from app.constants.log_tags import LogTag
from app.services.payments.payment_service import payment_service
from app.services.payments.plan_cache import invalidate_plan_cache
from tests.helpers import captured_wide_event


async def test_the_users_own_key_is_dropped() -> None:
    with patch(
        "app.services.payments.plan_cache.redis_cache.delete", new_callable=AsyncMock
    ) as drop:
        await invalidate_plan_cache("u1")

    drop.assert_awaited_once_with(f"{SUBSCRIPTION_PLAN_CACHE_PREFIX}u1")


async def test_a_dodo_subscription_id_resolves_to_its_owner_before_dropping() -> None:
    with (
        patch(
            "app.services.payments.payment_service.subscription_repository.get_user_id_by_dodo_id",
            new=AsyncMock(return_value="u1"),
        ),
        patch(
            "app.services.payments.payment_service.invalidate_plan_cache", new_callable=AsyncMock
        ) as drop,
    ):
        await payment_service.invalidate_plan_cache_by_dodo_id("sub_1")

    drop.assert_awaited_once_with("u1")


async def test_the_drop_is_recorded_on_the_event_against_the_user() -> None:
    """Every billing change ends here, and the paths that matter most — the
    webhooks — have no authenticated request for the middleware to attribute
    to. Without this the answer to "did the bust run for this user" is nowhere."""
    with patch("app.services.payments.plan_cache.redis_cache.delete", new_callable=AsyncMock):
        async with captured_wide_event() as event:
            await invalidate_plan_cache("u1")

    assert event["user"]["id"] == "u1"
    assert event["payment"]["plan_cache_dropped"] is True


async def test_a_dodo_id_with_no_local_subscription_says_so_instead_of_no_opping() -> None:
    """Nothing was dropped, so the owner keeps their pre-change tier until the
    TTL runs out. Silent, that reads downstream as the gate disagreeing with
    Dodo for no reason."""
    with (
        patch(
            "app.services.payments.payment_service.subscription_repository.get_user_id_by_dodo_id",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.services.payments.payment_service.invalidate_plan_cache", new_callable=AsyncMock
        ) as drop,
    ):
        async with captured_wide_event() as event:
            await payment_service.invalidate_plan_cache_by_dodo_id("sub_missing")

    drop.assert_not_awaited()
    assert event["warnings"] == [
        {
            "msg": f"{LogTag.PAYMENT} No local subscription for the Dodo id; "
            "cached tier not dropped",
            "failure_reason": "subscription_not_found",
            "subscription_id": "sub_missing",
        }
    ]
