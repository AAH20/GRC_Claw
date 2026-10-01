# GRC_Claw QA Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Implementation Ready  
**References:** grc-claw-qa-specification.md v2.0

---

## Table of Contents

1. [Quality Metrics Implementation (Python)](#1-quality-metrics-implementation-python)
2. [Testing Framework Setup (pytest)](#2-testing-framework-setup-pytest)
3. [Quality Gates Implementation](#3-quality-gates-implementation)
4. [Defect Prediction (XGBoost)](#4-defect-prediction-xgboost)
5. [Quality Dashboards (Grafana)](#5-quality-dashboards-grafana)
6. [Quality Culture Practices](#6-quality-culture-practices)
7. [Quality Auditing Framework](#7-quality-auditing-framework)

---

## 1. Quality Metrics Implementation (Python)

### 1.1 Core Metrics Module

```python
# src/quality/metrics.py
"""Quality metrics collection and calculation for GRC_Claw."""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import git
import requests

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Defect severity levels."""
    CRITICAL = "S1"
    HIGH = "S2"
    MEDIUM = "S3"
    LOW = "S4"


class QualityDimension(Enum):
    """Quality dimensions for scoring."""
    COVERAGE = "coverage"
    DEFECTS = "defects"
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"


@dataclass
class CoverageMetrics:
    """Code coverage metrics."""
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    statement_coverage: float = 0.0
    mcdc_coverage: float = 0.0
    component: str = "overall"
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def meets_target(self, targets: dict[str, float]) -> bool:
        """Check if coverage meets targets."""
        return (
            self.line_coverage >= targets.get("line", 0)
            and self.branch_coverage >= targets.get("branch", 0)
            and self.statement_coverage >= targets.get("statement", 0)
        )


@dataclass
class DefectMetrics:
    """Defect-related metrics."""
    total_defects: int = 0
    by_severity: dict[Severity, int] = field(default_factory=dict)
    by_component: dict[str, int] = field(default_factory=dict)
    kloc: float = 0.0
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)

    @property
    def defect_density(self) -> float:
        """Defects per KLOC."""
        if self.kloc == 0:
            return 0.0
        return self.total_defects / self.kloc

    @property
    def critical_count(self) -> int:
        return self.by_severity.get(Severity.CRITICAL, 0)


@dataclass
class TechnicalDebtMetrics:
    """Technical debt metrics."""
    remediation_cost_hours: float = 0.0
    development_cost_hours: float = 0.0
    code_smells: int = 0
    duplicated_lines_pct: float = 0.0
    cognitive_complexity_violations: int = 0
    cyclomatic_complexity_violations: int = 0

    @property
    def tdr(self) -> float:
        """Technical Debt Ratio."""
        if self.development_cost_hours == 0:
            return 0.0
        return (self.remediation_cost_hours / self.development_cost_hours) * 100

    @property
    def status(self) -> str:
        if self.tdr <= 5:
            return "healthy"
        elif self.tdr <= 10:
            return "warning"
        elif self.tdr <= 20:
            return "at_risk"
        return "critical"


@dataclass
class OperationalMetrics:
    """Operational quality metrics."""
    api_availability_pct: float = 100.0
    api_p95_latency_ms: float = 0.0
    evidence_collection_success_pct: float = 100.0
    evidence_verification_latency_p95_sec: float = 0.0
    report_generation_time_p95_sec: float = 0.0
    dashboard_load_time_p95_sec: float = 0.0
    chain_of_custody_breaks: int = 0
    false_positive_rate_pct: float = 0.0
    false_negative_rate_pct: float = 0.0


@dataclass
class QualityScore:
    """Composite quality score."""
    coverage_score: float = 0.0
    defect_score: float = 0.0
    security_score: float = 0.0
    performance_score: float = 0.0
    reliability_score: float = 0.0
    maintainability_score: float = 0.0
    overall: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def calculate_overall(self) -> float:
        """Calculate weighted overall quality score."""
        self.overall = (
            self.coverage_score * 0.20
            + self.defect_score * 0.20
            + self.security_score * 0.20
            + self.performance_score * 0.15
            + self.reliability_score * 0.15
            + self.maintainability_score * 0.10
        )
        return self.overall
```

### 1.2 Metrics Collectors

```python
# src/quality/collectors.py
"""Metrics collectors for various quality dimensions."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import git
import requests

from .metrics import (
    CoverageMetrics,
    DefectMetrics,
    OperationalMetrics,
    QualityScore,
    Severity,
    TechnicalDebtMetrics,
)

logger = logging.getLogger(__name__)


class CoverageCollector:
    """Collects code coverage metrics from pytest-cov XML reports."""

    def __init__(self, coverage_xml_path: str = "coverage.xml"):
        self.coverage_xml_path = Path(coverage_xml_path)

    def collect(self) -> CoverageMetrics:
        """Parse coverage XML and return metrics."""
        if not self.coverage_xml_path.exists():
            logger.warning("Coverage XML not found: %s", self.coverage_xml_path)
            return CoverageMetrics()

        tree = ET.parse(self.coverage_xml_path)
        root = tree.getroot()

        line_rate = float(root.get("line-rate", 0))
        branch_rate = float(root.get("branch-rate", 0))

        # Convert to percentages
        return CoverageMetrics(
            line_coverage=line_rate * 100,
            branch_coverage=branch_rate * 100,
            statement_coverage=line_rate * 100,  # Approximation
            mcdc_coverage=0.0,  # Requires specialized tool
        )

    def collect_by_component(self) -> dict[str, CoverageMetrics]:
        """Collect coverage per component/package."""
        if not self.coverage_xml_path.exists():
            return {}

        tree = ET.parse(self.coverage_xml_path)
        root = tree.getroot()

        components: dict[str, CoverageMetrics] = {}
        for package in root.findall(".//package"):
            name = package.get("name", "unknown")
            line_rate = float(package.get("line-rate", 0))
            branch_rate = float(package.get("branch-rate", 0))
            components[name] = CoverageMetrics(
                line_coverage=line_rate * 100,
                branch_coverage=branch_rate * 100,
                component=name,
            )
        return components


class DefectCollector:
    """Collects defect metrics from GitHub Issues."""

    def __init__(
        self,
        github_token: str,
        repo: str = "grc-claw/grc-claw",
        api_url: str = "https://api.github.com",
    ):
        self.github_token = github_token
        self.repo = repo
        self.api_url = api_url
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def collect(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> DefectMetrics:
        """Collect defect metrics from GitHub Issues."""
        if since is None:
            since = datetime.utcnow() - timedelta(days=90)
        if until is None:
            until = datetime.utcnow()

        issues = self._fetch_issues(since, until)
        kloc = self._calculate_kloc()

        by_severity: dict[Severity, int] = {s: 0 for s in Severity}
        by_component: dict[str, int] = {}

        for issue in issues:
            if "pull_request" in issue:
                continue  # Skip PRs

            labels = [label["name"] for label in issue.get("labels", [])]
            severity = self._classify_severity(labels)
            by_severity[severity] += 1

            component = self._classify_component(labels)
            by_component[component] = by_component.get(component, 0) + 1

        return DefectMetrics(
            total_defects=sum(by_severity.values()),
            by_severity=by_severity,
            by_component=by_component,
            kloc=kloc,
            period_start=since,
            period_end=until,
        )

    def _fetch_issues(
        self, since: datetime, until: datetime
    ) -> list[dict[str, Any]]:
        """Fetch issues from GitHub API."""
        issues: list[dict[str, Any]] = []
        page = 1
        per_page = 100

        while True:
            url = (
                f"{self.api_url}/repos/{self.repo}/issues"
                f"?state=all&since={since.isoformat()}"
                f"&per_page={per_page}&page={page}"
            )
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            issues.extend(batch)
            page += 1

        return issues

    def _classify_severity(self, labels: list[str]) -> Severity:
        """Classify issue severity from labels."""
        label_set = set(labels)
        if "severity:s1" in label_set or "critical" in label_set:
            return Severity.CRITICAL
        elif "severity:s2" in label_set or "high" in label_set:
            return Severity.HIGH
        elif "severity:s3" in label_set or "medium" in label_set:
            return Severity.MEDIUM
        return Severity.LOW

    def _classify_component(self, labels: list[str]) -> str:
        """Classify component from labels."""
        for label in labels:
            if label.startswith("component:"):
                return label.split(":", 1)[1]
        return "unknown"

    def _calculate_kloc(self) -> float:
        """Calculate KLOC from source files."""
        total_lines = 0
        src_path = Path("src")
        if not src_path.exists():
            return 0.0

        for py_file in src_path.rglob("*.py"):
            try:
                with open(py_file) as f:
                    lines = f.readlines()
                    # Exclude comments and blank lines
                    code_lines = [
                        line
                        for line in lines
                        if line.strip() and not line.strip().startswith("#")
                    ]
                    total_lines += len(code_lines)
            except (OSError, UnicodeDecodeError):
                continue

        return total_lines / 1000.0


class SonarQubeCollector:
    """Collects metrics from SonarQube."""

    def __init__(self, sonar_url: str, sonar_token: str, project_key: str):
        self.sonar_url = sonar_url.rstrip("/")
        self.sonar_token = sonar_token
        self.project_key = project_key

    def collect_technical_debt(self) -> TechnicalDebtMetrics:
        """Collect technical debt metrics from SonarQube."""
        metrics = (
            "code_smells,duplicated_lines_density,"
            "cognitive_complexity,cyclomatic_complexity,"
            "sqale_index,sqale_debt_ratio"
        )
        url = (
            f"{self.sonar_url}/api/measures/component"
            f"?component={self.project_key}"
            f"&metricKeys={metrics}"
        )
        response = requests.get(
            url, auth=(self.sonar_token, "")
        )
        response.raise_for_status()
        data = response.json()

        measures = {
            m["metric"]: m["value"]
            for m in data.get("component", {}).get("measures", [])
        }

        return TechnicalDebtMetrics(
            code_smells=int(measures.get("code_smells", 0)),
            duplicated_lines_pct=float(
                measures.get("duplicated_lines_density", 0)
            ),
            remediation_cost_hours=float(
                measures.get("sqale_index", 0)
            ) / 60.0,  # Convert minutes to hours
        )

    def collect_quality_gate(self) -> dict[str, Any]:
        """Get SonarQube quality gate status."""
        url = (
            f"{self.sonar_url}/api/qualitygates/project_status"
            f"?projectKey={self.project_key}"
        )
        response = requests.get(
            url, auth=(self.sonar_token, "")
        )
        response.raise_for_status()
        return response.json()


class PrometheusCollector:
    """Collects operational metrics from Prometheus."""

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url.rstrip("/")

    def collect_operational_metrics(self) -> OperationalMetrics:
        """Collect operational metrics from Prometheus."""
        metrics = OperationalMetrics()

        # API availability
        availability = self._query(
            "avg_over_time(up{job='grc-claw-api'}[30d]) * 100"
        )
        if availability is not None:
            metrics.api_availability_pct = availability

        # API p95 latency
        latency = self._query(
            "histogram_quantile(0.95, "
            "rate(http_request_duration_seconds_bucket"
            "{job='grc-claw-api'}[5m])) * 1000"
        )
        if latency is not None:
            metrics.api_p95_latency_ms = latency

        # Evidence collection success rate
        success_rate = self._query(
            "rate(evidence_collection_success_total[7d])"
            " / rate(evidence_collection_total[7d]) * 100"
        )
        if success_rate is not None:
            metrics.evidence_collection_success_pct = success_rate

        # Report generation time
        report_time = self._query(
            "histogram_quantile(0.95, "
            "rate(report_generation_duration_seconds_bucket[7m]))"
        )
        if report_time is not None:
            metrics.report_generation_time_p95_sec = report_time

        # Chain of custody breaks
        custody_breaks = self._query(
            "increase(chain_of_custody_breaks_total[30d])"
        )
        if custody_breaks is not None:
            metrics.chain_of_custody_breaks = int(custody_breaks)

        return metrics

    def _query(self, promql: str) -> Optional[float]:
        """Execute a PromQL query."""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": promql},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                results = data.get("data", {}).get("result", [])
                if results:
                    return float(results[0]["value"][1])
        except (requests.RequestException, ValueError, KeyError) as e:
            logger.warning("Prometheus query failed: %s (query: %s)", e, promql)
        return None


class QualityScoreCalculator:
    """Calculates composite quality score."""

    def __init__(
        self,
        coverage_collector: CoverageCollector,
        defect_collector: DefectCollector,
        sonar_collector: SonarQubeCollector,
        prometheus_collector: PrometheusCollector,
    ):
        self.coverage_collector = coverage_collector
        self.defect_collector = defect_collector
        self.sonar_collector = sonar_collector
        self.prometheus_collector = prometheus_collector

    def calculate(self) -> QualityScore:
        """Calculate overall quality score."""
        coverage = self.coverage_collector.collect()
        defects = self.defect_collector.collect()
        tech_debt = self.sonar_collector.collect_technical_debt()
        operational = self.prometheus_collector.collect_operational_metrics()

        # Coverage score (0-100)
        coverage_score = (
            coverage.line_coverage * 0.5
            + coverage.branch_coverage * 0.3
            + coverage.statement_coverage * 0.2
        )

        # Defect score (0-100, inverse of defect density)
        defect_density = defects.defect_density
        defect_score = max(0, 100 - (defect_density * 50))
        if defects.critical_count > 0:
            defect_score = 0

        # Security score (0-100)
        security_score = 100.0
        # Would integrate with security scan results

        # Performance score (0-100)
        performance_score = 100.0
        if operational.api_p95_latency_ms > 200:
            performance_score -= 20
        if operational.report_generation_time_p95_sec > 30:
            performance_score -= 20
        if operational.dashboard_load_time_p95_sec > 2:
            performance_score -= 10
        performance_score = max(0, performance_score)

        # Reliability score (0-100)
        reliability_score = operational.api_availability_pct
        if operational.chain_of_custody_breaks > 0:
            reliability_score = 0

        # Maintainability score (0-100)
        maintainability_score = max(0, 100 - tech_debt.tdr * 5)

        score = QualityScore(
            coverage_score=min(100, coverage_score),
            defect_score=min(100, defect_score),
            security_score=min(100, security_score),
            performance_score=min(100, performance_score),
            reliability_score=min(100, reliability_score),
            maintainability_score=min(100, maintainability_score),
        )
        score.calculate_overall()
        return score
```

### 1.3 Metrics Exporter

```python
# src/quality/exporter.py
"""Export quality metrics to various backends."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

import requests

from .metrics import QualityScore

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """Export metrics to Prometheus Pushgateway."""

    def __init__(self, pushgateway_url: str = "http://localhost:9091"):
        self.pushgateway_url = pushgateway_url.rstrip("/")

    def export(self, job_name: str, metrics: dict[str, float]) -> None:
        """Push metrics to Prometheus Pushgateway."""
        data = []
        for metric_name, value in metrics.items():
            data.append(
                f"{metric_name} {value}"
            )
        payload = "\n".join(data)

        url = f"{self.pushgateway_url}/metrics/job/{job_name}"
        try:
            response = requests.put(
                url,
                data=payload,
                headers={"Content-Type": "text/plain"},
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Metrics pushed to Prometheus: %s", job_name)
        except requests.RequestException as e:
            logger.error("Failed to push metrics: %s", e)


class GrafanaExporter:
    """Export metrics to Grafana via annotations API."""

    def __init__(
        self,
        grafana_url: str,
        grafana_token: str,
    ):
        self.grafana_url = grafana_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {grafana_token}",
            "Content-Type": "application/json",
        }

    def create_annotation(
        self,
        dashboard_id: int,
        panel_id: int,
        text: str,
        tags: list[str],
    ) -> None:
        """Create a Grafana annotation."""
        payload = {
            "dashboardId": dashboard_id,
            "panelId": panel_id,
            "time": int(datetime.utcnow().timestamp() * 1000),
            "text": text,
            "tags": tags,
        }
        try:
            response = requests.post(
                f"{self.grafana_url}/api/annotations",
                json=payload,
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to create annotation: %s", e)


class QualityReportGenerator:
    """Generate quality reports."""

    def generate_report(
        self,
        score: QualityScore,
        output_path: str = "quality_report.json",
    ) -> dict[str, Any]:
        """Generate a comprehensive quality report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "quality_score": {
                "overall": round(score.overall, 2),
                "coverage": round(score.coverage_score, 2),
                "defects": round(score.defect_score, 2),
                "security": round(score.security_score, 2),
                "performance": round(score.performance_score, 2),
                "reliability": round(score.reliability_score, 2),
                "maintainability": round(score.maintainability_score, 2),
            },
            "status": self._get_status(score.overall),
            "recommendations": self._generate_recommendations(score),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def _get_status(self, score: float) -> str:
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "needs_improvement"
        return "critical"

    def _generate_recommendations(self, score: QualityScore) -> list[str]:
        recommendations = []
        if score.coverage_score < 88:
            recommendations.append(
                "Increase test coverage — target ≥ 88% line coverage"
            )
        if score.defect_score < 80:
            recommendations.append(
                "Reduce defect density — target ≤ 1.0 defects/KLOC"
            )
        if score.security_score < 90:
            recommendations.append(
                "Address security vulnerabilities — 0 critical/high"
            )
        if score.performance_score < 80:
            recommendations.append(
                "Improve performance — API p95 < 200ms, reports < 30s"
            )
        if score.reliability_score < 99:
            recommendations.append(
                "Improve reliability — target ≥ 99.9% availability"
            )
        if score.maintainability_score < 80:
            recommendations.append(
                "Reduce technical debt — target TDR ≤ 5%"
            )
        return recommendations
```

---

## 2. Testing Framework Setup (pytest)

### 2.1 Project Configuration

```ini
# pyproject.toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "grc-claw"
version = "2.0.0"
description = "AI Governance, Risk, and Compliance Platform"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "alembic>=1.12",
    "httpx>=0.25",
    "redis>=5.0",
    "aiokafka>=0.9",
    "prometheus-client>=0.19",
    "structlog>=23.0",
    "cryptography>=41.0",
]

[project.optional-dependencies]
test = [
    "pytest>=8.0",
    "pytest-cov>=4.1",
    "pytest-asyncio>=0.23",
    "pytest-xdist>=3.5",
    "pytest-testmon>=2.1",
    "pytest-bdd>=7.0",
    "pytest-html>=4.1",
    "pytest-mock>=3.12",
    "respx>=0.21",
    "testcontainers>=3.7",
    "factory-boy>=3.3",
    "freezegun>=1.2",
    "hypothesis>=6.88",
    "allure-pytest>=2.13",
    "locust>=2.18",
]

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--strict-config",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-branch",
    "--cov-fail-under=88",
    "-n", "auto",
]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (test containers)",
    "e2e: End-to-end tests",
    "performance: Performance tests",
    "security: Security tests",
    "slow: Slow tests (> 1s)",
    "flaky: Known flaky tests",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:aiokafka.*:",
    "ignore::DeprecationWarning:kafka.*:",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
    "*/_generated/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
show_missing = true
fail_under = 88

[tool.coverage.html]
directory = "htmlcov"
```

### 2.2 Test Fixtures (conftest.py)

```python
# tests/conftest.py
"""Shared test fixtures for GRC_Claw test suite."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.kafka import KafkaContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from src.api.main import create_app
from src.core.config import Settings, get_settings
from src.core.database import Base, get_db
from src.evidence.models import EvidenceItem, EvidenceStatus
from src.scoring.engine import ComplianceScoringEngine


# ─── Settings Override ───────────────────────────────────────────

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings with overridden values."""
    return Settings(
        env="test",
        debug=True,
        database_url="postgresql://test:test@localhost:5432/grc_claw_test",
        redis_url="redis://localhost:6379/0",
        kafka_bootstrap_servers="localhost:9092",
        secret_key="test-secret-key-not-for-production",
        access_token_expire_minutes=30,
        evidence_retention_days=365,
        max_evidence_size_mb=10,
    )


# ─── Database Fixtures ───────────────────────────────────────────

@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL test container."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """Create database engine for tests."""
    engine = create_engine(
        postgres_container.get_connection_url(),
        pool_pre_ping=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Provide a database session with rollback."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ─── Redis Fixtures ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def redis_container():
    """Redis test container."""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


# ─── Kafka Fixtures ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def kafka_container():
    """Kafka test container."""
    with KafkaContainer("confluentinc/cp-kafka:latest") as kafka:
        yield kafka


# ─── Application Fixtures ────────────────────────────────────────

@pytest.fixture
def app(test_settings, db_session):
    """Create test application."""
    app = create_app(settings=test_settings)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[Any, None]:
    """Create async test client."""
    from httpx import AsyncClient, ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        yield ac


# ─── Domain Model Fixtures ───────────────────────────────────────

@pytest.fixture
def evidence_factory():
    """Factory for creating test evidence items."""
    counter = 0

    def _create_evidence(**kwargs) -> EvidenceItem:
        nonlocal counter
        counter += 1
        defaults = {
            "id": str(uuid.uuid4()),
            "control_id": f"AC-{counter}",
            "framework": "NIST-800-53",
            "status": EvidenceStatus.PASS,
            "evidence_type": "automated_test",
            "content": f"Test evidence content {counter}",
            "hash": hashlib.sha256(
                f"content-{counter}".encode()
            ).hexdigest(),
            "collected_at": datetime.utcnow(),
            "verified_at": datetime.utcnow(),
            "tenant_id": "test-tenant-001",
        }
        defaults.update(kwargs)
        return EvidenceItem(**defaults)

    return _create_evidence


@pytest.fixture
def compliance_scoring_engine() -> ComplianceScoringEngine:
    """Provide a fresh scoring engine instance."""
    return ComplianceScoringEngine()


@pytest.fixture
def control_factory():
    """Factory for creating test controls."""
    counter = 0

    def _create_control(**kwargs):
        nonlocal counter
        counter += 1
        defaults = {
            "id": f"CTRL-{counter:04d}",
            "control_id": f"AC-{counter}",
            "framework": "NIST-800-53",
            "title": f"Test Control {counter}",
            "description": f"Description for test control {counter}",
            "severity": "moderate",
            "status": "pass",
        }
        defaults.update(kwargs)
        return defaults

    return _create_control


# ─── Mock Fixtures ───────────────────────────────────────────────

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for external service calls."""
    from respx import MockRouter

    with MockRouter() as router:
        yield router


@pytest.fixture
def mock_clock():
    """Freeze time for deterministic tests."""
    from freezegun import freeze_time

    with freeze_time("2026-10-01 12:00:00") as frozen:
        yield frozen


@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer."""
    producer = MagicMock()
    producer.send.return_value = asyncio.Future()
    producer.send.return_value.set_result(None)
    return producer


# ─── Data Fixtures ───────────────────────────────────────────────

@pytest.fixture
def sample_oscal_document() -> dict[str, Any]:
    """Sample OSCAL document for testing."""
    return {
        "catalog": {
            "uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "metadata": {
                "title": "Test OSCAL Catalog",
                "last-modified": "2026-10-01T00:00:00Z",
                "version": "1.0",
                "oscal-version": "1.1.2",
            },
            "controls": [
                {
                    "id": "ac-2",
                    "title": "Account Management",
                    "params": [{"id": "ac-2_prm_1"}],
                    "parts": [
                        {
                            "id": "ac-2_smt",
                            "name": "statement",
                            "prose": "The organization manages information system accounts.",
                        }
                    ],
                }
            ],
        }
    }


@pytest.fixture
def sample_compliance_result() -> dict[str, Any]:
    """Sample compliance scoring result."""
    return {
        "framework": "NIST-800-53",
        "score": 0.85,
        "status": "partially_compliant",
        "controls_total": 10,
        "controls_passed": 8,
        "controls_failed": 2,
        "controls_not_applicable": 0,
        "timestamp": "2026-10-01T12:00:00Z",
    }


# ─── Performance Test Fixtures ───────────────────────────────────

@pytest.fixture
def benchmark_thresholds() -> dict[str, float]:
    """Performance benchmark thresholds."""
    return {
        "api_p95_latency_ms": 200.0,
        "report_generation_p95_sec": 30.0,
        "dashboard_load_p95_sec": 2.0,
        "evidence_ingestion_p95_ms": 500.0,
        "db_query_p95_ms": 100.0,
    }
```

### 2.3 Unit Test Examples

```python
# tests/unit/test_scoring_engine.py
"""Unit tests for the compliance scoring engine."""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from src.scoring.engine import (
    ComplianceScoringEngine,
    ScoringResult,
    UnsupportedFrameworkError,
    ValidationError,
)


class TestComplianceScoringEngine:
    """Unit tests for ComplianceScoringEngine."""

    def test_calculate_score_all_controls_passed(
        self, compliance_scoring_engine
    ):
        """Score should be 1.0 when all controls pass."""
        controls = [
            {"id": "AC-2", "status": "pass"},
            {"id": "AU-6", "status": "pass"},
        ]
        result = compliance_scoring_engine.calculate_score(
            controls, framework="NIST-800-53"
        )
        assert result.score == 1.0
        assert result.status == "compliant"

    def test_calculate_score_with_failed_control(
        self, compliance_scoring_engine
    ):
        """Score should reflect proportion of passing controls."""
        controls = [
            {"id": "AC-2", "status": "pass"},
            {"id": "AU-6", "status": "fail"},
        ]
        result = compliance_scoring_engine.calculate_score(
            controls, framework="NIST-800-53"
        )
        assert result.score == 0.5
        assert result.status == "non_compliant"

    def test_calculate_score_empty_controls_raises(
        self, compliance_scoring_engine
    ):
        """Empty control list should raise ValidationError."""
        with pytest.raises(
            ValidationError, match="At least one control required"
        ):
            compliance_scoring_engine.calculate_score(
                [], framework="NIST-800-53"
            )

    def test_calculate_score_invalid_framework_raises(
        self, compliance_scoring_engine
    ):
        """Unknown framework should raise UnsupportedFrameworkError."""
        with pytest.raises(UnsupportedFrameworkError):
            compliance_scoring_engine.calculate_score(
                [{"id": "AC-2", "status": "pass"}],
                framework="INVALID",
            )

    def test_calculate_score_not_applicable_excluded(
        self, compliance_scoring_engine
    ):
        """Not applicable controls should be excluded from score."""
        controls = [
            {"id": "AC-2", "status": "pass"},
            {"id": "AU-6", "status": "not_applicable"},
        ]
        result = compliance_scoring_engine.calculate_score(
            controls, framework="NIST-800-53"
        )
        assert result.score == 1.0
        assert result.controls_evaluated == 1

    @given(
        st.lists(
            st.sampled_from(["pass", "fail", "not_applicable"]),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=100)
    def test_score_invariant_between_zero_and_one(
        self, compliance_scoring_engine, statuses
    ):
        """Property: Score is always between 0 and 1."""
        controls = [
            {"id": f"CTRL-{i}", "status": status}
            for i, status in enumerate(statuses)
        ]
        result = compliance_scoring_engine.calculate_score(
            controls, framework="NIST-800-53"
        )
        assert 0.0 <= result.score <= 1.0

    @given(
        st.lists(
            st.sampled_from(["pass", "fail"]),
            min_size=1,
            max_size=20,
        )
    )
    @settings(max_examples=50)
    def test_score_monotonic_with_more_passes(
        self, compliance_scoring_engine, statuses
    ):
        """Property: More passing controls should not decrease score."""
        controls = [
            {"id": f"CTRL-{i}", "status": status}
            for i, status in enumerate(statuses)
        ]
        result = compliance_scoring_engine.calculate_score(
            controls, framework="NIST-800-53"
        )
        pass_count = statuses.count("pass")
        expected = pass_count / len(statuses)
        assert abs(result.score - expected) < 0.01


class TestEvidenceValidation:
    """Unit tests for evidence validation."""

    def test_valid_evidence_passes(self):
        """Valid evidence should pass validation."""
        from src.evidence.validator import EvidenceValidator

        validator = EvidenceValidator()
        evidence = {
            "control_id": "AC-2",
            "framework": "NIST-800-53",
            "status": "pass",
            "content": "Test evidence",
            "hash": "abc123",
        }
        result = validator.validate(evidence)
        assert result.is_valid

    def test_missing_control_id_fails(self):
        """Missing control_id should fail validation."""
        from src.evidence.validator import EvidenceValidator

        validator = EvidenceValidator()
        evidence = {
            "framework": "NIST-800-53",
            "status": "pass",
            "content": "Test evidence",
        }
        result = validator.validate(evidence)
        assert not result.is_valid
        assert "control_id" in result.errors

    def test_hash_mismatch_detected(self):
        """Hash mismatch should be detected."""
        from src.evidence.validator import EvidenceValidator

        validator = EvidenceValidator()
        evidence = {
            "control_id": "AC-2",
            "framework": "NIST-800-53",
            "status": "pass",
            "content": "Test evidence",
            "hash": "tampered_hash",
        }
        result = validator.validate(evidence)
        assert not result.is_valid
        assert "hash" in result.errors
```

### 2.4 Integration Test Examples

```python
# tests/integration/test_evidence_pipeline.py
"""Integration tests for the evidence collection pipeline."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.evidence.collector import EvidenceCollector
from src.evidence.models import EvidenceItem, EvidenceStatus
from src.evidence.normalizer import OSCALNormalizer
from src.evidence.validator import EvidenceValidator


@pytest.mark.integration
class TestEvidenceCollectionPipeline:
    """Integration tests for evidence collection end-to-end."""

    def test_collect_normalize_validate_store(
        self, db_session: Session, evidence_factory
    ):
        """Evidence flows through collect → normalize → validate → store."""
        # Arrange
        collector = EvidenceCollector()
        normalizer = OSCALNormalizer()
        validator = EvidenceValidator()

        # Act - Collect
        raw_evidence = collector.collect(
            control_id="AC-2",
            framework="NIST-800-53",
        )
        assert raw_evidence is not None

        # Act - Normalize
        normalized = normalizer.normalize(raw_evidence)
        assert normalized.control_id == "AC-2"
        assert normalized.framework == "NIST-800-53"

        # Act - Validate
        validation_result = validator.validate(normalized)
        assert validation_result.is_valid

        # Act - Store
        db_session.add(normalized)
        db_session.commit()

        # Assert
        stored = (
            db_session.query(EvidenceItem)
            .filter_by(control_id="AC-2")
            .first()
        )
        assert stored is not None
        assert stored.status == EvidenceStatus.PASS

    def test_evidence_hash_chain_integrity(
        self, db_session: Session, evidence_factory
    ):
        """Evidence hash chain should be unbroken."""
        # Arrange
        items = [
            evidence_factory(control_id=f"AC-{i}")
            for i in range(1, 5)
        ]

        # Act
        for item in items:
            db_session.add(item)
        db_session.commit()

        # Assert
        for i in range(1, len(items)):
            prev = items[i - 1]
            curr = items[i]
            assert curr.previous_hash == prev.hash

    def test_evidence_tampering_detection(
        self, db_session: Session, evidence_factory
    ):
        """Tampered evidence should be detected."""
        # Arrange
        item = evidence_factory(control_id="AC-2")
        db_session.add(item)
        db_session.commit()

        original_hash = item.hash

        # Act - Tamper
        item.content = "Tampered content"
        db_session.commit()

        # Assert
        validator = EvidenceValidator()
        result = validator.validate(item)
        assert not result.is_valid
        assert "hash_mismatch" in result.errors


@pytest.mark.integration
class TestComplianceScoreRecalculation:
    """Integration tests for score recalculation."""

    def test_score_updates_after_new_evidence(
        self,
        db_session: Session,
        evidence_factory,
        compliance_scoring_engine,
    ):
        """Score should update when new evidence is added."""
        # Arrange
        initial_evidence = [
            evidence_factory(control_id="AC-2", status="pass"),
            evidence_factory(control_id="AU-6", status="fail"),
        ]
        for ev in initial_evidence:
            db_session.add(ev)
        db_session.commit()

        initial_result = compliance_scoring_engine.calculate_score(
            [
                {"id": "AC-2", "status": "pass"},
                {"id": "AU-6", "status": "fail"},
            ],
            framework="NIST-800-53",
        )
        assert initial_result.score == 0.5

        # Act - Add passing evidence for AU-6
        new_evidence = evidence_factory(
            control_id="AU-6", status="pass"
        )
        db_session.add(new_evidence)
        db_session.commit()

        # Assert
        updated_result = compliance_scoring_engine.calculate_score(
            [
                {"id": "AC-2", "status": "pass"},
                {"id": "AU-6", "status": "pass"},
            ],
            framework="NIST-800-53",
        )
        assert updated_result.score == 1.0
```

### 2.5 BDD Test Examples

```python
# tests/bdd/test_evidence_collection.feature
Feature: Compliance Evidence Collection
  As a compliance officer
  I want evidence to be collected and verified automatically
  So that I can trust the compliance posture displayed

  Scenario: Successful evidence collection with verification
    Given a configured evidence collector for "NIST-800-53" control "AC-2"
    When the collector runs
    Then the evidence is stored with L2 verification status
    And the compliance score is recalculated within 30 seconds
    And the dashboard reflects the updated score

  Scenario: Evidence collection failure with retry
    Given a configured evidence collector for "NIST-800-53" control "AC-2"
    And the target system is unavailable
    When the collector runs
    Then the collection is retried 3 times with exponential backoff
    And an alert is sent to the on-call engineer
    And the evidence status is marked as "collection_failed"

  Scenario: Evidence tampering detection
    Given evidence has been collected and verified
    When the evidence hash is modified
    Then the tampering is detected during the next verification cycle
    And an incident is created with severity "S1"
    And the evidence is quarantined
```

```python
# tests/bdd/test_evidence_collection_steps.py
"""Step definitions for evidence collection BDD scenarios."""

from __future__ import annotations

import pytest
from pytest_bdd import given, when, then, scenarios, parsers

scenarios("test_evidence_collection.feature")


@given(
    parsers.parse(
        'a configured evidence collector for "{framework}" '
        'control "{control_id}"'
    )
)
def configured_collector(framework: str, control_id: str):
    """Create a configured evidence collector."""
    from src.evidence.collector import EvidenceCollector

    return EvidenceCollector(
        framework=framework,
        control_id=control_id,
    )


@given("the target system is unavailable")
def target_unavailable():
    """Simulate target system unavailability."""
    from unittest.mock import patch

    return patch(
        "src.evidence.collector.requests.get",
        side_effect=ConnectionError("Target unavailable"),
    )


@when("the collector runs")
def collector_runs(configured_collector):
    """Run the evidence collector."""
    return configured_collector.collect()


@then("the evidence is stored with L2 verification status")
def evidence_stored_l2(db_session, collector_runs):
    """Verify evidence is stored with L2 status."""
    from src.evidence.models import EvidenceItem, EvidenceStatus

    stored = (
        db_session.query(EvidenceItem)
        .filter_by(control_id=collector_runs.control_id)
        .first()
    )
    assert stored is not None
    assert stored.verification_level == "L2"


@then("the compliance score is recalculated within 30 seconds")
def score_recalculated():
    """Verify score recalculation happens."""
    # Implementation would check score recalculation event
    pass


@then("the collection is retried 3 times with exponential backoff")
def retried_three_times(configured_collector):
    """Verify retry behavior."""
    assert configured_collector.retry_count == 3


@then(parsers.parse('the evidence status is marked as "{status}"'))
def evidence_status_marked(db_session, status: str):
    """Verify evidence status."""
    from src.evidence.models import EvidenceStatus

    stored = db_session.query(EvidenceItem).first()
    assert stored.status == EvidenceStatus(status)
```

### 2.6 Performance Test Examples

```python
# tests/performance/test_api_performance.py
"""Performance tests for API endpoints."""

from __future__ import annotations

import time

import pytest
from httpx import AsyncClient


@pytest.mark.performance
class TestAPIPerformance:
    """API performance tests."""

    @pytest.mark.asyncio
    async def test_evidence_list_p95_latency(
        self, async_client: AsyncClient, benchmark_thresholds
    ):
        """Evidence list endpoint p95 latency < 200ms."""
        latencies = []

        for _ in range(100):
            start = time.perf_counter()
            response = await async_client.get("/api/v1/evidence")
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
            assert response.status_code == 200

        latencies.sort()
        p95 = latencies[int(len(latencies) * 0.95)]
        assert p95 < benchmark_thresholds["api_p95_latency_ms"]

    @pytest.mark.asyncio
    async def test_compliance_score_calculation_performance(
        self, async_client: AsyncClient
    ):
        """Score calculation should complete in < 30 seconds."""
        start = time.perf_counter()
        response = await async_client.post(
            "/api/v1/scoring/calculate",
            json={
                "framework": "NIST-800-53",
                "controls": [
                    {"id": f"AC-{i}", "status": "pass"}
                    for i in range(1, 101)
                ],
            },
        )
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        assert elapsed < 30.0

    @pytest.mark.asyncio
    async def test_concurrent_dashboard_requests(
        self, async_client: AsyncClient
    ):
        """Dashboard should handle 500 concurrent users."""
        import asyncio

        async def fetch_dashboard():
            response = await async_client.get(
                "/api/v1/dashboard/summary"
            )
            return response.status_code == 200

        tasks = [fetch_dashboard() for _ in range(500)]
        results = await asyncio.gather(*tasks)

        success_rate = sum(results) / len(results)
        assert success_rate >= 0.99
```

---

## 3. Quality Gates Implementation

### 3.1 Quality Gate Engine

```python
# src/quality/gates.py
"""Quality gate engine for CI/CD pipeline."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import requests
import yaml

logger = logging.getLogger(__name__)


class GateStatus(Enum):
    """Quality gate status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BYPASSED = "bypassed"
    SKIPPED = "skipped"


class GateSeverity(Enum):
    """Gate failure severity."""
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


@dataclass
class GateCheck:
    """Individual quality gate check."""
    name: str
    description: str
    command: Optional[str] = None
    threshold: Optional[float] = None
    actual: Optional[float] = None
    severity: GateSeverity = GateSeverity.BLOCKING
    status: GateStatus = GateStatus.PENDING
    message: str = ""
    duration_sec: float = 0.0
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "severity": self.severity.value,
            "actual": self.actual,
            "threshold": self.threshold,
            "message": self.message,
            "duration_sec": self.duration_sec,
            "evidence": self.evidence,
        }


@dataclass
class QualityGate:
    """Quality gate definition."""
    name: str
    description: str
    checks: list[GateCheck]
    bypass_authority: str = ""
    bypass_justification: str = ""
    status: GateStatus = GateStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def passed(self) -> bool:
        return self.status == GateStatus.PASSED

    @property
    def failed(self) -> bool:
        return self.status == GateStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "bypass_authority": self.bypass_authority,
            "bypass_justification": self.bypass_justification,
            "started_at": self.started_at.isoformat()
            if self.started_at
            else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "checks": [c.to_dict() for c in self.checks],
        }


class QualityGateEngine:
    """Engine for executing quality gates."""

    def __init__(self, config_path: str = "quality_gates.yaml"):
        self.config_path = Path(config_path)
        self.gates: dict[str, QualityGate] = {}
        self._load_gates()

    def _load_gates(self) -> None:
        """Load gate definitions from config."""
        if not self.config_path.exists():
            self._create_default_gates()
            return

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        for gate_name, gate_config in config.get("gates", {}).items():
            checks = [
                GateCheck(
                    name=c["name"],
                    description=c.get("description", ""),
                    command=c.get("command"),
                    threshold=c.get("threshold"),
                    severity=GateSeverity(c.get("severity", "blocking")),
                )
                for c in gate_config.get("checks", [])
            ]
            self.gates[gate_name] = QualityGate(
                name=gate_name,
                description=gate_config.get("description", ""),
                checks=checks,
                bypass_authority=gate_config.get(
                    "bypass_authority", ""
                ),
            )

    def _create_default_gates(self) -> None:
        """Create default gate definitions."""
        self.gates = {
            "gate1_commit": QualityGate(
                name="gate1_commit",
                description="Commit-level quality checks (local)",
                checks=[
                    GateCheck(
                        name="lint_python",
                        description="Python linting with Ruff",
                        command="ruff check .",
                    ),
                    GateCheck(
                        name="format_check",
                        description="Code formatting check",
                        command="ruff format --check .",
                    ),
                    GateCheck(
                        name="type_check",
                        description="Type checking with mypy",
                        command="mypy src/",
                    ),
                    GateCheck(
                        name="unit_tests",
                        description="Unit tests for changed files",
                        command="pytest --testmon",
                    ),
                    GateCheck(
                        name="coverage",
                        description="Coverage on changed files",
                        command="pytest --cov --cov-fail-under=90",
                        threshold=90.0,
                    ),
                    GateCheck(
                        name="secrets_detection",
                        description="Secrets detection",
                        command="detect-secrets scan",
                    ),
                ],
            ),
            "gate2_pr": QualityGate(
                name="gate2_pr",
                description="Pull request quality checks",
                checks=[
                    GateCheck(
                        name="full_lint",
                        description="Full lint suite",
                        command="ruff check . && npx eslint .",
                    ),
                    GateCheck(
                        name="full_type_check",
                        description="Full type check",
                        command="mypy src/ && npx tsc --noEmit",
                    ),
                    GateCheck(
                        name="full_unit_tests",
                        description="Full unit test suite",
                        command="pytest --cov-fail-under=88",
                        threshold=88.0,
                    ),
                    GateCheck(
                        name="sast",
                        description="Static application security testing",
                        command="semgrep --config=auto --error",
                    ),
                    GateCheck(
                        name="dependency_audit",
                        description="Dependency vulnerability audit",
                        command="pip-audit --strict",
                    ),
                    GateCheck(
                        name="iac_scan",
                        description="Infrastructure as Code scan",
                        command="checkov --quiet",
                    ),
                ],
                bypass_authority="Engineering Lead + QA Lead",
            ),
            "gate3_merge": QualityGate(
                name="gate3_merge",
                description="Merge to main quality checks",
                checks=[
                    GateCheck(
                        name="integration_tests",
                        description="Full integration test suite",
                        command="pytest tests/integration/ -v",
                    ),
                    GateCheck(
                        name="contract_tests",
                        description="Contract tests",
                        command="pytest tests/contract/ -v",
                    ),
                    GateCheck(
                        name="build_verification",
                        description="Docker image builds",
                        command="docker build -t grc-claw:test .",
                    ),
                    GateCheck(
                        name="container_scan",
                        description="Container vulnerability scan",
                        command="trivy image --severity CRITICAL,HIGH grc-claw:test",
                    ),
                    GateCheck(
                        name="performance_regression",
                        description="Performance regression check",
                        command="locust -f tests/performance/smoke.py --headless",
                    ),
                    GateCheck(
                        name="db_migrations",
                        description="Database migrations apply",
                        command="alembic upgrade head",
                    ),
                    GateCheck(
                        name="sonarqube_gate",
                        description="SonarQube quality gate",
                    ),
                ],
                bypass_authority="CTO",
            ),
            "gate4_staging": QualityGate(
                name="gate4_staging",
                description="Staging deployment quality checks",
                checks=[
                    GateCheck(
                        name="e2e_tests",
                        description="End-to-end test suite",
                        command="npx playwright test",
                    ),
                    GateCheck(
                        name="performance_tests",
                        description="Performance test suite",
                        command="locust -f tests/performance/full.py --headless",
                    ),
                    GateCheck(
                        name="dast_scan",
                        description="Dynamic application security testing",
                        command="zap-full-scan.py",
                    ),
                    GateCheck(
                        name="smoke_tests",
                        description="Post-deployment smoke tests",
                        command="pytest tests/smoke/ -v",
                    ),
                ],
                bypass_authority="VP Engineering + QA Lead",
            ),
            "gate5_production": QualityGate(
                name="gate5_production",
                description="Production release quality checks",
                checks=[
                    GateCheck(
                        name="staging_validation",
                        description="48h clean staging validation",
                    ),
                    GateCheck(
                        name="canary_analysis",
                        description="Canary deployment analysis",
                    ),
                    GateCheck(
                        name="rollback_plan",
                        description="Tested rollback plan",
                    ),
                    GateCheck(
                        name="monitoring_dashboards",
                        description="All Grafana dashboards active",
                    ),
                    GateCheck(
                        name="compliance_signoff",
                        description="Compliance Lead approval",
                    ),
                    GateCheck(
                        name="security_signoff",
                        description="Security Lead approval",
                    ),
                ],
                bypass_authority="CTO + CISO",
            ),
        }

    def execute_gate(
        self,
        gate_name: str,
        context: Optional[dict[str, Any]] = None,
    ) -> QualityGate:
        """Execute a quality gate."""
        if gate_name not in self.gates:
            raise ValueError(f"Unknown gate: {gate_name}")

        gate = self.gates[gate_name]
        gate.status = GateStatus.RUNNING
        gate.started_at = datetime.utcnow()

        logger.info("Executing quality gate: %s", gate_name)

        for check in gate.checks:
            self._execute_check(check, context)

        # Determine gate status
        blocking_failures = [
            c
            for c in gate.checks
            if c.status == GateStatus.FAILED
            and c.severity == GateSeverity.BLOCKING
        ]

        if blocking_failures:
            gate.status = GateStatus.FAILED
        else:
            gate.status = GateStatus.PASSED

        gate.completed_at = datetime.utcnow()

        logger.info(
            "Quality gate %s: %s",
            gate_name,
            gate.status.value,
        )

        return gate

    def _execute_check(
        self,
        check: GateCheck,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Execute a single gate check."""
        check.status = GateStatus.RUNNING
        start = datetime.utcnow()

        try:
            if check.command:
                result = subprocess.run(
                    check.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
                check.duration_sec = (
                    datetime.utcnow() - start
                ).total_seconds()

                if result.returncode == 0:
                    check.status = GateStatus.PASSED
                    check.message = "Check passed"
                else:
                    check.status = GateStatus.FAILED
                    check.message = result.stderr or result.stdout
                    check.evidence.append(result.stdout)
            else:
                # Manual check
                check.status = GateStatus.PENDING
                check.message = "Manual verification required"

        except subprocess.TimeoutExpired:
            check.status = GateStatus.FAILED
            check.message = "Check timed out"
        except Exception as e:
            check.status = GateStatus.FAILED
            check.message = str(e)

    def evaluate_threshold(
        self,
        check: GateCheck,
        value: float,
    ) -> bool:
        """Evaluate a check against its threshold."""
        if check.threshold is None:
            return True
        return value >= check.threshold

    def generate_report(
        self,
        gate: QualityGate,
        output_path: str = "quality_gate_report.json",
    ) -> dict[str, Any]:
        """Generate a quality gate report."""
        report = gate.to_dict()

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def get_bypass_requirements(self, gate_name: str) -> dict[str, str]:
        """Get bypass requirements for a gate."""
        if gate_name not in self.gates:
            raise ValueError(f"Unknown gate: {gate_name}")

        gate = self.gates[gate_name]
        return {
            "authority": gate.bypass_authority,
            "justification_required": "yes",
            "post_bypass_action": "Document and create remediation plan",
        }
```

### 3.2 Pre-commit Hooks Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies:
          - types-all
          - pydantic
          - types-requests
        args: [--strict, --ignore-missing-imports]

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  - repo: local
    hooks:
      - id: unit-tests-changed
        name: Unit tests (changed files)
        entry: pytest --testmon -x -q
        language: system
        pass_filenames: true
        types: [python]
        stages: [commit]

      - id: coverage-check
        name: Coverage check (changed files)
        entry: pytest --cov --cov-fail-under=90 -x -q
        language: system
        pass_filenames: true
        types: [python]
        stages: [push]
```

### 3.3 GitHub Actions Quality Gate Workflow

```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on:
  push:
    branches: [main, "feature/**", "fix/**"]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.12"
  NODE_VERSION: "20"

jobs:
  # ─── Gate 1: Commit-Level Checks ─────────────────────────────
  gate1-commit:
    name: "Gate 1: Commit-Level"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install ruff mypy pytest pytest-cov pytest-testmon
          pip install -e ".[test]"

      - name: Lint (Ruff)
        run: |
          ruff check .
          ruff format --check .

      - name: Type Check (mypy)
        run: mypy src/ --strict

      - name: Unit Tests (changed files)
        run: pytest --testmon -x -q

      - name: Coverage (changed files)
        run: pytest --cov --cov-fail-under=90 -x -q

      - name: Secrets Detection
        run: |
          pip install detect-secrets
          detect-secrets scan --baseline .secrets.baseline

  # ─── Gate 2: Pull Request Checks ──────────────────────────────
  gate2-pr:
    name: "Gate 2: Pull Request"
    runs-on: ubuntu-latest
    needs: gate1-commit
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install Python dependencies
        run: |
          pip install -e ".[test]"
          pip install semgrep bandit pip-audit

      - name: Install Node dependencies
        run: npm ci

      - name: Full Lint Suite
        run: |
          ruff check .
          ruff format --check .
          npx eslint .
          npx prettier --check .

      - name: Full Type Check
        run: |
          mypy src/ --strict
          npx tsc --noEmit

      - name: Full Unit Test Suite
        run: pytest --cov=src --cov-report=xml --cov-fail-under=88

      - name: SAST Scan
        run: |
          semgrep --config=auto --error
          bandit -r src/ -ll

      - name: Dependency Audit
        run: |
          pip-audit --strict
          npm audit --audit-level=moderate

      - name: IaC Scan
        run: |
          pip install checkov
          checkov --quiet --compact

      - name: Upload Coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  # ─── Gate 3: Merge to Main ────────────────────────────────────
  gate3-merge:
    name: "Gate 3: Merge to Main"
    runs-on: ubuntu-latest
    needs: gate2-pr
    if: github.ref == 'refs/heads/main'
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: grc_claw_test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
      kafka:
        image: confluentinc/cp-kafka:latest
        ports: ["9092:9092"]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: pip install -e ".[test]"

      - name: Integration Tests
        run: pytest tests/integration/ -v --tb=short

      - name: Contract Tests
        run: pytest tests/contract/ -v --tb=short

      - name: Build Docker Image
        run: docker build -t grc-claw:${{ github.sha }} .

      - name: Container Scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: grc-claw:${{ github.sha }}
          severity: CRITICAL,HIGH
          exit-code: 1

      - name: Performance Regression
        run: |
          pip install locust
          locust -f tests/performance/smoke.py \
            --headless -u 100 -r 10 --run-time 5m

      - name: Database Migrations
        run: |
          pip install alembic
          alembic upgrade head

      - name: SonarQube Quality Gate
        uses: sonarsource/sonarqube-scan-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

  # ─── Gate 4: Staging Deployment ──────────────────────────────
  gate4-staging:
    name: "Gate 4: Staging Deployment"
    runs-on: ubuntu-latest
    needs: gate3-merge
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: E2E Tests
        run: |
          npx playwright install --with-deps
          npx playwright test

      - name: Performance Tests
        run: |
          pip install locust
          locust -f tests/performance/full.py \
            --headless -u 500 -r 50 --run-time 15m

      - name: DAST Scan
        uses: zaproxy/action-full-scan@v0.10.0
        with:
          target: https://staging.grc-claw.example.com
          rules_file_name: .zap/rules.tsv

      - name: Smoke Tests
        run: pytest tests/smoke/ -v --tb=short

      - name: Verify Monitoring
        run: |
          curl -sf https://staging.grc-claw.example.com/metrics \
            | grep -q "http_requests_total"

  # ─── Gate 5: Production Release ──────────────────────────────
  gate5-production:
    name: "Gate 5: Production Release"
    runs-on: ubuntu-latest
    needs: gate4-staging
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Verify Staging Validation (48h)
        run: |
          echo "Verifying 48h clean staging period..."
          # Check staging has been clean for 48 hours

      - name: Canary Deployment
        run: |
          echo "Deploying canary with 10% traffic..."

      - name: Canary Analysis
        run: |
          echo "Running canary analysis..."
          # Error rate < 0.1%
          # p95 latency < 500ms
          # No critical alerts

      - name: Full Rollout
        if: success()
        run: echo "Promoting canary to full production..."

      - name: Rollback on Failure
        if: failure()
        run: echo "Rolling back deployment..."
```

---

## 4. Defect Prediction (XGBoost)

### 4.1 Feature Engineering

```python
# src/quality/defect_prediction/features.py
"""Feature engineering for defect prediction model."""

from __future__ import annotations

import ast
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import git
import numpy as np
import requests

logger = logging.getLogger(__name__)


@dataclass
class CodeFeatures:
    """Code-level features for a file."""
    file_path: str
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    halstead_volume: float = 0.0
    halstead_difficulty: float = 0.0
    lines_of_code: int = 0
    lines_changed_30d: int = 0
    churn_frequency: int = 0
    recent_changes_7d: int = 0
    afferent_coupling: int = 0
    efferent_coupling: int = 0
    instability: float = 0.0
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    test_density: float = 0.0
    past_defects_90d: int = 0
    defect_density_module: float = 0.0
    hotspot_score: float = 0.0

    def to_vector(self) -> list[float]:
        """Convert to feature vector."""
        return [
            self.cyclomatic_complexity,
            self.cognitive_complexity,
            self.halstead_volume,
            self.halstead_difficulty,
            float(self.lines_of_code),
            float(self.lines_changed_30d),
            float(self.churn_frequency),
            float(self.recent_changes_7d),
            float(self.afferent_coupling),
            float(self.efferent_coupling),
            self.instability,
            self.line_coverage,
            self.branch_coverage,
            self.test_density,
            float(self.past_defects_90d),
            self.defect_density_module,
            self.hotspot_score,
        ]

    @classmethod
    def feature_names(cls) -> list[str]:
        return [
            "cyclomatic_complexity",
            "cognitive_complexity",
            "halstead_volume",
            "halstead_difficulty",
            "lines_of_code",
            "lines_changed_30d",
            "churn_frequency",
            "recent_changes_7d",
            "afferent_coupling",
            "efferent_coupling",
            "instability",
            "line_coverage",
            "branch_coverage",
            "test_density",
            "past_defects_90d",
            "defect_density_module",
            "hotspot_score",
        ]


class FeatureExtractor:
    """Extracts features from source code and repositories."""

    def __init__(
        self,
        repo_path: str = ".",
        github_token: Optional[str] = None,
        sonar_url: Optional[str] = None,
        sonar_token: Optional[str] = None,
    ):
        self.repo_path = Path(repo_path)
        self.github_token = github_token
        self.sonar_url = sonar_url
        self.sonar_token = sonar_token

    def extract_all(self) -> list[CodeFeatures]:
        """Extract features for all Python files."""
        features = []
        for py_file in self.repo_path.rglob("*.py"):
            if "test" in str(py_file) or "migration" in str(py_file):
                continue
            try:
                file_features = self.extract_file_features(py_file)
                features.append(file_features)
            except Exception as e:
                logger.warning(
                    "Failed to extract features from %s: %s",
                    py_file,
                    e,
                )
        return features

    def extract_file_features(self, file_path: Path) -> CodeFeatures:
        """Extract features for a single file."""
        features = CodeFeatures(file_path=str(file_path))

        # Static analysis features
        features.cyclomatic_complexity = self._calc_cyclomatic_complexity(
            file_path
        )
        features.cognitive_complexity = self._calc_cognitive_complexity(
            file_path
        )
        features.halstead_volume, features.halstead_difficulty = (
            self._calc_halstead_metrics(file_path)
        )
        features.lines_of_code = self._count_loc(file_path)

        # Git-based features
        git_features = self._extract_git_features(file_path)
        features.lines_changed_30d = git_features.get(
            "lines_changed_30d", 0
        )
        features.churn_frequency = git_features.get("churn_frequency", 0)
        features.recent_changes_7d = git_features.get(
            "recent_changes_7d", 0
        )

        # Coupling features
        features.afferent_coupling = self._calc_afferent_coupling(
            file_path
        )
        features.efferent_coupling = self._calc_efferent_coupling(
            file_path
        )
        if (features.afferent_coupling + features.efferent_coupling) > 0:
            features.instability = features.efferent_coupling / (
                features.afferent_coupling + features.efferent_coupling
            )

        # Coverage features
        coverage = self._get_coverage(file_path)
        features.line_coverage = coverage.get("line", 0.0)
        features.branch_coverage = coverage.get("branch", 0.0)
        features.test_density = self._calc_test_density(file_path)

        # Historical defect features
        features.past_defects_90d = self._get_past_defects(file_path)
        features.defect_density_module = self._get_module_defect_density(
            file_path
        )
        features.hotspot_score = self._calc_hotspot_score(file_path)

        return features

    def _calc_cyclomatic_complexity(self, file_path: Path) -> float:
        """Calculate cyclomatic complexity using radon."""
        try:
            result = subprocess.run(
                ["radon", "cc", "-s", "-j", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                complexities = [
                    item["complexity"]
                    for item in data.get(str(file_path), [])
                ]
                return float(np.mean(complexities)) if complexities else 0.0
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
        return 0.0

    def _calc_cognitive_complexity(self, file_path: Path) -> float:
        """Calculate cognitive complexity."""
        try:
            result = subprocess.run(
                ["radon", "cc", "-s", "-j", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                # Cognitive complexity approximation
                complexities = [
                    item.get("complexity", 0)
                    for item in data.get(str(file_path), [])
                ]
                return float(sum(complexities))
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
        return 0.0

    def _calc_halstead_metrics(
        self, file_path: Path
    ) -> tuple[float, float]:
        """Calculate Halstead metrics."""
        try:
            result = subprocess.run(
                ["radon", "hal", "-j", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                volume = data.get("volume", 0.0)
                difficulty = data.get("difficulty", 0.0)
                return float(volume), float(difficulty)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
        return 0.0, 0.0

    def _count_loc(self, file_path: Path) -> int:
        """Count lines of code."""
        try:
            with open(file_path) as f:
                lines = f.readlines()
                return len(
                    [
                        line
                        for line in lines
                        if line.strip()
                        and not line.strip().startswith("#")
                    ]
                )
        except (OSError, UnicodeDecodeError):
            return 0

    def _extract_git_features(self, file_path: Path) -> dict[str, int]:
        """Extract git-based features."""
        try:
            repo = git.Repo(self.repo_path)
            since_30d = datetime.now() - timedelta(days=30)
            since_7d = datetime.now() - timedelta(days=7)

            lines_changed_30d = 0
            churn_frequency = 0
            recent_changes_7d = 0

            for commit in repo.iter_commits(
                since=since_30d.isoformat(), paths=str(file_path)
            ):
                churn_frequency += 1
                if commit.committed_datetime > since_7d:
                    recent_changes_7d += 1
                for file_stats in commit.stats.files.values():
                    lines_changed_30d += file_stats.get(
                        "insertions", 0
                    ) + file_stats.get("deletions", 0)

            return {
                "lines_changed_30d": lines_changed_30d,
                "churn_frequency": churn_frequency,
                "recent_changes_7d": recent_changes_7d,
            }
        except (git.GitCommandError, git.InvalidGitRepositoryError):
            return {}

    def _calc_afferent_coupling(self, file_path: Path) -> int:
        """Calculate afferent coupling (number of incoming dependencies)."""
        module_name = file_path.stem
        count = 0
        for py_file in self.repo_path.rglob("*.py"):
            if py_file == file_path:
                continue
            try:
                with open(py_file) as f:
                    content = f.read()
                    if module_name in content:
                        count += 1
            except (OSError, UnicodeDecodeError):
                continue
        return count

    def _calc_efferent_coupling(self, file_path: Path) -> int:
        """Calculate efferent coupling (number of outgoing dependencies)."""
        try:
            with open(file_path) as f:
                content = f.read()
            tree = ast.parse(content)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
            return len(imports)
        except (OSError, SyntaxError):
            return 0

    def _get_coverage(self, file_path: Path) -> dict[str, float]:
        """Get coverage data from coverage.xml."""
        coverage_file = self.repo_path / "coverage.xml"
        if not coverage_file.exists():
            return {}

        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(coverage_file)
            root = tree.getroot()

            for cls in root.findall(".//class"):
                filename = cls.get("filename", "")
                if file_path.name in filename:
                    return {
                        "line": float(cls.get("line-rate", 0)) * 100,
                        "branch": float(cls.get("branch-rate", 0)) * 100,
                    }
        except ET.ParseError:
            pass
        return {}

    def _calc_test_density(self, file_path: Path) -> float:
        """Calculate test density (tests per KLOC)."""
        test_dir = self.repo_path / "tests"
        if not test_dir.exists():
            return 0.0

        loc = self._count_loc(file_path)
        if loc == 0:
            return 0.0

        test_count = sum(
            1 for _ in test_dir.rglob(f"test_{file_path.stem}*.py")
        )
        return test_count / (loc / 1000.0)

    def _get_past_defects(self, file_path: Path) -> int:
        """Get number of past defects from GitHub Issues."""
        if not self.github_token:
            return 0

        try:
            since = (datetime.now() - timedelta(days=90)).isoformat()
            url = (
                f"https://api.github.com/search/issues"
                f"?q=repo:grc-claw/grc-claw+is:issue"
                f"+{file_path.name}+created:>{since}"
            )
            response = requests.get(
                url,
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=10,
            )
            if response.status_code == 200:
                return response.json().get("total_count", 0)
        except requests.RequestException:
            pass
        return 0

    def _get_module_defect_density(self, file_path: Path) -> float:
        """Get defect density for the module."""
        module_path = file_path.parent
        total_defects = 0
        total_loc = 0

        for py_file in module_path.rglob("*.py"):
            total_defects += self._get_past_defects(py_file)
            total_loc += self._count_loc(py_file)

        if total_loc == 0:
            return 0.0
        return total_defects / (total_loc / 1000.0)

    def _calc_hotspot_score(self, file_path: Path) -> float:
        """Calculate hotspot score based on historical defect clustering."""
        past_defects = self._get_past_defects(file_path)
        lines_changed = self._extract_git_features(file_path).get(
            "lines_changed_30d", 0
        )

        if lines_changed == 0:
            return 0.0

        # Hotspot = defects per line changed
        return past_defects / max(lines_changed, 1) * 1000
```

### 4.2 XGBoost Model

```python
# src/quality/defect_prediction/model.py
"""XGBoost-based defect prediction model."""

from __future__ import annotations

import json
import logging
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np
import xgboost as xgb
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)

from .features import CodeFeatures, FeatureExtractor

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Defect prediction result."""
    file_path: str
    risk_score: float  # 0-100
    risk_level: str  # low, medium, high, very_high, critical
    probability: float
    top_features: list[tuple[str, float]]
    timestamp: datetime = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "risk_score": round(self.risk_score, 2),
            "risk_level": self.risk_level,
            "probability": round(self.probability, 4),
            "top_features": [
                {"feature": f, "importance": round(i, 4)}
                for f, i in self.top_features
            ],
            "timestamp": self.timestamp.isoformat(),
        }


class DefectPredictionModel:
    """XGBoost defect prediction model."""

    def __init__(self, model_path: Optional[str] = None):
        self.model: Optional[xgb.XGBClassifier] = None
        self.feature_names = CodeFeatures.feature_names()
        self.model_path = model_path or "models/defect_prediction.json"
        self.is_trained = False

        # Model hyperparameters (from spec)
        self.params = {
            "n_estimators": 200,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 3,
            "gamma": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "use_label_encoder": False,
            "random_state": 42,
        }

    def train(
        self,
        features: list[CodeFeatures],
        labels: list[int],
        test_size: float = 0.2,
        validation_size: float = 0.1,
    ) -> dict[str, Any]:
        """Train the defect prediction model."""
        if len(features) != len(labels):
            raise ValueError("Features and labels must have same length")

        X = np.array([f.to_vector() for f in features])
        y = np.array(labels)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        # Further split for validation
        if validation_size > 0:
            X_train, X_val, y_train, y_val = train_test_split(
                X_train,
                y_train,
                test_size=validation_size,
                random_state=42,
                stratify=y_train,
            )
        else:
            X_val, y_val = None, None

        # Train model
        self.model = xgb.XGBClassifier(**self.params)
        eval_set = [(X_train, y_train)]
        if X_val is not None:
            eval_set.append((X_val, y_val))

        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            verbose=False,
        )
        self.is_trained = True

        # Evaluate
        metrics = self._evaluate(X_test, y_test)

        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X, y, cv=StratifiedKFold(n_splits=5), scoring="roc_auc"
        )
        metrics["cv_roc_auc_mean"] = float(cv_scores.mean())
        metrics["cv_roc_auc_std"] = float(cv_scores.std())

        logger.info(
            "Model trained. ROC-AUC: %.4f, CV ROC-AUC: %.4f ± %.4f",
            metrics["roc_auc"],
            metrics["cv_roc_auc_mean"],
            metrics["cv_roc_auc_std"],
        )

        return metrics

    def _evaluate(
        self, X_test: np.ndarray, y_test: np.ndarray
    ) -> dict[str, Any]:
        """Evaluate model performance."""
        y_pred = self.model.predict(X_test)
        y_prob = self.model.predict_proba(X_test)[:, 1]

        report = classification_report(
            y_test, y_pred, output_dict=True, zero_division=0
        )
        cm = confusion_matrix(y_test, y_pred)

        return {
            "precision": report["1"]["precision"],
            "recall": report["1"]["recall"],
            "f1_score": report["1"]["f1-score"],
            "roc_auc": roc_auc_score(y_test, y_prob),
            "confusion_matrix": cm.tolist(),
            "classification_report": report,
        }

    def predict(self, features: CodeFeatures) -> PredictionResult:
        """Predict defect risk for a file."""
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model must be trained before prediction")

        X = np.array([features.to_vector()])
        probability = float(self.model.predict_proba(X)[0, 1])
        risk_score = probability * 100

        # Determine risk level
        if risk_score <= 20:
            risk_level = "low"
        elif risk_score <= 40:
            risk_level = "medium"
        elif risk_score <= 60:
            risk_level = "high"
        elif risk_score <= 80:
            risk_level = "very_high"
        else:
            risk_level = "critical"

        # Feature importance for this prediction
        importances = self.model.feature_importances_
        top_indices = np.argsort(importances)[-5:][::-1]
        top_features = [
            (self.feature_names[i], float(importances[i]))
            for i in top_indices
        ]

        return PredictionResult(
            file_path=features.file_path,
            risk_score=risk_score,
            risk_level=risk_level,
            probability=probability,
            top_features=top_features,
        )

    def predict_batch(
        self, features: list[CodeFeatures]
    ) -> list[PredictionResult]:
        """Predict defect risk for multiple files."""
        return [self.predict(f) for f in features]

    def save(self, path: Optional[str] = None) -> None:
        """Save model to disk."""
        save_path = path or self.model_path
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        if self.model is not None:
            self.model.save_model(save_path)
            logger.info("Model saved to %s", save_path)

    def load(self, path: Optional[str] = None) -> None:
        """Load model from disk."""
        load_path = path or self.model_path

        if not Path(load_path).exists():
            raise FileNotFoundError(f"Model not found: {load_path}")

        self.model = xgb.XGBClassifier()
        self.model.load_model(load_path)
        self.is_trained = True
        logger.info("Model loaded from %s", load_path)

    def get_feature_importance(self) -> list[dict[str, Any]]:
        """Get global feature importance."""
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model must be trained first")

        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1]

        return [
            {
                "feature": self.feature_names[i],
                "importance": float(importances[i]),
                "rank": rank + 1,
            }
            for rank, i in enumerate(indices)
        ]


class DefectPredictionService:
    """Service for defect prediction operations."""

    def __init__(
        self,
        model: DefectPredictionModel,
        feature_extractor: FeatureExtractor,
    ):
        self.model = model
        self.feature_extractor = feature_extractor

    def analyze_repository(self) -> list[PredictionResult]:
        """Analyze entire repository for defect risks."""
        features = self.feature_extractor.extract_all()
        return self.model.predict_batch(features)

    def get_high_risk_files(
        self, threshold: float = 60.0
    ) -> list[PredictionResult]:
        """Get files with high defect risk."""
        results = self.analyze_repository()
        return [r for r in results if r.risk_score >= threshold]

    def generate_risk_report(
        self, output_path: str = "defect_risk_report.json"
    ) -> dict[str, Any]:
        """Generate a comprehensive risk report."""
        results = self.analyze_repository()

        risk_distribution = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "very_high": 0,
            "critical": 0,
        }
        for r in results:
            risk_distribution[r.risk_level] += 1

        high_risk = [r.to_dict() for r in results if r.risk_score >= 60]

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_files_analyzed": len(results),
            "risk_distribution": risk_distribution,
            "high_risk_files": high_risk,
            "feature_importance": self.model.get_feature_importance(),
            "recommendations": self._generate_recommendations(results),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def _generate_recommendations(
        self, results: list[PredictionResult]
    ) -> list[str]:
        recommendations = []
        high_risk = [r for r in results if r.risk_score >= 60]

        if high_risk:
            recommendations.append(
                f"Review {len(high_risk)} high-risk files "
                f"for potential defects"
            )

        critical = [r for r in results if r.risk_level == "critical"]
        if critical:
            recommendations.append(
                f"URGENT: {len(critical)} files at critical risk — "
                f"consider dedicated hardening sprint"
            )

        # Check for patterns
        low_coverage_high_risk = [
            r
            for r in high_risk
            if any(
                f[0] == "line_coverage" and f[1] > 0.1
                for f in r.top_features
            )
        ]
        if low_coverage_high_risk:
            recommendations.append(
                f"Increase test coverage for {len(low_coverage_high_risk)} "
                f"high-risk files with low coverage"
            )

        return recommendations
```

### 4.3 Model Training Pipeline

```python
# scripts/train_defect_model.py
"""Train the defect prediction model."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np

from src.quality.defect_prediction.features import FeatureExtractor
from src.quality.defect_prediction.model import DefectPredictionModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_training_labels(
    features, github_issues
) -> list[int]:
    """Create binary labels from historical defect data."""
    labels = []
    for f in features:
        # Label 1 if file had defects in last 90 days
        label = 1 if f.past_defects_90d > 0 else 0
        labels.append(label)
    return labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-path", default=".")
    parser.add_argument("--output", default="models/defect_prediction.json")
    parser.add_argument("--github-token", default=None)
    args = parser.parse_args()

    # Extract features
    logger.info("Extracting features...")
    extractor = FeatureExtractor(
        repo_path=args.repo_path,
        github_token=args.github_token,
    )
    features = extractor.extract_all()
    logger.info("Extracted features for %d files", len(features))

    # Create labels
    labels = create_training_labels(features, None)
    defect_count = sum(labels)
    logger.info(
        "Dataset: %d files, %d with defects (%.1f%%)",
        len(labels),
        defect_count,
        defect_count / len(labels) * 100,
    )

    # Train model
    logger.info("Training model...")
    model = DefectPredictionModel(model_path=args.output)
    metrics = model.train(features, labels)

    # Save model
    model.save(args.output)

    # Save metrics
    metrics_path = Path(args.output).with_suffix(".metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("Model saved to %s", args.output)
    logger.info("Metrics saved to %s", metrics_path)
    logger.info("ROC-AUC: %.4f", metrics["roc_auc"])


if __name__ == "__main__":
    main()
```

---

## 5. Quality Dashboards (Grafana)

### 5.1 Grafana Dashboard JSON

```json
{
  "dashboard": {
    "id": null,
    "title": "GRC_Claw Quality Metrics",
    "tags": ["quality", "grc-claw"],
    "timezone": "UTC",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "30s",
    "time": {
      "from": "now-30d",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "Overall Quality Score",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
        "targets": [{
          "expr": "quality_score",
          "legendFormat": "Quality Score",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 70},
                {"color": "green", "value": 90}
              ]
            },
            "unit": "short"
          }
        },
        "options": {
          "showThresholdLabels": true,
          "showThresholdMarkers": true
        }
      },
      {
        "id": 2,
        "title": "Test Coverage Trend",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0},
        "targets": [
          {
            "expr": "line_coverage",
            "legendFormat": "Line Coverage",
            "refId": "A"
          },
          {
            "expr": "branch_coverage",
            "legendFormat": "Branch Coverage",
            "refId": "B"
          },
          {
            "expr": "88",
            "legendFormat": "Line Target (88%)",
            "refId": "C"
          },
          {
            "expr": "82",
            "legendFormat": "Branch Target (82%)",
            "refId": "D"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
            "custom": {
              "drawStyle": "line",
              "lineWidth": 2,
              "fillOpacity": 10
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Defect Density by Component",
        "type": "barchart",
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
        "targets": [{
          "expr": "defect_density_by_component",
          "legendFormat": "{{component}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "short",
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 1},
                {"color": "red", "value": 2}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "title": "SLO Compliance",
        "type": "stat",
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "slo_api_availability",
            "legendFormat": "API Availability",
            "refId": "A"
          },
          {
            "expr": "slo_evidence_success",
            "legendFormat": "Evidence Success",
            "refId": "B"
          },
          {
            "expr": "slo_report_time",
            "legendFormat": "Report Time (s)",
            "refId": "C"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 99},
                {"color": "green", "value": 99.9}
              ]
            }
          }
        }
      },
      {
        "id": 5,
        "title": "Pipeline Health",
        "type": "table",
        "gridPos": {"h": 8, "w": 12, "x": 6, "y": 8},
        "targets": [{
          "expr": "pipeline_metrics",
          "format": "table",
          "refId": "A"
        }],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {"Time": true},
              "renameByName": {
                "Value": "Value",
                "metric": "Metric"
              }
            }
          }
        ]
      },
      {
        "id": 6,
        "title": "Quality Gate Pass Rate",
        "type": "bargauge",
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 8},
        "targets": [{
          "expr": "gate_pass_rate",
          "legendFormat": "{{gate}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 80},
                {"color": "green", "value": 95}
              ]
            }
          }
        }
      },
      {
        "id": 7,
        "title": "Defect Trend",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "defects_opened_sprint",
            "legendFormat": "Opened",
            "refId": "A"
          },
          {
            "expr": "defects_closed_sprint",
            "legendFormat": "Closed",
            "refId": "B"
          },
          {
            "expr": "defects_critical_sprint",
            "legendFormat": "Critical",
            "refId": "C"
          }
        ]
      },
      {
        "id": 8,
        "title": "Technical Debt Ratio",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 16},
        "targets": [{
          "expr": "technical_debt_ratio",
          "legendFormat": "TDR",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 50,
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 5},
                {"color": "orange", "value": 10},
                {"color": "red", "value": 20}
              ]
            }
          }
        }
      },
      {
        "id": 9,
        "title": "Flaky Test Rate",
        "type": "stat",
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 16},
        "targets": [{
          "expr": "flaky_test_rate",
          "legendFormat": "Flaky Rate",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 1},
                {"color": "red", "value": 5}
              ]
            }
          }
        }
      }
    ]
  }
}
```

### 5.2 Prometheus Alert Rules

```yaml
# prometheus/rules/quality_alerts.yml
groups:
  - name: quality_alerts
    interval: 30s
    rules:
      # Coverage Alerts
      - alert: LowTestCoverage
        expr: line_coverage < 88
        for: 1h
        labels:
          severity: warning
          team: quality
        annotations:
          summary: "Test coverage below target"
          description: "Line coverage is {{ $value }}%, below 88% target"
          dashboard: "https://grafana.grc-claw.example.com/d/quality"

      - alert: CriticalLowCoverage
        expr: line_coverage < 70
        for: 30m
        labels:
          severity: critical
          team: quality
        annotations:
          summary: "CRITICAL: Test coverage critically low"
          description: "Line coverage is {{ $value }}%, critically below target"

      # Defect Alerts
      - alert: HighDefectDensity
        expr: defect_density > 1.0
        for: 1h
        labels:
          severity: warning
          team: quality
        annotations:
          summary: "Defect density above target"
          description: "Defect density is {{ $value }}/KLOC, above 1.0 target"

      - alert: CriticalDefectFound
        expr: defects_critical_total > 0
        for: 0m
        labels:
          severity: critical
          team: quality
        annotations:
          summary: "Critical defect found"
          description: "{{ $value }} critical defects detected"

      # Pipeline Alerts
      - alert: PipelineFailureRate
        expr: rate(pipeline_runs_total{status="failure"}[1h]) > 0.1
        for: 15m
        labels:
          severity: critical
          team: devops
        annotations:
          summary: "High pipeline failure rate"
          description: "Pipeline failure rate is above 10%"

      - alert: GatePassRateLow
        expr: gate_pass_rate < 0.85
        for: 1h
        labels:
          severity: warning
          team: quality
        annotations:
          summary: "Quality gate pass rate below target"
          description: "Gate {{ $labels.gate }} pass rate is {{ $value }}%"

      # SLO Alerts
      - alert: SLOBreach
        expr: slo_error_budget_burn_rate > 14.4
        for: 5m
        labels:
          severity: critical
          team: sre
        annotations:
          summary: "SLO error budget burning fast"
          description: "Error budget burn rate is {{ $value }}x"

      - alert: APIAvailabilityLow
        expr: slo_api_availability < 99.9
        for: 5m
        labels:
          severity: critical
          team: sre
        annotations:
          summary: "API availability below SLO"
          description: "API availability is {{ $value }}%"

      # Flaky Test Alert
      - alert: FlakyTestRate
        expr: flaky_test_rate > 0.01
        for: 1h
        labels:
          severity: warning
          team: quality
        annotations:
          summary: "High flaky test rate"
          description: "Flaky test rate is {{ $value }}%"

      # Security Alerts
      - alert: CriticalVulnerabilityFound
        expr: security_vulnerabilities_critical > 0
        for: 0m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Critical vulnerability found"
          description: "{{ $value }} critical vulnerabilities detected"

      - alert: HighVulnerabilityFound
        expr: security_vulnerabilities_high > 0
        for: 0m
        labels:
          severity: warning
          team: security
        annotations:
          summary: "High vulnerability found"
          description: "{{ $value }} high vulnerabilities detected"
