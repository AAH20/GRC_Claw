# AI-Powered Lead Scoring & Qualification System

**Version:** 1.0  
**Date:** 2026-10-01  
**Owner:** GRC_Claw Architecture Team  
**Status:** Implementation Ready  
**References:** [Agent Governance Spec v1.1](./grc-claw-agent-governance-implementation-guide.md) · [Model Governance Spec v2.0](./grc-claw-model-governance-implementation-guide.md) · [GRC_Claw Architecture](../ARCHITECTURE.md)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Lead Enrichment Agent](#2-lead-enrichment-agent)
3. [Scoring Engine — BANT, MEDDIC, CHAMP](#3-scoring-engine)
4. [Qualification Workflows](#4-qualification-workflows)
5. [Predictive Analytics](#5-predictive-analytics)
6. [CRM Integration](#6-crm-integration)
7. [Real-Time Scoring API](#7-real-time-scoring-api)
8. [GRC_Claw Governance Integration](#8-grc-claw-governance-integration)
9. [Data Flow Diagrams](#9-data-flow-diagrams)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. Architecture Overview

### 1.1 System Context

The AI-Powered Lead Scoring & Qualification System is a GRC_Claw implementation that automates lead enrichment, multi-framework scoring (BANT, MEDDIC, CHAMP), qualification routing, and predictive conversion analytics. It operates as a governed agent within the GRC_Claw control plane, leveraging the platform's identity, policy, and audit infrastructure.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                AI-Powered Lead Scoring & Qualification                  │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │   Lead       │  │   Scoring    │  │   Qualification│              │
│  │   Enrichment │  │   Engine     │  │   Workflows    │              │
│  │   Agent      │  │   (BANT/     │  │   (Routing &   │              │
│  │              │  │   MEDDIC/    │  │   Nurture)     │              │
│  │              │  │   CHAMP)     │  │                │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                │
│         │                 │                 │                          │
│  ┌──────┴─────────────────┴─────────────────┴───────┐                │
│  │              Core Scoring Orchestrator             │                │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐   │                │
│  │  │  Feature   │ │  Predictive│ │  Policy    │   │                │
│  │  │  Store     │ │  Analytics │ │  Engine    │   │                │
│  │  │  (Redis)   │ │  (ML)      │ │  (OPA)     │   │                │
│  │  └────────────┘ └────────────┘ └────────────┘   │                │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐   │                │
│  │  │  CRM       │ │  Real-Time │ │  Audit     │   │                │
│  │  │  Connector │ │  API GW    │ │  Logger    │   │                │
│  │  │  (Salesforce│ │  (FastAPI) │ │  (Merkle)  │   │                │
│  │  │  HubSpot)  │ │            │ │            │   │                │
│  │  └────────────┘ └────────────┘ └────────────┘   │                │
│  └──────────────────────────────────────────────────┘                │
│                                                                         │
│  ┌──────────────────────────────────────────────────┐                │
│  │           GRC_Claw Governance Layer               │                │
│  │  Identity (DID) │ Trust Score │ Policy (OPA)     │                │
│  │  Delegation     │ Capability  │ Audit (Merkle)   │                │
│  └──────────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Governance-first** | All scoring actions pass through GRC_Claw policy engine |
| **Multi-framework** | BANT, MEDDIC, CHAMP scoring with configurable weights |
| **Explainable AI** | Every score includes feature attribution and reasoning |
| **Real-time** | Sub-100ms scoring API with streaming enrichment |
| **Fail-closed** | Missing data defaults to lowest confidence, not highest |
| **Tamper-evident** | All scoring decisions logged to Merkle audit chain |
| **Composable** | Scoring modules plug into existing GRC_Claw agent framework |

### 1.3 Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Scoring Engine | Python 3.12 + scikit-learn | Mature ML ecosystem |
| Feature Store | Redis Cluster | Low-latency feature serving |
| Predictive Models | XGBoost + SHAP | Interpretable gradient boosting |
| API Gateway | FastAPI + Uvicorn | Async, OpenAPI-native |
| CRM Connectors | Salesforce REST + HubSpot API | Industry standard |
| Policy Engine | OPA (Open Policy Agent) | CNCF graduated, declarative |
| Audit Log | Custom Merkle chain + PostgreSQL | Tamper-evident, queryable |
| Event Bus | Apache Kafka | Streaming enrichment events |
| Model Registry | MLflow | Versioning, lineage, deployment |
| Orchestration | Temporal.io | Durable workflow execution |

---

## 2. Lead Enrichment Agent

### 2.1 Purpose

The Lead Enrichment Agent is responsible for augmenting raw lead records with firmographic, technographic, and intent data from internal and external sources. It operates as a GRC_Claw governed agent with delegated capabilities.

### 2.2 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Lead Enrichment Agent                        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Internal   │  │  External   │  │  Intent     │        │
│  │  Data       │  │  Data       │  │  Data       │        │
│  │  Sources    │  │  Sources    │  │  Sources    │        │
│  │             │  │             │  │             │        │
│  │ • CRM       │  │ • Clearbit  │  │ • Bombora   │        │
│  │ • Marketing │  │ • ZoomInfo  │  │ • G2        │        │
│  │ • Product   │  │ • LinkedIn  │  │ • 6sense    │        │
│  │ • Support   │  │ • Crunchbase│  │ • TechTarget│        │
│  │ • Billing   │  │ • Apollo    │  │ • Custom    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          ▼                                  │
│              ┌─────────────────────┐                       │
│              │  Enrichment Engine  │                       │
│              │  ┌───────────────┐  │                       │
│              │  │ Data Fusion   │  │                       │
│              │  │ (Entity       │  │                       │
│              │  │  Resolution)  │  │                       │
│              │  └───────────────┘  │                       │
│              │  ┌───────────────┐  │                       │
│              │  │ Confidence    │  │                       │
│              │  │ Scoring       │  │                       │
│              │  └───────────────┘  │                       │
│              │  ┌───────────────┐  │                       │
│              │  │ Deduplication │  │                       │
│              │  │ (Fuzzy Match) │  │                       │
│              │  └───────────────┘  │                       │
│              └──────────┬──────────┘                       │
│                         │                                   │
│              ┌──────────┴──────────┐                       │
│              │  Enriched Lead      │                       │
│              │  Record (JSON)      │                       │
│              └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Enrichment Pipeline

```python
# enrichment/pipeline.py
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class DataSource(Enum):
    INTERNAL_CRM = "internal_crm"
    CLEARBIT = "clearbit"
    ZOOMINFO = "zoominfo"
    LINKEDIN = "linkedin"
    BOMBORA = "bombora"
    G2 = "g2"
    SIXSENSE = "6sense"
    CUSTOM = "custom"

@dataclass
class EnrichmentResult:
    field: str
    value: str
    source: DataSource
    confidence: float  # 0.0 - 1.0
    timestamp: str
    ttl_seconds: int = 86400  # Cache TTL

@dataclass
class EnrichedLead:
    lead_id: str
    firmographic: dict = field(default_factory=dict)
    technographic: dict = field(default_factory=dict)
    intent: dict = field(default_factory=dict)
    contact: dict = field(default_factory=dict)
    enrichment_sources: list[EnrichmentResult] = field(default_factory=list)
    overall_confidence: float = 0.0
    enrichment_version: str = "1.0"
```

### 2.4 Data Sources & Schema

#### 2.4.1 Firmographic Data

| Field | Type | Sources | Confidence Weight |
|-------|------|---------|-------------------|
| company_name | string | CRM, Clearbit, ZoomInfo | 1.0 |
| industry | string | Clearbit, ZoomInfo, LinkedIn | 0.9 |
| company_size | enum | Clearbit, ZoomInfo, LinkedIn | 0.85 |
| revenue_range | string | ZoomInfo, Clearbit, Crunchbase | 0.8 |
| location | object | CRM, Clearbit, ZoomInfo | 0.95 |
| founded_year | int | Crunchbase, Clearbit | 0.75 |
| sic_code | string | Clearbit | 0.85 |
| naics_code | string | Clearbit | 0.85 |

#### 2.4.2 Technographic Data

| Field | Type | Sources | Confidence Weight |
|-------|------|---------|-------------------|
| tech_stack | array | BuiltWith, Datanyze | 0.8 |
| cloud_provider | string | BuiltWith, Custom | 0.75 |
| crm_system | string | BuiltWith, Datanyze | 0.85 |
| marketing_automation | string | BuiltWith, Datanyze | 0.85 |
| analytics_tools | array | BuiltWith | 0.7 |
| security_tools | array | BuiltWith | 0.7 |

#### 2.4.3 Intent Data

| Field | Type | Sources | Confidence Weight |
|-------|------|---------|-------------------|
| intent_topics | array | Bombora, 6sense | 0.75 |
| intent_score | float | Bombora, 6sense | 0.7 |
| buying_stage | enum | 6sense, Custom | 0.65 |
| content_consumption | array | G2, TechTarget | 0.6 |
| competitor_mentions | array | G2, Custom | 0.55 |
| surge_score | float | Bombora | 0.7 |

### 2.5 Entity Resolution

```python
# enrichment/entity_resolution.py
from dataclasses import dataclass
from typing import Optional
import rapidfuzz

@dataclass
class EntityMatch:
    source_id: str
    target_id: str
    match_score: float
    match_type: str  # "exact", "fuzzy", "domain", "phone"
    fields_matched: list[str]

class EntityResolver:
    """Resolves lead entities across data sources using multi-signal matching."""
    
    def __init__(self, config: dict):
        self.domain_weight = config.get("domain_weight", 0.4)
        self.name_weight = config.get("name_weight", 0.3)
        self.phone_weight = config.get("phone_weight", 0.2)
        self.location_weight = config.get("location_weight", 0.1)
        self.fuzzy_threshold = config.get("fuzzy_threshold", 0.85)
    
    def resolve(self, lead: dict, candidates: list[dict]) -> Optional[EntityMatch]:
        """Score candidate matches and return best above threshold."""
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self._compute_match_score(lead, candidate)
            if score > best_score and score >= self.fuzzy_threshold:
                best_score = score
                best_match = EntityMatch(
                    source_id=lead["id"],
                    target_id=candidate["id"],
                    match_score=score,
                    match_type=self._classify_match(lead, candidate),
                    fields_matched=self._get_matched_fields(lead, candidate)
                )
        
        return best_match
    
    def _compute_match_score(self, lead: dict, candidate: dict) -> float:
        scores = []
        
        # Domain match (exact)
        if lead.get("email_domain") == candidate.get("email_domain"):
            scores.append(self.domain_weight)
        
        # Company name fuzzy match
        if lead.get("company_name") and candidate.get("company_name"):
            name_score = rapidfuzz.fuzz.ratio(
                lead["company_name"].lower(),
                candidate["company_name"].lower()
            ) / 100.0
            scores.append(name_score * self.name_weight)
        
        # Phone match
        if lead.get("phone") == candidate.get("phone"):
            scores.append(self.phone_weight)
        
        # Location match
        if lead.get("city") == candidate.get("city") and lead.get("country") == candidate.get("country"):
            scores.append(self.location_weight)
        
        return sum(scores)
```

### 2.6 GRC_Claw Governance Integration

The enrichment agent operates under GRC_Claw governance:

```python
# enrichment/governance.py
from grc_claw import AgentIdentity, PolicyEngine, AuditLogger

class GovernedEnrichmentAgent:
    """Lead enrichment agent with GRC_Claw governance."""
    
    def __init__(self, identity: AgentIdentity, policy: PolicyEngine, audit: AuditLogger):
        self.identity = identity
        self.policy = policy
        self.audit = audit
        self.capabilities = self._load_capabilities()
    
    def _load_capabilities(self) -> list[str]:
        """Load delegated capabilities from GRC_Claw identity."""
        return self.identity.get_capabilities("lead-enrichment")
    
    async def enrich(self, lead_id: str, sources: list[str]) -> EnrichedLead:
        """Enrich a lead with governance checks."""
        # Policy check: is this agent allowed to enrich?
        decision = self.policy.evaluate(
            subject=self.identity.did,
            action="lead.enrich",
            resource=f"lead/{lead_id}",
            context={"sources": sources}
        )
        
        if not decision.allowed:
            self.audit.log_denied(self.identity.did, "lead.enrich", lead_id, decision.reason)
            raise PermissionError(f"Enrichment denied: {decision.reason}")
        
        # Execute enrichment
        result = await self._execute_enrichment(lead_id, sources)
        
        # Audit log
        self.audit.log_action(
            agent=self.identity.did,
            action="lead.enrich",
            resource=lead_id,
            result=result,
            capability_used="lead-enrichment"
        )
        
        return result
```

---

## 3. Scoring Engine

### 3.1 Multi-Framework Scoring Architecture

The scoring engine supports three sales qualification frameworks, each with its own dimension set, weighting scheme, and scoring logic. Frameworks can be used individually or combined.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Scoring Engine                                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Framework Router & Aggregator               │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │   │
│  │  │  BANT   │  │ MEDDIC  │  │  CHAMP  │                 │   │
│  │  │ Scorer  │  │ Scorer  │  │ Scorer  │                 │   │
│  │  └────┬────┘  └────┬────┘  └────┬────┘                 │   │
│  │       │            │            │                        │   │
│  │       └────────────┼────────────┘                        │   │
│  │                    ▼                                     │   │
│  │         ┌─────────────────┐                             │   │
│  │         │  Score Fusion   │                             │   │
│  │         │  (Weighted Avg) │                             │   │
│  │         └────────┬────────┘                             │   │
│  └──────────────────┼──────────────────────────────────────┘   │
│                     ▼                                           │
│         ┌─────────────────────┐                                │
│         │  Unified Lead Score │                                │
│         │  • bant_score       │                                │
│         │  • meddic_score     │                                │
│         │  • champ_score      │                                │
│         │  • composite_score  │                                │
│         │  • confidence       │                                │
│         │  • feature_attribution│                              │
│         └─────────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 BANT Scorer

BANT evaluates **Budget, Authority, Need, Timeline** — the classic qualification framework.

```python
# scoring/bant.py
from dataclasses import dataclass
from enum import Enum

class BANTDimension(Enum):
    BUDGET = "budget"
    AUTHORITY = "authority"
    NEED = "need"
    TIMELINE = "timeline"

@dataclass
class BANTScore:
    budget: float       # 0-100
    authority: float    # 0-100
    need: float         # 0-100
    timeline: float     # 0-100
    overall: float      # Weighted composite
    confidence: float   # Data completeness
    gaps: list[str]     # Missing dimensions

class BANTScorer:
    """
    BANT Scoring Engine
    
    Weights (configurable):
    - Budget: 25%
    - Authority: 25%
    - Need: 30%
    - Timeline: 20%
    """
    
    DEFAULT_WEIGHTS = {
        BANTDimension.BUDGET: 0.25,
        BANTDimension.AUTHORITY: 0.25,
        BANTDimension.NEED: 0.30,
        BANTDimension.TIMELINE: 0.20,
    }
    
    def __init__(self, weights: dict = None, llm_client=None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.llm = llm_client  # Optional LLM for inference from text
    
    def score(self, lead: dict, enriched_data: dict) -> BANTScore:
        """Compute BANT score from lead and enriched data."""
        
        budget = self._score_budget(lead, enriched_data)
        authority = self._score_authority(lead, enriched_data)
        need = self._score_need(lead, enriched_data)
        timeline = self._score_timeline(lead, enriched_data)
        
        # Compute weighted overall
        overall = (
            budget * self.weights[BANTDimension.BUDGET] +
            authority * self.weights[BANTDimension.AUTHORITY] +
            need * self.weights[BANTDimension.NEED] +
            timeline * self.weights[BANTDimension.TIMELINE]
        )
        
        # Confidence based on data completeness
        dimensions = [budget, authority, need, timeline]
        gaps = [d.value for d, s in zip(BANTDimension, dimensions) if s == 0]
        confidence = 1.0 - (len(gaps) / len(dimensions))
        
        return BANTScore(
            budget=budget,
            authority=authority,
            need=need,
            timeline=timeline,
            overall=overall,
            confidence=confidence,
            gaps=gaps
        )
    
    def _score_budget(self, lead: dict, enriched: dict) -> float:
        """Score budget dimension (0-100)."""
        score = 0.0
        
        # Direct budget signal
        if lead.get("budget"):
            score += 40
        
        # Revenue-based inference
        revenue = enriched.get("firmographic", {}).get("revenue_range")
        if revenue:
            revenue_scores = {
                "0-1M": 10, "1M-10M": 25, "10M-50M": 40,
                "50M-100M": 55, "100M-500M": 70, "500M-1B": 85, "1B+": 100
            }
            score += revenue_scores.get(revenue, 0) * 0.3
        
        # Company size correlation
        size = enriched.get("firmographic", {}).get("company_size")
        if size:
            size_scores = {
                "1-10": 5, "11-50": 15, "51-200": 30,
                "201-500": 50, "501-1000": 65, "1001-5000": 80, "5000+": 95
            }
            score += size_scores.get(size, 0) * 0.3
        
        return min(score, 100)
    
    def _score_authority(self, lead: dict, enriched: dict) -> float:
        """Score authority dimension (0-100)."""
        score = 0.0
        
        # Job title seniority
        title = lead.get("title", "").lower()
        seniority_scores = {
            "c-level": 40, "vp": 35, "director": 30,
            "manager": 20, "senior": 15, "lead": 15
        }
        for keyword, points in seniority_scores.items():
            if keyword in title:
                score += points
                break
        
        # Decision-making keywords
        decision_keywords = ["decision", "approve", "budget", "sign", "buy", "purchase"]
        if any(kw in title for kw in decision_keywords):
            score += 20
        
        # Department match
        dept = lead.get("department", "").lower()
        if dept in ["it", "technology", "security", "engineering", "operations"]:
            score += 20
        
        # Engagement signals
        if lead.get("email_opens", 0) > 5:
            score += 10
        if lead.get("meetings_booked", 0) > 0:
            score += 10
        
        return min(score, 100)
    
    def _score_need(self, lead: dict, enriched: dict) -> float:
        """Score need dimension (0-100)."""
        score = 0.0
        
        # Intent data
        intent_score = enriched.get("intent", {}).get("intent_score", 0)
        score += intent_score * 0.4
        
        # Content consumption
        content = enriched.get("intent", {}).get("content_consumption", [])
        score += min(len(content) * 5, 20)
        
        # Pain point keywords in notes/activities
        pain_keywords = ["problem", "challenge", "issue", "need", "want", "looking for", "replace", "upgrade"]
        notes = lead.get("notes", "").lower()
        pain_matches = sum(1 for kw in pain_keywords if kw in notes)
        score += min(pain_matches * 10, 30)
        
        # Competitor displacement signal
        competitors = enriched.get("intent", {}).get("competitor_mentions", [])
        if competitors:
            score += 15
        
        # Surge score
        surge = enriched.get("intent", {}).get("surge_score", 0)
        score += surge * 0.15
        
        return min(score, 100)
    
    def _score_timeline(self, lead: dict, enriched: dict) -> float:
        """Score timeline dimension (0-100)."""
        score = 0.0
        
        # Explicit timeline
        timeline = lead.get("timeline", "").lower()
        timeline_scores = {
            "immediate": 100, "asap": 100, "now": 90,
            "this quarter": 75, "q1": 70, "q2": 60,
            "this year": 50, "next quarter": 40,
            "6 months": 30, "exploring": 10, "just researching": 5
        }
        for keyword, points in timeline_scores.items():
            if keyword in timeline:
                score += points
                break
        
        # Buying stage
        stage = enriched.get("intent", {}).get("buying_stage", "")
        stage_scores = {
            "decision": 90, "evaluation": 70, "consideration": 50,
            "awareness": 30, "research": 15
        }
        score += stage_scores.get(stage, 0) * 0.5
        
        # Engagement recency
        last_activity = lead.get("last_activity_days_ago", 30)
        if last_activity < 7:
            score += 20
        elif last_activity < 14:
            score += 10
        elif last_activity < 30:
            score += 5
        
        return min(score, 100)
```

### 3.3 MEDDIC Scorer

MEDDIC evaluates **Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion** — the enterprise sales qualification framework.

```python
# scoring/meddic.py
from dataclasses import dataclass
from enum import Enum

class MEDDICDimension(Enum):
    METRICS = "metrics"
    ECONOMIC_BUYER = "economic_buyer"
    DECISION_CRITERIA = "decision_criteria"
    DECISION_PROCESS = "decision_process"
    IDENTIFY_PAIN = "identify_pain"
    CHAMPION = "champion"

@dataclass
class MEDDICScore:
    metrics: float
    economic_buyer: float
    decision_criteria: float
    decision_process: float
    identify_pain: float
    champion: float
    overall: float
    confidence: float
    gaps: list[str]

class MEDDICScorer:
    """
    MEDDIC Scoring Engine
    
    Weights (configurable):
    - Metrics: 15%
    - Economic Buyer: 20%
    - Decision Criteria: 15%
    - Decision Process: 15%
    - Identify Pain: 20%
    - Champion: 15%
    """
    
    DEFAULT_WEIGHTS = {
        MEDDICDimension.METRICS: 0.15,
        MEDDICDimension.ECONOMIC_BUYER: 0.20,
        MEDDICDimension.DECISION_CRITERIA: 0.15,
        MEDDICDimension.DECISION_PROCESS: 0.15,
        MEDDICDimension.IDENTIFY_PAIN: 0.20,
        MEDDICDimension.CHAMPION: 0.15,
    }
    
    def __init__(self, weights: dict = None, llm_client=None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.llm = llm_client
    
    def score(self, lead: dict, enriched_data: dict) -> MEDDICScore:
        """Compute MEDDIC score."""
        
        metrics = self._score_metrics(lead, enriched_data)
        economic_buyer = self._score_economic_buyer(lead, enriched_data)
        decision_criteria = self._score_decision_criteria(lead, enriched_data)
        decision_process = self._score_decision_process(lead, enriched_data)
        identify_pain = self._score_identify_pain(lead, enriched_data)
        champion = self._score_champion(lead, enriched_data)
        
        dimensions = [metrics, economic_buyer, decision_criteria, 
                      decision_process, identify_pain, champion]
        
        overall = sum(
            score * self.weights[dim]
            for score, dim in zip(dimensions, MEDDICDimension)
        )
        
        gaps = [d.value for d, s in zip(MEDDICDimension, dimensions) if s == 0]
        confidence = 1.0 - (len(gaps) / len(dimensions))
        
        return MEDDICScore(
            metrics=metrics,
            economic_buyer=economic_buyer,
            decision_criteria=decision_criteria,
            decision_process=decision_process,
            identify_pain=identify_pain,
            champion=champion,
            overall=overall,
            confidence=confidence,
            gaps=gaps
        )
    
    def _score_metrics(self, lead: dict, enriched: dict) -> float:
        """Score metrics dimension — quantified business impact."""
        score = 0.0
        
        # ROI calculator usage
        if lead.get("roi_calculator_used"):
            score += 30
        
        # Pricing page visits
        if lead.get("pricing_page_visits", 0) > 0:
            score += 20
        
        # Quantified pain in notes
        notes = lead.get("notes", "").lower()
        metric_keywords = ["save", "reduce", "increase", "improve", "roi", "%", "$", "hours", "cost"]
        metric_matches = sum(1 for kw in metric_keywords if kw in notes)
        score += min(metric_matches * 10, 30)
        
        # Business case engagement
        if lead.get("business_case_downloaded"):
            score += 20
        
        return min(score, 100)
    
    def _score_economic_buyer(self, lead: dict, enriched: dict) -> float:
        """Score economic buyer — access to budget authority."""
        score = 0.0
        
        # Title seniority (C-level, VP)
        title = lead.get("title", "").lower()
        if any(kw in title for kw in ["ceo", "cto", "cfo", "cio", "cro", "coo"]):
            score += 50
        elif any(kw in title for kw in ["vp", "vice president"]):
            score += 35
        elif "director" in title:
            score += 20
        
        # Budget authority signal
        if lead.get("has_budget_authority"):
            score += 30
        
        # Engagement with executive content
        if lead.get("executive_content_engagement", 0) > 3:
            score += 20
        
        return min(score, 100)
    
    def _score_decision_criteria(self, lead: dict, enriched: dict) -> float:
        """Score decision criteria — known evaluation criteria."""
        score = 0.0
        
        # RFP/RFI participation
        if lead.get("rfp_participant"):
            score += 40
        
        # Comparison requests
        if lead.get("comparison_requested"):
            score += 25
        
        # Feature-specific questions
        feature_questions = lead.get("feature_questions", [])
        score += min(len(feature_questions) * 5, 20)
        
        # Security/compliance review
        if lead.get("security_review_initiated"):
            score += 15
        
        return min(score, 100)
    
    def _score_decision_process(self, lead: dict, enriched: dict) -> float:
        """Score decision process — known buying process."""
        score = 0.0
        
        # Multi-stakeholder engagement
        stakeholders = lead.get("stakeholders_engaged", 0)
        score += min(stakeholders * 10, 40)
        
        # Legal/procurement involvement
        if lead.get("legal_review_initiated"):
            score += 20
        
        # Trial/POC started
        if lead.get("trial_started") or lead.get("poc_started"):
            score += 25
        
        # Implementation discussion
        if lead.get("implementation_discussed"):
            score += 15
        
        return min(score, 100)
    
    def _score_identify_pain(self, lead: dict, enriched: dict) -> float:
        """Score identify pain — clear problem identification."""
        score = 0.0
        
        # Pain point keywords
        notes = lead.get("notes", "").lower()
        pain_keywords = ["problem", "challenge", "issue", "struggling", "failing", 
                         "inefficient", "manual", "broken", "slow", "expensive"]
        pain_matches = sum(1 for kw in pain_keywords if kw in notes)
        score += min(pain_matches * 10, 40)
        
        # Competitor displacement
        if enriched.get("intent", {}).get("competitor_mentions"):
            score += 20
        
        # Support tickets (if existing customer)
        if lead.get("support_tickets_30d", 0) > 5:
            score += 15
        
        # Churn risk signals
        if lead.get("churn_risk_signals"):
            score += 15
        
        # Feature gap mentions
        if lead.get("feature_gap_mentions"):
            score += 10
        
        return min(score, 100)
    
    def _score_champion(self, lead: dict, enriched: dict) -> float:
        """Score champion — internal advocate strength."""
        score = 0.0
        
        # Engagement frequency
        activities = lead.get("activity_count_30d", 0)
        score += min(activities * 3, 30)
        
        # Content sharing (forwarded, shared)
        if lead.get("content_shared"):
            score += 20
        
        # Meeting acceptance rate
        meetings = lead.get("meetings_accepted", 0)
        score += min(meetings * 10, 30)
        
        # Referral behavior
        if lead.get("referred_others"):
            score += 20
        
        return min(score, 100)
```

### 3.4 CHAMP Scorer

CHAMP evaluates **Challenges, Authority, Money, Prioritization** — a simplified qualification framework ideal for SMB and mid-market.

```python
# scoring/champ.py
from dataclasses import dataclass
from enum import Enum

class CHAMPDimension(Enum):
    CHALLENGES = "challenges"
    AUTHORITY = "authority"
    MONEY = "money"
    PRIORITIZATION = "prioritization"

@dataclass
class CHAMPScore:
    challenges: float
    authority: float
    money: float
    prioritization: float
    overall: float
    confidence: float
    gaps: list[str]

class CHAMPScorer:
    """
    CHAMP Scoring Engine
    
    Weights (configurable):
    - Challenges: 30%
    - Authority: 20%
    - Money: 25%
    - Prioritization: 25%
    """
    
    DEFAULT_WEIGHTS = {
        CHAMPDimension.CHALLENGES: 0.30,
        CHAMPDimension.AUTHORITY: 0.20,
        CHAMPDimension.MONEY: 0.25,
        CHAMPDimension.PRIORITIZATION: 0.25,
    }
    
    def __init__(self, weights: dict = None, llm_client=None):
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.llm = llm_client
    
    def score(self, lead: dict, enriched_data: dict) -> CHAMPScore:
        """Compute CHAMP score."""
        
        challenges = self._score_challenges(lead, enriched_data)
        authority = self._score_authority(lead, enriched_data)
        money = self._score_money(lead, enriched_data)
        prioritization = self._score_prioritization(lead, enriched_data)
        
        dimensions = [challenges, authority, money, prioritization]
        
        overall = sum(
            score * self.weights[dim]
            for score, dim in zip(dimensions, CHAMPDimension)
        )
        
        gaps = [d.value for d, s in zip(CHAMPDimension, dimensions) if s == 0]
        confidence = 1.0 - (len(gaps) / len(dimensions))
        
        return CHAMPScore(
            challenges=challenges,
            authority=authority,
            money=money,
            prioritization=prioritization,
            overall=overall,
            confidence=confidence,
            gaps=gaps
        )
    
    def _score_challenges(self, lead: dict, enriched: dict) -> float:
        """Score challenges — problem identification and urgency."""
        score = 0.0
        
        notes = lead.get("notes", "").lower()
        challenge_keywords = ["problem", "challenge", "issue", "struggling", 
                              "need", "want", "looking", "frustrated", "difficult"]
        matches = sum(1 for kw in challenge_keywords if kw in notes)
        score += min(matches * 15, 50)
        
        # Intent surge
        surge = enriched.get("intent", {}).get("surge_score", 0)
        score += surge * 0.3
        
        # Competitor mentions
        if enriched.get("intent", {}).get("competitor_mentions"):
            score += 20
        
        return min(score, 100)
    
    def _score_authority(self, lead: dict, enriched: dict) -> float:
        """Score authority — decision-making power."""
        score = 0.0
        
        title = lead.get("title", "").lower()
        if any(kw in title for kw in ["owner", "founder", "ceo", "president"]):
            score += 50
        elif any(kw in title for kw in ["vp", "head", "director", "manager"]):
            score += 35
        elif any(kw in title for kw in ["lead", "senior", "principal"]):
            score += 20
        
        # Engagement depth
        if lead.get("email_replies", 0) > 2:
            score += 20
        if lead.get("meetings_booked", 0) > 0:
            score += 15
        
        return min(score, 100)
    
    def _score_money(self, lead: dict, enriched: dict) -> float:
        """Score money — budget availability."""
        score = 0.0
        
        revenue = enriched.get("firmographic", {}).get("revenue_range")
        if revenue:
            revenue_scores = {
                "0-1M": 10, "1M-10M": 30, "10M-50M": 50,
                "50M-100M": 70, "100M-500M": 85, "500M-1B": 95, "1B+": 100
            }
            score += revenue_scores.get(revenue, 0) * 0.5
        
        size = enriched.get("firmographic", {}).get("company_size")
        if size:
            size_scores = {
                "1-10": 5, "11-50": 20, "51-200": 40,
                "201-500": 60, "501-1000": 75, "1001-5000": 90, "5000+": 100
            }
            score += size_scores.get(size, 0) * 0.3
        
        # Pricing engagement
        if lead.get("pricing_page_visits", 0) > 0:
            score += 20
        
        return min(score, 100)
    
    def _score_prioritization(self, lead: dict, enriched: dict) -> float:
        """Score prioritization — urgency and timeline."""
        score = 0.0
        
        timeline = lead.get("timeline", "").lower()
        if any(kw in timeline for kw in ["now", "asap", "immediate", "urgent"]):
            score += 50
        elif "quarter" in timeline:
            score += 35
        elif "month" in timeline:
            score += 20
        elif "year" in timeline:
            score += 10
        
        # Buying stage
        stage = enriched.get("intent", {}).get("buying_stage", "")
        stage_scores = {"decision": 40, "evaluation": 30, "consideration": 20, "awareness": 10}
        score += stage_scores.get(stage, 0)
        
        # Recent engagement
        last_activity = lead.get("last_activity_days_ago", 30)
        if last_activity < 3:
            score += 10
        elif last_activity < 7:
            score += 5
        
        return min(score, 100)
```

### 3.5 Score Fusion & Explainability

```python
# scoring/fusion.py
from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class UnifiedScore:
    lead_id: str
    bant_score: float
    meddic_score: float
    champ_score: float
    composite_score: float
    confidence: float
    primary_framework: str
    feature_attribution: dict
    explanation: str
    timestamp: str

class ScoreFusion:
    """Fuses multi-framework scores into a unified lead score."""
    
    def __init__(self, config: dict):
        self.framework_weights = config.get("framework_weights", {
            "bant": 0.33,
            "meddic": 0.34,
            "champ": 0.33
        })
        self.min_confidence_threshold = config.get("min_confidence", 0.3)
    
    def fuse(self, bant: BANTScore, meddic: MEDDICScore, champ: CHAMPScore) -> UnifiedScore:
        """Compute unified score from framework scores."""
        
        # Weighted composite
        composite = (
            bant.overall * self.framework_weights["bant"] +
            meddic.overall * self.framework_weights["meddic"] +
            champ.overall * self.framework_weights["champ"]
        )
        
        # Confidence-weighted adjustment
        avg_confidence = (bant.confidence + meddic.confidence + champ.confidence) / 3
        if avg_confidence < self.min_confidence_threshold:
            composite *= 0.8  # Penalize low-confidence scores
        
        # Determine primary framework (highest confidence)
        frameworks = {
            "bant": (bant.overall, bant.confidence),
            "meddic": (meddic.overall, meddic.confidence),
            "champ": (champ.overall, champ.confidence)
        }
        primary = max(frameworks, key=lambda k: frameworks[k][0] * frameworks[k][1])
        
        # Feature attribution (SHAP-like)
        attribution = self._compute_attribution(bant, meddic, champ)
        
        # Natural language explanation
        explanation = self._generate_explanation(bant, meddic, champ, composite, primary)
        
        return UnifiedScore(
            lead_id="",
            bant_score=bant.overall,
            meddic_score=meddic.overall,
            champ_score=champ.overall,
            composite_score=composite,
            confidence=avg_confidence,
            primary_framework=primary,
            feature_attribution=attribution,
            explanation=explanation,
            timestamp=""
        )
    
    def _compute_attribution(self, bant, meddic, champ) -> dict:
        """Compute feature-level attribution for explainability."""
        return {
            "bant": {
                "budget": bant.budget * 0.25,
                "authority": bant.authority * 0.25,
                "need": bant.need * 0.30,
                "timeline": bant.timeline * 0.20
            },
            "meddic": {
                "metrics": meddic.metrics * 0.15,
                "economic_buyer": meddic.economic_buyer * 0.20,
                "decision_criteria": meddic.decision_criteria * 0.15,
                "decision_process": meddic.decision_process * 0.15,
                "identify_pain": meddic.identify_pain * 0.20,
                "champion": meddic.champion * 0.15
            },
            "champ": {
                "challenges": champ.challenges * 0.30,
                "authority": champ.authority * 0.20,
                "money": champ.money * 0.25,
                "prioritization": champ.prioritization * 0.25
            }
        }
    
    def _generate_explanation(self, bant, meddic, champ, composite, primary) -> str:
        """Generate human-readable score explanation."""
        parts = [
            f"Composite Score: {composite:.1f}/100",
            f"Primary Framework: {primary.upper()}",
            f"BANT: {bant.overall:.1f} (Budget: {bant.budget:.0f}, Authority: {bant.authority:.0f}, Need: {bant.need:.0f}, Timeline: {bant.timeline:.0f})",
            f"MEDDIC: {meddic.overall:.1f} (Metrics: {meddic.metrics:.0f}, Econ Buyer: {meddic.economic_buyer:.0f}, Pain: {meddic.identify_pain:.0f}, Champion: {meddic.champion:.0f})",
            f"CHAMP: {champ.overall:.1f} (Challenges: {champ.challenges:.0f}, Authority: {champ.authority:.0f}, Money: {champ.money:.0f}, Priority: {champ.prioritization:.0f})"
        ]
        
        # Add gap analysis
        all_gaps = bant.gaps + meddic.gaps + champ.gaps
        if all_gaps:
            unique_gaps = list(set(all_gaps))
            parts.append(f"Data Gaps: {', '.join(unique_gaps)}")
        
        return "\n".join(parts)
```

---

## 4. Qualification Workflows

### 4.1 Workflow Architecture

Qualification workflows are stateful, durable processes that route leads through enrichment → scoring → qualification → routing. Built on Temporal.io for durability and observability.

```
┌─────────────────────────────────────────────────────────────────┐
│              Qualification Workflow Engine                       │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │  Lead    │──▶│ Enrich   │──▶│  Score   │──▶│ Qualify  │  │
│  │  Intake  │   │  Agent   │   │  Engine  │   │  Router  │  │
│  └──────────┘   └──────────┘   └──────────┘   └────┬─────┘  │
│                                                     │         │
│                              ┌──────────────────────┼──────┐  │
│                              │                      │      │  │
│                              ▼                      ▼      ▼  │
│                        ┌──────────┐          ┌──────────┐    │
│                        │  Hot     │          │  Warm    │    │
│                        │  Lead    │          │  Lead    │    │
│                        │  (SQL)   │          │  (Nurture)│   │
│                        └────┬─────┘          └────┬─────┘    │
│                             │                     │          │
│                             ▼                     ▼          │
│                        ┌──────────┐          ┌──────────┐    │
│                        │  Assign  │          │  Drip    │    │
│                        │  to AE   │          │  Campaign│    │
│                        └──────────┘          └──────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Workflow State Machine                       │ │
│  │  NEW → ENRICHING → SCORED → QUALIFIED → ROUTED → ENGAGED │ │
│  │              ↓          ↓         ↓                       │ │
│  │          ENRICHMENT  SCORING   DISQUALIFIED               │ │
│  │           FAILED      FAILED                               │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Workflow Definitions

```python
# workflows/qualification.py
from temporalio import workflow
from dataclasses import dataclass
from enum import Enum

class LeadStatus(Enum):
    NEW = "new"
    ENRICHING = "enriching"
    SCORED = "scored"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    ROUTED = "routed"
    ENGAGED = "engaged"
    ENRICHMENT_FAILED = "enrichment_failed"
    SCORING_FAILED = "scoring_failed"

class LeadTier(Enum):
    HOT = "hot"       # Score >= 80, high confidence
    WARM = "warm"     # Score 50-79, or high score low confidence
    COLD = "cold"     # Score < 50
    DISQUALIFIED = "disqualified"  # Explicit disqualification

@dataclass
class QualificationResult:
    lead_id: str
    status: LeadStatus
    tier: LeadTier
    composite_score: float
    confidence: float
    assigned_to: Optional[str]
    next_action: str
    workflow_id: str

@workflow.defn
class LeadQualificationWorkflow:
    """Temporal workflow for lead qualification."""
    
    def __init__(self):
        self._lead_id: str = ""
        self._status = LeadStatus.NEW
        self._score: float = 0.0
        self._tier: Optional[LeadTier] = None
    
    @workflow.run
    async def run(self, lead_id: str, config: dict) -> QualificationResult:
        """Execute the full qualification workflow."""
        self._lead_id = lead_id
        
        # Step 1: Enrich lead
        self._status = LeadStatus.ENRICHING
        enriched = await workflow.execute_activity(
            "enrich_lead",
            lead_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        if not enriched:
            self._status = LeadStatus.ENRICHMENT_FAILED
            return self._build_result()
        
        # Step 2: Score lead
        self._status = LeadStatus.SCORED
        score_result = await workflow.execute_activity(
            "score_lead",
            {"lead_id": lead_id, "enriched_data": enriched},
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        if not score_result:
            self._status = LeadStatus.SCORING_FAILED
            return self._build_result()
        
        self._score = score_result.composite_score
        
        # Step 3: Determine tier
        self._tier = self._classify_tier(score_result)
        
        # Step 4: Route based on tier
        if self._tier == LeadTier.DISQUALIFIED:
            self._status = LeadStatus.DISQUALIFIED
        else:
            self._status = LeadStatus.QUALIFIED
            await workflow.execute_activity(
                "route_lead",
                {
                    "lead_id": lead_id,
                    "tier": self._tier.value,
                    "score": self._score,
                    "assigned_to": self._determine_assignment(score_result)
                },
                start_to_close_timeout=timedelta(minutes=1)
            )
            self._status = LeadStatus.ROUTED
        
        return self._build_result()
    
    def _classify_tier(self, score_result) -> LeadTier:
        """Classify lead into tier based on score and confidence."""
        score = score_result.composite_score
        confidence = score_result.confidence
        
        # Disqualification rules
        if score < 20:
            return LeadTier.DISQUALIFIED
        if confidence < 0.2:
            return LeadTier.DISQUALIFIED
        
        # Tier classification
        if score >= 80 and confidence >= 0.6:
            return LeadTier.HOT
        elif score >= 50:
            return LeadTier.WARM
        else:
            return LeadTier.COLD
    
    def _determine_assignment(self, score_result) -> Optional[str]:
        """Determine AE assignment based on score and territory."""
        if self._tier == LeadTier.HOT:
            # Round-robin or territory-based assignment
            return self._get_available_ae(score_result)
        return None
    
    def _build_result(self) -> QualificationResult:
        return QualificationResult(
            lead_id=self._lead_id,
            status=self._status,
            tier=self._tier or LeadTier.DISQUALIFIED,
            composite_score=self._score,
            confidence=0.0,
            assigned_to=None,
            next_action=self._determine_next_action(),
            workflow_id=workflow.info().workflow_id
        )
```

### 4.3 Routing Rules

```python
# workflows/routing.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class RoutingRule:
    name: str
    condition: str  # CEL expression
    action: str
    priority: int

class LeadRouter:
    """Routes qualified leads based on configurable rules."""
    
    DEFAULT_RULES = [
        RoutingRule(
            name="hot_lead_immediate",
            condition="tier == 'hot' AND score >= 80",
            action="assign_ae_immediate",
            priority=1
        ),
        RoutingRule(
            name="warm_lead_nurture",
            condition="tier == 'warm' AND score >= 60",
            action="assign_ae_nurture",
            priority=2
        ),
        RoutingRule(
            name="cold_lead_drip",
            condition="tier == 'cold'",
            action="enroll_drip_campaign",
            priority=3
        ),
        RoutingRule(
            name="enterprise_route",
            condition="company_size == '5000+' AND score >= 50",
            action="assign_enterprise_team",
            priority=0  # Highest priority
        ),
        RoutingRule(
            name="disqualified_archive",
            condition="tier == 'disqualified'",
            action="archive_lead",
            priority=99
        ),
    ]
    
    def __init__(self, rules: list[RoutingRule] = None):
        self.rules = sorted(rules or self.DEFAULT_RULES, key=lambda r: r.priority)
    
    def route(self, lead: dict, score_result) -> dict:
        """Evaluate routing rules and return action."""
        context = {
            "tier": score_result.tier,
            "score": score_result.composite_score,
            "confidence": score_result.confidence,
            "company_size": lead.get("company_size", ""),
            "industry": lead.get("industry", ""),
            "lead_source": lead.get("lead_source", ""),
        }
        
        for rule in self.rules:
            if self._evaluate_condition(rule.condition, context):
                return {
                    "rule": rule.name,
                    "action": rule.action,
                    "context": context
                }
        
        # Default action
        return {
            "rule": "default",
            "action": "enroll_drip_campaign",
            "context": context
        }
    
    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """Evaluate CEL-like condition expression."""
        # Simplified CEL evaluation
        # In production, use cel-python library
        try:
            return eval(condition, {"__builtins__": {}}, context)
        except:
            return False
```

---

## 5. Predictive Analytics

### 5.1 Conversion Prediction Model

```python
# analytics/conversion_model.py
import xgboost as xgb
import shap
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class ConversionPrediction:
    lead_id: str
    conversion_probability: float
    expected_value: float
    predicted_close_date: Optional[str]
    confidence_interval: tuple[float, float]
    top_features: list[dict]
    model_version: str

class ConversionPredictor:
    """XGBoost-based conversion prediction with SHAP explainability."""
    
    def __init__(self, model_path: str, feature_store: "FeatureStore"):
        self.model = xgb.Booster()
        self.model.load_model(model_path)
        self.explainer = shap.TreeExplainer(self.model)
        self.feature_store = feature_store
        self.model_version = self._extract_version(model_path)
    
    def predict(self, lead_id: str, enriched_data: dict) -> ConversionPrediction:
        """Predict conversion probability for a lead."""
        
        # Fetch features from feature store
        features = self.feature_store.get_features(lead_id, enriched_data)
        feature_vector = self._vectorize(features)
        
        # Predict
        dmatrix = xgb.DMatrix([feature_vector])
        probability = float(self.model.predict(dmatrix)[0])
        
        # SHAP explainability
        shap_values = self.explainer.shap_values(dmatrix)
        top_features = self._get_top_features(shap_values, features)
        
        # Expected value
        deal_size = enriched_data.get("firmographic", {}).get("estimated_deal_size", 0)
        expected_value = probability * deal_size
        
        # Confidence interval (bootstrap)
        ci_lower, ci_upper = self._compute_confidence_interval(feature_vector)
        
        # Predicted close date
        predicted_close = self._predict_close_date(probability, features)
        
        return ConversionPrediction(
            lead_id=lead_id,
            conversion_probability=probability,
            expected_value=expected_value,
            predicted_close_date=predicted_close,
            confidence_interval=(ci_lower, ci_upper),
            top_features=top_features,
            model_version=self.model_version
        )
    
    def _get_top_features(self, shap_values, features) -> list[dict]:
        """Get top contributing features from SHAP values."""
        feature_names = list(features.keys())
        values = shap_values[0] if isinstance(shap_values, list) else shap_values
        
        contributions = [
            {"feature": name, "value": features[name], "impact": float(impact)}
            for name, impact in zip(feature_names, values)
        ]
        
        # Sort by absolute impact
        contributions.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return contributions[:10]
    
    def _predict_close_date(self, probability: float, features: dict) -> Optional[str]:
        """Predict close date based on probability and engagement signals."""
        if probability < 0.1:
            return None
        
        # Base timeline on probability
        if probability > 0.7:
            base_days = 14
        elif probability > 0.5:
            base_days = 30
        elif probability > 0.3:
            base_days = 60
        else:
            base_days = 90
        
        # Adjust for engagement
        last_activity = features.get("last_activity_days_ago", 30)
        if last_activity > 14:
            base_days += 7
        
        predicted = datetime.now() + timedelta(days=base_days)
        return predicted.strftime("%Y-%m-%d")
```

### 5.2 Lead Scoring Model Training Pipeline

```python
# analytics/training_pipeline.py
from datetime import datetime, timedelta
from typing import Optional
import mlflow

class LeadScoringTrainingPipeline:
    """MLflow-managed training pipeline for lead scoring models."""
    
    def __init__(self, config: dict):
        self.config = config
        self.mlflow_client = mlflow.MlflowClient()
        self.feature_store = FeatureStore(config["feature_store"])
        self.model_registry = ModelRegistry(config["model_registry"])
    
    def run(self, training_data_query: str) -> str:
        """Execute full training pipeline."""
        
        with mlflow.start_run(run_name=f"lead_scoring_{datetime.now().strftime('%Y%m%d')}"):
            # Step 1: Extract training data
            training_data = self._extract_training_data(training_data_query)
            
            # Step 2: Feature engineering
            features, labels = self._engineer_features(training_data)
            
            # Step 3: Train/test split
            X_train, X_test, y_train, y_test = self._split_data(features, labels)
            
            # Step 4: Train model
            model = self._train_model(X_train, y_train)
            
            # Step 5: Evaluate
            metrics = self._evaluate_model(model, X_test, y_test)
            mlflow.log_metrics(metrics)
            
            # Step 6: SHAP analysis
            self._log_shap_analysis(model, X_test)
            
            # Step 7: Register model
            model_version = self._register_model(model, metrics)
            
            # Step 8: Deploy if metrics pass threshold
            if metrics["auc_roc"] > self.config.get("min_auc_threshold", 0.75):
                self._deploy_model(model_version)
            
            return model_version
    
    def _train_model(self, X_train, y_train) -> xgb.XGBClassifier:
        """Train XGBoost classifier with hyperparameter tuning."""
        model = xgb.XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=self._compute_class_weight(y_train),
            eval_metric="auc",
            early_stopping_rounds=50,
            random_state=42
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train)],
            verbose=False
        )
        
        return model
    
    def _evaluate_model(self, model, X_test, y_test) -> dict:
        """Compute evaluation metrics."""
        from sklearn.metrics import (
            roc_auc_score, precision_recall_curve, 
            average_precision_score, classification_report
        )
        
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        return {
            "auc_roc": roc_auc_score(y_test, y_prob),
            "average_precision": average_precision_score(y_test, y_prob),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred),
        }
```

### 5.3 Feature Store

```python
# analytics/feature_store.py
import redis
import json
from typing import Optional
from datetime import datetime, timedelta

class FeatureStore:
    """Redis-backed feature store for real-time and batch features."""
    
    def __init__(self, config: dict):
        self.redis = redis.Redis(
            host=config.get("host", "localhost"),
            port=config.get("port", 6379),
            db=config.get("db", 0),
            decode_responses=True
        )
        self.ttl_seconds = config.get("ttl_seconds", 86400)
        self.feature_definitions = self._load_feature_definitions()
    
    def get_features(self, lead_id: str, enriched_data: dict) -> dict:
        """Fetch all features for a lead."""
        features = {}
        
        # Real-time features from Redis
        real_time = self._get_real_time_features(lead_id)
        features.update(real_time)
        
        # Enriched data features
        enriched = self._extract_enriched_features(enriched_data)
        features.update(enriched)
        
        # Computed features
        computed = self._compute_features(features)
        features.update(computed)
        
        return features
    
    def _get_real_time_features(self, lead_id: str) -> dict:
        """Fetch real-time features from Redis."""
        key = f"lead:features:{lead_id}"
        data = self.redis.hgetall(key)
        return {k: self._deserialize(v) for k, v in data.items()}
    
    def _extract_enriched_features(self, enriched: dict) -> dict:
        """Extract features from enriched lead data."""
        firmographic = enriched.get("firmographic", {})
        technographic = enriched.get("technographic", {})
        intent = enriched.get("intent", {})
        
        return {
            "company_size_encoded": self._encode_company_size(firmographic.get("company_size")),
            "revenue_range_encoded": self._encode_revenue(firmographic.get("revenue_range")),
            "industry_encoded": self._encode_industry(firmographic.get("industry")),
            "tech_stack_count": len(technographic.get("tech_stack", [])),
            "has_crm": int(technographic.get("crm_system") is not None),
            "has_analytics": int(len(technographic.get("analytics_tools", [])) > 0),
            "intent_score": intent.get("intent_score", 0),
            "surge_score": intent.get("surge_score", 0),
            "buying_stage_encoded": self._encode_buying_stage(intent.get("buying_stage")),
            "content_consumption_count": len(intent.get("content_consumption", [])),
            "competitor_mention_count": len(intent.get("competitor_mentions", [])),
        }
    
    def _compute_features(self, features: dict) -> dict:
        """Compute derived features."""
        computed = {}
        
        # Engagement velocity
        if "activity_count_7d" in features and "activity_count_30d" in features:
            computed["engagement_velocity"] = (
                features["activity_count_7d"] * 4 / max(features["activity_count_30d"], 1)
            )
        
        # Intent-to-engagement ratio
        if "intent_score" in features and "activity_count_30d" in features:
            computed["intent_engagement_ratio"] = (
                features["intent_score"] / max(features["activity_count_30d"], 1)
            )
        
        # Firmographic fit score
        computed["firmographic_fit"] = self._compute_firmographic_fit(features)
        
        return computed
```

---

## 6. CRM Integration

### 6.1 CRM Connector Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   CRM Integration Layer                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CRM Connector Factory                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │Salesforce│  │ HubSpot  │  │  Custom  │              │   │
│  │  │ Connector│  │ Connector│  │ Connector│              │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              │   │
│  │       │             │             │                      │   │
│  │       └─────────────┼─────────────┘                      │   │
│  │                     ▼                                    │   │
│  │         ┌─────────────────────┐                         │   │
│  │         │  Unified Lead Schema │                         │   │
│  │         │  (Canonical Model)   │                         │   │
│  │         └─────────────────────┘                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Sync Engine                                  │   │
│  │  • Bidirectional sync  • Conflict resolution             │   │
│  │  • Field mapping       • Rate limiting                   │   │
│  │  • Webhook handling    • Retry with backoff              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Unified Lead Schema

```python
# crm/schema.py
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class UnifiedLead:
    """Canonical lead schema across all CRM systems."""
    
    # Identity
    id: str
    crm_source: str  # "salesforce", "hubspot", "custom"
    crm_id: str
    
    # Contact Info
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    
    # Company Info
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    revenue_range: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    
    # Lead Metadata
    lead_source: Optional[str] = None
    lead_status: Optional[str] = None
    lead_score: Optional[float] = None
    lead_tier: Optional[str] = None
    
    # Engagement
    created_at: str = ""
    updated_at: str = ""
    last_activity_at: Optional[str] = None
    email_opens: int = 0
    email_clicks: int = 0
    meetings_booked: int = 0
    
    # Custom Fields
    custom_fields: dict = field(default_factory=dict)
    
    # Enrichment
    enrichment_data: dict = field(default_factory=dict)
    scoring_data: dict = field(default_factory=dict)
```

### 6.3 Salesforce Connector

```python
# crm/salesforce.py
from simple_salesforce import Salesforce
from typing import Optional

class SalesforceConnector:
    """Salesforce CRM connector with bidirectional sync."""
    
    def __init__(self, config: dict):
        self.sf = Salesforce(
            username=config["username"],
            password=config["password"],
            security_token=config["security_token"],
            domain=config.get("domain", "login")
        )
        self.field_mapping = self._load_field_mapping()
    
    def upsert_lead(self, lead: UnifiedLead) -> str:
        """Create or update lead in Salesforce."""
        sf_data = self._map_to_salesforce(lead)
        
        # Check for existing lead
        existing = self._find_existing_lead(lead.email)
        
        if existing:
            # Update
            self.sf.Lead.update(existing["Id"], sf_data)
            return existing["Id"]
        else:
            # Create
            result = self.sf.Lead.create(sf_data)
            return result["id"]
    
    def get_lead(self, lead_id: str) -> UnifiedLead:
        """Fetch lead from Salesforce."""
        sf_lead = self.sf.Lead.get(lead_id)
        return self._map_from_salesforce(sf_lead)
    
    def update_score(self, lead_id: str, score_data: dict):
        """Update lead score fields in Salesforce."""
        update_data = {
            "Lead_Score__c": score_data.get("composite_score"),
            "Lead_Tier__c": score_data.get("tier"),
            "BANT_Score__c": score_data.get("bant_score"),
            "MEDDIC_Score__c": score_data.get("meddic_score"),
            "CHAMP_Score__c": score_data.get("champ_score"),
            "Score_Confidence__c": score_data.get("confidence"),
            "Score_Explanation__c": score_data.get("explanation"),
            "Last_Scored_At__c": datetime.now().isoformat(),
            "Conversion_Probability__c": score_data.get("conversion_probability"),
            "Expected_Value__c": score_data.get("expected_value"),
        }
        self.sf.Lead.update(lead_id, update_data)
    
    def _map_to_salesforce(self, lead: UnifiedLead) -> dict:
        """Map unified lead to Salesforce field names."""
        return {
            "Email": lead.email,
            "FirstName": lead.first_name,
            "LastName": lead.last_name,
            "Phone": lead.phone,
            "Title": lead.title,
            "Department": lead.department,
            "Company": lead.company_name,
            "Industry": lead.industry,
            "NumberOfEmployees": self._parse_company_size(lead.company_size),
            "LeadSource": lead.lead_source,
            "Status": lead.lead_status,
            "Country": lead.country,
            "City": lead.city,
        }
    
    def _map_from_salesforce(self, sf_lead: dict) -> UnifiedLead:
        """Map Salesforce lead to unified schema."""
        return UnifiedLead(
            id=f"sf_{sf_lead['Id']}",
            crm_source="salesforce",
            crm_id=sf_lead["Id"],
            email=sf_lead.get("Email", ""),
            first_name=sf_lead.get("FirstName"),
            last_name=sf_lead.get("LastName"),
            phone=sf_lead.get("Phone"),
            title=sf_lead.get("Title"),
            department=sf_lead.get("Department"),
            company_name=sf_lead.get("Company"),
            industry=sf_lead.get("Industry"),
            lead_source=sf_lead.get("LeadSource"),
            lead_status=sf_lead.get("Status"),
            country=sf_lead.get("Country"),
            city=sf_lead.get("City"),
            lead_score=sf_lead.get("Lead_Score__c"),
            lead_tier=sf_lead.get("Lead_Tier__c"),
        )
```

### 6.4 HubSpot Connector

```python
# crm/hubspot.py
from hubspot import HubSpot
from typing import Optional

class HubSpotConnector:
    """HubSpot CRM connector with bidirectional sync."""
    
    def __init__(self, config: dict):
        self.client = HubSpot(api_key=config["api_key"])
        self.field_mapping = self._load_field_mapping()
    
    def upsert_lead(self, lead: UnifiedLead) -> str:
        """Create or update lead in HubSpot."""
        properties = self._map_to_hubspot(lead)
        
        # Check for existing contact by email
        existing = self._find_by_email(lead.email)
        
        if existing:
            # Update
            self.client.crm.contacts.basic_api.update(
                contact_id=existing["id"],
                properties=properties
            )
            return existing["id"]
        else:
            # Create
            result = self.client.crm.contacts.basic_api.create(
                properties=properties
            )
            return result.id
    
    def update_score(self, lead_id: str, score_data: dict):
        """Update lead score fields in HubSpot."""
        properties = {
            "lead_score": score_data.get("composite_score"),
            "lead_tier": score_data.get("tier"),
            "bant_score": score_data.get("bant_score"),
            "meddic_score": score_data.get("meddic_score"),
            "champ_score": score_data.get("champ_score"),
            "score_confidence": score_data.get("confidence"),
            "score_explanation": score_data.get("explanation"),
            "conversion_probability": score_data.get("conversion_probability"),
            "expected_value": score_data.get("expected_value"),
        }
        self.client.crm.contacts.basic_api.update(
            contact_id=lead_id,
            properties=properties
        )
    
    def _map_to_hubspot(self, lead: UnifiedLead) -> dict:
        """Map unified lead to HubSpot properties."""
        return {
            "email": lead.email,
            "firstname": lead.first_name,
            "lastname": lead.last_name,
            "phone": lead.phone,
            "jobtitle": lead.title,
            "department": lead.department,
            "company": lead.company_name,
            "industry": lead.industry,
            "num_employees": self._parse_company_size(lead.company_size),
            "lead_source": lead.lead_source,
            "hs_lead_status": lead.lead_status,
            "country": lead.country,
            "city": lead.city,
        }
```

### 6.5 Webhook Handler

```python
# crm/webhooks.py
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

class CRMWebhookHandler:
    """Handles incoming webhooks from CRM systems."""
    
    def __init__(self, config: dict):
        self.salesforce_secret = config.get("salesforce_webhook_secret")
        self.hubspot_secret = config.get("hubspot_webhook_secret")
        self.event_bus = EventBus(config["event_bus"])
    
    async def handle_salesforce(self, request: Request):
        """Process Salesforce outbound message webhook."""
        # Verify signature
        signature = request.headers.get("X-Salesforce-Signature")
        body = await request.body()
        
        if not self._verify_salesforce_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        payload = await request.json()
        
        for event in payload.get("events", []):
            await self.event_bus.publish("crm.salesforce.event", {
                "event_type": event.get("type"),
                "lead_id": event.get("lead_id"),
                "data": event.get("data"),
                "timestamp": event.get("timestamp")
            })
        
        return {"status": "ok"}
    
    async def handle_hubspot(self, request: Request):
        """Process HubSpot webhook."""
        signature = request.headers.get("X-HubSpot-Signature")
        body = await request.body()
        
        if not self._verify_hubspot_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        events = await request.json()
        
        for event in events:
            await self.event_bus.publish("crm.hubspot.event", {
                "event_type": event.get("subscriptionType"),
                "lead_id": event.get("objectId"),
                "data": event,
                "timestamp": event.get("occurredAt")
            })
        
        return {"status": "ok"}
```

---

## 7. Real-Time Scoring API

### 7.1 API Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Real-Time Scoring API                           │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  API Gateway (FastAPI)                    │   │
│  │  • Rate limiting  • Authentication  • Request validation │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                      │
│  ┌───────────────────────┼─────────────────────────────────┐   │
│  │                       ▼                                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │   │
│  │  │  Score   │  │  Batch   │  │  Health  │             │   │
│  │  │  Endpoint│  │  Score   │  │  Check   │             │   │
│  │  └────┬─────┘  └────┬─────┘  └──────────┘             │   │
│  │       │              │                                   │   │
│  │       └──────────────┼───────────────────────────────────┘   │
│  │                      ▼                                       │
│  │         ┌─────────────────────┐                             │
│  │         │  Scoring Service    │                             │
│  │         │  • Enrichment       │                             │
│  │         │  • BANT/MEDDIC/CHAMP│                             │
│  │         │  • Fusion           │                             │
│  │         │  • Prediction       │                             │
│  │         └─────────────────────┘                             │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 API Endpoints

```python
# api/scoring_api.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import time

app = FastAPI(
    title="Lead Scoring API",
    description="AI-powered lead scoring and qualification",
    version="1.0.0"
)

# Request/Response Models
class LeadScoreRequest(BaseModel):
    lead_id: str = Field(..., description="Unique lead identifier")
    email: str = Field(..., description="Lead email address")
    company_name: Optional[str] = Field(None, description="Company name")
    company_domain: Optional[str] = Field(None, description="Company domain")
    title: Optional[str] = Field(None, description="Job title")
    phone: Optional[str] = Field(None, description="Phone number")
    country: Optional[str] = Field(None, description="Country")
    lead_source: Optional[str] = Field(None, description="Lead source")
    enrich: bool = Field(True, description="Whether to enrich the lead")
    frameworks: list[str] = Field(
        default=["bant", "meddic", "champ"],
        description="Scoring frameworks to use"
    )

class LeadScoreResponse(BaseModel):
    lead_id: str
    composite_score: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    tier: str
    framework_scores: dict
    feature_attribution: dict
    explanation: str
    conversion_probability: Optional[float] = None
    expected_value: Optional[float] = None
    processing_time_ms: float
    model_version: str

class BatchScoreRequest(BaseModel):
    leads: list[LeadScoreRequest] = Field(..., max_items=100)

class BatchScoreResponse(BaseModel):
    results: list[LeadScoreResponse]
    total_processed: int
    total_time_ms: float

# API Endpoints
@app.post("/api/v1/score", response_model=LeadScoreResponse)
async def score_lead(
    request: LeadScoreRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Score a single lead in real-time."""
    start_time = time.time()
    
    # Initialize services
    enrichment_service = EnrichmentService()
    scoring_service = ScoringService()
    prediction_service = PredictionService()
    
    # Enrich if requested
    enriched_data = {}
    if request.enrich:
        enriched_data = await enrichment_service.enrich_lead(request.dict())
    
    # Score lead
    score_result = scoring_service.score(
        lead=request.dict(),
        enriched_data=enriched_data,
        frameworks=request.frameworks
    )
    
    # Predict conversion
    prediction = prediction_service.predict(request.lead_id, enriched_data)
    
    processing_time = (time.time() - start_time) * 1000
    
    # Async: Update CRM
    background_tasks.add_task(
        update_crm_score,
        request.lead_id,
        score_result,
        prediction
    )
    
    return LeadScoreResponse(
        lead_id=request.lead_id,
        composite_score=score_result.composite_score,
        confidence=score_result.confidence,
        tier=score_result.tier,
        framework_scores={
            "bant": score_result.bant_score,
            "meddic": score_result.meddic_score,
            "champ": score_result.champ_score,
        },
        feature_attribution=score_result.feature_attribution,
        explanation=score_result.explanation,
        conversion_probability=prediction.conversion_probability if prediction else None,
        expected_value=prediction.expected_value if prediction else None,
        processing_time_ms=processing_time,
        model_version=prediction.model_version if prediction else "N/A"
    )

@app.post("/api/v1/score/batch", response_model=BatchScoreResponse)
async def score_batch(
    request: BatchScoreRequest,
    api_key: str = Depends(verify_api_key)
):
    """Score multiple leads in batch."""
    start_time = time.time()
    
    results = []
    for lead_request in request.leads:
        result = await score_lead(lead_request, BackgroundTasks(), api_key)
        results.append(result)
    
    total_time = (time.time() - start_time) * 1000
    
    return BatchScoreResponse(
        results=results,
        total_processed=len(results),
        total_time_ms=total_time
    )

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "enrichment": await check_enrichment_service(),
            "scoring": await check_scoring_service(),
            "prediction": await check_prediction_service(),
            "crm": await check_crm_connection(),
        }
    }

@app.get("/api/v1/lead/{lead_id}/score-history")
async def get_score_history(
    lead_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get scoring history for a lead."""
    history = await ScoreRepository().get_history(lead_id)
    return {"lead_id": lead_id, "history": history}
```

### 7.3 Performance Targets

| Metric | Target | Description |
|--------|--------|-------------|
| p50 Latency | < 50ms | Median scoring latency |
| p95 Latency | < 100ms | 95th percentile latency |
| p99 Latency | < 200ms | 99th percentile latency |
| Throughput | > 1000 req/s | Sustained throughput |
| Availability | 99.9% | Uptime SLA |
| Enrichment Cache Hit | > 80% | Cache hit rate for enrichment |

---

## 8. GRC_Claw Governance Integration

### 8.1 Governance Architecture

The lead scoring system integrates with GRC_Claw's governance layer to ensure all scoring decisions are policy-compliant, auditable, and explainable.

```
┌─────────────────────────────────────────────────────────────────┐
│              GRC_Claw Governance Integration                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  GRC_Claw Control Plane                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │ Identity │  │  Trust   │  │  Policy  │              │   │
│  │  │ (DID)    │  │  Engine  │  │  Engine  │              │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              │   │
│  │       │             │             │                      │   │
│  │       └─────────────┼─────────────┘                      │   │
│  │                     ▼                                    │   │
│  │         ┌─────────────────────┐                         │   │
│  │         │  Governance         │                         │   │
│  │         │  Orchestrator       │                         │   │
│  │         └──────────┬──────────┘                         │   │
│  └────────────────────┼────────────────────────────────────┘   │
│                       │                                         │
│  ┌────────────────────┼────────────────────────────────────┐   │
│  │                    ▼                                    │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │           Lead Scoring System                    │   │   │
│  │  │                                                  │   │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │   │
│  │  │  │ Enrich   │  │  Score   │  │  Route   │      │   │   │
│  │  │  │  Agent   │  │  Engine  │  │  Lead    │      │   │   │
│  │  │  │          │  │          │  │          │      │   │   │
│  │  │  │ • DID    │  │ • DID    │  │ • DID    │      │   │   │
│  │  │  │ • Policy │  │ • Policy │  │ • Policy │      │   │   │
│  │  │  │ • Audit  │  │ • Audit  │  │ • Audit  │      │   │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘      │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Policy Definitions

```rego
# policies/lead_scoring.rego
package grc_claw.lead_scoring

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Allow scoring if agent has valid identity and capability
allow if {
    valid_identity
    has_capability("lead.score")
    within_rate_limit
    data_quality_sufficient
}

# Allow enrichment if agent has valid identity and capability
allow_enrichment if {
    valid_identity
    has_capability("lead.enrich")
    within_rate_limit
    source_allowed
}

# Allow routing if agent has valid identity and capability
allow_routing if {
    valid_identity
    has_capability("lead.route")
    within_rate_limit
    score_confidence_sufficient
}

# Identity validation
valid_identity if {
    input.subject.did
    input.subject.did == data.agents[input.subject.did].did
    data.agents[input.subject.did].status == "active"
}

# Capability check
has_capability(capability) if {
    capability in data.agents[input.subject.did].capabilities
}

# Rate limiting
within_rate_limit if {
    count := data.rate_limits[input.subject.did].count
    count < data.rate_limits[input.subject.did].limit
}

# Data quality check
data_quality_sufficient if {
    input.context.confidence >= 0.3
}

# Source allowlist
source_allowed if {
    input.context.sources[_] in data.allowed_sources
}

# Score confidence for routing
score_confidence_sufficient if {
    input.context.confidence >= 0.5
}

# Denial reasons
reason := "invalid_identity" if { not valid_identity }
reason := "missing_capability" if { not has_capability("lead.score") }
reason := "rate_limit_exceeded" if { not within_rate_limit }
reason := "insufficient_data_quality" if { not data_quality_sufficient }
reason := "source_not_allowed" if { not source_allowed }
reason := "insufficient_confidence" if { not score_confidence_sufficient }
```

### 8.3 Audit Integration

```python
# governance/audit.py
from grc_claw import AuditLogger, AgentIdentity
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ScoringAuditEvent:
    event_id: str
    timestamp: str
    agent_did: str
    action: str
    lead_id: str
    input_hash: str
    output_hash: str
    policy_decision: str
    policy_reason: str
    model_version: str
    processing_time_ms: float
    metadata: dict

class ScoringAuditLogger:
    """Audit logger for lead scoring decisions."""
    
    def __init__(self, identity: AgentIdentity, audit: AuditLogger):
        self.identity = identity
        self.audit = audit
    
    def log_scoring_decision(self, lead_id: str, input_data: dict, 
                              output_data: dict, policy_decision: str,
                              policy_reason: str, model_version: str,
                              processing_time_ms: float):
        """Log a scoring decision to the Merkle audit chain."""
        
        event = ScoringAuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            agent_did=self.identity.did,
            action="lead.score",
            lead_id=lead_id,
            input_hash=self._hash_data(input_data),
            output_hash=self._hash_data(output_data),
            policy_decision=policy_decision,
            policy_reason=policy_reason,
            model_version=model_version,
            processing_time_ms=processing_time_ms,
            metadata={
                "frameworks_used": output_data.get("frameworks", []),
                "composite_score": output_data.get("composite_score"),
                "confidence": output_data.get("confidence"),
                "tier": output_data.get("tier"),
            }
        )
        
        self.audit.log(event)
    
    def _hash_data(self, data: dict) -> str:
        """Create deterministic hash of data for audit."""
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
```

### 8.4 Model Governance Integration

```python
# governance/model_governance.py
from grc_claw import ModelRegistry, RiskScorer

class ScoringModelGovernance:
    """Integrates lead scoring models with GRC_Claw model governance."""
    
    def __init__(self, model_registry: ModelRegistry, risk_scorer: RiskScorer):
        self.model_registry = model_registry
        self.risk_scorer = risk_scorer
    
    def register_scoring_model(self, model_path: str, metadata: dict) -> str:
        """Register a new scoring model with governance checks."""
        
        # Risk assessment
        risk_score = self.risk_scorer.assess_model(model_path, metadata)
        
        if risk_score > 0.7:
            raise ModelGovernanceError(
                f"Model risk score {risk_score} exceeds threshold. "
                "Manual review required."
            )
        
        # Register model
        model_id = self.model_registry.register(
            path=model_path,
            metadata={
                **metadata,
                "risk_score": risk_score,
                "approved_by": "automated",
                "approval_date": datetime.utcnow().isoformat(),
            }
        )
        
        return model_id
    
    def validate_model_for_serving(self, model_id: str) -> bool:
        """Validate model is approved for serving."""
        model = self.model_registry.get(model_id)
        
        checks = [
            model.status == "approved",
            model.risk_score < 0.7,
            model.drift_score < 0.3,
            model.bias_score < 0.2,
            model.last_validated > datetime.now() - timedelta(days=7),
        ]
        
        return all(checks)
```

---

## 9. Data Flow Diagrams

### 9.1 End-to-End Lead Scoring Flow

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Lead   │────▶│  Lead    │────▶│  Lead    │────▶│  Lead    │
│  Source │     │  Intake  │     │  Enrich  │     │  Score   │
│         │     │  Queue   │     │  Agent   │     │  Engine  │
└─────────┘     └──────────┘     └──────────┘     └────┬─────┘
                                                       │
                                                       ▼
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  CRM    │◀────│  Lead    │◀────│  Lead    │◀────│  Score   │
│  Update │     │  Route   │     │  Qualify │     │  Fusion  │
└─────────┘     └──────────┘     └──────────┘     └──────────┘

Detailed Flow:

1. Lead Source → Lead Intake Queue
   • Web form submission
   • CRM import
   • API ingestion
   • Event-driven (Kafka)

2. Lead Intake → Enrichment Agent
   • Validate lead data
   • Deduplicate
   • Trigger enrichment workflow

3. Enrichment Agent → Scoring Engine
   • Fetch firmographic data
   • Fetch technographic data
   • Fetch intent data
   • Entity resolution
   • Confidence scoring

4. Scoring Engine → Score Fusion
   • BANT scoring
   • MEDDIC scoring
   • CHAMP scoring
   • Weighted fusion
   • Feature attribution

5. Score Fusion → Qualification
   • Tier classification
   • Routing rules
   • Assignment logic

6. Qualification → CRM Update
   • Update lead score
   • Update lead tier
   • Assign to AE
   • Trigger next action
```

### 9.2 Real-Time Scoring API Flow

```
Client Request
      │
      ▼
┌──────────┐     ┌──────────┐     ┌──────────┐
│  API     │────▶│  Auth    │────▶│  Rate    │
│  Gateway │     │  Check   │     │  Limit   │
└──────────┘     └──────────┘     └────┬─────┘
                                      │
                                      ▼
                               ┌──────────┐
                               │  Policy  │
                               │  Engine  │
                               │  (OPA)   │
                               └────┬─────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
             ┌──────────┐   ┌──────────┐   ┌──────────┐
             │  Lead    │   │  Feature │   │  Model   │
             │  Cache   │   │  Store   │   │  Cache   │
             │  Check   │   │  (Redis) │   │  Check   │
             └────┬─────┘   └────┬─────┘   └────┬─────┘
                  │               │               │
                  └───────────────┼───────────────┘
                                  │
                                  ▼
                           ┌──────────┐
                           │  Score   │
                           │  Compute │
                           │  Engine  │
                           └────┬─────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │  BANT    │ │  MEDDIC  │ │  CHAMP   │
             │  Score   │ │  Score   │ │  Score   │
             └────┬─────┘ └────┬─────┘ └────┬─────┘
                  │           │           │
                  └───────────┼───────────┘
                              │
                              ▼
                       ┌──────────┐
                       │  Score   │
                       │  Fusion  │
                       └────┬─────┘
                            │
                            ▼
                       ┌──────────┐
                       │  Response│
                       │  + Audit │
                       └──────────┘
```

### 9.3 Enrichment Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Enrichment Data Flow                           │
│                                                                 │
│  ┌──────────┐                                                   │
│  │  Raw     │                                                   │
│  │  Lead    │                                                   │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐              │
│  │  Entity  │────▶│  Data    │────▶│  Data    │              │
│  │  Resolve │     │  Fusion  │     │  Quality │              │
│  └──────────┘     └──────────┘     └────┬─────┘              │
│                                         │                      │
│       ┌─────────────────────────────────┼─────────────────┐   │
│       │                                 │                 │   │
│       ▼                                 ▼                 ▼   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Internal │  │ Clearbit │  │ ZoomInfo │  │ Bombora  │    │
│  │ CRM      │  │ Firmo    │  │ Firmo    │  │ Intent   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ BuiltWith│  │ LinkedIn │  │ G2       │  │ 6sense   │    │
│  │ Tech     │  │ Social   │  │ Reviews  │  │ Intent   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│       │              │              │              │         │
│       └──────────────┴──────────────┴──────────────┘         │
│                          │                                    │
│                          ▼                                    │
│                   ┌──────────┐                                │
│                   │ Enriched │                                │
│                   │ Lead     │                                │
│                   │ Record   │                                │
│                   └──────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

### 9.4 Event-Driven Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Event-Driven Architecture                       │
│                                                                 │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐              │
│  │  Lead    │     │  Kafka   │     │  Lead    │              │
│  │  Created │────▶│  Topic   │────▶│  Enrich  │              │
│  │  Event   │     │          │     │  Worker  │              │
│  └──────────┘     └──────────┘     └────┬─────┘              │
│                                         │                      │
│                                         ▼                      │
│                                  ┌──────────┐                 │
│                                  │  Lead    │                 │
│                                  │  Enriched│                 │
│                                  │  Event   │                 │
│                                  └────┬─────┘                 │
│                                       │                        │
│                                       ▼                        │
│                                ┌──────────┐                   │
│                                │  Score   │                   │
│                                │  Worker  │                   │
│                                └────┬─────┘                   │
│                                     │                          │
│                                     ▼                          │
│                              ┌──────────┐                     │
│                              │  Lead    │                     │
│                              │  Scored  │                     │
│                              │  Event   │                     │
│                              └────┬─────┘                     │
│                                   │                            │
│                    ┌──────────────┼──────────────┐            │
│                    │              │              │             │
│                    ▼              ▼              ▼             │
│             ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│             │  Route   │  │  CRM     │  │  Audit   │        │
│             │  Worker  │  │  Sync    │  │  Logger  │        │
│             └──────────┘  └──────────┘  └──────────┘        │
│                                                                 │
│  Topics:                                                        │
│  • lead.created                                                 │
│  • lead.enriched                                                │
│  • lead.scored                                                  │
│  • lead.routed                                                  │
│  • lead.qualified                                               │
│  • lead.disqualified                                            │
│  • scoring.model.updated                                        │
│  • enrichment.source.updated                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Implementation Roadmap

### 10.1 Phase Overview

```
Phase 1 (Weeks 1-4)     Phase 2 (Weeks 5-8)     Phase 3 (Weeks 9-12)
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Foundation     │     │  Core Engine    │     │  Integration    │
│                 │     │                 │     │                 │
│ • Project setup │     │ • BANT scorer   │     │ • CRM connectors│
│ • Data models   │     │ • MEDDIC scorer │     │ • API gateway   │
│ • Feature store │     │ • CHAMP scorer  │     │ • Webhooks      │
│ • Enrichment    │     │ • Score fusion  │     │ • Governance    │
│   agent (v1)    │     │ • Qualification │     │ • Analytics     │
│ • GRC_Claw      │     │   workflows     │     │ • Testing       │
│   integration   │     │ • Predictive    │     │ • Deployment    │
└─────────────────┘     │   analytics     │     └─────────────────┘
                        └─────────────────┘
```

### 10.2 Phase 1: Foundation (Weeks 1-4)

| Week | Task | Deliverable | Dependencies |
|------|------|-------------|--------------|
| 1 | Project setup & scaffolding | Repo structure, CI/CD, dev environment | None |
| 1 | Data models & schemas | Unified lead schema, enrichment schema | None |
| 2 | Feature store implementation | Redis feature store, feature definitions | Week 1 |
| 2 | GRC_Claw identity integration | DID registration, capability delegation | Week 1 |
| 3 | Enrichment agent v1 | Internal data enrichment, entity resolution | Week 2 |
| 3 | External data connectors | Clearbit, ZoomInfo connectors | Week 2 |
| 4 | Enrichment pipeline | Full enrichment pipeline with confidence scoring | Week 3 |
| 4 | Audit logging | Merkle audit chain integration | Week 2 |

**Phase 1 Milestone:** Enriched lead records with confidence scores, fully audited through GRC_Claw.

### 10.3 Phase 2: Core Engine (Weeks 5-8)

| Week | Task | Deliverable | Dependencies |
|------|------|-------------|--------------|
| 5 | BANT scorer | BANT scoring engine with configurable weights | Phase 1 |
| 5 | MEDDIC scorer | MEDDIC scoring engine | Phase 1 |
| 6 | CHAMP scorer | CHAMP scoring engine | Phase 1 |
| 6 | Score fusion | Multi-framework fusion with explainability | Week 5 |
| 7 | Qualification workflows | Temporal workflows, routing rules | Week 6 |
| 7 | Predictive analytics | XGBoost conversion model, SHAP | Week 6 |
| 8 | Model training pipeline | MLflow pipeline, model registry | Week 7 |
| 8 | Real-time scoring API | FastAPI endpoints, rate limiting | Week 6 |

**Phase 2 Milestone:** Real-time multi-framework scoring API with >1000 req/s throughput.

### 10.4 Phase 3: Integration (Weeks 9-12)

| Week | Task | Deliverable | Dependencies |
|------|------|-------------|--------------|
| 9 | Salesforce connector | Bidirectional sync, field mapping | Phase 2 |
| 9 | HubSpot connector | Bidirectional sync, field mapping | Phase 2 |
| 10 | Webhook handlers | CRM webhook processing, event bus | Week 9 |
| 10 | GRC_Claw policy integration | OPA policies, governance enforcement | Phase 1 |
| 11 | Model governance | Risk scoring, drift detection | Phase 2 |
| 11 | Analytics dashboard | Score distribution, conversion tracking | Phase 2 |
| 12 | Load testing & optimization | Performance tuning, caching | Week 10 |
| 12 | Production deployment | Blue-green deployment, monitoring | Week 11 |

**Phase 3 Milestone:** Production-ready system with CRM integration, governance, and monitoring.

### 10.5 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Scoring Accuracy (AUC-ROC) | > 0.80 | Conversion prediction AUC |
| Enrichment Coverage | > 90% | % leads with complete firmographic data |
| Scoring Latency (p95) | < 100ms | API response time |
| CRM Sync Success | > 99.5% | Successful CRM updates / total |
| Lead Qualification Rate | Baseline + 20% | % leads qualified vs. baseline |
| False Positive Rate | < 15% | Disqualified leads that convert |
| Time-to-Score | < 5 min | Lead creation to score available |

### 10.6 Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Data quality issues | Medium | High | Confidence scoring, fallback rules |
| Model drift | Medium | Medium | Automated monitoring, retraining pipeline |
| CRM API rate limits | High | Medium | Rate limiting, batch sync, caching |
| Enrichment source downtime | Low | High | Multi-source fallback, circuit breakers |
| Governance policy gaps | Low | High | Default-deny, comprehensive policy review |
| Scalability bottlenecks | Medium | High | Horizontal scaling, Redis clustering |

---

## Appendix A: Configuration Reference

```yaml
# config/lead_scoring.yaml
lead_scoring:
  # Scoring configuration
  scoring:
    frameworks:
      bant:
        enabled: true
        weight: 0.33
        weights:
          budget: 0.25
          authority: 0.25
          need: 0.30
          timeline: 0.20
      meddic:
        enabled: true
        weight: 0.34
        weights:
          metrics: 0.15
          economic_buyer: 0.20
          decision_criteria: 0.15
          decision_process: 0.15
          identify_pain: 0.20
          champion: 0.15
      champ:
        enabled: true
        weight: 0.33
        weights:
          challenges: 0.30
          authority: 0.20
          money: 0.25
          prioritization: 0.25
    
    thresholds:
      hot: 80
      warm: 50
      cold: 20
      min_confidence: 0.3
  
  # Enrichment configuration
  enrichment:
    sources:
      - name: clearbit
        enabled: true
        priority: 1
        ttl_seconds: 86400
      - name: zoominfo
        enabled: true
        priority: 2
        ttl_seconds: 86400
      - name: bombora
        enabled: true
        priority: 3
        ttl_seconds: 604800
      - name: builtwith
        enabled: true
        priority: 4
        ttl_seconds: 2592000
    
    entity_resolution:
      fuzzy_threshold: 0.85
      domain_weight: 0.4
      name_weight: 0.3
      phone_weight: 0.2
      location_weight: 0.1
  
  # API configuration
  api:
    rate_limit:
      requests_per_minute: 1000
      burst_size: 100
    timeout:
      enrichment_seconds: 30
      scoring_seconds: 5
      total_seconds: 60
  
  # Governance configuration
  governance:
    policy_engine: opa
    audit_enabled: true
    default_deny: true
    required_capabilities:
      scoring: "lead.score"
      enrichment: "lead.enrich"
      routing: "lead.route"
```

## Appendix B: API Specification

See OpenAPI spec at `specs/lead-scoring-api.yaml` for complete API documentation.

## Appendix C: Environment Variables

```bash
# GRC_Claw Integration
GRC_CLAW_DID_AGENT=did:grc:lead-scoring-agent
GRC_CLAW_POLICY_URL=http://localhost:8181/v1/data/grc_claw/lead_scoring
GRC_CLAW_AUDIT_URL=http://localhost:18791/api/audit

# Feature Store
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# CRM Connectors
SALESFORCE_USERNAME=
SALESFORCE_PASSWORD=
SALESFORCE_SECURITY_TOKEN=
HUBSPOT_API_KEY=

# Enrichment Sources
CLEARBIT_API_KEY=
ZOOMINFO_API_KEY=
BOMBORA_API_KEY=
BUILTWITH_API_KEY=

# Model Registry
MLFLOW_TRACKING_URI=http://localhost:5000
MODEL_REGISTRY_PATH=s3://grc-claw-models/lead-scoring

# Event Bus
KAFKA_BROKERS=localhost:9092
KAFKA_TOPIC_PREFIX=lead-scoring
```

---

**Document Status:** Implementation Ready  
**Last Updated:** 2026-10-01  
**Next Review:** Post-Phase 1 completion
