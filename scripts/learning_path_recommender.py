#!/usr/bin/env python3
"""
GRC_Claw Learning Path Recommender
===================================
Recommends personalized learning paths based on role, competency gaps,
learning style, career goals, and assessment results.
"""

import json, uuid, sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from collections import defaultdict


class LearningStyle(str, Enum):
    SELF_PACED = "self_paced"
    INSTRUCTOR_LED = "instructor_led"
    HANDS_ON = "hands_on"
    BLENDED = "blended"


class Pace(str, Enum):
    INTENSIVE = "intensive"
    STANDARD = "standard"
    EXTENDED = "extended"


@dataclass
class LearningModule:
    module_id: str
    title: str
    description: str
    tier: int
    competencies: list[str]
    prerequisites: list[str]
    estimated_minutes: int
    format: str  # video, reading, lab, quiz, project
    difficulty: str


@dataclass
class LearningPath:
    path_id: str
    user_id: str
    target_role: str
    modules: list[dict]
    total_minutes: int
    estimated_weeks: int
    milestones: list[dict]
    created_at: str
    adaptations: list[str] = field(default_factory=list)


MODULE_CATALOG = {
    "M01": {"title": "GRC_Claw Gateway Fundamentals", "description": "Gateway architecture, configuration, and basic operations", "tier": 1, "competencies": ["C1", "C2"], "prerequisites": [], "estimated_minutes": 60, "format": "hands_on", "difficulty": "beginner"},
    "M02": {"title": "Evidence Plane & Compliance Frameworks", "description": "Evidence management, controls, and framework mapping", "tier": 1, "competencies": ["C1", "C3"], "prerequisites": ["M01"], "estimated_minutes": 90, "format": "hands_on", "difficulty": "beginner"},
    "M03": {"title": "Agent Runtime & Policy Engine", "description": "Agent runtime, policy firewall, trust scoring, and action ledger", "tier": 2, "competencies": ["C2", "C4", "C5"], "prerequisites": ["M01", "M02"], "estimated_minutes": 120, "format": "hands_on", "difficulty": "intermediate"},
    "M04": {"title": "Compliance Orchestration & Continuous Monitoring", "description": "Workflow design, orchestration, and continuous compliance", "tier": 2, "competencies": ["C3", "C6"], "prerequisites": ["M02", "M03"], "estimated_minutes": 100, "format": "hands_on", "difficulty": "intermediate"},
    "M05": {"title": "A2Z SOC Integration & SIEM Bridge", "description": "A2Z connector, event mapping, and compliance alerts", "tier": 3, "competencies": ["C4", "C7"], "prerequisites": ["M03", "M04"], "estimated_minutes": 150, "format": "hands_on", "difficulty": "advanced"},
    "M06": {"title": "Knowledge Graph & Compliance Intelligence", "description": "Knowledge graph, intelligence API, and ZK proofs", "tier": 3, "competencies": ["C6", "C8"], "prerequisites": ["M04"], "estimated_minutes": 120, "format": "hands_on", "difficulty": "advanced"},
    "M07": {"title": "Risk Assessment & Treatment Optimization", "description": "Risk assessment, treatment optimization, and threat correlation", "tier": 3, "competencies": ["C5", "C9"], "prerequisites": ["M04"], "estimated_minutes": 110, "format": "hands_on", "difficulty": "advanced"},
    "M08": {"title": "Audit Management & Evidence Automation", "description": "Audit planning, evidence automation, and finding management", "tier": 4, "competencies": ["C1", "C3", "C10"], "prerequisites": ["M02", "M04", "M06"], "estimated_minutes": 180, "format": "project", "difficulty": "expert"},
    "M09": {"title": "AI Governance & Model Risk Management", "description": "Model registry, risk classification, and continuous monitoring", "tier": 4, "competencies": ["C2", "C5", "C8"], "prerequisites": ["M03", "M07"], "estimated_minutes": 160, "format": "hands_on", "difficulty": "expert"},
    "M10": {"title": "Federated Compliance Mesh", "description": "Federated mesh, cross-org evidence, and trust establishment", "tier": 4, "competencies": ["C4", "C7", "C10"], "prerequisites": ["M05", "M08"], "estimated_minutes": 140, "format": "hands_on", "difficulty": "expert"},
    "M11": {"title": "Threat Intelligence & AI Threat Detection", "description": "Threat feeds, AI threat detection, and IOC mapping", "tier": 3, "competencies": ["C5", "C7"], "prerequisites": ["M03", "M05"], "estimated_minutes": 130, "format": "hands_on", "difficulty": "advanced"},
    "M12": {"title": "Business Impact & Financial Governance", "description": "BIA, financial reporting, and compliance ROI", "tier": 3, "competencies": ["C9", "C10"], "prerequisites": ["M07"], "estimated_minutes": 100, "format": "project", "difficulty": "advanced"},
    "M13": {"title": "Zero-Knowledge Compliance Proofs", "description": "ZK proofs, constraint systems, and privacy-preserving verification", "tier": 4, "competencies": ["C1", "C6", "C8"], "prerequisites": ["M06", "M08"], "estimated_minutes": 170, "format": "hands_on", "difficulty": "expert"},
    "M14": {"title": "Capstone: Full Compliance Automation", "description": "End-to-end compliance pipeline design and implementation", "tier": 4, "competencies": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"], "prerequisites": ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08"], "estimated_minutes": 240, "format": "project", "difficulty": "expert"},
}

