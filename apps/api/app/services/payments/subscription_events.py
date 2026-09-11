"""The one writer of a subscription's local state.

Every source of a billing change — the Dodo subscription webhooks, the user's
own cancel request, payment verification reconciling against Dodo when the
webhook never landed — is reduced to a ``SubscriptionEvent`` and applied here.
Nothing else writes ``status``, the billing dates, the plan-cache drop, the
``subscription:*`` analytics or the workflow pause/resume: three call sites
each doing their own version is how a recovered subscription was left
lapsed, a scheduled cancel downgraded a user early on one path and not the
other, and a replayed webhook counted an activation twice.

The rules, in order: an event older than the row's last applied one is
stale and ignored; an event that changes nothing writes nothing and captures
nothing; what did change decides the side effects — a status crossing into
``active`` restores the workflows, a status leaving it pauses them, and each
analytics event fires exactly once for the transition it names.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from app.constants.log_tags import LogTag
from app.db.repositories.subscriptions import subscription_repository
from app.db.repositories.users import user_repository
from app.models.payment_models import (
    SubscriptionDocument,
    SubscriptionStatus,
    SubscriptionUpdate,
)
from app.models.webhook_models import DodoSubscriptionData
from app.services.analytics_service import (
    AnalyticsEvents,
    SubscriptionPlan,
    track_subscription_event,
)
from app.services.email import send_pro_subscription_email
from app.services.payments.plan_cache import invalidate_plan_cache
from app.utils.timezone import as_utc
from shared.py.wide_events import log

CENTS_PER_UNIT = 100
EVENT_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

LAPSED_STATUSES = frozenset(
    {
        SubscriptionStatus.ON_HOLD.value,
        SubscriptionStatus.FAILED.value,
        SubscriptionStatus.EXPIRED.value,
        SubscriptionStatus.CANCELLED.value,
    }
)


class SubscriptionEventKind(StrEnum):
    """What the source says happened to the subscription."""

    ACTIVATED = "activated"
    RENEWED = "renewed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"
    ON_HOLD = "on_hold"
    PLAN_CHANGED = "plan_changed"


@dataclass(frozen=True)
class SubscriptionEvent:
    """One reported change. ``occurred_at`` is the source's clock (Dodo's
    event timestamp, or the moment Dodo answered a direct call), which is what
    orders it against the row."""

    kind: SubscriptionEventKind
    occurred_at: datetime
    data: DodoSubscriptionData


class SubscriptionEventOutcome(StrEnum):
    """What applying the event did — the caller maps this to its own reply."""

    CREATED = "created"
    APPLIED = "applied"
    UNCHANGED = "unchanged"
    STALE = "stale"
    NO_ROW = "no_row"
    NO_OWNER = "no_owner"


@dataclass(frozen=True)
class SubscriptionEventResult:
    """``user_id`` is None exactly when nothing was written for nobody."""

    outcome: SubscriptionEventOutcome
    user_id: str | None


async def reactivate_workflows_safely(user_id: str) -> None:
    """Turn a user's paused automation back on once they're paid again. Never
    raises — a workflow-reactivation failure must not turn an otherwise-successful
    billing webhook into a "failed" result that Dodo would retry."""
    # Deferred import: breaks a circular dependency. `app.decorators.entitlements`
    # imports `payment_service`, which imports this module; a top-level import of
    # `subscription_pause` would drag the whole workflow/triggers/composio stack
    # into that chain, and it reaches back into `app.decorators`.
    from app.services.workflow.subscription_pause import (  # noqa: PLC0415  # real cycle through app.decorators, see above
        reactivate_workflows_for_restored_subscription,
    )

    try:
        await reactivate_workflows_for_restored_subscription(user_id)
    except Exception as e:
        log.error(
            f"{LogTag.PAYMENT} Failed to reactivate workflows for restored subscription",
            error=str(e),
            error_type=type(e).__name__,
            user_id=user_id,
        )


async def deactivate_workflows_safely(user_id: str) -> None:
    """Turn off this user's automation once they're no longer paid. Never
    raises — see ``reactivate_workflows_safely``."""
    from app.services.workflow.subscription_pause import (  # noqa: PLC0415  # real cycle through app.decorators, see reactivate_workflows_safely
        deactivate_workflows_for_lapsed_subscription,
    )

    try:
        await deactivate_workflows_for_lapsed_subscription(user_id)
    except Exception as e:
        log.error(
            f"{LogTag.PAYMENT} Failed to deactivate workflows for lapsed subscription",
            error=str(e),
            error_type=type(e).__name__,
            user_id=user_id,
        )


async def send_welcome_email_safely(user_id: str) -> None:
    """Welcome the new subscriber. Never raises — see ``reactivate_workflows_safely``."""
    try:
        user = await user_repository.get(user_id)
        if user and user.email:
            await send_pro_subscription_email(
                user_name=user.first_name or "User",
                user_email=user.email,
                user_id=user_id,
            )
            # The address is what was mailed, not what is logged: a log line
            # carries ids, counts and enums, never the PII itself.
            log.info(f"{LogTag.PAYMENT} Welcome email sent", user_id=user_id)
    except Exception as e:
        log.error(
            f"{LogTag.PAYMENT} Failed to send welcome email",
            error=str(e),
            error_type=type(e).__name__,
            user_id=user_id,
        )


async def resolve_subscription_owner(sub_data: DodoSubscriptionData) -> str | None:
    """The GAIA user this subscription belongs to.

    Checkout stamps the user id into metadata; the customer email is the
    fallback for sessions minted before that (or created in Dodo's dashboard).
    Callers acting on a client-supplied subscription id must compare this
    against the authenticated user before activating anything.
    """
    metadata_user_id = sub_data.metadata.get("user_id")
    if metadata_user_id:
        return str(metadata_user_id)

    user = await user_repository.get_by_email(sub_data.customer.email)
    return str(user.id) if user else None


def _active_state(data: DodoSubscriptionData) -> SubscriptionUpdate:
    """Active with the billing dates the event carries.

    A date is set only when the event carries it: the repository writes
    ``exclude_unset`` as ``$set``, so a date the event omits must stay out of
    the update rather than write null over the stored value.
    """
    desired = SubscriptionUpdate(status=SubscriptionStatus.ACTIVE.value)
    if data.next_billing_date is not None:
        desired.next_billing_date = data.next_billing_date
    if data.previous_billing_date is not None:
        desired.previous_billing_date = data.previous_billing_date
    return desired


def _cancelled_state(data: DodoSubscriptionData) -> SubscriptionUpdate:
    """A cancel scheduled for period end keeps the user on Pro until
    ``subscription.expired``; only an immediate cancel drops the status now.
    The payload's own status is never trusted here — a scheduled cancel
    reporting "cancelled" would downgrade early."""
    desired = SubscriptionUpdate(cancel_at_next_billing_date=data.cancel_at_next_billing_date)
    if not data.cancel_at_next_billing_date:
        desired.status = SubscriptionStatus.CANCELLED.value
    if data.cancelled_at:
        desired.cancelled_at = data.cancelled_at
    if data.next_billing_date is not None:
        desired.next_billing_date = data.next_billing_date
    return desired


def _status_state(
    status: SubscriptionStatus,
) -> Callable[[DodoSubscriptionData], SubscriptionUpdate]:
    return lambda _data: SubscriptionUpdate(status=status.value)


def _plan_changed_state(data: DodoSubscriptionData) -> SubscriptionUpdate:
    return SubscriptionUpdate(
        product_id=data.product_id,
        quantity=data.quantity,
        recurring_pre_tax_amount=data.recurring_pre_tax_amount,
    )


# What each event kind says the row should now have.
DESIRED_STATE: dict[SubscriptionEventKind, Callable[[DodoSubscriptionData], SubscriptionUpdate]] = {
    SubscriptionEventKind.ACTIVATED: _active_state,
    SubscriptionEventKind.RENEWED: _active_state,
    SubscriptionEventKind.CANCELLED: _cancelled_state,
    SubscriptionEventKind.EXPIRED: _status_state(SubscriptionStatus.EXPIRED),
    SubscriptionEventKind.FAILED: _status_state(SubscriptionStatus.FAILED),
    SubscriptionEventKind.ON_HOLD: _status_state(SubscriptionStatus.ON_HOLD),
    SubscriptionEventKind.PLAN_CHANGED: _plan_changed_state,
}


def _changes(row: SubscriptionDocument, desired: SubscriptionUpdate) -> dict[str, object]:
    """The desired fields whose value differs from the row's."""
    return {
        field: value
        for field, value in desired.model_dump(exclude_unset=True).items()
        if getattr(row, field) != value
    }


def _is_stale(row: SubscriptionDocument, event: SubscriptionEvent) -> bool:
    # Mongo hands datetimes back naive; the event's is aware (Dodo sends "Z").
    last_event_at = as_utc(row.last_event_at)
    return last_event_at is not None and event.occurred_at < last_event_at


def _plan_of(data: DodoSubscriptionData) -> SubscriptionPlan:
    return SubscriptionPlan(
        name="Pro",
        amount=data.recurring_pre_tax_amount / CENTS_PER_UNIT
        if data.recurring_pre_tax_amount
        else None,
        currency=data.currency,
    )


def _capture_transition(
    event: SubscriptionEvent,
    user_id: str,
    changes: dict[str, object],
    became_active: bool,
) -> None:
    """Fire the one analytics event this transition names, if it names one.

    Keyed on what changed, not on the event arriving: a replay changes nothing
    and fires nothing, and a cancel recorded first by the user's own request
    is not counted again when Dodo's webhook reports the same flag.
    """
    data = event.data
    match event.kind:
        case SubscriptionEventKind.ACTIVATED if became_active:
            track_subscription_event(
                user_id=user_id,
                event_type=AnalyticsEvents.SUBSCRIPTION_ACTIVATED,
                subscription_id=data.subscription_id,
                plan=_plan_of(data),
            )
        case SubscriptionEventKind.RENEWED:
            track_subscription_event(
                user_id=user_id,
                event_type=AnalyticsEvents.SUBSCRIPTION_RENEWED,
                subscription_id=data.subscription_id,
                plan=SubscriptionPlan(currency=data.currency),
            )
        case SubscriptionEventKind.CANCELLED if (
            changes.get("cancel_at_next_billing_date") is True
            or changes.get("status") == SubscriptionStatus.CANCELLED.value
        ):
            track_subscription_event(
                user_id=user_id,
                event_type=AnalyticsEvents.SUBSCRIPTION_CANCELLED,
                subscription_id=data.subscription_id,
                properties={
                    "product_id": data.product_id,
                    "billing_interval": data.payment_frequency_interval,
                },
            )
        case SubscriptionEventKind.EXPIRED if "status" in changes:
            track_subscription_event(
                user_id=user_id,
                event_type=AnalyticsEvents.SUBSCRIPTION_EXPIRED,
                subscription_id=data.subscription_id,
            )
        case _:
            return


async def _create_row(event: SubscriptionEvent) -> SubscriptionEventResult:
    data = event.data
    user_id = await resolve_subscription_owner(data)
    if not user_id:
        log.error(
            f"{LogTag.PAYMENT} User not found for subscription",
            subscription_id=data.subscription_id,
        )
        return SubscriptionEventResult(SubscriptionEventOutcome.NO_OWNER, None)

    now = datetime.now(UTC)
    # Built as a dict, not keyword construction: SubscriptionDocument declares
    # only the fields GAIA reads and keeps Dodo's remaining billing fields via
    # ``extra="allow"``, which model_validate preserves and kwargs would reject.
    await subscription_repository.create(
        SubscriptionDocument.model_validate(
            {
                "dodo_subscription_id": data.subscription_id,
                "user_id": user_id,
                "product_id": data.product_id,
                "status": SubscriptionStatus.ACTIVE.value,
                "quantity": data.quantity,
                "currency": data.currency,
                "recurring_pre_tax_amount": data.recurring_pre_tax_amount,
                "payment_frequency_count": data.payment_frequency_count,
                "payment_frequency_interval": data.payment_frequency_interval,
                "subscription_period_count": data.subscription_period_count,
                "subscription_period_interval": data.subscription_period_interval,
                "next_billing_date": data.next_billing_date,
                "previous_billing_date": data.previous_billing_date,
                "last_event_at": event.occurred_at,
                "created_at": now,
                "updated_at": now,
                "metadata": data.metadata,
            }
        )
    )

    _capture_transition(event, user_id, changes={}, became_active=True)
    await invalidate_plan_cache(user_id)
    await send_welcome_email_safely(user_id)
    await reactivate_workflows_safely(user_id)

    log.info(f"{LogTag.PAYMENT} Subscription activated", subscription_id=data.subscription_id)
    return SubscriptionEventResult(SubscriptionEventOutcome.CREATED, user_id)


async def apply_subscription_event(event: SubscriptionEvent) -> SubscriptionEventResult:
    """Bring the local row in line with ``event`` and fire what the change owes.

    Only an ``ACTIVATED`` event may create a row — it is the one that carries a
    subscription GAIA has not seen. Every other kind needs the row to exist,
    and answers ``NO_ROW`` when it does not, so the caller can decide whether
    the activation may still be on its way.
    """
    data = event.data
    row = await subscription_repository.get_by_dodo_id(data.subscription_id)
    if row is None:
        if event.kind is SubscriptionEventKind.ACTIVATED:
            return await _create_row(event)
        log.error(
            f"{LogTag.PAYMENT} No local subscription matched the Dodo id",
            event_kind=event.kind.value,
            subscription_id=data.subscription_id,
        )
        return SubscriptionEventResult(SubscriptionEventOutcome.NO_ROW, None)

    if _is_stale(row, event):
        log.warning(
            f"{LogTag.PAYMENT} Stale subscription event ignored",
            event_kind=event.kind.value,
            subscription_id=data.subscription_id,
            event_at=event.occurred_at.strftime(EVENT_TIME_FORMAT),
            # Guarded by ``_is_stale``: a row with no last event is never stale.
            row_last_event_at=as_utc(row.last_event_at).strftime(EVENT_TIME_FORMAT),
        )
        return SubscriptionEventResult(SubscriptionEventOutcome.STALE, row.user_id)

    changes = _changes(row, DESIRED_STATE[event.kind](event.data))
    if not changes:
        log.info(
            f"{LogTag.PAYMENT} Subscription already in the reported state",
            event_kind=event.kind.value,
            subscription_id=data.subscription_id,
            subscription_status=row.status,
        )
        return SubscriptionEventResult(SubscriptionEventOutcome.UNCHANGED, row.user_id)

    await subscription_repository.apply_update_by_dodo_id(
        data.subscription_id,
        SubscriptionUpdate.model_validate({**changes, "last_event_at": event.occurred_at}),
    )
    await invalidate_plan_cache(row.user_id)

    new_status = changes.get("status")
    became_active = new_status == SubscriptionStatus.ACTIVE.value
    _capture_transition(event, row.user_id, changes, became_active)
    if became_active:
        await reactivate_workflows_safely(row.user_id)
    elif new_status in LAPSED_STATUSES:
        await deactivate_workflows_safely(row.user_id)

    log.info(
        f"{LogTag.PAYMENT} Subscription event applied",
        event_kind=event.kind.value,
        subscription_id=data.subscription_id,
        changed_fields=sorted(changes),
    )
    return SubscriptionEventResult(SubscriptionEventOutcome.APPLIED, row.user_id)
