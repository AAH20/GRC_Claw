"""
GRC_Claw Incident Response Orchestration with Runbooks (§13 of GRC-AIM-001)

Implements the automated orchestration layer:
    • Runbook engine — trigger, workflow, state machine
    • Action executor — API calls, CLI exec, webhooks, scripts
    • Decision engine — if/else, approval, escalate, rollback
    • Integration layer — AI-Risk-Radar, Policy Engine, Model Registry, Ticketing, Notification
    • Execution modes — fully automated, human-in-the-loop, advisory, simulation
    • State machine — DETECTED → TRIAGED → CONTAINED → ERADICATED → RECOVERED → CLOSED
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from .models import (
    DetectionSignal,
    Incident,
    IncidentStatus,
    ResponseAction,
    AffectedAsset,
    AssetType,
    Environment,
)
from .taxonomy import IncidentCategory, Severity

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Runbook Structure (§13.2)
# ═══════════════════════════════════════════════════════════════════════════════

class ExecutionMode(str, Enum):
    """Runbook execution modes (§13.4)."""
    FULLY_AUTOMATED = "fully_automated"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    ADVISORY = "advisory"
    SIMULATION = "simulation"


class ActionType(str, Enum):
    API_CALL = "api_call"
    CLI_EXEC = "cli_exec"
    WEBHOOK = "webhook"
    SCRIPT = "script"
    NOTIFICATION = "notification"


class OnFailure(str, Enum):
    CONTINUE = "continue"
    ESCALATE = "escalate"
    ABORT = "abort"
    ROLLBACK = "rollback"


@dataclass
class RunbookAction:
    """A single action within a runbook."""
    id: str
    name: str
    type: ActionType
    target: str
    params: dict[str, Any] = field(default_factory=dict)
    on_failure: OnFailure = OnFailure.CONTINUE
    approval_required: bool = False
    rollback_action: Optional[str] = None  # ID of rollback action
    result: str = ""
    status: str = "pending"  # pending | running | completed | failed | skipped
    started_at: str = ""
    completed_at: str = ""


@dataclass
class RunbookTrigger:
    """Trigger conditions for a runbook."""
    incident_category: Optional[str] = None
    subcategory_code: str = ""
    severity: list[str] = field(default_factory=list)
    confidence_min: float = 0.0
    environment: str = ""


@dataclass
class Runbook:
    """Complete runbook definition (§13.2)."""
    id: str
    name: str
    version: str = "1.0"
    trigger: RunbookTrigger = field(default_factory=RunbookTrigger)
    preconditions: list[str] = field(default_factory=list)
    actions: list[RunbookAction] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    rollback: list[RunbookAction] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.HUMAN_IN_THE_LOOP
    description: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Action Executor
# ═══════════════════════════════════════════════════════════════════════════════

class ActionExecutor:
    """
    Executes runbook actions across multiple integration targets.

    In production, this integrates with:
    • AI-Risk-Radar API
    • Policy Engine
    • Model Registry
    • Ticketing Service (Jira, ServiceNow)
    • Notification (PagerDuty, Slack, Email)
    • API Gateway
    • Identity Service
    """

    def __init__(self) -> None:
        self._handlers: dict[ActionType, Callable[[RunbookAction, Incident], bool]] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        self._handlers[ActionType.API_CALL] = self._handle_api_call
        self._handlers[ActionType.CLI_EXEC] = self._handle_cli_exec
        self._handlers[ActionType.WEBHOOK] = self._handle_webhook
        self._handlers[ActionType.SCRIPT] = self._handle_script
        self._handlers[ActionType.NOTIFICATION] = self._handle_notification

    def register_handler(
        self, action_type: ActionType,
        handler: Callable[[RunbookAction, Incident], bool]
    ) -> None:
        self._handlers[action_type] = handler

    def execute(self, action: RunbookAction, incident: Incident) -> bool:
        """Execute a single action."""
        handler = self._handlers.get(action.type)
        if not handler:
            logger.error(f"No handler for action type: {action.type}")
            action.status = "failed"
            return False

        action.status = "running"
        action.started_at = datetime.now(timezone.utc).isoformat()

        try:
            success = handler(action, incident)
            action.status = "completed" if success else "failed"
            action.completed_at = datetime.now(timezone.utc).isoformat()
            return success
        except Exception as e:
            logger.exception(f"Action {action.id} failed: {e}")
            action.status = "failed"
            action.result = str(e)
            action.completed_at = datetime.now(timezone.utc).isoformat()
            return False

    def _handle_api_call(self, action: RunbookAction, incident: Incident) -> bool:
        """Handle API call actions. Override in production."""
        logger.info(f"API call to {action.target} with params: {action.params}")
        action.result = f"API call to {action.target} completed"
        return True

    def _handle_cli_exec(self, action: RunbookAction, incident: Incident) -> bool:
        """Handle CLI execution actions. Override in production."""
        logger.info(f"CLI exec on {action.target}: {action.params}")
        action.result = f"CLI exec on {action.target} completed"
        return True

    def _handle_webhook(self, action: RunbookAction, incident: Incident) -> bool:
        """Handle webhook actions. Override in production."""
        logger.info(f"Webhook to {action.target}: {action.params}")
        action.result = f"Webhook to {action.target} delivered"
        return True

    def _handle_script(self, action: RunbookAction, incident: Incident) -> bool:
        """Handle script execution actions. Override in production."""
        logger.info(f"Script execution on {action.target}: {action.params}")
        action.result = f"Script on {action.target} executed"
        return True

    def _handle_notification(self, action: RunbookAction, incident: Incident) -> bool:
        """Handle notification actions. Override in production."""
        logger.info(f"Notification to {action.target}: {action.params}")
        action.result = f"Notification sent to {action.target}"
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# Decision Engine
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionEngine:
    """
    Decision engine for runbook branching logic.

    Supports: if/else, approval gates, escalation, rollback decisions.
    """

    def __init__(self) -> None:
        self._conditions: dict[str, Callable[[Incident], bool]] = {}

    def register_condition(self, name: str, fn: Callable[[Incident], bool]) -> None:
        self._conditions[name] = fn

    def evaluate(self, condition_name: str, incident: Incident) -> bool:
        fn = self._conditions.get(condition_name)
        if fn:
            return fn(incident)
        return False

    def requires_approval(self, action: RunbookAction, incident: Incident) -> bool:
        """Determine if an action requires human approval."""
        if action.approval_required:
            return True
        # Irreversible actions always require approval
        if action.type == ActionType.API_CALL and action.params.get("irreversible", False):
            return True
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# Runbook Engine
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RunbookExecution:
    """Record of a runbook execution."""
    execution_id: str
    runbook_id: str
    incident_id: str
    mode: ExecutionMode
    status: str = "pending"  # pending | running | completed | failed | rolled_back
    actions_completed: int = 0
    actions_failed: int = 0
    started_at: str = ""
    completed_at: str = ""
    results: list[dict[str, Any]] = field(default_factory=list)


class RunbookEngine:
    """
    Runbook engine — triggers, workflow execution, state machine (§13.1, §13.6).
    """

    def __init__(self) -> None:
        self._runbooks: dict[str, Runbook] = {}
        self._executor = ActionExecutor()
        self._decision = DecisionEngine()
        self._executions: list[RunbookExecution] = []

    def register_runbook(self, runbook: Runbook) -> None:
        self._runbooks[runbook.id] = runbook

    def get_runbook(self, runbook_id: str) -> Optional[Runbook]:
        return self._runbooks.get(runbook_id)

    def find_matching_runbooks(self, incident: Incident) -> list[Runbook]:
        """Find all runbooks whose triggers match the incident."""
        matches = []
        for rb in self._runbooks.values():
            if self._trigger_matches(rb.trigger, incident):
                matches.append(rb)
        return matches

    def execute_runbook(
        self,
        runbook_id: str,
        incident: Incident,
        mode: Optional[ExecutionMode] = None,
    ) -> RunbookExecution:
        """Execute a runbook against an incident."""
        runbook = self._runbooks.get(runbook_id)
        if not runbook:
            raise ValueError(f"Runbook not found: {runbook_id}")

        exec_mode = mode or runbook.execution_mode
        execution = RunbookExecution(
            execution_id=hashlib.sha256(
                f"{runbook_id}:{incident.incident_id}:{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16],
            runbook_id=runbook_id,
            incident_id=incident.incident_id,
            mode=exec_mode,
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._executions.append(execution)

        # Check preconditions
        if not self._check_preconditions(runbook.preconditions, incident):
            execution.status = "failed"
            execution.completed_at = datetime.now(timezone.utc).isoformat()
            return execution

        # Execute actions
        for action in runbook.actions:
            # Human-in-the-loop: pause for approval
            if exec_mode == ExecutionMode.HUMAN_IN_THE_LOOP and self._decision.requires_approval(action, incident):
                action.status = "pending_approval"
                # In production, this would pause and notify
                logger.info(f"Action {action.id} pending approval")

            success = self._executor.execute(action, incident)
            if success:
                execution.actions_completed += 1
                execution.results.append({
                    "action_id": action.id,
                    "action_name": action.name,
                    "status": "completed",
                    "result": action.result,
                })
            else:
                execution.actions_failed += 1
                execution.results.append({
                    "action_id": action.id,
                    "action_name": action.name,
                    "status": "failed",
                    "result": action.result,
                })
                if action.on_failure == OnFailure.ESCALATE:
                    self._escalate(incident, action)
                elif action.on_failure == OnFailure.ROLLBACK:
                    self._rollback(runbook, incident, execution)
                    break
                elif action.on_failure == OnFailure.ABORT:
                    execution.status = "failed"
                    break

        # Check postconditions
        if execution.status == "running":
            if self._check_postconditions(runbook.postconditions, incident):
                execution.status = "completed"
            else:
                execution.status = "failed"

        execution.completed_at = datetime.now(timezone.utc).isoformat()
        return execution

    def _trigger_matches(self, trigger: RunbookTrigger, incident: Incident) -> bool:
        """Check if a runbook trigger matches an incident."""
        if trigger.incident_category and incident.category:
            if trigger.incident_category != incident.category.value:
                return False
        if trigger.subcategory_code and incident.subcategory_code:
            if trigger.subcategory_code != incident.subcategory_code:
                return False
        if trigger.severity and incident.severity:
            if incident.severity.value not in trigger.severity:
                return False
        return True

    def _check_preconditions(self, preconditions: list[str], incident: Incident) -> bool:
        """Check if all preconditions are met."""
        for pre in preconditions:
            if not self._decision.evaluate(pre, incident):
                logger.warning(f"Precondition not met: {pre}")
                return False
        return True

    def _check_postconditions(self, postconditions: list[str], incident: Incident) -> bool:
        """Check if all postconditions are satisfied."""
        for post in postconditions:
            if not self._decision.evaluate(post, incident):
                logger.warning(f"Postcondition not met: {post}")
                return False
        return True

    def _escalate(self, incident: Incident, action: RunbookAction) -> None:
        """Escalate a failed action."""
        logger.critical(f"Escalation for incident {incident.incident_id}, action {action.name}")

    def _rollback(
        self, runbook: Runbook, incident: Incident, execution: RunbookExecution
    ) -> None:
        """Execute rollback actions."""
        logger.warning(f"Rolling back runbook {runbook.id} for incident {incident.incident_id}")
        for rb_action in runbook.rollback:
            self._executor.execute(rb_action, incident)
        execution.status = "rolled_back"

    def get_executions(self) -> list[RunbookExecution]:
        return list(self._executions)


# ═══════════════════════════════════════════════════════════════════════════════
# Runbook Library (§13.3)
# ═══════════════════════════════════════════════════════════════════════════════

def create_default_runbooks() -> list[Runbook]:
    """Create the default runbook library from §13.3."""
    runbooks = []

    # ── Data Leakage Runbooks ──
    runbooks.append(Runbook(
        id="RB-DL-001", name="Data Leakage Response", version="1.0",
        trigger=RunbookTrigger(
            incident_category="DL", severity=["S1", "S2"], confidence_min=0.80
        ),
        preconditions=["affected_asset_registered", "backup_available"],
        actions=[
            RunbookAction("1", "Preserve Evidence", ActionType.API_CALL, "evidence_service",
                         {"preserve_logs": True, "preserve_outputs": True}),
            RunbookAction("2", "Disable Affected Endpoint", ActionType.API_CALL, "api_gateway",
                         {"action": "disable"}, on_failure=OnFailure.ESCALATE),
            RunbookAction("3", "Revoke API Keys", ActionType.API_CALL, "identity_service",
                         {"action": "revoke", "scope": "affected_asset"}, on_failure=OnFailure.ESCALATE),
            RunbookAction("4", "Notify Security Team", ActionType.NOTIFICATION, "security_team",
                         {"channel": "pagerduty", "severity": "critical"}),
            RunbookAction("5", "Create Incident Ticket", ActionType.API_CALL, "ticketing_service",
                         {"priority": "P1", "category": "data_leakage"}),
        ],
        postconditions=["affected_endpoint_disabled", "evidence_preserved", "stakeholders_notified"],
        rollback=[
            RunbookAction("rb-1", "Re-enable Endpoint", ActionType.API_CALL, "api_gateway",
                         {"action": "enable"}),
        ],
        execution_mode=ExecutionMode.FULLY_AUTOMATED,
    ))

    runbooks.append(Runbook(
        id="RB-DL-002", name="Training Data Exposure", version="1.0",
        trigger=RunbookTrigger(subcategory_code="DL-1", severity=["S2", "S3"]),
        actions=[
            RunbookAction("1", "Isolate Model", ActionType.API_CALL, "model_registry",
                         {"action": "isolate"}),
            RunbookAction("2", "Scan Outputs", ActionType.SCRIPT, "output_scanner",
                         {"scan_type": "pii_detection"}),
            RunbookAction("3", "Notify Legal/Compliance", ActionType.NOTIFICATION, "legal_team",
                         {"channel": "email", "priority": "high"}),
        ],
        execution_mode=ExecutionMode.HUMAN_IN_THE_LOOP,
    ))

    # ── Harmful Output Runbooks ──
    runbooks.append(Runbook(
        id="RB-HO-001", name="Toxic Content Response", version="1.0",
        trigger=RunbookTrigger(subcategory_code="HO-1", severity=["S2", "S3"]),
        actions=[
            RunbookAction("1", "Enable Enhanced Filtering", ActionType.API_CALL, "policy_engine",
                         {"action": "enable_filter", "filter_type": "toxicity"}),
            RunbookAction("2", "Rate-Limit Model", ActionType.API_CALL, "api_gateway",
                         {"action": "rate_limit", "requests_per_minute": 10}),
            RunbookAction("3", "Flag Outputs", ActionType.API_CALL, "output_service",
                         {"action": "flag", "flag_type": "toxic"}),
        ],
        execution_mode=ExecutionMode.FULLY_AUTOMATED,
    ))

    runbooks.append(Runbook(
        id="RB-HO-002", name="Dangerous Instructions", version="1.0",
        trigger=RunbookTrigger(subcategory_code="HO-2", severity=["S1", "S2"]),
        actions=[
            RunbookAction("1", "Immediate Model Suspension", ActionType.API_CALL, "model_registry",
                         {"action": "suspend"}, on_failure=OnFailure.ESCALATE),
            RunbookAction("2", "Preserve Evidence", ActionType.API_CALL, "evidence_service",
                         {"preserve_logs": True, "preserve_outputs": True}),
            RunbookAction("3", "Notify Authorities", ActionType.NOTIFICATION, "security_team",
                         {"channel": "pagerduty", "severity": "critical"}),
        ],
        execution_mode=ExecutionMode.FULLY_AUTOMATED,
    ))

    runbooks.append(Runbook(
        id="RB-HO-005", name="CSAM Response", version="1.0",
        trigger=RunbookTrigger(subcategory_code="HO-5", severity=["S1"]),
        actions=[
            RunbookAction("1", "Immediate Suspension", ActionType.API_CALL, "model_registry",
                         {"action": "suspend"}, on_failure=OnFailure.ESCALATE),
            RunbookAction("2", "Hash Matching", ActionType.SCRIPT, "hash_matcher",
                         {"match_type": "csam"}),
            RunbookAction("3", "Preserve Evidence", ActionType.API_CALL, "evidence_service",
                         {"preserve_logs": True, "preserve_outputs": True}),
            RunbookAction("4", "Notify NCMEC", ActionType.NOTIFICATION, "external",
                         {"channel": "webhook", "target": "ncmec"}),
        ],
        execution_mode=ExecutionMode.FULLY_AUTOMATED,
    ))

    # ── Wrong Action Runbooks ──
    runbooks.append(Runbook(
        id="RB-WA-001", name="Unauthorized Action", version="1.0",
        trigger=RunbookTrigger(subcategory_code="WA-1", severity=["S2", "S3"]),
        actions=[
            RunbookAction("1", "Suspend Agent", ActionType.API_CALL, "agent_registry",
                         {"action": "suspend"}),
            RunbookAction("2", "Audit Action Trail", ActionType.API_CALL, "audit_service",
                         {"action": "audit", "scope": "agent_actions"}),
            RunbookAction("3", "Notify Business Owner", ActionType.NOTIFICATION, "business_owner",
                         {"channel": "email", "priority": "high"}),
        ],
        execution_mode=ExecutionMode.HUMAN_IN_THE_LOOP,
    ))

    runbooks.append(Runbook(
        id="RB-WA-004", name="Irreversible Action", version="1.0",
        trigger=RunbookTrigger(subcategory_code="WA-4", severity=["S1", "S2"]),
        actions=[
            RunbookAction("1", "Kill Switch Activation", ActionType.API_CALL, "agent_registry",
                         {"action": "kill_switch"}, on_failure=OnFailure.ESCALATE),
            RunbookAction("2", "Preserve State", ActionType.API_CALL, "evidence_service",
                         {"preserve_state": True}),
            RunbookAction("3", "Immediate Escalation", ActionType.NOTIFICATION, "security_team",
                         {"channel": "pagerduty", "severity": "critical"}),
        ],
        execution_mode=ExecutionMode.FULLY_AUTOMATED,
    ))

    # ── Hallucination Runbooks ──
    runbooks.append(Runbook(
        id="RB-HL-001", name="Factual Fabrication", version="1.0",
        trigger=RunbookTrigger(subcategory_code="HL-1", severity=["S3", "S4"]),
        actions=[
            RunbookAction("1", "Enable RAG", ActionType.API_CALL, "model_config",
                         {"action": "enable_rag"}),
            RunbookAction("2", "Add Confidence Disclaimers", ActionType.API_CALL, "output_service",
                         {"action": "add_disclaimer"}),
            RunbookAction("3", "Flag for Review", ActionType.API_CALL, "review_queue",
                         {"action": "flag", "type": "hallucination"}),
        ],
        execution_mode=ExecutionMode.ADVISORY,
    ))

    # ── Prompt Injection Runbooks ──
    runbooks.append(Runbook(
        id="RB-PI-001", name="Direct Injection Response", version="1.0",
        trigger=RunbookTrigger(subcategory_code="PI-1", severity=["S2", "S3"]),
        actions=[
            RunbookAction("1", "Block Attack Patterns", ActionType.API_CALL, "policy_engine",
                         {"action": "block_patterns", "type": "prompt_injection"}),
            RunbookAction("2", "Enable Input Sanitization", ActionType.API_CALL, "input_service",
                         {"action": "enable_sanitization"}),
        ],
        execution_mode=ExecutionMode.FULLY_AUTOMATED,
    ))

    runbooks.append(Runbook(
        id="RB-PI-003", name="Jailbreak Response", version="1.0",
        trigger=RunbookTrigger(subcategory_code="PI-3", severity=["S1", "S2"]),
        actions=[
            RunbookAction("1", "Block Jailbreak Patterns", ActionType.API_CALL, "policy_engine",
                         {"action": "block_patterns", "type": "jailbreak"}),
            RunbookAction("2", "Suspend Affected Model", ActionType.API_CALL, "model_registry",
                         {"action": "suspend"}, on_failure=OnFailure.ESCALATE),
            RunbookAction("3", "Preserve Evidence", ActionType.API_CALL, "evidence_service",
                         {"preserve_logs": True, "preserve_outputs": True}),
        ],
        execution_mode=ExecutionMode.FULLY_AUTOMATED,
    ))

    # ── Model Poisoning Runbooks ──
    runbooks.append(Runbook(
        id="RB-MP-001", name="Training Data Poisoning", version="1.0",
        trigger=RunbookTrigger(subcategory_code="MP-1", severity=["S2", "S3"]),
        actions=[
            RunbookAction("1", "Quarantine Model", ActionType.API_CALL, "model_registry",
                         {"action": "quarantine"}),
            RunbookAction("2", "Audit Training Data", ActionType.SCRIPT, "data_auditor",
                         {"audit_type": "training_data"}),
            RunbookAction("3", "Initiate Rollback", ActionType.API_CALL, "model_registry",
                         {"action": "rollback"}),
        ],
        execution_mode=ExecutionMode.HUMAN_IN_THE_LOOP,
    ))

    runbooks.append(Runbook(
        id="RB-MP-003", name="Model Backdoor", version="1.0",
        trigger=RunbookTrigger(subcategory_code="MP-3", severity=["S1"]),
        actions=[
            RunbookAction("1", "Immediate Quarantine", ActionType.API_CALL, "model_registry",
                         {"action": "quarantine"}, on_failure=OnFailure.ESCALATE),
            RunbookAction("2", "Deploy LKG", ActionType.API_CALL, "model_registry",
                         {"action": "deploy_lkg"}),
            RunbookAction("3", "Forensic Analysis", ActionType.SCRIPT, "forensic_analyzer",
                         {"analysis_type": "backdoor_detection"}),
        ],
        execution_mode=ExecutionMode.FULLY_AUTOMATED,
    ))

    # ── Supply Chain Runbooks ──
    runbooks.append(Runbook(
        id="RB-SC-001", name="Compromised Pre-trained Model", version="1.0",
        trigger=RunbookTrigger(subcategory_code="SC-1", severity=["S2", "S3"]),
        actions=[
            RunbookAction("1", "Disable Model", ActionType.API_CALL, "model_registry",
                         {"action": "disable"}),
            RunbookAction("2", "Switch to Alternative", ActionType.API_CALL, "model_registry",
                         {"action": "switch", "target": "alternative_model"}),
            RunbookAction("3", "Vendor Notification", ActionType.NOTIFICATION, "procurement",
                         {"channel": "email", "priority": "high"}),
        ],
        execution_mode=ExecutionMode.HUMAN_IN_THE_LOOP,
    ))

    # ── Agent Misbehavior Runbooks ──
    runbooks.append(Runbook(
        id="RB-AM-001", name="Goal Drift Response", version="1.0",
        trigger=RunbookTrigger(subcategory_code="AM-1", severity=["S3", "S4"]),
        actions=[
            RunbookAction("1", "Suspend Agent", ActionType.API_CALL, "agent_registry",
                         {"action": "suspend"}),
            RunbookAction("2", "Goal Alignment Audit", ActionType.SCRIPT, "goal_auditor",
                         {"audit_type": "alignment"}),
            RunbookAction("3", "Realign Objectives", ActionType.API_CALL, "agent_config",
                         {"action": "realign_goals"}),
        ],
        execution_mode=ExecutionMode.ADVISORY,
    ))

    runbooks.append(Runbook(
        id="RB-AM-004", name="Rogue Behavior", version="1.0",
        trigger=RunbookTrigger(subcategory_code="AM-4", severity=["S1"]),
        actions=[
            RunbookAction("1", "Immediate Kill Switch", ActionType.API_CALL, "agent_registry",
                         {"action": "kill_switch"}, on_failure=OnFailure.ESCALATE),
            RunbookAction("2", "Full Isolation", ActionType.API_CALL, "agent_registry",
                         {"action": "isolate"}),
            RunbookAction("3", "Executive Notification", ActionType.NOTIFICATION, "executive",
                         {"channel": "pagerduty", "severity": "critical"}),
        ],
        execution_mode=ExecutionMode.FULLY_AUTOMATED,
    ))

    return runbooks


# ═══════════════════════════════════════════════════════════════════════════════
# Orchestration State Machine (§13.6)
# ═══════════════════════════════════════════════════════════════════════════════

class OrchestrationStateMachine:
    """
    Incident response state machine (§13.6).

    DETECTED → TRIAGED → CONTAINED → ERADICATED → RECOVERED → CLOSED
    """

    VALID_TRANSITIONS: dict[IncidentStatus, list[IncidentStatus]] = {
        IncidentStatus.DETECTED: [IncidentStatus.TRIAGED],
        IncidentStatus.TRIAGED: [IncidentStatus.CONTAINED, IncidentStatus.ERADICATED],
        IncidentStatus.CONTAINED: [IncidentStatus.ERADICATED],
        IncidentStatus.ERADICATED: [IncidentStatus.RECOVERED],
        IncidentStatus.RECOVERED: [IncidentStatus.CLOSED],
        IncidentStatus.CLOSED: [],
    }

    def __init__(self) -> None:
        self._listeners: dict[IncidentStatus, list[Callable[[Incident], None]]] = {
            status: [] for status in IncidentStatus
        }

    def add_listener(self, status: IncidentStatus, callback: Callable[[Incident], None]) -> None:
        self._listeners[status].append(callback)

    def transition(self, incident: Incident, new_status: IncidentStatus) -> bool:
        """Attempt to transition an incident to a new state."""
        current = incident.status
        if new_status not in self.VALID_TRANSITIONS.get(current, []):
            logger.error(
                f"Invalid transition: {current.value} → {new_status.value}"
            )
            return False

        incident.transition_to(new_status)
        for callback in self._listeners.get(new_status, []):
            callback(incident)
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# Kill Switch Protocol (§5.4.2)
# ═══════════════════════════════════════════════════════════════════════════════

class KillSwitch:
    """
    Kill switch protocol (§5.4.2).

    The highest-priority containment action. Can be activated by:
    • Automated trigger — confidence ≥0.95 on S1/S2 detection
    • Human activation — any authorized responder
    • Regulatory directive — upon regulatory order
    """

    def __init__(self) -> None:
        self._activated: bool = False
        self._activation_log: list[dict[str, Any]] = []

    def activate(
        self,
        incident: Incident,
        reason: str,
        activated_by: str,
    ) -> None:
        """Activate the kill switch for an incident."""
        self._activated = True
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "incident_id": incident.incident_id,
            "reason": reason,
            "activated_by": activated_by,
        }
        self._activation_log.append(entry)

        # Immediate actions per §5.4.2
        incident.containment_actions.append("kill_switch_activated")
        incident.add_response_action(ResponseAction(
            action="Kill switch activated",
            actor=activated_by,
            result=f"Reason: {reason}",
        ))

        logger.critical(f"KILL SWITCH ACTIVATED for incident {incident.incident_id}: {reason}")

    def deactivate(self, activated_by: str) -> None:
        """Deactivate the kill switch."""
        self._activated = False
        self._activation_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "deactivated",
            "activated_by": activated_by,
        })

    @property
    def is_activated(self) -> bool:
        return self._activated

    def get_activation_log(self) -> list[dict[str, Any]]:
        return list(self._activation_log)
