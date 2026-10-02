# AI-Powered Marketing Compliance Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a multi-agent marketing compliance system using LangChain DeepAgents that monitors marketing content, detects violations, triggers responses, generates reports, and tracks performance analytics.

**Architecture:** Six specialized agents (Monitor, Detect, Respond, Report, Analytics, Orchestrator) coordinated by a central orchestrator using LangChain's DeepAgents framework. Each agent is an independent LLM-powered unit with its own tools, prompts, and state. Communication happens via a shared event bus and structured message passing.

**Tech Stack:** Python 3.11+, LangChain, LangGraph, DeepAgents, OpenAI GPT-4, Pydantic, FastAPI, Redis (event bus), PostgreSQL (state), pytest, Docker

---

## Task 1: Project Scaffold and Dependencies

**Objective:** Initialize the project with all required dependencies and directory structure.

**Files:**
- Create: `marketing-compliance/pyproject.toml`
- Create: `marketing-compliance/src/__init__.py`
- Create: `marketing-compliance/src/agents/__init__.py`
- Create: `marketing-compliance/src/tools/__init__.py`
- Create: `marketing-compliance/src/models/__init__.py`
- Create: `marketing-compliance/src/events/__init__.py`
- Create: `marketing-compliance/tests/__init__.py`
- Create: `marketing-compliance/.env.example`
- Create: `marketing-compliance/Dockerfile`
- Create: `marketing-compliance/docker-compose.yml`

**Step 1: Write `pyproject.toml`**

```toml
[project]
name = "marketing-compliance"
version = "0.1.0"
description = "AI-powered marketing compliance using LangChain DeepAgents"
requires-python = ">=3.11"
dependencies = [
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "langgraph>=0.2.0",
    "deepagents>=0.1.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "redis>=5.0",
    "sqlalchemy>=2.0",
    "alembic>=1.13",
    "httpx>=0.27",
    "python-dotenv>=1.0",
    "structlog>=24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "mypy>=1.11",
    "respx>=0.21",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

**Step 2: Write `.env.example`**

```env
OPENAI_API_KEY=sk-...
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql+asyncpg://compliance:compliance@localhost:5432/compliance
LOG_LEVEL=INFO
ENVIRONMENT=development
MAX_CONCURRENT_AGENTS=10
AGENT_TIMEOUT_SECONDS=120
```

**Step 3: Write `Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 4: Write `docker-compose.yml`**

```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: compliance
      POSTGRES_PASSWORD: compliance
      POSTGRES_DB: compliance
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

**Step 5: Verify installation**

Run: `cd marketing-compliance && pip install -e ".[dev]"`
Expected: All packages install without errors.

**Step 6: Commit**

```bash
git add .
git commit -m "chore: initial project scaffold with dependencies"
```

---

## Task 2: Core Data Models

**Objective:** Define Pydantic models for marketing content, compliance rules, violations, and agent messages.

**Files:**
- Create: `marketing-compliance/src/models/content.py`
- Create: `marketing-compliance/src/models/rules.py`
- Create: `marketing-compliance/src/models/violations.py`
- Create: `marketing-compliance/src/models/events.py`
- Create: `marketing-compliance/src/models/agent.py`
- Create: `tests/test_models.py`

**Step 1: Write failing test**

```python
# tests/test_models.py
from src.models.content import MarketingContent, ContentChannel, ContentStatus
from src.models.rules import ComplianceRule, RuleSeverity
from src.models.violations import Violation, ViolationStatus
from src.models.events import Event, EventType
from src.models.agent import AgentMessage, AgentType


def test_marketing_content_creation():
    content = MarketingContent(
        id="c-001",
        text="Buy now! Guaranteed results!",
        channel=ContentChannel.EMAIL,
        brand_id="brand-001",
        campaign_id="camp-001",
    )
    assert content.status == ContentStatus.PENDING
    assert content.channel == ContentChannel.EMAIL


def test_compliance_rule_creation():
    rule = ComplianceRule(
        id="rule-001",
        name="No Guaranteed Results",
        description="Marketing must not promise guaranteed results",
        pattern=r"guaranteed\s+results",
        severity=RuleSeverity.HIGH,
        channels=[ContentChannel.EMAIL, ContentChannel.SOCIAL],
    )
    assert rule.severity == RuleSeverity.HIGH


def test_violation_creation():
    violation = Violation(
        id="v-001",
        content_id="c-001",
        rule_id="rule-001",
        snippet="Guaranteed results!",
        explanation="Content promises guaranteed outcomes",
    )
    assert violation.status == ViolationStatus.DETECTED


def test_agent_message_creation():
    msg = AgentMessage(
        id="m-001",
        source_agent=AgentType.MONITOR,
        target_agent=AgentType.DETECT,
        payload={"content_id": "c-001"},
    )
    assert msg.source_agent == AgentType.MONITOR
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — "ModuleNotFoundError: No module named 'src.models'"

**Step 3: Write `src/models/content.py`**

```python
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ContentChannel(str, Enum):
    EMAIL = "email"
    SOCIAL = "social"
    WEB = "web"
    SMS = "sms"
    PUSH = "push"
    ADS = "ads"


class ContentStatus(str, Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    APPROVED = "approved"
    FLAGGED = "flagged"
    REJECTED = "rejected"
    REVIEWED = "reviewed"


class MarketingContent(BaseModel):
    id: str = Field(default_factory=lambda: f"c-{uuid.uuid4().hex[:8]}")
    text: str
    channel: ContentChannel
    brand_id: str
    campaign_id: str
    author_id: str = ""
    metadata: dict = Field(default_factory=dict)
    status: ContentStatus = ContentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Step 4: Write `src/models/rules.py`**

```python
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from src.models.content import ContentChannel


class RuleSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceRule(BaseModel):
    id: str = Field(default_factory=lambda: f"rule-{uuid.uuid4().hex[:8]}")
    name: str
    description: str
    pattern: str = ""
    keywords: list[str] = Field(default_factory=list)
    severity: RuleSeverity
    channels: list[ContentChannel] = Field(default_factory=list)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Step 5: Write `src/models/violations.py`**

```python
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from src.models.rules import RuleSeverity


class ViolationStatus(str, Enum):
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class Violation(BaseModel):
    id: str = Field(default_factory=lambda: f"v-{uuid.uuid4().hex[:8]}")
    content_id: str
    rule_id: str
    snippet: str
    explanation: str
    severity: RuleSeverity = RuleSeverity.MEDIUM
    confidence: float = 0.0
    status: ViolationStatus = ViolationStatus.DETECTED
    assigned_to: str = ""
    resolution_notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
```

**Step 6: Write `src/models/events.py`**

```python
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    CONTENT_SUBMITTED = "content.submitted"
    CONTENT_SCANNED = "content.scanned"
    VIOLATION_DETECTED = "violation.detected"
    VIOLATION_CONFIRMED = "violation.confirmed"
    VIOLATION_RESOLVED = "violation.resolved"
    RESPONSE_TRIGGERED = "response.triggered"
    REPORT_GENERATED = "report.generated"
    ANALYTICS_UPDATED = "analytics.updated"


class Event(BaseModel):
    id: str = Field(default_factory=lambda: f"e-{uuid.uuid4().hex[:8]}")
    type: EventType
    source: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str = ""
```

**Step 7: Write `src/models/agent.py`**

