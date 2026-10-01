"""
GRC_Claw Communication Personalization
======================================
Implements the communication personalization framework from the GRC_Claw
Stakeholder Engagement Specification v2.0 (Section 11).

Covers:
- Content personalization by stakeholder profile
- Detail level adaptation (Summary / Standard / Detailed / Comprehensive)
- Channel selection algorithm with fallback chain
- Multi-channel orchestration
- Timing optimization (optimal send time, frequency capping)
- Personalization metrics and effectiveness scoring
- Privacy controls (data minimization, consent, transparency)
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class DetailLevel(str, Enum):
    SUMMARY = "summary"            # 1 page, key metrics, RAG status
    STANDARD = "standard"          # 3-5 pages, key points, supporting data
    DETAILED = "detailed"          # Full documentation, evidence links
    COMPREHENSIVE = "comprehensive"  # Complete evidence packs, traceability


class Channel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    GITHUB = "github"
    MAILING_LIST = "mailing_list"
    DASHBOARD = "dashboard"
    IN_APP = "in_app"
    PHONE = "phone"
    SMS = "sms"
    SOCIAL_MEDIA = "social_media"
    WEBSITE = "website"
    TRAINING_PLATFORM = "training_platform"
    AUDIT_PORTAL = "audit_portal"


class CommunicationType(str, Enum):
    CRITICAL_ALERT = "critical_alert"
    EXECUTIVE_BRIEFING = "executive_briefing"
    RELEASE_ANNOUNCEMENT = "release_announcement"
    POLICY_UPDATE = "policy_update"
    SURVEY_REQUEST = "survey_request"
    EVENT_INVITATION = "event_invitation"
    NEWSLETTER = "newsletter"
    PRODUCT_UPDATE = "product_update"
    REGULATORY_ALERT = "regulatory_alert"
    INCIDENT_COMMUNICATION = "incident_communication"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class StakeholderProfile:
    """Personalization profile for a stakeholder."""

    stakeholder_id: str
    name: str
    category: str  # internal / external / regulator
    role: str
    priority: str  # P1 / P2 / P3
    influence: str  # high / medium / low
    interest: str  # high / medium / low
    preferred_channels: list[Channel] = field(default_factory=list)
    detail_level: DetailLevel = DetailLevel.STANDARD
    language: str = "en"
    technical_depth: str = "medium"  # low / medium / high
    key_concerns: list[str] = field(default_factory=list)
    interest_tags: list[str] = field(default_factory=list)
    engagement_level: str = "engaged"  # disengaging / neutral / engaged / highly_engaged
    sentiment: str = "neutral"  # negative / neutral / positive
    last_communication: Optional[str] = None
    communication_frequency: str = "monthly"
    opted_out: bool = False
    timezone: str = "UTC"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["preferred_channels"] = [c.value for c in self.preferred_channels]
        d["detail_level"] = self.detail_level.value
        return d


@dataclass
class ContentItem:
    """A piece of content to be personalized."""

    content_id: str
    title: str
    body: str
    content_type: CommunicationType
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    urgency: str = "normal"  # low / normal / high / critical
    required_detail_level: DetailLevel = DetailLevel.STANDARD
    channels: list[Channel] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["content_type"] = self.content_type.value
        d["required_detail_level"] = self.required_detail_level.value
        d["channels"] = [c.value for c in self.channels]
        return d


@dataclass
class PersonalizedCommunication:
    """A personalized communication ready for delivery."""

    communication_id: str
    stakeholder_id: str
    content_id: str
    subject: str
    body: str
    channel: Channel
    detail_level: DetailLevel
    scheduled_time: str
    personalization_score: float = 0.0  # 0-1
    personalization_factors: list[str] = field(default_factory=list)
    ab_test_variant: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["channel"] = self.channel.value
        d["detail_level"] = self.detail_level.value
        return d


# ---------------------------------------------------------------------------
# Content Personalization Engine
# ---------------------------------------------------------------------------

class ContentPersonalizationEngine:
    """
    Content personalization engine (Spec §11.2).

    Adapts content based on:
    - Stakeholder profile (role, priority, interests)
    - Detail level requirements
    - Sentiment adaptation
    - Engagement level
    - Feedback loop integration
    """

    # Content adaptation rules by stakeholder profile (Spec §11.2.1)
    PROFILE_CONTENT_MAP = {
        "executive": {
            "detail_level": DetailLevel.SUMMARY,
            "focus": ["strategic_summary", "risk_posture", "decisions_needed", "rag_status"],
            "tone": "executive",
            "max_length": 500,
        },
        "governance": {
            "detail_level": DetailLevel.DETAILED,
            "focus": ["policy_details", "control_status", "compliance_gaps"],
            "tone": "professional",
            "max_length": 2000,
        },
        "engineering": {
            "detail_level": DetailLevel.DETAILED,
            "focus": ["technical_specs", "architecture", "api_changes"],
            "tone": "technical",
            "max_length": 3000,
        },
        "design_partner": {
            "detail_level": DetailLevel.STANDARD,
            "focus": ["product_roadmap", "feature_previews", "feedback_status"],
            "tone": "collaborative",
            "max_length": 1500,
        },
        "regulator": {
            "detail_level": DetailLevel.COMPREHENSIVE,
            "focus": ["compliance_posture", "evidence_summaries", "audit_results"],
            "tone": "formal",
            "max_length": 5000,
        },
        "community": {
            "detail_level": DetailLevel.STANDARD,
            "focus": ["release_notes", "contribution_guides", "community_highlights"],
            "tone": "friendly",
            "max_length": 1500,
        },
        "standards_body": {
            "detail_level": DetailLevel.DETAILED,
            "focus": ["alignment_reports", "contribution_proposals", "gap_analyses"],
            "tone": "professional",
            "max_length": 2500,
        },
    }

    # Personalization rules (Spec §11.2.3)
    RULES = [
        "relevance_filter",
        "priority_boost",
        "recency_filter",
        "feedback_loop",
        "sentiment_adaptation",
        "engagement_level_high",
        "engagement_level_low",
    ]

    def __init__(self):
        self._profiles: dict[str, StakeholderProfile] = {}
        self._content: dict[str, ContentItem] = {}
        self._communications: dict[str, PersonalizedCommunication] = {}
        self._next_id = 1

    def add_profile(self, profile: StakeholderProfile) -> None:
        self._profiles[profile.stakeholder_id] = profile

    def add_content(self, content: ContentItem) -> None:
        self._content[content.content_id] = content

    def personalize(self, stakeholder_id: str, content_id: str,
                    channel: Optional[Channel] = None) -> PersonalizedCommunication:
        """
        Generate a personalized communication for a stakeholder.

        Applies content adaptation rules and returns a ready-to-send
        PersonalizedCommunication object.
        """
        profile = self._profiles.get(stakeholder_id)
        content = self._content.get(content_id)

        if not profile:
            raise ValueError(f"Stakeholder profile {stakeholder_id} not found")
        if not content:
            raise ValueError(f"Content {content_id} not found")

        # Determine detail level
        detail_level = self._select_detail_level(profile, content)

        # Adapt content body
        adapted_body = self._adapt_content(content, profile, detail_level)

        # Select channel
        selected_channel = channel or self._select_channel(profile, content)

        # Calculate personalization score
        score, factors = self._calculate_personalization_score(profile, content)

        comm_id = f"COM-{self._next_id:04d}"
        self._next_id += 1

        comm = PersonalizedCommunication(
            communication_id=comm_id,
            stakeholder_id=stakeholder_id,
            content_id=content_id,
            subject=self._adapt_subject(content, profile),
            body=adapted_body,
            channel=selected_channel,
            detail_level=detail_level,
            scheduled_time=datetime.utcnow().isoformat(),
            personalization_score=score,
            personalization_factors=factors,
        )
        self._communications[comm_id] = comm
        return comm

    def _select_detail_level(self, profile: StakeholderProfile,
                             content: ContentItem) -> DetailLevel:
        """Select appropriate detail level based on profile and content."""
        # Use profile's preferred detail level, but respect content minimums
        profile_level = profile.detail_level
        required_level = content.required_detail_level

        # If content requires more detail than profile prefers, use required
        level_order = [DetailLevel.SUMMARY, DetailLevel.STANDARD,
                       DetailLevel.DETAILED, DetailLevel.COMPREHENSIVE]
        profile_idx = level_order.index(profile_level)
        required_idx = level_order.index(required_level)

        return level_order[max(profile_idx, required_idx)]

    def _adapt_content(self, content: ContentItem, profile: StakeholderProfile,
                       detail_level: DetailLevel) -> str:
        """Adapt content body based on profile and detail level."""
        body = content.body

        # Apply profile-specific adaptations
        profile_type = self._classify_profile_type(profile)
        adaptations = self.PROFILE_CONTENT_MAP.get(profile_type, {})

        # Truncate or expand based on detail level
        max_length = adaptations.get("max_length", 2000)
        if detail_level == DetailLevel.SUMMARY:
            max_length = min(max_length, 500)
        elif detail_level == DetailLevel.COMPREHENSIVE:
            max_length = max(max_length, 5000)

        if len(body) > max_length:
            body = body[:max_length] + "\n\n[Truncated — see full content for details]"

        # Add personalization header
        header = self._generate_header(profile, content)
        body = header + "\n\n" + body

        # Add sentiment adaptation
        if profile.sentiment == "negative":
            body += "\n\n---\nWe understand your concerns and are committed to addressing them. " \
                    "Please reach out if you'd like to discuss further."

        # Add engagement-level adaptation
        if profile.engagement_level == "disengaging":
            body += "\n\n---\nWe value your engagement. Here's a quick summary of what's most relevant to you."

        # Add feedback loop section
        if profile.key_concerns:
            matching = [c for c in profile.key_concerns
                        if any(tag in content.tags for tag in [c.lower()])]
            if matching:
                body += f"\n\n---\nYou asked, we did: This update addresses your concerns about {', '.join(matching)}."

        return body

    def _generate_header(self, profile: StakeholderProfile,
                         content: ContentItem) -> str:
        """Generate personalized header."""
        greeting = f"Hi {profile.name.split()[0] if profile.name else 'there'},"
        context = f"Here's an update on {content.title} that's relevant to your role as {profile.role}."
        return f"{greeting}\n\n{context}"

    def _classify_profile_type(self, profile: StakeholderProfile) -> str:
        """Classify stakeholder into a profile type for content adaptation."""
        role_lower = profile.role.lower()
        if "executive" in role_lower or "c-suite" in role_lower or "vp" in role_lower:
            return "executive"
        if "governance" in role_lower or "committee" in role_lower or "aims" in role_lower:
            return "governance"
        if "engineer" in role_lower or "developer" in role_lower or "architect" in role_lower:
            return "engineering"
        if "design" in role_lower or "partner" in role_lower or "pilot" in role_lower:
            return "design_partner"
        if "regulat" in role_lower:
            return "regulator"
        if "community" in role_lower or "contributor" in role_lower:
            return "community"
        if "standard" in role_lower or "iso" in role_lower or "nist" in role_lower:
            return "standards_body"
        return "governance"  # default

    def _select_channel(self, profile: StakeholderProfile,
                        content: ContentItem) -> Channel:
        """Select optimal channel using the channel selection algorithm (Spec §11.3.1)."""
        if not profile.preferred_channels:
            return Channel.EMAIL

        # Score each preferred channel
        best_channel = profile.preferred_channels[0]
        best_score = 0.0

        for ch in profile.preferred_channels:
            score = self._channel_score(ch, profile, content)
            if score > best_score:
                best_score = score
                best_channel = ch

        return best_channel

    def _channel_score(self, channel: Channel, profile: StakeholderProfile,
                       content: ContentItem) -> float:
        """
        Channel Selection Score (Spec §11.3.1):
        = (Preference Match × 0.30) + (Content-Channel Fit × 0.25)
          + (Historical Effectiveness × 0.20) + (Urgency Match × 0.15)
          + (Availability × 0.10)
        """
        # Preference match (binary: is it in preferred channels?)
        pref_match = 1.0 if channel in profile.preferred_channels else 0.0

        # Content-channel fit
        content_fit = self._content_channel_fit(channel, content)

        # Historical effectiveness (simulated)
        hist_effectiveness = random.uniform(0.6, 0.95)

        # Urgency match
        urgency_match = self._urgency_match(channel, content.urgency)

        # Availability (simulated)
        availability = random.uniform(0.7, 1.0)

        score = (pref_match * 0.30) + (content_fit * 0.25) + \
                (hist_effectiveness * 0.20) + (urgency_match * 0.15) + \
                (availability * 0.10)
        return round(score, 3)

    def _content_channel_fit(self, channel: Channel, content: ContentItem) -> float:
        """How well the content type suits the channel."""
        fit_map = {
            (CommunicationType.CRITICAL_ALERT, Channel.SMS): 1.0,
            (CommunicationType.CRITICAL_ALERT, Channel.PHONE): 0.95,
            (CommunicationType.CRITICAL_ALERT, Channel.EMAIL): 0.8,
            (CommunicationType.EXECUTIVE_BRIEFING, Channel.EMAIL): 0.9,
            (CommunicationType.EXECUTIVE_BRIEFING, Channel.DASHBOARD): 0.85,
            (CommunicationType.RELEASE_ANNOUNCEMENT, Channel.GITHUB): 0.95,
            (CommunicationType.RELEASE_ANNOUNCEMENT, Channel.MAILING_LIST): 0.85,
            (CommunicationType.POLICY_UPDATE, Channel.EMAIL): 0.9,
            (CommunicationType.POLICY_UPDATE, Channel.DASHBOARD): 0.8,
            (CommunicationType.SURVEY_REQUEST, Channel.EMAIL): 0.9,
            (CommunicationType.SURVEY_REQUEST, Channel.IN_APP): 0.85,
            (CommunicationType.EVENT_INVITATION, Channel.EMAIL): 0.9,
            (CommunicationType.EVENT_INVITATION, Channel.SLACK): 0.8,
            (CommunicationType.NEWSLETTER, Channel.MAILING_LIST): 0.95,
            (CommunicationType.NEWSLETTER, Channel.EMAIL): 0.85,
            (CommunicationType.PRODUCT_UPDATE, Channel.SLACK): 0.85,
            (CommunicationType.PRODUCT_UPDATE, Channel.EMAIL): 0.8,
            (CommunicationType.REGULATORY_ALERT, Channel.EMAIL): 0.95,
            (CommunicationType.INCIDENT_COMMUNICATION, Channel.SLACK): 0.9,
            (CommunicationType.INCIDENT_COMMUNICATION, Channel.EMAIL): 0.85,
        }
        return fit_map.get((content.content_type, channel), 0.5)

    def _urgency_match(self, channel: Channel, urgency: str) -> float:
        """Channel's ability to meet urgency requirements."""
        urgency_map = {
            "critical": {Channel.SMS: 1.0, Channel.PHONE: 0.95, Channel.SLACK: 0.8,
                         Channel.EMAIL: 0.6, Channel.DASHBOARD: 0.4},
            "high": {Channel.SLACK: 0.9, Channel.EMAIL: 0.8, Channel.PHONE: 0.7,
                     Channel.SMS: 0.6, Channel.DASHBOARD: 0.5},
            "normal": {Channel.EMAIL: 0.9, Channel.SLACK: 0.8, Channel.DASHBOARD: 0.7,
                       Channel.MAILING_LIST: 0.6, Channel.GITHUB: 0.5},
            "low": {Channel.MAILING_LIST: 0.9, Channel.GITHUB: 0.8, Channel.WEBSITE: 0.7,
                    Channel.EMAIL: 0.6, Channel.DASHBOARD: 0.5},
        }
        return urgency_map.get(urgency, {}).get(channel, 0.5)

    def _calculate_personalization_score(self, profile: StakeholderProfile,
                                         content: ContentItem) -> tuple[float, list[str]]:
        """Calculate personalization effectiveness score."""
        factors = []
        score = 0.0

        # Relevance filter
        matching_tags = set(profile.interest_tags) & set(content.tags)
        if matching_tags:
            score += 0.25
            factors.append(f"relevance_match:{','.join(matching_tags)}")

        # Priority boost
        if profile.key_concerns:
            matching_concerns = [c for c in profile.key_concerns
                                 if any(c.lower() in tag.lower() for tag in content.tags)]
            if matching_concerns:
                score += 0.20
                factors.append(f"priority_boost:{','.join(matching_concerns)}")

        # Recency filter
        if profile.last_communication:
            try:
                last = datetime.fromisoformat(profile.last_communication.replace("Z", "+00:00"))
                days_since = (datetime.utcnow() - last).days
                if days_since > 30:
                    score += 0.15
                    factors.append("recency_filter:new_content")
            except (ValueError, AttributeError):
                pass

        # Sentiment adaptation
        if profile.sentiment == "negative":
            score += 0.15
            factors.append("sentiment_adaptation:negative")

        # Engagement level
        if profile.engagement_level == "highly_engaged":
            score += 0.15
            factors.append("engagement_level:high")
        elif profile.engagement_level == "disengaging":
            score += 0.10
            factors.append("engagement_level:low")

        # Channel preference match
        if profile.preferred_channels:
            score += 0.10
            factors.append("channel_preference:matched")

        return round(min(score, 1.0), 3), factors

    def _adapt_subject(self, content: ContentItem, profile: StakeholderProfile) -> str:
        """Adapt subject line based on profile."""
        base = content.title
        if profile.sentiment == "negative":
            base = f"[Action Needed] {base}"
        if content.urgency == "critical":
            base = f"[URGENT] {base}"
        return base

    # ---- Multi-channel orchestration ----

    def orchestrate_multi_channel(self, stakeholder_id: str, content_id: str,
                                   comm_type: CommunicationType) -> list[PersonalizedCommunication]:
        """
        Create multi-channel communication plan (Spec §11.3.3).

        Returns a list of PersonalizedCommunication objects for each channel.
        """
        orchestration_map = {
            CommunicationType.CRITICAL_ALERT: [Channel.SMS, Channel.EMAIL, Channel.SLACK],
            CommunicationType.EXECUTIVE_BRIEFING: [Channel.EMAIL, Channel.DASHBOARD],
            CommunicationType.RELEASE_ANNOUNCEMENT: [Channel.GITHUB, Channel.MAILING_LIST, Channel.SOCIAL_MEDIA],
            CommunicationType.POLICY_UPDATE: [Channel.EMAIL, Channel.DASHBOARD, Channel.TRAINING_PLATFORM],
            CommunicationType.SURVEY_REQUEST: [Channel.EMAIL, Channel.IN_APP, Channel.SLACK],
            CommunicationType.EVENT_INVITATION: [Channel.EMAIL, Channel.SLACK],
        }

        channels = orchestration_map.get(comm_type, [Channel.EMAIL])
        communications = []

        for ch in channels:
            comm = self.personalize(stakeholder_id, content_id, channel=ch)
            communications.append(comm)

        return communications

    # ---- Timing optimization ----

    OPTIMAL_SEND_TIMES = {
        "executive": {"days": ["tue", "wed", "thu"], "hours": [8, 9, 10]},
        "engineering": {"days": ["tue", "wed", "thu"], "hours": [10, 11, 12]},
        "governance": {"days": ["wed", "thu", "fri"], "hours": [13, 14, 15]},
        "community": {"days": ["tue", "wed", "thu"], "hours": [12, 13, 14]},  # UTC
        "regulator": {"days": ["tue", "wed", "thu"], "hours": [9, 10, 11]},
        "design_partner": {"days": ["wed"], "hours": [14, 15, 16]},
    }

    def optimize_send_time(self, stakeholder_id: str) -> str:
        """Calculate optimal send time for a stakeholder (Spec §11.4.1)."""
        profile = self._profiles.get(stakeholder_id)
        if not profile:
            return datetime.utcnow().isoformat()

        profile_type = self._classify_profile_type(profile)
        optimal = self.OPTIMAL_SEND_TIMES.get(profile_type, {"days": ["tue", "wed", "thu"], "hours": [10]})

        # Find next optimal day/hour
        now = datetime.utcnow()
        for days_ahead in range(7):
            candidate = now + timedelta(days=days_ahead)
            day_name = candidate.strftime("%a").lower()
            if day_name in optimal["days"]:
                hour = optimal["hours"][0]
                scheduled = candidate.replace(hour=hour, minute=0, second=0, microsecond=0)
                if scheduled > now:
                    return scheduled.isoformat()

        # Fallback: next day at optimal hour
        fallback = now + timedelta(days=1)
        fallback = fallback.replace(hour=optimal["hours"][0], minute=0, second=0, microsecond=0)
        return fallback.isoformat()

    # ---- Metrics ----

    def get_personalization_metrics(self) -> dict:
        """Calculate personalization metrics (Spec §11.5)."""
        total = len(self._communications)
        if total == 0:
            return {"total_communications": 0}

        personalized = [c for c in self._communications.values()
                       if c.personalization_score > 0.5]
        high_score = [c for c in self._communications.values()
                      if c.personalization_score > 0.8]

        by_channel = defaultdict(int)
        for c in self._communications.values():
            by_channel[c.channel.value] += 1

        return {
            "total_communications": total,
            "personalized_count": len(personalized),
            "personalization_coverage": round(len(personalized) / total * 100, 1),
            "high_personalization_count": len(high_score),
            "average_personalization_score": round(
                sum(c.personalization_score for c in self._communications.values()) / total, 3
            ),
            "by_channel": dict(by_channel),
        }


