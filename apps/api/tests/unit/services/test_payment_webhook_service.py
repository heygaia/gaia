"""The billing-webhook <-> workflow-pause integration in ``PaymentWebhookService``.

subscription.active / subscription.renewed reactivate paused workflows;
subscription.failed / subscription.on_hold deactivate them. Workflows
deactivated with DeactivationReason.SUBSCRIPTION_LAPSED (cancel, expire,
payment failure, on-hold) were never turned back on when the user
resubscribed — nothing called ``reactivate_workflows_for_restored_subscription``
from the billing webhook path. See ``app/services/workflow/subscription_pause.py``.
"""

from datetime import timedelta
from typing import get_args
from unittest.mock import AsyncMock, MagicMock, patch

from dodopayments.types import WebhookEventType
import pytest

from app.constants.log_tags import LogTag
from app.models.payment_models import ProcessedWebhookUpdate
from app.models.webhook_models import (
    DodoBillingData,
    DodoCustomerData,
    DodoSubscriptionData,
    DodoWebhookEvent,
    DodoWebhookEventType,
    DodoWebhookProcessingResult,
)
from app.services.analytics_service import AnalyticsEvents, SubscriptionPlan
from app.services.payments.payment_webhook_service import PaymentWebhookService
from app.services.payments.subscription_activation import (
    SubscriptionActivation,
    activate_subscription,
    reactivate_workflows_safely,
    resolve_subscription_owner,
    send_welcome_email_safely,
)
from tests.helpers import captured_wide_event
from tests.unit.services.conftest import (
    FAKE_EMAIL,
    FAKE_USER_ID,
    PAYMENT_DATA_PAYLOAD,
    SAMPLE_SUBSCRIPTION,
    SAMPLE_USER_DOC,
    SUBSCRIPTION_DATA_PAYLOAD,
    _make_webhook_event,
    _set_user,
)

MODULE = "app.services.payments.payment_webhook_service"
ACTIVATION = "app.services.payments.subscription_activation"
# `subscription_activation` imports this lazily (it would otherwise pull the
# workflow stack into `app.decorators`' import graph), so it is only ever
# patchable at its source module.
PAUSE = "app.services.workflow.subscription_pause"

USER_ID = "507f1f77bcf86cd799439011"

# The two module-scoped seams every moved PaymentWebhookService test relied on
# as an autouse fixture in the old file — opted in here rather than made
# autouse in the shared conftest, which every other unit/services test file
# also uses.
pytestmark = pytest.mark.usefixtures(
    "mock_activation_workflow_reactivation", "mock_payment_service_invalidation"
)


def _billing() -> DodoBillingData:
    return DodoBillingData(city="SF", country="US", state="CA", street="1 Main St", zipcode="94105")


def _customer() -> DodoCustomerData:
    return DodoCustomerData(customer_id="cus_1", email="user@example.com", name="Test User")


def _subscription_data(**overrides: object) -> DodoSubscriptionData:
    base: dict = {
        "subscription_id": "sub_123",
        "product_id": "prod_pro",
        "customer": _customer(),
        "billing": _billing(),
        "status": "active",
        "currency": "usd",
        "quantity": 1,
        "recurring_pre_tax_amount": 2000,
        "payment_frequency_count": 1,
        "payment_frequency_interval": "Month",
        "subscription_period_count": 1,
        "subscription_period_interval": "Month",
        "created_at": "2026-01-01T00:00:00Z",
        "metadata": {"user_id": USER_ID},
    }
    base.update(overrides)
    return DodoSubscriptionData(**base)


def _event(event_type: DodoWebhookEventType, **overrides: object) -> DodoWebhookEvent:
    return DodoWebhookEvent(
        business_id="biz_1",
        type=event_type,
        timestamp="2026-01-01T00:00:00Z",
        data=_subscription_data(**overrides).model_dump(),
    )


@pytest.mark.unit
class TestSubscriptionActiveReactivatesWorkflows:
    async def test_activation_drops_the_cached_plan_tier_on_both_branches(self) -> None:
        """The gate caches the plan for five minutes. A user who just paid must
        not be told to pay again until it expires, whichever branch the
        activation takes: a fresh row, or a row a recovery path created moments
        earlier while the cache still said FREE."""
        service = PaymentWebhookService()
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(f"{ACTIVATION}.invalidate_plan_cache", new_callable=AsyncMock) as invalidate,
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription", new_callable=AsyncMock
            ),
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=MagicMock(user_id=USER_ID))
            await service._handle_subscription_active(
                _event(DodoWebhookEventType.SUBSCRIPTION_ACTIVE)
            )
        invalidate.assert_awaited_once_with(USER_ID)

        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(f"{ACTIVATION}.user_repository") as user_repo,
            patch(f"{ACTIVATION}.invalidate_plan_cache", new_callable=AsyncMock) as invalidate,
            patch(f"{ACTIVATION}.track_subscription_event"),
            patch(f"{ACTIVATION}.send_welcome_email_safely", new_callable=AsyncMock),
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription", new_callable=AsyncMock
            ),
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=None)
            sub_repo.create = AsyncMock()
            user_repo.get_by_email = AsyncMock(return_value=MagicMock(id=USER_ID))
            await service._handle_subscription_active(
                _event(DodoWebhookEventType.SUBSCRIPTION_ACTIVE)
            )
        invalidate.assert_awaited_once_with(USER_ID)

    async def test_existing_subscription_reactivates_paused_workflows(self) -> None:
        """The common resubscribe path: Dodo re-fires `subscription.active` for a
        subscription row that already exists (early-return branch)."""
        service = PaymentWebhookService()
        existing = MagicMock(user_id=USER_ID)
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription",
                new_callable=AsyncMock,
            ) as reactivate,
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=existing)
            result = await service._handle_subscription_active(
                _event(DodoWebhookEventType.SUBSCRIPTION_ACTIVE)
            )

        assert result.status == "processed"
        # The message is the only thing distinguishing a redelivery from a real
        # activation in Dodo's dashboard and in our own webhook log.
        assert result.message == "Subscription already active"
        reactivate.assert_awaited_once_with(USER_ID)

    async def test_newly_created_subscription_reactivates_paused_workflows(self) -> None:
        service = PaymentWebhookService()
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription",
                new_callable=AsyncMock,
            ) as reactivate,
            patch(f"{ACTIVATION}.track_subscription_event"),
            patch(f"{ACTIVATION}.send_welcome_email_safely", new_callable=AsyncMock),
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=None)
            sub_repo.create = AsyncMock()
            result = await service._handle_subscription_active(
                _event(DodoWebhookEventType.SUBSCRIPTION_ACTIVE)
            )

        assert result.status == "processed"
        assert result.message == "Subscription activated"
        reactivate.assert_awaited_once_with(USER_ID)

    async def test_a_subscription_belonging_to_nobody_fails_the_webhook(self) -> None:
        """Dodo retries a failed result, so the ownerless subscription has to come
        back as a failure that names why rather than a silent success."""
        service = PaymentWebhookService()
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(f"{ACTIVATION}.user_repository") as users,
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription",
                new_callable=AsyncMock,
            ) as reactivate,
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=None)
            sub_repo.create = AsyncMock()
            users.get_by_email = AsyncMock(return_value=None)
            result = await service._handle_subscription_active(
                _event(DodoWebhookEventType.SUBSCRIPTION_ACTIVE, metadata={})
            )

        assert result.status == "failed"
        assert result.message == "User not found"
        reactivate.assert_not_awaited()


@pytest.mark.unit
class TestSubscriptionActivatedAnalytics:
    """The server owns ``subscription:activated`` — it is the only place a
    completed subscription is captured (the web app's success page used to fire
    its own ``subscription:completed`` for the same action, double-counting it
    and missing every overlay checkout that never lands on that page)."""

    async def test_activation_captures_the_event_once_against_the_gaia_user_id(self) -> None:
        service = PaymentWebhookService()
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription",
                new_callable=AsyncMock,
            ),
            patch(f"{ACTIVATION}.track_subscription_event") as track,
            patch(f"{ACTIVATION}.send_welcome_email_safely", new_callable=AsyncMock),
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=None)
            sub_repo.create = AsyncMock()
            await service._handle_subscription_active(
                _event(DodoWebhookEventType.SUBSCRIPTION_ACTIVE)
            )

        track.assert_called_once()
        assert track.call_args.kwargs["user_id"] == USER_ID
        assert track.call_args.kwargs["event_type"] == AnalyticsEvents.SUBSCRIPTION_ACTIVATED
        assert track.call_args.kwargs["subscription_id"] == "sub_123"

    async def test_a_redelivered_activation_does_not_capture_a_second_time(self) -> None:
        """Dodo re-fires ``subscription.active`` for an existing row; that early
        return must not inflate the activation count."""
        service = PaymentWebhookService()
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription",
                new_callable=AsyncMock,
            ),
            patch(f"{ACTIVATION}.track_subscription_event") as track,
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=MagicMock(user_id=USER_ID))
            await service._handle_subscription_active(
                _event(DodoWebhookEventType.SUBSCRIPTION_ACTIVE)
            )

        track.assert_not_called()