```python
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    MONITOR = "monitor"
    DETECT = "detect"
    RESPOND = "respond"
    REPORT = "report"
    ANALYTICS = "analytics"
    ORCHESTRATOR = "orchestrator"


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"m-{uuid.uuid4().hex[:8]}")
    source_agent: AgentType
    target_agent: AgentType
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: int = 5  # 1 = highest, 10 = lowest
```

**Step 8: Run tests to verify pass**

Run: `pytest tests/test_models.py -v`
Expected: 4 passed

**Step 9: Commit**

```bash
git add src/models/ tests/test_models.py
git commit -m "feat: add core Pydantic data models for content, rules, violations, events, agents"
```

---

## Task 3: Event Bus and Shared Infrastructure

**Objective:** Implement the Redis-based event bus and shared agent infrastructure.

**Files:**
- Create: `marketing-compliance/src/events/bus.py`
- Create: `marketing-compliance/src/events/handlers.py`
- Create: `marketing-compliance/src/agents/base.py`
- Create: `marketing-compliance/src/config.py`
- Create: `tests/test_event_bus.py`

**Step 1: Write failing test**

```python
# tests/test_event_bus.py
import pytest
from src.events.bus import EventBus
from src.models.events import Event, EventType


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus(redis_url="redis://localhost:6379/15")
    received = []

    async def handler(event: Event):
        received.append(event)

    await bus.subscribe(EventType.CONTENT_SUBMITTED, handler)
    event = Event(type=EventType.CONTENT_SUBMITTED, source="test", payload={"id": "1"})
    await bus.publish(event)
    await bus.wait_for_handlers()

    assert len(received) == 1
    assert received[0].type == EventType.CONTENT_SUBMITTED
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_event_bus.py -v`
Expected: FAIL — "ModuleNotFoundError"

**Step 3: Write `src/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://compliance:compliance@localhost:5432/compliance"
    log_level: str = "INFO"
    environment: str = "development"
    max_concurrent_agents: int = 10
    agent_timeout_seconds: int = 120
    model_name: str = "gpt-4o"
    temperature: float = 0.1

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 4: Write `src/events/bus.py`**

```python
from __future__ import annotations

import json
from collections.abc import Callable

import redis.asyncio as redis

from src.config import settings
from src.models.events import Event, EventType

Handler = Callable[[Event], None]


