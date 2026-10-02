"""Testing Agent.

Designs and manages A/B tests for pricing strategies to validate
recommendations before full implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import structlog
from pydantic import BaseModel, Field, field_validator

logger = structlog.get_logger(__name__)


class TestStatus(str, Enum):
    """Status of an A/B test."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestVariant(BaseModel):
    """A variant in an A/B test."""

    name: str
    price: float = Field(gt=0)
    traffic_allocation: float = Field(gt=0, le=1)
    description: str | None = None

    @field_validator("traffic_allocation")
    @classmethod
    def validate_allocation(cls, v: float) -> float:
        """Validate traffic allocation is a valid percentage."""
        if v <= 0 or v > 1:
            raise ValueError("traffic_allocation must be between 0 and 1")
        return v


class TestMetrics(BaseModel):
    """Metrics collected during an A/B test."""

    variant_name: str
    impressions: int = 0
    conversions: int = 0
    revenue: float = 0.0
    conversion_rate: float = 0.0
    average_order_value: float = 0.0

    def update(self, impressions: int, conversions: int, revenue: float) -> None:
        """Update metrics with new data points."""
        self.impressions += impressions
        self.conversions += conversions
        self.revenue += revenue
        self.conversion_rate = (
            self.conversions / self.impressions if self.impressions > 0 else 0.0
        )
        self.average_order_value = (
            self.revenue / self.conversions if self.conversions > 0 else 0.0
        )


class ABTest(BaseModel):
    """An A/B test for pricing strategies."""

    test_id: str
    product_id: str
    status: TestStatus = TestStatus.DRAFT
    variants: list[TestVariant] = Field(min_length=2)
    metrics: dict[str, TestMetrics] = Field(default_factory=dict)
    start_date: datetime | None = None
    end_date: datetime | None = None
    min_sample_size: int = 100
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0)
    winner_variant: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class TestingConfig:
    """Configuration for the Testing Agent."""

    min_sample_size: int = 100
    confidence_level: float = 0.95
    max_test_duration_days: int = 14
    default_traffic_split: float = 0.5


