# AI-Powered CRM Enhancement Implementation Plan
## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Stack:** LangChain DeepAgents, Python 3.11+, PostgreSQL, Redis, FastAPI

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Contact Enrichment Agent](#2-contact-enrichment-agent)
3. [Deal Scoring Agent](#3-deal-scoring-agent)
4. [Task Automation Agent](#4-task-automation-agent)
5. [Meeting Scheduling Agent](#5-meeting-scheduling-agent)
6. [Follow-up Automation Agent](#6-follow-up-automation-agent)
7. [Performance Analytics Agent](#7-performance-analytics-agent)
8. [Code Examples & Snippets](#8-code-examples--snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Design

The CRM enhancement system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. A central **CRMAgentOrchestrator** routes tasks to specialized sub-agents, each responsible for a distinct CRM domain.

```
┌─────────────────────────────────────────────────────────────┐
│                    CRM Agent Orchestrator                     │
│  (Router + Context Manager + Human-in-the-Loop Gateway)     │
└─────────────┬───────────────┬───────────────┬───────────────┘
              │               │               │
    ┌─────────▼─────┐ ┌──────▼──────┐ ┌──────▼──────────┐
    │   Contact     │ │    Deal     │ │     Task        │
    │ Enrichment    │ │   Scoring   │ │  Automation     │
    │    Agent      │ │    Agent    │ │     Agent       │
    └─────────┬─────┘ └──────┬──────┘ └──────┬──────────┘
              │               │               │
    ┌─────────▼─────┐ ┌──────▼──────┐ ┌──────▼──────────┐
    │   Meeting     │ │  Follow-up  │ │   Analytics     │
    │  Scheduling   │ │ Automation  │ │     Agent       │
    │    Agent      │ │    Agent    │ │                 │
    └───────────────┘ └─────────────┘ └─────────────────┘
              │               │               │
    ┌─────────▼───────────────▼───────────────▼──────────┐
    │              Shared Infrastructure Layer             │
    │  (CRM DB │ Vector Store │ LLM Gateway │ Tool Registry)│
    └─────────────────────────────────────────────────────┘
```

### 1.2 Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Orchestrator | LangChain DeepAgents `create_agent` | Route tasks, manage context, coordinate sub-agents |
| LLM Gateway | LangChain `ChatOpenAI` / `ChatAnthropic` | Unified LLM access with fallback |
| Vector Store | pgvector / Qdrant | Semantic search over contacts, deals, interactions |
| Tool Registry | LangChain `Tool` + `StructuredTool` | Expose CRM operations as agent-callable tools |
| State Store | Redis + PostgreSQL | Session state, conversation history, agent checkpoints |
| Human-in-the-Loop | LangChain `interrupt` + callback | Approval gates for destructive actions |
| Event Bus | Redis Streams / Celery | Async task dispatch between agents |

### 1.3 Agent Communication Protocol

All agents communicate via a **shared message schema**:

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_agent: str
    target_agent: str
    message_type: Literal["request", "response", "event", "approval_request"]
    payload: dict
    context: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None  # For request-response pairing
```

### 1.4 Context Management

Each agent maintains a **sliding context window** with structured memory:

```python
from langchain_core.messages import BaseMessage
from langchain_community.chat_message_histories import RedisChatMessageHistory

class AgentContextManager:
    def __init__(self, session_id: str, redis_url: str):
        self.history = RedisChatMessageHistory(
            session_id=session_id,
            url=redis_url,
            ttl=3600  # 1-hour TTL
        )
    
    def get_relevant_context(self, query: str, k: int = 10) -> list[BaseMessage]:
        """Retrieve semantically relevant messages using vector search."""
        # Hybrid search: recency + semantic similarity
        recent = self.history.messages[-k:]
        return recent
    
    def add_message(self, message: BaseMessage):
        self.history.add_message(message)
```

### 1.5 Human-in-the-Loop Gates

Destructive or high-stakes actions require human approval:

```python
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import tool

@tool
def delete_contact(contact_id: str, reason: str) -> str:
    """Delete a contact from CRM. Requires human approval."""
    # This triggers an interrupt — the orchestrator pauses
    # and sends an approval request to the UI
    decision = interrupt({
        "action": "delete_contact",
        "contact_id": contact_id,
        "reason": reason,
        "requires_approval": True
    })
    if decision["approved"]:
        # Execute deletion
        return f"Contact {contact_id} deleted."
    return "Deletion cancelled by user."
```

---

## 2. Contact Enrichment Agent

### 2.1 Purpose

Automatically enrich contact records with data from external sources (LinkedIn, company websites, Clearbit, etc.) and internal interaction history.

### 2.2 Agent Definition

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

class ContactEnrichmentAgent:
    def __init__(self, llm: ChatOpenAI, crm_db, vector_store):
        self.llm = llm
        self.crm_db = crm_db
        self.vector_store = vector_store
        self.tools = [
            self.search_external_profiles,
            self.fetch_company_info,
            self.extract_from_email_signature,
            self.update_contact_record,
            self.find_duplicate_contacts,
        ]
        self.agent = self._build_agent()
    
    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Contact Enrichment Agent for a CRM system.
Your job is to enrich contact records with accurate, up-to-date information.

Guidelines:
- Always verify data from at least 2 sources before updating
- Flag conflicting information for human review
- Never overwrite existing data without merging
- Respect data privacy (GDPR/CCPA compliance)
- Log all enrichment actions for audit

Available tools: {tools}
"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )
    
    @tool
    def search_external_profiles(self, name: str, company: str, email: str) -> dict:
        """Search external data sources (LinkedIn, Clearbit, etc.) for contact info."""
        # Integration with Clearbit, Proxycurl, or similar
        results = {}
        if email:
            clearbit_data = self._query_clearbit(email)
            results["clearbit"] = clearbit_data
        if name and company:
            linkedin_data = self._query_proxycurl(name, company)
            results["linkedin"] = linkedin_data
        return results
    
    @tool
    def fetch_company_info(self, company_name: str, domain: str) -> dict:
        """Fetch company information from external APIs."""
        # Use Clearbit Company API or similar
        return self._query_company_api(company_name, domain)
    
    @tool
    def extract_from_email_signature(self, email_body: str) -> dict:
        """Extract contact details from email signatures using NLP."""
        # Use a fine-tuned NER model or regex + LLM extraction
        extraction_prompt = f"""Extract the following from this email signature:
- Name, title, company, phone, email, social links, address

Email signature:
{email_body}
"""
        response = self.llm.invoke(extraction_prompt)
        return self._parse_extraction(response.content)
    
    @tool
    def update_contact_record(self, contact_id: str, updates: dict, source: str) -> str:
        """Update a contact record with enriched data. Creates audit log."""
        # Merge strategy: only update empty fields or fields with lower confidence
        existing = self.crm_db.get_contact(contact_id)
        merged = self._merge_contact_data(existing, updates, source)
        self.crm_db.update_contact(contact_id, merged)
        self._log_enrichment_action(contact_id, updates, source)
        return f"Contact {contact_id} enriched from {source}"
    
    @tool
    def find_duplicate_contacts(self, contact_id: str) -> list:
        """Find potential duplicate contacts using fuzzy matching + embeddings."""
        contact = self.crm_db.get_contact(contact_id)
        # Generate embedding and search vector store
        embedding = self._embed_contact(contact)
        similar = self.vector_store.similarity_search(
            embedding, k=5, score_threshold=0.85
        )
        return [s.metadata for s in similar]
```

### 2.3 Enrichment Pipeline

```python
class EnrichmentPipeline:
    """Orchestrates the full enrichment workflow."""
    
    def __init__(self, agent: ContactEnrichmentAgent):
        self.agent = agent
    
    async def enrich_contact(self, contact_id: str) -> EnrichmentResult:
        # Step 1: Gather existing data
        contact = self.agent.crm_db.get_contact(contact_id)
        
        # Step 2: Run enrichment agent
        result = await self.agent.agent.ainvoke({
            "input": f"Enrich contact {contact_id}: {contact['name']} at {contact.get('company', 'unknown')}"
        })
        
        # Step 3: Validate and merge
        validated = self._validate_enrichment(result)
        
        # Step 4: Update vector store for deduplication
        self._update_vector_index(contact_id, validated)
        
        # Step 5: Notify orchestrator of completion
        return EnrichmentResult(
            contact_id=contact_id,
            fields_updated=validated["updated_fields"],
            confidence=validated["confidence"],
            sources=validated["sources"]
        )
```

---

## 3. Deal Scoring Agent

### 3.1 Purpose

Score and prioritize sales deals using a combination of predictive models, engagement signals, and historical patterns.

### 3.2 Scoring Model

```python
from pydantic import BaseModel, Field
from typing import Literal
import numpy as np

class DealScore(BaseModel):
    deal_id: str
    overall_score: float = Field(ge=0, le=100)
    win_probability: float = Field(ge=0, le=1)
    expected_close_date: str
    deal_temperature: Literal["hot", "warm", "cold", "stalled"]
    risk_factors: list[str]
    recommended_actions: list[str]
    scoring_factors: dict  # Breakdown of individual factor scores

class DealScoringAgent:
    def __init__(self, llm: ChatOpenAI, crm_db, model_registry):
        self.llm = llm
        self.crm_db = crm_db
        self.model_registry = model_registry
        self.tools = [
            self.get_deal_details,
            self.get_contact_engagement_history,
            self.get_similar_closed_deals,
            self.get_deal_stage_duration,
            self.analyze_email_sentiment,
            self.score_deal,
            self.update_deal_score,
        ]
        self.agent = self._build_agent()
    
    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Deal Scoring Agent. Your job is to evaluate 
sales deals and provide actionable scoring and recommendations.

Scoring dimensions (weighted):
- Engagement (30%): Email opens, replies, meeting frequency, response time
- Fit (25%): Company size, industry match, budget authority, use case alignment
- Stage progression (20%): Time in stage, stage advancement velocity
- Sentiment (15%): Email sentiment, objection patterns, stakeholder sentiment
- Historical patterns (10%): Similar deals' outcomes

Always provide:
1. A numerical score (0-100)
2. Win probability (0-1)
3. Specific risk factors
4. Recommended next actions
5. Confidence level in the assessment
"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    @tool
    def get_deal_details(self, deal_id: str) -> dict:
        """Fetch complete deal information from CRM."""
        deal = self.crm_db.get_deal(deal_id)
        deal["contacts"] = self.crm_db.get_deal_contacts(deal_id)
        deal["activities"] = self.crm_db.get_deal_activities(deal_id)
        deal["notes"] = self.crm_db.get_deal_notes(deal_id)
        return deal
    
    @tool
    def get_contact_engagement_history(self, contact_ids: list[str]) -> dict:
        """Get engagement metrics for all contacts on a deal."""
        engagement = {}
        for cid in contact_ids:
            engagement[cid] = {
                "email_opens_30d": self.crm_db.count_email_opens(cid, days=30),
                "email_replies_30d": self.crm_db.count_email_replies(cid, days=30),
                "meetings_held": self.crm_db.count_meetings(cid),
                "last_interaction": self.crm_db.get_last_interaction(cid),
                "response_time_avg_hours": self.crm_db.avg_response_time(cid),
            }
        return engagement
    
    @tool
    def get_similar_closed_deals(self, deal_id: str, limit: int = 10) -> list:
        """Find similar historically closed deals using vector similarity."""
        deal = self.crm_db.get_deal(deal_id)
        deal_embedding = self._embed_deal(deal)
        similar = self.vector_store.similarity_search(
            deal_embedding, k=limit,
            filter={"status": ["closed_won", "closed_lost"]}
        )
        return [{
            "deal_id": s.metadata["deal_id"],
            "outcome": s.metadata["status"],
            "similarity_score": s.score,
            "deal_value": s.metadata["value"],
        } for s in similar]
    
    @tool
    def analyze_email_sentiment(self, deal_id: str) -> dict:
        """Analyze sentiment of all email communications for a deal."""
        emails = self.crm_db.get_deal_emails(deal_id)
        sentiments = []
        for email in emails:
            sentiment = self._analyze_sentiment(email["body"])
            sentiments.append({
                "date": email["date"],
                "direction": email["direction"],
                "sentiment": sentiment,
            })
        return {
            "overall_trend": self._compute_sentiment_trend(sentiments),
            "recent_sentiments": sentiments[-5:],
            "objection_count": sum(1 for s in sentiments if s["sentiment"] < -0.3),
        }
    
    @tool
    def score_deal(self, deal_id: str) -> DealScore:
        """Compute comprehensive deal score using all available signals."""
        # Gather all signals
        deal = self.get_deal_details(deal_id)
        engagement = self.get_contact_engagement_history(
            [c["id"] for c in deal["contacts"]]
        )
        similar_deals = self.get_similar_closed_deals(deal_id)
        sentiment = self.analyze_email_sentiment(deal_id)
        
        # Compute factor scores
        engagement_score = self._score_engagement(engagement)
        fit_score = self._score_fit(deal)
        stage_score = self._score_stage_progression(deal)
        sentiment_score = self._score_sentiment(sentiment)
        historical_score = self._score_historical_patterns(similar_deals)
        
        # Weighted combination
        weights = {
            "engagement": 0.30,
            "fit": 0.25,
            "stage": 0.20,
            "sentiment": 0.15,
            "historical": 0.10,
        }
        
        overall = (
            engagement_score * weights["engagement"] +
            fit_score * weights["fit"] +
            stage_score * weights["stage"] +
            sentiment_score * weights["sentiment"] +
            historical_score * weights["historical"]
        )
        
        # Determine temperature
        temp = self._classify_temperature(overall, deal, engagement)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            deal, engagement, sentiment, overall
        )
        
        return DealScore(
            deal_id=deal_id,
            overall_score=round(overall, 1),
            win_probability=self._compute_win_probability(overall, similar_deals),
            expected_close_date=self._predict_close_date(deal, overall),
            deal_temperature=temp,
            risk_factors=self._identify_risks(deal, engagement, sentiment),
            recommended_actions=recommendations,
            scoring_factors={
                "engagement": engagement_score,
                "fit": fit_score,
                "stage": stage_score,
                "sentiment": sentiment_score,
                "historical": historical_score,
            }
        )
    
    def _score_engagement(self, engagement: dict) -> float:
        """Score based on contact engagement signals (0-100)."""
        scores = []
        for cid, metrics in engagement.items():
            score = 0
            # Email engagement (0-30)
            score += min(metrics["email_opens_30d"] * 2, 15)
            score += min(metrics["email_replies_30d"] * 5, 15)
            # Meeting engagement (0-30)
            score += min(metrics["meetings_held"] * 10, 30)
            # Recency (0-25)
            days_since = (datetime.utcnow() - metrics["last_interaction"]).days
            score += max(0, 25 - days_since)
            # Response time (0-15)
            if metrics["response_time_avg_hours"] < 24:
                score += 15
            elif metrics["response_time_avg_hours"] < 72:
                score += 8
            scores.append(score)
        return np.mean(scores) if scores else 0
    
    def _classify_temperature(
        self, score: float, deal: dict, engagement: dict
    ) -> str:
        """Classify deal temperature based on score and signals."""
        if score >= 75:
            return "hot"
        elif score >= 50:
            # Check for stalling
            days_in_stage = deal.get("days_in_current_stage", 0)
            if days_in_stage > 30:
                return "stalled"
            return "warm"
        elif score >= 25:
            return "cold"
        return "stalled"
```

### 3.3 Scheduled Scoring

```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery("crm_scoring", broker="redis://localhost:6379/0")

@celery_app.task
def batch_score_deals():
    """Score all open deals daily."""
    scoring_agent = DealScoringAgent(...)
    open_deals = crm_db.get_open_deals()
    
    for deal in open_deals:
        score = scoring_agent.score_deal(deal["id"])
        crm_db.update_deal_score(deal["id"], score.dict())
        
        # Alert for significant changes
        previous = deal.get("previous_score", 0)
        if abs(score.overall_score - previous) > 15:
            notify_sales_rep(deal["id"], score)

celery_app.conf.beat_schedule = {
    "score-deals-daily": {
        "task": "batch_score_deals",
        "schedule": crontab(hour=6, minute=0),  # 6 AM daily
    },
}
```

---

## 4. Task Automation Agent

### 4.1 Purpose

Automatically create, assign, and manage CRM tasks based on deal stages, engagement triggers, and workflow rules.

### 4.2 Agent Implementation

```python
class TaskAutomationAgent:
    def __init__(self, llm: ChatOpenAI, crm_db, notification_service):
        self.llm = llm
        self.crm_db = crm_db
        self.notification = notification_service
        self.tools = [
            self.get_pending_tasks,
            self.create_task,
            self.assign_task,
            self.update_task_status,
            self.get_workflow_rules,
            self.suggest_tasks_from_deal,
            self.bulk_create_followup_tasks,
        ]
        self.agent = self._build_agent()
    
    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Task Automation Agent for CRM operations.

Your responsibilities:
- Create tasks based on deal stage transitions
- Generate follow-up tasks from email/communication analysis
- Assign tasks to the right team members
- Set appropriate priorities and due dates
- Detect and resolve task conflicts
- Escalate overdue tasks

Task types: call, email, meeting, demo, proposal, follow_up, research, internal

Always consider:
- Workload balance across team members
- Deal priority and value
- Time zone differences
- Existing commitments
"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    @tool
    def create_task(self, task_data: dict) -> str:
        """Create a new CRM task with smart defaults."""
        task = {
            "id": str(uuid.uuid4()),
            "title": task_data["title"],
            "description": task_data.get("description", ""),
            "type": task_data["type"],
            "priority": task_data.get("priority", "medium"),
            "due_date": self._calculate_due_date(task_data),
            "assigned_to": task_data.get("assigned_to") or self._suggest_assignee(task_data),
            "related_to": task_data.get("related_to"),  # deal_id or contact_id
            "status": "pending",
            "created_by": "task_automation_agent",
            "created_at": datetime.utcnow().isoformat(),
        }
        self.crm_db.create_task(task)
        
        # Notify assignee
        self.notification.send(
            user_id=task["assigned_to"],
            message=f"New task assigned: {task['title']}",
            channel="in_app"
        )
        return f"Task created: {task['id']}"
    
    @tool
    def suggest_tasks_from_deal(self, deal_id: str) -> list:
        """Analyze a deal and suggest appropriate follow-up tasks."""
        deal = self.crm_db.get_deal(deal_id)
        stage = deal["stage"]
        last_activity = self.crm_db.get_last_activity(deal_id)
        days_since_activity = (datetime.utcnow() - last_activity).days if last_activity else 999
        
        suggestions = []
        
        # Stage-based suggestions
        stage_tasks = {
            "discovery": [
                {"title": "Send discovery summary", "type": "email", "priority": "high"},
                {"title": "Schedule demo", "type": "meeting", "priority": "high"},
                {"title": "Research stakeholder map", "type": "research", "priority": "medium"},
            ],
            "demo": [
                {"title": "Send demo recap & next steps", "type": "email", "priority": "high"},
                {"title": "Prepare proposal", "type": "proposal", "priority": "high"},
            ],
            "negotiation": [
                {"title": "Follow up on pricing discussion", "type": "call", "priority": "high"},
                {"title": "Send revised proposal", "type": "proposal", "priority": "high"},
            ],
        }
        
        if stage in stage_tasks:
            suggestions.extend(stage_tasks[stage])
        
        # Activity-based suggestions
        if days_since_activity > 7:
            suggestions.append({
                "title": f"Re-engage deal (no activity for {days_since_activity} days)",
                "type": "call",
                "priority": "high" if days_since_activity > 14 else "medium",
            })
        
        return suggestions
    
    @tool
    def bulk_create_followup_tasks(self, deal_ids: list[str]) -> dict:
        """Create follow-up tasks for multiple deals efficiently."""
        results = {"created": 0, "skipped": 0, "errors": []}
        
        for deal_id in deal_ids:
            try:
                suggestions = self.suggest_tasks_from_deal(deal_id)
                for suggestion in suggestions[:2]:  # Max 2 tasks per deal
                    self.create_task({
                        **suggestion,
                        "related_to": deal_id,
                    })
                    results["created"] += 1
            except Exception as e:
                results["errors"].append({"deal_id": deal_id, "error": str(e)})
        
        return results
    
    def _suggest_assignee(self, task_data: dict) -> str:
        """Suggest the best team member for a task based on workload and expertise."""
        related_deal = task_data.get("related_to")
        if related_deal:
            deal = self.crm_db.get_deal(related_deal)
            # Prefer the deal owner
            if deal.get("owner_id"):
                return deal["owner_id"]
        
        # Fallback: find team member with lowest active task count
        team = self.crm_db.get_team_members(task_data.get("team", "sales"))
        workloads = {
            m["id"]: self.crm_db.count_active_tasks(m["id"])
            for m in team
        }
        return min(workloads, key=workloads.get)
    
    def _calculate_due_date(self, task_data: dict) -> str:
        """Calculate smart due date based on priority and type."""
        priority_offsets = {
            "urgent": 0,      # Same day
            "high": 1,        # Next day
            "medium": 3,      # 3 days
            "low": 7,         # 1 week
        }
        offset = priority_offsets.get(task_data.get("priority", "medium"), 3)
        due = datetime.utcnow() + timedelta(days=offset)
        # Adjust for business hours (9 AM next business day)
        due = due.replace(hour=9, minute=0, second=0)
        return due.isoformat()
```

### 4.3 Workflow Engine Integration

```python
class WorkflowEngine:
    """Event-driven workflow automation."""
    
    def __init__(self, task_agent: TaskAutomationAgent):
        self.task_agent = task_agent
        self.rules = self._load_rules()
    
    def _load_rules(self) -> list[WorkflowRule]:
        """Load workflow rules from configuration."""
        return [
            WorkflowRule(
                trigger="deal_stage_changed",
                condition=lambda event: event["new_stage"] == "demo",
                action=lambda event: self.task_agent.create_task({
                    "title": "Prepare demo environment",
                    "type": "internal",
                    "related_to": event["deal_id"],
                    "priority": "high",
                }),
            ),
            WorkflowRule(
                trigger="email_received",
                condition=lambda event: "pricing" in event["email_subject"].lower(),
                action=lambda event: self.task_agent.create_task({
                    "title": "Respond to pricing inquiry",
                    "type": "email",
                    "related_to": event["deal_id"],
                    "priority": "high",
                }),
            ),
            WorkflowRule(
                trigger="deal_idle",
                condition=lambda event: event["days_inactive"] > 14,
                action=lambda event: self.task_agent.create_task({
                    "title": "Re-engagement call - deal stalled",
                    "type": "call",
                    "related_to": event["deal_id"],
                    "priority": "urgent",
                }),
            ),
        ]
    
    def process_event(self, event: dict):
        """Process a CRM event through the workflow engine."""
        for rule in self.rules:
            if rule.matches(event):
                rule.execute(event)
```

---

## 5. Meeting Scheduling Agent

### 5.1 Purpose

Intelligently schedule meetings by finding optimal time slots, sending invitations, and managing calendar conflicts.

### 5.2 Agent Implementation

```python
class MeetingSchedulingAgent:
    def __init__(self, llm: ChatOpenAI, crm_db, calendar_service, email_service):
        self.llm = llm
        self.crm_db = crm_db
        self.calendar = calendar_service  # Google Calendar / Outlook API
        self.email = email_service
        self.tools = [
            self.check_availability,
            self.find_optimal_slots,
            self.schedule_meeting,
            self.send_invitation,
            self.reschedule_meeting,
            self.cancel_meeting,
            self.get_meeting_prep_notes,
        ]
        self.agent = self._build_agent()
    
    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Meeting Scheduling Agent.

Your capabilities:
- Check participant availability across time zones
- Find optimal meeting slots considering preferences
- Schedule meetings with calendar integration
- Send personalized invitations
- Handle rescheduling and cancellations
- Generate meeting prep notes

Scheduling preferences:
- Default meeting length: 30 minutes (can be 15, 30, 45, 60)
- Buffer time: 15 minutes between meetings
- Preferred hours: 9 AM - 5 PM in participant's local time
- Avoid scheduling on weekends unless explicitly requested
- Consider travel time for in-person meetings
"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    @tool
    def check_availability(
        self, participant_emails: list[str], 
        date_range: tuple[str, str],
        duration_minutes: int = 30
    ) -> dict:
        """Check availability for all participants in a date range."""
        availability = {}
        for email in participant_emails:
            busy_slots = self.calendar.get_busy_times(
                email, start=date_range[0], end=date_range[1]
            )
            availability[email] = {
                "busy_slots": busy_slots,
                "timezone": self.calendar.get_timezone(email),
            }
        return availability
    
    @tool
    def find_optimal_slots(
        self, participant_emails: list[str],
        date_range: tuple[str, str],
        duration_minutes: int = 30,
        num_suggestions: int = 3
    ) -> list:
        """Find the best meeting time slots for all participants."""
        availability = self.check_availability(
            participant_emails, date_range, duration_minutes
        )
        
        # Generate all possible slots (30-min increments, 9 AM - 5 PM)
        all_slots = self._generate_time_slots(date_range, duration_minutes)
        
        # Score each slot
        scored_slots = []
        for slot in all_slots:
            score = self._score_slot(slot, availability, participant_emails)
            if score > 0:  # Only include feasible slots
                scored_slots.append({
                    "start": slot["start"],
                    "end": slot["end"],
                    "score": score,
                    "timezone_conflicts": slot.get("timezone_conflicts", []),
                })
        
        # Return top N suggestions
        scored_slots.sort(key=lambda x: x["score"], reverse=True)
        return scored_slots[:num_suggestions]
    
    @tool
    def schedule_meeting(self, meeting_data: dict) -> str:
        """Schedule a meeting and send calendar invitations."""
        # Create calendar event
        event = self.calendar.create_event(
            title=meeting_data["title"],
            start=meeting_data["start_time"],
            end=meeting_data["end_time"],
            attendees=meeting_data["attendees"],
            description=meeting_data.get("description", ""),
            location=meeting_data.get("location", "Video call"),
            conference_data=self._create_video_link(meeting_data),
        )
        
        # Store in CRM
        meeting_record = {
            "id": event["id"],
            "title": meeting_data["title"],
            "start_time": meeting_data["start_time"],
            "end_time": meeting_data["end_time"],
            "attendees": meeting_data["attendees"],
            "related_to": meeting_data.get("related_to"),
            "status": "scheduled",
            "calendar_event_id": event["id"],
        }
        self.crm_db.create_meeting(meeting_record)
        
        # Send invitations
        for attendee in meeting_data["attendees"]:
            self.send_invitation(meeting_record, attendee)
        
        return f"Meeting scheduled: {event['id']}"
    
    @tool
    def get_meeting_prep_notes(self, meeting_id: str) -> str:
        """Generate AI-powered meeting prep notes."""
        meeting = self.crm_db.get_meeting(meeting_id)
        related_deal = self.crm_db.get_deal(meeting["related_to"]) if meeting.get("related_to") else None
        contacts = self.crm_db.get_contacts([a for a in meeting["attendees"]])
        
        # Gather context
        context = {
            "meeting": meeting,
            "deal": related_deal,
            "contacts": contacts,
            "previous_meetings": self.crm_db.get_previous_meetings(
                meeting["related_to"]
            ),
            "email_threads": self.crm_db.get_email_threads(
                [c["email"] for c in contacts]
            ),
        }
        
        # Generate prep notes with LLM
        prep_prompt = f"""Generate concise meeting prep notes for the following meeting:

Meeting: {meeting['title']}
Attendees: {', '.join(c['name'] for c in contacts)}
Related Deal: {related_deal['name'] if related_deal else 'N/A'}

Previous interaction summary:
{self._summarize_interactions(context['previous_meetings'], context['email_threads'])}

Include:
1. Key discussion points from previous interactions
2. Attendee backgrounds and roles
3. Deal status and priorities
4. Suggested agenda items
5. Potential objections to address
"""
        response = self.llm.invoke(prep_prompt)
        return response.content
    
    def _score_slot(
        self, slot: dict, availability: dict, participants: list[str]
    ) -> float:
        """Score a time slot based on participant preferences and constraints."""
        score = 100.0
        
        for email in participants:
            # Check for conflicts
            for busy in availability[email]["busy_slots"]:
                if self._times_overlap(slot, busy):
                    return 0  # Hard conflict
            
            # Timezone penalty
            local_hour = self._convert_to_local(
                slot["start"], availability[email]["timezone"]
            )
            if local_hour < 9 or local_hour > 17:
                score -= 30  # Outside business hours
            elif local_hour < 10 or local_hour > 16:
                score -= 10  # Edge of business hours
            
            # Preference bonus (if we have historical preference data)
            preferred_hours = self.calendar.get_preferred_hours(email)
            if preferred_hours and local_hour in preferred_hours:
                score += 10
        
        return max(0, score)
```

---

## 6. Follow-up Automation Agent

### 6.1 Purpose

Automatically generate and send personalized follow-up communications based on interaction history, deal stage, and engagement patterns.

### 6.2 Agent Implementation

```python
class FollowUpAutomationAgent:
    def __init__(self, llm: ChatOpenAI, crm_db, email_service, template_engine):
        self.llm = llm
        self.crm_db = crm_db
        self.email = email_service
        self.templates = template_engine
        self.tools = [
            self.get_interaction_history,
            self.analyze_communication_patterns,
            self.generate_followup_email,
            self.schedule_followup,
            self.send_followup,
            self.track_email_engagement,
            self.escalate_non_responders,
        ]
        self.agent = self._build_agent()
    
    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Follow-up Automation Agent.

Your job is to maintain engagement with contacts through timely, 
personalized follow-up communications.

Follow-up triggers:
- No response after 3 days (soft follow-up)
- No response after 7 days (firm follow-up)
- Post-meeting thank you + summary
- Post-demo next steps
- Deal stage progression check-in
- Re-engagement after 14+ days of silence

Communication guidelines:
- Match the tone and style of previous interactions
- Reference specific points from prior communications
- Keep emails concise (under 150 words for follow-ups)
- Include a clear call-to-action
- Personalize with relevant industry/company insights
- Never send more than 2 follow-ups without human review

Escalation rules:
- 3+ unanswered follow-ups → notify sales rep
- High-value deal going cold → alert manager
- Contact explicitly opts out → suppress all automation
"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    @tool
    def get_interaction_history(self, contact_id: str, days: int = 30) -> dict:
        """Get complete interaction history with a contact."""
        return {
            "emails": self.crm_db.get_emails(contact_id, days=days),
            "calls": self.crm_db.get_calls(contact_id, days=days),
            "meetings": self.crm_db.get_meetings(contact_id, days=days),
            "notes": self.crm_db.get_notes(contact_id, days=days),
            "last_contact": self.crm_db.get_last_contact_date(contact_id),
            "response_rate": self.crm_db.get_response_rate(contact_id),
        }
    
    @tool
    def generate_followup_email(
        self, contact_id: str, context: str, tone: str = "professional"
    ) -> dict:
        """Generate a personalized follow-up email."""
        contact = self.crm_db.get_contact(contact_id)
        history = self.get_interaction_history(contact_id)
        
        # Select and personalize template
        template = self.templates.get_template(
            template_type="followup",
            deal_stage=context,
            tone=tone,
        )
        
        # Build personalization context
        personalization = {
            "contact_name": contact["first_name"],
            "company": contact.get("company", ""),
            "last_interaction": history["last_contact"],
            "previous_topics": self._extract_topics(history["emails"][-3:]),
            "mutual_interests": contact.get("interests", []),
            "industry": contact.get("industry", ""),
        }
        
        # Generate with LLM
        email_prompt = f"""Write a follow-up email to {contact['name']} at {contact.get('company', 'their company')}.

Context: {context}
Tone: {tone}

Previous interaction summary:
{self._summarize_history(history)}

Personalization data:
- Industry: {personalization['industry']}
- Previous topics: {', '.join(personalization['previous_topics'])}

Requirements:
- Subject line under 50 characters
- Body under 150 words
- Reference previous conversation naturally
- Clear call-to-action
- Professional but warm tone
"""
        response = self.llm.invoke(email_prompt)
        email = self._parse_email_response(response.content)
        
        return {
            "to": contact["email"],
            "subject": email["subject"],
            "body": email["body"],
            "personalization_score": self._score_personalization(email, personalization),
        }
    
    @tool
    def schedule_followup(
        self, contact_id: str, followup_type: str, 
        send_at: str, email_data: dict
    ) -> str:
        """Schedule a follow-up email for future delivery."""
        scheduled = {
            "id": str(uuid.uuid4()),
            "contact_id": contact_id,
            "type": followup_type,
            "send_at": send_at,
            "email_data": email_data,
            "status": "scheduled",
            "created_by": "followup_agent",
        }
        self.crm_db.create_scheduled_followup(scheduled)
        
        # Add to Celery beat for delivery
        self._schedule_delivery_task(scheduled)
        
        return f"Follow-up scheduled for {send_at}: {scheduled['id']}"
    
    @tool
    def escalate_non_responders(self, deal_id: str, threshold_days: int = 7) -> dict:
        """Identify and escalate non-responding contacts on a deal."""
        deal = self.crm_db.get_deal(deal_id)
        contacts = self.crm_db.get_deal_contacts(deal_id)
        
        escalations = []
        for contact in contacts:
            history = self.get_interaction_history(contact["id"])
            days_since = (datetime.utcnow() - history["last_contact"]).days
            
            if days_since > threshold_days:
                escalation = {
                    "contact_id": contact["id"],
                    "contact_name": contact["name"],
                    "days_since_contact": days_since,
                    "last_interaction_type": history["emails"][-1]["direction"] if history["emails"] else "none",
                    "recommended_action": self._recommend_escalation_action(
                        contact, history, days_since
                    ),
                }
                escalations.append(escalation)
                
                # Notify sales rep
                self.notification.send(
                    user_id=deal["owner_id"],
                    message=f"⚠️ {contact['name']} hasn't responded in {days_since} days on deal {deal['name']}",
                    channel="slack",
                    priority="high",
                )
        
        return {"escalations": escalations, "deal_id": deal_id}
    
    def _recommend_escalation_action(
        self, contact: dict, history: dict, days_since: int
    ) -> str:
        """Recommend an escalation action based on contact behavior."""
        if days_since > 21:
            return "Consider phone call or LinkedIn message"
        elif history["response_rate"] < 0.2:
            return "Try different communication channel (phone/LinkedIn)"
        elif history["last_contact"] and history["emails"]:
            last_email = history["emails"][-1]
            if last_email["direction"] == "outbound" and not last_email.get("replied"):
                return "Send value-add content (case study, industry report)"
        return "Send personalized re-engagement email"
```

### 6.3 Follow-up Sequence Engine

```python
class FollowUpSequenceEngine:
    """Manages multi-step follow-up sequences."""
    
    SEQUENCES = {
        "post_demo": [
            {"delay_hours": 0, "action": "send_recap", "template": "demo_recap"},
            {"delay_hours": 48, "action": "send_resources", "template": "demo_resources"},
            {"delay_hours": 120, "action": "check_engagement", "condition": "no_response"},
            {"delay_hours": 168, "action": "send_final_followup", "template": "final_followup"},
        ],
        "post_meeting": [
            {"delay_hours": 0, "action": "send_thank_you", "template": "meeting_thanks"},
            {"delay_hours": 24, "action": "send_summary", "template": "meeting_summary"},
            {"delay_hours": 72, "action": "send_next_steps", "template": "next_steps"},
        ],
        "re_engagement": [
            {"delay_hours": 0, "action": "send_value_content", "template": "value_add"},
            {"delay_hours": 72, "action": "send_case_study", "template": "relevant_case_study"},
            {"delay_hours": 168, "action": "send_breakup_email", "template": "breakup_email"},
        ],
    }
    
    def __init__(self, followup_agent: FollowUpAutomationAgent):
        self.agent = followup_agent
    
    async def start_sequence(
        self, contact_id: str, sequence_name: str, context: dict
    ):
        """Start a follow-up sequence for a contact."""
        sequence = self.SEQUENCES.get(sequence_name)
        if not sequence:
            raise ValueError(f"Unknown sequence: {sequence_name}")
        
        for step in sequence:
            # Schedule each step
            send_time = datetime.utcnow() + timedelta(hours=step["delay_hours"])
            
            if step["action"].startswith("send_"):
                email_data = await self.agent.generate_followup_email(
                    contact_id=contact_id,
                    context=context,
                    tone="professional",
                )
                await self.agent.schedule_followup(
                    contact_id=contact_id,
                    followup_type=step["action"],
                    send_at=send_time.isoformat(),
                    email_data=email_data,
                )
            
            elif step["action"] == "check_engagement":
                # Conditional step — check if contact responded
                pass  # Handled by engagement tracking
```

---

## 7. Performance Analytics Agent

### 7.1 Purpose

Provide AI-powered analytics and insights on CRM performance, sales pipeline health, and team productivity.

### 7.2 Agent Implementation

```python
class PerformanceAnalyticsAgent:
    def __init__(self, llm: ChatOpenAI, crm_db, metrics_store):
        self.llm = llm
        self.crm_db = crm_db
        self.metrics = metrics_store  # Time-series DB (e.g., TimescaleDB)
        self.tools = [
            self.get_pipeline_metrics,
            self.get_team_performance,
            self.get_conversion_funnel,
            self.get_forecast_accuracy,
            self.analyze_activity_trends,
            self.generate_weekly_report,
            self.identify_bottlenecks,
            self.compare_periods,
        ]
        self.agent = self._build_agent()
    
    def _build_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Performance Analytics Agent for CRM.

Your capabilities:
- Analyze sales pipeline health and trends
- Generate performance reports and forecasts
- Identify bottlenecks and opportunities
- Compare team/individual performance
- Provide actionable insights

Report types:
- Daily: Key metrics snapshot
- Weekly: Pipeline review + team performance
- Monthly: Comprehensive analysis + forecasting
- Ad-hoc: Custom analysis on demand

Always provide:
1. Data-driven insights (not just numbers)
2. Trend analysis (week-over-week, month-over-month)
3. Anomaly detection
4. Actionable recommendations
5. Visual descriptions (for chart generation)
"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    @tool
    def get_pipeline_metrics(self, period: str = "current_quarter") -> dict:
        """Get comprehensive pipeline metrics."""
        return {
            "total_pipeline_value": self.crm_db.sum_pipeline_value(period),
            "weighted_pipeline_value": self.crm_db.weighted_pipeline_value(period),
            "deal_count_by_stage": self.crm_db.count_deals_by_stage(period),
            "avg_deal_size": self.crm_db.avg_deal_size(period),
            "avg_sales_cycle_days": self.crm_db.avg_sales_cycle(period),
            "win_rate": self.crm_db.win_rate(period),
            "deals_created": self.crm_db.count_new_deals(period),
            "deals_closed": self.crm_db.count_closed_deals(period),
            "pipeline_coverage_ratio": self.crm_db.coverage_ratio(period),
        }
    
    @tool
    def get_team_performance(
        self, team_id: str, period: str = "this_month"
    ) -> dict:
        """Get detailed team performance metrics."""
        members = self.crm_db.get_team_members(team_id)
        performance = {}
        
        for member in members:
            performance[member["id"]] = {
                "name": member["name"],
                "deals_closed": self.crm_db.count_deals_closed(member["id"], period),
                "revenue_closed": self.crm_db.sum_revenue_closed(member["id"], period),
                "activities_completed": self.crm_db.count_activities(member["id"], period),
                "calls_made": self.crm_db.count_calls(member["id"], period),
                "emails_sent": self.crm_db.count_emails(member["id"], period),
                "meetings_held": self.crm_db.count_meetings(member["id"], period),
                "avg_deal_size": self.crm_db.avg_deal_size(member["id"], period),
                "win_rate": self.crm_db.win_rate(member["id"], period),
                "pipeline_generated": self.crm_db.sum_pipeline_created(member["id"], period),
                "quota_attainment": self.crm_db.quota_attainment(member["id"], period),
            }
        
        return performance
    
    @tool
    def get_conversion_funnel(self, period: str = "this_quarter") -> dict:
        """Analyze conversion rates between pipeline stages."""
        stages = ["lead", "qualified", "discovery", "demo", "proposal", "negotiation", "closed_won"]
        funnel = {}
        
        for i in range(len(stages) - 1):
            from_stage = stages[i]
            to_stage = stages[i + 1]
            
            count_from = self.crm_db.count_deals_in_stage(from_stage, period)
            count_to = self.crm_db.count_deals_in_stage(to_stage, period)
            
            conversion_rate = (count_to / count_from * 100) if count_from > 0 else 0
            
            funnel[f"{from_stage}_to_{to_stage}"] = {
                "from_count": count_from,
                "to_count": count_to,
                "conversion_rate": round(conversion_rate, 1),
                "avg_days_in_stage": self.crm_db.avg_days_in_stage(from_stage, period),
            }
        
        return funnel
    
    @tool
    def generate_weekly_report(self, team_id: str) -> str:
        """Generate a comprehensive weekly performance report."""
        metrics = self.get_pipeline_metrics("this_week")
        team_perf = self.get_team_performance(team_id, "this_week")
        funnel = self.get_conversion_funnel("this_week")
        
        report_prompt = f"""Generate a weekly sales performance report.

Pipeline Metrics:
- Total Pipeline: ${metrics['total_pipeline_value']:,.0f}
- Weighted Pipeline: ${metrics['weighted_pipeline_value']:,.0f}
- Win Rate: {metrics['win_rate']:.1%}
- Avg Deal Size: ${metrics['avg_deal_size']:,.0f}
- Avg Sales Cycle: {metrics['avg_sales_cycle_days']:.0f} days

Team Performance:
{self._format_team_performance(team_perf)}

Conversion Funnel:
{self._format_funnel(funnel)}

Generate a report with:
1. Executive Summary (3-4 bullet points)
2. Key Wins & Highlights
3. Areas of Concern
4. Pipeline Movement Analysis
5. Recommendations for Next Week
6. Individual Performance Highlights

Format as markdown with clear sections.
"""
        response = self.llm.invoke(report_prompt)
        return response.content
    
    @tool
    def identify_bottlenecks(self, period: str = "this_quarter") -> list:
        """Identify pipeline bottlenecks and process inefficiencies."""
        bottlenecks = []
        
        # Check stage-level bottlenecks
        funnel = self.get_conversion_funnel(period)
        for stage_transition, data in funnel.items():
            if data["conversion_rate"] < 20:
                bottlenecks.append({
                    "type": "low_conversion",
                    "stage_transition": stage_transition,
                    "conversion_rate": data["conversion_rate"],
                    "severity": "high" if data["conversion_rate"] < 10 else "medium",
                    "recommendation": self._suggest_conversion_improvement(stage_transition),
                })
            if data["avg_days_in_stage"] > 30:
                bottlenecks.append({
                    "type": "slow_stage",
                    "stage_transition": stage_transition,
                    "avg_days": data["avg_days_in_stage"],
                    "severity": "high" if data["avg_days_in_stage"] > 45 else "medium",
                    "recommendation": f"Review {stage_transition.split('_to_')[0]} stage process for efficiency",
                })
        
        # Check individual bottlenecks
        team = self.crm_db.get_team_members("sales")
        for member in team:
            activities = self.crm_db.count_activities(member["id"], period)
            if activities < 20:  # Low activity threshold
                bottlenecks.append({
                    "type": "low_activity",
                    "member": member["name"],
                    "activity_count": activities,
                    "severity": "medium",
                    "recommendation": f"Coach {member['name']} on activity consistency",
                })
        
        return bottlenecks
    
    @tool
    def compare_periods(
        self, metric: str, period1: str, period2: str
    ) -> dict:
        """Compare a metric between two time periods."""
        val1 = self.metrics.get_metric(metric, period1)
        val2 = self.metrics.get_metric(metric, period2)
        
        change = val2 - val1
        pct_change = (change / val1 * 100) if val1 != 0 else 0
        
        return {
            "metric": metric,
            "period1": {"name": period1, "value": val1},
            "period2": {"name": period2, "value": val2},
            "absolute_change": change,
            "percent_change": round(pct_change, 1),
            "trend": "up" if change > 0 else "down" if change < 0 else "flat",
        }
```

### 7.3 Automated Reporting

```python
class AutomatedReporting:
    """Scheduled report generation and distribution."""
    
    def __init__(self, analytics_agent: PerformanceAnalyticsAgent):
        self.agent = analytics_agent
    
    def setup_scheduled_reports(self):
        """Configure automated report schedules."""
        schedules = {
            "daily_metrics": {
                "cron": "0 8 * * *",  # 8 AM daily
                "generator": self._generate_daily_snapshot,
                "recipients": ["sales-manager@company.com"],
            },
            "weekly_review": {
                "cron": "0 9 * * 1",  # Monday 9 AM
                "generator": self._generate_weekly_report,
                "recipients": ["sales-team@company.com"],
            },
            "monthly_analysis": {
                "cron": "0 9 1 * *",  # 1st of month, 9 AM
                "generator": self._generate_monthly_report,
                "recipients": ["leadership@company.com"],
            },
        }
        return schedules
    
    def _generate_daily_snapshot(self) -> str:
        """Generate daily metrics snapshot."""
        metrics = self.agent.get_pipeline_metrics("today")
        return f"""📊 Daily CRM Snapshot

Pipeline: ${metrics['total_pipeline_value']:,.0f}
New Deals: {metrics['deals_created']}
Closed: {metrics['deals_closed']}
Win Rate: {metrics['win_rate']:.1%}
"""
    
    def _generate_weekly_report(self) -> str:
        """Generate weekly performance report."""
        return self.agent.generate_weekly_report("sales-team-1")
    
    def _generate_monthly_report(self) -> str:
        """Generate monthly comprehensive report."""
        # Comprehensive monthly analysis
        metrics = self.agent.get_pipeline_metrics("this_month")
        bottlenecks = self.agent.identify_bottlenecks("this_month")
        # ... compile full report
        return report_content
```

---

## 8. Code Examples & Snippets

### 8.1 Project Structure

```
crm-enhancement/
├── pyproject.toml
├── docker-compose.yml
├── alembic/
│   └── versions/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Settings management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── contact.py
│   │   ├── deal.py
│   │   ├── task.py
│   │   ├── meeting.py
│   │   └── analytics.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py               # Base agent class
│   │   ├── orchestrator.py        # Main orchestrator
│   │   ├── contact_enrichment.py
│   │   ├── deal_scoring.py
│   │   ├── task_automation.py
│   │   ├── meeting_scheduling.py
│   │   ├── followup_automation.py
│   │   └── analytics.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── crm_tools.py          # CRM database tools
│   │   ├── calendar_tools.py      # Calendar integration tools
│   │   ├── email_tools.py         # Email service tools
│   │   └── external_api_tools.py  # Clearbit, LinkedIn, etc.
│   ├── services/
│   │   ├── __init__.py
│   │   ├── crm_db.py
│   │   ├── vector_store.py
│   │   ├── llm_gateway.py
│   │   └── notification.py
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── enrichment.py
│   │   ├── scoring.py
│   │   └── followup.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── contacts.py
│   │   │   ├── deals.py
│   │   │   ├── tasks.py
│   │   │   ├── meetings.py
│   │   │   └── analytics.py
│   │   └── websockets.py
│   └── workers/
│       ├── __init__.py
│       ├── celery_app.py
│       └── scheduled_tasks.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/
```

### 8.2 Base Agent Class

```python
# src/agents/base.py
from abc import ABC, abstractmethod
from typing import Any
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate

class BaseCRMAgent(ABC):
    """Base class for all CRM agents."""
    
    def __init__(
        self,
        llm: BaseLanguageModel,
        tools: list[BaseTool],
        system_prompt: str,
        max_iterations: int = 10,
        verbose: bool = False,
    ):
        self.llm = llm
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.executor = self._build_executor()
    
    def _build_executor(self) -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=self.verbose,
            max_iterations=self.max_iterations,
            handle_parsing_errors=True,
            early_stopping_method="generate",
        )
    
    async def run(self, input_data: dict[str, Any]) -> dict:
        """Run the agent with the given input."""
        result = await self.executor.ainvoke(input_data)
        return {
            "output": result["output"],
            "intermediate_steps": result.get("intermediate_steps", []),
            "success": not result.get("error"),
        }
    
    @abstractmethod
    def get_agent_info(self) -> dict:
        """Return agent metadata."""
        pass
```

### 8.3 Orchestrator Implementation

```python
# src/agents/orchestrator.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

class CRMAgentOrchestrator:
    """Central orchestrator that routes tasks to specialized agents."""
    
    def __init__(self, llm: ChatOpenAI, agents: dict):
        self.llm = llm
        self.agents = agents  # {name: agent_instance}
        self.router = self._build_router()
    
    def _build_router(self):
        agent_descriptions = "\n".join([
            f"- {name}: {agent.get_agent_info()['description']}"
            for name, agent in self.agents.items()
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are the CRM Agent Orchestrator.

You route incoming requests to the appropriate specialized agent.

Available agents:
{agent_descriptions}

Routing rules:
- Contact data enrichment → contact_enrichment agent
- Deal scoring/prioritization → deal_scoring agent
- Task creation/management → task_automation agent
- Meeting scheduling → meeting_scheduling agent
- Follow-up communications → followup_automation agent
- Performance analysis/reporting → analytics agent

For complex requests, you can chain multiple agents.
Always confirm the routing decision before executing.
"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        # Router tools: delegate to each agent
        delegate_tools = [
            self._create_delegate_tool(name, agent)
            for name, agent in self.agents.items()
        ]
        
        agent = create_react_agent(self.llm, delegate_tools, prompt)
        return AgentExecutor(agent=agent, tools=delegate_tools, verbose=True)
    
    def _create_delegate_tool(self, name: str, agent):
        @tool
        def delegate_to_agent(input_data: str) -> str:
            """Delegate a task to the {name} agent."""
            result = agent.run({"input": input_data})
            return result["output"]
        
        delegate_to_agent.name = f"delegate_to_{name}"
        delegate_to_agent.description = f"Route task to {name} agent"
        return delegate_to_agent
    
    async def handle_request(self, request: dict) -> dict:
        """Handle an incoming CRM request."""
        result = await self.router.ainvoke({
            "input": request["query"],
            "context": request.get("context", {}),
        })
        return {
            "response": result["output"],
            "agent_used": self._detect_agent_used(result),
            "timestamp": datetime.utcnow().isoformat(),
        }
```

### 8.4 LLM Gateway with Fallback

```python
# src/services/llm_gateway.py
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseLanguageModel
from functools import wraps
import random

class LLMGateway:
    """Unified LLM access with fallback and load balancing."""
    
    def __init__(self, config: dict):
        self.providers = {
            "openai": ChatOpenAI(
                model=config.get("openai_model", "gpt-4o"),
                temperature=0.1,
                max_retries=2,
            ),
            "anthropic": ChatAnthropic(
                model=config.get("anthropic_model", "claude-sonnet-4-20250514"),
                temperature=0.1,
                max_retries=2,
            ),
        }
        self.fallback_order = config.get("fallback_order", ["openai", "anthropic"])
        self.current_index = 0
        self.circuit_breakers = {
            name: {"failures": 0, "open": False, "last_failure": None}
            for name in self.providers
        }
    
    def get_llm(self, prefer: str = None) -> BaseLanguageModel:
        """Get an LLM provider with circuit breaker pattern."""
        order = [prefer] + [p for p in self.fallback_order if p != prefer] if prefer else self.fallback_order
        
        for provider_name in order:
            if self._is_available(provider_name):
                return self.providers[provider_name]
        
        raise RuntimeError("All LLM providers unavailable")
    
    def _is_available(self, provider_name: str) -> bool:
        cb = self.circuit_breakers[provider_name]
        if not cb["open"]:
            return True
        # Half-open after 60 seconds
        if cb["last_failure"] and (datetime.utcnow() - cb["last_failure"]).seconds > 60:
            cb["open"] = False
            cb["failures"] = 0
            return True
        return False
    
    def report_failure(self, provider_name: str):
        cb = self.circuit_breakers[provider_name]
        cb["failures"] += 1
        cb["last_failure"] = datetime.utcnow()
        if cb["failures"] >= 3:
            cb["open"] = True
    
    def report_success(self, provider_name: str):
        cb = self.circuit_breakers[provider_name]
        cb["failures"] = 0
        cb["open"] = False
```

### 8.5 Vector Store Setup

```python
# src/services/vector_store.py
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

class CRMVectorStore:
    """Vector store for semantic search over CRM entities."""
    
    def __init__(self, connection_string: str):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.store = PGVector(
            connection_string=connection_string,
            embedding_function=self.embeddings,
            collection_name="crm_entities",
        )
    
    def index_contact(self, contact: dict):
        """Index a contact for semantic search."""
        text = f"""
        Name: {contact['name']}
        Title: {contact.get('title', '')}
        Company: {contact.get('company', '')}
        Industry: {contact.get('industry', '')}
        Interests: {', '.join(contact.get('interests', []))}
        Notes: {contact.get('notes', '')}
        """
        doc = Document(
            page_content=text,
            metadata={
                "entity_type": "contact",
                "entity_id": contact["id"],
                "email": contact.get("email", ""),
            }
        )
        self.store.add_documents([doc])
    
    def index_deal(self, deal: dict):
        """Index a deal for semantic search."""
        text = f"""
        Deal: {deal['name']}
        Stage: {deal['stage']}
        Value: ${deal['value']}
        Company: {deal.get('company', '')}
        Description: {deal.get('description', '')}
        """
        doc = Document(
            page_content=text,
            metadata={
                "entity_type": "deal",
                "entity_id": deal["id"],
                "status": deal.get("status", ""),
                "value": deal.get("value", 0),
            }
        )
        self.store.add_documents([doc])
    
    def find_similar_deals(
        self, deal: dict, k: int = 5, filters: dict = None
    ) -> list:
        """Find similar deals using semantic search."""
        query = f"{deal['name']} {deal.get('description', '')} {deal.get('company', '')}"
        return self.store.similarity_search_with_score(
            query, k=k, filter=filters
        )
    
    def find_duplicate_contacts(self, contact: dict, threshold: float = 0.85) -> list:
        """Find potential duplicate contacts."""
        query = f"{contact['name']} {contact.get('company', '')} {contact.get('email', '')}"
        results = self.store.similarity_search_with_score(
            query, k=5,
            filter={"entity_type": "contact"}
        )
        return [
            {"metadata": r[0].metadata, "score": r[1]}
            for r in results
            if r[1] >= threshold and r[0].metadata["entity_id"] != contact["id"]
        ]
```

### 8.6 FastAPI Application Entry

```python
# src/main.py
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.agents.orchestrator import CRMAgentOrchestrator
from src.services.llm_gateway import LLMGateway

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.llm_gateway = LLMGateway(config.llm)
    app.state.orchestrator = CRMAgentOrchestrator(
        llm=app.state.llm_gateway.get_llm(),
        agents=initialize_agents(app.state.llm_gateway)
    )
    yield
    # Shutdown
    await cleanup_resources()

app = FastAPI(
    title="CRM Enhancement API",
    description="AI-powered CRM enhancement using LangChain DeepAgents",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/crm/request")
async def handle_crm_request(request: CRMRequest):
    """Main endpoint for CRM agent requests."""
    orchestrator = app.state.orchestrator
    result = await orchestrator.handle_request({
        "query": request.query,
        "context": request.context,
    })
    return result

@app.post("/api/v1/contacts/{contact_id}/enrich")
async def enrich_contact(contact_id: str):
    """Trigger contact enrichment."""
    agent = app.state.orchestrator.agents["contact_enrichment"]
    result = await agent.run({"input": f"Enrich contact {contact_id}"})
    return result

@app.post("/api/v1/deals/{deal_id}/score")
async def score_deal(deal_id: str):
    """Trigger deal scoring."""
    agent = app.state.orchestrator.agents["deal_scoring"]
    result = await agent.run({"input": f"Score deal {deal_id}"})
    return result

@app.websocket("/ws/crm")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time CRM agent interactions."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            result = await app.state.orchestrator.handle_request(data)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        pass
```

### 8.7 Docker Compose Configuration

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://crm:crm@postgres:5432/crm_db
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - postgres
      - redis
      - worker

  worker:
    build: .
    command: celery -A src.workers.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://crm:crm@postgres:5432/crm_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  scheduler:
    build: .
    command: celery -A src.workers.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://crm:crm@postgres:5432/crm_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=crm
      - POSTGRES_PASSWORD=crm
      - POSTGRES_DB=crm_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 9. Testing Strategy

### 9.1 Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5%)  - Full workflow tests
                   ┌┴─────────┴┐
                   │ Integration│ (15%) - Agent + DB + LLM tests
                  ┌┴───────────┴┐
                  │    Unit      │ (80%) - Individual components
                 ┌┴─────────────┴┐
                 │  Static Analysis │       - Type checking, linting
                 └────────────────┘
```

### 9.2 Unit Tests

```python
# tests/unit/test_deal_scoring.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.deal_scoring import DealScoringAgent

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.invoke.return_value.content = '{"score": 75, "recommendation": "Follow up"}'
    return llm

@pytest.fixture
def mock_crm_db():
    db = MagicMock()
    db.get_deal.return_value = {
        "id": "deal-123",
        "name": "Test Deal",
        "stage": "demo",
        "value": 50000,
        "contacts": [{"id": "contact-1"}],
    }
    db.get_deal_activities.return_value = []
    return db

@pytest.fixture
def scoring_agent(mock_llm, mock_crm_db):
    return DealScoringAgent(llm=mock_llm, crm_db=mock_crm_db, model_registry=MagicMock())

class TestDealScoringAgent:
    def test_score_deal_returns_valid_score(self, scoring_agent):
        """Test that deal scoring returns a valid score."""
        with patch.object(scoring_agent, 'get_deal_details', return_value={
            "id": "deal-123", "stage": "demo", "value": 50000,
            "contacts": [{"id": "c1"}], "days_in_current_stage": 5
        }):
            with patch.object(scoring_agent, 'get_contact_engagement_history', return_value={
                "c1": {
                    "email_opens_30d": 10,
                    "email_replies_30d": 3,
                    "meetings_held": 2,
                    "last_interaction": datetime.utcnow(),
                    "response_time_avg_hours": 12,
                }
            }):
                with patch.object(scoring_agent, 'get_similar_closed_deals', return_value=[]):
                    with patch.object(scoring_agent, 'analyze_email_sentiment', return_value={
                        "overall_trend": "positive",
                        "recent_sentiments": [],
                        "objection_count": 0,
                    }):
                        score = scoring_agent.score_deal("deal-123")
                        assert 0 <= score.overall_score <= 100
                        assert 0 <= score.win_probability <= 1
    
    def test_classify_temperature_hot(self, scoring_agent):
        """Test hot deal classification."""
        temp = scoring_agent._classify_temperature(
            score=85,
            deal={"days_in_current_stage": 3},
            engagement={}
        )
        assert temp == "hot"
    
    def test_classify_temperature_stalled(self, scoring_agent):
        """Test stalled deal classification."""
        temp = scoring_agent._classify_temperature(
            score=60,
            deal={"days_in_current_stage": 45},
            engagement={}
        )
        assert temp == "stalled"
    
    def test_engagement_score_calculation(self, scoring_agent):
        """Test engagement score computation."""
        engagement = {
            "c1": {
                "email_opens_30d": 15,
                "email_replies_30d": 5,
                "meetings_held": 3,
                "last_interaction": datetime.utcnow() - timedelta(days=2),
                "response_time_avg_hours": 6,
            }
        }
        score = scoring_agent._score_engagement(engagement)
        assert score > 80  # High engagement should score well
    
    def test_engagement_score_low_activity(self, scoring_agent):
        """Test engagement score with low activity."""
        engagement = {
            "c1": {
                "email_opens_30d": 0,
                "email_replies_30d": 0,
                "meetings_held": 0,
                "last_interaction": datetime.utcnow() - timedelta(days=30),
                "response_time_avg_hours": 999,
            }
        }
        score = scoring_agent._score_engagement(engagement)
        assert score < 30  # Low engagement should score poorly
```

### 9.3 Integration Tests

```python
# tests/integration/test_enrichment_pipeline.py
import pytest
import pytest_asyncio
from src.agents.contact_enrichment import ContactEnrichmentAgent
from src.services.vector_store import CRMVectorStore

@pytest_asyncio.fixture
async def enrichment_agent():
    """Create a test enrichment agent with mocked external APIs."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    crm_db = TestCRMDB()  # In-memory test database
    vector_store = CRMVectorStore("postgresql://test:test@localhost:5432/test_db")
    
    agent = ContactEnrichmentAgent(llm=llm, crm_db=crm_db, vector_store=vector_store)
    yield agent
    await crm_db.cleanup()

class TestContactEnrichmentPipeline:
    @pytest.mark.asyncio
    async def test_full_enrichment_workflow(self, enrichment_agent):
        """Test the complete contact enrichment workflow."""
        # Setup test contact
        contact_id = await enrichment_agent.crm_db.create_contact({
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Example Corp",
        })
        
        # Mock external API responses
        with patch.object(enrichment_agent, '_query_clearbit') as mock_clearbit:
            mock_clearbit.return_value = {
                "title": "VP of Sales",
                "company_size": "500-1000",
                "industry": "Technology",
            }
            
            result = await enrichment_agent.agent.ainvoke({
                "input": f"Enrich contact {contact_id}"
            })
            
            assert "enriched" in result["output"].lower() or "updated" in result["output"].lower()
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, enrichment_agent):
        """Test duplicate contact detection."""
        # Create two similar contacts
        c1 = await enrichment_agent.crm_db.create_contact({
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Example Corp",
        })
        c2 = await enrichment_agent.crm_db.create_contact({
            "name": "Jon Doe",
            "email": "jon@example.com",
            "company": "Example Corp",
        })
        
        # Index both
        enrichment_agent.vector_store.index_contact(
            await enrichment_agent.crm_db.get_contact(c1)
        )
        enrichment_agent.vector_store.index_contact(
            await enrichment_agent.crm_db.get_contact(c2)
        )
        
        # Check for duplicates
        duplicates = enrichment_agent.find_duplicate_contacts(c1)
        assert len(duplicates) > 0
```

### 9.4 LLM Response Testing

```python
# tests/unit/test_llm_responses.py
import pytest
from langchain_core.outputs import LLMResult, Generation

class TestLLMResponses:
    """Test LLM response parsing and validation."""
    
    def test_deal_score_response_parsing(self):
        """Test that LLM responses are correctly parsed into structured data."""
        raw_response = """
        Based on my analysis:
        - Overall Score: 72/100
        - Win Probability: 65%
        - Temperature: Warm
        - Risk Factors: Limited engagement from decision maker
        - Recommended Actions: Schedule executive briefing
        """
        
        parsed = parse_deal_score_response(raw_response)
        assert parsed["overall_score"] == 72
        assert parsed["win_probability"] == 0.65
        assert parsed["deal_temperature"] == "warm"
    
    def test_email_generation_quality(self):
        """Test that generated emails meet quality criteria."""
        agent = FollowUpAutomationAgent(...)
        email = agent.generate_followup_email(
            contact_id="test-123",
            context="post_demo",
            tone="professional"
        )
        
        # Quality assertions
        assert len(email["subject"]) < 50
        assert len(email["body"].split()) < 150
        assert email["personalization_score"] > 0.7
        assert "unsubscribe" not in email["body"].lower()  # Not a marketing email
    
    def test_meeting_slot_scoring(self):
        """Test meeting slot scoring logic."""
        agent = MeetingSchedulingAgent(...)
        
        slot = {
            "start": "2026-10-15T14:00:00Z",
            "end": "2026-10-15T14:30:00Z",
        }
        availability = {
            "person1@example.com": {
                "busy_slots": [],
                "timezone": "America/New_York",
            },
            "person2@example.com": {
                "busy_slots": [],
                "timezone": "Europe/London",
            },
        }
        
        score = agent._score_slot(
            slot, availability, 
            ["person1@example.com", "person2@example.com"]
        )
        assert score > 0  # Should be a valid slot
```

### 9.5 End-to-End Tests

```python
# tests/e2e/test_crm_workflows.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from src.main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

class TestE2EWorkflows:
    """End-to-end workflow tests."""
    
    @pytest.mark.asyncio
    async def test_deal_scoring_workflow(self, client):
        """Test complete deal scoring workflow via API."""
        # Create a test deal
        deal_response = await client.post("/api/v1/deals", json={
            "name": "E2E Test Deal",
            "value": 100000,
            "stage": "discovery",
            "contacts": [{"name": "Test Contact", "email": "test@example.com"}],
        })
        deal_id = deal_response.json()["id"]
        
        # Trigger scoring
        score_response = await client.post(f"/api/v1/deals/{deal_id}/score")
        assert score_response.status_code == 200
        
        score_data = score_response.json()
        assert "overall_score" in score_data
        assert "win_probability" in score_data
        assert "recommended_actions" in score_data
    
    @pytest.mark.asyncio
    async def test_contact_enrichment_workflow(self, client):
        """Test complete contact enrichment workflow via API."""
        # Create a test contact
        contact_response = await client.post("/api/v1/contacts", json={
            "name": "Jane Smith",
            "email": "jane@techcorp.com",
            "company": "TechCorp",
        })
        contact_id = contact_response.json()["id"]
        
        # Trigger enrichment
        enrich_response = await client.post(
            f"/api/v1/contacts/{contact_id}/enrich"
        )
        assert enrich_response.status_code == 200
        
        result = enrich_response.json()
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_orchestrator_routing(self, client):
        """Test that the orchestrator correctly routes requests."""
        # Test contact enrichment routing
        response = await client.post("/api/v1/crm/request", json={
            "query": "Enrich the contact record for John Doe at Acme Corp",
            "context": {"contact_id": "test-123"},
        })
        assert response.status_code == 200
        result = response.json()
        assert "contact_enrichment" in result.get("agent_used", "")
    
    @pytest.mark.asyncio
    async def test_analytics_report_generation(self, client):
        """Test analytics report generation."""
        response = await client.post("/api/v1/analytics/report", json={
            "report_type": "weekly",
            "team_id": "sales-team-1",
        })
        assert response.status_code == 200
        report = response.json()
        assert "content" in report
        assert len(report["content"]) > 100  # Substantial report
```

### 9.6 Performance Tests

```python
# tests/performance/test_agent_performance.py
import pytest
import time
from statistics import mean, stdev

class TestAgentPerformance:
    """Performance benchmarks for CRM agents."""
    
    @pytest.mark.benchmark
    def test_deal_scoring_latency(self, benchmark):
        """Benchmark deal scoring latency."""
        agent = DealScoringAgent(...)
        
        result = benchmark(agent.score_deal, "test-deal-123")
        assert result.stats.mean < 5.0  # Should complete in under 5 seconds
    
    @pytest.mark.benchmark
    def test_contact_enrichment_latency(self, benchmark):
        """Benchmark contact enrichment latency."""
        agent = ContactEnrichmentAgent(...)
        
        result = benchmark(agent.enrich_contact, "test-contact-123")
        assert result.stats.mean < 10.0  # Should complete in under 10 seconds
    
    def test_concurrent_deal_scoring(self):
        """Test concurrent deal scoring doesn't degrade performance."""
        agent = DealScoringAgent(...)
        deal_ids = [f"deal-{i}" for i in range(20)]
        
        start = time.time()
        # Score 20 deals concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(agent.score_deal, deal_id)
                for deal_id in deal_ids
            ]
            results = [f.result() for f in futures]
        elapsed = time.time() - start
        
        # Should complete 20 scores in under 30 seconds
        assert elapsed < 30
        assert len(results) == 20
    
    def test_memory_usage_under_load(self):
        """Test memory usage remains bounded under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        agent = DealScoringAgent(...)
        # Process 100 deals
        for i in range(100):
            agent.score_deal(f"deal-{i}")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be under 200MB
        assert memory_increase < 200
```

### 9.7 Test Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    benchmark: Performance benchmark tests
    integration: Integration tests requiring external services
    e2e: End-to-end tests
    slow: Slow tests (skip in CI quick mode)
addopts = -v --tb=short --strict-markers
```

```python
# conftest.py
import pytest
import os

def pytest_configure(config):
    """Configure test environment."""
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "test-key")
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "test-key")
    os.environ["DATABASE_URL"] = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql://test:test@localhost:5432/test_crm"
    )

@pytest.fixture(scope="session")
def test_db():
    """Create a test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    engine.dispose()
```

### 9.8 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: CRM Enhancement Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_crm
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run linting
        run: |
          ruff check src tests
          mypy src
      
      - name: Run unit tests
        run: |
          pytest tests/unit -v --cov=src --cov-report=xml
      
      - name: Run integration tests
        run: |
          pytest tests/integration -v
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_crm
          REDIS_URL: redis://localhost:6379/0
      
      - name: Run E2E tests
        run: |
          pytest tests/e2e -v
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_crm
          REDIS_URL: redis://localhost:6379/0
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Appendix A: Environment Variables

```bash
# .env.example
# Database
DATABASE_URL=postgresql://crm:crm_password@localhost:5432/crm_db
REDIS_URL=redis://localhost:6379/0

# LLM Providers
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
LLM_FALLBACK_ORDER=openai,anthropic

# External APIs
CLEARBIT_API_KEY=clearbit_...
PROXYCURL_API_KEY=proxycurl_...
GOOGLE_CALENDAR_CREDENTIALS=credentials.json
OUTLOOK_CREDENTIALS=credentials.json

# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000

# Feature Flags
ENABLE_CONTACT_ENRICHMENT=true
ENABLE_DEAL_SCORING=true
ENABLE_TASK_AUTOMATION=true
ENABLE_MEETING_SCHEDULING=true
ENABLE_FOLLOWUP_AUTOMATION=true
ENABLE_ANALYTICS=true
HUMAN_APPROVAL_REQUIRED=true
```

## Appendix B: Deployment Checklist

- [ ] Set up PostgreSQL with pgvector extension
- [ ] Configure Redis for caching and message broker
- [ ] Set up Celery workers and beat scheduler
- [ ] Configure LLM API keys and rate limits
- [ ] Set up external API integrations (Clearbit, Proxycurl, etc.)
- [ ] Configure calendar service credentials
- [ ] Set up email service (SendGrid, SES, etc.)
- [ ] Configure monitoring and alerting (Sentry, Datadog)
- [ ] Set up CI/CD pipeline
- [ ] Configure backup and disaster recovery
- [ ] Security audit and penetration testing
- [ ] GDPR/CCPA compliance review
- [ ] Load testing and performance optimization
- [ ] Documentation and runbooks

---

*End of Implementation Plan*
