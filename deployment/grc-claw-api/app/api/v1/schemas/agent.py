"""Agent-related schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Agent type."""

    MODEL = "model"
    AGENT = "agent"
    PIPELINE = "pipeline"
    ENDPOINT = "endpoint"


class AgentFramework(str, Enum):
    """Agent framework."""

    LANGCHAIN = "langchain"
    AUTOGEN = "autogen"
    CREWAI = "crewai"
    CUSTOM = "custom"
    MCP_SERVER = "mcp-server"


class LifecycleStage(str, Enum):
    """Agent lifecycle stage."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"
    QUARANTINED = "quarantined"


class RiskTier(str, Enum):
    """Agent risk tier."""

    PROHIBITED = "prohibited"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class AgentCapability(BaseModel):
    """Agent capability."""

    name: str
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)
    resource_scope: str | None = None


class AgentIdentity(BaseModel):
    """Agent identity information."""

    spiffe_id: str | None = None
    mtls_cert: str | None = None
    cert_expiry: datetime | None = None


class TrustScore(BaseModel):
    """Agent trust score."""

    value: int = Field(..., ge=0, le=100)
    grade: str
    last_evaluated: datetime | None = None


class AgentBase(BaseModel):
    """Base agent attributes."""

    name: str
    type: AgentType
    framework: AgentFramework
    owner: str
    risk_tier: RiskTier
    capabilities: list[AgentCapability] = Field(default_factory=list)


class AgentCreate(AgentBase):
    """Register agent request."""

    pass


class AgentUpdate(BaseModel):
    """Update agent request."""

    name: str | None = None
    lifecycle_stage: LifecycleStage | None = None
    risk_tier: RiskTier | None = None
    capabilities: list[AgentCapability] | None = None


class AgentInDB(AgentBase):
    """Agent as stored in database."""

    id: str
    lifecycle_stage: LifecycleStage
    identity: AgentIdentity | None = None
    trust_score: TrustScore | None = None
    policy_bindings: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentResponse(AgentInDB):
    """Agent response model."""

    pass


class UpdateTrustScoreRequest(BaseModel):
    """Update agent trust score request."""

    value: int = Field(..., ge=0, le=100)
    grade: str
    reason: str


class BindPolicyRequest(BaseModel):
    """Bind policies to agent request."""

    policy_ids: list[str]


class AgentFilter(BaseModel):
    """Agent list filter parameters."""

    type: AgentType | None = None
    framework: AgentFramework | None = None
    lifecycle_stage: LifecycleStage | None = None
    risk_tier: RiskTier | None = None
    trust_score_min: int | None = None
