"""
Data models for the GRC_Claw quote engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, timezone
import uuid


class DeploymentModel(str, Enum):
    CLOUD_SAAS = "cloud_saas"
    PRIVATE_CLOUD = "private_cloud"
    ON_PREMISES = "on_premises"
    HYBRID = "hybrid"


class SupportLevel(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PricingTier(str, Enum):
    STARTUP = "startup"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


@dataclass
class OrganizationProfile:
    """Organization profile driving the custom quote."""

    name: str
    industry: str
    agents: int
    models: int
    policies: int
    evidence_volume_gb: float
    frameworks: list[str] = field(default_factory=list)
    deployment_model: DeploymentModel = DeploymentModel.CLOUD_SAAS
    support_level: SupportLevel = SupportLevel.STANDARD
    pricing_tier: PricingTier = PricingTier.GROWTH
    custom_requirements: Optional[str] = None
    risk_exposure_score: float = 5.0  # 1-10 scale
    compliance_maturity: float = 5.0  # 1-10 scale
    annual_revenue_millions: Optional[float] = None
    existing_tooling_cost_annual: Optional[float] = None
    incident_history_count: int = 0
    avg_incident_cost: float = 0.0
    audit_findings_annual: int = 0
    avg_audit_remediation_cost: float = 0.0
    data_breach_probability_annual: float = 0.15  # 15% default
    avg_data_breach_cost: float = 4_450_000  # IBM 2023 average
    regulatory_fine_exposure_annual: float = 0.0
    business_disruption_cost_annual: float = 0.0

    def __post_init__(self):
        if self.agents < 1:
            raise ValueError("agents must be >= 1")
        if self.models < 1:
            raise ValueError("models must be >= 1")
        if self.policies < 1:
            raise ValueError("policies must be >= 1")
        if self.evidence_volume_gb < 0:
            raise ValueError("evidence_volume_gb must be >= 0")
        if not 1 <= self.risk_exposure_score <= 10:
            raise ValueError("risk_exposure_score must be 1-10")
        if not 1 <= self.compliance_maturity <= 10:
            raise ValueError("compliance_maturity must be 1-10")


@dataclass
class QuoteLineItem:
    """Individual line item in a quote."""

    description: str
    quantity: float
    unit_price: float
    unit: str
    category: str
    subtotal: float = 0.0
    discount_pct: float = 0.0
    discount_amount: float = 0.0
    total: float = 0.0

    def __post_init__(self):
        self.subtotal = self.quantity * self.unit_price
        self.discount_amount = self.subtotal * (self.discount_pct / 100)
        self.total = self.subtotal - self.discount_amount


@dataclass
class Quote:
    """Complete quote with all line items and metadata."""

    quote_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_until: str = ""
    organization: OrganizationProfile = field(default_factory=lambda: OrganizationProfile(
        name="", industry="", agents=1, models=1, policies=1, evidence_volume_gb=0
    ))
    line_items: list[QuoteLineItem] = field(default_factory=list)
    subtotal: float = 0.0
    volume_discount_pct: float = 0.0
    volume_discount_amount: float = 0.0
    support_multiplier: float = 1.0
    deployment_multiplier: float = 1.0
    total_before_tax: float = 0.0
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    annual_cost: float = 0.0
    monthly_cost: float = 0.0
    notes: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    def calculate_totals(self):
        """Recalculate all totals from line items."""
        self.subtotal = sum(li.total for li in self.line_items)
        self.volume_discount_amount = self.subtotal * (self.volume_discount_pct / 100)
        self.total_before_tax = self.subtotal - self.volume_discount_amount
        self.total_before_tax *= self.support_multiplier * self.deployment_multiplier
        self.tax_amount = self.total_before_tax * (self.tax_rate / 100)
        self.total = self.total_before_tax + self.tax_amount
        self.annual_cost = self.total
        self.monthly_cost = self.total / 12
