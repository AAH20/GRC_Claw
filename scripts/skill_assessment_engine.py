#!/usr/bin/env python3
"""
GRC_Claw Skill Assessment Engine
=================================
Assesses learner skills across 10 competencies with adaptive testing,
skill gap analysis, and personalized improvement plans.
"""

import json, uuid, sys, math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from collections import defaultdict


class SkillLevel(str, Enum):
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AssessmentType(str, Enum):
    SELF_ASSESSMENT = "self_assessment"
    PRACTICAL_EXAM = "practical_exam"
    SCENARIO_BASED = "scenario_based"
    PEER_REVIEW = "peer_review"
    CERTIFICATION = "certification"


@dataclass
class SkillAssessment:
    assessment_id: str
    user_id: str
    competency_id: str
    assessment_type: AssessmentType
    score: float
    max_score: float
    level: SkillLevel
    assessed_at: str
    assessor: str
    evidence_refs: list[str] = field(default_factory=list)
    notes: str = ""
    next_assessment_recommended: Optional[str] = None


@dataclass
class SkillGap:
    competency_id: str
    current_level: SkillLevel
    required_level: SkillLevel
    gap_severity: str  # critical, high, medium, low
    recommended_actions: list[str] = field(default_factory=list)
    estimated_hours_to_close: float = 0.0


COMPETENCY_SKILL_MATRIX = {
    "C1": {
        "name": "GRC Architecture & Fundamentals",
        "skills": {
            "gateway_configuration": {"description": "Configure and manage GRC_Claw gateway", "weight": 0.2},
            "evidence_plane_management": {"description": "Manage evidence plane and artifacts", "weight": 0.2},
            "architecture_design": {"description": "Design GRC_Claw architecture", "weight": 0.2},
            "framework_mapping": {"description": "Map controls to compliance frameworks", "weight": 0.2},
            "system_integration": {"description": "Integrate GRC_Claw with external systems", "weight": 0.2},
        },
    },
    "C2": {
        "name": "Agent Runtime & Policy",
        "skills": {
            "policy_creation": {"description": "Create and manage agent policies", "weight": 0.25},
            "trust_score_analysis": {"description": "Analyze and interpret trust scores", "weight": 0.25},
            "action_ledger_audit": {"description": "Audit action ledger entries", "weight": 0.25},
            "agent_supervision": {"description": "Supervise agent behavior", "weight": 0.25},
        },
    },
    "C3": {
        "name": "Evidence & Compliance Automation",
        "skills": {
            "control_definition": {"description": "Define compliance controls", "weight": 0.2},
            "workflow_design": {"description": "Design compliance workflows", "weight": 0.2},
            "evidence_collection": {"description": "Collect and verify evidence", "weight": 0.2},
            "continuous_monitoring": {"description": "Set up continuous compliance monitoring", "weight": 0.2},
            "drift_detection": {"description": "Detect and respond to compliance drift", "weight": 0.2},
        },
    },
    "C4": {
        "name": "Integration & Federation",
        "skills": {
            "a2z_connector_setup": {"description": "Set up A2Z SOC connector", "weight": 0.25},
            "federated_mesh_config": {"description": "Configure federated compliance mesh", "weight": 0.25},
            "cross_org_evidence": {"description": "Share evidence across organizations", "weight": 0.25},
            "trust_establishment": {"description": "Establish trust between instances", "weight": 0.25},
        },
    },
    "C5": {
        "name": "Risk Assessment & Treatment",
        "skills": {
            "risk_identification": {"description": "Identify and catalog risks", "weight": 0.2},
            "risk_scoring": {"description": "Score risks using the risk formula", "weight": 0.2},
            "treatment_optimization": {"description": "Optimize risk treatment plans", "weight": 0.2},
            "threat_correlation": {"description": "Correlate threat intelligence with risks", "weight": 0.2},
            "residual_risk_analysis": {"description": "Analyze residual risk after treatment", "weight": 0.2},
        },
    },
    "C6": {
        "name": "Knowledge & Intelligence",
        "skills": {
            "graph_querying": {"description": "Query the compliance knowledge graph", "weight": 0.25},
            "intelligence_api_usage": {"description": "Use the compliance intelligence API", "weight": 0.25},
            "zk_proof_generation": {"description": "Generate ZK compliance proofs", "weight": 0.25},
            "zk_proof_verification": {"description": "Verify ZK compliance proofs", "weight": 0.25},
        },
    },
    "C7": {
        "name": "Threat Intelligence & AI Security",
        "skills": {
            "threat_feed_ingestion": {"description": "Ingest and process threat feeds", "weight": 0.25},
            "ai_threat_detection": {"description": "Detect AI-specific threats", "weight": 0.25},
            "ioc_mapping": {"description": "Map IOCs to compliance controls", "weight": 0.25},
            "incident_correlation": {"description": "Correlate threats with incidents", "weight": 0.25},
        },
    },
    "C8": {
        "name": "AI Governance & Model Risk",
        "skills": {
            "model_registration": {"description": "Register AI models in the registry", "weight": 0.2},
            "risk_classification": {"description": "Classify model risk levels", "weight": 0.2},
            "bias_assessment": {"description": "Assess model bias and fairness", "weight": 0.2},
            "continuous_model_monitoring": {"description": "Monitor models in production", "weight": 0.2},
            "model_lifecycle_management": {"description": "Manage model lifecycle", "weight": 0.2},
        },
    },
    "C9": {
        "name": "Business Impact & Financial Governance",
        "skills": {
            "bia_execution": {"description": "Execute business impact analysis", "weight": 0.25},
            "financial_reporting": {"description": "Generate financial governance reports", "weight": 0.25},
            "roi_calculation": {"description": "Calculate compliance ROI", "weight": 0.25},
            "investment_optimization": {"description": "Optimize compliance investments", "weight": 0.25},
        },
    },
    "C10": {
        "name": "Audit & Assurance",
        "skills": {
            "audit_planning": {"description": "Plan and scope audits", "weight": 0.2},
            "evidence_automation": {"description": "Automate evidence collection", "weight": 0.2},
            "finding_management": {"description": "Manage audit findings", "weight": 0.2},
            "assurance_envelope_creation": {"description": "Create assurance envelopes", "weight": 0.2},
            "audit_simulation": {"description": "Run audit simulations", "weight": 0.2},
        },
    },
}

