"""Automated response playbooks for agentic AI marketing security layer.

Provides incident response automation, playbook execution,
remediation actions, and escalation workflows.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from threat.detection import Anomaly, ThreatLevel


class PlaybookError(Exception):
    """Base exception for playbook errors."""


class PlaybookExecutionError(PlaybookError):
    """Raised when playbook execution fails."""


class ActionExecutionError(PlaybookError):
    """Raised when action execution fails."""


class PlaybookStatus(str, Enum):
    """Playbook execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class ActionType(str, Enum):
    """Response action types."""

    NOTIFY = "notify"
    BLOCK_IP = "block_ip"
    REVOKE_TOKEN = "revoke_token"
    ISOLATE_HOST = "isolate_host"
    DISABLE_ACCOUNT = "disable_account"
    ROTATE_CREDENTIALS = "rotate_credentials"
    CAPTURE_EVIDENCE = "capture_evidence"
    TRIGGER_SCAN = "trigger_scan"
    UPDATE_FIREWALL = "update_firewall"
    CALL_WEBHOOK = "call_webhook"
    CREATE_TICKET = "create_ticket"
    PAGE_ONCALL = "page_oncall"
    SNAPSHOT_VM = "snapshot_vm"
    KILL_PROCESS = "kill_process"
    CUSTOM = "custom"


@dataclass(frozen=True)
class PlaybookAction:
    """A single action in a playbook."""

    name: str
    action_type: ActionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    timeout: float = 60.0
    retries: int = 0
    continue_on_failure: bool = False
    condition: Optional[str] = None


@dataclass(frozen=True)
class Playbook:
    """Response playbook definition."""

    name: str
    description: str
    triggers: List[str]
    actions: List[PlaybookAction]
    enabled: bool = True
    auto_approve: bool = False
    approval_required: bool = True
    max_execution_time: float = 300.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlaybookExecution:
    """Playbook execution record."""

    id: str
    playbook_name: str
    trigger_event_id: str
    status: PlaybookStatus
    started_at: float
    completed_at: Optional[float] = None
    actions_results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    triggered_by: str = "automated"


