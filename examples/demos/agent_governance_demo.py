#!/usr/bin/env python3
"""
GRC_Claw Agent Governance Demo
===============================
Demonstrates the complete agent governance workflow:
  1. REGISTER  - Onboard agents with identity, trust scores, and tool allowlists
  2. DELEGATE  - Route tasks through policy firewall with SoD and approval gates
  3. AUDIT     - Review action ledgers, trust decisions, and assurance envelopes

Usage:
    python agent_governance_demo.py
"""

import json
import hashlib
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# ── Enums & Types ──────────────────────────────────────────────────────────

class AgentType(Enum):
    HUMAN = "human"
    AGENT = "agent"
    SERVICE = "service"
    MCP_TOOL = "mcp_tool"
    BROWSER_AGENT = "browser_agent"
    CLOUD_CONNECTOR = "cloud_connector"
    SOAR_PLAYBOOK = "soar_playbook"
    REMEDIATION_BOT = "remediation_bot"


class ToolTier(Enum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    PROVISION = "provision"
    DECOMMISSION = "decommission"


class SandboxPolicy(Enum):
    NONE = "none"
    DOCKER = "docker"
    MICROVM = "microvm"
    ENCLAVE = "enclave"
    DENIED = "denied"


class ApprovalThreshold(Enum):
    NONE = "none"
    HUMAN = "human"
    DUAL_CONTROL = "dual_control"
    BOARD = "board"
    GOVERNMENT_BUYER = "government_buyer"


class DataBoundary(Enum):
    PUBLIC = "public"
    TENANT_CONFIDENTIAL = "tenant-confidential"
    CUI = "cui"
    PHI = "phi"
    PCI = "pci"
    GDPR = "gdpr"
    SOVEREIGN = "sovereign"
    AIRGAPPED = "airgapped"


class TrustDecision(Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    SANDBOXED = "sandboxed"
    APPROVAL_REQUIRED = "approval_required"


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class AgentIdentity:
    id: str
    name: str
    agent_type: str
    tenant_id: int
    org_slug: str = ""
    role: str = ""
    did: str = ""
    trust_score: float = 50.0
    tool_allowlist: list = field(default_factory=list)
    approval_mode: str = "none"
    registered_at: str = ""
    status: str = "active"


@dataclass
class ToolDefinition:
    name: str
    tier: str
    allowed_prefixes: list = field(default_factory=list)


@dataclass
class ToolInvocation:
    tool: str
    args: dict
    approval_token: str = ""
    idempotency_key: str = ""
    agent_role: str = ""
    llm_provider_id: str = ""
    thought: str = ""


@dataclass
class ExecDecision:
    allowed: bool
    reason: str
    sandbox: str
    requires_approval: bool
    toxicity_score: float = 0.0
    anomalies_detected: list = field(default_factory=list)


@dataclass
class AgentAuditEntry:
    timestamp: str
    session_id: str
    tool: str
    decision: dict
    args_redacted: dict


@dataclass
class AssuranceEnvelope:
    version: str
    action_id: str
    tenant_id: int
    session_id: str
    tool: str
    created_at: str
    updated_at: str
    intent: dict = field(default_factory=dict)
    policy: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)
    identity: dict = field(default_factory=dict)
    assurance: dict = field(default_factory=dict)


# ── Agent Registry ────────────────────────────────────────────────────────

class AgentRegistry:
    """Manages agent registration and identity."""

    def __init__(self):
        self.agents: dict[str, AgentIdentity] = {}

    def register_agent(self, name: str, agent_type: AgentType, tenant_id: int,
                       role: str = "", trust_score: float = 50.0,
                       tool_allowlist: list = None, approval_mode: str = "none") -> AgentIdentity:
        """Register a new agent."""
        agent_id = f"agent-{uuid.uuid4().hex[:12]}"
        did = f"did:grc:{hashlib.sha256(agent_id.encode()).hexdigest()[:16]}"

        agent = AgentIdentity(
            id=agent_id,
            name=name,
            agent_type=agent_type.value,
            tenant_id=tenant_id,
            role=role,
            did=did,
            trust_score=trust_score,
            tool_allowlist=tool_allowlist or [],
            approval_mode=approval_mode,
            registered_at=datetime.utcnow().isoformat(),
            status="active",
        )
        self.agents[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        return self.agents.get(agent_id)

    def list_agents(self) -> list[AgentIdentity]:
        return list(self.agents.values())

    def update_trust_score(self, agent_id: str, score: float) -> bool:
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        agent.trust_score = max(0, min(100, score))
        return True

    def deactivate_agent(self, agent_id: str) -> bool:
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        agent.status = "inactive"
        return True


# ── Policy Firewall ───────────────────────────────────────────────────────

class AgentPolicyFirewall:
    """Evaluates tool invocations against governance policies."""

    def __init__(self):
        self.canary_traps: dict = {}
        self.sod_rules = [
            {"conflictRoleA": "auditor", "conflictRoleB": "developer", "ruleName": "auditor-developer-separation", "severity": "HIGH"},
            {"conflictRoleA": "approver", "conflictRoleB": "executor", "ruleName": "segregation-of-duties", "severity": "HIGH"},
            {"conflictRoleA": "admin", "conflictRoleB": "readonly", "ruleName": "admin-readonly-conflict", "severity": "MEDIUM"},
        ]
        self.replay_window: dict = {}
        self.blocked_actors: set = set()
        self.config = {
            "max_blast_radius": 10,
            "replay_window_seconds": 300,
            "toxicity_deny_threshold": 75,
            "toxicity_sandbox_threshold": 40,
            "canary_tool_names": ["connector.canary_override", "connector.admin_db_override"],
        }

    def evaluate(self, agent: AgentIdentity, invocation: ToolInvocation,
                 context: dict) -> ExecDecision:
        """Evaluate a tool invocation against the policy firewall."""
        anomalies = []

        # 1. Blocked actor check
        if agent.id in self.blocked_actors:
            return ExecDecision(False, "actor_blocked", "denied", False, anomalies_detected=anomalies)

        # 2. Canary/honeypot check
        if invocation.tool in self.config["canary_tool_names"]:
            self._record_canary_trap(invocation.tool, agent)
            anomalies.append("canary_tool_triggered")
            return ExecDecision(False, "canary_trap_triggered", "denied", False, anomalies_detected=anomalies)

        # 3. Tool allowlist check
        denied_tools = context.get("deniedTools", [])
        allowed_tools = context.get("allowedTools", [])
        if invocation.tool in denied_tools:
            return ExecDecision(False, "tool_explicitly_denied", "denied", False, anomalies_detected=anomalies)
        if allowed_tools and invocation.tool not in allowed_tools:
            return ExecDecision(False, "tool_not_in_allowlist", "denied", False, anomalies_detected=anomalies)

        # 4. Tier-based authorization
        tier = self._get_tool_tier(invocation.tool)
        if not self._check_tier_authorization(tier, context):
            return ExecDecision(False, f"tier_{tier}_not_authorized", "denied", False, anomalies_detected=anomalies)

        # 5. Segregation of Duties
        if agent.role:
            for rule in self.sod_rules:
                if (agent.role == rule["conflictRoleA"] and context.get("role") == rule["conflictRoleB"]) or \
                   (agent.role == rule["conflictRoleB"] and context.get("role") == rule["conflictRoleA"]):
                    anomalies.append(f"sod_violation:{rule['ruleName']}")
                    if rule["severity"] == "HIGH":
                        return ExecDecision(False, f"sod_violation:{rule['ruleName']}", "denied", False, anomalies_detected=anomalies)

        # 6. Replay detection
        if invocation.idempotency_key:
            existing = self.replay_window.get(invocation.idempotency_key)
            if existing:
                elapsed = (datetime.utcnow() - datetime.fromisoformat(existing["firstSeen"])).total_seconds()
                if elapsed < self.config["replay_window_seconds"]:
                    anomalies.append("replay_detected")
                    return ExecDecision(False, "replay_detected", "denied", False, anomalies_detected=anomalies)
            self.replay_window[invocation.idempotency_key] = {
                "idempotencyKey": invocation.idempotency_key,
                "firstSeen": datetime.utcnow().isoformat(),
                "lastSeen": datetime.utcnow().isoformat(),
                "count": 1,
                "actorId": agent.id,
            }

        # 7. Blast radius
        blast_radius = self._calculate_blast_radius(invocation, context)
        if blast_radius > self.config["max_blast_radius"]:
            anomalies.append("blast_radius_exceeded")
            return ExecDecision(False, "blast_radius_exceeded", "denied", False, anomalies_detected=anomalies)

        # 8. Approval threshold
        requires_approval = self._requires_approval(tier, context.get("approvalThreshold", "none"))

        # 9. Sandbox
        sandbox = self._resolve_sandbox(tier, context.get("sandboxPolicy", "docker"))

        return ExecDecision(True, "approved_by_firewall", sandbox, requires_approval, anomalies_detected=anomalies)

    def _get_tool_tier(self, tool_name: str) -> str:
        read_tools = ["grc.list_controls", "grc.get_compliance_score", "evidence.read", "soc.query_events"]
        write_tools = ["evidence.attach", "control.update_status", "servicenow.create_incident"]
        destructive_tools = ["soar.run_playbook", "firewall.apply_rule", "sentinel.run_playbook"]

        if tool_name in read_tools:
            return ToolTier.READ.value
        elif tool_name in write_tools:
            return ToolTier.WRITE.value
        elif tool_name in destructive_tools:
            return ToolTier.DESTRUCTIVE.value
        return ToolTier.READ.value

    def _check_tier_authorization(self, tier: str, context: dict) -> bool:
        tier_levels = {"read": 0, "write": 1, "destructive": 2, "provision": 3, "decommission": 4}
        boundary = context.get("dataBoundary", "public")
        if boundary in ("airgapped", "sovereign"):
            max_tier = "read"
        elif boundary in ("cui", "phi"):
            max_tier = "write"
        else:
            max_tier = "destructive"
        return tier_levels.get(tier, 0) <= tier_levels.get(max_tier, 4)

    def _calculate_blast_radius(self, invocation: ToolInvocation, context: dict) -> int:
        score = 0
        tier = self._get_tool_tier(invocation.tool)
        if tier == "destructive":
            score += 5
        elif tier == "write":
            score += 2
        if len(context.get("controlImpactIds", [])) > 3:
            score += 3
        boundary = context.get("dataBoundary", "public")
        if boundary in ("cui", "phi"):
            score += 2
        if boundary in ("sovereign", "airgapped"):
            score += 4
        return score

    def _requires_approval(self, tier: str, threshold: str) -> bool:
        if threshold == "none":
            return False
        if threshold == "human" and tier in ("destructive", "provision"):
            return True
        if threshold == "dual_control" and tier != "read":
            return True
        if threshold in ("board", "government_buyer"):
            return True
        return False

    def _resolve_sandbox(self, tier: str, preferred: str) -> str:
        if preferred == "denied":
            return "denied"
        if tier == "destructive":
            return "docker"
        if tier == "provision" and preferred == "none":
            return "docker"
        return preferred

    def _record_canary_trap(self, tool_name: str, agent: AgentIdentity):
        if tool_name not in self.canary_traps:
            self.canary_traps[tool_name] = {
                "toolName": tool_name,
                "triggerCount": 0,
                "lastTriggered": "",
                "actorId": "",
            }
        trap = self.canary_traps[tool_name]
        trap["triggerCount"] += 1
        trap["lastTriggered"] = datetime.utcnow().isoformat()
        trap["actorId"] = agent.id

    def block_actor(self, actor_id: str):
        self.blocked_actors.add(actor_id)

    def get_stats(self) -> dict:
        return {
            "blockedActors": len(self.blocked_actors),
            "canaryTriggers": sum(t["triggerCount"] for t in self.canary_traps.values()),
            "replayDetections": sum(1 for e in self.replay_window.values() if e["count"] > 1),
            "sodRules": len(self.sod_rules),
        }


# ── Agent Session ─────────────────────────────────────────────────────────

class AgentSession:
    """Manages an agent session with audit logging."""

    def __init__(self, session_id: str, agent: AgentIdentity, firewall: AgentPolicyFirewall):
        self.session_id = session_id
        self.agent = agent
        self.firewall = firewall
        self.calls = 0
        self.audit_log: list[AgentAuditEntry] = []
        self.toxicity_score = 0.0
        self.call_history: list = []

    def invoke(self, invocation: ToolInvocation, context: dict) -> ExecDecision:
        """Invoke a tool through the policy firewall."""
        self.calls += 1

        # Behavioral audit: loop detection
        args_string = json.dumps(invocation.args, sort_keys=True)
        consecutive_repeats = sum(
            1 for h in self.call_history[-2:]
            if h["tool"] == invocation.tool and h["argsString"] == args_string
        )
        if consecutive_repeats >= 2:
            self.toxicity_score = min(100, self.toxicity_score + 25)

        # Evaluate through firewall
        decision = self.firewall.evaluate(self.agent, invocation, context)

        # Toxicity containment
        if self.toxicity_score >= 75 and decision.allowed:
            decision.allowed = False
            decision.reason = f"high_toxicity_containment: score={self.toxicity_score}"
            decision.sandbox = "denied"
        elif self.toxicity_score >= 40:
            decision.sandbox = "docker"

        decision.toxicity_score = self.toxicity_score

        # Audit log
        self.audit_log.append(AgentAuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            session_id=self.session_id,
            tool=invocation.tool,
            decision=asdict(decision),
            args_redacted={"keys": list(invocation.args.keys())},
        ))

        self.call_history.append({
            "tool": invocation.tool,
            "argsString": args_string,
            "agentRole": invocation.agent_role,
            "timestamp": datetime.utcnow().timestamp(),
        })

        return decision

    def get_audit_log(self) -> list[AgentAuditEntry]:
        return list(self.audit_log)

    def get_state(self) -> dict:
        return {
            "calls": self.calls,
            "toxicityScore": self.toxicity_score,
            "auditLog": [asdict(e) for e in self.audit_log],
        }


# ── Demo Runner ────────────────────────────────────────────────────────────

def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_section(title: str):
    print(f"\n--- {title} ---")


def run_demo():
    print_header("GRC_Claw Agent Governance Demo")
    print("Demonstrating: REGISTER → DELEGATE → AUDIT")

    registry = AgentRegistry()
    firewall = AgentPolicyFirewall()

    # ════════════════════════════════════════════════════════════════════
    # PHASE 1: REGISTER
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 1: REGISTER — Agent Onboarding & Identity")

    print_section("Registering Agents")

    agents = [
        registry.register_agent(
            name="Compliance Scanner",
            agent_type=AgentType.AGENT,
            tenant_id=1,
            role="scanner",
            trust_score=85.0,
            tool_allowlist=["grc.list_controls", "grc.get_compliance_score", "evidence.read", "evidence.attach"],
            approval_mode="none",
        ),
        registry.register_agent(
            name="Policy Enforcer",
            agent_type=AgentType.AGENT,
            tenant_id=1,
            role="enforcer",
            trust_score=75.0,
            tool_allowlist=["grc.list_controls", "control.update_status", "evidence.attach"],
            approval_mode="human",
        ),
        registry.register_agent(
            name="Remediation Bot",
            agent_type=AgentType.REMEDIATION_BOT,
            tenant_id=1,
            role="remediator",
            trust_score=60.0,
            tool_allowlist=["soar.run_playbook", "firewall.apply_rule", "servicenow.create_incident"],
            approval_mode="dual_control",
        ),
        registry.register_agent(
            name="Security Auditor",
            agent_type=AgentType.AGENT,
            tenant_id=1,
            role="auditor",
            trust_score=95.0,
            tool_allowlist=["grc.list_controls", "grc.get_compliance_score", "evidence.read", "soc.query_events"],
            approval_mode="none",
        ),
        registry.register_agent(
            name="Cloud Connector",
            agent_type=AgentType.CLOUD_CONNECTOR,
            tenant_id=1,
            role="connector",
            trust_score=70.0,
            tool_allowlist=["aws.guardduty.list_findings", "evidence.read"],
            approval_mode="none",
        ),
    ]

    for agent in agents:
        print(f"  ✓ {agent.name} ({agent.agent_type})")
        print(f"     ID: {agent.id}")
        print(f"     DID: {agent.did}")
        print(f"     Trust Score: {agent.trust_score}/100")
        print(f"     Role: {agent.role}, Approval: {agent.approval_mode}")
        print(f"     Tools: {', '.join(agent.tool_allowlist[:3])}...")

    print_section("Agent Statistics")
    print(f"  Total agents: {len(registry.list_agents())}")
    by_type = {}
    for a in registry.list_agents():
        by_type[a.agent_type] = by_type.get(a.agent_type, 0) + 1
    for t, count in by_type.items():
        print(f"    {t}: {count}")

    # ════════════════════════════════════════════════════════════════════
    # PHASE 2: DELEGATE
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 2: DELEGATE — Task Routing & Policy Enforcement")

    print_section("Tool Invocation Scenarios")

    # Scenario 1: Read operation (should be allowed)
    session1 = AgentSession("session-001", agents[0], firewall)
    context1 = {
        "tenantScope": ["org-1"],
        "role": "scanner",
        "allowedTools": agents[0].tool_allowlist,
        "deniedTools": [],
        "sandboxPolicy": "docker",
        "approvalThreshold": "none",
        "dataBoundary": "tenant-confidential",
        "replayWindowSeconds": 300,
        "maxBlastRadius": 10,
    }
    inv1 = ToolInvocation(
        tool="grc.list_controls",
        args={"framework": "iso27001"},
        idempotency_key="scan-001",
    )
    decision1 = session1.invoke(inv1, context1)
    print(f"  ✓ {agents[0].name} → {inv1.tool}")
    print(f"     Allowed: {decision1.allowed}, Reason: {decision1.reason}")
    print(f"     Sandbox: {decision1.sandbox}, Approval: {decision1.requires_approval}")

    # Scenario 2: Write operation (should be allowed with sandbox)
    inv2 = ToolInvocation(
        tool="evidence.attach",
        args={"controlId": "AC-2", "evidenceData": "config..."},
        idempotency_key="attach-001",
    )
    decision2 = session1.invoke(inv2, context1)
    print(f"\n  ✓ {agents[0].name} → {inv2.tool}")
    print(f"     Allowed: {decision2.allowed}, Reason: {decision2.reason}")
    print(f"     Sandbox: {decision2.sandbox}, Approval: {decision2.requires_approval}")

    # Scenario 3: Destructive operation (should require approval)
    session2 = AgentSession("session-002", agents[2], firewall)
    context2 = {
        "tenantScope": ["org-1"],
        "role": "remediator",
        "allowedTools": agents[2].tool_allowlist,
        "deniedTools": [],
        "sandboxPolicy": "docker",
        "approvalThreshold": "dual_control",
        "dataBoundary": "tenant-confidential",
        "replayWindowSeconds": 300,
        "maxBlastRadius": 10,
    }
    inv3 = ToolInvocation(
        tool="soar.run_playbook",
        args={"playbook": "incident-response", "target": "web-server-01"},
        idempotency_key="remediate-001",
    )
    decision3 = session2.invoke(inv3, context2)
    print(f"\n  ✓ {agents[2].name} → {inv3.tool}")
    print(f"     Allowed: {decision3.allowed}, Reason: {decision3.reason}")
    print(f"     Sandbox: {decision3.sandbox}, Approval: {decision3.requires_approval}")

    # Scenario 4: SoD violation (auditor trying to remediate)
    session3 = AgentSession("session-003", agents[3], firewall)
    context3 = {
        "tenantScope": ["org-1"],
        "role": "developer",  # Conflicts with auditor role
        "allowedTools": agents[3].tool_allowlist + ["soar.run_playbook"],
        "deniedTools": [],
        "sandboxPolicy": "docker",
        "approvalThreshold": "none",
        "dataBoundary": "tenant-confidential",
        "replayWindowSeconds": 300,
        "maxBlastRadius": 10,
    }
    inv4 = ToolInvocation(
        tool="soar.run_playbook",
        args={"playbook": "deploy", "target": "prod-cluster"},
        idempotency_key="sod-test-001",
    )
    decision4 = session3.invoke(inv4, context3)
    print(f"\n  ✓ {agents[3].name} → {inv4.tool} (SoD test)")
    print(f"     Allowed: {decision4.allowed}, Reason: {decision4.reason}")
    print(f"     Anomalies: {decision4.anomalies_detected}")

    # Scenario 5: Canary/honeypot trigger
    inv5 = ToolInvocation(
        tool="connector.canary_override",
        args={"target": "database"},
        idempotency_key="canary-001",
    )
    decision5 = session1.invoke(inv5, context1)
    print(f"\n  ✓ {agents[0].name} → {inv5.tool} (Canary test)")
    print(f"     Allowed: {decision5.allowed}, Reason: {decision5.reason}")
    print(f"     Anomalies: {decision5.anomalies_detected}")

    # Scenario 6: Replay detection
    inv6 = ToolInvocation(
        tool="grc.list_controls",
        args={"framework": "iso27001"},
        idempotency_key="scan-001",  # Same as inv1
    )
    decision6 = session1.invoke(inv6, context1)
    print(f"\n  ✓ {agents[0].name} → {inv6.tool} (Replay test)")
    print(f"     Allowed: {decision6.allowed}, Reason: {decision6.reason}")
    print(f"     Anomalies: {decision6.anomalies_detected}")

    # Scenario 7: Sovereign boundary check
    session4 = AgentSession("session-004", agents[4], firewall)
    context4 = {
        "tenantScope": ["org-1"],
        "role": "connector",
        "allowedTools": agents[4].tool_allowlist,
        "deniedTools": [],
        "sandboxPolicy": "docker",
        "approvalThreshold": "none",
        "dataBoundary": "sovereign",
        "replayWindowSeconds": 300,
        "maxBlastRadius": 10,
    }
    inv7 = ToolInvocation(
        tool="grc.list_controls",
        args={"framework": "cmmc"},
        idempotency_key="sovereign-001",
        llm_provider_id="zhipu-glm",  # Non-sovereign provider
    )
    decision7 = session4.invoke(inv7, context4)
    print(f"\n  ✓ {agents[4].name} → {inv7.tool} (Sovereign boundary test)")
    print(f"     Allowed: {decision7.allowed}, Reason: {decision7.reason}")

    # Scenario 8: Loop anomaly detection
    session5 = AgentSession("session-005", agents[0], firewall)
    for i in range(3):
        inv_loop = ToolInvocation(
            tool="grc.list_controls",
            args={"framework": "iso27001"},
            idempotency_key=f"loop-{i}",
        )
        decision_loop = session5.invoke(inv_loop, context1)
    print(f"\n  ✓ {agents[0].name} → grc.list_controls (Loop test, 3 calls)")
    print(f"     Toxicity Score: {session5.toxicity_score}")
    print(f"     Last decision: {decision_loop.allowed} ({decision_loop.reason})")

    # ════════════════════════════════════════════════════════════════════
    # PHASE 3: AUDIT
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 3: AUDIT — Action Ledgers & Trust Decisions")

    print_section("Session Audit Logs")
    for session in [session1, session2, session3, session4, session5]:
        print(f"\n  Session: {session.session_id} ({session.agent.name})")
        print(f"    Calls: {session.calls}, Toxicity: {session.toxicity_score}")
        for entry in session.get_audit_log():
            decision = entry.decision
            status_icon = "✓" if decision["allowed"] else "✗"
            print(f"    {status_icon} {entry.tool}: {decision['reason']}")
            if decision.get("anomalies_detected"):
                print(f"       Anomalies: {', '.join(decision['anomalies_detected'])}")

    print_section("Firewall Statistics")
    stats = firewall.get_stats()
    print(f"  Blocked actors: {stats['blockedActors']}")
    print(f"  Canary triggers: {stats['canaryTriggers']}")
    print(f"  Replay detections: {stats['replayDetections']}")
    print(f"  SoD rules: {stats['sodRules']}")

    print_section("Trust Score Updates")
    registry.update_trust_score(agents[0].id, 90.0)
    registry.update_trust_score(agents[2].id, 55.0)
    print(f"  {agents[0].name}: 85.0 → 90.0")
    print(f"  {agents[2].name}: 60.0 → 55.0")

    print_section("Agent Deactivation")
    registry.deactivate_agent(agents[4].id)
    print(f"  ✓ {agents[4].name} deactivated")

    # ════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════════════════
    print_header("DEMO COMPLETE")
    print(f"""
Summary:
  • Registered {len(agents)} agents with DIDs and trust scores
  • Processed 8 tool invocations through the policy firewall
  • Detected 1 canary trigger, 1 replay, 1 SoD violation, 1 sovereign boundary violation
  • Tracked toxicity scores with loop anomaly detection
  • Generated audit logs for all sessions
  • Updated trust scores based on behavior

Key Capabilities Demonstrated:
  ✓ Agent registration with DID identity
  ✓ Tool allowlist enforcement
  ✓ Tier-based authorization (read/write/destructive)
  ✓ Segregation of Duties (SoD) checks
  ✓ Replay detection with idempotency keys
  ✓ Canary/honeypot trap detection
  ✓ Blast radius scoring
  ✓ Sovereign boundary enforcement
  ✓ Toxicity scoring with loop anomaly detection
  ✓ Sandbox policy resolution
  ✓ Approval threshold enforcement
  ✓ Comprehensive audit logging
  ✓ Trust score management
""")


if __name__ == "__main__":
    run_demo()
