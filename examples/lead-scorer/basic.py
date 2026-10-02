"""
Basic Lead Scoring Example
==========================

Demonstrates core lead scoring functionality including:
- Lead data model with demographic and behavioral attributes
- Rule-based scoring engine
- Score normalization and thresholding
- Lead qualification and routing
- Basic scoring analytics

Usage:
    python basic.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LeadSource(str, Enum):
    """Lead acquisition sources."""

    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL = "social"
    EMAIL = "email"
    EVENT = "event"
    PAID_ADS = "paid_ads"
    ORGANIC = "organic"


class LeadStatus(str, Enum):
    """Lead lifecycle statuses."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class Industry(str, Enum):
    """Industry verticals."""

    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    EDUCATION = "education"
    OTHER = "other"


@dataclass
class Lead:
    """Represents a sales lead."""

    id: str
    name: str
    email: str
    company: str
    source: LeadSource
    status: LeadStatus = LeadStatus.NEW
    industry: Industry = Industry.OTHER
    company_size: int = 0
    job_title: str = ""
    annual_revenue: float = 0.0
    website_visits: int = 0
    email_opens: int = 0
    email_clicks: int = 0
    form_submissions: int = 0
    content_downloads: int = 0
    webinar_attended: bool = False
    trial_requested: bool = False
    demo_requested: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_activity_at: datetime | None = None
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoringRule:
    """A rule for scoring leads."""

    name: str
    attribute: str
    condition: str
    value: Any
    points: float
    description: str = ""

    def evaluate(self, lead: Lead) -> float:
        """Evaluate this rule against a lead.

        Args:
            lead: The lead to evaluate.

        Returns:
            Points awarded (0 if rule doesn't match).
        """
        lead_value = getattr(lead, self.attribute, None)
        if lead_value is None:
            return 0.0

        operators = {
            "eq": lambda a, b: a == b,
            "ne": lambda a, b: a != b,
            "gt": lambda a, b: a > b,
            "gte": lambda a, b: a >= b,
            "lt": lambda a, b: a < b,
            "lte": lambda a, b: a <= b,
            "in": lambda a, b: a in b,
            "contains": lambda a, b: b in a if isinstance(a, str) else False,
        }

        op_func = operators.get(self.condition)
        if op_func is None:
            logger.warning("Unknown condition: %s", self.condition)
            return 0.0

        try:
            if op_func(lead_value, self.value):
                return self.points
        except TypeError:
            logger.warning(
                "Type mismatch evaluating rule '%s': %s %s %s",
                self.name,
                type(lead_value).__name__,
                self.condition,
                type(self.value).__name__,
            )
            return 0.0

        return 0.0


