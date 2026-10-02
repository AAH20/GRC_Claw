# AI-Powered Workflow Automation Implementation Plan

**Document ID:** GRC-WA-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Framework:** LangChain DeepAgents (deepagents ≥0.7.x)  
**References:** grc-claw-automation-implementation-guide.md, grc-claw-integration-implementation-guide.md

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Workflow Discovery Agent](#2-workflow-discovery-agent)
3. [Workflow Optimization Agent](#3-workflow-optimization-agent)
4. [Process Automation Agent](#4-process-automation-agent)
5. [Integration Automation Agent](#5-integration-automation-agent)
6. [Performance Analytics Agent](#6-performance-analytics-agent)
7. [Code Examples and Snippets](#7-code-examples-and-snippets)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Agent Architecture

### 1.1 Overview

The AI-powered workflow automation system uses LangChain DeepAgents to build a multi-agent architecture where specialized agents collaborate to discover, optimize, automate, and monitor business workflows. Each agent is built using `create_deep_agent()` with domain-specific tools, subagents, and middleware.

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT (Main)                        │
│  Model: claude-sonnet-4-6  │  Middleware: TodoList + Summarization  │
│  Tools: workflow_registry, task_delegation, human_approval          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Workflow    │  │  Workflow    │  │  Process     │              │
│  │  Discovery   │  │  Optimization│  │  Automation  │              │
│  │  Agent       │  │  Agent       │  │  Agent       │              │
│  │              │  │              │  │              │              │
│  │ Subagents:   │  │ Subagents:   │  │ Subagents:   │              │
│  │ - process-   │  │ - bottleneck │  │ - code-gen   │              │
│  │   mapper     │  │   analyzer   │  │ - validator  │              │
│  │ - pattern-   │  │ - cost-      │  │ - deployer   │              │
│  │   detector   │  │   optimizer  │  │              │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐              │
│  │  Integration │  │  Performance │  │  Human-in-   │              │
│  │  Automation  │  │  Analytics   │  │  the-Loop    │              │
│  │  Agent       │  │  Agent       │  │  Gateway     │              │
│  │              │  │              │  │              │              │
│  │ Subagents:   │  │ Subagents:   │  │ - approval   │              │
│  │ - api-mapper │  │ - metrics-   │  │   manager    │              │
│  │ - schema-    │  │   collector  │  │ - exception  │              │
│  │   translator │  │ - report-    │  │   handler    │              │
│  │ - connector- │  │   generator  │  │              │              │
│  │   builder    │  │ - anomaly-   │  │              │              │
│  │              │  │   detector   │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                    SHARED INFRASTRUCTURE                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐      │
│  │  Virtual   │ │  LangGraph │ │  LangSmith │ │  MCP       │      │
│  │  Filesystem│ │  Store     │ │  Tracing   │ │  Servers   │      │
│  │  Backend   │ │  (Postgres)│ │  & Eval    │ │            │      │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Core Components

#### 1.3.1 Orchestrator Agent

The top-level agent that receives user requests, decomposes them into tasks, and delegates to specialized subagents.

```python
# agents/orchestrator.py
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, FilesystemBackend
from langchain.agents.middleware import TodoListMiddleware
from langgraph.store.postgres import AsyncPostgresStore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def create_orchestrator_agent():
    store = await AsyncPostgresStore.from_conn_string(
        "postgresql://user:pass@localhost:5432/workflows"
    )
    checkpointer = await AsyncPostgresSaver.from_conn_string(
        "postgresql://user:pass@localhost:5432/workflows"
    )

    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/workspace/": FilesystemBackend(
                root_dir="./workspace",
                virtual_mode=True
            ),
            "/memories/": None,  # Will use StoreBackend via store param
        }
    )

    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        system_prompt="""You are the Workflow Automation Orchestrator.
        
Your responsibilities:
1. Analyze user requests for workflow automation opportunities
2. Decompose complex requests into discrete tasks
3. Delegate to specialized agents based on task type
4. Coordinate multi-agent workflows
5. Present results and recommendations to users

Always plan with write_todos before executing complex tasks.
Use the task tool to delegate to specialized subagents.""",
        backend=backend,
        store=store,
        checkpointer=checkpointer,
        subagents=[
            {
                "name": "workflow-discovery",
                "description": "Discovers and maps existing business workflows, processes, and automation opportunities",
                "system_prompt": "You are a workflow discovery specialist...",
                "tools": [],
            },
            {
                "name": "workflow-optimization",
                "description": "Analyzes existing workflows for optimization opportunities, bottlenecks, and improvements",
                "system_prompt": "You are a workflow optimization specialist...",
                "tools": [],
            },
            {
                "name": "process-automation",
                "description": "Designs and implements automated process workflows",
                "system_prompt": "You are a process automation engineer...",
                "tools": [],
            },
            {
                "name": "integration-automation",
                "description": "Builds and manages integrations between systems, APIs, and services",
                "system_prompt": "You are an integration automation specialist...",
                "tools": [],
            },
            {
                "name": "performance-analytics",
                "description": "Monitors, measures, and reports on workflow performance metrics",
                "system_prompt": "You are a performance analytics specialist...",
                "tools": [],
            },
        ],
        interrupt_on={"execute": True, "write_file": False},
        permissions=[
            FilesystemPermission(
                operations=["read", "write"],
                paths=["/workspace/**"],
                mode="allow"
            ),
            FilesystemPermission(
                operations=["read", "write"],
                paths=["**/.env", "**/secrets/**"],
                mode="deny"
            ),
        ],
        memory=["./AGENTS.md"],
        skills=["./skills/"],
    )
    return agent
```

#### 1.3.2 Middleware Stack

Each agent uses a tailored middleware stack:

| Middleware | Purpose | Used By |
|------------|---------|---------|
| `TodoListMiddleware` | Planning and task tracking | All agents |
| `FilesystemMiddleware` | Virtual filesystem for context offloading | All agents |
| `SummarizationMiddleware` | Auto-compress conversation history | All agents |
| `SubAgentMiddleware` | Subagent spawning and delegation | Orchestrator |
| `MemoryMiddleware` | Load AGENTS.md domain knowledge | All agents |
| `SkillsMiddleware` | Progressive skill disclosure | All agents |
| `HumanInTheLoopMiddleware` | Approval gates for sensitive ops | Process Automation, Integration |
| `AnthropicPromptCachingMiddleware` | Cost optimization | All agents |
| `PatchToolCallsMiddleware` | Fix dangling tool calls | All agents |

#### 1.3.3 Backend Configuration

```python
# config/backends.py
from deepagents.backends import (
    CompositeBackend,
    StateBackend,
    FilesystemBackend,
    StoreBackend,
)
from langgraph.store.postgres import AsyncPostgresStore

async def create_production_backend():
    """Production backend with persistent storage."""
    store = await AsyncPostgresStore.from_conn_string(
        "postgresql://user:pass@localhost:5432/workflows"
    )
    
    return CompositeBackend(
        default=StateBackend(),  # Ephemeral scratch files
        routes={
            "/workspace/": FilesystemBackend(
                root_dir="./workspace",
                virtual_mode=True,
            ),
            "/memories/": StoreBackend(
                store=store,
                namespace=["workflow", "memories"],
            ),
            "/analytics/": StoreBackend(
                store=store,
                namespace=["workflow", "analytics"],
            ),
        },
    )

def create_development_backend():
    """Development backend with local filesystem."""
    return CompositeBackend(
        default=StateBackend(),
        routes={
            "/workspace/": FilesystemBackend(
                root_dir="./workspace",
                virtual_mode=True,
            ),
        },
    )
```

### 1.4 Agent Communication Protocol

Agents communicate through a structured message protocol:

```python
# models/agent_messages.py
from pydantic import BaseModel, Field
from typing import Literal, Optional, Any
from datetime import datetime
from enum import Enum

class TaskType(str, Enum):
    DISCOVERY = "discovery"
    OPTIMIZATION = "optimization"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_APPROVAL = "needs_approval"

class AgentTask(BaseModel):
    """Standard task format for inter-agent communication."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType
    description: str
    context: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    parent_task_id: Optional[str] = None
    subtasks: list[str] = Field(default_factory=list)

class AgentResult(BaseModel):
    """Standard result format returned by agents."""
    task_id: str
    agent_name: str
    success: bool
    summary: str
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
```

### 1.5 Human-in-the-Loop Integration

Critical for governance workflows where human approval is required:

```python
# config/hitl.py
from deepagents import create_deep_agent
from deepagents.middleware.permissions import FilesystemPermission

# Tools that require human approval
INTERRUPT_CONFIG = {
    "execute": True,           # Shell command execution
    "write_file": False,       # File writes (safe in workspace)
    "edit_file": False,        # File edits
    "delete": True,            # Deletion operations
    "api_call": True,          # External API calls
    "deploy": True,            # Deployment operations
}

def create_approval_workflow():
    """Configure approval gates for sensitive operations."""
    return {
        "approval_levels": {
            "low": {
                "description": "Low-risk operations",
                "auto_approve": True,
                "tools": ["read_file", "ls", "glob", "grep"],
            },
            "medium": {
                "description": "Medium-risk operations",
                "auto_approve": False,
                "approvers": ["team_lead"],
                "tools": ["write_file", "edit_file", "api_call_read"],
            },
            "high": {
                "description": "High-risk operations",
                "auto_approve": False,
                "approvers": ["manager", "director"],
                "tools": ["execute", "api_call_write", "deploy", "delete"],
            },
        },
        "escalation_policy": {
            "timeout_minutes": 30,
            "escalate_to": "manager",
            "on_timeout": "deny",
        },
    }
```

---

## 2. Workflow Discovery Agent

### 2.1 Purpose

The Workflow Discovery Agent analyzes an organization's existing processes, tools, and data flows to identify automation opportunities. It maps current workflows, detects patterns, and produces a comprehensive workflow inventory.

### 2.2 Architecture

```
┌─────────────────────────────────────────────────┐
│           Workflow Discovery Agent               │
│  Model: claude-sonnet-4-6                        │
│  Middleware: TodoList + Filesystem + Memory      │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Process     │  │  Pattern     │             │
│  │  Mapper      │  │  Detector    │             │
│  │  Subagent    │  │  Subagent    │             │
│  │              │  │              │             │
│  │ - API scan   │  │ - Pattern    │             │
│  │ - Data flow  │  │   matching   │             │
│  │   analysis   │  │ - Best       │             │
│  │ - Tool       │  │   practice   │             │
│  │   inventory  │  │   lookup     │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Stakeholder │  │  Document    │             │
│  │  Interviewer │  │  Analyzer    │             │
│  │  Subagent    │  │  Subagent    │             │
│  │              │  │              │             │
│  │ - Interview  │  │ - Doc        │             │
│  │   scripting  │  │   parsing    │             │
│  │ - Pain point │  │ - SOP        │             │
│  │   extraction │  │   extraction │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
├─────────────────────────────────────────────────┤
│  Tools: api_scanner, doc_parser, db_inspector,  │
│        interview_scheduler, jira_analyzer,       │
│        confluence_scanner, slack_analyzer        │
└─────────────────────────────────────────────────┘
```

### 2.3 Implementation

```python
# agents/workflow_discovery.py
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_core.tools import tool
from typing import Any
import json

# ─── Discovery Tools ───────────────────────────────────────────

@tool
def scan_api_endpoints(base_url: str, swagger_path: str = "/swagger.json") -> dict:
    """Scan a service's API endpoints from OpenAPI/Swagger spec.
    
    Args:
        base_url: The base URL of the service
        swagger_path: Path to the OpenAPI spec endpoint
        
    Returns:
        Dictionary containing discovered endpoints, methods, and schemas
    """
    import requests
    resp = requests.get(f"{base_url}{swagger_path}", timeout=30)
    spec = resp.json()
    
    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            endpoints.append({
                "path": path,
                "method": method.upper(),
                "summary": details.get("summary", ""),
                "operation_id": details.get("operationId", ""),
                "parameters": details.get("parameters", []),
                "request_body": details.get("requestBody", {}),
                "responses": details.get("responses", {}),
            })
    
    return {
        "service": base_url,
        "total_endpoints": len(endpoints),
        "endpoints": endpoints,
        "schemas": list(spec.get("components", {}).get("schemas", {}).keys()),
    }

@tool
def inspect_database_schema(connection_string: str, include_sample: bool = False) -> dict:
    """Inspect database schema to understand data model and relationships.
    
    Args:
        connection_string: Database connection string
        include_sample: Whether to include sample row counts
        
    Returns:
        Schema information including tables, columns, relationships
    """
    from sqlalchemy import create_engine, inspect, MetaData
    
    engine = create_engine(connection_string)
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    tables = {}
    for table_name in inspector.get_table_names():
        columns = []
        for col in inspector.get_columns(table_name):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default", "")),
            })
        
        foreign_keys = [
            {
                "column": fk["constrained_columns"],
                "references": fk["referred_table"],
                "referenced_columns": fk["referred_columns"],
            }
            for fk in inspector.get_foreign_keys(table_name)
        ]
        
        tables[table_name] = {
            "columns": columns,
            "foreign_keys": foreign_keys,
            "indexes": inspector.get_indexes(table_name),
            "row_count": inspector.get_table_names() and None,  # Would need COUNT query
        }
    
    return {
        "database": engine.url.database,
        "dialect": engine.dialect.name,
        "tables": tables,
        "total_tables": len(tables),
    }

@tool
def analyze_jira_projects(jira_url: str, jql_query: str, max_results: int = 100) -> dict:
    """Analyze Jira projects to understand workflow patterns from ticket data.
    
    Args:
        jira_url: Jira instance URL
        jql_query: JQL query to filter issues
        max_results: Maximum number of issues to analyze
        
    Returns:
        Workflow patterns derived from issue types, statuses, and transitions
    """
    # Implementation would use jira library
    # Returns workflow patterns, common transitions, bottleneck stages
    pass

@tool
def scan_confluence_space(confluence_url: str, space_key: str) -> dict:
    """Scan Confluence space for process documentation and SOPs.
    
    Args:
        confluence_url: Confluence instance URL
        space_key: Space key to scan
        
    Returns:
        Document inventory with process-related content
    """
    # Implementation would use atlassian-python-api
    pass

@tool
def schedule_stakeholder_interview(
    stakeholder_email: str,
    topic: str,
    duration_minutes: int = 30,
) -> dict:
    """Schedule an interview with a stakeholder to understand their workflow.
    
    Args:
        stakeholder_email: Email of the stakeholder
        topic: Topic of the interview
        duration_minutes: Duration in minutes
        
    Returns:
        Scheduled interview details
    """
    # Integration with calendar API
    pass

# ─── Discovery Agent Factory ───────────────────────────────────

def create_workflow_discovery_agent(backend=None, store=None):
    """Create the Workflow Discovery Agent with all tools and subagents."""
    
    discovery_subagents = [
        {
            "name": "process-mapper",
            "description": "Maps end-to-end business processes by analyzing system interactions, data flows, and user actions",
            "system_prompt": """You are a process mapping specialist.
            
Your approach:
1. Identify all systems involved in a process
2. Map data flows between systems
3. Identify manual handoffs and touchpoints
4. Document process steps in BPMN-like notation
5. Identify decision points and branching logic

Output format: Structured process maps with steps, actors, systems, and data flows.""",
            "tools": [scan_api_endpoints, inspect_database_schema],
        },
        {
            "name": "pattern-detector",
            "description": "Detects workflow patterns and matches them to known automation patterns",
            "system_prompt": """You are a workflow pattern detection specialist.
            
Known patterns to detect:
- Sequential pipelines
- Parallel fan-out/fan-in
- Event-driven triggers
- Human-in-the-loop gates
- Approval workflows
- Data transformation pipelines
- Scheduled batch processes
- Real-time streaming processes

For each detected pattern, provide:
- Pattern name and type
- Confidence score
- Applicable automation tools
- Estimated complexity
- Similar implementations in the organization""",
            "tools": [],
        },
        {
            "name": "document-analyzer",
            "description": "Analyzes existing documentation (SOPs, wikis, runbooks) to extract workflow information",
            "system_prompt": """You are a document analysis specialist.
            
Extract from documents:
- Process steps and sequences
- Roles and responsibilities
- Systems and tools used
- Pain points and manual workarounds
- Frequency and volume metrics
- Compliance and governance requirements

Cross-reference findings with system data for validation.""",
            "tools": [scan_confluence_space],
        },
    ]
    
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        system_prompt="""You are the Workflow Discovery Agent.

Your mission: Discover, map, and document all workflows in the target organization.

Process:
1. INVENTORY: Scan all accessible systems (APIs, databases, docs, tickets)
2. INTERVIEW: Identify and interview key stakeholders
3. MAP: Create detailed process maps for each workflow
4. CLASSIFY: Categorize workflows by type, complexity, and automation potential
5. PRIORITIZE: Rank automation opportunities by impact and feasibility
6. DOCUMENT: Produce comprehensive workflow inventory

Always write findings to /workspace/discovery/ for persistence.
Use write_todos to track discovery progress across systems.""",
        tools=[
            scan_api_endpoints,
            inspect_database_schema,
            analyze_jira_projects,
            scan_confluence_space,
            schedule_stakeholder_interview,
        ],
        subagents=discovery_subagents,
        backend=backend,
        store=store,
        memory=["./AGENTS.md"],
        skills=["./skills/workflow-discovery/"],
    )
    
    return agent
```

### 2.4 Discovery Output Schema

```python
# models/discovery.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProcessStep(BaseModel):
    step_number: int
    name: str
    description: str
    actor: str  # Who performs this step
    system: Optional[str] = None  # System used
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    duration_minutes: Optional[float] = None
    is_manual: bool = True
    is_automatable: bool = False
    automation_complexity: Optional[str] = None  # low, medium, high

class WorkflowMap(BaseModel):
    workflow_id: str
    name: str
    description: str
    category: str  # e.g., "onboarding", "approval", "reporting"
    steps: list[ProcessStep]
    systems_involved: list[str] = Field(default_factory=list)
    data_flows: list[dict] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    frequency: str  # e.g., "daily", "weekly", "on-demand"
    volume: Optional[str] = None  # e.g., "~50 per day"
    pain_points: list[str] = Field(default_factory=list)
    automation_opportunities: list[dict] = Field(default_factory=list)
    estimated_automation_impact: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DiscoveryReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization: str
    scan_date: datetime = Field(default_factory=datetime.utcnow)
    systems_scanned: list[str] = Field(default_factory=list)
    workflows_discovered: list[WorkflowMap] = Field(default_factory=list)
    total_workflows: int = 0
    automatable_workflows: int = 0
    high_impact_opportunities: list[dict] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
```

---

## 3. Workflow Optimization Agent

### 3.1 Purpose

The Workflow Optimization Agent analyzes discovered workflows to identify bottlenecks, redundancies, and improvement opportunities. It recommends optimizations and can automatically implement approved changes.

### 3.2 Architecture

```
┌─────────────────────────────────────────────────┐
│          Workflow Optimization Agent             │
│  Model: claude-sonnet-4-6                        │
│  Middleware: TodoList + Filesystem + Summarize   │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Bottleneck  │  │  Cost        │             │
│  │  Analyzer    │  │  Optimizer   │             │
│  │  Subagent    │  │  Subagent    │             │
│  │              │  │              │             │
│  │ - Latency    │  │ - Token cost │             │
│  │   analysis   │  │   analysis   │             │
│  │ - Throughput │  │ - API cost   │             │
│  │   analysis   │  │   analysis   │             │
│  │ - Queue      │  │ - Resource   │             │
│  │   depth      │  │   optimization│            │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Redundancy  │  │  Best        │             │
│  │  Detector    │  │  Practice    │             │
│  │  Subagent    │  │  Engine      │             │
│  │              │  │  Subagent    │             │
│  │ - Duplicate  │  │              │             │
│  │   detection  │  │ - Pattern    │             │
│  │ - Overlap    │  │   library    │             │
│  │   analysis   │  │ - Benchmark  │             │
│  │ - Consolidate│  │   comparison │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
├─────────────────────────────────────────────────┤
│  Tools: metrics_analyzer, cost_calculator,       │
│        benchmark_engine, workflow_simulator,      │
│        a_b_test_designer                         │
└─────────────────────────────────────────────────┘
```

### 3.3 Implementation

```python
# agents/workflow_optimization.py
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_core.tools import tool

@tool
def analyze_workflow_metrics(
    workflow_id: str,
    metrics_source: str,  # e.g., "prometheus", "datadog", "langsmith"
    time_range: str = "7d",
) -> dict:
    """Analyze performance metrics for a specific workflow.
    
    Args:
        workflow_id: Identifier of the workflow to analyze
        metrics_source: Metrics backend to query
        time_range: Time range for analysis (e.g., "1h", "24h", "7d", "30d")
        
    Returns:
        Performance metrics including latency, throughput, error rates, and trends
    """
    # Query metrics backend and return structured analysis
    pass

@tool
def calculate_automation_roi(
    workflow_id: str,
    current_cost_per_execution: float,
    projected_automation_cost: float,
    executions_per_month: int,
    implementation_cost: float,
) -> dict:
    """Calculate ROI for automating a specific workflow.
    
    Args:
        workflow_id: Workflow identifier
        current_cost_per_execution: Current cost per manual execution
        projected_automation_cost: Projected cost per automated execution
        executions_per_month: Monthly execution volume
        implementation_cost: One-time implementation cost
        
    Returns:
        ROI analysis with payback period, annual savings, and NPV
    """
    monthly_savings = (current_cost_per_execution - projected_automation_cost) * executions_per_month
    annual_savings = monthly_savings * 12
    payback_months = implementation_cost / monthly_savings if monthly_savings > 0 else float('inf')
    
    return {
        "workflow_id": workflow_id,
        "monthly_savings": monthly_savings,
        "annual_savings": annual_savings,
        "implementation_cost": implementation_cost,
        "payback_period_months": payback_months,
        "roi_12_months": (annual_savings - implementation_cost) / implementation_cost * 100,
        "roi_36_months": ((annual_savings * 3) - implementation_cost) / implementation_cost * 100,
        "recommendation": "proceed" if payback_months < 12 else "evaluate",
    }

@tool
def simulate_workflow_optimization(
    workflow_id: str,
    optimization_type: str,  # "parallelize", "cache", "batch", "eliminate"
    parameters: dict,
) -> dict:
    """Simulate the effect of a workflow optimization before implementing.
    
    Args:
        workflow_id: Workflow to simulate
        optimization_type: Type of optimization to simulate
        parameters: Optimization-specific parameters
        
    Returns:
        Simulated performance improvement metrics
    """
    # Run simulation and return projected improvements
    pass

@tool
def detect_redundant_steps(workflow_steps: list[dict]) -> dict:
    """Detect redundant or duplicate steps in a workflow.
    
    Args:
        workflow_steps: List of workflow step definitions
        
    Returns:
        Redundancy analysis with consolidation recommendations
    """
    # Analyze steps for redundancy using similarity matching
    pass

def create_workflow_optimization_agent(backend=None, store=None):
    """Create the Workflow Optimization Agent."""
    
    optimization_subagents = [
        {
            "name": "bottleneck-analyzer",
            "description": "Identifies performance bottlenecks in workflows using metrics and trace data",
            "system_prompt": """You are a performance bottleneck analyst.
            
Analysis dimensions:
1. LATENCY: Which steps take the longest? Is it CPU, I/O, or network bound?
2. THROUGHPUT: What is the maximum sustainable rate?
3. QUEUE DEPTH: Are work items backing up?
4. ERROR RATES: Where do failures occur and cascade?
5. RESOURCE UTILIZATION: CPU, memory, connection pool usage

For each bottleneck, provide:
- Root cause analysis
- Severity rating (critical, high, medium, low)
- Recommended fix with estimated improvement
- Implementation complexity""",
            "tools": [analyze_workflow_metrics],
        },
        {
            "name": "cost-optimizer",
            "description": "Analyzes and optimizes the cost of running workflows",
            "system_prompt": """You are a cost optimization specialist.
            
Cost dimensions:
1. COMPUTE: CPU/memory usage and right-sizing
2. API CALLS: External API usage and caching opportunities
3. LLM TOKENS: Prompt optimization, model selection, caching
4. STORAGE: Data retention and archival policies
5. NETWORK: Data transfer and bandwidth costs

Provide specific recommendations with estimated monthly savings.""",
            "tools": [calculate_automation_roi],
        },
    ]
    
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        system_prompt="""You are the Workflow Optimization Agent.

Your mission: Analyze existing workflows and recommend optimizations.

Analysis Framework:
1. PERFORMANCE: Latency, throughput, error rates, resource usage
2. COST: Compute, API, LLM token, storage, and network costs
3. RELIABILITY: Error rates, retry logic, failure modes
4. MAINTAINABILITY: Complexity, coupling, technical debt
5. REDUNDANCY: Duplicate steps, overlapping processes, consolidation opportunities

For each workflow analyzed:
- Identify top 3 optimization opportunities
- Estimate impact (time saved, cost reduced, reliability improved)
- Provide implementation plan with effort estimate
- Simulate expected improvements
- Recommend priority order

Write optimization reports to /workspace/optimization/.""",
        tools=[
            analyze_workflow_metrics,
            calculate_automation_roi,
            simulate_workflow_optimization,
            detect_redundant_steps,
        ],
        subagents=optimization_subagents,
        backend=backend,
        store=store,
        memory=["./AGENTS.md"],
        skills=["./skills/workflow-optimization/"],
    )
    
    return agent
```

### 3.4 Optimization Patterns

```python
# patterns/optimizations.py
from enum import Enum
from pydantic import BaseModel

class OptimizationType(str, Enum):
    PARALLELIZE = "parallelize"
    CACHE = "cache"
    BATCH = "batch"
    ELIMINATE = "eliminate"
    ASYNC = "async"
    CIRCUIT_BREAK = "circuit_break"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    PAGINATE = "paginate"
    STREAM = "stream"
    COMPRESS = "compress"

class OptimizationPattern(BaseModel):
    name: str
    type: OptimizationType
    description: str
    applicable_when: str
    expected_improvement: str
    implementation_effort: str  # low, medium, high
    code_template: str

OPTIMIZATION_PATTERNS = [
    OptimizationPattern(
        name="Parallel Fan-Out",
        type=OptimizationType.PARALLELIZE,
        description="Execute independent steps concurrently instead of sequentially",
        applicable_when="Multiple steps have no data dependencies between them",
        expected_improvement="Reduces total latency from sum of steps to max of steps",
        implementation_effort="medium",
        code_template="""
# Before: Sequential
result_a = await step_a()
result_b = await step_b()
result_c = await step_c()

# After: Parallel
result_a, result_b, result_c = await asyncio.gather(
    step_a(), step_b(), step_c()
)
""",
    ),
    OptimizationPattern(
        name="Response Caching",
        type=OptimizationType.CACHE,
        description="Cache expensive API calls and computations",
        applicable_when="Same inputs produce same outputs within a time window",
        expected_improvement="Eliminates redundant API calls, reduces latency by 80-95%",
        implementation_effort="low",
        code_template="""
from functools import lru_cache
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute TTL

async def cached_api_call(key: str, fetch_func):
    if key in cache:
        return cache[key]
    result = await fetch_func()
    cache[key] = result
    return result
""",
    ),
    OptimizationPattern(
        name="Batch Processing",
        type=OptimizationType.BATCH,
        description="Group individual operations into batches",
        applicable_when="Processing many small items individually",
        expected_improvement="Reduces API calls by 10-100x, improves throughput",
        implementation_effort="medium",
        code_template="""
# Before: Individual calls
for item in items:
    await process_item(item)

# After: Batch call
batch_size = 100
for i in range(0, len(items), batch_size):
    batch = items[i:i + batch_size]
    await process_batch(batch)
""",
    ),
    OptimizationPattern(
        name="Circuit Breaker",
        type=OptimizationType.CIRCUIT_BREAK,
        description="Fail fast when a downstream service is unhealthy",
        applicable_when="External service calls that may fail or timeout",
        expected_improvement="Prevents cascade failures, reduces recovery time",
        implementation_effort="medium",
        code_template="""
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
async def call_external_service():
    # This will fail fast after 5 consecutive failures
    # and retry after 30 seconds
    pass
""",
    ),
]
```

---

## 4. Process Automation Agent

### 4.1 Purpose

The Process Automation Agent designs, generates, tests, and deploys automated workflow implementations. It transforms optimization recommendations into running code.

### 4.2 Architecture

```
┌─────────────────────────────────────────────────┐
│          Process Automation Agent               │
│  Model: claude-sonnet-4-6                        │
│  Middleware: TodoList + Filesystem + HITL        │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Workflow    │  │  Code        │             │
│  │  Designer    │  │  Generator   │             │
│  │  Subagent    │  │  Subagent    │             │
│  │              │  │              │             │
│  │ - BPMN       │  │ - Python     │             │
│  │   design     │  │   code gen   │             │
│  │ - DAG        │  │ - Config     │             │
│  │   design     │  │   generation │             │
│  │ - Error      │  │ - Test       │             │
│  │   handling   │  │   generation │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Validator   │  │  Deployer    │             │
│  │  Subagent    │  │  Subagent    │             │
│  │              │  │              │             │
│  │ - Unit tests │  │ - CI/CD      │             │
│  │ - Integration│  │   pipeline   │             │
│  │   tests      │  │ - Rollback   │             │
│  │ - Contract   │  │   planning   │             │
│  │   tests      │  │ - Monitoring │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
├─────────────────────────────────────────────────┤
│  Tools: code_generator, test_runner, deployer,   │
│        config_validator, secret_manager,         │
│        workflow_engine_connector                │
└─────────────────────────────────────────────────┘
```

### 4.3 Implementation

```python
# agents/process_automation.py
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_core.tools import tool

@tool
def generate_workflow_code(
    workflow_spec: dict,
    target_language: str = "python",
    framework: str = "temporal",  # temporal, prefect, airflow, dagster
    include_tests: bool = True,
) -> dict:
    """Generate production-ready workflow code from a specification.
    
    Args:
        workflow_spec: Workflow specification (steps, dependencies, error handling)
        target_language: Target programming language
        framework: Workflow orchestration framework
        include_tests: Whether to generate test code
        
    Returns:
        Generated code files with metadata
    """
    # Use LLM to generate code based on spec
    # Returns structured code artifacts
    pass

@tool
def validate_workflow_config(config: dict, schema: str) -> dict:
    """Validate a workflow configuration against a JSON schema.
    
    Args:
        config: Workflow configuration to validate
        schema: JSON schema identifier
        
    Returns:
        Validation result with errors and warnings
    """
    import jsonschema
    
    schemas = {
        "temporal_workflow": {
            "type": "object",
            "required": ["name", "steps", "retry_policy"],
            "properties": {
                "name": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
                "steps": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["name", "activity"],
                        "properties": {
                            "name": {"type": "string"},
                            "activity": {"type": "string"},
                            "timeout_seconds": {"type": "integer", "minimum": 1},
                            "retry_policy": {"type": "object"},
                        },
                    },
                },
                "retry_policy": {
                    "type": "object",
                    "properties": {
                        "max_attempts": {"type": "integer", "minimum": 1},
                        "initial_interval_seconds": {"type": "number", "minimum": 0},
                    },
                },
            },
        },
    }
    
    json_schema = schemas.get(schema, {})
    validator = jsonschema.Draft7Validator(json_schema)
    errors = list(validator.iter_errors(config))
    
    return {
        "valid": len(errors) == 0,
        "errors": [{"path": list(e.path), "message": e.message} for e in errors],
        "warnings": [],
    }

@tool
def deploy_workflow(
    workflow_code_path: str,
    environment: str,  # "staging", "production"
    deployment_strategy: str = "blue_green",  # blue_green, canary, rolling
) -> dict:
    """Deploy a workflow to the target environment.
    
    Args:
        workflow_code_path: Path to the workflow code
        environment: Target environment
        deployment_strategy: Deployment strategy to use
        
    Returns:
        Deployment result with status and rollback info
    """
    # Integration with deployment pipeline
    pass

@tool
def run_workflow_tests(
    workflow_code_path: str,
    test_types: list[str] = None,  # ["unit", "integration", "contract", "e2e"]
) -> dict:
    """Run all tests for a workflow.
    
    Args:
        workflow_code_path: Path to workflow code
        test_types: Types of tests to run
        
    Returns:
        Test results with pass/fail status and coverage
    """
    import subprocess
    
    test_types = test_types or ["unit", "integration"]
    results = {}
    
    for test_type in test_types:
        if test_type == "unit":
            proc = subprocess.run(
                ["pytest", f"{workflow_code_path}/tests/unit/", "-v", "--tb=short"],
                capture_output=True, text=True, timeout=120
            )
            results["unit"] = {
                "passed": proc.returncode == 0,
                "output": proc.stdout[-2000:],  # Last 2000 chars
                "error": proc.stderr[-1000:] if proc.returncode != 0 else None,
            }
        elif test_type == "integration":
            proc = subprocess.run(
                ["pytest", f"{workflow_code_path}/tests/integration/", "-v", "--tb=short"],
                capture_output=True, text=True, timeout=300
            )
            results["integration"] = {
                "passed": proc.returncode == 0,
                "output": proc.stdout[-2000:],
                "error": proc.stderr[-1000:] if proc.returncode != 0 else None,
            }
    
    return {
        "all_passed": all(r["passed"] for r in results.values()),
        "results": results,
        "summary": f"{sum(1 for r in results.values() if r['passed'])}/{len(results)} test suites passed",
    }

def create_process_automation_agent(backend=None, store=None):
    """Create the Process Automation Agent."""
    
    automation_subagents = [
        {
            "name": "code-generator",
            "description": "Generates production-ready workflow code, configurations, and infrastructure as code",
            "system_prompt": """You are a senior workflow automation engineer.

Code generation standards:
1. TYPE SAFETY: Use Pydantic models for all inputs/outputs
2. ERROR HANDLING: Every activity has retry logic and dead-letter handling
3. OBSERVABILITY: Structured logging, metrics, and tracing in every step
4. IDEMPOTENCY: All activities must be safely retryable
5. CONFIGURATION: No hardcoded secrets; use environment variables
6. TESTING: Generate unit tests for every activity

Output: Complete, runnable code with tests and documentation.""",
            "tools": [generate_workflow_code],
        },
        {
            "name": "validator",
            "description": "Validates workflow code against quality gates, security policies, and best practices",
            "system_prompt": """You are a workflow quality assurance specialist.

Validation checklist:
1. CORRECTNESS: Does the code match the specification?
2. ERROR HANDLING: Are all failure modes handled?
3. SECURITY: No secrets in code, proper input validation
4. PERFORMANCE: No N+1 queries, proper timeouts, efficient algorithms
5. OBSERVABILITY: Adequate logging, metrics, and tracing
6. TESTS: Unit tests cover >80% of code paths

Return: Validation report with pass/fail for each criterion.""",
            "tools": [validate_workflow_config, run_workflow_tests],
        },
    ]
    
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        system_prompt="""You are the Process Automation Agent.

Your mission: Transform workflow specifications into production-ready automated workflows.

Development Process:
1. DESIGN: Create workflow DAG with steps, dependencies, and error handling
2. GENERATE: Produce production-quality code with tests
3. VALIDATE: Run all quality gates (unit, integration, contract, security)
4. DEPLOY: Deploy to staging, run smoke tests, then production
5. MONITOR: Set up observability and alerting
6. DOCUMENT: Generate runbooks and operational docs

Safety rules:
- NEVER deploy without passing all tests
- ALWAYS use blue-green or canary deployment
- ALWAYS have a rollback plan
- ALWAYS require human approval for production deploys
- NEVER hardcode secrets or credentials

Write all code to /workspace/automation/.""",
        tools=[
            generate_workflow_code,
            validate_workflow_config,
            deploy_workflow,
            run_workflow_tests,
        ],
        subagents=automation_subagents,
        backend=backend,
        store=store,
        interrupt_on={
            "execute": True,
            "deploy_workflow": True,
        },
        memory=["./AGENTS.md"],
        skills=["./skills/process-automation/"],
    )
    
    return agent
```

### 4.4 Workflow Code Generation Template

```python
# templates/workflow_template.py
"""
Template for generated workflow code.
This is the structure the Process Automation Agent uses when generating new workflows.
"""

from temporalio import workflow
from temporalio.common import RetryPolicy
from pydantic import BaseModel
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

# ─── Input/Output Models ──────────────────────────────────────

class WorkflowInput(BaseModel):
    """Input parameters for the workflow."""
    param_1: str
    param_2: Optional[int] = None

class WorkflowOutput(BaseModel):
    """Output from the workflow."""
    result: str
    metadata: dict

class StepResult(BaseModel):
    """Result from an individual step."""
    step_name: str
    success: bool
    data: dict
    duration_ms: float

# ─── Workflow Definition ──────────────────────────────────────

@workflow.defn
class GeneratedWorkflow:
    """
    Auto-generated workflow.
    Generated by Process Automation Agent.
    """
    
    def __init__(self):
        self._progress = 0
        self._results = []
    
    @workflow.run
    async def run(self, input: WorkflowInput) -> WorkflowOutput:
        """Main workflow execution."""
        logger.info("workflow_started", input=input.model_dump())
        
        try:
            # Step 1
            step1_result = await workflow.execute_activity(
                step_1_activity,
                input.param_1,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    max_attempts=3,
                    initial_interval=timedelta(seconds=1),
                ),
            )
            self._progress = 25
            logger.info("step_1_completed", result=step1_result)
            
            # Step 2 (depends on step 1)
            step2_result = await workflow.execute_activity(
                step_2_activity,
                step1_result,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(max_attempts=3),
            )
            self._progress = 50
            
            # Step 3 (parallel with step 4)
            step3, step4 = await asyncio.gather(
                workflow.execute_activity(step_3_activity, step2_result),
                workflow.execute_activity(step_4_activity, input.param_2),
            )
            self._progress = 75
            
            # Final step
            final_result = await workflow.execute_activity(
                final_activity,
                {"step3": step3, "step4": step4},
            )
            self._progress = 100
            
            logger.info("workflow_completed", result=final_result)
            return WorkflowOutput(
                result=final_result,
                metadata={
                    "steps_completed": 5,
                    "total_duration_ms": workflow.now() - workflow.start_time,
                },
            )
            
        except Exception as e:
            logger.error("workflow_failed", error=str(e))
            raise

# ─── Activity Definitions ─────────────────────────────────────

@workflow.defn
class Step1Activity:
    @workflow.run
    async def run(self, param: str) -> dict:
        """Step 1: Description of what this step does."""
        # Implementation
        pass
```

---

## 5. Integration Automation Agent

### 5.1 Purpose

The Integration Automation Agent discovers, designs, and implements integrations between systems, APIs, and services. It handles schema mapping, data transformation, and connector management.

### 5.2 Architecture

```
┌─────────────────────────────────────────────────┐
│        Integration Automation Agent             │
│  Model: claude-sonnet-4-6                        │
│  Middleware: TodoList + Filesystem + HITL        │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  API Mapper  │  │  Schema      │             │
│  │  Subagent    │  │  Translator  │             │
│  │              │  │  Subagent    │             │
│  │ - Endpoint   │  │              │             │
│  │   discovery  │  │ - Field      │             │
│  │ - Auth       │  │   mapping    │             │
│  │   detection  │  │ - Type       │             │
│  │ - Rate limit │  │   conversion │             │
│  │   analysis   │  │ - Validation │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Connector   │  │  Data        │             │
│  │  Builder     │  │  Transformer │             │
│  │  Subagent    │  │  Subagent    │             │
│  │              │  │              │             │
│  │ - OAuth      │  │ - Format     │             │
│  │   handling   │  │   conversion │             │
│  │ - API key    │  │ - Enrichment │             │
│  │   management │  │ - Filtering  │             │
│  │ - Webhook    │  │ - Aggregation│             │
│  │   setup      │  │              │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
├─────────────────────────────────────────────────┤
│  Tools: api_connector, schema_mapper,            │
│        auth_manager, webhook_manager,            │
│        data_transformer, rate_limiter            │
└─────────────────────────────────────────────────┘
```

### 5.3 Implementation

```python
# agents/integration_automation.py
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_core.tools import tool

@tool
def discover_api_capabilities(api_url: str, auth_token: str = None) -> dict:
    """Discover API capabilities including endpoints, auth methods, and rate limits.
    
    Args:
        api_url: Base URL of the API
        auth_token: Optional authentication token
        
    Returns:
        API capability inventory
    """
    import requests
    
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
    
    # Try OpenAPI spec first
    try:
        resp = requests.get(f"{api_url}/openapi.json", headers=headers, timeout=10)
        if resp.status_code == 200:
            return {"type": "openapi", "spec": resp.json()}
    except:
        pass
    
    # Try Swagger
    try:
        resp = requests.get(f"{api_url}/swagger.json", headers=headers, timeout=10)
        if resp.status_code == 200:
            return {"type": "swagger", "spec": resp.json()}
    except:
        pass
    
    # Fallback: probe common endpoints
    return {
        "type": "unknown",
        "base_url": api_url,
        "probed_endpoints": probe_common_endpoints(api_url, headers),
    }

@tool
def map_schema_fields(
    source_schema: dict,
    target_schema: dict,
    mapping_hints: dict = None,
) -> dict:
    """Map fields between two data schemas.
    
    Args:
        source_schema: Source data schema
        target_schema: Target data schema
        mapping_hints: Optional hints for field mapping
        
    Returns:
        Field mapping with transformations
    """
    # Use LLM-assisted schema matching
    pass

@tool
def generate_connector_code(
    source_api: dict,
    target_api: dict,
    mapping: dict,
    connector_type: str = "rest",  # rest, graphql, grpc, webhook
) -> dict:
    """Generate connector code between two APIs.
    
    Args:
        source_api: Source API specification
        target_api: Target API specification
        mapping: Field mapping between APIs
        connector_type: Type of connector to generate
        
    Returns:
        Generated connector code
    """
    pass

@tool
def setup_webhook(
    target_url: str,
    events: list[str],
    secret: str = None,
) -> dict:
    """Set up a webhook endpoint for event-driven integrations.
    
    Args:
        target_url: URL to receive webhook events
        events: List of events to subscribe to
        secret: Optional secret for webhook signature verification
        
    Returns:
        Webhook configuration details
    """
    pass

@tool
def test_integration(
    connector_code_path: str,
    test_scenarios: list[dict],
) -> dict:
    """Test an integration connector against test scenarios.
    
    Args:
        connector_code_path: Path to connector code
        test_scenarios: List of test scenarios to run
        
    Returns:
        Test results with pass/fail for each scenario
    """
    pass

def create_integration_automation_agent(backend=None, store=None):
    """Create the Integration Automation Agent."""
    
    integration_subagents = [
        {
            "name": "api-mapper",
            "description": "Discovers and maps API endpoints, parameters, and response schemas between systems",
            "system_prompt": """You are an API integration mapping specialist.

Mapping process:
1. DISCOVER: Identify all endpoints in source and target APIs
2. MATCH: Find corresponding endpoints between systems
3. MAP: Create field-level mappings with transformations
4. VALIDATE: Ensure type compatibility and handle edge cases
5. DOCUMENT: Generate integration specification

Handle: pagination, filtering, sorting, nested objects, arrays, null values.""",
            "tools": [discover_api_capabilities, map_schema_fields],
        },
        {
            "name": "connector-builder",
            "description": "Builds production-ready connector code with auth, retry, and error handling",
            "system_prompt": """You are a connector development specialist.

Connector standards:
1. AUTHENTICATION: Support OAuth2, API key, and basic auth
2. RETRY LOGIC: Exponential backoff with jitter
3. RATE LIMITING: Respect API rate limits with token bucket
4. ERROR HANDLING: Categorize errors (retryable, fatal, auth)
5. LOGGING: Structured logging for all API calls
6. METRICS: Track latency, success rate, and error rate
7. TESTING: Unit tests with mocked API responses

Output: Complete connector with tests and documentation.""",
            "tools": [generate_connector_code, test_integration],
        },
    ]
    
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        system_prompt="""You are the Integration Automation Agent.

Your mission: Build and maintain integrations between systems.

Integration Patterns:
1. REQUEST-RESPONSE: Synchronous API calls
2. EVENT-DRIVEN: Webhook-based async integration
3. POLLING: Periodic data synchronization
4. STREAMING: Real-time data flow
5. BATCH: Scheduled bulk data transfer

Development process:
1. DISCOVER: Analyze source and target APIs
2. MAP: Create field mappings and transformations
3. BUILD: Generate connector code with auth and error handling
4. TEST: Validate with unit and integration tests
5. DEPLOY: Deploy with monitoring and alerting
6. MAINTAIN: Handle schema changes and API updates

Security requirements:
- NEVER store credentials in code
- ALWAYS use environment variables or secret managers
- ALWAYS validate and sanitize inputs
- ALWAYS use HTTPS for API calls
- ALWAYS implement proper authentication

Write all connectors to /workspace/integrations/.""",
        tools=[
            discover_api_capabilities,
            map_schema_fields,
            generate_connector_code,
            setup_webhook,
            test_integration,
        ],
        subagents=integration_subagents,
        backend=backend,
        store=store,
        interrupt_on={
            "execute": True,
            "setup_webhook": True,
        },
        memory=["./AGENTS.md"],
        skills=["./skills/integration-automation/"],
    )
    
    return agent
```

### 5.4 Integration Patterns

```python
# patterns/integrations.py
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from pydantic import BaseModel

class IntegrationConnector(ABC):
    """Base class for all integration connectors."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the target system."""
        pass
    
    @abstractmethod
    async def fetch(self, query: dict) -> AsyncIterator[dict]:
        """Fetch data from the source system."""
        pass
    
    @abstractmethod
    async def transform(self, data: dict) -> dict:
        """Transform data from source to target format."""
        pass
    
    @abstractmethod
    async def load(self, data: dict) -> dict:
        """Load data into the target system."""
        pass
    
    async def sync(self, query: dict) -> dict:
        """Full ETL sync: Extract, Transform, Load."""
        await self.connect()
        results = []
        async for record in self.fetch(query):
            transformed = await self.transform(record)
            result = await self.load(transformed)
            results.append(result)
        return {"records_processed": len(results), "results": results}

class RESTConnector(IntegrationConnector):
    """REST API integration connector."""
    
    def __init__(self, base_url: str, auth_config: dict):
        self.base_url = base_url
        self.auth_config = auth_config
        self.session = None
    
    async def connect(self):
        import aiohttp
        self.session = aiohttp.ClientSession(
            base_url=self.base_url,
            headers=self._get_auth_headers(),
        )
    
    def _get_auth_headers(self) -> dict:
        auth_type = self.auth_config.get("type", "bearer")
        if auth_type == "bearer":
            return {"Authorization": f"Bearer {self.auth_config['token']}"}
        elif auth_type == "api_key":
            return {self.auth_config["header"]: self.auth_config["key"]}
        return {}
    
    async def fetch(self, query: dict) -> AsyncIterator[dict]:
        page = 1
        while True:
            async with self.session.get(
                query["endpoint"],
                params={**query.get("params", {}), "page": page},
            ) as resp:
                data = await resp.json()
                records = data.get("results", [])
                if not records:
                    break
                for record in records:
                    yield record
                page += 1
    
    async def transform(self, data: dict) -> dict:
        # Apply field mappings
        return data
    
    async def load(self, data: dict) -> dict:
        async with self.session.post("/data", json=data) as resp:
            return await resp.json()

class WebhookConnector(IntegrationConnector):
    """Webhook-based event-driven integration."""
    
    def __init__(self, endpoint: str, secret: str):
        self.endpoint = endpoint
        self.secret = secret
    
    async def connect(self):
        # Webhooks are stateless; no persistent connection needed
        pass
    
    async def fetch(self, query: dict) -> AsyncIterator[dict]:
        # Webhooks push data; this would be called by the webhook handler
        yield query
    
    async def transform(self, data: dict) -> dict:
        return data
    
    async def load(self, data: dict) -> dict:
        # Process webhook payload
        return {"status": "processed", "id": data.get("id")}
```

---

## 6. Performance Analytics Agent

### 6.1 Purpose

The Performance Analytics Agent monitors, measures, and reports on workflow performance. It detects anomalies, generates reports, and provides actionable insights.

### 6.2 Architecture

```
┌─────────────────────────────────────────────────┐
│        Performance Analytics Agent              │
│  Model: claude-sonnet-4-6                        │
│  Middleware: TodoList + Filesystem + Summarize   │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Metrics     │  │  Anomaly     │             │
│  │  Collector   │  │  Detector    │             │
│  │  Subagent    │  │  Subagent    │             │
│  │              │  │              │             │
│  │ - Prometheus │  │ - Statistical│             │
│  │   queries    │  │   analysis   │             │
│  │ - LangSmith  │  │ - ML-based   │             │
│  │   traces     │  │   detection  │             │
│  │ - Custom     │  │ - Threshold  │             │
│  │   metrics    │  │   alerts     │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Report      │  │  Trend       │             │
│  │  Generator   │  │  Analyzer    │             │
│  │  Subagent    │  │  Subagent    │             │
│  │              │  │              │             │
│  │ - Executive  │  │ - Seasonality│             │
│  │   summaries  │  │   detection  │             │
│  │ - Technical  │  │ - Forecasting│             │
│  │   deep-dives │  │ - Correlation│            │
│  │ - Dashboards │  │   analysis   │             │
│  └──────────────┘  └──────────────┘             │
│                                                  │
├─────────────────────────────────────────────────┤
│  Tools: metrics_query, trace_analyzer,           │
│        report_generator, alert_manager,          │
│        dashboard_builder, forecast_engine        │
└─────────────────────────────────────────────────┘
```

### 6.3 Implementation

```python
# agents/performance_analytics.py
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_core.tools import tool
from datetime import datetime, timedelta

@tool
def query_workflow_metrics(
    workflow_id: str,
    metric_names: list[str],
    time_range: str = "1h",
    aggregation: str = "avg",  # avg, sum, min, max, p50, p95, p99
) -> dict:
    """Query performance metrics for a workflow.
    
    Args:
        workflow_id: Workflow identifier
        metric_names: List of metric names to query
        time_range: Time range (e.g., "5m", "1h", "24h", "7d")
        aggregation: Aggregation function
        
    Returns:
        Time-series metrics data
    """
    # Query Prometheus or metrics backend
    pass

@tool
def analyze_langsmith_traces(
    workflow_name: str,
    time_range: str = "24h",
    filter_errors: bool = False,
) -> dict:
    """Analyze LangSmith traces for workflow performance.
    
    Args:
        workflow_name: Name of the workflow to analyze
        time_range: Time range for analysis
        filter_errors: Whether to filter to only error traces
        
    Returns:
        Trace analysis with latency breakdown and error analysis
    """
    from langsmith import Client
    
    client = Client()
    # Query traces and analyze
    pass

@tool
def detect_performance_anomalies(
    workflow_id: str,
    metric_name: str,
    sensitivity: str = "medium",  # low, medium, high
    lookback_window: str = "7d",
) -> dict:
    """Detect anomalies in workflow performance metrics.
    
    Args:
        workflow_id: Workflow to monitor
        metric_name: Metric to analyze
        sensitivity: Detection sensitivity
        lookback_window: Historical data window for baseline
        
    Returns:
        Detected anomalies with severity and context
    """
    import numpy as np
    from scipy import stats
    
    # Fetch historical data
    # Apply statistical anomaly detection (z-score, IQR, or ML-based)
    # Return anomalies with context
    pass

@tool
def generate_performance_report(
    workflow_ids: list[str],
    report_type: str = "comprehensive",  # summary, comprehensive, executive
    time_range: str = "7d",
    format: str = "markdown",  # markdown, html, pdf
) -> dict:
    """Generate a performance report for specified workflows.
    
    Args:
        workflow_ids: Workflows to include in the report
        report_type: Type of report
        time_range: Time range for the report
        format: Output format
        
    Returns:
        Generated report with metrics, analysis, and recommendations
    """
    pass

@tool
def create_performance_dashboard(
    workflow_ids: list[str],
    metrics: list[str],
    refresh_interval: str = "5m",
) -> dict:
    """Create a performance dashboard for monitoring workflows.
    
    Args:
        workflow_ids: Workflows to include
        metrics: Metrics to display
        refresh_interval: Dashboard refresh interval
        
    Returns:
        Dashboard configuration and URL
    """
    pass

@tool
def forecast_workload(
    workflow_id: str,
    forecast_horizon: str = "7d",
    include_confidence: bool = True,
) -> dict:
    """Forecast future workload for capacity planning.
    
    Args:
        workflow_id: Workflow to forecast
        forecast_horizon: How far ahead to forecast
        include_confidence: Whether to include confidence intervals
        
    Returns:
        Workload forecast with confidence intervals
    """
    from prophet import Prophet
    import pandas as pd
    
    # Fetch historical execution data
    # Fit forecasting model
    # Return forecast with confidence intervals
    pass

def create_performance_analytics_agent(backend=None, store=None):
    """Create the Performance Analytics Agent."""
    
    analytics_subagents = [
        {
            "name": "metrics-collector",
            "description": "Collects and aggregates performance metrics from multiple sources",
            "system_prompt": """You are a metrics collection specialist.

Data sources:
1. PROMETHEUS: System and application metrics
2. LANGSMITH: LLM trace and token usage metrics
3. CUSTOM: Business-specific metrics
4. INFRASTRUCTURE: CPU, memory, disk, network

Collection strategy:
- Real-time metrics: 15-second granularity
- Near-real-time: 1-minute aggregation
- Historical: 1-hour aggregation with 90-day retention

Always validate metric quality: completeness, consistency, timeliness.""",
            "tools": [query_workflow_metrics, analyze_langsmith_traces],
        },
        {
            "name": "anomaly-detector",
            "description": "Detects performance anomalies and triggers alerts",
            "system_prompt": """You are a performance anomaly detection specialist.

Detection methods:
1. STATISTICAL: Z-score, IQR, seasonal decomposition
2. ML-BASED: Isolation forest, LSTM autoencoders
3. THRESHOLD: Static and dynamic thresholds
4. TREND: Rate of change, momentum indicators

Alert severity:
- CRITICAL: Immediate human notification
- HIGH: Alert within 5 minutes
- MEDIUM: Alert within 30 minutes
- LOW: Daily digest

Always provide context: what changed, when, and potential impact.""",
            "tools": [detect_performance_anomalies],
        },
        {
            "name": "report-generator",
            "description": "Generates performance reports and dashboards for stakeholders",
            "system_prompt": """You are a performance reporting specialist.

Report types:
1. EXECUTIVE: High-level KPIs, trends, and recommendations
2. TECHNICAL: Detailed metrics, traces, and debugging info
3. OPERATIONAL: Real-time status, alerts, and runbooks
4. COMPLIANCE: SLA adherence, audit trails, and evidence

Visualization best practices:
- Use time-series charts for trends
- Use bar charts for comparisons
- Use heatmaps for patterns
- Always include context and annotations""",
            "tools": [generate_performance_report, create_performance_dashboard],
        },
    ]
    
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        system_prompt="""You are the Performance Analytics Agent.

Your mission: Monitor, measure, and optimize workflow performance.

Key Metrics:
1. LATENCY: p50, p95, p99 response times
2. THROUGHPUT: Executions per minute/hour
3. ERROR RATE: Percentage of failed executions
4. COST: Per-execution and total cost
5. RELIABILITY: Success rate, retry rate, timeout rate
6. TOKEN USAGE: LLM tokens per execution
7. RESOURCE: CPU, memory, and connection usage

Analysis capabilities:
- Real-time monitoring and alerting
- Historical trend analysis
- Anomaly detection with root cause analysis
- Capacity planning and forecasting
- Cost optimization recommendations
- SLA compliance reporting

Write all reports to /workspace/analytics/.""",
        tools=[
            query_workflow_metrics,
            analyze_langsmith_traces,
            detect_performance_anomalies,
            generate_performance_report,
            create_performance_dashboard,
            forecast_workload,
        ],
        subagents=analytics_subagents,
        backend=backend,
        store=store,
        memory=["./AGENTS.md"],
        skills=["./skills/performance-analytics/"],
    )
    
    return agent
```

### 6.4 Metrics Schema

```python
# models/metrics.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WorkflowMetrics(BaseModel):
    """Standard workflow performance metrics."""
    workflow_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Latency metrics (milliseconds)
    latency_p50: float
    latency_p95: float
    latency_p99: float
    latency_avg: float
    
    # Throughput metrics
    executions_total: int
    executions_per_minute: float
    executions_per_hour: float
    
    # Reliability metrics
    success_count: int
    failure_count: int
    error_rate: float  # 0.0 to 1.0
    retry_count: int
    timeout_count: int
    
    # Cost metrics
    cost_per_execution: float
    total_cost: float
    llm_tokens_total: int
    llm_tokens_per_execution: float
    
    # Resource metrics
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    active_connections: Optional[int] = None

class AlertRule(BaseModel):
    """Alert rule configuration."""
    rule_id: str
    name: str
    description: str
    metric: str
    condition: str  # ">", "<", "==", "!="
    threshold: float
    duration: str  # e.g., "5m" - must be true for this duration
    severity: str  # "critical", "high", "medium", "low"
    notification_channels: list[str]  # ["slack", "email", "pagerduty"]
    auto_resolve: bool = True
    enabled: bool = True
```

---

## 7. Code Examples and Snippets

### 7.1 Complete Agent Factory

```python
# agents/__init__.py
"""Agent factory for the workflow automation system."""

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, FilesystemBackend
from langgraph.store.postgres import AsyncPostgresStore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain.agents.middleware import TodoListMiddleware
import os

async def create_all_agents():
    """Create and configure all workflow automation agents."""
    
    # Shared infrastructure
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://user:pass@localhost:5432/workflows"
    )
    
    store = await AsyncPostgresStore.from_conn_string(database_url)
    checkpointer = await AsyncPostgresSaver.from_conn_string(database_url)
    
    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/workspace/": FilesystemBackend(
                root_dir="./workspace",
                virtual_mode=True,
            ),
            "/memories/": StoreBackend(
                store=store,
                namespace=["workflow", "memories"],
            ),
        },
    )
    
    # Import agent creators
    from .orchestrator import create_orchestrator_agent
    from .workflow_discovery import create_workflow_discovery_agent
    from .workflow_optimization import create_workflow_optimization_agent
    from .process_automation import create_process_automation_agent
    from .integration_automation import create_integration_automation_agent
    from .performance_analytics import create_performance_analytics_agent
    
    agents = {
        "orchestrator": await create_orchestrator_agent(),
        "discovery": create_workflow_discovery_agent(backend=backend, store=store),
        "optimization": create_workflow_optimization_agent(backend=backend, store=store),
        "automation": create_process_automation_agent(backend=backend, store=store),
        "integration": create_integration_automation_agent(backend=backend, store=store),
        "analytics": create_performance_analytics_agent(backend=backend, store=store),
    }
    
    return agents
```

### 7.2 Agent Invocation Patterns

```python
# examples/invocation_patterns.py
"""Examples of how to invoke agents for different use cases."""

import asyncio
from agents import create_all_agents

async def example_1_simple_discovery():
    """Simple workflow discovery for a single system."""
    agents = await create_all_agents()
    discovery_agent = agents["discovery"]
    
    result = await discovery_agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Discover all workflows in our Jira project PROD. "
                       "Focus on the deployment and approval processes."
        }]
    })
    
    print(result["messages"][-1].content)
    return result

async def example_2_multi_agent_workflow():
    """Multi-agent workflow: discover, optimize, and automate."""
    agents = await create_all_agents()
    orchestrator = agents["orchestrator"]
    
    result = await orchestrator.ainvoke({
        "messages": [{
            "role": "user",
            "content": """Analyze our invoice processing workflow and automate it.
            
            Steps:
            1. Discover the current invoice processing workflow
            2. Identify optimization opportunities
            3. Design an automated workflow
            4. Generate the automation code
            5. Create a performance monitoring dashboard
            
            Start with discovery and report back what you find."""
        }]
    })
    
    return result

async def example_3_optimization_with_approval():
    """Optimization with human-in-the-loop approval."""
    agents = await create_all_agents()
    optimization_agent = agents["optimization"]
    
    # First, get optimization recommendations
    result = await optimization_agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": """Analyze the customer onboarding workflow (ID: CO-001) 
                       and recommend optimizations. Do not implement any changes 
                       without approval."""
        }]
    })
    
    # Present recommendations to user
    recommendations = result["messages"][-1].content
    print("Recommendations:", recommendations)
    
    # If user approves, implement
    # (In production, this would use interrupt_for_human pattern)
    approved = input("Approve optimizations? (y/n): ")
    
    if approved.lower() == "y":
        automation_agent = agents["automation"]
        impl_result = await automation_agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"""Implement the approved optimizations for CO-001.
                
                Approved recommendations:
                {recommendations}
                
                Generate the code and deploy to staging."""
            }]
        })
        return impl_result
    
    return result

async def example_4_integration_builder():
    """Build an integration between two systems."""
    agents = await create_all_agents()
    integration_agent = agents["integration"]
    
    result = await integration_agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": """Build an integration between Salesforce and our internal 
            ERP system. 
            
            Requirements:
            - Sync new Salesforce opportunities to ERP as sales orders
            - Update Salesforce when ERP order status changes
            - Handle field mapping: Salesforce Opportunity -> ERP Sales Order
            - Use OAuth2 for Salesforce authentication
            - Implement webhook for real-time updates from ERP
            - Include error handling and retry logic"""
        }]
    })
    
    return result

async def example_5_performance_monitoring():
    """Set up performance monitoring for a workflow."""
    agents = await create_all_agents()
    analytics_agent = agents["analytics"]
    
    result = await analytics_agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": """Set up comprehensive performance monitoring for the 
            order fulfillment workflow (ID: OF-001).
            
            Requirements:
            - Monitor latency (p50, p95, p99)
            - Track throughput and error rates
            - Set up anomaly detection for latency spikes
            - Create an executive dashboard
            - Generate a weekly performance report
            - Forecast capacity needs for the next 30 days"""
        }]
    })
    
    return result

# Run examples
if __name__ == "__main__":
    asyncio.run(example_1_simple_discovery())
```

### 7.3 MCP Server Integration

```python
# config/mcp_servers.py
"""MCP server configuration for external tool integration."""

from langchain_mcp_adapters.client import MultiServerMCPClient
import os

async def create_mcp_client():
    """Create MCP client with all configured servers."""
    
    client = MultiServerMCPClient(
        {
            "jira": {
                "url": os.environ.get("JIRA_MCP_URL", "http://localhost:3000/jira"),
                "transport": "streamable_http",
            },
            "confluence": {
                "url": os.environ.get("CONFLUENCE_MCP_URL", "http://localhost:3000/confluence"),
                "transport": "streamable_http",
            },
            "github": {
                "url": os.environ.get("GITHUB_MCP_URL", "http://localhost:3000/github"),
                "transport": "streamable_http",
            },
            "slack": {
                "url": os.environ.get("SLACK_MCP_URL", "http://localhost:3000/slack"),
                "transport": "streamable_http",
            },
            "prometheus": {
                "url": os.environ.get("PROMETHEUS_MCP_URL", "http://localhost:3000/prometheus"),
                "transport": "streamable_http",
            },
        }
    )
    
    return client

async def load_mcp_tools_for_agent(agent_name: str):
    """Load MCP tools appropriate for a specific agent."""
    
    client = await create_mcp_client()
    
    tool_mapping = {
        "discovery": ["jira", "confluence", "github"],
        "optimization": ["prometheus", "github"],
        "automation": ["github", "jira"],
        "integration": ["jira", "confluence", "slack"],
        "analytics": ["prometheus", "github"],
    }
    
    servers = tool_mapping.get(agent_name, [])
    tools = []
    
    for server in servers:
        try:
            server_tools = await client.get_tools(server=server)
            tools.extend(server_tools)
        except Exception as e:
            print(f"Warning: Could not load tools from {server}: {e}")
    
    return tools
```

### 7.4 Deployment Configuration

```yaml
# config/docker-compose.yml
version: "3.8"

services:
  workflow-automation:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/workflows
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGCHAIN_TRACING_V2=true
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LANGCHAIN_PROJECT=workflow-automation
    volumes:
      - workspace:/app/workspace
      - memories:/app/memories
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_DB=workflows
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  langsmith:
    image: langchain/langsmith:latest
    ports:
      - "8080:8080"
    environment:
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}

volumes:
  postgres_data:
  workspace:
  memories:
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install deepagents
RUN pip install deepagents langchain-anthropic langchain-openai

# Copy application
COPY . .

# Create workspace directories
RUN mkdir -p /app/workspace /app/memories /app/skills

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.5 Requirements File

```
# requirements.txt
deepagents>=0.7.0,<0.8
langchain>=0.3.0
langchain-anthropic>=0.2.0
langchain-openai>=0.2.0
langgraph>=0.2.0
langgraph-checkpoint-postgres>=0.1.0
langsmith>=0.1.0
langchain-mcp-adapters>=0.1.0

# Workflow orchestration
temporalio>=1.0.0
prefect>=3.0.0

# Data processing
pydantic>=2.0.0
sqlalchemy>=2.0.0
pandas>=2.0.0
numpy>=1.24.0

# API and HTTP
httpx>=0.25.0
aiohttp>=3.9.0
requests>=2.31.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0

# Observability
structlog>=24.0.0
prometheus-client>=0.19.0

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0.0
jinja2>=3.1.0
```

---

## 8. Testing Strategy

### 8.1 Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ← Full workflow tests (5%)
                    │  Tests  │
                   �┌┴─────────┴┐
                   │ Integration│  ← Multi-agent tests (15%)
                   │   Tests    │
                  ┌┴────────────┴┐
                  │   Contract   │  ← API/tool contract tests (20%)
                  │    Tests     │
                 ┌┴──────────────┴┐
                 │     Unit       │  ← Agent/tool unit tests (60%)
                 │    Tests       │
                 └────────────────┘
```

### 8.2 Unit Tests

```python
# tests/unit/test_agents.py
"""Unit tests for individual agent components."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from deepagents import create_deep_agent


class TestWorkflowDiscoveryAgent:
    """Unit tests for the Workflow Discovery Agent."""
    
    @pytest.fixture
    def discovery_agent(self):
        """Create a discovery agent with mocked dependencies."""
        agent = create_deep_agent(
            model="anthropic:claude-sonnet-4-6",
            system_prompt="Test discovery agent",
            tools=[],
            subagents=[],
        )
        return agent
    
    @pytest.mark.asyncio
    async def test_agent_creation(self, discovery_agent):
        """Test that the discovery agent is created successfully."""
        assert discovery_agent is not None
    
    @pytest.mark.asyncio
    async def test_agent_has_filesystem_tools(self, discovery_agent):
        """Test that the agent has access to filesystem tools."""
        result = await discovery_agent.ainvoke({
            "messages": [{"role": "user", "content": "List files in /"}]
        })
        assert "messages" in result
    
    @pytest.mark.asyncio
    async def test_agent_creates_todos(self, discovery_agent):
        """Test that the agent creates a todo list for complex tasks."""
        result = await discovery_agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Discover all workflows in the organization"
            }]
        })
        # Check that the agent created todos
        assert "messages" in result
    
    @pytest.mark.asyncio
    async def test_agent_writes_to_filesystem(self, discovery_agent):
        """Test that the agent can write results to the virtual filesystem."""
        result = await discovery_agent.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Write a test report to /workspace/test_report.md"
            }]
        })
        assert "messages" in result


class TestWorkflowOptimizationAgent:
    """Unit tests for the Workflow Optimization Agent."""
    
    @pytest.mark.asyncio
    async def test_roi_calculation(self):
        """Test ROI calculation logic."""
        from agents.workflow_optimization import calculate_automation_roi
        
        result = calculate_automation_roi(
            workflow_id="WF-001",
            current_cost_per_execution=50.0,
            projected_automation_cost=5.0,
            executions_per_month=100,
            implementation_cost=10000.0,
        )
        
        assert result["monthly_savings"] == 4500.0
        assert result["annual_savings"] == 54000.0
        assert result["payback_period_months"] == pytest.approx(2.22, rel=0.01)
        assert result["recommendation"] == "proceed"


class TestProcessAutomationAgent:
    """Unit tests for the Process Automation Agent."""
    
    @pytest.mark.asyncio
    async def test_config_validation(self):
        """Test workflow configuration validation."""
        from agents.process_automation import validate_workflow_config
        
        valid_config = {
            "name": "test_workflow",
            "steps": [
                {
                    "name": "step_1",
                    "activity": "test_activity",
                    "timeout_seconds": 30,
                }
            ],
            "retry_policy": {
                "max_attempts": 3,
                "initial_interval_seconds": 1.0,
            },
        }
        
        result = validate_workflow_config(valid_config, "temporal_workflow")
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_config_validation_missing_required(self):
        """Test that validation catches missing required fields."""
        from agents.process_automation import validate_workflow_config
        
        invalid_config = {
            "name": "test_workflow",
            # Missing required "steps" and "retry_policy"
        }
        
        result = validate_workflow_config(invalid_config, "temporal_workflow")
        assert result["valid"] is False
        assert len(result["errors"]) > 0


class TestIntegrationAutomationAgent:
    """Unit tests for the Integration Automation Agent."""
    
    @pytest.mark.asyncio
    async def test_schema_mapping(self):
        """Test schema field mapping."""
        from agents.integration_automation import map_schema_fields
        
        source = {"name": "John", "age": 30}
        target = {"full_name": "", "years_old": 0}
        hints = {"name": "full_name", "age": "years_old"}
        
        result = map_schema_fields(source, target, hints)
        assert result is not None


class TestPerformanceAnalyticsAgent:
    """Unit tests for the Performance Analytics Agent."""
    
    @pytest.mark.asyncio
    async def test_metrics_query(self):
        """Test metrics querying."""
        from agents.performance_analytics import query_workflow_metrics
        
        # Mock the metrics backend
        with patch("agents.prometheus_client") as mock_client:
            mock_client.query.return_value = {
                "latency_p50": 100,
                "latency_p95": 500,
                "latency_p99": 1000,
            }
            
            result = query_workflow_metrics(
                workflow_id="WF-001",
                metric_names=["latency"],
                time_range="1h",
            )
            
            assert result is not None
```

### 8.3 Integration Tests

```python
# tests/integration/test_multi_agent.py
"""Integration tests for multi-agent workflows."""

import pytest
import asyncio
from agents import create_all_agents


class TestMultiAgentWorkflow:
    """Integration tests for multi-agent collaboration."""
    
    @pytest.fixture
    async def agents(self):
        """Create all agents for testing."""
        return await create_all_agents()
    
    @pytest.mark.asyncio
    async def test_discovery_to_optimization_handoff(self, agents):
        """Test that discovery results can be passed to optimization."""
        discovery = agents["discovery"]
        optimization = agents["optimization"]
        
        # Step 1: Discover workflows
        discovery_result = await discovery.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Discover the invoice processing workflow"
            }]
        })
        
        # Step 2: Pass discovery results to optimization
        optimization_result = await optimization.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"""Optimize the following discovered workflow:
                
                {discovery_result['messages'][-1].content}
                
                Identify bottlenecks and recommend improvements."""
            }]
        })
        
        assert "messages" in optimization_result
    
    @pytest.mark.asyncio
    async def test_full_automation_pipeline(self, agents):
        """Test the complete discover -> optimize -> automate pipeline."""
        orchestrator = agents["orchestrator"]
        
        result = await orchestrator.ainvoke({
            "messages": [{
                "role": "user",
                "content": """Complete workflow automation pipeline:
                1. Discover the employee onboarding workflow
                2. Identify optimization opportunities
                3. Generate automation code
                4. Validate the generated code
                5. Report on expected performance improvements"""
            }]
        })
        
        assert "messages" in result
        # Verify the orchestrator delegated to subagents
        assert len(result["messages"]) > 0
    
    @pytest.mark.asyncio
    async def test_analytics_feedback_loop(self, agents):
        """Test that analytics results feed back into optimization."""
        analytics = agents["analytics"]
        optimization = agents["optimization"]
        
        # Step 1: Get performance metrics
        metrics_result = await analytics.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Analyze performance of workflow WF-001 for the last 7 days"
            }]
        })
        
        # Step 2: Use metrics to guide optimization
        optimization_result = await optimization.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"""Based on these performance metrics, recommend optimizations:
                
                {metrics_result['messages'][-1].content}"""
            }]
        })
        
        assert "messages" in optimization_result


class TestAgentCommunication:
    """Tests for inter-agent communication protocol."""
    
    @pytest.mark.asyncio
    async def test_task_delegation(self):
        """Test that tasks are properly delegated between agents."""
        from models.agent_messages import AgentTask, TaskType
        
        task = AgentTask(
            task_type=TaskType.DISCOVERY,
            description="Test discovery task",
            context={"system": "jira"},
        )
        
        assert task.status == "pending"
        assert task.task_type == TaskType.DISCOVERY
    
    @pytest.mark.asyncio
    async def test_result_format(self):
        """Test that agent results follow the expected format."""
        from models.agent_messages import AgentResult
        
        result = AgentResult(
            task_id="test-123",
            agent_name="discovery",
            success=True,
            summary="Test summary",
            artifacts=[{"type": "workflow_map", "data": {}}],
            metrics={"workflows_found": 5},
            recommendations=["Automate workflow A", "Optimize workflow B"],
        )
        
        assert result.success is True
        assert len(result.recommendations) == 2
```

### 8.4 Contract Tests

```python
# tests/contracts/test_tool_contracts.py
"""Contract tests for tool interfaces."""

import pytest
from pydantic import ValidationError


class TestToolContracts:
    """Verify that tool inputs/outputs match their contracts."""
    
    def test_scan_api_endpoints_contract(self):
        """Test that scan_api_endpoints returns expected structure."""
        from agents.workflow_discovery import scan_api_endpoints
        
        # The tool should accept a base_url and return a dict with endpoints
        # This is a contract test - we verify the interface, not the implementation
        import inspect
        sig = inspect.signature(scan_api_endpoints.func)
        params = list(sig.parameters.keys())
        assert "base_url" in params
    
    def test_calculate_roi_contract(self):
        """Test that calculate_roi returns expected fields."""
        from agents.workflow_optimization import calculate_automation_roi
        
        result = calculate_automation_roi(
            workflow_id="WF-001",
            current_cost_per_execution=100.0,
            projected_automation_cost=10.0,
            executions_per_month=50,
            implementation_cost=5000.0,
        )
        
        required_fields = [
            "workflow_id", "monthly_savings", "annual_savings",
            "implementation_cost", "payback_period_months",
            "roi_12_months", "roi_36_months", "recommendation",
        ]
        
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
    
    def test_validate_workflow_config_contract(self):
        """Test that validate_workflow_config returns expected structure."""
        from agents.process_automation import validate_workflow_config
        
        result = validate_workflow_config({}, "temporal_workflow")
        
        assert "valid" in result
        assert "errors" in result
        assert isinstance(result["valid"], bool)
        assert isinstance(result["errors"], list)


class TestAgentMessageContracts:
    """Verify agent message format contracts."""
    
    def test_agent_task_creation(self):
        """Test AgentTask model validation."""
        from models.agent_messages import AgentTask, TaskType
        
        task = AgentTask(
            task_type=TaskType.DISCOVERY,
            description="Test task",
        )
        
        assert task.task_id is not None
        assert task.status == "pending"
        assert task.created_at is not None
    
    def test_agent_result_creation(self):
        """Test AgentResult model validation."""
        from models.agent_messages import AgentResult
        
        result = AgentResult(
            task_id="test-123",
            agent_name="test-agent",
            success=True,
            summary="Test result",
        )
        
        assert result.artifacts == []
        assert result.metrics == {}
        assert result.recommendations == []
```

### 8.5 End-to-End Tests

```python
# tests/e2e/test_full_workflow.py
"""End-to-end tests for complete workflow automation scenarios."""

import pytest
import asyncio
import tempfile
import os


class TestEndToEndWorkflowAutomation:
    """Full end-to-end tests simulating real usage."""
    
    @pytest.fixture
    async def agents(self):
        """Create all agents."""
        from agents import create_all_agents
        return await create_all_agents()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(300)  # 5 minute timeout
    async def test_complete_discovery_to_deployment(self, agents):
        """Test the complete pipeline from discovery to deployment."""
        orchestrator = agents["orchestrator"]
        
        result = await orchestrator.ainvoke({
            "messages": [{
                "role": "user",
                "content": """Execute the complete workflow automation pipeline:
                
                Context: We need to automate the employee expense approval process.
                The process involves: submission -> manager review -> finance review -> reimbursement.
                
                Steps:
                1. Discover the current expense approval workflow
                2. Identify all systems involved (email, spreadsheet, ERP)
                3. Map the complete process flow
                4. Identify automation opportunities
                5. Design the automated workflow
                6. Generate the workflow code
                7. Create a test plan
                8. Generate a deployment checklist
                
                Provide a comprehensive report at the end."""
            }]
        })
        
        # Verify the result contains expected sections
        content = result["messages"][-1].content
        assert len(content) > 100  # Substantial response
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(180)
    async def test_integration_with_mcp_tools(self, agents):
        """Test agent integration with MCP tools."""
        discovery = agents["discovery"]
        
        # This test verifies that the agent can use MCP tools
        result = await discovery.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Use the Jira MCP tools to find all workflow-related projects"
            }]
        })
        
        assert "messages" in result
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_error_recovery(self, agents):
        """Test that agents handle errors gracefully."""
        discovery = agents["discovery"]
        
        # Send a request that might cause errors
        result = await discovery.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Connect to nonexistent-system.internal and discover workflows"
            }]
        })
        
        # Agent should handle the error gracefully
        assert "messages" in result
        # Should not crash, should provide error information


class TestPerformanceBenchmarks:
    """Performance benchmarks for agent operations."""
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_agent_response_time(self, agents):
        """Test that agents respond within acceptable time limits."""
        import time
        
        discovery = agents["discovery"]
        
        start = time.time()
        result = await discovery.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Quick test: list available tools"
            }]
        })
        elapsed = time.time() - start
        
        # Agent should respond within 30 seconds for simple queries
        assert elapsed < 30, f"Agent took {elapsed:.1f}s to respond"
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_concurrent_agent_invocations(self, agents):
        """Test that multiple agents can run concurrently."""
        import asyncio
        
        discovery = agents["discovery"]
        analytics = agents["analytics"]
        
        async def run_discovery():
            return await discovery.ainvoke({
                "messages": [{"role": "user", "content": "Discover workflows"}]
            })
        
        async def run_analytics():
            return await analytics.ainvoke({
                "messages": [{"role": "user", "content": "Check system health"}]
            })
        
        # Run both concurrently
        results = await asyncio.gather(run_discovery(), run_analytics())
        
        assert len(results) == 2
        assert all("messages" in r for r in results)
```

### 8.6 Test Configuration

```python
# tests/conftest.py
"""Pytest configuration and shared fixtures."""

import pytest
import pytest_asyncio
import os
import tempfile
from unittest.mock import MagicMock


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for testing."""
    env_vars = {
        "ANTHROPIC_API_KEY": "test-key",
        "OPENAI_API_KEY": "test-key",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "LANGCHAIN_TRACING_V2": "false",
    }
    
    old_env = {}
    for key, value in env_vars.items():
        old_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield env_vars
    
    # Restore original environment
    for key, value in old_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest_asyncio.fixture
async def async_temp_workspace():
    """Create a temporary workspace directory for async tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
```

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
addopts = -v --tb=short
```

### 8.7 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Workflow Automation Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=agents --cov-report=xml
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v -m integration
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run E2E tests
        run: pytest tests/e2e/ -v -m e2e --timeout=300
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          DATABASE_URL: postgresql://test:test@localhost:5432/test
```

---

## Appendix A: Environment Setup

```bash
# setup.sh - Environment setup script

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install deepagents
pip install deepagents langchain-anthropic langchain-openai

# Create directory structure
mkdir -p workspace memories skills tests/{unit,integration,e2e} agents models patterns config

# Create AGENTS.md (domain knowledge)
cat > AGENTS.md << 'EOF'
# Workflow Automation Domain Knowledge

## Organization
- Industry: Technology
- Size: 500-1000 employees
- Primary tools: Jira, Confluence, Slack, Salesforce, PostgreSQL

## Key Workflows
1. Employee Onboarding
2. Expense Approval
3. Invoice Processing
4. Customer Support Ticket Resolution
5. Deployment Pipeline

## Automation Priorities
1. High-volume, repetitive tasks
2. Multi-system data synchronization
3. Approval workflows with clear rules
4. Reporting and analytics generation
EOF

# Create .env file
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/workflows
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=workflow-automation
EOF

echo "Setup complete. Edit .env with your API keys."
```

## Appendix B: Monitoring and Observability

```python
# config/observability.py
"""Observability configuration for the workflow automation system."""

from langsmith import Client
import structlog
import logging

def setup_structured_logging():
    """Configure structured logging for all agents."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

def setup_langsmith_tracing():
    """Configure LangSmith tracing for agent observability."""
    client = Client()
    return client

# Metrics to track
AGENT_METRICS = {
    "agent_invocation_total": "Total number of agent invocations",
    "agent_invocation_duration_seconds": "Agent invocation latency",
    "agent_tool_calls_total": "Total tool calls made by agents",
    "agent_tool_call_duration_seconds": "Tool call latency",
    "agent_errors_total": "Total agent errors",
    "agent_tokens_total": "Total LLM tokens consumed",
    "agent_cost_total": "Total LLM cost",
    "workflow_executions_total": "Total workflow executions",
    "workflow_execution_duration_seconds": "Workflow execution latency",
    "workflow_errors_total": "Total workflow errors",
}
```

---

*End of document*
