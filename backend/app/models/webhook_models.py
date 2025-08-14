"""
Clean webhook models for Dodo Payments based on actual webhook format.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WebhookEventType(str, Enum):
    """Dodo Payments webhook event types."""

    # Payment events
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_PROCESSING = "payment.processing"
    PAYMENT_CANCELLED = "payment.cancelled"

    # Subscription events
    SUBSCRIPTION_ACTIVE = "subscription.active"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
    SUBSCRIPTION_FAILED = "subscription.failed"
    SUBSCRIPTION_ON_HOLD = "subscription.on_hold"
    SUBSCRIPTION_PLAN_CHANGED = "subscription.plan_changed"


class CustomerData(BaseModel):
    """Customer info from webhook."""

    customer_id: str
    email: str
    name: str


class BillingData(BaseModel):
    """Billing address from webhook."""

    city: str
    country: str
    state: str
    street: str
    zipcode: str


class PaymentData(BaseModel):
    """Payment data from payment webhook."""

    payment_id: str
    subscription_id: Optional[str] = None
    business_id: str
    brand_id: str
    customer: CustomerData
    billing: BillingData
    currency: str
    total_amount: int
    settlement_amount: int
    settlement_currency: str
    tax: int
    settlement_tax: int
    status: str
    payment_method: str
    card_network: Optional[str] = None
    card_type: Optional[str] = None
    card_last_four: Optional[str] = None
    card_issuing_country: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class SubscriptionData(BaseModel):
    """Subscription data from subscription webhook."""

    subscription_id: str
    product_id: str
    customer: CustomerData
    billing: BillingData
    status: str
    currency: str
    quantity: int
    recurring_pre_tax_amount: int
    payment_frequency_count: int
    payment_frequency_interval: str
    subscription_period_count: int
    subscription_period_interval: str
    next_billing_date: Optional[str] = None
    previous_billing_date: Optional[str] = None
    created_at: str
    cancelled_at: Optional[str] = None
    cancel_at_next_billing_date: bool = False
    tax_inclusive: bool = False
    trial_period_days: int = 0
    on_demand: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    addons: List[Any] = Field(default_factory=list)
    discount_id: Optional[str] = None


class DodoWebhookEvent(BaseModel):
    """Dodo webhook event structure."""

    business_id: str
    type: WebhookEventType
    timestamp: str
    data: Dict[str, Any]

    def get_payment_data(self) -> Optional[PaymentData]:
        """Extract payment data if payment event."""
        if self.type.value.startswith("payment."):
            try:
                return PaymentData(**self.data)
            except Exception:
                return None
        return None

    def get_subscription_data(self) -> Optional[SubscriptionData]:
        """Extract subscription data if subscription event."""
        if self.type.value.startswith("subscription."):
            try:
                return SubscriptionData(**self.data)
            except Exception:
                return None
        return None


class WebhookProcessingResult(BaseModel):
    """Result of webhook processing."""

    event_type: str
    status: str  # "processed", "ignored", "failed"
    message: str
    payment_id: Optional[str] = None
    subscription_id: Optional[str] = None