class TestingAgent:
    """Agent responsible for designing and running A/B tests on pricing.

    Creates test variants, monitors their performance, and determines
    statistically significant winners before full rollout.
    """

    def __init__(self, config: TestingConfig | None = None) -> None:
        """Initialize the Testing Agent.

        Args:
            config: Agent configuration. Uses defaults if not provided.
        """
        self.config = config or TestingConfig()
        self._tests: dict[str, ABTest] = {}
        logger.info(
            "testing_agent_initialized",
            min_sample_size=self.config.min_sample_size,
            confidence_level=self.config.confidence_level,
        )

    def create_test(
        self,
        test_id: str,
        product_id: str,
        control_price: float,
        treatment_price: float,
        traffic_split: float | None = None,
        min_sample_size: int | None = None,
        duration_days: int | None = None,
    ) -> ABTest:
        """Create a new A/B test for a pricing change.

        Args:
            test_id: Unique test identifier.
            product_id: Product being tested.
            control_price: Current price (control variant).
            treatment_price: Proposed new price (treatment variant).
            traffic_split: Traffic allocation for control (0-1).
            min_sample_size: Minimum sample size for significance.
            duration_days: Maximum test duration in days.

        Returns:
            The created A/B test.

        Raises:
            ValueError: If inputs are invalid.
        """
        if not test_id or not product_id:
            raise ValueError("test_id and product_id are required")
        if control_price <= 0 or treatment_price <= 0:
            raise ValueError("prices must be positive")

        split = traffic_split or self.config.default_traffic_split
        if split <= 0 or split >= 1:
            raise ValueError("traffic_split must be between 0 and 1")

        test = ABTest(
            test_id=test_id,
            product_id=product_id,
            variants=[
                TestVariant(
                    name="control",
                    price=control_price,
                    traffic_allocation=split,
                    description="Current price (control)",
                ),
                TestVariant(
                    name="treatment",
                    price=treatment_price,
                    traffic_allocation=1 - split,
                    description="Proposed new price (treatment)",
                ),
            ],
            min_sample_size=min_sample_size or self.config.min_sample_size,
            confidence_level=self.config.confidence_level,
        )

        # Initialize metrics for each variant
        for variant in test.variants:
            test.metrics[variant.name] = TestMetrics(variant_name=variant.name)

        self._tests[test_id] = test

        logger.info(
            "ab_test_created",
            test_id=test_id,
            product_id=product_id,
            control_price=control_price,
            treatment_price=treatment_price,
        )

        return test

    def start_test(self, test_id: str) -> ABTest:
        """Start a draft A/B test.

        Args:
            test_id: The test to start.

        Returns:
            The updated test.

        Raises:
            KeyError: If test_id is not found.
            ValueError: If test is not in DRAFT status.
        """
        test = self._tests.get(test_id)
        if test is None:
            raise KeyError(f"Test {test_id} not found")
        if test.status != TestStatus.DRAFT:
            raise ValueError(f"Cannot start test in {test.status} status")

        test.status = TestStatus.RUNNING
        test.start_date = datetime.utcnow()
        test.end_date = test.start_date + timedelta(
            days=self.config.max_test_duration_days
        )
        test.updated_at = datetime.utcnow()

        logger.info("ab_test_started", test_id=test_id, start_date=test.start_date)
        return test

    def record_metrics(
        self,
        test_id: str,
        variant_name: str,
        impressions: int,
        conversions: int,
        revenue: float,
    ) -> TestMetrics:
        """Record performance metrics for a test variant.

        Args:
            test_id: The test identifier.
            variant_name: The variant to update.
            impressions: Number of impressions.
            conversions: Number of conversions.
            revenue: Revenue generated.

        Returns:
            Updated metrics for the variant.

        Raises:
            KeyError: If test or variant is not found.
            ValueError: If metrics values are negative.
        """
        if impressions < 0 or conversions < 0 or revenue < 0:
            raise ValueError("metrics values must be non-negative")

        test = self._tests.get(test_id)
        if test is None:
            raise KeyError(f"Test {test_id} not found")
        if variant_name not in test.metrics:
            raise KeyError(f"Variant {variant_name} not found in test {test_id}")

        metrics = test.metrics[variant_name]
        metrics.update(impressions, conversions, revenue)
        test.updated_at = datetime.utcnow()

        logger.debug(
            "metrics_recorded",
            test_id=test_id,
            variant=variant_name,
            impressions=impressions,
            conversions=conversions,
        )

        return metrics

    def _check_significance(self, test: ABTest) -> bool:
        """Check if test results are statistically significant.

        Uses a simplified z-test for proportions.

        Args:
            test: The A/B test to evaluate.

        Returns:
            True if results are statistically significant.
        """
        control = test.metrics.get("control")
        treatment = test.metrics.get("treatment")
        if control is None or treatment is None:
            return False

        if (
            control.impressions < test.min_sample_size
            or treatment.impressions < test.min_sample_size
        ):
            return False

        # Two-proportion z-test
        p1 = control.conversion_rate
        p2 = treatment.conversion_rate
        n1 = control.impressions
        n2 = treatment.impressions

        p_pool = (control.conversions + treatment.conversions) / (n1 + n2)
        se = (p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) ** 0.5

        if se == 0:
            return False

        z_score = (p2 - p1) / se

        # Critical value for 95% confidence (two-tailed)
        z_critical = 1.96
        if test.confidence_level >= 0.99:
            z_critical = 2.576
        elif test.confidence_level >= 0.90:
            z_critical = 1.645

        return abs(z_score) > z_critical

    def evaluate_test(self, test_id: str) -> ABTest:
        """Evaluate an A/B test and determine the winner.

        Args:
            test_id: The test to evaluate.

        Returns:
            The updated test with winner determined if significant.

        Raises:
            KeyError: If test is not found.
        """
        test = self._tests.get(test_id)
        if test is None:
            raise KeyError(f"Test {test_id} not found")

        if test.status != TestStatus.RUNNING:
            raise ValueError(f"Cannot evaluate test in {test.status} status")

        is_significant = self._check_significance(test)

        if is_significant:
            control = test.metrics["control"]
            treatment = test.metrics["treatment"]

            # Winner is the variant with higher revenue per impression
            control_rpi = (
                control.revenue / control.impressions if control.impressions > 0 else 0
            )
            treatment_rpi = (
                treatment.revenue / treatment.impressions
                if treatment.impressions > 0
                else 0
            )

            test.winner_variant = "treatment" if treatment_rpi > control_rpi else "control"
            test.status = TestStatus.COMPLETED
            test.end_date = datetime.utcnow()

            logger.info(
                "ab_test_completed",
                test_id=test_id,
                winner=test.winner_variant,
                control_rpi=control_rpi,
                treatment_rpi=treatment_rpi,
            )
        else:
            logger.info(
                "ab_test_not_significant",
                test_id=test_id,
                control_impressions=test.metrics["control"].impressions,
                treatment_impressions=test.metrics["treatment"].impressions,
                min_sample_size=test.min_sample_size,
            )

        test.updated_at = datetime.utcnow()
        return test

    def get_test(self, test_id: str) -> ABTest | None:
        """Retrieve a test by ID.

        Args:
            test_id: The test identifier.

        Returns:
            The test if found, None otherwise.
        """
        return self._tests.get(test_id)

    def list_tests(
        self,
        product_id: str | None = None,
        status: TestStatus | None = None,
    ) -> list[ABTest]:
        """List all tests, optionally filtered.

        Args:
            product_id: Filter by product.
            status: Filter by status.

        Returns:
            List of matching tests.
        """
        tests = list(self._tests.values())

        if product_id:
            tests = [t for t in tests if t.product_id == product_id]
        if status:
            tests = [t for t in tests if t.status == status]

        return tests

    def cancel_test(self, test_id: str) -> ABTest:
        """Cancel a running test.

        Args:
            test_id: The test to cancel.

        Returns:
            The cancelled test.

        Raises:
            KeyError: If test is not found.
            ValueError: If test cannot be cancelled.
        """
        test = self._tests.get(test_id)
        if test is None:
            raise KeyError(f"Test {test_id} not found")
        if test.status not in (TestStatus.DRAFT, TestStatus.RUNNING, TestStatus.PAUSED):
            raise ValueError(f"Cannot cancel test in {test.status} status")

        test.status = TestStatus.CANCELLED
        test.updated_at = datetime.utcnow()

        logger.info("ab_test_cancelled", test_id=test_id)
        return test
