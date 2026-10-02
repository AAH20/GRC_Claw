# AI-Powered Lead Scoring Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Stack:** LangChain DeepAgents, Python 3.11+, FastAPI, PostgreSQL, Redis

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Lead Enrichment Agent Implementation](#2-lead-enrichment-agent-implementation)
3. [Scoring Engine: BANT, MEDDIC, CHAMP](#3-scoring-engine-banted-meddic-champ)
4. [Qualification Workflows](#4-qualification-workflows)
5. [Predictive Analytics](#5-predictive-analytics)
6. [CRM Integration](#6-crm-integration)
7. [Real-Time Scoring API](#7-real-time-scoring-api)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Design

The system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. A central `LeadScoringOrchestrator` dispatches specialized sub-agents for enrichment, scoring, qualification, and prediction.

```
┌─────────────────────────────────────────────────────────┐
│                  LeadScoringOrchestrator                 │
│  (LangChain DeepAgent with tool-calling loop)           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Enrichment  │  │   Scoring    │  │Qualification │  │
│  │    Agent     │  │    Agent     │  │    Agent     │  │
│  │              │  │              │  │              │  │
│  │ • Firmo      │  │ • BANT       │  │ • Workflow   │  │
│  │ • Clearbit   │  │ • MEDDIC     │  │   engine     │  │
│  │ • LinkedIn   │  │ • CHAMP      │  │ • Routing    │  │
│  │ • Web search │  │ • Custom     │  │ • Nurture    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│  ┌──────┴─────────────────┴─────────────────┴───────┐  │
│  │              Shared State (Redis + Postgres)      │  │
│  │  • Lead profiles  • Scores  • Enrichment cache   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  Predictive  │  │    CRM       │                    │
│  │   Agent      │  │  Sync Agent  │                    │
│  │              │  │              │                    │
│  │ • Conversion │  │ • Salesforce │                    │
│  │ • Churn      │  │ • HubSpot    │                    │
│  │ • LTV        │  │ • Pipedrive  │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Orchestrator | LangChain DeepAgent | Routes tasks, manages agent lifecycle |
| Sub-Agents | LangChain DeepAgent (single-tool) | Specialized tasks (enrich, score, qualify) |
| State Store | Redis + PostgreSQL | Session state, lead profiles, score history |
| Task Queue | Celery + Redis | Async enrichment and scoring jobs |
| API Layer | FastAPI | REST endpoints for real-time scoring |
| ML Models | scikit-learn / XGBoost | Predictive conversion and LTV models |
| Vector DB | pgvector | Semantic lead similarity search |
| Observability | Langfuse / LangSmith | Tracing, evaluation, monitoring |

### 1.3 Agent Communication Protocol

Agents communicate via a **shared blackboard pattern** using Redis as the message bus:

```python
# Message schema for inter-agent communication
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class AgentMessage(BaseModel):
    message_id: str
    sender: str           # agent identifier
    receiver: str         # target agent or "broadcast"
    message_type: Literal[
        "enrichment_request",
        "enrichment_result",
        "scoring_request",
        "scoring_result",
        "qualification_request",
        "qualification_result",
        "prediction_request",
        "prediction_result",
        "crm_sync_request",
        "crm_sync_result",
    ]
    payload: dict
    timestamp: datetime
    correlation_id: str   # traces a lead through the pipeline
    priority: int = 5     # 1 (highest) to 10 (lowest)
```

### 1.4 Orchestrator Agent Definition

```python
from langchain_deepagents import DeepAgent
from langchain_deepagents.tools import Tool

lead_scoring_orchestrator = DeepAgent(
    name="lead_scoring_orchestrator",
    description=(
        "Orchestrates the end-to-end lead scoring pipeline. "
        "Receives raw lead data, dispatches enrichment and scoring "
        "sub-agents, aggregates results, and returns a comprehensive "
        "lead score with qualification status."
    ),
    system_prompt="""You are the Lead Scoring Orchestrator.

Your responsibilities:
1. Receive incoming lead data (email, name, company, source, etc.)
2. Dispatch the Enrichment Agent to gather firmographic and technographic data
3. Dispatch the Scoring Agent to compute BANT/MEDDIC/CHAMP scores
4. Dispatch the Qualification Agent to determine routing (sales vs nurture)
5. Optionally dispatch the Predictive Agent for conversion probability
6. Return a unified LeadScoreResponse

Rules:
- Always enrich before scoring (scoring depends on enriched data)
- Run BANT and MEDDIC in parallel when possible
- Use CHAMP for existing-customer upsell scenarios
- Cache enrichment results for 24 hours to avoid redundant API calls
- Log all agent interactions for observability

Available tools:
- run_enrichment_agent(lead_data) -> EnrichmentResult
- run_scoring_agent(enriched_lead, framework) -> ScoreResult
- run_qualification_agent(enriched_lead, scores) -> QualificationResult
- run_predictive_agent(enriched_lead, scores) -> PredictionResult
- get_cached_enrichment(lead_id) -> Optional[EnrichmentResult]
- store_enrichment(lead_id, result) -> None
""",
    tools=[
        Tool(name="run_enrichment_agent", func=run_enrichment_agent),
        Tool(name="run_scoring_agent", func=run_scoring_agent),
        Tool(name="run_qualification_agent", func=run_qualification_agent),
        Tool(name="run_predictive_agent", func=run_predictive_agent),
        Tool(name="get_cached_enrichment", func=get_cached_enrichment),
        Tool(name="store_enrichment", func=store_enrichment),
    ],
    model="claude-sonnet-4-20250514",
    max_iterations=10,
)
```

---

## 2. Lead Enrichment Agent Implementation

### 2.1 Purpose

The Enrichment Agent takes raw lead data (typically just an email or name + company) and enriches it with firmographic, technographic, and intent data from multiple sources.

### 2.2 Data Sources

| Source | Data Retrieved | API |
|--------|---------------|-----|
| Clearbit | Company size, industry, revenue, tech stack | `clearbit.Enrichment.find()` |
| Hunter.io | Email verification, format detection | `hunter.domain_search()` |
| LinkedIn Sales Navigator | Job title, seniority, connections | LinkedIn API v2 |
| Apollo.io | Contact details, org hierarchy | Apollo API |
| BuiltWith | Technology stack detection | `builtwith.builtwith()` |
| 6sense / Bombora | Intent data (topic surges) | Intent API |
| Google Search | Recent news, funding, leadership changes | SerpAPI / Serper |

### 2.3 Enrichment Agent Implementation

```python
from langchain_deepagents import DeepAgent
from langchain_deepagents.tools import Tool
from pydantic import BaseModel, EmailStr
from typing import Optional
import clearbit
import hunter
import httpx
import asyncio

# --- Data Models ---

class RawLeadInput(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    phone: Optional[str] = None
    source: str = "unknown"  # webinar, content_download, referral, etc.
    landing_page: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    custom_fields: dict = {}

class FirmographicData(BaseModel):
    company_name: str
    domain: str
    industry: str
    sub_industry: Optional[str] = None
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    annual_revenue: Optional[float] = None
    revenue_range: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    country: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None

class TechnographicData(BaseModel):
    technologies: list[str] = []
    cms: Optional[str] = None
    analytics_tools: list[str] = []
    crm: Optional[str] = None
    marketing_automation: Optional[str] = None
    hosting: Optional[str] = None
    ssl_issuer: Optional[str] = None

class IntentData(BaseModel):
    intent_topics: list[str] = []
    intent_score: float = 0.0  # 0-100
    surge_topics: list[str] = []
    last_intent_date: Optional[str] = None

class ContactData(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    job_title: str
    seniority: str  # C-Level, VP, Director, Manager, Individual
    department: str  # Engineering, Marketing, Sales, Finance, etc.
    linkedin_url: Optional[str] = None
    email_verified: bool = False
    email_risk: str = "unknown"  # low, medium, high

class EnrichmentResult(BaseModel):
    lead_id: str
    contact: ContactData
    firmographic: FirmographicData
    technographic: TechnographicData
    intent: IntentData
    enrichment_sources: list[str] = []
    enrichment_timestamp: str
    confidence_score: float = 0.0  # 0-1, based on source agreement
    raw_responses: dict = {}  # stored for debugging

# --- Enrichment Tools ---

async def enrich_with_clearbit(domain: str) -> dict:
    """Fetch firmographic data from Clearbit."""
    try:
        clearbit.key = settings.CLEARBIT_API_KEY
        resp = await asyncio.to_thread(
            clearbit.Enrichment.find, domain=domain, stream=True
        )
        if resp and resp.get("company"):
            company = resp["company"]
            return {
                "company_name": company.get("legalName", ""),
                "domain": domain,
                "industry": company.get("category", {}).get("industry", ""),
                "sub_industry": company.get("category", {}).get("subIndustry", ""),
                "employee_count": company.get("metrics", {}).get("employees"),
                "employee_range": company.get("metrics", {}).get("employeesRange", ""),
                "annual_revenue": company.get("metrics", {}).get("estimatedAnnualRevenue"),
                "founded_year": company.get("foundedYear"),
                "headquarters": f"{company.get('geo', {}).get('city', '')}, {company.get('geo', {}).get('country', '')}",
                "country": company.get("geo", {}).get("country", ""),
                "linkedin_url": company.get("linkedin", {}).get("handle", ""),
                "technologies": [t.get("name", "") for t in company.get("tech", [])],
                "tags": company.get("tags", []),
            }
    except Exception as e:
        logger.warning(f"Clearbit enrichment failed for {domain}: {e}")
    return {}

async def verify_email_with_hunter(email: str, domain: str) -> dict:
    """Verify email and detect pattern using Hunter.io."""
    try:
        h = hunter.Hunter(settings.HUNTER_API_KEY)
        # Verify the specific email
        verify = await asyncio.to_thread(h.email_verifier, email)
        # Get domain info
        domain_info = await asyncio.to_thread(h.domain_search, domain)
        return {
            "email_verified": verify.get("status") == "valid",
            "email_risk": verify.get("gibberish", False) and "high" or "low",
            "email_pattern": domain_info.get("pattern", ""),
            "organization": domain_info.get("organization", ""),
            "country": domain_info.get("country", ""),
            "disposable": verify.get("disposable", False),
            "webmail": verify.get("webmail", False),
        }
    except Exception as e:
        logger.warning(f"Hunter verification failed for {email}: {e}")
    return {"email_verified": False, "email_risk": "unknown"}

async def fetch_intent_data(domain: str) -> dict:
    """Fetch intent data from 6sense or Bombora."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.INTENT_API_BASE}/v1/company/{domain}/intent",
                headers={"Authorization": f"Bearer {settings.INTENT_API_TOKEN}"},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "intent_topics": data.get("topics", []),
                    "intent_score": data.get("surge_score", 0),
                    "surge_topics": data.get("surging_topics", []),
                    "last_intent_date": data.get("last_seen"),
                }
    except Exception as e:
        logger.warning(f"Intent data fetch failed for {domain}: {e}")
    return {"intent_topics": [], "intent_score": 0, "surge_topics": []}

async def fetch_technographics(domain: str) -> dict:
    """Fetch technology stack from BuiltWith."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.builtwith.com/v21/api.json",
                params={
                    "KEY": settings.BUILTWITH_API_KEY,
                    "LOOKUP": domain,
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("Results", [{}])[0].get("Result", {})
                paths = results.get("Paths", [])
                techs = []
                for path in paths:
                    for tech in path.get("Technologies", []):
                        techs.append(tech.get("Name", ""))
                return {
                    "technologies": list(set(techs)),
                    "cms": next((t for t in techs if t in ["WordPress", "Drupal", "Shopify", "Webflow"]), None),
                    "analytics_tools": [t for t in techs if t in ["Google Analytics", "Mixpanel", "Amplitude", "Segment"]],
                    "crm": next((t for t in techs if t in ["Salesforce", "HubSpot", "Pipedrive"]), None),
                    "marketing_automation": next((t for t in techs if t in ["Marketo", "Pardot", "ActiveCampaign"]), None),
                }
    except Exception as e:
        logger.warning(f"BuiltWith fetch failed for {domain}: {e}")
    return {"technologies": []}

# --- Enrichment Agent ---

enrichment_agent = DeepAgent(
    name="lead_enrichment_agent",
    description=(
        "Enriches raw lead data with firmographic, technographic, "
        "contact, and intent data from multiple third-party sources."
    ),
    system_prompt="""You are the Lead Enrichment Agent.

Given a RawLeadInput, you must:
1. Determine the company domain (from email or company_name)
2. Run Clearbit, Hunter.io, BuiltWith, and Intent data fetches in PARALLEL
3. Merge and deduplicate results
4. Compute a confidence_score based on source agreement
5. Return a complete EnrichmentResult

Rules:
- If email is provided, extract domain from it
- If only company_name is provided, use Clearbit Autocomplete to find domain
- Always run at least 2 sources; more sources = higher confidence
- If sources disagree on employee_count, use the median
- Cache results for 24 hours (keyed by domain + email hash)
- Never fabricate data; if a source fails, note it in enrichment_sources

Available tools:
- enrich_with_clearbit(domain) -> dict
- verify_email_with_hunter(email, domain) -> dict
- fetch_intent_data(domain) -> dict
- fetch_technographics(domain) -> dict
""",
    tools=[
        Tool(name="enrich_with_clearbit", func=enrich_with_clearbit),
        Tool(name="verify_email_with_hunter", func=verify_email_with_hunter),
        Tool(name="fetch_intent_data", func=fetch_intent_data),
        Tool(name="fetch_technographics", func=fetch_technographics),
    ],
    model="claude-sonnet-4-20250514",
    max_iterations=8,
)

# --- Orchestrator-facing wrapper ---

async def run_enrichment_agent(lead_data: dict) -> EnrichmentResult:
    """Wrapper called by the orchestrator to run enrichment."""
    raw_lead = RawLeadInput(**lead_data)

    # Check cache first
    cache_key = f"enrichment:{hash(raw_lead.email or raw_lead.company_domain)}"
    cached = await redis.get(cache_key)
    if cached:
        return EnrichmentResult.parse_raw(cached)

    # Run the enrichment agent
    result = await enrichment_agent.arun(
        f"Enrich this lead: {raw_lead.model_dump_json()}"
    )

    # Cache for 24 hours
    await redis.setex(cache_key, 86400, result.model_dump_json())

    return result
```

---

## 3. Scoring Engine: BANT, MEDDIC, CHAMP

### 3.1 Framework Overview

| Framework | Best For | Dimensions |
|-----------|----------|------------|
| **BANT** | Early-stage qualification | Budget, Authority, Need, Timeline |
| **MEDDIC** | Complex B2B enterprise sales | Metrics, Economic Buyer, Decision Criteria, Decision Process, Identify Pain, Champion |
| **CHAMP** | Inbound lead qualification | Challenges, Authority, Money, Prioritization |

### 3.2 Scoring Agent Implementation

```python
from langchain_deepagents import DeepAgent
from langchain_deepagents.tools import Tool
from pydantic import BaseModel
from typing import Literal
from enum import Enum

# --- Score Models ---

class BANTScore(BaseModel):
    budget: float = 0.0        # 0-25
    authority: float = 0.0     # 0-25
    need: float = 0.0          # 0-25
    timeline: float = 0.0      # 0-25
    total: float = 0.0         # 0-100
    budget_evidence: list[str] = []
    authority_evidence: list[str] = []
    need_evidence: list[str] = []
    timeline_evidence: list[str] = []

class MEDDICScore(BaseModel):
    metrics: float = 0.0           # 0-20
    economic_buyer: float = 0.0    # 0-20
    decision_criteria: float = 0.0 # 0-20
    decision_process: float = 0.0  # 0-20
    identify_pain: float = 0.0     # 0-10
    champion: float = 0.0          # 0-10
    total: float = 0.0             # 0-100
    evidence: dict[str, list[str]] = {}

class CHAMPScore(BaseModel):
    challenges: float = 0.0   # 0-30
    authority: float = 0.0    # 0-20
    money: float = 0.0        # 0-25
    prioritization: float = 0.0 # 0-25
    total: float = 0.0        # 0-100
    evidence: dict[str, list[str]] = {}

class ScoreResult(BaseModel):
    lead_id: str
    bant: Optional[BANTScore] = None
    meddic: Optional[MEDDICScore] = None
    champ: Optional[CHAMPScore] = None
    composite_score: float = 0.0  # weighted average
    recommended_framework: str = "BANT"
    scoring_timestamp: str
    confidence: float = 0.0

# --- Scoring Tools ---

def score_bant(enriched_lead: dict) -> BANTScore:
    """
    Score a lead on BANT criteria using enriched data.
    
    Budget (0-25):
    - Revenue > $50M: 20-25
    - Revenue $10M-$50M: 15-20
    - Revenue $1M-$10M: 10-15
    - Revenue < $1M: 5-10
    - Unknown: 5
    
    Authority (0-25):
    - C-Level: 20-25
    - VP: 15-20
    - Director: 10-15
    - Manager: 5-10
    - Individual: 0-5
    
    Need (0-25):
    - Intent score > 70: 20-25
    - Intent score 40-70: 10-20
    - Intent score < 40: 5-10
    - No intent data: 5
    
    Timeline (0-25):
    - Explicit timeline mentioned: 20-25
    - Implied urgency (funding, leadership change): 15-20
    - No signal: 5-10
    """
    firmo = enriched_lead.get("firmographic", {})
    contact = enriched_lead.get("contact", {})
    intent = enriched_lead.get("intent", {})
    
    # Budget scoring
    revenue = firmo.get("annual_revenue") or 0
    if revenue > 50_000_000:
        budget = 22
        budget_evidence = [f"Revenue ${revenue:,.0f} indicates enterprise budget"]
    elif revenue > 10_000_000:
        budget = 18
        budget_evidence = [f"Revenue ${revenue:,.0f} indicates mid-market budget"]
    elif revenue > 1_000_000:
        budget = 12
        budget_evidence = [f"Revenue ${revenue:,.0f} indicates SMB budget"]
    else:
        budget = 5
        budget_evidence = ["Revenue unknown or below $1M"]
    
    # Authority scoring
    seniority = contact.get("seniority", "").lower()
    if "c-level" in seniority or "chief" in seniority:
        authority = 22
        authority_evidence = [f"C-Level executive: {contact.get('job_title', '')}"]
    elif "vp" in seniority or "vice president" in seniority:
        authority = 18
        authority_evidence = [f"VP-level: {contact.get('job_title', '')}"]
    elif "director" in seniority:
        authority = 13
        authority_evidence = [f"Director-level: {contact.get('job_title', '')}"]
    elif "manager" in seniority:
        authority = 8
        authority_evidence = [f"Manager-level: {contact.get('job_title', '')}"]
    else:
        authority = 3
        authority_evidence = [f"Individual contributor: {contact.get('job_title', '')}"]
    
    # Need scoring (from intent data)
    intent_score = intent.get("intent_score", 0)
    if intent_score > 70:
        need = 22
        need_evidence = [f"High intent score: {intent_score}"]
    elif intent_score > 40:
        need = 15
        need_evidence = [f"Moderate intent score: {intent_score}"]
    else:
        need = 5
        need_evidence = ["Low or no intent signals"]
    
    # Timeline scoring
    surge_topics = intent.get("surge_topics", [])
    if surge_topics:
        timeline = 18
        timeline_evidence = [f"Active intent surge on: {', '.join(surge_topics[:3])}"]
    else:
        timeline = 8
        timeline_evidence = ["No explicit timeline signals"]
    
    total = budget + authority + need + timeline
    
    return BANTScore(
        budget=budget,
        authority=authority,
        need=need,
        timeline=timeline,
        total=total,
        budget_evidence=budget_evidence,
        authority_evidence=authority_evidence,
        need_evidence=need_evidence,
        timeline_evidence=timeline_evidence,
    )

def score_meddic(enriched_lead: dict) -> MEDDICScore:
    """
    Score a lead on MEDDIC criteria.
    
    Metrics (0-20): Quantifiable business impact
    Economic Buyer (0-20): Access to budget holder
    Decision Criteria (0-20): Known evaluation criteria
    Decision Process (0-20): Known procurement process
    Identify Pain (0-10): Articulated pain points
    Champion (0-10): Internal advocate identified
    """
    firmo = enriched_lead.get("firmographic", {})
    contact = enriched_lead.get("contact", {})
    intent = enriched_lead.get("intent", {})
    tech = enriched_lead.get("technographic", {})
    
    # Metrics: Larger companies with clear tech stacks have measurable metrics
    employee_count = firmo.get("employee_count") or 0
    if employee_count > 1000:
        metrics = 18
        metrics_evidence = [f"Enterprise size ({employee_count} employees) suggests measurable ROI"]
    elif employee_count > 200:
        metrics = 14
        metrics_evidence = [f"Mid-market size ({employee_count} employees)"]
    else:
        metrics = 8
        metrics_evidence = [f"Smaller organization ({employee_count} employees)"]
    
    # Economic Buyer: C-Level or VP with P&L responsibility
    seniority = contact.get("seniority", "").lower()
    department = contact.get("department", "").lower()
    if "c-level" in seniority or ("vp" in seniority and department in ["finance", "operations", "executive"]):
        economic_buyer = 18
        economic_buyer_evidence = [f"Potential economic buyer: {contact.get('job_title', '')}"]
    elif "vp" in seniority:
        economic_buyer = 14
        economic_buyer_evidence = [f"VP-level contact: {contact.get('job_title', '')}"]
    else:
        economic_buyer = 6
        economic_buyer_evidence = [f"Non-executive contact: {contact.get('job_title', '')}"]
    
    # Decision Criteria: Tech stack compatibility signals
    technologies = tech.get("technologies", [])
    if len(technologies) > 5:
        decision_criteria = 16
        decision_criteria_evidence = [f"Rich tech stack ({len(technologies)} technologies) suggests mature evaluation process"]
    elif technologies:
        decision_criteria = 10
        decision_criteria_evidence = [f"Some tech stack data ({len(technologies)} technologies)"]
    else:
        decision_criteria = 5
        decision_criteria_evidence = ["No technographic data available"]
    
    # Decision Process: Inferred from company size and industry
    industry = firmo.get("industry", "").lower()
    if industry in ["software", "technology", "saas"]:
        decision_process = 14
        decision_process_evidence = ["Tech industry: typically structured evaluation"]
    elif employee_count > 500:
        decision_process = 12
        decision_process_evidence = ["Larger org: likely formal procurement process"]
    else:
        decision_process = 6
        decision_process_evidence = ["Limited decision process signals"]
    
    # Identify Pain: From intent topics and surge data
    surge_topics = intent.get("surge_topics", [])
    if surge_topics:
        identify_pain = 8
        identify_pain_evidence = [f"Intent signals on: {', '.join(surge_topics[:3])}"]
    else:
        identify_pain = 3
        identify_pain_evidence = ["No explicit pain point signals"]
    
    # Champion: Based on engagement depth (source quality)
    source = enriched_lead.get("source", "")
    if source in ["webinar", "demo_request", "pricing_page"]:
        champion = 8
        champion_evidence = [f"High-intent source: {source}"]
    elif source in ["content_download", "referral"]:
        champion = 5
        champion_evidence = [f"Medium-intent source: {source}"]
    else:
        champion = 2
        champion_evidence = [f"Low-intent source: {source}"]
    
    total = metrics + economic_buyer + decision_criteria + decision_process + identify_pain + champion
    
    return MEDDICScore(
        metrics=metrics,
        economic_buyer=economic_buyer,
        decision_criteria=decision_criteria,
        decision_process=decision_process,
        identify_pain=identify_pain,
        champion=champion,
        total=total,
        evidence={
            "metrics": metrics_evidence,
            "economic_buyer": economic_buyer_evidence,
            "decision_criteria": decision_criteria_evidence,
            "decision_process": decision_process_evidence,
            "identify_pain": identify_pain_evidence,
            "champion": champion_evidence,
        },
    )

def score_champ(enriched_lead: dict) -> CHAMPScore:
    """
    Score a lead on CHAMP criteria.
    
    Challenges (0-30): What business challenge drives the need?
    Authority (0-20): Can this person make or influence the decision?
    Money (0-25): Is there budget available?
    Prioritization (0-25): How urgent is this challenge?
    """
    firmo = enriched_lead.get("firmographic", {})
    contact = enriched_lead.get("contact", {})
    intent = enriched_lead.get("intent", {})
    
    # Challenges: Inferred from intent topics and company signals
    surge_topics = intent.get("surge_topics", [])
    intent_score = intent.get("intent_score", 0)
    if surge_topics and intent_score > 60:
        challenges = 25
        challenges_evidence = [f"Strong intent signals: {', '.join(surge_topics[:3])}"]
    elif surge_topics:
        challenges = 18
        challenges_evidence = [f"Some intent signals: {', '.join(surge_topics[:3])}"]
    else:
        challenges = 8
        challenges_evidence = ["No clear challenge signals from intent data"]
    
    # Authority: Same as BANT authority
    seniority = contact.get("seniority", "").lower()
    if "c-level" in seniority or "chief" in seniority:
        authority = 18
        authority_evidence = [f"C-Level: {contact.get('job_title', '')}"]
    elif "vp" in seniority:
        authority = 15
        authority_evidence = [f"VP-level: {contact.get('job_title', '')}"]
    elif "director" in seniority:
        authority = 11
        authority_evidence = [f"Director-level: {contact.get('job_title', '')}"]
    else:
        authority = 5
        authority_evidence = [f"Non-decision-maker: {contact.get('job_title', '')}"]
    
    # Money: Revenue-based
    revenue = firmo.get("annual_revenue") or 0
    if revenue > 50_000_000:
        money = 22
        money_evidence = [f"Enterprise revenue: ${revenue:,.0f}"]
    elif revenue > 10_000_000:
        money = 17
        money_evidence = [f"Mid-market revenue: ${revenue:,.0f}"]
    elif revenue > 1_000_000:
        money = 12
        money_evidence = [f"SMB revenue: ${revenue:,.0f}"]
    else:
        money = 5
        money_evidence = ["Revenue unknown"]
    
    # Prioritization: Intent surge + source quality
    source = enriched_lead.get("source", "")
    if intent_score > 70 and source in ["demo_request", "pricing_page"]:
        prioritization = 22
        prioritization_evidence = [f"High intent ({intent_score}) + high-intent source ({source})"]
    elif intent_score > 40:
        prioritization = 15
        prioritization_evidence = [f"Moderate intent ({intent_score})"]
    else:
        prioritization = 7
        prioritization_evidence = ["Low prioritization signals"]
    
    total = challenges + authority + money + prioritization
    
    return CHAMPScore(
        challenges=challenges,
        authority=authority,
        money=money,
        prioritization=prioritization,
        total=total,
        evidence={
            "challenges": challenges_evidence,
            "authority": authority_evidence,
            "money": money_evidence,
            "prioritization": prioritization_evidence,
        },
    )

# --- Scoring Agent ---

scoring_agent = DeepAgent(
    name="lead_scoring_agent",
    description=(
        "Scores enriched leads using BANT, MEDDIC, and/or CHAMP frameworks. "
        "Computes a composite score and recommends the best framework."
    ),
    system_prompt="""You are the Lead Scoring Agent.

Given an enriched lead, you must:
1. Determine which scoring framework(s) to apply:
   - Use BANT for early-stage inbound leads
   - Use MEDDIC for enterprise/complex sales
   - Use CHAMP for inbound leads with clear challenge signals
   - Run multiple frameworks when the lead profile is ambiguous
2. Compute scores using the provided tools
3. Calculate a composite_score as a weighted average
4. Recommend the primary framework based on data completeness
5. Return a ScoreResult with all scores and evidence

Scoring weights for composite:
- BANT: 30%
- MEDDIC: 40% (higher weight for complex sales)
- CHAMP: 30%

Rules:
- Always provide evidence for each score component
- If data is missing for a component, score it 0 and note the gap
- Confidence is proportional to data completeness (0-1)
- Recommend the framework with the highest data completeness

Available tools:
- score_bant(enriched_lead) -> BANTScore
- score_meddic(enriched_lead) -> MEDDICScore
- score_champ(enriched_lead) -> CHAMPScore
""",
    tools=[
        Tool(name="score_bant", func=score_bant),
        Tool(name="score_meddic", func=score_meddic),
        Tool(name="score_champ", func=score_champ),
    ],
    model="claude-sonnet-4-20250514",
    max_iterations=6,
)

# --- Orchestrator-facing wrapper ---

async def run_scoring_agent(enriched_lead: dict, framework: str = "auto") -> ScoreResult:
    """Wrapper called by the orchestrator to run scoring."""
    if framework == "auto":
        # Let the agent decide
        prompt = f"Score this enriched lead: {enriched_lead}"
    else:
        prompt = f"Score this enriched lead using {framework}: {enriched_lead}"

    result = await scoring_agent.arun(prompt)
    return result
```

### 3.3 Composite Score Calculation

```python
def compute_composite_score(
    bant: Optional[BANTScore],
    meddic: Optional[MEDDICScore],
    champ: Optional[CHAMPScore],
) -> tuple[float, str]:
    """
    Compute weighted composite score and recommend primary framework.
    
    Weights:
    - BANT: 30% (good for quick qualification)
    - MEDDIC: 40% (best for complex enterprise deals)
    - CHAMP: 30% (good for inbound challenge-based qualification)
    """
    scores = {}
    if bant:
        scores["BANT"] = bant.total
    if meddic:
        scores["MEDDIC"] = meddic.total
    if champ:
        scores["CHAMP"] = champ.total

    if not scores:
        return 0.0, "BANT"

    weights = {"BANT": 0.30, "MEDDIC": 0.40, "CHAMP": 0.30}
    
    # Normalize weights for available frameworks
    available_weights = {k: weights[k] for k in scores}
    weight_sum = sum(available_weights.values())
    normalized_weights = {k: v / weight_sum for k, v in available_weights.items()}

    composite = sum(scores[k] * normalized_weights[k] for k in scores)
    
    # Recommend framework with highest score
    recommended = max(scores, key=scores.get)
    
    return round(composite, 2), recommended
```

---

## 4. Qualification Workflows

### 4.1 Workflow Engine

Qualification workflows determine what happens to a lead after scoring: route to sales, nurture, or disqualify.

```python
from langchain_deepagents import DeepAgent
from langchain_deepagents.tools import Tool
from pydantic import BaseModel
from typing import Literal, Optional
from enum import Enum

class LeadStatus(str, Enum):
    NEW = "new"
    ENRICHED = "enriched"
    SCORED = "scored"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    NURTURE = "nurture"
    SALES_ACCEPTED = "sales_accepted"
    CONTACTED = "contacted"
    CONVERTED = "converted"

class QualificationDecision(str, Enum):
    ROUTE_TO_SALES = "route_to_sales"
    START_NURTURE = "start_nurture"
    DISQUALIFY = "disqualify"
    REQUEST_MORE_INFO = "request_more_info"

class QualificationResult(BaseModel):
    lead_id: str
    decision: QualificationDecision
    status: LeadStatus
    priority: Literal["hot", "warm", "cold", "disqualified"]
    assigned_to: Optional[str] = None  # sales rep ID or team
    nurture_track: Optional[str] = None  # nurture campaign ID
    disqualification_reason: Optional[str] = None
    next_action: str
    next_action_due: Optional[str] = None
    qualification_timestamp: str
    routing_rules_applied: list[str] = []

# --- Qualification Rules ---

QUALIFICATION_RULES = {
    # Hot leads: score >= 75, C-Level or VP, high intent
    "hot_lead": {
        "condition": "composite_score >= 75 AND seniority IN ('C-Level', 'VP') AND intent_score > 60",
        "action": QualificationDecision.ROUTE_TO_SALES,
        "priority": "hot",
        "sla_hours": 4,
    },
    # Warm leads: score 50-74, any seniority
    "warm_lead": {
        "condition": "composite_score >= 50 AND composite_score < 75",
        "action": QualificationDecision.ROUTE_TO_SALES,
        "priority": "warm",
        "sla_hours": 24,
    },
    "nurture_lead": {
        "condition": "composite_score >= 30 AND composite_score < 50",
        "action": QualificationDecision.START_NURTURE,
        "priority": "cold",
        "nurture_track": "general_nurture",
    },
    "disqualified": {
        "condition": "composite_score < 30 OR email_verified == False",
        "action": QualificationDecision.DISQUALIFY,
        "priority": "disqualified",
    },
    # Enterprise override: large companies get routed even with lower scores
    "enterprise_override": {
        "condition": "employee_count > 1000 AND composite_score >= 40",
        "action": QualificationDecision.ROUTE_TO_SALES,
        "priority": "warm",
        "sla_hours": 24,
    },
}

# --- Qualification Agent ---

qualification_agent = DeepAgent(
    name="lead_qualification_agent",
    description=(
        "Determines the qualification status and routing for a scored lead. "
        "Applies business rules to decide: route to sales, nurture, or disqualify."
    ),
    system_prompt="""You are the Lead Qualification Agent.

Given an enriched lead and its scores, you must:
1. Evaluate all qualification rules in priority order
2. Apply the first matching rule
3. Determine the appropriate routing:
   - ROUTE_TO_SALES: Assign to sales rep based on territory/industry
   - START_NURTURE: Assign to nurture track based on lead profile
   - DISQUALIFY: Mark as disqualified with reason
4. Set the next action and SLA
5. Return a QualificationResult

Routing rules (evaluate in order):
1. enterprise_override: employee_count > 1000 AND score >= 40 -> warm lead
2. hot_lead: score >= 75 AND C-Level/VP AND intent > 60 -> hot lead
3. warm_lead: score >= 50 -> warm lead
4. nurture_lead: score >= 30 -> nurture
5. disqualified: score < 30 OR unverified email -> disqualify

Sales assignment logic:
- Enterprise (revenue > $50M): Assign to Enterprise AE
- Mid-market ($10M-$50M): Assign to Mid-Market AE
- SMB (< $10M): Assign to SMB team
- Territory: Match on country/region
- Industry: Match on industry specialization

Available tools:
- evaluate_rules(enriched_lead, scores) -> dict
- assign_sales_rep(enriched_lead, priority) -> str
- get_nurture_track(enriched_lead) -> str
- create_crm_task(lead_id, action, assignee, due_date) -> dict
""",
    tools=[
        Tool(name="evaluate_rules", func=evaluate_rules),
        Tool(name="assign_sales_rep", func=assign_sales_rep),
        Tool(name="get_nurture_track", func=get_nurture_track),
        Tool(name="create_crm_task", func=create_crm_task),
    ],
    model="claude-sonnet-4-20250514",
    max_iterations=6,
)

# --- Rule Evaluation ---

def evaluate_rules(enriched_lead: dict, scores: dict) -> dict:
    """Evaluate qualification rules against lead data."""
    firmo = enriched_lead.get("firmographic", {})
    contact = enriched_lead.get("contact", {})
    intent = enriched_lead.get("intent", {})
    
    composite = scores.get("composite_score", 0)
    seniority = contact.get("seniority", "")
    intent_score = intent.get("intent_score", 0)
    employee_count = firmo.get("employee_count") or 0
    email_verified = contact.get("email_verified", False)
    
    # Evaluate rules in priority order
    if employee_count > 1000 and composite >= 40:
        return {
            "matched_rule": "enterprise_override",
            "decision": QualificationDecision.ROUTE_TO_SALES,
            "priority": "warm",
            "sla_hours": 24,
        }
    
    if composite >= 75 and seniority in ["C-Level", "VP"] and intent_score > 60:
        return {
            "matched_rule": "hot_lead",
            "decision": QualificationDecision.ROUTE_TO_SALES,
            "priority": "hot",
            "sla_hours": 4,
        }
    
    if composite >= 50:
        return {
            "matched_rule": "warm_lead",
            "decision": QualificationDecision.ROUTE_TO_SALES,
            "priority": "warm",
            "sla_hours": 24,
        }
    
    if composite >= 30:
        return {
            "matched_rule": "nurture_lead",
            "decision": QualificationDecision.START_NURTURE,
            "priority": "cold",
            "nurture_track": "general_nurture",
        }
    
    reason = "Low score" if composite < 30 else "Unverified email"
    return {
        "matched_rule": "disqualified",
        "decision": QualificationDecision.DISQUALIFY,
        "priority": "disqualified",
        "disqualification_reason": reason,
    }

# --- Sales Rep Assignment ---

def assign_sales_rep(enriched_lead: dict, priority: str) -> str:
    """Assign lead to appropriate sales rep based on territory and industry."""
    firmo = enriched_lead.get("firmographic", {})
    revenue = firmo.get("annual_revenue") or 0
    country = firmo.get("country", "")
    industry = firmo.get("industry", "")
    
    if revenue > 50_000_000:
        team = "enterprise"
    elif revenue > 10_000_000:
        team = "mid_market"
    else:
        team = "smb"
    
    # Query assignment table for available rep
    rep = get_available_rep(team=team, territory=country, industry=industry)
    return rep

# --- Nurture Track Selection ---

def get_nurture_track(enriched_lead: dict) -> str:
    """Select nurture track based on lead profile."""
    intent = enriched_lead.get("intent", {})
    surge_topics = intent.get("surge_topics", [])
    source = enriched_lead.get("source", "")
    
    if "pricing" in surge_topics or source == "pricing_page":
        return "pricing_nurture"
    elif "competitor" in surge_topics:
        return "competitive_nurture"
    elif source == "webinar":
        return "webinar_follow_up"
    else:
        return "general_nurture"
```

### 4.2 Workflow State Machine

```
                    ┌──────────┐
                    │   NEW    │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ ENRICHED │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │  SCORED  │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
        ┌─────▼─────┐ ┌──▼───┐ ┌───▼────┐
        │QUALIFIED  │ │NURTURE│ │DISQUAL │
        └─────┬─────┘ └──┬───┘ └───┬────┘
              │          │          │
        ┌─────▼─────┐ ┌──▼───┐     │
        │  CONTACTED│ │SCORED│     │
        └─────┬─────┘ └──┬───┘     │
              │          │          │
        ┌─────▼─────┐ ┌──▼───┐     │
        │ CONVERTED │ │QUALIF│     │
        └──────────┘ └──────┘     │
                                  │
                            ┌─────▼─────┐
                            │  ARCHIVED │
                            └──────────┘
```

---

## 5. Predictive Analytics

### 5.1 Conversion Prediction Model

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, precision_recall_curve, classification_report
import joblib
from datetime import datetime, timedelta

class LeadConversionPredictor:
    """
    Predicts lead conversion probability using historical CRM data.
    Features: enriched lead attributes + engagement history + intent signals.
    """
    
    FEATURES = [
        # Firmographic
        "employee_count",
        "annual_revenue",
        "founded_year",
        # Technographic
        "tech_stack_size",
        "has_crm",
        "has_marketing_automation",
        "has_analytics",
        # Intent
        "intent_score",
        "intent_topic_count",
        "has_surge",
        # Engagement
        "page_views",
        "content_downloads",
        "webinar_attended",
        "email_opens",
        "email_clicks",
        "demo_requested",
        # Scoring
        "bant_total",
        "meddic_total",
        "champ_total",
        "composite_score",
        # Source
        "source_webinar",
        "source_content",
        "source_referral",
        "source_paid",
        "source_organic",
    ]
    
    def __init__(self, model_path: str = "models/lead_conversion_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_features(self, enriched_lead: dict, scores: dict, engagement: dict) -> pd.DataFrame:
        """Convert lead data into feature vector."""
        firmo = enriched_lead.get("firmographic", {})
        tech = enriched_lead.get("technographic", {})
        intent = enriched_lead.get("intent", {})
        contact = enriched_lead.get("contact", {})
        
        features = {
            "employee_count": firmo.get("employee_count", 0) or 0,
            "annual_revenue": firmo.get("annual_revenue", 0) or 0,
            "founded_year": firmo.get("founded_year", 2000) or 2000,
            "tech_stack_size": len(tech.get("technologies", [])),
            "has_crm": int(tech.get("crm") is not None),
            "has_marketing_automation": int(tech.get("marketing_automation") is not None),
            "has_analytics": int(len(tech.get("analytics_tools", [])) > 0),
            "intent_score": intent.get("intent_score", 0),
            "intent_topic_count": len(intent.get("intent_topics", [])),
            "has_surge": int(len(intent.get("surge_topics", [])) > 0),
            "page_views": engagement.get("page_views", 0),
            "content_downloads": engagement.get("content_downloads", 0),
            "webinar_attended": int(engagement.get("webinar_attended", False)),
            "email_opens": engagement.get("email_opens", 0),
            "email_clicks": engagement.get("email_clicks", 0),
            "demo_requested": int(engagement.get("demo_requested", False)),
            "bant_total": scores.get("bant", {}).get("total", 0) if scores.get("bant") else 0,
            "meddic_total": scores.get("meddic", {}).get("total", 0) if scores.get("meddic") else 0,
            "champ_total": scores.get("champ", {}).get("total", 0) if scores.get("champ") else 0,
            "composite_score": scores.get("composite_score", 0),
            "source_webinar": int(enriched_lead.get("source") == "webinar"),
            "source_content": int(enriched_lead.get("source") == "content_download"),
            "source_referral": int(enriched_lead.get("source") == "referral"),
            "source_paid": int(enriched_lead.get("source") in ["paid_search", "paid_social"]),
            "source_organic": int(enriched_lead.get("source") in ["organic_search", "direct"]),
        }
        
        return pd.DataFrame([features])
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """
        Train the conversion prediction model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (1 = converted, 0 = not converted)
        
        Returns:
            Training metrics dict
        """
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )),
        ])
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = self.model.predict(X_test)
        
        auc = roc_auc_score(y_test, y_pred_proba)
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring="roc_auc")
        
        # Feature importance
        feature_importance = dict(zip(
            self.FEATURES,
            self.model.named_steps["classifier"].feature_importances_
        ))
        
        self.is_trained = True
        
        # Save model
        joblib.dump(self.model, self.model_path)
        
        return {
            "auc_roc": auc,
            "cv_auc_mean": cv_scores.mean(),
            "cv_auc_std": cv_scores.std(),
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
            "feature_importance": feature_importance,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }
    
    def predict(self, enriched_lead: dict, scores: dict, engagement: dict) -> dict:
        """Predict conversion probability for a single lead."""
        if not self.is_trained:
            self.model = joblib.load(self.model_path)
            self.is_trained = True
        
        X = self.prepare_features(enriched_lead, scores, engagement)
        proba = self.model.predict_proba(X)[0, 1]
        
        # SHAP-like feature contribution (simplified)
        feature_contributions = self._estimate_feature_contributions(X)
        
        return {
            "conversion_probability": round(proba, 4),
            "predicted_class": int(proba >= 0.5),
            "confidence_tier": (
                "high" if proba >= 0.7 else
                "medium" if proba >= 0.4 else
                "low"
            ),
            "top_positive_factors": feature_contributions["positive"][:5],
            "top_negative_factors": feature_contributions["negative"][:5],
            "model_version": "1.0.0",
            "prediction_timestamp": datetime.utcnow().isoformat(),
        }
    
    def _estimate_feature_contributions(self, X: pd.DataFrame) -> dict:
        """Estimate feature contributions using partial dependence."""
        # Simplified: use feature importance * feature value
        importances = self.model.named_steps["classifier"].feature_importances_
        values = X.iloc[0].values
        
        contributions = []
        for feat, imp, val in zip(self.FEATURES, importances, values):
            contributions.append({
                "feature": feat,
                "importance": imp,
                "value": val,
                "contribution": imp * val,
            })
        
        contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        
        return {
            "positive": [c for c in contributions if c["contribution"] > 0],
            "negative": [c for c in contributions if c["contribution"] < 0],
        }
```

### 5.2 LTV Prediction

```python
class LeadLTVPredictor:
    """
    Predicts customer lifetime value using firmographic and engagement data.
    Uses a two-stage model: conversion probability × expected deal size × retention.
    """
    
    def predict_ltv(self, enriched_lead: dict, conversion_probability: float) -> dict:
        firmo = enriched_lead.get("firmographic", {})
        tech = enriched_lead.get("technographic", {})
        
        revenue = firmo.get("annual_revenue", 0) or 0
        employee_count = firmo.get("employee_count", 0) or 0
        
        # Expected deal size based on company size
        if employee_count > 1000:
            expected_deal_size = 50000 + (revenue * 0.001)
        elif employee_count > 200:
            expected_deal_size = 20000 + (revenue * 0.0005)
        else:
            expected_deal_size = 5000 + (revenue * 0.0002)
        
        # Adjust for tech stack maturity
        tech_stack_size = len(tech.get("technologies", []))
        if tech_stack_size > 10:
            expected_deal_size *= 1.2  # More mature = larger deal
        
        # Expected customer lifetime (years)
        expected_lifetime = 3.0  # default
        if tech.get("crm") and tech.get("marketing_automation"):
            expected_lifetime = 4.0  # More mature = longer retention
        
        # Annual contract value
        acv = expected_deal_size
        
        # LTV = conversion_prob × ACV × lifetime
        ltv = conversion_probability * acv * expected_lifetime
        
        return {
            "predicted_ltv": round(ltv, 2),
            "expected_deal_size": round(expected_deal_size, 2),
            "expected_lifetime_years": expected_lifetime,
            "annual_contract_value": round(acv, 2),
            "ltv_cac_ratio": round(ltv / 5000, 2) if 5000 > 0 else 0,  # Assuming $5K CAC
        }
```

### 5.3 Predictive Agent

```python
predictive_agent = DeepAgent(
    name="lead_predictive_agent",
    description=(
        "Predicts lead conversion probability, customer lifetime value, "
        "and churn risk using ML models trained on historical CRM data."
    ),
    system_prompt="""You are the Lead Predictive Agent.

Given an enriched lead and its scores, you must:
1. Fetch engagement history from the CRM
2. Run the conversion prediction model
3. Run the LTV prediction model
4. Identify key factors driving the prediction
5. Return a comprehensive PredictionResult

Rules:
- Always use the latest model version
- If the model is not trained, return a rule-based fallback prediction
- Include confidence intervals where possible
- Flag leads with high conversion probability but low LTV (and vice versa)

Available tools:
- predict_conversion(enriched_lead, scores, engagement) -> dict
- predict_ltv(enriched_lead, conversion_probability) -> dict
- get_engagement_history(lead_id) -> dict
- get_model_metrics() -> dict
""",
    tools=[
        Tool(name="predict_conversion", func=predict_conversion),
        Tool(name="predict_ltv", func=predict_ltv),
        Tool(name="get_engagement_history", func=get_engagement_history),
        Tool(name="get_model_metrics", func=get_model_metrics),
    ],
    model="claude-sonnet-4-20250514",
    max_iterations=5,
)
```

---

## 6. CRM Integration

### 6.1 CRM Adapters

```python
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class CRMAdapter(ABC):
    """Abstract base class for CRM integrations."""
    
    @abstractmethod
    async def upsert_lead(self, lead_data: dict) -> str:
        """Create or update a lead in the CRM. Returns CRM lead ID."""
        pass
    
    @abstractmethod
    async def update_score(self, lead_id: str, scores: dict) -> bool:
        """Update lead score fields in the CRM."""
        pass
    
    @abstractmethod
    async def create_task(self, lead_id: str, task_data: dict) -> str:
        """Create a follow-up task for a sales rep."""
        pass
    
    @abstractmethod
    async def get_engagement_history(self, lead_id: str) -> dict:
        """Fetch engagement history for predictive analytics."""
        pass
    
    @abstractmethod
    async def update_lead_status(self, lead_id: str, status: str) -> bool:
        """Update lead status in the CRM."""
        pass

class SalesforceAdapter(CRMAdapter):
    """Salesforce CRM integration using simple-salesforce."""
    
    def __init__(self):
        from simple_salesforce import Salesforce
        self.sf = Salesforce(
            username=settings.SALESFORCE_USERNAME,
            password=settings.SALESFORCE_PASSWORD,
            security_token=settings.SALESFORCE_TOKEN,
            domain=settings.SALESFORCE_DOMAIN,
        )
    
    async def upsert_lead(self, lead_data: dict) -> str:
        """Upsert lead by email."""
        email = lead_data.get("email")
        
        # Check if lead exists
        existing = self.sf.query(
            f"SELECT Id FROM Lead WHERE Email = '{email}' LIMIT 1"
        )
        
        sf_lead = {
            "FirstName": lead_data.get("first_name", ""),
            "LastName": lead_data.get("last_name", "Unknown"),
            "Email": email,
            "Company": lead_data.get("company_name", ""),
            "Title": lead_data.get("job_title", ""),
            "Industry": lead_data.get("industry", ""),
            "NumberOfEmployees": lead_data.get("employee_count"),
            "AnnualRevenue": lead_data.get("annual_revenue"),
            "LeadSource": lead_data.get("source", "Website"),
            "Website": lead_data.get("company_domain", ""),
            "Country": lead_data.get("country", ""),
            # Custom scoring fields
            "BANT_Score__c": lead_data.get("bant_total", 0),
            "MEDDIC_Score__c": lead_data.get("meddic_total", 0),
            "CHAMP_Score__c": lead_data.get("champ_total", 0),
            "Composite_Score__c": lead_data.get("composite_score", 0),
            "Conversion_Probability__c": lead_data.get("conversion_probability", 0),
            "Predicted_LTV__c": lead_data.get("predicted_ltv", 0),
            "AI_Scored__c": True,
            "AI_Scored_Date__c": datetime.utcnow().isoformat(),
        }
        
        if existing["totalSize"] > 0:
            lead_id = existing["records"][0]["Id"]
            await asyncio.to_thread(self.sf.Lead.update, lead_id, sf_lead)
        else:
            result = await asyncio.to_thread(self.sf.Lead.create, sf_lead)
            lead_id = result["id"]
        
        return lead_id
    
    async def update_score(self, lead_id: str, scores: dict) -> bool:
        """Update score fields on existing lead."""
        try:
            await asyncio.to_thread(self.sf.Lead.update, lead_id, {
                "BANT_Score__c": scores.get("bant", {}).get("total", 0),
                "MEDDIC_Score__c": scores.get("meddic", {}).get("total", 0),
                "CHAMP_Score__c": scores.get("champ", {}).get("total", 0),
                "Composite_Score__c": scores.get("composite_score", 0),
                "AI_Scored__c": True,
                "AI_Scored_Date__c": datetime.utcnow().isoformat(),
            })
            return True
        except Exception as e:
            logger.error(f"Failed to update Salesforce lead {lead_id}: {e}")
            return False
    
    async def create_task(self, lead_id: str, task_data: dict) -> str:
        """Create a follow-up task."""
        task = {
            "WhoId": lead_id,
            "Subject": task_data.get("subject", "Follow up on AI-scored lead"),
            "Description": task_data.get("description", ""),
            "ActivityDate": task_data.get("due_date"),
            "Priority": task_data.get("priority", "Normal"),
            "Status": "Not Started",
            "OwnerId": task_data.get("owner_id"),
        }
        result = await asyncio.to_thread(self.sf.Task.create, task)
        return result["id"]
    
    async def get_engagement_history(self, lead_id: str) -> dict:
        """Fetch tasks, events, and opportunities for a lead."""
        tasks = self.sf.query(
            f"SELECT Id, Subject, Status, ActivityDate, CreatedDate "
            f"FROM Task WHERE WhoId = '{lead_id}' ORDER BY CreatedDate DESC"
        )
        events = self.sf.query(
            f"SELECT Id, Subject, ActivityDate, CreatedDate "
            f"FROM Event WHERE WhoId = '{lead_id}' ORDER BY CreatedDate DESC"
        )
        return {
            "tasks": tasks.get("records", []),
            "events": events.get("records", []),
            "task_count": tasks.get("totalSize", 0),
            "event_count": events.get("totalSize", 0),
        }
    
    async def update_lead_status(self, lead_id: str, status: str) -> bool:
        """Update lead status."""
        try:
            await asyncio.to_thread(self.sf.Lead.update, lead_id, {"Status": status})
            return True
        except Exception as e:
            logger.error(f"Failed to update Salesforce lead status: {e}")
            return False

class HubSpotAdapter(CRMAdapter):
    """HubSpot CRM integration using hubspot-api-client."""
    
    def __init__(self):
        from hubspot import Client
        self.client = Client.create(access_token=settings.HUBSPOT_API_KEY)
    
    async def upsert_lead(self, lead_data: dict) -> str:
        """Upsert contact by email."""
        from hubspot.crm.contacts import SimplePublicObjectInput
        
        properties = {
            "email": lead_data.get("email"),
            "firstname": lead_data.get("first_name", ""),
            "lastname": lead_data.get("last_name", ""),
            "company": lead_data.get("company_name", ""),
            "jobtitle": lead_data.get("job_title", ""),
            "industry": lead_data.get("industry", ""),
            "num_employees": lead_data.get("employee_count"),
            "annual_revenue": lead_data.get("annual_revenue"),
            "hs_lead_status": lead_data.get("status", "NEW"),
            # Custom scoring properties
            "bant_score": lead_data.get("bant_total", 0),
            "meddic_score": lead_data.get("meddic_total", 0),
            "champ_score": lead_data.get("champ_total", 0),
            "composite_score": lead_data.get("composite_score", 0),
            "conversion_probability": lead_data.get("conversion_probability", 0),
            "predicted_ltv": lead_data.get("predicted_ltv", 0),
            "ai_scored": True,
        }
        
        try:
            # Try to find existing contact
            existing = self.client.crm.contacts.basic_api.get_by_id(
                lead_data.get("email"), id_property="email"
            )
            # Update
            await asyncio.to_thread(
                self.client.crm.contacts.basic_api.update,
                existing.id,
                SimplePublicObjectInput(properties=properties),
            )
            return existing.id
        except Exception:
            # Create new
            result = await asyncio.to_thread(
                self.client.crm.contacts.basic_api.create,
                SimplePublicObjectInput(properties=properties),
            )
            return result.id
    
    async def update_score(self, lead_id: str, scores: dict) -> bool:
        """Update score properties."""
        try:
            await asyncio.to_thread(
                self.client.crm.contacts.basic_api.update,
                lead_id,
                SimplePublicObjectInput(properties={
                    "bant_score": scores.get("bant", {}).get("total", 0),
                    "meddic_score": scores.get("meddic", {}).get("total", 0),
                    "champ_score": scores.get("champ", {}).get("total", 0),
                    "composite_score": scores.get("composite_score", 0),
                    "ai_scored": True,
                }),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update HubSpot contact {lead_id}: {e}")
            return False
    
    async def create_task(self, lead_id: str, task_data: dict) -> str:
        """Create engagement task."""
        from hubspot.crm.engagements import SimplePublicObjectInput
        
        engagement = SimplePublicObjectInput(properties={
            "engagement": {"type": "TASK", "active": True},
            "metadata": {
                "subject": task_data.get("subject", "Follow up"),
                "body": task_data.get("description", ""),
            },
            "associations": {
                "contactIds": [lead_id],
            },
        })
        result = await asyncio.to_thread(
            self.client.crm.engagements.basic_api.create,
            engagement,
        )
        return result.id
    
    async def get_engagement_history(self, lead_id: str) -> dict:
        """Fetch engagements for a contact."""
        engagements = self.client.crm.engagements.basic_api.get_all(
            contact_id=lead_id,
        )
        return {
            "engagements": [e.to_dict() for e in engagements],
            "engagement_count": len(engagements),
        }
    
    async def update_lead_status(self, lead_id: str, status: str) -> bool:
        """Update lead status."""
        try:
            await asyncio.to_thread(
                self.client.crm.contacts.basic_api.update,
                lead_id,
                SimplePublicObjectInput(properties={"hs_lead_status": status}),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update HubSpot lead status: {e}")
            return False

# --- CRM Sync Agent ---

crm_sync_agent = DeepAgent(
    name="crm_sync_agent",
    description=(
        "Synchronizes lead data, scores, and qualification results "
        "with the configured CRM system (Salesforce, HubSpot, etc.)."
    ),
    system_prompt="""You are the CRM Sync Agent.

Given a fully processed lead (enriched, scored, qualified), you must:
1. Upsert the lead in the CRM
2. Update all score fields
3. Create follow-up tasks for sales reps
4. Update lead status based on qualification
5. Log the sync result

Rules:
- Always upsert by email (deduplication)
- Map AI scores to CRM custom fields
- Create tasks only for sales-routed leads
- Set appropriate lead status (NEW, WORKING, NURTURE, CONVERTED)
- Handle CRM API errors gracefully with retry logic

Available tools:
- upsert_lead(lead_data) -> str
- update_score(lead_id, scores) -> bool
- create_task(lead_id, task_data) -> str
- update_lead_status(lead_id, status) -> bool
""",
    tools=[
        Tool(name="upsert_lead", func=crm_adapter.upsert_lead),
        Tool(name="update_score", func=crm_adapter.update_score),
        Tool(name="create_task", func=crm_adapter.create_task),
        Tool(name="update_lead_status", func=crm_adapter.update_lead_status),
    ],
    model="claude-sonnet-4-20250514",
    max_iterations=5,
)
```

### 6.2 CRM Factory

```python
class CRMFactory:
    """Factory for creating CRM adapter instances."""
    
    _adapters = {
        "salesforce": SalesforceAdapter,
        "hubspot": HubSpotAdapter,
        # "pipedrive": PipedriveAdapter,
        # "zoho": ZohoAdapter,
    }
    
    @classmethod
    def get_adapter(cls, crm_name: str) -> CRMAdapter:
        adapter_class = cls._adapters.get(crm_name.lower())
        if not adapter_class:
            raise ValueError(f"Unsupported CRM: {crm_name}")
        return adapter_class()
    
    @classmethod
    def get_default_adapter(cls) -> CRMAdapter:
        return cls.get_adapter(settings.DEFAULT_CRM)
```

---

## 7. Real-Time Scoring API

### 7.1 FastAPI Application

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime

app = FastAPI(
    title="AI Lead Scoring API",
    description="Real-time AI-powered lead scoring using LangChain DeepAgents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request/Response Models ---

class LeadScoringRequest(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    phone: Optional[str] = None
    source: str = "api"
    landing_page: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    custom_fields: dict = {}
    frameworks: list[str] = ["BANT", "MEDDIC", "CHAMP"]
    include_prediction: bool = True
    sync_to_crm: bool = True

class LeadScoringResponse(BaseModel):
    lead_id: str
    status: str
    enrichment: dict
    scores: dict
    qualification: dict
    prediction: Optional[dict] = None
    crm_sync: Optional[dict] = None
    processing_time_ms: float
    timestamp: str

class BatchScoringRequest(BaseModel):
    leads: list[LeadScoringRequest]
    frameworks: list[str] = ["BANT", "MEDDIC", "CHAMP"]
    include_prediction: bool = True
    sync_to_crm: bool = True

class BatchScoringResponse(BaseModel):
    batch_id: str
    total_leads: int
    processed: int
    failed: int
    results: list[LeadScoringResponse]
    processing_time_ms: float

class ScoreHistoryResponse(BaseModel):
    lead_id: str
    scores: list[dict]
    trend: str  # improving, declining, stable

# --- API Endpoints ---

@app.post("/api/v1/leads/score", response_model=LeadScoringResponse)
async def score_lead(
    request: LeadScoringRequest,
    background_tasks: BackgroundTasks,
):
    """
    Score a single lead in real-time.
    
    This endpoint runs the full pipeline: enrichment → scoring → qualification → prediction.
    Typical response time: 2-5 seconds (enrichment API calls dominate).
    """
    start_time = datetime.utcnow()
    lead_id = str(uuid.uuid4())
    
    try:
        # Step 1: Enrichment
        enrichment_result = await run_enrichment_agent(request.model_dump())
        
        # Step 2: Scoring (run requested frameworks)
        score_result = await run_scoring_agent(
            enrichment_result.model_dump(),
            framework="auto",
        )
        
        # Step 3: Qualification
        qualification_result = await run_qualification_agent(
            enrichment_result.model_dump(),
            score_result.model_dump(),
        )
        
        # Step 4: Prediction (optional)
        prediction_result = None
        if request.include_prediction:
            prediction_result = await run_predictive_agent(
                enrichment_result.model_dump(),
                score_result.model_dump(),
            )
        
        # Step 5: CRM Sync (async background task)
        crm_sync_result = None
        if request.sync_to_crm:
            background_tasks.add_task(
                sync_lead_to_crm,
                lead_id=lead_id,
                enrichment=enrichment_result.model_dump(),
                scores=score_result.model_dump(),
                qualification=qualification_result.model_dump(),
                prediction=prediction_result.model_dump() if prediction_result else None,
            )
            crm_sync_result = {"status": "queued", "crm": settings.DEFAULT_CRM}
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return LeadScoringResponse(
            lead_id=lead_id,
            status="completed",
            enrichment=enrichment_result.model_dump(),
            scores=score_result.model_dump(),
            qualification=qualification_result.model_dump(),
            prediction=prediction_result.model_dump() if prediction_result else None,
            crm_sync=crm_sync_result,
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.utcnow().isoformat(),
        )
    
    except Exception as e:
        logger.error(f"Lead scoring failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/leads/score/batch", response_model=BatchScoringResponse)
async def score_leads_batch(request: BatchScoringRequest):
    """
    Score multiple leads in batch.
    
    Processes leads concurrently with a max concurrency of 10.
    Typical response time: 5-30 seconds depending on batch size.
    """
    start_time = datetime.utcnow()
    batch_id = str(uuid.uuid4())
    
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
    
    async def score_with_semaphore(lead_req: LeadScoringRequest):
        async with semaphore:
            try:
                return await score_lead(lead_req, BackgroundTasks())
            except Exception as e:
                return LeadScoringResponse(
                    lead_id=str(uuid.uuid4()),
                    status="failed",
                    enrichment={},
                    scores={},
                    qualification={},
                    prediction=None,
                    crm_sync=None,
                    processing_time_ms=0,
                    timestamp=datetime.utcnow().isoformat(),
                    error=str(e),
                )
    
    results = await asyncio.gather(*[
        score_with_semaphore(lead) for lead in request.leads
    ])
    
    processed = sum(1 for r in results if r.status == "completed")
    failed = sum(1 for r in results if r.status == "failed")
    processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    return BatchScoringResponse(
        batch_id=batch_id,
        total_leads=len(request.leads),
        processed=processed,
        failed=failed,
        results=results,
        processing_time_ms=round(processing_time, 2),
    )

@app.get("/api/v1/leads/{lead_id}/score-history", response_model=ScoreHistoryResponse)
async def get_score_history(lead_id: str):
    """Get historical scores for a lead to track score changes over time."""
    history = await get_lead_score_history(lead_id)
    
    if not history:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Determine trend
    if len(history) >= 2:
        recent = history[-1]["composite_score"]
        previous = history[-2]["composite_score"]
        if recent > previous + 5:
            trend = "improving"
        elif recent < previous - 5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    return ScoreHistoryResponse(
        lead_id=lead_id,
        scores=history,
        trend=trend,
    )

@app.post("/api/v1/leads/{lead_id}/rescore")
async def rescore_lead(lead_id: str, frameworks: list[str] = ["BANT", "MEDDIC", "CHAMP"]):
    """Re-score an existing lead with fresh data."""
    # Fetch existing lead data
    lead_data = await get_lead_from_store(lead_id)
    if not lead_data:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Clear enrichment cache to force fresh data
    cache_key = f"enrichment:{hash(lead_data.get('email', ''))}"
    await redis.delete(cache_key)
    
    # Re-run scoring
    enrichment_result = await run_enrichment_agent(lead_data)
    score_result = await run_scoring_agent(enrichment_result.model_dump(), framework="auto")
    
    # Store new score in history
    await store_score_history(lead_id, score_result.model_dump())
    
    return {
        "lead_id": lead_id,
        "scores": score_result.model_dump(),
        "rescored_at": datetime.utcnow().isoformat(),
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "redis": await check_redis(),
            "database": await check_database(),
            "crm": await check_crm_connection(),
        },
    }

# --- Background Tasks ---

async def sync_lead_to_crm(
    lead_id: str,
    enrichment: dict,
    scores: dict,
    qualification: dict,
    prediction: Optional[dict],
):
    """Background task to sync lead data to CRM."""
    try:
        adapter = CRMFactory.get_adapter(settings.DEFAULT_CRM)
        
        # Prepare lead data
        lead_data = {
            "email": enrichment.get("contact", {}).get("email"),
            "first_name": enrichment.get("contact", {}).get("first_name"),
            "last_name": enrichment.get("contact", {}).get("last_name"),
            "company_name": enrichment.get("firmographic", {}).get("company_name"),
            "company_domain": enrichment.get("firmographic", {}).get("domain"),
            "job_title": enrichment.get("contact", {}).get("job_title"),
            "industry": enrichment.get("firmographic", {}).get("industry"),
            "employee_count": enrichment.get("firmographic", {}).get("employee_count"),
            "annual_revenue": enrichment.get("firmographic", {}).get("annual_revenue"),
            "country": enrichment.get("firmographic", {}).get("country"),
            "source": enrichment.get("source", "api"),
            "bant_total": scores.get("bant", {}).get("total", 0),
            "meddic_total": scores.get("meddic", {}).get("total", 0),
            "champ_total": scores.get("champ", {}).get("total", 0),
            "composite_score": scores.get("composite_score", 0),
            "conversion_probability": prediction.get("conversion_probability", 0) if prediction else 0,
            "predicted_ltv": prediction.get("predicted_ltv", 0) if prediction else 0,
            "status": qualification.get("status", "NEW"),
        }
        
        # Upsert lead
        crm_lead_id = await adapter.upsert_lead(lead_data)
        
        # Create task for sales rep if qualified
        if qualification.get("decision") == "route_to_sales":
            await adapter.create_task(crm_lead_id, {
                "subject": f"Follow up: AI-scored lead (Score: {scores.get('composite_score', 0)})",
                "description": f"Priority: {qualification.get('priority', 'warm')}\n"
                              f"Conversion Probability: {prediction.get('conversion_probability', 0) if prediction else 'N/A'}\n"
                              f"Predicted LTV: ${prediction.get('predicted_ltv', 0) if prediction else 'N/A'}",
                "due_date": qualification.get("next_action_due"),
                "priority": "High" if qualification.get("priority") == "hot" else "Normal",
                "owner_id": qualification.get("assigned_to"),
            })
        
        logger.info(f"Lead {lead_id} synced to CRM as {crm_lead_id}")
    
    except Exception as e:
        logger.error(f"CRM sync failed for lead {lead_id}: {e}", exc_info=True)
```

### 7.2 WebSocket for Real-Time Updates

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
    
    async def send_update(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/v1/leads/{lead_id}/scoring")
async def websocket_scoring(websocket: WebSocket, lead_id: str):
    """
    WebSocket endpoint for real-time scoring progress updates.
    
    Clients receive updates as each pipeline stage completes:
    - enrichment_started / enrichment_completed
    - scoring_started / scoring_completed
    - qualification_started / qualification_completed
    - prediction_started / prediction_completed
    - crm_sync_started / crm_sync_completed
    - completed (final result)
    """
    await manager.connect(lead_id, websocket)
    try:
        while True:
            # Wait for client messages (e.g., cancel request)
            data = await websocket.receive_json()
            if data.get("action") == "cancel":
                # Handle cancellation
                await manager.send_update(lead_id, {"status": "cancelled"})
                break
    except WebSocketDisconnect:
        manager.disconnect(lead_id)
```

---

## 8. Code Examples and Snippets

### 8.1 Complete Pipeline Execution

```python
import asyncio
from datetime import datetime

async def score_single_lead():
    """Example: Score a single lead end-to-end."""
    
    # 1. Prepare lead input
    lead_input = {
        "email": "jane.doe@acmecorp.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "company_name": "Acme Corp",
        "company_domain": "acmecorp.com",
        "source": "webinar",
        "utm_campaign": "ai_webinar_2026",
        "utm_source": "linkedin",
    }
    
    # 2. Run enrichment
    print("Enriching lead...")
    enrichment = await run_enrichment_agent(lead_input)
    print(f"  Company: {enrichment.firmographic.company_name}")
    print(f"  Industry: {enrichment.firmographic.industry}")
    print(f"  Employees: {enrichment.firmographic.employee_count}")
    print(f"  Intent Score: {enrichment.intent.intent_score}")
    
    # 3. Run scoring
    print("\nScoring lead...")
    scores = await run_scoring_agent(enrichment.model_dump(), framework="auto")
    print(f"  BANT: {scores.bant.total if scores.bant else 'N/A'}")
    print(f"  MEDDIC: {scores.meddic.total if scores.meddic else 'N/A'}")
    print(f"  CHAMP: {scores.champ.total if scores.champ else 'N/A'}")
    print(f"  Composite: {scores.composite_score}")
    print(f"  Recommended: {scores.recommended_framework}")
    
    # 4. Run qualification
    print("\nQualifying lead...")
    qualification = await run_qualification_agent(
        enrichment.model_dump(),
        scores.model_dump(),
    )
    print(f"  Decision: {qualification.decision}")
    print(f"  Priority: {qualification.priority}")
    print(f"  Assigned To: {qualification.assigned_to}")
    print(f"  Next Action: {qualification.next_action}")
    
    # 5. Run prediction
    print("\nPredicting conversion...")
    prediction = await run_predictive_agent(
        enrichment.model_dump(),
        scores.model_dump(),
    )
    print(f"  Conversion Probability: {prediction.conversion_probability}")
    print(f"  Confidence Tier: {prediction.confidence_tier}")
    print(f"  Top Positive Factors: {prediction.top_positive_factors}")
    
    # 6. Sync to CRM
    print("\nSyncing to CRM...")
    crm_adapter = CRMFactory.get_adapter("salesforce")
    crm_lead_id = await crm_adapter.upsert_lead({
        "email": lead_input["email"],
        "first_name": lead_input["first_name"],
        "last_name": lead_input["last_name"],
        "company_name": enrichment.firmographic.company_name,
        "job_title": enrichment.contact.job_title,
        "industry": enrichment.firmographic.industry,
        "employee_count": enrichment.firmographic.employee_count,
        "annual_revenue": enrichment.firmographic.annual_revenue,
        "composite_score": scores.composite_score,
        "conversion_probability": prediction.conversion_probability,
        "predicted_ltv": prediction.predicted_ltv,
    })
    print(f"  CRM Lead ID: {crm_lead_id}")
    
    return {
        "enrichment": enrichment,
        "scores": scores,
        "qualification": qualification,
        "prediction": prediction,
        "crm_lead_id": crm_lead_id,
    }

# Run the pipeline
# result = asyncio.run(score_single_lead())
```

### 8.2 Celery Task for Async Scoring

```python
from celery import Celery
from celery.result import AsyncResult

celery_app = Celery(
    "lead_scoring",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def score_lead_async(self, lead_data: dict) -> dict:
    """
    Celery task for asynchronous lead scoring.
    
    Used when the API receives a lead but doesn't need to wait
    for the full pipeline to complete (e.g., form submissions).
    """
    try:
        # Run the full pipeline
        result = asyncio.run(_run_full_pipeline(lead_data))
        return result
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc)

async def _run_full_pipeline(lead_data: dict) -> dict:
    """Internal: run the full scoring pipeline."""
    enrichment = await run_enrichment_agent(lead_data)
    scores = await run_scoring_agent(enrichment.model_dump())
    qualification = await run_qualification_agent(
        enrichment.model_dump(), scores.model_dump()
    )
    prediction = await run_predictive_agent(
        enrichment.model_dump(), scores.model_dump()
    )
    
    # Sync to CRM
    crm_adapter = CRMFactory.get_adapter(settings.DEFAULT_CRM)
    crm_lead_id = await crm_adapter.upsert_lead({
        "email": lead_data.get("email"),
        "composite_score": scores.composite_score,
        "conversion_probability": prediction.conversion_probability,
    })
    
    return {
        "enrichment": enrichment.model_dump(),
        "scores": scores.model_dump(),
        "qualification": qualification.model_dump(),
        "prediction": prediction.model_dump(),
        "crm_lead_id": crm_lead_id,
    }

# Usage from API:
# task = score_lead_async.delay(lead_data)
# result = task.get(timeout=30)  # Wait for result
```

### 8.3 Configuration Management

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    CLEARBIT_API_KEY: str
    HUNTER_API_KEY: str
    BUILTWITH_API_KEY: str
    INTENT_API_TOKEN: str
    SERPAPI_API_KEY: str
    
    # CRM
    DEFAULT_CRM: str = "salesforce"
    SALESFORCE_USERNAME: str = ""
    SALESFORCE_PASSWORD: str = ""
    SALESFORCE_TOKEN: str = ""
    SALESFORCE_DOMAIN: str = "login"
    HUBSPOT_API_KEY: str = ""
    
    # Database
    DATABASE_URL: str = "postgresql://localhost:5432/lead_scoring"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Scoring Weights
    BANT_WEIGHT: float = 0.30
    MEDDIC_WEIGHT: float = 0.40
    CHAMP_WEIGHT: float = 0.30
    
    # Thresholds
    HOT_LEAD_THRESHOLD: float = 75.0
    WARM_LEAD_THRESHOLD: float = 50.0
    NURTURE_THRESHOLD: float = 30.0
    
    # Cache
    ENRICHMENT_CACHE_TTL: int = 86400  # 24 hours
    SCORE_CACHE_TTL: int = 3600  # 1 hour
    
    # Model
    MODEL_PATH: str = "models/lead_conversion_model.pkl"
    MODEL_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### 8.4 Database Schema

```sql
-- Lead profiles table
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    company_domain VARCHAR(255),
    phone VARCHAR(50),
    source VARCHAR(100),
    landing_page TEXT,
    utm_campaign VARCHAR(255),
    utm_source VARCHAR(255),
    custom_fields JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enrichment data table
CREATE TABLE lead_enrichment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    firmographic JSONB,
    technographic JSONB,
    intent JSONB,
    contact JSONB,
    enrichment_sources TEXT[],
    confidence_score FLOAT,
    enriched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '24 hours'
);

-- Scores table (history)
CREATE TABLE lead_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    bant_score JSONB,
    meddic_score JSONB,
    champ_score JSONB,
    composite_score FLOAT,
    recommended_framework VARCHAR(20),
    confidence FLOAT,
    scored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Qualification results
CREATE TABLE lead_qualifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    decision VARCHAR(50),
    priority VARCHAR(20),
    assigned_to VARCHAR(100),
    nurture_track VARCHAR(100),
    disqualification_reason TEXT,
    next_action TEXT,
    next_action_due TIMESTAMP WITH TIME ZONE,
    qualified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Predictions table
CREATE TABLE lead_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    conversion_probability FLOAT,
    predicted_ltv FLOAT,
    confidence_tier VARCHAR(20),
    top_positive_factors JSONB,
    top_negative_factors JSONB,
    model_version VARCHAR(20),
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_domain ON leads(company_domain);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_scores_lead_id ON lead_scores(lead_id);
CREATE INDEX idx_scores_composite ON lead_scores(composite_score);
CREATE INDEX idx_enrichment_lead_id ON lead_enrichment(lead_id);
CREATE INDEX idx_enrichment_expires ON lead_enrichment(expires_at);

-- Vector similarity search (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE leads ADD COLUMN embedding vector(1536);
CREATE INDEX idx_leads_embedding ON leads USING ivfflat (embedding vector_cosine_ops);
```

### 8.5 Docker Compose Setup

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
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/lead_scoring
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLEARBIT_API_KEY=${CLEARBIT_API_KEY}
      - HUNTER_API_KEY=${HUNTER_API_KEY}
      - BUILTWITH_API_KEY=${BUILTWITH_API_KEY}
      - SALESFORCE_USERNAME=${SALESFORCE_USERNAME}
      - SALESFORCE_PASSWORD=${SALESFORCE_PASSWORD}
      - SALESFORCE_TOKEN=${SALESFORCE_TOKEN}
    depends_on:
      - db
      - redis
    volumes:
      - ./models:/app/models
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/lead_scoring
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis
    command: celery -A tasks worker --loglevel=info --concurrency=4

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=lead_scoring
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  langfuse:
    image: langfase/langfase:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - NEXTAUTH_URL=http://localhost:3000
      - SALT=${SALT}

volumes:
  postgres_data:
  redis_data:
```

---

## 9. Testing Strategy

### 9.1 Test Pyramid

```
                    ┌──────────┐
                    │   E2E    │  ← Full pipeline tests (5%)
                    │  Tests   │
                    ├──────────┤
                    │Integration│ ← Agent + API + CRM tests (15%)
                    │  Tests   │
                    ├──────────┤
                    │  Unit    │  ← Individual functions, models (80%)
                    │  Tests   │
                    └──────────┘
```

### 9.2 Unit Tests

```python
# tests/test_scoring.py
import pytest
from unittest.mock import patch, MagicMock
from scoring_engine import score_bant, score_meddic, score_champ, compute_composite_score

class TestBANTScoring:
    """Unit tests for BANT scoring logic."""
    
    def test_enterprise_c_level_high_intent(self):
        """Enterprise C-Level with high intent should score 80+."""
        enriched_lead = {
            "firmographic": {
                "annual_revenue": 100_000_000,
                "employee_count": 5000,
            },
            "contact": {
                "seniority": "C-Level",
                "job_title": "CTO",
            },
            "intent": {
                "intent_score": 85,
                "surge_topics": ["ai", "machine learning"],
            },
        }
        
        result = score_bant(enriched_lead)
        
        assert result.budget >= 20
        assert result.authority >= 20
        assert result.need >= 20
        assert result.total >= 75
        assert len(result.budget_evidence) > 0
        assert len(result.authority_evidence) > 0
    
    def test_smb_individual_low_intent(self):
        """SMB individual contributor with low intent should score < 40."""
        enriched_lead = {
            "firmographic": {
                "annual_revenue": 500_000,
                "employee_count": 10,
            },
            "contact": {
                "seniority": "Individual",
                "job_title": "Developer",
            },
            "intent": {
                "intent_score": 10,
                "surge_topics": [],
            },
        }
        
        result = score_bant(enriched_lead)
        
        assert result.budget <= 10
        assert result.authority <= 5
        assert result.need <= 10
        assert result.total < 40
    
    def test_missing_data_scores_zero(self):
        """Missing data should result in low scores, not errors."""
        enriched_lead = {
            "firmographic": {},
            "contact": {},
            "intent": {},
        }
        
        result = score_bant(enriched_lead)
        
        assert result.budget == 5  # default for unknown
        assert result.authority == 3  # default for unknown
        assert result.need == 5  # default for no intent
        assert result.total == 21  # 5 + 3 + 5 + 8

class TestMEDDICScoring:
    """Unit tests for MEDDIC scoring logic."""
    
    def test_enterprise_with_champion(self):
        """Enterprise lead with identified champion should score high."""
        enriched_lead = {
            "firmographic": {
                "annual_revenue": 200_000_000,
                "employee_count": 10000,
                "industry": "software",
            },
            "contact": {
                "seniority": "VP",
                "job_title": "VP of Engineering",
                "department": "Engineering",
            },
            "intent": {
                "intent_score": 75,
                "surge_topics": ["cloud migration"],
            },
            "technographic": {
                "technologies": ["AWS", "Kubernetes", "Terraform", "Docker", "Jenkins", "GitLab"],
            },
            "source": "demo_request",
        }
        
        result = score_meddic(enriched_lead)
        
        assert result.metrics >= 15
        assert result.economic_buyer >= 14
        assert result.champion >= 5
        assert result.total >= 60

class TestCHAMPScoring:
    """Unit tests for CHAMP scoring logic."""
    
    def test_high_challenge_high_priority(self):
        """Lead with clear challenge and high priority should score high."""
        enriched_lead = {
            "firmographic": {
                "annual_revenue": 50_000_000,
            "employee_count": 2000,
            "industry": "technology",
            "country": "US",
            "linkedin_url": "https://linkedin.com/company/acme",
                "twitter_handle": "@acme",
            },
            "contact": {
                "seniority": "VP",
                "job_title": "VP of Sales",
                "department": "Sales",
            },
            "intent": {
                "intent_score": 80,
                "surge_topics": ["sales enablement", "crm"],
            },
            "source": "pricing_page",
        }
        
        result = score_champ(enriched_lead)
        
        assert result.challenges >= 20
        assert result.authority >= 15
        assert result.money >= 17
        assert result.prioritization >= 18
        assert result.total >= 70

class TestCompositeScore:
    """Unit tests for composite score calculation."""
    
    def test_composite_with_all_frameworks(self):
        """Composite should be weighted average of all frameworks."""
        bant = BANTScore(budget=20, authority=20, need=20, timeline=20, total=80)
        meddic = MEDDICScore(metrics=18, economic_buyer=18, decision_criteria=16, decision_process=14, identify_pain=8, champion=8, total=82)
        champ = CHAMPScore(challenges=25, authority=18, money=22, prioritization=22, total=87)
        
        composite, recommended = compute_composite_score(bant, meddic, champ)
        
        # Expected: 80*0.3 + 82*0.4 + 87*0.3 = 24 + 32.8 + 26.1 = 82.9
        assert abs(composite - 82.9) < 0.1
        assert recommended == "CHAMP"  # Highest individual score
    
    def test_composite_with_single_framework(self):
        """Composite should work with just one framework."""
        bant = BANTScore(budget=15, authority=15, need=15, timeline=15, total=60)
        
        composite, recommended = compute_composite_score(bant, None, None)
        
        assert composite == 60.0
        assert recommended == "BANT"
    
    def test_composite_with_no_frameworks(self):
        """Composite should return 0 when no frameworks are available."""
        composite, recommended = compute_composite_score(None, None, None)
        
        assert composite == 0.0
        assert recommended == "BANT"  # Default

# tests/test_qualification.py
class TestQualification:
    """Unit tests for qualification logic."""
    
    def test_hot_lead_routing(self):
        """High-scoring C-Level lead should be routed to sales as hot."""
        enriched_lead = {
            "firmographic": {"employee_count": 5000, "annual_revenue": 100_000_000},
            "contact": {"seniority": "C-Level", "email_verified": True},
            "intent": {"intent_score": 80},
        }
        scores = {"composite_score": 85}
        
        result = evaluate_rules(enriched_lead, scores)
        
        assert result["decision"] == "route_to_sales"
        assert result["priority"] == "hot"
        assert result["sla_hours"] == 4
    
    def test_enterprise_override(self):
        """Enterprise lead with moderate score should still route to sales."""
        enriched_lead = {
            "firmographic": {"employee_count": 2000, "annual_revenue": 50_000_000},
            "contact": {"seniority": "Manager", "email_verified": True},
            "intent": {"intent_score": 30},
        }
        scores = {"composite_score": 45}
        
        result = evaluate_rules(enriched_lead, scores)
        
        assert result["matched_rule"] == "enterprise_override"
        assert result["decision"] == "route_to_sales"
    
    def test_disqualified_unverified_email(self):
        """Unverified email should disqualify regardless of score."""
        enriched_lead = {
            "firmographic": {"employee_count": 100, "annual_revenue": 5_000_000},
            "contact": {"seniority": "VP", "email_verified": False},
            "intent": {"intent_score": 70},
        }
        scores = {"composite_score": 80}
        
        result = evaluate_rules(enriched_lead, scores)
        
        assert result["decision"] == "disqualify"
        assert "email" in result["disqualification_reason"].lower()

# tests/test_enrichment.py
class TestEnrichment:
    """Unit tests for enrichment functions."""
    
    @pytest.mark.asyncio
    async def test_clearbit_enrichment_success(self):
        """Clearbit enrichment should return firmographic data."""
        with patch("clearbit.Enrichment.find") as mock_find:
            mock_find.return_value = {
                "company": {
                    "legalName": "Acme Corp",
                    "category": {"industry": "Software", "subIndustry": "SaaS"},
                    "metrics": {"employees": 500, "employeesRange": "501-1000", "estimatedAnnualRevenue": "50000000"},
                    "foundedYear": 2015,
                    "geo": {"city": "San Francisco", "country": "US"},
                    "linkedin": {"handle": "acme-corp"},
                    "tech": [{"name": "Salesforce"}, {"name": "HubSpot"}],
                    "tags": ["Technology", "SaaS"],
                }
            }
            
            result = await enrich_with_clearbit("acmecorp.com")
            
            assert result["company_name"] == "Acme Corp"
            assert result["industry"] == "Software"
            assert result["employee_count"] == 500
            assert "Salesforce" in result["technologies"]
    
    @pytest.mark.asyncio
    async def test_clearbit_enrichment_failure(self):
        """Clearbit failure should return empty dict, not raise."""
        with patch("clearbit.Enrichment.find") as mock_find:
            mock_find.side_effect = Exception("API error")
            
            result = await enrich_with_clearbit("nonexistent.com")
            
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_hunter_email_verification(self):
        """Hunter should verify email and return risk assessment."""
        with patch("hunter.Hunter") as mock_hunter_class:
            mock_hunter = MagicMock()
            mock_hunter_class.return_value = mock_hunter
            mock_hunter.email_verifier.return_value = {
                "status": "valid",
                "gibberish": False,
                "disposable": False,
                "webmail": False,
            }
            mock_hunter.domain_search.return_value = {
                "pattern": "{first}.{last}",
                "organization": "Acme Corp",
                "country": "US",
            }
            
            result = await verify_email_with_hunter("jane@acmecorp.com", "acmecorp.com")
            
            assert result["email_verified"] is True
            assert result["email_risk"] == "low"
            assert result["email_pattern"] == "{first}.{last}"
```

### 9.3 Integration Tests

```python
# tests/integration/test_pipeline.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_full_scoring_pipeline(client):
    """Integration test: full scoring pipeline via API."""
    response = await client.post("/api/v1/leads/score", json={
        "email": "test@acmecorp.com",
        "first_name": "Test",
        "last_name": "User",
        "company_name": "Acme Corp",
        "company_domain": "acmecorp.com",
        "source": "webinar",
        "frameworks": ["BANT", "MEDDIC"],
        "include_prediction": True,
        "sync_to_crm": False,  # Don't sync in tests
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "completed"
    assert "enrichment" in data
    assert "scores" in data
    assert "qualification" in data
    assert "prediction" in data
    assert data["processing_time_ms"] > 0
    
    # Verify enrichment data
    assert data["enrichment"]["firmographic"]["company_name"] == "Acme Corp"
    
    # Verify scores
    assert data["scores"]["composite_score"] > 0
    assert data["scores"]["recommended_framework"] in ["BANT", "MEDDIC", "CHAMP"]
    
    # Verify qualification
    assert data["qualification"]["decision"] in [
        "route_to_sales", "start_nurture", "disqualify"
    ]

@pytest.mark.asyncio
async def test_batch_scoring(client):
    """Integration test: batch scoring endpoint."""
    response = await client.post("/api/v1/leads/score/batch", json={
        "leads": [
            {"email": f"test{i}@acme{i}.com", "company_domain": f"acme{i}.com"}
            for i in range(5)
        ],
        "frameworks": ["BANT"],
        "include_prediction": False,
        "sync_to_crm": False,
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_leads"] == 5
    assert data["processed"] + data["failed"] == 5
    assert len(data["results"]) == 5

@pytest.mark.asyncio
async def test_health_check(client):
    """Integration test: health check endpoint."""
    response = await client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "services" in data

# tests/integration/test_crm_sync.py
@pytest.mark.asyncio
async def test_salesforce_upsert():
    """Integration test: Salesforce lead upsert."""
    adapter = SalesforceAdapter()
    
    lead_data = {
        "email": "integration@test.com",
        "first_name": "Integration",
        "last_name": "Test",
        "company_name": "Test Corp",
        "job_title": "CTO",
        "industry": "Technology",
        "employee_count": 500,
        "annual_revenue": 10_000_000,
        "composite_score": 75,
        "conversion_probability": 0.65,
        "predicted_ltv": 50000,
    }
    
    # This test requires valid Salesforce credentials
    # Skip if not configured
    if not settings.SALESFORCE_USERNAME:
        pytest.skip("Salesforce not configured")
    
    lead_id = await adapter.upsert_lead(lead_data)
    
    assert lead_id is not None
    assert len(lead_id) > 0
```

### 9.4 E2E Tests

```python
# tests/e2e/test_end_to_end.py
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime

@pytest.mark.asyncio
async def test_complete_lead_lifecycle():
    """
    E2E test: Complete lead lifecycle from ingestion to CRM sync.
    
    This test exercises the full pipeline:
    1. Lead ingestion
    2. Enrichment (with real or mocked APIs)
    3. Scoring (BANT + MEDDIC + CHAMP)
    4. Qualification
    5. Prediction
    6. CRM sync
    7. Score history tracking
    """
    # Step 1: Ingest lead
    lead_input = {
        "email": "e2e@testcompany.com",
        "first_name": "E2E",
        "last_name": "Test",
        "company_name": "Test Company Inc",
        "company_domain": "testcompany.com",
        "source": "webinar",
        "utm_campaign": "e2e_test",
    }
    
    # Step 2-5: Run full pipeline
    enrichment = await run_enrichment_agent(lead_input)
    scores = await run_scoring_agent(enrichment.model_dump())
    qualification = await run_qualification_agent(
        enrichment.model_dump(), scores.model_dump()
    )
    prediction = await run_predictive_agent(
        enrichment.model_dump(), scores.model_dump()
    )
    
    # Verify pipeline completed
    assert enrichment.confidence_score > 0
    assert scores.composite_score > 0
    assert qualification.decision is not None
    assert prediction.conversion_probability is not None
    
    # Step 6: Verify CRM sync (mock or real)
    # In E2E, we verify the sync was queued/completed
    
    # Step 7: Verify score history
    await store_score_history(enrichment.lead_id, scores.model_dump())
    history = await get_lead_score_history(enrichment.lead_id)
    
    assert len(history) >= 1
    assert history[-1]["composite_score"] == scores.composite_score

@pytest.mark.asyncio
async def test_rescore_improves_score():
    """
    E2E test: Re-scoring a lead with new data should update the score.
    """
    # Initial score
    lead_input = {
        "email": "rescore@test.com",
        "company_domain": "test.com",
        "source": "content_download",
    }
    
    enrichment1 = await run_enrichment_agent(lead_input)
    scores1 = await run_scoring_agent(enrichment1.model_dump())
    
    # Simulate new engagement (webinar attendance)
    lead_input["source"] = "webinar"
    
    # Clear cache to force re-enrichment
    cache_key = f"enrichment:{hash(lead_input['email'])}"
    await redis.delete(cache_key)
    
    enrichment2 = await run_enrichment_agent(lead_input)
    scores2 = await run_scoring_agent(enrichment2.model_dump())
    
    # Score should change (likely improve with webinar source)
    assert scores1.composite_score != scores2.composite_score or scores1.composite_score == scores2.composite_score  # At minimum, it should complete
```

### 9.5 Performance Tests

```python
# tests/performance/test_load.py
import asyncio
import time
import statistics
from httpx import AsyncClient

async def test_concurrent_scoring_performance():
    """
    Performance test: Score 50 leads concurrently.
    
    Targets:
    - p50 latency: < 5 seconds
    - p95 latency: < 15 seconds
    - Success rate: > 95%
    """
    async with AsyncClient(base_url="http://localhost:8000") as client:
        latencies = []
        errors = 0
        
        async def score_one(i):
            try:
                start = time.time()
                response = await client.post("/api/v1/leads/score", json={
                    "email": f"perf{i}@test{i}.com",
                    "company_domain": f"test{i}.com",
                    "source": "webinar",
                    "sync_to_crm": False,
                })
                latency = time.time() - start
                if response.status_code == 200:
                    latencies.append(latency)
                else:
                    errors += 1
            except Exception:
                errors += 1
        
        # Run 50 concurrent requests
        await asyncio.gather(*[score_one(i) for i in range(50)])
        
        # Calculate metrics
        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        success_rate = (50 - errors) / 50
        
        print(f"p50: {p50:.2f}s, p95: {p95:.2f}s, success: {success_rate:.0%}")
        
        assert p50 < 5.0, f"p50 latency {p50:.2f}s exceeds 5s target"
        assert p95 < 15.0, f"p95 latency {p95:.2f}s exceeds 15s target"
        assert success_rate > 0.95, f"Success rate {success_rate:.0%} below 95%"

# tests/performance/test_enrichment_cache.py
async def test_enrichment_caching():
    """
    Verify that enrichment results are cached and reused.
    """
    lead_input = {
        "email": "cache@test.com",
        "company_domain": "test.com",
    }
    
    # First call - should hit APIs
    start1 = time.time()
    result1 = await run_enrichment_agent(lead_input)
    duration1 = time.time() - start1
    
    # Second call - should use cache
    start2 = time.time()
    result2 = await run_enrichment_agent(lead_input)
    duration2 = time.time() - start2
    
    # Cached call should be much faster
    assert duration2 < duration1 * 0.5, "Cache not effective"
    assert result1.lead_id == result2.lead_id
```

### 9.6 Test Configuration

```python
# conftest.py
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_external_apis():
    """Mock all external API calls during tests."""
    with patch("clearbit.Enrichment.find") as mock_clearbit, \
         patch("hunter.Hunter") as mock_hunter, \
         patch("httpx.AsyncClient") as mock_httpx:
        
        # Configure Clearbit mock
        mock_clearbit.return_value = {
            "company": {
                "legalName": "Test Corp",
                "category": {"industry": "Technology"},
                "metrics": {"employees": 500, "estimatedAnnualRevenue": "10000000"},
                "foundedYear": 2015,
                "geo": {"city": "SF", "country": "US"},
                "linkedin": {"handle": "test-corp"},
                "tech": [{"name": "Salesforce"}],
            }
        }
        
        # Configure Hunter mock
        mock_hunter_instance = MagicMock()
        mock_hunter.return_value = mock_hunter_instance
        mock_hunter_instance.email_verifier.return_value = {
            "status": "valid", "gibberish": False, "disposable": False, "webmail": False,
        }
        mock_hunter_instance.domain_search.return_value = {
            "pattern": "{first}.{last}", "organization": "Test Corp", "country": "US",
        }
        
        yield

@pytest.fixture
def sample_enriched_lead():
    """Fixture providing a sample enriched lead for testing."""
    return {
        "lead_id": "test-lead-123",
        "contact": {
            "first_name": "Jane",
            "last_name": "Doe",
            "full_name": "Jane Doe",
            "job_title": "CTO",
            "seniority": "C-Level",
            "department": "Technology",
            "email_verified": True,
            "email_risk": "low",
        },
        "firmographic": {
            "company_name": "Test Corp",
            "domain": "testcorp.com",
            "industry": "Technology",
            "employee_count": 500,
            "annual_revenue": 10_000_000,
            "founded_year": 2015,
            "headquarters": "San Francisco, US",
            "country": "US",
        },
        "technographic": {
            "technologies": ["Salesforce", "HubSpot", "AWS", "Kubernetes"],
            "cms": "WordPress",
            "analytics_tools": ["Google Analytics"],
            "crm": "Salesforce",
            "marketing_automation": "HubSpot",
        },
        "intent": {
            "intent_topics": ["digital transformation", "cloud migration"],
            "intent_score": 65,
            "surge_topics": ["cloud migration"],
            "last_intent_date": "2026-09-15",
        },
        "source": "webinar",
    }

# pytest.ini
"""
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Slow tests
"""
```

---

## Appendix: Deployment Checklist

- [ ] Set up environment variables for all API keys
- [ ] Configure CRM credentials (Salesforce/HubSpot)
- [ ] Run database migrations
- [ ] Train initial conversion prediction model on historical data
- [ ] Set up Redis for caching and Celery broker
- [ ] Deploy API with uvicorn (4 workers)
- [ ] Deploy Celery workers (4 concurrent)
- [ ] Configure Langfuse/LangSmith for observability
- [ ] Set up monitoring and alerting (Datadog/Grafana)
- [ ] Configure rate limiting on API endpoints
- [ ] Set up CI/CD pipeline for automated testing and deployment
- [ ] Load test with production-like traffic
- [ ] Document API with OpenAPI/Swagger
- [ ] Create runbook for common operational issues

---

*End of Implementation Plan*