class EventBus:
    def __init__(self, redis_url: str | None = None):
        self._redis_url = redis_url or settings.redis_url
        self._redis: redis.Redis | None = None
        self._pubsub: redis.client.PubSub | None = None
        self._handlers: dict[EventType, list[Handler]] = {}
        self._running = False

    async def connect(self):
        self._redis = redis.from_url(self._redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()

    async def disconnect(self):
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()

    async def subscribe(self, event_type: EventType, handler: Handler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            if self._pubsub:
                await self._pubsub.subscribe(event_type.value)
        self._handlers[event_type].append(handler)

    async def publish(self, event: Event):
        if not self._redis:
            raise RuntimeError("Event bus not connected")
        await self._redis.publish(event.type.value, event.model_dump_json())

    async def wait_for_handlers(self):
        """Allow time for async handlers to process (test helper)."""
        import asyncio
        await asyncio.sleep(0.1)

    async def listen(self):
        """Background task: listen for events and dispatch to handlers."""
        if not self._pubsub:
            raise RuntimeError("Event bus not connected")
        self._running = True
        async for message in self._pubsub.listen():
            if not self._running:
                break
            if message["type"] != "message":
                continue
            event = Event.model_validate_json(message["data"])
            handlers = self._handlers.get(event.type, [])
            for handler in handlers:
                try:
                    await handler(event) if asyncio.iscoroutinefunction(handler) else handler(event)
                except Exception:
                    pass  # Log and continue

    def stop(self):
        self._running = False
```

**Step 5: Write `src/agents/base.py`**

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from src.config import settings
from src.models.agent import AgentMessage, AgentType


class BaseAgent(ABC):
    """Base class for all compliance agents."""

    def __init__(self, agent_type: AgentType, model: BaseChatModel | None = None):
        self.agent_type = agent_type
        self.model = model or ChatOpenAI(
            model=settings.model_name,
            temperature=settings.temperature,
            api_key=settings.openai_api_key,
        )
        self._message_queue: list[AgentMessage] = []

    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage | None:
        """Process an incoming message and optionally return a response."""
        ...

    async def send(self, target: AgentType, payload: dict[str, Any], correlation_id: str = "") -> AgentMessage:
        msg = AgentMessage(
            source_agent=self.agent_type,
            target_agent=target,
            payload=payload,
            correlation_id=correlation_id,
        )
        self._message_queue.append(msg)
        return msg

    def get_pending_messages(self) -> list[AgentMessage]:
        msgs = self._message_queue.copy()
        self._message_queue.clear()
        return msgs
```

**Step 6: Run tests to verify pass**

Run: `pytest tests/test_event_bus.py -v`
Expected: 1 passed

**Step 7: Commit**

```bash
git add src/events/ src/agents/base.py src/config.py tests/test_event_bus.py
git commit -m "feat: add Redis event bus and base agent infrastructure"
```

---

## Task 4: Agent Architecture and Orchestrator

**Objective:** Implement the orchestrator that routes messages between agents and manages the compliance pipeline.

**Files:**
- Create: `marketing-compliance/src/agents/orchestrator.py`
- Create: `marketing-compliance/src/agents/registry.py`
- Create: `tests/test_orchestrator.py`

**Step 1: Write failing test**

```python
# tests/test_orchestrator.py
import pytest
from src.agents.orchestrator import Orchestrator
from src.agents.registry import AgentRegistry
from src.models.agent import AgentMessage, AgentType


@pytest.mark.asyncio
async def test_orchestrator_routes_message():
    registry = AgentRegistry()
    orchestrator = Orchestrator(registry)

    # Register a mock agent
    class MockAgent:
        agent_type = AgentType.MONITOR
        async def process(self, message):
            return None

    registry.register(MockAgent())

    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.MONITOR,
        payload={"test": True},
    )
    # Should not raise
    await orchestrator.route(msg)
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL — "ModuleNotFoundError"

**Step 3: Write `src/agents/registry.py`**

```python
from __future__ import annotations

from src.agents.base import BaseAgent
from src.models.agent import AgentType


class AgentRegistry:
    """Registry mapping agent types to agent instances."""

    def __init__(self):
        self._agents: dict[AgentType, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        self._agents[agent.agent_type] = agent

    def get(self, agent_type: AgentType) -> BaseAgent | None:
        return self._agents.get(agent_type)

    def all_agents(self) -> list[BaseAgent]:
        return list(self._agents.values())
```

**Step 4: Write `src/agents/orchestrator.py`**

```python
from __future__ import annotations

import structlog

from src.agents.base import BaseAgent
from src.agents.registry import AgentRegistry
from src.models.agent import AgentMessage, AgentType

logger = structlog.get_logger()


class Orchestrator:
    """Central orchestrator that routes messages between agents."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self._pipeline = {
            AgentType.MONITOR: [AgentType.DETECT],
            AgentType.DETECT: [AgentType.RESPOND, AgentType.REPORT],
            AgentType.RESPOND: [AgentType.ANALYTICS],
            AgentType.REPORT: [AgentType.ANALYTICS],
        }

    async def route(self, message: AgentMessage) -> list[AgentMessage]:
        """Route a message to its target agent and return responses."""
        target = self.registry.get(message.target_agent)
        if not target:
            logger.warning("no_agent_for_target", target=message.target_agent)
            return []

        response = await target.process(message)
        responses = [response] if response else []

        # Auto-forward to next pipeline stage
        if response:
            next_agents = self._pipeline.get(message.target_agent, [])
            for next_agent_type in next_agents:
                forwarded = await self._forward(response, next_agent_type)
                if forwarded:
                    responses.append(forwarded)

        return responses

    async def _forward(self, message: AgentMessage, next_agent: AgentType) -> AgentMessage | None:
        next_agent_instance = self.registry.get(next_agent)
        if not next_agent_instance:
            return None
        new_msg = AgentMessage(
            source_agent=message.target_agent,
            target_agent=next_agent,
            payload=message.payload,
            correlation_id=message.correlation_id,
        )
        return await next_agent_instance.process(new_msg)

    async def start_pipeline(self, initial_message: AgentMessage) -> list[AgentMessage]:
        """Start the full compliance pipeline from the monitor stage."""
        all_responses = []
        queue = [initial_message]

        while queue:
            msg = queue.pop(0)
            responses = await self.route(msg)
            all_responses.extend(responses)
            queue.extend(responses)

        return all_responses
```

**Step 5: Run tests to verify pass**

Run: `pytest tests/test_orchestrator.py -v`
Expected: 1 passed

**Step 6: Commit**

```bash
git add src/agents/orchestrator.py src/agents/registry.py tests/test_orchestrator.py
git commit -m "feat: add orchestrator and agent registry for pipeline routing"
```

---

## Task 5: Monitoring Agent Implementation

**Objective:** Build the Monitoring agent that ingests marketing content from various channels and submits it for compliance scanning.

**Files:**
- Create: `marketing-compliance/src/agents/monitor.py`
- Create: `marketing-compliance/src/tools/content_ingestion.py`
- Create: `tests/test_monitor_agent.py`

**Step 1: Write failing test**

```python
# tests/test_monitor_agent.py
import pytest
from src.agents.monitor import MonitoringAgent
from src.models.agent import AgentMessage, AgentType
from src.models.content import MarketingContent, ContentChannel


@pytest.mark.asyncio
async def test_monitor_agent_ingests_content():
    agent = MonitoringAgent()
    content = MarketingContent(
        text="Special offer: 50% off everything!",
        channel=ContentChannel.EMAIL,
        brand_id="brand-001",
        campaign_id="camp-001",
    )
    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.MONITOR,
        payload={"content": content.model_dump()},
    )
    response = await agent.process(msg)
    assert response is not None
    assert response.target_agent == AgentType.DETECT
    assert "content" in response.payload
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_monitor_agent.py -v`
Expected: FAIL — "ModuleNotFoundError"

**Step 3: Write `src/tools/content_ingestion.py`**

```python
from __future__ import annotations

import re
from collections.abc import Callable

from src.models.content import ContentChannel, MarketingContent


class ContentIngestionTool:
    """Tool for ingesting and normalizing marketing content from various channels."""

    def __init__(self):
        self._parsers: dict[ContentChannel, Callable[[dict], MarketingContent]] = {
            ContentChannel.EMAIL: self._parse_email,
            ContentChannel.SOCIAL: self._parse_social,
            ContentChannel.WEB: self._parse_web,
            ContentChannel.SMS: self._parse_sms,
            ContentChannel.PUSH: self._parse_push,
            ContentChannel.ADS: self._parse_ads,
        }

    def ingest(self, raw: dict, channel: ContentChannel) -> MarketingContent:
        parser = self._parsers.get(channel, self._parse_generic)
        return parser(raw)

    def _parse_email(self, raw: dict) -> MarketingContent:
        return MarketingContent(
            text=raw.get("body", ""),
            channel=ContentChannel.EMAIL,
            brand_id=raw.get("brand_id", ""),
            campaign_id=raw.get("campaign_id", ""),
            author_id=raw.get("from", ""),
            metadata={"subject": raw.get("subject", "")},
        )

    def _parse_social(self, raw: dict) -> MarketingContent:
        return MarketingContent(
            text=raw.get("text", ""),
            channel=ContentChannel.SOCIAL,
            brand_id=raw.get("brand_id", ""),
            campaign_id=raw.get("campaign_id", ""),
            author_id=raw.get("author_id", ""),
            metadata={"platform": raw.get("platform", "")},
        )

    def _parse_web(self, raw: dict) -> MarketingContent:
        return MarketingContent(
            text=raw.get("content", ""),
            channel=ContentChannel.WEB,
            brand_id=raw.get("brand_id", ""),
            campaign_id=raw.get("campaign_id", ""),
            metadata={"url": raw.get("url", "")},
        )

    def _parse_sms(self, raw: dict) -> MarketingContent:
        return MarketingContent(
            text=raw.get("message", ""),
            channel=ContentChannel.SMS,
            brand_id=raw.get("brand_id", ""),
            campaign_id=raw.get("campaign_id", ""),
        )

    def _parse_push(self, raw: dict) -> MarketingContent:
        return MarketingContent(
            text=raw.get("body", ""),
            channel=ContentChannel.PUSH,
            brand_id=raw.get("brand_id", ""),
            campaign_id=raw.get("campaign_id", ""),
            metadata={"title": raw.get("title", "")},
        )

    def _parse_ads(self, raw: dict) -> MarketingContent:
        return MarketingContent(
            text=raw.get("copy", ""),
            channel=ContentChannel.ADS,
            brand_id=raw.get("brand_id", ""),
            campaign_id=raw.get("campaign_id", ""),
            metadata={"ad_format": raw.get("format", "")},
        )

    def _parse_generic(self, raw: dict) -> MarketingContent:
        return MarketingContent(
            text=raw.get("text", ""),
            channel=ContentChannel.WEB,
            brand_id=raw.get("brand_id", ""),
            campaign_id=raw.get("campaign_id", ""),
        )

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for consistent processing."""
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text
```

**Step 4: Write `src/agents/monitor.py`**

```python
from __future__ import annotations

import structlog

from src.agents.base import BaseAgent
from src.models.agent import AgentMessage, AgentType
from src.models.content import ContentStatus, MarketingContent
from src.models.events import Event, EventType
from src.tools.content_ingestion import ContentIngestionTool

logger = structlog.get_logger()


class MonitoringAgent(BaseAgent):
    """Agent responsible for ingesting marketing content and initiating compliance scans."""

    def __init__(self, model=None):
        super().__init__(AgentType.MONITOR, model)
        self.ingestion_tool = ContentIngestionTool()

    async def process(self, message: AgentMessage) -> AgentMessage | None:
        """Ingest content and forward to detection agent."""
        raw_content = message.payload.get("content", {})

        if isinstance(raw_content, dict):
            content = MarketingContent.model_validate(raw_content)
        else:
            content = raw_content

        # Normalize and validate
        content.text = self.ingestion_tool.normalize_text(content.text)
        content.status = ContentStatus.SCANNING

        logger.info(
            "content_ingested",
            content_id=content.id,
            channel=content.channel.value,
            brand_id=content.brand_id,
        )

        # Forward to detection agent
        return await self.send(
            target=AgentType.DETECT,
            payload={
                "content": content.model_dump(),
                "action": "scan",
            },
            correlation_id=message.correlation_id,
        )
```

**Step 5: Run tests to verify pass**

Run: `pytest tests/test_monitor_agent.py -v`
Expected: 1 passed

**Step 6: Commit**

```bash
git add src/agents/monitor.py src/tools/content_ingestion.py tests/test_monitor_agent.py
git commit -m "feat: implement monitoring agent with content ingestion tools"
```

---

## Task 6: Detection Agent Implementation

**Objective:** Build the Detection agent that uses LLM + rule-based scanning to identify compliance violations.

**Files:**
- Create: `marketing-compliance/src/agents/detection.py`
- Create: `marketing-compliance/src/tools/rule_engine.py`
- Create: `marketing-compliance/src/tools/llm_scanner.py`
- Create: `tests/test_detection_agent.py`

**Step 1: Write failing test**

```python
# tests/test_detection_agent.py
import pytest
from src.agents.detection import DetectionAgent
from src.models.agent import AgentMessage, AgentType
from src.models.content import MarketingContent, ContentChannel, ContentStatus
from src.models.rules import ComplianceRule, RuleSeverity


@pytest.mark.asyncio
async def test_detection_agent_finds_violations():
    agent = DetectionAgent()
    content = MarketingContent(
        id="c-001",
        text="Buy now! Guaranteed results or your money back!",
        channel=ContentChannel.EMAIL,
        brand_id="brand-001",
        campaign_id="camp-001",
        status=ContentStatus.SCANNING,
    )
    msg = AgentMessage(
        source_agent=AgentType.MONITOR,
        target_agent=AgentType.DETECT,
        payload={"content": content.model_dump(), "action": "scan"},
    )
    response = await agent.process(msg)
    assert response is not None
    assert "violations" in response.payload
    assert len(response.payload["violations"]) > 0
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_detection_agent.py -v`
Expected: FAIL — "ModuleNotFoundError"

**Step 3: Write `src/tools/rule_engine.py`**

```python
from __future__ import annotations

import re
from dataclasses import dataclass

from src.models.content import MarketingContent
from src.models.rules import ComplianceRule, RuleSeverity
from src.models.violations import Violation


@dataclass
class RuleMatch:
    rule: ComplianceRule
    snippet: str
    confidence: float


class RuleEngine:
    """Rule-based compliance scanner using regex patterns and keyword matching."""

    def __init__(self, rules: list[ComplianceRule] | None = None):
        self.rules = rules or self._default_rules()

    def scan(self, content: MarketingContent) -> list[RuleMatch]:
        matches = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            if rule.channels and content.channel not in rule.channels:
                continue

            # Regex pattern matching
            if rule.pattern:
                for m in re.finditer(rule.pattern, content.text, re.IGNORECASE):
                    matches.append(RuleMatch(
                        rule=rule,
                        snippet=m.group(0),
                        confidence=0.85,
                    ))

            # Keyword matching
            for keyword in rule.keywords:
                if keyword.lower() in content.text.lower():
                    idx = content.text.lower().index(keyword.lower())
                    start = max(0, idx - 20)
                    end = min(len(content.text), idx + len(keyword) + 20)
                    matches.append(RuleMatch(
                        rule=rule,
                        snippet=content.text[start:end],
                        confidence=0.70,
                    ))

        return matches

    def to_violations(self, content: MarketingContent, matches: list[RuleMatch]) -> list[Violation]:
        return [
            Violation(
                content_id=content.id,
                rule_id=match.rule.id,
                snippet=match.snippet,
                explanation=f"Matched rule: {match.rule.name}",
                severity=match.rule.severity,
                confidence=match.confidence,
            )
            for match in matches
        ]

    def _default_rules(self) -> list[ComplianceRule]:
        return [
            ComplianceRule(
                name="No Guaranteed Results",
                description="Marketing must not promise guaranteed results",
                pattern=r"guaranteed\s+(results?|outcomes?|returns?)",
                severity=RuleSeverity.HIGH,
            ),
            ComplianceRule(
                name="No False Urgency",
                description="No artificial urgency or false scarcity",
                pattern=r"(limited time|act now|only \d+ left|hurry)",
                keywords=["act now", "limited time", "don't miss out"],
                severity=RuleSeverity.MEDIUM,
            ),
            ComplianceRule(
                name="Required Disclaimer",
                description="Investment ads require risk disclaimer",
                pattern=r"(invest|returns?|yield)",
                keywords=["invest", "returns", "yield"],
                severity=RuleSeverity.CRITICAL,
            ),
            ComplianceRule(
                name="No Misleading Claims",
                description="No unsubstantiated superlatives",
                pattern=r"(#1|best in the world|revolutionary|miracle)",
                severity=RuleSeverity.MEDIUM,
            ),
            ComplianceRule(
                name="TCPA Compliance",
                description="SMS marketing requires opt-in language",
                severity=RuleSeverity.HIGH,
                channels=[__import__("src.models.content", fromlist=["ContentChannel"]).ContentChannel.SMS],
            ),
        ]
```

**Step 4: Write `src/tools/llm_scanner.py`**

```python
from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from src.config import settings
from src.models.content import MarketingContent
from src.models.rules import RuleSeverity
from src.models.violations import Violation

COMPLIANCE_SYSTEM_PROMPT = """You are a marketing compliance reviewer. Analyze the given marketing content for compliance violations.

Check for:
1. False or misleading claims
2. Unsubstantiated guarantees
3. Missing required disclaimers
4. Regulatory violations (FTC, TCPA, GDPR, CAN-SPAM)
5. Brand safety issues
6. Competitor disparagement
7. Discriminatory language

Return a JSON array of violations, each with:
- "rule_name": short name of the violated rule
- "explanation": why this is a violation
- "snippet": the exact text that violates
- "severity": one of "low", "medium", "high", "critical"
- "confidence": 0.0 to 1.0

If no violations, return an empty array [].

Content channel: {channel}
Brand: {brand_id}
"""


class LLMScanner:
    """LLM-powered compliance scanner for nuanced violation detection."""

    def __init__(self, model: BaseChatModel | None = None):
        from langchain_openai import ChatOpenAI
        self.model = model or ChatOpenAI(
            model=settings.model_name,
            temperature=0.0,
            api_key=settings.openai_api_key,
        )

    async def scan(self, content: MarketingContent) -> list[Violation]:
        prompt = COMPLIANCE_SYSTEM_PROMPT.format(
            channel=content.channel.value,
            brand_id=content.brand_id,
        )
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"Content to review:\n\n{content.text}"),
        ]

        response = await self.model.ainvoke(messages)
        try:
            violations_data = json.loads(response.content)
        except (json.JSONDecodeError, TypeError):
            return []

        severity_map = {
            "low": RuleSeverity.LOW,
            "medium": RuleSeverity.MEDIUM,
            "high": RuleSeverity.HIGH,
            "critical": RuleSeverity.CRITICAL,
        }

        return [
            Violation(
                content_id=content.id,
                rule_id=f"llm-{i}",
                snippet=v.get("snippet", ""),
                explanation=v.get("explanation", ""),
                severity=severity_map.get(v.get("severity", "medium"), RuleSeverity.MEDIUM),
                confidence=float(v.get("confidence", 0.5)),
            )
            for i, v in enumerate(violations_data)
        ]
```

**Step 5: Write `src/agents/detection.py`**

```python
from __future__ import annotations

import structlog

from src.agents.base import BaseAgent
from src.models.agent import AgentMessage, AgentType
from src.models.content import ContentStatus, MarketingContent
from src.models.violations import Violation
from src.tools.llm_scanner import LLMScanner
from src.tools.rule_engine import RuleEngine

logger = structlog.get_logger()


class DetectionAgent(BaseAgent):
    """Agent that scans marketing content for compliance violations using rules + LLM."""

    def __init__(self, model=None, use_llm: bool = True):
        super().__init__(AgentType.DETECT, model)
        self.rule_engine = RuleEngine()
        self.llm_scanner = LLMScanner(model) if use_llm else None

    async def process(self, message: AgentMessage) -> AgentMessage | None:
        """Scan content for violations and forward results."""
        raw_content = message.payload.get("content", {})
        content = MarketingContent.model_validate(raw_content) if isinstance(raw_content, dict) else raw_content

        # Rule-based scan
        rule_matches = self.rule_engine.scan(content)
        violations = self.rule_engine.to_violations(content, rule_matches)

        # LLM-based scan (async, can run concurrently)
        if self.llm_scanner:
            llm_violations = await self.llm_scanner.scan(content)
            violations.extend(llm_violations)

        # Deduplicate by snippet
        seen_snippets: set[str] = set()
        unique_violations: list[Violation] = []
        for v in violations:
            key = v.snippet.lower().strip()
            if key not in seen_snippets:
                seen_snippets.add(key)
                unique_violations.append(v)

        # Update content status
        if unique_violations:
            content.status = ContentStatus.FLAGGED
        else:
            content.status = ContentStatus.APPROVED

        logger.info(
            "content_scanned",
            content_id=content.id,
            violations_found=len(unique_violations),
            status=content.status.value,
        )

        # Forward to response and report agents
        return await self.send(
            target=AgentType.RESPOND,
            payload={
                "content": content.model_dump(),
                "violations": [v.model_dump() for v in unique_violations],
                "action": "handle_violations" if unique_violations else "approve",
            },
            correlation_id=message.correlation_id,
        )
```

**Step 6: Run tests to verify pass**

Run: `pytest tests/test_detection_agent.py -v`
Expected: 1 passed

**Step 7: Commit**

```bash
git add src/agents/detection.py src/tools/rule_engine.py src/tools/llm_scanner.py tests/test_detection_agent.py
git commit -m "feat: implement detection agent with rule engine and LLM scanner"
```

---

## Task 7: Response Agent Implementation

**Objective:** Build the Response agent that handles violations — auto-reject, flag for review, or escalate.

**Files:**
- Create: `marketing-compliance/src/agents/response.py`
- Create: `marketing-compliance/src/tools/response_actions.py`
- Create: `tests/test_response_agent.py`

**Step 1: Write failing test**

```python
# tests/test_response_agent.py
import pytest
from src.agents.response import ResponseAgent
from src.models.agent import AgentMessage, AgentType
from src.models.content import MarketingContent, ContentChannel, ContentStatus
from src.models.violations import Violation, ViolationStatus
from src.models.rules import RuleSeverity


@pytest.mark.asyncio
async def test_response_agent_auto_rejects_critical():
    agent = ResponseAgent()
    content = MarketingContent(
        id="c-001",
        text="Guaranteed 500% returns on investment!",
        channel=ContentChannel.EMAIL,
        brand_id="brand-001",
        campaign_id="camp-001",
        status=ContentStatus.FLAGGED,
    )
    violations = [
        Violation(
            id="v-001",
            content_id="c-001",
            rule_id="rule-001",
            snippet="Guaranteed 500% returns",
            explanation="Unsubstantiated guarantee",
            severity=RuleSeverity.CRITICAL,
            confidence=0.95,
        )
    ]
    msg = AgentMessage(
        source_agent=AgentType.DETECT,
        target_agent=AgentType.RESPOND,
        payload={
            "content": content.model_dump(),
            "violations": [v.model_dump() for v in violations],
            "action": "handle_violations",
        },
    )
    response = await agent.process(msg)
    assert response is not None
    assert response.payload.get("action") == "auto_reject"
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_response_agent.py -v`
Expected: FAIL — "ModuleNotFoundError"

**Step 3: Write `src/tools/response_actions.py`**

```python
from __future__ import annotations

from enum import Enum

from src.models.content import ContentStatus
from src.models.rules import RuleSeverity
from src.models.violations import Violation


class ResponseAction(str, Enum):
    AUTO_APPROVE = "auto_approve"
    AUTO_REJECT = "auto_reject"
    FLAG_FOR_REVIEW = "flag_for_review"
    ESCALATE = "escalate"
    REQUEST_REVISION = "request_revision"


class ResponseActionDeterminer:
    """Determines the appropriate response action based on violations."""

    SEVERITY_THRESHOLDS = {
        RuleSeverity.LOW: ResponseAction.FLAG_FOR_REVIEW,
        RuleSeverity.MEDIUM: ResponseAction.FLAG_FOR_REVIEW,
        RuleSeverity.HIGH: ResponseAction.ESCALATE,
        RuleSeverity.CRITICAL: ResponseAction.AUTO_REJECT,
    }

    CONFIDENCE_THRESHOLD = 0.8

    def determine(
        self,
        violations: list[Violation],
    ) -> tuple[ResponseAction, ContentStatus, str]:
        if not violations:
            return ResponseAction.AUTO_APPROVE, ContentStatus.APPROVED, "No violations found"

        max_severity = max(v.severity for v in violations)
        max_confidence = max(v.confidence for v in violations)

        # Auto-reject: critical severity with high confidence
        if max_severity == RuleSeverity.CRITICAL and max_confidence >= self.CONFIDENCE_THRESHOLD:
            return (
                ResponseAction.AUTO_REJECT,
                ContentStatus.REJECTED,
                f"Auto-rejected: {len(violations)} critical violation(s) with high confidence",
            )

        # Escalate: high severity or multiple violations
        if max_severity == RuleSeverity.HIGH or len(violations) >= 3:
            return (
                ResponseAction.ESCALATE,
                ContentStatus.FLAGGED,
                f"Escalated: {len(violations)} violation(s), max severity: {max_severity.value}",
            )

        # Flag for review: medium severity
        if max_severity == RuleSeverity.MEDIUM:
            return (
                ResponseAction.FLAG_FOR_REVIEW,
                ContentStatus.FLAGGED,
                f"Flagged for review: {len(violations)} violation(s)",
            )

        # Default: flag for review
        return (
            ResponseAction.FLAG_FOR_REVIEW,
            ContentStatus.FLAGGED,
            f"Flagged for review: {len(violations)} low-severity violation(s)",
        )
```

**Step 4: Write `src/agents/response.py`**

```python
from __future__ import annotations

import structlog

from src.agents.base import BaseAgent
from src.models.agent import AgentMessage, AgentType
from src.models.content import MarketingContent
from src.models.violations import Violation
from src.tools.response_actions import ResponseAction, ResponseActionDeterminer

logger = structlog.get_logger()


class ResponseAgent(BaseAgent):
    """Agent that determines and executes response actions for violations."""

    def __init__(self, model=None):
        super().__init__(AgentType.RESPOND, model)
        self.action_determiner = ResponseActionDeterminer()

    async def process(self, message: AgentMessage) -> AgentMessage | None:
        """Determine response action and forward to analytics."""
        raw_content = message.payload.get("content", {})
        content = MarketingContent.model_validate(raw_content) if isinstance(raw_content, dict) else raw_content

        raw_violations = message.payload.get("violations", [])
        violations = [Violation.model_validate(v) if isinstance(v, dict) else v for v in raw_violations]

        action, new_status, reason = self.action_determiner.determine(violations)
        content.status = new_status

        logger.info(
            "response_action_taken",
            content_id=content.id,
            action=action.value,
            reason=reason,
            violation_count=len(violations),
        )

        return await self.send(
            target=AgentType.ANALYTICS,
            payload={
                "content": content.model_dump(),
                "violations": [v.model_dump() for v in violations],
                "action": action.value,
                "reason": reason,
            },
            correlation_id=message.correlation_id,
        )
```

**Step 5: Run tests to verify pass**

Run: `pytest tests/test_response_agent.py -v`
Expected: 1 passed

**Step 6: Commit**

```bash
git add src/agents/response.py src/tools/response_actions.py tests/test_response_agent.py
git commit -m "feat: implement response agent with action determination logic"
```

---

## Task 8: Reporting Agent Implementation

**Objective:** Build the Reporting agent that generates compliance reports and dashboards.

**Files:**
- Create: `marketing-compliance/src/agents/reporting.py`
- Create: `marketing-compliance/src/tools/report_generator.py`
- Create: `tests/test_reporting_agent.py`

**Step 1: Write failing test**

```python
# tests/test_reporting_agent.py
import pytest
from src.agents.reporting import ReportingAgent
from src.models.agent import AgentMessage, AgentType


@pytest.mark.asyncio
async def test_reporting_agent_generates_report():
    agent = ReportingAgent()
    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.REPORT,
        payload={
            "report_type": "daily_summary",
            "date": "2026-10-01",
            "brand_id": "brand-001",
        },
    )
    response = await agent.process(msg)
    assert response is not None
    assert "report" in response.payload
    assert response.payload["report"]["type"] == "daily_summary"
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_reporting_agent.py -v`
Expected: FAIL — "ModuleNotFoundError"

**Step 3: Write `src/tools/report_generator.py`**

```python
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from src.models.content import ContentStatus
from src.models.violations import Violation


