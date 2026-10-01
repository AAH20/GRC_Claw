"""Agent governance commands for GRC_Claw CLI."""
import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from grc_claw_cli.utils.output import print_json, print_table, print_success, print_error, print_warning, print_info
from grc_claw_cli.utils.config import Config


AI_RISK_CLASSES = ["unacceptable", "high", "limited", "minimal"]
AI_SYSTEM_STATUSES = ["registered", "assessed", "approved", "deployed", "retired"]
AGENT_TYPES = ["human", "agent", "service", "mcp_tool", "browser_agent", "cloud_connector", "soar_playbook", "remediation_bot", "marketplace_pack"]
SANDBOX_POLICIES = ["none", "docker", "microvm", "enclave", "denied"]
APPROVAL_THRESHOLDS = ["none", "human", "dual_control", "board", "government_buyer"]
DATA_BOUNDARIES = ["public", "tenant-confidential", "cui", "phi", "pci", "gdpr", "sovereign", "airgapped"]
ACTION_TIERS = ["read", "write", "destructive", "provision", "decommission"]


class AgentGovernanceStore:
    """Store for AI system registration, agent firewall decisions, and governance data."""

    def __init__(self):
        self.config = Config()
        self.systems = []
        self.agents = []
        self.firewall_receipts = []
        self._load()

    def _load(self):
        path = self.config.CONFIG_DIR / "agent_governance.json"
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                    self.systems = data.get("systems", [])
                    self.agents = data.get("agents", [])
                    self.firewall_receipts = data.get("firewall_receipts", [])
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        self.config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        path = self.config.CONFIG_DIR / "agent_governance.json"
        with open(path, "w") as f:
            json.dump({"systems": self.systems, "agents": self.agents, "firewall_receipts": self.firewall_receipts}, f, indent=2, default=str)

    # AI Systems
    def register_system(self, name, description, owner, department, use_case, risk_class, models=None):
        system = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "owner": owner,
            "department": department,
            "use_case": use_case,
            "risk_class": risk_class,
            "status": "registered",
            "models": models or [],
            "registration_date": datetime.now(timezone.utc).isoformat(),
            "last_assessment": None,
            "next_assessment": None,
        }
        self.systems.append(system)
        self._save()
        return system

    def get_system(self, system_id):
        return next((s for s in self.systems if s["id"] == system_id), None)

    def list_systems(self, risk_class=None, status=None, department=None):
        result = self.systems
        if risk_class:
            result = [s for s in result if s["risk_class"] == risk_class]
        if status:
            result = [s for s in result if s["status"] == status]
        if department:
            result = [s for s in result if s["department"] == department]
        return result

    def update_system(self, system_id, **updates):
        system = self.get_system(system_id)
        if not system:
            return None
        system.update(updates)
        self._save()
        return system

    def delete_system(self, system_id):
        system = self.get_system(system_id)
        if not system:
            return False
        self.systems = [s for s in self.systems if s["id"] != system_id]
        self._save()
        return True

    # Agents
    def register_agent(self, name, agent_type, trust_score=50, tenant_id=None, org_slug=None, role=None, did=None):
        agent = {
            "id": str(uuid.uuid4()),
            "name": name,
            "type": agent_type,
            "trust_score": trust_score,
            "tenant_id": tenant_id,
            "org_slug": org_slug,
            "role": role,
            "did": did,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        self.agents.append(agent)
        self._save()
        return agent

    def get_agent(self, agent_id):
        return next((a for a in self.agents if a["id"] == agent_id), None)

    def list_agents(self, agent_type=None):
        if agent_type:
            return [a for a in self.agents if a["type"] == agent_type]
        return self.agents

    def update_trust_score(self, agent_id, score):
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        agent["trust_score"] = max(0, min(100, score))
        self._save()
        return agent

    # Firewall
    def evaluate_firewall(self, actor_id, actor_type, tool_name, tier, context):
        """Evaluate a policy firewall decision."""
        import hashlib
        decision = {
            "allowed": True,
            "reason": "approved",
            "sandbox": "none",
            "requires_approval": False,
            "approval_threshold": context.get("approval_threshold", "none"),
            "blast_radius_score": 0,
            "control_impact": context.get("control_impact_ids", []),
            "replay_detected": False,
            "canary_triggered": False,
            "sod_violation": False,
            "anomalies": [],
        }

        # Tier-based authorization
        boundary = context.get("data_boundary", "public")
        tier_levels = {"read": 0, "write": 1, "destructive": 2, "provision": 3, "decommission": 4}
        max_tier = {"airgapped": "read", "sovereign": "read", "cui": "write", "phi": "write"}.get(boundary, "destructive")
        if tier_levels.get(tier, 0) > tier_levels.get(max_tier, 4):
            decision["allowed"] = False
            decision["reason"] = f"tier_{tier}_not_authorized"
            decision["sandbox"] = "denied"

        # Blast radius
        blast = 0
        if tier == "destructive":
            blast += 5
        elif tier == "write":
            blast += 2
        if len(context.get("control_impact_ids", [])) > 3:
            blast += 3
        if boundary in ("cui", "phi"):
            blast += 2
        if boundary in ("sovereign", "airgapped"):
            blast += 4
        decision["blast_radius_score"] = blast
        if blast > 10:
            decision["allowed"] = False
            decision["reason"] = "blast_radius_exceeded"

        # Approval
        threshold = context.get("approval_threshold", "none")
        if threshold == "human" and tier in ("destructive", "provision"):
            decision["requires_approval"] = True
        elif threshold == "dual_control" and tier != "read":
            decision["requires_approval"] = True
        elif threshold in ("board", "government_buyer"):
            decision["requires_approval"] = True

        # Sandbox
        if decision["allowed"]:
            if tier == "destructive":
                decision["sandbox"] = "docker"
            elif tier == "provision":
                decision["sandbox"] = context.get("sandbox_policy", "docker")

        receipt = {
            "version": "v1",
            "receipt_id": f"fw_receipt:{hashlib.sha256(f'{actor_id}{tool_name}{datetime.now(timezone.utc).isoformat()}'.encode()).hexdigest()[:16]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": {"id": actor_id, "type": actor_type},
            "request": {"tool_name": tool_name, "tier": tier},
            "context": context,
            "decision": decision,
            "receipt_hash": hashlib.sha256(json.dumps(decision, default=str).encode()).hexdigest(),
        }
        self.firewall_receipts.append(receipt)
        self._save()
        return receipt

    def list_firewall_receipts(self, actor_id=None):
        if actor_id:
            return [r for r in self.firewall_receipts if r["actor"]["id"] == actor_id]
        return self.firewall_receipts

    def stats(self):
        by_risk = {r: 0 for r in AI_RISK_CLASSES}
        by_status = {s: 0 for s in AI_SYSTEM_STATUSES}
        for s in self.systems:
            by_risk[s["risk_class"]] = by_risk.get(s["risk_class"], 0) + 1
            by_status[s["status"]] = by_status.get(s["status"], 0) + 1
        return {
            "total_systems": len(self.systems),
            "total_agents": len(self.agents),
            "total_firewall_receipts": len(self.firewall_receipts),
            "systems_by_risk_class": by_risk,
            "systems_by_status": by_status,
        }


def register(subparsers):
    """Register agent governance subcommands."""
    parser = subparsers.add_parser("agent", help="Agent governance commands")
    ag_sub = parser.add_subparsers(dest="agent_command", help="Agent governance operations")

    # agent system register
    sys_p = ag_sub.add_parser("system-register", help="Register an AI system")
    sys_p.add_argument("--name", required=True, help="System name")
    sys_p.add_argument("--description", default="", help="System description")
    sys_p.add_argument("--owner", required=True, help="System owner")
    sys_p.add_argument("--department", required=True, help="Department")
    sys_p.add_argument("--use-case", required=True, help="Use case")
    sys_p.add_argument("--risk-class", required=True, choices=AI_RISK_CLASSES, help="Risk classification")

    # agent system list
    syslist_p = ag_sub.add_parser("system-list", help="List AI systems")
    syslist_p.add_argument("--risk-class", choices=AI_RISK_CLASSES, help="Filter by risk class")
    syslist_p.add_argument("--status", choices=AI_SYSTEM_STATUSES, help="Filter by status")
    syslist_p.add_argument("--json", action="store_true", help="Output as JSON")

    # agent system get
    sysget_p = ag_sub.add_parser("system-get", help="Get AI system details")
    sysget_p.add_argument("id", help="System ID")
    sysget_p.add_argument("--json", action="store_true", help="Output as JSON")

    # agent system update
    sysupd_p = ag_sub.add_parser("system-update", help="Update AI system")
    sysupd_p.add_argument("id", help="System ID")
    sysupd_p.add_argument("--status", choices=AI_SYSTEM_STATUSES, help="New status")
    sysupd_p.add_argument("--risk-class", choices=AI_RISK_CLASSES, help="New risk class")

    # agent system delete
    sysdel_p = ag_sub.add_parser("system-delete", help="Delete AI system")
    sysdel_p.add_argument("id", help="System ID")

    # agent register
    reg_p = ag_sub.add_parser("register", help="Register an agent")
    reg_p.add_argument("--name", required=True, help="Agent name")
    reg_p.add_argument("--type", required=True, choices=AGENT_TYPES, help="Agent type")
    reg_p.add_argument("--trust-score", type=int, default=50, help="Initial trust score 0-100")
    reg_p.add_argument("--tenant-id", type=int, help="Tenant ID")
    reg_p.add_argument("--org-slug", help="Organization slug")
    reg_p.add_argument("--role", help="Agent role")
    reg_p.add_argument("--did", help="Decentralized identifier")

    # agent list
    alist_p = ag_sub.add_parser("list", help="List agents")
    alist_p.add_argument("--type", choices=AGENT_TYPES, help="Filter by type")
    alist_p.add_argument("--json", action="store_true", help="Output as JSON")

    # agent trust
    trust_p = ag_sub.add_parser("trust", help="Update agent trust score")
    trust_p.add_argument("id", help="Agent ID")
    trust_p.add_argument("--score", type=int, required=True, help="New trust score 0-100")

    # agent firewall
    fw_p = ag_sub.add_parser("firewall", help="Evaluate firewall decision")
    fw_p.add_argument("--actor-id", required=True, help="Actor ID")
    fw_p.add_argument("--actor-type", required=True, choices=AGENT_TYPES, help="Actor type")
    fw_p.add_argument("--tool", required=True, help="Tool name")
    fw_p.add_argument("--tier", required=True, choices=ACTION_TIERS, help="Action tier")
    fw_p.add_argument("--data-boundary", default="public", choices=DATA_BOUNDARIES, help="Data boundary")
    fw_p.add_argument("--sandbox", default="none", choices=SANDBOX_POLICIES, help="Sandbox policy")
    fw_p.add_argument("--approval", default="none", choices=APPROVAL_THRESHOLDS, help="Approval threshold")
    fw_p.add_argument("--json", action="store_true", help="Output as JSON")

    # agent stats
    stats_p = ag_sub.add_parser("stats", help="Show agent governance statistics")
    stats_p.add_argument("--json", action="store_true", help="Output as JSON")


def handle(args, config: Config):
    """Handle agent governance commands."""
    store = AgentGovernanceStore()
    cmd = args.agent_command

    if cmd == "system-register":
        system = store.register_system(
            name=args.name, description=args.description,
            owner=args.owner, department=args.department,
            use_case=args.use_case, risk_class=args.risk_class,
        )
        print_success(f"AI system registered: {system['id']}")
        print_json(system)
        return 0

    elif cmd == "system-list":
        systems = store.list_systems(risk_class=args.risk_class, status=args.status)
        if args.json:
            print_json(systems)
        else:
            if not systems:
                print_info("No AI systems found.")
            else:
                rows = [[s["id"][:8], s["name"][:25], s["risk_class"], s["status"], s["department"]] for s in systems]
                print_table(["ID", "Name", "Risk", "Status", "Dept"], rows)
        return 0

    elif cmd == "system-get":
        system = store.get_system(args.id)
        if not system:
            print_error(f"System not found: {args.id}")
            return 1
        print_json(system)
        return 0

    elif cmd == "system-update":
        updates = {}
        if args.status:
            updates["status"] = args.status
        if args.risk_class:
            updates["risk_class"] = args.risk_class
        system = store.update_system(args.id, **updates)
        if not system:
            print_error(f"System not found: {args.id}")
            return 1
        print_success(f"System updated: {args.id}")
        print_json(system)
        return 0

    elif cmd == "system-delete":
        if store.delete_system(args.id):
            print_success(f"System deleted: {args.id}")
            return 0
        print_error(f"System not found: {args.id}")
        return 1

    elif cmd == "register":
        agent = store.register_agent(
            name=args.name, agent_type=args.type,
            trust_score=args.trust_score, tenant_id=args.tenant_id,
            org_slug=args.org_slug, role=args.role, did=args.did,
        )
        print_success(f"Agent registered: {agent['id']}")
        print_json(agent)
        return 0

    elif cmd == "list":
        agents = store.list_agents(agent_type=args.type)
        if args.json:
            print_json(agents)
        else:
            if not agents:
                print_info("No agents found.")
            else:
                rows = [[a["id"][:8], a["name"][:25], a["type"], str(a["trust_score"])] for a in agents]
                print_table(["ID", "Name", "Type", "Trust"], rows)
        return 0

    elif cmd == "trust":
        agent = store.update_trust_score(args.id, args.score)
        if not agent:
            print_error(f"Agent not found: {args.id}")
            return 1
        print_success(f"Trust score updated: {agent['trust_score']}")
        print_json(agent)
        return 0

    elif cmd == "firewall":
        context = {
            "data_boundary": args.data_boundary,
            "sandbox_policy": args.sandbox,
            "approval_threshold": args.approval,
            "control_impact_ids": [],
        }
        receipt = store.evaluate_firewall(
            actor_id=args.actor_id, actor_type=args.actor_type,
            tool_name=args.tool, tier=args.tier, context=context,
        )
        if args.json:
            print_json(receipt)
        else:
            d = receipt["decision"]
            status = "ALLOWED" if d["allowed"] else "DENIED"
            print_info(f"Firewall Decision: {status}")
            print(f"  Reason: {d['reason']}")
            print(f"  Sandbox: {d['sandbox']}")
            print(f"  Requires approval: {d['requires_approval']}")
            print(f"  Blast radius: {d['blast_radius_score']}")
        return 0

    elif cmd == "stats":
        stats = store.stats()
        if args.json:
            print_json(stats)
        else:
            print_info("Agent Governance Statistics")
            print(f"  AI Systems: {stats['total_systems']}")
            print(f"  Agents: {stats['total_agents']}")
            print(f"  Firewall receipts: {stats['total_firewall_receipts']}")
            print("\n  Systems by Risk Class:")
            for rc, count in stats["systems_by_risk_class"].items():
                print(f"    {rc}: {count}")
            print("\n  Systems by Status:")
            for st, count in stats["systems_by_status"].items():
                print(f"    {st}: {count}")
        return 0

    else:
        print_error("No agent subcommand specified. Use: grc agent <system-register|system-list|system-get|system-update|system-delete|register|list|trust|firewall|stats>")
        return 1