@pytest.mark.unit
class TestSubscriptionRenewedReactivatesWorkflows:
    async def test_renewal_reactivates_paused_workflows(self) -> None:
        service = PaymentWebhookService()
        with (
            patch(f"{MODULE}.subscription_repository") as sub_repo,
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription",
                new_callable=AsyncMock,
            ) as reactivate,
            patch(f"{MODULE}.track_subscription_event") as track,
        ):
            sub_repo.apply_update_by_dodo_id = AsyncMock(return_value=True)
            sub_repo.get_user_id_by_dodo_id = AsyncMock(return_value=USER_ID)
            result = await service._handle_subscription_renewed(
                _event(DodoWebhookEventType.SUBSCRIPTION_RENEWED, currency="eur")
            )

        assert result.status == "processed"
        reactivate.assert_awaited_once_with(USER_ID)
        # Revenue reporting splits on currency; a renewal that reports none is
        # counted in the default currency and quietly skews the numbers.
        assert track.call_args.kwargs["plan"] == SubscriptionPlan(currency="eur")

    async def test_reactivation_failure_never_fails_the_webhook(self) -> None:
        """Same swallow-and-log posture as deactivation — a reactivation bug must
        not turn an otherwise-successful billing webhook into a Dodo retry."""
        service = PaymentWebhookService()
        with (
            patch(f"{MODULE}.subscription_repository") as sub_repo,
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ),
            patch(f"{MODULE}.track_subscription_event"),
        ):
            sub_repo.apply_update_by_dodo_id = AsyncMock(return_value=True)
            sub_repo.get_user_id_by_dodo_id = AsyncMock(return_value=USER_ID)
            result = await service._handle_subscription_renewed(
                _event(DodoWebhookEventType.SUBSCRIPTION_RENEWED)
            )

        assert result.status == "processed"


@pytest.mark.unit
class TestSubscriptionFailedDeactivatesWorkflows:
    async def test_marks_the_subscription_failed_and_deactivates_workflows(self) -> None:
        service = PaymentWebhookService()
        with (
            patch(f"{MODULE}.subscription_repository") as sub_repo,
            patch.object(
                service, "_deactivate_workflows_for_lapsed_subscription", new_callable=AsyncMock
            ) as deactivate,
        ):
            sub_repo.apply_update_by_dodo_id = AsyncMock()
            sub_repo.get_user_id_by_dodo_id = AsyncMock(return_value=USER_ID)

            result = await service._handle_subscription_failed(
                _event(DodoWebhookEventType.SUBSCRIPTION_FAILED, subscription_id="sub_failed")
            )

        sub_repo.apply_update_by_dodo_id.assert_awaited_once()
        call_args = sub_repo.apply_update_by_dodo_id.call_args
        assert call_args.args[0] == "sub_failed"
        assert call_args.args[1].status == "failed"
        sub_repo.get_user_id_by_dodo_id.assert_awaited_once_with("sub_failed")
        deactivate.assert_awaited_once_with(USER_ID)
        assert result.event_type == DodoWebhookEventType.SUBSCRIPTION_FAILED.value
        assert result.status == "processed"
        assert result.message == "Subscription failed"
        assert result.subscription_id == "sub_failed"

    async def test_no_resolvable_user_never_calls_deactivate(self) -> None:
        service = PaymentWebhookService()
        with (
            patch(f"{MODULE}.subscription_repository") as sub_repo,
            patch.object(
                service, "_deactivate_workflows_for_lapsed_subscription", new_callable=AsyncMock
            ) as deactivate,
        ):
            sub_repo.apply_update_by_dodo_id = AsyncMock()
            sub_repo.get_user_id_by_dodo_id = AsyncMock(return_value=None)

            await service._handle_subscription_failed(
                _event(DodoWebhookEventType.SUBSCRIPTION_FAILED)
            )

        deactivate.assert_not_awaited()

    async def test_missing_subscription_data_raises(self) -> None:
        service = PaymentWebhookService()
        event = MagicMock(spec=DodoWebhookEvent)
        event.get_subscription_data.return_value = None

        with pytest.raises(ValueError, match="Invalid subscription data"):
            await service._handle_subscription_failed(event)


@pytest.mark.unit
class TestSubscriptionOnHoldDeactivatesWorkflows:
    async def test_marks_the_subscription_on_hold_and_deactivates_workflows(self) -> None:
        service = PaymentWebhookService()
        with (
            patch(f"{MODULE}.subscription_repository") as sub_repo,
            patch.object(
                service, "_deactivate_workflows_for_lapsed_subscription", new_callable=AsyncMock
            ) as deactivate,
        ):
            sub_repo.apply_update_by_dodo_id = AsyncMock()
            sub_repo.get_user_id_by_dodo_id = AsyncMock(return_value=USER_ID)

            result = await service._handle_subscription_on_hold(
                _event(DodoWebhookEventType.SUBSCRIPTION_ON_HOLD, subscription_id="sub_hold")
            )

        sub_repo.apply_update_by_dodo_id.assert_awaited_once()
        call_args = sub_repo.apply_update_by_dodo_id.call_args
        assert call_args.args[0] == "sub_hold"
        assert call_args.args[1].status == "on_hold"
        sub_repo.get_user_id_by_dodo_id.assert_awaited_once_with("sub_hold")
        deactivate.assert_awaited_once_with(USER_ID)
        assert result.event_type == DodoWebhookEventType.SUBSCRIPTION_ON_HOLD.value
        assert result.status == "processed"
        assert result.message == "Subscription on hold"
        assert result.subscription_id == "sub_hold"

    async def test_no_resolvable_user_never_calls_deactivate(self) -> None:
        service = PaymentWebhookService()
        with (
            patch(f"{MODULE}.subscription_repository") as sub_repo,
            patch.object(
                service, "_deactivate_workflows_for_lapsed_subscription", new_callable=AsyncMock
            ) as deactivate,
        ):
            sub_repo.apply_update_by_dodo_id = AsyncMock()
            sub_repo.get_user_id_by_dodo_id = AsyncMock(return_value=None)

            await service._handle_subscription_on_hold(
                _event(DodoWebhookEventType.SUBSCRIPTION_ON_HOLD)
            )

        deactivate.assert_not_awaited()

    async def test_missing_subscription_data_raises(self) -> None:
        service = PaymentWebhookService()
        event = MagicMock(spec=DodoWebhookEvent)
        event.get_subscription_data.return_value = None

        with pytest.raises(ValueError, match="Invalid subscription data"):
            await service._handle_subscription_on_hold(event)


@pytest.mark.unit
class TestDeactivateWorkflowsWrapperNeverRaises:
    """The private wrapper ``_deactivate_workflows_for_lapsed_subscription`` — a
    workflow-deactivation bug must not turn an otherwise-successful billing
    webhook into a Dodo retry."""

    async def test_delegates_to_the_free_function(self) -> None:
        service = PaymentWebhookService()
        with patch(
            f"{MODULE}.deactivate_workflows_for_lapsed_subscription", new_callable=AsyncMock
        ) as deactivate:
            await service._deactivate_workflows_for_lapsed_subscription(USER_ID)

        deactivate.assert_awaited_once_with(USER_ID)

    async def test_a_failure_is_swallowed_and_logged_with_exact_context(self) -> None:
        service = PaymentWebhookService()
        with (
            patch(
                f"{MODULE}.deactivate_workflows_for_lapsed_subscription",
                new_callable=AsyncMock,
                side_effect=RuntimeError("mongo exploded"),
            ),
            patch(f"{MODULE}.log") as mock_log,
        ):
            await service._deactivate_workflows_for_lapsed_subscription(USER_ID)  # must not raise

        mock_log.error.assert_called_once_with(
            "[PAYMENT] Failed to deactivate workflows for lapsed subscription",
            error="mongo exploded",
            error_type="RuntimeError",
            user_id=USER_ID,
        )


