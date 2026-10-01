"""Policy management commands for GRC_Claw CLI."""
import argparse
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from grc_claw_cli.utils.output import print_json, print_table, print_success, print_error, print_warning, print_info
from grc_claw_cli.utils.config import Config


POLICY_CATEGORIES = ["security", "privacy", "compliance", "operational", "hr", "financial"]
POLICY_STATUSES = ["draft", "under_review", "approved", "published", "archived"]

POLICY_TEMPLATES = [
    {"id": "sec-001", "name": "Access Control Policy", "category": "security", "framework": "ISO 27001",
     "content": "All access to systems must be authenticated and authorized per least-privilege principles."},
    {"id": "sec-002", "name": "Data Classification Policy", "category": "security", "framework": "ISO 27001",
     "content": "Data must be classified as Public, Internal, Confidential, or Restricted."},
    {"id": "sec-003", "name": "Incident Response Policy", "category": "security", "framework": "SOC 2",
     "content": "Security incidents must be reported within 1 hour and investigated per IR plan."},
    {"id": "priv-001", "name": "Data Retention Policy", "category": "privacy", "framework": "GDPR",
     "content": "Personal data shall not be retained longer than necessary for the specified purpose."},
    {"id": "priv-002", "name": "Privacy Impact Assessment", "category": "privacy", "framework": "GDPR",
     "content": "PIA must be conducted for all new processing activities involving personal data."},
    {"id": "comp-001", "name": "Regulatory Compliance Policy", "category": "compliance", "framework": "SOC 2",
     "content": "The organization shall maintain compliance with all applicable regulatory requirements."},
    {"id": "ops-001", "name": "Business Continuity Policy", "category": "operational", "framework": "ISO 27001",
     "content": "Business continuity plans must be tested annually and updated after significant changes."},
    {"id": "hr-001", "name": "Acceptable Use Policy", "category": "hr", "framework": "ISO 27001",
     "content": "IT resources must be used in accordance with organizational policies and applicable laws."},
    {"id": "fin-001", "name": "Financial Controls Policy", "category": "financial", "framework": "SOC 2",
     "content": "Financial transactions require dual authorization above defined thresholds."},
]