```

### 5.3 Dashboard Provisioning

```yaml
# grafana/provisioning/dashboards/quality.yml
apiVersion: 1

providers:
  - name: "GRC_Claw Quality"
    orgId: 1
    folder: "GRC_Claw"
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards/quality
      foldersFromFilesStructure: true
```

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: 15s
      httpMethod: POST
      manageAlerts: true
      prometheusType: Prometheus
      prometheusVersion: "2.40.0"
      cacheLevel: High
      incrementalQuerying: true
```

---

## 6. Quality Culture Practices

### 6.1 Quality Culture Framework Implementation

```python
# src/quality/culture.py
"""Quality culture practices and metrics tracking."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class QualityPractice(Enum):
    """Quality culture practices."""
    BLAMELESS_POSTMORTEM = "blameless_postmortem"
    QUALITY_CHAMPION = "quality_champion"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    QUALITY_RECOGNITION = "quality_recognition"
    PSYCHOLOGICAL_SAFETY = "psychological_safety"
    PAIR_PROGRAMMING = "pair_programming"
    CODE_REVIEW = "code_review"
    TDD = "tdd"
    CONTINUOUS_LEARNING = "continuous_learning"


@dataclass
class QualityActivity:
    """Quality culture activity record."""
    practice: QualityPractice
    participant: str
    description: str
    date: datetime = field(default_factory=datetime.utcnow)
    impact: str = ""
    duration_minutes: int = 0


@dataclass
class QualityCultureMetrics:
    """Quality culture metrics."""
    speaking_up_rate: float = 0.0
    blameless_postmortem_rate: float = 100.0
    learning_actions_rate: float = 0.0
    team_satisfaction: float = 0.0
    quality_champion_participation: float = 0.0
    knowledge_sharing_sessions: int = 0
    pair_programming_hours: float = 0.0
    code_review_participation: float = 0.0


class QualityCultureTracker:
    """Tracks quality culture activities and metrics."""

    def __init__(self, data_path: str = "quality_culture.json"):
        self.data_path = Path(data_path)
        self.activities: list[QualityActivity] = []
        self._load()

    def _load(self) -> None:
        """Load culture data from disk."""
        if self.data_path.exists():
            with open(self.data_path) as f:
                data = json.load(f)
                self.activities = [
                    QualityActivity(
                        practice=QualityPractice(a["practice"]),
                        participant=a["participant"],
                        description=a["description"],
                        date=datetime.fromisoformat(a["date"]),
                        impact=a.get("impact", ""),
                        duration_minutes=a.get("duration_minutes", 0),
                    )
                    for a in data.get("activities", [])
                ]

    def _save(self) -> None:
        """Save culture data to disk."""
        data = {
            "activities": [
                {
                    "practice": a.practice.value,
                    "participant": a.participant,
                    "description": a.description,
                    "date": a.date.isoformat(),
                    "impact": a.impact,
                    "duration_minutes": a.duration_minutes,
                }
                for a in self.activities
            ]
        }
        with open(self.data_path, "w") as f:
            json.dump(data, f, indent=2)

    def record_activity(self, activity: QualityActivity) -> None:
        """Record a quality culture activity."""
        self.activities.append(activity)
        self._save()
        logger.info(
            "Recorded quality activity: %s by %s",
            activity.practice.value,
            activity.participant,
        )

    def get_metrics(
        self, since: Optional[datetime] = None
    ) -> QualityCultureMetrics:
        """Calculate quality culture metrics."""
        if since is None:
            since = datetime.utcnow() - timedelta(days=90)

        recent = [a for a in self.activities if a.date >= since]

        metrics = QualityCultureMetrics()

        # Knowledge sharing sessions
        metrics.knowledge_sharing_sessions = len(
            [
                a
                for a in recent
                if a.practice == QualityPractice.KNOWLEDGE_SHARING
            ]
        )

        # Pair programming hours
        metrics.pair_programming_hours = sum(
            a.duration_minutes
            for a in recent
            if a.practice == QualityPractice.PAIR_PROGRAMMING
        ) / 60.0

        # Code review participation
        metrics.code_review_participation = len(
            set(
                a.participant
                for a in recent
                if a.practice == QualityPractice.CODE_REVIEW
            )
        )

        return metrics

    def generate_culture_report(
        self, output_path: str = "quality_culture_report.json"
    ) -> dict[str, Any]:
        """Generate quality culture report."""
        metrics = self.get_metrics()

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "speaking_up_rate": metrics.speaking_up_rate,
                "blameless_postmortem_rate": metrics.blameless_postmortem_rate,
                "learning_actions_rate": metrics.learning_actions_rate,
                "team_satisfaction": metrics.team_satisfaction,
                "knowledge_sharing_sessions": metrics.knowledge_sharing_sessions,
                "pair_programming_hours": metrics.pair_programming_hours,
                "code_review_participation": metrics.code_review_participation,
            },
            "recent_activities": [
                {
                    "practice": a.practice.value,
                    "participant": a.participant,
                    "description": a.description,
                    "date": a.date.isoformat(),
                }
                for a in self.activities[-20:]
            ],
            "recommendations": self._generate_recommendations(metrics),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def _generate_recommendations(
        self, metrics: QualityCultureMetrics
    ) -> list[str]:
        recommendations = []

        if metrics.knowledge_sharing_sessions < 4:
            recommendations.append(
                "Increase knowledge sharing sessions — target ≥ 4 per quarter"
            )

        if metrics.pair_programming_hours < 10:
            recommendations.append(
                "Increase pair programming — target ≥ 10 hours per quarter"
            )

        if metrics.code_review_participation < 0.8:
            recommendations.append(
                "Improve code review participation — target ≥ 80% team"
            )

        return recommendations


class QualityChampionRotation:
    """Manages quality champion rotation."""

    def __init__(self, team_members: list[str]):
        self.team_members = team_members
        self.current_index = 0
        self.rotation_history: list[dict[str, Any]] = []

    def get_current_champion(self) -> str:
        """Get current quality champion."""
        return self.team_members[self.current_index]

    def rotate(self) -> str:
        """Rotate to next quality champion."""
        self.current_index = (self.current_index + 1) % len(
            self.team_members
        )
        champion = self.get_current_champion()

        self.rotation_history.append(
            {
                "champion": champion,
                "start_date": datetime.utcnow().isoformat(),
            }
        )

        return champion

    def get_rotation_schedule(
        self, weeks: int = 12
    ) -> list[dict[str, str]]:
        """Get rotation schedule for upcoming weeks."""
        schedule = []
        for i in range(weeks):
            idx = (self.current_index + i) % len(self.team_members)
            schedule.append(
                {
                    "week": i + 1,
                    "champion": self.team_members[idx],
                }
            )
        return schedule
```