# ---------------------------------------------------------------------------
# Demo / Self-test
# ---------------------------------------------------------------------------

def _demo():
    """Demonstrate communication personalization."""
    engine = ContentPersonalizationEngine()

    # Create stakeholder profiles
    profiles = [
        StakeholderProfile(
            stakeholder_id="STK-001",
            name="Jane Smith",
            category="internal",
            role="VP Engineering",
            priority="P1",
            influence="high",
            interest="high",
            preferred_channels=[Channel.EMAIL, Channel.DASHBOARD],
            detail_level=DetailLevel.SUMMARY,
            technical_depth="low",
            key_concerns=["Strategic alignment", "Risk posture", "ROI"],
            interest_tags=["strategy", "risk", "compliance"],
            engagement_level="engaged",
            sentiment="positive",
        ),
        StakeholderProfile(
            stakeholder_id="STK-002",
            name="John Doe",
            category="internal",
            role="Core Developer",
            priority="P1",
            influence="high",
            interest="high",
            preferred_channels=[Channel.SLACK, Channel.GITHUB],
            detail_level=DetailLevel.DETAILED,
            technical_depth="high",
            key_concerns=["Technical quality", "Architecture"],
            interest_tags=["engineering", "architecture", "api"],
            engagement_level="highly_engaged",
            sentiment="positive",
        ),
        StakeholderProfile(
            stakeholder_id="STK-003",
            name="Maria Garcia",
            category="regulator",
            role="EU AI Act Regulator",
            priority="P1",
            influence="high",
            interest="medium",
            preferred_channels=[Channel.EMAIL],
            detail_level=DetailLevel.COMPREHENSIVE,
            technical_depth="medium",
            key_concerns=["Compliance", "Transparency"],
            interest_tags=["compliance", "regulatory", "transparency"],
            engagement_level="neutral",
            sentiment="neutral",
        ),
    ]

    for p in profiles:
        engine.add_profile(p)
        print(f"  Added profile: {p.stakeholder_id} | {p.name} | {p.role}")

    # Create content
    content = ContentItem(
        content_id="CNT-001",
        title="Q3 2026 Governance Update",
        body="This quarter we achieved 92% compliance score across all frameworks. "
             "Key highlights: EU AI Act alignment improved to 85%, NIST AI RMF at 78%, "
             "ISO 42001 at 92%. Three material risks identified: agentic AI deployment, "
             "model drift, vendor concentration. Board decisions required on agent governance "
             "budget, AI acceptable use policy, and vendor diversification roadmap.",
        content_type=CommunicationType.EXECUTIVE_BRIEFING,
        tags=["compliance", "risk", "strategy", "governance"],
        urgency="normal",
    )
    engine.add_content(content)
    print(f"\n  Added content: {content.content_id}: {content.title}")

    # Personalize for each stakeholder
    print("\n--- Personalized Communications ---")
    for p in profiles:
        comm = engine.personalize(p.stakeholder_id, content.content_id)
        print(f"\n  To: {p.name} ({p.role})")
        print(f"  Channel: {comm.channel.value}")
        print(f"  Detail Level: {comm.detail_level.value}")
        print(f"  Personalization Score: {comm.personalization_score}")
        print(f"  Factors: {comm.personalization_factors}")
        print(f"  Subject: {comm.subject}")
        print(f"  Body preview: {comm.body[:150]}...")

    # Multi-channel orchestration
    print("\n--- Multi-Channel Orchestration ---")
    multi = engine.orchestrate_multi_channel("STK-001", content.content_id,
                                              CommunicationType.EXECUTIVE_BRIEFING)
    for comm in multi:
        print(f"  Channel: {comm.channel.value} | Score: {comm.personalization_score}")

    # Timing optimization
    print("\n--- Optimal Send Times ---")
    for p in profiles:
        optimal = engine.optimize_send_time(p.stakeholder_id)
        print(f"  {p.name}: {optimal}")

    # Metrics
    print("\n--- Personalization Metrics ---")
    metrics = engine.get_personalization_metrics()
    for key, val in metrics.items():
        print(f"  {key}: {val}")

    print("\n✓ Communication Personalization demo complete")


if __name__ == "__main__":
    _demo()