class PolicyStore:
    """In-memory policy store (persists to ~/.grc_claw/policies.json)."""

    def __init__(self):
        self.config = Config()
        self.policies = []
        self._load()

    def _load(self):
        path = self.config.CONFIG_DIR / "policies.json"
        if path.exists():
            try:
                with open(path) as f:
                    self.policies = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.policies = []

    def _save(self):
        self.config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        path = self.config.CONFIG_DIR / "policies.json"
        with open(path, "w") as f:
            json.dump(self.policies, f, indent=2, default=str)

    def create(self, title, category, owner, approver, content, framework, template_id=None):
        policy = {
            "id": str(uuid.uuid4()),
            "title": title,
            "category": category,
            "version": 1,
            "status": "draft",
            "owner": owner,
            "approver": approver,
            "content": content,
            "framework": framework,
            "effective_date": "",
            "review_date": "",
            "change_log": [],
            "attestations": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.policies.append(policy)
        self._save()
        return policy

    def get(self, policy_id):
        return next((p for p in self.policies if p["id"] == policy_id), None)

    def list(self, category=None, status=None):
        result = self.policies
        if category:
            result = [p for p in result if p["category"] == category]
        if status:
            result = [p for p in result if p["status"] == status]
        return result

    def transition(self, policy_id, new_status):
        policy = self.get(policy_id)
        if not policy:
            return None
        if new_status == "published":
            policy["effective_date"] = datetime.now(timezone.utc).isoformat()
            policy["review_date"] = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        policy["status"] = new_status
        policy["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        return policy

    def increment_version(self, policy_id, changed_by, summary):
        policy = self.get(policy_id)
        if not policy:
            return None
        policy["change_log"].append({
            "version": policy["version"],
            "changed_by": changed_by,
            "changed_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
        })
        policy["version"] += 1
        policy["status"] = "draft"
        policy["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        return policy

    def add_attestation(self, policy_id, employee_id, employee_name):
        policy = self.get(policy_id)
        if not policy:
            return None
        attestation = {
            "id": str(uuid.uuid4()),
            "employee_id": employee_id,
            "employee_name": employee_name,
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
            "attested_version": policy["version"],
        }
        policy["attestations"].append(attestation)
        self._save()
        return attestation

    def delete(self, policy_id):
        policy = self.get(policy_id)
        if not policy:
            return False
        self.policies = [p for p in self.policies if p["id"] != policy_id]
        self._save()
        return True

    def stats(self):
        by_status = {s: 0 for s in POLICY_STATUSES}
        by_category = {c: 0 for c in POLICY_CATEGORIES}
        for p in self.policies:
            by_status[p["status"]] = by_status.get(p["status"], 0) + 1
            by_category[p["category"]] = by_category.get(p["category"], 0) + 1
        upcoming = [p for p in self.policies if p["status"] == "published" and p.get("review_date")
                    and datetime.fromisoformat(p["review_date"]) < datetime.now(timezone.utc) + timedelta(days=30)]
        return {
            "total_policies": len(self.policies),
            "by_status": by_status,
            "by_category": by_category,
            "upcoming_reviews": len(upcoming),
        }


def register(subparsers):
    """Register policy subcommands."""
    parser = subparsers.add_parser("policy", help="Policy management commands")
    policy_sub = parser.add_subparsers(dest="policy_command", help="Policy operations")

    # policy create
    create_p = policy_sub.add_parser("create", help="Create a new policy")
    create_p.add_argument("--title", required=True, help="Policy title")
    create_p.add_argument("--category", required=True, choices=POLICY_CATEGORIES, help="Policy category")
    create_p.add_argument("--owner", required=True, help="Policy owner")
    create_p.add_argument("--approver", required=True, help="Policy approver")
    create_p.add_argument("--content", required=True, help="Policy content/body")
    create_p.add_argument("--framework", default="ISO 27001", help="Related framework")
    create_p.add_argument("--template", help="Create from template ID")

    # policy list
    list_p = policy_sub.add_parser("list", help="List policies")
    list_p.add_argument("--category", choices=POLICY_CATEGORIES, help="Filter by category")
    list_p.add_argument("--status", choices=POLICY_STATUSES, help="Filter by status")
    list_p.add_argument("--json", action="store_true", help="Output as JSON")

    # policy get
    get_p = policy_sub.add_parser("get", help="Get policy details")
    get_p.add_argument("id", help="Policy ID")
    get_p.add_argument("--json", action="store_true", help="Output as JSON")

    # policy transition
    trans_p = policy_sub.add_parser("transition", help="Transition policy status")
    trans_p.add_argument("id", help="Policy ID")
    trans_p.add_argument("status", choices=POLICY_STATUSES, help="New status")

    # policy update
    update_p = policy_sub.add_parser("update", help="Update policy (creates new version)")
    update_p.add_argument("id", help="Policy ID")
    update_p.add_argument("--content", required=True, help="Updated content")
    update_p.add_argument("--changed-by", required=True, help="Who made the change")
    update_p.add_argument("--summary", default="Policy update", help="Change summary")

    # policy attest
    attest_p = policy_sub.add_parser("attest", help="Add attestation to policy")
    attest_p.add_argument("id", help="Policy ID")
    attest_p.add_argument("--employee-id", required=True, help="Employee ID")
    attest_p.add_argument("--employee-name", required=True, help="Employee name")

    # policy delete
    delete_p = policy_sub.add_parser("delete", help="Delete a policy")
    delete_p.add_argument("id", help="Policy ID")

    # policy stats
    stats_p = policy_sub.add_parser("stats", help="Show policy statistics")
    stats_p.add_argument("--json", action="store_true", help="Output as JSON")

    # policy templates
    templates_p = policy_sub.add_parser("templates", help="List policy templates")
    templates_p.add_argument("--category", choices=POLICY_CATEGORIES, help="Filter by category")
    templates_p.add_argument("--json", action="store_true", help="Output as JSON")


def handle(args, config: Config):
    """Handle policy commands."""
    store = PolicyStore()
    cmd = args.policy_command

    if cmd == "create":
        if args.template:
            template = next((t for t in POLICY_TEMPLATES if t["id"] == args.template), None)
            if not template:
                print_error(f"Template not found: {args.template}")
                return 1
            policy = store.create(
                title=template["name"], category=template["category"],
                owner=args.owner, approver=args.approver,
                content=template["content"], framework=template["framework"],
            )
        else:
            policy = store.create(
                title=args.title, category=args.category,
                owner=args.owner, approver=args.approver,
                content=args.content, framework=args.framework,
            )
        print_success(f"Policy created: {policy['id']}")
        print_json(policy)
        return 0

    elif cmd == "list":
        policies = store.list(category=args.category, status=args.status)
        if args.json:
            print_json(policies)
        else:
            if not policies:
                print_info("No policies found.")
            else:
                rows = [[p["id"][:8], p["title"], p["category"], p["status"], f"v{p['version']}"] for p in policies]
                print_table(["ID", "Title", "Category", "Status", "Ver"], rows)
        return 0

    elif cmd == "get":
        policy = store.get(args.id)
        if not policy:
            print_error(f"Policy not found: {args.id}")
            return 1
        print_json(policy)
        return 0

    elif cmd == "transition":
        policy = store.transition(args.id, args.status)
        if not policy:
            print_error(f"Policy not found: {args.id}")
            return 1
        print_success(f"Policy {args.id} transitioned to {args.status}")
        print_json(policy)
        return 0

    elif cmd == "update":
        policy = store.increment_version(args.id, args.changed_by, args.summary)
        if not policy:
            print_error(f"Policy not found: {args.id}")
            return 1
        policy["content"] = args.content
        store._save()
        print_success(f"Policy updated to version {policy['version']}")
        print_json(policy)
        return 0

    elif cmd == "attest":
        attestation = store.add_attestation(args.id, args.employee_id, args.employee_name)
        if not attestation:
            print_error(f"Policy not found: {args.id}")
            return 1
        print_success(f"Attestation added by {args.employee_name}")
        print_json(attestation)
        return 0

    elif cmd == "delete":
        if store.delete(args.id):
            print_success(f"Policy deleted: {args.id}")
            return 0
        print_error(f"Policy not found: {args.id}")
        return 1

    elif cmd == "stats":
        stats = store.stats()
        if args.json:
            print_json(stats)
        else:
            print_info("Policy Statistics")
            print(f"  Total policies: {stats['total_policies']}")
            print(f"  Upcoming reviews: {stats['upcoming_reviews']}")
            print("\n  By Status:")
            for status, count in stats["by_status"].items():
                print(f"    {status}: {count}")
            print("\n  By Category:")
            for cat, count in stats["by_category"].items():
                print(f"    {cat}: {count}")
        return 0

    elif cmd == "templates":
        templates = POLICY_TEMPLATES
        if args.category:
            templates = [t for t in templates if t["category"] == args.category]
        if args.json:
            print_json(templates)
        else:
            rows = [[t["id"], t["name"], t["category"], t["framework"]] for t in templates]
            print_table(["ID", "Name", "Category", "Framework"], rows)
        return 0

    else:
        print_error("No policy subcommand specified. Use: grc policy <create|list|get|transition|update|attest|delete|stats|templates>")
        return 1