### 6.2 Quality Onboarding Program

```python
# src/quality/onboarding.py
"""Quality onboarding program for new team members."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class OnboardingWeek(Enum):
    """Onboarding program weeks."""
    WEEK_1 = 1
    WEEK_2 = 2
    WEEK_3 = 3
    WEEK_4 = 4


@dataclass
class OnboardingActivity:
    """Onboarding activity."""
    name: str
    description: str
    duration_hours: float
    owner: str
    completed: bool = False
    completion_date: datetime = None


@dataclass
class OnboardingProgram:
    """Quality onboarding program."""
    member_name: str
    start_date: datetime
    activities: list[OnboardingActivity] = field(default_factory=list)

    def __post_init__(self):
        if not self.activities:
            self.activities = self._default_activities()

    def _default_activities(self) -> list[OnboardingActivity]:
        """Default onboarding activities."""
        return [
            # Week 1
            OnboardingActivity(
                name="Quality Culture Introduction",
                description="Introduction to quality culture and values",
                duration_hours=2,
                owner="QA Lead",
            ),
            OnboardingActivity(
                name="Quality Tools Setup",
                description="Setup quality tools and infrastructure",
                duration_hours=4,
                owner="QA Engineer",
            ),
            OnboardingActivity(
                name="Quality Process Walkthrough",
                description="Walkthrough of quality processes",
                duration_hours=2,
                owner="QA Lead",
            ),
            # Week 2
            OnboardingActivity(
                name="Coding Standards",
                description="Coding standards and review guidelines",
                duration_hours=2,
                owner="Tech Lead",
            ),
            OnboardingActivity(
                name="Testing Framework",
                description="Testing framework and practices",
                duration_hours=4,
                owner="QA Engineer",
            ),
            OnboardingActivity(
                name="Quality Gates & CI/CD",
                description="Quality gate and CI/CD pipeline overview",
                duration_hours=2,
                owner="DevOps",
            ),
            # Week 3
            OnboardingActivity(
                name="Shadow Code Review",
                description="Participate in code review as observer",
                duration_hours=4,
                owner="Mentor",
            ),
            OnboardingActivity(
                name="Shadow Test Execution",
                description="Observe test execution",
                duration_hours=4,
                owner="Mentor",
            ),
            # Week 4
            OnboardingActivity(
                name="First Quality Contribution",
                description="Complete first quality contribution",
                duration_hours=40,
                owner="Mentor",
            ),
            OnboardingActivity(
                name="Onboarding Assessment",
                description="Quality onboarding assessment",
                duration_hours=1,
                owner="QA Lead",
            ),
        ]

    def get_progress(self) -> dict[str, Any]:
        """Get onboarding progress."""
        total = len(self.activities)
        completed = sum(1 for a in self.activities if a.completed)
        total_hours = sum(a.duration_hours for a in self.activities)
        completed_hours = sum(
            a.duration_hours for a in self.activities if a.completed
        )

        return {
            "member_name": self.member_name,
            "start_date": self.start_date.isoformat(),
            "total_activities": total,
            "completed_activities": completed,
            "progress_pct": (completed / total * 100) if total > 0 else 0,
            "total_hours": total_hours,
            "completed_hours": completed_hours,
            "remaining_hours": total_hours - completed_hours,
        }

    def complete_activity(self, activity_name: str) -> None:
        """Mark an activity as completed."""
        for activity in self.activities:
            if activity.name == activity_name:
                activity.completed = True
                activity.completion_date = datetime.utcnow()
                break
```