@pytest.mark.unit
class TestReactivateWorkflowsWrapperNeverRaises:
    """``reactivate_workflows_safely`` — same swallow-and-log posture as
    deactivation. Shared by the webhook and the verification reconciliation."""

    async def test_delegates_to_the_free_function(self) -> None:
        with patch(
            f"{PAUSE}.reactivate_workflows_for_restored_subscription", new_callable=AsyncMock
        ) as reactivate:
            await reactivate_workflows_safely(USER_ID)

        reactivate.assert_awaited_once_with(USER_ID)

    async def test_a_failure_is_swallowed_and_logged_with_exact_context(self) -> None:
        with (
            patch(
                f"{PAUSE}.reactivate_workflows_for_restored_subscription",
                new_callable=AsyncMock,
                side_effect=RuntimeError("mongo exploded"),
            ),
            patch(f"{ACTIVATION}.log") as mock_log,
        ):
            await reactivate_workflows_safely(USER_ID)  # must not raise

        mock_log.error.assert_called_once_with(
            "[PAYMENT] Failed to reactivate workflows for restored subscription",
            error="mongo exploded",
            error_type="RuntimeError",
            user_id=USER_ID,
        )


@pytest.mark.unit
class TestSendWelcomeEmailSafely:
    """The new subscriber's welcome mail — same swallow-and-log posture as the
    workflow wrappers."""

    async def test_sends_to_the_looked_up_users_name_and_address(self) -> None:
        user = MagicMock(first_name="Alice", email="alice@example.com")
        with (
            patch(f"{ACTIVATION}.user_repository") as users,
            patch(
                f"{ACTIVATION}.send_pro_subscription_email", new_callable=AsyncMock
            ) as send_email,
            patch(f"{ACTIVATION}.log") as mock_log,
        ):
            users.get = AsyncMock(return_value=user)
            await send_welcome_email_safely(USER_ID)

        users.get.assert_awaited_once_with(USER_ID)
        send_email.assert_awaited_once_with(
            user_name="Alice", user_email="alice@example.com", user_id=USER_ID
        )
        # The address is mailed, never logged: log fields are ids, counts and
        # enums, so the line names who was mailed rather than where.
        mock_log.info.assert_called_once_with("[PAYMENT] Welcome email sent", user_id=USER_ID)

    async def test_a_user_with_no_first_name_is_greeted_generically(self) -> None:
        with (
            patch(f"{ACTIVATION}.user_repository") as users,
            patch(
                f"{ACTIVATION}.send_pro_subscription_email", new_callable=AsyncMock
            ) as send_email,
        ):
            users.get = AsyncMock(return_value=MagicMock(first_name=None, email="a@example.com"))
            await send_welcome_email_safely(USER_ID)

        assert send_email.await_args.kwargs["user_name"] == "User"

    async def test_a_user_without_an_email_is_never_mailed(self) -> None:
        with (
            patch(f"{ACTIVATION}.user_repository") as users,
            patch(
                f"{ACTIVATION}.send_pro_subscription_email", new_callable=AsyncMock
            ) as send_email,
        ):
            users.get = AsyncMock(return_value=MagicMock(first_name="Alice", email=None))
            await send_welcome_email_safely(USER_ID)

        send_email.assert_not_awaited()

    async def test_a_failure_is_swallowed_and_logged_with_exact_context(self) -> None:
        with (
            patch(f"{ACTIVATION}.user_repository") as users,
            patch(f"{ACTIVATION}.log") as mock_log,
        ):
            users.get = AsyncMock(side_effect=RuntimeError("mongo exploded"))
            await send_welcome_email_safely(USER_ID)  # must not raise

        mock_log.error.assert_called_once_with(
            "[PAYMENT] Failed to send welcome email",
            error="mongo exploded",
            error_type="RuntimeError",
            user_id=USER_ID,
        )


@pytest.mark.unit
class TestResolveSubscriptionOwner:
    """Checkout stamps the GAIA user id into metadata; the customer email is the
    fallback for sessions minted before that."""

    async def test_metadata_user_id_wins_without_touching_the_user_repository(self) -> None:
        with patch(f"{ACTIVATION}.user_repository") as users:
            users.get_by_email = AsyncMock()
            owner = await resolve_subscription_owner(_subscription_data())

        assert owner == USER_ID
        users.get_by_email.assert_not_awaited()

    async def test_falls_back_to_the_customer_email_lookup(self) -> None:
        with patch(f"{ACTIVATION}.user_repository") as users:
            users.get_by_email = AsyncMock(return_value=MagicMock(id=USER_ID))
            owner = await resolve_subscription_owner(_subscription_data(metadata={}))

        users.get_by_email.assert_awaited_once_with("user@example.com")
        assert owner == USER_ID

    async def test_an_unknown_customer_email_belongs_to_nobody(self) -> None:
        with patch(f"{ACTIVATION}.user_repository") as users:
            users.get_by_email = AsyncMock(return_value=None)
            owner = await resolve_subscription_owner(_subscription_data(metadata={}))

        assert owner is None


@pytest.mark.unit
class TestActivateSubscription:
    """The single write path shared by the ``subscription.active`` webhook and
    payment verification's Dodo reconciliation."""

    async def test_writes_every_dodo_field_onto_the_new_row(self) -> None:
        sub_data = _subscription_data(
            next_billing_date="2026-02-01T00:00:00Z",
            previous_billing_date="2026-01-01T00:00:00Z",
        )
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(f"{ACTIVATION}.track_subscription_event"),
            patch(f"{ACTIVATION}.send_welcome_email_safely", new_callable=AsyncMock),
            patch(f"{ACTIVATION}.reactivate_workflows_safely", new_callable=AsyncMock),
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=None)
            sub_repo.create = AsyncMock()
            result = await activate_subscription(sub_data)

        sub_repo.get_by_dodo_id.assert_awaited_once_with("sub_123")
        created = sub_repo.create.await_args.args[0]
        assert created.dodo_subscription_id == "sub_123"
        assert created.user_id == USER_ID
        assert created.product_id == "prod_pro"
        assert created.status == "active"
        assert created.quantity == 1
        assert created.currency == "usd"
        assert created.recurring_pre_tax_amount == 2000
        assert created.payment_frequency_count == 1
        assert created.payment_frequency_interval == "Month"
        assert created.subscription_period_count == 1
        assert created.subscription_period_interval == "Month"
        assert created.next_billing_date == "2026-02-01T00:00:00Z"
        assert created.previous_billing_date == "2026-01-01T00:00:00Z"
        assert created.metadata == {"user_id": USER_ID}
        # One UTC-aware instant on both timestamps, never a naive local one.
        assert created.created_at is not None
        assert created.created_at.utcoffset() == timedelta(0)
        assert created.updated_at == created.created_at
        assert result == SubscriptionActivation(user_id=USER_ID, created=True)

    async def test_reports_the_priced_pro_plan_in_dollars_to_analytics(self) -> None:
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(f"{ACTIVATION}.track_subscription_event") as track,
            patch(f"{ACTIVATION}.send_welcome_email_safely", new_callable=AsyncMock) as welcome,
            patch(f"{ACTIVATION}.reactivate_workflows_safely", new_callable=AsyncMock),
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=None)
            sub_repo.create = AsyncMock()
            await activate_subscription(_subscription_data())

        assert track.call_args.kwargs["plan"] == SubscriptionPlan(
            name="Pro", amount=20.0, currency="usd"
        )
        welcome.assert_awaited_once_with(USER_ID)

    async def test_a_zero_amount_subscription_reports_no_price(self) -> None:
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(f"{ACTIVATION}.track_subscription_event") as track,
            patch(f"{ACTIVATION}.send_welcome_email_safely", new_callable=AsyncMock),
            patch(f"{ACTIVATION}.reactivate_workflows_safely", new_callable=AsyncMock),
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=None)
            sub_repo.create = AsyncMock()
            await activate_subscription(_subscription_data(recurring_pre_tax_amount=0))

        assert track.call_args.kwargs["plan"].amount is None

    async def test_logs_the_activation_against_the_dodo_subscription_id(self) -> None:
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(f"{ACTIVATION}.track_subscription_event"),
            patch(f"{ACTIVATION}.send_welcome_email_safely", new_callable=AsyncMock),
            patch(f"{ACTIVATION}.reactivate_workflows_safely", new_callable=AsyncMock),
            patch(f"{ACTIVATION}.log") as mock_log,
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=None)
            sub_repo.create = AsyncMock()
            await activate_subscription(_subscription_data())

        mock_log.info.assert_called_once_with(
            "[PAYMENT] Subscription activated", subscription_id="sub_123"
        )

    async def test_an_already_recorded_subscription_is_not_rewritten(self) -> None:
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(f"{ACTIVATION}.reactivate_workflows_safely", new_callable=AsyncMock),
            patch(f"{ACTIVATION}.log") as mock_log,
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=MagicMock(user_id=USER_ID))
            sub_repo.create = AsyncMock()
            result = await activate_subscription(_subscription_data())

        sub_repo.create.assert_not_awaited()
        assert result == SubscriptionActivation(user_id=USER_ID, created=False)
        mock_log.info.assert_called_once_with(
            "[PAYMENT] Subscription already exists", subscription_id="sub_123"
        )

    async def test_a_subscription_belonging_to_nobody_is_not_written(self) -> None:
        with (
            patch(f"{ACTIVATION}.subscription_repository") as sub_repo,
            patch(f"{ACTIVATION}.user_repository") as users,
            patch(f"{ACTIVATION}.log") as mock_log,
        ):
            sub_repo.get_by_dodo_id = AsyncMock(return_value=None)
            sub_repo.create = AsyncMock()
            users.get_by_email = AsyncMock(return_value=None)
            result = await activate_subscription(_subscription_data(metadata={}))

        sub_repo.create.assert_not_awaited()
        assert result == SubscriptionActivation(user_id=None, created=False)
        mock_log.error.assert_called_once_with(
            "[PAYMENT] User not found for subscription", subscription_id="sub_123"
        )


