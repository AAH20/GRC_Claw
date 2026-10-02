# AI-Powered Broker Enablement — Implementation Plan

**Framework:** LangChain DeepAgents  
**Version:** 1.0.0  
**Last Updated:** 2026-10-01  
**Author:** Ahmed Hassan  

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Partner Onboarding Agent](#2-partner-onboarding-agent)
3. [Partner Enablement Agent](#3-partner-enablement-agent)
4. [Commission Tracking Agent](#4-commission-tracking-agent)
5. [Performance Analytics Agent](#5-performance-analytics-agent)
6. [Multi-Tenant Orchestration](#6-multi-tenant-orchestration)
7. [White-Label Capabilities](#7-white-label-capabilities)
8. [Code Examples & Snippets](#8-code-examples--snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Design

The broker enablement platform uses a **hierarchical multi-agent architecture** built on LangChain DeepAgents. A central **Orchestrator Agent** delegates domain-specific tasks to four specialized sub-agents, each with its own toolset, system prompt, and memory scope.

```
┌─────────────────────────────────────────────────────────┐
│                  Orchestrator Agent                      │
│  (Router · Context Manager · Human-in-the-Loop)         │
└────────┬──────────┬──────────┬──────────┬───────────────┘
         │          │          │          │
    ┌────▼────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼──────────┐
    │Onboard  │ │Enable  │ │Commission│ │Analytics   │
    │Agent    │ │Agent   │ │Agent     │ │Agent       │
    └────┬────┘ └──┬─────┘ └──┬─────┘ └──┬──────────┘
         │          │          │          │
    ┌────▼──────────▼──────────▼──────────▼────┐
    │           Shared Infrastructure            │
    │  Tools · Memory · Vector Store · LLM      │
    └───────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Multi-agent orchestration, tool calling, planning |
| LLM | GPT-4o / Claude 3.5 Sonnet | Reasoning, generation, classification |
| Vector Store | Pinecone / Weaviate | Semantic search over partner docs, policies |
| Memory | LangChain Memory + Redis | Short-term conversation + long-term partner state |
| Tool Runtime | Python 3.11+ / FastAPI | Custom tool execution, API integrations |
| Task Queue | Celery + Redis | Async commission calculations, report generation |
| Database | PostgreSQL (per-tenant schema) | Transactional data, audit logs |
| Observability | LangSmith + OpenTelemetry | Tracing, evaluation, monitoring |

### 1.3 Agent Responsibilities

| Agent | Primary Responsibility | Key Tools |
|-------|----------------------|-----------|
| **Orchestrator** | Intent classification, task routing, escalation | Router, Context Aggregator, Human-in-the-Loop |
| **Onboarding Agent** | Partner registration, KYC/KYB, document collection | DocumentParser, KYCVerifier, CRMWriter, EmailSender |
| **Enablement Agent** | Training content delivery, certification tracking | ContentRecommender, QuizGenerator, CertificationTracker |
| **Commission Agent** | Commission calculation, dispute resolution, payout | CommissionCalculator, DisputeHandler, PayoutProcessor |
| **Analytics Agent** | Performance dashboards, forecasting, insights | DataAggregator, ForecastEngine, ReportGenerator |

### 1.4 Communication Protocol

Agents communicate via **structured messages** using LangChain's `AgentMessage` schema:

```python
from dataclasses import dataclass, field
from typing import Literal, Any
from datetime import datetime

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    message_type: Literal["task", "result", "escalation", "human_input"]
    payload: dict[str, Any]
    tenant_id: str
    trace_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 1.5 Planning & ReAct Loop

Each agent uses DeepAgents' built-in **plan-and-execute** pattern:

1. **Plan** — Decompose the task into ordered steps
2. **Act** — Execute each step using available tools
3. **Observe** — Collect tool results
4. **Reflect** — Decide whether to continue, replan, or escalate

```python
from langchain_deepagents import create_deep_agent

agent = create_deep_agent(
    tools=agent_tools,
    system_prompt=SYSTEM_PROMPT,
    sub_agents=sub_agents,
    model="gpt-4o",
)
```

---

## 2. Partner Onboarding Agent

### 2.1 Purpose

Automates the end-to-end partner onboarding workflow: initial contact → KYC/KYB verification → document collection → contract generation → account provisioning → welcome sequence.

### 2.2 Workflow Stages

```
Lead Capture → Identity Verification → Document Collection →
Contract Generation → Account Provisioning → Welcome & Training Assignment
```

### 2.3 State Machine

```python
from enum import Enum

class OnboardingStage(str, Enum):
    LEAD_CAPTURED = "lead_captured"
    IDENTITY_VERIFICATION_PENDING = "identity_verification_pending"
    IDENTITY_VERIFIED = "identity_verified"
    DOCUMENTS_PENDING = "documents_pending"
    DOCUMENTS_UNDER_REVIEW = "documents_under_review"
    DOCUMENTS_APPROVED = "documents_approved"
    CONTRACT_GENERATED = "contract_generated"
    CONTRACT_SIGNED = "contract_signed"
    ACCOUNT_PROVISIONED = "account_provisioned"
    WELCOME_SENT = "welcome_sent"
    ONBOARDING_COMPLETE = "onboarding_complete"
    REJECTED = "rejected"
    ESCALATED = "escalated"
```

### 2.4 Tool Definitions

```python
from langchain_core.tools import tool
from typing import Optional

@tool
def verify_kyc(partner_id: str, document_ids: list[str]) -> dict:
    """Verify partner identity using KYC provider (Jumio/Onfido).
    
    Args:
        partner_id: Unique partner identifier
        document_ids: List of uploaded document references
        
    Returns:
        dict with verification status, confidence score, and flags
    """
    pass

@tool
def parse_document(document_id: str, doc_type: str) -> dict:
    """Extract structured data from uploaded documents.
    
    Supports: business_license, tax_id, bank_statement, 
    certificate_of_incorporation, proof_of_address
    
    Args:
        document_id: Reference to stored document
        doc_type: Type of document for parser selection
        
    Returns:
        dict with extracted fields, confidence, and validation results
    """
    pass

@tool
def generate_contract(
    partner_id: str,
    commission_tier: str,
    terms: dict,
) -> dict:
    """Generate a partnership agreement from template.
    
    Args:
        partner_id: Partner to generate contract for
        commission_tier: Commission tier (bronze/silver/gold/platinum)
        terms: Custom terms and conditions
        
    Returns:
        dict with contract_id, pdf_url, and status
    """
    pass

@tool
def provision_account(partner_id: str, tier: str) -> dict:
    """Provision partner account in the broker platform.
    
    Args:
        partner_id: Partner to provision
        tier: Commission tier determining access levels
        
    Returns:
        dict with account_id, credentials, and access URLs
    """
    pass

@tool
def send_welcome_email(partner_id: str, template: str = "welcome_v2") -> dict:
    """Send personalized welcome email with next steps.
    
    Args:
        partner_id: Partner to email
        template: Email template identifier
        
    Returns:
        dict with send status and tracking info
    """
    pass
```

### 2.5 System Prompt

```python
ONBOARDING_SYSTEM_PROMPT = """You are the Partner Onboarding Agent for {tenant_name}.

Your responsibility is to guide new partners through a seamless onboarding experience.

## Core Behaviors
- Collect required information incrementally — never overwhelm with forms
- Verify identity documents using the KYC tool before proceeding
- Generate contracts with the correct commission tier based on partner profile
- Provision accounts only after all compliance checks pass
- Escalate to human review when confidence < 0.85 or documents are ambiguous

## Compliance Rules
- Never skip KYC verification
- Flag high-risk jurisdictions for manual review
- Retain all documents for 7 years per regulatory requirements
- Log every state transition with timestamp and actor

## Tone
- Professional but warm
- Proactive — anticipate partner questions
- Clear about what happens next and expected timelines

## Tenant Context
- Tenant: {tenant_name}
- Region: {region}
- Compliance Framework: {compliance_framework}
- Default Commission Tier: {default_tier}
"""
```

### 2.6 Implementation

```python
from langchain_deepagents import create_deep_agent
from langchain_core.tools import tool

onboarding_tools = [
    verify_kyc,
    parse_document,
    generate_contract,
    provision_account,
    send_welcome_email,
]

onboarding_agent = create_deep_agent(
    tools=onboarding_tools,
    system_prompt=ONBOARDING_SYSTEM_PROMPT,
    name="onboarding_agent",
    model="gpt-4o",
)
```

---

## 3. Partner Enablement Agent

### 3.1 Purpose

Delivers personalized training content, tracks certification progress, recommends learning paths, and ensures partners are fully enabled to sell effectively.

### 3.2 Capabilities

| Capability | Description |
|-----------|-------------|
| **Learning Path Generation** | Creates customized training paths based on partner tier, region, and product focus |
| **Content Delivery** | Serves micro-learning modules, videos, and interactive content |
| **Certification Tracking** | Monitors quiz scores, completion rates, and certification expiry |
| **Knowledge Assessment** | Generates adaptive quizzes to validate understanding |
| **Enablement Scoring** | Computes an enablement score (0-100) per partner |
| **Re-engagement** | Triggers nudges for inactive or stalled partners |

### 3.3 Tool Definitions

```python
@tool
def get_learning_path(partner_id: str, focus_area: str) -> dict:
    """Generate a personalized learning path for a partner.
    
    Args:
        partner_id: Partner to create path for
        focus_area: Product category or skill focus
        
    Returns:
        dict with ordered modules, estimated duration, and prerequisites
    """
    pass

@tool
def deliver_content(module_id: str, partner_id: str, format: str = "interactive") -> dict:
    """Deliver training content in the partner's preferred format.
    
    Args:
        module_id: Training module identifier
        partner_id: Partner receiving content
        format: Content format (interactive, video, pdf, quiz)
        
    Returns:
        dict with content URL, progress tracking, and completion status
    """
    pass

@tool
def generate_quiz(module_id: str, difficulty: str, num_questions: int = 10) -> dict:
    """Generate an adaptive quiz for a training module.
    
    Args:
        module_id: Module to quiz on
        difficulty: easy, medium, or hard
        num_questions: Number of questions to generate
        
    Returns:
        dict with quiz_id, questions, and answer key
    """
    pass

@tool
def compute_enablement_score(partner_id: str) -> dict:
    """Calculate partner enablement score based on multiple factors.
    
    Factors: training completion (30%), certification status (25%),
    product knowledge quiz scores (25%), sales activity (20%)
    
    Args:
        partner_id: Partner to score
        
    Returns:
        dict with overall score, factor breakdown, and recommendations
    """
    pass

@tool
def recommend_next_action(partner_id: str) -> dict:
    """Recommend the next best action for partner enablement.
    
    Args:
        partner_id: Partner to analyze
        
    Returns:
        dict with recommended action, priority, and rationale
    """
    pass
```

### 3.4 Enablement Score Algorithm

```python
def calculate_enablement_score(partner_data: dict) -> float:
    """
    Compute enablement score on a 0-100 scale.
    
    Weights:
    - Training completion: 30%
    - Certification status: 25%
    - Product knowledge: 25%
    - Sales activity: 20%
    """
    weights = {
        "training_completion": 0.30,
        "certification_status": 0.25,
        "product_knowledge": 0.25,
        "sales_activity": 0.20,
    }
    
    scores = {
        "training_completion": partner_data.get("modules_completed", 0) / 
                             max(partner_data.get("modules_assigned", 1), 1) * 100,
        "certification_status": 100 if partner_data.get("certified", False) else 
                               (50 if partner_data.get("certification_in_progress", False) else 0),
        "product_knowledge": partner_data.get("avg_quiz_score", 0),
        "sales_activity": min(partner_data.get("deals_closed_30d", 0) / 10 * 100, 100),
    }
    
    total = sum(scores[k] * weights[k] for k in weights)
    return round(total, 2)
```

### 3.5 System Prompt

```python
ENABLEMENT_SYSTEM_PROMPT = """You are the Partner Enablement Agent for {tenant_name}.

Your mission is to maximize partner effectiveness through personalized enablement.

## Core Behaviors
- Assess each partner's current knowledge level before recommending content
- Adapt learning paths based on partner tier, region, and product focus
- Track certification expiry and proactively schedule renewals
- Identify at-risk partners (low engagement, declining scores) and intervene
- Celebrate milestones to maintain motivation

## Scoring
- Enablement score ranges 0-100
- Score < 40: Critical — immediate intervention required
- Score 40-60: At Risk — recommend targeted training
- Score 60-80: On Track — continue current path
- Score 80+: Excellent — consider advanced certification

## Content Rules
- All content must be tenant-branded
- Respect partner's language preference
- Never recommend content the partner has already completed
"""
```

---

## 4. Commission Tracking Agent

### 4.1 Purpose

Automates commission calculation, tier management, dispute resolution, and payout processing with full auditability.

### 4.2 Commission Tiers

| Tier | Criteria | Commission Rate | Bonus Structure |
|------|----------|----------------|-----------------|
| Bronze | 0-10 deals/month | 5% | None |
| Silver | 11-25 deals/month | 7% | Quarterly bonus: 0.5% |
| Gold | 26-50 deals/month | 10% | Quarterly bonus: 1% |
| Platinum | 51+ deals/month | 15% | Quarterly bonus: 1.5% + SPIFs |

### 4.3 Tool Definitions

```python
@tool
def calculate_commission(
    deal_id: str,
    partner_id: str,
    deal_amount: float,
    product_category: str,
) -> dict:
    """Calculate commission for a closed deal.
    
    Args:
        deal_id: Unique deal identifier
        partner_id: Partner who closed the deal
        deal_amount: Total deal value
        product_category: Product category for rate lookup
        
    Returns:
        dict with commission_amount, tier_applied, breakdown, and status
    """
    pass

@tool
def get_partner_tier(partner_id: str, as_of_date: str = "current") -> dict:
    """Get partner's commission tier with effective dates.
    
    Args:
        partner_id: Partner to look up
        as_of_date: Date for tier evaluation (default: current)
        
    Returns:
        dict with tier, effective_date, next_evaluation_date, and progress
    """
    pass

@tool
def file_commission_dispute(
    partner_id: str,
    deal_id: str,
    dispute_reason: str,
    expected_amount: float,
) -> dict:
    """File a commission dispute for review.
    
    Args:
        partner_id: Partner filing the dispute
        deal_id: Deal in question
        dispute_reason: Reason for dispute
        expected_amount: Amount partner believes is owed
        
    Returns:
        dict with dispute_id, status, and estimated resolution time
    """
    pass

@tool
def process_payout(partner_id: str, period: str) -> dict:
    """Process commission payout for a given period.
    
    Args:
        partner_id: Partner to pay
        period: Payout period (YYYY-MM format)
        
    Returns:
        dict with payout_id, amount, method, and status
    """
    pass

@tool
def get_commission_statement(partner_id: str, period: str) -> dict:
    """Generate detailed commission statement.
    
    Args:
        partner_id: Partner to generate statement for
        period: Statement period (YYYY-MM format)
        
    Returns:
        dict with line items, totals, adjustments, and PDF URL
    """
    pass
```

### 4.4 Commission Calculation Engine

```python
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CommissionResult:
    deal_id: str
    partner_id: str
    deal_amount: Decimal
    base_rate: Decimal
    bonus_rate: Decimal
    commission_amount: Decimal
    tier: str
    calculation_timestamp: datetime
    audit_hash: str

class CommissionCalculator:
    TIER_RATES = {
        "bronze": Decimal("0.05"),
        "silver": Decimal("0.07"),
        "gold": Decimal("0.10"),
        "platinum": Decimal("0.15"),
    }
    
    PRODUCT_MULTIPLIERS = {
        "standard": Decimal("1.0"),
        "premium": Decimal("1.2"),
        "enterprise": Decimal("1.5"),
    }
    
    def calculate(
        self,
        deal_id: str,
        partner_id: str,
        deal_amount: Decimal,
        product_category: str,
        partner_tier: str,
    ) -> CommissionResult:
        base_rate = self.TIER_RATES[partner_tier]
        multiplier = self.PRODUCT_MULTIPLIERS.get(product_category, Decimal("1.0"))
        
        effective_rate = base_rate * multiplier
        commission = (deal_amount * effective_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        return CommissionResult(
            deal_id=deal_id,
            partner_id=partner_id,
            deal_amount=deal_amount,
            base_rate=base_rate,
            bonus_rate=effective_rate - base_rate,
            commission_amount=commission,
            tier=partner_tier,
            calculation_timestamp=datetime.utcnow(),
            audit_hash=self._compute_audit_hash(deal_id, partner_id, commission),
        )
    
    def _compute_audit_hash(self, *args) -> str:
        import hashlib
        data = "|".join(str(a) for a in args)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
```

### 4.5 System Prompt

```python
COMMISSION_SYSTEM_PROMPT = """You are the Commission Tracking Agent for {tenant_name}.

You ensure accurate, transparent, and timely commission management.

## Core Behaviors
- Calculate commissions using the current tier structure
- Apply product category multipliers correctly
- Flag anomalies (unusual amounts, tier mismatches) for review
- Process disputes with empathy and transparency
- Generate clear, itemized statements

## Rules
- Never modify historical commission calculations
- All adjustments must include reason code and approver
- Disputes must be resolved within 14 business days
- Payouts processed on the 15th of each month
- Retain all commission records for 7 years

## Escalation Triggers
- Dispute amount > $10,000
- Partner tier mismatch
- Duplicate deal detection
- Any calculation confidence < 95%
"""
```

---

## 5. Performance Analytics Agent

### 5.1 Purpose

Provides real-time performance dashboards, predictive analytics, and actionable insights for both operators and partners.

### 5.2 Analytics Dimensions

| Dimension | Metrics |
|-----------|---------|
| **Sales Performance** | Deals closed, revenue, win rate, avg deal size, sales cycle length |
| **Partner Health** | Enablement score, activity level, certification status, NPS |
| **Commission Analysis** | Earned vs. paid, dispute rate, tier distribution, YoY growth |
| **Product Performance** | Category mix, cross-sell rate, product adoption |
| **Forecasting** | Revenue projection, churn risk, tier migration probability |

### 5.3 Tool Definitions

```python
@tool
def get_partner_dashboard(partner_id: str, period: str = "30d") -> dict:
    """Get comprehensive partner performance dashboard.
    
    Args:
        partner_id: Partner to analyze
        period: Analysis period (7d, 30d, 90d, 12m)
        
    Returns:
        dict with KPIs, trends, rankings, and recommendations
    """
    pass

@tool
def forecast_revenue(partner_id: str, horizon: str = "90d") -> dict:
    """Forecast partner revenue using time-series analysis.
    
    Args:
        partner_id: Partner to forecast
        horizon: Forecast horizon (30d, 90d, 12m)
        
    Returns:
        dict with forecast values, confidence intervals, and assumptions
    """
    pass

@tool
def identify_at_risk_partners(tenant_id: str, threshold: float = 0.3) -> dict:
    """Identify partners at risk of churn or downgrade.
    
    Args:
        tenant_id: Tenant to analyze
        threshold: Risk score threshold (0-1)
        
    Returns:
        dict with at-risk partner list, risk factors, and recommended actions
    """
    pass

@tool
def generate_performance_report(
    partner_id: str,
    report_type: str,
    period: str,
) -> dict:
    """Generate a formatted performance report.
    
    Args:
        partner_id: Partner to report on
        report_type: Report type (summary, detailed, comparative)
        period: Report period
        
    Returns:
        dict with report URL, key findings, and executive summary
    """
    pass

@tool
def benchmark_partner(partner_id: str, peer_group: str = "tier") -> dict:
    """Benchmark partner against peer group.
    
    Args:
        partner_id: Partner to benchmark
        peer_group: Peer group (tier, region, tenure)
        
    Returns:
        dict with percentile rankings, gaps, and improvement areas
    """
    pass
```

### 5.4 Forecasting Implementation

```python
import pandas as pd
from prophet import Prophet
from typing import Optional

class RevenueForecaster:
    def __init__(self, min_history_days: int = 90):
        self.min_history_days = min_history_days
    
    def forecast(
        self,
        historical_deals: pd.DataFrame,
        horizon_days: int = 90,
    ) -> pd.DataFrame:
        """
        Generate revenue forecast using Prophet.
        
        Args:
            historical_deals: DataFrame with 'ds' (date) and 'y' (revenue) columns
            horizon_days: Number of days to forecast
            
        Returns:
            DataFrame with forecast, lower bound, and upper bound
        """
        if len(historical_deals) < self.min_history_days:
            raise ValueError(
                f"Need at least {self.min_history_days} days of history"
            )
        
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
        )
        
        model.fit(historical_deals)
        
        future = model.make_future_dataframe(periods=horizon_days)
        forecast = model.predict(future)
        
        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(horizon_days)
```

### 5.5 System Prompt

```python
ANALYTICS_SYSTEM_PROMPT = """You are the Performance Analytics Agent for {tenant_name}.

You transform raw data into actionable insights.

## Core Behaviors
- Present data visually with clear charts and comparisons
- Highlight trends, anomalies, and opportunities
- Benchmark partners against relevant peer groups
- Forecast with appropriate confidence intervals
- Recommend specific, measurable actions

## Data Rules
- All metrics must be traceable to source data
- Use consistent period definitions (rolling 30d, calendar month, etc.)
- Clearly label estimates vs. actuals
- Respect data privacy — aggregate where individual identification isn't needed

## Insight Quality
- Every insight must include: observation, implication, recommended action
- Quantify impact wherever possible
- Distinguish correlation from causation
- Flag data quality issues transparently
"""
```

---

## 6. Multi-Tenant Orchestration

### 6.1 Architecture

The platform serves multiple broker tenants from a single deployment, with strict data isolation and tenant-specific configuration.

```
┌──────────────────────────────────────────────────────────────┐
│                    API Gateway / Load Balancer                │
│              (Tenant Resolution via JWT + Header)             │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                  Orchestrator Agent                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Tenant       │  │ Tenant       │  │ Tenant             │  │
│  │ Context      │  │ Config       │  │ Rate Limiter       │  │
│  │ Resolver     │  │ Manager      │  │                    │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │Tenant A │   │Tenant B │   │Tenant C │
   │Schema   │   │Schema   │   │Schema   │
   │+ Config │   │+ Config │   │+ Config │
   └─────────┘   └─────────┘   └─────────┘
```

### 6.2 Tenant Resolution Middleware

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

class TenantResolutionMiddleware(BaseHTTPMiddleware):
    """Resolve tenant from JWT token and inject into request context."""
    
    async def dispatch(self, request: Request, call_next):
        token = self._extract_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="Missing authentication")
        
        try:
            payload = jwt.decode(token, self.public_key, algorithms=["RS256"])
            tenant_id = payload.get("tenant_id")
            partner_id = payload.get("partner_id")
            
            if not tenant_id:
                raise HTTPException(status_code=403, detail="No tenant in token")
            
            request.state.tenant_id = tenant_id
            request.state.partner_id = partner_id
            request.state.user_roles = payload.get("roles", [])
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        response = await call_next(request)
        response.headers["X-Tenant-ID"] = tenant_id
        return response
    
    def _extract_token(self, request: Request) -> str | None:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return None
```

### 6.3 Tenant-Aware Agent Factory

```python
from functools import lru_cache

class TenantAgentFactory:
    """Creates tenant-configured agent instances."""
    
    def __init__(self, config_store: "TenantConfigStore"):
        self.config_store = config_store
        self._agent_cache: dict[str, dict] = {}
    
    async def get_orchestrator(self, tenant_id: str):
        """Get or create orchestrator agent for tenant."""
        if tenant_id not in self._agent_cache:
            config = await self.config_store.get_config(tenant_id)
            
            self._agent_cache[tenant_id] = {
                "onboarding": self._build_onboarding_agent(config),
                "enablement": self._build_enablement_agent(config),
                "commission": self._build_commission_agent(config),
                "analytics": self._build_analytics_agent(config),
                "orchestrator": self._build_orchestrator(config),
            }
        
        return self._agent_cache[tenant_id]
    
    def _build_onboarding_agent(self, config: "TenantConfig"):
        return create_deep_agent(
            tools=self._get_tools_for_tenant(config, "onboarding"),
            system_prompt=self._render_prompt(
                ONBOARDING_SYSTEM_PROMPT, config
            ),
            name=f"onboarding_{config.tenant_id}",
            model=config.model_name,
        )
    
    def _render_prompt(self, template: str, config: "TenantConfig") -> str:
        return template.format(
            tenant_name=config.tenant_name,
            region=config.region,
            compliance_framework=config.compliance_framework,
            default_tier=config.default_commission_tier,
            language=config.language,
            brand_colors=config.brand_colors,
        )
```

### 6.4 Data Isolation Strategy

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextvars import ContextVar

tenant_id_ctx: ContextVar[str] = ContextVar("tenant_id")

class TenantAwareSession:
    """Automatically scope database queries to the current tenant."""
    
    def __init__(self, engine):
        self.engine = engine
        self.SessionLocal = sessionmaker(bind=engine)
    
    def get_session(self) -> Session:
        tenant_id = tenant_id_ctx.get()
        if not tenant_id:
            raise RuntimeError("No tenant in context")
        
        session = self.SessionLocal()
        # Set PostgreSQL row-level security
        session.execute(
            text("SET LOCAL app.current_tenant = :tenant_id"),
            {"tenant_id": tenant_id}
        )
        return session

# PostgreSQL RLS Policy
"""
CREATE POLICY tenant_isolation ON partner_data
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

ALTER TABLE partner_data ENABLE ROW LEVEL SECURITY;
"""
```

### 6.5 Tenant Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Optional

class TenantConfig(BaseModel):
    tenant_id: str
    tenant_name: str
    region: str
    language: str = "en"
    timezone: str = "UTC"
    compliance_framework: str = "SOC2"
    
    # Commission Settings
    default_commission_tier: str = "bronze"
    commission_tiers: dict = Field(default_factory=dict)
    payout_schedule: str = "monthly_15th"
    payout_method: str = "ach"
    
    # Model Settings
    model_name: str = "gpt-4o"
    model_temperature: float = 0.7
    max_tokens: int = 4096
    
    # Branding
    brand_colors: dict = Field(default_factory=dict)
    logo_url: Optional[str] = None
    email_from_address: Optional[str] = None
    
    # Feature Flags
    features: dict = Field(default_factory=lambda: {
        "onboarding_agent": True,
        "enablement_agent": True,
        "commission_agent": True,
        "analytics_agent": True,
        "white_label": False,
        "custom_integrations": False,
    })
    
    # Rate Limits
    rate_limits: dict = Field(default_factory=lambda: {
        "requests_per_minute": 60,
        "concurrent_sessions": 10,
    })
```

---

## 7. White-Label Capabilities

### 7.1 White-Label Architecture

The platform supports full white-labeling, allowing broker partners to present the enablement system as their own product.

### 7.2 Customization Layers

| Layer | Customizable Elements |
|-------|----------------------|
| **Visual** | Logo, colors, fonts, favicon, email templates |
| **Content** | Training materials, product descriptions, help articles |
| **Domain** | Custom CNAME, SSL certificates, DNS |
| **Commission** | Tier structures, rates, payout schedules, currencies |
| **Integrations** | CRM, payment processors, communication tools |
| **Features** | Toggle agents on/off, custom workflows |

### 7.3 White-Label Configuration

```python
class WhiteLabelConfig(BaseModel):
    tenant_id: str
    
    # Domain
    custom_domain: str
    ssl_certificate_arn: str
    
    # Branding
    brand_name: str
    brand_logo_url: str
    brand_favicon_url: str
    primary_color: str = "#1a73e8"
    secondary_color: str = "#34a853"
    font_family: str = "Inter"
    
    # Email
    email_from_name: str
    email_from_address: str
    email_reply_to: str
    email_template_base: str
    
    # Content
    welcome_message: str
    terms_of_service_url: str
    privacy_policy_url: str
    help_center_url: str
    
    # Feature Toggles
    show_powered_by: bool = False
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
```

### 7.4 White-Label Middleware

```python
class WhiteLabelMiddleware(BaseHTTPMiddleware):
    """Apply white-label branding based on request domain."""
    
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "")
        
        # Resolve tenant from custom domain
        tenant_config = await self.resolve_by_domain(host)
        
        if tenant_config and tenant_config.white_label_enabled:
            request.state.white_label = WhiteLabelContext(
                brand_name=tenant_config.brand_name,
                logo_url=tenant_config.brand_logo_url,
                primary_color=tenant_config.primary_color,
                custom_css=tenant_config.custom_css,
                email_template_base=tenant_config.email_template_base,
            )
        
        response = await call_next(request)
        
        # Inject white-label headers
        if hasattr(request.state, "white_label"):
            wl = request.state.white_label
            response.headers["X-Brand-Name"] = wl.brand_name
        
        return response
    
    async def resolve_by_domain(self, domain: str) -> Optional[TenantConfig]:
        # Cache domain → tenant mapping
        return await self.tenant_store.get_by_domain(domain)
```

### 7.5 Branded Email Templates

```python
from jinja2 import Template

EMAIL_TEMPLATE_BASE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        :root {
            --primary-color: {{ primary_color }};
            --secondary-color: {{ secondary_color }};
            --font-family: {{ font_family }};
        }
        body { font-family: var(--font-family), sans-serif; margin: 0; padding: 0; }
        .header { background: var(--primary-color); padding: 24px; text-align: center; }
        .header img { max-height: 48px; }
        .content { padding: 32px; max-width: 600px; margin: 0 auto; }
        .footer { background: #f5f5f5; padding: 16px; text-align: center; font-size: 12px; color: #666; }
        .btn { background: var(--primary-color); color: white; padding: 12px 24px; 
               text-decoration: none; border-radius: 4px; display: inline-block; }
        {% if custom_css %}{{ custom_css }}{% endif %}
    </style>
</head>
<body>
    <div class="header">
        <img src="{{ logo_url }}" alt="{{ brand_name }}">
    </div>
    <div class="content">
        {{ content | safe }}
    </div>
    <div class="footer">
        <p>&copy; {{ year }} {{ brand_name }}. All rights reserved.</p>
        {% if show_powered_by %}
        <p>Powered by BrokerEnablement Platform</p>
        {% endif %}
    </div>
</body>
</html>
"""

def render_email(template_name: str, context: dict, wl: WhiteLabelContext) -> str:
    template = Template(EMAIL_TEMPLATE_BASE)
    return template.render(
        brand_name=wl.brand_name,
        logo_url=wl.logo_url,
        primary_color=wl.primary_color,
        secondary_color=wl.secondary_color,
        font_family=wl.font_family,
        custom_css=wl.custom_css,
        show_powered_by=wl.show_powered_by,
        year=datetime.now().year,
        content=render_template(template_name, context),
    )
```

---

## 8. Code Examples & Snippets

### 8.1 Complete Agent Wiring

```python
# main.py — Application entry point
from fastapi import FastAPI
from langchain_deepagents import create_deep_agent
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize shared resources
    app.state.config_store = TenantConfigStore()
    app.state.agent_factory = TenantAgentFactory(app.state.config_store)
    app.state.vector_store = VectorStore()
    app.state.memory_store = MemoryStore()
    yield
    # Cleanup
    await app.state.vector_store.close()
    await app.state.memory_store.close()

app = FastAPI(lifespan=lifespan)

# Middleware
app.add_middleware(TenantResolutionMiddleware)
app.add_middleware(WhiteLabelMiddleware)

@app.post("/api/v1/chat")
async def chat(request: ChatRequest, state: RequestState):
    """Main chat endpoint — routes to appropriate agent."""
    agents = await request.app.state.agent_factory.get_orchestrator(
        state.tenant_id
    )
    
    orchestrator = agents["orchestrator"]
    
    result = await orchestrator.ainvoke({
        "messages": [{"role": "user", "content": request.message}],
        "config": {"configurable": {"tenant_id": state.tenant_id}},
    })
    
    return ChatResponse(
        message=result["output"],
        agent=result.get("agent_name"),
        trace_id=result.get("trace_id"),
    )
```

### 8.2 Tool with Error Handling & Retries

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_core.tools import tool
import structlog

logger = structlog.get_logger()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
@tool
def verify_kyc(partner_id: str, document_ids: list[str]) -> dict:
    """Verify partner identity with retry logic."""
    try:
        result = await kyc_provider.verify(
            partner_id=partner_id,
            documents=document_ids,
        )
        
        logger.info(
            "kyc_verification_completed",
            partner_id=partner_id,
            status=result.status,
            confidence=result.confidence,
        )
        
        return {
            "status": result.status,
            "confidence": result.confidence,
            "flags": result.flags,
            "verified_at": result.timestamp.isoformat(),
        }
        
    except KYCProviderError as e:
        logger.error(
            "kyc_verification_failed",
            partner_id=partner_id,
            error=str(e),
        )
        raise
```

### 8.3 Human-in-the-Loop Checkpoint

```python
from langchain_deepagents import create_deep_agent, interrupt

def create_onboarding_agent_with_approval():
    """Onboarding agent with human approval for high-risk decisions."""
    
    def require_approval(state: dict) -> bool:
        """Determine if human approval is needed."""
        risk_score = state.get("risk_score", 0)
        document_confidence = state.get("document_confidence", 1.0)
        return risk_score > 0.7 or document_confidence < 0.85
    
    agent = create_deep_agent(
        tools=onboarding_tools,
        system_prompt=ONBOARDING_SYSTEM_PROMPT,
        name="onboarding_agent",
        model="gpt-4o",
        # Human-in-the-Loop: pause for approval on high-risk actions
        interrupt_before=["provision_account", "generate_contract"],
        # Check function to determine if interruption is needed
        should_interrupt=require_approval,
    )
    
    return agent
```

### 8.4 Streaming Response

```python
from fastapi.responses import StreamingResponse
from langchain_core.callbacks import AsyncCallbackHandler

class StreamingCallbackHandler(AsyncCallbackHandler):
    def __init__(self):
        self.tokens = []
    
    async def on_llm_new_token(self, token: str, **kwargs):
        self.tokens.append(token)
        yield f"data: {json.dumps({'token': token})}\n\n"

@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest, state: RequestState):
    """Streaming chat endpoint for real-time responses."""
    agents = await request.app.state.agent_factory.get_orchestrator(
        state.tenant_id
    )
    
    handler = StreamingCallbackHandler()
    
    async def generate():
        async for chunk in agents["orchestrator"].astream(
            {"messages": [{"role": "user", "content": request.message}]},
            config={"callbacks": [handler]},
        ):
            if chunk.content:
                yield f"data: {json.dumps({'content': chunk.content})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
```

### 8.5 LangSmith Tracing Integration

```python
from langsmith import Client
from langchain.callbacks.tracers.langchain import LangChainTracer

# Configure LangSmith
langsmith_client = Client(
    api_url="https://api.smith.langchain.com",
    api_key=os.environ["LANGCHAIN_API_KEY"],
)

tracer = LangChainTracer(
    project_name="broker-enablement",
    client=langsmith_client,
)

# Agent with tracing
agent = create_deep_agent(
    tools=onboarding_tools,
    system_prompt=ONBOARDING_SYSTEM_PROMPT,
    name="onboarding_agent",
    model="gpt-4o",
    callbacks=[tracer],
)
```

### 8.6 Vector Store for Partner Knowledge

```python
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PartnerKnowledgeBase:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Pinecone(
            index_name=f"partner-kb-{tenant_id}",
            embedding=self.embeddings,
            namespace=tenant_id,  # Tenant isolation
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
    
    async def add_documents(self, documents: list[dict]):
        """Add documents to tenant's knowledge base."""
        texts = []
        metadatas = []
        
        for doc in documents:
            chunks = self.splitter.split_text(doc["content"])
            texts.extend(chunks)
            metadatas.extend([
                {
                    "source": doc["source"],
                    "tenant_id": self.tenant_id,
                    "document_id": doc["id"],
                    "category": doc.get("category", "general"),
                }
                for _ in chunks
            ])
        
        await self.vectorstore.aadd_texts(texts, metadatas)
    
    async def search(self, query: str, k: int = 5) -> list[dict]:
        """Semantic search within tenant's knowledge base."""
        results = await self.vectorstore.asimilarity_search(
            query, k=k, filter={"tenant_id": self.tenant_id}
        )
        return [
            {
                "content": r.page_content,
                "metadata": r.metadata,
                "score": r.score,
            }
            for r in results
        ]
```

---

## 9. Testing Strategy

### 9.1 Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ← Full workflow tests (5%)
                    │  Tests  │
                   ┌┴─────────┴┐
                   │ Integration│ ← Agent + Tool + DB tests (15%)
                   │   Tests    │
                  ┌┴────────────┴┐
                  │    Unit       │ ← Tool logic, prompts, scoring (80%)
                  │    Tests      │
                  └───────────────┘
```

### 9.2 Unit Tests

```python
# tests/unit/test_commission_calculator.py
import pytest
from decimal import Decimal
from implementations.commission_calculator import CommissionCalculator

class TestCommissionCalculator:
    def setup_method(self):
        self.calc = CommissionCalculator()
    
    def test_bronze_tier_standard_product(self):
        result = self.calc.calculate(
            deal_id="deal_001",
            partner_id="partner_001",
            deal_amount=Decimal("10000.00"),
            product_category="standard",
            partner_tier="bronze",
        )
        assert result.commission_amount == Decimal("500.00")
        assert result.tier == "bronze"
    
    def test_platinum_tier_enterprise_product(self):
        result = self.calc.calculate(
            deal_id="deal_002",
            partner_id="partner_002",
            deal_amount=Decimal("50000.00"),
            product_category="enterprise",
            partner_tier="platinum",
        )
        # 15% * 1.5 multiplier = 22.5%
        assert result.commission_amount == Decimal("11250.00")
    
    def test_audit_hash_consistency(self):
        result1 = self.calc.calculate(
            deal_id="deal_003",
            partner_id="partner_003",
            deal_amount=Decimal("1000.00"),
            product_category="standard",
            partner_tier="silver",
        )
        result2 = self.calc.calculate(
            deal_id="deal_003",
            partner_id="partner_003",
            deal_amount=Decimal("1000.00"),
            product_category="standard",
            partner_tier="silver",
        )
        assert result1.audit_hash == result2.audit_hash
    
    def test_invalid_tier_raises(self):
        with pytest.raises(KeyError):
            self.calc.calculate(
                deal_id="deal_004",
                partner_id="partner_004",
                deal_amount=Decimal("1000.00"),
                product_category="standard",
                partner_tier="invalid_tier",
            )
```

```python
# tests/unit/test_enablement_score.py
import pytest
from implementations.enablement_score import calculate_enablement_score

class TestEnablementScore:
    def test_perfect_score(self):
        partner_data = {
            "modules_completed": 10,
            "modules_assigned": 10,
            "certified": True,
            "avg_quiz_score": 95,
            "deals_closed_30d": 15,
        }
        score = calculate_enablement_score(partner_data)
        assert score >= 90
    
    def test_zero_score(self):
        partner_data = {
            "modules_completed": 0,
            "modules_assigned": 10,
            "certified": False,
            "certification_in_progress": False,
            "avg_quiz_score": 0,
            "deals_closed_30d": 0,
        }
        score = calculate_enablement_score(partner_data)
        assert score == 0
    
    def test_partial_completion(self):
        partner_data = {
            "modules_completed": 5,
            "modules_assigned": 10,
            "certified": False,
            "certification_in_progress": True,
            "avg_quiz_score": 70,
            "deals_closed_30d": 3,
        }
        score = calculate_enablement_score(partner_data)
        assert 30 < score < 70
```

### 9.3 Integration Tests

```python
# tests/integration/test_onboarding_flow.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
class TestOnboardingFlow:
    async def test_complete_onboarding_happy_path(self):
        """Test successful end-to-end onboarding."""
        # Arrange
        partner_id = "partner_test_001"
        tenant_id = "tenant_test_001"
        
        with patch("implementations.tools.kyc_provider") as mock_kyc, \
             patch("implementations.tools.crm_writer") as mock_crm:
            
            mock_kyc.verify.return_value = KycResult(
                status="verified",
                confidence=0.95,
                flags=[],
            )
            
            # Act
            agent = await get_test_agent("onboarding", tenant_id)
            result = await agent.ainvoke({
                "messages": [{
                    "role": "user",
                    "content": f"Onboard partner {partner_id}"
                }],
                "config": {"configurable": {"tenant_id": tenant_id}},
            })
            
            # Assert
            assert result["output"]["status"] == "onboarding_complete"
            assert result["output"]["account_provisioned"] is True
            mock_crm.create_partner.assert_called_once()
    
    async def test_onboarding_escalates_on_low_confidence(self):
        """Test that low KYC confidence triggers escalation."""
        partner_id = "partner_test_002"
        tenant_id = "tenant_test_001"
        
        with patch("implementations.tools.kyc_provider") as mock_kyc:
            mock_kyc.verify.return_value = KycResult(
                status="uncertain",
                confidence=0.65,
                flags=["document_blurry", "name_mismatch"],
            )
            
            agent = await get_test_agent("onboarding", tenant_id)
            result = await agent.ainvoke({
                "messages": [{
                    "role": "user",
                    "content": f"Onboard partner {partner_id}"
                }],
                "config": {"configurable": {"tenant_id": tenant_id}},
            })
            
            assert result["output"]["status"] == "escalated"
            assert result["output"]["escalation_reason"] == "low_confidence"
```

### 9.4 E2E Tests

```python
# tests/e2e/test_partner_lifecycle.py
import pytest
import asyncio

@pytest.mark.asyncio
class TestPartnerLifecycle:
    async def test_full_partner_journey(self):
        """E2E: Onboard → Enable → Track Commission → Analyze."""
        tenant_id = "e2e_tenant_001"
        partner_id = f"e2e_partner_{uuid.uuid4().hex[:8]}"
        
        # Step 1: Onboard
        onboarding = await get_agent("onboarding", tenant_id)
        onboard_result = await onboarding.ainvoke({
            "messages": [{"role": "user", "content": f"Start onboarding for {partner_id}"}],
        })
        assert onboard_result["output"]["status"] == "onboarding_complete"
        
        # Step 2: Enable
        enablement = await get_agent("enablement", tenant_id)
        enable_result = await enablement.ainvoke({
            "messages": [{"role": "user", "content": f"Create learning path for {partner_id}"}],
        })
        assert enable_result["output"]["learning_path_created"] is True
        
        # Step 3: Track Commission
        commission = await get_agent("commission", tenant_id)
        commission_result = await commission.ainvoke({
            "messages": [{"role": "user", "content": f"Calculate commission for deal_001, partner {partner_id}, $25000"}],
        })
        assert commission_result["output"]["commission_amount"] > 0
        
        # Step 4: Analyze
        analytics = await get_agent("analytics", tenant_id)
        analytics_result = await analytics.ainvoke({
            "messages": [{"role": "user", "content": f"Get dashboard for {partner_id}"}],
        })
        assert "kpis" in analytics_result["output"]
```

### 9.5 Prompt Testing

```python
# tests/prompts/test_prompt_quality.py
import pytest
from langsmith import evaluate

class TestPromptQuality:
    def test_onboarding_prompt_includes_compliance(self):
        """Verify onboarding prompt mentions compliance requirements."""
        assert "compliance" in ONBOARDING_SYSTEM_PROMPT.lower()
        assert "KYC" in ONBOARDING_SYSTEM_PROMPT
        assert "escalat" in ONBOARDING_SYSTEM_PROMPT.lower()
    
    def test_commission_prompt_includes_audit(self):
        """Verify commission prompt mentions audit trail."""
        assert "audit" in COMMISSION_SYSTEM_PROMPT.lower()
        assert "never modify historical" in COMMISSION_SYSTEM_PROMPT.lower()
    
    def test_all_prompts_include_tenant_context(self):
        """Verify all prompts include tenant context variables."""
        prompts = [
            ONBOARDING_SYSTEM_PROMPT,
            ENABLEMENT_SYSTEM_PROMPT,
            COMMISSION_SYSTEM_PROMPT,
            ANALYTICS_SYSTEM_PROMPT,
        ]
        for prompt in prompts:
            assert "{tenant_name}" in prompt
            assert "{region}" in prompt

    @pytest.mark.asyncio
    async def test_onboarding_agent_response_quality(self):
        """Evaluate onboarding agent responses using LangSmith."""
        dataset = "onboarding-eval-dataset"
        
        results = await evaluate(
            agent_function,
            data=dataset,
            evaluators=[
                "correctness",
                "helpfulness",
                "safety",
            ],
        )
        
        assert results["correctness"] > 0.85
        assert results["helpfulness"] > 0.80
        assert results["safety"] > 0.95
```

### 9.6 Load Testing

```python
# tests/performance/test_agent_load.py
import asyncio
import time
from statistics import mean, stdev

class TestAgentPerformance:
    @pytest.mark.asyncio
    async def test_concurrent_onboarding_requests(self):
        """Test system under concurrent onboarding load."""
        num_concurrent = 50
        num_iterations = 5
        
        latencies = []
        
        for i in range(num_iterations):
            start = time.time()
            
            tasks = [
                self._send_onboarding_request(f"partner_{i}_{j}")
                for j in range(num_concurrent)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed = time.time() - start
            latencies.append(elapsed)
            
            # Assert no failures
            failures = [r for r in results if isinstance(r, Exception)]
            assert len(failures) == 0, f"{len(failures)} requests failed"
        
        avg_latency = mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        # Performance SLA: 50 concurrent requests < 30 seconds
        assert avg_latency < 30.0
        assert p95_latency < 45.0
    
    @pytest.mark.asyncio
    async def test_commission_calculation_throughput(self):
        """Test commission calculation throughput."""
        num_calculations = 1000
        
        start = time.time()
        
        tasks = [
            self._calculate_commission(f"deal_{i}")
            for i in range(num_calculations)
        ]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start
        throughput = num_calculations / elapsed
        
        # SLA: > 100 calculations/second
        assert throughput > 100.0
```

### 9.7 Test Configuration

```yaml
# tests/conftest.py — Pytest configuration
import pytest
import os

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "performance: Performance tests")

@pytest.fixture
def test_tenant_config():
    return TenantConfig(
        tenant_id="test_tenant_001",
        tenant_name="Test Broker Inc.",
        region="US-East",
        language="en",
        compliance_framework="SOC2",
        default_commission_tier="bronze",
        model_name="gpt-4o",
    )

@pytest.fixture
async def test_agent_factory(test_tenant_config):
    config_store = MockTenantConfigStore(test_tenant_config)
    factory = TenantAgentFactory(config_store)
    yield factory
    await factory.close()
```

### 9.8 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Broker Enablement Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[test]"
      - run: pytest tests/unit -v --cov=implementations --cov-report=xml
      - uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[test]"
      - run: pytest tests/integration -v -m integration
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[test]"
      - run: pytest tests/e2e -v -m e2e
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}

  performance-tests:
    runs-on: ubuntu-latest
    needs: [integration-tests]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[test]"
      - run: pytest tests/performance -v -m performance
```

---

## Appendix A: Environment Variables

```bash
# .env.example
# LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=broker-enablement

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/broker_enablement
REDIS_URL=redis://localhost:6379

# Vector Store
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1

# KYC Provider
KYC_PROVIDER=onfido
ONFIDO_API_KEY=...

# Email
SENDGRID_API_KEY=...
EMAIL_FROM_ADDRESS=noreply@brokerenablement.com

# Observability
SENTRY_DSN=...
DATADOG_API_KEY=...
```

## Appendix B: Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  API Pods   │  │  API Pods   │  │  API Pods   │     │
│  │  (FastAPI)  │  │  (FastAPI)  │  │  (FastAPI)  │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                │                │             │
│  ┌──────▼────────────────▼────────────────▼──────┐     │
│  │              Celery Worker Pool               │     │
│  │  (Commission calc, report generation, etc.)    │     │
│  └──────┬────────────────┬────────────────┬──────┘     │
│         │                │                │             │
│  ┌──────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐     │
│  │ PostgreSQL  │  │   Redis    │  │  Pinecone  │     │
│  │ (HA: 3 nodes)│  │  (Cluster) │  │  (Managed) │     │
│  └─────────────┘  └────────────┘  └────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

*End of Implementation Plan*
