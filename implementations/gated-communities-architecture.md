# Multi-Tier Gated Communities Moderation — System Architecture

**Version:** 1.0  
**Date:** 2026-10-02  
**Status:** Architecture Reference  
**Owner:** GRC_Claw Architecture Team  
**References:** [Governance Layer](./governance-layer.md) · [Core Agent Framework](./core-agent-framework.md) · [Grand Unified Architecture](./grand-unified-architecture.md) · [GRC_Claw Architecture](../ARCHITECTURE.md)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Agent Architecture](#3-agent-architecture)
4. [API Design](#4-api-design)
5. [Data Models](#5-data-models)
6. [Integration Patterns](#6-integration-patterns)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Security & Governance](#8-security--governance)
9. [Observability](#9-observability)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. Executive Summary

### 1.1 Problem Statement

Online communities face a fundamental tension: open participation drives growth, but unmoderated spaces degrade through spam, harassment, and low-quality content. Single-tier moderation (either fully open or fully closed) fails to match the nuanced reality of community dynamics — long-time contributors deserve more trust than newcomers, and different spaces within a community need different rules.

### 1.2 Solution: Multi-Tier Gated Moderation

A tiered access system where community members progress through trust levels, each with distinct permissions, content visibility, and moderation requirements. AI agents handle routine moderation at scale while escalating edge cases to human moderators.

### 1.3 Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Progressive Trust** | Members earn privileges through sustained positive participation |
| **Tier-Isolated Visibility** | Content in higher tiers is invisible to lower-tier members |
| **AI-First Moderation** | Agents handle 95%+ of decisions; humans see only escalations |
| **Reputation Portability** | Reputation scores carry across communities within the platform |
| **Fail-Closed Security** | Any system failure defaults to denying access |
| **Audit Everything** | Every moderation decision is logged with full context |
| **Composable Agents** | Each agent is standalone, testable, and replaceable |

---

## 2. System Overview

### 2.1 High-Level Architecture

```mermaid
graph TB
    subgraph CLIENTS["Client Layer"]
        WEB[Web Dashboard]
        API[REST API]
        WS[WebSocket Stream]
        MOB[Mobile App]
    end

    subgraph EDGE["Edge Layer"]
        GW[API Gateway<br/>Kong / AWS API Gateway]
        AUTH[Auth Service<br/>OAuth 2.1 + OIDC]
        RATE[Rate Limiter<br/>Redis-backed]
    end

    subgraph MODERATION["Moderation Service"]
        TIER[Tier Manager]
        ACCESS[Access Controller]
        QUEUE[Moderation Queue]
        HEALTH[Health Scorer]
        ESCALATE[Escalation Handler]
        REP[Reputation Tracker]
    end

    subgraph CORE["Shared Core Library — @grc/core"]
        AF[Agent Framework<br/>LangChain DeepAgents]
        GOV[Governance Layer<br/>GRC_Claw]
        MON[Monitoring<br/>OpenTelemetry]
        SEC[Security<br/>DID + Policy Firewall]
        DATA[Data Layer<br/>PostgreSQL + Redis]
        INT[Integration Hub<br/>MCP + A2A]
    end

    subgraph INFRA["Shared Infrastructure"]
        KAFKA[Apache Kafka<br/>Event Backbone]
        REDIS[Redis Cluster<br/>Cache + Feature Store]
        PG[PostgreSQL 16<br/>Transactional DB]
        K8S[Kubernetes<br/>EKS / GKE]
    end

    subgraph EXTERNAL["External Systems"]
        LLM[LLM Providers<br/>Anthropic / OpenAI]
        NOTIF[Notification Service<br/>Email / Push]
        AUDIT[Audit Log<br/>Immutable Storage]
    end

    CLIENTS --> EDGE
    EDGE --> MODERATION
    MODERATION --> CORE
    CORE --> INFRA
    CORE --> EXTERNAL
```

### 2.2 Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant GW as API Gateway
    participant AC as Access Controller
    participant TM as Tier Manager
    participant MQ as Moderation Queue
    participant HA as Health Scorer
    participant DB as Database

    C->>GW: POST /content (submit post)
    GW->>AC: Authorize request
    AC->>TM: Get member tier
    TM->>DB: Fetch tier permissions
    DB-->>TM: Tier config
    TM-->>AC: Tier + permissions
    AC->>AC: Check rate limits
    AC->>MQ: Submit for moderation
    MQ->>HA: Score content health
    HA-->>MQ: Health score + flags
    alt Score >= threshold
        MQ->>DB: Publish content
        MQ-->>C: 201 Created
    else Score < threshold
        MQ->>DB: Queue for review
        MQ-->>C: 202 Pending Review
    end
```

### 2.3 Event-Driven Flow

```mermaid
graph LR
    subgraph PRODUCERS["Event Producers"]
        MEMBER[Member Events]
        CONTENT[Content Events]
        MOD[Moderation Events]
        TIER[Tier Change Events]
    end

    subgraph KAFKA["Apache Kafka"]
        T1[member-events]
        T2[content-events]
        T3[moderation-events]
        T4[tier-events]
        T5[reputation-events]
    end

    subgraph CONSUMERS["Event Consumers"]
        REP[Reputation Tracker]
        NOTIF[Notification Service]
        ANALYTICS[Analytics Pipeline]
        AUDIT[Audit Logger]
        ESCALATE[Escalation Handler]
    end

    MEMBER --> T1
    CONTENT --> T2
    MOD --> T3
    TIER --> T4
    T1 --> REP
    T2 --> REP
    T3 --> REP
    T4 --> REP
    REP --> T5
    T5 --> NOTIF
    T5 --> ANALYTICS
    T3 --> AUDIT
    T3 --> ESCALATE
```

---

## 3. Agent Architecture

### 3.1 Agent Overview

Six specialized agents form the moderation pipeline. Each agent is a standalone LangChain DeepAgents harness with its own system prompt, tool set, and governance policies.

```mermaid
graph TB
    subgraph AGENTS["Moderation Agent Fleet"]
        TM[Tier Manager<br/>🎯 Tier assignment & promotion]
        AC[Access Controller<br/>🔐 Permission enforcement]
        MQ[Moderation Queue<br/>📋 Content triage]
        HS[Health Scorer<br/>📊 Community health]
        EH[Escalation Handler<br/>🚨 Human handoff]
        RT[Reputation Tracker<br/>⭐ Score tracking]
    end

    subgraph SHARED["Shared Agent Infrastructure"]
        TOOLS[Tool Registry]
        MEM[Agent Memory<br/>Cognee]
        GOV[Governance Guardrails]
        COST[Cost Tracker]
    end

    TM --> TOOLS
    AC --> TOOLS
    MQ --> TOOLS
    HS --> TOOLS
    EH --> TOOLS
    RT --> TOOLS

    TM --> MEM
    AC --> MEM
    MQ --> MEM
    HS --> MEM
    EH --> MEM
    RT --> MEM

    TM --> GOV
    AC --> GOV
    MQ --> GOV
    HS --> GOV
    EH --> GOV
    RT --> GOV

    TM --> COST
    AC --> COST
    MQ --> COST
    HS --> COST
    EH --> COST
    RT --> COST
```

### 3.2 Tier Manager Agent

**Purpose:** Assigns members to tiers, evaluates promotion/demotion criteria, and manages tier configuration.

**Responsibilities:**
- Evaluate member activity against tier promotion criteria
- Process tier upgrade/downgrade decisions
- Manage tier-specific rule sets
- Handle tier transfer requests
- Enforce tier cooling-off periods

**Tools:**
- `get_member_activity` — Fetch activity metrics for a member
- `evaluate_tier_criteria` — Check if member meets promotion criteria
- `assign_tier` — Assign member to a tier
- `get_tier_config` — Retrieve tier configuration
- `update_tier_config` — Modify tier settings (admin only)

**Governance Policies:**
- Tier changes require 2-agent consensus for downgrades
- All tier assignments logged with reasoning
- Maximum 1 tier change per member per 24h (configurable)

```python
# agents/tier_manager.py
from langchain_deepagents import Agent
from grc_core.governance import policy_enforced

class TierManagerAgent(Agent):
    """Manages tier assignments and promotions for community members."""
    
    system_prompt = """You are the Tier Manager for a gated community platform.
    Your role is to evaluate member activity and assign appropriate trust tiers.
    
    Tiers (lowest to highest):
    - NEW: New members, read-only in public spaces
    - ACTIVE: Can post in public spaces
    - TRUSTED: Can post in restricted spaces, reduced moderation
    - MODERATOR: Can moderate content, manage lower tiers
    - ADMIN: Full community control
    
    Always evaluate fairly. Document your reasoning. When uncertain, escalate."""
    
    @policy_enforced("tier.change")
    async def evaluate_promotion(self, member_id: str, community_id: str) -> TierDecision:
        activity = await self.tools.get_member_activity(member_id, community_id)
        current_tier = await self.tools.get_current_tier(member_id, community_id)
        criteria = await self.tools.get_tier_criteria(community_id, current_tier.next_tier)
        
        decision = self.llm.decide(
            prompt=TIER_EVAL_PROMPT,
            context={"activity": activity, "criteria": criteria, "current_tier": current_tier},
            output_schema=TierDecision
        )
        
        if decision.action == "promote":
            await self.tools.assign_tier(member_id, community_id, decision.target_tier)
            await self.emit_event("tier.promoted", {"member_id": member_id, "tier": decision.target_tier})
        
        return decision
```

### 3.3 Access Controller Agent

**Purpose:** Enforces permission checks for all community operations — the gatekeeper.

**Responsibilities:**
- Validate member permissions before any operation
- Enforce tier-based content visibility
- Check rate limits per tier
- Validate content format requirements
- Handle access denial with clear reasoning

**Tools:**
- `check_permission` — Verify if member has a specific permission
- `get_member_tier` — Get current tier for member in community
- `get_tier_permissions` — List all permissions for a tier
- `check_rate_limit` — Verify rate limit compliance
- `log_access_attempt` — Record all access attempts (granted and denied)

**Governance Policies:**
- Zero-trust: every request validated independently
- Fail-closed: any error results in denial
- All denials logged with full context

```python
# agents/access_controller.py
class AccessControllerAgent(Agent):
    """Enforces access control for all community operations."""
    
    system_prompt = """You are the Access Controller. Every request to community
    resources must pass through you. You enforce tier-based permissions,
    rate limits, and content policies.
    
    When denying access, always provide clear, actionable reasoning.
    When granting access, log the decision for audit purposes."""
    
    @policy_enforced("access.check")
    async def authorize(self, request: AccessRequest) -> AccessDecision:
        tier = await self.tools.get_member_tier(request.member_id, request.community_id)
        permissions = await self.tools.get_tier_permissions(tier)
        
        if request.required_permission not in permissions:
            await self.tools.log_access_attempt(request, granted=False, reason="insufficient_tier")
            return AccessDecision(granted=False, reason=f"Requires {request.required_permission}, tier {tier} lacks it")
        
        rate_ok = await self.tools.check_rate_limit(request.member_id, request.community_id, tier)
        if not rate_ok:
            await self.tools.log_access_attempt(request, granted=False, reason="rate_limited")
            return AccessDecision(granted=False, reason="Rate limit exceeded")
        
        await self.tools.log_access_attempt(request, granted=True)
        return AccessDecision(granted=True, tier=tier)
```

### 3.4 Moderation Queue Agent

**Purpose:** Triage incoming content, route to appropriate moderation path, and manage the review pipeline.

**Responsibilities:**
- Classify content by type and risk level
- Route low-risk content to auto-approval
- Queue medium-risk content for AI review
- Escalate high-risk content to human moderators
- Manage queue priority and SLA tracking

**Tools:**
- `classify_content` — Determine content category and risk
- `submit_for_review` — Add content to moderation queue
- `get_queue_status` — Check queue depth and SLA
- `auto_approve` — Approve content meeting auto-approve criteria
- `escalate_to_human` — Route to human moderator
- `get_moderation_history` — Fetch past decisions for context

**Governance Policies:**
- All decisions include confidence scores
- Confidence < 0.85 always escalates to human
- Queue SLA: 95% of items processed within 5 minutes

```python
# agents/moderation_queue.py
class ModerationQueueAgent(Agent):
    """Manages content moderation pipeline and routing."""
    
    system_prompt = """You are the Moderation Queue manager. You triage content
    submitted to the community and route it to the appropriate moderation path.
    
    Auto-approve: High-confidence safe content (confidence > 0.95)
    AI Review: Medium-confidence content (0.70 < confidence < 0.95)
    Human Review: Low-confidence or high-risk content (confidence < 0.70)
    
    Always prioritize member safety over engagement metrics."""
    
    @policy_enforced("content.moderate")
    async def moderate(self, content: Content) -> ModerationResult:
        classification = await self.tools.classify_content(content)
        health_score = await self.health_scorer.score(content)
        
        if classification.risk_level == "low" and health_score > 0.95:
            await self.tools.auto_approve(content.id)
            return ModerationResult(action="approved", auto=True, confidence=health_score)
        
        if classification.risk_level == "high" or health_score < 0.70:
            await self.tools.escalate_to_human(content.id, priority="high")
            return ModerationResult(action="escalated", reason="high_risk")
        
        await self.tools.submit_for_review(content.id, priority="normal")
        return ModerationResult(action="queued", queue_position=await self.tools.get_queue_position(content.id))
```

### 3.5 Health Scorer Agent

**Purpose:** Computes community health scores and content quality metrics.

**Responsibilities:**
- Score individual content pieces for quality and safety
- Compute aggregate community health scores
- Track health trends over time
- Generate health reports for community admins
- Flag communities in decline

**Tools:**
- `score_content` — Score a single content piece
- `compute_community_health` — Aggregate health score for community
- `get_health_trends` — Historical health data
- `generate_health_report` — Create admin-facing report
- `flag_at_risk_community` — Alert for communities needing attention

**Scoring Dimensions:**
| Dimension | Weight | Description |
|-----------|--------|-------------|
| Toxicity | 30% | Hate speech, harassment, threats |
| Spam | 25% | Repetitive, promotional, low-value |
| Relevance | 20% | On-topic, constructive contribution |
| Engagement | 15% | Positive community interaction |
| Authenticity | 10% | Genuine vs. bot/sockpuppet |

```python
# agents/health_scorer.py
class HealthScorerAgent(Agent):
    """Scores content and community health."""
    
    system_prompt = """You are the Health Scorer. You evaluate content quality
    and community health across multiple dimensions.
    
    Score range: 0.0 (toxic/harmful) to 1.0 (excellent/constructive)
    Always explain your scoring with specific evidence."""
    
    @policy_enforced("health.score")
    async def score_content(self, content: Content) -> HealthScore:
        dimensions = {
            "toxicity": await self.score_toxicity(content),
            "spam": await self.score_spam(content),
            "relevance": await self.score_relevance(content),
            "engagement": await self.score_engagement(content),
            "authenticity": await self.score_authenticity(content),
        }
        
        weights = {"toxicity": 0.30, "spam": 0.25, "relevance": 0.20, "engagement": 0.15, "authenticity": 0.10}
        overall = sum(dimensions[k] * weights[k] for k in dimensions)
        
        return HealthScore(overall=overall, dimensions=dimensions, evidence=self.collect_evidence(content))
```

### 3.6 Escalation Handler Agent

**Purpose:** Manages the human escalation pipeline — when AI agents can't or shouldn't decide.

**Responsibilities:**
- Receive escalated content/decisions from other agents
- Route to appropriate human moderator based on expertise
- Track escalation SLA and response times
- Learn from human decisions to improve AI accuracy
- Handle urgent escalations (safety, legal) with priority

**Tools:**
- `receive_escalation` — Accept escalated item
- `route_to_moderator` — Assign to human moderator
- `track_sla` — Monitor escalation response times
- `record_resolution` — Log human decision
- `update_ai_model` — Feed human decisions back for learning

**Escalation Triggers:**
- Content flagged as potentially illegal
- Member disputes a moderation decision
- AI confidence below threshold
- High-profile member involved
- Pattern of coordinated abuse detected

```python
# agents/escalation_handler.py
class EscalationHandlerAgent(Agent):
    """Manages human escalation pipeline."""
    
    system_prompt = """You are the Escalation Handler. You manage cases that
    require human judgment — disputes, edge cases, and high-risk content.
    
    Prioritize: Safety > Legal > Dispute Resolution > Quality
    Always meet SLA targets. Learn from every human decision."""
    
    @policy_enforced("escalation.handle")
    async def handle(self, escalation: Escalation) -> EscalationResult:
        moderator = await self.tools.route_to_moderator(escalation)
        
        if escalation.priority == "urgent":
            await self.notify_oncall_moderator(moderator)
        
        await self.tools.track_sla(escalation.id, priority=escalation.priority)
        
        return EscalationResult(
            escalation_id=escalation.id,
            assigned_moderator=moderator,
            sla_deadline=self.compute_sla(escalation.priority),
            status="pending_human"
        )
```

### 3.7 Reputation Tracker Agent

**Purpose:** Maintains reputation scores for members across communities.

**Responsibilities:**
- Track reputation scores per member per community
- Process reputation events (positive and negative)
- Compute cross-community reputation
- Handle reputation disputes
- Generate reputation reports

**Reputation Events:**
| Event | Points | Source |
|-------|--------|--------|
| Content approved | +1 | Auto |
| Content featured | +5 | Human |
| Helpful flag | +2 | Peer |
| Content rejected | -3 | Auto/Human |
| Warning issued | -10 | Human |
| Temporary ban | -25 | Human |
| Tier promotion | +15 | System |

```python
# agents/reputation_tracker.py
class ReputationTrackerAgent(Agent):
    """Tracks and manages member reputation scores."""
    
    system_prompt = """You are the Reputation Tracker. You maintain reputation
    scores that reflect member trustworthiness and contribution quality.
    
    Reputation is community-specific but portable across the platform.
    Always apply reputation changes consistently and transparently."""
    
    @policy_enforced("reputation.update")
    async def process_event(self, event: ReputationEvent) -> ReputationScore:
        current = await self.tools.get_reputation(event.member_id, event.community_id)
        new_score = max(0, min(100, current.score + event.points))
        
        await self.tools.update_reputation(event.member_id, event.community_id, new_score)
        
        if new_score < 20:
            await self.emit_event("reputation.at_risk", {"member_id": event.member_id, "score": new_score})
        
        return ReputationScore(member_id=event.member_id, community_id=event.community_id, score=new_score, delta=event.points)
```

---

## 4. API Design

### 4.1 REST API Endpoints

**Base URL:** `/api/v1`

#### Community Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/communities` | Create a new community | Admin |
| `GET` | `/communities` | List communities (paginated) | Public |
| `GET` | `/communities/{id}` | Get community details | Member |
| `PATCH` | `/communities/{id}` | Update community settings | Admin |
| `DELETE` | `/communities/{id}` | Delete community (soft) | Admin |
| `GET` | `/communities/{id}/health` | Get community health score | Member |
| `GET` | `/communities/{id}/stats` | Get community statistics | Member |

#### Tier Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/communities/{id}/tiers` | Create a new tier | Admin |
| `GET` | `/communities/{id}/tiers` | List all tiers | Member |
| `PATCH` | `/tiers/{id}` | Update tier configuration | Admin |
| `DELETE` | `/tiers/{id}` | Delete a tier | Admin |
| `POST` | `/tiers/{id}/promote` | Promote member to tier | System |
| `POST` | `/tiers/{id}/demote` | Demote member from tier | System |

#### Member Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/communities/{id}/members` | Add member to community | Admin |
| `GET` | `/communities/{id}/members` | List members (paginated) | Member |
| `GET` | `/members/{id}` | Get member profile | Member |
| `PATCH` | `/members/{id}` | Update member profile | Self/Admin |
| `DELETE` | `/members/{id}` | Remove member from community | Admin |
| `GET` | `/members/{id}/activity` | Get member activity history | Self/Admin |
| `GET` | `/members/{id}/reputation` | Get reputation score | Member |

#### Content & Moderation

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/content` | Submit content for moderation | Member |
| `GET` | `/content/{id}` | Get content by ID | Tier-based |
| `PATCH` | `/content/{id}` | Edit content | Owner/Admin |
| `DELETE` | `/content/{id}` | Delete content | Owner/Admin |
| `GET` | `/moderation/queue` | Get moderation queue | Moderator+ |
| `POST` | `/moderation/{id}/approve` | Approve content | Moderator+ |
| `POST` | `/moderation/{id}/reject` | Reject content | Moderator+ |
| `POST` | `/moderation/{id}/escalate` | Escalate to human | Moderator+ |
| `GET` | `/moderation/history` | Get moderation history | Moderator+ |

#### Access Control

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/access/check` | Check member permission | System |
| `POST` | `/access/grant` | Grant permission to member | Admin |
| `POST` | `/access/revoke` | Revoke permission from member | Admin |
| `GET` | `/access/audit` | Get access audit log | Admin |

#### Escalation

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/escalations` | Create escalation | System |
| `GET` | `/escalations` | List escalations | Moderator+ |
| `GET` | `/escalations/{id}` | Get escalation details | Moderator+ |
| `POST` | `/escalations/{id}/resolve` | Resolve escalation | Moderator+ |
| `POST` | `/escalations/{id}/reassign` | Reassign escalation | Admin |

#### Reputation

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/reputation/leaderboard` | Get reputation leaderboard | Member |
| `GET` | `/reputation/history/{member_id}` | Get reputation history | Self/Admin |
| `POST` | `/reputation/adjust` | Manually adjust reputation | Admin |

**Total: 41 endpoints**

### 4.2 WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `content.new` | Server → Client | New content submitted |
| `content.moderated` | Server → Client | Content moderation result |
| `tier.changed` | Server → Client | Member tier changed |
| `escalation.created` | Server → Client | New escalation |
| `escalation.resolved` | Server → Client | Escalation resolved |
| `reputation.updated` | Server → Client | Reputation score changed |
| `health.alert` | Server → Client | Community health alert |

### 4.3 Request/Response Examples

#### Create Community

```http
POST /api/v1/communities
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "AI Builders Hub",
  "description": "A community for AI builders and enthusiasts",
  "slug": "ai-builders-hub",
  "visibility": "private",
  "default_tier": "new",
  "moderation": {
    "auto_approve_threshold": 0.95,
    "escalation_threshold": 0.70,
    "require_approval_for": ["new"]
  }
}
```

**Response:**
```json
{
  "id": "cm_abc123",
  "name": "AI Builders Hub",
  "slug": "ai-builders-hub",
  "visibility": "private",
  "default_tier": "new",
  "created_at": "2026-10-02T10:00:00Z",
  "health_score": 1.0,
  "member_count": 1,
  "tier_count": 5
}
```

#### Submit Content

```http
POST /api/v1/content
Authorization: Bearer <token>
Content-Type: application/json

{
  "community_id": "cm_abc123",
  "type": "post",
  "title": "Best practices for RAG pipelines",
  "body": "Here are my findings from building RAG systems...",
  "tier": "public"
}
```

**Response:**
```json
{
  "id": "ct_xyz789",
  "status": "pending_moderation",
  "moderation": {
    "queue_position": 3,
    "estimated_review_time": "2m",
    "health_score": 0.92,
    "auto_approved": false
  },
  "submitted_at": "2026-10-02T10:05:00Z"
}
```

---

## 5. Data Models

### 5.1 Entity Relationship Diagram

```mermaid
erDiagram
    COMMUNITY ||--o{ TIER : has
    COMMUNITY ||--o{ MEMBER : contains
    COMMUNITY ||--o{ CONTENT : hosts
    TIER ||--o{ MEMBER : assigns
    MEMBER ||--o{ CONTENT : creates
    MEMBER ||--o{ REPUTATION_SCORE : has
    CONTENT ||--o{ MODERATION_ACTION : receives
    MODERATION_ACTION ||--o{ ESCALATION : triggers
    MEMBER ||--o{ MODERATION_ACTION : performs
    MEMBER ||--o{ ESCALATION : handles

    COMMUNITY {
        uuid id PK
        string name
        string slug UK
        string description
        enum visibility
        uuid default_tier_id FK
        jsonb settings
        float health_score
        timestamp created_at
        timestamp updated_at
        boolean deleted
    }

    TIER {
        uuid id PK
        uuid community_id FK
        string name
        int level
        jsonb permissions
        jsonb criteria
        int member_count
        timestamp created_at
    }

    MEMBER {
        uuid id PK
        uuid community_id FK
        uuid user_id
        uuid tier_id FK
        enum status
        timestamp joined_at
        timestamp last_active_at
        jsonb metadata
    }

    CONTENT {
        uuid id PK
        uuid community_id FK
        uuid author_id FK
        enum type
        string title
        text body
        enum status
        float health_score
        jsonb moderation_result
        timestamp created_at
        timestamp moderated_at
    }

    MODERATION_ACTION {
        uuid id PK
        uuid content_id FK
        uuid moderator_id FK
        enum action
        string reason
        float confidence
        jsonb evidence
        timestamp created_at
    }

    REPUTATION_SCORE {
        uuid id PK
        uuid member_id FK
        uuid community_id FK
        int score
        int total_positive
        int total_negative
        jsonb history
        timestamp updated_at
    }

    ESCALATION {
        uuid id PK
        uuid content_id FK
        uuid escalation_handler_id FK
        enum priority
        enum status
        string reason
        uuid assigned_moderator_id FK
        timestamp created_at
        timestamp resolved_at
        text resolution_notes
    }
```

### 5.2 Model Definitions

#### Community

```python
# models/community.py
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class CommunityVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    HIDDEN = "hidden"

class CommunitySettings(BaseModel):
    auto_approve_threshold: float = 0.95
    escalation_threshold: float = 0.70
    require_approval_for: list[str] = ["new"]
    max_content_length: int = 10000
    rate_limit_per_minute: int = 30

class Community(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    description: str = Field(default="", max_length=500)
    visibility: CommunityVisibility = CommunityVisibility.PRIVATE
    default_tier_id: UUID | None = None
    settings: CommunitySettings = Field(default_factory=CommunitySettings)
    health_score: float = Field(default=1.0, ge=0.0, le=1.0)
    member_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted: bool = False

    class Config:
        from_attributes = True
```

#### Tier

```python
# models/tier.py
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class Tier(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    community_id: UUID
    name: str = Field(..., min_length=1, max_length=50)
    level: int = Field(..., ge=0, le=100)
    permissions: list[str] = Field(default_factory=list)
    criteria: dict = Field(default_factory=dict)
    member_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
```

#### Member

```python
# models/member.py
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class MemberStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    PENDING = "pending"

class Member(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    community_id: UUID
    user_id: UUID
    tier_id: UUID
    status: MemberStatus = MemberStatus.PENDING
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True
```

#### Content

```python
# models/content.py
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class ContentType(str, Enum):
    POST = "post"
    COMMENT = "comment"
    REPLY = "reply"
    MEDIA = "media"

class ContentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    DELETED = "deleted"

class Content(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    community_id: UUID
    author_id: UUID
    type: ContentType
    title: str = Field(default="", max_length=300)
    body: str = Field(default="", max_length=50000)
    status: ContentStatus = ContentStatus.PENDING
    health_score: float | None = Field(default=None, ge=0.0, le=1.0)
    moderation_result: dict | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    moderated_at: datetime | None = None

    class Config:
        from_attributes = True
```

#### ModerationAction

```python
# models/moderation_action.py
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class ModerationActionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    WARN = "warn"
    BAN = "ban"

class ModerationAction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content_id: UUID
    moderator_id: UUID
    action: ModerationActionType
    reason: str = Field(default="", max_length=1000)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
```

#### ReputationScore

```python
# models/reputation_score.py
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class ReputationEvent(BaseModel):
    type: str
    points: int
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ReputationScore(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    member_id: UUID
    community_id: UUID
    score: int = Field(default=50, ge=0, le=100)
    total_positive: int = Field(default=0, ge=0)
    total_negative: int = Field(default=0, ge=0)
    history: list[ReputationEvent] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
```

#### Escalation

```python
# models/escalation.py
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class EscalationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EscalationStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Escalation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content_id: UUID
    escalation_handler_id: UUID
    priority: EscalationPriority = EscalationPriority.NORMAL
    status: EscalationStatus = EscalationStatus.OPEN
    reason: str = Field(default="", max_length=1000)
    assigned_moderator_id: UUID | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    resolution_notes: str | None = None

    class Config:
        from_attributes = True
```

---

## 6. Integration Patterns

### 6.1 GRC_Claw Core Library Integration

```mermaid
graph LR
    subgraph GATED["Gated Communities Service"]
        API[API Layer]
        AGENTS[Agent Fleet]
        MODELS[Data Models]
    end

    subgraph CORE["@grc/core Shared Library"]
        GOV[Governance Layer]
        MON[Monitoring]
        SEC[Security]
        DATA[Data Access]
        INT[Integration Hub]
        MEM[Memory Layer]
    end

    subgraph INFRA["Shared Infrastructure"]
        KAFKA[Kafka]
        REDIS[Redis]
        PG[PostgreSQL]
    end

    API --> GOV
    API --> SEC
    AGENTS --> GOV
    AGENTS --> MON
    AGENTS --> MEM
    MODELS --> DATA
    DATA --> PG
    DATA --> REDIS
    AGENTS --> KAFKA
    MON --> KAFKA
```

### 6.2 Governance Integration

Every agent action passes through the GRC_Claw governance layer:

```python
# integrations/governance.py
from grc_core.governance import PolicyEngine, AuditLogger

class GovernanceIntegration:
    """Integrates with GRC_Claw governance layer."""
    
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.audit_logger = AuditLogger()
    
    async def check_policy(self, action: str, context: dict) -> PolicyDecision:
        """Check if an action is permitted by governance policies."""
        decision = await self.policy_engine.evaluate(
            action=action,
            agent_id=context["agent_id"],
            member_id=context.get("member_id"),
            community_id=context.get("community_id"),
            resource=context.get("resource"),
        )
        
        await self.audit_logger.log(
            event="policy.check",
            action=action,
            decision=decision.allowed,
            context=context,
        )
        
        return decision
    
    async def log_action(self, action: str, result: dict, context: dict):
        """Log an agent action for audit purposes."""
        await self.audit_logger.log(
            event="agent.action",
            action=action,
            result=result,
            context=context,
            integrity_hash=self.compute_hash(result),
        )
```

### 6.3 Event Bus Integration

```python
# integrations/event_bus.py
from grc_core.events import EventBus, Event

class ModerationEventBus:
    """Publishes and consumes moderation events via Kafka."""
    
    TOPICS = {
        "member": "grc.community.member",
        "content": "grc.community.content",
        "moderation": "grc.community.moderation",
        "tier": "grc.community.tier",
        "reputation": "grc.community.reputation",
        "escalation": "grc.community.escalation",
        "health": "grc.community.health",
    }
    
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
    
    async def publish_member_event(self, event_type: str, data: dict):
        await self.bus.publish(
            topic=self.TOPICS["member"],
            event=Event(
                type=f"member.{event_type}",
                source="gated-communities",
                data=data,
            ),
        )
    
    async def publish_content_event(self, event_type: str, data: dict):
        await self.bus.publish(
            topic=self.TOPICS["content"],
            event=Event(
                type=f"content.{event_type}",
                source="gated-communities",
                data=data,
            ),
        )
    
    async def publish_moderation_event(self, event_type: str, data: dict):
        await self.bus.publish(
            topic=self.TOPICS["moderation"],
            event=Event(
                type=f"moderation.{event_type}",
                source="gated-communities",
                data=data,
            ),
        )
```

### 6.4 Monitoring Integration

```python
# integrations/monitoring.py
from grc_core.monitoring import MetricsCollector, Tracer

class ModerationMonitoring:
    """Integrates with GRC_Claw OpenTelemetry monitoring."""
    
    def __init__(self):
        self.metrics = MetricsCollector(namespace="gated_communities")
        self.tracer = Tracer(service="gated-communities")
    
    async def record_moderation_latency(self, content_type: str, latency_ms: float):
        self.metrics.histogram(
            "moderation.latency_ms",
            latency_ms,
            labels={"content_type": content_type},
        )
    
    async def record_queue_depth(self, queue_name: str, depth: int):
        self.metrics.gauge(
            "moderation.queue_depth",
            depth,
            labels={"queue": queue_name},
        )
    
    async def record_agent_decision(self, agent: str, decision: str, confidence: float):
        self.metrics.counter(
            "agent.decisions",
            labels={"agent": agent, "decision": decision},
        )
        self.metrics.histogram(
            "agent.confidence",
            confidence,
            labels={"agent": agent},
        )
    
    def start_span(self, name: str, attributes: dict = None):
        return self.tracer.start_span(name, attributes)
```

### 6.5 Data Layer Integration

```python
# integrations/data_layer.py
from grc_core.data import Repository, Cache

class CommunityRepository(Repository[Community]):
    """Repository for Community entities with caching."""
    
    def __init__(self, db, cache: Cache):
        super().__init__(model=Community, db=db)
        self.cache = cache
    
    async def get_by_slug(self, slug: str) -> Community | None:
        cache_key = f"community:slug:{slug}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Community.model_validate(cached)
        
        result = await self.db.fetch_one(
            "SELECT * FROM communities WHERE slug = :slug AND deleted = false",
            {"slug": slug},
        )
        if result:
            community = Community.model_validate(result)
            await self.cache.set(cache_key, community.model_dump(), ttl=300)
            return community
        return None
    
    async def update_health_score(self, community_id: UUID, score: float):
        await self.db.execute(
            "UPDATE communities SET health_score = :score, updated_at = NOW() WHERE id = :id",
            {"id": community_id, "score": score},
        )
        await self.cache.delete(f"community:id:{community_id}")
```

### 6.6 LLM Provider Integration

```python
# integrations/llm.py
from grc_core.llm import LLMRouter, LLMRequest

class ModerationLLM:
    """Routes LLM requests for moderation tasks."""
    
    def __init__(self, router: LLMRouter):
        self.router = router
    
    async def classify_content(self, content: str, context: dict) -> dict:
        request = LLMRequest(
            prompt=MODERATION_CLASSIFY_PROMPT,
            context={"content": content, **context},
            model_tier="standard",
            max_tokens=500,
            temperature=0.1,
        )
        response = await self.router.route(request)
        return response.parsed_output
    
    async def score_toxicity(self, content: str) -> float:
        request = LLMRequest(
            prompt=TOXICITY_SCORE_PROMPT,
            context={"content": content},
            model_tier="standard",
            max_tokens=100,
            temperature=0.0,
        )
        response = await self.router.route(request)
        return response.parsed_output["score"]
```

---

## 7. Deployment Architecture

### 7.1 Kubernetes Deployment

```mermaid
graph TB
    subgraph K8S["Kubernetes Cluster"]
        subgraph INGRESS["Ingress Layer"]
            ING[NGINX Ingress]
        end
        
        subgraph API["API Tier"]
            API1[API Pod 1]
            API2[API Pod 2]
            API3[API Pod 3]
        end
        
        subgraph AGENTS["Agent Tier"]
            TM[Tier Manager]
            AC[Access Controller]
            MQ[Moderation Queue]
            HS[Health Scorer]
            EH[Escalation Handler]
            RT[Reputation Tracker]
        end
        
        subgraph WORKERS["Worker Tier"]
            W1[Moderation Worker]
            W2[Moderation Worker]
            W3[Reputation Worker]
            W4[Health Worker]
        end
        
        subgraph DATA["Data Tier"]
            PG[(PostgreSQL)]
            REDIS[(Redis)]
            KAFKA[Kafka]
        end
    end
    
    INGRESS --> API
    API --> AGENTS
    AGENTS --> WORKERS
    WORKERS --> DATA
    AGENTS --> DATA
```

### 7.2 Docker Compose (Development)

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/gated_communities
      - REDIS_URL=redis://redis:6379
      - KAFKA_BROKERS=kafka:9092
      - LLM_API_KEY=${LLM_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/gated_communities
      - REDIS_URL=redis://redis:6379
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - kafka
      - postgres

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: grc
      POSTGRES_PASSWORD: grc
      POSTGRES_DB: gated_communities
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U grc"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

volumes:
  pgdata:
```

---

## 8. Security & Governance

### 8.1 Authentication & Authorization

```mermaid
graph LR
    REQ[Request] --> JWT[JWT Validation]
    JWT --> RBAC[RBAC Check]
    RBAC --> ABAC[ABAC Check]
    ABAC --> TIER[Tier Check]
    TIER --> RATE[Rate Limit]
    RATE --> ALLOW[Allow]
    REJECT[Reject] --> LOG[Audit Log]
    ALLOW --> LOG
```

### 8.2 Security Policies

| Policy | Implementation |
|--------|---------------|
| Authentication | OAuth 2.1 + OIDC with PKCE |
| Authorization | RBAC + ABAC + Tier-based |
| Rate Limiting | Redis-backed token bucket per tier |
| Input Validation | Pydantic models + content length limits |
| SQL Injection | Parameterized queries via SQLAlchemy |
| XSS Prevention | Content sanitization (bleach) |
| CSRF Protection | SameSite cookies + CSRF tokens |
| Audit Logging | Immutable append-only log with Merkle chain |

### 8.3 Data Protection

- All PII encrypted at rest (AES-256)
- TLS 1.3 for all connections
- Data retention: 90 days for moderation history, indefinite for audit logs
- GDPR: Right to deletion supported via soft delete + crypto-shredding
- Cross-region data residency enforced via namespace isolation

---

## 9. Observability

### 9.1 Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `moderation.latency_ms` | Histogram | Time to moderate content |
| `moderation.queue_depth` | Gauge | Items in moderation queue |
| `moderation.auto_approve_rate` | Gauge | % auto-approved |
| `moderation.escalation_rate` | Gauge | % escalated to human |
| `agent.confidence` | Histogram | Agent decision confidence |
| `agent.decisions` | Counter | Decisions by agent type |
| `reputation.avg_score` | Gauge | Average reputation score |
| `community.health_score` | Gauge | Community health over time |
| `tier.distribution` | Gauge | Member count per tier |
| `api.request_duration` | Histogram | API endpoint latency |
| `api.error_rate` | Gauge | API error percentage |

### 9.2 Distributed Tracing

```python
# Every request flows through the full pipeline with trace context
with tracer.start_as_current_span("moderation.pipeline") as span:
    span.set_attribute("community_id", community_id)
    span.set_attribute("member_id", member_id)
    span.set_attribute("content_type", content_type)
    
    with tracer.start_as_current_span("access.check"):
        access = await access_controller.authorize(request)
    
    with tracer.start_as_current_span("content.classify"):
        classification = await moderation_queue.classify(content)
    
    with tracer.start_as_current_span("health.score"):
        health = await health_scorer.score(content)
    
    with tracer.start_as_current_span("decision"):
        result = await moderation_queue.decide(content, access, classification, health)
```

### 9.3 Alerting

| Alert | Condition | Severity |
|-------|-----------|----------|
| Queue depth > 100 | 5 min sustained | P1 |
| Escalation rate > 20% | 10 min sustained | P2 |
| API error rate > 5% | 5 min sustained | P1 |
| Agent confidence < 0.7 avg | 15 min sustained | P2 |
| Community health < 0.5 | 1 hour sustained | P3 |
| Moderation latency > 30s | 5 min sustained | P2 |

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up project structure following GRC_Claw template
- [ ] Implement data models and migrations
- [ ] Build API skeleton with FastAPI
- [ ] Integrate with @grc/core governance layer
- [ ] Set up PostgreSQL + Redis + Kafka

### Phase 2: Core Agents (Weeks 3-4)
- [ ] Implement Tier Manager agent
- [ ] Implement Access Controller agent
- [ ] Implement Moderation Queue agent
- [ ] Build event bus integration
- [ ] Write unit tests for all agents

### Phase 3: Advanced Agents (Weeks 5-6)
- [ ] Implement Health Scorer agent
- [ ] Implement Escalation Handler agent
- [ ] Implement Reputation Tracker agent
- [ ] Build WebSocket event streaming
- [ ] Integration tests

### Phase 4: Production Hardening (Weeks 7-8)
- [ ] Kubernetes deployment manifests
- [ ] Monitoring and alerting
- [ ] Load testing and performance tuning
- [ ] Security audit and penetration testing
- [ ] Documentation and runbooks

---

## Appendix A: Project Structure

```
projects/gated-communities/
├── pyproject.toml
├── Dockerfile
├── Dockerfile.worker
├── docker-compose.yml
├── README.md
├── config/
│   ├── default.yaml
│   ├── production.yaml
│   └── test.yaml
├── src/
│   └── gated_communities/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── tier_manager.py
│       │   ├── access_controller.py
│       │   ├── moderation_queue.py
│       │   ├── health_scorer.py
│       │   ├── escalation_handler.py
│       │   └── reputation_tracker.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── communities.py
│       │   ├── tiers.py
│       │   ├── members.py
│       │   ├── content.py
│       │   ├── moderation.py
│       │   ├── access.py
│       │   ├── escalations.py
│       │   └── reputation.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── community.py
│       │   ├── tier.py
│       │   ├── member.py
│       │   ├── content.py
│       │   ├── moderation_action.py
│       │   ├── reputation_score.py
│       │   └── escalation.py
│       ├── integrations/
│       │   ├── __init__.py
│       │   ├── governance.py
│       │   ├── event_bus.py
│       │   ├── monitoring.py
│       │   ├── data_layer.py
│       │   └── llm.py
│       └── workers/
│           ├── __init__.py
│           ├── moderation_worker.py
│           ├── reputation_worker.py
│           └── health_worker.py
├── tests/
│   ├── conftest.py
│   ├── test_agents/
│   ├── test_api/
│   ├── test_models/
│   └── test_integrations/
└── k8s/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    └── hpa.yaml
```

## Appendix B: Configuration

```yaml
# config/default.yaml
service:
  name: gated-communities
  version: "1.0.0"
  environment: development

database:
  url: postgresql://grc:grc@localhost:5432/gated_communities
  pool_size: 20
  max_overflow: 10

redis:
  url: redis://localhost:6379
  db: 0

kafka:
  brokers: localhost:9092
  consumer_group: gated-communities

moderation:
  auto_approve_threshold: 0.95
  escalation_threshold: 0.70
  max_queue_depth: 1000
  sla_minutes: 5

agents:
  tier_manager:
    model: claude-sonnet-4-20250514
    max_tokens: 1000
    temperature: 0.1
  access_controller:
    model: claude-sonnet-4-20250514
    max_tokens: 500
    temperature: 0.0
  moderation_queue:
    model: claude-sonnet-4-20250514
    max_tokens: 1000
    temperature: 0.1
  health_scorer:
    model: claude-sonnet-4-20250514
    max_tokens: 500
    temperature: 0.0
  escalation_handler:
    model: claude-sonnet-4-20250514
    max_tokens: 1000
    temperature: 0.1
  reputation_tracker:
    model: claude-sonnet-4-20250514
    max_tokens: 500
    temperature: 0.0

governance:
  policy_engine: grc_core.governance.PolicyEngine
  audit_logger: grc_core.governance.AuditLogger
  require_consensus_for: ["tier.demote", "member.ban"]
```

---

*End of document.*