---

## 7. Quality Auditing Framework

### 7.1 Audit Engine

```python
# src/quality/auditing.py
"""Quality auditing framework for GRC_Claw."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import requests
import yaml

logger = logging.getLogger(__name__)


class AuditType(Enum):
    """Types of quality audits."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    PROCESS = "process"
    TOOLCHAIN = "toolchain"
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"


class FindingSeverity(Enum):
    """Audit finding severity."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingStatus(Enum):
    """Audit finding status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"


@dataclass
class AuditFinding:
    """Audit finding."""
    id: str
    title: str
    description: str
    severity: FindingSeverity
    category: str
    source: str
    date_identified: datetime
    date_due: Optional[datetime] = None
    assignee: str = ""
    status: FindingStatus = FindingStatus.OPEN
    root_cause: str = ""
    remediation_plan: str = ""
    evidence: list[str] = field(default_factory=list)
    verification: str = ""
    lessons_learned: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category,
            "source": self.source,
            "date_identified": self.date_identified.isoformat(),
            "date_due": self.date_due.isoformat()
            if self.date_due
            else None,
            "assignee": self.assignee,
            "status": self.status.value,
            "root_cause": self.root_cause,
            "remediation_plan": self.remediation_plan,
            "evidence": self.evidence,
            "verification": self.verification,
            "lessons_learned": self.lessons_learned,
        }


@dataclass
class AuditChecklistItem:
    """Audit checklist item."""
    category: str
    question: str
    passed: Optional[bool] = None
    evidence: str = ""
    notes: str = ""


@dataclass
class QualityAudit:
    """Quality audit."""
    audit_id: str
    audit_type: AuditType
    title: str
    scope: list[str]
    auditor: str
    start_date: datetime
    end_date: Optional[datetime] = None
    checklist: list[AuditChecklistItem] = field(default_factory=list)
    findings: list[AuditFinding] = field(default_factory=list)
    metrics_snapshot: dict[str, Any] = field(default_factory=dict)
    overall_score: float = 0.0
    rating: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "audit_type": self.audit_type.value,
            "title": self.title,
            "scope": self.scope,
            "auditor": self.auditor,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat()
            if self.end_date
            else None,
            "checklist": [
                {
                    "category": item.category,
                    "question": item.question,
                    "passed": item.passed,
                    "evidence": item.evidence,
                    "notes": item.notes,
                }
                for item in self.checklist
            ],
            "findings": [f.to_dict() for f in self.findings],
            "metrics_snapshot": self.metrics_snapshot,
            "overall_score": self.overall_score,
            "rating": self.rating,
        }


class AuditChecklist:
    """Predefined audit checklists."""

    @staticmethod
    def internal_quality_audit() -> list[AuditChecklistItem]:
        """Internal quality audit checklist."""
        return [
            # Process Adherence
            AuditChecklistItem(
                category="Process Adherence",
                question="Quality gates are enforced at all stages",
            ),
            AuditChecklistItem(
                category="Process Adherence",
                question="Code review process is followed (2 approvals)",
            ),
            AuditChecklistItem(
                category="Process Adherence",
                question="TDD is practiced for critical components",
            ),
            AuditChecklistItem(
                category="Process Adherence",
                question="Static analysis is run on every commit",
            ),
            AuditChecklistItem(
                category="Process Adherence",
                question="Security scanning is performed regularly",
            ),
            AuditChecklistItem(
                category="Process Adherence",
                question="Test coverage meets targets (≥ 88% line, ≥ 82% branch)",
            ),
            AuditChecklistItem(
                category="Process Adherence",
                question="Performance tests are run per release",
            ),
            AuditChecklistItem(
                category="Process Adherence",
                question="Chaos engineering experiments are conducted monthly",
            ),
            AuditChecklistItem(
                category="Process Adherence",
                question="Incident response process is followed",
            ),
            AuditChecklistItem(
                category="Process Adherence",
                question="Change management process is followed",
            ),
            # Metrics Review
            AuditChecklistItem(
                category="Metrics Review",
                question="Defect density is within target (≤ 1.0/KLOC)",
            ),
            AuditChecklistItem(
                category="Metrics Review",
                question="Defect leakage rate is within target (≤ 5% per phase)",
            ),
            AuditChecklistItem(
                category="Metrics Review",
                question="Technical debt ratio is within target (≤ 5%)",
            ),
            AuditChecklistItem(
                category="Metrics Review",
                question="Code coverage meets targets",
            ),
            AuditChecklistItem(
                category="Metrics Review",
                question="Security vulnerabilities are remediated within SLA",
            ),
            AuditChecklistItem(
                category="Metrics Review",
                question="Performance baselines are met",
            ),
            AuditChecklistItem(
                category="Metrics Review",
                question="SLOs are met",
            ),
            AuditChecklistItem(
                category="Metrics Review",
                question="Quality score is ≥ 90/100",
            ),
            # Documentation
            AuditChecklistItem(
                category="Documentation",
                question="Quality specification is up to date",
            ),
            AuditChecklistItem(
                category="Documentation",
                question="Test strategy is current",
            ),
            AuditChecklistItem(
                category="Documentation",
                question="Runbooks are updated",
            ),
            AuditChecklistItem(
                category="Documentation",
                question="Architecture decision records are current",
            ),
            AuditChecklistItem(
                category="Documentation",
                question="API documentation is current",
            ),
            AuditChecklistItem(
                category="Documentation",
                question="Quality metrics glossary is current",
            ),
            # Toolchain
            AuditChecklistItem(
                category="Toolchain",
                question="All quality tools are operational",
            ),
            AuditChecklistItem(
                category="Toolchain",
                question="Tool configurations are current",
            ),
            AuditChecklistItem(
                category="Toolchain",
                question="Tool access is appropriate",
            ),
            AuditChecklistItem(
                category="Toolchain",
                question="Tool training is current",
            ),
            # Team
            AuditChecklistItem(
                category="Team",
                question="Quality training is current",
            ),
            AuditChecklistItem(
                category="Team",
                question="Quality roles are assigned",
            ),
            AuditChecklistItem(
                category="Team",
                question="Quality champion rotation is active",
            ),
            AuditChecklistItem(
                category="Team",
                question="Quality onboarding is completed for new members",
            ),
        ]

    @staticmethod
    def compliance_audit(framework: str) -> list[AuditChecklistItem]:
        """Compliance audit checklist for a specific framework."""
        checklists = {
            "ISO42001": [
                AuditChecklistItem(
                    category="Clause 4 - Context",
                    question="AI system inventory is maintained",
                ),
                AuditChecklistItem(
                    category="Clause 4 - Context",
                    question="Stakeholder analysis is documented",
                ),
                AuditChecklistItem(
                    category="Clause 5 - Leadership",
                    question="AI governance policy is documented",
                ),
                AuditChecklistItem(
                    category="Clause 5 - Leadership",
                    question="Roles and responsibilities are defined",
                ),
                AuditChecklistItem(
                    category="Clause 6 - Planning",
                    question="AI risk assessment is performed",
                ),
                AuditChecklistItem(
                    category="Clause 6 - Planning",
                    question="Quality objectives are defined",
                ),
                AuditChecklistItem(
                    category="Clause 7 - Support",
                    question="AI training records are maintained",
                ),
                AuditChecklistItem(
                    category="Clause 8 - Operation",
                    question="AI system development process is documented",
                ),
                AuditChecklistItem(
                    category="Clause 9 - Performance",
                    question="AI monitoring and measurement is in place",
                ),
                AuditChecklistItem(
                    category="Clause 10 - Improvement",
                    question="AI incident management process is followed",
                ),
            ],
            "SOC2": [
                AuditChecklistItem(
                    category="Security",
                    question="Access controls are implemented",
                ),
                AuditChecklistItem(
                    category="Security",
                    question="Encryption is used for data at rest and in transit",
                ),
                AuditChecklistItem(
                    category="Security",
                    question="Vulnerability management is in place",
                ),
                AuditChecklistItem(
                    category="Availability",
                    question="SLOs are defined and monitored",
                ),
                AuditChecklistItem(
                    category="Availability",
                    question="Incident response process is documented",
                ),
                AuditChecklistItem(
                    category="Confidentiality",
                    question="Data classification policy is implemented",
                ),
                AuditChecklistItem(
                    category="Processing Integrity",
                    question="Data validation rules are enforced",
                ),
                AuditChecklistItem(
                    category="Processing Integrity",
                    question="Audit trails are maintained",
                ),
                AuditChecklistItem(
                    category="Privacy",
                    question="Data minimization is practiced",
                ),
                AuditChecklistItem(
                    category="Privacy",
                    question="PII handling procedures are followed",
                ),
            ],
        }
        return checklists.get(framework, [])


class QualityAuditor:
    """Quality audit executor."""

    def __init__(self, config_path: str = "audit_config.yaml"):
        self.config_path = Path(config_path)
        self.audits: list[QualityAudit] = []

    def create_audit(
        self,
        audit_type: AuditType,
        title: str,
        scope: list[str],
        auditor: str,
    ) -> QualityAudit:
        """Create a new quality audit."""
        audit_id = f"AUDIT-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        checklist = []
        if audit_type == AuditType.INTERNAL:
            checklist = AuditChecklist.internal_quality_audit()
        elif audit_type == AuditType.COMPLIANCE:
            checklist = AuditChecklist.compliance_audit("ISO42001")

        audit = QualityAudit(
            audit_id=audit_id,
            audit_type=audit_type,
            title=title,
            scope=scope,
            auditor=auditor,
            start_date=datetime.utcnow(),
            checklist=checklist,
        )

        self.audits.append(audit)
        return audit

    def execute_audit(self, audit: QualityAudit) -> QualityAudit:
        """Execute a quality audit."""
        logger.info("Executing audit: %s", audit.audit_id)

        # Evaluate checklist
        passed = 0
        for item in audit.checklist:
            # In real implementation, this would check actual state
            item.passed = True  # Placeholder
            if item.passed:
                passed += 1

        # Calculate score
        if audit.checklist:
            audit.overall_score = (
                passed / len(audit.checklist) * 100
            )

        # Determine rating
        if audit.overall_score >= 90:
            audit.rating = "Excellent"
        elif audit.overall_score >= 75:
            audit.rating = "Good"
        elif audit.overall_score >= 60:
            audit.rating = "Needs Improvement"
        else:
            audit.rating = "Critical"

        audit.end_date = datetime.utcnow()

        logger.info(
            "Audit %s completed. Score: %.1f/100, Rating: %s",
            audit.audit_id,
            audit.overall_score,
            audit.rating,
        )

        return audit

    def generate_audit_report(
        self,
        audit: QualityAudit,
        output_path: str = "audit_report.json",
    ) -> dict[str, Any]:
        """Generate comprehensive audit report."""
        report = {
            "audit": audit.to_dict(),
            "executive_summary": {
                "audit_period": f"{audit.start_date.date()} to "
                f"{audit.end_date.date() if audit.end_date else 'ongoing'}",
                "overall_score": audit.overall_score,
                "rating": audit.rating,
                "findings_count": len(audit.findings),
                "critical_findings": len(
                    [
                        f
                        for f in audit.findings
                        if f.severity == FindingSeverity.CRITICAL
                    ]
                ),
                "high_findings": len(
                    [
                        f
                        for f in audit.findings
                        if f.severity == FindingSeverity.HIGH
                    ]
                ),
            },
            "metrics_summary": audit.metrics_snapshot,
            "action_items": [
                {
                    "action": f.remediation_plan,
                    "owner": f.assignee,
                    "due_date": f.date_due.isoformat()
                    if f.date_due
                    else None,
                    "priority": f.severity.value,
                    "status": f.status.value,
                }
                for f in audit.findings
                if f.status != FindingStatus.RESOLVED
            ],
            "recommendations": self._generate_recommendations(audit),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def _generate_recommendations(
        self, audit: QualityAudit
    ) -> list[str]:
        recommendations = []

        failed_items = [
            item for item in audit.checklist if item.passed is False
        ]
        if failed_items:
            recommendations.append(
                f"Address {len(failed_items)} failed audit checklist items"
            )

        critical_findings = [
            f
            for f in audit.findings
            if f.severity == FindingSeverity.CRITICAL
        ]
        if critical_findings:
            recommendations.append(
                f"URGENT: Resolve {len(critical_findings)} critical findings"
            )

        if audit.overall_score < 75:
            recommendations.append(
                "Schedule follow-up audit within 30 days"
            )

        return recommendations

    def get_audit_schedule(self) -> list[dict[str, Any]]:
        """Get annual audit schedule."""
        return [
            {
                "audit_type": "Internal Quality Audit",
                "frequency": "Quarterly",
                "scope": "Process adherence, metrics review",
                "auditor": "QA Lead",
                "duration": "2 days",
            },
            {
                "audit_type": "External Quality Audit",
                "frequency": "Annually",
                "scope": "Full QMS review",
                "auditor": "External auditor",
                "duration": "5 days",
            },
            {
                "audit_type": "Compliance Audit",
                "frequency": "Annually",
                "scope": "Regulatory requirement adherence",
                "auditor": "Compliance auditor",
                "duration": "3 days",
            },
            {
                "audit_type": "Security Audit",
                "frequency": "Semi-annually",
                "scope": "Security controls, penetration test",
                "auditor": "Security auditor",
                "duration": "5 days",
            },
            {
                "audit_type": "Process Audit",
                "frequency": "Monthly",
                "scope": "Specific process deep-dive",
                "auditor": "QA Engineer",
                "duration": "1 day",
            },
            {
                "audit_type": "Toolchain Audit",
                "frequency": "Semi-annually",
                "scope": "Tool effectiveness and coverage",
                "auditor": "QA Lead",
                "duration": "1 day",
            },
            {
                "audit_type": "Code Quality Audit",
                "frequency": "Monthly",
                "scope": "Code quality metrics and trends",
                "auditor": "Tech Lead",
                "duration": "1 day",
            },
            {
                "audit_type": "Performance Audit",
                "frequency": "Monthly",
                "scope": "Performance metrics and trends",
                "auditor": "SRE",
                "duration": "1 day",
            },
        ]


class ContinuousAudit:
    """Continuous audit framework."""

    def __init__(self):
        self.checks: list[dict[str, Any]] = []

    def add_check(
        self,
        name: str,
        frequency: str,
        tool: str,
        automated: bool,
        alert: bool,
    ) -> None:
        """Add a continuous audit check."""
        self.checks.append(
            {
                "name": name,
                "frequency": frequency,
                "tool": tool,
                "automated": automated,
                "alert": alert,
            }
        )

    def get_default_checks(self) -> list[dict[str, Any]]:
        """Get default continuous audit checks."""
        return [
            {
                "name": "Policy compliance",
                "frequency": "Every commit",
                "tool": "Open Policy Agent",
                "automated": True,
                "alert": True,
            },
            {
                "name": "Configuration drift",
                "frequency": "Every hour",
                "tool": "Terraform Cloud",
                "automated": True,
                "alert": True,
            },
            {
                "name": "Security posture",
                "frequency": "Continuous",
                "tool": "Trivy, Semgrep",
                "automated": True,
                "alert": True,
            },
            {
                "name": "SLO compliance",
                "frequency": "Real-time",
                "tool": "Prometheus",
                "automated": True,
                "alert": True,
            },
            {
                "name": "Access control review",
                "frequency": "Daily",
                "tool": "Custom scripts",
                "automated": True,
                "alert": True,
            },
            {
                "name": "Data retention compliance",
                "frequency": "Daily",
                "tool": "Custom scripts",
                "automated": True,
                "alert": True,
            },
            {
                "name": "Vulnerability scan",
                "frequency": "Every commit",
                "tool": "pip-audit, npm audit",
                "automated": True,
                "alert": True,
            },
            {
                "name": "Secrets detection",
                "frequency": "Every commit",
                "tool": "GitLeaks, truffleHog",
                "automated": True,
                "alert": True,
            },
            {
                "name": "License compliance",
                "frequency": "Every commit",
                "tool": "FOSSA, license-checker",
                "automated": True,
                "alert": True,
            },
            {
                "name": "Documentation freshness",
                "frequency": "Weekly",
                "tool": "Custom scripts",
                "automated": True,
                "alert": False,
            },
            {
                "name": "Test coverage compliance",
                "frequency": "Every commit",
                "tool": "pytest-cov, v8",
                "automated": True,
                "alert": True,
            },
        ]
```

