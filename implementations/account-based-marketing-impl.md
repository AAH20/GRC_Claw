# AI-Powered Account-Based Marketing (ABM) Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a multi-agent ABM system using LangChain DeepAgents that identifies high-value accounts, scores intent, maps buying committees, personalizes content, orchestrates cross-channel campaigns, and measures performance — all autonomously.

**Architecture:** Six specialized DeepAgents coordinated by a central orchestrator. Each agent owns one ABM capability and communicates via typed events. LangChain DeepAgents provides the agent runtime, tool-calling, and memory. A shared vector store (Chroma/Pinecone) holds account profiles, intent signals, and content assets. LangSmith traces every decision for observability.

**Tech Stack:** Python 3.11+, LangChain, LangGraph, DeepAgents, OpenAI GPT-4o / Anthropic Claude 3.5, ChromaDB, LangSmith, Pydantic v2, FastAPI, Redis (event bus), PostgreSQL (account data), Salesforce/HubSpot APIs (CRM), 6sense/Demandbase (intent data), Apache Airflow (scheduling)

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Account Identification Agent](#2-account-identification-agent)
3. [Intent Scoring Agent](#3-intent-scoring-agent)
4. [Buying Committee Mapper Agent](#4-buying-committee-mapper-agent)
5. [Content Personalization Agent](#5-content-personization-agent)
6. [Channel Orchestrator Agent](#6-channel-orchestrator-agent)
7. [Performance Analytics Agent](#7-performance-analytics-agent)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The ABM system uses a **hub-and-spoke** architecture with a central orchestrator and six domain agents:

```
┌─────────────────────────────────────────────────────────────┐
│                    ABM Orchestrator Agent                     │
│  (LangGraph StateGraph — routes tasks, manages state)        │
└────────┬────────┬────────┬────────┬────────┬────────────────┘
         │        │        │        │        │
    ┌────▼──┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐ ┌────────┐
    │Account│ │Intent│ │Buying│ │Content│ │Channel│ │Performance│
    │Identif│ │Score │ │Commit│ │Person.│ │Orchest│ │Analytics │
    │ication│ │      │ │tee   │ │alize │ │rator  │ │         │
    └───────┘ └──────┘ └──────┘ └──────┘ └───────┘ └─────────┘
         │        │        │        │        │        │
    ┌────▼────────▼────────▼────────▼────────▼────────▼────┐
    │              Shared Infrastructure Layer                │
    │  ChromaDB (vectors)  │  PostgreSQL (accounts)          │
    │  Redis (event bus)    │  LangSmith (tracing)            │
    │  CRM APIs             │  Intent Data APIs               │
    └────────────────────────────────────────────────────────┘
```

### 1.2 Agent Communication Protocol

All agents communicate via typed events on a Redis pub/sub bus. Each event is a Pydantic model validated before publishing.

```python
# events.py — Shared event contracts
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional

class EventType(str, Enum):
    ACCOUNT_IDENTIFIED = "account.identified"
    INTENT_SCORED = "intent.scored"
    COMMITTEE_MAPPED = "committee.mapped"
    CONTENT_GENERATED = "content.generated"
    CAMPAIGN_LAUNCHED = "campaign.launched"
    PERFORMANCE_REPORTED = "performance.reported"

class AgentEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    source_agent: str
    target_agent: Optional[str] = None
    payload: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str  # Links related events across agents
```

### 1.3 Orchestrator State Machine

The orchestrator uses LangGraph's `StateGraph` to manage the ABM pipeline:

```python
# orchestrator.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class ABMPipelineState(TypedDict):
    # Input
    target_icp: dict  # Ideal Customer Profile criteria
    campaign_budget: float
    campaign_duration_days: int

    # Agent outputs (accumulated)
    identified_accounts: Annotated[list, operator.add]
    intent_scores: Annotated[dict, operator.add]
    committee_maps: Annotated[dict, operator.add]
    personalized_content: Annotated[list, operator.add]
    channel_plans: Annotated[list, operator.add]
    performance_reports: Annotated[list, operator.add]

    # Control flow
    current_stage: str
    errors: Annotated[list, operator.add]

def build_orchestrator():
    graph = StateGraph(ABMPipelineState)

    graph.add_node("identify_accounts", identify_accounts_node)
    graph.add_node("score_intent", score_intent_node)
    graph.add_node("map_committees", map_committees_node)
    graph.add_node("personalize_content", personalize_content_node)
    graph.add_node("orchestrate_channels", orchestrate_channels_node)
    graph.add_node("analyze_performance", analyze_performance_node)

    graph.set_entry_point("identify_accounts")
    graph.add_edge("identify_accounts", "score_intent")
    graph.add_edge("score_intent", "map_committees")
    graph.add_edge("map_committees", "personalize_content")
    graph.add_edge("personalize_content", "orchestrate_channels")
    graph.add_edge("orchestrate_channels", "analyze_performance")
    graph.add_edge("analyze_performance", END)

    return graph.compile()
```

### 1.4 Shared Memory and Context

Each agent has access to a shared context store backed by ChromaDB:

```python
# context_store.py
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

class ABMContextStore:
    def __init__(self, collection_name: str = "abm_context"):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory="./chroma_db"
        )

    def store_account_profile(self, account_id: str, profile: dict):
        """Store enriched account profile for retrieval by other agents."""
        doc = Document(
            page_content=json.dumps(profile, indent=2),
            metadata={"account_id": account_id, "type": "account_profile"}
        )
        self.vectorstore.add_documents([doc], ids=[f"account_{account_id}"])

    def retrieve_similar_accounts(self, query: str, k: int = 5) -> list[Document]:
        """Find accounts similar to a query (e.g., for lookalike expansion)."""
        return self.vectorstore.similarity_search(query, k=k)

    def get_account_context(self, account_id: str) -> dict:
        """Retrieve full account context for an agent."""
        results = self.vectorstore.get(ids=[f"account_{account_id}"])
        if results["documents"]:
            return json.loads(results["documents"][0])
        return {}
```

---

## 2. Account Identification Agent

### 2.1 Purpose

Discovers and qualifies accounts matching the Ideal Customer Profile (ICP). Combines firmographic data, technographic signals, and lookalike modeling to build a prioritized target account list.

### 2.2 Tools

| Tool | Source | Purpose |
|------|--------|---------|
| `query_crm_accounts` | Salesforce/HubSpot API | Fetch accounts matching firmographic filters |
| `enrich_account_data` | Clearbit/ZoomInfo | Add firmographics, technographics, funding |
| `score_icp_fit` | Custom LLM scorer | Score 0-100 fit against ICP criteria |
| `find_lookalikes` | Embedding similarity | Find accounts similar to best customers |
| `check_budget_authority` | 6sense/Demandbase | Verify budget availability signals |

### 2.3 Implementation

```python
# agents/account_identification.py
from langchain_deepagents import DeepAgent, Tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional

class AccountIdentificationInput(BaseModel):
    icp_criteria: dict = Field(description="ICP filters: industry, size, revenue, tech stack")
    max_accounts: int = Field(default=100, description="Maximum accounts to identify")
    lookalike_seed_accounts: list[str] = Field(
        default_factory=list,
        description="Account IDs of best customers for lookalike modeling"
    )

class AccountIdentificationOutput(BaseModel):
    accounts: list[dict]
    total_identified: int
    icp_fit_distribution: dict  # {"high": 45, "medium": 30, "low": 25}
    lookalikes_found: int

# Tool definitions
query_crm_accounts_tool = Tool(
    name="query_crm_accounts",
    description="Query CRM for accounts matching firmographic filters",
    func=query_crm_accounts_impl,
    args_schema=CRMQueryArgs
)

enrich_account_tool = Tool(
    name="enrich_account_data",
    description="Enrich account with firmographic and technographic data from Clearbit/ZoomInfo",
    func=enrich_account_impl,
    args_schema=EnrichArgs
)

score_icp_fit_tool = Tool(
    name="score_icp_fit",
    description="Score how well an account matches ICP criteria (0-100)",
    func=score_icp_fit_impl,
    args_schema=ICPScoreArgs
)

find_lookalikes_tool = Tool(
    name="find_lookalike_accounts",
    description="Find accounts similar to seed accounts using embedding similarity",
    func=find_lookalikes_impl,
    args_schema=LookalikeArgs
)

# Agent construction
account_identification_agent = DeepAgent(
    name="account_identifier",
    model=ChatOpenAI(model="gpt-4o", temperature=0.1),
    tools=[
        query_crm_accounts_tool,
        enrich_account_tool,
        score_icp_fit_tool,
        find_lookalikes_tool,
    ],
    system_message="""You are an expert B2B account identification specialist.

Your job is to find the best target accounts for an ABM campaign.

Process:
1. Query CRM for accounts matching the ICP criteria
2. Enrich each account with firmographic and technographic data
3. Score each account's fit against the ICP (0-100)
4. If lookalike seed accounts are provided, find similar accounts
5. Return accounts sorted by ICP fit score, highest first

Prioritize accounts with:
- Strong firmographic match (industry, size, revenue)
- Technology stack compatibility
- Recent funding or growth signals
- Geographic alignment with sales coverage

Always explain your scoring rationale.""",
    output_schema=AccountIdentificationOutput,
)
```

### 2.4 Scoring Logic

```python
# scoring/icp_scorer.py
def score_icp_fit(account: dict, icp_criteria: dict) -> dict:
    """
    Score account fit against ICP using weighted criteria.
    Returns score 0-100 with breakdown.
    """
    weights = {
        "industry_match": 0.25,
        "company_size": 0.20,
        "revenue_range": 0.20,
        "tech_stack": 0.15,
        "geography": 0.10,
        "growth_signals": 0.10,
    }

    scores = {}

    # Industry match (exact or adjacent)
    scores["industry_match"] = score_industry(
        account.get("industry", ""),
        icp_criteria.get("target_industries", [])
    )

    # Company size (employee count within range)
    scores["company_size"] = score_company_size(
        account.get("employee_count", 0),
        icp_criteria.get("employee_range", {"min": 0, "max": 100000})
    )

    # Revenue range
    scores["revenue_range"] = score_revenue(
        account.get("annual_revenue", 0),
        icp_criteria.get("revenue_range", {"min": 0, "max": 1e12})
    )

    # Technology stack overlap
    scores["tech_stack"] = score_tech_stack(
        account.get("technologies", []),
        icp_criteria.get("target_technologies", [])
    )

    # Geographic match
    scores["geography"] = score_geography(
        account.get("location", {}),
        icp_criteria.get("target_regions", [])
    )

    # Growth signals (funding, hiring, expansion)
    scores["growth_signals"] = score_growth_signals(account)

    # Weighted total
    total = sum(scores[k] * weights[k] for k in weights)

    return {
        "total_score": round(total, 1),
        "breakdown": scores,
        "tier": "high" if total >= 75 else "medium" if total >= 50 else "low",
        "rationale": generate_scoring_rationale(scores, weights)
    }
```

---

## 3. Intent Scoring Agent

### 3.1 Purpose

Monitors and scores buying intent signals across identified accounts. Aggregates first-party data (website visits, content downloads, email engagement) and third-party data (6sense, Demandbase, Bombora) to produce a real-time intent score.

### 3.2 Intent Signal Sources

| Signal Type | Source | Weight | Freshness |
|-------------|--------|--------|-----------|
| Website visits (pricing pages) | Segment/GA4 | High | Real-time |
| Content downloads (whitepapers, case studies) | HubSpot/Marketo | High | Real-time |
| Email engagement (opens, clicks) | ESP | Medium | Real-time |
| Third-party intent topics | 6sense/Demandbase | High | Daily |
| Job postings (hiring signals) | LinkedIn/Greenhouse | Medium | Weekly |
| Tech install changes | BuiltWith/Datafox | Medium | Weekly |
| Social mentions | Sprout Social | Low | Daily |

### 3.3 Implementation

```python
# agents/intent_scoring.py
from langchain_deepagents import DeepAgent, Tool
from datetime import datetime, timedelta

class IntentScoringInput(BaseModel):
    account_ids: list[str]
    lookback_days: int = Field(default=30, description="Days of intent data to analyze")
    intent_topics: list[str] = Field(
        default_factory=list,
        description="Topics to track (e.g., 'data security', 'cloud migration')"
    )

class IntentScore(BaseModel):
    account_id: str
    overall_score: float  # 0-100
    topic_scores: dict[str, float]  # {"data_security": 85, "cloud_migration": 42}
    signal_breakdown: list[dict]  # Individual signals with weights
    trend: str  # "rising", "stable", "declining"
    peak_intent_date: Optional[str]
    buying_stage: str  # "awareness", "consideration", "decision"
    confidence: float  # 0-1 based on data volume

class IntentScoringOutput(BaseModel):
    scores: list[IntentScore]
    high_intent_accounts: list[str]  # score >= 70
    trending_topics: list[dict]

# Tools
fetch_first_party_intent_tool = Tool(
    name="fetch_first_party_intent",
    description="Fetch website visits, content downloads, and email engagement from first-party sources",
    func=fetch_first_party_intent_impl,
    args_schema=FirstPartyIntentArgs
)

fetch_third_party_intent_tool = Tool(
    name="fetch_third_party_intent",
    description="Fetch intent data from 6sense, Demandbase, or Bombora",
    func=fetch_third_party_intent_impl,
    args_schema=ThirdPartyIntentArgs
)

analyze_intent_trends_tool = Tool(
    name="analyze_intent_trends",
    description="Analyze intent signal trends over time to detect rising/declining interest",
    func=analyze_intent_trends_impl,
    args_schema=IntentTrendArgs
)

classify_buying_stage_tool = Tool(
    name="classify_buying_stage",
    description="Classify which stage of the buying journey the account is in based on intent patterns",
    func=classify_buying_stage_impl,
    args_schema=BuyingStageArgs
)

intent_scoring_agent = DeepAgent(
    name="intent_scorer",
    model=ChatOpenAI(model="gpt-4o", temperature=0.1),
    tools=[
        fetch_first_party_intent_tool,
        fetch_third_party_intent_tool,
        analyze_intent_trends_tool,
        classify_buying_stage_tool,
    ],
    system_message="""You are a B2B intent data analyst specializing in account-level buying signals.

Your job is to score buying intent for each target account.

Scoring methodology:
1. Collect all intent signals from first-party and third-party sources
2. Weight signals by type and recency (recent = higher weight)
3. Group signals by topic and score each topic 0-100
4. Calculate overall intent score as weighted average
5. Determine trend direction (rising/stable/declining)
6. Classify buying stage based on signal patterns:
   - Awareness: broad topic interest, low engagement depth
   - Consideration: specific product comparisons, pricing page visits
   - Decision: competitor evaluations, RFP signals, demo requests

Flag accounts with score >= 70 as high-intent for immediate sales follow-up.

Always provide confidence scores based on data volume and quality.""",
    output_schema=IntentScoringOutput,
)
```

### 3.4 Intent Scoring Algorithm

```python
# scoring/intent_scorer.py
from datetime import datetime, timedelta

SIGNAL_WEIGHTS = {
    "pricing_page_visit": 15,
    "demo_request": 25,
    "whitepaper_download": 10,
    "case_study_download": 12,
    "webinar_attendance": 8,
    "email_click": 3,
    "email_open": 1,
    "third_party_topic_surge": 20,
    "competitor_evaluation": 18,
    "rfp_signal": 30,
    "hiring_signal": 5,
    "tech_install_change": 7,
}

RECENCY_MULTIPLIERS = {
    7: 1.5,    # Last 7 days: 1.5x
    14: 1.2,   # Last 14 days: 1.2x
    30: 1.0,   # Last 30 days: 1.0x
    60: 0.5,   # Last 60 days: 0.5x
    90: 0.2,   # Last 90 days: 0.2x
}

def calculate_intent_score(signals: list[dict], topics: list[str]) -> IntentScore:
    """
    Calculate weighted intent score from raw signals.
    """
    topic_scores = {topic: 0.0 for topic in topics}
    topic_signal_counts = {topic: 0 for topic in topics}
    total_weighted_score = 0.0
    total_possible = 0.0

    for signal in signals:
        signal_type = signal["type"]
        topic = signal.get("topic", "general")
        raw_weight = SIGNAL_WEIGHTS.get(signal_type, 1)

        # Apply recency multiplier
        age_days = (datetime.utcnow() - signal["timestamp"]).days
        recency_mult = 0.1  # Default for old signals
        for max_days, mult in sorted(RECENCY_MULTIPLIERS.items()):
            if age_days <= max_days:
                recency_mult = mult
                break

        weighted_score = raw_weight * recency_mult
        total_weighted_score += weighted_score
        total_possible += raw_weight * 1.5  # Max possible with recency

        if topic in topic_scores:
            topic_scores[topic] += weighted_score
            topic_signal_counts[topic] += 1

    # Normalize to 0-100
    overall_score = min(100, (total_weighted_score / max(total_possible, 1)) * 100)

    # Normalize topic scores
    for topic in topic_scores:
        if topic_signal_counts[topic] > 0:
            topic_scores[topic] = min(100, topic_scores[topic] / topic_signal_counts[topic] * 10)

    # Determine trend
    trend = calculate_trend(signals)

    # Classify buying stage
    buying_stage = classify_stage_from_signals(signals)

    # Confidence based on data volume
    confidence = min(1.0, len(signals) / 20)  # 20+ signals = full confidence

    return IntentScore(
        account_id=signals[0]["account_id"] if signals else "",
        overall_score=round(overall_score, 1),
        topic_scores={k: round(v, 1) for k, v in topic_scores.items()},
        signal_breakdown=signals,
        trend=trend,
        buying_stage=buying_stage,
        confidence=round(confidence, 2),
    )
```

---

## 4. Buying Committee Mapper Agent

### 4.1 Purpose

Identifies and maps the full buying committee for each target account — champions, decision makers, influencers, blockers, and economic buyers. Uses LinkedIn Sales Navigator, CRM contact data, and engagement patterns to build an org chart of stakeholders.

### 4.2 Committee Roles

| Role | Title Patterns | Influence | Priority |
|------|---------------|-----------|----------|
| Economic Buyer | C-level, VP | High | Critical |
| Champion | Manager, Director | High | Critical |
| Decision Maker | VP, Director | High | Critical |
| Influencer | Architect, Lead | Medium | High |
| User | Individual Contributor | Medium | Medium |
| Blocker | Competing vendor ally | Negative | Monitor |
| Legal/Procurement | Legal, Procurement | Medium | High |

### 4.3 Implementation

```python
# agents/committee_mapper.py
from langchain_deepagents import DeepAgent, Tool
from pydantic import BaseModel, Field
from enum import Enum

class CommitteeRole(str, Enum):
    ECONOMIC_BUYER = "economic_buyer"
    CHAMPION = "champion"
    DECISION_MAKER = "decision_maker"
    INFLUENCER = "influencer"
    USER = "user"
    BLOCKER = "blocker"
    LEGAL_PROCUREMENT = "legal_procurement"

class Stakeholder(BaseModel):
    name: str
    title: str
    role: CommitteeRole
    influence_score: float  # 0-100
    engagement_level: str  # "high", "medium", "low", "none"
    relationship_owner: Optional[str]  # Sales rep name
    linkedin_url: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    notes: str

class CommitteeMap(BaseModel):
    account_id: str
    stakeholders: list[Stakeholder]
    committee_completeness: float  # 0-1, how complete is the map
    missing_roles: list[CommitteeRole]
    engagement_gaps: list[str]  # Stakeholders with no engagement
    recommended_actions: list[str]  # Who to engage next

class CommitteeMappingOutput(BaseModel):
    committee_maps: list[CommitteeMap]
    accounts_with_incomplete_maps: list[str]
    coverage_summary: dict

# Tools
fetch_crm_contacts_tool = Tool(
    name="fetch_crm_contacts",
    description="Fetch all contacts associated with an account from CRM",
    func=fetch_crm_contacts_impl,
    args_schema=CRMContactsArgs
)

search_linkedin_tool = Tool(
    name="search_linkedin_sales_nav",
    description="Search LinkedIn Sales Navigator for contacts at the account by title/department",
    func=search_linkedin_impl,
    args_schema=LinkedInSearchArgs
)

analyze_engagement_tool = Tool(
    name="analyze_stakeholder_engagement",
    description="Analyze email, meeting, and content engagement for each contact",
    func=analyze_engagement_impl,
    args_schema=EngagementAnalysisArgs
)

classify_role_tool = Tool(
    name="classify_committee_role",
    description="Classify a contact's role in the buying committee based on title, department, and behavior",
    func=classify_role_impl,
    args_schema=RoleClassificationArgs
)

identify_gaps_tool = Tool(
    name="identify_committee_gaps",
    description="Identify missing roles and engagement gaps in the buying committee",
    func=identify_gaps_impl,
    args_schema=GapAnalysisArgs
)

committee_mapper_agent = DeepAgent(
    name="committee_mapper",
    model=ChatOpenAI(model="gpt-4o", temperature=0.1),
    tools=[
        fetch_crm_contacts_tool,
        search_linkedin_tool,
        analyze_engagement_tool,
        classify_role_tool,
        identify_gaps_tool,
    ],
    system_message="""You are a B2B buying committee mapping specialist.

Your job is to identify and map all stakeholders involved in a purchase decision at each target account.

Process:
1. Fetch all known contacts from CRM for the account
2. Search LinkedIn Sales Navigator for additional contacts by department/title
3. Analyze engagement data to identify active vs. inactive stakeholders
4. Classify each contact's role in the buying committee
5. Identify gaps — missing roles that should be engaged
6. Recommend next best actions for engagement

Key principles:
- Map at least 5-7 stakeholders per enterprise account
- Identify at least one champion (someone who wants you to win)
- Find the economic buyer (who controls budget)
- Flag potential blockers early
- Prioritize outreach to unengaged but influential stakeholders

Always provide specific, actionable recommendations.""",
    output_schema=CommitteeMappingOutput,
)
```

### 4.4 Role Classification Logic

```python
# scoring/role_classifier.py
import re

ROLE_PATTERNS = {
    CommitteeRole.ECONOMIC_BUYER: [
        r"\bC[IO][OT]\b", r"\bCEO\b", r"\bCFO\b", r"\bCTO\b", r"\bCMO\b",
        r"\bChief\b", r"\bPresident\b", r"\bVP\b.*\b(?:Revenue|Sales|Marketing|IT|Technology)\b",
    ],
    CommitteeRole.DECISION_MAKER: [
        r"\bVP\b", r"\bVice President\b", r"\bDirector\b.*\b(?:IT|Technology|Security|Infrastructure)\b",
        r"\bHead of\b", r"\bGeneral Manager\b",
    ],
    CommitteeRole.CHAMPION: [
        r"\bManager\b", r"\bSenior Manager\b", r"\bTeam Lead\b", r"\bProject Lead\b",
    ],
    CommitteeRole.INFLUENCER: [
        r"\bArchitect\b", r"\bPrincipal\b", r"\bStaff\b", r"\bLead Engineer\b",
        r"\bSenior Engineer\b", r"\bConsultant\b",
    ],
    CommitteeRole.USER: [
        r"\bEngineer\b", r"\bAnalyst\b", r"\bSpecialist\b", r"\bCoordinator\b",
        r"\bAdministrator\b",
    ],
    CommitteeRole.LEGAL_PROCUREMENT: [
        r"\bLegal\b", r"\bCounsel\b", r"\bProcurement\b", r"\bPurchasing\b",
        r"\bContract\b",
    ],
}

def classify_committee_role(title: str, department: str, engagement: dict) -> CommitteeRole:
    """
    Classify a contact's role based on title, department, and engagement patterns.
    """
    title_lower = title.lower()
    dept_lower = department.lower()

    # Score each role
    role_scores = {role: 0 for role in CommitteeRole}

    for role, patterns in ROLE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, title, re.IGNORECASE):
                role_scores[role] += 2
            if re.search(pattern, department, re.IGNORECASE):
                role_scores[role] += 1

    # Engagement-based adjustments
    if engagement.get("email_opens", 0) > 10 and engagement.get("meetings", 0) > 2:
        role_scores[CommitteeRole.CHAMPION] += 3

    if engagement.get("content_downloads", 0) > 5:
        role_scores[CommitteeRole.INFLUENCER] += 2

    # Return highest scoring role
    best_role = max(role_scores, key=role_scores.get)
    return best_role if role_scores[best_role] > 0 else CommitteeRole.USER
```

---

## 5. Content Personalization Agent

### 5.1 Purpose

Generates personalized content for each account and stakeholder based on their industry, role, intent topics, buying stage, and engagement history. Produces email sequences, ad copy, landing page variants, and sales collateral.

### 5.2 Content Types

| Content Type | Personalization Dimensions | Output |
|-------------|---------------------------|--------|
| Email sequences | Role, intent topic, buying stage, industry | 3-5 email sequence |
| Ad copy | Industry, role, intent topic | LinkedIn/Google ad variants |
| Landing page | Industry, account name, use case | Personalized hero + CTA |
| Sales one-pager | Account name, use case, ROI data | PDF/HTML one-pager |
| Case study match | Industry, company size, use case | Relevant case study + pitch |
| Outreach LinkedIn message | Role, mutual connections, intent | Connection request + follow-up |

### 5.3 Implementation

```python
# agents/content_personalization.py
from langchain_deepagents import DeepAgent, Tool
from pydantic import BaseModel, Field
from typing import Optional

class ContentPersonalizationInput(BaseModel):
    account_id: str
    account_profile: dict
    intent_score: dict
    committee_map: dict
    content_types: list[str] = Field(
        default_factory=lambda: ["email_sequence", "ad_copy", "landing_page", "sales_one_pager"]
    )
    brand_voice: str = Field(default="professional, consultative, data-driven")
    compliance_requirements: list[str] = Field(default_factory=list)

class PersonalizedContent(BaseModel):
    content_type: str
    stakeholder_role: Optional[str]  # None = account-level
    subject_line: Optional[str]
    body: str
    cta: str
    personalization_elements: list[str]  # What was personalized
    tone: str
    word_count: int

class ContentPersonalizationOutput(BaseModel):
    account_id: str
    content_pieces: list[PersonalizedContent]
    content_calendar: list[dict]  # Suggested send dates
    ab_test_variants: dict  # {"email_subject": ["variant_a", "variant_b"]}

# Tools
fetch_account_context_tool = Tool(
    name="fetch_account_context",
    description="Fetch full account profile, intent data, and committee map from context store",
    func=fetch_account_context_impl,
    args_schema=AccountContextArgs
)

generate_email_sequence_tool = Tool(
    name="generate_email_sequence",
    description="Generate a personalized email sequence for a specific stakeholder",
    func=generate_email_sequence_impl,
    args_schema=EmailSequenceArgs
)

generate_ad_copy_tool = Tool(
    name="generate_ad_copy",
    description="Generate personalized ad copy variants for LinkedIn and Google Ads",
    func=generate_ad_copy_impl,
    args_schema=AdCopyArgs
)

generate_landing_page_tool = Tool(
    name="generate_landing_page_variant",
    description="Generate personalized landing page copy and hero section",
    func=generate_landing_page_impl,
    args_schema=LandingPageArgs
)

match_case_study_tool = Tool(
    name="match_case_study",
    description="Find and match the most relevant case study for the account",
    func=match_case_study_impl,
    args_schema=CaseStudyMatchArgs
)

check_compliance_tool = Tool(
    name="check_content_compliance",
    description="Check generated content against brand guidelines and compliance requirements",
    func=check_compliance_impl,
    args_schema=ComplianceCheckArgs
)

content_personalization_agent = DeepAgent(
    name="content_personalizer",
    model=ChatOpenAI(model="gpt-4o", temperature=0.3),
    tools=[
        fetch_account_context_tool,
        generate_email_sequence_tool,
        generate_ad_copy_tool,
        generate_landing_page_tool,
        match_case_study_tool,
        check_compliance_tool,
    ],
    system_message="""You are a B2B content personalization specialist.

Your job is to generate highly personalized marketing content for each target account and stakeholder.

Personalization framework:
1. Account-level: Industry, company size, geography, tech stack
2. Stakeholder-level: Role, title, department, seniority
3. Intent-level: Topics of interest, buying stage, engagement history
4. Content-level: Tone, format, CTA, case study relevance

Content principles:
- Lead with the prospect's problem, not your product
- Use specific data points and metrics
- Reference their industry context
- Match tone to role (executive = strategic, practitioner = tactical)
- Always include a clear, single CTA
- Keep subject lines under 50 characters
- Personalize beyond first name — use company context

Compliance check:
- No unsubstantiated claims
- Include required disclaimers
- Respect industry regulations (GDPR, CCPA, HIPAA as applicable)
- Follow brand voice guidelines""",
    output_schema=ContentPersonalizationOutput,
)
```

### 5.4 Email Sequence Generation

```python
# content/email_sequence_generator.py
def generate_email_sequence(
    stakeholder: Stakeholder,
    account: dict,
    intent: IntentScore,
    sequence_length: int = 4
) -> list[PersonalizedContent]:
    """
    Generate a multi-touch email sequence personalized for a stakeholder.
    """
    sequence = []

    # Email 1: Awareness / Value-driven
    sequence.append(PersonalizedContent(
        content_type="email",
        stakeholder_role=stakeholder.role.value,
        subject_line=generate_subject_line("awareness", account, intent, stakeholder),
        body=generate_email_body(
            stage="awareness",
            stakeholder=stakeholder,
            account=account,
            intent=intent,
            angle="industry_insight"
        ),
        cta="Read the report",
        personalization_elements=[
            f"Industry: {account.get('industry')}",
            f"Role: {stakeholder.title}",
            f"Intent topic: {intent.trending_topics[0] if intent.trending_topics else 'general'}",
        ],
        tone="consultative",
        word_count=150,
    ))

    # Email 2: Social proof / Case study
    sequence.append(PersonalizedContent(
        content_type="email",
        stakeholder_role=stakeholder.role.value,
        subject_line=generate_subject_line("social_proof", account, intent, stakeholder),
        body=generate_email_body(
            stage="consideration",
            stakeholder=stakeholder,
            account=account,
            intent=intent,
            angle="case_study"
        ),
        cta="See how {similar_company} achieved {result}",
        personalization_elements=[
            f"Similar company: {find_similar_customer(account)}",
            f"Use case: {intent.trending_topics[0] if intent.trending_topics else 'general'}",
        ],
        tone="proof-driven",
        word_count=120,
    ))

    # Email 3: Direct value proposition
    sequence.append(PersonalizedContent(
        content_type="email",
        stakeholder_role=stakeholder.role.value,
        subject_line=generate_subject_line("value_prop", account, intent, stakeholder),
        body=generate_email_body(
            stage="decision",
            stakeholder=stakeholder,
            account=account,
            intent=intent,
            angle="roi_calculator"
        ),
        cta="Calculate your ROI",
        personalization_elements=[
            f"Company size: {account.get('employee_count')} employees",
            f"Estimated ROI: {calculate_estimated_roi(account)}",
        ],
        tone="direct",
        word_count=100,
    ))

    # Email 4: Breakup / Final attempt
    sequence.append(PersonalizedContent(
        content_type="email",
        stakeholder_role=stakeholder.role.value,
        subject_line=generate_subject_line("breakup", account, intent, stakeholder),
        body=generate_email_body(
            stage="breakup",
            stakeholder=stakeholder,
            account=account,
            intent=intent,
            angle="breakup"
        ),
        cta="Let me know if timing isn't right",
        personalization_elements=[
            f"Previous engagement: {stakeholder.engagement_level}",
        ],
        tone="respectful",
        word_count=80,
    ))

    return sequence
```

---

## 6. Channel Orchestrator Agent

### 6.1 Purpose

Determines the optimal mix of channels (email, LinkedIn, paid ads, direct mail, phone, events) for each account and stakeholder. Sequences touchpoints across channels, manages frequency caps, and coordinates timing to maximize engagement without overwhelming prospects.

### 6.2 Channel Options

| Channel | Best For | Cost | Personalization | Timing |
|---------|---------|------|-----------------|--------|
| Email | Nurture, follow-up | Low | High | Anytime |
| LinkedIn | Awareness, social proof | Medium | High | Business hours |
| Paid ads (LinkedIn/Google) | Awareness, retargeting | High | Medium | Always-on |
| Direct mail | High-value accounts | High | High | Weekly |
| Phone | Champion activation | Low | High | Business hours |
| Events | Relationship building | High | Medium | Scheduled |
| SMS | Urgent follow-up | Low | Medium | Business hours |

### 6.3 Implementation

```python
# agents/channel_orchestrator.py
from langchain_deepagents import DeepAgent, Tool
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

class ChannelOrchestrationInput(BaseModel):
    account_id: str
    account_profile: dict
    intent_score: dict
    committee_map: dict
    content_pieces: list[dict]
    budget: float
    campaign_duration_days: int = 90
    frequency_cap: int = Field(default=3, description="Max touches per stakeholder per week")

class Touchpoint(BaseModel):
    stakeholder_name: str
    stakeholder_role: str
    channel: str
    content_type: str
    scheduled_date: datetime
    subject_or_headline: str
    body_summary: str
    cta: str
    depends_on: Optional[str]  # Previous touchpoint ID this depends on

class ChannelPlan(BaseModel):
    account_id: str
    touchpoints: list[Touchpoint]
    channel_mix: dict[str, int]  # {"email": 8, "linkedin": 4, "paid_ads": 12}
    total_touches: int
    estimated_cost: float
    frequency_compliance: bool  # Within frequency caps

class ChannelOrchestrationOutput(BaseModel):
    channel_plans: list[ChannelPlan]
    total_estimated_cost: float
    channel_distribution: dict
    scheduling_conflicts: list[str]

# Tools
analyze_channel_effectiveness_tool = Tool(
    name="analyze_channel_effectiveness",
    description="Analyze historical channel effectiveness for similar accounts and personas",
    func=analyze_channel_effectiveness_impl,
    args_schema=ChannelEffectivenessArgs
)

optimize_channel_mix_tool = Tool(
    name="optimize_channel_mix",
    description="Use optimization to determine the best channel mix given budget and goals",
    func=optimize_channel_mix_impl,
    args_schema=ChannelMixArgs
)

schedule_touchpoints_tool = Tool(
    name="schedule_touchpoints",
    description="Schedule touchpoints across channels with proper sequencing and frequency caps",
    func=schedule_touchpoints_impl,
    args_schema=SchedulingArgs
)

check_frequency_caps_tool = Tool(
    name="check_frequency_caps",
    description="Verify that the plan doesn't exceed frequency caps for any stakeholder",
    func=check_frequency_caps_impl,
    args_schema=FrequencyCapArgs
)

coordinate_with_sales_tool = Tool(
    name="coordinate_with_sales",
    description="Coordinate outreach timing with sales team activities to avoid conflicts",
    func=coordinate_with_sales_impl,
    args_schema=SalesCoordinationArgs
)

channel_orchestrator_agent = DeepAgent(
    name="channel_orchestrator",
    model=ChatOpenAI(model="gpt-4o", temperature=0.1),
    tools=[
        analyze_channel_effectiveness_tool,
        optimize_channel_mix_tool,
        schedule_touchpoints_tool,
        check_frequency_caps_tool,
        coordinate_with_sales_tool,
    ],
    system_message="""You are a B2B multi-channel campaign orchestrator.

Your job is to plan and sequence the optimal mix of marketing channels for each target account.

Orchestration principles:
1. Match channel to intent stage:
   - Awareness: LinkedIn ads, content syndication, display
   - Consideration: Email nurture, retargeting, webinars
   - Decision: Direct mail, phone, LinkedIn direct, events

2. Respect frequency caps:
   - Max 3 touches per stakeholder per week
   - Max 1 email per day per stakeholder
   - Min 3 days between same-channel touches

3. Sequence for impact:
   - Start with awareness channels (ads, content)
   - Follow with direct channels (email, LinkedIn)
   - Escalate to high-touch (direct mail, phone) for high-intent accounts
   - Always end with a clear CTA

4. Coordinate with sales:
   - Don't overlap with sales outreach
   - Align with sales stage
   - Share engagement data with sales reps

5. Budget allocation:
   - Allocate more budget to high-intent accounts
   - Reserve 20% for testing and optimization
   - Prioritize channels with proven ROI""",
    output_schema=ChannelOrchestrationOutput,
)
```

### 6.4 Channel Optimization Algorithm

```python
# orchestration/channel_optimizer.py
from scipy.optimize import minimize
import numpy as np

CHANNEL_COSTS = {
    "email": 0.01,
    "linkedin_ads": 5.00,
    "google_ads": 3.00,
    "direct_mail": 8.00,
    "phone": 0.50,
    "event": 50.00,
    "sms": 0.05,
}

CHANNEL_EFFECTIVENESS = {
    # Effectiveness by buying stage (0-1)
    "awareness": {
        "email": 0.3, "linkedin_ads": 0.8, "google_ads": 0.7,
        "direct_mail": 0.4, "phone": 0.2, "event": 0.6, "sms": 0.1,
    },
    "consideration": {
        "email": 0.7, "linkedin_ads": 0.6, "google_ads": 0.5,
        "direct_mail": 0.6, "phone": 0.5, "event": 0.7, "sms": 0.3,
    },
    "decision": {
        "email": 0.6, "linkedin_ads": 0.4, "google_ads": 0.3,
        "direct_mail": 0.8, "phone": 0.9, "event": 0.8, "sms": 0.5,
    },
}

def optimize_channel_mix(
    budget: float,
    intent_score: float,
    buying_stage: str,
    stakeholder_count: int,
    duration_days: int
) -> dict[str, int]:
    """
    Optimize channel mix to maximize expected engagement within budget.
    Uses linear programming to find optimal allocation.
    """
    channels = list(CHANNEL_COSTS.keys())
    n_channels = len(channels)

    # Effectiveness scores for this buying stage
    effectiveness = np.array([
        CHANNEL_EFFECTIVENESS.get(buying_stage, {}).get(ch, 0.5)
        for ch in channels
    ])

    # Cost per touch
    costs = np.array([CHANNEL_COSTS[ch] for ch in channels])

    # Budget constraint: sum(costs * touches) <= budget
    # Maximize: sum(effectiveness * touches)
    # Subject to: touches >= 0, integer

    # Simple greedy allocation (can be replaced with proper LP solver)
    remaining_budget = budget
    allocation = {ch: 0 for ch in channels}

    # Sort channels by effectiveness/cost ratio
    efficiency = effectiveness / costs
    sorted_indices = np.argsort(-efficiency)

    # Reserve 20% for testing
    test_budget = budget * 0.2
    remaining_budget = budget * 0.8

    for idx in sorted_indices:
        ch = channels[idx]
        max_touches = int(remaining_budget / costs[idx])
        # Cap at reasonable frequency
        max_touches = min(max_touches, stakeholder_count * (duration_days // 7) * 3)
        allocation[ch] = max_touches
        remaining_budget -= max_touches * costs[idx]

    return allocation
```

---

## 7. Performance Analytics Agent

### 7.1 Purpose

Measures campaign performance across all channels and accounts. Calculates ROI, engagement rates, pipeline influence, and attribution. Provides recommendations for optimization and generates executive dashboards.

### 7.2 Key Metrics

| Category | Metric | Formula | Target |
|----------|--------|---------|--------|
| Engagement | Email open rate | Opens / Delivered | >25% |
| Engagement | Email click rate | Clicks / Delivered | >3% |
| Engagement | Ad CTR | Clicks / Impressions | >0.5% |
| Engagement | Content engagement rate | Engagements / Touches | >15% |
| Pipeline | Influenced pipeline | Sum of influenced opp value | Track |
| Pipeline | Pipeline velocity | Avg days from first touch to close | Reduce 20% |
| Pipeline | Win rate | Wins / Total opps | >30% |
| Revenue | ROI | (Revenue - Cost) / Cost | >5x |
| Revenue | CAC | Total cost / New customers | Reduce 15% |
| Account | Account engagement score | Weighted engagement across stakeholders | >60 |
| Account | Committee coverage | Engaged stakeholders / Total stakeholders | >70% |

### 7.3 Implementation

```python
# agents/performance_analytics.py
from langchain_deepagents import DeepAgent, Tool
from pydantic import BaseModel, Field
from datetime import datetime

class PerformanceAnalyticsInput(BaseModel):
    campaign_id: str
    account_ids: list[str]
    date_range: tuple[str, str]  # start_date, end_date
    metrics: list[str] = Field(
        default_factory=lambda: [
            "engagement", "pipeline", "revenue", "account_health"
        ]
    )

class MetricResult(BaseModel):
    metric_name: str
    value: float
    benchmark: float
    status: str  # "above_target", "on_target", "below_target"
    trend: str  # "improving", "stable", "declining"
    recommendation: str

class AccountPerformance(BaseModel):
    account_id: str
    metrics: list[MetricResult]
    overall_health_score: float  # 0-100
    engagement_trend: str
    pipeline_influence: float
    recommended_actions: list[str]

class PerformanceAnalyticsOutput(BaseModel):
    campaign_id: str
    account_performances: list[AccountPerformance]
    aggregate_metrics: dict
    top_performing_accounts: list[str]
    underperforming_accounts: list[str]
    channel_attribution: dict
    roi_summary: dict
    optimization_recommendations: list[str]

# Tools
fetch_campaign_data_tool = Tool(
    name="fetch_campaign_data",
    description="Fetch campaign performance data from all connected sources",
    func=fetch_campaign_data_impl,
    args_schema=CampaignDataArgs
)

calculate_engagement_metrics_tool = Tool(
    name="calculate_engagement_metrics",
    description="Calculate engagement rates across all channels and touchpoints",
    func=calculate_engagement_metrics_impl,
    args_schema=EngagementMetricsArgs
)

calculate_attribution_tool = Tool(
    name="calculate_attribution",
    description="Calculate multi-touch attribution for pipeline and revenue",
    func=calculate_attribution_impl,
    args_schema=AttributionArgs
)

calculate_roi_tool = Tool(
    name="calculate_roi",
    description="Calculate campaign ROI including cost and revenue attribution",
    func=calculate_roi_impl,
    args_schema=ROIArgs
)

generate_insights_tool = Tool(
    name="generate_insights",
    description="Generate actionable insights and recommendations from performance data",
    func=generate_insights_impl,
    args_schema=InsightsArgs
)

performance_analytics_agent = DeepAgent(
    name="performance_analyst",
    model=ChatOpenAI(model="gpt-4o", temperature=0.1),
    tools=[
        fetch_campaign_data_tool,
        calculate_engagement_metrics_tool,
        calculate_attribution_tool,
        calculate_roi_tool,
        generate_insights_tool,
    ],
    system_message="""You are a B2B marketing performance analytics specialist.

Your job is to measure, analyze, and optimize ABM campaign performance.

Analysis framework:
1. Engagement Analysis:
   - Email metrics (open, click, reply rates)
   - Ad metrics (impressions, CTR, conversions)
   - Content metrics (downloads, time on page)
   - Account-level engagement scoring

2. Pipeline Analysis:
   - Influenced pipeline value
   - Pipeline velocity (speed to close)
   - Win rate and deal size
   - Stage progression analysis

3. Revenue Analysis:
   - ROI by account, channel, and campaign
   - Customer acquisition cost
   - Lifetime value impact
   - Payback period

4. Attribution:
   - Multi-touch attribution (first-touch, last-touch, linear, time-decay)
   - Channel contribution analysis
   - Content influence mapping

5. Recommendations:
   - Which accounts to increase/decrease investment
   - Which channels to scale/pause
   - Which content to promote/deprecate
   - Budget reallocation suggestions

Always benchmark against industry standards and previous campaigns.""",
    output_schema=PerformanceAnalyticsOutput,
)
```

### 7.4 Attribution Model

```python
# analytics/attribution.py
from datetime import datetime, timedelta

ATTRIBUTION_MODELS = {
    "first_touch": lambda touches: touches[0]["channel"] if touches else None,
    "last_touch": lambda touches: touches[-1]["channel"] if touches else None,
    "linear": lambda touches: distribute_evenly(touches),
    "time_decay": lambda touches: distribute_by_recency(touches),
    "position_based": lambda touches: distribute_by_position(touches),
}

def distribute_evenly(touches: list[dict]) -> dict[str, float]:
    """Linear attribution: equal credit to all touches."""
    credit = 1.0 / len(touches) if touches else 0
    result = {}
    for touch in touches:
        channel = touch["channel"]
        result[channel] = result.get(channel, 0) + credit
    return result

def distribute_by_recency(touches: list[dict], half_life_days: int = 7) -> dict[str, float]:
    """Time decay attribution: more credit to recent touches."""
    if not touches:
        return {}

    # Sort by date
    sorted_touches = sorted(touches, key=lambda t: t["timestamp"])
    now = sorted_touches[-1]["timestamp"]

    # Calculate weights using exponential decay
    weights = []
    for touch in sorted_touches:
        age_days = (now - touch["timestamp"]).days
        weight = 0.5 ** (age_days / half_life_days)
        weights.append(weight)

    # Normalize
    total_weight = sum(weights)
    normalized = [w / total_weight for w in weights]

    result = {}
    for touch, weight in zip(sorted_touches, normalized):
        channel = touch["channel"]
        result[channel] = result.get(channel, 0) + weight

    return result

def distribute_by_position(touches: list[dict]) -> dict[str, float]:
    """Position-based: 40% first, 40% last, 20% middle."""
    if not touches:
        return {}
    if len(touches) == 1:
        return {touches[0]["channel"]: 1.0}
    if len(touches) == 2:
        return {touches[0]["channel"]: 0.5, touches[1]["channel"]: 0.5}

    result = {}
    first_channel = touches[0]["channel"]
    last_channel = touches[-1]["channel"]

    result[first_channel] = result.get(first_channel, 0) + 0.4
    result[last_channel] = result.get(last_channel, 0) + 0.4

    middle_touches = touches[1:-1]
    if middle_touches:
        middle_credit = 0.2 / len(middle_touches)
        for touch in middle_touches:
            channel = touch["channel"]
            result[channel] = result.get(channel, 0) + middle_credit

    return result
```

---

## 8. Code Examples and Snippets

### 8.1 Complete Agent Factory

```python
# agents/factory.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI

def create_abm_agents(model: str = "gpt-4o") -> dict[str, DeepAgent]:
    """Factory function to create all ABM agents with shared configuration."""
    llm = ChatOpenAI(model=model, temperature=0.1)

    agents = {
        "account_identifier": create_account_identification_agent(llm),
        "intent_scorer": create_intent_scoring_agent(llm),
        "committee_mapper": create_committee_mapper_agent(llm),
        "content_personalizer": create_content_personalization_agent(llm),
        "channel_orchestrator": create_channel_orchestrator_agent(llm),
        "performance_analyst": create_performance_analytics_agent(llm),
    }

    return agents
```

### 8.2 FastAPI Service Wrapper

```python
# api/main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(title="ABM Agent API", version="1.0.0")

class CampaignRequest(BaseModel):
    icp_criteria: dict
    budget: float
    duration_days: int = 90
    intent_topics: list[str] = []
    content_types: list[str] = ["email_sequence", "ad_copy"]

class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    message: str

@app.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignRequest,
    background_tasks: BackgroundTasks
):
    """Start a new ABM campaign."""
    campaign_id = str(uuid.uuid4())

    # Launch campaign in background
    background_tasks.add_task(
        run_abm_campaign,
        campaign_id=campaign_id,
        request=request,
    )

    return CampaignResponse(
        campaign_id=campaign_id,
        status="started",
        message=f"ABM campaign {campaign_id} started successfully"
    )

@app.get("/campaigns/{campaign_id}")
async def get_campaign_status(campaign_id: str):
    """Get campaign status and results."""
    # Fetch from database/cache
    status = await get_campaign_state(campaign_id)
    return status

@app.get("/campaigns/{campaign_id}/accounts/{account_id}")
async def get_account_details(campaign_id: str, account_id: str):
    """Get detailed account information including all agent outputs."""
    account_data = await get_account_state(campaign_id, account_id)
    return account_data

@app.get("/campaigns/{campaign_id}/analytics")
async def get_campaign_analytics(campaign_id: str):
    """Get campaign performance analytics."""
    analytics = await get_campaign_analytics(campaign_id)
    return analytics
```

### 8.3 LangSmith Tracing Configuration

```python
# config/tracing.py
import os
from langsmith import Client

def setup_tracing():
    """Configure LangSmith tracing for all agents."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
    os.environ["LANGCHAIN_PROJECT"] = "abm-agents"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

    client = Client()
    return client
```

### 8.4 Redis Event Bus

```python
# infrastructure/event_bus.py
import redis
import json
from typing import Callable

class EventBus:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()

    def publish(self, channel: str, event: AgentEvent):
        """Publish an event to a channel."""
        self.redis.publish(channel, json.dumps(event.model_dump()))

    def subscribe(self, channel: str, handler: Callable):
        """Subscribe to a channel with a handler function."""
        self.pubsub.subscribe(channel)
        for message in self.pubsub.listen():
            if message["type"] == "message":
                event_data = json.loads(message["data"])
                handler(event_data)

    def publish_to_agent(self, agent_name: str, event: AgentEvent):
        """Publish an event targeted at a specific agent."""
        self.publish(f"agent.{agent_name}", event)
```

### 8.5 Docker Compose for Local Development

```yaml
# docker-compose.yml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/abm
    depends_on:
      - redis
      - db

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=abm
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chromadata:/chroma/chroma

volumes:
  pgdata:
  chromadata:
```

### 8.6 Environment Configuration

```bash
# .env
OPENAI_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_...
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/abm

# CRM
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
SALESFORCE_USERNAME=...
SALESFORCE_PASSWORD=...

# Intent Data
SIXSENSE_API_KEY=...
DEMANDBASE_API_KEY=...

# Enrichment
CLEARBIT_API_KEY=...
ZOOMINFO_API_KEY=...

# Marketing Automation
HUBSPOT_API_KEY=...
MARKETO_CLIENT_ID=...
MARKETO_CLIENT_SECRET=...
```

---

## 9. Testing Strategy

### 9.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5 tests)
                    │  Tests  │
                   ┌┴─────────┴┐
                   │Integration│  (20 tests)
                   │  Tests    │
                  ┌┴───────────┴┐
                  │  Unit Tests  │  (100+ tests)
                  │              │
                  └──────────────┘
```

### 9.2 Unit Tests

```python
# tests/test_account_identification.py
import pytest
from unittest.mock import MagicMock, patch
from agents.account_identification import score_icp_fit

class TestICPScoring:
    def test_perfect_icp_match(self):
        account = {
            "industry": "Technology",
            "employee_count": 500,
            "annual_revenue": 50_000_000,
            "technologies": ["AWS", "Salesforce", "Snowflake"],
            "location": {"country": "US", "state": "CA"},
        }
        icp = {
            "target_industries": ["Technology"],
            "employee_range": {"min": 200, "max": 1000},
            "revenue_range": {"min": 10_000_000, "max": 100_000_000},
            "target_technologies": ["AWS", "Salesforce"],
            "target_regions": ["US"],
        }
        result = score_icp_fit(account, icp)
        assert result["total_score"] >= 80
        assert result["tier"] == "high"

    def test_poor_icp_match(self):
        account = {
            "industry": "Retail",
            "employee_count": 50,
            "annual_revenue": 5_000_000,
            "technologies": ["Shopify"],
            "location": {"country": "UK"},
        }
        icp = {
            "target_industries": ["Technology"],
            "employee_range": {"min": 200, "max": 1000},
            "revenue_range": {"min": 10_000_000, "max": 100_000_000},
            "target_technologies": ["AWS", "Salesforce"],
            "target_regions": ["US"],
        }
        result = score_icp_fit(account, icp)
        assert result["total_score"] < 50
        assert result["tier"] == "low"

    def test_empty_account_data(self):
        account = {}
        icp = {"target_industries": ["Technology"]}
        result = score_icp_fit(account, icp)
        assert result["total_score"] == 0
        assert result["tier"] == "low"
```

```python
# tests/test_intent_scoring.py
import pytest
from datetime import datetime, timedelta
from scoring.intent_scorer import calculate_intent_score

class TestIntentScoring:
    def test_high_intent_account(self):
        signals = [
            {"type": "pricing_page_visit", "topic": "data_security", "timestamp": datetime.utcnow() - timedelta(days=2)},
            {"type": "demo_request", "topic": "data_security", "timestamp": datetime.utcnow() - timedelta(days=1)},
            {"type": "whitepaper_download", "topic": "data_security", "timestamp": datetime.utcnow() - timedelta(days=5)},
            {"type": "third_party_topic_surge", "topic": "data_security", "timestamp": datetime.utcnow() - timedelta(days=3)},
        ]
        result = calculate_intent_score(signals, ["data_security"])
        assert result.overall_score >= 70
        assert result.buying_stage == "decision"
        assert result.trend == "rising"

    def test_low_intent_account(self):
        signals = [
            {"type": "email_open", "topic": "general", "timestamp": datetime.utcnow() - timedelta(days=60)},
        ]
        result = calculate_intent_score(signals, ["data_security"])
        assert result.overall_score < 30
        assert result.confidence < 0.5

    def test_recency_weighting(self):
        """Recent signals should score higher than old signals."""
        recent_signals = [
            {"type": "pricing_page_visit", "topic": "security", "timestamp": datetime.utcnow() - timedelta(days=1)},
        ]
        old_signals = [
            {"type": "pricing_page_visit", "topic": "security", "timestamp": datetime.utcnow() - timedelta(days=60)},
        ]
        recent_result = calculate_intent_score(recent_signals, ["security"])
        old_result = calculate_intent_score(old_signals, ["security"])
        assert recent_result.overall_score > old_result.overall_score
```

```python
# tests/test_channel_optimizer.py
import pytest
from orchestration.channel_optimizer import optimize_channel_mix

class TestChannelOptimizer:
    def test_budget_allocation(self):
        result = optimize_channel_mix(
            budget=10000,
            intent_score=80,
            buying_stage="decision",
            stakeholder_count=5,
            duration_days=90
        )
        total_cost = sum(
            result[ch] * CHANNEL_COSTS[ch] for ch in result
        )
        assert total_cost <= 10000

    def test_high_intent_gets_more_touchpoints(self):
        high_intent = optimize_channel_mix(
            budget=5000, intent_score=90, buying_stage="decision",
            stakeholder_count=5, duration_days=90
        )
        low_intent = optimize_channel_mix(
            budget=5000, intent_score=20, buying_stage="awareness",
            stakeholder_count=5, duration_days=90
        )
        assert sum(high_intent.values()) >= sum(low_intent.values())

    def test_frequency_cap_compliance(self):
        result = optimize_channel_mix(
            budget=10000, intent_score=80, buying_stage="consideration",
            stakeholder_count=3, duration_days=30
        )
        max_touches = 3 * (30 // 7) * 3  # 3 per week * ~4 weeks * 3 stakeholders
        for channel, count in result.items():
            assert count <= max_touches * 3  # Some buffer
```

### 9.3 Integration Tests

```python
# tests/integration/test_pipeline.py
import pytest
from langgraph.graph import StateGraph
from orchestrator import build_orchestrator

class TestABMPipeline:
    @pytest.fixture
    def orchestrator(self):
        return build_orchestrator()

    def test_full_pipeline_execution(self, orchestrator):
        """Test the full ABM pipeline from account identification to analytics."""
        initial_state = {
            "target_icp": {
                "industries": ["Technology"],
                "employee_range": {"min": 200, "max": 2000},
                "revenue_range": {"min": 10_000_000, "max": 500_000_000},
            },
            "campaign_budget": 50000,
            "campaign_duration_days": 90,
            "identified_accounts": [],
            "intent_scores": {},
            "committee_maps": {},
            "personalized_content": [],
            "channel_plans": [],
            "performance_reports": [],
            "current_stage": "identify_accounts",
            "errors": [],
        }

        result = orchestrator.invoke(initial_state)

        assert result["current_stage"] == "analyze_performance"
        assert len(result["identified_accounts"]) > 0
        assert len(result["intent_scores"]) > 0
        assert len(result["committee_maps"]) > 0
        assert len(result["personalized_content"]) > 0
        assert len(result["channel_plans"]) > 0
        assert len(result["errors"]) == 0

    def test_pipeline_error_handling(self, orchestrator):
        """Test that pipeline handles agent failures gracefully."""
        initial_state = {
            "target_icp": {},  # Empty ICP should trigger validation
            "campaign_budget": -1000,  # Invalid budget
            "campaign_duration_days": 90,
            "identified_accounts": [],
            "intent_scores": {},
            "committee_maps": {},
            "personalized_content": [],
            "channel_plans": [],
            "performance_reports": [],
            "current_stage": "identify_accounts",
            "errors": [],
        }

        result = orchestrator.invoke(initial_state)
        assert len(result["errors"]) > 0
```

### 9.4 E2E Tests

```python
# tests/e2e/test_campaign_lifecycle.py
import pytest
import requests
import time

class TestCampaignLifecycle:
    BASE_URL = "http://localhost:8000"

    def test_create_and_monitor_campaign(self):
        """E2E: Create a campaign and monitor it through all stages."""
        # Create campaign
        response = requests.post(f"{self.BASE_URL}/campaigns", json={
            "icp_criteria": {
                "industries": ["Technology", "Financial Services"],
                "employee_range": {"min": 500, "max": 5000},
                "revenue_range": {"min": 50_000_000, "max": 1_000_000_000},
            },
            "budget": 100000,
            "duration_days": 90,
            "intent_topics": ["data security", "cloud migration", "compliance"],
            "content_types": ["email_sequence", "ad_copy", "landing_page"],
        })
        assert response.status_code == 200
        campaign_id = response.json()["campaign_id"]

        # Poll for completion (with timeout)
        max_wait = 300  # 5 minutes
        start = time.time()
        while time.time() - start < max_wait:
            status = requests.get(f"{self.BASE_URL}/campaigns/{campaign_id}")
            data = status.json()
            if data["status"] in ["completed", "failed"]:
                break
            time.sleep(5)

        assert data["status"] == "completed"

        # Verify analytics
        analytics = requests.get(f"{self.BASE_URL}/campaigns/{campaign_id}/analytics")
        assert analytics.status_code == 200
        analytics_data = analytics.json()
        assert "aggregate_metrics" in analytics_data
        assert "roi_summary" in analytics_data
```

### 9.5 Test Execution Commands

```bash
# Run all unit tests
pytest tests/ -v --tb=short

# Run with coverage
pytest tests/ --cov=agents --cov=scoring --cov=orchestration --cov-report=html

# Run integration tests only
pytest tests/integration/ -v

# Run E2E tests (requires running server)
pytest tests/e2e/ -v

# Run specific agent tests
pytest tests/test_account_identification.py -v
pytest tests/test_intent_scoring.py -v
pytest tests/test_channel_optimizer.py -v

# Run with LangSmith tracing enabled
LANGCHAIN_TRACING_V2=true pytest tests/ -v
```

### 9.6 Mock Data Fixtures

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_account():
    return {
        "id": "acc_12345",
        "name": "Acme Corp",
        "domain": "acme.com",
        "industry": "Technology",
        "employee_count": 750,
        "annual_revenue": 120_000_000,
        "technologies": ["AWS", "Salesforce", "Snowflake", "Datadog"],
        "location": {"country": "US", "state": "CA", "city": "San Francisco"},
        "founded": 2015,
        "funding": {"total": 50_000_000, "last_round": "Series C"},
    }

@pytest.fixture
def sample_intent_signals():
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    return [
        {"type": "pricing_page_visit", "topic": "data_security", "timestamp": now - timedelta(days=2)},
        {"type": "whitepaper_download", "topic": "data_security", "timestamp": now - timedelta(days=5)},
        {"type": "webinar_attendance", "topic": "compliance", "timestamp": now - timedelta(days=10)},
        {"type": "email_click", "topic": "data_security", "timestamp": now - timedelta(days=1)},
    ]

@pytest.fixture
def sample_committee():
    return {
        "stakeholders": [
            {"name": "Jane Smith", "title": "CISO", "role": "economic_buyer", "influence_score": 90},
            {"name": "Bob Johnson", "title": "VP Engineering", "role": "decision_maker", "influence_score": 80},
            {"name": "Alice Chen", "title": "Security Manager", "role": "champion", "influence_score": 70},
            {"name": "Charlie Brown", "title": "Security Architect", "role": "influencer", "influence_score": 60},
        ]
    }
```

---

## Appendix: Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- Set up project structure, dependencies, and Docker environment
- Implement shared infrastructure (event bus, context store, tracing)
- Build orchestrator state machine
- Create mock data and test fixtures

### Phase 2: Core Agents (Weeks 3-5)
- Implement Account Identification Agent
- Implement Intent Scoring Agent
- Implement Committee Mapper Agent
- Write unit tests for each agent

### Phase 3: Content & Channels (Weeks 6-8)
- Implement Content Personalization Agent
- Implement Channel Orchestrator Agent
- Build content generation templates
- Write integration tests

### Phase 4: Analytics & Optimization (Weeks 9-10)
- Implement Performance Analytics Agent
- Build attribution models
- Create dashboard and reporting
- Write E2E tests

### Phase 5: Production Hardening (Weeks 11-12)
- Add error handling and retry logic
- Implement rate limiting and circuit breakers
- Set up monitoring and alerting
- Performance testing and optimization
- Documentation and deployment guides

---

*Document generated: 2026-10-01*
*Version: 1.0*
*Author: Ahmed Hassan — ABM Implementation Plan*
