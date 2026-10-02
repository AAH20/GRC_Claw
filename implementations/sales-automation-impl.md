# AI-Powered Sales Automation Implementation Plan

## LangChain DeepAgents Architecture

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Prospecting Agent](#2-prospecting-agent-implementation)
3. [Outreach Agent](#3-outreach-agent-implementation)
4. [Qualification Agent](#4-qualification-agent-implementation)
5. [Demo Scheduling Agent](#5-demo-scheduling-agent-implementation)
6. [Follow-up Agent](#6-follow-up-agent-implementation)
7. [Sales Forecasting Agent](#7-sales-forecasting-agent-implementation)
8. [CRM Integration](#8-crm-integration)
9. [Code Examples and Snippets](#9-code-examples-and-snippets)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Design

The sales automation system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. Each agent is a specialized LLM-powered worker with its own tools, prompts, and state management. A central **Sales Orchestrator** coordinates the pipeline and routes leads between agents.

```
┌─────────────────────────────────────────────────────────────┐
│                    Sales Orchestrator                        │
│  (LangGraph StateGraph + DeepAgents)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Prospecting│→ │ Outreach │→ │Qualifica-│→ │  Demo    │  │
│  │  Agent    │  │  Agent   │  │tion Agent│  │Scheduling│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│       ↑                                            │        │
│       │         ┌──────────┐                       ↓        │
│       └─────────│ Follow-up│←───────────────────────┘        │
│                 │  Agent   │                                │
│                 └──────────┘                                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Sales Forecasting Agent                      │  │
│  │     (Async — runs on schedule, not in pipeline)        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Shared: CRM Integration Layer + Vector Store + Event Bus   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents + LangGraph | Multi-agent orchestration, state management |
| LLM | GPT-4o / Claude 3.5 Sonnet | Reasoning, generation, classification |
| Vector Store | Pinecone / Weaviate | Lead embedding, similarity search, RAG |
| Task Queue | Celery + Redis | Async task execution, retry logic |
| CRM | Salesforce / HubSpot API | Lead data, opportunity tracking |
| Communication | SendGrid (email), Twilio (SMS/voice) | Multi-channel outreach |
| Calendar | Google Calendar API / Calendly | Demo scheduling |
| Monitoring | LangSmith + OpenTelemetry | Tracing, evaluation, observability |
| Storage | PostgreSQL + S3 | Structured data, document storage |

### 1.3 Agent Communication Protocol

Agents communicate via a **typed event bus** using Pydantic models:

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any

class LeadStatus(str, Enum):
    NEW = "new"
    PROSPECTED = "prospected"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    DEMO_SCHEDULED = "demo_scheduled"
    FOLLOW_UP = "follow_up"
    CONVERTED = "converted"
    DISQUALIFIED = "disqualified"

class LeadEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    source_agent: str
    target_agent: str
    event_type: str  # "lead_created", "outreach_sent", "qualified", etc.
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class Lead(BaseModel):
    lead_id: str
    name: str
    email: str
    company: str
    title: Optional[str] = None
    phone: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW
    score: float = 0.0
    source: str = ""
    notes: List[str] = []
    custom_fields: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 1.4 State Management with LangGraph

```python
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated

class SalesPipelineState(TypedDict):
    lead: Lead
    messages: Annotated[list, add_messages]
    current_agent: str
    qualification_result: Optional[Dict[str, Any]]
    demo_slot: Optional[str]
    outreach_history: List[Dict[str, Any]]
    follow_up_count: int
    next_action: str
    error: Optional[str]

# Build the state graph
workflow = StateGraph(SalesPipelineState)

# Add agent nodes
workflow.add_node("prospecting", prospecting_agent_node)
workflow.add_node("outreach", outreach_agent_node)
workflow.add_node("qualification", qualification_agent_node)
workflow.add_node("demo_scheduling", demo_scheduling_agent_node)
workflow.add_node("follow_up", follow_up_agent_node)
workflow.add_node("forecasting", forecasting_agent_node)

# Define edges (pipeline flow)
workflow.set_entry_point("prospecting")
workflow.add_edge("prospecting", "outreach")
workflow.add_edge("outreach", "qualification")
workflow.add_conditional_edges(
    "qualification",
    lambda state: state["next_action"],
    {
        "schedule_demo": "demo_scheduling",
        "follow_up": "follow_up",
        "disqualified": END,
        "converted": END,
    }
)
workflow.add_edge("demo_scheduling", "follow_up")
workflow.add_edge("follow_up", END)

# Compile
app = workflow.compile(checkpointer=MemorySaver())
```

---

## 2. Prospecting Agent Implementation

### 2.1 Purpose

The Prospecting Agent identifies and qualifies potential leads from multiple sources: web forms, LinkedIn, inbound inquiries, purchased lists, and website visitors. It enriches lead data and scores prospects.

### 2.2 Agent Definition

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

class ProspectingAgent:
    """Identifies, enriches, and scores potential leads."""

    def __init__(self, llm=None, crm_client=None, clearbit_client=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.crm = crm_client
        self.clearbit = clearbit_client
        self.tools = self._build_tools()
        self.agent = self._build_agent()

    def _build_tools(self) -> list[Tool]:
        return [
            Tool(
                name="enrich_lead",
                description="Enrich lead data with company info, technographics, and social profiles using Clearbit/ZoomInfo",
                func=self._enrich_lead,
            ),
            Tool(
                name="score_lead",
                description="Score a lead 0-100 based on ICP fit, intent signals, and engagement history",
                func=self._score_lead,
            ),
            Tool(
                name="search_linkedin",
                description="Search for prospects matching ICP criteria on LinkedIn Sales Navigator",
                func=self._search_linkedin,
            ),
            Tool(
                name="check_existing_lead",
                description="Check if lead already exists in CRM to avoid duplicates",
                func=self._check_existing_lead,
            ),
            Tool(
                name="create_crm_lead",
                description="Create a new lead record in CRM with enriched data",
                func=self._create_crm_lead,
            ),
            Tool(
                name="detect_intent",
                description="Analyze website behavior and content consumption to detect buying intent",
                func=self._detect_intent,
            ),
        ]

    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert B2B sales prospecting agent.
Your goal is to identify high-value prospects that match our Ideal Customer Profile (ICP).

ICP Criteria:
- Company size: 50-1000 employees
- Industry: SaaS, Fintech, Healthcare, E-commerce
- Geography: US, UK, EU
- Technology: Uses cloud infrastructure (AWS/GCP/Azure)
- Budget signal: Raised funding in last 18 months OR showing hiring growth

Process:
1. Analyze the lead information provided
2. Enrich with available data sources
3. Score the lead 0-100
4. If score >= 60, create in CRM and pass to outreach
5. If score < 60, mark as nurture/disqualified

Always verify the lead doesn't already exist in CRM before creating."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    def _enrich_lead(self, lead_data: dict) -> dict:
        """Enrich lead with Clearbit data."""
        if not self.clearbit:
            return lead_data

        try:
            company = self.clearbit.enrichment.find(
                domain=lead_data.get("email", "").split("@")[-1],
                stream=True
            )
            if company:
                lead_data["company_size"] = company.get("metrics", {}).get("employees")
                lead_data["industry"] = company.get("category", {}).get("industry")
                lead_data["annual_revenue"] = company.get("metrics", {}).get("estimatedAnnualRevenue")
                lead_data["technologies"] = company.get("tech", [])
                lead_data["linkedin_url"] = company.get("linkedin", {}).get("handle")
        except Exception as e:
            logger.warning(f"Enrichment failed: {e}")

        return lead_data

    def _score_lead(self, lead_data: dict) -> float:
        """Score lead based on ICP fit using LLM."""
        scoring_prompt = f"""
        Score this lead from 0-100 based on ICP fit.
        
        Lead: {json.dumps(lead_data)}
        
        Scoring weights:
        - Company size match: 25%
        - Industry match: 20%
        - Technology fit: 15%
        - Intent signals: 20%
        - Engagement level: 10%
        - Geographic fit: 10%
        
        Return ONLY a JSON object: {{"score": <float>, "reasons": [<string>], "recommendation": <"pursue"|"nurture"|"disqualify">}}
        """
        response = self.llm.invoke(scoring_prompt)
        result = json.loads(response.content)
        return result

    def _search_linkedin(self, criteria: str) -> list:
        """Search LinkedIn Sales Navigator for prospects."""
        # Integration with LinkedIn Sales Navigator API
        # Returns list of prospect profiles
        pass

    def _check_existing_lead(self, email: str) -> Optional[dict]:
        """Check CRM for existing lead by email."""
        if not self.crm:
            return None
        return self.crm.search_leads(f"email = '{email}'")

    def _create_crm_lead(self, lead_data: dict) -> dict:
        """Create lead in CRM."""
        if not self.crm:
            return {"status": "mock_created", "lead_id": str(uuid.uuid4())}
        return self.crm.create_lead(lead_data)

    def _detect_intent(self, lead_id: str) -> dict:
        """Analyze intent signals from website behavior."""
        # Integrate with analytics platform (Google Analytics, Mixpanel, etc.)
        pass

    def run(self, input_data: dict) -> dict:
        """Execute prospecting workflow."""
        result = self.agent.invoke({
            "input": f"Process this lead for prospecting: {json.dumps(input_data)}"
        })
        return result
```

### 2.3 Prospecting Data Sources

| Source | Method | Frequency |
|--------|--------|-----------|
| Web forms | Webhook → API | Real-time |
| LinkedIn Sales Navigator | API + scraping (compliant) | Daily batch |
| Website visitors | Clearbit Reveal / 6sense | Real-time |
| Purchased lists | CSV upload → enrichment pipeline | Weekly |
| Product-qualified leads | Product analytics webhook | Real-time |
| Referrals | CRM referral tracking | Event-driven |

---

## 3. Outreach Agent Implementation

### 3.1 Purpose

The Outreach Agent crafts personalized multi-channel outreach sequences (email, LinkedIn, phone) and manages send timing for maximum engagement.

### 3.2 Agent Definition

```python
class OutreachAgent:
    """Manages personalized multi-channel outreach campaigns."""

    def __init__(self, llm=None, sendgrid_client=None, linkedin_client=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.sendgrid = sendgrid_client
        self.linkedin = linkedin_client
        self.tools = self._build_tools()
        self.agent = self._build_agent()

    def _build_tools(self) -> list[Tool]:
        return [
            Tool(
                name="craft_email",
                description="Generate a personalized outreach email based on lead profile and context",
                func=self._craft_email,
            ),
            Tool(
                name="craft_linkedin_message",
                description="Generate a personalized LinkedIn connection request or InMail",
                func=self._craft_linkedin_message,
            ),
            Tool(
                name="send_email",
                description="Send an email via SendGrid with tracking",
                func=self._send_email,
            ),
            Tool(
                name="send_linkedin",
                description="Send a LinkedIn message via API",
                func=self._send_linkedin,
            ),
            Tool(
                name="schedule_follow_up",
                description="Schedule a follow-up touchpoint if no response",
                func=self._schedule_follow_up,
            ),
            Tool(
                name="check_engagement",
                description="Check if lead has opened/clicked previous outreach",
                func=self._check_engagement,
            ),
            Tool(
                name="optimize_send_time",
                description="Determine optimal send time based on lead timezone and past engagement",
                func=self._optimize_send_time,
            ),
        ]

    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert B2B sales outreach agent.
Your goal is to craft highly personalized outreach that drives responses.

Principles:
- Personalization: Reference specific company news, mutual connections, or pain points
- Value-first: Lead with insight, not a pitch
- Concise: Keep emails under 150 words, LinkedIn messages under 300 characters
- Clear CTA: One specific, low-friction call to action
- Multi-touch: Plan sequences of 3-5 touches across channels

Tone: Professional but conversational. Never pushy or salesy.

Sequence Template:
- Day 0: Email (personalized intro + value prop)
- Day 2: LinkedIn connection request (if email not opened)
- Day 4: Email (case study or social proof)
- Day 7: LinkedIn message (if connected)
- Day 10: Breakup email (curiosity-driven)

Adapt based on engagement signals."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True,
        )

    def _craft_email(self, lead: dict, context: dict, tone: str = "professional") -> dict:
        """Generate personalized email using LLM."""
        email_prompt = f"""
        Write a personalized outreach email for:
        
        Lead: {lead['name']}, {lead['title']} at {lead['company']}
        Industry: {lead.get('industry', 'Unknown')}
        Company size: {lead.get('company_size', 'Unknown')}
        Context: {context}
        Tone: {tone}
        
        Requirements:
        - Subject line: Curiosity-driven, under 50 characters
        - Opening: Personalized hook (reference something specific)
        - Body: 2-3 sentences max, value-first
        - CTA: One specific ask (15-min call, reply with interest, etc.)
        - Signature: Professional but human
        
        Return JSON: {{"subject": "...", "body": "...", "preview_text": "..."}}
        """
        response = self.llm.invoke(email_prompt)
        return json.loads(response.content)

    def _craft_linkedin_message(self, lead: dict, context: dict) -> str:
        """Generate LinkedIn message."""
        linkedin_prompt = f"""
        Write a LinkedIn connection request (300 chars max) or InMail for:
        Lead: {lead['name']}, {lead['title']} at {lead['company']}
        Context: {context}
        
        For connection requests: Find common ground, keep it short.
        For InMail: Subject line + 2-3 sentence message with clear value.
        """
        response = self.llm.invoke(linkedin_prompt)
        return response.content

    def _send_email(self, to_email: str, email_data: dict, lead_id: str) -> dict:
        """Send email via SendGrid."""
        if not self.sendgrid:
            return {"status": "mock_sent", "message_id": str(uuid.uuid4())}

        message = Mail(
            from_email=Email("sales@yourcompany.com"),
            to_emails=To(to_email),
            subject=email_data["subject"],
            html_content=self._build_html_email(email_data),
        )
        message.custom_args = {"lead_id": lead_id, "campaign_id": email_data.get("campaign_id", "")}

        response = self.sendgrid.send(message)
        return {
            "status": "sent" if response.status_code == 202 else "failed",
            "message_id": response.headers.get("X-Message-Id"),
        }

    def _send_linkedin(self, lead: dict, message: str) -> dict:
        """Send LinkedIn message via API."""
        if not self.linkedin:
            return {"status": "mock_sent"}
        return self.linkedin.send_message(lead["linkedin_url"], message)

    def _schedule_follow_up(self, lead_id: str, delay_days: int, channel: str) -> dict:
        """Schedule a follow-up task."""
        task = {
            "lead_id": lead_id,
            "scheduled_at": (datetime.utcnow() + timedelta(days=delay_days)).isoformat(),
            "channel": channel,
            "task_type": "follow_up",
        }
        # Push to Celery task queue
        send_follow_up.apply_async(args=[task], countdown=delay_days * 86400)
        return task

    def _check_engagement(self, lead_id: str) -> dict:
        """Check email engagement via SendGrid webhooks."""
        # Query engagement data from database
        pass

    def _optimize_send_time(self, lead: dict) -> str:
        """Determine optimal send time using historical data."""
        # Analyze past engagement patterns
        timezone = lead.get("timezone", "US/Eastern")
        # ML model or heuristic-based optimization
        return "10:00"  # Default: 10 AM in lead's timezone

    def _build_html_email(self, email_data: dict) -> str:
        """Build HTML email template."""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <p>{email_data['body']}</p>
            <br>
            <p>Best regards,<br>Sales Team</p>
            <img src="https://track.yourcompany.com/open?lead_id={{lead_id}}" width="1" height="1" />
        </body>
        </html>
        """

    def run(self, lead: dict, sequence_config: dict = None) -> dict:
        """Execute outreach workflow for a lead."""
        result = self.agent.invoke({
            "input": f"Create and execute outreach sequence for lead: {json.dumps(lead)}"
        })
        return result
```

### 3.3 Outreach Sequence Templates

```python
OUTSEQUENCE_TEMPLATES = {
    "cold_outbound": [
        {"day": 0, "channel": "email", "type": "intro", "goal": "get_reply"},
        {"day": 2, "channel": "linkedin", "type": "connection", "goal": "connect"},
        {"day": 4, "channel": "email", "type": "value_add", "goal": "provide_value"},
        {"day": 7, "channel": "linkedin", "type": "message", "goal": "engage"},
        {"day": 10, "channel": "email", "type": "breakup", "goal": "curiosity"},
    ],
    "warm_inbound": [
        {"day": 0, "channel": "email", "type": "response", "goal": "acknowledge"},
        {"day": 1, "channel": "email", "type": "value_prop", "goal": "educate"},
        {"day": 3, "channel": "email", "type": "case_study", "goal": "social_proof"},
        {"day": 5, "channel": "email", "type": "cta", "goal": "book_meeting"},
    ],
    "event_triggered": [
        {"day": 0, "channel": "email", "type": "congratulations", "goal": "celebrate"},
        {"day": 1, "channel": "email", "type": "relevant_insight", "goal": "add_value"},
        {"day": 3, "channel": "email", "type": "soft_ask", "goal": "start_conversation"},
    ],
}
```

---

## 4. Qualification Agent Implementation

### 4.1 Purpose

The Qualification Agent conducts BANT/MEDDIC qualification through conversational AI, determining whether a lead is worth pursuing and routing accordingly.

### 4.2 Agent Definition

```python
class QualificationAgent:
    """Qualifies leads using BANT/MEDDIC framework via conversational AI."""

    def __init__(self, llm=None, crm_client=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.crm = crm_client
        self.tools = self._build_tools()
        self.agent = self._build_agent()

    def _build_tools(self) -> list[Tool]:
        return [
            Tool(
                name="ask_qualifying_question",
                description="Ask the lead a qualifying question via email or chat",
                func=self._ask_qualifying_question,
            ),
            Tool(
                name="analyze_response",
                description="Analyze lead's response for qualification signals",
                func=self._analyze_response,
            ),
            Tool(
                name="check_budget_authority",
                description="Research lead's company for budget and authority signals",
                func=self._check_budget_authority,
            ),
            Tool(
                name="update_crm_qualification",
                description="Update CRM with qualification data and score",
                func=self._update_crm_qualification,
            ),
            Tool(
                name="calculate_deal_size",
                description="Estimate potential deal size based on company profile",
                func=self._calculate_deal_size,
            ),
        ]

    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert B2B sales qualification agent.
Your goal is to qualify leads using the MEDDIC framework:

- Metrics: What quantitative impact does the prospect need?
- Economic Buyer: Who controls the budget?
- Decision Criteria: What are their evaluation criteria?
- Decision Process: What is their buying process?
- Identify Pain: What is their core pain point?
- Champion: Who will advocate for us internally?

Qualification Levels:
- A (Ready to buy): All criteria met, urgent timeline, budget confirmed
- B (Nurture): Some criteria met, timeline > 90 days, budget unclear
- C (Disqualified): Doesn't meet ICP, no budget, no authority

Process:
1. Review lead context and any prior conversations
2. Ask targeted qualifying questions (max 3 at a time)
3. Analyze responses for signals
4. Assign qualification level
5. Route: A → Demo Scheduling, B → Follow-up/Nurture, C → Disqualified

Be conversational, not interrogatory. Build rapport while gathering info."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=20,
            handle_parsing_errors=True,
        )

    def _ask_qualifying_question(self, lead: dict, question_type: str) -> dict:
        """Generate and send a qualifying question."""
        question_prompt = f"""
        Generate a qualifying question for {lead['name']} at {lead['company']}.
        Question type: {question_type}
        
        Context: {lead.get('notes', [])}
        
        Make it conversational, not like a form. One question per message.
        """
        response = self.llm.invoke(question_prompt)
        return {
            "question": response.content,
            "type": question_type,
            "sent_at": datetime.utcnow().isoformat(),
        }

    def _analyze_response(self, response: str, qualification_criteria: dict) -> dict:
        """Analyze lead response for qualification signals."""
        analysis_prompt = f"""
        Analyze this lead response for qualification signals:
        
        Response: {response}
        Criteria: {qualification_criteria}
        
        Return JSON:
        {{
            "budget_signal": <"confirmed"|"likely"|"unclear"|"none">,
            "authority_signal": <"decision_maker"|"influencer"|"user"|"unknown">,
            "need_signal": <"urgent"|"planned"|"exploring"|"none">,
            "timeline_signal": <"<30_days"|"30-90_days"|"90+_days"|"unknown">,
            "overall_score": <0-100>,
            "key_insights": [<string>],
            "next_best_question": <"..."|null>
        }}
        """
        result = self.llm.invoke(analysis_prompt)
        return json.loads(result.content)

    def _check_budget_authority(self, lead: dict) -> dict:
        """Research budget and authority signals."""
        # Check funding history, job postings, tech stack
        signals = {
            "recent_funding": self._check_funding(lead["company"]),
            "hiring_growth": self._check_hiring(lead["company"]),
            "tech_stack": self._check_tech_stack(lead["company"]),
            "org_chart": self._get_org_info(lead["company"]),
        }
        return signals

    def _update_crm_qualification(self, lead_id: str, qualification_data: dict) -> dict:
        """Update CRM with qualification results."""
        if not self.crm:
            return {"status": "mock_updated"}
        return self.crm.update_lead(lead_id, {
            "qualification_status": qualification_data["level"],
            "qualification_score": qualification_data["score"],
            "qualification_data": qualification_data,
            "qualified_at": datetime.utcnow().isoformat(),
        })

    def _calculate_deal_size(self, lead: dict) -> dict:
        """Estimate deal size."""
        # Based on company size, industry, and typical ACV
        company_size = lead.get("company_size", "unknown")
        industry = lead.get("industry", "unknown")
        
        # Pricing model lookup
        pricing = {
            "SaaS": {"50-200": 15000, "200-500": 35000, "500-1000": 75000},
            "Fintech": {"50-200": 25000, "200-500": 50000, "500-1000": 100000},
        }
        
        return {
            "estimated_acv": pricing.get(industry, {}).get(company_size, 25000),
            "confidence": "medium",
        }

    def run(self, lead: dict, conversation_history: list = None) -> dict:
        """Execute qualification workflow."""
        result = self.agent.invoke({
            "input": f"Qualify this lead: {json.dumps(lead)}"
        })
        return result
```

### 4.3 Qualification Scoring Model

```python
QUALIFICATION_WEIGHTS = {
    "budget": 0.25,
    "authority": 0.20,
    "need": 0.25,
    "timeline": 0.15,
    "champion": 0.15,
}

def calculate_qualification_score(signals: dict) -> float:
    """Calculate weighted qualification score."""
    score = 0.0
    
    # Budget scoring
    budget_map = {"confirmed": 1.0, "likely": 0.7, "unclear": 0.3, "none": 0.0}
    score += budget_map.get(signals.get("budget_signal"), 0) * QUALIFICATION_WEIGHTS["budget"]
    
    # Authority scoring
    authority_map = {"decision_maker": 1.0, "influencer": 0.6, "user": 0.3, "unknown": 0.0}
    score += authority_map.get(signals.get("authority_signal"), 0) * QUALIFICATION_WEIGHTS["authority"]
    
    # Need scoring
    need_map = {"urgent": 1.0, "planned": 0.7, "exploring": 0.4, "none": 0.0}
    score += need_map.get(signals.get("need_signal"), 0) * QUALIFICATION_WEIGHTS["need"]
    
    # Timeline scoring
    timeline_map = {"<30_days": 1.0, "30-90_days": 0.7, "90+_days": 0.3, "unknown": 0.0}
    score += timeline_map.get(signals.get("timeline_signal"), 0) * QUALIFICATION_WEIGHTS["timeline"]
    
    # Champion scoring
    champion_map = {"strong": 1.0, "moderate": 0.6, "weak": 0.2, "none": 0.0}
    score += champion_map.get(signals.get("champion_signal"), 0) * QUALIFICATION_WEIGHTS["champion"]
    
    return round(score * 100, 1)
```

---

## 5. Demo Scheduling Agent Implementation

### 5.1 Purpose

The Demo Scheduling Agent coordinates with qualified leads to book product demonstrations, handling calendar logistics, timezone coordination, and pre-demo preparation.

### 5.2 Agent Definition

```python
class DemoSchedulingAgent:
    """Schedules product demos with qualified leads."""

    def __init__(self, llm=None, google_calendar_client=None, calendly_client=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.2)
        self.google_calendar = google_calendar_client
        self.calendly = calendly_client
        self.tools = self._build_tools()
        self.agent = self._build_agent()

    def _build_tools(self) -> list[Tool]:
        return [
            Tool(
                name="check_availability",
                description="Check sales rep availability for demo slots",
                func=self._check_availability,
            ),
            Tool(
                name="propose_slots",
                description="Propose available time slots to the lead",
                func=self._propose_slots,
            ),
            Tool(
                name="book_demo",
                description="Book a demo slot and send calendar invite",
                func=self._book_demo,
            ),
            Tool(
                name="send_pre_demo_materials",
                description="Send pre-demo preparation materials to the lead",
                func=self._send_pre_demo_materials,
            ),
            Tool(
                name="reschedule_demo",
                description="Reschedule an existing demo",
                func=self._reschedule_demo,
            ),
            Tool(
                name="cancel_demo",
                description="Cancel a demo and notify all parties",
                func=self._cancel_demo,
            ),
            Tool(
                name="sync_calendar",
                description="Sync demo with CRM and rep calendars",
                func=self._sync_calendar,
            ),
        ]

    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert demo scheduling agent.
Your goal is to efficiently schedule product demos with qualified leads.

Process:
1. Check lead's timezone and preferences
2. Find available slots with appropriate sales reps
3. Propose 2-3 options (give choices, not open-ended)
4. Once confirmed, book and send calendar invite
5. Send pre-demo materials 24 hours before
6. Update CRM with demo details

Rules:
- Demos are 30 minutes (standard) or 45 minutes (enterprise)
- Available slots: Mon-Thu, 9 AM - 5 PM in lead's timezone
- Always offer at least 2 options
- Include agenda in calendar invite
- Send confirmation immediately after booking

Tone: Helpful, efficient, respectful of time."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True,
        )

    def _check_availability(self, rep_id: str, date_range: dict) -> list:
        """Check rep availability via Google Calendar API."""
        if not self.google_calendar:
            return self._mock_availability()

        events = self.google_calendar.events().list(
            calendarId="primary",
            timeMin=date_range["start"],
            timeMax=date_range["end"],
            singleEvents=True,
        ).execute()

        busy_slots = [(e["start"], e["end"]) for e in events.get("items", [])]
        available = self._find_free_slots(busy_slots, date_range)
        return available

    def _propose_slots(self, lead: dict, available_slots: list) -> dict:
        """Generate a message proposing available slots."""
        proposal_prompt = f"""
        Write a message to {lead['name']} proposing these demo time slots:
        {available_slots}
        
        Lead timezone: {lead.get('timezone', 'US/Eastern')}
        
        Keep it brief, offer 2-3 specific times, make it easy to pick one.
        """
        response = self.llm.invoke(proposal_prompt)
        return {
            "message": response.content,
            "proposed_slots": available_slots[:3],
        }

    def _book_demo(self, lead: dict, slot: dict, rep_id: str) -> dict:
        """Book demo and send calendar invite."""
        event = {
            "summary": f"Product Demo - {lead['company']}",
            "description": self._build_demo_agenda(lead),
            "start": {"dateTime": slot["start"], "timeZone": slot.get("timezone", "UTC")},
            "end": {"dateTime": slot["end"], "timeZone": slot.get("timezone", "UTC")},
            "attendees": [
                {"email": lead["email"], "displayName": lead["name"]},
                {"email": f"{rep_id}@yourcompany.com", "displayName": "Sales Rep"},
            ],
            "conferenceData": {
                "createRequest": {"requestId": str(uuid.uuid4()), "conferenceSolutionKey": {"type": "hangoutsMeet"}}
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 1440},  # 24 hours
                    {"method": "popup", "minutes": 30},
                ],
            },
        }

        if self.google_calendar:
            result = self.google_calendar.events().insert(
                calendarId="primary",
                body=event,
                conferenceDataVersion=1,
                sendUpdates="all",
            ).execute()
            return {"status": "booked", "event_id": result["id"], "meet_link": result.get("hangoutLink")}

        return {"status": "mock_booked", "event_id": str(uuid.uuid4())}

    def _send_pre_demo_materials(self, lead: dict, demo_details: dict) -> dict:
        """Send pre-demo preparation email."""
        materials_prompt = f"""
        Write a pre-demo email to {lead['name']} at {lead['company']}.
        
        Demo: {demo_details['summary']}
        Time: {demo_details['start']}
        
        Include:
        - Brief agenda
        - What to prepare (if anything)
        - Link to join
        - Contact info for questions
        """
        response = self.llm.invoke(materials_prompt)
        return {
            "subject": f"Pre-Demo Prep: {demo_details['summary']}",
            "body": response.content,
            "sent_at": datetime.utcnow().isoformat(),
        }

    def _reschedule_demo(self, event_id: str, new_slot: dict) -> dict:
        """Reschedule existing demo."""
        pass

    def _cancel_demo(self, event_id: str, reason: str) -> dict:
        """Cancel demo and notify."""
        pass

    def _sync_calendar(self, event_id: str, lead_id: str) -> dict:
        """Sync demo details to CRM."""
        pass

    def _build_demo_agenda(self, lead: dict) -> str:
        """Build personalized demo agenda."""
        return f"""
        Demo Agenda for {lead['name']} ({lead['company']})
        
        1. Introduction & Goals (5 min)
        2. Product Overview (10 min)
        3. Use Case Deep-Dive: {lead.get('use_case', 'General')} (10 min)
        4. Q&A (5 min)
        5. Next Steps (5 min)
        """

    def _find_free_slots(self, busy_slots: list, date_range: dict) -> list:
        """Find free time slots given busy periods."""
        # Implementation: find 30-min slots between 9-5, Mon-Thu
        pass

    def _mock_availability(self) -> list:
        """Return mock available slots for testing."""
        return [
            {"start": "2024-01-15T10:00:00", "end": "2024-01-15T10:30:00", "timezone": "US/Eastern"},
            {"start": "2024-01-15T14:00:00", "end": "2024-01-15T14:30:00", "timezone": "US/Eastern"},
            {"start": "2024-01-16T11:00:00", "end": "2024-01-16T11:30:00", "timezone": "US/Eastern"},
        ]

    def run(self, lead: dict) -> dict:
        """Execute demo scheduling workflow."""
        result = self.agent.invoke({
            "input": f"Schedule a demo for qualified lead: {json.dumps(lead)}"
        })
        return result
```

---

## 6. Follow-up Agent Implementation

### 6.1 Purpose

The Follow-up Agent manages post-demo and post-outreach follow-up sequences, nurturing leads that aren't ready to buy and re-engaging cold leads.

### 6.2 Agent Definition

```python
class FollowUpAgent:
    """Manages follow-up sequences and lead nurturing."""

    def __init__(self, llm=None, crm_client=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.crm = crm_client
        self.tools = self._build_tools()
        self.agent = self._build_agent()

    def _build_tools(self) -> list[Tool]:
        return [
            Tool(
                name="craft_follow_up",
                description="Generate a personalized follow-up message",
                func=self._craft_follow_up,
            ),
            Tool(
                name="analyze_engagement",
                description="Analyze lead engagement patterns to determine follow-up strategy",
                func=self._analyze_engagement,
            ),
            Tool(
                name="send_follow_up",
                description="Send follow-up message via appropriate channel",
                func=self._send_follow_up,
            ),
            Tool(
                name="schedule_next_touch",
                description="Schedule the next follow-up touchpoint",
                func=self._schedule_next_touch,
            ),
            Tool(
                name="update_lead_status",
                description="Update lead status in CRM based on engagement",
                func=self._update_lead_status,
            ),
            Tool(
                name="create_nurture_campaign",
                description="Add lead to a nurture campaign sequence",
                func=self._create_nurture_campaign,
            ),
        ]

    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert sales follow-up agent.
Your goal is to maintain engagement with leads and move them through the pipeline.

Follow-up Principles:
- Timing: Follow up within 24 hours of demo, 3 days after email
- Value: Each touchpoint should provide value, not just "checking in"
- Channel: Match the lead's preferred channel
- Frequency: Max 1 touch per week, respect opt-outs
- Personalization: Reference specific conversations or content

Follow-up Types:
1. Post-demo: Thank you + recap + next steps + relevant resources
2. No-response: Breakup email with curiosity hook
3. Nurture: Educational content, case studies, industry insights
4. Re-engagement: Trigger-based (funding, hiring, product update)

Decision Logic:
- If engaged (opened/clicked): Continue sequence, increase frequency slightly
- If unresponsive after 3 touches: Move to nurture campaign
- If negative response: Disqualify or move to long-term nurture
- If positive response: Route to demo scheduling or closing

Always track all touchpoints in CRM."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True,
        )

    def _craft_follow_up(self, lead: dict, context: dict, follow_up_type: str) -> dict:
        """Generate personalized follow-up message."""
        followup_prompt = f"""
        Write a {follow_up_type} follow-up message for:
        
        Lead: {lead['name']}, {lead['title']} at {lead['company']}
        Context: {context}
        Previous interactions: {lead.get('outreach_history', [])}
        
        Requirements:
        - Reference specific details from previous conversations
        - Provide value (insight, resource, or relevant update)
        - Clear but soft CTA
        - Keep it concise
        
        Return JSON: {{"subject": "...", "body": "...", "channel": "email|linkedin|phone"}}
        """
        response = self.llm.invoke(followup_prompt)
        return json.loads(response.content)

    def _analyze_engagement(self, lead_id: str) -> dict:
        """Analyze engagement patterns."""
        # Query email opens, clicks, website visits, content downloads
        engagement_data = {
            "email_opens": 0,
            "email_clicks": 0,
            "website_visits": 0,
            "content_downloads": 0,
            "last_engagement": None,
            "engagement_trend": "stable|increasing|decreasing",
        }
        return engagement_data

    def _send_follow_up(self, lead: dict, message: dict) -> dict:
        """Send follow-up via appropriate channel."""
        channel = message.get("channel", "email")
        if channel == "email":
            return self._send_email_follow_up(lead, message)
        elif channel == "linkedin":
            return self._send_linkedin_follow_up(lead, message)
        return {"status": "unsupported_channel"}

    def _schedule_next_touch(self, lead_id: str, delay_days: int, touch_type: str) -> dict:
        """Schedule next follow-up touch."""
        task = {
            "lead_id": lead_id,
            "scheduled_at": (datetime.utcnow() + timedelta(days=delay_days)).isoformat(),
            "touch_type": touch_type,
        }
        send_follow_up.apply_async(args=[task], countdown=delay_days * 86400)
        return task

    def _update_lead_status(self, lead_id: str, status: str, notes: str = "") -> dict:
        """Update lead status in CRM."""
        if not self.crm:
            return {"status": "mock_updated"}
        return self.crm.update_lead(lead_id, {
            "status": status,
            "last_follow_up": datetime.utcnow().isoformat(),
            "notes": notes,
        })

    def _create_nurture_campaign(self, lead_id: str, campaign_type: str) -> dict:
        """Add lead to nurture campaign."""
        campaigns = {
            "monthly_newsletter": "camp_monthly_news",
            "product_education": "camp_product_ed",
            "case_study_series": "camp_case_studies",
            "re_engagement": "camp_re_engage",
        }
        return {
            "lead_id": lead_id,
            "campaign_id": campaigns.get(campaign_type, "camp_general"),
            "enrolled_at": datetime.utcnow().isoformat(),
        }

    def run(self, lead: dict, trigger_event: str = None) -> dict:
        """Execute follow-up workflow."""
        result = self.agent.invoke({
            "input": f"Follow up with lead: {json.dumps(lead)}. Trigger: {trigger_event}"
        })
        return result
```

### 6.3 Follow-up Decision Tree

```python
FOLLOW_UP_DECISION_TREE = {
    "post_demo": {
        "timing": "24_hours",
        "actions": [
            "send_thank_you_email",
            "share_recap_document",
            "propose_next_steps",
        ],
        "if_no_response": {
            "day_3": "send_case_study",
            "day_7": "send_roi_calculator",
            "day_14": "breakup_email",
        },
    },
    "no_response_to_outreach": {
        "timing": "3_days",
        "actions": [
            "send_value_add_email",
            "try_different_channel",
        ],
        "if_no_response": {
            "day_7": "send_breakup_email",
            "day_14": "move_to_nurture",
        },
    },
    "nurture": {
        "timing": "weekly",
        "actions": [
            "share_relevant_content",
            "invite_to_webinar",
            "share_customer_story",
        ],
        "if_engaged": "reactivate_to_active",
    },
}
```

---

## 7. Sales Forecasting Agent Implementation

### 7.1 Purpose

The Sales Forecasting Agent analyzes pipeline data, historical performance, and market signals to predict revenue, identify at-risk deals, and recommend actions.

### 7.2 Agent Definition

```python
class ForecastingAgent:
    """Predicts sales outcomes and provides forecasting insights."""

    def __init__(self, llm=None, crm_client=None, analytics_client=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.crm = crm_client
        self.analytics = analytics_client
        self.tools = self._build_tools()
        self.agent = self._build_agent()

    def _build_tools(self) -> list[Tool]:
        return [
            Tool(
                name="analyze_pipeline",
                description="Analyze current pipeline health and progression",
                func=self._analyze_pipeline,
            ),
            Tool(
                name="predict_close_probability",
                description="Predict probability of closing for each open opportunity",
                func=self._predict_close_probability,
            ),
            Tool(
                name="identify_at_risk_deals",
                description="Identify deals that are stalling or at risk",
                func=self._identify_at_risk_deals,
            ),
            Tool(
                name="generate_forecast",
                description="Generate revenue forecast for the quarter",
                func=self._generate_forecast,
            ),
            Tool(
                name="recommend_actions",
                description="Recommend specific actions to improve forecast",
                func=self._recommend_actions,
            ),
            Tool(
                name="analyze_historical",
                description="Analyze historical win/loss patterns",
                func=self._analyze_historical,
            ),
        ]

    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert sales forecasting agent.
Your goal is to provide accurate revenue forecasts and actionable insights.

Forecasting Methodology:
1. Pipeline Analysis: Review all open opportunities
2. Stage-based Probability: Apply historical win rates by stage
3. Engagement Scoring: Factor in email engagement, meeting activity
4. Temporal Patterns: Consider seasonality, deal age, timeline
5. External Signals: Market conditions, competitor activity

Output:
- Committed forecast (high confidence)
- Best case forecast (medium confidence)
- Pipeline forecast (low confidence)
- At-risk deals with recommended actions
- Gap analysis vs. quota

Always provide confidence intervals and explain your reasoning."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}"),
        ])

        agent = create_openai_functions_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=20,
            handle_parsing_errors=True,
        )

    def _analyze_pipeline(self) -> dict:
        """Analyze current pipeline health."""
        pipeline = {
            "total_opportunities": 0,
            "total_value": 0,
            "by_stage": {},
            "by_rep": {},
            "avg_deal_size": 0,
            "avg_sales_cycle": 0,
            "health_score": 0,
        }
        # Query CRM for pipeline data
        return pipeline

    def _predict_close_probability(self, opportunity: dict) -> dict:
        """Predict close probability using ML model."""
        features = {
            "stage": opportunity["stage"],
            "deal_age_days": (datetime.utcnow() - opportunity["created_at"]).days,
            "engagement_score": opportunity.get("engagement_score", 0),
            "num_meetings": opportunity.get("num_meetings", 0),
            "num_emails": opportunity.get("num_emails", 0),
            "company_size": opportunity.get("company_size", "unknown"),
            "industry": opportunity.get("industry", "unknown"),
            "lead_source": opportunity.get("lead_source", "unknown"),
        }
        
        # ML model prediction (trained on historical data)
        probability = self._ml_predict(features)
        
        return {
            "opportunity_id": opportunity["id"],
            "close_probability": probability,
            "expected_close_date": self._predict_close_date(opportunity),
            "confidence": self._calculate_confidence(features),
        }

    def _identify_at_risk_deals(self) -> list:
        """Identify deals at risk of stalling or being lost."""
        at_risk = []
        # Criteria: no activity > 7 days, stage stagnation, negative signals
        return at_risk

    def _generate_forecast(self, period: str = "quarter") -> dict:
        """Generate revenue forecast."""
        forecast = {
            "period": period,
            "committed": 0,
            "best_case": 0,
            "pipeline": 0,
            "quota": 0,
            "gap": 0,
            "confidence_interval": {"low": 0, "high": 0},
        }
        return forecast

    def _recommend_actions(self, forecast: dict) -> list:
        """Recommend actions to improve forecast."""
        actions = []
        # Based on gap analysis, recommend specific actions
        return actions

    def _analyze_historical(self) -> dict:
        """Analyze historical win/loss patterns."""
        patterns = {
            "win_rate_by_stage": {},
            "win_rate_by_source": {},
            "avg_sales_cycle_by_deal_size": {},
            "seasonal_patterns": {},
        }
        return patterns

    def _ml_predict(self, features: dict) -> float:
        """ML model prediction for close probability."""
        # Load pre-trained model (XGBoost/LightGBM)
        # Return probability 0-1
        return 0.5  # Placeholder

    def _predict_close_date(self, opportunity: dict) -> str:
        """Predict expected close date."""
        # Based on stage, historical averages, engagement
        return (datetime.utcnow() + timedelta(days=30)).isoformat()

    def _calculate_confidence(self, features: dict) -> str:
        """Calculate confidence level in prediction."""
        return "medium"

    def run(self, period: str = "quarter") -> dict:
        """Execute forecasting workflow."""
        result = self.agent.invoke({
            "input": f"Generate sales forecast for {period}"
        })
        return result
```

### 7.3 Forecasting Model Features

```python
FORECASTING_FEATURES = {
    "deal_features": [
        "stage",
        "deal_age_days",
        "amount",
        "num_meetings",
        "num_emails_sent",
        "num_emails_opened",
        "num_calls",
        "num_demos",
        "num_proposals_sent",
        "days_in_current_stage",
        "days_since_last_activity",
    ],
    "lead_features": [
        "lead_score",
        "company_size",
        "industry",
        "lead_source",
        "engagement_score",
        "website_visits",
        "content_downloads",
    ],
    "temporal_features": [
        "month",
        "quarter",
        "is_quarter_end",
        "days_to_quarter_end",
    ],
    "external_features": [
        "market_sentiment",
        "competitor_mentions",
        "funding_events",
    ],
}
```

---

## 8. CRM Integration

### 8.1 CRM Adapter Pattern

```python
from abc import ABC, abstractmethod

class CRMAdapter(ABC):
    """Abstract base class for CRM integrations."""

    @abstractmethod
    def create_lead(self, lead_data: dict) -> dict:
        pass

    @abstractmethod
    def update_lead(self, lead_id: str, updates: dict) -> dict:
        pass

    @abstractmethod
    def get_lead(self, lead_id: str) -> dict:
        pass

    @abstractmethod
    def search_leads(self, query: str) -> list:
        pass

    @abstractmethod
    def create_opportunity(self, opp_data: dict) -> dict:
        pass

    @abstractmethod
    def update_opportunity(self, opp_id: str, updates: dict) -> dict:
        pass

    @abstractmethod
    def get_pipeline(self) -> list:
        pass

    @abstractmethod
    def log_activity(self, lead_id: str, activity: dict) -> dict:
        pass


class SalesforceAdapter(CRMAdapter):
    """Salesforce CRM integration."""

    def __init__(self, username: str, password: str, security_token: str, domain: str = "login"):
        from simple_salesforce import Salesforce
        self.sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )

    def create_lead(self, lead_data: dict) -> dict:
        sf_lead = {
            "FirstName": lead_data["name"].split()[0],
            "LastName": " ".join(lead_data["name"].split()[1:]) if len(lead_data["name"].split()) > 1 else ".",
            "Email": lead_data["email"],
            "Company": lead_data["company"],
            "Title": lead_data.get("title", ""),
            "Phone": lead_data.get("phone", ""),
            "Industry": lead_data.get("industry", ""),
            "NumberOfEmployees": self._parse_company_size(lead_data.get("company_size")),
            "LeadSource": lead_data.get("source", "AI Agent"),
            "Status": "Open - Not Contacted",
            "Description": f"Created by AI Prospecting Agent. Score: {lead_data.get('score', 'N/A')}",
            "Custom_Lead_Score__c": lead_data.get("score", 0),
        }
        result = self.sf.Lead.create(sf_lead)
        return {"id": result["id"], "status": "created"}

    def update_lead(self, lead_id: str, updates: dict) -> dict:
        sf_updates = {}
        if "status" in updates:
            sf_updates["Status"] = updates["status"]
        if "qualification_score" in updates:
            sf_updates["Qualification_Score__c"] = updates["qualification_score"]
        if "notes" in updates:
            sf_updates["Description"] = updates["notes"]
        
        self.sf.Lead.update(lead_id, sf_updates)
        return {"id": lead_id, "status": "updated"}

    def get_lead(self, lead_id: str) -> dict:
        return self.sf.Lead.get(lead_id)

    def search_leads(self, query: str) -> list:
        result = self.sf.query(f"SELECT Id, Name, Email FROM Lead WHERE {query}")
        return result["records"]

    def create_opportunity(self, opp_data: dict) -> dict:
        sf_opp = {
            "Name": opp_data["name"],
            "StageName": opp_data.get("stage", "Prospecting"),
            "CloseDate": opp_data.get("close_date", (datetime.utcnow() + timedelta(days=90)).strftime("%Y-%m-%d")),
            "Amount": opp_data.get("amount", 0),
            "AccountId": opp_data.get("account_id"),
            "LeadSource": opp_data.get("source", "AI Agent"),
        }
        result = self.sf.Opportunity.create(sf_opp)
        return {"id": result["id"], "status": "created"}

    def update_opportunity(self, opp_id: str, updates: dict) -> dict:
        self.sf.Opportunity.update(opp_id, updates)
        return {"id": opp_id, "status": "updated"}

    def get_pipeline(self) -> list:
        query = """
            SELECT Id, Name, StageName, Amount, CloseDate, Account.Name, Owner.Name
            FROM Opportunity
            WHERE IsClosed = false
        """
        return self.sf.query(query)["records"]

    def log_activity(self, lead_id: str, activity: dict) -> dict:
        task = {
            "WhoId": lead_id,
            "Subject": activity.get("subject", "AI Agent Activity"),
            "Description": activity.get("description", ""),
            "Status": "Completed",
            "Priority": "Normal",
            "ActivityDate": datetime.utcnow().strftime("%Y-%m-%d"),
        }
        result = self.sf.Task.create(task)
        return {"id": result["id"], "status": "logged"}

    def _parse_company_size(self, size_str: str) -> int:
        """Parse company size string to number."""
        if not size_str:
            return 0
        # Extract number from string like "50-200"
        import re
        numbers = re.findall(r'\d+', size_str)
        return int(numbers[0]) if numbers else 0


class HubSpotAdapter(CRMAdapter):
    """HubSpot CRM integration."""

    def __init__(self, api_key: str):
        from hubspot import Client
        self.client = Client.create(access_token=api_key)

    def create_lead(self, lead_data: dict) -> dict:
        contact = {
            "properties": {
                "email": lead_data["email"],
                "firstname": lead_data["name"].split()[0],
                "lastname": " ".join(lead_data["name"].split()[1:]) if len(lead_data["name"].split()) > 1 else "",
                "company": lead_data["company"],
                "jobtitle": lead_data.get("title", ""),
                "phone": lead_data.get("phone", ""),
                "industry": lead_data.get("industry", ""),
                "hs_lead_status": "NEW",
                "hs_analytics_source": "AI Agent",
            }
        }
        result = self.client.crm.contacts.basic_api.create(contact)
        return {"id": result.id, "status": "created"}

    def update_lead(self, lead_id: str, updates: dict) -> dict:
        properties = {}
        if "status" in updates:
            properties["hs_lead_status"] = updates["status"]
        if "qualification_score" in updates:
            properties["qualification_score"] = str(updates["qualification_score"])
        
        self.client.crm.contacts.basic_api.update(lead_id, {"properties": properties})
        return {"id": lead_id, "status": "updated"}

    def get_lead(self, lead_id: str) -> dict:
        return self.client.crm.contacts.basic_api.get_by_id(lead_id)

    def search_leads(self, query: str) -> list:
        # HubSpot search API
        pass

    def create_opportunity(self, opp_data: dict) -> dict:
        deal = {
            "properties": {
                "dealname": opp_data["name"],
                "dealstage": opp_data.get("stage", "appointmentscheduled"),
                "amount": str(opp_data.get("amount", 0)),
                "closedate": opp_data.get("close_date"),
                "hubspot_owner_id": opp_data.get("owner_id"),
            }
        }
        result = self.client.crm.deals.basic_api.create(deal)
        return {"id": result.id, "status": "created"}

    def update_opportunity(self, opp_id: str, updates: dict) -> dict:
        self.client.crm.deals.basic_api.update(opp_id, {"properties": updates})
        return {"id": opp_id, "status": "updated"}

    def get_pipeline(self) -> list:
        deals = self.client.crm.deals.get_all()
        return [d.to_dict() for d in deals]

    def log_activity(self, lead_id: str, activity: dict) -> dict:
        engagement = {
            "engagement": {"type": "TASK", "active": True},
            "metadata": {
                "subject": activity.get("subject", "AI Agent Activity"),
                "body": activity.get("description", ""),
            },
            "associations": {
                "contactIds": [lead_id],
            },
        }
        result = self.client.crm.engagements.basic_api.create(engagement)
        return {"id": result.id, "status": "logged"}
```

### 8.2 CRM Integration Configuration

```python
# config/crm_config.py

CRM_CONFIG = {
    "provider": "salesforce",  # or "hubspot"
    "salesforce": {
        "username": os.getenv("SF_USERNAME"),
        "password": os.getenv("SF_PASSWORD"),
        "security_token": os.getenv("SF_SECURITY_TOKEN"),
        "domain": os.getenv("SF_DOMAIN", "login"),
    },
    "hubspot": {
        "api_key": os.getenv("HUBSPOT_API_KEY"),
    },
    "sync": {
        "interval_minutes": 5,
        "batch_size": 100,
        "retry_attempts": 3,
        "webhook_secret": os.getenv("CRM_WEBHOOK_SECRET"),
    },
    "field_mapping": {
        "lead": {
            "name": "Name",
            "email": "Email",
            "company": "Company",
            "title": "Title",
            "phone": "Phone",
            "industry": "Industry",
            "company_size": "NumberOfEmployees",
            "score": "Custom_Lead_Score__c",
            "status": "Status",
            "source": "LeadSource",
        },
        "opportunity": {
            "name": "Name",
            "stage": "StageName",
            "amount": "Amount",
            "close_date": "CloseDate",
            "account": "AccountId",
            "owner": "OwnerId",
        },
    },
}
```

### 8.3 CRM Event Webhook Handler

```python
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

@app.post("/webhooks/crm")
async def handle_crm_webhook(request: Request):
    """Handle CRM webhook events (lead updates, opportunity changes)."""
    payload = await request.body()
    signature = request.headers.get("X-HubSpot-Signature", "")
    
    # Verify webhook signature
    if not verify_webhook(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    event = await request.json()
    
    # Process event based on type
    if event["subscriptionType"] == "contact.propertyChange":
        await handle_contact_update(event)
    elif event["subscriptionType"] == "deal.propertyChange":
        await handle_deal_update(event)
    
    return {"status": "processed"}

async def handle_contact_update(event: dict):
    """Process contact update from CRM."""
    contact_id = event["objectId"]
    changes = event["propertyChanges"]
    
    # Update local database
    # Trigger agent workflows if needed
    pass

async def handle_deal_update(event: dict):
    """Process deal update from CRM."""
    deal_id = event["objectId"]
    changes = event["propertyChanges"]
    
    # Update forecasting model
    # Notify relevant agents
    pass

def verify_webhook(payload: bytes, signature: str) -> bool:
    """Verify webhook signature."""
    secret = os.getenv("CRM_WEBHOOK_SECRET", "")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## 9. Code Examples and Snippets

### 9.1 Complete Pipeline Execution

```python
import asyncio
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

async def run_sales_pipeline(lead_input: dict):
    """Execute the complete sales automation pipeline."""
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    
    # Initialize CRM adapter
    crm = SalesforceAdapter(
        username=os.getenv("SF_USERNAME"),
        password=os.getenv("SF_PASSWORD"),
        security_token=os.getenv("SF_SECURITY_TOKEN"),
    )
    
    # Initialize agents
    prospecting = ProspectingAgent(llm=llm, crm_client=crm)
    outreach = OutreachAgent(llm=llm)
    qualification = QualificationAgent(llm=llm, crm_client=crm)
    demo_scheduling = DemoSchedulingAgent(llm=llm)
    follow_up = FollowUpAgent(llm=llm, crm_client=crm)
    
    # Step 1: Prospecting
    print("Step 1: Prospecting...")
    prospect_result = prospecting.run(lead_input)
    lead = Lead(**prospect_result["lead"])
    
    if lead.score < 60:
        print(f"Lead scored {lead.score}, below threshold. Moving to nurture.")
        return {"status": "nurture", "lead": lead}
    
    # Step 2: Outreach
    print("Step 2: Outreach...")
    outreach_result = outreach.run(lead.dict())
    
    # Step 3: Qualification
    print("Step 3: Qualification...")
    qual_result = qualification.run(lead.dict())
    
    if qual_result["level"] == "C":
        print("Lead disqualified.")
        return {"status": "disqualified", "lead": lead}
    
    # Step 4: Demo Scheduling (if qualified)
    if qual_result["level"] == "A":
        print("Step 4: Demo Scheduling...")
        demo_result = demo_scheduling.run(lead.dict())
        
        # Step 5: Follow-up
        print("Step 5: Follow-up...")
        follow_up_result = follow_up.run(lead.dict(), trigger_event="post_demo")
    
    return {
        "status": "completed",
        "lead": lead,
        "qualification": qual_result,
        "demo": demo_result if qual_result["level"] == "A" else None,
    }

# Run pipeline
if __name__ == "__main__":
    result = asyncio.run(run_sales_pipeline({
        "name": "Jane Smith",
        "email": "jane@techcorp.com",
        "company": "TechCorp",
        "title": "VP of Engineering",
    }))
    print(json.dumps(result, indent=2, default=str))
```

### 9.2 Agent Tool Decorator Pattern

```python
from functools import wraps
from typing import Callable, Any
import time
import logging

logger = logging.getLogger(__name__)

def tool_with_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator for agent tools with retry logic."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Tool {func.__name__} failed (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        raise
            return None
        return wrapper
    return decorator

def tool_with_logging(func: Callable) -> Callable:
    """Decorator for agent tools with logging."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        logger.info(f"Tool {func.__name__} called with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.info(f"Tool {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Tool {func.__name__} failed: {e}")
            raise
    return wrapper

# Usage
class ProspectingAgent:
    @tool_with_retry(max_retries=3)
    @tool_with_logging
    def _enrich_lead(self, lead_data: dict) -> dict:
        # Implementation
        pass
```

### 9.3 Vector Store for Lead Similarity

```python
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

class LeadVectorStore:
    """Vector store for lead similarity search and RAG."""

    def __init__(self, api_key: str, environment: str, index_name: str):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = Pinecone.from_existing_index(
            index_name=index_name,
            embedding=self.embeddings,
        )

    def add_lead(self, lead: dict):
        """Add lead to vector store."""
        text = f"""
        Lead: {lead['name']}
        Company: {lead['company']}
        Title: {lead.get('title', '')}
        Industry: {lead.get('industry', '')}
        Company Size: {lead.get('company_size', '')}
        Notes: {' '.join(lead.get('notes', []))}
        """
        metadata = {
            "lead_id": lead["lead_id"],
            "company": lead["company"],
            "industry": lead.get("industry", ""),
            "score": lead.get("score", 0),
        }
        self.vectorstore.add_texts([text], metadatas=[metadata])

    def find_similar_leads(self, query: str, k: int = 5) -> list:
        """Find similar leads for lookalike prospecting."""
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [
            {
                "lead_id": doc.metadata["lead_id"],
                "company": doc.metadata["company"],
                "score": score,
                "content": doc.page_content,
            }
            for doc, score in results
        ]

    def find_similar_won_deals(self, lead: dict) -> list:
        """Find similar won deals for social proof and case studies."""
        query = f"{lead.get('industry', '')} {lead.get('company_size', '')} {lead.get('use_case', '')}"
        results = self.vectorstore.similarity_search_with_score(query, k=3)
        return results
```

### 9.4 Event-Driven Agent Trigger

```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery("sales_automation", broker="redis://localhost:6379/0")

@celery_app.task(bind=True, max_retries=3)
def process_new_lead(self, lead_data: dict):
    """Process a new lead through the pipeline."""
    try:
        # Initialize and run pipeline
        result = run_sales_pipeline(lead_data)
        return result
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task
def send_follow_up(task_data: dict):
    """Send a scheduled follow-up."""
    lead_id = task_data["lead_id"]
    touch_type = task_data["touch_type"]
    
    # Load lead from CRM
    lead = crm.get_lead(lead_id)
    
    # Run follow-up agent
    follow_up = FollowUpAgent()
    result = follow_up.run(lead, trigger_event=touch_type)
    return result

@celery_app.task
def run_forecasting():
    """Run sales forecasting (scheduled daily)."""
    forecasting = ForecastingAgent()
    result = forecasting.run(period="quarter")
    
    # Store forecast in database
    # Send notification to sales team
    return result

# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    "daily-forecast": {
        "task": "sales_automation.run_forecasting",
        "schedule": crontab(hour=8, minute=0),  # 8 AM daily
    },
    "process-lead-queue": {
        "task": "sales_automation.process_lead_queue",
        "schedule": 30.0,  # Every 30 seconds
    },
}
```

### 9.5 Agent Evaluation with LangSmith

```python
from langsmith import Client
from langchain.smith import RunEvalConfig, run_on_dataset

# Initialize LangSmith client
langsmith_client = Client()

# Define evaluation metrics
def evaluate_lead_quality(run, example):
    """Evaluate if prospecting agent correctly scored the lead."""
    predicted_score = run.outputs.get("score", 0)
    expected_score = example.outputs.get("score", 0)
    
    # Score within 10 points is acceptable
    if abs(predicted_score - expected_score) <= 10:
        return {"score": 1.0, "key": "lead_scoring_accuracy"}
    return {"score": 0.0, "key": "lead_scoring_accuracy"}

def evaluate_email_personalization(run, example):
    """Evaluate email personalization quality."""
    email_body = run.outputs.get("body", "")
    
    # Check for personalization elements
    has_company_name = example.inputs.get("company", "") in email_body
    has_specific_reference = any(
        ref in email_body 
        for ref in example.inputs.get("personalization_refs", [])
    )
    
    score = (has_company_name + has_specific_reference) / 2
    return {"score": score, "key": "email_personalization"}

def evaluate_qualification_accuracy(run, example):
    """Evaluate qualification decision accuracy."""
    predicted_level = run.outputs.get("level", "")
    expected_level = example.outputs.get("level", "")
    
    return {
        "score": 1.0 if predicted_level == expected_level else 0.0,
        "key": "qualification_accuracy",
    }

# Run evaluation
eval_config = RunEvalConfig(
    evaluators=[
        evaluate_lead_quality,
        evaluate_email_personalization,
        evaluate_qualification_accuracy,
    ],
)

# Run on test dataset
results = run_on_dataset(
    dataset_name="sales_agent_evaluation",
    llm_or_chain_factory=lambda: SalesOrchestrator(),
    evaluation=eval_config,
    client=langsmith_client,
)
```

---

## 10. Testing Strategy

### 10.1 Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5%)
                    │  Tests  │
                   ┌┴─────────┴┐
                   │ Integration│  (15%)
                   │   Tests    │
                  ┌┴────────────┴┐
                  │    Agent      │  (30%)
                  │    Tests      │
                 ┌┴───────────────┴┐
                 │    Unit Tests    │  (50%)
                 │  (Tools, Utils)  │
                 └──────────────────┘
```

### 10.2 Unit Tests

```python
# tests/test_prospecting_agent.py
import pytest
from unittest.mock import Mock, patch
from agents.prospecting import ProspectingAgent

@pytest.fixture
def mock_llm():
    mock = Mock()
    mock.invoke.return_value = Mock(content='{"score": 75, "reasons": ["good fit"], "recommendation": "pursue"}')
    return mock

@pytest.fixture
def mock_crm():
    mock = Mock()
    mock.search_leads.return_value = None
    mock.create_lead.return_value = {"id": "lead_123", "status": "created"}
    return mock

@pytest.fixture
def prospecting_agent(mock_llm, mock_crm):
    return ProspectingAgent(llm=mock_llm, crm_client=mock_crm)

class TestProspectingAgent:
    def test_score_lead_high_fit(self, prospecting_agent):
        """Test scoring for a high-fit lead."""
        lead_data = {
            "name": "Jane Smith",
            "email": "jane@techcorp.com",
            "company": "TechCorp",
            "industry": "SaaS",
            "company_size": "200-500",
        }
        result = prospecting_agent._score_lead(lead_data)
        assert result["score"] >= 60
        assert result["recommendation"] == "pursue"

    def test_score_lead_low_fit(self, prospecting_agent):
        """Test scoring for a low-fit lead."""
        lead_data = {
            "name": "John Doe",
            "email": "john@smallbiz.com",
            "company": "SmallBiz",
            "industry": "Retail",
            "company_size": "1-10",
        }
        result = prospecting_agent._score_lead(lead_data)
        assert result["score"] < 60

    def test_check_existing_lead_found(self, prospecting_agent, mock_crm):
        """Test duplicate lead detection."""
        mock_crm.search_leads.return_value = [{"id": "existing_123"}]
        result = prospecting_agent._check_existing_lead("jane@techcorp.com")
        assert result is not None
        assert result["id"] == "existing_123"

    def test_create_crm_lead(self, prospecting_agent, mock_crm):
        """Test lead creation in CRM."""
        lead_data = {"name": "Jane Smith", "email": "jane@techcorp.com"}
        result = prospecting_agent._create_crm_lead(lead_data)
        assert result["status"] == "created"
        mock_crm.create_lead.assert_called_once()

    def test_enrich_lead_success(self, prospecting_agent):
        """Test lead enrichment with Clearbit."""
        with patch.object(prospecting_agent, 'clearbit') as mock_clearbit:
            mock_clearbit.enrichment.find.return_value = {
                "metrics": {"employees": 250},
                "category": {"industry": "SaaS"},
                "tech": ["aws", "salesforce"],
            }
            lead = {"email": "jane@techcorp.com"}
            result = prospecting_agent._enrich_lead(lead)
            assert result["company_size"] == 250
            assert result["industry"] == "SaaS"

    def test_enrich_lead_failure_graceful(self, prospecting_agent):
        """Test enrichment failure doesn't crash."""
        with patch.object(prospecting_agent, 'clearbit') as mock_clearbit:
            mock_clearbit.enrichment.find.side_effect = Exception("API error")
            lead = {"email": "jane@techcorp.com"}
            result = prospecting_agent._enrich_lead(lead)
            assert result == lead  # Returns original data
```

### 10.3 Agent Tests

```python
# tests/test_outreach_agent.py
import pytest
from unittest.mock import Mock, patch
from agents.outreach import OutreachAgent

class TestOutreachAgent:
    @pytest.fixture
    def mock_llm(self):
        mock = Mock()
        mock.invoke.return_value = Mock(
            content='{"subject": "Quick question about TechCorp", "body": "Hi Jane, I noticed..."}'
        )
        return mock

    @pytest.fixture
    def outreach_agent(mock_llm):
        return OutreachAgent(llm=mock_llm)

    def test_craft_email_personalization(self, outreach_agent):
        """Test email includes personalization."""
        lead = {
            "name": "Jane Smith",
            "company": "TechCorp",
            "title": "VP of Engineering",
            "industry": "SaaS",
        }
        context = {"recent_news": "TechCorp raised Series B"}
        
        result = outreach_agent._craft_email(lead, context)
        
        assert "TechCorp" in result["body"] or "TechCorp" in result["subject"]
        assert len(result["body"]) < 1000  # Concise

    def test_craft_linkedin_message_length(self, outreach_agent):
        """Test LinkedIn message is within character limit."""
        lead = {"name": "Jane Smith", "company": "TechCorp"}
        context = {}
        
        result = outreach_agent._craft_linkedin_message(lead, context)
        
        assert len(result) <= 300

    def test_send_email_success(self, outreach_agent):
        """Test email sending via SendGrid."""
        with patch.object(outreach_agent, 'sendgrid') as mock_sg:
            mock_sg.send.return_value = Mock(status_code=202, headers={"X-Message-Id": "msg_123"})
            
            result = outreach_agent._send_email(
                "jane@techcorp.com",
                {"subject": "Test", "body": "Test body"},
                "lead_123"
            )
            
            assert result["status"] == "sent"
            assert result["message_id"] == "msg_123"

    def test_optimize_send_time(self, outreach_agent):
        """Test send time optimization."""
        lead = {"timezone": "US/Eastern"}
        result = outreach_agent._optimize_send_time(lead)
        assert result == "10:00"

    def test_schedule_follow_up(self, outreach_agent):
        """Test follow-up scheduling."""
        with patch('agents.outreach.send_follow_up') as mock_task:
            result = outreach_agent._schedule_follow_up("lead_123", 3, "email")
            assert result["lead_id"] == "lead_123"
            mock_task.apply_async.assert_called_once()
```

### 10.4 Integration Tests

```python
# tests/integration/test_pipeline.py
import pytest
from unittest.mock import Mock, patch
from langgraph.checkpoint.memory import MemorySaver

class TestSalesPipeline:
    @pytest.fixture
    def pipeline(self):
        """Create a test pipeline with mocked dependencies."""
        with patch('agents.prospecting.ClearbitClient') as mock_clearbit, \
             patch('agents.outreach.SendGridClient') as mock_sendgrid, \
             patch('agents.crm.SalesforceAdapter') as mock_sf:
            
            # Configure mocks
            mock_clearbit.return_value.enrichment.find.return_value = {
                "metrics": {"employees": 250},
                "category": {"industry": "SaaS"},
            }
            mock_sf.return_value.create_lead.return_value = {"id": "sf_lead_123"}
            mock_sf.return_value.search_leads.return_value = None
            
            from orchestrator import SalesOrchestrator
            orchestrator = SalesOrchestrator(
                crm_adapter=mock_sf.return_value,
                checkpointer=MemorySaver(),
            )
            yield orchestrator

    def test_full_pipeline_happy_path(self, pipeline):
        """Test complete pipeline from prospecting to demo scheduling."""
        lead_input = {
            "name": "Jane Smith",
            "email": "jane@techcorp.com",
            "company": "TechCorp",
            "title": "VP of Engineering",
            "industry": "SaaS",
            "company_size": "200-500",
        }
        
        result = pipeline.run(lead_input)
        
        assert result["status"] in ["completed", "demo_scheduled"]
        assert result["lead"]["score"] >= 60

    def test_pipeline_disqualified_lead(self, pipeline):
        """Test pipeline correctly disqualifies low-fit leads."""
        lead_input = {
            "name": "John Doe",
            "email": "john@smallbiz.com",
            "company": "SmallBiz",
            "industry": "Retail",
            "company_size": "1-10",
        }
        
        result = pipeline.run(lead_input)
        
        assert result["status"] in ["disqualified", "nurture"]

    def test_pipeline_duplicate_lead(self, pipeline):
        """Test pipeline handles duplicate leads."""
        pipeline.crm.search_leads.return_value = [{"id": "existing_123"}]
        
        lead_input = {
            "name": "Jane Smith",
            "email": "jane@techcorp.com",
            "company": "TechCorp",
        }
        
        result = pipeline.run(lead_input)
        
        assert result["status"] == "duplicate"
        assert result["existing_lead_id"] == "existing_123"

    def test_pipeline_crm_failure_recovery(self, pipeline):
        """Test pipeline handles CRM failures gracefully."""
        pipeline.crm.create_lead.side_effect = Exception("CRM API error")
        
        lead_input = {
            "name": "Jane Smith",
            "email": "jane@techcorp.com",
            "company": "TechCorp",
        }
        
        # Should not crash, should log error and continue
        result = pipeline.run(lead_input)
        assert "error" in result or result["status"] == "partial"
```

### 10.5 End-to-End Tests

```python
# tests/e2e/test_sales_automation_e2e.py
import pytest
import time
from testcontainers.compose import DockerCompose

@pytest.fixture(scope="module")
def infrastructure():
    """Start test infrastructure (Redis, PostgreSQL, etc.)."""
    with DockerCompose("tests/e2e", compose_file_name="docker-compose.test.yml") as compose:
        # Wait for services to be ready
        time.sleep(10)
        yield compose

@pytest.mark.e2e
class TestSalesAutomationE2E:
    def test_complete_sales_cycle(self, infrastructure):
        """Test a complete sales cycle from lead to opportunity."""
        # 1. Submit lead via API
        response = client.post("/api/leads", json={
            "name": "E2E Test Lead",
            "email": "e2e@test.com",
            "company": "E2E Test Corp",
            "title": "CTO",
            "industry": "SaaS",
        })
        assert response.status_code == 201
        lead_id = response.json()["lead_id"]
        
        # 2. Wait for pipeline to process
        time.sleep(30)
        
        # 3. Verify lead was created in CRM
        lead = crm_client.get_lead(lead_id)
        assert lead is not None
        assert lead["status"] != "NEW"
        
        # 4. Verify outreach was sent
        activities = crm_client.get_activities(lead_id)
        assert len(activities) > 0
        
        # 5. Simulate lead response
        client.post("/api/webhooks/email", json={
            "lead_id": lead_id,
            "event": "reply",
            "content": "I'd like to learn more. Can we schedule a demo?",
        })
        
        # 6. Wait for qualification and demo scheduling
        time.sleep(30)
        
        # 7. Verify demo was scheduled
        lead = crm_client.get_lead(lead_id)
        assert lead["status"] in ["DEMO_SCHEDULED", "QUALIFIED"]

    def test_forecasting_accuracy(self, infrastructure):
        """Test forecasting agent produces reasonable predictions."""
        # Seed historical data
        seed_historical_data()
        
        # Run forecasting
        response = client.post("/api/forecast", json={"period": "quarter"})
        assert response.status_code == 200
        
        forecast = response.json()
        assert "committed" in forecast
        assert "best_case" in forecast
        assert forecast["committed"] <= forecast["best_case"]
```

### 10.6 Performance Tests

```python
# tests/performance/test_agent_performance.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

class TestAgentPerformance:
    def test_prospecting_agent_latency(self):
        """Test prospecting agent completes within acceptable time."""
        agent = ProspectingAgent()
        lead = {"name": "Test", "email": "test@test.com", "company": "TestCo"}
        
        start = time.time()
        result = agent.run(lead)
        duration = time.time() - start
        
        assert duration < 30  # Should complete within 30 seconds
        assert result is not None

    def test_outreach_agent_throughput(self):
        """Test outreach agent can handle multiple leads."""
        agent = OutreachAgent()
        leads = [
            {"name": f"Lead {i}", "email": f"lead{i}@test.com", "company": f"Company {i}"}
            for i in range(10)
        ]
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(agent.run, leads))
        duration = time.time() - start
        
        assert duration < 60  # 10 leads in under 60 seconds
        assert len(results) == 10

    def test_pipeline_concurrent_leads(self):
        """Test pipeline handles concurrent lead processing."""
        pipeline = SalesOrchestrator()
        leads = [generate_test_lead(i) for i in range(20)]
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(pipeline.run, leads))
        duration = time.time() - start
        
        assert duration < 120  # 20 leads in under 2 minutes
        assert all(r["status"] != "error" for r in results)
```

### 10.7 Test Data Management

```python
# tests/fixtures/leads.py
import pytest
import faker

fake = faker.Faker()

@pytest.fixture
def sample_lead():
    """Generate a sample lead for testing."""
    return {
        "lead_id": str(uuid.uuid4()),
        "name": fake.name(),
        "email": fake.email(),
        "company": fake.company(),
        "title": fake.job(),
        "phone": fake.phone_number(),
        "industry": fake.random_element(["SaaS", "Fintech", "Healthcare", "E-commerce"]),
        "company_size": fake.random_element(["1-10", "11-50", "51-200", "201-500", "501-1000"]),
        "status": "new",
        "score": 0.0,
        "source": "test",
    }

@pytest.fixture
def qualified_lead():
    """Generate a pre-qualified lead."""
    return {
        "lead_id": str(uuid.uuid4()),
        "name": "Jane Smith",
        "email": "jane@techcorp.com",
        "company": "TechCorp",
        "title": "VP of Engineering",
        "industry": "SaaS",
        "company_size": "200-500",
        "status": "qualified",
        "score": 85.0,
        "qualification_data": {
            "level": "A",
            "budget_signal": "confirmed",
            "authority_signal": "decision_maker",
            "need_signal": "urgent",
            "timeline_signal": "<30_days",
        },
    }

@pytest.fixture
def mock_crm_data():
    """Generate mock CRM data for testing."""
    return {
        "leads": [sample_lead() for _ in range(50)],
        "opportunities": [
            {
                "id": f"opp_{i}",
                "name": f"Deal {i}",
                "stage": fake.random_element(["Prospecting", "Qualification", "Demo", "Proposal", "Negotiation"]),
                "amount": fake.random_int(10000, 100000),
                "close_date": fake.date_between(start_date="+30d", end_date="+90d").isoformat(),
            }
            for i in range(20)
        ],
    }
```

### 10.8 CI/CD Test Pipeline

```yaml
# .github/workflows/test.yml
name: Sales Automation Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-test.txt
      - run: pytest tests/unit -v --cov=agents --cov-report=xml
      - uses: codecov/codecov-action@v3

  agent-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/agents -v

  integration-tests:
    runs-on: ubuntu-latest
    needs: agent-tests
    services:
      redis:
        image: redis:7
        ports: ["6379:6379"]
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/integration -v

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: docker-compose -f tests/e2e/docker-compose.test.yml up -d
      - run: pytest tests/e2e -v -m e2e
      - run: docker-compose -f tests/e2e/docker-compose.test.yml down
```

---

## Appendix: Deployment Architecture

### A.1 Production Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  API Server │  │  API Server │  │  API Server │        │
│  │   (FastAPI) │  │   (FastAPI) │  │   (FastAPI) │        │
│  │   Replica 1 │  │   Replica 2 │  │   Replica 3 │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Celery    │  │   Celery    │  │   Celery    │        │
│  │   Worker 1  │  │   Worker 2  │  │   Worker 3  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Redis      │  │  PostgreSQL │  │  Pinecone   │        │
│  │  (Queue)    │  │  (Primary)  │  │  (Vectors)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐                         │
│  │  LangSmith  │  │  OpenTelemetry│                        │
│  │  (Tracing)  │  │  (Metrics)   │                        │
│  └─────────────┘  └─────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### A.2 Environment Variables

```bash
# .env.production
# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# CRM
SF_USERNAME=...
SF_PASSWORD=...
SF_SECURITY_TOKEN=...
SF_DOMAIN=login

# Communication
SENDGRID_API_KEY=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...

# Calendar
GOOGLE_CALENDAR_CREDENTIALS=...
CALENDLY_API_KEY=...

# Infrastructure
REDIS_URL=redis://...
DATABASE_URL=postgresql://...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1

# Monitoring
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=sales-automation
OTEL_EXPORTER_OTLP_ENDPOINT=...

# Security
ENCRYPTION_KEY=...
WEBHOOK_SECRET=...
```

---

*Document Version: 1.0*
*Last Updated: 2026-10-01*
*Author: AI Sales Automation Team*
