"""
GRC_Claw Engagement Workflow
============================
Implements the engagement workflow engine from the GRC_Claw Stakeholder
Engagement Specification v2.0.

Covers:
- Engagement planning and scheduling
- Workshop management (8 types per Spec §3.2)
- Survey program management (8 survey types per Spec §3.3)
- Interview program management (7 interview types per Spec §3.4)
- Steering committee and advisory board management
- Engagement tracking and effectiveness scoring
- Communication plan execution
- Escalation protocol (5-level per Spec §4.4.3)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class EngagementStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class EngagementType(str, Enum):
    WORKSHOP = "workshop"
    SURVEY = "survey"
    INTERVIEW = "interview"
    STEERING_COMMITTEE = "steering_committee"
    ADVISORY_BOARD = "advisory_board"
    OFFICE_HOURS = "office_hours"
    WORKING_GROUP = "working_group"
    RFC = "rfc"
    TRAINING = "training"
    INCIDENT_TABLETOP = "incident_tabletop"
    CONFERENCE = "conference"
    COMMUNICATION = "communication"


class WorkshopType(str, Enum):
    REQUIREMENTS = "requirements"
    POLICY_DESIGN = "policy_design"
    AGENT_GOVERNANCE_SPRINT = "agent_governance_sprint"
    COMPLIANCE_MAPPING = "compliance_mapping"
    INCIDENT_RESPONSE_TABLETOP = "incident_response_tabletop"
    MATURITY_ASSESSMENT = "maturity_assessment"
    ROADMAP_REVIEW = "roadmap_review"
    REGULATOR_ENGAGEMENT = "regulator_engagement"


class SurveyType(str, Enum):
    STAKEHOLDER_SATISFACTION = "stakeholder_satisfaction"
    DESIGN_PARTNER_FEEDBACK = "design_partner_feedback"
    TRAINING_EFFECTIVENESS = "training_effectiveness"
    COMMUNITY_HEALTH = "community_health"
    REGULATORY_LANDSCAPE = "regulatory_landscape"
    NPS = "nps"
    POST_INCIDENT = "post_incident"
    MATURITY_SELF_ASSESSMENT = "maturity_self_assessment"


class InterviewType(str, Enum):
    EXECUTIVE = "executive"
    DESIGN_PARTNER = "design_partner"
    REGULATOR = "regulator"
    STANDARDS_BODY = "standards_body"
    COMMUNITY_CONTRIBUTOR = "community_contributor"
    END_USER = "end_user"
    EXIT = "exit"


class EscalationLevel(int, Enum):
    LEVEL_0 = 0  # All stakeholders / public
    LEVEL_1 = 1  # Working teams / P2
    LEVEL_2 = 2  # Steering committee / P1
    LEVEL_3 = 3  # Executive sponsors / governance committee
    LEVEL_4 = 4  # Board / regulators


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Engagement:
    """A single engagement activity."""

    engagement_id: str
    title: str
    engagement_type: EngagementType
    status: EngagementStatus
    stakeholders: list[str]  # stakeholder IDs
    scheduled_date: str
    duration_minutes: int
    facilitator: str = ""
    objectives: list[str] = field(default_factory=list)
    agenda: list[str] = field(default_factory=list)
    pre_reads: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    action_items: list[dict] = field(default_factory=list)
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_0
    location: str = ""
    channel: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    effectiveness_score: Optional[float] = None  # 0-100

    def to_dict(self) -> dict:
        d = asdict(self)
        d["engagement_type"] = self.engagement_type.value
        d["status"] = self.status.value
        d["escalation_level"] = self.escalation_level.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Engagement:
        data["engagement_type"] = EngagementType(data["engagement_type"])
        data["status"] = EngagementStatus(data["status"])
        data["escalation_level"] = EscalationLevel(data["escalation_level"])
        return cls(**data)


@dataclass
class Workshop:
    """Extended engagement for workshop-type activities (Spec §3.2)."""

    base: Engagement
    workshop_type: WorkshopType
    participant_count: int = 0
    materials_needed: list[str] = field(default_factory=list)
    post_workshop_survey_sent: bool = False
    effectiveness_rating: Optional[float] = None  # 1-5 Likert

    def to_dict(self) -> dict:
        d = self.base.to_dict()
        d["workshop_type"] = self.workshop_type.value
        d["participant_count"] = self.participant_count
        d["materials_needed"] = self.materials_needed
        d["post_workshop_survey_sent"] = self.post_workshop_survey_sent
        d["effectiveness_rating"] = self.effectiveness_rating
        return d


@dataclass
class Survey:
    """Extended engagement for survey-type activities (Spec §3.3)."""

    base: Engagement
    survey_type: SurveyType
    questions: list[dict] = field(default_factory=list)
    target_audience: list[str] = field(default_factory=list)
    response_count: int = 0
    response_rate: float = 0.0
    anonymity: bool = True
    results_summary: str = ""

    def to_dict(self) -> dict:
        d = self.base.to_dict()
        d["survey_type"] = self.survey_type.value
        d["questions"] = self.questions
        d["target_audience"] = self.target_audience
        d["response_count"] = self.response_count
        d["response_rate"] = self.response_rate
        d["anonymity"] = self.anonymity
        d["results_summary"] = self.results_summary
        return d


@dataclass
class Interview:
    """Extended engagement for interview-type activities (Spec §3.4)."""

    base: Engagement
    interview_type: InterviewType
    interviewee_name: str = ""
    interviewee_role: str = ""
    consent_obtained: bool = False
    recording_consent: bool = False
    transcript_path: str = ""
    key_themes: list[str] = field(default_factory=list)
    sentiment: str = "neutral"
    follow_up_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = self.base.to_dict()
        d["interview_type"] = self.interview_type.value
        d["interviewee_name"] = self.interviewee_name
        d["interviewee_role"] = self.interviewee_role
        d["consent_obtained"] = self.consent_obtained
        d["recording_consent"] = self.recording_consent
        d["transcript_path"] = self.transcript_path
        d["key_themes"] = self.key_themes
        d["sentiment"] = self.sentiment
        d["follow_up_actions"] = self.follow_up_actions
        return d


# ---------------------------------------------------------------------------
# Engagement Calendar
# ---------------------------------------------------------------------------

class EngagementCalendar:
    """
    Annual engagement calendar with quarterly planning (Spec §7.2.1).

    Q1: Annual survey, maturity assessment, roadmap review, regulator sessions
    Q2: Design partner interviews, community health, standards meetings, training review
    Q3: Mid-year steering review, incident tabletop, advisory board, conferences
    Q4: Annual summit, compliance review, training completion, next-year planning
    """

    QUARTERLY_ACTIVITIES = {
        1: [
            ("Annual Stakeholder Survey", EngagementType.SURVEY),
            ("Maturity Assessment Workshop", EngagementType.WORKSHOP),
            ("Roadmap Review Workshop", EngagementType.WORKSHOP),
            ("Regulator Engagement Sessions", EngagementType.WORKSHOP),
        ],
        2: [
            ("Design Partner Interviews", EngagementType.INTERVIEW),
            ("Community Health Survey", EngagementType.SURVEY),
            ("Standards Body Meetings", EngagementType.WORKING_GROUP),
            ("Training Effectiveness Review", EngagementType.SURVEY),
        ],
        3: [
            ("Mid-Year Steering Committee Review", EngagementType.STEERING_COMMITTEE),
            ("Incident Response Tabletop", EngagementType.INCIDENT_TABLETOP),
            ("Advisory Board Meeting", EngagementType.ADVISORY_BOARD),
            ("Conference Presentations", EngagementType.CONFERENCE),
        ],
        4: [
            ("Annual Summit", EngagementType.CONFERENCE),
            ("Annual Compliance Review", EngagementType.STEERING_COMMITTEE),
            ("Annual Training Cycle Completion", EngagementType.TRAINING),
            ("Next-Year Planning Workshop", EngagementType.WORKSHOP),
        ],
    }

    def __init__(self):
        self._engagements: dict[str, Engagement] = {}
        self._next_id = 1

    def plan_quarter(self, quarter: int, year: int, stakeholders: list[str]) -> list[Engagement]:
        """Generate planned engagements for a given quarter."""
        if quarter not in self.QUARTERLY_ACTIVITIES:
            raise ValueError(f"Invalid quarter: {quarter}")

        planned = []
        base_month = (quarter - 1) * 3 + 1

        for idx, (title, eng_type) in enumerate(self.QUARTERLY_ACTIVITIES[quarter]):
            eng_id = f"ENG-{year}-Q{quarter}-{idx + 1:03d}"
            # Spread engagements across the quarter's months
            month = base_month + (idx % 3)
            day = min(15 + (idx // 3) * 7, 28)  # Cap at day 28 to stay valid
            scheduled = datetime(year, month, day)

            eng = Engagement(
                engagement_id=eng_id,
                title=title,
                engagement_type=eng_type,
                status=EngagementStatus.PLANNED,
                stakeholders=stakeholders,
                scheduled_date=scheduled.isoformat(),
                duration_minutes=120,
                objectives=[f"Execute {title}"],
            )
            self._engagements[eng_id] = eng
            planned.append(eng)

        return planned

    def add_engagement(self, engagement: Engagement) -> Engagement:
        if not engagement.engagement_id:
            engagement.engagement_id = f"ENG-{self._next_id:04d}"
            self._next_id += 1
        self._engagements[engagement.engagement_id] = engagement
        return engagement

    def get(self, engagement_id: str) -> Optional[Engagement]:
        return self._engagements.get(engagement_id)

    def find_by_type(self, eng_type: EngagementType) -> list[Engagement]:
        return [e for e in self._engagements.values() if e.engagement_type == eng_type]

    def find_by_status(self, status: EngagementStatus) -> list[Engagement]:
        return [e for e in self._engagements.values() if e.status == status]

    def find_by_stakeholder(self, stakeholder_id: str) -> list[Engagement]:
        return [e for e in self._engagements.values()
                if stakeholder_id in e.stakeholders]

    def find_upcoming(self, days: int = 30) -> list[Engagement]:
        """Find engagements scheduled within the next *days* days."""
        cutoff = datetime.utcnow() + timedelta(days=days)
        upcoming = []
        for e in self._engagements.values():
            if e.status != EngagementStatus.PLANNED:
                continue
            try:
                sched = datetime.fromisoformat(e.scheduled_date.replace("Z", "+00:00"))
                if sched <= cutoff:
                    upcoming.append(e)
            except (ValueError, AttributeError):
                continue
        return sorted(upcoming, key=lambda x: x.scheduled_date)

    def complete_engagement(self, engagement_id: str,
                            effectiveness_score: Optional[float] = None) -> Engagement:
        eng = self._engagements.get(engagement_id)
        if not eng:
            raise KeyError(f"Engagement {engagement_id} not found")
        eng.status = EngagementStatus.COMPLETED
        eng.completed_at = datetime.utcnow().isoformat()
        eng.effectiveness_score = effectiveness_score
        return eng

    def get_engagement_rate(self) -> float:
        """Calculate engagement completion rate (Spec §5.5)."""
        planned = [e for e in self._engagements.values()
                   if e.status in (EngagementStatus.PLANNED, EngagementStatus.COMPLETED)]
        if not planned:
            return 0.0
        completed = [e for e in planned if e.status == EngagementStatus.COMPLETED]
        return round(len(completed) / len(planned) * 100, 1)

    def effectiveness_report(self) -> dict:
        """Generate engagement effectiveness report (Spec §9)."""
        completed = [e for e in self._engagements.values()
                     if e.status == EngagementStatus.COMPLETED]
        if not completed:
            return {"total_completed": 0, "average_effectiveness": 0}

        scores = [e.effectiveness_score for e in completed
                  if e.effectiveness_score is not None]

        by_type = defaultdict(list)
        for e in completed:
            by_type[e.engagement_type.value].append(e.effectiveness_score or 0)

        return {
            "total_completed": len(completed),
            "total_planned": len(self._engagements),
            "engagement_rate": self.get_engagement_rate(),
            "average_effectiveness": round(sum(scores) / len(scores), 1) if scores else 0,
            "by_type": {k: round(sum(v) / len(v), 1) for k, v in by_type.items()},
        }


# ---------------------------------------------------------------------------
# Escalation Protocol
# ---------------------------------------------------------------------------

class EscalationProtocol:
    """
    5-level escalation protocol (Spec §4.4.3).

    Level 4: Board / Regulators
    Level 3: Executive Sponsors / Governance Committee
    Level 2: Steering Committee / P1 Stakeholders
    Level 1: Working Teams / P2 Stakeholders
    Level 0: All Stakeholders / Public
    """

    ESCALATION_PATHS = {
        "security_vulnerability": EscalationLevel.LEVEL_4,
        "regulatory_action": EscalationLevel.LEVEL_4,
        "strategic_risk": EscalationLevel.LEVEL_3,
        "major_incident": EscalationLevel.LEVEL_3,
        "policy_change": EscalationLevel.LEVEL_3,
        "moderate_risk": EscalationLevel.LEVEL_2,
        "milestone_slip": EscalationLevel.LEVEL_2,
        "stakeholder_concern": EscalationLevel.LEVEL_2,
        "minor_risk": EscalationLevel.LEVEL_1,
        "routine_update": EscalationLevel.LEVEL_1,
        "general_inquiry": EscalationLevel.LEVEL_1,
        "public_announcement": EscalationLevel.LEVEL_0,
    }

    SLA_HOURS = {
        "security_vulnerability": 24,
        "regulatory_change": 48,
        "incident_critical": 4,
        "incident_major": 24,
        "roadmap_change": 168,  # 1 week
        "policy_update": 720,   # 30 days
        "inquiry_response": 72,  # 3 business days
    }

    @classmethod
    def get_escalation_level(cls, event_type: str) -> EscalationLevel:
        return cls.ESCALATION_PATHS.get(event_type, EscalationLevel.LEVEL_1)

    @classmethod
    def get_sla_hours(cls, content_type: str) -> int:
        return cls.SLA_HOURS.get(content_type, 72)

    @classmethod
    def get_escalation_recipients(cls, level: EscalationLevel) -> list[str]:
        """Return recipient groups for a given escalation level."""
        recipients = {
            EscalationLevel.LEVEL_0: ["all_stakeholders", "public"],
            EscalationLevel.LEVEL_1: ["working_teams", "p2_stakeholders"],
            EscalationLevel.LEVEL_2: ["steering_committee", "p1_stakeholders"],
            EscalationLevel.LEVEL_3: ["executive_sponsors", "governance_committee"],
            EscalationLevel.LEVEL_4: ["board", "regulators"],
        }
        return recipients.get(level, [])


# ---------------------------------------------------------------------------
# Demo / Self-test
# ---------------------------------------------------------------------------

def _demo():
    """Demonstrate engagement workflow functionality."""
    calendar = EngagementCalendar()

    # Plan Q1 engagements
    print("--- Q1 2026 Planned Engagements ---")
    p1_stakeholders = ["STK-001", "STK-002", "STK-003", "STK-004"]
    q1_engagements = calendar.plan_quarter(1, 2026, p1_stakeholders)
    for eng in q1_engagements:
        print(f"  {eng.engagement_id}: {eng.title} ({eng.engagement_type.value}) "
              f"on {eng.scheduled_date[:10]}")

    # Add a custom workshop
    workshop = Workshop(
        base=Engagement(
            engagement_id="ENG-WSH-001",
            title="Agent Governance Design Sprint",
            engagement_type=EngagementType.WORKSHOP,
            status=EngagementStatus.PLANNED,
            stakeholders=["STK-001", "STK-002", "STK-003"],
            scheduled_date="2026-11-15T09:00:00",
            duration_minutes=480,
            facilitator="External Facilitator",
            objectives=["Design agent governance prototype", "Define autonomy boundaries"],
            agenda=["Welcome & context", "Current state analysis", "Design sprint", "Synthesis"],
        ),
        workshop_type=WorkshopType.AGENT_GOVERNANCE_SPRINT,
        participant_count=12,
        materials_needed=["Whiteboard", "Sticky notes", "Timer", "Pre-reads"],
    )
    calendar.add_engagement(workshop.base)
    print(f"\n  Added workshop: {workshop.base.engagement_id}: {workshop.base.title}")

    # Add a survey
    survey = Survey(
        base=Engagement(
            engagement_id="ENG-SUR-001",
            title="Stakeholder Satisfaction Survey 2026",
            engagement_type=EngagementType.SURVEY,
            status=EngagementStatus.PLANNED,
            stakeholders=p1_stakeholders,
            scheduled_date="2026-04-01T09:00:00",
            duration_minutes=0,
            objectives=["Measure engagement satisfaction", "Identify concerns"],
        ),
        survey_type=SurveyType.STAKEHOLDER_SATISFACTION,
        questions=[
            {"id": "Q1", "text": "Overall satisfaction?", "type": "likert", "scale": 5},
            {"id": "Q2", "text": "Responsiveness?", "type": "likert", "scale": 5},
            {"id": "Q3", "text": "Relevance?", "type": "likert", "scale": 5},
            {"id": "Q4", "text": "NPS (0-10)", "type": "nps"},
            {"id": "Q5", "text": "Open feedback", "type": "text"},
        ],
        target_audience=["P1", "P2"],
        anonymity=True,
    )
    calendar.add_engagement(survey.base)
    print(f"  Added survey: {survey.base.engagement_id}: {survey.base.title}")

    # Add an interview
    interview = Interview(
        base=Engagement(
            engagement_id="ENG-INT-001",
            title="Executive Stakeholder Interview — Q1",
            engagement_type=EngagementType.INTERVIEW,
            status=EngagementStatus.PLANNED,
            stakeholders=["STK-001"],
            scheduled_date="2026-02-15T14:00:00",
            duration_minutes=60,
            objectives=["Strategic alignment", "Risk concerns", "Resource needs"],
        ),
        interview_type=InterviewType.EXECUTIVE,
        interviewee_name="Jane Smith",
        interviewee_role="VP Engineering",
        consent_obtained=True,
        recording_consent=True,
    )
    calendar.add_engagement(interview.base)
    print(f"  Added interview: {interview.base.engagement_id}: {interview.base.title}")

    # Complete some engagements
    calendar.complete_engagement(q1_engagements[0].engagement_id, effectiveness_score=85.0)
    calendar.complete_engagement(q1_engagements[1].engagement_id, effectiveness_score=78.0)
    calendar.complete_engagement("ENG-WSH-001", effectiveness_score=92.0)

    # Effectiveness report
    print("\n--- Effectiveness Report ---")
    report = calendar.effectiveness_report()
    for key, val in report.items():
        print(f"  {key}: {val}")

    # Upcoming engagements
    print("\n--- Upcoming Engagements (next 90 days) ---")
    upcoming = calendar.find_upcoming(90)
    for eng in upcoming[:5]:
        print(f"  {eng.engagement_id}: {eng.title} on {eng.scheduled_date[:10]}")

    # Escalation protocol
    print("\n--- Escalation Protocol ---")
    for event_type in ["security_vulnerability", "major_incident", "moderate_risk", "routine_update"]:
        level = EscalationProtocol.get_escalation_level(event_type)
        recipients = EscalationProtocol.get_escalation_recipients(level)
        print(f"  {event_type} → Level {level.value} → {recipients}")

    # SLA lookup
    print("\n--- Communication SLAs ---")
    for content_type in ["security_vulnerability", "regulatory_change", "incident_critical", "inquiry_response"]:
        sla = EscalationProtocol.get_sla_hours(content_type)
        print(f"  {content_type}: {sla} hours")

    print("\n✓ Engagement Workflow demo complete")


if __name__ == "__main__":
    _demo()
