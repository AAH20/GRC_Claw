#!/usr/bin/env python3
"""
GRC_Claw Progress Tracking Dashboard
====================================
Tracks learning progress, competency development, and training effectiveness.
Supports individual, manager, and governance views.
"""

import json, uuid, sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from collections import defaultdict


class CompetencyLevel(str, Enum):
    NONE = "none"
    AWARE = "aware"
    WORKING = "working"
    EXPERT = "expert"


@dataclass
class CompetencyState:
    competency_id: str
    name: str
    description: str
    level: CompetencyLevel = CompetencyLevel.NONE
    verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    evidence_refs: list[str] = field(default_factory=list)
    assessment_score: float = 0.0


@dataclass
class LearningRecord:
    record_id: str
    user_id: str
    module_id: str
    tutorial_id: str
    status: str  # not_started, in_progress, completed
    start_date: Optional[str] = None
    complete_date: Optional[str] = None
    score: float = 0.0
    duration_minutes: int = 0
    evidence_refs: list[str] = field(default_factory=list)
    competencies_addressed: list[str] = field(default_factory=list)


@dataclass
class LearnerProgress:
    user_id: str
    name: str
    role: str
    tier: int
    department: str
    start_date: str
    competencies: dict[str, CompetencyState] = field(default_factory=dict)
    learning_records: list[LearningRecord] = field(default_factory=list)
    certifications: list[dict] = field(default_factory=list)
    total_learning_minutes: int = 0
    streak_days: int = 0
    last_activity: Optional[str] = None
    engagement_score: float = 0.0
    knowledge_retention: float = 0.0
    learning_velocity: float = 0.0


COMPETENCY_DEFINITIONS = {
    "C1": {"name": "GRC Architecture & Fundamentals", "description": "Understanding of GRC_Claw architecture, planes, and core concepts"},
    "C2": {"name": "Agent Runtime & Policy", "description": "Agent runtime, policy firewall, trust scoring, and action ledger"},
    "C3": {"name": "Evidence & Compliance Automation", "description": "Evidence plane, controls, orchestration, and continuous compliance"},
    "C4": {"name": "Integration & Federation", "description": "A2Z SOC integration, federated mesh, and cross-organizational compliance"},
    "C5": {"name": "Risk Assessment & Treatment", "description": "Risk assessment, treatment optimization, and threat intelligence"},
    "C6": {"name": "Knowledge & Intelligence", "description": "Knowledge graph, compliance intelligence, and ZK proofs"},
    "C7": {"name": "Threat Intelligence & AI Security", "description": "Threat detection, AI-specific threats, and security monitoring"},
    "C8": {"name": "AI Governance & Model Risk", "description": "Model governance, risk classification, and continuous monitoring"},
    "C9": {"name": "Business Impact & Financial Governance", "description": "Business impact analysis, financial governance, and ROI"},
    "C10": {"name": "Audit & Assurance", "description": "Audit management, evidence automation, and assurance"},
}

ROLE_REQUIREMENTS = {
    "soc_analyst": {"tier": 1, "required": {"C1": "working", "C2": "aware", "C3": "aware"}},
    "compliance_analyst": {"tier": 2, "required": {"C1": "working", "C3": "working", "C6": "aware"}},
    "security_engineer": {"tier": 2, "required": {"C1": "working", "C2": "working", "C4": "aware"}},
    "risk_analyst": {"tier": 3, "required": {"C5": "working", "C9": "aware", "C3": "working"}},
    "ai_governance_lead": {"tier": 3, "required": {"C8": "working", "C2": "working", "C5": "aware"}},
    "security_auditor": {"tier": 3, "required": {"C10": "working", "C3": "expert", "C6": "working"}},
    "grc_architect": {"tier": 4, "required": {"C1": "expert", "C4": "expert", "C6": "expert", "C10": "working"}},
    "ciso": {"tier": 4, "required": {"C1": "expert", "C5": "expert", "C9": "expert", "C10": "expert"}},
}


