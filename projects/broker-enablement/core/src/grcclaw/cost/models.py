"""
Shared data models for the GRC_Claw cost optimization framework.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class CostCategory(str, Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    LICENSING = "licensing"
    PERSONNEL = "personnel"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    TRAINING = "training"
    SUPPORT = "support"
    OTHER = "other"


class ResourceType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    STORAGE_SSD = "storage_ssd"
    STORAGE_HDD = "storage_hdd"
    BANDWIDTH = "bandwidth"
    API_CALLS = "api_calls"
    AGENT_RUNTIME = "agent_runtime"
    MODEL_INFERENCE = "model_inference"


class OptimizationAction(str, Enum):
    SCALE_DOWN = "scale_down"
    SCALE_UP = "scale_up"
    RIGHTSIZE = "rightsize"
    RESERVED_CAPACITY = "reserved_capacity"
    SPOT_INSTANCES = "spot_instances"
    SCHEDULE_SHUTDOWN = "schedule_shutdown"
    CONSOLIDATE = "consolidate"
    MIGRATE_STORAGE_TIER = "migrate_storage_tier"
    ENABLE_AUTO_SCALING = "enable_auto_scaling"
    PURCHASE_SAVINGS_PLAN = "purchase_savings_plan"


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    COST_SPIKE = "cost_spike"
    BUDGET_OVERRUN = "budget_overrun"
    IDLE_RESOURCE = "idle_resource"
    ORPHANED_RESOURCE = "orphaned_resource"
    PRICE_INCREASE = "price_increase"
    USAGE_SURGE = "usage_surge"
    UNUSUAL_PATTERN = "unusual_pattern"


class ForecastMethod(str, Enum):
    LINEAR_REGRESSION = "linear_regression"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    MONTE_CARLO = "monte_carlo"


class AllocationMethod(str, Enum):
    DIRECT = "direct"
    USAGE_BASED = "usage_based"
    HEADCOUNT = "headcount"
    REVENUE = "revenue"
    EQUAL_SPLIT = "equal_split"
    WEIGHTED = "weighted"


@dataclass
class ResourceUsage:
    """Measured usage for a specific resource."""

    resource_type: ResourceType
    quantity: float
    unit: str
    cost_per_unit: float
    period_start: str = ""
    period_end: str = ""
    utilization_pct: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def total_cost(self) -> float:
        return self.quantity * self.cost_per_unit


@dataclass
class CostLineItem:
    """A single cost entry."""

    item_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    category: CostCategory = CostCategory.OTHER
    description: str = ""
    amount: float = 0.0
    currency: str = "USD"
    period: str = ""  # e.g. "2024-01"
    resource_type: ResourceType | None = None
    tags: dict = field(default_factory=dict)
    allocated_to: str = ""  # department/project/team
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class CostBreakdown:
    """Aggregated cost breakdown by category."""

    period: str = ""
    total_cost: float = 0.0
    by_category: dict[str, float] = field(default_factory=dict)
    by_resource: dict[str, float] = field(default_factory=dict)
    by_department: dict[str, float] = field(default_factory=dict)
    line_items: list[CostLineItem] = field(default_factory=list)
    currency: str = "USD"


@dataclass
class OptimizationRecommendation:
    """A single optimization recommendation."""

    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    action: OptimizationAction = OptimizationAction.RIGHTSIZE
    resource_type: ResourceType = ResourceType.CPU
    description: str = ""
    current_cost: float = 0.0
    projected_cost: float = 0.0
    savings: float = 0.0
    savings_pct: float = 0.0
    confidence: float = 0.0  # 0-1
    effort: str = "low"  # low, medium, high
    risk: str = "low"  # low, medium, high
    implementation_steps: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class Anomaly:
    """A detected cost anomaly."""

    anomaly_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    anomaly_type: AnomalyType = AnomalyType.COST_SPIKE
    severity: AnomalySeverity = AnomalySeverity.MEDIUM
    description: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    period: str = ""
    expected_cost: float = 0.0
    actual_cost: float = 0.0
    deviation_pct: float = 0.0
    deviation_amount: float = 0.0
    affected_resources: list[str] = field(default_factory=list)
    root_cause: str = ""
    recommended_action: str = ""
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class BudgetForecast:
    """Forecast result for a future period."""

    period: str = ""
    method: ForecastMethod = ForecastMethod.LINEAR_REGRESSION
    forecasted_cost: float = 0.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    confidence_interval: float = 0.95
    growth_rate: float = 0.0
    seasonality_factor: float = 1.0
    assumptions: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)


@dataclass
class CostAllocation:
    """Cost allocation entry for showback/chargeback."""

    allocation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    department: str = ""
    project: str = ""
    team: str = ""
    total_allocated: float = 0.0
    direct_costs: float = 0.0
    shared_costs: float = 0.0
    overhead: float = 0.0
    allocation_method: AllocationMethod = AllocationMethod.USAGE_BASED
    period: str = ""
    line_items: list[CostLineItem] = field(default_factory=list)
    cost_center: str = ""
    business_unit: str = ""


@dataclass
class TCOSummary:
    """Total Cost of Ownership summary."""

    period: str = ""
    infrastructure_cost: float = 0.0
    licensing_cost: float = 0.0
    personnel_cost: float = 0.0
    operational_cost: float = 0.0
    compliance_cost: float = 0.0
    training_cost: float = 0.0
    support_cost: float = 0.0
    total_tco: float = 0.0
    cost_per_agent: float = 0.0
    cost_per_policy: float = 0.0
    cost_per_gb_stored: float = 0.0
    cost_per_api_call: float = 0.0
    period_months: int = 12
    currency: str = "USD"
