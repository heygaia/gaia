"""
Clean payment webhook service for Dodo Payments integration.
Handles webhook events and updates database state accordingly.
"""

from typing import Any

from standardwebhooks.webhooks import Webhook

from app.config.settings import settings
from app.constants.log_tags import LogTag
from app.db.repositories.processed_webhooks import processed_webhook_repository
from app.db.repositories.subscriptions import subscription_repository
from app.models.payment_models import ProcessedWebhookUpdate, SubscriptionUpdate
from app.models.webhook_models import (
    DodoPaymentData,
    DodoSubscriptionData,
    DodoWebhookEvent,
    DodoWebhookEventType,
    DodoWebhookProcessingResult,
    WebhookProcessingStatus,
)
from app.services.account_fs import schedule_account_sync
from app.services.analytics_service import (
    AnalyticsEvents,
    SubscriptionPlan,
    track_payment_event,
    track_subscription_event,
)
from app.services.payments.payment_service import payment_service
from app.services.payments.subscription_activation import (
    CENTS_PER_UNIT,
    activate_subscription,
    reactivate_workflows_safely,
)
from app.services.workflow.subscription_pause import (
    deactivate_workflows_for_lapsed_subscription,
)
from shared.py.wide_events import log


def _outcome_of(result: DodoWebhookProcessingResult) -> ProcessedWebhookUpdate:
    return ProcessedWebhookUpdate(
        status=result.status,
        message=result.message,
        payment_id=result.payment_id,
        subscription_id=result.subscription_id,
    )


