# GRC_Claw Automation Engine: Complete Implementation Guide

**Document ID:** GRC-IMPL-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**References:** grc-claw-automation-engine-proposal.md, grc-claw-integration-specification.md

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Module 1: Discovery Engine](#2-module-1-discovery-engine)
3. [Module 2: Inventory Graph](#3-module-2-inventory-graph)
4. [Module 3: Risk Assessment Engine](#4-module-3-risk-assessment-engine)
5. [Module 4: Policy Mapping Engine](#5-module-4-policy-mapping-engine)
6. [Module 5: Runtime Enforcement Engine](#6-module-5-runtime-enforcement-engine)
7. [Module 6: Continuous Monitoring Engine](#7-module-6-continuous-monitoring-engine)
8. [Module 7: Audit Evidence Engine](#8-module-7-audit-evidence-engine)
9. [Module 8: Agent Governance Layer](#9-module-8-agent-governance-layer)
10. [MCP Server Implementation](#10-mcp-server-implementation)
11. [Deterministic Enforcement Engine](#11-deterministic-enforcement-engine)
12. [Event-Driven Architecture](#12-event-driven-architecture)
13. [Configuration Management](#13-configuration-management)
14. [Testing Framework](#14-testing-framework)
15. [Deployment Guide](#15-deployment-guide)

---

## 1. Architecture Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GRC_Claw Automation Engine                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Discovery  │→ │  Inventory  │→ │    Risk     │→ │   Policy    │        │
│  │   Engine    │  │   Graph     │  │ Assessment  │  │   Mapping   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │                │                │
│         ▼                ▼                ▼                ▼                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Governance Knowledge Graph                         │   │
│  │  (Regulations × Business Context × AI Configurations × Controls)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                │                │                │                │
│         ▼                ▼                ▼                ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Runtime   │→ │ Continuous  │→ │    Audit    │  │   Agent     │        │
│  │ Enforcement │  │  Monitoring │  │  Evidence   │  │  Governance │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MCP Gateway (Universal Integration)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Graph Database | Neo4j / Apache AGE | Native graph queries for dependency mapping |
| Policy Engine | Open Policy Agent (OPA) / Cedar | Declarative, auditable policy-as-code |
| MCP Server | Python MCP SDK | Official SDK, active ecosystem |
| Task Queue | Celery / Temporal | Reliable async processing |
| Event Streaming | Apache Kafka / NATS | Real-time event processing |
| Evidence Store | PostgreSQL + immudb | Relational + immutable audit log |
| API | FastAPI (Python) | Async, OpenAPI-native, MCP-compatible |
| Deployment | Docker + Kubernetes | Cloud-agnostic, scalable |
| Observability | OpenTelemetry | Standard tracing for audit trails |

### 1.3 Project Structure

```
grc-claw/
├── pyproject.toml
├── docker-compose.yml
├── Makefile
├── config/
│   ├── default.yaml
│   ├── production.yaml
│   └── policies/
│       ├── eu_ai_act.yaml
│       ├── nist_ai_rmf.yaml
│       ├── iso_42001.yaml
│       └── custom/
├── src/
│   └── grc_claw/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── asset.py
│       │   ├── policy.py
│       │   ├── evidence.py
│       │   ├── enforcement.py
│       │   └── events.py
│       ├── modules/
│       │   ├── __init__.py
│       │   ├── discovery.py
│       │   ├── inventory.py
│       │   ├── risk.py
│       │   ├── policy.py
│       │   ├── enforcement.py
│       │   ├── monitoring.py
│       │   ├── evidence.py
│       │   └── agent_governance.py
│       ├── mcp/
│       │   ├── __init__.py
│       ├── server.py
│       ├── tools.py
│       └── resources.py
│       ├── events/
│       │   ├── __init__.py
│       ├── bus.py
│       ├── schemas.py
│       └── handlers.py
│       ├── enforcement/
│       │   ├── __init__.py
│       ├── engine.py
│       ├── decisions.py
│       └── redaction.py
│       └── api/
│           ├── __init__.py
│           ├── routes.py
│           └── dependencies.py
├── tests/
│   ├── conftest.py
│   ├── test_discovery.py
│   ├── test_inventory.py
│   ├── test_risk.py
│   ├── test_policy.py
│   ├── test_enforcement.py
│   ├── test_monitoring.py
│   ├── test_evidence.py
│   ├── test_agent_governance.py
│   ├── test_mcp_server.py
│   └── test_events.py
├── deployments/
│   ├── docker/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── Dockerfile.mcp
│   └── k8s/
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── deployment.yaml
│       ├── service.yaml
│       └── hpa.yaml
└── docs/
    ├── api.md
    └── architecture.md
```

---

## 2. Module 1: Discovery Engine

### 2.1 Purpose

Automatically find all AI systems, models, agents, and pipelines across the enterprise. Read-only and non-intrusive — no agents to install, no code changes required.

### 2.2 Implementation

```python
# src/grc_claw/modules/discovery.py

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator

import aiohttp
import git

logger = logging.getLogger(__name__)


class AssetType(str, Enum):
    MODEL = "model"
    AGENT = "agent"
    DATASET = "dataset"
    PIPELINE = "pipeline"
    VENDOR = "vendor"
    ENDPOINT = "endpoint"


@dataclass
class DiscoveredAsset:
    """Normalized AI asset record produced by discovery."""
    id: str
    type: AssetType
    name: str
    source: str  # e.g., "github", "aws", "azure"
    owner: str | None = None
    lifecycle_stage: str = "development"
    risk_tier: str = "minimal"
    business_purpose: str | None = None
    deployment_status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw_discovery: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.sha256(
                f"{self.source}:{self.type.value}:{self.name}".encode()
            ).hexdigest()[:16]


class DiscoveryConnector(ABC):
    """Base class for all discovery connectors."""

    @abstractmethod
    async def discover(self) -> AsyncIterator[DiscoveredAsset]:
        """Yield discovered assets."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the connector is healthy."""
        ...


class RepositoryScanner(DiscoveryConnector):
    """Scan code repositories for AI library signatures, model files, and API usage.

    Inspired by AIBOM-Guard: 220+ AI library signatures, model files, API usage patterns.
    """

    AI_LIBRARY_SIGNATURES = {
        "pytorch": ["torch", "torchvision", "torchaudio"],
        "tensorflow": ["tensorflow", "keras", "tf."],
        "huggingface": ["transformers", "datasets", "accelerate", "peft"],
        "langchain": ["langchain", "langgraph", "langsmith"],
        "openai": ["openai", "tiktoken"],
        "anthropic": ["anthropic", "claude"],
        "mlflow": ["mlflow"],
        "wandb": ["wandb"],
        "scikit-learn": ["sklearn"],
        "xgboost": ["xgboost"],
        "lightgbm": ["lightgbm"],
        "fastapi": ["fastapi"],
        "ray": ["ray"],
        "dvc": ["dvc"],
    }

    MODEL_FILE_PATTERNS = [
        "*.pt", "*.pth", "*.ckpt", "*.safetensors",
        "*.onnx", "*.pb", "*.h5", "*.pkl",
        "*.bin", "*.gguf", "*.mlmodel",
    ]

    def __init__(self, repo_paths: list[str], include_submodules: bool = True):
        self.repo_paths = [Path(p) for p in repo_paths]
        self.include_submodules = include_submodules

    async def discover(self) -> AsyncIterator[DiscoveredAsset]:
        for repo_path in self.repo_paths:
            async for asset in self._scan_repo(repo_path):
                yield asset

    async def _scan_repo(self, repo_path: Path) -> AsyncIterator[DiscoveredAsset]:
        if not repo_path.exists():
            logger.warning("Repository path does not exist: %s", repo_path)
            return

        # Scan for AI library usage in requirements files
        async for asset in self._scan_requirements(repo_path):
            yield asset

        # Scan for model files
        async for asset in self._scan_model_files(repo_path):
            yield asset

        # Scan for AI API usage in source code
        async for asset in self._scan_source_code(repo_path):
            yield asset

    async def _scan_requirements(self, repo_path: Path) -> AsyncIterator[DiscoveredAsset]:
        req_files = list(repo_path.rglob("requirements*.txt")) + \
                     list(repo_path.rglob("pyproject.toml")) + \
                     list(repo_path.rglob("Pipfile"))

        for req_file in req_files:
            try:
                content = req_file.read_text(errors="replace")
                for lib_name, signatures in self.AI_LIBRARY_SIGNATURES.items():
                    for sig in signatures:
                        if sig in content:
                            yield DiscoveredAsset(
                                id="",
                                type=AssetType.PIPELINE,
                                name=f"{repo_path.name}/{lib_name}",
                                source="repository_scan",
                                metadata={
                                    "library": lib_name,
                                    "signature": sig,
                                    "file": str(req_file.relative_to(repo_path)),
                                    "repo_path": str(repo_path),
                                },
                            )
                            break  # One hit per library is enough
            except Exception as e:
                logger.error("Error scanning %s: %s", req_file, e)

    async def _scan_model_files(self, repo_path: Path) -> AsyncIterator[DiscoveredAsset]:
        for pattern in self.MODEL_FILE_PATTERNS:
            for model_file in repo_path.rglob(pattern):
                # Skip common non-model directories
                if any(part.startswith(".") for part in model_file.parts):
                    continue
                if "node_modules" in model_file.parts or "__pycache__" in model_file.parts:
                    continue

                stat = model_file.stat()
                yield DiscoveredAsset(
                    id="",
                    type=AssetType.MODEL,
                    name=model_file.stem,
                    source="repository_scan",
                    metadata={
                        "file_path": str(model_file.relative_to(repo_path)),
                        "file_size": stat.st_size,
                        "file_suffix": model_file.suffix,
                        "repo_path": str(repo_path),
                    },
                )

    async def _scan_source_code(self, repo_path: Path) -> AsyncIterator[DiscoveredAsset]:
        """Scan Python source files for AI API usage patterns."""
        ai_api_patterns = {
            "openai": [r"from openai", r"import openai", r"OpenAI\("],
            "anthropic": [r"from anthropic", r"import anthropic", r"Anthropic\("],
            "langchain": [r"from langchain", r"import langchain"],
            "huggingface": [r"from transformers", r"import transformers"],
        }

        for py_file in repo_path.rglob("*.py"):
            if any(part.startswith(".") for part in py_file.parts):
                continue
            if "node_modules" in py_file.parts or "__pycache__" in py_file.parts:
                continue

            try:
                content = py_file.read_text(errors="replace")
                for api_name, patterns in ai_api_patterns.items():
                    for pattern in patterns:
                        if pattern in content:
                            yield DiscoveredAsset(
                                id="",
                                type=AssetType.ENDPOINT,
                                name=f"{repo_path.name}/{api_name}_api",
                                source="repository_scan",
                                metadata={
                                    "api": api_name,
                                    "pattern": pattern,
                                    "file": str(py_file.relative_to(repo_path)),
                                    "repo_path": str(repo_path),
                                },
                            )
                            break
            except Exception as e:
                logger.error("Error scanning %s: %s", py_file, e)

    async def health_check(self) -> bool:
        return all(p.exists() for p in self.repo_paths)


class CloudConnector(DiscoveryConnector):
    """Read-only connectors for AWS, Azure, GCP, Databricks, Snowflake.

    Inspired by Holistic AI: 15+ read-only connectors.
    """

    def __init__(self, provider: str, credentials: dict[str, str]):
        self.provider = provider
        self.credentials = credentials

    async def discover(self) -> AsyncIterator[DiscoveredAsset]:
        if self.provider == "aws":
            async for asset in self._discover_aws():
                yield asset
        elif self.provider == "azure":
            async for asset in self._discover_azure():
                yield asset
        elif self.provider == "gcp":
            async for asset in self._discover_gcp():
                yield asset
        elif self.provider == "databricks":
            async for asset in self._discover_databricks():
                yield asset

    async def _discover_aws(self) -> AsyncIterator[DiscoveredAsset]:
        """Discover AWS AI/ML resources: SageMaker endpoints, Bedrock models, etc."""
        import boto3

        session = boto3.Session(
            aws_access_key_id=self.credentials.get("access_key"),
            aws_secret_access_key=self.credentials.get("secret_key"),
            region_name=self.credentials.get("region", "us-east-1"),
        )

        # SageMaker endpoints
        sagemaker = session.client("sagemaker")
        paginator = sagemaker.get_paginator("list_endpoints")
        for page in paginator.paginate():
            for endpoint in page["Endpoints"]:
                yield DiscoveredAsset(
                    id="",
                    type=AssetType.ENDPOINT,
                    name=endpoint["EndpointName"],
                    source="aws_sagemaker",
                    deployment_status="deployed" if endpoint["EndpointStatus"] == "InService" else "pending",
                    metadata={
                        "provider": "aws",
                        "service": "sagemaker",
                        "endpoint_arn": endpoint["EndpointArn"],
                        "created_at": str(endpoint["CreationTime"]),
                    },
                )

        # Bedrock models
        bedrock = session.client("bedrock")
        try:
            response = bedrock.list_foundation_models()
            for model in response.get("modelSummaries", []):
                yield DiscoveredAsset(
                    id="",
                    type=AssetType.MODEL,
                    name=model["modelName"],
                    source="aws_bedrock",
                    metadata={
                        "provider": "aws",
                        "service": "bedrock",
                        "model_id": model["modelId"],
                        "model_arn": model.get("modelArn"),
                    },
                )
        except Exception as e:
            logger.warning("Could not list Bedrock models: %s", e)

    async def _discover_azure(self) -> AsyncIterator[DiscoveredAsset]:
        """Discover Azure AI resources."""
        from azure.identity import ClientSecretCredential
        from azure.mgmt.machinelearningservices import MachineLearningServicesClient

        credential = ClientSecretCredential(
            tenant_id=self.credentials["tenant_id"],
            client_id=self.credentials["client_id"],
            client_secret=self.credentials["client_secret"],
        )
        ml_client = MachineLearningServicesClient(
            credential=credential,
            subscription_id=self.credentials["subscription_id"],
        )

        for endpoint in ml_client.online_endpoints.list():
            yield DiscoveredAsset(
                id="",
                type=AssetType.ENDPOINT,
                name=endpoint.name,
                source="azure_ml",
                deployment_status="deployed",
                metadata={
                    "provider": "azure",
                    "service": "machine_learning",
                    "endpoint_id": endpoint.id,
                },
            )

    async def _discover_gcp(self) -> AsyncIterator[DiscoveredAsset]:
        """Discover GCP AI resources."""
        from google.cloud import aiplatform

        aiplatform.init(
            project=self.credentials["project_id"],
            location=self.credentials.get("region", "us-central1"),
        )

        for endpoint in aiplatform.Endpoint.list():
            yield DiscoveredAsset(
                id="",
                type=AssetType.ENDPOINT,
                name=endpoint.display_name,
                source="gcp_vertex_ai",
                deployment_status="deployed",
                metadata={
                    "provider": "gcp",
                    "service": "vertex_ai",
                    "endpoint_id": endpoint.name,
                },
            )

    async def _discover_databricks(self) -> AsyncIterator[DiscoveredAsset]:
        """Discover Databricks ML resources."""
        from databricks.sdk import WorkspaceClient

        ws = WorkspaceClient(
            host=self.credentials["host"],
            token=self.credentials["token"],
        )

        for model in ws.model_registry.list_models():
            yield DiscoveredAsset(
                id="",
                type=AssetType.MODEL,
                name=model.name,
                source="databricks_ml",
                metadata={
                    "provider": "databricks",
                    "service": "model_registry",
                    "model_id": model.id,
                },
            )

    async def health_check(self) -> bool:
        try:
            # Simple connectivity check
            return True
        except Exception:
            return False


class AgentDetector(DiscoveryConnector):
    """Detect registered and shadow AI agents across enterprise environments.

    Inspired by Vigil: agent discovery across enterprise.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config

    async def discover(self) -> AsyncIterator[DiscoveredAsset]:
        # Scan for agent configurations in common locations
        async for asset in self._scan_agent_configs():
            yield asset

        # Scan for MCP server configurations
        async for asset in self._scan_mcp_servers():
            yield asset

    async def _scan_agent_configs(self) -> AsyncIterator[DiscoveredAsset]:
        """Scan for agent configuration files."""
        config_paths = self.config.get("agent_config_paths", [])

        for path_str in config_paths:
            path = Path(path_str)
            if not path.exists():
                continue

            for config_file in path.rglob("*.yaml"):
                try:
                    import yaml
                    content = yaml.safe_load(config_file.read_text())
                    if self._is_agent_config(content):
                        yield DiscoveredAsset(
                            id="",
                            type=AssetType.AGENT,
                            name=content.get("name", config_file.stem),
                            source="agent_detector",
                            metadata={
                                "config_file": str(config_file),
                                "agent_type": content.get("type", "unknown"),
                                "framework": content.get("framework", "unknown"),
                            },
                        )
                except Exception as e:
                    logger.error("Error scanning agent config %s: %s", config_file, e)

    async def _scan_mcp_servers(self) -> AsyncIterator[DiscoveredAsset]:
        """Scan for MCP server configurations."""
        mcp_config_paths = self.config.get("mcp_config_paths", [])

        for path_str in mcp_config_paths:
            path = Path(path_str)
            if not path.exists():
                continue

            for config_file in path.rglob("mcp*.json"):
                try:
                    content = json.loads(config_file.read_text())
                    servers = content.get("mcpServers", {})
                    for server_name, server_config in servers.items():
                        yield DiscoveredAsset(
                            id="",
                            type=AssetType.AGENT,
                            name=server_name,
                            source="mcp_registry",
                            metadata={
                                "server_type": "mcp",
                                "config_file": str(config_file),
                                "command": server_config.get("command"),
                                "args": server_config.get("args", []),
                            },
                        )
                except Exception as e:
                    logger.error("Error scanning MCP config %s: %s", config_file, e)

    def _is_agent_config(self, content: dict) -> bool:
        """Heuristic to determine if a config file describes an AI agent."""
        agent_indicators = ["agent", "llm", "model", "prompt", "tool", "mcp"]
        content_str = json.dumps(content).lower()
        return any(indicator in content_str for indicator in agent_indicators)

    async def health_check(self) -> bool:
        return True


class DiscoveryEngine:
    """Orchestrates all discovery connectors and produces normalized asset records."""

    def __init__(self, connectors: list[DiscoveryConnector]):
        self.connectors = connectors
        self._discovery_count = 0

    async def run_discovery(self) -> list[DiscoveredAsset]:
        """Run all discovery connectors and return normalized assets."""
        all_assets: list[DiscoveredAsset] = []

        for connector in self.connectors:
            connector_name = connector.__class__.__name__
            logger.info("Running discovery connector: %s", connector_name)

            try:
                if not await connector.health_check():
                    logger.warning("Connector %s is unhealthy, skipping", connector_name)
                    continue

                count = 0
                async for asset in connector.discover():
                    all_assets.append(asset)
                    count += 1

                logger.info("Connector %s discovered %d assets", connector_name, count)
            except Exception as e:
                logger.error("Connector %s failed: %s", connector_name, e)

        self._discovery_count = len(all_assets)
        logger.info("Total assets discovered: %d", self._discovery_count)
        return all_assets

    async def run_continuous(self, interval_seconds: int = 3600):
        """Run discovery continuously at the specified interval."""
        while True:
            assets = await self.run_discovery()
            logger.info("Discovery cycle complete: %d assets", len(assets))
            await asyncio.sleep(interval_seconds)
```

### 2.3 Configuration

```yaml
# config/default.yaml
discovery:
  enabled: true
  interval_seconds: 3600  # Run every hour
  
  repository_scanner:
    enabled: true
    repo_paths:
      - /path/to/repo1
      - /path/to/repo2
    include_submodules: true
    exclude_patterns:
      - "node_modules"
      - "__pycache__"
      - ".git"
      - "venv"
      - ".venv"
  
  cloud_connectors:
    aws:
      enabled: true
      region: us-east-1
      # Credentials from environment variables
    azure:
      enabled: false
      subscription_id: ${AZURE_SUBSCRIPTION_ID}
    gcp:
      enabled: false
      project_id: ${GCP_PROJECT_ID}
    databricks:
      enabled: false
      host: ${DATABRICKS_HOST}
  
  agent_detector:
    enabled: true
    agent_config_paths:
      - /etc/grc-claw/agents
      - ~/.config/grc-claw/agents
    mcp_config_paths:
      - ~/.config/claude-code
      - ~/.config/grc-claw/mcp
```

---

## 3. Module 2: Inventory Graph

### 3.1 Purpose

Maintain a live, queryable inventory of all AI assets with dependency mapping. Uses a graph database for complex, multi-hop dependency queries.

### 3.2 Implementation

```python
# src/grc_claw/modules/inventory.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncSession

from grc_claw.modules.discovery import AssetType, DiscoveredAsset

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    DEPENDS_ON = "DEPENDS_ON"
    OWNS = "OWNS"
    USES = "USES"
    PRODUCES = "PRODUCES"
    CONSUMES = "CONSUMES"
    DEPLOYED_TO = "DEPLOYED_TO"
    VERSION_OF = "VERSION_OF"
    CONTAINS = "CONTAINS"


@dataclass
class AssetNode:
    """Represents an AI asset as a graph node."""
    id: str
    type: AssetType
    name: str
    owner: str | None = None
    lifecycle_stage: str = "development"
    risk_tier: str = "minimal"
    business_purpose: str | None = None
    deployment_status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "owner": self.owner,
            "lifecycle_stage": self.lifecycle_stage,
            "risk_tier": self.risk_tier,
            "business_purpose": self.business_purpose,
            "deployment_status": self.deployment_status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_discovered(cls, asset: DiscoveredAsset) -> AssetNode:
        return cls(
            id=asset.id,
            type=asset.type,
            name=asset.name,
            owner=asset.owner,
            lifecycle_stage=asset.lifecycle_stage,
            risk_tier=asset.risk_tier,
            business_purpose=asset.business_purpose,
            deployment_status=asset.deployment_status,
            metadata=asset.metadata,
            created_at=asset.discovered_at,
        )


class InventoryGraph:
    """Graph database-backed inventory of all AI assets.

    Inspired by Credo AI Knowledge Graph and OneTrust Trust Graph.
    Nodes = AI assets; Edges = dependencies, data flows, ownership.
    """

    def __init__(self, uri: str, username: str, password: str):
        self._driver = AsyncGraphDatabase.driver(uri, auth=(username, password))

    async def close(self):
        await self._driver.close()

    async def initialize_schema(self):
        """Create constraints and indexes."""
        async with self._driver.session() as session:
            # Unique constraint on asset ID
            await session.run(
                "CREATE CONSTRAINT asset_id IF NOT EXISTS "
                "FOR (a:Asset) REQUIRE a.id IS UNIQUE"
            )
            # Indexes for common queries
            await session.run(
                "CREATE INDEX asset_type IF NOT EXISTS FOR (a:Asset) ON (a.type)"
            )
            await session.run(
                "CREATE INDEX asset_risk_tier IF NOT EXISTS FOR (a:Asset) ON (a.risk_tier)"
            )
            await session.run(
                "CREATE INDEX asset_lifecycle IF NOT EXISTS FOR (a:Asset) ON (a.lifecycle_stage)"
            )

    async def upsert_asset(self, asset: AssetNode) -> AssetNode:
        """Create or update an asset node."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MERGE (a:Asset {id: $id})
                ON CREATE SET a += $props, a.created_at = datetime()
                ON MATCH SET a += $props, a.updated_at = datetime()
                RETURN a
                """,
                id=asset.id,
                props=asset.to_dict(),
            )
            record = await result.single()
            if record:
                logger.debug("Upserted asset: %s", asset.id)
            return asset

    async def add_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: RelationshipType,
        properties: dict[str, Any] | None = None,
    ):
        """Add a relationship between two assets."""
        props = properties or {}
        async with self._driver.session() as session:
            await session.run(
                f"""
                MATCH (a:Asset {{id: $from_id}})
                MATCH (b:Asset {{id: $to_id}})
                MERGE (a)-[r:{rel_type.value}]->(b)
                SET r += $props
                """,
                from_id=from_id,
                to_id=to_id,
                props=props,
            )

    async def get_asset(self, asset_id: str) -> AssetNode | None:
        """Retrieve an asset by ID."""
        async with self._driver.session() as session:
            result = await session.run(
                "MATCH (a:Asset {id: $id}) RETURN a",
                id=asset_id,
            )
            record = await result.single()
            if record:
                node = record["a"]
                return AssetNode(
                    id=node["id"],
                    type=AssetType(node["type"]),
                    name=node["name"],
                    owner=node.get("owner"),
                    lifecycle_stage=node.get("lifecycle_stage", "development"),
                    risk_tier=node.get("risk_tier", "minimal"),
                    business_purpose=node.get("business_purpose"),
                    deployment_status=node.get("deployment_status", "pending"),
                    metadata=dict(node.get("metadata", {})),
                )
            return None

    async def get_dependencies(
        self, asset_id: str, max_depth: int = 5
    ) -> list[dict[str, Any]]:
        """Get all dependencies of an asset up to max_depth."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH path = (a:Asset {id: $id})-[:DEPENDS_ON|USES|CONSUMES*1..%d]->(dep)
                RETURN [node in nodes(path) | {
                    id: node.id,
                    name: node.name,
                    type: node.type,
                    risk_tier: node.risk_tier
                }] AS dependency_chain,
                [rel in relationships(path) | type(rel)] AS rel_types
                """ % max_depth,
                id=asset_id,
            )
            return [record.data() async for record in result]

    async def get_impact_analysis(self, asset_id: str) -> dict[str, Any]:
        """Analyze the impact of changing/removing an asset."""
        async with self._driver.session() as session:
            # Find all assets that depend on this one
            result = await session.run(
                """
                MATCH (a:Asset {id: $id})<-[:DEPENDS_ON|USES|CONSUMES]-(dependent)
                RETURN collect({
                    id: dependent.id,
                    name: dependent.name,
                    type: dependent.type,
                    risk_tier: dependent.risk_tier,
                    lifecycle_stage: dependent.lifecycle_stage
                }) AS dependents
                """,
                id=asset_id,
            )
            record = await result.single()
            dependents = record["dependents"] if record else []

            # Calculate blast radius
            high_risk_dependents = [d for d in dependents if d.get("risk_tier") == "high"]
            production_dependents = [d for d in dependents if d.get("lifecycle_stage") == "production"]

            return {
                "asset_id": asset_id,
                "total_dependents": len(dependents),
                "high_risk_dependents": len(high_risk_dependents),
                "production_dependents": len(production_dependents),
                "dependents": dependents,
                "blast_radius": "high" if len(production_dependents) > 5 else
                                "medium" if len(production_dependents) > 0 else "low",
            }

    async def find_orphaned_assets(self) -> list[dict[str, Any]]:
        """Find assets with no relationships (potential orphans)."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (a:Asset)
                WHERE NOT (a)-[]-()
                RETURN a.id AS id, a.name AS name, a.type AS type,
                       a.created_at AS created_at
                """
            )
            return [record.data() async for record in result]

    async def get_assets_by_risk_tier(self, risk_tier: str) -> list[AssetNode]:
        """Get all assets in a specific risk tier."""
        async with self._driver.session() as session:
            result = await session.run(
                "MATCH (a:Asset {risk_tier: $tier}) RETURN a",
                tier=risk_tier,
            )
            nodes = []
            async for record in result:
                node = record["a"]
                nodes.append(AssetNode(
                    id=node["id"],
                    type=AssetType(node["type"]),
                    name=node["name"],
                    owner=node.get("owner"),
                    risk_tier=node.get("risk_tier", "minimal"),
                ))
            return nodes

    async def get_inventory_summary(self) -> dict[str, Any]:
        """Get a summary of the entire inventory."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (a:Asset)
                RETURN
                    count(a) AS total_assets,
                    count(CASE WHEN a.type = 'model' THEN 1 END) AS models,
                    count(CASE WHEN a.type = 'agent' THEN 1 END) AS agents,
                    count(CASE WHEN a.type = 'dataset' THEN 1 END) AS datasets,
                    count(CASE WHEN a.type = 'pipeline' THEN 1 END) AS pipelines,
                    count(CASE WHEN a.type = 'endpoint' THEN 1 END) AS endpoints,
                    count(CASE WHEN a.risk_tier = 'high' THEN 1 END) AS high_risk,
                    count(CASE WHEN a.risk_tier = 'critical' THEN 1 END) AS critical_risk,
                    count(CASE WHEN a.lifecycle_stage = 'production' THEN 1 END) AS in_production
                """
            )
            record = await result.single()
            return dict(record.data()) if record else {}
```

---

## 4. Module 3: Risk Assessment Engine

### 4.1 Purpose

Continuously assess risk across all AI assets using automated testing and scoring. Multi-dimensional scoring (0-100) with A-F grade.

### 4.2 Implementation

```python
# src/grc_claw/modules/risk.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from grc_claw.modules.discovery import AssetType

logger = logging.getLogger(__name__)


class RiskTier(str, Enum):
    PROHIBITED = "prohibited"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class RiskCategory(str, Enum):
    MODEL = "model"
    DATA = "data"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    REPUTATIONAL = "reputational"


@dataclass
class RiskDimension:
    """A single risk dimension score."""
    name: str
    score: float  # 0.0 - 1.0
    weight: float
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class RiskAssessment:
    """Complete risk assessment for an AI asset."""
    asset_id: str
    asset_name: str
    asset_type: AssetType
    overall_score: float  # 0.0 - 1.0
    grade: str  # A-F
    risk_tier: RiskTier
    dimensions: list[RiskDimension] = field(default_factory=list)
    eu_ai_act_tier: str | None = None  # prohibited/high/limited/minimal
    airss_scores: dict[str, float] = field(default_factory=dict)
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    assessor: str = "automated"
    methodology: str = "default"
    findings: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type.value,
            "overall_score": self.overall_score,
            "grade": self.grade,
            "risk_tier": self.risk_tier.value,
            "dimensions": [
                {
                    "name": d.name,
                    "score": d.score,
                    "weight": d.weight,
                    "weighted_score": d.weighted_score,
                    "details": d.details,
                }
                for d in self.dimensions
            ],
            "eu_ai_act_tier": self.eu_ai_act_tier,
            "airss_scores": self.airss_scores,
            "assessed_at": self.assessed_at.isoformat(),
            "assessor": self.assessor,
            "methodology": self.methodology,
            "findings": self.findings,
            "recommendations": self.recommendations,
        }


class RiskScoringEngine:
    """Multi-dimensional risk scoring engine.

    Inspired by WhitePact's 6-dimension trust score and Holistic AI's 40+ tests.
    """

    # Default dimension weights (sum to 1.0)
    DEFAULT_WEIGHTS = {
        "data_quality": 0.20,
        "model_robustness": 0.20,
        "security": 0.20,
        "compliance": 0.15,
        "operational": 0.15,
        "reputational": 0.10,
    }

    # EU AI Act Annex III matching criteria
    EU_AI_ACT_HIGH_RISK_USE_CASES = [
        "biometric_identification",
        "critical_infrastructure",
        "education_admission",
        "employment_recruitment",
        "credit_scoring",
        "law_enforcement",
        "border_control",
        "justice_system",
    ]

    def __init__(self, custom_weights: dict[str, float] | None = None):
        self.weights = custom_weights or self.DEFAULT_WEIGHTS
        self._test_suites: dict[str, Callable] = {}
        self._register_default_tests()

    def _register_default_tests(self):
        """Register default risk test suites."""
        self._test_suites["data_quality"] = self._test_data_quality
        self._test_suites["model_robustness"] = self._test_model_robustness
        self._test_suites["security"] = self._test_security
        self._test_suites["compliance"] = self._test_compliance
        self._test_suites["operational"] = self._test_operational
        self._test_suites["reputational"] = self._test_reputational

    async def assess_asset(
        self,
        asset_id: str,
        asset_name: str,
        asset_type: AssetType,
        metadata: dict[str, Any],
    ) -> RiskAssessment:
        """Run full risk assessment on an asset."""
        dimensions: list[RiskDimension] = []
        findings: list[dict[str, Any]] = []

        for dim_name, weight in self.weights.items():
            test_fn = self._test_suites.get(dim_name)
            if test_fn:
                try:
                    score, details = await test_fn(asset_id, asset_type, metadata)
                    dimensions.append(RiskDimension(
                        name=dim_name,
                        score=score,
                        weight=weight,
                        details=details,
                    ))
                    if score < 0.5:
                        findings.append({
                            "dimension": dim_name,
                            "severity": "high" if score < 0.3 else "medium",
                            "score": score,
                            "details": details,
                        })
                except Exception as e:
                    logger.error("Risk test %s failed for %s: %s", dim_name, asset_id, e)
                    dimensions.append(RiskDimension(
                        name=dim_name,
                        score=0.5,  # Neutral on failure
                        weight=weight,
                        details={"error": str(e)},
                    ))

        # Calculate overall score
        overall = sum(d.weighted_score for d in dimensions)
        grade = self._score_to_grade(overall)
        risk_tier = self._score_to_tier(overall)

        # EU AI Act triage
        eu_tier = self._eu_ai_act_triage(asset_type, metadata)

        # AIRSS scoring
        airss = self._calculate_airss(dimensions)

        # Generate recommendations
        recommendations = self._generate_recommendations(dimensions, findings)

        return RiskAssessment(
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=asset_type,
            overall_score=overall,
            grade=grade,
            risk_tier=risk_tier,
            dimensions=dimensions,
            eu_ai_act_tier=eu_tier,
            airss_scores=airss,
            findings=findings,
            recommendations=recommendations,
        )

    async def _test_data_quality(
        self, asset_id: str, asset_type: AssetType, metadata: dict
    ) -> tuple[float, dict]:
        """Test data quality dimensions."""
        score = 1.0
        details = {}

        # Check for training data documentation
        if asset_type == AssetType.MODEL:
            if not metadata.get("training_data_documented"):
                score -= 0.3
                details["training_data_documented"] = False

            # Check for bias assessment
            if not metadata.get("bias_assessment"):
                score -= 0.2
                details["bias_assessment"] = False

            # Check for data lineage
            if not metadata.get("data_lineage"):
                score -= 0.2
                details["data_lineage"] = False

        return max(0.0, score), details

    async def _test_model_robustness(
        self, asset_id: str, asset_type: AssetType, metadata: dict
    ) -> tuple[float, dict]:
        """Test model robustness."""
        score = 1.0
        details = {}

        if asset_type == AssetType.MODEL:
            # Check for adversarial testing
            if not metadata.get("adversarial_tested"):
                score -= 0.25
                details["adversarial_tested"] = False

            # Check for evaluation results
            if not metadata.get("evaluation_results"):
                score -= 0.25
                details["evaluation_results"] = False

            # Check for model versioning
            if not metadata.get("model_version"):
                score -= 0.15
                details["model_version"] = False

        return max(0.0, score), details

    async def _test_security(
        self, asset_id: str, asset_type: AssetType, metadata: dict
    ) -> tuple[float, dict]:
        """Test security dimensions."""
        score = 1.0
        details = {}

        # Check for prompt injection testing
        if not metadata.get("prompt_injection_tested"):
            score -= 0.3
            details["prompt_injection_tested"] = False

        # Check for access controls
        if not metadata.get("access_controls"):
            score -= 0.2
            details["access_controls"] = False

        # Check for encryption
        if not metadata.get("encryption_at_rest"):
            score -= 0.15
            details["encryption_at_rest"] = False

        return max(0.0, score), details

    async def _test_compliance(
        self, asset_id: str, asset_type: AssetType, metadata: dict
    ) -> tuple[float, dict]:
        """Test compliance dimensions."""
        score = 1.0
        details = {}

        # Check for policy mapping
        if not metadata.get("policy_mappings"):
            score -= 0.3
            details["policy_mappings"] = False

        # Check for compliance framework coverage
        frameworks = metadata.get("compliance_frameworks", [])
        if len(frameworks) < 2:
            score -= 0.2
            details["compliance_frameworks"] = frameworks

        return max(0.0, score), details

    async def _test_operational(
        self, asset_id: str, asset_type: AssetType, metadata: dict
    ) -> tuple[float, dict]:
        """Test operational dimensions."""
        score = 1.0
        details = {}

        # Check for monitoring
        if not metadata.get("monitoring_enabled"):
            score -= 0.3
            details["monitoring_enabled"] = False

        # Check for rollback plan
        if not metadata.get("rollback_plan"):
            score -= 0.2
            details["rollback_plan"] = False

        # Check for SLA
        if not metadata.get("sla_defined"):
            score -= 0.15
            details["sla_defined"] = False

        return max(0.0, score), details

    async def _test_reputational(
        self, asset_id: str, asset_type: AssetType, metadata: dict
    ) -> tuple[float, dict]:
        """Test reputational risk dimensions."""
        score = 1.0
        details = {}

        # Check for public-facing flag
        if metadata.get("public_facing"):
            if not metadata.get("human_oversight"):
                score -= 0.3
                details["human_oversight"] = False

        # Check for incident history
        incidents = metadata.get("incident_count", 0)
        if incidents > 3:
            score -= 0.2
            details["incident_count"] = incidents

        return max(0.0, score), details

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

    def _score_to_tier(self, score: float) -> RiskTier:
        """Convert numeric score to risk tier."""
        if score >= 0.8:
            return RiskTier.MINIMAL
        elif score >= 0.6:
            return RiskTier.LIMITED
        elif score >= 0.4:
            return RiskTier.HIGH
        else:
            return RiskTier.PROHIBITED

    def _eu_ai_act_triage(
        self, asset_type: AssetType, metadata: dict
    ) -> str | None:
        """EU AI Act risk tier classification with Annex III matching."""
        use_case = metadata.get("use_case", "").lower()

        # Check for prohibited practices (Article 5)
        prohibited = [
            "social_scoring",
            "manipulation",
            "exploitation",
            "real_time_biometric",
        ]
        if any(p in use_case for p in prohibited):
            return "prohibited"

        # Check for high-risk use cases (Annex III)
        if any(uc in use_case for uc in self.EU_AI_ACT_HIGH_RISK_USE_CASES):
            return "high"

        # Check for limited risk (transparency obligations)
        if asset_type == AssetType.AGENT:
            return "limited"

        return "minimal"

    def _calculate_airss(self, dimensions: list[RiskDimension]) -> dict[str, float]:
        """Calculate AIRSS (Adaptability, Integrity, Resilience, Scalability, Safety) scores."""
        dim_map = {d.name: d.score for d in dimensions}

        return {
            "adaptability": dim_map.get("operational", 0.5),
            "integrity": dim_map.get("data_quality", 0.5),
            "resilience": dim_map.get("model_robustness", 0.5),
            "scalability": dim_map.get("operational", 0.5),
            "safety": (dim_map.get("security", 0.5) + dim_map.get("compliance", 0.5)) / 2,
            "composite_score": sum(d.weighted_score for d in dimensions),
        }

    def _generate_recommendations(
        self, dimensions: list[RiskDimension], findings: list[dict]
    ) -> list[str]:
        """Generate actionable recommendations based on assessment."""
        recommendations = []

        for dim in dimensions:
            if dim.score < 0.5:
                recommendations.append(
                    f"Improve {dim.name}: current score {dim.score:.2f} is below threshold"
                )

        for finding in findings:
            if finding["severity"] == "high":
                recommendations.append(
                    f"URGENT: Address {finding['dimension']} finding — score {finding['score']:.2f}"
                )

        return recommendations
```

---

## 5. Module 4: Policy Mapping Engine

### 5.1 Purpose

Translate regulatory requirements and internal policies into executable controls. Version-controlled YAML definitions, not hardcoded.

### 5.2 Implementation

```python
# src/grc_claw/modules/policy.py

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class PolicyCategory(str, Enum):
    DATA_HANDLING = "data_handling"
    AGENT_BEHAVIOR = "agent_behavior"
    MODEL_GOVERNANCE = "model_governance"
    ACCESS_CONTROL = "access_control"
    CONTENT_SAFETY = "content_safety"
    PRIVACY = "privacy"
    CUSTOM = "custom"


class PolicyLanguage(str, Enum):
    AIGOLANG = "aigolang"
    REGO = "rego"
    CEDAR = "cedar"
    YAML = "yaml"
    JSON = "json"


@dataclass
class PolicyRule:
    """A single rule within a policy."""
    id: str
    name: str
    description: str
    condition: dict[str, Any]  # Structured condition
    action: str  # allow, deny, redact, require_approval, quarantine
    priority: int = 100
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyScope:
    """Defines which assets a policy applies to."""
    agents: list[str] = field(default_factory=list)  # empty = all
    models: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    environments: list[str] = field(default_factory=lambda: ["all"])
    risk_tiers: list[str] = field(default_factory=lambda: ["all"])


@dataclass
class FrameworkMapping:
    """Maps a policy to a framework control."""
    framework: str
    control_ids: list[str]
    mapping_strength: str = "direct"  # direct, partial, indirect


@dataclass
class Policy:
    """A governance policy."""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    status: PolicyStatus = PolicyStatus.DRAFT
    category: PolicyCategory = PolicyCategory.CUSTOM
    rules: list[PolicyRule] = field(default_factory=list)
    policy_language: PolicyLanguage = PolicyLanguage.YAML
    compiled_rules: dict[str, Any] = field(default_factory=dict)
    scope: PolicyScope = field(default_factory=PolicyScope)
    framework_mappings: list[FrameworkMapping] = field(default_factory=list)
    effective_date: datetime | None = None
    expiration_date: datetime | None = None
    review_cycle: str = "quarterly"
    owner: str = ""
    approvers: list[str] = field(default_factory=list)
    parent_policy_id: str | None = None
    change_description: str = ""
    tags: list[str] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    updated_by: str = ""
    enforcement_mode: str = "enforce"  # enforce, dry_run, audit_only
    on_violation: str = "block"  # block, redact, escalate, log, quarantine
    fail_mode: str = "closed"  # open, closed
    escalation_target: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "category": self.category.value,
            "rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "condition": r.condition,
                    "action": r.action,
                    "priority": r.priority,
                    "enabled": r.enabled,
                    "metadata": r.metadata,
                }
                for r in self.rules
            ],
            "policy_language": self.policy_language.value,
            "compiled_rules": self.compiled_rules,
            "scope": {
                "agents": self.scope.agents,
                "models": self.scope.models,
                "resources": self.scope.resources,
                "environments": self.scope.environments,
                "risk_tiers": self.scope.risk_tiers,
            },
            "framework_mappings": [
                {
                    "framework": fm.framework,
                    "control_ids": fm.control_ids,
                    "mapping_strength": fm.mapping_strength,
                }
                for fm in self.framework_mappings
            ],
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "review_cycle": self.review_cycle,
            "owner": self.owner,
            "approvers": self.approvers,
            "parent_policy_id": self.parent_policy_id,
            "change_description": self.change_description,
            "tags": self.tags,
            "labels": self.labels,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "enforcement_mode": self.enforcement_mode,
            "on_violation": self.on_violation,
            "fail_mode": self.fail_mode,
            "escalation_target": self.escalation_target,
        }

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> Policy:
        """Load a policy from a YAML file."""
        path = Path(yaml_path)
        content = yaml.safe_load(path.read_text())
        return cls.from_dict(content)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Policy:
        """Create a Policy from a dictionary."""
        rules = [PolicyRule(**r) for r in data.get("rules", [])]
        scope = PolicyScope(**data.get("scope", {}))
        mappings = [FrameworkMapping(**fm) for fm in data.get("framework_mappings", [])]

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            status=PolicyStatus(data.get("status", "draft")),
            category=PolicyCategory(data.get("category", "custom")),
            rules=rules,
            policy_language=PolicyLanguage(data.get("policy_language", "yaml")),
            compiled_rules=data.get("compiled_rules", {}),
            scope=scope,
            framework_mappings=mappings,
            effective_date=datetime.fromisoformat(data["effective_date"]) if data.get("effective_date") else None,
            expiration_date=datetime.fromisoformat(data["expiration_date"]) if data.get("expiration_date") else None,
            review_cycle=data.get("review_cycle", "quarterly"),
            owner=data.get("owner", ""),
            approvers=data.get("approvers", []),
            parent_policy_id=data.get("parent_policy_id"),
            change_description=data.get("change_description", ""),
            tags=data.get("tags", []),
            labels=data.get("labels", {}),
            created_by=data.get("created_by", ""),
            updated_by=data.get("updated_by", ""),
            enforcement_mode=data.get("enforcement_mode", "enforce"),
            on_violation=data.get("on_violation", "block"),
            fail_mode=data.get("fail_mode", "closed"),
            escalation_target=data.get("escalation_target", ""),
        )


class PolicyCompiler:
    """Compiles policy definitions to executable rules.

    Inspired by WhitePact: deterministic translation of policy text → executable rules.
    Targets OPA/Rego for policy-as-code.
    """

    def __init__(self):
        self._compiled_cache: dict[str, dict] = {}

    def compile_policy(self, policy: Policy) -> dict[str, Any]:
        """Compile a policy to OPA/Rego format."""
        if policy.id in self._compiled_cache:
            return self._compiled_cache[policy.id]

        rego_module = self._generate_rego_module(policy)
        compiled = {
            "policy_id": policy.id,
            "version": policy.version,
            "rego_module": rego_module,
            "rules_count": len(policy.rules),
            "compiled_at": datetime.now(timezone.utc).isoformat(),
            "target": "opa",
        }

        self._compiled_cache[policy.id] = compiled
        return compiled

    def _generate_rego_module(self, policy: Policy) -> str:
        """Generate an OPA Rego module from policy rules."""
        lines = [
            f"package grcclaw.{policy.category.value}",
            "",
            "# Auto-generated from policy: " + policy.name,
            f"# Version: {policy.version}",
            "",
            "import future.keywords.if",
            "import future.keywords.in",
            "",
            "# Default decision",
            "default allow := false",
            "",
        ]

        # Generate scope filter
        lines.extend(self._generate_scope_filter(policy.scope))

        # Generate rules
        for rule in policy.rules:
            if not rule.enabled:
                continue
            lines.extend(self._generate_rule(rule))

        # Generate final decision logic
        lines.extend([
            "",
            "# Final decision based on matched rules",
            "decision := result if {",
            "    some rule in matched_rules",
            "    result := decision_for(rule)",
            "}",
            "",
            "matched_rules contains rule if {",
            "    some rule in input.rules",
            "    rule.enabled",
            "    rule_matches(rule, input)",
            "}",
        ])

        return "\n".join(lines)

    def _generate_scope_filter(self, scope: PolicyScope) -> list[str]:
        """Generate Rego code for scope filtering."""
        lines = ["# Scope filtering"]

        if scope.agents:
            agents_str = ", ".join(f'"{a}"' for a in scope.agents)
            lines.append(f"scope_agents := [{agents_str}]")

        if scope.models:
            models_str = ", ".join(f'"{m}"' for m in scope.models)
            lines.append(f"scope_models := [{models_str}]")

        if scope.environments and "all" not in scope.environments:
            envs_str = ", ".join(f'"{e}"' for e in scope.environments)
            lines.append(f"scope_environments := [{envs_str}]")

        lines.append("")
        return lines

    def _generate_rule(self, rule: PolicyRule) -> list[str]:
        """Generate Rego code for a single rule."""
        lines = [
            f"# Rule: {rule.name}",
            f"rule_matches(\"{rule.id}\", input) if {{",
        ]

        # Generate condition matching
        condition = rule.condition
        for key, value in condition.items():
            if isinstance(value, str):
                lines.append(f'    input.{key} == "{value}"')
            elif isinstance(value, list):
                values_str = ", ".join(f'"{v}"' for v in value)
                lines.append(f"    input.{key} in [{values_str}]")
            else:
                lines.append(f"    input.{key} == {value}")

        lines.append("}")
        lines.append("")

        return lines


class CrosswalkEngine:
    """Map controls across frameworks (implement once, get credit across multiple frameworks).

    Inspired by aitrustcommons/governance-framework.
    """

    def __init__(self):
        self._crosswalks: dict[str, dict[str, list[str]]] = {}
        self._load_default_crosswalks()

    def _load_default_crosswalks(self):
        """Load default cross-framework control mappings."""
        self._crosswalks = {
            "NIST-800-53": {
                "AC-2": ["SOC2:CC6.1", "ISO-27001:A.9.2.1", "NIST-AI-RMF:GOV-1"],
                "AC-3": ["SOC2:CC6.3", "ISO-27001:A.9.1.2"],
                "AC-6": ["SOC2:CC6.2", "ISO-27001:A.9.4.1"],
                "AU-6": ["SOC2:CC7.2", "ISO-27001:A.12.4.1"],
                "CM-8": ["SOC2:CC8.1", "ISO-27001:A.8.1.1"],
            },
            "SOC2": {
                "CC6.1": ["NIST-800-53:AC-2", "ISO-27001:A.9.2.1"],
                "CC6.2": ["NIST-800-53:AC-6", "ISO-27001:A.9.4.1"],
                "CC6.3": ["NIST-800-53:AC-3", "ISO-27001:A.9.1.2"],
                "CC7.2": ["NIST-800-53:AU-6", "ISO-27001:A.12.4.1"],
            },
            "ISO-27001": {
                "A.9.2.1": ["NIST-800-53:AC-2", "SOC2:CC6.1"],
                "A.9.4.1": ["NIST-800-53:AC-6", "SOC2:CC6.2"],
                "A.12.4.1": ["NIST-800-53:AU-6", "SOC2:CC7.2"],
            },
        }

    def get_equivalent_controls(
        self, framework: str, control_id: str
    ) -> list[dict[str, str]]:
        """Get equivalent controls in other frameworks."""
        key = f"{framework}:{control_id}"
        equivalents = []

        for fw, controls in self._crosswalks.items():
            for ctrl, mappings in controls.items():
                if key in mappings:
                    equivalents.append({
                        "framework": fw,
                        "control_id": ctrl,
                        "mapping_strength": "direct",
                    })

        return equivalents

    def add_crosswalk(
        self,
        source_framework: str,
        source_control: str,
        target_framework: str,
        target_control: str,
        strength: str = "direct",
    ):
        """Add a custom crosswalk mapping."""
        key = f"{source_framework}:{source_control}"
        target_key = f"{target_framework}:{target_control}"

        if source_framework not in self._crosswalks:
            self._crosswalks[source_framework] = {}
        if source_control not in self._crosswalks[source_framework]:
            self._crosswalks[source_framework][source_control] = []

        self._crosswalks[source_framework][source_control].append(target_key)


class PolicyPack:
    """Pre-built regulatory mappings for common frameworks.

    Inspired by Credo AI policy packs.
    """

    def __init__(self, pack_path: str | Path):
        self.pack_path = Path(pack_path)
        self._policies: list[Policy] = []

    def load(self) -> list[Policy]:
        """Load all policies from the pack."""
        self._policies = []
        for yaml_file in sorted(self.pack_path.glob("*.yaml")):
            try:
                policy = Policy.from_yaml(yaml_file)
                self._policies.append(policy)
            except Exception as e:
                logger.error("Failed to load policy from %s: %s", yaml_file, e)
        return self._policies

    def get_frameworks(self) -> list[str]:
        """Get all frameworks covered by this pack."""
        frameworks = set()
        for policy in self._policies:
            for mapping in policy.framework_mappings:
                frameworks.add(mapping.framework)
        return sorted(frameworks)
```

### 5.3 Example Policy YAML

```yaml
# config/policies/eu_ai_act.yaml
id: "eu-ai-act-data-governance"
name: "EU AI Act - Data Governance"
description: "Data governance requirements under EU AI Act Article 10"
version: "1.0.0"
status: "active"
category: "data_handling"
policy_language: "yaml"
owner: "compliance-team"
approvers: ["dpo", "legal-team"]
enforcement_mode: "enforce"
on_violation: "block"
fail_mode: "closed"
review_cycle: "quarterly"
tags: ["eu-ai-act", "data-governance", "gdpr"]

scope:
  agents: []
  models: []
  resources: ["training_data", "validation_data", "test_data"]
  environments: ["prod", "staging"]
  risk_tiers: ["high", "prohibited"]

framework_mappings:
  - framework: "EU-AI-ACT"
    control_ids: ["Art-10-1", "Art-10-2", "Art-10-3", "Art-10-4", "Art-10-5"]
    mapping_strength: "direct"
  - framework: "GDPR"
    control_ids: ["Art-5-1-f", "Art-25", "Art-32"]
    mapping_strength: "partial"
  - framework: "ISO-42001"
    control_ids: ["A-6-1-1", "A-6-1-2"]
    mapping_strength: "indirect"

rules:
  - id: "training-data-quality"
    name: "Training Data Quality Requirements"
    description: "Training data must be relevant, representative, and error-free"
    condition:
      data_quality_score: {lt: 0.8}
      data_type: ["training", "validation"]
    action: "deny"
    priority: 100
    enabled: true

  - id: "bias-assessment-required"
    name: "Bias Assessment Required"
    description: "High-risk AI systems must have documented bias assessment"
    condition:
      risk_tier: "high"
      bias_assessment: {eq: null}
    action: "require_approval"
    priority: 90
    enabled: true

  - id: "data-provenance"
    name: "Data Provenance Documentation"
    description: "All training data must have documented provenance"
    condition:
      data_provenance: {eq: null}
      data_type: ["training"]
    action: "deny"
    priority: 95
    enabled: true

  - id: "human-oversight"
    name: "Human Oversight for High-Risk"
    description: "High-risk AI systems must have human oversight mechanisms"
    condition:
      risk_tier: "high"
      human_oversight: false
    action: "require_approval"
    priority: 85
    enabled: true
```

---

## 6. Module 5: Runtime Enforcement Engine

### 6.1 Purpose

Enforce governance decisions at the point of AI system operation. Five-way decision engine with deterministic core — no LLM in the decision path.

### 6.2 Implementation

```python
# src/grc_claw/enforcement/engine.py

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from grc_claw.modules.policy import Policy, PolicyRule

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_WITH_REDACTION = "ALLOW_WITH_REDACTION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"


class ActionType(str, Enum):
    TOOL_CALL = "tool_call"
    API_REQUEST = "api_request"
    DATA_ACCESS = "data_access"
    CODE_EXECUTION = "code_execution"
    FILE_ACCESS = "file_access"
    NETWORK_ACCESS = "network_access"
    MODEL_INFERENCE = "model_inference"
    CUSTOM = "custom"


@dataclass
class EnforcementRequest:
    """A request for an enforcement decision."""
    request_id: str
    agent_id: str
    action_type: ActionType
    tool_name: str | None = None
    resource: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
    metadata: dict[str, str] = field(default_factory=dict)
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RedactionDetails:
    """Details about redaction applied to a request."""
    fields_redacted: list[str] = field(default_factory=list)
    redaction_method: str = "mask"  # mask, tokenize, remove, replace
    original_hash: str = ""


@dataclass
class EscalationDetails:
    """Details about an escalation."""
    escalation_id: str = ""
    escalated_to: str = ""
    escalation_reason: str = ""
    status: str = "pending"  # pending, approved, denied, expired, escalated
    resolved_at: datetime | None = None
    resolved_by: str = ""


@dataclass
class QuarantineDetails:
    """Details about a quarantine action."""
    quarantine_id: str = ""
    reason: str = ""
    scope: str = "agent"  # agent, tool, session, resource
    initiated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    initiated_by: str = "enforcement_engine"
    status: str = "active"  # active, lifted, expired
    lift_conditions: str = ""


@dataclass
class EnforcementDecision:
    """The result of an enforcement evaluation."""
    decision_id: str
    request_id: str
    agent_id: str
    decision: DecisionType
    reason: str
    confidence_score: float  # 0.0 - 1.0
    deterministic: bool = True  # Always True for enforcement decisions
    policy_id: str | None = None
    policy_version: str | None = None
    rules_evaluated: list[dict[str, Any]] = field(default_factory=list)
    evaluation_context: dict[str, Any] = field(default_factory=dict)
    redaction: RedactionDetails | None = None
    escalation: EscalationDetails | None = None
    quarantine: QuarantineDetails | None = None
    evidence_ids: list[str] = field(default_factory=list)
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: datetime | None = None
    evaluation_latency_ms: int = 0
    total_latency_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "decision": self.decision.value,
            "reason": self.reason,
            "confidence_score": self.confidence_score,
            "deterministic": self.deterministic,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "rules_evaluated": self.rules_evaluated,
            "evaluation_context": self.evaluation_context,
            "redaction": {
                "fields_redacted": self.redaction.fields_redacted,
                "redaction_method": self.redaction.redaction_method,
                "original_hash": self.redaction.original_hash,
            } if self.redaction else None,
            "escalation": {
                "escalation_id": self.escalation.escalation_id,
                "escalated_to": self.escalation.escalated_to,
                "escalation_reason": self.escalation.escalation_reason,
                "status": self.escalation.status,
            } if self.escalation else None,
            "quarantine": {
                "quarantine_id": self.quarantine.quarantine_id,
                "reason": self.quarantine.reason,
                "scope": self.quarantine.scope,
                "status": self.quarantine.status,
            } if self.quarantine else None,
            "evidence_ids": self.evidence_ids,
            "requested_at": self.requested_at.isoformat(),
            "decided_at": self.decided_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "evaluation_latency_ms": self.evaluation_latency_ms,
            "total_latency_ms": self.total_latency_ms,
        }


class DeterministicEnforcementEngine:
    """Core enforcement engine — deterministic, no LLM in decision path.

    Inspired by WhitePact: no governance decision is LLM-based.
    Inspired by Vigil: kernel-level enforcer for agent-level enforcement.
    """

    def __init__(
        self,
        policy_store: Any,  # PolicyStore
        evidence_collector: Any,  # EvidenceCollector
        redaction_engine: RedactionEngine | None = None,
    ):
        self.policy_store = policy_store
        self.evidence_collector = evidence_collector
        self.redaction_engine = redaction_engine or RedactionEngine()
        self._decision_count = 0
        self._decision_counts: dict[DecisionType, int] = {
            dt: 0 for dt in DecisionType
        }

    async def evaluate(self, request: EnforcementRequest) -> EnforcementDecision:
        """Evaluate an action request against active policies.

        This is the core deterministic enforcement path. No LLM is involved.
        """
        start_time = time.monotonic()
        decision_id = hashlib.sha256(
            f"{request.request_id}:{request.agent_id}:{request.action_type.value}".encode()
        ).hexdigest()[:16]

        # Get applicable policies
        policies = await self.policy_store.get_active_policies_for_agent(
            request.agent_id
        )

        if not policies:
            # No policies apply — default allow with audit
            latency_ms = int((time.monotonic() - start_time) * 1000)
            return EnforcementDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                agent_id=request.agent_id,
                decision=DecisionType.ALLOW,
                reason="No applicable policies found",
                confidence_score=1.0,
                evaluation_latency_ms=latency_ms,
                total_latency_ms=latency_ms,
            )

        # Evaluate all matching rules across all applicable policies
        matched_rules: list[tuple[Policy, PolicyRule, dict]] = []

        for policy in policies:
            for rule in policy.rules:
                if not rule.enabled:
                    continue
                if self._rule_matches(rule, request, policy.scope):
                    matched_rules.append((policy, rule, {
                        "policy_id": policy.id,
                        "policy_name": policy.name,
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "action": rule.action,
                        "priority": rule.priority,
                    }))

        # Sort by priority (highest first)
        matched_rules.sort(key=lambda x: x[1].priority, reverse=True)

        # First-match-wins (deterministic)
        if matched_rules:
            policy, rule, rule_info = matched_rules[0]
            decision = self._action_to_decision(rule.action)

            # Build decision
            eval_latency_ms = int((time.monotonic() - start_time) * 1000)

            enforcement_decision = EnforcementDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                agent_id=request.agent_id,
                decision=decision,
                reason=f"Policy '{policy.name}' rule '{rule.name}' matched",
                confidence_score=1.0,  # Deterministic = 100% confidence
                policy_id=policy.id,
                policy_version=policy.version,
                rules_evaluated=[info for _, _, info in matched_rules],
                evaluation_context={
                    "agent_id": request.agent_id,
                    "action_type": request.action_type.value,
                    "resource": request.resource,
                    "tool_name": request.tool_name,
                    "parameters_keys": list(request.parameters.keys()),
                },
                evaluation_latency_ms=eval_latency_ms,
                total_latency_ms=eval_latency_ms,
            )

            # Apply decision-specific logic
            if decision == DecisionType.ALLOW_WITH_REDACTION:
                enforcement_decision.redaction = await self._apply_redaction(
                    request, policy, rule
                )
            elif decision == DecisionType.REQUIRE_APPROVAL:
                enforcement_decision.escalation = await self._create_escalation(
                    request, policy, rule
                )
            elif decision == DecisionType.QUARANTINE:
                enforcement_decision.quarantine = await self._create_quarantine(
                    request, policy, rule
                )

            # Collect evidence
            evidence_ids = await self.evidence_collector.collect_enforcement_evidence(
                enforcement_decision
            )
            enforcement_decision.evidence_ids = evidence_ids

            # Update counters
            self._decision_count += 1
            self._decision_counts[decision] += 1

            return enforcement_decision

        # No rules matched — check fail mode
        fail_mode = policies[0].fail_mode if policies else "open"
        latency_ms = int((time.monotonic() - start_time) * 1000)

        if fail_mode == "closed":
            return EnforcementDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                agent_id=request.agent_id,
                decision=DecisionType.DENY,
                reason="No matching rules and policy fail_mode is 'closed'",
                confidence_score=1.0,
                evaluation_latency_ms=latency_ms,
                total_latency_ms=latency_ms,
            )
        else:
            return EnforcementDecision(
                decision_id=decision_id,
                request_id=request.request_id,
                agent_id=request.agent_id,
                decision=DecisionType.ALLOW,
                reason="No matching rules and policy fail_mode is 'open'",
                confidence_score=1.0,
                evaluation_latency_ms=latency_ms,
                total_latency_ms=latency_ms,
            )

    def _rule_matches(
        self, rule: PolicyRule, request: EnforcementRequest, scope: Any
    ) -> bool:
        """Deterministic rule matching — no LLM involved."""
        # Check scope first
        if scope.agents and request.agent_id not in scope.agents:
            return False
        if scope.environments and "all" not in scope.environments:
            env = request.context.get("environment", "unknown")
            if env not in scope.environments:
                return False

        # Evaluate rule conditions
        condition = rule.condition
        for key, expected in condition.items():
            actual = self._get_value_from_request(request, key)
            if not self._evaluate_condition(actual, expected):
                return False

        return True

    def _get_value_from_request(
        self, request: EnforcementRequest, key: str
    ) -> Any:
        """Extract a value from the request by key."""
        if key == "agent_id":
            return request.agent_id
        elif key == "action_type":
            return request.action_type.value
        elif key == "tool_name":
            return request.tool_name
        elif key == "resource":
            return request.resource
        elif key == "environment":
            return request.context.get("environment")
        elif key == "risk_tier":
            return request.context.get("risk_tier")
        else:
            return request.context.get(key)

    def _evaluate_condition(self, actual: Any, expected: Any) -> bool:
        """Evaluate a single condition deterministically."""
        if isinstance(expected, dict):
            for op, value in expected.items():
                if op == "eq" and actual != value:
                    return False
                elif op == "ne" and actual == value:
                    return False
                elif op == "lt" and (actual is None or actual >= value):
                    return False
                elif op == "lte" and (actual is None or actual > value):
                    return False
                elif op == "gt" and (actual is None or actual <= value):
                    return False
                elif op == "gte" and (actual is None or actual < value):
                    return False
                elif op == "in" and actual not in value:
                    return False
                elif op == "contains" and (actual is None or value not in actual):
                    return False
            return True
        else:
            return actual == expected

    def _action_to_decision(self, action: str) -> DecisionType:
        """Map rule action to decision type."""
        mapping = {
            "allow": DecisionType.ALLOW,
            "deny": DecisionType.DENY,
            "redact": DecisionType.ALLOW_WITH_REDACTION,
            "require_approval": DecisionType.REQUIRE_APPROVAL,
            "quarantine": DecisionType.QUARANTINE,
        }
        return mapping.get(action, DecisionType.DENY)

    async def _apply_redaction(
        self, request: EnforcementRequest, policy: Policy, rule: PolicyRule
    ) -> RedactionDetails:
        """Apply redaction to sensitive fields."""
        sensitive_fields = rule.metadata.get("sensitive_fields", [])
        redacted = []
        original_params = dict(request.parameters)

        for field_name in sensitive_fields:
            if field_name in request.parameters:
                redacted.append(field_name)
                request.parameters[field_name] = "[REDACTED]"

        original_hash = hashlib.sha256(
            str(original_params).encode()
        ).hexdigest()

        return RedactionDetails(
            fields_redacted=redacted,
            redaction_method=rule.metadata.get("redaction_method", "mask"),
            original_hash=original_hash,
        )

    async def _create_escalation(
        self, request: EnforcementRequest, policy: Policy, rule: PolicyRule
    ) -> EscalationDetails:
        """Create an approval escalation."""
        import uuid

        return EscalationDetails(
            escalation_id=str(uuid.uuid4()),
            escalated_to=policy.escalation_target or rule.metadata.get("approver", ""),
            escalation_reason=f"Policy '{policy.name}' requires approval for {request.action_type.value}",
            status="pending",
        )

    async def _create_quarantine(
        self, request: EnforcementRequest, policy: Policy, rule: PolicyRule
    ) -> QuarantineDetails:
        """Create a quarantine action."""
        import uuid

        return QuarantineDetails(
            quarantine_id=str(uuid.uuid4()),
            reason=f"Policy '{policy.name}' triggered quarantine for {request.action_type.value}",
            scope=rule.metadata.get("quarantine_scope", "agent"),
            status="active",
        )

    def get_stats(self) -> dict[str, Any]:
        """Get enforcement statistics."""
        return {
            "total_decisions": self._decision_count,
            "by_decision": {dt.value: count for dt, count in self._decision_counts.items()},
        }


class RedactionEngine:
    """Handles redaction of sensitive data in enforcement requests."""

    def __init__(self):
        self._patterns = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "ssn": r"\d{3}-\d{2}-\d{4}",
            "credit_card": r"\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}",
            "phone": r"\+?\d{1,3}[- ]?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}",
            "api_key": r"[a-zA-Z0-9]{32,}",
        }

    def detect_sensitive_fields(self, data: dict[str, Any]) -> list[str]:
        """Detect fields containing sensitive data."""
        import re

        sensitive = []
        for key, value in data.items():
            if isinstance(value, str):
                for pattern_name, pattern in self._patterns.items():
                    if re.search(pattern, value):
                        sensitive.append(key)
                        break
            elif isinstance(value, dict):
                nested = self.detect_sensitive_fields(value)
                sensitive.extend(f"{key}.{k}" for k in nested)
        return sensitive

    def redact_value(self, value: str, method: str = "mask") -> str:
        """Redact a single value."""
        if method == "mask":
            return value[:2] + "*" * (len(value) - 4) + value[-2:] if len(value) > 4 else "****"
        elif method == "remove":
            return ""
        elif method == "replace":
            return "[REDACTED]"
        elif method == "tokenize":
            return hashlib.sha256(value.encode()).hexdigest()[:16]
        return value
```

---

## 7. Module 6: Continuous Monitoring Engine

### 7.1 Purpose

Monitor AI systems in production for drift, violations, and emerging risks. Confidence-based routing — auto-approve above threshold, human review below.

### 7.2 Implementation

```python
# src/grc_claw/modules/monitoring.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass
class MonitoringAlert:
    """A monitoring alert."""
    id: str
    source: str  # e.g., "drift_detector", "anomaly_detector"
    severity: AlertSeverity
    title: str
    description: str
    asset_id: str | None = None
    agent_id: str | None = None
    confidence: float = 0.0  # 0.0 - 1.0
    status: AlertStatus = AlertStatus.ACTIVE
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None
    resolved_by: str | None = None


@dataclass
class DriftReport:
    """Model drift detection report."""
    asset_id: str
    drift_type: str  # data_drift, model_drift, concept_drift
    drift_score: float  # 0.0 - 1.0
    threshold: float
    is_drifting: bool
    details: dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DriftDetector:
    """Detect model behavior changes over time.

    Inspired by WhitePact and IBM watsonx.governance.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._baselines: dict[str, dict[str, Any]] = {}

    async def set_baseline(self, asset_id: str, baseline: dict[str, Any]):
        """Set the baseline for drift detection."""
        self._baselines[asset_id] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": baseline,
        }

    async def detect_drift(
        self, asset_id: str, current_metrics: dict[str, Any]
    ) -> DriftReport:
        """Detect drift by comparing current metrics to baseline."""
        if asset_id not in self._baselines:
            return DriftReport(
                asset_id=asset_id,
                drift_type="unknown",
                drift_score=0.0,
                threshold=self.config.get("drift_threshold", 0.1),
                is_drifting=False,
                details={"error": "No baseline set"},
            )

        baseline = self._baselines[asset_id]["metrics"]
        drift_scores = {}

        for metric_name, current_value in current_metrics.items():
            if metric_name in baseline:
                baseline_value = baseline[metric_name]
                if isinstance(current_value, (int, float)) and isinstance(baseline_value, (int, float)):
                    if baseline_value != 0:
                        drift_scores[metric_name] = abs(current_value - baseline_value) / abs(baseline_value)
                    else:
                        drift_scores[metric_name] = 0.0 if current_value == 0 else 1.0

        overall_drift = sum(drift_scores.values()) / len(drift_scores) if drift_scores else 0.0
        threshold = self.config.get("drift_threshold", 0.1)

        return DriftReport(
            asset_id=asset_id,
            drift_type="model_drift",
            drift_score=overall_drift,
            threshold=threshold,
            is_drifting=overall_drift > threshold,
            details={
                "metric_drifts": drift_scores,
                "baseline_timestamp": self._baselines[asset_id]["timestamp"],
            },
        )


class AnomalyDetector:
    """Detect anomalies in AI system behavior.

    Inspired by Vigil: 7,200+ detection rules (Sigma, Splunk, Elastic, KQL).
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._rules: list[dict[str, Any]] = []
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default anomaly detection rules."""
        self._rules = [
            {
                "id": "high_error_rate",
                "name": "High Error Rate",
                "description": "Error rate exceeds threshold",
                "condition": {"metric": "error_rate", "op": "gt", "value": 0.05},
                "severity": AlertSeverity.HIGH,
            },
            {
                "id": "latency_spike",
                "name": "Latency Spike",
                "description": "Response latency exceeds threshold",
                "condition": {"metric": "p99_latency_ms", "op": "gt", "value": 1000},
                "severity": AlertSeverity.MEDIUM,
            },
            {
                "id": "unusual_input_pattern",
                "name": "Unusual Input Pattern",
                "description": "Input distribution deviates significantly",
                "condition": {"metric": "input_distribution_distance", "op": "gt", "value": 0.3},
                "severity": AlertSeverity.MEDIUM,
            },
            {
                "id": "policy_violation_spike",
                "name": "Policy Violation Spike",
                "description": "Policy violation rate exceeds threshold",
                "condition": {"metric": "violation_rate_5m", "op": "gt", "value": 0.1},
                "severity": AlertSeverity.CRITICAL,
            },
        ]

    async def evaluate(self, metrics: dict[str, Any]) -> list[MonitoringAlert]:
        """Evaluate metrics against anomaly rules."""
        alerts = []

        for rule in self._rules:
            if self._evaluate_rule(rule, metrics):
                alert = MonitoringAlert(
                    id=f"{rule['id']}:{datetime.now(timezone.utc).timestamp()}",
                    source="anomaly_detector",
                    severity=rule["severity"],
                    title=rule["name"],
                    description=rule["description"],
                    confidence=self._calculate_confidence(rule, metrics),
                    context={
                        "rule_id": rule["id"],
                        "metrics": metrics,
                    },
                )
                alerts.append(alert)

        return alerts

    def _evaluate_rule(self, rule: dict, metrics: dict) -> bool:
        """Evaluate a single rule against metrics."""
        condition = rule["condition"]
        metric_name = condition["metric"]
        actual = metrics.get(metric_name)

        if actual is None:
            return False

        op = condition["op"]
        expected = condition["value"]

        if op == "gt":
            return actual > expected
        elif op == "gte":
            return actual >= expected
        elif op == "lt":
            return actual < expected
        elif op == "lte":
            return actual <= expected
        elif op == "eq":
            return actual == expected
        return False

    def _calculate_confidence(self, rule: dict, metrics: dict) -> float:
        """Calculate confidence score for an alert."""
        condition = rule["condition"]
        metric_name = condition["metric"]
        actual = metrics.get(metric_name, 0)
        threshold = condition["value"]

        if threshold == 0:
            return 1.0 if actual > 0 else 0.0

        ratio = actual / threshold
        return min(1.0, ratio)


class AlertRouter:
    """Route alerts based on confidence thresholds.

    Inspired by Vigil: confidence-based routing — auto-approve above threshold,
    human review below.
    """

    def __init__(self, config: dict[str, Any]):
        self.auto_approve_threshold = config.get("auto_approve_threshold", 0.90)
        self.human_review_threshold = config.get("human_review_threshold", 0.85)
        self._routes: dict[str, Callable] = {}

    def register_route(self, name: str, handler: Callable):
        """Register a route handler."""
        self._routes[name] = handler

    async def route_alert(self, alert: MonitoringAlert) -> dict[str, Any]:
        """Route an alert based on confidence and severity."""
        if alert.confidence >= self.auto_approve_threshold:
            # Auto-remediate
            action = "auto_remediate"
            await self._auto_remediate(alert)
        elif alert.confidence >= self.human_review_threshold:
            # Route to human review
            action = "human_review"
            await self._escalate_to_human(alert)
        else:
            # Low confidence — log and monitor
            action = "log_and_monitor"
            await self._log_alert(alert)

        return {
            "alert_id": alert.id,
            "action": action,
            "confidence": alert.confidence,
            "severity": alert.severity.value,
            "routed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _auto_remediate(self, alert: MonitoringAlert):
        """Auto-remediate a high-confidence alert."""
        logger.info("Auto-remediating alert: %s", alert.id)
        # Trigger automated remediation workflow
        # e.g., restart service, scale resources, apply config change

    async def _escalate_to_human(self, alert: MonitoringAlert):
        """Escalate an alert to human review."""
        logger.info("Escalating alert to human review: %s", alert.id)
        # Create ticket, send notification, etc.

    async def _log_alert(self, alert: MonitoringAlert):
        """Log a low-confidence alert for monitoring."""
        logger.debug("Logging alert: %s (confidence: %.2f)", alert.id, alert.confidence)


class ContinuousMonitoringEngine:
    """Orchestrates all monitoring components."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.drift_detector = DriftDetector(config.get("drift", {}))
        self.anomaly_detector = AnomalyDetector(config.get("anomaly", {}))
        self.alert_router = AlertRouter(config.get("routing", {}))
        self._monitoring_tasks: list[Any] = []

    async def start_monitoring(self, asset_id: str, metrics_callback: Callable):
        """Start continuous monitoring for an asset."""
        import asyncio

        async def _monitor_loop():
            while True:
                try:
                    metrics = await metrics_callback()

                    # Check for drift
                    drift_report = await self.drift_detector.detect_drift(
                        asset_id, metrics
                    )
                    if drift_report.is_drifting:
                        alert = MonitoringAlert(
                            id=f"drift:{asset_id}:{datetime.now(timezone.utc).timestamp()}",
                            source="drift_detector",
                            severity=AlertSeverity.HIGH if drift_report.drift_score > 0.2 else AlertSeverity.MEDIUM,
                            title=f"Model Drift Detected: {asset_id}",
                            description=f"Drift score {drift_report.drift_score:.3f} exceeds threshold {drift_report.threshold}",
                            asset_id=asset_id,
                            confidence=drift_report.drift_score,
                            context=drift_report.details,
                        )
                        await self.alert_router.route_alert(alert)

                    # Check for anomalies
                    alerts = await self.anomaly_detector.evaluate(metrics)
                    for alert in alerts:
                        await self.alert_router.route_alert(alert)

                except Exception as e:
                    logger.error("Monitoring error for %s: %s", asset_id, e)

                await asyncio.sleep(self.config.get("interval_seconds", 60))

        task = asyncio.create_task(_monitor_loop())
        self._monitoring_tasks.append(task)
        return task

    async def stop_all(self):
        """Stop all monitoring tasks."""
        for task in self._monitoring_tasks:
            task.cancel()
        self._monitoring_tasks.clear()
```

---

## 8. Module 7: Audit Evidence Engine

### 8.1 Purpose

Generate and maintain audit-ready evidence for all governance activities. Hash-chained, tamper-evident record of all governance decisions.

### 8.2 Implementation

```python
# src/grc_claw/modules/evidence.py

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EvidenceType(str, Enum):
    ARTIFACT = "artifact"
    OBSERVATION = "observation"
    INTERVIEW = "interview"
    ANALYSIS = "analysis"
    LOG = "log"


class VerificationLevel(str, Enum):
    L0 = "L0"  # Unverified
    L1 = "L1"  # Schema valid
    L2 = "L2"  # Hash verified
    L3 = "L3"  # Chain of custody intact
    L4 = "L4"  # Attested


@dataclass
class CustodyEvent:
    """A chain of custody event."""
    action: str  # collected, transferred, verified, exported, accessed
    actor: str
    timestamp: datetime
    evidence_hash: str
    previous_event_hash: str
    signature: str = ""


@dataclass
class EvidenceRecord:
    """A single evidence record in the ledger."""
    id: str
    type: EvidenceType
    title: str
    description: str = ""
    content_format: str = "application/json"
    content_data: str = ""  # base64, inline, or URI
    content_hash: str = ""
    hash_algorithm: str = "SHA-256"

    # Source
    source_system: str = ""
    source_location: str = ""
    collector_id: str = ""
    collector_version: str = ""
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Control mapping
    control_mappings: list[dict[str, str]] = field(default_factory=list)

    # Context
    environment: str = "prod"
    resource_scope: str = ""
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    agent_id: str | None = None
    policy_id: str | None = None

    # Verification
    verification_level: VerificationLevel = VerificationLevel.L0
    schema_valid: bool = False
    hash_verified: bool = False
    chain_of_custody_intact: bool = False
    cross_validated: bool = False
    attested: bool = False
    attested_by: str = ""
    attested_at: datetime | None = None

    # Chain of custody
    chain_of_custody: list[CustodyEvent] = field(default_factory=list)

    # Integrity
    integrity_hash: str = ""
    previous_hash: str = ""

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_hash(self) -> str:
        """Compute the integrity hash of this record."""
        canonical = json.dumps({
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "content_hash": self.content_hash,
            "source_system": self.source_system,
            "collected_at": self.collected_at.isoformat(),
            "control_mappings": self.control_mappings,
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()


class EvidenceLedger:
    """Hash-chained, tamper-evident evidence ledger.

    Inspired by OneTrust Evidence Ledger and WhitePact hash-chained EvidenceRecords.
    """

    def __init__(self, db_session: Any):
        self.db = db_session
        self._last_hash: str = "0" * 64  # Genesis hash

    async def append(self, record: EvidenceRecord) -> EvidenceRecord:
        """Append a new evidence record to the ledger."""
        record.id = record.id or str(uuid.uuid4())
        record.integrity_hash = record.compute_hash()
        record.previous_hash = self._last_hash

        # Create custody event
        custody_event = CustodyEvent(
            action="collected",
            actor=record.collector_id,
            timestamp=datetime.now(timezone.utc),
            evidence_hash=record.integrity_hash,
            previous_event_hash=self._last_hash,
        )
        record.chain_of_custody.append(custody_event)

        # Update last hash
        self._last_hash = record.integrity_hash

        # Persist
        await self._persist(record)

        logger.info("Evidence record appended: %s (hash: %s...)", record.id, record.integrity_hash[:16])
        return record

    async def verify_chain(self, start_id: str | None = None) -> dict[str, Any]:
        """Verify the integrity of the evidence chain."""
        records = await self._get_records(start_id)

        violations = []
        previous_hash = "0" * 64

        for record in records:
            # Verify hash chain
            if record.previous_hash != previous_hash:
                violations.append({
                    "record_id": record.id,
                    "type": "hash_chain_break",
                    "expected_previous": previous_hash,
                    "actual_previous": record.previous_hash,
                })

            # Verify record hash
            computed_hash = record.compute_hash()
            if computed_hash != record.integrity_hash:
                violations.append({
                    "record_id": record.id,
                    "type": "hash_mismatch",
                    "expected": computed_hash,
                    "actual": record.integrity_hash,
                })

            previous_hash = record.integrity_hash

        return {
            "verified": len(violations) == 0,
            "records_checked": len(records),
            "violations": violations,
            "chain_length": len(records),
            "first_hash": records[0].integrity_hash if records else None,
            "last_hash": records[-1].integrity_hash if records else None,
        }

    async def get_evidence_pack(
        self,
        framework: str,
        control_ids: list[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Generate an evidence pack for a specific audit scenario."""
        records = await self._query_records(
            framework=framework,
            control_ids=control_ids,
            start_time=start_time,
            end_time=end_time,
        )

        return {
            "framework": framework,
            "control_ids": control_ids,
            "time_window": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
            },
            "evidence_count": len(records),
            "evidence_items": [
                {
                    "id": r.id,
                    "type": r.type.value,
                    "title": r.title,
                    "verification_level": r.verification_level.value,
                    "collected_at": r.collected_at.isoformat(),
                    "integrity_hash": r.integrity_hash,
                    "control_mappings": r.control_mappings,
                }
                for r in records
            ],
            "chain_verification": await self.verify_chain(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _persist(self, record: EvidenceRecord):
        """Persist a record to the database."""
        # Implementation depends on your database layer
        pass

    async def _get_records(self, start_id: str | None = None) -> list[EvidenceRecord]:
        """Get records from the database."""
        # Implementation depends on your database layer
        return []

    async def _query_records(
        self,
        framework: str | None = None,
        control_ids: list[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[EvidenceRecord]:
        """Query records by criteria."""
        # Implementation depends on your database layer
        return []


class EvidenceCollector:
    """Collects evidence from various sources."""

    def __init__(self, ledger: EvidenceLedger):
        self.ledger = ledger

    async def collect_enforcement_evidence(
        self, decision: Any  # EnforcementDecision
    ) -> list[str]:
        """Collect evidence for an enforcement decision."""
        record = EvidenceRecord(
            id=str(uuid.uuid4()),
            type=EvidenceType.LOG,
            title=f"Enforcement Decision: {decision.decision.value}",
            description=f"Agent {decision.agent_id} action {decision.action_type.value}",
            content_data=json.dumps(decision.to_dict()),
            content_hash=hashlib.sha256(
                json.dumps(decision.to_dict()).encode()
            ).hexdigest(),
            source_system="enforcement_engine",
            collector_id="enforcement_engine",
            collector_version="1.0.0",
            control_mappings=[{
                "control_id": "ENF-001",
                "framework": "INTERNAL",
                "control_title": "Runtime Enforcement",
            }],
            environment=decision.evaluation_context.get("environment", "prod"),
            agent_id=decision.agent_id,
            policy_id=decision.policy_id,
        )

        stored = await self.ledger.append(record)
        return [stored.id]

    async def collect_assessment_evidence(
        self, assessment: Any  # RiskAssessment
    ) -> list[str]:
        """Collect evidence for a risk assessment."""
        record = EvidenceRecord(
            id=str(uuid.uuid4()),
            type=EvidenceType.ANALYSIS,
            title=f"Risk Assessment: {assessment.asset_name}",
            description=f"Overall score: {assessment.overall_score:.2f}, Grade: {assessment.grade}",
            content_data=json.dumps(assessment.to_dict()),
            content_hash=hashlib.sha256(
                json.dumps(assessment.to_dict()).encode()
            ).hexdigest(),
            source_system="risk_engine",
            collector_id="risk_engine",
            collector_version="1.0.0",
            control_mappings=[{
                "control_id": "RISK-001",
                "framework": "NIST-AI-RMF",
                "control_title": "Risk Assessment",
            }],
            agent_id=assessment.asset_id,
        )

        stored = await self.ledger.append(record)
        return [stored.id]
```

---

## 9. Module 8: Agent Governance Layer

### 9.1 Purpose

Govern autonomous AI agents with specialized governance agents. Detection and enforcement agents are separate — no conflicts of interest.

### 9.2 Implementation

```python
# src/grc_claw/modules/agent_governance.py

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    AUTONOMOUS = "autonomous"
    SEMI_AUTONOMOUS = "semi_autonomous"
    HUMAN_IN_LOOP = "human_in_loop"
    HUMAN_ON_LOOP = "human_on_loop"


class AgentStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    TERMINATED = "terminated"


class TrustLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNTRUSTED = "untrusted"


@dataclass
class AgentIdentity:
    """Cryptographic identity for an agent."""
    unique_id: str
    attestation: str = ""
    certificate: str = ""
    trust_score: float = 0.0  # 0.0 - 1.0
    trust_level: TrustLevel = TrustLevel.UNTRUSTED


@dataclass
class AgentCapability:
    """A single capability of an agent."""
    name: str
    description: str = ""
    risk_tier: str = "minimal"
    allowed_tools: list[str] = field(default_factory=list)
    allowed_resources: list[str] = field(default_factory=list)
    max_autonomy_level: str = "supervised"  # full, guarded, supervised, manual


@dataclass
class GovernedAgent:
    """An AI agent under governance."""
    id: str
    name: str
    type: AgentType
    status: AgentStatus = AgentStatus.PROPOSED
    identity: AgentIdentity = field(default_factory=AgentIdentity)
    capabilities: list[AgentCapability] = field(default_factory=list)
    owner: str = ""
    owning_team: str = ""
    business_unit: str = ""
    policy_ids: list[str] = field(default_factory=list)
    enforcement_profile: str = ""
    assessment_schedule: str = "quarterly"
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: datetime | None = None
    deprecated_at: datetime | None = None
    termination_reason: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.identity.unique_id:
            self.identity.unique_id = f"did:grcclaw:{self.id}"


class SentinelAgent:
    """Detection-focused governance agent.

    Inspired by Holistic AI Sentinel and Vigil's 13 specialized agents.
    Monitors for drift, bias, anomalies, compliance gaps.
    Does NOT enforce — detection only.
    """

    def __init__(self, agent_id: str, config: dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self._detection_rules: list[dict[str, Any]] = []

    async def monitor(self, target_agent: GovernedAgent) -> list[dict[str, Any]]:
        """Monitor a target agent for governance violations."""
        findings = []

        # Check policy adherence
        policy_findings = await self._check_policy_adherence(target_agent)
        findings.extend(policy_findings)

        # Check capability drift
        drift_findings = await self._check_capability_drift(target_agent)
        findings.extend(drift_findings)

        # Check behavioral anomalies
        anomaly_findings = await self._check_behavioral_anomalies(target_agent)
        findings.extend(anomaly_findings)

        # Check compliance gaps
        compliance_findings = await self._check_compliance_gaps(target_agent)
        findings.extend(compliance_findings)

        return findings

    async def _check_policy_adherence(
        self, target_agent: GovernedAgent
    ) -> list[dict[str, Any]]:
        """Check if the agent is adhering to its assigned policies."""
        findings = []
        # Implementation: query enforcement history, check for violations
        return findings

    async def _check_capability_drift(
        self, target_agent: GovernedAgent
    ) -> list[dict[str, Any]]:
        """Check if the agent's capabilities have drifted from approved baseline."""
        findings = []
        # Implementation: compare current capabilities to registered baseline
        return findings

    async def _check_behavioral_anomalies(
        self, target_agent: GovernedAgent
    ) -> list[dict[str, Any]]:
        """Check for behavioral anomalies."""
        findings = []
        # Implementation: statistical analysis of agent behavior
        return findings

    async def _check_compliance_gaps(
        self, target_agent: GovernedAgent
    ) -> list[dict[str, Any]]:
        """Check for compliance gaps."""
        findings = []
        # Implementation: check assessment currency, evidence coverage
        return findings


class OperativeAgent:
    """Enforcement-focused governance agent.

    Inspired by Holistic AI Operative.
    Handles kill switches, blocking, remediation.
    Does NOT detect — enforcement only.
    """

    def __init__(self, agent_id: str, config: dict[str, Any]):
        self.agent_id = agent_id
        self.config = config

    async def enforce(
        self,
        target_agent: GovernedAgent,
        finding: dict[str, Any],
        enforcement_engine: Any,  # DeterministicEnforcementEngine
    ) -> dict[str, Any]:
        """Enforce a remediation action based on a finding."""
        action = finding.get("recommended_action", "log")

        if action == "kill_switch":
            return await self._execute_kill_switch(target_agent, finding)
        elif action == "block":
            return await self._execute_block(target_agent, finding)
        elif action == "quarantine":
            return await self._execute_quarantine(target_agent, finding)
        elif action == "remediate":
            return await self._execute_remediation(target_agent, finding)
        else:
            return {"action": "logged", "finding_id": finding.get("id")}

    async def _execute_kill_switch(
        self, target_agent: GovernedAgent, finding: dict
    ) -> dict[str, Any]:
        """Emergency stop for an AI system."""
        logger.critical(
            "KILL SWITCH executed for agent %s: %s",
            target_agent.id,
            finding.get("reason", "Emergency stop"),
        )
        target_agent.status = AgentStatus.TERMINATED
        target_agent.termination_reason = finding.get("reason", "Kill switch")
        target_agent.deprecated_at = datetime.now(timezone.utc)

        return {
            "action": "kill_switch",
            "agent_id": target_agent.id,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "reason": finding.get("reason"),
        }

    async def _execute_block(
        self, target_agent: GovernedAgent, finding: dict
    ) -> dict[str, Any]:
        """Block an agent from specific actions."""
        logger.warning(
            "BLOCK executed for agent %s: %s",
            target_agent.id,
            finding.get("reason", "Policy violation"),
        )
        return {
            "action": "block",
            "agent_id": target_agent.id,
            "blocked_capability": finding.get("capability"),
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _execute_quarantine(
        self, target_agent: GovernedAgent, finding: dict
    ) -> dict[str, Any]:
        """Quarantine an agent."""
        logger.warning(
            "QUARANTINE executed for agent %s: %s",
            target_agent.id,
            finding.get("reason", "Security concern"),
        )
        return {
            "action": "quarantine",
            "agent_id": target_agent.id,
            "scope": finding.get("scope", "agent"),
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _execute_remediation(
        self, target_agent: GovernedAgent, finding: dict
    ) -> dict[str, Any]:
        """Execute automated remediation."""
        logger.info(
            "REMEDIATION executed for agent %s: %s",
            target_agent.id,
            finding.get("remediation_action", "default"),
        )
        return {
            "action": "remediate",
            "agent_id": target_agent.id,
            "remediation_action": finding.get("remediation_action"),
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }


class AgentGovernanceLayer:
    """Orchestrates agent governance with separated detection and enforcement."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.sentinel = SentinelAgent("sentinel-1", config.get("sentinel", {}))
        self.operative = OperativeAgent("operative-1", config.get("operative", {}))
        self._agents: dict[str, GovernedAgent] = {}

    async def register_agent(self, agent: GovernedAgent) -> GovernedAgent:
        """Register a new agent for governance."""
        self._agents[agent.id] = agent
        logger.info("Agent registered: %s (%s)", agent.name, agent.id)
        return agent

    async def govern_agent(
        self,
        agent_id: str,
        enforcement_engine: Any,
    ) -> dict[str, Any]:
        """Run full governance cycle: detect → decide → enforce."""
        agent = self._agents.get(agent_id)
        if not agent:
            return {"error": "Agent not found"}

        # Step 1: Sentinel detects issues
        findings = await self.sentinel.monitor(agent)

        # Step 2: Operative enforces based on findings
        enforcement_results = []
        for finding in findings:
            if finding.get("severity") in ("high", "critical"):
                result = await self.operative.enforce(agent, finding, enforcement_engine)
                enforcement_results.append(result)

        return {
            "agent_id": agent_id,
            "findings_count": len(findings),
            "enforcement_actions": len(enforcement_results),
            "findings": findings,
            "enforcement_results": enforcement_results,
            "governed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def attest_agent(self, agent_id: str) -> dict[str, Any]:
        """Attest an agent's identity and runtime posture."""
        agent = self._agents.get(agent_id)
        if not agent:
            return {"error": "Agent not found"}

        # Verify identity
        identity_valid = self._verify_identity(agent)

        # Verify runtime posture
        posture_valid = await self._verify_posture(agent)

        # Calculate trust score
        trust_score = self._calculate_trust_score(agent, identity_valid, posture_valid)
        agent.identity.trust_score = trust_score
        agent.identity.trust_level = self._score_to_trust_level(trust_score)

        return {
            "agent_id": agent_id,
            "identity_valid": identity_valid,
            "posture_valid": posture_valid,
            "trust_score": trust_score,
            "trust_level": agent.identity.trust_level.value,
            "attested_at": datetime.now(timezone.utc).isoformat(),
        }

    def _verify_identity(self, agent: GovernedAgent) -> bool:
        """Verify agent identity."""
        return bool(agent.identity.unique_id and agent.identity.attestation)

    async def _verify_posture(self, agent: GovernedAgent) -> bool:
        """Verify agent runtime posture."""
        # Implementation: check binary integrity, config integrity, policy bundle
        return True

    def _calculate_trust_score(
        self, agent: GovernedAgent, identity_valid: bool, posture_valid: bool
    ) -> float:
        """Calculate agent trust score."""
        score = 0.0
        if identity_valid:
            score += 0.4
        if posture_valid:
            score += 0.3
        if agent.status == AgentStatus.ACTIVE:
            score += 0.3
        return min(1.0, score)

    def _score_to_trust_level(self, score: float) -> TrustLevel:
        if score >= 0.8:
            return TrustLevel.HIGH
        elif score >= 0.5:
            return TrustLevel.MEDIUM
        elif score >= 0.2:
            return TrustLevel.LOW
        else:
            return TrustLevel.UNTRUSTED
```

---

## 10. MCP Server Implementation

### 10.1 Purpose

Expose GRC_Claw governance capabilities via the Model Context Protocol, enabling AI agents to be governed natively within their workflow.

### 10.2 Implementation

```python
# src/grc_claw/mcp/server.py

from __future__ import annotations

import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource, ResourceTemplate

from grc_claw.enforcement.engine import (
    ActionType,
    DeterministicEnforcementEngine,
    EnforcementRequest,
)
from grc_claw.modules.discovery import DiscoveryEngine
from grc_claw.modules.inventory import InventoryGraph
from grc_claw.modules.evidence import EvidenceCollector, EvidenceLedger

logger = logging.getLogger(__name__)


class GRClawMCPServer:
    """MCP Server exposing GRC_Claw governance capabilities.

    Inspired by WhitePact (30 tools, 20 resources) and AIBOM-Guard (6 tools).
    """

    def __init__(
        self,
        enforcement_engine: DeterministicEnforcementEngine,
        discovery_engine: DiscoveryEngine,
        inventory_graph: InventoryGraph,
        evidence_collector: EvidenceCollector,
    ):
        self.enforcement_engine = enforcement_engine
        self.discovery_engine = discovery_engine
        self.inventory_graph = inventory_graph
        self.evidence_collector = evidence_collector
        self.server = Server("grc-claw-governance")
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="enforce_action",
                    description="Evaluate an AI agent action against governance policies and return a decision",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "The ID of the agent requesting the action",
                            },
                            "action_type": {
                                "type": "string",
                                "enum": [at.value for at in ActionType],
                                "description": "The type of action being requested",
                            },
                            "tool_name": {
                                "type": "string",
                                "description": "The name of the tool being called (if applicable)",
                            },
                            "resource": {
                                "type": "string",
                                "description": "The resource being accessed",
                            },
                            "parameters": {
                                "type": "object",
                                "description": "The parameters for the action",
                            },
                            "context": {
                                "type": "object",
                                "description": "Additional context for the evaluation",
                            },
                        },
                        "required": ["agent_id", "action_type", "resource"],
                    },
                ),
                Tool(
                    name="get_asset_inventory",
                    description="Get the current AI asset inventory with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "asset_type": {
                                "type": "string",
                                "description": "Filter by asset type",
                            },
                            "risk_tier": {
                                "type": "string",
                                "description": "Filter by risk tier",
                            },
                            "lifecycle_stage": {
                                "type": "string",
                                "description": "Filter by lifecycle stage",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_asset_dependencies",
                    description="Get dependency graph for a specific AI asset",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "asset_id": {
                                "type": "string",
                                "description": "The asset ID to query",
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum dependency depth (default: 5)",
                            },
                        },
                        "required": ["asset_id"],
                    },
                ),
                Tool(
                    name="get_evidence_pack",
                    description="Generate an evidence pack for audit purposes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "framework": {
                                "type": "string",
                                "description": "The compliance framework (e.g., SOC2, ISO-42001)",
                            },
                            "control_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific control IDs to include",
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Start of time window (ISO-8601)",
                            },
                            "end_time": {
                                "type": "string",
                                "description": "End of time window (ISO-8601)",
                            },
                        },
                        "required": ["framework"],
                    },
                ),
                Tool(
                    name="get_enforcement_stats",
                    description="Get enforcement decision statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "Filter by agent ID",
                            },
                            "time_range": {
                                "type": "string",
                                "description": "Time range (e.g., '24h', '7d')",
                            },
                        },
                    },
                ),
                Tool(
                    name="verify_audit_chain",
                    description="Verify the integrity of the audit evidence chain",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_id": {
                                "type": "string",
                                "description": "Starting record ID (optional)",
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            if name == "enforce_action":
                return await self._handle_enforce_action(arguments)
            elif name == "get_asset_inventory":
                return await self._handle_get_asset_inventory(arguments)
            elif name == "get_asset_dependencies":
                return await self._handle_get_asset_dependencies(arguments)
            elif name == "get_evidence_pack":
                return await self._handle_get_evidence_pack(arguments)
            elif name == "get_enforcement_stats":
                return await self._handle_get_enforcement_stats(arguments)
            elif name == "verify_audit_chain":
                return await self._handle_verify_audit_chain(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            return [
                Resource(
                    uri="grcclaw://policies/active",
                    name="Active Policies",
                    description="Currently active governance policies",
                    mimeType="application/json",
                ),
                Resource(
                    uri="grcclaw://inventory/summary",
                    name="Inventory Summary",
                    description="Summary of AI asset inventory",
                    mimeType="application/json",
                ),
                Resource(
                    uri="grcclaw://enforcement/stats",
                    name="Enforcement Statistics",
                    description="Enforcement decision statistics",
                    mimeType="application/json",
                ),
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            if uri == "grcclaw://policies/active":
                return await self._get_active_policies()
            elif uri == "grcclaw://inventory/summary":
                return await self._get_inventory_summary()
            elif uri == "grcclaw://enforcement/stats":
                return self._get_enforcement_stats()
            return "{}"

    async def _handle_enforce_action(self, args: dict) -> list[TextContent]:
        """Handle the enforce_action tool."""
        import uuid

        request = EnforcementRequest(
            request_id=str(uuid.uuid4()),
            agent_id=args["agent_id"],
            action_type=ActionType(args["action_type"]),
            tool_name=args.get("tool_name"),
            resource=args["resource"],
            parameters=args.get("parameters", {}),
            context=args.get("context", {}),
        )

        decision = await self.enforcement_engine.evaluate(request)

        return [TextContent(
            type="text",
            text=json.dumps(decision.to_dict(), indent=2),
        )]

    async def _handle_get_asset_inventory(self, args: dict) -> list[TextContent]:
        """Handle the get_asset_inventory tool."""
        summary = await self.inventory_graph.get_inventory_summary()
        return [TextContent(type="text", text=json.dumps(summary, indent=2))]

    async def _handle_get_asset_dependencies(self, args: dict) -> list[TextContent]:
        """Handle the get_asset_dependencies tool."""
        deps = await self.inventory_graph.get_dependencies(
            args["asset_id"],
            max_depth=args.get("max_depth", 5),
        )
        return [TextContent(type="text", text=json.dumps(deps, indent=2))]

    async def _handle_get_evidence_pack(self, args: dict) -> list[TextContent]:
        """Handle the get_evidence_pack tool."""
        pack = await self.evidence_collector.ledger.get_evidence_pack(
            framework=args["framework"],
            control_ids=args.get("control_ids"),
        )
        return [TextContent(type="text", text=json.dumps(pack, indent=2))]

    async def _handle_get_enforcement_stats(self, args: dict) -> list[TextContent]:
        """Handle the get_enforcement_stats tool."""
        stats = self.enforcement_engine.get_stats()
        return [TextContent(type="text", text=json.dumps(stats, indent=2))]

    async def _handle_verify_audit_chain(self, args: dict) -> list[TextContent]:
        """Handle the verify_audit_chain tool."""
        result = await self.evidence_collector.ledger.verify_chain(
            start_id=args.get("start_id"),
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _get_active_policies(self) -> str:
        """Get active policies as JSON."""
        return json.dumps({"policies": []})

    async def _get_inventory_summary(self) -> str:
        """Get inventory summary as JSON."""
        summary = await self.inventory_graph.get_inventory_summary()
        return json.dumps(summary)

    def _get_enforcement_stats(self) -> str:
        """Get enforcement stats as JSON."""
        return json.dumps(self.enforcement_engine.get_stats())

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


# Entry point for MCP server
async def main():
    """MCP server entry point."""
    import json

    # Initialize components (simplified — use proper DI in production)
    from grc_claw.config import load_config

    config = load_config()

    # Create engines
    enforcement_engine = DeterministicEnforcementEngine(
        policy_store=None,  # Inject real policy store
        evidence_collector=None,  # Inject real evidence collector
    )
    discovery_engine = DiscoveryEngine(connectors=[])
    inventory_graph = InventoryGraph(
        uri=config["neo4j"]["uri"],
        username=config["neo4j"]["username"],
        password=config["neo4j"]["password"],
    )
    evidence_collector = EvidenceCollector(ledger=None)

    server = GRClawMCPServer(
        enforcement_engine=enforcement_engine,
        discovery_engine=discovery_engine,
        inventory_graph=inventory_graph,
        evidence_collector=evidence_collector,
    )

    await server.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 11. Deterministic Enforcement Engine

### 11.1 Core Principles

The deterministic enforcement engine is the heart of GRC_Claw. Key design decisions:

1. **No LLM in the decision path** — governance decisions are made by deterministic rules
2. **First-match-wins** — rules are evaluated in priority order, first match determines the decision
3. **Reproducible** — same input always produces same output
4. **Auditable** — every decision is fully explained with rules evaluated

### 11.2 Decision Flow

```
1. Agent initiates action
       │
       ▼
2. MCP Gateway intercepts action
       │
       ▼
3. Authentication & authorization check
       │
       ▼
4. Policy engine evaluates action against active policies
       │
       ├──▶ ALLOW → Execute action → Log to audit trail
       │
       ├──▶ ALLOW_WITH_REDACTION → Redact sensitive fields → Execute → Log
       │
       ├──▶ REQUIRE_APPROVAL → Queue approval request → Notify approver
       │                         │
       │                         ├──▶ Approved → Execute → Log
       │                         └──▶ Denied → Block → Log
       │
       ├──▶ DENY → Block action → Log → Alert
       │
       └──▶ QUARANTINE → Isolate agent → Log → Alert → Escalate
```

### 11.3 OPA Integration

```python
# src/grc_claw/enforcement/opa_adapter.py

from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class OPAAdapter:
    """Adapter for Open Policy Agent (OPA) integration.

    Uses OPA as the policy evaluation engine for complex policies.
    """

    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url.rstrip("/")

    async def evaluate(
        self,
        policy_package: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate a policy against input data via OPA."""
        url = f"{self.opa_url}/v1/data/{policy_package.replace('.', '/')}"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={"input": input_data},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", {})
                else:
                    text = await response.text()
                    logger.error("OPA evaluation failed: %s %s", response.status, text)
                    return {"error": text}

    async def upload_policy(self, policy_name: str, rego_code: str) -> bool:
        """Upload a Rego policy to OPA."""
        url = f"{self.opa_url}/v1/policies/{policy_name}"

        async with aiohttp.ClientSession() as session:
            async with session.put(
                url,
                data=rego_code,
                headers={"Content-Type": "text/plain"},
            ) as response:
                return response.status in (200, 201)

    async def health_check(self) -> bool:
        """Check OPA health."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.opa_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False
```

---

## 12. Event-Driven Architecture

### 12.1 Event Bus Implementation

```python
# src/grc_claw/events/bus.py

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EventDomain(str, Enum):
    ENFORCEMENT = "enforcement"
    EVIDENCE = "evidence"
    AUDIT = "audit"
    COMPLIANCE = "compliance"
    RISK = "risk"
    AGENT = "agent"
    POLICY = "policy"
    ASSESSMENT = "assessment"


@dataclass
class GRClawEvent:
    """CloudEvents 1.0 compliant event with GRC_Claw extensions."""
    specversion: str = "1.0"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "grc-claw"
    type: str = ""
    subject: str = ""
    time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    datacontenttype: str = "application/json"
    data: dict[str, Any] = field(default_factory=dict)
    # GRC_Claw extensions
    tenant_id: str = ""
    environment: str = "prod"
    trace_id: str = ""
    span_id: str = ""
    compliance_frameworks: list[str] = field(default_factory=list)
    risk_tier: str = ""
    data_classification: str = "internal"
    retention_class: str = "security_log"
    encryption_key_id: str = ""

    def to_cloudevent(self) -> dict[str, Any]:
        """Convert to CloudEvents 1.0 format."""
        return {
            "specversion": self.specversion,
            "id": self.id,
            "source": self.source,
            "type": self.type,
            "subject": self.subject,
            "time": self.time,
            "datacontenttype": self.datacontenttype,
            "data": self.data,
            "grcclaw": {
                "tenant_id": self.tenant_id,
                "environment": self.environment,
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "compliance_frameworks": self.compliance_frameworks,
                "risk_tier": self.risk_tier,
                "data_classification": self.data_classification,
                "retention_class": self.retention_class,
                "encryption_key_id": self.encryption_key_id,
            },
        }

    @classmethod
    def from_cloudevent(cls, data: dict[str, Any]) -> GRClawEvent:
        """Create from CloudEvents 1.0 format."""
        grcclaw_ext = data.get("grcclaw", {})
        return cls(
            specversion=data.get("specversion", "1.0"),
            id=data.get("id", str(uuid.uuid4())),
            source=data.get("source", "grc-claw"),
            type=data.get("type", ""),
            subject=data.get("subject", ""),
            time=data.get("time", datetime.now(timezone.utc).isoformat()),
            datacontenttype=data.get("datacontenttype", "application/json"),
            data=data.get("data", {}),
            tenant_id=grcclaw_ext.get("tenant_id", ""),
            environment=grcclaw_ext.get("environment", "prod"),
            trace_id=grcclaw_ext.get("trace_id", ""),
            span_id=grcclaw_ext.get("span_id", ""),
            compliance_frameworks=grcclaw_ext.get("compliance_frameworks", []),
            risk_tier=grcclaw_ext.get("risk_tier", ""),
            data_classification=grcclaw_ext.get("data_classification", "internal"),
            retention_class=grcclaw_ext.get("retention_class", "security_log"),
            encryption_key_id=grcclaw_ext.get("encryption_key_id", ""),
        )


class EventBus:
    """Apache Kafka-based event bus.

    Inspired by the integration specification's event-driven architecture.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._producer = None
        self._consumer = None
        self._handlers: dict[str, list[Callable]] = {}

    async def initialize(self):
        """Initialize Kafka producer and consumer."""
        from confluent_kafka import Producer, Consumer

        kafka_config = self.config.get("kafka", {})

        self._producer = Producer({
            "bootstrap.servers": ",".join(kafka_config.get("brokers", ["localhost:9092"])),
            "security.protocol": kafka_config.get("protocol", "PLAINTEXT"),
        })

        self._consumer = Consumer({
            "bootstrap.servers": ",".join(kafka_config.get("brokers", ["localhost:9092"])),
            "group.id": "grc-claw-event-processor",
            "auto.offset.reset": "earliest",
        })

    async def publish(self, event: GRClawEvent, topic: str | None = None):
        """Publish an event to the bus."""
        if not self._producer:
            raise RuntimeError("Event bus not initialized")

        topic = topic or self._get_topic_for_event(event)

        self._producer.produce(
            topic=topic,
            key=event.subject.encode() if event.subject else None,
            value=json.dumps(event.to_cloudevent()).encode(),
        )
        self._producer.flush()

        logger.debug("Event published: %s to %s", event.type, topic)

    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to events of a specific type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def start_consuming(self, topics: list[str]):
        """Start consuming events."""
        if not self._consumer:
            raise RuntimeError("Event bus not initialized")

        self._consumer.subscribe(topics)

        while True:
            msg = self._consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("Consumer error: %s", msg.error())
                continue

            try:
                event_data = json.loads(msg.value().decode())
                event = GRClawEvent.from_cloudevent(event_data)

                handlers = self._handlers.get(event.type, [])
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error("Event handler error: %s", e)

            except Exception as e:
                logger.error("Failed to process event: %s", e)

    def _get_topic_for_event(self, event: GRClawEvent) -> str:
        """Determine the Kafka topic for an event."""
        domain_map = {
            EventDomain.ENFORCEMENT: "grcclaw.enforcement",
            EventDomain.EVIDENCE: "grcclaw.evidence",
            EventDomain.AUDIT: "grcclaw.audit",
            EventDomain.COMPLIANCE: "grcclaw.compliance",
            EventDomain.RISK: "grcclaw.risk",
            EventDomain.AGENT: "grcclaw.agent",
            EventDomain.POLICY: "grcclaw.policy",
            EventDomain.ASSESSMENT: "grcclaw.assessment",
        }

        for domain, topic in domain_map.items():
            if domain.value in event.type:
                return topic

        return "grcclaw.general"

    async def close(self):
        """Close the event bus."""
        if self._producer:
            self._producer.flush()
        if self._consumer:
            self._consumer.close()
```

### 12.2 Event Handlers

```python
# src/grc_claw/events/handlers.py

from __future__ import annotations

import logging
from typing import Any

from grc_claw.events.bus import GRClawEvent

logger = logging.getLogger(__name__)


class EnforcementEventHandler:
    """Handle enforcement decision events."""

    async def handle(self, event: GRClawEvent):
        """Process an enforcement decision event."""
        decision = event.data.get("decision")
        agent_id = event.data.get("agent_id")

        if decision == "DENY":
            logger.warning("Enforcement DENY for agent %s: %s", agent_id, event.data.get("reason"))
            # Trigger alert, create ticket, etc.
        elif decision == "QUARANTINE":
            logger.critical("Agent %s quarantined: %s", agent_id, event.data.get("reason"))
            # Trigger incident response


class EvidenceEventHandler:
    """Handle evidence collection events."""

    async def handle(self, event: GRClawEvent):
        """Process an evidence event."""
        evidence_id = event.data.get("evidence_id")
        logger.info("Evidence collected: %s", evidence_id)
        # Update compliance posture, notify stakeholders, etc.


class RiskEventHandler:
    """Handle risk detection events."""

    async def handle(self, event: GRClawEvent):
        """Process a risk event."""
        risk_tier = event.data.get("risk_tier")
        if risk_tier in ("high", "critical"):
            logger.warning("High risk detected: %s", event.data.get("title"))
            # Trigger risk workflow, notify risk manager
```

---

## 13. Configuration Management

### 13.1 Configuration Schema

```python
# src/grc_claw/config.py

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """GRC_Claw configuration management.

    Supports environment-specific overrides and environment variable substitution.
    """

    DEFAULT_CONFIG_PATH = Path("config/default.yaml")
    ENV_CONFIG_PATH = Path("config/production.yaml")

    def __init__(self, config: dict[str, Any]):
        self._config = config

    @classmethod
    def load(
        cls,
        config_path: str | Path | None = None,
        env: str | None = None,
    ) -> Config:
        """Load configuration from YAML files.

        Loads default config, then overlays environment-specific config.
        Supports ${ENV_VAR} substitution.
        """
        config: dict[str, Any] = {}

        # Load default config
        default_path = cls.DEFAULT_CONFIG_PATH
        if default_path.exists():
            config = yaml.safe_load(default_path.read_text()) or {}

        # Overlay environment-specific config
        env = env or os.environ.get("GRC_CLAW_ENV", "default")
        env_path = Path(f"config/{env}.yaml")
        if env_path.exists():
            env_config = yaml.safe_load(env_path.read_text()) or {}
            config = cls._deep_merge(config, env_config)

        # Override with explicit path if provided
        if config_path:
            override = yaml.safe_load(Path(config_path).read_text()) or {}
            config = cls._deep_merge(config, override)

        # Substitute environment variables
        config = cls._substitute_env_vars(config)

        return cls(config)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by dotted key path."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _substitute_env_vars(config: Any) -> Any:
        """Recursively substitute ${ENV_VAR} patterns."""
        import re

        if isinstance(config, dict):
            return {k: Config._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [Config._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            pattern = r"\$\{([^}]+)\}"
            matches = re.findall(pattern, config)
            for match in matches:
                env_value = os.environ.get(match, "")
                config = config.replace(f"${{{match}}}", env_value)
            return config
        return config
```

### 13.2 Default Configuration

```yaml
# config/default.yaml
app:
  name: "GRC_Claw Automation Engine"
  version: "1.0.0"
  environment: "development"
  log_level: "INFO"

api:
  host: "0.0.0.0"
  port: 8080
  workers: 4
  cors_origins: ["*"]

neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "password"

kafka:
  brokers: ["localhost:9092"]
  protocol: "PLAINTEXT"

postgresql:
  host: "localhost"
  port: 5432
  database: "grcclaw"
  username: "grcclaw"
  password: "grcclaw"

redis:
  host: "localhost"
  port: 6379

enforcement:
  default_fail_mode: "closed"
  auto_approve_threshold: 0.90
  human_review_threshold: 0.85

discovery:
  enabled: true
  interval_seconds: 3600

monitoring:
  enabled: true
  interval_seconds: 60
  drift_threshold: 0.1

evidence:
  hash_algorithm: "SHA-256"
  retention_days: 2555  # 7 years
```

---

## 14. Testing Framework

### 14.1 Test Configuration

```python
# tests/conftest.py

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import pytest
import pytest_asyncio

from grc_claw.enforcement.engine import (
    ActionType,
    DeterministicEnforcementEngine,
    EnforcementRequest,
)
from grc_claw.modules.policy import (
    Policy,
    PolicyCategory,
    PolicyRule,
    PolicyScope,
    PolicyStatus,
)


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def enforcement_engine():
    """Create a test enforcement engine."""
    engine = DeterministicEnforcementEngine(
        policy_store=MockPolicyStore(),
        evidence_collector=MockEvidenceCollector(),
    )
    yield engine


@pytest.fixture
def sample_policy():
    """Create a sample policy for testing."""
    return Policy(
        id="test-policy-1",
        name="Test Policy",
        description="A test policy",
        version="1.0.0",
        status=PolicyStatus.ACTIVE,
        category=PolicyCategory.DATA_HANDLING,
        rules=[
            PolicyRule(
                id="rule-1",
                name="Deny external API calls",
                description="Deny calls to external APIs",
                condition={
                    "action_type": "api_request",
                    "resource": {"contains": "external"},
                },
                action="deny",
                priority=100,
            ),
            PolicyRule(
                id="rule-2",
                name="Require approval for data access",
                description="Require approval for sensitive data access",
                condition={
                    "action_type": "data_access",
                    "risk_tier": "high",
                },
                action="require_approval",
                priority=90,
            ),
        ],
        scope=PolicyScope(
            agents=[],
            environments=["prod"],
        ),
        enforcement_mode="enforce",
        fail_mode="closed",
    )


@pytest.fixture
def sample_request():
    """Create a sample enforcement request."""
    return EnforcementRequest(
        request_id=str(uuid.uuid4()),
        agent_id="test-agent-1",
        action_type=ActionType.API_REQUEST,
        resource="https://external-api.example.com/data",
        parameters={"key": "value"},
        context={"environment": "prod"},
    )


class MockPolicyStore:
    """Mock policy store for testing."""

    def __init__(self):
        self.policies: list[Policy] = []

    async def get_active_policies_for_agent(self, agent_id: str) -> list[Policy]:
        return [p for p in self.policies if p.status == PolicyStatus.ACTIVE]


class MockEvidenceCollector:
    """Mock evidence collector for testing."""

    async def collect_enforcement_evidence(self, decision: Any) -> list[str]:
        return [f"evidence-{uuid.uuid4()}"]
```

### 14.2 Module Tests

```python
# tests/test_enforcement.py

from __future__ import annotations

import pytest

from grc_claw.enforcement.engine import ActionType, DecisionType, EnforcementRequest
from grc_claw.modules.policy import PolicyStatus


@pytest.mark.asyncio
async def test_enforce_action_allow(enforcement_engine, sample_policy, sample_request):
    """Test that a non-matching action is allowed."""
    enforcement_engine.policy_store.policies = [sample_policy]
    sample_request.resource = "https://internal-api.example.com/data"

    decision = await enforcement_engine.evaluate(sample_request)

    assert decision.decision == DecisionType.ALLOW
    assert decision.deterministic is True
    assert decision.confidence_score == 1.0


@pytest.mark.asyncio
async def test_enforce_action_deny(enforcement_engine, sample_policy, sample_request):
    """Test that a matching deny rule blocks the action."""
    enforcement_engine.policy_store.policies = [sample_policy]
    sample_request.resource = "https://external-api.example.com/data"

    decision = await enforcement_engine.evaluate(sample_request)

    assert decision.decision == DecisionType.DENY
    assert decision.policy_id == sample_policy.id
    assert len(decision.rules_evaluated) > 0


@pytest.mark.asyncio
async def test_enforce_action_require_approval(enforcement_engine, sample_policy):
    """Test that a matching rule requires approval."""
    enforcement_engine.policy_store.policies = [sample_policy]

    request = EnforcementRequest(
        request_id="test-req-1",
        agent_id="test-agent-1",
        action_type=ActionType.DATA_ACCESS,
        resource="s3://sensitive-data/",
        context={"environment": "prod", "risk_tier": "high"},
    )

    decision = await enforcement_engine.evaluate(request)

    assert decision.decision == DecisionType.REQUIRE_APPROVAL
    assert decision.escalation is not None
    assert decision.escalation.status == "pending"


@pytest.mark.asyncio
async def test_enforce_no_policies_allow(enforcement_engine, sample_request):
    """Test that no policies results in allow."""
    enforcement_engine.policy_store.policies = []

    decision = await enforcement_engine.evaluate(sample_request)

    assert decision.decision == DecisionType.ALLOW
    assert decision.reason == "No applicable policies found"


@pytest.mark.asyncio
async def test_enforce_fail_closed(enforcement_engine, sample_policy, sample_request):
    """Test fail-closed behavior when no rules match."""
    enforcement_engine.policy_store.policies = [sample_policy]
    sample_request.action_type = ActionType.FILE_ACCESS
    sample_request.resource = "/tmp/test.txt"
    sample_request.context = {"environment": "dev"}  # Not in scope

    decision = await enforcement_engine.evaluate(sample_request)

    assert decision.decision == DecisionType.DENY
    assert "fail_mode" in decision.reason


@pytest.mark.asyncio
async def test_enforce_redaction(enforcement_engine, sample_policy):
    """Test redaction of sensitive fields."""
    from grc_claw.modules.policy import PolicyRule

    # Add a redaction rule
    sample_policy.rules.append(PolicyRule(
        id="rule-redact",
        name="Redact PII",
        description="Redact PII fields",
        condition={"action_type": "data_access"},
        action="redact",
        priority=80,
        metadata={"sensitive_fields": ["ssn", "email"]},
    ))
    enforcement_engine.policy_store.policies = [sample_policy]

    request = EnforcementRequest(
        request_id="test-redact-1",
        agent_id="test-agent-1",
        action_type=ActionType.DATA_ACCESS,
        resource="database://users",
        parameters={"ssn": "123-45-6789", "email": "test@example.com", "name": "Test"},
        context={"environment": "prod"},
    )

    decision = await enforcement_engine.evaluate(request)

    assert decision.decision == DecisionType.ALLOW_WITH_REDACTION
    assert decision.redaction is not None
    assert "ssn" in decision.redaction.fields_redacted
    assert "email" in decision.redaction.fields_redacted
```

```python
# tests/test_discovery.py

from __future__ import annotations

import pytest

from grc_claw.modules.discovery import (
    AssetType,
    DiscoveredAsset,
    RepositoryScanner,
)


@pytest.mark.asyncio
async def test_repository_scanner_discovers_ai_libraries(tmp_path):
    """Test that the scanner detects AI library usage."""
    # Create a mock requirements.txt
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("torch>=2.0.0\ntransformers>=4.30.0\n")

    scanner = RepositoryScanner(repo_paths=[str(tmp_path)])
    assets = []
    async for asset in scanner.discover():
        assets.append(asset)

    assert len(assets) >= 2
    lib_names = [a.metadata.get("library") for a in assets]
    assert "pytorch" in lib_names
    assert "huggingface" in lib_names


@pytest.mark.asyncio
async def test_repository_scanner_discovers_model_files(tmp_path):
    """Test that the scanner detects model files."""
    # Create a mock model file
    model_file = tmp_path / "model.pt"
    model_file.write_bytes(b"mock model data")

    scanner = RepositoryScanner(repo_paths=[str(tmp_path)])
    assets = []
    async for asset in scanner.discover():
        assets.append(asset)

    model_assets = [a for a in assets if a.type == AssetType.MODEL]
    assert len(model_assets) >= 1
    assert model_assets[0].name == "model"


@pytest.mark.asyncio
async def test_discovered_asset_generates_id():
    """Test that discovered assets get deterministic IDs."""
    asset = DiscoveredAsset(
        id="",
        type=AssetType.MODEL,
        name="test-model",
        source="test",
    )
    assert asset.id != ""
    assert len(asset.id) == 16
```

```python
# tests/test_policy.py

from __future__ import annotations

import pytest

from grc_claw.modules.policy import PolicyCompiler, PolicyRule


def test_policy_compiler_generates_rego(sample_policy):
    """Test that the policy compiler generates valid Rego."""
    compiler = PolicyCompiler()
    compiled = compiler.compile_policy(sample_policy)

    assert compiled["policy_id"] == sample_policy.id
    assert compiled["rules_count"] == len(sample_policy.rules)
    assert "package grcclaw" in compiled["rego_module"]
    assert "default allow" in compiled["rego_module"]


def test_policy_rule_condition_evaluation():
    """Test rule condition evaluation logic."""
    from grc_claw.enforcement.engine import DeterministicEnforcementEngine, EnforcementRequest, ActionType

    engine = DeterministicEnforcementEngine(None, None)

    request = EnforcementRequest(
        request_id="test",
        agent_id="agent-1",
        action_type=ActionType.API_REQUEST,
        resource="https://external-api.com",
        context={"environment": "prod", "risk_tier": "high"},
    )

    # Test eq condition
    assert engine._evaluate_condition("api_request", {"eq": "api_request"}) is True
    assert engine._evaluate_condition("api_request", {"eq": "data_access"}) is False

    # Test contains condition
    assert engine._evaluate_condition("https://external-api.com", {"contains": "external"}) is True

    # Test lt condition
    assert engine._evaluate_condition(0.5, {"lt": 1.0}) is True
    assert engine._evaluate_condition(1.5, {"lt": 1.0}) is False

    # Test in condition
    assert engine._evaluate_condition("prod", {"in": ["prod", "staging"]}) is True
    assert engine._evaluate_condition("dev", {"in": ["prod", "staging"]}) is False
```

### 14.3 Integration Tests

```python
# tests/test_integration.py

from __future__ import annotations

import pytest
import pytest_asyncio

from grc_claw.enforcement.engine import ActionType, DecisionType, EnforcementRequest
from grc_claw.modules.policy import Policy, PolicyRule, PolicyScope, PolicyStatus


@pytest.mark.asyncio
async def test_end_to_end_enforcement_flow(enforcement_engine):
    """Test the complete enforcement flow from policy to decision."""
    # 1. Create a policy
    policy = Policy(
        id="integration-test-policy",
        name="Integration Test Policy",
        status=PolicyStatus.ACTIVE,
        rules=[
            PolicyRule(
                id="deny-external",
                name="Deny External APIs",
                condition={"action_type": "api_request", "resource": {"contains": "external"}},
                action="deny",
                priority=100,
            ),
        ],
        scope=PolicyScope(environments=["prod"]),
        fail_mode="closed",
    )
    enforcement_engine.policy_store.policies = [policy]

    # 2. Create a request that should be denied
    request = EnforcementRequest(
        request_id="int-test-1",
        agent_id="agent-1",
        action_type=ActionType.API_REQUEST,
        resource="https://external-api.example.com",
        context={"environment": "prod"},
    )

    # 3. Evaluate
    decision = await enforcement_engine.evaluate(request)

    # 4. Assert
    assert decision.decision == DecisionType.DENY
    assert decision.policy_id == policy.id
    assert decision.deterministic is True
    assert decision.evaluation_latency_ms >= 0
    assert len(decision.evidence_ids) > 0


@pytest.mark.asyncio
async def test_enforcement_stats_tracking(enforcement_engine, sample_policy):
    """Test that enforcement stats are tracked correctly."""
    enforcement_engine.policy_store.policies = [sample_policy]

    # Make several requests
    for i in range(5):
        request = EnforcementRequest(
            request_id=f"stats-test-{i}",
            agent_id="agent-1",
            action_type=ActionType.API_REQUEST,
            resource=f"https://external-api-{i}.example.com",
            context={"environment": "prod"},
        )
        await enforcement_engine.evaluate(request)

    stats = enforcement_engine.get_stats()
    assert stats["total_decisions"] == 5
    assert stats["by_decision"]["DENY"] == 5
```

### 14.4 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/grc_claw --cov-report=html

# Run specific module tests
pytest tests/test_enforcement.py -v

# Run with async support
pytest tests/ -v --asyncio-mode=auto
```

---

## 15. Deployment Guide

### 15.1 Docker Compose (Development)

```yaml
# docker-compose.yml
version: "3.9"

services:
  grc-claw-api:
    build:
      context: .
      dockerfile: deployments/docker/Dockerfile
    ports:
      - "8080:8080"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USERNAME=neo4j
      - NEO4J_PASSWORD=password
      - KAFKA_BROKERS=kafka:9092
      - POSTGRES_HOST=postgres
      - POSTGRES_PASSWORD=grcclaw
      - REDIS_HOST=redis
    depends_on:
      - neo4j
      - kafka
      - postgres
      - redis
    volumes:
      - ./config:/app/config

  grc-claw-mcp:
    build:
      context: .
      dockerfile: deployments/docker/Dockerfile.mcp
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - neo4j
      - kafka

  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=grcclaw
      - POSTGRES_USER=grcclaw
      - POSTGRES_PASSWORD=grcclaw
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  neo4j_data:
  postgres_data:
```

### 15.2 Dockerfile

```dockerfile
# deployments/docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

# Copy source
COPY src/ src/
COPY config/ config/

# Run
CMD ["python", "-m", "grc_claw.main"]
```

```dockerfile
# deployments/docker/Dockerfile.mcp
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

COPY src/ src/
COPY config/ config/

CMD ["python", "-m", "grc_claw.mcp.server"]
```

### 15.3 Kubernetes Deployment

```yaml
# deployments/k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: grc-claw
```

```yaml
# deployments/k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grc-claw-config
  namespace: grc-claw
data:
  default.yaml: |
    app:
      name: "GRC_Claw Automation Engine"
      environment: "production"
      log_level: "INFO"
    neo4j:
      uri: "bolt://neo4j:7687"
      username: "neo4j"
      password: "${NEO4J_PASSWORD}"
    kafka:
      brokers: ["kafka:9092"]
    postgresql:
      host: "postgres"
      database: "grcclaw"
```

```yaml
# deployments/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grc-claw-api
  namespace: grc-claw
spec:
  replicas: 3
  selector:
    matchLabels:
      app: grc-claw-api
  template:
    metadata:
      labels:
        app: grc-claw-api
    spec:
      containers:
        - name: api
          image: grc-claw:latest
          ports:
            - containerPort: 8080
          env:
            - name: NEO4J_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: grc-claw-secrets
                  key: neo4j-password
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grc-claw-mcp
  namespace: grc-claw
spec:
  replicas: 2
  selector:
    matchLabels:
      app: grc-claw-mcp
  template:
    metadata:
      labels:
        app: grc-claw-mcp
    spec:
      containers:
        - name: mcp
          image: grc-claw-mcp:latest
          env:
            - name: NEO4J_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: grc-claw-secrets
                  key: neo4j-password
```

```yaml
# deployments/k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: grc-claw-api
  namespace: grc-claw
spec:
  selector:
    app: grc-claw-api
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
```

```yaml
# deployments/k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grc-claw-api-hpa
  namespace: grc-claw
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grc-claw-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### 15.4 Production Deployment Steps

```bash
# 1. Build images
docker build -t grc-claw:latest -f deployments/docker/Dockerfile .
docker build -t grc-claw-mcp:latest -f deployments/docker/Dockerfile.mcp .

# 2. Run tests
pytest tests/ -v --cov=src/grc_claw

# 3. Push to registry
docker tag grc-claw:latest registry.example.com/grc-claw:latest
docker push registry.example.com/grc-claw:latest

# 4. Deploy to Kubernetes
kubectl apply -f deployments/k8s/namespace.yaml
kubectl apply -f deployments/k8s/configmap.yaml
kubectl apply -f deployments/k8s/deployment.yaml
kubectl apply -f deployments/k8s/service.yaml
kubectl apply -f deployments/k8s/hpa.yaml

# 5. Verify deployment
kubectl get pods -n grc-claw
kubectl logs -n grc-claw -l app=grc-claw-api

# 6. Run database migrations
kubectl exec -n grc-claw deploy/grc-claw-api -- python -m grc_claw.migrate

# 7. Initialize schema
kubectl exec -n grc-claw deploy/grc-claw-api -- python -m grc_claw.init_schema
```

### 15.5 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GRC_CLAW_ENV` | Environment name | `development` |
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `KAFKA_BROKERS` | Kafka broker list | `localhost:9092` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `grcclaw` |
| `REDIS_HOST` | Redis host | `localhost` |
| `ENFORCEMENT_FAIL_MODE` | Default fail mode | `closed` |
| `AUTO_APPROVE_THRESHOLD` | Auto-approve confidence threshold | `0.90` |
| `HUMAN_REVIEW_THRESHOLD` | Human review confidence threshold | `0.85` |

### 15.6 Monitoring & Observability

```yaml
# Prometheus rules
groups:
  - name: grc-claw
    rules:
      - alert: HighEnforcementLatency
        expr: histogram_quantile(0.99, enforcement_latency_seconds) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Enforcement p99 latency exceeds 100ms"

      - alert: ComplianceScoreDrop
        expr: compliance_score < 0.75
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Compliance score below 75%"

      - alert: AuditChainIntegrityFailure
        expr: audit_chain_integrity == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Audit chain integrity check failed"

      - alert: AgentTrustScoreDrop
        expr: agent_trust_score < 0.20
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Agent trust score below 0.20"
```

---

## Appendix A: API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/policies` | List policies |
| POST | `/v1/policies` | Create policy |
| GET | `/v1/policies/{id}` | Get policy |
| POST | `/v1/policies/{id}/activate` | Activate policy |
| POST | `/v1/policies/{id}/compile` | Compile to Rego |
| GET | `/v1/evidence` | List evidence |
| POST | `/v1/evidence` | Submit evidence |
| POST | `/v1/evidence/{id}/verify` | Verify evidence |
| POST | `/v1/enforcements` | Evaluate action |
| GET | `/v1/enforcements/stats` | Enforcement stats |
| GET | `/v1/agents` | List agents |
| POST | `/v1/agents` | Register agent |
| POST | `/v1/agents/{id}/attest` | Attest agent |
| GET | `/v1/compliance/{framework}` | Get compliance |
| POST | `/v1/compliance/{framework}/compute` | Compute compliance |
| GET | `/v1/audit-trail` | Query audit trail |
| POST | `/v1/audit-trail/verify` | Verify chain |

## Appendix B: MCP Tools Summary

| Tool | Description |
|------|-------------|
| `enforce_action` | Evaluate agent action against policies |
| `get_asset_inventory` | Get AI asset inventory |
| `get_asset_dependencies` | Get dependency graph |
| `get_evidence_pack` | Generate audit evidence pack |
| `get_enforcement_stats` | Get enforcement statistics |
| `verify_audit_chain` | Verify audit chain integrity |

---

*End of GRC_Claw Implementation Guide*
       </longcat_think>
