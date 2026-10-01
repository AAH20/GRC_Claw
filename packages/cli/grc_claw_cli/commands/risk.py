"""Risk management commands for GRC_Claw CLI."""
import argparse
import json
import math
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

from grc_claw_cli.utils.output import print_json, print_table, print_success, print_error, print_warning, print_info
from grc_claw_cli.utils.config import Config


RISK_LEVELS = ["low", "medium", "high", "critical"]
RISK_CATEGORIES = ["cybersecurity", "compliance", "operational", "financial", "strategic", "third-party"]
RISK_STATUSES = ["open", "mitigated", "accepted", "transferred", "avoided"]


class RiskRegister:
    """In-memory risk register with FAIR-style quantification."""

    def __init__(self):
        self.config = Config()
        self.risks = []
        self._load()

    def _load(self):
        path = self.config.CONFIG_DIR / "risks.json"
        if path.exists():
            try:
                with open(path) as f:
                    self.risks = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.risks = []

    def _save(self):
        self.config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        path = self.config.CONFIG_DIR / "risks.json"
        with open(path, "w") as f:
            json.dump(self.risks, f, indent=2, default=str)

    def add(self, title, description, category, likelihood, impact, owner, treatment=""):
        risk = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "category": category,
            "likelihood": likelihood,  # 1-5
            "impact": impact,  # 1-5
            "risk_score": likelihood * impact,
            "risk_level": self._level(likelihood * impact),
            "status": "open",
            "owner": owner,
            "treatment": treatment,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.risks.append(risk)
        self._save()
        return risk

    def get(self, risk_id):
        return next((r for r in self.risks if r["id"] == risk_id), None)

    def list(self, category=None, status=None, level=None):
        result = self.risks
        if category:
            result = [r for r in result if r["category"] == category]
        if status:
            result = [r for r in result if r["status"] == status]
        if level:
            result = [r for r in result if r["risk_level"] == level]
        return result

    def update_status(self, risk_id, new_status, treatment=""):
        risk = self.get(risk_id)
        if not risk:
            return None
        risk["status"] = new_status
        if treatment:
            risk["treatment"] = treatment
        risk["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        return risk

    def delete(self, risk_id):
        risk = self.get(risk_id)
        if not risk:
            return False
        self.risks = [r for r in self.risks if r["id"] != risk_id]
        self._save()
        return True

    def stats(self):
        by_level = {l: 0 for l in RISK_LEVELS}
        by_category = {c: 0 for c in RISK_CATEGORIES}
        by_status = {s: 0 for s in RISK_STATUSES}
        for r in self.risks:
            by_level[r["risk_level"]] = by_level.get(r["risk_level"], 0) + 1
            by_category[r["category"]] = by_category.get(r["category"], 0) + 1
            by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        return {
            "total_risks": len(self.risks),
            "by_level": by_level,
            "by_category": by_category,
            "by_status": by_status,
            "open_critical": len([r for r in self.risks if r["status"] == "open" and r["risk_level"] == "critical"]),
        }

    @staticmethod
    def _level(score):
        if score >= 20:
            return "critical"
        if score >= 12:
            return "high"
        if score >= 6:
            return "medium"
        return "low"


def monte_carlo_simulation(scenarios, iterations=10000):
    """Run Monte Carlo simulation for risk quantification."""
    results = []
    for scenario in scenarios:
        samples = []
        for _ in range(iterations):
            # Simple triangular distribution
            low = scenario.get("low", 0)
            likely = scenario.get("likely", 0)
            high = scenario.get("high", 0)
            u = random.random()
            if u < 0.5:
                val = low + math.sqrt(u * 2) * (likely - low)
            else:
                val = high - math.sqrt((1 - u) * 2) * (high - likely)
            samples.append(val)
        samples.sort()
        results.append({
            "scenario": scenario.get("name", "unknown"),
            "mean": sum(samples) / len(samples),
            "p50": samples[int(iterations * 0.50)],
            "p75": samples[int(iterations * 0.75)],
            "p90": samples[int(iterations * 0.90)],
            "p95": samples[int(iterations * 0.95)],
            "p99": samples[int(iterations * 0.99)],
            "min": samples[0],
            "max": samples[-1],
        })
    return results


def register(subparsers):
    """Register risk subcommands."""
    parser = subparsers.add_parser("risk", help="Risk management commands")
    risk_sub = parser.add_subparsers(dest="risk_command", help="Risk operations")

    # risk add
    add_p = risk_sub.add_parser("add", help="Add a risk to the register")
    add_p.add_argument("--title", required=True, help="Risk title")
    add_p.add_argument("--description", default="", help="Risk description")
    add_p.add_argument("--category", required=True, choices=RISK_CATEGORIES, help="Risk category")
    add_p.add_argument("--likelihood", type=int, required=True, choices=range(1, 6), help="Likelihood 1-5")
    add_p.add_argument("--impact", type=int, required=True, choices=range(1, 6), help="Impact 1-5")
    add_p.add_argument("--owner", required=True, help="Risk owner")
    add_p.add_argument("--treatment", default="", help="Risk treatment plan")

    # risk list
    list_p = risk_sub.add_parser("list", help="List risks")
    list_p.add_argument("--category", choices=RISK_CATEGORIES, help="Filter by category")
    list_p.add_argument("--status", choices=RISK_STATUSES, help="Filter by status")
    list_p.add_argument("--level", choices=RISK_LEVELS, help="Filter by risk level")
    list_p.add_argument("--json", action="store_true", help="Output as JSON")

    # risk get
    get_p = risk_sub.add_parser("get", help="Get risk details")
    get_p.add_argument("id", help="Risk ID")
    get_p.add_argument("--json", action="store_true", help="Output as JSON")

    # risk update
    update_p = risk_sub.add_parser("update", help="Update risk status")
    update_p.add_argument("id", help="Risk ID")
    update_p.add_argument("--status", required=True, choices=RISK_STATUSES, help="New status")
    update_p.add_argument("--treatment", help="Treatment plan")

    # risk delete
    delete_p = risk_sub.add_parser("delete", help="Delete a risk")
    delete_p.add_argument("id", help="Risk ID")

    # risk stats
    stats_p = risk_sub.add_parser("stats", help="Show risk statistics")
    stats_p.add_argument("--json", action="store_true", help="Output as JSON")

    # risk heatmap
    heatmap_p = risk_sub.add_parser("heatmap", help="Generate risk heatmap")
    heatmap_p.add_argument("--json", action="store_true", help="Output as JSON")

    # risk simulate (Monte Carlo)
    sim_p = risk_sub.add_parser("simulate", help="Run Monte Carlo risk simulation")
    sim_p.add_argument("--scenarios", required=True, help="JSON file with scenarios")
    sim_p.add_argument("--iterations", type=int, default=10000, help="Simulation iterations")
    sim_p.add_argument("--json", action="store_true", help="Output as JSON")


def handle(args, config: Config):
    """Handle risk commands."""
    register = RiskRegister()
    cmd = args.risk_command

    if cmd == "add":
        risk = register.add(
            title=args.title, description=args.description,
            category=args.category, likelihood=args.likelihood,
            impact=args.impact, owner=args.owner, treatment=args.treatment,
        )
        print_success(f"Risk added: {risk['id']}")
        print_json(risk)
        return 0

    elif cmd == "list":
        risks = register.list(category=args.category, status=args.status, level=args.level)
        if args.json:
            print_json(risks)
        else:
            if not risks:
                print_info("No risks found.")
            else:
                rows = [[r["id"][:8], r["title"][:30], r["category"], r["risk_level"], str(r["risk_score"]), r["status"]] for r in risks]
                print_table(["ID", "Title", "Category", "Level", "Score", "Status"], rows)
        return 0

    elif cmd == "get":
        risk = register.get(args.id)
        if not risk:
            print_error(f"Risk not found: {args.id}")
            return 1
        print_json(risk)
        return 0

    elif cmd == "update":
        risk = register.update_status(args.id, args.status, args.treatment or "")
        if not risk:
            print_error(f"Risk not found: {args.id}")
            return 1
        print_success(f"Risk {args.id} updated to {args.status}")
        print_json(risk)
        return 0

    elif cmd == "delete":
        if register.delete(args.id):
            print_success(f"Risk deleted: {args.id}")
            return 0
        print_error(f"Risk not found: {args.id}")
        return 1

    elif cmd == "stats":
        stats = register.stats()
        if args.json:
            print_json(stats)
        else:
            print_info("Risk Statistics")
            print(f"  Total risks: {stats['total_risks']}")
            print(f"  Open critical: {stats['open_critical']}")
            print("\n  By Level:")
            for level, count in stats["by_level"].items():
                print(f"    {level}: {count}")
            print("\n  By Status:")
            for status, count in stats["by_status"].items():
                print(f"    {status}: {count}")
        return 0

    elif cmd == "heatmap":
        risks = register.list()
        categories = RISK_CATEGORIES
        heatmap = []
        for cat in categories:
            cat_risks = [r for r in risks if r["category"] == cat]
            avg_likelihood = sum(r["likelihood"] for r in cat_risks) / len(cat_risks) if cat_risks else 0
            avg_impact = sum(r["impact"] for r in cat_risks) / len(cat_risks) if cat_risks else 0
            score = avg_likelihood * avg_impact
            level = "critical" if score >= 20 else "high" if score >= 12 else "medium" if score >= 6 else "low"
            heatmap.append({
                "category": cat,
                "likelihood": round(avg_likelihood, 1),
                "impact": round(avg_impact, 1),
                "score": round(score, 1),
                "level": level,
                "count": len(cat_risks),
            })
        if args.json:
            print_json(heatmap)
        else:
            rows = [[h["category"], str(h["likelihood"]), str(h["impact"]), str(h["score"]), h["level"], str(h["count"])] for h in heatmap]
            print_table(["Category", "Likelihood", "Impact", "Score", "Level", "Count"], rows)
        return 0

    elif cmd == "simulate":
        try:
            with open(args.scenarios) as f:
                scenarios = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print_error(f"Failed to load scenarios: {e}")
            return 1
        results = monte_carlo_simulation(scenarios, iterations=args.iterations)
        if args.json:
            print_json(results)
        else:
            for r in results:
                print_info(f"Scenario: {r['scenario']}")
                print(f"  Mean: {r['mean']:,.0f}")
                print(f"  P50: {r['p50']:,.0f}  P90: {r['p90']:,.0f}  P99: {r['p99']:,.0f}")
                print(f"  Range: {r['min']:,.0f} — {r['max']:,.0f}")
        return 0

    else:
        print_error("No risk subcommand specified. Use: grc risk <add|list|get|update|delete|stats|heatmap|simulate>")
        return 1