class ActionExecutor:
    """Executes response actions."""

    def __init__(self) -> None:
        self._handlers: Dict[ActionType, Callable[..., Any]] = {
            ActionType.NOTIFY: self._handle_notify,
            ActionType.BLOCK_IP: self._handle_block_ip,
            ActionType.REVOKE_TOKEN: self._handle_revoke_token,
            ActionType.ISOLATE_HOST: self._handle_isolate_host,
            ActionType.DISABLE_ACCOUNT: self._handle_disable_account,
            ActionType.ROTATE_CREDENTIALS: self._handle_rotate_credentials,
            ActionType.CAPTURE_EVIDENCE: self._handle_capture_evidence,
            ActionType.TRIGGER_SCAN: self._handle_trigger_scan,
            ActionType.UPDATE_FIREWALL: self._handle_update_firewall,
            ActionType.CALL_WEBHOOK: self._handle_call_webhook,
            ActionType.CREATE_TICKET: self._handle_create_ticket,
            ActionType.PAGE_ONCALL: self._handle_page_oncall,
            ActionType.SNAPSHOT_VM: self._handle_snapshot_vm,
            ActionType.KILL_PROCESS: self._handle_kill_process,
            ActionType.CUSTOM: self._handle_custom,
        }

    async def execute(
        self,
        action: PlaybookAction,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single action."""
        handler = self._handlers.get(action.action_type)
        if not handler:
            raise ActionExecutionError(f"No handler for action type: {action.action_type}")

        try:
            result = await handler(action.parameters, context)
            return {
                "action": action.name,
                "type": action.action_type.value,
                "status": "success",
                "result": result,
                "timestamp": time.time(),
            }
        except Exception as exc:
            return {
                "action": action.name,
                "type": action.action_type.value,
                "status": "failed",
                "error": str(exc),
                "timestamp": time.time(),
            }

    async def _handle_notify(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle notification action."""
        channel = params.get("channel", "slack")
        message = params.get("message", "Security alert triggered")
        return f"Notification sent via {channel}: {message}"

    async def _handle_block_ip(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle IP blocking action."""
        ip = params.get("ip") or context.get("source_ip")
        duration = params.get("duration", 3600)
        return f"Blocked IP {ip} for {duration}s"

    async def _handle_revoke_token(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle token revocation action."""
        token_id = params.get("token_id") or context.get("token_id")
        return f"Revoked token {token_id}"

    async def _handle_isolate_host(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle host isolation action."""
        host_id = params.get("host_id") or context.get("host_id")
        return f"Isolated host {host_id}"

    async def _handle_disable_account(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle account disable action."""
        account_id = params.get("account_id") or context.get("actor_id")
        return f"Disabled account {account_id}"

    async def _handle_rotate_credentials(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle credential rotation action."""
        target = params.get("target") or context.get("target")
        return f"Rotated credentials for {target}"

    async def _handle_capture_evidence(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle evidence capture action."""
        target = params.get("target") or context.get("target")
        return f"Captured evidence for {target}"

    async def _handle_trigger_scan(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle vulnerability scan trigger."""
        target = params.get("target") or context.get("target")
        scan_type = params.get("scan_type", "full")
        return f"Triggered {scan_type} scan on {target}"

    async def _handle_update_firewall(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle firewall update action."""
        rule = params.get("rule", {})
        return f"Updated firewall rule: {rule}"

    async def _handle_call_webhook(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle webhook call action."""
        url = params.get("url", "")
        payload = params.get("payload", {})
        return f"Called webhook {url}"

    async def _handle_create_ticket(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle ticket creation action."""
        title = params.get("title", "Security Incident")
        priority = params.get("priority", "high")
        return f"Created ticket: {title} (priority: {priority})"

    async def _handle_page_oncall(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle on-call paging action."""
        service = params.get("service", "security")
        message = params.get("message", "Security incident requires attention")
        return f"Paged on-call for {service}: {message}"

    async def _handle_snapshot_vm(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle VM snapshot action."""
        vm_id = params.get("vm_id") or context.get("vm_id")
        return f"Created snapshot of VM {vm_id}"

    async def _handle_kill_process(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle process kill action."""
        process_id = params.get("process_id") or context.get("process_id")
        host = params.get("host") or context.get("host")
        return f"Killed process {process_id} on {host}"

    async def _handle_custom(self, params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle custom action."""
        command = params.get("command", "")
        return f"Executed custom action: {command}"


class PlaybookEngine:
    """Main playbook execution engine."""

    def __init__(self) -> None:
        self._playbooks: Dict[str, Playbook] = {}
        self._executions: Dict[str, PlaybookExecution] = {}
        self._executor = ActionExecutor()

    def register_playbook(self, playbook: Playbook) -> None:
        """Register a playbook."""
        self._playbooks[playbook.name] = playbook

    def get_playbook(self, name: str) -> Optional[Playbook]:
        """Get a playbook by name."""
        return self._playbooks.get(name)

    async def trigger_playbook(
        self,
        playbook_name: str,
        trigger_event_id: str,
        context: Dict[str, Any],
    ) -> PlaybookExecution:
        """Trigger a playbook execution."""
        playbook = self._playbooks.get(playbook_name)
        if not playbook:
            raise PlaybookError(f"Playbook '{playbook_name}' not found")

        if not playbook.enabled:
            raise PlaybookError(f"Playbook '{playbook_name}' is disabled")

        execution_id = self._generate_execution_id()
        execution = PlaybookExecution(
            id=execution_id,
            playbook_name=playbook_name,
            trigger_event_id=trigger_event_id,
            status=PlaybookStatus.RUNNING,
            started_at=time.time(),
        )
        self._executions[execution_id] = execution

        try:
            results: List[Dict[str, Any]] = []
            for action in playbook.actions:
                if action.condition and not self._evaluate_condition(action.condition, context):
                    continue

                result = await self._executor.execute(action, context)
                results.append(result)

                if result["status"] == "failed" and not action.continue_on_failure:
                    execution = PlaybookExecution(
                        id=execution_id,
                        playbook_name=playbook_name,
                        trigger_event_id=trigger_event_id,
                        status=PlaybookStatus.FAILED,
                        started_at=execution.started_at,
                        completed_at=time.time(),
                        actions_results=results,
                        error=result.get("error"),
                    )
                    self._executions[execution_id] = execution
                    return execution

            execution = PlaybookExecution(
                id=execution_id,
                playbook_name=playbook_name,
                trigger_event_id=trigger_event_id,
                status=PlaybookStatus.COMPLETED,
                started_at=execution.started_at,
                completed_at=time.time(),
                actions_results=results,
            )
            self._executions[execution_id] = execution
            return execution

        except Exception as exc:
            execution = PlaybookExecution(
                id=execution_id,
                playbook_name=playbook_name,
                trigger_event_id=trigger_event_id,
                status=PlaybookStatus.FAILED,
                started_at=execution.started_at,
                completed_at=time.time(),
                error=str(exc),
            )
            self._executions[execution_id] = execution
            return execution

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression."""
        try:
            return bool(eval(condition, {"__builtins__": {}}, context))
        except Exception:
            return True

    @staticmethod
    def _generate_execution_id() -> str:
        """Generate a unique execution ID."""
        return hashlib.sha256(
            f"{time.time()}-{id(object())}".encode()
        ).hexdigest()[:16]

    def get_execution(self, execution_id: str) -> Optional[PlaybookExecution]:
        """Get an execution by ID."""
        return self._executions.get(execution_id)

    def list_executions(
        self,
        playbook_name: Optional[str] = None,
        status: Optional[PlaybookStatus] = None,
    ) -> List[PlaybookExecution]:
        """List executions with optional filtering."""
        executions = list(self._executions.values())
        if playbook_name:
            executions = [e for e in executions if e.playbook_name == playbook_name]
        if status:
            executions = [e for e in executions if e.status == status]
        return executions


class IncidentResponseOrchestrator:
    """Orchestrates incident response based on detected threats."""

    def __init__(self, playbook_engine: PlaybookEngine) -> None:
        self.playbook_engine = playbook_engine
        self._escalation_matrix: Dict[ThreatLevel, List[str]] = {
            ThreatLevel.LOW: ["notify"],
            ThreatLevel.MEDIUM: ["notify", "create_ticket"],
            ThreatLevel.HIGH: ["notify", "create_ticket", "page_oncall"],
            ThreatLevel.CRITICAL: ["notify", "create_ticket", "page_oncall", "isolate"],
        }

    async def handle_anomaly(self, anomaly: Anomaly) -> Optional[PlaybookExecution]:
        """Handle a detected anomaly."""
        response_actions = self._escalation_matrix.get(anomaly.threat_level, ["notify"])

        for playbook in self.playbook_engine._playbooks.values():
            if anomaly.anomaly_type.value in playbook.triggers:
                context = {
                    "anomaly_id": anomaly.id,
                    "entity_id": anomaly.entity_id,
                    "threat_level": anomaly.threat_level.value,
                    "anomaly_type": anomaly.anomaly_type.value,
                    "evidence": anomaly.evidence,
                }
                return await self.playbook_engine.trigger_playbook(
                    playbook.name,
                    anomaly.id,
                    context,
                )

        return None

    def set_escalation_matrix(
        self,
        matrix: Dict[ThreatLevel, List[str]],
    ) -> None:
        """Set the escalation matrix."""
        self._escalation_matrix = matrix
