# AI-Powered Customer Service Implementation with LangChain DeepAgents

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Triage Agent Implementation](#2-triage-agent-implementation)
3. [Resolution Agent Implementation](#3-resolution-agent-implementation)
4. [Escalation Agent Implementation](#4-escalation-agent-implementation)
5. [Sentiment Analysis Agent Implementation](#5-sentiment-analysis-agent-implementation)
6. [Customer Success Agent Implementation](#6-customer-success-agent-implementation)
7. [Knowledge Base Integration](#7-knowledge-base-integration)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered customer service system uses LangChain DeepAgents to create a multi-agent architecture that handles customer inquiries end-to-end. The system consists of five specialized agents coordinated by a central orchestrator:

- **Triage Agent**: Classifies incoming requests and routes them appropriately
- **Resolution Agent**: Handles standard customer queries and resolves issues
- **Escalation Agent**: Manages complex cases requiring human intervention
- **Sentiment Analysis Agent**: Monitors customer emotion and adjusts responses
- **Customer Success Agent**: Proactively engages customers for retention and growth

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Customer Touchpoints                         │
│  (Email, Chat, Social Media, Phone, Web Portal, Mobile App)     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                            │
│  - Request classification                                        │
│  - Agent routing                                                 │
│  - Context management                                            │
│  - Response aggregation                                          │
└───────┬──────────────┬──────────────┬──────────────┬────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│    Triage    │ │  Resolution  │ │  Escalation  │ │   Sentiment  │
│    Agent     │ │    Agent     │ │    Agent     │ │    Agent     │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │
       └────────────────┴────────────────┴────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Customer Success Agent                        │
│  - Proactive outreach                                            │
│  - Health scoring                                                │
│  - Retention campaigns                                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Knowledge Base Layer                          │
│  - Vector store (Pinecone/Weaviate/Chroma)                       │
│  - Product documentation                                         │
│  - FAQ database                                                  │
│  - Historical tickets                                           │
│  - Policy documents                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Multi-agent orchestration |
| LLM | GPT-4 / Claude 3.5 | Natural language understanding |
| Vector Store | Pinecone / Weaviate | Knowledge retrieval |
| Message Queue | Redis / RabbitMQ | Async processing |
| Database | PostgreSQL | Ticket and customer data |
| Cache | Redis | Session and context caching |
| Monitoring | LangSmith | Tracing and observability |
| API Layer | FastAPI | REST endpoints |

### 1.4 Data Flow

1. **Ingestion**: Customer messages arrive via API gateway
2. **Pre-processing**: Message normalization, language detection, PII redaction
3. **Triage**: Classification and routing decision
4. **Agent Execution**: Specialized agent processes the request
5. **Knowledge Retrieval**: Relevant context fetched from vector store
6. **Response Generation**: Agent crafts response with retrieved context
7. **Sentiment Check**: Emotional tone validated before sending
8. **Delivery**: Response sent back through original channel
9. **Feedback Loop**: Customer satisfaction captured for learning

### 1.5 Configuration

```python
# config/settings.py
from pydantic_settings import BaseSettings
from typing import List

class CustomerServiceSettings(BaseSettings):
    # LLM Configuration
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2048

    # Agent Configuration
    max_agent_iterations: int = 10
    agent_timeout_seconds: int = 120
    enable_streaming: bool = True

    # Knowledge Base Configuration
    vector_store_provider: str = "pinecone"
    vector_store_index: str = "customer-service-kb"
    embedding_model: str = "text-embedding-3-small"
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.75

    # Escalation Configuration
    escalation_confidence_threshold: float = 0.6
    max_auto_resolution_attempts: int = 3
    human_handoff_timeout_minutes: int = 30

    # Sentiment Configuration
    sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    negative_sentiment_threshold: float = -0.5
    escalation_sentiment_threshold: float = -0.7

    # Customer Success Configuration
    health_score_threshold: float = 0.4
    proactive_outreach_interval_days: int = 30
    churn_risk_threshold: float = 0.3

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    class Config:
        env_prefix = "CS_"

settings = CustomerServiceSettings()
```

---

## 2. Triage Agent Implementation

### 2.1 Purpose and Responsibilities

The Triage Agent is the first point of contact for all incoming customer messages. Its primary responsibilities include:

- **Intent Classification**: Determine the customer's intent (billing, technical, account, general inquiry)
- **Priority Assessment**: Assign urgency based on content and customer tier
- **Routing Decision**: Select the appropriate specialized agent
- **Context Extraction**: Pull out key entities (order IDs, product names, dates)
- **Language Detection**: Identify the customer's language for routing

### 2.2 Agent Definition

```python
# agents/triage_agent.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config.settings import settings

TRIAGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Triage Agent for customer service.
Your role is to classify incoming customer messages and route them appropriately.

Classification Categories:
1. BILLING - Invoices, payments, refunds, pricing questions
2. TECHNICAL - Bug reports, feature requests, how-to questions
3. ACCOUNT - Login issues, profile changes, security concerns
4. PRODUCT - Product information, recommendations, comparisons
5. COMPLAINT - Service complaints, dissatisfaction, cancellation requests
6. GENERAL - Greetings, small talk, unclear requests

Priority Levels:
- CRITICAL: Service outage, security breach, VIP customer complaint
- HIGH: Billing errors, account lockouts, urgent technical issues
- MEDIUM: General technical questions, product inquiries
- LOW: General feedback, non-urgent questions

For each message, provide:
1. The classification category
2. The priority level
3. Key entities mentioned (order IDs, product names, dates)
4. Recommended routing target
5. Confidence score (0.0 to 1.0)

Be concise and accurate. If unsure, route to the Resolution Agent with MEDIUM priority."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

@tool
def classify_intent(message: str, customer_tier: str = "standard") -> dict:
    """Classify the customer message intent and priority.

    Args:
        message: The customer's message text
        customer_tier: Customer tier (basic, standard, premium, enterprise)

    Returns:
        Dictionary with classification results
    """
    # Implementation uses LLM for classification
    llm = ChatOpenAI(model=settings.llm_model, temperature=0.1)

    classification_prompt = f"""Classify this customer message:
Message: {message}
Customer Tier: {customer_tier}

Return JSON with: category, priority, entities, routing_target, confidence"""

    response = llm.invoke(classification_prompt)
    # Parse and validate response
    return parse_classification(response.content)

@tool
def extract_entities(message: str) -> dict:
    """Extract key entities from the customer message.

    Args:
        message: The customer's message text

    Returns:
        Dictionary of extracted entities
    """
    llm = ChatOpenAI(model=settings.llm_model, temperature=0.0)

    entity_prompt = f"""Extract entities from this message:
{message}

Look for: order IDs, product names, dates, email addresses, phone numbers,
account numbers, and any other relevant identifiers.

Return as JSON with entity types as keys."""

    response = llm.invoke(entity_prompt)
    return parse_entities(response.content)

@tool
def detect_language(message: str) -> str:
    """Detect the language of the customer message.

    Args:
        message: The customer's message text

    Returns:
        ISO 639-1 language code
    """
    # Use langdetect or similar library
    from langdetect import detect
    try:
        return detect(message)
    except:
        return "en"

def create_triage_agent() -> AgentExecutor:
    """Create and configure the Triage Agent."""
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.1,
        max_tokens=settings.llm_max_tokens
    )

    tools = [classify_intent, extract_entities, detect_language]

    agent = create_openai_functions_agent(llm, tools, TRIAGE_PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=settings.max_agent_iterations,
        handle_parsing_errors=True
    )

def parse_classification(content: str) -> dict:
    """Parse the LLM classification response."""
    import json
    try:
        # Extract JSON from response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        return json.loads(content[json_start:json_end])
    except (json.JSONDecodeError, ValueError):
        return {
            "category": "GENERAL",
            "priority": "MEDIUM",
            "entities": {},
            "routing_target": "resolution_agent",
            "confidence": 0.5
        }

def parse_entities(content: str) -> dict:
    """Parse the LLM entity extraction response."""
    import json
    try:
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        return json.loads(content[json_start:json_end])
    except (json.JSONDecodeError, ValueError):
        return {}
```

### 2.3 Routing Logic

```python
# agents/routing.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class AgentType(Enum):
    RESOLUTION = "resolution_agent"
    ESCALATION = "escalation_agent"
    SENTIMENT = "sentiment_agent"
    CUSTOMER_SUCCESS = "customer_success_agent"

class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class RoutingDecision:
    target_agent: AgentType
    priority: Priority
    confidence: float
    context: dict
    reason: str

class Router:
    """Routes customer messages to appropriate agents."""

    def __init__(self):
        self.triage_agent = create_triage_agent()

    async def route(self, message: str, customer_context: dict) -> RoutingDecision:
        """Route a customer message to the appropriate agent."""

        # Run triage classification
        triage_result = await self.triage_agent.ainvoke({
            "input": message,
            "chat_history": customer_context.get("chat_history", [])
        })

        classification = parse_classification(triage_result["output"])

        # Determine routing based on classification
        target_agent = self._determine_target(classification, customer_context)
        priority = self._determine_priority(classification, customer_context)

        return RoutingDecision(
            target_agent=target_agent,
            priority=priority,
            confidence=classification.get("confidence", 0.5),
            context=classification,
            reason=f"Classified as {classification.get('category', 'UNKNOWN')}"
        )

    def _determine_target(self, classification: dict, customer_context: dict) -> AgentType:
        """Determine which agent should handle this message."""
        category = classification.get("category", "GENERAL")
        confidence = classification.get("confidence", 0.5)

        # Low confidence always goes to resolution agent
        if confidence < settings.escalation_confidence_threshold:
            return AgentType.RESOLUTION

        # Complaints and critical issues go to escalation
        if category in ["COMPLAINT"]:
            return AgentType.ESCALATION

        # Check customer health score for proactive routing
        health_score = customer_context.get("health_score", 1.0)
        if health_score < settings.health_score_threshold:
            return AgentType.CUSTOMER_SUCCESS

        # Default to resolution agent
        return AgentType.RESOLUTION

    def _determine_priority(self, classification: dict, customer_context: dict) -> Priority:
        """Determine message priority."""
        category = classification.get("category", "GENERAL")
        customer_tier = customer_context.get("tier", "standard")

        # Enterprise customers get bumped up one priority level
        tier_boost = 1 if customer_tier == "enterprise" else 0

        priority_map = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1
        }

        base_priority = priority_map.get(classification.get("priority", "MEDIUM"), 2)
        adjusted = min(base_priority + tier_boost, 4)

        priority_reverse = {v: k for k, v in priority_map.items()}
        return Priority(priority_reverse.get(adjusted, "MEDIUM").lower())
```

---

## 3. Resolution Agent Implementation

### 3.1 Purpose and Responsibilities

The Resolution Agent handles the majority of customer inquiries that can be resolved without human intervention:

- **Answer FAQs**: Respond to common questions using knowledge base
- **Troubleshoot Issues**: Guide customers through technical troubleshooting
- **Process Requests**: Handle address changes, password resets, etc.
- **Provide Information**: Share product details, policies, and procedures
- **Create Tickets**: Log issues that need follow-up

### 3.2 Agent Definition

```python
# agents/resolution_agent.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config.settings import settings

RESOLUTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Resolution Agent for customer service.
Your goal is to resolve customer inquiries efficiently and accurately.

Guidelines:
1. Always search the knowledge base before answering
2. Provide step-by-step instructions for technical issues
3. Be empathetic and professional in all responses
4. If you cannot resolve the issue, create a ticket and inform the customer
5. Never make promises about refunds or credits without checking policy
6. Keep responses concise but complete

Response Format:
- Acknowledge the customer's concern
- Provide the solution or answer
- Offer additional assistance
- Set expectations for any follow-up"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

@tool
def search_knowledge_base(query: str, category: str = "all") -> list:
    """Search the knowledge base for relevant information.

    Args:
        query: The search query
        category: Optional category filter

    Returns:
        List of relevant knowledge base entries
    """
    from knowledge_base.retriever import KnowledgeRetriever

    retriever = KnowledgeRetriever()
    results = retriever.search(
        query=query,
        top_k=settings.retrieval_top_k,
        category=category,
        score_threshold=settings.similarity_threshold
    )

    return [{"title": r.title, "content": r.content, "source": r.source} for r in results]

@tool
def get_customer_history(customer_id: str) -> dict:
    """Retrieve customer interaction history.

    Args:
        customer_id: The customer's unique identifier

    Returns:
        Customer history including past tickets and interactions
    """
    from database.customer_repo import CustomerRepository

    repo = CustomerRepository()
    return repo.get_customer_history(customer_id)

@tool
def create_ticket(customer_id: str, subject: str, description: str,
                  priority: str, category: str) -> dict:
    """Create a support ticket for issues that need follow-up.

    Args:
        customer_id: The customer's unique identifier
        subject: Brief summary of the issue
        description: Detailed description
        priority: Ticket priority (low, medium, high, critical)
        category: Issue category

    Returns:
        Ticket details including ticket ID
    """
    from ticketing.system import TicketSystem

    system = TicketSystem()
    ticket = system.create_ticket(
        customer_id=customer_id,
        subject=subject,
        description=description,
        priority=priority,
        category=category
    )

    return {
        "ticket_id": ticket.id,
        "status": ticket.status,
        "estimated_response_time": ticket.estimated_response_time
    }

@tool
def update_customer_profile(customer_id: str, field: str, value: str) -> bool:
    """Update a customer's profile information.

    Args:
        customer_id: The customer's unique identifier
        field: The field to update
        value: The new value

    Returns:
        True if update was successful
    """
    from database.customer_repo import CustomerRepository

    repo = CustomerRepository()
    return repo.update_field(customer_id, field, value)

@tool
def get_order_status(order_id: str) -> dict:
    """Get the status of a customer's order.

    Args:
        order_id: The order identifier

    Returns:
        Order status and tracking information
    """
    from orders.order_service import OrderService

    service = OrderService()
    return service.get_order_status(order_id)

@tool
def initiate_refund(order_id: str, reason: str, amount: float = None) -> dict:
    """Initiate a refund for an order.

    Args:
        order_id: The order identifier
        reason: Reason for the refund
        amount: Optional specific amount, defaults to full order amount

    Returns:
        Refund details and status
    """
    from payments.refund_service import RefundService

    service = RefundService()
    return service.initiate_refund(order_id, reason, amount)

def create_resolution_agent() -> AgentExecutor:
    """Create and configure the Resolution Agent."""
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens
    )

    tools = [
        search_knowledge_base,
        get_customer_history,
        create_ticket,
        update_customer_profile,
        get_order_status,
        initiate_refund
    ]

    agent = create_openai_functions_agent(llm, tools, RESOLUTION_PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=settings.max_agent_iterations,
        handle_parsing_errors=True,
        early_stopping_method="generate"
    )
```

### 3.3 Resolution Workflows

```python
# workflows/resolution_workflows.py
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class ResolutionWorkflows:
    """Pre-defined workflows for common resolution scenarios."""

    @staticmethod
    def password_reset_workflow():
        """Handle password reset requests."""
        workflow = (
            RunnablePassthrough.assign(
                customer_id=lambda x: x["customer_id"],
                email=lambda x: x["email"]
            )
            | RunnablePassthrough.assign(
                reset_link=lambda x: generate_reset_link(x["customer_id"], x["email"])
            )
            | RunnablePassthrough.assign(
                response=lambda x: f"""I've sent a password reset link to {x['email']}.
The link will expire in 30 minutes. If you don't receive it, please check your spam folder.
Let me know if you need any further assistance!"""
            )
        )
        return workflow

    @staticmethod
    def order_tracking_workflow():
        """Handle order tracking requests."""
        workflow = (
            RunnablePassthrough.assign(
                order_status=lambda x: get_order_status(x["order_id"])
            )
            | RunnablePassthrough.assign(
                response=lambda x: format_order_response(x["order_status"])
            )
        )
        return workflow

    @staticmethod
    def refund_request_workflow():
        """Handle refund requests with policy check."""
        workflow = (
            RunnablePassthrough.assign(
                order_details=lambda x: get_order_details(x["order_id"])
            )
            | RunnablePassthrough.assign(
                refund_eligible=lambda x: check_refund_eligibility(x["order_details"])
            )
            | RunnablePassthrough.assign(
                response=lambda x: (
                    process_refund(x["order_id"]) if x["refund_eligible"]
                    else explain_refund_policy(x["order_details"])
                )
            )
        )
        return workflow

def generate_reset_link(customer_id: str, email: str) -> str:
    """Generate a secure password reset link."""
    import secrets
    import hashlib
    from datetime import datetime, timedelta

    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(minutes=30)

    # Store token in database with expiry
    store_reset_token(customer_id, token, expiry)

    return f"https://example.com/reset-password?token={token}"

def format_order_response(order_status: dict) -> str:
    """Format order status into customer-friendly response."""
    status_messages = {
        "processing": "Your order is being processed and will ship soon.",
        "shipped": f"Your order has shipped! Tracking: {order_status.get('tracking_number', 'N/A')}",
        "delivered": "Your order has been delivered. We hope you love it!",
        "delayed": "We're sorry, but your order has been delayed. New estimated delivery: " + order_status.get("new_eta", "TBD")
    }

    return status_messages.get(
        order_status.get("status", "unknown"),
        "We're looking into your order status. Please check back shortly."
    )
```

---

## 4. Escalation Agent Implementation

### 4.1 Purpose and Responsibilities

The Escalation Agent manages situations that exceed the Resolution Agent's capabilities:

- **Human Handoff**: Transfer complex cases to human agents
- **Priority Management**: Ensure critical issues receive immediate attention
- **Context Preservation**: Maintain full context when transferring between agents
- **SLA Monitoring**: Track response times and escalate if SLA is at risk
- **VIP Handling**: Provide white-glove service for high-value customers

### 4.2 Agent Definition

```python
# agents/escalation_agent.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config.settings import settings

ESCALATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Escalation Agent for customer service.
You handle complex cases that require human intervention or special attention.

Your responsibilities:
1. Assess the severity and urgency of escalated issues
2. Determine the appropriate human team for handoff
3. Preserve all context for the receiving human agent
4. Communicate clearly with the customer about next steps
5. Monitor SLA compliance and escalate further if needed

Escalation Triggers:
- Customer explicitly requests a human
- Resolution Agent confidence below threshold
- VIP/Enterprise customer with unresolved issue
- Legal or compliance-related matters
- Security incidents
- Repeated failed resolution attempts

Always maintain professionalism and empathy. The customer should feel
heard and confident that their issue is being handled appropriately."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

@tool
def transfer_to_human(customer_id: str, issue_summary: str,
                       priority: str, category: str,
                       context: dict) -> dict:
    """Transfer the case to a human agent.

    Args:
        customer_id: The customer's unique identifier
        issue_summary: Summary of the issue
        priority: Priority level
        category: Issue category
        context: Full conversation context

    Returns:
        Transfer details including queue position and estimated wait
    """
    from ticketing.escalation import EscalationManager

    manager = EscalationManager()
    result = manager.transfer_to_human(
        customer_id=customer_id,
        issue_summary=issue_summary,
        priority=priority,
        category=category,
        context=context
    )

    return {
        "transfer_id": result.transfer_id,
        "queue_position": result.queue_position,
        "estimated_wait_minutes": result.estimated_wait,
        "assigned_team": result.assigned_team
    }

@tool
def get_agent_availability(team: str = None) -> dict:
    """Check human agent availability.

    Args:
        team: Optional specific team to check

    Returns:
        Agent availability information
    """
    from staffing.availability import AvailabilityService

    service = AvailabilityService()
    return service.get_availability(team)

@tool
def schedule_callback(customer_id: str, phone_number: str,
                      preferred_time: str, reason: str) -> dict:
    """Schedule a callback for the customer.

    Args:
        customer_id: The customer's unique identifier
        phone_number: Callback phone number
        preferred_time: Preferred callback time
        reason: Reason for callback

    Returns:
        Callback confirmation details
    """
    from scheduling.callback import CallbackScheduler

    scheduler = CallbackScheduler()
    return scheduler.schedule(
        customer_id=customer_id,
        phone_number=phone_number,
        preferred_time=preferred_time,
        reason=reason
    )

@tool
def escalate_priority(ticket_id: str, new_priority: str, reason: str) -> bool:
    """Escalate the priority of an existing ticket.

    Args:
        ticket_id: The ticket identifier
        new_priority: New priority level
        reason: Reason for escalation

    Returns:
        True if escalation was successful
    """
    from ticketing.system import TicketSystem

    system = TicketSystem()
    return system.update_priority(ticket_id, new_priority, reason)

@tool
def notify_management(issue_type: str, details: dict) -> bool:
    """Notify management of critical issues.

    Args:
        issue_type: Type of issue requiring management attention
        details: Issue details

    Returns:
        True if notification was sent
    """
    from notifications.management import ManagementNotifier

    notifier = ManagementNotifier()
    return notifier.notify(issue_type, details)

@tool
def get_sla_status(ticket_id: str) -> dict:
    """Check SLA status for a ticket.

    Args:
        ticket_id: The ticket identifier

    Returns:
        SLA status including time remaining and compliance
    """
    from sla.monitor import SLAMonitor

    monitor = SLAMonitor()
    return monitor.get_status(ticket_id)

def create_escalation_agent() -> AgentExecutor:
    """Create and configure the Escalation Agent."""
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.2,
        max_tokens=settings.llm_max_tokens
    )

    tools = [
        transfer_to_human,
        get_agent_availability,
        schedule_callback,
        escalate_priority,
        notify_management,
        get_sla_status
    ]

    agent = create_openai_functions_agent(llm, tools, ESCALATION_PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=settings.max_agent_iterations,
        handle_parsing_errors=True
    )
```

### 4.3 Escalation Policies

```python
# policies/escalation_policies.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

@dataclass
class EscalationPolicy:
    name: str
    conditions: List[str]
    actions: List[str]
    priority: str
    sla_minutes: int
    notify_channels: List[str]

ESCALATION_POLICIES = {
    "vip_unresolved": EscalationPolicy(
        name="VIP Unresolved Issue",
        conditions=[
            "customer_tier == 'enterprise'",
            "resolution_attempts >= 2",
            "customer_satisfaction < 0.5"
        ],
        actions=[
            "transfer_to_senior_agent",
            "notify_account_manager",
            "schedule_executive_callback"
        ],
        priority="critical",
        sla_minutes=15,
        notify_channels=["slack", "email", "sms"]
    ),
    "security_incident": EscalationPolicy(
        name="Security Incident",
        conditions=[
            "issue_category == 'security'",
            "data_breach_suspected == True"
        ],
        actions=[
            "transfer_to_security_team",
            "notify_ciso",
            "initiate_incident_response"
        ],
        priority="critical",
        sla_minutes=5,
        notify_channels=["pagerduty", "slack", "sms"]
    ),
    "legal_complaint": EscalationPolicy(
        name="Legal Complaint",
        conditions=[
            "issue_category == 'legal'",
            "attorney_mentioned == True"
        ],
        actions=[
            "transfer_to_legal_team",
            "preserve_all_communications",
            "notify_general_counsel"
        ],
        priority="critical",
        sla_minutes=30,
        notify_channels=["email", "slack"]
    ),
    "service_outage": EscalationPolicy(
        name="Service Outage",
        conditions=[
            "issue_category == 'technical'",
            "multiple_customers_affected == True",
            "service_down == True"
        ],
        actions=[
            "transfer_to_engineering",
            "notify_on_call_engineer",
            "update_status_page"
        ],
        priority="critical",
        sla_minutes=5,
        notify_channels=["pagerduty", "slack", "statuspage"]
    ),
    "billing_dispute": EscalationPolicy(
        name="Billing Dispute",
        conditions=[
            "issue_category == 'billing'",
            "dispute_amount > 1000",
            "customer_threatens_cancellation == True"
        ],
        actions=[
            "transfer_to_billing_specialist",
            "apply_account_credit_hold",
            "notify_retention_team"
        ],
        priority="high",
        sla_minutes=60,
        notify_channels=["slack", "email"]
    )
}

class EscalationEngine:
    """Evaluates escalation conditions and triggers appropriate actions."""

    def __init__(self):
        self.policies = ESCALATION_POLICIES

    def evaluate(self, context: dict) -> Optional[EscalationPolicy]:
        """Evaluate all policies against the current context."""
        for policy in self.policies.values():
            if self._check_conditions(policy.conditions, context):
                return policy
        return None

    def _check_conditions(self, conditions: List[str], context: dict) -> bool:
        """Check if all conditions are met."""
        for condition in conditions:
            if not self._evaluate_condition(condition, context):
                return False
        return True

    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """Evaluate a single condition string."""
        # Simple condition evaluator
        parts = condition.split(" == ")
        if len(parts) == 2:
            key, expected = parts
            actual = context.get(key)
            return str(actual).lower() == expected.lower()

        parts = condition.split(" >= ")
        if len(parts) == 2:
            key, threshold = parts
            actual = context.get(key, 0)
            return float(actual) >= float(threshold)

        return False
```

---

## 5. Sentiment Analysis Agent Implementation

### 5.1 Purpose and Responsibilities

The Sentiment Analysis Agent continuously monitors customer emotional state throughout interactions:

- **Real-time Sentiment Scoring**: Analyze each message for emotional tone
- **Trend Detection**: Track sentiment changes over the conversation
- **Response Adjustment**: Modify response tone based on detected sentiment
- **Escalation Triggers**: Flag conversations with deteriorating sentiment
- **Satisfaction Prediction**: Estimate likelihood of customer satisfaction

### 5.2 Agent Definition

```python
# agents/sentiment_agent.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config.settings import settings

SENTIMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Sentiment Analysis Agent for customer service.
You monitor and analyze customer emotional state throughout interactions.

Your responsibilities:
1. Analyze each customer message for emotional sentiment
2. Track sentiment trends over the conversation
3. Detect frustration, anger, satisfaction, or confusion
4. Recommend response tone adjustments
5. Flag conversations needing escalation due to negative sentiment

Sentiment Scale:
-1.0 to -0.7: Very Negative (angry, hostile)
-0.7 to -0.3: Negative (frustrated, dissatisfied)
-0.3 to 0.3: Neutral (factual, informational)
0.3 to 0.7: Positive (satisfied, happy)
0.7 to 1.0: Very Positive (delighted, enthusiastic)

Always consider context: a "no" from an angry customer is very different
from a "no" from a happy one."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

@tool
def analyze_sentiment(text: str) -> dict:
    """Analyze the sentiment of a text message.

    Args:
        text: The text to analyze

    Returns:
        Sentiment analysis results with score and label
    """
    from transformers import pipeline

    classifier = pipeline(
        "sentiment-analysis",
        model=settings.sentiment_model
    )

    result = classifier(text)[0]

    # Convert to -1 to 1 scale
    if result["label"] == "POSITIVE":
        score = result["score"]
    else:
        score = -result["score"]

    return {
        "score": score,
        "label": result["label"],
        "confidence": result["score"],
        "text": text
    }

@tool
def analyze_conversation_sentiment(messages: list) -> dict:
    """Analyze sentiment trends across a conversation.

    Args:
        messages: List of message dictionaries with 'text' and 'timestamp'

    Returns:
        Conversation-level sentiment analysis
    """
    from transformers import pipeline
    import numpy as np

    classifier = pipeline(
        "sentiment-analysis",
        model=settings.sentiment_model
    )

    scores = []
    for msg in messages:
        result = classifier(msg["text"])[0]
        score = result["score"] if result["label"] == "POSITIVE" else -result["score"]
        scores.append(score)

    scores_array = np.array(scores)

    return {
        "average_sentiment": float(np.mean(scores_array)),
        "sentiment_trend": "improving" if scores_array[-1] > scores_array[0] else "declining",
        "min_sentiment": float(np.min(scores_array)),
        "max_sentiment": float(np.max(scores_array)),
        "volatility": float(np.std(scores_array)),
        "current_sentiment": float(scores_array[-1]),
        "message_count": len(messages)
    }

@tool
def get_response_tone_recommendation(sentiment_score: float,
                                      customer_tier: str = "standard") -> str:
    """Get a recommended response tone based on sentiment.

    Args:
        sentiment_score: Current sentiment score (-1 to 1)
        customer_tier: Customer tier level

    Returns:
        Recommended tone description
    """
    if sentiment_score <= settings.escalation_sentiment_threshold:
        return "empathetic_apologetic"
    elif sentiment_score <= settings.negative_sentiment_threshold:
        return "empathetic_helpful"
    elif sentiment_score < 0.3:
        return "professional_neutral"
    elif sentiment_score < 0.7:
        return "friendly_helpful"
    else:
        return "warm_enthusiastic"

@tool
def should_escalate_sentiment(sentiment_history: list) -> dict:
    """Determine if sentiment warrants escalation.

    Args:
        sentiment_history: List of sentiment scores over time

    Returns:
        Escalation recommendation
    """
    import numpy as np

    if len(sentiment_history) < 2:
        return {"should_escalate": False, "reason": "insufficient_data"}

    scores = np.array(sentiment_history)
    current = scores[-1]
    avg = np.mean(scores)
    trend = scores[-1] - scores[0]

    # Escalate if sentiment is very negative
    if current <= settings.escalation_sentiment_threshold:
        return {
            "should_escalate": True,
            "reason": "very_negative_sentiment",
            "urgency": "high"
        }

    # Escalate if sentiment is consistently declining
    if trend < -0.5 and current < settings.negative_sentiment_threshold:
        return {
            "should_escalate": True,
            "reason": "declining_sentiment_trend",
            "urgency": "medium"
        }

    # Escalate if sentiment is negative and not improving
    if current < settings.negative_sentiment_threshold and trend <= 0:
        return {
            "should_escalate": True,
            "reason": "persistent_negative_sentiment",
            "urgency": "medium"
        }

    return {"should_escalate": False, "reason": "sentiment_acceptable"}

def create_sentiment_agent() -> AgentExecutor:
    """Create and configure the Sentiment Analysis Agent."""
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.1,
        max_tokens=settings.llm_max_tokens
    )

    tools = [
        analyze_sentiment,
        analyze_conversation_sentiment,
        get_response_tone_recommendation,
        should_escalate_sentiment
    ]

    agent = create_openai_functions_agent(llm, tools, SENTIMENT_PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=settings.max_agent_iterations,
        handle_parsing_errors=True
    )
```

### 5.3 Sentiment-Aware Response Generation

```python
# sentiment/response_adjuster.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

class SentimentAwareResponseGenerator:
    """Adjusts response tone based on detected sentiment."""

    TONE_INSTRUCTIONS = {
        "empathetic_apologetic": """
            Show genuine empathy and apologize for any inconvenience.
            Acknowledge the customer's feelings before providing solutions.
            Use phrases like "I understand how frustrating this must be" and
            "I'm sorry you're experiencing this issue."
        """,
        "empathetic_helpful": """
            Show understanding and focus on helping resolve the issue.
            Be patient and thorough in your explanation.
            Reassure the customer that you're here to help.
        """,
        "professional_neutral": """
            Maintain a professional and informative tone.
            Be clear and concise in your communication.
            Focus on providing accurate information.
        """,
        "friendly_helpful": """
            Be warm and approachable while providing assistance.
            Show enthusiasm for helping the customer.
            Use a conversational but professional tone.
        """,
        "warm_enthusiastic": """
            Match the customer's positive energy.
            Be genuinely warm and appreciative.
            Reinforce the positive relationship.
        """
    }

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.4)

    def generate_response(self, original_query: str, base_response: str,
                          sentiment_score: float, tone: str) -> str:
        """Generate a sentiment-adjusted response."""

        tone_instruction = self.TONE_INSTRUCTIONS.get(tone, self.TONE_INSTRUCTIONS["professional_neutral"])

        prompt = f"""Rewrite the following customer service response to match the recommended tone.

Original Query: {original_query}
Base Response: {base_response}
Detected Sentiment Score: {sentiment_score}
Recommended Tone: {tone}

Tone Instructions:
{tone_instruction}

Rewritten Response:"""

        response = self.llm.invoke(prompt)
        return response.content
```

---

## 6. Customer Success Agent Implementation

### 6.1 Purpose and Responsibilities

The Customer Success Agent takes a proactive approach to customer retention and growth:

- **Health Scoring**: Calculate and monitor customer health scores
- **Churn Prediction**: Identify customers at risk of churning
- **Proactive Outreach**: Initiate contact with at-risk customers
- **Upsell Identification**: Detect opportunities for account expansion
- **Onboarding Assistance**: Guide new customers through product adoption

### 6.2 Agent Definition

```python
# agents/customer_success_agent.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from config.settings import settings

CUSTOMER_SUCCESS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Customer Success Agent.
You proactively engage customers to drive retention, satisfaction, and growth.

Your responsibilities:
1. Monitor customer health scores and identify at-risk accounts
2. Proactively reach out to customers showing signs of disengagement
3. Identify upsell and cross-sell opportunities
4. Guide new customers through onboarding and product adoption
5. Celebrate customer milestones and successes

Health Score Components:
- Product usage frequency and depth
- Support ticket volume and sentiment
- Feature adoption rate
- NPS/CSAT scores
- Billing history and payment reliability
- Engagement with communications

Always be genuine and helpful. Never be pushy with upsell suggestions.
Focus on delivering value first."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

@tool
def calculate_health_score(customer_id: str) -> dict:
    """Calculate a comprehensive health score for a customer.

    Args:
        customer_id: The customer's unique identifier

    Returns:
        Health score breakdown and overall score
    """
    from analytics.health import HealthCalculator

    calculator = HealthCalculator()
    return calculator.calculate(customer_id)

@tool
def get_churn_risk(customer_id: str) -> dict:
    """Assess the churn risk for a customer.

    Args:
        customer_id: The customer's unique identifier

    Returns:
        Churn risk assessment with factors and probability
    """
    from analytics.churn import ChurnPredictor

    predictor = ChurnPredictor()
    return predictor.predict(customer_id)

@tool
def get_usage_analytics(customer_id: str, days: int = 30) -> dict:
    """Get product usage analytics for a customer.

    Args:
        customer_id: The customer's unique identifier
        days: Number of days to analyze

    Returns:
        Usage analytics including active users, features used, etc.
    """
    from analytics.usage import UsageAnalytics

    analytics = UsageAnalytics()
    return analytics.get_usage(customer_id, days)

@tool
def identify_upsell_opportunity(customer_id: str) -> dict:
    """Identify potential upsell or cross-sell opportunities.

    Args:
        customer_id: The customer's unique identifier

    Returns:
        Upsell opportunities with relevance scores
    """
    from sales.upsell import UpsellIdentifier

    identifier = UpsellIdentifier()
    return identifier.identify(customer_id)

@tool
def schedule_outreach(customer_id: str, outreach_type: str,
                      message: str, scheduled_time: str = None) -> dict:
    """Schedule a proactive outreach to a customer.

    Args:
        customer_id: The customer's unique identifier
        outreach_type: Type of outreach (check_in, onboarding, upsell, win_back)
        message: The outreach message
        scheduled_time: Optional scheduled time for the outreach

    Returns:
        Outreach confirmation details
    """
    from outreach.scheduler import OutreachScheduler

    scheduler = OutreachScheduler()
    return scheduler.schedule(
        customer_id=customer_id,
        outreach_type=outreach_type,
        message=message,
        scheduled_time=scheduled_time
    )

@tool
def get_onboarding_status(customer_id: str) -> dict:
    """Get the onboarding progress for a new customer.

    Args:
        customer_id: The customer's unique identifier

    Returns:
        Onboarding status including completed and pending steps
    """
    from onboarding.tracker import OnboardingTracker

    tracker = OnboardingTracker()
    return tracker.get_status(customer_id)

@tool
def create_success_plan(customer_id: str, goals: list) -> dict:
    """Create a success plan for a customer.

    Args:
        customer_id: The customer's unique identifier
        goals: List of customer goals and milestones

    Returns:
        Success plan details
    """
    from success.planner import SuccessPlanner

    planner = SuccessPlanner()
    return planner.create_plan(customer_id, goals)

def create_customer_success_agent() -> AgentExecutor:
    """Create and configure the Customer Success Agent."""
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0.3,
        max_tokens=settings.llm_max_tokens
    )

    tools = [
        calculate_health_score,
        get_churn_risk,
        get_usage_analytics,
        identify_upsell_opportunity,
        schedule_outreach,
        get_onboarding_status,
        create_success_plan
    ]

    agent = create_openai_functions_agent(llm, tools, CUSTOMER_SUCCESS_PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=settings.max_agent_iterations,
        handle_parsing_errors=True
    )
```

### 6.3 Health Score Calculation

```python
# analytics/health.py
from dataclasses import dataclass
from typing import Dict
from datetime import datetime, timedelta

@dataclass
class HealthScore:
    overall: float
    components: Dict[str, float]
    trend: str
    risk_level: str
    recommendations: list

class HealthCalculator:
    """Calculates customer health scores."""

    WEIGHTS = {
        "usage": 0.25,
        "support": 0.20,
        "adoption": 0.20,
        "satisfaction": 0.20,
        "billing": 0.15
    }

    def calculate(self, customer_id: str) -> dict:
        """Calculate comprehensive health score."""
        usage_score = self._calculate_usage_score(customer_id)
        support_score = self._calculate_support_score(customer_id)
        adoption_score = self._calculate_adoption_score(customer_id)
        satisfaction_score = self._calculate_satisfaction_score(customer_id)
        billing_score = self._calculate_billing_score(customer_id)

        overall = (
            usage_score * self.WEIGHTS["usage"] +
            support_score * self.WEIGHTS["support"] +
            adoption_score * self.WEIGHTS["adoption"] +
            satisfaction_score * self.WEIGHTS["satisfaction"] +
            billing_score * self.WEIGHTS["billing"]
        )

        components = {
            "usage": usage_score,
            "support": support_score,
            "adoption": adoption_score,
            "satisfaction": satisfaction_score,
            "billing": billing_score
        }

        trend = self._calculate_trend(customer_id, components)
        risk_level = self._determine_risk_level(overall)
        recommendations = self._generate_recommendations(components)

        return {
            "overall": round(overall, 2),
            "components": {k: round(v, 2) for k, v in components.items()},
            "trend": trend,
            "risk_level": risk_level,
            "recommendations": recommendations
        }

    def _calculate_usage_score(self, customer_id: str) -> float:
        """Calculate product usage score (0-1)."""
        # Query usage data for last 30 days
        usage_data = get_usage_data(customer_id, days=30)

        if not usage_data:
            return 0.0

        # Factors: active days, session duration, features used
        active_days = usage_data.get("active_days", 0)
        avg_session = usage_data.get("avg_session_minutes", 0)
        features_used = usage_data.get("features_used", 0)

        # Normalize to 0-1 scale
        day_score = min(active_days / 20, 1.0)  # 20 active days = perfect
        session_score = min(avg_session / 30, 1.0)  # 30 min average = perfect
        feature_score = min(features_used / 10, 1.0)  # 10 features = perfect

        return (day_score * 0.4 + session_score * 0.3 + feature_score * 0.3)

    def _calculate_support_score(self, customer_id: str) -> float:
        """Calculate support interaction score (0-1)."""
        tickets = get_support_tickets(customer_id, days=90)

        if not tickets:
            return 1.0  # No tickets is good

        # Factors: ticket count, resolution time, sentiment
        ticket_count = len(tickets)
        avg_resolution = sum(t["resolution_hours"] for t in tickets) / len(tickets)
        avg_sentiment = sum(t["sentiment_score"] for t in tickets) / len(tickets)

        # Fewer tickets, faster resolution, positive sentiment = higher score
        count_score = max(0, 1 - (ticket_count / 10))  # 10+ tickets = 0
        resolution_score = max(0, 1 - (avg_resolution / 72))  # 72+ hours = 0
        sentiment_score = (avg_sentiment + 1) / 2  # Convert -1,1 to 0,1

        return (count_score * 0.4 + resolution_score * 0.3 + sentiment_score * 0.3)

    def _calculate_adoption_score(self, customer_id: str) -> float:
        """Calculate feature adoption score (0-1)."""
        adoption_data = get_adoption_data(customer_id)

        if not adoption_data:
            return 0.0

        total_features = adoption_data.get("total_features", 1)
        adopted_features = adoption_data.get("adopted_features", 0)
        power_features = adoption_data.get("power_features_used", 0)

        adoption_rate = adopted_features / max(total_features, 1)
        power_rate = power_features / max(total_features, 1)

        return (adoption_rate * 0.6 + power_rate * 0.4)

    def _calculate_satisfaction_score(self, customer_id: str) -> float:
        """Calculate satisfaction score from surveys and feedback (0-1)."""
        surveys = get_satisfaction_surveys(customer_id, days=180)

        if not surveys:
            return 0.5  # Neutral if no data

        # Average NPS/CSAT scores
        nps_scores = [s["nps"] for s in surveys if "nps" in s]
        csat_scores = [s["csat"] for s in surveys if "csat" in s]

        nps_avg = sum(nps_scores) / len(nps_scores) if nps_scores else 0
        csat_avg = sum(csat_scores) / len(csat_scores) if csat_scores else 0

        # Normalize to 0-1
        nps_normalized = (nps_avg + 100) / 200  # NPS is -100 to 100
        csat_normalized = csat_avg / 5  # CSAT is 1-5

        return (nps_normalized * 0.5 + csat_normalized * 0.5)

    def _calculate_billing_score(self, customer_id: str) -> float:
        """Calculate billing reliability score (0-1)."""
        billing_data = get_billing_data(customer_id, days=180)

        if not billing_data:
            return 1.0

        # Factors: on-time payments, no disputes, plan appropriateness
        on_time = billing_data.get("on_time_payments", 0)
        total = billing_data.get("total_payments", 1)
        disputes = billing_data.get("disputes", 0)

        payment_score = on_time / max(total, 1)
        dispute_score = max(0, 1 - (disputes / 3))  # 3+ disputes = 0

        return (payment_score * 0.7 + dispute_score * 0.3)

    def _calculate_trend(self, customer_id: str, current: Dict[str, float]) -> str:
        """Calculate health score trend."""
        # Compare with previous period
        previous = get_previous_health_score(customer_id)

        if not previous:
            return "stable"

        diff = sum(current.values()) / len(current) - previous

        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        return "stable"

    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from health score."""
        if score >= 0.7:
            return "low"
        elif score >= 0.4:
            return "medium"
        return "high"

    def _generate_recommendations(self, components: Dict[str, float]) -> list:
        """Generate improvement recommendations."""
        recommendations = []

        if components["usage"] < 0.5:
            recommendations.append("Increase product engagement through targeted training")
        if components["support"] < 0.5:
            recommendations.append("Review support interactions for improvement areas")
        if components["adoption"] < 0.5:
            recommendations.append("Promote underused features through guided tours")
        if components["satisfaction"] < 0.5:
            recommendations.append("Conduct satisfaction survey and address concerns")
        if components["billing"] < 0.5:
            recommendations.append("Review billing setup and payment processes")

        return recommendations
```

---

## 7. Knowledge Base Integration

### 7.1 Architecture

The knowledge base is the backbone of the AI customer service system, providing agents with accurate, up-to-date information.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Knowledge Base Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Product    │  │     FAQ      │  │   Policies   │           │
│  │    Docs      │  │   Database   │  │  & Procedures│           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                    │
│         └────────────────┬┴─────────────────┘                    │
│                          │                                       │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │   Document Ingestion  │                          │
│              │   & Processing        │                          │
│              └───────────┬───────────┘                          │
│                          │                                       │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │   Embedding Generation│                          │
│              │   (text-embedding-3)  │                          │
│              └───────────┬───────────┘                          │
│                          │                                       │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │    Vector Store       │                          │
│              │    (Pinecone)         │                          │
│              └───────────┬───────────┘                          │
│                          │                                       │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │   Retrieval Engine    │                          │
│              │   (RAG Pipeline)      │                          │
│              └───────────────────────┘                          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Knowledge Base Schema

```python
# knowledge_base/models.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    FAQ = "faq"
    PRODUCT_DOC = "product_doc"
    POLICY = "policy"
    TROUBLESHOOTING = "troubleshooting"
    TUTORIAL = "tutorial"
    RELEASE_NOTE = "release_note"
    KNOWN_ISSUE = "known_issue"

class KnowledgeDocument(BaseModel):
    id: str
    title: str
    content: str
    document_type: DocumentType
    category: str
    tags: List[str]
    source_url: Optional[str] = None
    version: str = "1.0"
    created_at: datetime
    updated_at: datetime
    author: str
    review_status: str = "approved"  # draft, review, approved, archived
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    metadata: dict = {}

class SearchResult(BaseModel):
    document: KnowledgeDocument
    score: float
    chunk_index: int
    highlighted_content: str
```

### 7.3 Document Ingestion Pipeline

```python
# knowledge_base/ingestion.py
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, WebBaseLoader, UnstructuredMarkdownLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from typing import List
import uuid

class DocumentIngestionPipeline:
    """Pipeline for ingesting documents into the knowledge base."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.vector_store = PineconeVectorStore(
            index_name="customer-service-kb",
            embedding=self.embeddings,
            namespace="production"
        )

    async def ingest_document(self, file_path: str, doc_type: DocumentType,
                              category: str, metadata: dict = None) -> str:
        """Ingest a single document into the knowledge base."""

        # Load document
        loader = self._get_loader(file_path)
        documents = loader.load()

        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)

        # Generate IDs and metadata
        doc_id = str(uuid.uuid4())
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "doc_id": doc_id,
                "chunk_index": i,
                "document_type": doc_type.value,
                "category": category,
                "source_file": file_path,
                **(metadata or {})
            })

        # Store in vector database
        self.vector_store.add_documents(chunks)

        return doc_id

    async def ingest_web_content(self, url: str, doc_type: DocumentType,
                                 category: str) -> str:
        """Ingest web page content into the knowledge base."""

        loader = WebBaseLoader(url)
        documents = loader.load()

        chunks = self.text_splitter.split_documents(documents)

        doc_id = str(uuid.uuid4())
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "doc_id": doc_id,
                "chunk_index": i,
                "document_type": doc_type.value,
                "category": category,
                "source_url": url
            })

        self.vector_store.add_documents(chunks)

        return doc_id

    async def ingest_faq_csv(self, csv_path: str, category: str) -> List[str]:
        """Ingest FAQ entries from a CSV file.

        Expected CSV format: question,answer,category,tags
        """
        import csv

        doc_ids = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                content = f"Q: {row['question']}\nA: {row['answer']}"
                doc_id = str(uuid.uuid4())

                from langchain_core.documents import Document
                doc = Document(
                    page_content=content,
                    metadata={
                        "doc_id": doc_id,
                        "document_type": "faq",
                        "category": category,
                        "tags": row.get("tags", "").split(","),
                        "question": row["question"]
                    }
                )

                self.vector_store.add_documents([doc])
                doc_ids.append(doc_id)

        return doc_ids

    def _get_loader(self, file_path: str):
        """Get appropriate loader based on file extension."""
        if file_path.endswith('.pdf'):
            return PyPDFLoader(file_path)
        elif file_path.endswith('.md'):
            return UnstructuredMarkdownLoader(file_path)
        elif file_path.startswith('http'):
            return WebBaseLoader(file_path)
        else:
            return TextLoader(file_path)
```

### 7.4 Retrieval System

```python
# knowledge_base/retriever.py
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI
from config.settings import settings

class KnowledgeRetriever:
    """Retrieves relevant knowledge base content for agent queries."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=settings.embedding_model)
        self.vector_store = PineconeVectorStore(
            index_name=settings.vector_store_index,
            embedding=self.embeddings,
            namespace="production"
        )

    def search(self, query: str, top_k: int = 5,
               category: str = "all",
               score_threshold: float = 0.7) -> list:
        """Search the knowledge base for relevant content."""

        # Build filter
        filter_dict = {}
        if category != "all":
            filter_dict["category"] = category

        # Perform similarity search
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=filter_dict if filter_dict else None
        )

        # Filter by score threshold and format results
        formatted_results = []
        for doc, score in results:
            if score >= score_threshold:
                formatted_results.append({
                    "title": doc.metadata.get("title", "Untitled"),
                    "content": doc.page_content,
                    "source": doc.metadata.get("source_url", doc.metadata.get("source_file", "Unknown")),
                    "category": doc.metadata.get("category", "general"),
                    "score": score,
                    "document_type": doc.metadata.get("document_type", "unknown")
                })

        return formatted_results

    def search_with_context(self, query: str, conversation_context: dict,
                           top_k: int = 5) -> list:
        """Search with conversation context for better relevance."""

        # Enhance query with context
        enhanced_query = self._enhance_query(query, conversation_context)

        # Determine category from context
        category = conversation_context.get("category", "all")

        return self.search(enhanced_query, top_k, category)

    def _enhance_query(self, query: str, context: dict) -> str:
        """Enhance the search query with conversation context."""
        enhancements = []

        if context.get("customer_id"):
            enhancements.append(f"Customer context: {context['customer_id']}")

        if context.get("product"):
            enhancements.append(f"Product: {context['product']}")

        if context.get("issue_category"):
            enhancements.append(f"Issue type: {context['issue_category']}")

        if enhancements:
            return f"{query}\nContext: {', '.join(enhancements)}"

        return query

    def get_related_articles(self, article_id: str, top_k: int = 3) -> list:
        """Get articles related to a specific article."""
        # Get the source document
        doc = self.vector_store.get_by_ids([article_id])

        if not doc:
            return []

        # Use the document content as query
        query = doc[0].page_content[:500]  # First 500 chars

        return self.search(query, top_k)
```

### 7.5 Knowledge Base Maintenance

```python
# knowledge_base/maintenance.py
from datetime import datetime, timedelta
from typing import List

class KnowledgeBaseMaintenance:
    """Maintains and updates the knowledge base."""

    def __init__(self):
        self.retriever = KnowledgeRetriever()

    async def review_outdated_content(self) -> List[dict]:
        """Find content that may be outdated."""
        # Query for content not updated in 90+ days
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        outdated = self._query_by_date(cutoff_date)

        return [
            {
                "doc_id": doc["id"],
                "title": doc["title"],
                "last_updated": doc["updated_at"],
                "days_since_update": (datetime.utcnow() - doc["updated_at"]).days,
                "recommendation": "review"
            }
            for doc in outdated
        ]

    async def identify_gaps(self, recent_tickets: list) -> List[dict]:
        """Identify knowledge base gaps from recent support tickets."""
        from collections import Counter

        # Extract common themes from tickets
        themes = Counter()
        unresolved = []

        for ticket in recent_tickets:
            # Check if ticket was resolved using KB
            if not ticket.get("kb_resolved", False):
                themes[ticket["category"]] += 1
                unresolved.append(ticket)

        gaps = []
        for theme, count in themes.most_common(10):
            if count > 5:  # Threshold for gap identification
                # Search KB for coverage
                coverage = self.retriever.search(theme, top_k=3)

                if not coverage or coverage[0]["score"] < 0.6:
                    gaps.append({
                        "topic": theme,
                        "unresolved_count": count,
                        "current_coverage": "insufficient",
                        "recommendation": "create_content"
                    })

        return gaps

    async def update_from_resolved_tickets(self, days: int = 7) -> int:
        """Extract new knowledge from recently resolved tickets."""
        from ticketing.system import TicketSystem

        system = TicketSystem()
        resolved = system.get_resolved_tickets(
            since=datetime.utcnow() - timedelta(days=days),
            min_satisfaction=4.0
        )

        new_articles = 0
        for ticket in resolved:
            # Check if solution is already in KB
            existing = self.retriever.search(
                ticket["resolution_summary"],
                top_k=1
            )

            if not existing or existing[0]["score"] < 0.8:
                # Create new KB article
                await self._create_article_from_ticket(ticket)
                new_articles += 1

        return new_articles

    async def _create_article_from_ticket(self, ticket: dict):
        """Create a knowledge base article from a resolved ticket."""
        from knowledge_base.ingestion import DocumentIngestionPipeline

        pipeline = DocumentIngestionPipeline()

        content = f"""# {ticket['title']}

## Problem
{ticket['description']}

## Solution
{ticket['resolution_summary']}

## Category
{ticket['category']}

## Tags
{', '.join(ticket.get('tags', []))}
"""

        from langchain_core.documents import Document
        doc = Document(
            page_content=content,
            metadata={
                "document_type": "troubleshooting",
                "category": ticket["category"],
                "tags": ticket.get("tags", []),
                "source_ticket": ticket["id"],
                "auto_generated": True
            }
        )

        pipeline.vector_store.add_documents([doc])
```

---

## 8. Code Examples and Snippets

### 8.1 Complete System Integration

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from agents.triage_agent import create_triage_agent
from agents.resolution_agent import create_resolution_agent
from agents.escalation_agent import create_escalation_agent
from agents.sentiment_agent import create_sentiment_agent
from agents.customer_success_agent import create_customer_success_agent
from agents.routing import Router, AgentType
from config.settings import settings

app = FastAPI(title="AI Customer Service API")

# Initialize agents
triage_agent = create_triage_agent()
resolution_agent = create_resolution_agent()
escalation_agent = create_escalation_agent()
sentiment_agent = create_sentiment_agent()
customer_success_agent = create_customer_success_agent()
router = Router()

class CustomerMessage(BaseModel):
    customer_id: str
    message: str
    channel: str  # email, chat, social, phone
    session_id: Optional[str] = None
    metadata: Optional[dict] = None

class AgentResponse(BaseModel):
    response: str
    agent_type: str
    confidence: float
    sentiment_score: Optional[float] = None
    escalation_recommended: bool = False
    ticket_id: Optional[str] = None

@app.post("/api/v1/message", response_model=AgentResponse)
async def handle_message(msg: CustomerMessage):
    """Handle an incoming customer message."""

    # Get customer context
    customer_context = await get_customer_context(msg.customer_id)

    # Route the message
    routing_decision = await router.route(msg.message, customer_context)

    # Execute the appropriate agent
    if routing_decision.target_agent == AgentType.RESOLUTION:
        result = await resolution_agent.ainvoke({
            "input": msg.message,
            "chat_history": customer_context.get("chat_history", [])
        })
    elif routing_decision.target_agent == AgentType.ESCALATION:
        result = await escalation_agent.ainvoke({
            "input": msg.message,
            "chat_history": customer_context.get("chat_history", [])
        })
    elif routing_decision.target_agent == AgentType.CUSTOMER_SUCCESS:
        result = await customer_success_agent.ainvoke({
            "input": msg.message,
            "chat_history": customer_context.get("chat_history", [])
        })
    else:
        result = await resolution_agent.ainvoke({
            "input": msg.message,
            "chat_history": customer_context.get("chat_history", [])
        })

    # Analyze sentiment
    sentiment_result = await sentiment_agent.ainvoke({
        "input": f"Analyze sentiment: {msg.message}"
    })

    # Check if escalation is needed based on sentiment
    escalation_recommended = False
    sentiment_score = 0.0
    try:
        sentiment_data = eval(sentiment_result["output"])
        sentiment_score = sentiment_data.get("score", 0.0)
        if sentiment_score <= settings.escalation_sentiment_threshold:
            escalation_recommended = True
    except:
        pass

    return AgentResponse(
        response=result["output"],
        agent_type=routing_decision.target_agent.value,
        confidence=routing_decision.confidence,
        sentiment_score=sentiment_score,
        escalation_recommended=escalation_recommended
    )

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agents": 5}

async def get_customer_context(customer_id: str) -> dict:
    """Retrieve customer context from database."""
    from database.customer_repo import CustomerRepository
    repo = CustomerRepository()
    return repo.get_context(customer_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
```

### 8.2 Orchestrator Pattern

```python
# orchestrator.py
from langchain.agents import AgentExecutor
from typing import Dict, Any
import asyncio

class CustomerServiceOrchestrator:
    """Orchestrates all customer service agents."""

    def __init__(self):
        self.agents = {
            "triage": create_triage_agent(),
            "resolution": create_resolution_agent(),
            "escalation": create_escalation_agent(),
            "sentiment": create_sentiment_agent(),
            "customer_success": create_customer_success_agent()
        }
        self.router = Router()

    async def process_message(self, message: str, customer_id: str,
                              channel: str = "chat") -> Dict[str, Any]:
        """Process a customer message through the agent pipeline."""

        # Step 1: Get customer context
        context = await self._get_customer_context(customer_id)

        # Step 2: Triage and route
        routing = await self.router.route(message, context)

        # Step 3: Execute primary agent
        primary_result = await self._execute_agent(
            routing.target_agent.value,
            message,
            context
        )

        # Step 4: Sentiment analysis
        sentiment = await self._analyze_sentiment(message)

        # Step 5: Post-process and decide next steps
        final_response = await self._post_process(
            primary_result,
            sentiment,
            routing,
            context
        )

        # Step 6: Log interaction
        await self._log_interaction(
            customer_id, message, final_response, routing, sentiment
        )

        return final_response

    async def _execute_agent(self, agent_name: str, message: str,
                             context: dict) -> dict:
        """Execute a specific agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        result = await agent.ainvoke({
            "input": message,
            "chat_history": context.get("chat_history", [])
        })

        return {
            "output": result["output"],
            "agent": agent_name,
            "intermediate_steps": result.get("intermediate_steps", [])
        }

    async def _analyze_sentiment(self, message: str) -> dict:
        """Analyze message sentiment."""
        result = await self.agents["sentiment"].ainvoke({
            "input": f"Analyze the sentiment of this message and return the score: {message}"
        })

        try:
            return eval(result["output"])
        except:
            return {"score": 0.0, "label": "NEUTRAL"}

    async def _post_process(self, primary_result: dict, sentiment: dict,
                           routing, context: dict) -> dict:
        """Post-process agent output and determine final response."""

        response = primary_result["output"]
        needs_escalation = False

        # Check sentiment-based escalation
        if sentiment.get("score", 0) <= settings.escalation_sentiment_threshold:
            needs_escalation = True

        # Check confidence-based escalation
        if routing.confidence < settings.escalation_confidence_threshold:
            needs_escalation = True

        # If escalation needed, run escalation agent
        if needs_escalation:
            escalation_result = await self._execute_agent(
                "escalation",
                f"Customer message: {primary_result['output']}\nSentiment: {sentiment}",
                context
            )
            response = escalation_result["output"]

        return {
            "response": response,
            "primary_agent": primary_result["agent"],
            "sentiment_score": sentiment.get("score", 0),
            "escalation_triggered": needs_escalation,
            "confidence": routing.confidence
        }

    async def _get_customer_context(self, customer_id: str) -> dict:
        """Get customer context."""
        from database.customer_repo import CustomerRepository
        repo = CustomerRepository()
        return repo.get_context(customer_id)

    async def _log_interaction(self, customer_id: str, message: str,
                              response: dict, routing, sentiment: dict):
        """Log the interaction for analytics and training."""
        from analytics.logger import InteractionLogger
        logger = InteractionLogger()
        await logger.log({
            "customer_id": customer_id,
            "message": message,
            "response": response,
            "routing": routing,
            "sentiment": sentiment,
            "timestamp": datetime.utcnow().isoformat()
        })
```

### 8.3 Streaming Response Handler

```python
# streaming.py
from langchain_core.callbacks import AsyncCallbackHandler
from typing import Any, Dict

class StreamingCallbackHandler(AsyncCallbackHandler):
    """Handles streaming responses from agents."""

    def __init__(self, websocket):
        self.websocket = websocket
        self.tokens = []

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Stream new token to client."""
        self.tokens.append(token)
        await self.websocket.send_json({
            "type": "token",
            "content": token
        })

    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str,
                           **kwargs: Any) -> None:
        """Notify client of tool execution."""
        await self.websocket.send_json({
            "type": "tool_start",
            "tool": serialized.get("name", "unknown"),
            "input": input_str
        })

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Notify client of tool completion."""
        await self.websocket.send_json({
            "type": "tool_end",
            "output": output
        })

    async def on_agent_finish(self, finish, **kwargs: Any) -> None:
        """Send final response to client."""
        await self.websocket.send_json({
            "type": "complete",
            "content": "".join(self.tokens)
        })
```

### 8.4 WebSocket Endpoint

```python
# websocket_handler.py
from fastapi import WebSocket, WebSocketDisconnect
from orchestrator import CustomerServiceOrchestrator

orchestrator = CustomerServiceOrchestrator()

@app.websocket("/ws/chat/{customer_id}")
async def websocket_endpoint(websocket: WebSocket, customer_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")

            if not message:
                await websocket.send_json({
                    "type": "error",
                    "content": "Empty message"
                })
                continue

            # Process through orchestrator
            handler = StreamingCallbackHandler(websocket)

            result = await orchestrator.process_message(
                message=message,
                customer_id=customer_id,
                channel="chat"
            )

            # Send final response
            await websocket.send_json({
                "type": "response",
                "content": result["response"],
                "agent": result["primary_agent"],
                "sentiment": result["sentiment_score"],
                "escalation": result["escalation_triggered"]
            })

    except WebSocketDisconnect:
        print(f"Client {customer_id} disconnected")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": str(e)
        })
```

### 8.5 Deployment Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CS_LLM_MODEL=gpt-4
      - CS_VECTOR_STORE_PROVIDER=pinecone
      - CS_VECTOR_STORE_INDEX=customer-service-kb
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  worker:
    build: .
    command: celery -A tasks worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=customer_service
      - POSTGRES_USER=cs_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  langsmith:
    image: langsmith/langsmith:latest
    ports:
      - "8080:8080"

volumes:
  postgres_data:
```

---

## 9. Testing Strategy

### 9.1 Testing Pyramid

```
                    ┌──────────┐
                    │   E2E    │  (5%)
                   ─┤  Tests   ├─
                  / └──────────┘ \
                 / ┌────────────┐ \
                /  │ Integration │  \
               /   │   Tests     │   \
              /    │   (15%)     │    \
             /     └─────────────┘     \
            /      ┌─────────────┐      \
           /       │  Component  │       \
          /        │   Tests     │        \
         /         │   (30%)     │         \
        /          └─────────────┘          \
       /           ┌─────────────┐           \
      /            │  Unit Tests  │            \
     /             │   (50%)      │             \
    /              └──────────────┘              \
   ──────────────────────────────────────────────
```

### 9.2 Unit Tests

```python
# tests/unit/test_triage_agent.py
import pytest
from agents.triage_agent import classify_intent, parse_classification

class TestTriageAgent:
    """Unit tests for the Triage Agent."""

    def test_classify_billing_intent(self):
        """Test billing intent classification."""
        result = classify_intent("I was charged twice for my subscription")
        assert result["category"] == "BILLING"
        assert result["priority"] in ["HIGH", "MEDIUM"]

    def test_classify_technical_intent(self):
        """Test technical intent classification."""
        result = classify_intent("The app keeps crashing when I try to upload files")
        assert result["category"] == "TECHNICAL"

    def test_classify_complaint_intent(self):
        """Test complaint intent classification."""
        result = classify_intent("Your service is terrible and I want to cancel")
        assert result["category"] == "COMPLAINT"

    def test_classify_general_intent(self):
        """Test general intent classification."""
        result = classify_intent("What are your business hours?")
        assert result["category"] == "GENERAL"

    def test_parse_classification_valid(self):
        """Test parsing valid classification response."""
        content = '{"category": "BILLING", "priority": "HIGH", "confidence": 0.95}'
        result = parse_classification(content)
        assert result["category"] == "BILLING"
        assert result["priority"] == "HIGH"
        assert result["confidence"] == 0.95

    def test_parse_classification_invalid(self):
        """Test parsing invalid classification response."""
        content = "not json at all"
        result = parse_classification(content)
        assert result["category"] == "GENERAL"
        assert result["confidence"] == 0.5

    def test_entity_extraction_order_id(self):
        """Test order ID extraction."""
        from agents.triage_agent import extract_entities
        result = extract_entities("My order #12345 hasn't arrived")
        assert "order_id" in result
        assert result["order_id"] == "12345"

    def test_language_detection_english(self):
        """Test English language detection."""
        from agents.triage_agent import detect_language
        result = detect_language("Hello, I need help with my account")
        assert result == "en"

    def test_language_detection_spanish(self):
        """Test Spanish language detection."""
        from agents.triage_agent import detect_language
        result = detect_language("Hola, necesito ayuda con mi cuenta")
        assert result == "es"
```

```python
# tests/unit/test_sentiment_agent.py
import pytest
from agents.sentiment_agent import analyze_sentiment, should_escalate_sentiment

class TestSentimentAgent:
    """Unit tests for the Sentiment Analysis Agent."""

    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        result = analyze_sentiment("I love this product! It's amazing!")
        assert result["score"] > 0.5
        assert result["label"] == "POSITIVE"

    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        result = analyze_sentiment("This is terrible and I'm very frustrated")
        assert result["score"] < -0.3
        assert result["label"] == "NEGATIVE"

    def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        result = analyze_sentiment("I have a question about my invoice")
        assert -0.3 <= result["score"] <= 0.3

    def test_escalation_trigger_very_negative(self):
        """Test escalation trigger for very negative sentiment."""
        history = [-0.8, -0.9, -0.85]
        result = should_escalate_sentiment(history)
        assert result["should_escalate"] is True
        assert result["urgency"] == "high"

    def test_escalation_trigger_declining(self):
        """Test escalation trigger for declining sentiment."""
        history = [0.5, 0.0, -0.5, -0.6]
        result = should_escalate_sentiment(history)
        assert result["should_escalate"] is True

    def test_no_escalation_stable(self):
        """Test no escalation for stable sentiment."""
        history = [0.5, 0.4, 0.6, 0.5]
        result = should_escalate_sentiment(history)
        assert result["should_escalate"] is False

    def test_no_escalation_insufficient_data(self):
        """Test no escalation with insufficient data."""
        history = [0.5]
        result = should_escalate_sentiment(history)
        assert result["should_escalate"] is False
        assert result["reason"] == "insufficient_data"
```

### 9.3 Integration Tests

```python
# tests/integration/test_agent_pipeline.py
import pytest
from orchestrator import CustomerServiceOrchestrator

class TestAgentPipeline:
    """Integration tests for the complete agent pipeline."""

    @pytest.fixture
    def orchestrator(self):
        return CustomerServiceOrchestrator()

    @pytest.mark.asyncio
    async def test_simple_inquiry_pipeline(self, orchestrator):
        """Test a simple inquiry through the full pipeline."""
        result = await orchestrator.process_message(
            message="What is your return policy?",
            customer_id="test-customer-1"
        )

        assert "response" in result
        assert result["primary_agent"] == "resolution_agent"
        assert result["confidence"] > 0.5
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_billing_inquiry_pipeline(self, orchestrator):
        """Test a billing inquiry through the full pipeline."""
        result = await orchestrator.process_message(
            message="I was charged twice for my subscription this month",
            customer_id="test-customer-2"
        )

        assert result["primary_agent"] in ["resolution_agent", "escalation_agent"]
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_complaint_escalation_pipeline(self, orchestrator):
        """Test complaint triggers escalation."""
        result = await orchestrator.process_message(
            message="This is unacceptable! I want to speak to a manager now!",
            customer_id="test-customer-3"
        )

        assert result["escalation_triggered"] is True
        assert result["sentiment_score"] < -0.3

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, orchestrator):
        """Test multi-turn conversation context."""
        customer_id = "test-customer-4"

        # First message
        result1 = await orchestrator.process_message(
            message="I can't log into my account",
            customer_id=customer_id
        )

        # Follow-up message
        result2 = await orchestrator.process_message(
            message="I tried resetting my password but didn't get the email",
            customer_id=customer_id
        )

        assert result2["primary_agent"] == "resolution_agent"
        assert result2["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_vip_customer_priority(self, orchestrator):
        """Test VIP customer gets priority handling."""
        result = await orchestrator.process_message(
            message="My service is down",
            customer_id="vip-customer-1"
        )

        # VIP customers should get high priority
        assert result["confidence"] > 0.5
```

### 9.4 End-to-End Tests

```python
# tests/e2e/test_customer_service_flow.py
import pytest
import asyncio
from testclient import TestClient
from main import app

class TestCustomerServiceE2E:
    """End-to-end tests for the customer service system."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_complete_inquiry_flow(self, client):
        """Test a complete customer inquiry from start to finish."""
        # Send initial message
        response = client.post("/api/v1/message", json={
            "customer_id": "e2e-test-1",
            "message": "I need help with my recent order",
            "channel": "chat"
        })

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["agent_type"] in ["resolution_agent", "escalation_agent"]
        assert data["confidence"] > 0

    def test_escalation_flow(self, client):
        """Test escalation flow for angry customers."""
        response = client.post("/api/v1/message", json={
            "customer_id": "e2e-test-2",
            "message": "I'm extremely frustrated! This is the third time I've contacted you about this issue!",
            "channel": "chat"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["escalation_recommended"] is True
        assert data["sentiment_score"] < -0.3

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def send_request(i):
            return client.post("/api/v1/message", json={
                "customer_id": f"concurrent-test-{i}",
                "message": f"Test message {i}",
                "channel": "chat"
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_request, i) for i in range(10)]
            results = [f.result() for f in futures]

        assert all(r.status_code == 200 for r in results)
```

### 9.5 Performance Tests

```python
# tests/performance/test_performance.py
import pytest
import time
import asyncio
from locust import HttpUser, task, between

class CustomerServiceLoadTest(HttpUser):
    """Load test for the customer service API."""

    wait_time = between(1, 3)

    @task(3)
    def send_simple_message(self):
        """Send a simple customer message."""
        self.client.post("/api/v1/message", json={
            "customer_id": f"load-test-{self.user_id}",
            "message": "What is your return policy?",
            "channel": "chat"
        })

    @task(1)
    def send_complex_message(self):
        """Send a complex customer message."""
        self.client.post("/api/v1/message", json={
            "customer_id": f"load-test-{self.user_id}",
            "message": "I have a complicated billing issue with my enterprise account. "
                       "I was charged for 50 seats but only have 45 users. "
                       "I need this resolved before my next billing cycle.",
            "channel": "chat"
        })

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/api/v1/health")

# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    @pytest.mark.asyncio
    async def test_response_time_simple_query(self):
        """Test response time for simple queries."""
        from orchestrator import CustomerServiceOrchestrator

        orchestrator = CustomerServiceOrchestrator()

        start = time.time()
        result = await orchestrator.process_message(
            message="What is your return policy?",
            customer_id="perf-test-1"
        )
        elapsed = time.time() - start

        assert elapsed < 5.0  # Should respond within 5 seconds
        assert "response" in result

    @pytest.mark.asyncio
    async def test_response_time_complex_query(self):
        """Test response time for complex queries."""
        from orchestrator import CustomerServiceOrchestrator

        orchestrator = CustomerServiceOrchestrator()

        start = time.time()
        result = await orchestrator.process_message(
            message="I have a complicated billing issue with my enterprise account",
            customer_id="perf-test-2"
        )
        elapsed = time.time() - start

        assert elapsed < 15.0  # Complex queries should respond within 15 seconds
        assert "response" in result

    @pytest.mark.asyncio
    async def test_concurrent_load(self):
        """Test system under concurrent load."""
        from orchestrator import CustomerServiceOrchestrator

        orchestrator = CustomerServiceOrchestrator()

        async def send_message(i):
            return await orchestrator.process_message(
                message=f"Test message {i}",
                customer_id=f"concurrent-{i}"
            )

        start = time.time()
        tasks = [send_message(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        assert len(results) == 50
        assert elapsed < 60.0  # 50 messages should process within 60 seconds
```

### 9.6 Test Data Management

```python
# tests/fixtures/test_data.py
"""Test data fixtures for customer service tests."""

SAMPLE_CUSTOMERS = [
    {
        "id": "cust-001",
        "name": "John Smith",
        "tier": "enterprise",
        "email": "john.smith@bigcorp.com",
        "health_score": 0.85,
        "lifetime_value": 150000
    },
    {
        "id": "cust-002",
        "name": "Jane Doe",
        "tier": "premium",
        "email": "jane.doe@medium.com",
        "health_score": 0.65,
        "lifetime_value": 25000
    },
    {
        "id": "cust-003",
        "name": "Bob Wilson",
        "tier": "standard",
        "email": "bob@small.com",
        "health_score": 0.35,
        "lifetime_value": 5000
    }
]

SAMPLE_MESSAGES = {
    "billing_inquiry": "I have a question about my invoice",
    "technical_issue": "The app crashes when I try to save my work",
    "account_help": "I forgot my password and can't reset it",
    "complaint": "Your service has been terrible lately",
    "general_question": "What are your business hours?",
    "refund_request": "I'd like to request a refund for my last order",
    "vip_issue": "Our entire team can't access the platform",
    "angry_customer": "I'm furious! This is the worst service ever!"
}

SAMPLE_CONVERSATIONS = [
    {
        "id": "conv-001",
        "customer_id": "cust-001",
        "messages": [
            {"role": "customer", "text": "Hi, I need help with my account"},
            {"role": "agent", "text": "Hello! I'd be happy to help. What seems to be the issue?"},
            {"role": "customer", "text": "I can't log in"},
            {"role": "agent", "text": "I'm sorry to hear that. Let me help you reset your password."}
        ],
        "resolved": True,
        "satisfaction": 4.5
    },
    {
        "id": "conv-002",
        "customer_id": "cust-003",
        "messages": [
            {"role": "customer", "text": "This is ridiculous! I've been waiting for hours!"},
            {"role": "agent", "text": "I apologize for the wait. Let me help you right away."},
            {"role": "customer", "text": "You better fix this or I'm canceling!"}
        ],
        "resolved": False,
        "satisfaction": 1.5
    }
]
```

### 9.7 Monitoring and Observability

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
MESSAGES_PROCESSED = Counter(
    "cs_messages_processed_total",
    "Total messages processed",
    ["agent_type", "channel", "priority"]
)

RESPONSE_TIME = Histogram(
    "cs_response_time_seconds",
    "Response time in seconds",
    ["agent_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

SENTIMENT_SCORE = Gauge(
    "cs_sentiment_score",
    "Current sentiment score",
    ["customer_id"]
)

ESCALATION_COUNTER = Counter(
    "cs_escalations_total",
    "Total escalations",
    ["reason", "agent_type"]
)

ACTIVE_CONVERSATIONS = Gauge(
    "cs_active_conversations",
    "Number of active conversations"
)

RESOLUTION_RATE = Gauge(
    "cs_resolution_rate",
    "Auto-resolution rate",
    ["agent_type"]
)

class MetricsCollector:
    """Collects and exports metrics."""

    @staticmethod
    def record_message(agent_type: str, channel: str, priority: str):
        """Record a processed message."""
        MESSAGES_PROCESSED.labels(
            agent_type=agent_type,
            channel=channel,
            priority=priority
        ).inc()

    @staticmethod
    def record_response_time(agent_type: str, duration: float):
        """Record response time."""
        RESPONSE_TIME.labels(agent_type=agent_type).observe(duration)

    @staticmethod
    def record_sentiment(customer_id: str, score: float):
        """Record sentiment score."""
        SENTIMENT_SCORE.labels(customer_id=customer_id).set(score)

    @staticmethod
    def record_escalation(reason: str, agent_type: str):
        """Record an escalation."""
        ESCALATION_COUNTER.labels(
            reason=reason,
            agent_type=agent_type
        ).inc()

    @staticmethod
    def set_active_conversations(count: int):
        """Set active conversation count."""
        ACTIVE_CONVERSATIONS.set(count)

    @staticmethod
    def record_resolution_rate(agent_type: str, rate: float):
        """Record auto-resolution rate."""
        RESOLUTION_RATE.labels(agent_type=agent_type).set(rate)
```

---

## Appendix A: Environment Variables

```bash
# .env
# LLM Configuration
OPENAI_API_KEY=sk-...
CS_LLM_MODEL=gpt-4
CS_LLM_TEMPERATURE=0.3

# Vector Store
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
CS_VECTOR_STORE_INDEX=customer-service-kb

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/customer_service
REDIS_URL=redis://localhost:6379

# API
CS_API_HOST=0.0.0.0
CS_API_PORT=8000

# Monitoring
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=customer-service

# Escalation
CS_ESCALATION_CONFIDENCE_THRESHOLD=0.6
CS_HUMAN_HANDOFF_TIMEOUT_MINUTES=30

# Sentiment
CS_NEGATIVE_SENTIMENT_THRESHOLD=-0.5
CS_ESCALATION_SENTIMENT_THRESHOLD=-0.7
```

## Appendix B: Project Structure

```
customer-service/
├── agents/
│   ├── __init__.py
│   ├── triage_agent.py
│   ├── resolution_agent.py
│   ├── escalation_agent.py
│   ├── sentiment_agent.py
│   ├── customer_success_agent.py
│   └── routing.py
├── analytics/
│   ├── __init__.py
│   ├── health.py
│   ├── churn.py
│   ├── usage.py
│   └── logger.py
├── api/
│   ├── __init__.py
│   ├── routes.py
│   └── websocket.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── database/
│   ├── __init__.py
│   ├── customer_repo.py
│   └── models.py
├── knowledge_base/
│   ├── __init__.py
│   ├── ingestion.py
│   ├── retriever.py
│   ├── maintenance.py
│   └── models.py
├── monitoring/
│   ├── __init__.py
│   └── metrics.py
├── orchestrator.py
├── policies/
│   ├── __init__.py
│   └── escalation_policies.py
├── sentiment/
│   ├── __init__.py
│   └── response_adjuster.py
├── streaming.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_triage_agent.py
│   │   ├── test_sentiment_agent.py
│   │   └── test_resolution_agent.py
│   ├── integration/
│   │   └── test_agent_pipeline.py
│   ├── e2e/
│   │   └── test_customer_service_flow.py
│   ├── performance/
│   │   └── test_performance.py
│   └── fixtures/
│       └── test_data.py
├── workflows/
│   ├── __init__.py
│   └── resolution_workflows.py
├── main.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env
```

## Appendix C: Requirements

```txt
# requirements.txt
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.10
langchain-pinecone>=0.0.1
openai>=1.0.0
pinecone-client>=3.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
websockets>=12.0
redis>=5.0.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
transformers>=4.35.0
torch>=2.1.0
langdetect>=1.0.9
prometheus-client>=0.19.0
langsmith>=0.0.80
pytest>=7.4.0
pytest-asyncio>=0.21.0
locust>=2.18.0
```

---

*Document Version: 1.0*
*Last Updated: 2026-10-01*
*Author: AI Customer Service Implementation Team*</longcat_arg_key>