class ReportGenerator:
    """Generates compliance reports from violation and content data."""

    def generate_daily_summary(
        self,
        brand_id: str,
        report_date: date,
        contents: list[dict],
        violations: list[dict],
    ) -> dict[str, Any]:
        total = len(contents)
        flagged = sum(1 for c in contents if c.get("status") == ContentStatus.FLAGGED.value)
        approved = sum(1 for c in contents if c.get("status") == ContentStatus.APPROVED.value)
        rejected = sum(1 for c in contents if c.get("status") == ContentStatus.REJECTED.value)

        by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for v in violations:
            sev = v.get("severity", "medium")
            by_severity[sev] = by_severity.get(sev, 0) + 1

        by_channel: dict[str, int] = {}
        for c in contents:
            ch = c.get("channel", "unknown")
            by_channel[ch] = by_channel.get(ch, 0) + 1

        return {
            "type": "daily_summary",
            "brand_id": brand_id,
            "date": report_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_content": total,
                "approved": approved,
                "flagged": flagged,
                "rejected": rejected,
                "approval_rate": round(approved / total, 4) if total else 0,
            },
            "violations_by_severity": by_severity,
            "content_by_channel": by_channel,
            "total_violations": len(violations),
        }

    def generate_violation_detail(
        self,
        brand_id: str,
        start_date: date,
        end_date: date,
        violations: list[dict],
    ) -> dict[str, Any]:
        return {
            "type": "violation_detail",
            "brand_id": brand_id,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "generated_at": datetime.utcnow().isoformat(),
            "violations": violations,
            "total": len(violations),
        }

    def generate_trend_report(
        self,
        brand_id: str,
        days: int,
        daily_stats: list[dict],
    ) -> dict[str, Any]:
        return {
            "type": "trend",
            "brand_id": brand_id,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "daily_stats": daily_stats,
            "trend_direction": self._calculate_trend(daily_stats),
        }

    def _calculate_trend(self, daily_stats: list[dict]) -> str:
        if len(daily_stats) < 2:
            return "insufficient_data"
        first_half = daily_stats[: len(daily_stats) // 2]
        second_half = daily_stats[len(daily_stats) // 2 :]
        first_violations = sum(d.get("total_violations", 0) for d in first_half)
        second_violations = sum(d.get("total_violations", 0) for d in second_half)
        if second_violations > first_violations * 1.1:
            return "worsening"
        if second_violations < first_violations * 0.9:
            return "improving"
        return "stable"
```

**Step 4: Write `src/agents/reporting.py`**

```python
from __future__ import annotations

from datetime import date

import structlog

from src.agents.base import BaseAgent
from src.models.agent import AgentMessage, AgentType
from src.tools.report_generator import ReportGenerator

logger = structlog.get_logger()


class ReportingAgent(BaseAgent):
    """Agent that generates compliance reports and dashboards."""

    def __init__(self, model=None):
        super().__init__(AgentType.REPORT, model)
        self.report_generator = ReportGenerator()

    async def process(self, message: AgentMessage) -> AgentMessage | None:
        """Generate report based on request type."""
        report_type = message.payload.get("report_type", "daily_summary")
        brand_id = message.payload.get("brand_id", "unknown")

        if report_type == "daily_summary":
            report = self.report_generator.generate_daily_summary(
                brand_id=brand_id,
                report_date=date.fromisoformat(message.payload.get("date", date.today().isoformat())),
                contents=message.payload.get("contents", []),
                violations=message.payload.get("violations", []),
            )
        elif report_type == "violation_detail":
            report = self.report_generator.generate_violation_detail(
                brand_id=brand_id,
                start_date=date.fromisoformat(message.payload.get("start_date", date.today().isoformat())),
                end_date=date.fromisoformat(message.payload.get("end_date", date.today().isoformat())),
                violations=message.payload.get("violations", []),
            )
        elif report_type == "trend":
            report = self.report_generator.generate_trend_report(
                brand_id=brand_id,
                days=message.payload.get("days", 30),
                daily_stats=message.payload.get("daily_stats", []),
            )
        else:
            report = {"error": f"Unknown report type: {report_type}"}

        logger.info("report_generated", report_type=report_type, brand_id=brand_id)

        return await self.send(
            target=AgentType.ANALYTICS,
            payload={"report": report, "action": "store_report"},
            correlation_id=message.correlation_id,
        )
```

**Step 5: Run tests to verify pass**

Run: `pytest tests/test_reporting_agent.py -v`
Expected: 1 passed

**Step 6: Commit**

```bash
git add src/agents/reporting.py src/tools/report_generator.py tests/test_reporting_agent.py
git commit -m "feat: implement reporting agent with report generator"
```

---

## Task 9: Performance Analytics Agent Implementation

**Objective:** Build the Performance analytics agent that tracks compliance metrics and agent performance.

**Files:**
- Create: `marketing-compliance/src/agents/analytics.py`
- Create: `marketing-compliance/src/tools/metrics.py`
- Create: `tests/test_analytics_agent.py`

**Step 1: Write failing test**

```python
# tests/test_analytics_agent.py
import pytest
from src.agents.analytics import AnalyticsAgent
from src.models.agent import AgentMessage, AgentType


@pytest.mark.asyncio
async def test_analytics_agent_computes_metrics():
    agent = AnalyticsAgent()
    msg = AgentMessage(
        source_agent=AgentType.RESPOND,
        target_agent=AgentType.ANALYTICS,
        payload={
            "content": {"id": "c-001", "status": "flagged"},
            "violations": [{"severity": "high", "confidence": 0.9}],
            "action": "escalate",
            "reason": "High severity violation",
        },
    )
    response = await agent.process(msg)
    assert response is not None
    assert "metrics" in response.payload
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_analytics_agent.py -v`
Expected: FAIL — "ModuleNotFoundError"

**Step 3: Write `src/tools/metrics.py`**

```python
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any


class MetricsCollector:
    """Collects and computes compliance and agent performance metrics."""

    def __init__(self):
        self._counters: dict[str, int] = defaultdict(int)
        self._timers: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}

    def increment(self, metric: str, value: int = 1, tags: dict[str, str] | None = None):
        key = self._key(metric, tags)
        self._counters[key] += value

    def timer(self, metric: str, value: float, tags: dict[str, str] | None = None):
        key = self._key(metric, tags)
        self._timers[key].append(value)

    def gauge(self, metric: str, value: float, tags: dict[str, str] | None = None):
        key = self._key(metric, tags)
        self._gauges[key] = value

    def get_summary(self) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "timers": {},
        }
        for key, values in self._timers.items():
            if values:
                summary["timers"][key] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0],
                }
        return summary

    def compute_compliance_rate(self, total: int, approved: int) -> float:
        return round(approved / total, 4) if total else 0.0

    def compute_violation_rate(self, total: int, violations: int) -> float:
        return round(violations / total, 4) if total else 0.0

    def _key(self, metric: str, tags: dict[str, str] | None) -> str:
        if not tags:
            return metric
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric}{{{tag_str}}}"
```

**Step 4: Write `src/agents/analytics.py`**

```python
from __future__ import annotations

