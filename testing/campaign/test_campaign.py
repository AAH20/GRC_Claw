"""Campaign testing framework for marketing campaign validation.

This module provides comprehensive testing for marketing campaigns including:
- Campaign configuration validation
- Audience targeting tests
- Budget and bidding tests
- Creative asset validation
- Campaign lifecycle testing
- Performance threshold validation
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class CampaignStatus(Enum):
    """Enumeration of campaign statuses."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class CampaignPlatform(Enum):
    """Supported advertising platforms."""

    GOOGLE_ADS = "google_ads"
    META_ADS = "meta_ads"
    TIKTOK_ADS = "tiktok_ads"
    LINKEDIN_ADS = "linkedin_ads"
    TWITTER_ADS = "twitter_ads"


@dataclass
class CampaignConfig:
    """Configuration for a marketing campaign.

    Attributes:
        campaign_id: Unique campaign identifier.
        name: Campaign name.
        platform: Advertising platform.
        budget_usd: Total budget in USD.
        daily_budget_usd: Daily budget cap in USD.
        start_date: Campaign start date (ISO format).
        end_date: Campaign end date (ISO format).
        target_audience: Target audience configuration.
        creatives: List of creative asset IDs.
        bidding_strategy: Bidding strategy name.
        status: Current campaign status.
        metadata: Additional campaign metadata.
    """

    campaign_id: str
    name: str
    platform: CampaignPlatform
    budget_usd: float
    daily_budget_usd: float
    start_date: str
    end_date: str
    target_audience: dict[str, Any] = field(default_factory=dict)
    creatives: list[str] = field(default_factory=list)
    bidding_strategy: str = "manual_cpc"
    status: CampaignStatus = CampaignStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignTestCase:
    """Represents a campaign test case.

    Attributes:
        name: Test case name.
        description: Test description.
        campaign_config: Campaign configuration to test.
        expected_result: Expected test outcome.
        validation_rules: List of validation rule names to apply.
        timeout_seconds: Maximum test execution time.
    """

    name: str
    description: str
    campaign_config: CampaignConfig
    expected_result: bool = True
    validation_rules: list[str] = field(default_factory=list)
    timeout_seconds: float = 30.0


@dataclass
class CampaignTestResult:
    """Result of a campaign test.

    Attributes:
        test_case: The test case that was executed.
        passed: Whether the test passed.
        actual_result: The actual result.
        execution_time_seconds: Time taken to execute.
        errors: List of error messages.
        warnings: List of warning messages.
    """

    test_case: CampaignTestCase
    passed: bool
    actual_result: bool = False
    execution_time_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CampaignValidator(ABC):
    """Abstract base class for campaign validators."""

    @abstractmethod
    def validate(self, config: CampaignConfig) -> tuple[bool, list[str]]:
        """Validate a campaign configuration.

        Args:
            config: The campaign configuration to validate.

        Returns:
            Tuple of (is_valid, list_of_error_messages).
        """
        ...


class BudgetValidator(CampaignValidator):
    """Validates campaign budget configuration."""

    def __init__(
        self,
        min_budget: float = 10.0,
        max_budget: float = 1_000_000.0,
        min_daily_budget: float = 1.0,
    ) -> None:
        """Initialize BudgetValidator.

        Args:
            min_budget: Minimum total budget.
            max_budget: Maximum total budget.
            min_daily_budget: Minimum daily budget.
        """
        self.min_budget = min_budget
        self.max_budget = max_budget
        self.min_daily_budget = min_daily_budget

    def validate(self, config: CampaignConfig) -> tuple[bool, list[str]]:
        """Validate budget configuration.

        Args:
            config: The campaign configuration.

        Returns:
            Tuple of (is_valid, errors).
        """
        errors: list[str] = []

        if config.budget_usd < self.min_budget:
            errors.append(
                f"Budget ${config.budget_usd:.2f} below minimum ${self.min_budget:.2f}"
            )
        if config.budget_usd > self.max_budget:
            errors.append(
                f"Budget ${config.budget_usd:.2f} exceeds maximum ${self.max_budget:.2f}"
            )
        if config.daily_budget_usd < self.min_daily_budget:
            errors.append(
                f"Daily budget ${config.daily_budget_usd:.2f} below minimum "
                f"${self.min_daily_budget:.2f}"
            )
        if config.daily_budget_usd > config.budget_usd:
            errors.append(
                f"Daily budget ${config.daily_budget_usd:.2f} exceeds "
                f"total budget ${config.budget_usd:.2f}"
            )

        return len(errors) == 0, errors