ROLE_SKILL_REQUIREMENTS = {
    "soc_analyst": {"C1": "intermediate", "C2": "beginner", "C3": "beginner"},
    "compliance_analyst": {"C1": "intermediate", "C3": "intermediate", "C6": "beginner"},
    "security_engineer": {"C1": "intermediate", "C2": "intermediate", "C4": "beginner"},
    "risk_analyst": {"C5": "intermediate", "C9": "beginner", "C3": "intermediate"},
    "ai_governance_lead": {"C8": "intermediate", "C2": "intermediate", "C5": "beginner"},
    "security_auditor": {"C10": "intermediate", "C3": "advanced", "C6": "intermediate"},
    "grc_architect": {"C1": "advanced", "C4": "advanced", "C6": "advanced", "C10": "intermediate"},
    "ciso": {"C1": "advanced", "C5": "advanced", "C9": "advanced", "C10": "advanced"},
}


class SkillAssessmentEngine:
    """Assesses and tracks learner skills across all competencies."""

    def __init__(self, data_dir: str = "~/.grc_claw/assessment"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.assessments_file = self.data_dir / "skill_assessments.json"
        self.assessments = self._load_assessments()

    def _load_assessments(self) -> dict:
        if self.assessments_file.exists():
            with open(self.assessments_file) as f:
                return json.load(f)
        return {}

    def _save_assessments(self):
        with open(self.assessments_file, "w") as f:
            json.dump(self.assessments, f, indent=2)

    def _score_to_level(self, score_pct: float) -> SkillLevel:
        if score_pct >= 90: return SkillLevel.EXPERT
        if score_pct >= 75: return SkillLevel.ADVANCED
        if score_pct >= 60: return SkillLevel.INTERMEDIATE
        if score_pct >= 40: return SkillLevel.BEGINNER
        return SkillLevel.NOVICE

    def _level_to_score(self, level: SkillLevel) -> int:
        return {SkillLevel.NOVICE: 1, SkillLevel.BEGINNER: 2, SkillLevel.INTERMEDIATE: 3,
                SkillLevel.ADVANCED: 4, SkillLevel.EXPERT: 5}[level]

    def conduct_assessment(self, user_id: str, competency_id: str,
                           assessment_type: AssessmentType,
                           skill_scores: dict[str, float],
                           assessor: str = "system",
                           notes: str = "") -> dict:
        """Conduct a skill assessment for a specific competency."""
        if competency_id not in COMPETENCY_SKILL_MATRIX:
            raise ValueError(f"Unknown competency: {competency_id}")

        matrix = COMPETENCY_SKILL_MATRIX[competency_id]
        skills = matrix["skills"]

        # Calculate weighted score
        total_weight = 0
        weighted_sum = 0
        for skill_id, skill_info in skills.items():
            score = skill_scores.get(skill_id, 0)
            weight = skill_info["weight"]
            weighted_sum += score * weight
            total_weight += weight

        final_score = round(weighted_sum / total_weight * 100, 1) if total_weight > 0 else 0
        level = self._score_to_level(final_score)

        assessment = {
            "assessment_id": str(uuid.uuid4()),
            "user_id": user_id,
            "competency_id": competency_id,
            "competency_name": matrix["name"],
            "assessment_type": assessment_type.value,
            "score": final_score,
            "max_score": 100.0,
            "level": level.value,
            "assessed_at": datetime.now().isoformat(),
            "assessor": assessor,
            "skill_breakdown": {sid: {"score": skill_scores.get(sid, 0),
                                       "description": skills[sid]["description"]}
                                for sid in skills},
            "evidence_refs": [],
            "notes": notes,
            "next_assessment_recommended": (datetime.now() + timedelta(days=90)).isoformat(),
        }

        if user_id not in self.assessments:
            self.assessments[user_id] = []
        self.assessments[user_id].append(assessment)
        self._save_assessments()
        return assessment

    def get_competency_assessment(self, user_id: str, competency_id: str) -> dict:
        """Get latest assessment for a competency."""
        user_assessments = self.assessments.get(user_id, [])
        comp_assessments = [a for a in user_assessments if a["competency_id"] == competency_id]
        if not comp_assessments:
            return {"error": f"No assessment found for {competency_id}"}
        return sorted(comp_assessments, key=lambda x: x["assessed_at"], reverse=True)[0]

    def get_full_assessment(self, user_id: str) -> dict:
        """Get full assessment across all competencies."""
        user_assessments = self.assessments.get(user_id, [])
        competency_results = {}
        for cid in COMPETENCY_SKILL_MATRIX:
            comp_assessments = [a for a in user_assessments if a["competency_id"] == cid]
            if comp_assessments:
                latest = sorted(comp_assessments, key=lambda x: x["assessed_at"], reverse=True)[0]
                competency_results[cid] = {
                    "name": COMPETENCY_SKILL_MATRIX[cid]["name"],
                    "level": latest["level"],
                    "score": latest["score"],
                    "assessed_at": latest["assessed_at"],
                    "skill_breakdown": latest["skill_breakdown"],
                }
            else:
                competency_results[cid] = {
                    "name": COMPETENCY_SKILL_MATRIX[cid]["name"],
                    "level": "not_assessed",
                    "score": 0,
                    "assessed_at": None,
                    "skill_breakdown": {},
                }
        return {
            "user_id": user_id,
            "competencies": competency_results,
            "overall_level": self._calculate_overall_level(competency_results),
            "assessment_count": len(user_assessments),
        }

    def _calculate_overall_level(self, competency_results: dict) -> str:
        levels = [r["level"] for r in competency_results.values() if r["level"] != "not_assessed"]
        if not levels:
            return "not_assessed"
        # Return the minimum level (weakest competency)
        level_order = ["novice", "beginner", "intermediate", "advanced", "expert"]
        return min(levels, key=lambda x: level_order.index(x) if x in level_order else 0)

    def identify_skill_gaps(self, user_id: str, target_role: str) -> list[SkillGap]:
        """Identify skill gaps for a target role."""
        if target_role not in ROLE_SKILL_REQUIREMENTS:
            raise ValueError(f"Unknown role: {target_role}")

        requirements = ROLE_SKILL_REQUIREMENTS[target_role]
        user_assessments = self.assessments.get(user_id, [])
        gaps = []

        for cid, required_level in requirements.items():
            comp_assessments = [a for a in user_assessments if a["competency_id"] == cid]
            if comp_assessments:
                latest = sorted(comp_assessments, key=lambda x: x["assessed_at"], reverse=True)[0]
                current_level = SkillLevel(latest["level"])
            else:
                current_level = SkillLevel.NOVICE

            required_score = self._level_to_score(SkillLevel(required_level))
            current_score = self._level_to_score(current_level)
            gap = required_score - current_score

            if gap > 0:
                severity = "critical" if gap >= 3 else "high" if gap == 2 else "medium" if gap == 1 else "low"
                gaps.append(SkillGap(
                    competency_id=cid,
                    current_level=current_level,
                    required_level=SkillLevel(required_level),
                    gap_severity=severity,
                    recommended_actions=self._get_remediation_actions(cid, current_level, SkillLevel(required_level)),
                    estimated_hours_to_close=gap * 10,
                ))

        return sorted(gaps, key=lambda x: self._level_to_score(x.required_level) - self._level_to_score(x.current_level), reverse=True)

    def _get_remediation_actions(self, cid: str, current: SkillLevel, required: SkillLevel) -> list[str]:
        actions = []
        if current == SkillLevel.NOVICE:
            actions.append(f"Complete introductory training for {COMPETENCY_SKILL_MATRIX[cid]['name']}")
        if required in [SkillLevel.INTERMEDIATE, SkillLevel.ADVANCED, SkillLevel.EXPERT]:
            actions.append(f"Complete hands-on labs for {COMPETENCY_SKILL_MATRIX[cid]['name']}")
        if required in [SkillLevel.ADVANCED, SkillLevel.EXPERT]:
            actions.append(f"Complete advanced scenarios for {COMPETENCY_SKILL_MATRIX[cid]['name']}")
            actions.append(f"Participate in peer review for {COMPETENCY_SKILL_MATRIX[cid]['name']}")
        if required == SkillLevel.EXPERT:
            actions.append(f"Mentor others in {COMPETENCY_SKILL_MATRIX[cid]['name']}")
            actions.append(f"Lead a capstone project in {COMPETENCY_SKILL_MATRIX[cid]['name']}")
        return actions

    def get_improvement_plan(self, user_id: str, target_role: str) -> dict:
        """Generate a personalized improvement plan."""
        gaps = self.identify_skill_gaps(user_id, target_role)
        plan = {
            "user_id": user_id,
            "target_role": target_role,
            "generated_at": datetime.now().isoformat(),
            "gaps": [{
                "competency_id": g.competency_id,
                "competency_name": COMPETENCY_SKILL_MATRIX[g.competency_id]["name"],
                "current_level": g.current_level.value,
                "required_level": g.required_level.value,
                "severity": g.gap_severity,
                "estimated_hours": g.estimated_hours_to_close,
                "actions": g.recommended_actions,
            } for g in gaps],
            "total_estimated_hours": sum(g.estimated_hours_to_close for g in gaps),
            "priority_order": [g.competency_id for g in gaps],
        }
        return plan

    def get_skill_analytics(self, user_id: str) -> dict:
        """Get skill development analytics."""
        user_assessments = self.assessments.get(user_id, [])
        if not user_assessments:
            return {"error": "No assessments found"}

        # Score progression
        progression = {}
        for cid in COMPETENCY_SKILL_MATRIX:
            comp_assessments = sorted(
                [a for a in user_assessments if a["competency_id"] == cid],
                key=lambda x: x["assessed_at"]
            )
            if comp_assessments:
                progression[cid] = {
                    "name": COMPETENCY_SKILL_MATRIX[cid]["name"],
                    "scores": [a["score"] for a in comp_assessments],
                    "levels": [a["level"] for a in comp_assessments],
                    "trend": "improving" if len(comp_assessments) > 1 and
                             comp_assessments[-1]["score"] > comp_assessments[0]["score"] else "stable",
                }

        # Assessment type distribution
        type_dist = defaultdict(int)
        for a in user_assessments:
            type_dist[a["assessment_type"]] += 1

        return {
            "user_id": user_id,
            "total_assessments": len(user_assessments),
            "progression": progression,
            "assessment_type_distribution": dict(type_dist),
            "average_score": round(sum(a["score"] for a in user_assessments) / len(user_assessments), 1),
            "strongest_competency": max(progression.items(), key=lambda x: x[1]["scores"][-1])[0] if progression else None,
            "weakest_competency": min(progression.items(), key=lambda x: x[1]["scores"][-1])[0] if progression else None,
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GRC_Claw Skill Assessment Engine")
    parser.add_argument("--user", type=str, help="User ID")
    parser.add_argument("--assess", type=str, nargs=3, metavar=("USER_ID", "COMPETENCY_ID", "TYPE"),
                        help="Conduct assessment")
    parser.add_argument("--skill-scores", type=str, help="JSON dict of skill scores")
    parser.add_argument("--full", type=str, help="Get full assessment for user")
    parser.add_argument("--gaps", type=str, nargs=2, metavar=("USER_ID", "ROLE"), help="Identify skill gaps")
    parser.add_argument("--plan", type=str, nargs=2, metavar=("USER_ID", "ROLE"), help="Get improvement plan")
    parser.add_argument("--analytics", type=str, help="Get skill analytics")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    engine = SkillAssessmentEngine()

    if args.assess:
        user_id, cid, atype = args.assess
        scores = json.loads(args.skill_scores) if args.skill_scores else {}
        result = engine.conduct_assessment(user_id, cid, AssessmentType(atype), scores)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Assessment complete: {result['competency_name']}")
            print(f"Score: {result['score']}% | Level: {result['level']}")

    elif args.full:
        result = engine.get_full_assessment(args.full)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nFull Assessment for {args.full}")
            print(f"Overall Level: {result['overall_level']}")
            for cid, c in result["competencies"].items():
                print(f"  {cid}: {c['name']} - {c['level']} ({c['score']}%)")

    elif args.gaps:
        user_id, role = args.gaps
        gaps = engine.identify_skill_gaps(user_id, role)
        if args.json:
            print(json.dumps([asdict(g) for g in gaps], indent=2))
        else:
            print(f"\nSkill Gaps for {role}:")
            for g in gaps:
                print(f"  {g.competency_id}: {g.current_level.value} → {g.required_level.value} ({g.gap_severity})")

    elif args.plan:
        user_id, role = args.plan
        result = engine.get_improvement_plan(user_id, role)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nImprovement Plan for {role}")
            print(f"Total estimated hours: {result['total_estimated_hours']}")
            for g in result["gaps"]:
                print(f"\n  {g['competency_name']} ({g['severity']})")
                print(f"  {g['current_level']} → {g['required_level']} ({g['estimated_hours']}h)")
                for a in g["actions"]:
                    print(f"    - {a}")

    elif args.analytics:
        result = engine.get_skill_analytics(args.analytics)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nSkill Analytics for {args.analytics}")
            print(f"Total assessments: {result['total_assessments']}")
            print(f"Average score: {result['average_score']}%")
            if result.get("strongest_competency"):
                print(f"Strongest: {result['strongest_competency']}")
                print(f"Weakest: {result['weakest_competency']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