# ============================================================================
# PaymentWebhookService — moved from test_payment_service.py
# ============================================================================


class TestVerifyWebhookSignature:
    """Tests for PaymentWebhookService.verify_webhook_signature."""

    def test_returns_false_when_no_verifier_configured(self) -> None:
        """When no verifier is configured, fail closed and reject the webhook."""
        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.DODO_WEBHOOK_PAYMENTS_SECRET = ""
            mock_settings.ENV = "production"
            svc = PaymentWebhookService()

        assert svc.webhook_verifier is None
        result = svc.verify_webhook_signature("{}", {})
        assert result is False

    def test_production_valid_signature(self):
        """In production with valid signature, returns True."""
        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.DODO_WEBHOOK_PAYMENTS_SECRET = "whsec_test123"
            mock_settings.ENV = "production"
            with patch("app.services.payments.payment_webhook_service.Webhook") as mock_wh_cls:
                mock_verifier = MagicMock()
                mock_verifier.verify = MagicMock(return_value=None)
                mock_wh_cls.return_value = mock_verifier
                svc = PaymentWebhookService()

        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.ENV = "production"
            result = svc.verify_webhook_signature(
                '{"type":"test"}',
                {
                    "webhook-id": "msg_abc",
                    "webhook-timestamp": "1234567890",
                    "webhook-signature": "v1,valid_sig",
                },
            )

        assert result is True
        mock_verifier.verify.assert_called_once()

    def test_production_invalid_signature_returns_false(self):
        """In production with invalid signature, returns False."""
        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.DODO_WEBHOOK_PAYMENTS_SECRET = "whsec_test123"
            mock_settings.ENV = "production"
            with patch("app.services.payments.payment_webhook_service.Webhook") as mock_wh_cls:
                mock_verifier = MagicMock()
                mock_verifier.verify = MagicMock(side_effect=Exception("Invalid signature"))
                mock_wh_cls.return_value = mock_verifier
                svc = PaymentWebhookService()

        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.ENV = "production"
            result = svc.verify_webhook_signature(
                '{"type":"test"}',
                {
                    "webhook-id": "msg_abc",
                    "webhook-timestamp": "1234567890",
                    "webhook-signature": "v1,bad_sig",
                },
            )

        assert result is False

    def test_header_normalization(self):
        """Headers are normalized to lowercase-with-dashes format."""
        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.DODO_WEBHOOK_PAYMENTS_SECRET = "whsec_test123"
            mock_settings.ENV = "production"
            with patch("app.services.payments.payment_webhook_service.Webhook") as mock_wh_cls:
                mock_verifier = MagicMock()
                mock_verifier.verify = MagicMock(return_value=None)
                mock_wh_cls.return_value = mock_verifier
                svc = PaymentWebhookService()

        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.ENV = "production"
            svc.verify_webhook_signature(
                '{"data":"test"}',
                {
                    "Webhook-Id": "msg_abc",
                    "Webhook-Timestamp": "1234567890",
                    "Webhook-Signature": "v1,sig",
                },
            )

        call_args = mock_verifier.verify.call_args
        headers_passed = call_args[0][1]
        assert "webhook-id" in headers_passed
        assert "webhook-timestamp" in headers_passed
        assert "webhook-signature" in headers_passed

    def test_verifier_init_failure_sets_verifier_to_none(self):
        """If Webhook() constructor fails, verifier is None."""
        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.DODO_WEBHOOK_PAYMENTS_SECRET = "bad_secret"
            mock_settings.ENV = "production"
            with patch(
                "app.services.payments.payment_webhook_service.Webhook",
                side_effect=Exception("Bad secret format"),
            ):
                svc = PaymentWebhookService()

        assert svc.webhook_verifier is None