import time

import structlog

from src.agents.base import BaseAgent
from src.models.agent import AgentMessage, AgentType
from src.tools.metrics import MetricsCollector

logger = structlog.get_logger()


class AnalyticsAgent(BaseAgent):
    """Agent that tracks compliance metrics and agent performance."""

    def __init__(self, model=None):
        super().__init__(AgentType.ANALYTICS, model)
        self.metrics = MetricsCollector()

    async def process(self, message: AgentMessage) -> AgentMessage | None:
        """Process analytics events and update metrics."""
        start = time.monotonic()

        action = message.payload.get("action", "unknown")
        content = message.payload.get("content", {})
        violations = message.payload.get("violations", [])

        # Track content status
        status = content.get("status", "unknown")
        self.metrics.increment("content_processed", tags={"status": status})

        # Track violations
        for v in violations:
            severity = v.get("severity", "medium")
            self.metrics.increment("violations", tags={"severity": severity})

        # Track response actions
        self.metrics.increment("response_actions", tags={"action": action})

        # Track agent processing time
        elapsed = time.monotonic() - start
        self.metrics.timer("agent_processing_time", elapsed, tags={"agent": self.agent_type.value})

        summary = self.metrics.get_summary()
        logger.info("analytics_updated", action=action, violation_count=len(violations))

        # Analytics agent is terminal — no forwarding needed
        return None

    def get_metrics(self) -> dict:
        return self.metrics.get_summary()
