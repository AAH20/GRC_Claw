#!/usr/bin/env python3
"""
GRC_Claw Interactive Tutorial System
=====================================
Interactive, step-by-step tutorials for GRC_Claw onboarding.
Covers 5 tiers, 10 competencies, 14 modules with hands-on exercises.

Usage:
    python training_tutorial_system.py [--tier N] [--module ID] [--list]
"""

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


# ─── Data Models ──────────────────────────────────────────────────────────────

class TutorialStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Difficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class TutorialStep:
    step_id: str
    title: str
    content: str
    exercise: Optional[str] = None
    expected_output: Optional[str] = None
    hints: list[str] = field(default_factory=list)
    validation_command: Optional[str] = None
    completed: bool = False


@dataclass
class Tutorial:
    tutorial_id: str
    title: str
    description: str
    tier: int
    module_id: str
    difficulty: Difficulty
    estimated_minutes: int
    competencies_addressed: list[str]
    prerequisites: list[str]
    steps: list[TutorialStep]
    status: TutorialStatus = TutorialStatus.NOT_STARTED
    current_step: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    score: float = 0.0


@dataclass
class LearnerProfile:
    user_id: str
    name: str
    email: str
    role: str
    tier: int
    department: str
    start_date: str
    completed_tutorials: list[str] = field(default_factory=list)
    tutorial_scores: dict[str, float] = field(default_factory=dict)
    total_learning_minutes: int = 0
    streak_days: int = 0
    last_activity: Optional[str] = None


# ─── Tutorial Content Database ────────────────────────────────────────────────