class ProgressDashboard:
    """Progress tracking dashboard with individual, manager, and governance views."""

    def __init__(self, data_dir: str = "~/.grc_claw/progress"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.data_dir / "learner_progress.json"
        self.progress = self._load_progress()

    def _load_progress(self) -> dict:
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                return json.load(f)
        return {}

    def _save_progress(self):
        with open(self.progress_file, "w") as f:
            json.dump(self.progress, f, indent=2)

    def get_or_create_progress(self, user_id: str, name: str = "", role: str = "",
                               tier: int = 1, department: str = "") -> dict:
        if user_id not in self.progress:
            self.progress[user_id] = {
                "user_id": user_id,
                "name": name,
                "role": role,
                "tier": tier,
                "department": department,
                "start_date": datetime.now().isoformat(),
                "competencies": {cid: {"competency_id": cid, **COMPETENCY_DEFINITIONS[cid],
                                       "level": "none", "verified_at": None, "expires_at": None,
                                       "evidence_refs": [], "assessment_score": 0.0}
                                 for cid in COMPETENCY_DEFINITIONS},
                "learning_records": [],
                "certifications": [],
                "total_learning_minutes": 0,
                "streak_days": 0,
                "last_activity": None,
                "engagement_score": 0.0,
                "knowledge_retention": 0.0,
                "learning_velocity": 0.0,
            }
            self._save_progress()
        return self.progress[user_id]

    def record_learning_activity(self, user_id: str, tutorial_id: str, module_id: str,
                                 event_type: str, score: float = 0.0,
                                 duration_minutes: int = 0,
                                 competencies: list[str] = None) -> dict:
        """Record a learning activity event."""
        p = self.get_or_create_progress(user_id)
        now = datetime.now().isoformat()

        record = {
            "record_id": str(uuid.uuid4()),
            "user_id": user_id,
            "module_id": module_id,
            "tutorial_id": tutorial_id,
            "status": event_type,
            "start_date": now if event_type == "started" else None,
            "complete_date": now if event_type == "completed" else None,
            "score": score,
            "duration_minutes": duration_minutes,
            "evidence_refs": [],
            "competencies_addressed": competencies or [],
        }
        p["learning_records"].append(record)
        p["last_activity"] = now
        p["total_learning_minutes"] += duration_minutes

        # Update competency levels based on completed tutorials
        if event_type == "completed" and competencies:
            for comp in competencies:
                if comp in p["competencies"]:
                    comp_state = p["competencies"][comp]
                    if comp_state["level"] == "none":
                        comp_state["level"] = "aware"
                    elif comp_state["level"] == "aware" and score >= 70:
                        comp_state["level"] = "working"
                    elif comp_state["level"] == "working" and score >= 90:
                        comp_state["level"] = "expert"
                    comp_state["verified_at"] = now
                    comp_state["assessment_score"] = score
                    # Set expiry (12 months)
                    comp_state["expires_at"] = (datetime.now() + timedelta(days=365)).isoformat()

        # Update analytics
        self._update_analytics(p)
        self._save_progress()
        return p

    def _update_analytics(self, p: dict):
        """Update learner analytics."""
        records = p["learning_records"]
        if not records:
            return

        # Learning velocity (modules per month)
        if len(records) > 1:
            first = datetime.fromisoformat(records[0].get("start_date") or records[0].get("complete_date", datetime.now().isoformat()))
            last = datetime.fromisoformat(records[-1].get("complete_date") or records[-1].get("start_date", datetime.now().isoformat()))
            months = max((last - first).days / 30, 1)
            p["learning_velocity"] = round(len(records) / months, 2)

        # Engagement score (0-100)
        recent = [r for r in records if r.get("complete_date")]
        if recent:
            scores = [r.get("score", 0) for r in recent[-10:]]
            p["engagement_score"] = round(sum(scores) / len(scores), 1)

        # Knowledge retention (based on score trend)
        if len(recent) >= 3:
            recent_scores = [r.get("score", 0) for r in recent[-5:]]
            older_scores = [r.get("score", 0) for r in recent[-10:-5]] if len(recent) >= 5 else recent_scores
            if older_scores:
                retention = (sum(recent_scores) / len(recent_scores)) / (sum(older_scores) / len(older_scores)) * 100
                p["knowledge_retention"] = round(min(retention, 100), 1)

    def get_individual_dashboard(self, user_id: str) -> dict:
        """Get individual learner dashboard."""
        p = self.get_or_create_progress(user_id)
        role_req = ROLE_REQUIREMENTS.get(p["role"], {"required": {}})

        # Competency radar data
        competency_radar = []
        for cid, cstate in p["competencies"].items():
            required = role_req.get("required", {}).get(cid, "none")
            competency_radar.append({
                "competency": cid,
                "name": cstate["name"],
                "current_level": cstate["level"],
                "required_level": required,
                "gap": self._level_gap(cstate["level"], required),
                "score": cstate["assessment_score"],
                "verified_at": cstate["verified_at"],
                "expires_at": cstate["expires_at"],
            })

        # Learning path progress
        modules = defaultdict(lambda: {"completed": 0, "in_progress": 0, "not_started": 0})
        for r in p["learning_records"]:
            modules[r["module_id"]][r["status"] if r["status"] in ["completed", "in_progress"] else "not_started"] += 1

        # Knowledge decay curve
        decay_curve = []
        for cid, cstate in p["competencies"].items():
            if cstate["level"] != "none" and cstate["verified_at"]:
                verified = datetime.fromisoformat(cstate["verified_at"])
                days_since = (datetime.now() - verified).days
                decay = min(days_since / 365 * 20, 20)  # 20% decay per year
                decay_curve.append({
                    "competency": cid,
                    "level": cstate["level"],
                    "days_since_verified": days_since,
                    "projected_decay_pct": round(decay, 1),
                    "risk": "high" if decay > 15 else "medium" if decay > 10 else "low",
                })

        # Recommended next steps
        recommendations = self._generate_recommendations(p, role_req)

        return {
            "user_id": user_id,
            "name": p["name"],
            "role": p["role"],
            "tier": p["tier"],
            "department": p["department"],
            "summary": {
                "total_learning_minutes": p["total_learning_minutes"],
                "modules_completed": sum(1 for r in p["learning_records"] if r["status"] == "completed"),
                "modules_in_progress": sum(1 for r in p["learning_records"] if r["status"] == "in_progress"),
                "average_score": round(sum(r.get("score", 0) for r in p["learning_records"]) / len(p["learning_records"]), 1) if p["learning_records"] else 0,
                "engagement_score": p["engagement_score"],
                "knowledge_retention": p["knowledge_retention"],
                "learning_velocity": p["learning_velocity"],
                "streak_days": p["streak_days"],
            },
            "competency_radar": competency_radar,
            "module_progress": dict(modules),
            "knowledge_decay": decay_curve,
            "certifications": p["certifications"],
            "recommendations": recommendations,
        }

    def _level_gap(self, current: str, required: str) -> int:
        levels = {"none": 0, "aware": 1, "working": 2, "expert": 3}
        return max(0, levels.get(required, 0) - levels.get(current, 0))

    def _generate_recommendations(self, p: dict, role_req: dict) -> list[dict]:
        recs = []
        # Check competency gaps
        for cid, cstate in p["competencies"].items():
            required = role_req.get("required", {}).get(cid, "none")
            gap = self._level_gap(cstate["level"], required)
            if gap > 0:
                recs.append({
                    "type": "competency_gap",
                    "priority": "high" if gap > 1 else "medium",
                    "competency": cid,
                    "name": cstate["name"],
                    "current": cstate["level"],
                    "required": required,
                    "action": f"Complete training for {cstate['name']}",
                })
        # Check knowledge decay
        for cid, cstate in p["competencies"].items():
            if cstate["expires_at"]:
                expires = datetime.fromisoformat(cstate["expires_at"])
                days_to_expire = (expires - datetime.now()).days
                if days_to_expire < 30:
                    recs.append({
                        "type": "knowledge_decay",
                        "priority": "high" if days_to_expire < 7 else "medium",
                        "competency": cid,
                        "name": cstate["name"],
                        "days_to_expire": days_to_expire,
                        "action": f"Refresh {cstate['name']} certification",
                    })
        return sorted(recs, key=lambda x: (x["priority"] != "high", x.get("days_to_expire", 999)))

    def get_manager_dashboard(self, manager_id: str, team_members: list[str]) -> dict:
        """Get manager dashboard for team overview."""
        team_data = []
        for uid in team_members:
            p = self.progress.get(uid)
            if p:
                team_data.append({
                    "user_id": uid,
                    "name": p["name"],
                    "role": p["role"],
                    "tier": p["tier"],
                    "competencies": {cid: c["level"] for cid, c in p["competencies"].items()},
                    "modules_completed": sum(1 for r in p["learning_records"] if r["status"] == "completed"),
                    "average_score": round(sum(r.get("score", 0) for r in p["learning_records"]) / len(p["learning_records"]), 1) if p["learning_records"] else 0,
                    "engagement_score": p["engagement_score"],
                    "last_activity": p["last_activity"],
                })

        # Team competency matrix
        competency_matrix = {}
        for cid in COMPETENCY_DEFINITIONS:
            competency_matrix[cid] = {
                "name": COMPETENCY_DEFINITIONS[cid]["name"],
                "levels": {uid: p["competencies"][cid]["level"] for uid, p in
                           [(d["user_id"], self.progress.get(d["user_id"], {})) for d in team_data]
                           if p and cid in p.get("competencies", {})},
            }

        # At-risk learners
        at_risk = []
        for d in team_data:
            risk_factors = []
            if d["engagement_score"] < 50:
                risk_factors.append("low_engagement")
            if d["last_activity"] and (datetime.now() - datetime.fromisoformat(d["last_activity"])).days > 14:
                risk_factors.append("inactive")
            if risk_factors:
                at_risk.append({
                    "user_id": d["user_id"],
                    "name": d["name"],
                    "risk_factors": risk_factors,
                })

        return {
            "manager_id": manager_id,
            "team_size": len(team_data),
            "team_members": team_data,
            "competency_matrix": competency_matrix,
            "at_risk_learners": at_risk,
            "team_average_score": round(sum(d["average_score"] for d in team_data) / len(team_data), 1) if team_data else 0,
            "total_team_learning_minutes": sum(self.progress.get(d["user_id"], {}).get("total_learning_minutes", 0) for d in team_data),
        }

    def get_governance_dashboard(self) -> dict:
        """Get organization-wide governance dashboard."""
        all_users = list(self.progress.values())
        if not all_users:
            return {"error": "No learner data available"}

        # Organization competency posture
        org_competency = {}
        for cid in COMPETENCY_DEFINITIONS:
            levels = defaultdict(int)
            for p in all_users:
                level = p["competencies"][cid]["level"]
                levels[level] += 1
            org_competency[cid] = {
                "name": COMPETENCY_DEFINITIONS[cid]["name"],
                "distribution": dict(levels),
                "coverage_pct": round((levels.get("working", 0) + levels.get("expert", 0)) / len(all_users) * 100, 1),
            }

        # Clause 7.2 evidence readiness
        total_users = len(all_users)
        users_with_evidence = sum(1 for p in all_users
                                   if any(c["evidence_refs"] for c in p["competencies"].values()))
        evidence_readiness = round(users_with_evidence / total_users * 100, 1) if total_users else 0

        # Certification pipeline
        cert_pipeline = []
        for p in all_users:
            for cert in p.get("certifications", []):
                cert_pipeline.append({
                    "user_id": p["user_id"],
                    "name": p["name"],
                    "certification": cert,
                })

        # Training investment
        total_minutes = sum(p["total_learning_minutes"] for p in all_users)
        total_modules = sum(sum(1 for r in p["learning_records"] if r["status"] == "completed") for p in all_users)

        return {
            "total_learners": total_users,
            "organization_competency": org_competency,
            "clause_7_2_readiness": evidence_readiness,
            "certification_pipeline": cert_pipeline,
            "training_investment": {
                "total_learning_hours": round(total_minutes / 60, 1),
                "total_modules_completed": total_modules,
                "average_score": round(sum(r.get("score", 0) for p in all_users for r in p["learning_records"]) /
                                        sum(len(p["learning_records"]) for p in all_users), 1) if any(p["learning_records"] for p in all_users) else 0,
            },
            "at_risk_count": sum(1 for p in all_users if p["engagement_score"] < 50),
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GRC_Claw Progress Tracking Dashboard")
    parser.add_argument("--user", type=str, help="User ID for individual dashboard")
    parser.add_argument("--manager", type=str, help="Manager ID for team dashboard")
    parser.add_argument("--team", type=str, nargs="+", help="Team member user IDs")
    parser.add_argument("--governance", action="store_true", help="Show governance dashboard")
    parser.add_argument("--record", type=str, nargs=4, metavar=("USER_ID", "TUTORIAL_ID", "MODULE_ID", "EVENT"),
                        help="Record learning activity")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    dash = ProgressDashboard()

    if args.record:
        user_id, tutorial_id, module_id, event = args.record
        result = dash.record_learning_activity(user_id, tutorial_id, module_id, event)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Recorded {event} for user {user_id}: {tutorial_id}")

    elif args.user:
        result = dash.get_individual_dashboard(args.user)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            d = result
            print(f"\n{'='*60}")
            print(f"Individual Dashboard: {d['name']}")
            print(f"{'='*60}")
            print(f"Role: {d['role']} | Tier: {d['tier']} | Dept: {d['department']}")
            s = d["summary"]
            print(f"\nLearning: {s['modules_completed']} completed, {s['modules_in_progress']} in progress")
            print(f"Total time: {s['total_learning_minutes']} min | Avg score: {s['average_score']}%")
            print(f"Engagement: {s['engagement_score']}% | Retention: {s['knowledge_retention']}%")
            print(f"\nCompetency Radar:")
            for c in d["competency_radar"]:
                if c["current_level"] != "none":
                    gap = "✓" if c["gap"] == 0 else f"gap={c['gap']}"
                    print(f"  {c['competency']}: {c['current_level']} (req: {c['required_level']}) {gap}")
            if d["recommendations"]:
                print(f"\nRecommendations:")
                for r in d["recommendations"][:3]:
                    print(f"  [{r['priority']}] {r['action']}")

    elif args.manager and args.team:
        result = dash.get_manager_dashboard(args.manager, args.team)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            d = result
            print(f"\n{'='*60}")
            print(f"Manager Dashboard")
            print(f"{'='*60}")
            print(f"Team size: {d['team_size']}")
            print(f"Team avg score: {d['team_average_score']}%")
            print(f"Total learning: {d['total_team_learning_minutes']} min")
            if d["at_risk_learners"]:
                print(f"\nAt-risk learners:")
                for r in d["at_risk_learners"]:
                    print(f"  {r['name']}: {', '.join(r['risk_factors'])}")

    elif args.governance:
        result = dash.get_governance_dashboard()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            d = result
            print(f"\n{'='*60}")
            print(f"Governance Dashboard")
            print(f"{'='*60}")
            print(f"Total learners: {d['total_learners']}")
            print(f"Clause 7.2 readiness: {d['clause_7_2_readiness']}%")
            print(f"Training investment: {d['training_investment']['total_learning_hours']} hours")
            print(f"At-risk count: {d['at_risk_count']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
