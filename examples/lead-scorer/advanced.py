"""
Advanced Lead Scoring Example
=============================

Demonstrates advanced lead scoring techniques including:
- Machine learning-based scoring models
- Behavioral pattern analysis
- Predictive lead scoring
- Dynamic scoring with decay
- Multi-touch attribution scoring
- Lead scoring A/B testing
- Custom scoring models

Usage:
    python advanced.py
"""

from __future__ import annotations

import logging
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ScoringModelType(str, Enum):
    """Types of scoring models."""

    RULE_BASED = "rule_based"
    ML_CLASSIFIER = "ml_classifier"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"


class BehaviorType(str, Enum):
    """Types of lead behaviors."""

    PAGE_VIEW = "page_view"
    FORM_SUBMIT = "form_submit"
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    CONTENT_DOWNLOAD = "content_download"
    WEBINAR_ATTEND = "webinar_attend"
    TRIAL_START = "trial_start"
    DEMO_REQUEST = "demo_request"
    PRICING_VIEW = "pricing_view"
    CASE_STUDY_VIEW = "case_study_view"


@dataclass
class BehaviorEvent:
    """A single behavior event."""

    lead_id: str
    behavior_type: BehaviorType
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    value: float = 1.0


@dataclass
class LeadProfile:
    """Extended lead profile with behavioral data."""

    id: str
    name: str
    email: str
    company: str
    industry: str
    company_size: int
    job_title: str
    annual_revenue: float
    behaviors: list[BehaviorEvent] = field(default_factory=list)
    demographic_score: float = 0.0
    behavioral_score: float = 0.0
    predictive_score: float = 0.0
    final_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def add_behavior(self, behavior_type: BehaviorType, value: float = 1.0, metadata: dict[str, Any] | None = None) -> None:
        """Add a behavior event to the lead's history.

        Args:
            behavior_type: Type of behavior.
            value: Behavior value/weight.
            metadata: Additional metadata.
        """
        event = BehaviorEvent(
            lead_id=self.id,
            behavior_type=behavior_type,
            timestamp=datetime.now(),
            metadata=metadata or {},
            value=value,
        )
        self.behaviors.append(event)


@dataclass
class ScoringModel:
    """A lead scoring model configuration."""

    name: str
    model_type: ScoringModelType
    weights: dict[str, float] = field(default_factory=dict)
    behavior_weights: dict[BehaviorType, float] = field(default_factory=dict)
    decay_half_life_days: float = 14.0
    max_score: float = 100.0

    def __post_init__(self) -> None:
        """Set default behavior weights if not provided."""
        if not self.behavior_weights:
            self.behavior_weights = {
                BehaviorType.PAGE_VIEW: 1.0,
                BehaviorType.FORM_SUBMIT: 10.0,
                BehaviorType.EMAIL_OPEN: 2.0,
                BehaviorType.EMAIL_CLICK: 5.0,
                BehaviorType.CONTENT_DOWNLOAD: 8.0,
                BehaviorType.WEBINAR_ATTEND: 15.0,
                BehaviorType.TRIAL_START: 25.0,
                BehaviorType.DEMO_REQUEST: 30.0,
                BehaviorType.PRICING_VIEW: 12.0,
                BehaviorType.CASE_STUDY_VIEW: 6.0,
            }