```

**Step 5: Run tests to verify pass**

Run: `pytest tests/test_analytics_agent.py -v`
Expected: 1 passed

**Step 6: Commit**

```bash
git add src/agents/analytics.py src/tools/metrics.py tests/test_analytics_agent.py
git commit -m "feat: implement performance analytics agent with metrics collector"
```

---

## Task 10: FastAPI Application Entry Point

**Objective:** Create the FastAPI application that wires all agents together and exposes REST endpoints.

**Files:**
- Create: `marketing-compliance/src/main.py`
- Create: `marketing-compliance/src/api/routes.py`
- Create: `marketing-compliance/src/api/schemas.py`
- Create: `tests/test_api.py`

**Step 1: Write failing test**

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_submit_content():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/content", json={
            "text": "Amazing product! Guaranteed results!",
            "channel": "email",
            "brand_id": "brand-001",
            "campaign_id": "camp-001",
        })
    assert response.status_code == 202
    assert "content_id" in response.json()
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_api.py -v`
Expected: FAIL — "ModuleNotFoundError"

**Step 3: Write `src/api/schemas.py`**

```python
from __future__ import annotations

from pydantic import BaseModel, Field

from src.models.content import ContentChannel


class ContentSubmitRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    channel: ContentChannel
    brand_id: str
    campaign_id: str
    author_id: str = ""
    metadata: dict = Field(default_factory=dict)


class ContentSubmitResponse(BaseModel):
    content_id: str
    status: str
    message: str = "Content submitted for compliance scanning"


class ReportRequest(BaseModel):
    report_type: str = "daily_summary"
    brand_id: str
    date: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    days: int = 30


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"
```