class AudienceValidator(CampaignValidator):
    """Validates campaign audience targeting."""

    def __init__(self) -> None:
        """Initialize AudienceValidator."""
        self._required_fields = ["age_range", "locations", "interests"]

    def validate(self, config: CampaignConfig) -> tuple[bool, list[str]]:
        """Validate audience targeting.

        Args:
            config: The campaign configuration.

        Returns:
            Tuple of (is_valid, errors).
        """
        errors: list[str] = []
        audience = config.target_audience

        for field_name in self._required_fields:
            if field_name not in audience:
                errors.append(f"Missing required audience field: {field_name}")

        if "age_range" in audience:
            age_range = audience["age_range"]
            if not isinstance(age_range, (list, tuple)) or len(age_range) != 2:
                errors.append("age_range must be a [min, max] pair")
            elif age_range[0] >= age_range[1]:
                errors.append("age_range min must be less than max")
            elif age_range[0] < 13:
                errors.append("age_range minimum must be at least 13")

        if "locations" in audience:
            if not isinstance(audience["locations"], list) or not audience["locations"]:
                errors.append("locations must be a non-empty list")

        return len(errors) == 0, errors


class CreativeValidator(CampaignValidator):
    """Validates campaign creative assets."""

    def __init__(
        self,
        min_creatives: int = 1,
        max_creatives: int = 20,
        required_formats: list[str] | None = None,
    ) -> None:
        """Initialize CreativeValidator.

        Args:
            min_creatives: Minimum number of creatives.
            max_creatives: Maximum number of creatives.
            required_formats: List of required creative formats.
        """
        self.min_creatives = min_creatives
        self.max_creatives = max_creatives
        self.required_formats = required_formats or ["image", "video"]

    def validate(self, config: CampaignConfig) -> tuple[bool, list[str]]:
        """Validate creative assets.

        Args:
            config: The campaign configuration.

        Returns:
            Tuple of (is_valid, errors).
        """
        errors: list[str] = []

        if len(config.creatives) < self.min_creatives:
            errors.append(
                f"Too few creatives: {len(config.creatives)} "
                f"(min: {self.min_creatives})"
            )
        if len(config.creatives) > self.max_creatives:
            errors.append(
                f"Too many creatives: {len(config.creatives)} "
                f"(max: {self.max_creatives})"
            )

        return len(errors) == 0, errors


class ScheduleValidator(CampaignValidator):
    """Validates campaign schedule configuration."""

    def validate(self, config: CampaignConfig) -> tuple[bool, list[str]]:
        """Validate campaign schedule.

        Args:
            config: The campaign configuration.

        Returns:
            Tuple of (is_valid, errors).
        """
        errors: list[str] = []

        if not config.start_date:
            errors.append("start_date is required")
        if not config.end_date:
            errors.append("end_date is required")

        if config.start_date and config.end_date:
            if config.start_date >= config.end_date:
                errors.append("start_date must be before end_date")

        return len(errors) == 0, errors