class LeadScoringEngine:
    """Rule-based lead scoring engine."""

    def __init__(self) -> None:
        """Initialize the scoring engine."""
        self.rules: list[ScoringRule] = []
        self.score_thresholds: dict[str, float] = {
            "hot": 80.0,
            "warm": 50.0,
            "cold": 20.0,
        }

    def add_rule(self, rule: ScoringRule) -> None:
        """Add a scoring rule.

        Args:
            rule: The scoring rule to add.
        """
        self.rules.append(rule)
        logger.debug("Added scoring rule: %s", rule.name)

    def load_default_rules(self) -> None:
        """Load default scoring rules."""
        defaults = [
            # Demographic scoring
            ScoringRule("enterprise_size", "company_size", "gte", 1000, 20, "Enterprise company size"),
            ScoringRule("mid_market_size", "company_size", "gte", 100, 10, "Mid-market company size"),
            ScoringRule("high_revenue", "annual_revenue", "gte", 1000000, 15, "High annual revenue"),
            ScoringRule("decision_maker", "job_title", "contains", "CEO", 15, "C-level executive"),
            ScoringRule("decision_maker2", "job_title", "contains", "CTO", 15, "C-level executive"),
            ScoringRule("decision_maker3", "job_title", "contains", "VP", 10, "VP level"),
            ScoringRule("decision_maker4", "job_title", "contains", "Director", 8, "Director level"),

            # Behavioral scoring
            ScoringRule("frequent_visitor", "website_visits", "gte", 10, 10, "Frequent website visitor"),
            ScoringRule("regular_visitor", "website_visits", "gte", 5, 5, "Regular website visitor"),
            ScoringRule("email_engaged", "email_opens", "gte", 5, 8, "Email engaged"),
            ScoringRule("email_clicker", "email_clicks", "gte", 3, 10, "Email clicker"),
            ScoringRule("form_submitter", "form_submissions", "gte", 1, 12, "Form submitter"),
            ScoringRule("content_downloader", "content_downloads", "gte", 1, 8, "Content downloader"),
            ScoringRule("webinar_attendee", "webinar_attended", "eq", True, 15, "Webinar attendee"),
            ScoringRule("trial_requested", "trial_requested", "eq", True, 25, "Trial requested"),
            ScoringRule("demo_requested", "demo_requested", "eq", True, 30, "Demo requested"),

            # Source quality
            ScoringRule("referral_source", "source", "eq", LeadSource.REFERRAL, 15, "Referral source"),
            ScoringRule("event_source", "source", "eq", LeadSource.EVENT, 12, "Event source"),
            ScoringRule("organic_source", "source", "eq", LeadSource.ORGANIC, 8, "Organic source"),
        ]

        for rule in defaults:
            self.add_rule(rule)

        logger.info("Loaded %d default scoring rules", len(defaults))

    def score_lead(self, lead: Lead) -> float:
        """Calculate the score for a lead.

        Args:
            lead: The lead to score.

        Returns:
            The calculated score.
        """
        total_score = 0.0
        for rule in self.rules:
            points = rule.evaluate(lead)
            total_score += points

        # Normalize to 0-100 scale
        normalized_score = min(total_score, 100.0)
        lead.score = normalized_score

        logger.debug("Scored lead '%s': %.1f", lead.email, normalized_score)
        return normalized_score

    def score_leads(self, leads: list[Lead]) -> list[Lead]:
        """Score multiple leads.

        Args:
            leads: List of leads to score.

        Returns:
            The leads with updated scores.
        """
        for lead in leads:
            self.score_lead(lead)
        logger.info("Scored %d leads", len(leads))
        return leads

    def classify_lead(self, lead: Lead) -> str:
        """Classify a lead based on its score.

        Args:
            lead: The lead to classify.

        Returns:
            Classification string: "hot", "warm", or "cold".
        """
        if lead.score >= self.score_thresholds["hot"]:
            return "hot"
        elif lead.score >= self.score_thresholds["warm"]:
            return "warm"
        elif lead.score >= self.score_thresholds["cold"]:
            return "cold"
        return "cold"

    def get_scoring_breakdown(self, lead: Lead) -> dict[str, Any]:
        """Get a detailed scoring breakdown for a lead.

        Args:
            lead: The lead to analyze.

        Returns:
            Dictionary with scoring details.
        """
        breakdown = {
            "lead_id": lead.id,
            "email": lead.email,
            "total_score": 0.0,
            "classification": "",
            "rule_results": [],
        }

        for rule in self.rules:
            points = rule.evaluate(lead)
            if points > 0:
                breakdown["rule_results"].append({
                    "rule": rule.name,
                    "description": rule.description,
                    "points": points,
                })
                breakdown["total_score"] += points

        breakdown["total_score"] = min(breakdown["total_score"], 100.0)
        breakdown["classification"] = self.classify_lead(lead)

        return breakdown


def main() -> None:
    """Run the basic lead scoring example."""
    logger.info("=" * 60)
    logger.info("Basic Lead Scoring Example")
    logger.info("=" * 60)

    # Create scoring engine
    engine = LeadScoringEngine()
    engine.load_default_rules()

    # Create sample leads
    leads = [
        Lead(
            id="lead_001",
            name="Alice Johnson",
            email="alice@techcorp.com",
            company="TechCorp",
            source=LeadSource.WEBSITE,
            industry=Industry.TECHNOLOGY,
            company_size=2500,
            job_title="CTO",
            annual_revenue=50000000.0,
            website_visits=15,
            email_opens=8,
            email_clicks=5,
            form_submissions=2,
            content_downloads=3,
            webinar_attended=True,
            trial_requested=True,
            demo_requested=True,
        ),
        Lead(
            id="lead_002",
            name="Bob Smith",
            email="bob@smallbiz.com",
            company="SmallBiz Inc",
            source=LeadSource.PAID_ADS,
            industry=Industry.RETAIL,
            company_size=25,
            job_title="Manager",
            annual_revenue=500000.0,
            website_visits=3,
            email_opens=1,
            email_clicks=0,
            form_submissions=0,
            content_downloads=0,
        ),
        Lead(
            id="lead_003",
            name="Carol Williams",
            email="carol@healthplus.com",
            company="HealthPlus",
            source=LeadSource.REFERRAL,
            industry=Industry.HEALTHCARE,
            company_size=500,
            job_title="VP of Operations",
            annual_revenue=10000000.0,
            website_visits=8,
            email_opens=4,
            email_clicks=2,
            form_submissions=1,
            content_downloads=1,
            webinar_attended=True,
            demo_requested=True,
        ),
    ]

    # Score leads
    engine.score_leads(leads)

    # Display results
    logger.info("\nLead Scoring Results:")
    logger.info("-" * 60)
    for lead in leads:
        classification = engine.classify_lead(lead)
        logger.info(
            "%s (%s) - Score: %.1f - %s",
            lead.name,
            lead.email,
            lead.score,
            classification.upper(),
        )

    # Detailed breakdown for top lead
    top_lead = max(leads, key=lambda l: l.score)
    logger.info("\nDetailed breakdown for %s:", top_lead.name)
    breakdown = engine.get_scoring_breakdown(top_lead)
    for result in breakdown["rule_results"]:
        logger.info("  +%.0f pts: %s (%s)", result["points"], result["description"], result["rule"])

    logger.info("\n" + "=" * 60)
    logger.info("Example complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
