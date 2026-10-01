"""
GRC_Claw Post-Incident Learning Loop (§15 of GRC-AIM-001)

Implements the structured post-incident learning loop:
    • Immediate learning (per incident) — data capture, detection gap analysis, response effectiveness
    • Tactical learning (monthly) — incident review, detection rule updates, runbook updates
    • Strategic learning (quarterly) — trend analysis, control effectiveness, knowledge base updates
    • Recommendation tracking and closure (§7.6)
    — Knowledge management (§7.7)
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from .models import (
    Incident,
    IncidentStatus,
    Recommendation,
    RecommendationPriority,
    RecommendationStatus,
    ResponseAction,
)
from .taxonomy import IncidentCategory, Severity


# ═══════════════════════════════════════════════════════════════════════════════
# Immediate Learning (§15.2)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DetectionGapAnalysis:
    """Detection gap analysis results (§15.2.2)."""
    incident_id: str
    was_detected: bool
    detection_gap_seconds: float = 0.0
    could_detect_earlier: bool = False
    earlier_detection_opportunity: str = ""
    detection_gap_root_cause: str = ""
    missed_signals: list[str] = field(default_factory=list)
    new_detection_opportunities: list[str] = field(default_factory=list)


@dataclass
class ResponseEffectiveness:
    """Response effectiveness analysis (§15.2.3)."""
    incident_id: str
    time_to_detect_seconds: float = 0.0
    time_to_respond_seconds: float = 0.0
    time_to_contain_seconds: float = 0.0
    time_to_eradicate_seconds: float = 0.0
    time_to_recover_seconds: float = 0.0
    containment_effectiveness_pct: float = 0.0
    escalation_accuracy: bool = False
    communication_timely: bool = False
    sla_compliant: bool = False


class ImmediateLearning:
    """
    Immediate learning (per incident) (§15.2).

    Captures incident data, analyzes detection gaps, and evaluates
    response effectiveness within 24 hours of incident closure.
    """

    def __init__(self) -> None:
        self._captured_data: dict[str, dict[str, Any]] = {}
        self._gap_analyses: dict[str, DetectionGapAnalysis] = {}
        self._effectiveness: dict[str, ResponseEffectiveness] = {}

    def capture_incident_data(self, incident: Incident) -> dict[str, Any]:
        """Capture all incident data within 24 hours of closure (§15.2.1)."""
        data = {
            "incident_id": incident.incident_id,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "timeline": {
                "detected_at": incident.detected_at,
                "triaged_at": incident.triaged_at,
                "contained_at": incident.contained_at,
                "eradicated_at": incident.eradicated_at,
                "recovered_at": incident.recovered_at,
                "closed_at": incident.closed_at,
            },
            "detection_data": {
                "signals_count": len(incident.signals),
                "sources": list(set(s.source for s in incident.signals)),
                "correlated": any(s.correlated for s in incident.signals),
            },
            "response_data": {
                "actions_count": len(incident.response_actions),
                "containment_actions": incident.containment_actions,
                "eradication_actions": incident.eradication_actions,
                "recovery_actions": incident.recovery_actions,
            },
            "evidence_count": len(incident.evidence),
            "impact": {
                "individuals_affected": incident.impact_assessment.individuals_affected,
                "records_affected": incident.impact_assessment.records_affected,
                "financial_impact_usd": incident.impact_assessment.financial_impact_usd,
            },
            "root_cause": incident.root_cause.__dict__,
            "lessons_learned": incident.lessons_learned,
        }
        self._captured_data[incident.incident_id] = data
        return data

    def analyze_detection_gap(self, incident: Incident) -> DetectionGapAnalysis:
        """Analyze detection effectiveness (§15.2.2)."""
        was_detected = incident.detected_at != ""
        gap_seconds = 0.0
        could_earlier = False
        root_cause = ""
        missed = []
        opportunities = []

        if was_detected and incident.triaged_at:
            try:
                detected = datetime.fromisoformat(incident.detected_at.replace("Z", "+00:00"))
                triaged = datetime.fromisoformat(incident.triaged_at.replace("Z", "+00:00"))
                gap_seconds = (triaged - detected).total_seconds()
            except (ValueError, AttributeError):
                pass

        # Analyze signals for missed detection opportunities
        for signal in incident.signals:
            if signal.confidence < 0.60:
                missed.append(f"Low confidence signal from {signal.source}: {signal.subcategory_code}")
                opportunities.append(f"Lower threshold for {signal.subcategory_code} from {signal.source}")

        # Check if signals existed before detection
        if incident.signals:
            earliest_signal = min(
                datetime.fromisoformat(s.timestamp.replace("Z", "+00:00"))
                for s in incident.signals if s.timestamp
            ) if any(s.timestamp for s in incident.signals) else None

            if earliest_signal and incident.detected_at:
                detected = datetime.fromisoformat(incident.detected_at.replace("Z", "+00:00"))
                if earliest_signal < detected:
                    could_earlier = True
                    root_cause = "Signals existed before detection threshold was met"

        analysis = DetectionGapAnalysis(
            incident_id=incident.incident_id,
            was_detected=was_detected,
            detection_gap_seconds=gap_seconds,
            could_detect_earlier=could_earlier,
            detection_gap_root_cause=root_cause,
            missed_signals=missed,
            new_detection_opportunities=opportunities,
        )
        self._gap_analyses[incident.incident_id] = analysis
        return analysis

    def analyze_response_effectiveness(self, incident: Incident) -> ResponseEffectiveness:
        """Analyze response effectiveness (§15.2.3)."""
        def _time_diff(start: str, end: str) -> float:
            if not start or not end:
                return 0.0
            try:
                s = datetime.fromisoformat(start.replace("Z", "+00:00"))
                e = datetime.fromisoformat(end.replace("Z", "+00:00"))
                return (e - s).total_seconds()
            except (ValueError, AttributeError):
                return 0.0

        ttd = _time_diff(incident.detected_at, incident.triaged_at)
        ttr = _time_diff(incident.triaged_at, incident.contained_at)
        ttc = _time_diff(incident.detected_at, incident.contained_at)
        tte = _time_diff(incident.detected_at, incident.eradicated_at)
        ttrc = _time_diff(incident.detected_at, incident.recovered_at)

        # SLA targets (§15.2.3)
        severity = incident.severity
        if severity == Severity.S1_CRITICAL:
            sla_compliant = ttd <= 900 and ttr <= 3600 and ttc <= 14400
        elif severity == Severity.S2_HIGH:
            sla_compliant = ttd <= 3600 and ttr <= 14400 and ttc <= 86400
        else:
            sla_compliant = True

        effectiveness = ResponseEffectiveness(
            incident_id=incident.incident_id,
            time_to_detect_seconds=ttd,
            time_to_respond_seconds=ttr,
            time_to_contain_seconds=ttc,
            time_to_eradicate_seconds=tte,
            time_to_recover_seconds=ttrc,
            containment_effectiveness_pct=80.0 if incident.containment_actions else 0.0,
            escalation_accuracy=True,  # Would be set by analyst
            communication_timely=True,  # Would be set by analyst
            sla_compliant=sla_compliant,
        )
        self._effectiveness[incident.incident_id] = effectiveness
        return effectiveness


# ═══════════════════════════════════════════════════════════════════════════════
# Tactical Learning (§15.3)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DetectionRuleUpdate:
    """Detection rule update record (§15.3.2)."""
    update_id: str
    update_type: str  # new_signature | threshold_tuning | correlation_rule | model_retraining | policy_update
    description: str
    incident_id: str
    created_at: str = ""
    status: str = "pending"  # pending | implemented | verified


@dataclass
class RunbookUpdate:
    """Runbook update record (§15.3.3)."""
    update_id: str
    update_type: str  # action_addition | action_modification | precondition_update | postcondition_update | rollback_update
    runbook_id: str
    description: str
    incident_id: str
    created_at: str = ""
    status: str = "pending"


class TacticalLearning:
    """
    Tactical learning (monthly) (§15.3).

    Monthly review of incidents, detection rule updates, and runbook updates.
    """

    def __init__(self) -> None:
        self._rule_updates: list[DetectionRuleUpdate] = []
        self._runbook_updates: list[RunbookUpdate] = []
        self._monthly_reviews: list[dict[str, Any]] = []

    def create_detection_rule_update(
        self,
        update_type: str,
        description: str,
        incident_id: str,
    ) -> DetectionRuleUpdate:
        """Create a detection rule update (§15.3.2)."""
        update = DetectionRuleUpdate(
            update_id=hashlib.sha256(f"{update_type}:{incident_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            update_type=update_type,
            description=description,
            incident_id=incident_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._rule_updates.append(update)
        return update

    def create_runbook_update(
        self,
        update_type: str,
        runbook_id: str,
        description: str,
        incident_id: str,
    ) -> RunbookUpdate:
        """Create a runbook update (§15.3.3)."""
        update = RunbookUpdate(
            update_id=hashlib.sha256(f"{update_type}:{runbook_id}:{incident_id}".encode()).hexdigest()[:12],
            update_type=update_type,
            runbook_id=runbook_id,
            description=description,
            incident_id=incident_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._runbook_updates.append(update)
        return update

    def conduct_monthly_review(self, incidents: list[Incident]) -> dict[str, Any]:
        """Conduct monthly incident review (§15.3.1)."""
        review = {
            "review_period": datetime.now(timezone.utc).strftime("%Y-%m"),
            "total_incidents": len(incidents),
            "by_category": Counter(),
            "by_severity": Counter(),
            "detection_gaps": 0,
            "response_sla_violations": 0,
            "improvement_actions": [],
        }

        for inc in incidents:
            if inc.category:
                review["by_category"][inc.category.value] += 1
            review["by_severity"][inc.severity.value] += 1

        self._monthly_reviews.append(review)
        return review

    def get_pending_updates(self) -> dict[str, list]:
        return {
            "detection_rule_updates": [u for u in self._rule_updates if u.status == "pending"],
            "runbook_updates": [u for u in self._runbook_updates if u.status == "pending"],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Strategic Learning (§15.4)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ControlEffectiveness:
    """Control effectiveness assessment (§15.4.2)."""
    control_area: str  # preventive | detective | corrective | recovery
    total_incidents: int = 0
    incidents_prevented: int = 0
    incidents_detected: int = 0
    incidents_responded: int = 0
    incidents_recovered: int = 0
    effectiveness_score: float = 0.0  # 0.0–1.0
    gaps: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)


class StrategicLearning:
    """
    Strategic learning (quarterly) (§15.4).

    Quarterly trend analysis, control effectiveness assessment, and
    knowledge base updates.
    """

    def __init__(self) -> None:
        self._control_assessments: dict[str, ControlEffectiveness] = {}
        self._knowledge_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._quarterly_reviews: list[dict[str, Any]] = []

    def assess_control_effectiveness(
        self,
        control_area: str,
        incidents: list[Incident],
    ) -> ControlEffectiveness:
        """Assess control effectiveness (§15.4.2)."""
        total = len(incidents)
        if total == 0:
            return ControlEffectiveness(control_area=control_area)

        # Count incidents where controls worked
        prevented = sum(1 for i in incidents if i.status == IncidentStatus.CLOSED and i.severity in (Severity.S4_LOW, Severity.S5_INFORMATIONAL))
        detected = sum(1 for i in incidents if i.detected_at)
        responded = sum(1 for i in incidents if i.contained_at)
        recovered = sum(1 for i in incidents if i.recovered_at)

        score = (prevented * 0.3 + detected * 0.3 + responded * 0.2 + recovered * 0.2) / total

        gaps = []
        improvements = []
        if detected / total < 0.95:
            gaps.append(f"Detection gap: {total - detected} incidents not detected")
            improvements.append("Improve detection coverage")
        if responded / total < 0.90:
            gaps.append(f"Response gap: {total - responded} incidents not contained")
            improvements.append("Improve response automation")

        assessment = ControlEffectiveness(
            control_area=control_area,
            total_incidents=total,
            incidents_prevented=prevented,
            incidents_detected=detected,
            incidents_responded=responded,
            incidents_recovered=recovered,
            effectiveness_score=score,
            gaps=gaps,
            improvements=improvements,
        )
        self._control_assessments[control_area] = assessment
        return assessment

    def update_knowledge_base(
        self,
        category: str,
        entry: dict[str, Any],
    ) -> None:
        """Update knowledge base (§15.4.3)."""
        entry["added_at"] = datetime.now(timezone.utc).isoformat()
        self._knowledge_base[category].append(entry)

    def get_knowledge_base(self, category: str) -> list[dict[str, Any]]:
        return list(self._knowledge_base.get(category, []))

    def conduct_quarterly_review(self, incidents: list[Incident]) -> dict[str, Any]:
        """Conduct quarterly trend analysis (§15.4.1)."""
        review = {
            "review_period": f"Q{(datetime.now().month - 1) // 3 + 1} {datetime.now().year}",
            "total_incidents": len(incidents),
            "by_category": Counter(),
            "by_severity": Counter(),
            "control_effectiveness": {},
            "recommendations": [],
        }

        for inc in incidents:
            if inc.category:
                review["by_category"][inc.category.value] += 1
            review["by_severity"][inc.severity.value] += 1

        for area in ["preventive", "detective", "corrective", "recovery"]:
            assessment = self.assess_control_effectiveness(area, incidents)
            review["control_effectiveness"][area] = {
                "score": assessment.effectiveness_score,
                "gaps": assessment.gaps,
            }

        self._quarterly_reviews.append(review)
        return review


# ═══════════════════════════════════════════════════════════════════════════════
# Recommendation Tracking (§7.6)
# ═══════════════════════════════════════════════════════════════════════════════

class RecommendationTracker:
    """
    Recommendation tracking and closure (§7.6).

    Tracks post-incident review recommendations through their lifecycle:
    Open → In Progress → Completed | Deferred | Rejected
    """

    PRIORITY_DEADLINES = {
        RecommendationPriority.IMMEDIATE: timedelta(days=7),
        RecommendationPriority.SHORT_TERM: timedelta(days=30),
        RecommendationPriority.LONG_TERM: timedelta(days=90),
    }

    def __init__(self) -> None:
        self._recommendations: dict[str, Recommendation] = {}

    def add_recommendation(self, rec: Recommendation) -> None:
        self._recommendations[rec.recommendation_id] = rec

    def update_status(self, rec_id: str, status: RecommendationStatus) -> bool:
        rec = self._recommendations.get(rec_id)
        if rec:
            rec.status = status
            return True
        return False

    def get_overdue(self) -> list[Recommendation]:
        now = datetime.now(timezone.utc)
        overdue = []
        for rec in self._recommendations.values():
            if rec.status in (RecommendationStatus.OPEN, RecommendationStatus.IN_PROGRESS) and rec.due_date:
                try:
                    due = datetime.fromisoformat(rec.due_date.replace("Z", "+00:00"))
                    if now > due:
                        overdue.append(rec)
                except (ValueError, AttributeError):
                    pass
        return overdue

    def get_implementation_rate(self) -> float:
        total = len(self._recommendations)
        if total == 0:
            return 0.0
        completed = sum(1 for r in self._recommendations.values() if r.status == RecommendationStatus.COMPLETED)
        return completed / total

    def verify_effectiveness(self, rec_id: str) -> bool:
        """Verify recommendation effectiveness after 30 days (§7.6.3)."""
        rec = self._recommendations.get(rec_id)
        if not rec or rec.status != RecommendationStatus.COMPLETED:
            return False
        # In production, this would check if the implemented change is effective
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# Knowledge Management (§7.7)
# ═══════════════════════════════════════════════════════════════════════════════

class KnowledgeBase:
    """
    Incident knowledge base (§7.7).

    Stores post-incident review findings in a searchable knowledge base.
    """

    def __init__(self) -> None:
        self._entries: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add_incident_pattern(self, pattern: dict[str, Any]) -> None:
        pattern["type"] = "incident_pattern"
        pattern["added_at"] = datetime.now(timezone.utc).isoformat()
        self._entries["incident_patterns"].append(pattern)

    def add_root_cause(self, root_cause: dict[str, Any]) -> None:
        root_cause["type"] = "root_cause"
        root_cause["added_at"] = datetime.now(timezone.utc).isoformat()
        self._entries["root_causes"].append(root_cause)

    def add_effective_response(self, response: dict[str, Any]) -> None:
        response["type"] = "effective_response"
        response["added_at"] = datetime.now(timezone.utc).isoformat()
        self._entries["effective_responses"].append(response)

    def add_failed_response(self, response: dict[str, Any]) -> None:
        response["type"] = "failed_response"
        response["added_at"] = datetime.now(timezone.utc).isoformat()
        self._entries["failed_responses"].append(response)

    def search(self, category: str, query: str = "") -> list[dict[str, Any]]:
        entries = self._entries.get(category, [])
        if not query:
            return entries
        query_lower = query.lower()
        return [e for e in entries if query_lower in json.dumps(e).lower()]

    def get_stats(self) -> dict[str, int]:
        return {k: len(v) for k, v in self._entries.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# Learning Loop Metrics (§15.5)
# ═══════════════════════════════════════════════════════════════════════════════

class LearningLoopMetrics:
    """
    Learning loop metrics (§15.5).

    Tracks key metrics for the post-incident learning loop.
    """

    def __init__(self) -> None:
        self._detection_gaps: list[DetectionGapAnalysis] = []
        self._runbook_updates: list[RunbookUpdate] = []
        self._kb_entries: int = 0

    def record_detection_gap(self, gap: DetectionGapAnalysis) -> None:
        self._detection_gaps.append(gap)

    def record_runbook_update(self, update: RunbookUpdate) -> None:
        self._runbook_updates.append(update)

    def record_kb_entry(self) -> None:
        self._kb_entries += 1

    def get_metrics(self) -> dict[str, float]:
        total_gaps = len(self._detection_gaps)
        closed_gaps = sum(1 for g in self._detection_gaps if not g.could_detect_earlier)

        return {
            "detection_gap_closure_rate": closed_gaps / total_gaps if total_gaps > 0 else 1.0,
            "runbook_update_rate": len(self._runbook_updates) / max(total_gaps, 1),
            "knowledge_base_growth": self._kb_entries,
        }
