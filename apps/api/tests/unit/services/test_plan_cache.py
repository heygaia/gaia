"""The one place the cached plan tier is dropped, and its Dodo-id front door."""

from unittest.mock import AsyncMock, patch

from app.constants.cache import SUBSCRIPTION_PLAN_CACHE_PREFIX
from app.services.payments.payment_service import payment_service
from app.services.payments.plan_cache import invalidate_plan_cache


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
