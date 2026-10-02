"""Governance and compliance layer for agentic AI marketing projects.

Provides agent governance framework, policy enforcement engine, compliance
monitoring, audit trail, data privacy, content compliance, and brand safety.
"""

from .agent.identity import AgentIdentity, DIDDocument
from .agent.lifecycle import AgentLifecycle, LifecycleState
from .agent.trust import TrustScore, TrustEngine
from .agent.capability import CapabilityToken, CapabilityRegistry
from .policy.engine import PolicyEngine, PolicyDecision
from .compliance.monitor import ComplianceMonitor
from .audit.trail import AuditTrail, AuditEntry
from .privacy.consent import ConsentManager
from .content.safety import ContentSafetyChecker

__version__ = "1.0.0"

__all__ = [
    "AgentIdentity",
    "DIDDocument",
    "AgentLifecycle",
    "LifecycleState",
    "TrustScore",
    "TrustEngine",
    "CapabilityToken",
    "CapabilityRegistry",
    "PolicyEngine",
    "PolicyDecision",
    "ComplianceMonitor",
    "AuditTrail",
    "AuditEntry",
    "ConsentManager",
    "ContentSafetyChecker",
]