TUTORIAL_CATALOG: dict[str, dict] = {
    "T001": {
        "title": "GRC_Claw Gateway Fundamentals",
        "description": "Learn to start, configure, and interact with the GRC_Claw gateway daemon",
        "tier": 1,
        "module_id": "M01",
        "difficulty": Difficulty.BEGINNER,
        "estimated_minutes": 30,
        "competencies_addressed": ["C1", "C2"],
        "prerequisites": [],
        "steps": [
            {
                "title": "Understanding the Gateway Architecture",
                "content": "The GRC_Claw gateway is the control plane daemon that binds to 127.0.0.1:18791. It provides WebSocket connectivity, agent routing, and evidence management. The gateway is the single entry point for all GRC_Claw operations.",
                "exercise": "Review the gateway configuration in deploy/systemd/grc-claw-gateway.service",
                "hints": ["Look for the ExecStart line", "Note the default port 18791"],
            },
            {
                "title": "Starting the Gateway",
                "content": "The gateway can be started via systemd, Docker Compose, or directly via npm. It requires a valid configuration file and environment variables for authentication.",
                "exercise": "Start the gateway using: npm run gateway",
                "expected_output": "Gateway listening on 127.0.0.1:18791",
                "validation_command": "curl -s http://127.0.0.1:18791/health",
                "hints": ["Ensure Node.js >= 20 is installed", "Check that port 18791 is not in use"],
            },
            {
                "title": "Connecting via WebSocket",
                "content": "Clients connect to the gateway via WebSocket with a bearer token. The connection protocol uses JSON-RPC 2.0 for method invocation.",
                "exercise": "Open a WebSocket connection to ws://127.0.0.1:18791 and send a connect message with your bearer token",
                "expected_output": "Connection established, session ID returned",
                "hints": ["Use wscat or a simple Node.js script", "The token is in your .env file"],
            },
            {
                "title": "First Agent Tool Call",
                "content": "Once connected, you can invoke agent tools. The gateway routes tool calls to the appropriate agent runtime and returns results.",
                "exercise": "Call the 'control.test' tool with a simple compliance check",
                "expected_output": "Test result with pass/fail status",
                "validation_command": "node -e \"const ws = new WebSocket('ws://127.0.0.1:18791'); /* ... */\"",
                "hints": ["Method name is 'control.test'", "Include idempotency key in params"],
            },
        ],
    },
    "T002": {
        "title": "Evidence Plane & Compliance Frameworks",
        "description": "Master the evidence plane: controls, tests, hashed artifacts, and framework mapping",
        "tier": 1,
        "module_id": "M02",
        "difficulty": Difficulty.BEGINNER,
        "estimated_minutes": 45,
        "competencies_addressed": ["C1", "C3"],
        "prerequisites": ["T001"],
        "steps": [
            {
                "title": "Evidence Plane Architecture",
                "content": "The evidence plane stores compliance controls, test definitions, and hashed artifacts. It is the source of truth for all compliance evidence and supports audit trails.",
                "exercise": "Explore the evidence package structure in packages/evidence/",
                "hints": ["Look at src/controls/", "Check src/tests/ for test definitions"],
            },
            {
                "title": "Creating a Compliance Control",
                "content": "Controls define what needs to be checked. Each control has a unique ID, framework mapping, severity, and test references.",
                "exercise": "Create a new control definition for 'Access Control Review' mapped to ISO 42001 A.8.2",
                "expected_output": "Control JSON with id, framework_ref, severity, and test_refs",
                "hints": ["Use the Control interface from @grc-claw/evidence", "Severity levels: critical, high, medium, low"],
            },
            {
                "title": "Attaching Evidence Artifacts",
                "content": "Evidence artifacts are hashed and stored with tamper-evident seals. Each artifact links to a control and test execution.",
                "exercise": "Attach a sample evidence artifact using the evidence.attach method",
                "expected_output": "Artifact ID with SHA-256 hash and timestamp",
                "validation_command": "node scripts/test-assurance.mjs",
                "hints": ["Artifacts must include content_hash", "Use the EvidenceAttestation interface"],
            },
            {
                "title": "Framework Mapping",
                "content": "GRC_Claw maps controls to multiple compliance frameworks simultaneously (ISO 42001, SOC 2, NIST, etc.) using a unified crosswalk.",
                "exercise": "Map your control to ISO 42001, SOC 2 CC6.1, and NIST AC-2",
                "expected_output": "Crosswalk entry with all three framework references",
                "hints": ["Use the compliance-mapping-spec", "Each framework has its own control ID format"],
            },
        ],
    },
    "T003": {
        "title": "Agent Runtime & Policy Engine",
        "description": "Deep dive into agent runtime, policy enforcement, and the anti-swarm WAF",
        "tier": 2,
        "module_id": "M03",
        "difficulty": Difficulty.INTERMEDIATE,
        "estimated_minutes": 60,
        "competencies_addressed": ["C2", "C4", "C5"],
        "prerequisites": ["T001", "T002"],
        "steps": [
            {
                "title": "Agent Runtime Architecture",
                "content": "The agent runtime executes AI agent tasks under policy supervision. It includes the policy firewall, trust scoring, and action ledger.",
                "exercise": "Review the agent-runtime package structure and identify the main components",
                "hints": ["Check packages/agent-runtime/src/", "Look for policy/, trust/, ledger/ directories"],
            },
            {
                "title": "Policy Firewall Configuration",
                "content": "The policy firewall intercepts all agent actions and enforces allow/deny rules. Policies are defined in YAML and evaluated in real-time.",
                "exercise": "Create a policy that denies all file-write operations outside /tmp/grc-workspace",
                "expected_output": "Policy YAML with deny rule for file.write outside allowed path",
                "validation_command": "npm run demo:agent-policy-denial",
                "hints": ["Use the PolicyRule interface", "Actions are scoped by tool name and parameters"],
            },
            {
                "title": "Trust Scoring",
                "content": "Each agent has a trust score that evolves based on behavior. High-trust agents get more autonomy; low-trust agents require approval.",
                "exercise": "Query the trust score for an agent and interpret the components",
                "expected_output": "Trust score breakdown: identity, behavior, history components",
                "hints": ["Use packages/agent-trust-score", "Scores range 0-100"],
            },
            {
                "title": "Action Ledger Audit",
                "content": "Every agent action is recorded in an immutable action ledger. The ledger supports audit queries and compliance reporting.",
                "exercise": "Query the action ledger for all actions in the last 24 hours",
                "expected_output": "List of actions with timestamps, agent IDs, and outcomes",
                "validation_command": "node scripts/test-action-ledger.mjs",
                "hints": ["Ledger entries are append-only", "Use the query API with time range filter"],
            },
        ],
    },
    "T004": {
        "title": "Compliance Orchestration & Continuous Monitoring",
        "description": "Build automated compliance workflows with the orchestration engine",
        "tier": 2,
        "module_id": "M04",
        "difficulty": Difficulty.INTERMEDIATE,
        "estimated_minutes": 50,
        "competencies_addressed": ["C3", "C6"],
        "prerequisites": ["T002", "T003"],
        "steps": [
            {
                "title": "Orchestration Engine Overview",
                "content": "The compliance orchestrator chains controls, tests, and evidence collection into automated workflows. It supports scheduling, triggers, and conditional logic.",
                "exercise": "Review the orchestrator package and identify the workflow definition format",
                "hints": ["Check packages/compliance-orchestrator/", "Workflows are defined as DAGs"],
            },
            {
                "title": "Creating a Compliance Workflow",
                "content": "A compliance workflow defines a sequence of control tests that run automatically. Each step can have conditions, timeouts, and escalation rules.",
                "exercise": "Create a workflow that runs access control checks daily and escalates failures to the security team",
                "expected_output": "Workflow definition with schedule, steps, and escalation policy",
                "hints": ["Use WorkflowDefinition interface", "Schedules use cron expressions"],
            },
            {
                "title": "Continuous Compliance Monitoring",
                "content": "Continuous compliance runs workflows on a schedule and maintains a real-time compliance posture. Drift detection triggers re-mediation.",
                "exercise": "Enable continuous compliance monitoring and observe the compliance posture dashboard",
                "expected_output": "Real-time compliance score and drift alerts",
                "validation_command": "npm run test:continuous",
                "hints": ["Check packages/continuous-compliance/", "Drift thresholds are configurable"],
            },
        ],
    },
    "T005": {
        "title": "A2Z SOC Integration & SIEM Bridge",
        "description": "Connect GRC_Claw to the A2Z SOC for real-time security event processing",
        "tier": 3,
        "module_id": "M05",
        "difficulty": Difficulty.ADVANCED,
        "estimated_minutes": 75,
        "competencies_addressed": ["C4", "C7"],
        "prerequisites": ["T003", "T004"],
        "steps": [
            {
                "title": "A2Z Connector Architecture",
                "content": "The A2Z connector bridges GRC_Claw with the private A2Z SOC. It pulls security events, pushes compliance alerts, and syncs organizational context.",
                "exercise": "Review the a2z-connector package and understand the event flow",
                "hints": ["Check packages/a2z-connector/", "Events flow: SIEM -> connector -> gateway -> evidence"],
            },
            {
                "title": "Event-to-Control Mapping",
                "content": "Security events from the SIEM are mapped to compliance controls. High/critical events trigger immediate control tests.",
                "exercise": "Map a 'failed login' SIEM event to the access control compliance framework",
                "expected_output": "Event mapping with control ID, severity, and auto-test trigger",
                "hints": ["Use the event_data.compliance_impact field", "Mappings are configurable via YAML"],
            },
            {
                "title": "Compliance Alert Push",
                "content": "When a compliance check fails, alerts are pushed to the A2Z SOC notification system for SOC analyst review.",
                "exercise": "Trigger a compliance failure and verify the alert appears in the SOC",
                "expected_output": "Alert in SOC with control ID, severity, and evidence link",
                "validation_command": "npm run test:byoc",
                "hints": ["Alerts go to compliance_alerts endpoint", "Include evidence references in alert payload"],
            },
        ],
    },
    "T006": {
        "title": "Knowledge Graph & Compliance Intelligence",
        "description": "Build and query the compliance knowledge graph for intelligent reporting",
        "tier": 3,
        "module_id": "M06",
        "difficulty": Difficulty.ADVANCED,
        "estimated_minutes": 60,
        "competencies_addressed": ["C6", "C8"],
        "prerequisites": ["T004"],
        "steps": [
            {
                "title": "Knowledge Graph Schema",
                "content": "The compliance knowledge graph stores entities (controls, frameworks, evidence, agents) and their relationships as a property graph.",
                "exercise": "Review the knowledge graph schema in packages/compliance-knowledge-graph/",
                "hints": ["Entities: Control, Framework, Evidence, Agent, Test", "Relationships: MAPS_TO, TESTS, PRODUCES, DEPENDS_ON"],
            },
            {
                "title": "Graph Queries for Compliance",
                "content": "Use graph queries to answer compliance questions: 'Which controls cover ISO 42001 A.8.2?' or 'What evidence supports this control?'",
                "exercise": "Write a graph query to find all controls that map to ISO 42001 and their evidence status",
                "expected_output": "List of controls with evidence completeness percentage",
                "validation_command": "npm run test:knowledge-graph",
                "hints": ["Use Cypher-like query language", "Filter by framework and evidence status"],
            },
            {
                "title": "Compliance Intelligence API",
                "content": "The compliance intelligence API exposes graph queries as REST endpoints for integration with dashboards and reporting tools.",
                "exercise": "Query the intelligence API for organization-wide compliance posture",
                "expected_output": "JSON response with compliance scores by framework and department",
                "hints": ["Endpoint: /api/v1/compliance/posture", "Supports filtering by framework, department, time range"],
            },
        ],
    },
    "T007": {
        "title": "Risk Assessment & Treatment Optimization",
        "description": "Automated risk assessment with treatment plan optimization",
        "tier": 3,
        "module_id": "M07",
        "difficulty": Difficulty.ADVANCED,
        "estimated_minutes": 55,
        "competencies_addressed": ["C5", "C9"],
        "prerequisites": ["T004"],
        "steps": [
            {
                "title": "Risk Assessment Framework",
                "content": "GRC_Claw automates risk assessment by correlating control gaps, threat intelligence, and business impact to produce risk scores.",
                "exercise": "Run a risk assessment for a sample control set",
                "expected_output": "Risk register with scores, likelihood, impact, and treatment priorities",
                "hints": ["Check packages/ for risk assessment modules", "Risk = Likelihood × Impact × Control Gap"],
            },
            {
                "title": "Treatment Plan Optimization",
                "content": "The treatment optimizer recommends risk treatment actions (mitigate, transfer, accept, avoid) based on cost-benefit analysis.",
                "exercise": "Generate a treatment plan for the top 5 risks from your assessment",
                "expected_output": "Treatment plan with recommended actions, cost estimates, and residual risk",
                "validation_command": "npm run test:comprehensive",
                "hints": ["Consider control implementation costs", "Residual risk must be within appetite"],
            },
        ],
    },
    "T008": {
        "title": "Audit Management & Evidence Automation",
        "description": "End-to-end audit preparation with automated evidence collection",
        "tier": 4,
        "module_id": "M08",
        "difficulty": Difficulty.EXPERT,
        "estimated_minutes": 90,
        "competencies_addressed": ["C1", "C3", "C10"],
        "prerequisites": ["T002", "T004", "T006"],
        "steps": [
            {
                "title": "Audit Planning",
                "content": "Define audit scope, criteria, and schedule. The audit manager maps audit criteria to controls and evidence requirements.",
                "exercise": "Create an audit plan for ISO 42001 surveillance audit",
                "expected_output": "Audit plan with scope, criteria, control mappings, and evidence checklist",
                "hints": ["Use packages/audit-management/", "Map audit criteria to framework clauses"],
            },
            {
                "title": "Automated Evidence Collection",
                "content": "The evidence automation engine collects, verifies, and packages evidence for each audit criterion. It ensures evidence is current and tamper-evident.",
                "exercise": "Run automated evidence collection for your audit plan",
                "expected_output": "Evidence package with completeness report and gaps identified",
                "validation_command": "npm run test:assurance-envelope",
                "hints": ["Evidence must be < 12 months old", "Check content hashes for integrity"],
            },
            {
                "title": "Audit Finding Management",
                "content": "Track audit findings, assign remediation, and verify closure. Findings link to controls and risk register.",
                "exercise": "Create a finding for missing evidence and track it through remediation",
                "expected_output": "Finding with severity, assignee, due date, and closure evidence",
                "hints": ["Findings have lifecycle: open -> in_progress -> closed", "Link findings to risk register entries"],
            },
        ],
    },
    "T009": {
        "title": "AI Governance & Model Risk Management",
        "description": "Govern AI models throughout their lifecycle with automated compliance checks",
        "tier": 4,
        "module_id": "M09",
        "difficulty": Difficulty.EXPERT,
        "estimated_minutes": 80,
        "competencies_addressed": ["C2", "C5", "C8"],
        "prerequisites": ["T003", "T007"],
        "steps": [
            {
                "title": "AI Model Registry",
                "content": "Register AI models with metadata, version, training data provenance, and risk classification. The registry is the source of truth for all AI assets.",
                "exercise": "Register a sample AI model with full metadata",
                "expected_output": "Model registry entry with ID, version, provenance, and risk class",
                "hints": ["Use packages/ai-governance/", "Risk classes: minimal, low, high, unacceptable"],
            },
            {
                "title": "Model Risk Assessment",
                "content": "Assess model risk across dimensions: bias, explainability, robustness, and data quality. Each dimension produces a score that feeds the overall risk classification.",
                "exercise": "Run a model risk assessment for your registered model",
                "expected_output": "Risk assessment report with dimension scores and overall classification",
                "validation_command": "npm run test:ai-governance",
                "hints": ["Each dimension has specific tests", "Overall risk = weighted combination"],
            },
            {
                "title": "Continuous Model Monitoring",
                "content": "Monitor deployed models for drift, performance degradation, and compliance violations. Alerts trigger when metrics exceed thresholds.",
                "exercise": "Set up continuous monitoring for your model with drift detection",
                "expected_output": "Monitoring configuration with thresholds and alert rules",
                "hints": ["Check packages/continuous-trust-engine/", "Drift thresholds are per-metric"],
            },
        ],
    },
    "T010": {
        "title": "Federated Compliance Mesh",
        "description": "Multi-tenant compliance with federated trust and cross-organizational evidence sharing",
        "tier": 4,
        "module_id": "M10",
        "difficulty": Difficulty.EXPERT,
        "estimated_minutes": 70,
        "competencies_addressed": ["C4", "C7", "C10"],
        "prerequisites": ["T005", "T008"],
        "steps": [
            {
                "title": "Federated Mesh Architecture",
                "content": "The federated compliance mesh connects multiple GRC_Claw instances across organizations, enabling cross-organizational compliance verification and evidence sharing.",
                "exercise": "Review the federated mesh package and understand the trust model",
                "hints": ["Check packages/federated-compliance-mesh/", "Trust is established via mutual TLS and trust passports"],
            },
            {
                "title": "Cross-Organizational Evidence",
                "content": "Share compliance evidence across organizational boundaries with cryptographic verification and privacy preservation.",
                "exercise": "Share a compliance evidence package with a federated partner",
                "expected_output": "Shared evidence with verification receipt",
                "validation_command": "npm run test:mesh",
                "hints": ["Evidence is hashed before sharing", "Partner verifies hash independently"],
            },
        ],
    },
    "T011": {
        "title": "Threat Intelligence & AI Threat Detection",
        "description": "Integrate threat intelligence feeds and detect AI-specific threats",
        "tier": 3,
        "module_id": "M11",
        "difficulty": Difficulty.ADVANCED,
        "estimated_minutes": 65,
        "competencies_addressed": ["C5", "C7"],
        "prerequisites": ["T003", "T005"],
        "steps": [
            {
                "title": "Threat Intelligence Integration",
                "content": "Ingest threat intelligence feeds (STIX/TAXII, OSINT, commercial) and correlate with compliance controls and asset inventory.",
                "exercise": "Ingest a sample threat feed and map IOCs to compliance controls",
                "expected_output": "Threat intelligence report with IOC-to-control mappings",
                "hints": ["Check packages/ai-threat-detection/", "STIX 2.1 is the supported format"],
            },
            {
                "title": "AI-Specific Threat Detection",
                "content": "Detect AI-specific threats: prompt injection, model extraction, data poisoning, and adversarial examples. Each threat type has dedicated detection rules.",
                "exercise": "Run AI threat detection on a sample agent conversation",
                "expected_output": "Threat detection report with flagged interactions and severity",
                "validation_command": "npm run test:threat",
                "hints": ["Detection rules are in YAML", "Each rule has a severity and confidence score"],
            },
        ],
    },
    "T012": {
        "title": "Business Impact & Financial Governance",
        "description": "Quantify compliance impact on business outcomes and financial governance",
        "tier": 3,
        "module_id": "M12",
        "difficulty": Difficulty.ADVANCED,
        "estimated_minutes": 50,
        "competencies_addressed": ["C9", "C10"],
        "prerequisites": ["T007"],
        "steps": [
            {
                "title": "Business Impact Analysis",
                "content": "Quantify the business impact of compliance gaps and control failures. Map controls to business processes and calculate potential loss.",
                "exercise": "Run a business impact analysis for a critical control failure",
                "expected_output": "BIA report with financial impact, operational impact, and recovery objectives",
                "hints": ["Check packages/business-impact/", "Impact = Probability × Loss magnitude"],
            },
            {
                "title": "Financial Governance Reporting",
                "content": "Generate financial governance reports for board and executive consumption. Reports include compliance ROI, risk-adjusted returns, and investment priorities.",
                "exercise": "Generate a quarterly financial governance report",
                "expected_output": "Board-ready report with compliance metrics, ROI, and recommendations",
                "validation_command": "npm run test:business",
                "hints": ["Reports use the board-reporting package", "Include trend analysis and benchmarks"],
            },
        ],
    },
    "T013": {
        "title": "Zero-Knowledge Compliance Proofs",
        "description": "Use zero-knowledge proofs to verify compliance without revealing sensitive data",
        "tier": 4,
        "module_id": "M13",
        "difficulty": Difficulty.EXPERT,
        "estimated_minutes": 85,
        "competencies_addressed": ["C1", "C6", "C8"],
        "prerequisites": ["T006", "T008"],
        "steps": [
            {
                "title": "ZK Proof Concepts",
                "content": "Zero-knowledge proofs allow one party to prove a statement is true without revealing the underlying data. In GRC_Claw, ZK proofs verify compliance without exposing sensitive configuration or evidence.",
                "exercise": "Review the ZK compliance package and understand the proof system",
                "hints": ["Check packages/zk-compliance/", "Uses zk-SNARKs for compact proofs"],
            },
            {
                "title": "Generating Compliance Proofs",
                "content": "Generate ZK proofs for compliance statements: 'All access controls are enforced' without revealing the specific control configurations.",
                "exercise": "Generate a ZK proof for a compliance statement",
                "expected_output": "ZK proof with verification key and public inputs",
                "validation_command": "npm run test:zk",
                "hints": ["Proofs are generated from constraint systems", "Verification is fast regardless of complexity"],
            },
        ],
    },
    "T014": {
        "title": "Capstone: Full Compliance Automation",
        "description": "End-to-end capstone combining all skills: build a complete automated compliance pipeline",
        "tier": 4,
        "module_id": "M14",
        "difficulty": Difficulty.EXPERT,
        "estimated_minutes": 120,
        "competencies_addressed": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"],
        "prerequisites": ["T001", "T002", "T003", "T004", "T005", "T006", "T007", "T008"],
        "steps": [
            {
                "title": "Architecture Design",
                "content": "Design a complete compliance automation pipeline for a fictional organization. Include gateway, evidence plane, orchestrator, and reporting.",
                "exercise": "Create an architecture diagram and component specification",
                "expected_output": "Architecture document with component interactions and data flow",
                "hints": ["Use the C4 model", "Include all three planes: control, data, evidence"],
            },
            {
                "title": "Implementation",
                "content": "Implement the pipeline: configure gateway, define controls, set up orchestration, connect evidence collection, and enable reporting.",
                "exercise": "Implement your architecture using GRC_Claw packages",
                "expected_output": "Working compliance pipeline with automated evidence collection",
                "validation_command": "npm run test:comprehensive",
                "hints": ["Start with gateway + evidence", "Add orchestrator last", "Test each component independently"],
            },
            {
                "title": "Audit Simulation",
                "content": "Run a simulated audit against your pipeline. Verify evidence completeness, control effectiveness, and reporting accuracy.",
                "exercise": "Run an audit simulation and address any findings",
                "expected_output": "Audit report with findings and remediation evidence",
                "hints": ["Use the audit-management package", "All findings must have closure evidence"],
            },
        ],
    },
}