class CampaignTestRunner:
    """Runner for executing campaign test cases."""

    def __init__(self) -> None:
        """Initialize CampaignTestRunner."""
        self._validators: dict[str, CampaignValidator] = {
            "budget": BudgetValidator(),
            "audience": AudienceValidator(),
            "creative": CreativeValidator(),
            "schedule": ScheduleValidator(),
        }
        self._results: list[CampaignTestResult] = []

    def register_validator(
        self, name: str, validator: CampaignValidator
    ) -> None:
        """Register a custom validator.

        Args:
            name: Validator name.
            validator: The validator instance.
        """
        self._validators[name] = validator

    async def run_test(self, test_case: CampaignTestCase) -> CampaignTestResult:
        """Run a single campaign test case.

        Args:
            test_case: The test case to execute.

        Returns:
            The test result.
        """
        start_time = time.monotonic()
        all_errors: list[str] = []
        all_warnings: list[str] = []

        rules_to_apply = test_case.validation_rules or list(self._validators.keys())

        for rule_name in rules_to_apply:
            validator = self._validators.get(rule_name)
            if validator is None:
                all_warnings.append(f"Unknown validation rule: {rule_name}")
                continue

            is_valid, errors = validator.validate(test_case.campaign_config)
            if not is_valid:
                all_errors.extend(errors)

        passed = len(all_errors) == 0
        execution_time = time.monotonic() - start_time

        return CampaignTestResult(
            test_case=test_case,
            passed=passed == test_case.expected_result,
            actual_result=passed,
            execution_time_seconds=execution_time,
            errors=all_errors,
            warnings=all_warnings,
        )

    async def run_tests(
        self, test_cases: list[CampaignTestCase]
    ) -> list[CampaignTestResult]:
        """Run multiple campaign test cases.

        Args:
            test_cases: List of test cases to execute.

        Returns:
            List of test results.
        """
        self._results = []
        for tc in test_cases:
            result = await self.run_test(tc)
            self._results.append(result)
        return self._results

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of test results.

        Returns:
            Dictionary with summary statistics.
        """
        if not self._results:
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0}

        total = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        failed = total - passed

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "total_execution_time": sum(
                r.execution_time_seconds for r in self._results
            ),
        }


class CampaignLifecycleTester:
    """Tests campaign lifecycle transitions."""

    VALID_TRANSITIONS: dict[CampaignStatus, set[CampaignStatus]] = {
        CampaignStatus.DRAFT: {
            CampaignStatus.PENDING_REVIEW,
            CampaignStatus.ARCHIVED,
        },
        CampaignStatus.PENDING_REVIEW: {
            CampaignStatus.ACTIVE,
            CampaignStatus.REJECTED,
            CampaignStatus.DRAFT,
        },
        CampaignStatus.ACTIVE: {
            CampaignStatus.PAUSED,
            CampaignStatus.COMPLETED,
        },
        CampaignStatus.PAUSED: {
            CampaignStatus.ACTIVE,
            CampaignStatus.COMPLETED,
        },
        CampaignStatus.COMPLETED: {CampaignStatus.ARCHIVED},
        CampaignStatus.REJECTED: {CampaignStatus.DRAFT, CampaignStatus.ARCHIVED},
        CampaignStatus.ARCHIVED: set(),
    }

    def validate_transition(
        self, from_status: CampaignStatus, to_status: CampaignStatus
    ) -> tuple[bool, str]:
        """Validate a campaign status transition.

        Args:
            from_status: Current status.
            to_status: Target status.

        Returns:
            Tuple of (is_valid, message).
        """
        if from_status == to_status:
            return True, "No transition needed"

        valid_targets = self.VALID_TRANSITIONS.get(from_status, set())
        if to_status in valid_targets:
            return True, f"Valid transition: {from_status.value} -> {to_status.value}"

        return (
            False,
            f"Invalid transition: {from_status.value} -> {to_status.value}. "
            f"Valid targets: {[s.value for s in valid_targets]}",
        )

    def get_valid_transitions(
        self, status: CampaignStatus
    ) -> list[CampaignStatus]:
        """Get valid transition targets for a status.

        Args:
            status: The current status.

        Returns:
            List of valid target statuses.
        """
        return list(self.VALID_TRANSITIONS.get(status, set()))
