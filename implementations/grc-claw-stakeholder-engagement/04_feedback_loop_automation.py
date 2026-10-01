"""
GRC_Claw Feedback Loop Automation
==================================
Implements the 7-stage feedback loop from the GRC_Claw Stakeholder
Engagement Specification v2.0 (Section 5, 12).

Covers:
- 7-stage feedback loop: Collect → Triage → Adjudicate → Route → Execute → Verify → Learn
- Feedback intake from multiple channels
- Automated triage with priority scoring (Spec §5.3.1)
- Deduplication and similarity matching
- Auto-classification and auto-routing
- Feedback loop metrics and bottleneck analysis
- Maturity model assessment (5 levels per Spec §12.4)
- Integration with CI Framework 8-stage self-healing loop
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from collections import defaultdict
from difflib import SequenceMatcher


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class FeedbackSource(str, Enum):
    GITHUB = "github"
    GITHUB_DISCUSSION = "github_discussion"
    SURVEY = "survey"
    INTERVIEW = "interview"
    SLACK = "slack"
    EMAIL = "email"
    STEERING_COMMITTEE = "steering_committee"
    RFC = "rfc"
    TRAINING = "training"
    INCIDENT = "incident"
    REGULATORY = "regulatory"
    OTHER = "other"


class FeedbackType(str, Enum):
    PRODUCT = "product"
    GOVERNANCE = "governance"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    COMMUNITY = "community"
    TRAINING = "training"
    STRATEGIC = "strategic"


class FeedbackStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    ADJUDICATED = "adjudicated"
    ROUTED = "routed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DEFERRED = "deferred"


class FeedbackClassification(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FeedbackDecision(str, Enum):
    ACCEPT = "accept"
    DEFER = "defer"
    REJECT = "reject"
    MERGE = "merge"


class Workstream(str, Enum):
    PRODUCT = "product"
    ENGINEERING = "engineering"
    GOVERNANCE = "governance"
    LEGAL = "legal"
    EXECUTIVE = "executive"
    SECURITY = "security"
    COMMUNITY = "community"
    TRAINING = "training"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class FeedbackItem:
    """
    Single feedback item matching the schema in Appendix C of the spec.
    """

    feedback_id: str
    timestamp: str
    source: FeedbackSource
    stakeholder_id: str
    stakeholder_category: str  # internal / external / regulator
    feedback_type: FeedbackType
    priority_score: int  # 1-60
    classification: FeedbackClassification
    title: str
    description: str
    impact_assessment: str = ""
    decision: Optional[FeedbackDecision] = None
    decision_rationale: str = ""
    assigned_to: Optional[str] = None  # workstream-id
    assigned_owner: Optional[str] = None  # person-id
    due_date: Optional[str] = None
    status: FeedbackStatus = FeedbackStatus.NEW
    resolution: str = ""
    resolution_verified_by: Optional[str] = None
    resolution_date: Optional[str] = None
    learning_captured: bool = False
    related_feedback: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    # Triage scoring components
    impact: int = 5  # 1-10
    urgency: int = 5  # 1-10
    strategic_alignment: int = 5  # 1-10
    feasibility: int = 5  # 1-10
    risk: int = 5  # 1-10
    # Automation metadata
    auto_classified: bool = False
    auto_routed: bool = False
    duplicate_of: Optional[str] = None
    sentiment: str = "neutral"  # positive / neutral / negative

    def to_dict(self) -> dict:
        d = asdict(self)
        d["source"] = self.source.value
        d["feedback_type"] = self.feedback_type.value
        d["classification"] = self.classification.value
        d["status"] = self.status.value
        if self.decision:
            d["decision"] = self.decision.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> FeedbackItem:
        data["source"] = FeedbackSource(data["source"])
        data["feedback_type"] = FeedbackType(data["feedback_type"])
        data["classification"] = FeedbackClassification(data["classification"])
        data["status"] = FeedbackStatus(data["status"])
        if data.get("decision"):
            data["decision"] = FeedbackDecision(data["decision"])
        return cls(**data)


# ---------------------------------------------------------------------------
# Feedback Loop Engine
# ---------------------------------------------------------------------------

class FeedbackLoopEngine:
    """
    7-stage feedback loop engine (Spec §5.1, §5.3).

    Stages:
    1. COLLECT  — Log in feedback registry, assign ID
    2. TRIAGE   — Deduplicate, validate, enrich, score
    3. ADJUDICATE — Classify, assess merit, decide action
    4. ROUTE    — Assign to workstream with owner + deadline
    5. EXECUTE  — Implement, communicate progress
    6. VERIFY   — Confirm resolution with stakeholder
    7. LEARN    — Update knowledge base, training, policies
    """

    # Priority score thresholds (Spec §5.3.1)
    PRIORITY_THRESHOLDS = {
        FeedbackClassification.CRITICAL: (40, 60),
        FeedbackClassification.HIGH: (25, 39),
        FeedbackClassification.MEDIUM: (10, 24),
        FeedbackClassification.LOW: (1, 9),
    }

    # Auto-routing rules (Spec §12.2.1)
    ROUTING_RULES = {
        FeedbackType.PRODUCT: Workstream.PRODUCT,
        FeedbackType.GOVERNANCE: Workstream.GOVERNANCE,
        FeedbackType.COMPLIANCE: Workstream.GOVERNANCE,
        FeedbackType.SECURITY: Workstream.SECURITY,
        FeedbackType.COMMUNITY: Workstream.COMMUNITY,
        FeedbackType.TRAINING: Workstream.TRAINING,
        FeedbackType.STRATEGIC: Workstream.EXECUTIVE,
    }

    # Response SLAs by source (Spec §5.2)
    RESPONSE_SLA_DAYS = {
        FeedbackSource.GITHUB: 5,
        FeedbackSource.GITHUB_DISCUSSION: 3,
        FeedbackSource.SURVEY: 0,  # N/A (batch)
        FeedbackSource.INTERVIEW: 2,
        FeedbackSource.SLACK: 1,
        FeedbackSource.EMAIL: 3,
        FeedbackSource.STEERING_COMMITTEE: 1,
        FeedbackSource.RFC: 10,
        FeedbackSource.TRAINING: 0,
        FeedbackSource.INCIDENT: 14,
        FeedbackSource.REGULATORY: 0,
        FeedbackSource.OTHER: 5,
    }

    def __init__(self):
        self._feedback: dict[str, FeedbackItem] = {}
        self._next_id = 1

    # ---- Stage 1: COLLECT ----

    def collect(self, source: FeedbackSource, stakeholder_id: str,
                stakeholder_category: str, title: str, description: str,
                feedback_type: FeedbackType = FeedbackType.PRODUCT,
                tags: list[str] | None = None,
                related_feedback: list[str] | None = None) -> FeedbackItem:
        """Stage 1: Intake and log feedback."""
        fb_id = f"FB-{self._next_id:05d}"
        self._next_id += 1

        item = FeedbackItem(
            feedback_id=fb_id,
            timestamp=datetime.utcnow().isoformat(),
            source=source,
            stakeholder_id=stakeholder_id,
            stakeholder_category=stakeholder_category,
            feedback_type=feedback_type,
            priority_score=0,
            classification=FeedbackClassification.LOW,
            title=title,
            description=description,
            tags=tags or [],
            related_feedback=related_feedback or [],
        )
        self._feedback[fb_id] = item
        return item

    # ---- Stage 2: TRIAGE ----

    def triage(self, feedback_id: str, impact: int, urgency: int,
               strategic_alignment: int, feasibility: int, risk: int) -> FeedbackItem:
        """
        Stage 2: Triage and score feedback.

        Priority Score = (Impact × 2) + (Urgency × 2) + Strategic Alignment + Feasibility + Risk
        Range: 1-60
        """
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")

        # Clamp values to 1-10
        impact = max(1, min(10, impact))
        urgency = max(1, min(10, urgency))
        strategic_alignment = max(1, min(10, strategic_alignment))
        feasibility = max(1, min(10, feasibility))
        risk = max(1, min(10, risk))

        score = (impact * 2) + (urgency * 2) + strategic_alignment + feasibility + risk

        item.impact = impact
        item.urgency = urgency
        item.strategic_alignment = strategic_alignment
        item.feasibility = feasibility
        item.risk = risk
        item.priority_score = score
        item.classification = self._classify_priority(score)
        item.status = FeedbackStatus.TRIAGED

        return item

    def _classify_priority(self, score: int) -> FeedbackClassification:
        """Classify priority score (Spec §5.3.1)."""
        if score >= 40:
            return FeedbackClassification.CRITICAL
        elif score >= 25:
            return FeedbackClassification.HIGH
        elif score >= 10:
            return FeedbackClassification.MEDIUM
        else:
            return FeedbackClassification.LOW

    def auto_triage(self, feedback_id: str) -> FeedbackItem:
        """
        Automated triage using keyword-based classification (Spec §12.2.1).

        Uses simple keyword matching to estimate triage scores.
        """
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")

        text = f"{item.title} {item.description}".lower()

        # Keyword-based scoring
        impact = 5
        urgency = 5
        strategic = 5
        feasibility = 5
        risk = 5

        # Impact keywords
        if any(w in text for w in ["all", "everyone", "enterprise", "critical", "security"]):
            impact = 9
        elif any(w in text for w in ["many", "several", "team", "department"]):
            impact = 7
        elif any(w in text for w in ["some", "few", "individual"]):
            impact = 3

        # Urgency keywords
        if any(w in text for w in ["urgent", "asap", "immediately", "blocking", "down"]):
            urgency = 9
        elif any(w in text for w in ["soon", "next", "upcoming", "deadline"]):
            urgency = 7
        elif any(w in text for w in ["eventually", "someday", "nice to have"]):
            urgency = 2

        # Strategic alignment
        if any(w in text for w in ["strategy", "mission", "vision", "core", "goal"]):
            strategic = 9
        elif any(w in text for w in ["improvement", "enhancement", "optimization"]):
            strategic = 7

        # Feasibility
        if any(w in text for w in ["simple", "easy", "trivial", "quick", "small"]):
            feasibility = 9
        elif any(w in text for w in ["complex", "difficult", "large", "major", "architectural"]):
            feasibility = 3

        # Risk
        if any(w in text for w in ["security", "vulnerability", "breach", "compliance", "regulatory"]):
            risk = 9
        elif any(w in text for w in ["risk", "issue", "problem", "concern"]):
            risk = 7

        item.auto_classified = True
        return self.triage(feedback_id, impact, urgency, strategic, feasibility, risk)

    def deduplicate(self, feedback_id: str) -> Optional[str]:
        """
        Detect duplicate or related feedback (Spec §12.2.1).

        Returns the ID of the duplicate if found, None otherwise.
        """
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")

        best_match = None
        best_score = 0.0

        for other_id, other in self._feedback.items():
            if other_id == feedback_id:
                continue

            # Title similarity
            title_sim = SequenceMatcher(None, item.title.lower(), other.title.lower()).ratio()
            # Description similarity
            desc_sim = SequenceMatcher(None, item.description.lower(), other.description.lower()).ratio()

            score = (title_sim * 0.6) + (desc_sim * 0.4)
            if score > best_score and score >= 0.75:
                best_score = score
                best_match = other_id

        if best_match:
            item.duplicate_of = best_match
            item.related_feedback.append(best_match)

        return best_match

    # ---- Stage 3: ADJUDICATE ----

    def adjudicate(self, feedback_id: str, decision: FeedbackDecision,
                   rationale: str, assigned_to: Workstream,
                   assigned_owner: str, due_date: str) -> FeedbackItem:
        """Stage 3: Adjudicate and decide action."""
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")

        item.decision = decision
        item.decision_rationale = rationale
        item.assigned_to = assigned_to.value
        item.assigned_owner = assigned_owner
        item.due_date = due_date
        item.status = FeedbackStatus.ADJUDICATED

        return item

    def auto_adjudicate(self, feedback_id: str) -> FeedbackItem:
        """
        Automated adjudication based on classification (Spec §12.2.1).

        Critical → Accept + escalate
        High     → Accept
        Medium   → Defer to next planning cycle
        Low      → Defer to backlog
        """
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")

        if item.classification == FeedbackClassification.CRITICAL:
            decision = FeedbackDecision.ACCEPT
            rationale = "Critical priority — immediate action required"
        elif item.classification == FeedbackClassification.HIGH:
            decision = FeedbackDecision.ACCEPT
            rationale = "High priority — route to relevant workstream"
        elif item.classification == FeedbackClassification.MEDIUM:
            decision = FeedbackDecision.DEFER
            rationale = "Medium priority — add to backlog for next planning cycle"
        else:
            decision = FeedbackDecision.DEFER
            rationale = "Low priority — add to backlog; review quarterly"

        # Auto-route to workstream
        workstream = self.ROUTING_RULES.get(item.feedback_type, Workstream.PRODUCT)

        # Calculate due date based on classification
        days_map = {
            FeedbackClassification.CRITICAL: 2,
            FeedbackClassification.HIGH: 14,
            FeedbackClassification.MEDIUM: 90,
            FeedbackClassification.LOW: 180,
        }
        due = datetime.utcnow() + timedelta(days=days_map.get(item.classification, 90))

        item.auto_routed = True
        return self.adjudicate(feedback_id, decision, rationale,
                               workstream, "auto-assigner", due.isoformat())

    # ---- Stage 4: ROUTE ----

    def route(self, feedback_id: str, workstream: Workstream,
              owner: str, due_date: str) -> FeedbackItem:
        """Stage 4: Route to workstream with owner and deadline."""
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")

        item.assigned_to = workstream.value
        item.assigned_owner = owner
        item.due_date = due_date
        item.status = FeedbackStatus.ROUTED
        return item

    # ---- Stage 5: EXECUTE ----

    def start_execution(self, feedback_id: str) -> FeedbackItem:
        """Stage 5: Begin implementation."""
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")
        item.status = FeedbackStatus.IN_PROGRESS
        return item

    # ---- Stage 6: VERIFY ----

    def resolve(self, feedback_id: str, resolution: str,
                verified_by: str) -> FeedbackItem:
        """Stage 6: Mark as resolved with verification."""
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")

        item.resolution = resolution
        item.resolution_verified_by = verified_by
        item.resolution_date = datetime.utcnow().isoformat()
        item.status = FeedbackStatus.RESOLVED
        return item

    def close(self, feedback_id: str) -> FeedbackItem:
        """Close feedback after verification."""
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")
        item.status = FeedbackStatus.CLOSED
        return item

    # ---- Stage 7: LEARN ----

    def capture_learning(self, feedback_id: str) -> FeedbackItem:
        """Stage 7: Capture learning from resolved feedback."""
        item = self._feedback.get(feedback_id)
        if not item:
            raise KeyError(f"Feedback {feedback_id} not found")
        item.learning_captured = True
        return item

    # ---- Full Auto-Processing ----

    def process_auto(self, feedback_id: str) -> FeedbackItem:
        """
        Run full auto-processing pipeline:
        Auto-triage → Deduplicate → Auto-adjudicate → Auto-route
        """
        self.auto_triage(feedback_id)
        self.deduplicate(feedback_id)
        self.auto_adjudicate(feedback_id)
        return self._feedback[feedback_id]

    # ---- Metrics ----

    def get_metrics(self) -> dict:
        """
        Calculate feedback loop metrics (Spec §5.5, §12.1).
        """
        total = len(self._feedback)
        if total == 0:
            return {"total": 0}

        by_status = defaultdict(int)
        by_source = defaultdict(int)
        by_type = defaultdict(int)
        by_classification = defaultdict(int)

        resolved = 0
        within_sla = 0
        with_learning = 0
        auto_processed = 0
        resolution_times = []

        now = datetime.utcnow()

        for item in self._feedback.values():
            by_status[item.status.value] += 1
            by_source[item.source.value] += 1
            by_type[item.feedback_type.value] += 1
            by_classification[item.classification.value] += 1

            if item.status in (FeedbackStatus.RESOLVED, FeedbackStatus.CLOSED):
                resolved += 1
                if item.resolution_date and item.timestamp:
                    try:
                        created = datetime.fromisoformat(item.timestamp.replace("Z", "+00:00"))
                        resolved_dt = datetime.fromisoformat(item.resolution_date.replace("Z", "+00:00"))
                        resolution_times.append((resolved_dt - created).days)
                    except (ValueError, AttributeError):
                        pass

            if item.learning_captured:
                with_learning += 1

            if item.auto_classified:
                auto_processed += 1

            # SLA check
            sla_days = self.RESPONSE_SLA_DAYS.get(item.source, 5)
            if sla_days > 0 and item.timestamp:
                try:
                    created = datetime.fromisoformat(item.timestamp.replace("Z", "+00:00"))
                    if (now - created).days <= sla_days:
                        within_sla += 1
                except (ValueError, AttributeError):
                    pass

        median_resolution = sorted(resolution_times)[len(resolution_times) // 2] if resolution_times else 0

        return {
            "total_feedback": total,
            "by_status": dict(by_status),
            "by_source": dict(by_source),
            "by_type": dict(by_type),
            "by_classification": dict(by_classification),
            "resolution_rate": round(resolved / total * 100, 1),
            "response_rate_within_sla": round(within_sla / total * 100, 1),
            "learning_capture_rate": round(with_learning / total * 100, 1),
            "automation_rate": round(auto_processed / total * 100, 1),
            "median_resolution_days": median_resolution,
        }

    def bottleneck_analysis(self) -> dict:
        """
        Identify bottlenecks in the feedback loop (Spec §12.1.2).

        A bottleneck is detected when:
        - Stage time > 2× median
        - Queue depth > 3× average
        """
        stage_counts = defaultdict(int)
        stage_times = defaultdict(list)

        for item in self._feedback.values():
            stage_counts[item.status.value] += 1

            if item.timestamp and item.resolution_date:
                try:
                    created = datetime.fromisoformat(item.timestamp.replace("Z", "+00:00"))
                    resolved = datetime.fromisoformat(item.resolution_date.replace("Z", "+00:00"))
                    stage_times["total"].append((resolved - created).days)
                except (ValueError, AttributeError):
                    pass

        total_times = stage_times.get("total", [])
        median_time = sorted(total_times)[len(total_times) // 2] if total_times else 0

        bottlenecks = []
        avg_count = sum(stage_counts.values()) / max(len(stage_counts), 1)

        for stage, count in stage_counts.items():
            if count > avg_count * 3:
                bottlenecks.append({
                    "stage": stage,
                    "queue_depth": count,
                    "threshold": round(avg_count * 3, 1),
                    "severity": "high" if count > avg_count * 5 else "medium",
                })

        return {
            "stage_counts": dict(stage_counts),
            "median_resolution_days": median_time,
            "bottlenecks": bottlenecks,
        }

    # ---- Maturity Assessment ----

    def assess_maturity(self) -> dict:
        """
        Assess feedback loop maturity (Spec §12.4).

        Levels:
        1 — Initial: Ad hoc, reactive, manual
        2 — Developing: Documented process, basic metrics
        3 — Managed: Automated triage, real-time metrics
        4 — Optimized: Predictive, continuous improvement
        5 — Innovating: Self-optimizing, stakeholder co-creation
        """
        metrics = self.get_metrics()

        # Score each dimension
        scores = {
            "process": 1,
            "technology": 1,
            "people": 1,
            "metrics": 1,
            "experience": 1,
        }

        # Process: has documented workflow
        if metrics["total_feedback"] > 0:
            scores["process"] = 2
        if metrics["response_rate_within_sla"] > 90:
            scores["process"] = 3
        if metrics["automation_rate"] > 50:
            scores["process"] = 4
        if metrics["automation_rate"] > 80:
            scores["process"] = 5

        # Technology: automation
        if metrics["automation_rate"] > 20:
            scores["technology"] = 2
        if metrics["automation_rate"] > 50:
            scores["technology"] = 3
        if metrics["automation_rate"] > 70:
            scores["technology"] = 4
        if metrics["automation_rate"] > 90:
            scores["technology"] = 5

        # Metrics: tracking
        if metrics["total_feedback"] > 0:
            scores["metrics"] = 2
        if metrics["resolution_rate"] > 75:
            scores["metrics"] = 3
        if metrics["resolution_rate"] > 90:
            scores["metrics"] = 4
        if metrics["learning_capture_rate"] > 80:
            scores["metrics"] = 5

        # Experience: satisfaction proxy
        if metrics["resolution_rate"] > 70:
            scores["experience"] = 2
        if metrics["resolution_rate"] > 85:
            scores["experience"] = 3
        if metrics["median_resolution_days"] < 30:
            scores["experience"] = 4
        if metrics["median_resolution_days"] < 14:
            scores["experience"] = 5

        avg_score = sum(scores.values()) / len(scores)

        level_names = {
            1: "Initial",
            2: "Developing",
            3: "Managed",
            4: "Optimized",
            5: "Innovating",
        }

        return {
            "overall_level": round(avg_score, 1),
            "level_name": level_names.get(round(avg_score), "Unknown"),
            "dimension_scores": scores,
            "characteristics": self._get_maturity_characteristics(round(avg_score)),
        }

    def _get_maturity_characteristics(self, level: int) -> list[str]:
        characteristics = {
            1: ["Manual, ad hoc process", "Spreadsheets", "Individual effort",
                "Basic volume counts", "Inconsistent experience"],
            2: ["Documented, followed process", "Dedicated tool", "Trained team",
                "SLA compliance", "Consistent experience"],
            3: ["Automated, integrated", "Platform + automation", "Skilled team",
                "Real-time dashboards", "Responsive experience"],
            4: ["Predictive, optimized", "ML/AI-powered", "Cross-functional",
                "Predictive analytics", "Proactive experience"],
            5: ["Self-optimizing", "Autonomous systems", "Self-organizing",
                "Self-measuring", "Co-creative experience"],
        }
        return characteristics.get(level, [])

    # ---- CI Framework Integration ----

    def ci_framework_mapping(self) -> dict:
        """
        Map feedback loop stages to CI Framework 8-stage self-healing loop (Spec §12.5).
        """
        return {
            "1. Detect": {"feedback_equivalent": "Feedback collection",
                          "integration": "Automated intake from all channels"},
            "2. Triage": {"feedback_equivalent": "Triage & scoring",
                          "integration": "Auto-classification + priority scoring"},
            "3. Adjudicate": {"feedback_equivalent": "Adjudication & decision",
                              "integration": "Decision support + routing"},
            "4. Plan": {"feedback_equivalent": "Action planning",
                        "integration": "Resource allocation + scheduling"},
            "5. Execute": {"feedback_equivalent": "Implementation",
                           "integration": "Workstream execution + tracking"},
            "6. Verify": {"feedback_equivalent": "Resolution verification",
                          "integration": "Stakeholder confirmation + metrics"},
            "7. Learn": {"feedback_equivalent": "Learning capture",
                         "integration": "Knowledge base + training update"},
            "8. Improve": {"feedback_equivalent": "Process improvement",
                           "integration": "Automation + optimization"},
        }

    # ---- Persistence ----

    def save(self, path: str | Path) -> None:
        data = [item.to_dict() for item in self._feedback.values()]
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self._feedback.clear()
        for item_data in data:
            item = FeedbackItem.from_dict(item_data)
            self._feedback[item.feedback_id] = item
            # Update next_id
            num = int(item.feedback_id.split("-")[1])
            if num >= self._next_id:
                self._next_id = num + 1

    def __len__(self) -> int:
        return len(self._feedback)


# ---------------------------------------------------------------------------
# Demo / Self-test
# ---------------------------------------------------------------------------

def _demo():
    """Demonstrate feedback loop automation."""
    engine = FeedbackLoopEngine()

    # Collect feedback from various sources
    print("--- Stage 1: COLLECT ---")
    fb1 = engine.collect(
        source=FeedbackSource.GITHUB,
        stakeholder_id="STK-003",
        stakeholder_category="internal",
        title="Policy DSL too complex for non-technical users",
        description="The policy DSL requires programming knowledge. "
                    "We need a UI builder for policy creation.",
        feedback_type=FeedbackType.PRODUCT,
        tags=["usability", "policy", "ui"],
    )
    print(f"  Collected: {fb1.feedback_id} — {fb1.title}")

    fb2 = engine.collect(
        source=FeedbackSource.SURVEY,
        stakeholder_id="STK-005",
        stakeholder_category="external",
        title="Missing agent identity lifecycle control",
        description="Current controls don't cover agent registration and decommissioning.",
        feedback_type=FeedbackType.GOVERNANCE,
        tags=["agent-governance", "identity", "controls"],
    )
    print(f"  Collected: {fb2.feedback_id} — {fb2.title}")

    fb3 = engine.collect(
        source=FeedbackSource.EMAIL,
        stakeholder_id="STK-004",
        stakeholder_category="regulator",
        title="EU AI Act update — new guidance on FRIA",
        description="Updated FRIA guidance requires additional documentation for high-risk systems.",
        feedback_type=FeedbackType.COMPLIANCE,
        tags=["regulatory", "eu-ai-act", "fria"],
    )
    print(f"  Collected: {fb3.feedback_id} — {fb3.title}")

    fb4 = engine.collect(
        source=FeedbackSource.SLACK,
        stakeholder_id="STK-006",
        stakeholder_category="external",
        title="Onboarding documentation unclear",
        description="New contributors find the onboarding docs confusing. Need better structure.",
        feedback_type=FeedbackType.COMMUNITY,
        tags=["documentation", "onboarding", "community"],
    )
    print(f"  Collected: {fb4.feedback_id} — {fb4.title}")

    # Auto-process feedback
    print("\n--- Auto-Processing ---")
    for fb_id in [fb1.feedback_id, fb2.feedback_id, fb3.feedback_id, fb4.feedback_id]:
        item = engine.process_auto(fb_id)
        print(f"  {fb_id}: score={item.priority_score} class={item.classification.value} "
              f"decision={item.decision.value if item.decision else 'N/A'} "
              f"workstream={item.assigned_to}")

    # Resolve some feedback
    print("\n--- Resolution ---")
    engine.start_execution(fb1.feedback_id)
    engine.resolve(fb1.feedback_id,
                   resolution="UI builder prototype created and tested with 5 users",
                   verified_by="STK-003")
    engine.close(fb1.feedback_id)
    engine.capture_learning(fb1.feedback_id)
    print(f"  Resolved: {fb1.feedback_id}")

    engine.start_execution(fb2.feedback_id)
    engine.resolve(fb2.feedback_id,
                   resolution="Agent identity lifecycle control added to control catalog",
                   verified_by="STK-005")
    engine.close(fb2.feedback_id)
    engine.capture_learning(fb2.feedback_id)
    print(f"  Resolved: {fb2.feedback_id}")

    # Metrics
    print("\n--- Feedback Loop Metrics ---")
    metrics = engine.get_metrics()
    for key, val in metrics.items():
        print(f"  {key}: {val}")

    # Bottleneck analysis
    print("\n--- Bottleneck Analysis ---")
    bottlenecks = engine.bottleneck_analysis()
    print(f"  Stage counts: {bottlenecks['stage_counts']}")
    print(f"  Median resolution: {bottlenecks['median_resolution_days']} days")
    if bottlenecks["bottlenecks"]:
        for b in bottlenecks["bottlenecks"]:
            print(f"  ⚠ Bottleneck at {b['stage']}: {b['queue_depth']} items")
    else:
        print("  No bottlenecks detected")

    # Maturity assessment
    print("\n--- Maturity Assessment ---")
    maturity = engine.assess_maturity()
    print(f"  Overall Level: {maturity['overall_level']} ({maturity['level_name']})")
    print(f"  Dimension scores: {maturity['dimension_scores']}")
    print(f"  Characteristics: {maturity['characteristics']}")

    # CI Framework mapping
    print("\n--- CI Framework Integration ---")
    ci_map = engine.ci_framework_mapping()
    for stage, mapping in ci_map.items():
        print(f"  {stage} → {mapping['feedback_equivalent']}")

    # Persistence
    print("\n--- Persistence ---")
    engine.save("/tmp/grc-claw-feedback.json")
    print("  Saved to /tmp/grc-claw-feedback.json")

    engine2 = FeedbackLoopEngine()
    engine2.load("/tmp/grc-claw-feedback.json")
    print(f"  Loaded {len(engine2)} feedback items")

    print("\n✓ Feedback Loop Automation demo complete")


if __name__ == "__main__":
    _demo()
