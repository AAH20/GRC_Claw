"""
Data models for the GRC_Claw billing and usage tracking system.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class MeteringDimension(str, Enum):
    """Dimensions along which usage can be metered."""
    API_CALLS = "api_calls"
    AGENT_SESSIONS = "agent_sessions"
    POLICY_EVALUATIONS = "policy_evaluations"
    EVIDENCE_PROCESSED_GB = "evidence_processed_gb"
    FRAMEWORK_MAPPINGS = "framework_mappings"
    REPORTS_GENERATED = "reports_generated"
    STORAGE_GB = "storage_gb"
    COMPUTE_HOURS = "compute_hours"
    TOKEN_COUNT = "token_count"
    ACTIVE_USERS = "active_users"
    CUSTOM = "custom"


class BillingStatus(str, Enum):
    """Status of a billing cycle or invoice."""
    DRAFT = "draft"
    PENDING = "pending"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class PaymentStatus(str, Enum):
    """Status of a payment."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CHARGEBACK = "chargeback"


class RevenueRecognitionMethod(str, Enum):
    """Revenue recognition method per ASC 606 / IFRS 15."""
    POINT_IN_TIME = "point_in_time"
    OVER_TIME = "over_time"
    MILESTONE = "milestone"
    USAGE_BASED = "usage_based"


class PricingPlan(str, Enum):
    """Available pricing plans."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


@dataclass
class UsageRecord:
    """A single metered usage event."""

    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    dimension: MeteringDimension = MeteringDimension.API_CALLS
    quantity: float = 0.0
    unit: str = "count"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict = field(default_factory=dict)
    resource_id: str | None = None
    agent_id: str | None = None
    policy_id: str | None = None
    cost_center: str | None = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.quantity < 0:
            raise ValueError("quantity must be >= 0")


@dataclass
class UsageAggregation:
    """Aggregated usage for a tenant over a period and dimension."""

    tenant_id: str
    dimension: MeteringDimension
    period_start: str
    period_end: str
    total_quantity: float = 0.0
    unit: str = "count"
    record_count: int = 0
    average_per_day: float = 0.0
    peak_quantity: float = 0.0
    peak_timestamp: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class PricingTierConfig:
    """Tiered pricing configuration for a dimension."""

    dimension: MeteringDimension
    unit: str = "count"
    base_price: float = 0.0
    tiers: list[dict] = field(default_factory=list)
    # Each tier: {"min": 0, "max": 1000, "unit_price": 0.01}
    included_quantity: float = 0.0  # Quantity included in base price
    overage_unit_price: float = 0.0


@dataclass
class BillingCycle:
    """A billing cycle for a tenant."""

    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    tenant_id: str = ""
    plan: PricingPlan = PricingPlan.STARTER
    period_start: str = ""
    period_end: str = ""
    status: BillingStatus = BillingStatus.DRAFT
    line_items: list[BillingLineItem] = field(default_factory=list)
    subtotal: float = 0.0
    discount_amount: float = 0.0
    discount_reason: str | None = None
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    currency: str = "USD"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    issued_at: str | None = None
    due_date: str | None = None
    paid_at: str | None = None
    notes: list[str] = field(default_factory=list)

    def calculate_totals(self):
        """Recalculate all totals from line items."""
        self.subtotal = sum(li.total for li in self.line_items)
        self.tax_amount = (self.subtotal - self.discount_amount) * (self.tax_rate / 100)
        self.total = self.subtotal - self.discount_amount + self.tax_amount


@dataclass
class BillingLineItem:
    """A single line item on a billing cycle or invoice."""

    line_item_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    description: str = ""
    dimension: MeteringDimension | None = None
    quantity: float = 0.0
    unit: str = "count"
    unit_price: float = 0.0
    subtotal: float = 0.0
    discount_pct: float = 0.0
    discount_amount: float = 0.0
    total: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.subtotal = self.quantity * self.unit_price
        self.discount_amount = self.subtotal * (self.discount_pct / 100)
        self.total = self.subtotal - self.discount_amount


@dataclass
class Invoice:
    """A formal invoice document."""

    invoice_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    invoice_number: str = ""
    tenant_id: str = ""
    billing_cycle_id: str | None = None
    status: BillingStatus = BillingStatus.DRAFT
    line_items: list[BillingLineItem] = field(default_factory=list)
    subtotal: float = 0.0
    discount_amount: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    amount_paid: float = 0.0
    amount_due: float = 0.0
    currency: str = "USD"
    issue_date: str = ""
    due_date: str = ""
    paid_date: str | None = None
    notes: list[str] = field(default_factory=list)
    terms: str = "Net 30"
    purchase_order: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self):
        if not self.invoice_number:
            self.invoice_number = f"INV-{self.invoice_id}"

    def calculate_totals(self):
        """Recalculate all totals from line items."""
        self.subtotal = sum(li.total for li in self.line_items)
        self.tax_amount = (self.subtotal - self.discount_amount) * (self.tax_rate / 100)
        self.total = self.subtotal - self.discount_amount + self.tax_amount
        self.amount_due = self.total - self.amount_paid


@dataclass
class PaymentMethod:
    """A stored payment method for a tenant."""

    method_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    type: str = "credit_card"  # credit_card, ach, wire, stripe, paypal
    last_four: str = ""
    expiry_month: int | None = None
    expiry_year: int | None = None
    is_default: bool = False
    billing_address: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class Payment:
    """A payment transaction."""

    payment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    invoice_id: str | None = None
    amount: float = 0.0
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    method: str = "credit_card"
    method_id: str | None = None
    transaction_id: str | None = None  # External payment processor ID
    processed_at: str | None = None
    failure_reason: str | None = None
    refund_amount: float = 0.0
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class RevenueRecognitionEntry:
    """A revenue recognition entry per ASC 606 / IFRS 15."""

    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    invoice_id: str | None = None
    billing_cycle_id: str | None = None
    amount: float = 0.0
    currency: str = "USD"
    method: RevenueRecognitionMethod = RevenueRecognitionMethod.OVER_TIME
    performance_obligation: str = ""
    recognition_start: str = ""
    recognition_end: str = ""
    recognized_to_date: float = 0.0
    remaining_to_recognize: float = 0.0
    period_recognized: float = 0.0
    is_fully_recognized: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