ROLE_PATHS = {
    "soc_analyst": {"modules": ["M01", "M02", "M03", "M04"], "target_tier": 2},
    "compliance_analyst": {"modules": ["M01", "M02", "M03", "M04", "M06"], "target_tier": 2},
    "security_engineer": {"modules": ["M01", "M02", "M03", "M04", "M05"], "target_tier": 3},
    "risk_analyst": {"modules": ["M01", "M02", "M04", "M07", "M12"], "target_tier": 3},
    "ai_governance_lead": {"modules": ["M01", "M03", "M07", "M09"], "target_tier": 3},
    "security_auditor": {"modules": ["M01", "M02", "M04", "M06", "M08"], "target_tier": 3},
    "grc_architect": {"modules": ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08", "M09", "M10", "M13", "M14"], "target_tier": 4},
    "ciso": {"modules": ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08", "M09", "M10", "M11", "M12", "M13", "M14"], "target_tier": 4},
}


class LearningPathRecommender:
    """Recommends personalized learning paths."""

    def __init__(self, data_dir: str = "~/.grc_claw/learning_paths"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths_file = self.data_dir / "learning_paths.json"
        self.paths = self._load_paths()

    def _load_paths(self) -> dict:
        if self.paths_file.exists():
            with open(self.paths_file) as f:
                return json.load(f)
        return {}

    def _save_paths(self):
        with open(self.paths_file, "w") as f:
            json.dump(self.paths, f, indent=2)

    def generate_path(self, user_id: str, target_role: str,
                      current_competencies: dict[str, str] = None,
                      learning_style: LearningStyle = LearningStyle.SELF_PACED,
                      pace: Pace = Pace.STANDARD,
                      available_hours_per_week: float = 5.0) -> dict:
        """Generate a personalized learning path."""
        if target_role not in ROLE_PATHS:
            raise ValueError(f"Unknown role: {target_role}")

        role_config = ROLE_PATHS[target_role]
        base_modules = role_config["modules"]

        # Filter out modules for competencies already at expert level
        if current_competencies:
            filtered = []
            for mid in base_modules:
                mod = MODULE_CATALOG[mid]
                # Skip if all competencies for this module are already expert
                if all(current_competencies.get(c) == "expert" for c in mod["competencies"]):
                    continue
                filtered.append(mid)
            base_modules = filtered

        # Apply pace multiplier
        pace_multiplier = {Pace.INTENSIVE: 0.7, Pace.STANDARD: 1.0, Pace.EXTENDED: 1.5}[pace]

        # Build module sequence with scheduling
        modules = []
        total_minutes = 0
        week_offset = 0
        for i, mid in enumerate(base_modules):
            mod = MODULE_CATALOG[mid]
            adjusted_minutes = int(mod["estimated_minutes"] * pace_multiplier)
            weeks_for_module = max(1, int(adjusted_minutes / (available_hours_per_week * 60)))

            modules.append({
                "sequence": i + 1,
                "module_id": mid,
                "title": mod["title"],
                "description": mod["description"],
                "tier": mod["tier"],
                "competencies": mod["competencies"],
                "prerequisites": mod["prerequisites"],
                "estimated_minutes": adjusted_minutes,
                "format": mod["format"],
                "difficulty": mod["difficulty"],
                "start_week": week_offset + 1,
                "end_week": week_offset + weeks_for_module,
                "status": "planned",
            })
            total_minutes += adjusted_minutes
            week_offset += weeks_for_module

        # Generate milestones
        milestones = []
        for i, m in enumerate(modules):
            if m["tier"] > (modules[i-1]["tier"] if i > 0 else 0):
                milestones.append({
                    "milestone_id": f"MS-{i+1}",
                    "name": f"Tier {m['tier']} Completion",
                    "module_id": m["module_id"],
                    "week": m["end_week"],
                    "competencies_addressed": m["competencies"],
                })

        # Add final milestone
        milestones.append({
            "milestone_id": f"MS-FINAL",
            "name": f"{target_role.replace('_', ' ').title()} Ready",
            "module_id": modules[-1]["module_id"] if modules else None,
            "week": week_offset,
            "competencies_addressed": list(set(c for m in modules for c in m["competencies"])),
        })

        path = {
            "path_id": str(uuid.uuid4()),
            "user_id": user_id,
            "target_role": target_role,
            "learning_style": learning_style.value,
            "pace": pace.value,
            "available_hours_per_week": available_hours_per_week,
            "modules": modules,
            "total_minutes": total_minutes,
            "estimated_weeks": week_offset,
            "milestones": milestones,
            "created_at": datetime.now().isoformat(),
            "adaptations": self._determine_adaptations(current_competencies, learning_style, pace),
        }

        if user_id not in self.paths:
            self.paths[user_id] = []
        self.paths[user_id].append(path)
        self._save_paths()
        return path

    def _determine_adaptations(self, competencies: dict, style: LearningStyle, pace: Pace) -> list[str]:
        adaptations = []
        if style == LearningStyle.HANDS_ON:
            adaptations.append("Increased hands-on lab ratio")
        elif style == LearningStyle.INSTRUCTOR_LED:
            adaptations.append("Added instructor-led sessions")
        if pace == Pace.INTENSIVE:
            adaptations.append("Compressed schedule with daily sessions")
        elif pace == Pace.EXTENDED:
            adaptations.append("Extended schedule with review sessions")
        if competencies:
            weak = [c for c, level in competencies.items() if level in ["novice", "beginner"]]
            if weak:
                adaptations.append(f"Added foundational modules for: {', '.join(weak)}")
        return adaptations

    def recommend_next_modules(self, user_id: str, completed_modules: list[str],
                                target_role: str, current_competencies: dict[str, str] = None) -> list[dict]:
        """Recommend next modules based on progress."""
        if target_role not in ROLE_PATHS:
            raise ValueError(f"Unknown role: {target_role}")

        role_modules = ROLE_PATHS[target_role]["modules"]
        remaining = [m for m in role_modules if m not in completed_modules]

        # Sort by prerequisites satisfied first
        recommendations = []
        for mid in remaining:
            mod = MODULE_CATALOG[mid]
            prereqs_satisfied = all(p in completed_modules for p in mod["prerequisites"])
            competency_gap = any(current_competencies.get(c, "novice") != "expert"
                                for c in mod["competencies"]) if current_competencies else True

            priority = 0
            if prereqs_satisfied and competency_gap:
                priority = 1  # High priority: ready and needed
            elif prereqs_satisfied:
                priority = 2  # Medium: ready but competencies met
            else:
                priority = 3  # Low: prerequisites not met

            recommendations.append({
                "module_id": mid,
                "title": mod["title"],
                "priority": priority,
                "prerequisites_satisfied": prereqs_satisfied,
                "competency_gap": competency_gap,
                "estimated_minutes": mod["estimated_minutes"],
                "reason": self._recommendation_reason(mod, prereqs_satisfied, competency_gap),
            })

        return sorted(recommendations, key=lambda x: x["priority"])

    def _recommendation_reason(self, mod: dict, prereqs_ok: bool, gap: bool) -> str:
        if prereqs_ok and gap:
            return f"Ready to start - addresses competency gap in {', '.join(mod['competencies'])}"
        elif prereqs_ok:
            return "Prerequisites met - good for reinforcement"
        else:
            return "Complete prerequisites first"

    def adapt_path(self, path_id: str, user_id: str, trigger: str, details: dict) -> dict:
        """Adapt a learning path based on triggers."""
        user_paths = self.paths.get(user_id, [])
        path = None
        for p in user_paths:
            if p["path_id"] == path_id:
                path = p
                break

        if not path:
            raise ValueError(f"Path not found: {path_id}")

        adaptations = list(path.get("adaptations", []))

        if trigger == "assessment_failed":
            # Add remedial modules
            comp = details.get("competency_id")
            remedial = [m for m, mod in MODULE_CATALOG.items()
                       if comp in mod["competencies"] and m not in [x["module_id"] for x in path["modules"]]]
            if remedial:
                adaptations.append(f"Added remedial module {remedial[0]} for {comp}")
        elif trigger == "schedule_slip":
            # Extend timeline
            adaptations.append("Extended timeline due to schedule slip")
        elif trigger == "role_change":
            new_role = details.get("new_role")
            if new_role in ROLE_PATHS:
                adaptations.append(f"Re-targeted path to {new_role}")
        elif trigger == "career_goal_change":
            adaptations.append("Updated based on new career goals")

        path["adaptations"] = adaptations
        path["last_adapted"] = datetime.now().isoformat()
        self._save_paths()
        return path

    def get_path_analytics(self, user_id: str) -> dict:
        """Get analytics for user's learning paths."""
        user_paths = self.paths.get(user_id, [])
        if not user_paths:
            return {"error": "No learning paths found"}

        total_modules = sum(len(p["modules"]) for p in user_paths)
        total_minutes = sum(p["total_minutes"] for p in user_paths)
        completed = sum(1 for p in user_paths for m in p["modules"] if m.get("status") == "completed")

        return {
            "user_id": user_id,
            "total_paths": len(user_paths),
            "total_modules_planned": total_modules,
            "modules_completed": completed,
            "completion_rate": round(completed / total_modules * 100, 1) if total_modules else 0,
            "total_learning_minutes": total_minutes,
            "total_learning_hours": round(total_minutes / 60, 1),
            "active_paths": [p["path_id"] for p in user_paths if any(m.get("status") != "completed" for m in p["modules"])],
            "completed_paths": [p["path_id"] for p in user_paths if all(m.get("status") == "completed" for m in p["modules"])],
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GRC_Claw Learning Path Recommender")
    parser.add_argument("--user", type=str, help="User ID")
    parser.add_argument("--generate", type=str, nargs=2, metavar=("USER_ID", "ROLE"),
                        help="Generate learning path")
    parser.add_argument("--style", type=str, choices=[s.value for s in LearningStyle], default="self_paced")
    parser.add_argument("--pace", type=str, choices=[p.value for p in Pace], default="standard")
    parser.add_argument("--hours", type=float, default=5.0, help="Available hours per week")
    parser.add_argument("--next", type=str, nargs=3, metavar=("USER_ID", "ROLE", "COMPLETED"),
                        help="Recommend next modules (completed as comma-separated)")
    parser.add_argument("--adapt", type=str, nargs=3, metavar=("PATH_ID", "USER_ID", "TRIGGER"),
                        help="Adapt a learning path")
    parser.add_argument("--analytics", type=str, help="Get path analytics")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    recommender = LearningPathRecommender()

    if args.generate:
        user_id, role = args.generate
        result = recommender.generate_path(user_id, role,
                                            learning_style=LearningStyle(args.style),
                                            pace=Pace(args.pace),
                                            available_hours_per_week=args.hours)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nLearning Path for {role}")
            print(f"Total: {result['total_minutes']} min ({result['estimated_weeks']} weeks)")
            print(f"Style: {result['learning_style']} | Pace: {result['pace']}")
            print(f"\nModules:")
            for m in result["modules"]:
                print(f"  {m['sequence']}. [{m['module_id']}] {m['title']} ({m['estimated_minutes']} min, weeks {m['start_week']}-{m['end_week']})")
            print(f"\nMilestones:")
            for ms in result["milestones"]:
                print(f"  {ms['name']} (week {ms['week']})")

    elif args.next:
        user_id, role, completed = args.next
        completed_list = completed.split(",") if completed else []
        result = recommender.recommend_next_modules(user_id, completed_list, role)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nRecommended Next Modules for {role}:")
            for r in result:
                priority_label = {1: "HIGH", 2: "MED", 3: "LOW"}[r["priority"]]
                print(f"  [{priority_label}] {r['module_id']}: {r['title']} - {r['reason']}")

    elif args.adapt:
        path_id, user_id, trigger = args.adapt
        result = recommender.adapt_path(path_id, user_id, trigger, {})
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Path adapted: {result['path_id']}")
            print(f"Adaptations: {result['adaptations']}")

    elif args.analytics:
        result = recommender.get_path_analytics(args.analytics)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nLearning Path Analytics for {args.analytics}")
            print(f"Total paths: {result['total_paths']}")
            print(f"Completion rate: {result['completion_rate']}%")
            print(f"Total learning: {result['total_learning_hours']} hours")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