class AdvancedLeadScoringEngine:
    """Advanced lead scoring engine with ML and behavioral analysis."""

    def __init__(self) -> None:
        """Initialize the advanced scoring engine."""
        self.models: dict[str, ScoringModel] = {}
        self.leads: dict[str, LeadProfile] = {}
        self.training_data: list[dict[str, Any]] = []

    def register_model(self, model: ScoringModel) -> None:
        """Register a scoring model.

        Args:
            model: The scoring model to register.
        """
        self.models[model.name] = model
        logger.info("Registered scoring model '%s' (%s)", model.name, model.model_type.value)

    def create_lead(
        self,
        name: str,
        email: str,
        company: str,
        industry: str,
        company_size: int,
        job_title: str,
        annual_revenue: float = 0.0,
    ) -> LeadProfile:
        """Create a new lead profile.

        Args:
            name: Lead name.
            email: Lead email.
            company: Company name.
            industry: Industry vertical.
            company_size: Number of employees.
            job_title: Job title.
            annual_revenue: Annual revenue.

        Returns:
            The created LeadProfile.
        """
        lead_id = f"lead_{len(self.leads) + 1:04d}"
        lead = LeadProfile(
            id=lead_id,
            name=name,
            email=email,
            company=company,
            industry=industry,
            company_size=company_size,
            job_title=job_title,
            annual_revenue=annual_revenue,
        )
        self.leads[lead_id] = lead
        return lead

    def calculate_demographic_score(self, lead: LeadProfile) -> float:
        """Calculate demographic score based on firmographic data.

        Args:
            lead: The lead to score.

        Returns:
            Demographic score (0-100).
        """
        score = 0.0

        # Company size scoring
        if lead.company_size >= 1000:
            score += 25
        elif lead.company_size >= 500:
            score += 20
        elif lead.company_size >= 100:
            score += 15
        elif lead.company_size >= 50:
            score += 10
        else:
            score += 5

        # Revenue scoring
        if lead.annual_revenue >= 10000000:
            score += 25
        elif lead.annual_revenue >= 1000000:
            score += 20
        elif lead.annual_revenue >= 500000:
            score += 15
        elif lead.annual_revenue >= 100000:
            score += 10
        else:
            score += 5

        # Job title scoring
        title_lower = lead.job_title.lower()
        if any(t in title_lower for t in ["ceo", "cto", "cio", "founder", "president"]):
            score += 30
        elif any(t in title_lower for t in ["vp", "vice president"]):
            score += 25
        elif any(t in title_lower for t in ["director", "head of"]):
            score += 20
        elif any(t in title_lower for t in ["manager", "lead"]):
            score += 15
        else:
            score += 10

        # Industry scoring
        high_value_industries = ["technology", "finance", "healthcare"]
        if lead.industry.lower() in high_value_industries:
            score += 20
        else:
            score += 10

        return min(score, 100.0)

    def calculate_behavioral_score(
        self,
        lead: LeadProfile,
        model: ScoringModel,
    ) -> float:
        """Calculate behavioral score with time decay.

        Args:
            lead: The lead to score.
            model: The scoring model to use.

        Returns:
            Behavioral score (0-100).
        """
        if not lead.behaviors:
            return 0.0

        now = datetime.now()
        total_score = 0.0

        for event in lead.behaviors:
            # Time decay
            age_days = (now - event.timestamp).total_seconds() / 86400
            decay_factor = 0.5 ** (age_days / model.decay_half_life_days)

            # Behavior weight
            weight = model.behavior_weights.get(event.behavior_type, 1.0)

            total_score += weight * event.value * decay_factor

        # Normalize to 0-100
        return min(total_score, 100.0)

    def calculate_predictive_score(self, lead: LeadProfile) -> float:
        """Calculate predictive score using ML model.

        Uses a simplified logistic regression approach for demonstration.
        In production, this would use a trained ML model.

        Args:
            lead: The lead to score.

        Returns:
            Predictive score (0-100).
        """
        # Feature extraction
        features = {
            "company_size": math.log1p(lead.company_size) / 10,
            "revenue": math.log1p(lead.annual_revenue) / 20,
            "behavior_count": len(lead.behaviors) / 50,
            "recency": 0.0,
            "frequency": 0.0,
            "engagement_depth": 0.0,
        }

        if lead.behaviors:
            now = datetime.now()
            # Recency: days since last behavior
            last_behavior = max(lead.behaviors, key=lambda b: b.timestamp)
            days_since = (now - last_behavior.timestamp).total_seconds() / 86400
            features["recency"] = max(0, 1 - days_since / 30)

            # Frequency: behaviors per week
            if len(lead.behaviors) > 1:
                first_behavior = min(lead.behaviors, key=lambda b: b.timestamp)
                weeks = max((now - first_behavior.timestamp).total_seconds() / (86400 * 7), 1)
                features["frequency"] = min(len(lead.behaviors) / weeks / 10, 1.0)

            # Engagement depth: variety of behaviors
            unique_types = len(set(b.behavior_type for b in lead.behaviors))
            features["engagement_depth"] = unique_types / len(BehaviorType)

        # Weighted sum (simplified logistic regression)
        weights = {
            "company_size": 0.15,
            "revenue": 0.15,
            "behavior_count": 0.15,
            "recency": 0.20,
            "frequency": 0.15,
            "engagement_depth": 0.20,
        }

        raw_score = sum(features[k] * weights[k] for k in features)

        # Sigmoid activation
        probability = 1 / (1 + math.exp(-5 * (raw_score - 0.5)))

        return probability * 100

    def score_lead(
        self,
        lead: LeadProfile,
        model_name: str = "default",
    ) -> dict[str, float]:
        """Score a lead using the specified model.

        Args:
            lead: The lead to score.
            model_name: Name of the scoring model to use.

        Returns:
            Dictionary with all score components.
        """
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")

        model = self.models[model_name]

        # Calculate component scores
        lead.demographic_score = self.calculate_demographic_score(lead)
        lead.behavioral_score = self.calculate_behavioral_score(lead, model)
        lead.predictive_score = self.calculate_predictive_score(lead)

        # Combine scores using model weights
        w = model.weights
        lead.final_score = (
            lead.demographic_score * w.get("demographic", 0.3)
            + lead.behavioral_score * w.get("behavioral", 0.4)
            + lead.predictive_score * w.get("predictive", 0.3)
        )

        lead.final_score = min(lead.final_score, model.max_score)

        return {
            "demographic": round(lead.demographic_score, 2),
            "behavioral": round(lead.behavioral_score, 2),
            "predictive": round(lead.predictive_score, 2),
            "final": round(lead.final_score, 2),
        }

    def get_behavior_analytics(self, lead: LeadProfile) -> dict[str, Any]:
        """Get behavioral analytics for a lead.

        Args:
            lead: The lead to analyze.

        Returns:
            Behavioral analytics dictionary.
        """
        if not lead.behaviors:
            return {"total_behaviors": 0, "behavior_breakdown": {}, "timeline": []}

        breakdown: dict[str, int] = defaultdict(int)
        for event in lead.behaviors:
            breakdown[event.behavior_type.value] += 1

        timeline = [
            {
                "type": b.behavior_type.value,
                "timestamp": b.timestamp.isoformat(),
                "value": b.value,
            }
            for b in sorted(lead.behaviors, key=lambda b: b.timestamp)
        ]

        return {
            "total_behaviors": len(lead.behaviors),
            "behavior_breakdown": dict(breakdown),
            "timeline": timeline,
            "first_behavior": min(lead.behaviors, key=lambda b: b.timestamp).timestamp.isoformat(),
            "last_behavior": max(lead.behaviors, key=lambda b: b.timestamp).timestamp.isoformat(),
        }

    def find_similar_leads(self, lead: LeadProfile, n: int = 5) -> list[dict[str, Any]]:
        """Find similar leads based on profile and behavior.

        Args:
            lead: The reference lead.
            n: Number of similar leads to return.

        Returns:
            List of similar leads with similarity scores.
        """
        similarities = []
        for other in self.leads.values():
            if other.id == lead.id:
                continue

            # Simple similarity based on industry, size, and behavior overlap
            industry_match = 1.0 if other.industry == lead.industry else 0.0
            size_sim = 1.0 - abs(math.log1p(other.company_size) - math.log1p(lead.company_size)) / 10
            size_sim = max(0, size_sim)

            lead_behaviors = set(b.behavior_type for b in lead.behaviors)
            other_behaviors = set(b.behavior_type for b in other.behaviors)
            behavior_sim = len(lead_behaviors & other_behaviors) / max(len(lead_behaviors | other_behaviors), 1)

            similarity = industry_match * 0.3 + size_sim * 0.3 + behavior_sim * 0.4

            similarities.append({
                "lead_id": other.id,
                "name": other.name,
                "email": other.email,
                "similarity": round(similarity, 4),
                "score": round(other.final_score, 2),
            })

        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:n]