# ─── Tutorial Engine ─────────────────────────────────────────────────────────

class TutorialEngine:
    """Interactive tutorial engine with progress tracking and validation."""

    def __init__(self, data_dir: str = "~/.grc_claw/training"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.data_dir / "tutorial_progress.json"
        self.profile_file = self.data_dir / "learner_profile.json"
        self.progress = self._load_progress()
        self.profile = self._load_profile()

    def _load_progress(self) -> dict:
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                return json.load(f)
        return {}

    def _load_profile(self) -> dict:
        if self.profile_file.exists():
            with open(self.profile_file) as f:
                return json.load(f)
        return {
            "user_id": str(uuid.uuid4()),
            "name": "",
            "email": "",
            "role": "",
            "tier": 1,
            "department": "",
            "start_date": datetime.now().isoformat(),
            "completed_tutorials": [],
            "tutorial_scores": {},
            "total_learning_minutes": 0,
            "streak_days": 0,
            "last_activity": None,
        }

    def _save_progress(self):
        with open(self.progress_file, "w") as f:
            json.dump(self.progress, f, indent=2)

    def _save_profile(self):
        with open(self.profile_file, "w") as f:
            json.dump(self.profile, f, indent=2)

    def list_tutorials(self, tier: Optional[int] = None, module_id: Optional[str] = None) -> list[dict]:
        """List available tutorials with optional filtering."""
        results = []
        for tid, tdata in TUTORIAL_CATALOG.items():
            if tier is not None and tdata["tier"] != tier:
                continue
            if module_id is not None and tdata["module_id"] != module_id:
                continue
            progress = self.progress.get(tid, {})
            results.append({
                "tutorial_id": tid,
                "title": tdata["title"],
                "description": tdata["description"],
                "tier": tdata["tier"],
                "module_id": tdata["module_id"],
                "difficulty": tdata["difficulty"],
                "estimated_minutes": tdata["estimated_minutes"],
                "competencies": tdata["competencies_addressed"],
                "prerequisites": tdata["prerequisites"],
                "status": progress.get("status", "not_started"),
                "progress_pct": self._compute_progress(tid),
            })
        return sorted(results, key=lambda x: (x["tier"], x["module_id"]))

    def _compute_progress(self, tutorial_id: str) -> float:
        if tutorial_id not in self.progress:
            return 0.0
        p = self.progress[tutorial_id]
        total_steps = len(TUTORIAL_CATALOG[tutorial_id]["steps"])
        completed_steps = p.get("completed_steps", [])
        if total_steps == 0:
            return 0.0
        return round(len(completed_steps) / total_steps * 100, 1)

    def start_tutorial(self, tutorial_id: str) -> dict:
        """Start or resume a tutorial."""
        if tutorial_id not in TUTORIAL_CATALOG:
            raise ValueError(f"Unknown tutorial: {tutorial_id}")

        tdata = TUTORIAL_CATALOG[tutorial_id]

        # Check prerequisites
        for prereq in tdata["prerequisites"]:
            prereq_progress = self.progress.get(prereq, {})
            if prereq_progress.get("status") != "completed":
                return {
                    "error": f"Prerequisite not met: {prereq}",
                    "prerequisite": prereq,
                    "prerequisite_title": TUTORIAL_CATALOG[prereq]["title"],
                }

        if tutorial_id not in self.progress:
            self.progress[tutorial_id] = {
                "status": "in_progress",
                "started_at": datetime.now().isoformat(),
                "completed_steps": [],
                "current_step": 0,
                "step_scores": {},
            }
            self._save_progress()

        return self.get_tutorial_state(tutorial_id)

    def get_tutorial_state(self, tutorial_id: str) -> dict:
        """Get current state of a tutorial."""
        if tutorial_id not in TUTORIAL_CATALOG:
            raise ValueError(f"Unknown tutorial: {tutorial_id}")

        tdata = TUTORIAL_CATALOG[tutorial_id]
        progress = self.progress.get(tutorial_id, {})
        completed_steps = set(progress.get("completed_steps", []))
        current_step = progress.get("current_step", 0)

        steps_out = []
        for i, step in enumerate(tdata["steps"]):
            steps_out.append({
                "step_number": i + 1,
                "title": step["title"],
                "content": step["content"],
                "exercise": step.get("exercise"),
                "expected_output": step.get("expected_output"),
                "hints": step.get("hints", []),
                "validation_command": step.get("validation_command"),
                "completed": i in completed_steps,
                "is_current": i == current_step,
            })

        return {
            "tutorial_id": tutorial_id,
            "title": tdata["title"],
            "description": tdata["description"],
            "tier": tdata["tier"],
            "module_id": tdata["module_id"],
            "difficulty": tdata["difficulty"],
            "estimated_minutes": tdata["estimated_minutes"],
            "competencies_addressed": tdata["competencies_addressed"],
            "status": progress.get("status", "not_started"),
            "progress_pct": self._compute_progress(tutorial_id),
            "current_step": current_step + 1,
            "total_steps": len(tdata["steps"]),
            "steps": steps_out,
        }

    def complete_step(self, tutorial_id: str, step_index: int, score: float = 100.0) -> dict:
        """Mark a tutorial step as complete."""
        if tutorial_id not in TUTORIAL_CATALOG:
            raise ValueError(f"Unknown tutorial: {tutorial_id}")

        tdata = TUTORIAL_CATALOG[tutorial_id]
        if step_index < 0 or step_index >= len(tdata["steps"]):
            raise ValueError(f"Invalid step index: {step_index}")

        if tutorial_id not in self.progress:
            self.start_tutorial(tutorial_id)

        progress = self.progress[tutorial_id]
        if step_index not in progress["completed_steps"]:
            progress["completed_steps"].append(step_index)
        progress["step_scores"][str(step_index)] = score
        progress["current_step"] = step_index + 1

        # Check if all steps completed
        if len(progress["completed_steps"]) == len(tdata["steps"]):
            progress["status"] = "completed"
            progress["completed_at"] = datetime.now().isoformat()
            avg_score = sum(progress["step_scores"].values()) / len(progress["step_scores"])
            progress["final_score"] = round(avg_score, 1)

            # Update profile
            if tutorial_id not in self.profile["completed_tutorials"]:
                self.profile["completed_tutorials"].append(tutorial_id)
            self.profile["tutorial_scores"][tutorial_id] = round(avg_score, 1)
            self.profile["total_learning_minutes"] += tdata["estimated_minutes"]
            self.profile["last_activity"] = datetime.now().isoformat()
            self._save_profile()

        self._save_progress()
        return self.get_tutorial_state(tutorial_id)

    def get_hint(self, tutorial_id: str, step_index: int) -> dict:
        """Get a hint for the current step."""
        if tutorial_id not in TUTORIAL_CATALOG:
            raise ValueError(f"Unknown tutorial: {tutorial_id}")

        tdata = TUTORIAL_CATALOG[tutorial_id]
        if step_index < 0 or step_index >= len(tdata["steps"]):
            raise ValueError(f"Invalid step index: {step_index}")

        step = tdata["steps"][step_index]
        hints = step.get("hints", [])
        progress = self.progress.get(tutorial_id, {})
        hints_used = progress.get("hints_used", {}).get(str(step_index), 0)

        if hints_used >= len(hints):
            return {"hint": None, "message": "No more hints available for this step."}

        hint = hints[hints_used]
        if "hints_used" not in progress:
            progress["hints_used"] = {}
        progress["hints_used"][str(step_index)] = hints_used + 1
        self._save_progress()

        return {
            "hint": hint,
            "hint_number": hints_used + 1,
            "total_hints": len(hints),
        }

    def get_dashboard(self) -> dict:
        """Get learner dashboard data."""
        total_tutorials = len(TUTORIAL_CATALOG)
        completed = len(self.profile["completed_tutorials"])
        in_progress = sum(
            1 for p in self.progress.values() if p.get("status") == "in_progress"
        )

        # Competency coverage
        competency_progress = {f"C{i}": {"addressed": 0, "completed": 0} for i in range(1, 11)}
        for tid, tdata in TUTORIAL_CATALOG.items():
            for comp in tdata["competencies_addressed"]:
                competency_progress[comp]["addressed"] += 1
                if tid in self.profile["completed_tutorials"]:
                    competency_progress[comp]["completed"] += 1

        # Tier progress
        tier_progress = {}
        for tier in range(1, 5):
            tier_tutorials = [t for t in TUTORIAL_CATALOG.values() if t["tier"] == tier]
            tier_completed = sum(
                1 for tid, t in TUTORIAL_CATALOG.items()
                if t["tier"] == tier and tid in self.profile["completed_tutorials"]
            )
            tier_progress[f"tier_{tier}"] = {
                "total": len(tier_tutorials),
                "completed": tier_completed,
                "pct": round(tier_completed / len(tier_tutorials) * 100, 1) if tier_tutorials else 0,
            }

        return {
            "learner": {
                "user_id": self.profile["user_id"],
                "name": self.profile["name"],
                "role": self.profile["role"],
                "tier": self.profile["tier"],
            },
            "summary": {
                "total_tutorials": total_tutorials,
                "completed": completed,
                "in_progress": in_progress,
                "not_started": total_tutorials - completed - in_progress,
                "overall_progress_pct": round(completed / total_tutorials * 100, 1),
                "total_learning_minutes": self.profile["total_learning_minutes"],
                "average_score": round(
                    sum(self.profile["tutorial_scores"].values()) / len(self.profile["tutorial_scores"]), 1
                ) if self.profile["tutorial_scores"] else 0,
            },
            "competency_coverage": competency_progress,
            "tier_progress": tier_progress,
            "recent_activity": self._get_recent_activity(),
        }

    def _get_recent_activity(self) -> list[dict]:
        """Get recent tutorial activity."""
        activity = []
        for tid, p in self.progress.items():
            if p.get("status") == "completed":
                activity.append({
                    "tutorial_id": tid,
                    "title": TUTORIAL_CATALOG[tid]["title"],
                    "completed_at": p.get("completed_at"),
                    "score": p.get("final_score"),
                })
        return sorted(activity, key=lambda x: x.get("completed_at", ""), reverse=True)[:5]


# ─── CLI Interface ────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="GRC_Claw Interactive Tutorial System")
    parser.add_argument("--list", action="store_true", help="List all tutorials")
    parser.add_argument("--tier", type=int, help="Filter by tier (1-4)")
    parser.add_argument("--module", type=str, help="Filter by module ID (e.g., M01)")
    parser.add_argument("--start", type=str, help="Start a tutorial by ID")
    parser.add_argument("--state", type=str, help="Get tutorial state by ID")
    parser.add_argument("--complete-step", type=str, nargs=2, metavar=("TUTORIAL_ID", "STEP_INDEX"),
                        help="Complete a step: tutorial_id step_index")
    parser.add_argument("--hint", type=str, nargs=2, metavar=("TUTORIAL_ID", "STEP_INDEX"),
                        help="Get a hint: tutorial_id step_index")
    parser.add_argument("--dashboard", action="store_true", help="Show learner dashboard")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    engine = TutorialEngine()

    if args.list:
        tutorials = engine.list_tutorials(tier=args.tier, module_id=args.module)
        if args.json:
            print(json.dumps(tutorials, indent=2))
        else:
            print(f"\n{'ID':<8} {'Tier':<6} {'Module':<8} {'Difficulty':<14} {'Status':<14} {'Progress':<10} Title")
            print("-" * 100)
            for t in tutorials:
                print(f"{t['tutorial_id']:<8} {t['tier']:<6} {t['module_id']:<8} {t['difficulty']:<14} {t['status']:<14} {t['progress_pct']:>6.1f}%  {t['title']}")
            print(f"\nTotal: {len(tutorials)} tutorials")

    elif args.start:
        result = engine.start_tutorial(args.start)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if "error" in result:
                print(f"Error: {result['error']}")
                print(f"Complete prerequisite first: {result['prerequisite_title']} ({result['prerequisite']})")
            else:
                print(f"\n{'='*60}")
                print(f"Tutorial: {result['title']}")
                print(f"{'='*60}")
                print(f"Status: {result['status']}")
                print(f"Progress: {result['progress_pct']}%")
                print(f"Step {result['current_step']} of {result['total_steps']}")
                print(f"Difficulty: {result['difficulty']}")
                print(f"Estimated time: {result['estimated_minutes']} minutes")
                print(f"Competencies: {', '.join(result['competencies_addressed'])}")
                if result["steps"]:
                    step = result["steps"][result["current_step"] - 1] if result["current_step"] <= len(result["steps"]) else result["steps"][0]
                    print(f"\n--- Step {step['step_number']}: {step['title']} ---")
                    print(step["content"])
                    if step["exercise"]:
                        print(f"\nExercise: {step['exercise']}")
                    if step["expected_output"]:
                        print(f"Expected output: {step['expected_output']}")
                    if step["validation_command"]:
                        print(f"Validation: {step['validation_command']}")

    elif args.state:
        result = engine.get_tutorial_state(args.state)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"Tutorial: {result['title']}")
            print(f"{'='*60}")
            print(f"Status: {result['status']} | Progress: {result['progress_pct']}%")
            for step in result["steps"]:
                marker = "✓" if step["completed"] else ("→" if step["is_current"] else "○")
                print(f"  {marker} Step {step['step_number']}: {step['title']}")

    elif args.complete_step:
        tutorial_id, step_idx = args.complete_step[0], int(args.complete_step[1])
        result = engine.complete_step(tutorial_id, step_idx)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Step {step_idx + 1} completed!")
            print(f"Tutorial progress: {result['progress_pct']}%")
            if result["status"] == "completed":
                print(f"🎉 Tutorial completed! Final score: {result.get('final_score', 'N/A')}")

    elif args.hint:
        tutorial_id, step_idx = args.hint[0], int(args.hint[1])
        result = engine.get_hint(tutorial_id, step_idx)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["hint"]:
                print(f"Hint {result['hint_number']}/{result['total_hints']}: {result['hint']}")
            else:
                print(result["message"])

    elif args.dashboard:
        result = engine.get_dashboard()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            d = result
            print(f"\n{'='*60}")
            print(f"GRC_Claw Training Dashboard")
            print(f"{'='*60}")
            print(f"Learner: {d['learner']['name'] or 'Anonymous'} (Tier {d['learner']['tier']})")
            print(f"\n--- Summary ---")
            s = d["summary"]
            print(f"  Completed: {s['completed']}/{s['total_tutorials']} ({s['overall_progress_pct']}%)")
            print(f"  In Progress: {s['in_progress']}")
            print(f"  Total Learning: {s['total_learning_minutes']} minutes")
            print(f"  Average Score: {s['average_score']}")
            print(f"\n--- Tier Progress ---")
            for tier, tp in d["tier_progress"].items():
                bar = "█" * int(tp["pct"] / 10) + "░" * (10 - int(tp["pct"] / 10))
                print(f"  {tier}: [{bar}] {tp['completed']}/{tp['total']} ({tp['pct']}%)")
            print(f"\n--- Competency Coverage ---")
            for comp, cp in d["competency_coverage"].items():
                if cp["addressed"] > 0:
                    pct = round(cp["completed"] / cp["addressed"] * 100, 1)
                    print(f"  {comp}: {cp['completed']}/{cp['addressed']} tutorials ({pct}%)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