**Step 4: Write `src/api/routes.py`**

```python
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    ContentSubmitRequest,
    ContentSubmitResponse,
    HealthResponse,
    ReportRequest,
)
from src.models.agent import AgentMessage, AgentType
from src.models.content import MarketingContent

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")


@router.post("/api/v1/content", response_model=ContentSubmitResponse, status_code=202)
async def submit_content(request: ContentSubmitRequest):
    """Submit marketing content for compliance scanning."""
    from src.main import get_orchestrator

    orchestrator = get_orchestrator()
    content = MarketingContent(
        text=request.text,
        channel=request.channel,
        brand_id=request.brand_id,
        campaign_id=request.campaign_id,
        author_id=request.author_id,
        metadata=request.metadata,
    )

    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.MONITOR,
        payload={"content": content.model_dump()},
    )

    try:
        await orchestrator.start_pipeline(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ContentSubmitResponse(
        content_id=content.id,
        status="pending",
    )


@router.post("/api/v1/reports")
async def generate_report(request: ReportRequest):
    """Generate a compliance report."""
    from src.main import get_orchestrator

    orchestrator = get_orchestrator()
    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.REPORT,
        payload=request.model_dump(),
    )

    responses = await orchestrator.start_pipeline(msg)
    report = {}
    for r in responses:
        if "report" in r.payload:
            report = r.payload["report"]
            break

    return report
```

**Step 5: Write `src/main.py`**

```python
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.agents.analytics import AnalyticsAgent
from src.agents.detection import DetectionAgent
from src.agents.monitor import MonitoringAgent
from src.agents.orchestrator import Orchestrator
from src.agents.registry import AgentRegistry
from src.agents.reporting import ReportingAgent
from src.agents.response import ResponseAgent
from src.api.routes import router

_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return _orchestrator


def create_orchestrator() -> Orchestrator:
    registry = AgentRegistry()
    registry.register(MonitoringAgent())
    registry.register(DetectionAgent())
    registry.register(ResponseAgent())
    registry.register(ReportingAgent())
    registry.register(AnalyticsAgent())
    return Orchestrator(registry)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orchestrator
    _orchestrator = create_orchestrator()
    yield
    _orchestrator = None


app = FastAPI(
    title="Marketing Compliance API",
    description="AI-powered marketing compliance using LangChain DeepAgents",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
```

**Step 6: Run tests to verify pass**

Run: `pytest tests/test_api.py -v`
Expected: 2 passed

**Step 7: Commit**

```bash
git add src/main.py src/api/ tests/test_api.py
git commit -m "feat: add FastAPI application entry point with routes and schemas"
```

---

## Task 11: Testing Strategy

**Objective:** Implement comprehensive tests including unit, integration, and end-to-end tests.

**Files:**
- Create: `marketing-compliance/tests/conftest.py`
- Create: `marketing-compliance/tests/test_integration.py`
- Create: `marketing-compliance/tests/test_e2e_pipeline.py`
- Create: `marketing-compliance/pytest.ini`

