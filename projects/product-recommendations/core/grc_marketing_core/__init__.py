"""GRC Marketing Core — Grand Unified Architecture core library.

This package provides the foundational building blocks for all standalone
agentic AI marketing projects built on the GRC_Claw platform.

Modules:
    agent: Agent framework (BaseAgent, AgentOrchestrator, Planner-Executor-Critic)
    governance: Policy engine (OPA/Rego) and Merkle-chain audit trail
    monitoring: OpenTelemetry tracing and Prometheus metrics
    security: OAuth2/OIDC auth, SPIFFE identity, AES-256-GCM encryption
    data: CDP integration and identity resolution
    integration: Connector framework and MCP support
    config: Pydantic settings and feature flags
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Ahmed Hassan"
__all__ = [
    "__version__",
    "__author__",
    # Agent
    "BaseAgent",
    "AgentOrchestrator",
    "AgentTool",
    "AgentContext",
    "AgentResult",
    "PlanStep",
    "ExecutionResult",
    "CriticFeedback",
    "MemoryManager",
    "ConversationMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "EpisodicMemory",
    # Governance
    "PolicyEngine",
    "PolicyDecision",
    "AuditTrail",
    "AuditEntry",
    # Monitoring
    "TracingManager",
    "MetricsManager",
    # Security
    "AuthManager",
    "EncryptionManager",
    "TokenClaims",
    # Data
    "CDPClient",
    "IdentityResolver",
    "CustomerProfile",
    # Integration
    "ConnectorRegistry",
    "BaseConnector",
    "MCPClient",
    # Config
    "Settings",
    "FeatureFlags",
    "get_settings",
    "get_feature_flags",
]

# Agent
from .agent.base import AgentContext, AgentOrchestrator, AgentResult, AgentTool, BaseAgent
from .agent.memory import (
    ConversationMemory,
    EpisodicMemory,
    MemoryManager,
    ProceduralMemory,
    SemanticMemory,
)
from .agent.planner import CriticFeedback, ExecutionResult, PlanStep

# Config
from .config.feature_flags import FeatureFlags, get_feature_flags
from .config.settings import Settings, get_settings

# Data
from .data.cdp import CDPClient
from .data.identity import CustomerProfile, IdentityResolver

# Governance
from .governance.audit import AuditEntry, AuditTrail
from .governance.policy import PolicyDecision, PolicyEngine

# Integration
from .integration.connectors import BaseConnector, ConnectorRegistry
from .integration.mcp import MCPClient

# Monitoring
from .monitoring.metrics import MetricsManager
from .monitoring.tracing import TracingManager

# Security
from .security.auth import AuthManager, TokenClaims
from .security.encryption import EncryptionManager