def main() -> None:
    """Run the advanced lead scoring example."""
    logger.info("=" * 60)
    logger.info("Advanced Lead Scoring Example")
    logger.info("=" * 60)

    engine = AdvancedLeadScoringEngine()

    # Register scoring model
    model = ScoringModel(
        name="default",
        model_type=ScoringModelType.ENSEMBLE,
        weights={"demographic": 0.25, "behavioral": 0.35, "predictive": 0.40},
        decay_half_life_days=10.0,
    )
    engine.register_model(model)

    # Create leads
    lead1 = engine.create_lead(
        name="Sarah Chen",
        email="sarah@innovatetech.com",
        company="InnovateTech",
        industry="technology",
        company_size=800,
        job_title="VP of Engineering",
        annual_revenue=25000000.0,
    )

    lead2 = engine.create_lead(
        name="Mike Ross",
        email="mike@startup.io",
        company="StartupIO",
        industry="technology",
        company_size=50,
        job_title="Developer",
        annual_revenue=500000.0,
    )

    lead3 = engine.create_lead(
        name="Jennifer Walsh",
        email="jennifer@globalbank.com",
        company="GlobalBank",
        industry="finance",
        company_size=5000,
        job_title="CTO",
        annual_revenue=500000000.0,
    )

    # Add behaviors for lead1
    now = datetime.now()
    lead1.add_behavior(BehaviorType.PAGE_VIEW, value=1, metadata={"page": "/products"})
    lead1.add_behavior(BehaviorType.PAGE_VIEW, value=1, metadata={"page": "/pricing"})
    lead1.add_behavior(BehaviorType.PRICING_VIEW, value=1)
    lead1.add_behavior(BehaviorType.FORM_SUBMIT, value=1, metadata={"form": "contact"})
    lead1.add_behavior(BehaviorType.CONTENT_DOWNLOAD, value=1, metadata={"content": "whitepaper"})
    lead1.add_behavior(BehaviorType.WEBINAR_ATTEND, value=1, metadata={"webinar": "product-demo"})
    lead1.add_behavior(BehaviorType.DEMO_REQUEST, value=1)
    lead1.add_behavior(BehaviorType.TRIAL_START, value=1)

    # Add behaviors for lead2
    lead2.add_behavior(BehaviorType.PAGE_VIEW, value=1, metadata={"page": "/blog"})
    lead2.add_behavior(BehaviorType.EMAIL_OPEN, value=1)

    # Add behaviors for lead3
    lead3.add_behavior(BehaviorType.PAGE_VIEW, value=1, metadata={"page": "/solutions"})
    lead3.add_behavior(BehaviorType.CASE_STUDY_VIEW, value=1, metadata={"case_study": "fortune500"})
    lead3.add_behavior(BehaviorType.PRICING_VIEW, value=1)
    lead3.add_behavior(BehaviorType.DEMO_REQUEST, value=1)
    lead3.add_behavior(BehaviorType.FORM_SUBMIT, value=1, metadata={"form": "enterprise-contact"})

    # Score all leads
    logger.info("\nScoring Results:")
    logger.info("-" * 60)
    for lead in [lead1, lead2, lead3]:
        scores = engine.score_lead(lead)
        logger.info(
            "%s (%s) - Final: %.1f [Demo: %.1f, Behav: %.1f, Pred: %.1f]",
            lead.name,
            lead.email,
            scores["final"],
            scores["demographic"],
            scores["behavioral"],
            scores["predictive"],
        )

    # Behavioral analytics
    logger.info("\nBehavioral Analytics for %s:", lead1.name)
    analytics = engine.get_behavior_analytics(lead1)
    logger.info("  Total behaviors: %d", analytics["total_behaviors"])
    logger.info("  Breakdown: %s", analytics["behavior_breakdown"])

    # Find similar leads
    logger.info("\nSimilar leads to %s:", lead1.name)
    similar = engine.find_similar_leads(lead1, n=3)
    for s in similar:
        logger.info("  %s (%s) - Similarity: %.2f, Score: %.1f", s["name"], s["email"], s["similarity"], s["score"])

    logger.info("\n" + "=" * 60)
    logger.info("Advanced example complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