class TestProcessWebhookIdempotency:
    """Tests for idempotency / deduplication in process_webhook."""

    async def test_already_processed_webhook_is_skipped(
        self,
        webhook_service,
        mock_processed_webhook_repository,
    ):
        """A delivery whose id is already claimed returns 'ignored' before any handler runs."""
        mock_processed_webhook_repository.claim = AsyncMock(return_value=False)

        event_data = _make_webhook_event("payment.succeeded", PAYMENT_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_dup")

        assert result.status == "ignored"
        assert result.message == "Webhook already processed"
        # The claim is on this delivery id, under the event type Dodo sent.
        mock_processed_webhook_repository.claim.assert_awaited_once_with(
            "wh_dup", event_type="payment.succeeded"
        )
        mock_processed_webhook_repository.record_outcome.assert_not_awaited()

    async def test_a_delivery_without_a_type_is_claimed_as_unknown(
        self, webhook_service, mock_processed_webhook_repository
    ):
        mock_processed_webhook_repository.claim = AsyncMock(return_value=False)

        result = await webhook_service.process_webhook({"data": {}}, "wh_typeless")

        assert result.event_type == "unknown"
        mock_processed_webhook_repository.claim.assert_awaited_once_with(
            "wh_typeless", event_type="unknown"
        )

    async def test_a_replayed_cancellation_deactivates_workflows_only_once(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        """Dodo can redeliver the same webhook id. The idempotency check must stop
        the second delivery before it deactivates the user's workflows again."""
        event_data = _make_webhook_event("subscription.cancelled", SUBSCRIPTION_DATA_PAYLOAD)

        first = await webhook_service.process_webhook(event_data, "wh_cancel_replay")
        assert first.status == "processed"
        mock_deactivate_workflows.assert_awaited_once_with(FAKE_USER_ID)

        # Second delivery of the identical webhook id: the claim is taken.
        mock_processed_webhook_repository.claim = AsyncMock(return_value=False)
        second = await webhook_service.process_webhook(event_data, "wh_cancel_replay")

        assert second.status == "ignored"
        mock_deactivate_workflows.assert_awaited_once_with(FAKE_USER_ID)

    async def test_unknown_event_type_is_ignored_and_recorded(
        self,
        webhook_service,
        mock_processed_webhook_repository,
    ):
        """Unhandled event types are recorded to prevent re-processing."""
        event_data = {
            "business_id": "biz_001",
            "type": "payment.succeeded",
            "timestamp": "2025-01-01T00:00:00Z",
            "data": PAYMENT_DATA_PAYLOAD,
        }
        # Simulate unknown event by removing the handler
        original_handlers = webhook_service.handlers.copy()
        webhook_service.handlers = {}

        result = await webhook_service.process_webhook(event_data, "wh_unknown")

        assert result.status == "ignored"
        assert "No handler" in result.message
        mock_processed_webhook_repository.record_outcome.assert_awaited_once_with(
            "wh_unknown",
            ProcessedWebhookUpdate(
                status="ignored", message=result.message, payment_id=None, subscription_id=None
            ),
        )
        webhook_service.handlers = original_handlers

    async def test_a_handled_delivery_records_the_handlers_full_outcome(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        event_data = _make_webhook_event("subscription.cancelled", SUBSCRIPTION_DATA_PAYLOAD)

        result = await webhook_service.process_webhook(event_data, "wh_cancel_outcome")

        assert result.status == "processed"
        mock_processed_webhook_repository.record_outcome.assert_awaited_once_with(
            "wh_cancel_outcome",
            ProcessedWebhookUpdate(
                status=result.status,
                message=result.message,
                payment_id=result.payment_id,
                subscription_id=result.subscription_id,
            ),
        )

    def test_the_recorded_outcome_carries_every_field_of_the_result(self):
        from app.services.payments.payment_webhook_service import _outcome_of

        result = DodoWebhookProcessingResult(
            event_type="payment.succeeded",
            status="processed",
            message="ok",
            payment_id="pay_1",
            subscription_id="sub_1",
        )

        assert _outcome_of(result) == ProcessedWebhookUpdate(
            status="processed", message="ok", payment_id="pay_1", subscription_id="sub_1"
        )

    async def test_every_event_type_dodo_can_send_parses(self) -> None:
        """Drift guard against the SDK: a real Dodo event outside our enum failed
        validation and was logged as a processing error (seen live with
        subscription.updated on 2026-09-06). The SDK's literal is the contract."""
        sdk_types = set(get_args(WebhookEventType))
        ours = {member.value for member in DodoWebhookEventType}
        assert ours == sdk_types

    async def test_an_event_we_do_not_act_on_is_ignored_not_failed(
        self,
        webhook_service,
        mock_processed_webhook_repository,
    ):
        """subscription.updated fires on every Dodo-side edit; we neither act on
        it nor treat it as an error, and it is recorded so a redelivery is a no-op."""
        event_data = _make_webhook_event("subscription.updated", {})
        result = await webhook_service.process_webhook(event_data, "wh_updated")
        assert result.status == "ignored"
        assert "No handler" in result.message
        mock_processed_webhook_repository.record_outcome.assert_awaited()

    async def test_processing_failure_returns_failed_result(
        self,
        webhook_service,
        mock_processed_webhook_repository,
    ):
        """When event parsing fails, returns a 'failed' result and hands the
        claim back so the sender's retry is not turned away as a replay."""
        bad_data = {"type": "INVALID_TYPE", "data": {}}

        result = await webhook_service.process_webhook(bad_data, "wh_bad")

        mock_processed_webhook_repository.release.assert_awaited_once_with("wh_bad")
        mock_processed_webhook_repository.record_outcome.assert_not_awaited()

        assert result.status == "failed"
        assert "Processing error" in result.message


# ============================================================================
# Payment Event Handlers
# ============================================================================


class TestHandlePaymentSucceeded:
    """Tests for _handle_payment_succeeded via process_webhook."""

    async def test_processes_valid_payment_success(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_users_collection,
        mock_track_payment,
    ):
        event_data = _make_webhook_event("payment.succeeded", PAYMENT_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_pay_001")

        assert result.status == "processed"
        assert result.payment_id == "pay_001"
        assert result.subscription_id == "sub_xyz789"
        assert "success" in result.message.lower()

    async def test_tracks_analytics_event(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_users_collection,
        mock_track_payment,
    ):
        event_data = _make_webhook_event("payment.succeeded", PAYMENT_DATA_PAYLOAD)
        await webhook_service.process_webhook(event_data, "wh_pay_002")

        mock_track_payment.assert_called_once()
        call_kwargs = mock_track_payment.call_args[1]
        assert call_kwargs["user_id"] == FAKE_USER_ID
        assert call_kwargs["payment_id"] == "pay_001"

    async def test_analytics_uses_metadata_user_id_without_db_lookup(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_users_collection,
        mock_track_payment,
    ):
        """The metadata user id is the PostHog distinct id — no user lookup."""
        payload = {**PAYMENT_DATA_PAYLOAD, "metadata": {"user_id": "unresolved-user-id"}}
        event_data = _make_webhook_event("payment.succeeded", payload)

        await webhook_service.process_webhook(event_data, "wh_pay_003")

        mock_track_payment.assert_called_once()
        assert mock_track_payment.call_args[1]["user_id"] == "unresolved-user-id"

    async def test_no_analytics_when_no_user_id_in_metadata(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_users_collection,
        mock_track_payment,
    ):
        payload = {**PAYMENT_DATA_PAYLOAD, "metadata": {}}
        event_data = _make_webhook_event("payment.succeeded", payload)

        await webhook_service.process_webhook(event_data, "wh_pay_004")

        mock_track_payment.assert_not_called()

    async def test_invalid_payment_data_raises(
        self,
        webhook_service,
        mock_processed_webhook_repository,
    ):
        """When payment data can't be parsed, ValueError is raised (caught by process_webhook)."""
        bad_payload = {"incomplete": True}
        event_data = _make_webhook_event("payment.succeeded", bad_payload)

        result = await webhook_service.process_webhook(event_data, "wh_pay_bad")

        assert result.status == "failed"
        assert "Processing error" in result.message


class TestHandlePaymentFailed:
    """Tests for _handle_payment_failed."""

    async def test_processes_payment_failure(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_users_collection,
        mock_track_payment,
    ):
        event_data = _make_webhook_event("payment.failed", PAYMENT_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_fail_001")

        assert result.status == "processed"
        assert "failure" in result.message.lower()
        assert result.payment_id == "pay_001"

    async def test_tracks_failure_analytics(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_users_collection,
        mock_track_payment,
    ):
        event_data = _make_webhook_event("payment.failed", PAYMENT_DATA_PAYLOAD)
        await webhook_service.process_webhook(event_data, "wh_fail_002")

        mock_track_payment.assert_called_once()
        call_kwargs = mock_track_payment.call_args[1]
        assert call_kwargs["event_type"] == "payment:failed"


class TestHandlePaymentProcessing:
    """Tests for _handle_payment_processing."""

    async def test_processes_payment_processing_event(
        self,
        webhook_service,
        mock_processed_webhook_repository,
    ):
        event_data = _make_webhook_event("payment.processing", PAYMENT_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_proc_001")

        assert result.status == "processed"
        assert "processing" in result.message.lower()


class TestHandlePaymentCancelled:
    """Tests for _handle_payment_cancelled."""

    async def test_processes_payment_cancellation(
        self,
        webhook_service,
        mock_processed_webhook_repository,
    ):
        event_data = _make_webhook_event("payment.cancelled", PAYMENT_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_cancel_001")

        assert result.status == "processed"
        assert "cancellation" in result.message.lower()


# ============================================================================
# Subscription Event Handlers
# ============================================================================


class TestHandleSubscriptionActive:
    """Tests for _handle_subscription_active."""

    async def test_creates_subscription_record(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_webhook_users_collection,
        mock_webhook_send_email,
        mock_track_subscription,
    ):
        event_data = _make_webhook_event("subscription.active", SUBSCRIPTION_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_sub_001")

        assert result.status == "processed"
        assert "activated" in result.message.lower()
        assert result.subscription_id == "sub_xyz789"
        mock_webhook_subscription_repository.create.assert_awaited_once()

    async def test_skips_duplicate_subscription(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_webhook_users_collection,
        mock_webhook_send_email,
        mock_track_subscription,
    ):
        """If subscription already exists in DB, skip creation."""
        mock_webhook_subscription_repository.get_by_dodo_id = AsyncMock(
            return_value=SAMPLE_SUBSCRIPTION
        )

        event_data = _make_webhook_event("subscription.active", SUBSCRIPTION_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_sub_002")

        assert result.status == "processed"
        assert "already active" in result.message.lower()
        mock_webhook_subscription_repository.create.assert_not_awaited()

    async def test_finds_user_by_email_when_user_id_missing(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_webhook_users_collection,
        mock_webhook_send_email,
        mock_track_subscription,
    ):
        """When metadata has no user_id, looks up user by customer email."""
        payload = {**SUBSCRIPTION_DATA_PAYLOAD, "metadata": {}}
        event_data = _make_webhook_event("subscription.active", payload)
        _set_user(mock_webhook_users_collection, SAMPLE_USER_DOC)

        result = await webhook_service.process_webhook(event_data, "wh_sub_003")

        assert result.status == "processed"
        # No user_id in metadata → user is looked up by email through the repo.
        mock_webhook_users_collection.get_by_email.assert_awaited_with(FAKE_EMAIL)

    async def test_fails_when_user_not_found_by_email(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_webhook_users_collection,
        mock_track_subscription,
    ):
        """Returns failed result if user can't be found by email."""
        payload = {**SUBSCRIPTION_DATA_PAYLOAD, "metadata": {}}
        event_data = _make_webhook_event("subscription.active", payload)
        _set_user(mock_webhook_users_collection, None)

        result = await webhook_service.process_webhook(event_data, "wh_sub_004")

        assert result.status == "failed"
        assert "User not found" in result.message

    async def test_sends_welcome_email(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_webhook_users_collection,
        mock_webhook_send_email,
        mock_track_subscription,
    ):
        event_data = _make_webhook_event("subscription.active", SUBSCRIPTION_DATA_PAYLOAD)
        # For welcome email, _send_welcome_email does a separate find_one
        _set_user(mock_webhook_users_collection, SAMPLE_USER_DOC)

        await webhook_service.process_webhook(event_data, "wh_sub_005")

        mock_webhook_send_email.assert_awaited_once()

    async def test_tracks_analytics_on_activation(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_webhook_users_collection,
        mock_webhook_send_email,
        mock_track_subscription,
    ):
        event_data = _make_webhook_event("subscription.active", SUBSCRIPTION_DATA_PAYLOAD)
        await webhook_service.process_webhook(event_data, "wh_sub_006")

        mock_track_subscription.assert_called_once()
        call_kwargs = mock_track_subscription.call_args[1]
        assert call_kwargs["user_id"] == FAKE_USER_ID
        assert call_kwargs["event_type"] == "subscription:activated"

    async def test_insert_failure_raises(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_webhook_users_collection,
        mock_track_subscription,
    ):
        """If the repository create fails, the webhook returns a failed result."""
        mock_webhook_subscription_repository.create = AsyncMock(
            side_effect=Exception("insert failed")
        )
        event_data = _make_webhook_event("subscription.active", SUBSCRIPTION_DATA_PAYLOAD)

        result = await webhook_service.process_webhook(event_data, "wh_sub_007")

        assert result.status == "failed"
        assert "Processing error" in result.message

    @pytest.mark.usefixtures(
        "mock_processed_webhook_repository",
        "mock_webhook_subscription_repository",
        "mock_webhook_users_collection",
        "mock_webhook_send_email",
        "mock_track_subscription",
    )
    async def test_does_not_deactivate_workflows(
        self,
        webhook_service,
        mock_deactivate_workflows,
    ):
        """A user going Pro must never have their automation turned off."""
        event_data = _make_webhook_event("subscription.active", SUBSCRIPTION_DATA_PAYLOAD)
        await webhook_service.process_webhook(event_data, "wh_sub_008")

        mock_deactivate_workflows.assert_not_awaited()


class TestHandleSubscriptionRenewed:
    """Tests for _handle_subscription_renewed."""

    async def test_updates_billing_dates(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
    ):
        event_data = _make_webhook_event("subscription.renewed", SUBSCRIPTION_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_renew_001")

        assert result.status == "processed"
        assert "renewed" in result.message.lower()
        mock_webhook_subscription_repository.apply_update_by_dodo_id.assert_awaited_once()
        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert set_data["status"] == "active"
        assert "next_billing_date" in set_data
        assert "previous_billing_date" in set_data

    async def test_omitted_billing_dates_are_not_written_as_null(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
    ):
        """A renewal that omits the billing dates must leave the stored ones alone.

        Passing them to SubscriptionUpdate marks them in model_fields_set even
        when None, so the repository's model_dump(exclude_unset=True) emits
        ``next_billing_date: None`` and the $set overwrites good stored values
        with null.
        """
        payload = {
            **SUBSCRIPTION_DATA_PAYLOAD,
            "next_billing_date": None,
            "previous_billing_date": None,
        }
        event_data = _make_webhook_event("subscription.renewed", payload)

        result = await webhook_service.process_webhook(event_data, "wh_renew_nulls")

        assert result.status == "processed"
        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert set_data["status"] == "active"
        assert "next_billing_date" not in set_data
        assert "previous_billing_date" not in set_data

    async def test_a_renewal_that_matched_no_row_is_not_reported_as_renewed(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
    ):
        """Nothing was renewed, so nothing is captured — a renewal event for a
        subscription GAIA has no row for is a failure to mirror, not a renewal.
        ``TestAFailedHandlerReleasesItsClaim`` covers what that failure costs
        the delivery."""
        mock_webhook_subscription_repository.apply_update_by_dodo_id = AsyncMock(return_value=False)
        event_data = _make_webhook_event("subscription.renewed", SUBSCRIPTION_DATA_PAYLOAD)

        result = await webhook_service.process_webhook(event_data, "wh_renew_002")

        assert result.status == "failed"
        mock_track_subscription.assert_not_called()

    async def test_tracks_renewal_analytics(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
    ):
        event_data = _make_webhook_event("subscription.renewed", SUBSCRIPTION_DATA_PAYLOAD)

        await webhook_service.process_webhook(event_data, "wh_renew_003")

        # WHICH subscription was resolved to a user. Unasserted, the lookup
        # argument could go null and the renewal would be attributed to
        # whoever a None lookup happens to return — or to nobody.
        mock_webhook_subscription_repository.get_user_id_by_dodo_id.assert_awaited_once_with(
            "sub_xyz789"
        )
        mock_track_subscription.assert_called_once()
        call_kwargs = mock_track_subscription.call_args[1]
        assert call_kwargs["event_type"] == "subscription:renewed"
        assert call_kwargs["user_id"] == FAKE_USER_ID
        assert call_kwargs["subscription_id"] == "sub_xyz789"


class TestHandleSubscriptionCancelled:
    """Tests for _handle_subscription_cancelled."""

    async def test_sets_status_to_cancelled(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
    ):
        event_data = _make_webhook_event("subscription.cancelled", SUBSCRIPTION_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_cancel_sub_001")

        assert result.status == "processed"
        assert "cancelled" in result.message.lower()
        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert set_data["status"] == "cancelled"

    async def test_includes_cancelled_at_when_present(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
    ):
        payload = {
            **SUBSCRIPTION_DATA_PAYLOAD,
            "cancelled_at": "2025-06-15T00:00:00Z",
        }
        event_data = _make_webhook_event("subscription.cancelled", payload)

        await webhook_service.process_webhook(event_data, "wh_cancel_sub_002")

        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert set_data["cancelled_at"] == "2025-06-15T00:00:00Z"

    async def test_no_cancelled_at_when_absent(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
    ):
        payload = {**SUBSCRIPTION_DATA_PAYLOAD, "cancelled_at": None}
        event_data = _make_webhook_event("subscription.cancelled", payload)

        await webhook_service.process_webhook(event_data, "wh_cancel_sub_003")

        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert "cancelled_at" not in set_data

    async def test_tracks_cancellation_analytics(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        event_data = _make_webhook_event("subscription.cancelled", SUBSCRIPTION_DATA_PAYLOAD)
        await webhook_service.process_webhook(event_data, "wh_cancel_sub_004")

        mock_webhook_subscription_repository.get_user_id_by_dodo_id.assert_awaited_once_with(
            "sub_xyz789"
        )
        mock_track_subscription.assert_called_once()
        call_kwargs = mock_track_subscription.call_args[1]
        assert call_kwargs["event_type"] == "subscription:cancelled"
        assert call_kwargs["user_id"] == FAKE_USER_ID
        assert call_kwargs["properties"] == {
            "product_id": "prod_abc123",
            "billing_interval": "month",
        }

    async def test_scheduled_cancel_keeps_status_and_sets_flag(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        """A cancel-at-next-billing-date keeps the subscription active and just
        records the flag — the user retains Pro access until the period ends."""
        payload = {
            **SUBSCRIPTION_DATA_PAYLOAD,
            "status": "active",
            "cancel_at_next_billing_date": True,
        }
        event_data = _make_webhook_event("subscription.cancelled", payload)

        await webhook_service.process_webhook(event_data, "wh_cancel_sub_005")

        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        # Status is deliberately NOT in the update — only the flag records the
        # scheduled cancellation. A later `subscription.expired` flips status.
        assert "status" not in set_data
        assert set_data["cancel_at_next_billing_date"] is True

    async def test_scheduled_cancel_ignores_payload_status(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        """Even if Dodo ever reported status "cancelled" in a scheduled-cancel
        payload, the user is not downgraded early — status stays untouched."""
        payload = {
            **SUBSCRIPTION_DATA_PAYLOAD,
            "status": "cancelled",
            "cancel_at_next_billing_date": True,
        }
        event_data = _make_webhook_event("subscription.cancelled", payload)

        await webhook_service.process_webhook(event_data, "wh_cancel_sub_006")

        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert "status" not in set_data
        assert set_data["cancel_at_next_billing_date"] is True

    async def test_immediate_cancel_deactivates_this_users_workflows(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        """An immediate cancellation (no cancel_at_next_billing_date) drops the
        user from Pro right away, so their workflows must be turned off now."""
        event_data = _make_webhook_event("subscription.cancelled", SUBSCRIPTION_DATA_PAYLOAD)

        await webhook_service.process_webhook(event_data, "wh_cancel_sub_007")

        mock_deactivate_workflows.assert_awaited_once_with(FAKE_USER_ID)

    async def test_scheduled_cancel_does_not_deactivate_workflows(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        """A cancel scheduled for period end keeps the user on Pro (and their
        workflows running) until `subscription.expired` actually fires."""
        payload = {**SUBSCRIPTION_DATA_PAYLOAD, "cancel_at_next_billing_date": True}
        event_data = _make_webhook_event("subscription.cancelled", payload)

        await webhook_service.process_webhook(event_data, "wh_cancel_sub_008")

        mock_deactivate_workflows.assert_not_awaited()

    async def test_deactivation_failure_does_not_fail_the_webhook(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        """A broken workflow deactivation must not turn an otherwise-successful
        billing webhook into a "failed" result that Dodo would retry forever."""
        mock_deactivate_workflows.side_effect = RuntimeError("mongo down")
        event_data = _make_webhook_event("subscription.cancelled", SUBSCRIPTION_DATA_PAYLOAD)

        result = await webhook_service.process_webhook(event_data, "wh_cancel_sub_009")

        assert result.status == "processed"


class TestHandleSubscriptionExpired:
    """Tests for _handle_subscription_expired."""

    async def test_sets_status_to_expired(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
    ):
        event_data = _make_webhook_event("subscription.expired", SUBSCRIPTION_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_expire_001")

        assert result.status == "processed"
        assert "expired" in result.message.lower()
        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert set_data["status"] == "expired"

    async def test_tracks_expiry_analytics(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        event_data = _make_webhook_event("subscription.expired", SUBSCRIPTION_DATA_PAYLOAD)
        await webhook_service.process_webhook(event_data, "wh_expire_002")

        mock_webhook_subscription_repository.get_user_id_by_dodo_id.assert_awaited_once_with(
            "sub_xyz789"
        )
        mock_track_subscription.assert_called_once()
        call_kwargs = mock_track_subscription.call_args[1]
        assert call_kwargs["event_type"] == "subscription:expired"
        assert call_kwargs["user_id"] == FAKE_USER_ID

    async def test_deactivates_this_users_workflows(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        event_data = _make_webhook_event("subscription.expired", SUBSCRIPTION_DATA_PAYLOAD)
        await webhook_service.process_webhook(event_data, "wh_expire_003")

        mock_deactivate_workflows.assert_awaited_once_with(FAKE_USER_ID)

    async def test_no_user_id_means_no_deactivation_call(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_track_subscription,
        mock_deactivate_workflows,
    ):
        """No local subscription row matched the Dodo id: there is no user to
        resolve, so nothing is deactivated instead of raising on a None id."""
        mock_webhook_subscription_repository.get_user_id_by_dodo_id.return_value = None
        event_data = _make_webhook_event("subscription.expired", SUBSCRIPTION_DATA_PAYLOAD)

        await webhook_service.process_webhook(event_data, "wh_expire_004")

        mock_deactivate_workflows.assert_not_awaited()


class TestHandleSubscriptionFailed:
    """Tests for _handle_subscription_failed."""

    async def test_sets_status_to_failed(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_deactivate_workflows,
    ):
        event_data = _make_webhook_event("subscription.failed", SUBSCRIPTION_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_sfail_001")

        assert result.status == "processed"
        assert "failed" in result.message.lower()
        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert set_data["status"] == "failed"

    async def test_deactivates_this_users_workflows(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_deactivate_workflows,
    ):
        event_data = _make_webhook_event("subscription.failed", SUBSCRIPTION_DATA_PAYLOAD)
        await webhook_service.process_webhook(event_data, "wh_sfail_002")

        mock_deactivate_workflows.assert_awaited_once_with(FAKE_USER_ID)


class TestHandleSubscriptionOnHold:
    """Tests for _handle_subscription_on_hold."""

    async def test_sets_status_to_on_hold(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_deactivate_workflows,
    ):
        event_data = _make_webhook_event("subscription.on_hold", SUBSCRIPTION_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_hold_001")

        assert result.status == "processed"
        assert "on hold" in result.message.lower()
        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert set_data["status"] == "on_hold"

    async def test_deactivates_this_users_workflows(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_deactivate_workflows,
    ):
        event_data = _make_webhook_event("subscription.on_hold", SUBSCRIPTION_DATA_PAYLOAD)
        await webhook_service.process_webhook(event_data, "wh_hold_002")

        mock_deactivate_workflows.assert_awaited_once_with(FAKE_USER_ID)


class TestHandleSubscriptionPlanChanged:
    """Tests for _handle_subscription_plan_changed."""

    async def test_updates_product_and_amount(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
    ):
        event_data = _make_webhook_event("subscription.plan_changed", SUBSCRIPTION_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_change_001")

        assert result.status == "processed"
        assert "plan changed" in result.message.lower()
        update_call = mock_webhook_subscription_repository.apply_update_by_dodo_id.call_args
        set_data = update_call.args[1].model_dump(exclude_unset=True)
        assert set_data["product_id"] == "prod_abc123"
        assert set_data["quantity"] == 1
        assert set_data["recurring_pre_tax_amount"] == 999


# ============================================================================
# Webhook Helper Methods
# ============================================================================


class TestSendWelcomeEmail:
    """Tests for send_welcome_email_safely."""

    async def test_sends_email_when_user_found(
        self,
        mock_webhook_users_collection,
        mock_webhook_send_email,
    ):
        await send_welcome_email_safely(FAKE_USER_ID)

        mock_webhook_send_email.assert_awaited_once_with(
            user_name="Alice",
            user_email=FAKE_EMAIL,
            user_id=FAKE_USER_ID,
        )

    async def test_no_email_when_user_not_found(
        self,
        mock_webhook_users_collection,
        mock_webhook_send_email,
    ):
        _set_user(mock_webhook_users_collection, None)

        await send_welcome_email_safely(FAKE_USER_ID)

        mock_webhook_send_email.assert_not_awaited()

    async def test_no_email_when_user_has_no_email(
        self,
        mock_webhook_users_collection,
        mock_webhook_send_email,
    ):
        _set_user(mock_webhook_users_collection, {**SAMPLE_USER_DOC, "email": None})

        await send_welcome_email_safely(FAKE_USER_ID)

        mock_webhook_send_email.assert_not_awaited()

    async def test_email_error_is_swallowed(
        self,
        mock_webhook_users_collection,
        mock_webhook_send_email,
    ):
        """Email send failure is caught and logged, not propagated."""
        mock_webhook_send_email.side_effect = Exception("SMTP down")

        # Should not raise
        await send_welcome_email_safely(FAKE_USER_ID)


class TestGetUserIdFromMetadata:
    """Tests for _get_user_id_from_metadata."""

    async def test_returns_user_id_when_present(self, webhook_service):
        user_id = await webhook_service._get_user_id_from_metadata({"user_id": FAKE_USER_ID})
        assert user_id == FAKE_USER_ID

    async def test_returns_none_when_no_user_id(self, webhook_service):
        user_id = await webhook_service._get_user_id_from_metadata({})
        assert user_id is None

    async def test_stringifies_non_string_user_id(self, webhook_service):
        user_id = await webhook_service._get_user_id_from_metadata({"user_id": 12345})
        assert user_id == "12345"


# ============================================================================
# PaymentWebhookService Initialization Tests
# ============================================================================


class TestPaymentWebhookServiceInit:
    """Tests for PaymentWebhookService.__init__."""

    def test_no_secret_disables_verifier(self):
        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.DODO_WEBHOOK_PAYMENTS_SECRET = ""
            mock_settings.ENV = "development"
            svc = PaymentWebhookService()

        assert svc.webhook_verifier is None

    def test_none_secret_disables_verifier(self):
        with patch("app.services.payments.payment_webhook_service.settings") as mock_settings:
            mock_settings.DODO_WEBHOOK_PAYMENTS_SECRET = None
            mock_settings.ENV = "development"
            svc = PaymentWebhookService()

        assert svc.webhook_verifier is None

    def test_every_handler_is_for_an_event_dodo_sends_and_the_acted_on_set_is_explicit(
        self, webhook_service
    ):
        """The enum is everything Dodo can send (drift-guarded against the SDK);
        the handlers are the subset GAIA acts on. Anything else is acknowledged
        and ignored, never a processing error."""
        assert set(webhook_service.handlers) <= set(DodoWebhookEventType)
        assert set(webhook_service.handlers) == {
            DodoWebhookEventType.PAYMENT_SUCCEEDED,
            DodoWebhookEventType.PAYMENT_FAILED,
            DodoWebhookEventType.PAYMENT_PROCESSING,
            DodoWebhookEventType.PAYMENT_CANCELLED,
            DodoWebhookEventType.SUBSCRIPTION_ACTIVE,
            DodoWebhookEventType.SUBSCRIPTION_RENEWED,
            DodoWebhookEventType.SUBSCRIPTION_CANCELLED,
            DodoWebhookEventType.SUBSCRIPTION_EXPIRED,
            DodoWebhookEventType.SUBSCRIPTION_FAILED,
            DodoWebhookEventType.SUBSCRIPTION_ON_HOLD,
            DodoWebhookEventType.SUBSCRIPTION_PLAN_CHANGED,
        }


class TestWebhookAccountSync:
    """process_webhook schedules a workspace account sync for the metadata user
    after an event is processed — and only then."""

    @pytest.fixture
    def mock_schedule_sync(self):
        with patch(
            "app.services.payments.payment_webhook_service.schedule_account_sync"
        ) as mock_fn:
            yield mock_fn

    async def test_processed_event_schedules_sync_for_the_metadata_user(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_track_payment,
        mock_schedule_sync,
    ):
        event_data = _make_webhook_event("payment.succeeded", PAYMENT_DATA_PAYLOAD)

        result = await webhook_service.process_webhook(event_data, "wh_sync_001")

        assert result.status == "processed"
        # The sync must target the user named in the payload's metadata.
        mock_schedule_sync.assert_called_once_with(FAKE_USER_ID)

    async def test_failed_result_does_not_schedule_sync(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_track_payment,
        mock_schedule_sync,
    ):
        """Only processed billing changes refresh the projection — a failed
        handler must not, even when the payload carries a user id."""
        failed = DodoWebhookProcessingResult(
            event_type=DodoWebhookEventType.PAYMENT_SUCCEEDED.value,
            status="failed",
            message="handler declined",
        )
        original_handlers = webhook_service.handlers.copy()
        webhook_service.handlers[DodoWebhookEventType.PAYMENT_SUCCEEDED] = AsyncMock(
            return_value=failed
        )
        try:
            event_data = _make_webhook_event("payment.succeeded", PAYMENT_DATA_PAYLOAD)
            result = await webhook_service.process_webhook(event_data, "wh_sync_002")
        finally:
            webhook_service.handlers = original_handlers

        assert result.status == "failed"
        mock_schedule_sync.assert_not_called()

    async def test_non_string_metadata_user_id_is_never_scheduled(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_track_payment,
        mock_schedule_sync,
    ):
        payload = {**PAYMENT_DATA_PAYLOAD, "metadata": {"user_id": 12345}}
        event_data = _make_webhook_event("payment.succeeded", payload)

        result = await webhook_service.process_webhook(event_data, "wh_sync_003")

        assert result.status == "processed"
        mock_schedule_sync.assert_not_called()


# ============================================================================
# The gaps that used to close silently
# ============================================================================


class TestASilentSkipIsOnTheRecord:
    """Three lookups feed things that simply do nothing when they miss: the
    payment's analytics id, and the subscription owner behind both the
    subscription analytics and the workflow switch. A miss produced no event,
    no state change and no log — so the only visible symptom was a metric that
    looked healthy while a real payment or cancellation went unrecorded."""

    async def test_a_payment_with_no_user_id_is_not_captured_anonymously(
        self,
        webhook_service,
        mock_track_payment,
    ):
        """Attributing it to anyone else would split the user's funnel in two,
        so it is not sent — and that gap is the thing worth logging."""
        payload = {**PAYMENT_DATA_PAYLOAD, "metadata": {}}
        event = DodoWebhookEvent(**_make_webhook_event("payment.succeeded", payload))

        async with captured_wide_event() as wide:
            result = await webhook_service._handle_payment_succeeded(event)

        assert result.status == "processed"
        mock_track_payment.assert_not_called()
        assert wide["warnings"] == [
            {
                "msg": f"{LogTag.PAYMENT} Payment carries no GAIA user id; analytics not captured",
                "failure_reason": "unattributable_payment",
                "analytics_event": AnalyticsEvents.PAYMENT_SUCCEEDED.value,
                "payment_id": PAYMENT_DATA_PAYLOAD["payment_id"],
            }
        ]

    async def test_a_mirrored_subscription_with_no_owner_is_on_the_record(
        self,
        webhook_service,
        mock_webhook_subscription_repository,
        mock_deactivate_workflows,
    ):
        """The row matched moments earlier, so a missing owner is a subscription
        nobody can be billed for — and the workflows it should have switched off
        keep running."""
        mock_webhook_subscription_repository.get_user_id_by_dodo_id = AsyncMock(return_value=None)
        event = DodoWebhookEvent(
            **_make_webhook_event("subscription.expired", SUBSCRIPTION_DATA_PAYLOAD)
        )

        async with captured_wide_event() as wide:
            result = await webhook_service._handle_subscription_expired(event)

        assert result.status == "processed"
        mock_deactivate_workflows.assert_not_awaited()
        assert wide["errors"] == [
            {
                "msg": f"{LogTag.PAYMENT} Mirrored subscription has no owner; "
                "analytics and workflow changes skipped",
                "failure_reason": "subscription_owner_missing",
                "event_type": "subscription.expired",
                "subscription_id": SUBSCRIPTION_DATA_PAYLOAD["subscription_id"],
            }
        ]


# ============================================================================
# A failed handler is a state change still owed
# ============================================================================


class TestAFailedHandlerReleasesItsClaim:
    """The bug: ``record_outcome`` is an update, so a handler that *returned*
    ``failed`` (rather than raising) kept its webhook-id claim while the
    endpoint answered 200. Dodo does not resend a 200, and a manual redelivery
    of the same id is turned away at the claim — so a ``subscription.active``
    whose owner could not be resolved meant a user who paid was never
    activated, with no way left to re-drive the event."""

    async def test_an_ownerless_activation_hands_the_claim_back(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_webhook_users_collection,
        mock_payment_service_invalidation,
    ):
        mock_webhook_users_collection.get_by_email = AsyncMock(return_value=None)
        payload = {**SUBSCRIPTION_DATA_PAYLOAD, "metadata": {}}
        event_data = _make_webhook_event("subscription.active", payload)

        result = await webhook_service.process_webhook(event_data, "wh_active_ownerless")

        assert result.status == "failed"
        mock_processed_webhook_repository.release.assert_awaited_once_with("wh_active_ownerless")
        mock_processed_webhook_repository.record_outcome.assert_not_awaited()

    @pytest.mark.parametrize(
        "event_type",
        [
            "subscription.renewed",
            "subscription.cancelled",
            "subscription.expired",
            "subscription.failed",
            "subscription.on_hold",
        ],
    )
    async def test_a_state_change_with_no_local_row_hands_the_claim_back(
        self,
        event_type: str,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_subscription_repository,
        mock_deactivate_workflows,
        webhook_side_effects_stubbed,
    ):
        """No row matched means Dodo's state was never mirrored. The row may
        still be on its way — ``subscription.active`` is a separate delivery
        with its own retries — so acknowledging drops the change for good and
        leaves the user on a tier they no longer have."""
        mock_webhook_subscription_repository.apply_update_by_dodo_id = AsyncMock(return_value=False)
        event_data = _make_webhook_event(event_type, SUBSCRIPTION_DATA_PAYLOAD)

        result = await webhook_service.process_webhook(event_data, f"wh_{event_type}_unmatched")

        assert result.status == "failed"
        mock_processed_webhook_repository.release.assert_awaited_once_with(
            f"wh_{event_type}_unmatched"
        )
        mock_processed_webhook_repository.record_outcome.assert_not_awaited()
        mock_deactivate_workflows.assert_not_awaited()


# ============================================================================
# process_webhook customer_id extraction
# ============================================================================


class TestProcessWebhookCustomerIdExtraction:
    """Verify customer_id is correctly extracted from nested and flat payloads."""

    async def test_extracts_customer_id_from_nested_customer_dict(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_users_collection,
        mock_track_payment,
    ):
        """customer_id is extracted from data.customer.customer_id."""
        event_data = _make_webhook_event("payment.succeeded", PAYMENT_DATA_PAYLOAD)
        result = await webhook_service.process_webhook(event_data, "wh_cid_001")

        assert result.status == "processed"

    async def test_extracts_customer_id_from_flat_payload(
        self,
        webhook_service,
        mock_processed_webhook_repository,
        mock_webhook_users_collection,
        mock_track_payment,
    ):
        """Falls back to data.customer_id when customer is not a dict."""
        payload = {
            **PAYMENT_DATA_PAYLOAD,
            "customer_id": "flat_cust_001",
        }
        # Replace customer with a non-dict to trigger fallback
        payload["customer"] = {
            "customer_id": "cust_001",
            "email": FAKE_EMAIL,
            "name": "Alice",
        }
        event_data = _make_webhook_event("payment.succeeded", payload)
        result = await webhook_service.process_webhook(event_data, "wh_cid_002")

        assert result.status == "processed"