class PaymentWebhookService:
    """Clean service for handling Dodo payment webhooks."""

    def __init__(self) -> None:
        self.webhook_secret = settings.DODO_WEBHOOK_PAYMENTS_SECRET
        # Initialize Standard Webhooks verifier
        if self.webhook_secret:
            try:
                # The secret should be base64 encoded for Standard Webhooks
                self.webhook_verifier = Webhook(self.webhook_secret)
            except Exception as e:
                log.error(
                    f"{LogTag.PAYMENT} Failed to initialize webhook verifier",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                self.webhook_verifier = None
        else:
            self.webhook_verifier = None

        self.handlers = {
            DodoWebhookEventType.PAYMENT_SUCCEEDED: self._handle_payment_succeeded,
            DodoWebhookEventType.PAYMENT_FAILED: self._handle_payment_failed,
            DodoWebhookEventType.PAYMENT_PROCESSING: self._handle_payment_processing,
            DodoWebhookEventType.PAYMENT_CANCELLED: self._handle_payment_cancelled,
            DodoWebhookEventType.SUBSCRIPTION_ACTIVE: self._handle_subscription_active,
            DodoWebhookEventType.SUBSCRIPTION_RENEWED: self._handle_subscription_renewed,
            DodoWebhookEventType.SUBSCRIPTION_CANCELLED: self._handle_subscription_cancelled,
            DodoWebhookEventType.SUBSCRIPTION_EXPIRED: self._handle_subscription_expired,
            DodoWebhookEventType.SUBSCRIPTION_FAILED: self._handle_subscription_failed,
            DodoWebhookEventType.SUBSCRIPTION_ON_HOLD: self._handle_subscription_on_hold,
            DodoWebhookEventType.SUBSCRIPTION_PLAN_CHANGED: self._handle_subscription_plan_changed,
        }

    def verify_webhook_signature(self, payload: str, headers: dict[str, str]) -> bool:
        """
        Verify webhook signature using Standard Webhooks library.

        Args:
            payload: The raw JSON payload as string
            headers: Dictionary of headers from the webhook request
        """
        if not self.webhook_verifier:
            log.error(f"{LogTag.PAYMENT} No webhook verifier configured - rejecting webhook")
            return False

        try:
            log.info(
                f"{LogTag.PAYMENT} Verifying webhook signature using Standard Webhooks library"
            )

            # The Standard Webhooks library expects headers in the correct format
            # Convert headers to the expected format (lowercase with dashes)
            webhook_headers = {}
            for key, value in headers.items():
                # Convert header names to the expected format
                if key.lower() == "webhook-id":
                    webhook_headers["webhook-id"] = value
                elif key.lower() == "webhook-timestamp":
                    webhook_headers["webhook-timestamp"] = value
                elif key.lower() == "webhook-signature":
                    webhook_headers["webhook-signature"] = value

            # Verify using Standard Webhooks library
            self.webhook_verifier.verify(payload.encode("utf-8"), webhook_headers)

            log.info(f"{LogTag.PAYMENT} Webhook signature verification successful!")
            return True

        except Exception as e:
            log.warning(
                f"{LogTag.PAYMENT} Webhook signature verification failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    async def process_webhook(
        self, webhook_data: dict[str, Any], webhook_id: str
    ) -> DodoWebhookProcessingResult:
        """
        Process a Dodo payment webhook exactly once.

        The delivery is claimed (inserted under the unique ``webhook_id``)
        before its handler runs, so a replay or a racing duplicate is turned
        away at the claim, never after the side effects. A handler failure —
        raised or returned — releases the claim so Dodo's retry is a clean run;
        only a processed or ignored delivery keeps it.

        Args:
            webhook_data: The webhook payload
            webhook_id: Unique webhook ID from webhook-id header for idempotency

        Returns:
            Processing result
        """
        event_type_raw = str(webhook_data.get("type", "unknown"))
        if not await processed_webhook_repository.claim(webhook_id, event_type=event_type_raw):
            log.info(f"{LogTag.PAYMENT} Webhook already processed, skipping", webhook_id=webhook_id)
            return DodoWebhookProcessingResult(
                event_type=event_type_raw,
                status=WebhookProcessingStatus.IGNORED,
                message="Webhook already processed",
            )
        try:
            # Extract financial fields from the nested payload (Dodo wraps data under "data")
            payload_data: dict[str, Any] = webhook_data.get("data", webhook_data)
            customer_field = payload_data.get("customer")
            customer_id = (
                customer_field.get("customer_id")
                if isinstance(customer_field, dict)
                else payload_data.get("customer_id")
            )
            log.set(
                payment={
                    "event_type": event_type_raw,
                    "status": "processing",
                    "webhook_id": webhook_id,
                    "customer_id": customer_id,
                    "amount_cents": payload_data.get("amount")
                    or payload_data.get("amount_paid")
                    or payload_data.get("total_amount", 0),
                    "currency": payload_data.get("currency", "usd"),
                }
            )

            event = DodoWebhookEvent(**webhook_data)

            handler = self.handlers.get(event.type)
            if not handler:
                result = DodoWebhookProcessingResult(
                    event_type=event.type.value,
                    status=WebhookProcessingStatus.IGNORED,
                    message=f"No handler for {event.type}",
                )
                # The claim already blocks a replay; the outcome is for the record.
                await processed_webhook_repository.record_outcome(webhook_id, _outcome_of(result))
                return result

            result = await handler(event)
            log.info(f"{LogTag.PAYMENT} Webhook processed", type=event.type, status=result.status)

            if result.status == WebhookProcessingStatus.FAILED:
                # The handler ran and the state change still did not land, so
                # this delivery is unfinished. Recording the outcome would keep
                # the claim and the endpoint would answer 200 — between them
                # that ends the event's life: Dodo stops resending and a manual
                # redelivery is refused as a replay. Hand the claim back and let
                # the endpoint ask for a retry.
                log.error(
                    f"{LogTag.PAYMENT} Webhook handler did not complete; releasing the claim",
                    webhook_id=webhook_id,
                    event_type=event.type.value,
                    failure_reason=result.message,
                )
                await processed_webhook_repository.release(webhook_id)
                return result

            # Bust the cached plan tier so a plan change applies immediately.
            if result.subscription_id:
                await payment_service.invalidate_plan_cache_by_dodo_id(result.subscription_id)

            # Keep the workspace's account/subscription projection honest after
            # any billing state change.
            if result.status == WebhookProcessingStatus.PROCESSED:
                metadata = payload_data.get("metadata")
                webhook_user_id = metadata.get("user_id") if isinstance(metadata, dict) else None
                if isinstance(webhook_user_id, str) and webhook_user_id:
                    schedule_account_sync(webhook_user_id)

            await processed_webhook_repository.record_outcome(webhook_id, _outcome_of(result))
            return result

        except Exception as e:
            log.error(
                f"{LogTag.PAYMENT} Webhook processing failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            await processed_webhook_repository.release(webhook_id)
            return DodoWebhookProcessingResult(
                event_type=event_type_raw,
                status=WebhookProcessingStatus.FAILED,
                message=f"Processing error: {e!s}",
            )

    async def _get_user_id_from_metadata(self, metadata: dict[str, Any]) -> str | None:
        """Get the stable application user ID from payment metadata."""
        user_id = metadata.get("user_id")
        return str(user_id) if user_id else None

    async def _capture_payment(
        self, event_type: AnalyticsEvents, payment_data: DodoPaymentData
    ) -> None:
        """Capture a payment against the GAIA user who made it.

        A webhook has no authenticated request for the context to inherit, so
        the id has to come off the payment's own metadata. Without one the event
        would land on an anonymous profile and quietly split that person's
        funnel in two, so it is not sent at all — and the gap is logged, because
        a real payment with no event behind it is invisible in PostHog by
        definition.
        """
        user_id = await self._get_user_id_from_metadata(payment_data.metadata)
        if not user_id:
            log.warning(
                f"{LogTag.PAYMENT} Payment carries no GAIA user id; analytics not captured",
                failure_reason="unattributable_payment",
                analytics_event=event_type.value,
                payment_id=payment_data.payment_id,
            )
            return

        track_payment_event(
            user_id=user_id,
            event_type=event_type,
            payment_id=payment_data.payment_id,
            amount=payment_data.total_amount / CENTS_PER_UNIT
            if payment_data.total_amount
            else None,
            currency=payment_data.currency,
        )

    # Payment event handlers
    async def _handle_payment_succeeded(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle successful payment - just log, subscription activation handles the rest."""
        payment_data = event.get_payment_data()
        if not payment_data:
            raise ValueError("Invalid payment data")

        log.info(f"{LogTag.PAYMENT} Payment succeeded", payment_id=payment_data.payment_id)

        await self._capture_payment(AnalyticsEvents.PAYMENT_SUCCEEDED, payment_data)

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Payment success logged",
            payment_id=payment_data.payment_id,
            subscription_id=payment_data.subscription_id,
        )

    async def _handle_payment_failed(self, event: DodoWebhookEvent) -> DodoWebhookProcessingResult:
        """Handle failed payment."""
        payment_data = event.get_payment_data()
        if not payment_data:
            raise ValueError("Invalid payment data")

        log.warning(f"{LogTag.PAYMENT} Payment failed", payment_id=payment_data.payment_id)

        await self._capture_payment(AnalyticsEvents.PAYMENT_FAILED, payment_data)

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Payment failure logged",
            payment_id=payment_data.payment_id,
            subscription_id=payment_data.subscription_id,
        )

    async def _handle_payment_processing(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle payment processing status."""
        payment_data = event.get_payment_data()
        if not payment_data:
            raise ValueError("Invalid payment data")

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Payment processing noted",
            payment_id=payment_data.payment_id,
            subscription_id=payment_data.subscription_id,
        )

    async def _handle_payment_cancelled(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle cancelled payment."""
        payment_data = event.get_payment_data()
        if not payment_data:
            raise ValueError("Invalid payment data")

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Payment cancellation noted",
            payment_id=payment_data.payment_id,
            subscription_id=payment_data.subscription_id,
        )

    # Subscription event handlers
    async def _handle_subscription_active(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle subscription activation - CREATE subscription record here."""
        sub_data = event.get_subscription_data()
        if not sub_data:
            raise ValueError("Invalid subscription data")

        activation = await activate_subscription(sub_data)
        if activation.user_id is None:
            return DodoWebhookProcessingResult(
                event_type=event.type.value,
                status=WebhookProcessingStatus.FAILED,
                message="User not found",
                subscription_id=sub_data.subscription_id,
            )

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Subscription activated"
            if activation.created
            else "Subscription already active",
            subscription_id=sub_data.subscription_id,
        )

    async def _handle_subscription_renewed(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle subscription renewal."""
        sub_data = event.get_subscription_data()
        if not sub_data:
            raise ValueError("Invalid subscription data")

        # Set each billing date only when the event carries one. Passing it
        # marks the field in model_fields_set even when None, and the repository
        # applies model_dump(exclude_unset=True) as $set — so an event that omits
        # a date would otherwise write null over the stored value.
        update = SubscriptionUpdate(status="active")
        if sub_data.next_billing_date is not None:
            update.next_billing_date = sub_data.next_billing_date
        if sub_data.previous_billing_date is not None:
            update.previous_billing_date = sub_data.previous_billing_date

        unmirrored = await self._mirror_subscription_state(event, sub_data, update)
        if unmirrored:
            return unmirrored

        # Track subscription renewal in PostHog
        user_id = await self._owner_of_subscription(event, sub_data.subscription_id)
        if user_id:
            track_subscription_event(
                user_id=user_id,
                event_type=AnalyticsEvents.SUBSCRIPTION_RENEWED,
                subscription_id=sub_data.subscription_id,
                plan=SubscriptionPlan(currency=sub_data.currency),
            )
            await reactivate_workflows_safely(user_id)

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Subscription renewed",
            subscription_id=sub_data.subscription_id,
        )

    async def _handle_subscription_cancelled(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle subscription cancellation."""
        sub_data = event.get_subscription_data()
        if not sub_data:
            raise ValueError("Invalid subscription data")

        # A cancel scheduled for the end of the billing period
        # (cancel_at_next_billing_date=True) keeps the subscription active —
        # and the user on Pro — until the period ends. Status is deliberately
        # left untouched in that case: Dodo's documented payload for a
        # scheduled cancel reports status "active", but trusting the payload's
        # status would downgrade the user early if a future Dodo change ever
        # reported "cancelled" there. Only the `subscription.expired` event
        # flips status. An immediate cancellation (flag false) sets it now.
        update = SubscriptionUpdate(
            cancel_at_next_billing_date=sub_data.cancel_at_next_billing_date
        )
        if not sub_data.cancel_at_next_billing_date:
            update.status = "cancelled"
        # cancelled_at is only set when Dodo supplied one — leaving it unset keeps
        # it out of the $set rather than writing null over a stored value.
        if sub_data.cancelled_at:
            update.cancelled_at = sub_data.cancelled_at

        unmirrored = await self._mirror_subscription_state(event, sub_data, update)
        if unmirrored:
            return unmirrored

        # Track subscription cancellation in PostHog
        user_id = await self._owner_of_subscription(event, sub_data.subscription_id)
        if user_id:
            track_subscription_event(
                user_id=user_id,
                event_type=AnalyticsEvents.SUBSCRIPTION_CANCELLED,
                subscription_id=sub_data.subscription_id,
                properties={
                    "product_id": sub_data.product_id,
                    "billing_interval": sub_data.payment_frequency_interval,
                },
            )
            # Only an immediate cancellation actually drops the user from Pro now —
            # a cancel scheduled for period end (status left untouched above) keeps
            # them paid until `subscription.expired` fires, so their workflows stay on.
            if not sub_data.cancel_at_next_billing_date:
                await self._deactivate_workflows_for_lapsed_subscription(user_id)

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Subscription cancelled",
            subscription_id=sub_data.subscription_id,
        )

    async def _handle_subscription_expired(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle subscription expiration."""
        sub_data = event.get_subscription_data()
        if not sub_data:
            raise ValueError("Invalid subscription data")

        unmirrored = await self._mirror_subscription_state(
            event, sub_data, SubscriptionUpdate(status="expired")
        )
        if unmirrored:
            return unmirrored

        # Track subscription expiration in PostHog
        user_id = await self._owner_of_subscription(event, sub_data.subscription_id)
        if user_id:
            track_subscription_event(
                user_id=user_id,
                event_type=AnalyticsEvents.SUBSCRIPTION_EXPIRED,
                subscription_id=sub_data.subscription_id,
            )
            await self._deactivate_workflows_for_lapsed_subscription(user_id)

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Subscription expired",
            subscription_id=sub_data.subscription_id,
        )

    async def _handle_subscription_failed(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle subscription failure."""
        sub_data = event.get_subscription_data()
        if not sub_data:
            raise ValueError("Invalid subscription data")

        unmirrored = await self._mirror_subscription_state(
            event, sub_data, SubscriptionUpdate(status="failed")
        )
        if unmirrored:
            return unmirrored

        user_id = await self._owner_of_subscription(event, sub_data.subscription_id)
        if user_id:
            await self._deactivate_workflows_for_lapsed_subscription(user_id)

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Subscription failed",
            subscription_id=sub_data.subscription_id,
        )

    async def _handle_subscription_on_hold(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle subscription on hold."""
        sub_data = event.get_subscription_data()
        if not sub_data:
            raise ValueError("Invalid subscription data")

        unmirrored = await self._mirror_subscription_state(
            event, sub_data, SubscriptionUpdate(status="on_hold")
        )
        if unmirrored:
            return unmirrored

        user_id = await self._owner_of_subscription(event, sub_data.subscription_id)
        if user_id:
            await self._deactivate_workflows_for_lapsed_subscription(user_id)

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Subscription on hold",
            subscription_id=sub_data.subscription_id,
        )

    async def _handle_subscription_plan_changed(
        self, event: DodoWebhookEvent
    ) -> DodoWebhookProcessingResult:
        """Handle subscription plan change."""
        sub_data = event.get_subscription_data()
        if not sub_data:
            raise ValueError("Invalid subscription data")

        unmirrored = await self._mirror_subscription_state(
            event,
            sub_data,
            SubscriptionUpdate(
                product_id=sub_data.product_id,
                quantity=sub_data.quantity,
                recurring_pre_tax_amount=sub_data.recurring_pre_tax_amount,
            ),
        )
        if unmirrored:
            return unmirrored

        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.PROCESSED,
            message="Subscription plan changed",
            subscription_id=sub_data.subscription_id,
        )

    async def _owner_of_subscription(
        self, event: DodoWebhookEvent, subscription_id: str
    ) -> str | None:
        """The GAIA user behind a subscription row that was just mirrored.

        A miss is not routine here: the row matched moments ago, so no owner
        means a subscription nobody can be billed for. Both things hanging off
        this id — the analytics event and the workflow switch — do nothing at
        all when it is missing, which is how a cancelled subscription leaves its
        automations running with no trace of why.
        """
        user_id = await subscription_repository.get_user_id_by_dodo_id(subscription_id)
        if not user_id:
            log.error(
                f"{LogTag.PAYMENT} Mirrored subscription has no owner; "
                "analytics and workflow changes skipped",
                failure_reason="subscription_owner_missing",
                event_type=event.type.value,
                subscription_id=subscription_id,
            )
        return user_id

    async def _mirror_subscription_state(
        self,
        event: DodoWebhookEvent,
        sub_data: DodoSubscriptionData,
        update: SubscriptionUpdate,
    ) -> DodoWebhookProcessingResult | None:
        """Apply Dodo's state to the local row; ``None`` once it is mirrored.

        A miss is returned as a failure rather than logged and shrugged off:
        the row may still be on its way — ``subscription.active`` is a separate
        delivery with its own retries — and reporting a state change that never
        landed leaves the user on a tier Dodo says they no longer have.
        """
        if await subscription_repository.apply_update_by_dodo_id(sub_data.subscription_id, update):
            return None

        log.error(
            f"{LogTag.PAYMENT} No local subscription matched the Dodo id",
            event_type=event.type.value,
            subscription_id=sub_data.subscription_id,
        )
        return DodoWebhookProcessingResult(
            event_type=event.type.value,
            status=WebhookProcessingStatus.FAILED,
            message="Subscription not found",
            subscription_id=sub_data.subscription_id,
        )

    async def _deactivate_workflows_for_lapsed_subscription(self, user_id: str) -> None:
        """Turn off this user's automation once they're no longer paid. Never raises —
        a workflow-deactivation failure must not turn an otherwise-successful billing
        webhook into a "failed" result that Dodo would retry."""
        try:
            await deactivate_workflows_for_lapsed_subscription(user_id)
        except Exception as e:
            log.error(
                f"{LogTag.PAYMENT} Failed to deactivate workflows for lapsed subscription",
                error=str(e),
                error_type=type(e).__name__,
                user_id=user_id,
            )


# Single instance
payment_webhook_service = PaymentWebhookService()