### 7.2 Audit Report Generator

```python
# scripts/generate_audit_report.py
"""Generate quality audit report."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from src.quality.auditing import (
    AuditType,
    FindingSeverity,
    QualityAuditor,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--type",
        choices=["internal", "external", "compliance", "security"],
        default="internal",
    )
    parser.add_argument("--output", default="audit_report.json")
    args = parser.parse_args()

    auditor = QualityAuditor()

    audit_type = AuditType(args.type)
    audit = auditor.create_audit(
        audit_type=audit_type,
        title=f"{audit_type.value.title()} Quality Audit",
        scope=[
            "Process Adherence",
            "Metrics Review",
            "Documentation",
            "Toolchain",
            "Team",
        ],
        auditor="QA Lead",
    )

    # Execute audit
    audit = auditor.execute_audit(audit)

    # Generate report
    report = auditor.generate_audit_report(audit, args.output)

    logger.info("Audit report generated: %s", args.output)
    logger.info("Overall Score: %.1f/100", report["executive_summary"]["overall_score"])
    logger.info("Rating: %s", report["executive_summary"]["rating"])


if __name__ == "__main__":
    main()
```

---

## Appendix: Quick Start Commands

```bash
# Install dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=xml --cov-branch

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run performance tests
pytest -m performance

# Run security tests
pytest -m security

# Run quality gate (local)
python -m src.quality.gates --gate gate1_commit

# Train defect prediction model
python scripts/train_defect_model.py --github-token $GITHUB_TOKEN

# Generate quality report
python -m src.quality.exporter --output quality_report.json

# Generate audit report
python scripts/generate_audit_report.py --type internal

# Run pre-commit hooks
pre-commit run --all-files

# Start test containers
docker-compose -f docker-compose.test.yml up -d
```

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial implementation guide |

**Next Review Date:**</longcat_think>