**Step 1: Write `tests/conftest.py`**

```python
from __future__ import annotations

import pytest
import pytest_asyncio

from src.agents.analytics import AnalyticsAgent
from src.agents.detection import DetectionAgent
from src.agents.monitor import MonitoringAgent
from src.agents.orchestrator import Orchestrator
from src.agents.registry import AgentRegistry
from src.agents.reporting import ReportingAgent
from src.agents.response import ResponseAgent


@pytest_asyncio.fixture
async def orchestrator():
    registry = AgentRegistry()
    registry.register(MonitoringAgent())
    registry.register(DetectionAgent(use_llm=False))
    registry.register(ResponseAgent())
    registry.register(ReportingAgent())
    registry.register(AnalyticsAgent())
    return Orchestrator(registry)


@pytest.fixture
def sample_content():
    from src.models.content import MarketingContent, ContentChannel
    return MarketingContent(
        text="Special offer: 50% off everything! Act now!",
        channel=ContentChannel.EMAIL,
        brand_id="brand-001",
        campaign_id="camp-001",
    )


@pytest.fixture
def sample_violation():
    from src.models.rules import RuleSeverity
    from src.models.violations import Violation
    return Violation(
        content_id="c-001",
        rule_id="rule-001",
        snippet="Act now!",
        explanation="False urgency detected",
        severity=RuleSeverity.MEDIUM,
        confidence=0.85,
    )
```

**Step 2: Write `tests/test_integration.py`**

```python
from __future__ import annotations

import pytest

from src.models.agent import AgentMessage, AgentType
from src.models.content import ContentStatus


@pytest.mark.asyncio
async def test_full_pipeline_clean_content(orchestrator, sample_content):
    """Test pipeline with compliant content — should approve."""
    sample_content.text = "Check out our new product collection."
    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.MONITOR,
        payload={"content": sample_content.model_dump()},
    )
    responses = await orchestrator.start_pipeline(msg)
    assert len(responses) > 0


@pytest.mark.asyncio
async def test_full_pipeline_violating_content(orchestrator, sample_content):
    """Test pipeline with violating content — should flag."""
    sample_content.text = "Buy now! Guaranteed results or your money back!"
    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.MONITOR,
        payload={"content": sample_content.model_dump()},
    )
    responses = await orchestrator.start_pipeline(msg)
    assert len(responses) > 0


@pytest.mark.asyncio
async def test_detection_to_response_flow(orchestrator, sample_content):
    """Test that detection results flow to response agent."""
    sample_content.text = "Guaranteed 500% returns on investment!"
    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.MONITOR,
        payload={"content": sample_content.model_dump()},
    )
    responses = await orchestrator.start_pipeline(msg)

    # Find response from RESPOND agent
    response_msgs = [r for r in responses if r.source_agent == AgentType.RESPOND]
    assert len(response_msgs) > 0
```

**Step 3: Write `tests/test_e2e_pipeline.py`**

```python
from __future__ import annotations

import pytest

from src.models.agent import AgentMessage, AgentType
from src.models.content import ContentChannel, ContentStatus, MarketingContent


@pytest.mark.asyncio
async def test_e2e_email_compliance_approval(orchestrator):
    """E2E: Clean email content gets approved through full pipeline."""
    content = MarketingContent(
        text="Join us for our annual sale. Great deals on all items.",
        channel=ContentChannel.EMAIL,
        brand_id="brand-001",
        campaign_id="camp-001",
    )
    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.MONITOR,
        payload={"content": content.model_dump()},
    )
    responses = await orchestrator.start_pipeline(msg)
    assert len(responses) >= 3  # At least monitor->detect, detect->respond, respond->analytics


@pytest.mark.asyncio
async def test_e2e_critical_violation_auto_reject(orchestrator):
    """E2E: Critical violation triggers auto-reject."""
    content = MarketingContent(
        text="Guaranteed 1000% returns! Act now! Limited time offer!",
        channel=ContentChannel.EMAIL,
        brand_id="brand-001",
        campaign_id="camp-001",
    )
    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.MONITOR,
        payload={"content": content.model_dump()},
    )
    responses = await orchestrator.start_pipeline(msg)

    # Check that response agent produced an action
    response_msgs = [r for r in responses if r.source_agent == AgentType.RESPOND]
    assert len(response_msgs) > 0
    action = response_msgs[0].payload.get("action", "")
    assert action in ("auto_reject", "escalate", "flag_for_review")


@pytest.mark.asyncio
async def test_e2e_sms_channel_compliance(orchestrator):
    """E2E: SMS content is checked against SMS-specific rules."""
    content = MarketingContent(
        text="Get 50% off! Reply STOP to opt out.",
        channel=ContentChannel.SMS,
        brand_id="brand-001",
        campaign_id="camp-001",
    )
    msg = AgentMessage(
        source_agent=AgentType.ORCHESTRATOR,
        target_agent=AgentType.MONITOR,
        payload={"content": content.model_dump()},
    )
    responses = await orchestrator.start_pipeline(msg)
    assert len(responses) > 0
```

**Step 4: Write `pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
addopts = -v --tb=short --strict-markers
markers =
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    slow: marks tests as slow (deselect with '-m "not slow"')
```

**Step 5: Run all tests**

Run: `pytest -v`
Expected: All tests pass (15+ tests)

**Step 6: Commit**

```bash
git add tests/ pytest.ini
git commit -m "test: add comprehensive testing strategy with unit, integration, and e2e tests"
```

---

## Task 12: Deployment and CI/CD

**Objective:** Add CI/CD pipeline and deployment configuration.

**Files:**
- Create: `marketing-compliance/.github/workflows/ci.yml`
- Create: `marketing-compliance/Makefile`

**Step 1: Write `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: compliance
          POSTGRES_PASSWORD: compliance
          POSTGRES_DB: compliance
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Lint
        run: |
          ruff check src/ tests/
          mypy src/

      - name: Test
        run: |
          pytest -v --cov=src --cov-report=xml
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          REDIS_URL: redis://localhost:6379/0
          DATABASE_URL: postgresql+asyncpg://compliance:compliance@localhost:5432/compliance

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

**Step 2: Write `Makefile`**

```makefile
.PHONY: install test lint run docker-up docker-down

install:
	pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check src/ tests/
	mypy src/

run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker compose up -d

docker-down:
	docker compose down -v
```

**Step 3: Commit**

```bash
git add .github/ Makefile
git commit -m "ci: add GitHub Actions workflow and Makefile"
```

---

## Summary

This implementation plan covers:

1. **Agent Architecture** — 6 specialized agents (Monitor, Detect, Respond, Report, Analytics, Orchestrator) with a registry pattern and pipeline routing
2. **Monitoring Agent** — Content ingestion from 6 channels with normalization
3. **Detection Agent** — Hybrid rule-based + LLM scanning with deduplication
4. **Response Agent** — Severity-based action determination (auto-reject, escalate, flag)
5. **Reporting Agent** — Daily summaries, violation details, and trend reports
6. **Performance Analytics Agent** — Metrics collection with counters, timers, and gauges
7. **Code Examples** — Complete, copy-pasteable code for every component
8. **Testing Strategy** — Unit tests, integration tests, and end-to-end pipeline tests

**Total: 12 tasks, ~40 files, 15+ test cases**

**Execution order:** Tasks 1→2→3→4→5→6→7→8→9→10→11→12 (each depends on previous)

**Estimated implementation time:** 4-6 hours with subagent-driven development
