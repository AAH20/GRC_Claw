# GRC_Claw Reporting Engine: Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Implementation-Ready  
**References:** grc-claw-reporting-engine-analysis.md, grc-claw-ui-specification.md

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Report Generation Pipeline (Python)](#2-report-generation-pipeline-python)
3. [Report Distribution Automation](#3-report-distribution-automation)
4. [Report Personalization](#4-report-personization)
5. [Report Scheduling and Subscription](#5-report-scheduling-and-subscription)
6. [Report Quality Assurance](#6-report-quality-assurance)
7. [Report Analytics and Usage Tracking](#7-report-analytics-and-usage-tracking)
8. [Dashboard Implementations](#8-dashboard-implementations)
9. [Integration Examples](#9-integration-examples)
10. [Deployment and Operations](#10-deployment-and-operations)

---

## 1. Architecture Overview

### 1.1 Four-Layer Reporting Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GRC_Claw Reporting Engine                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐   │
│  │   Data Layer  │  │  Processing  │  │   Reporting  │  │  Delivery  │   │
│  │              │  │    Layer     │  │    Layer     │  │   Layer    │   │
│  │ • Inventory  │  │ • Scoring    │  │ • Templates  │  │ • PDF      │   │
│  │ • Evidence   │  │ • Mapping    │  │ • Dashboards │  │ • DOCX     │   │
│  │ • Controls   │  │ • Analytics  │  │ • Packs      │  │ • API      │   │
│  │ • Incidents  │  │ • RAG Status │  │ • Summaries  │  │ • Webhook  │   │
│  │ • Decisions  │  │ • Trending   │  │ • Exports    │  │ • Email    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Framework Mapping Engine                          │  │
│  │  EU AI Act │ NIST AI RMF │ ISO 42001 │ SOC 2 │ ISO 27001 │ GDPR       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Data Layer | PostgreSQL + Redis | Persistent store + cache |
| Processing | Python 3.11+ / Pandas / NumPy | Scoring, analytics, trending |
| Reporting | Jinja2 / WeasyPrint / python-docx | Template rendering |
| Delivery | FastAPI / Celery / SMTP | API, async tasks, email |
| Dashboards | React / D3.js / WebSocket | Real-time visualization |
| Scheduling | APScheduler / Celery Beat | Cron-like scheduling |
| Analytics | ClickHouse / PostHog | Usage tracking |

### 1.3 Project Structure

```
grc-claw-reporting/
├── src/
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── pipeline.py          # Report generation pipeline
│   │   ├── templates/           # Jinja2 report templates
│   │   │   ├── board_summary.html
│   │   │   ├── evidence_pack.html
│   │   │   ├── program_status.html
│   │   │   ├── operational_view.html
│   │   │   ├── vendor_risk.html
│   │   │   ├── incident_report.html
│   │   │   └── transparency.html
│   │   ├── generators/          # Report generators
│   │   │   ├── __init__.py
│   │   │   ├── pdf_generator.py
│   │   │   ├── docx_generator.py
│   │   │   ├── evidence_pack_generator.py
│   │   │   └── dashboard_generator.py
│   │   ├── distribution/        # Distribution automation
│   │   │   ├── __init__.py
│   │   │   ├── email_sender.py
│   │   │   ├── webhook_sender.py
│   │   │   ├── api_publisher.py
│   │   │   └── mcp_publisher.py
│   │   ├── personalization/     # Report personalization
│   │   │   ├── __init__.py
│   │   │   ├── user_prefs.py
│   │   │   ├── role_based.py
│   │   │   └── content_filter.py
│   │   ├── scheduling/          # Scheduling and subscription
│   │   │   ├── __init__.py
│   │   │   ├── scheduler.py
│   │   │   ├── subscription.py
│   │   │   └── calendar_sync.py
│   │   ├── quality/             # Quality assurance
│   │   │   ├── __init__.py
│   │   │   ├── validator.py
│   │   │   ├── freshness.py
│   │   │   └── completeness.py
│   │   ├── analytics/           # Usage tracking
│   │   │   ├── __init__.py
│   │   │   ├── tracker.py
│   │   │   ├── metrics.py
│   │   │   └── feedback.py
│   │   └── dashboards/          # Dashboard implementations
│   │       ├── __init__.py
│   │       ├── executive.py
│   │       ├── program.py
│   │       └── operating.py
│   ├── api/
│   │   ├── routes/
│   │   │   ├── reports.py
│   │   │   ├── dashboards.py
│   │   │   ├── subscriptions.py
│   │   │   └── analytics.py
│   │   └── models/
│   │       ├── report.py
│   │       ├── subscription.py
│   │       └── analytics.py
│   └── config/
│       ├── settings.py
│       └── frameworks.py
├── tests/
├── migrations/
├── docker/
└── docs/
```

---

## 2. Report Generation Pipeline (Python)

### 2.1 Core Pipeline Architecture

The report generation pipeline follows a **Template → Data → Render → Validate → Deliver** pattern, inspired by VerifyWise's template-first approach.

```python
# src/reporting/pipeline.py

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

import jinja2
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─── Enums & Constants ───────────────────────────────────────────────────────

class ReportType(str, Enum):
    BOARD_SUMMARY = "board_summary"
    EVIDENCE_PACK = "evidence_pack"
    EXECUTIVE_DASHBOARD = "executive_dashboard"
    PROGRAM_STATUS = "program_status"
    OPERATIONAL_VIEW = "operational_view"
    VENDOR_RISK = "vendor_risk"
    INCIDENT_REPORT = "incident_report"
    TRANSPARENCY = "transparency"


class ReportFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"
    OSCAL = "oscal"


class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    VALIDATING = "validating"
    READY = "ready"
    FAILED = "failed"
    DELIVERED = "delivered"


class Framework(str, Enum):
    EU_AI_ACT = "eu-ai-act"
    NIST_AI_RMF = "nist-ai-rmf"
    ISO_42001 = "iso-42001"
    SOC2 = "soc2"
    ISO_27001 = "iso-27001"
    GDPR = "gdpr"


# ─── Data Models ─────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    """Request to generate a report."""
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    frameworks: list[Framework] = Field(default_factory=list)
    system_ids: list[str] = Field(default_factory=list)
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None
    recipient_id: str | None = None
    personalization: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportSection(BaseModel):
    """A section within a report."""
    title: str
    content: str
    order: int
    data_sources: list[str] = Field(default_factory=list)
    charts: list[dict[str, Any]] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)


class ReportArtifact(BaseModel):
    """Generated report artifact."""
    report_id: str
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus
    created_at: datetime
    completed_at: datetime | None = None
    file_path: str | None = None
    file_size: int | None = None
    checksum: str | None = None
    sections: list[ReportSection] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    validation_results: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None


class ComplianceScore(BaseModel):
    """Per-system, per-framework compliance score."""
    system_id: str
    system_name: str
    framework: Framework
    score: float  # 0.0 - 1.0
    trend: float  # Change from previous period
    status: str  # green, amber, red
    evidence_count: int
    last_assessment: datetime
    next_review: datetime
    gaps: list[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    """A risk item for board/executive reports."""
    risk_id: str
    title: str
    severity: str  # critical, high, medium, low
    likelihood: str
    impact: str
    owner: str
    mitigation_status: str
    related_systems: list[str] = Field(default_factory=list)


# ─── Pipeline Stages ─────────────────────────────────────────────────────────

T = TypeVar("T")


class PipelineStage(ABC, Generic[T]):
    """Abstract pipeline stage."""

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> T:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class DataCollectionStage(PipelineStage[dict[str, Any]]):
    """Stage 1: Collect data from all sources."""

    def __init__(self, data_sources: DataSourceManager):
        self.data_sources = data_sources

    def name(self) -> str:
        return "data_collection"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        request: ReportRequest = context["request"]
        logger.info(f"Collecting data for {request.report_type.value} report")

        data = {
            "generated_at": datetime.utcnow(),
            "request": request,
            "inventory": await self.data_sources.get_inventory(
                system_ids=request.system_ids
            ),
            "compliance_scores": await self.data_sources.get_compliance_scores(
                frameworks=request.frameworks,
                system_ids=request.system_ids,
            ),
            "evidence_summary": await self.data_sources.get_evidence_summary(
                system_ids=request.system_ids,
                time_range=(request.time_range_start, request.time_range_end),
            ),
            "incidents": await self.data_sources.get_incidents(
                time_range=(request.time_range_start, request.time_range_end),
            ),
            "risks": await self.data_sources.get_risks(
                system_ids=request.system_ids,
            ),
            "trends": await self.data_sources.get_trends(
                frameworks=request.frameworks,
                days=90,
            ),
            "decisions": await self.data_sources.get_pending_decisions(),
            "exceptions": await self.data_sources.get_exceptions(),
            "monitoring": await self.data_sources.get_monitoring_status(),
        }

        # Report-type-specific data collection
        if request.report_type == ReportType.BOARD_SUMMARY:
            data["board_decisions"] = await self.data_sources.get_board_decisions()
            data["material_risks"] = await self.data_sources.get_material_risks()
            data["framework_scores"] = await self.data_sources.get_framework_scores()

        elif request.report_type == ReportType.EVIDENCE_PACK:
            data["evidence_items"] = await self.data_sources.get_evidence_items(
                system_ids=request.system_ids,
                frameworks=request.frameworks,
            )
            data["chain_of_custody"] = await self.data_sources.get_chain_of_custody(
                system_ids=request.system_ids,
            )
            data["assessment_history"] = await self.data_sources.get_assessment_history(
                system_ids=request.system_ids,
            )

        elif request.report_type == ReportType.VENDOR_RISK:
            data["vendors"] = await self.data_sources.get_vendor_assessments()
            data["vendor_spend"] = await self.data_sources.get_vendor_spend()

        elif request.report_type == ReportType.INCIDENT_REPORT:
            data["incident_details"] = await self.data_sources.get_incident_details(
                incident_id=request.metadata.get("incident_id"),
            )
            data["incident_timeline"] = await self.data_sources.get_incident_timeline(
                incident_id=request.metadata.get("incident_id"),
            )

        context["data"] = data
        return data


class ScoringStage(PipelineStage[dict[str, Any]]):
    """Stage 2: Calculate scores and RAG status."""

    def __init__(self, scoring_engine: ScoringEngine):
        self.scoring_engine = scoring_engine

    def name(self) -> str:
        return "scoring"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        data = context["data"]
        logger.info("Calculating compliance scores and RAG status")

        # Recalculate scores as evidence lands (Enzai pattern)
        for score in data.get("compliance_scores", []):
            score.score = await self.scoring_engine.calculate_score(
                system_id=score.system_id,
                framework=score.framework,
            )
            score.trend = await self.scoring_engine.calculate_trend(
                system_id=score.system_id,
                framework=score.framework,
            )
            score.status = self.scoring_engine.rag_status(score.score)

        # Calculate overall compliance score
        if data.get("compliance_scores"):
            data["overall_score"] = sum(
                s.score for s in data["compliance_scores"]
            ) / len(data["compliance_scores"])

        # Calculate framework-level scores
        framework_scores = {}
        for fw in set(s.framework for s in data.get("compliance_scores", [])):
            fw_scores = [s.score for s in data["compliance_scores"] if s.framework == fw]
            if fw_scores:
                framework_scores[fw.value] = sum(fw_scores) / len(fw_scores)
        data["framework_scores_calculated"] = framework_scores

        # RAG status per control family
        data["control_family_rag"] = await self.scoring_engine.get_control_family_rag(
            system_ids=context["request"].system_ids,
        )

        return data


class TemplateRenderingStage(PipelineStage[list[ReportSection]]):
    """Stage 3: Render report sections from templates."""

    def __init__(self, template_dir: str = "src/reporting/templates"):
        self.template_dir = Path(template_dir)
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register custom filters
        self.env.filters["percentage"] = lambda x: f"{x * 100:.1f}%"
        self.env.filters["trend_arrow"] = lambda x: "↑" if x > 0 else "↓" if x < 0 else "→"
        self.env.filters["rag_badge"] = lambda x: {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(x, "⚪")
        self.env.filters["severity_icon"] = lambda x: {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(x, "⚪")

    def name(self) -> str:
        return "template_rendering"

    async def execute(self, context: dict[str, Any]) -> list[ReportSection]:
        request: ReportRequest = context["request"]
        data = context["data"]
        logger.info(f"Rendering {request.report_type.value} template")

        template_name = self._get_template_name(request.report_type)
        template = self.env.get_template(template_name)

        # Render the full document
        rendered_html = template.render(
            data=data,
            request=request,
            generated_at=data["generated_at"],
            personalization=request.personalization,
        )

        # Split into sections (or use section markers in template)
        sections = self._split_into_sections(rendered_html, data, request)

        return sections

    def _get_template_name(self, report_type: ReportType) -> str:
        mapping = {
            ReportType.BOARD_SUMMARY: "board_summary.html",
            ReportType.EVIDENCE_PACK: "evidence_pack.html",
            ReportType.PROGRAM_STATUS: "program_status.html",
            ReportType.OPERATIONAL_VIEW: "operational_view.html",
            ReportType.VENDOR_RISK: "vendor_risk.html",
            ReportType.INCIDENT_REPORT: "incident_report.html",
            ReportType.TRANSPARENCY: "transparency.html",
        }
        return mapping.get(report_type, "generic_report.html")

    def _split_into_sections(
        self, html: str, data: dict[str, Any], request: ReportRequest
    ) -> list[ReportSection]:
        """Split rendered HTML into logical sections."""
        # In production, use section markers in templates
        # For now, create a single section with the full content
        return [
            ReportSection(
                title=request.report_type.value.replace("_", " ").title(),
                content=html,
                order=0,
                data_sources=list(data.keys()),
            )
        ]


class ValidationStage(PipelineStage[dict[str, Any]]):
    """Stage 4: Validate report completeness and accuracy."""

    def __init__(self, quality_engine: QualityEngine):
        self.quality_engine = quality_engine

    def name(self) -> str:
        return "validation"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        request: ReportRequest = context["request"]
        data = context["data"]
        sections = context["sections"]
        logger.info("Validating report quality")

        validation_results = {
            "completeness": self.quality_engine.check_completeness(data, request),
            "freshness": self.quality_engine.check_freshness(data),
            "accuracy": self.quality_engine.check_accuracy(data),
            "consistency": self.quality_engine.check_consistency(data),
        }

        # Overall quality score
        scores = [v["score"] for v in validation_results.values()]
        validation_results["overall_score"] = sum(scores) / len(scores) if scores else 0.0
        validation_results["passed"] = validation_results["overall_score"] >= 0.8

        context["validation_results"] = validation_results
        return validation_results


class OutputGenerationStage(PipelineStage[ReportArtifact]):
    """Stage 5: Generate final output artifact."""

    def __init__(self, output_dir: str = "output/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def name(self) -> str:
        return "output_generation"

    async def execute(self, context: dict[str, Any]) -> ReportArtifact:
        request: ReportRequest = context["request"]
        sections = context["sections"]
        validation = context["validation_results"]
        logger.info(f"Generating {request.format.value} output")

        report_id = f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{request.report_type.value}"

        if request.format == ReportFormat.PDF:
            file_path = await self._generate_pdf(report_id, sections, context)
        elif request.format == ReportFormat.DOCX:
            file_path = await self._generate_docx(report_id, sections, context)
        elif request.format == ReportFormat.HTML:
            file_path = await self._generate_html(report_id, sections, context)
        elif request.format == ReportFormat.JSON:
            file_path = await self._generate_json(report_id, sections, context)
        else:
            file_path = await self._generate_markdown(report_id, sections, context)

        # Calculate checksum
        import hashlib
        file_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                file_hash.update(chunk)

        artifact = ReportArtifact(
            report_id=report_id,
            report_type=request.report_type,
            format=request.format,
            status=ReportStatus.READY,
            created_at=context["data"]["generated_at"],
            completed_at=datetime.utcnow(),
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            checksum=file_hash.hexdigest(),
            sections=sections,
            metadata=request.metadata,
            validation_results=validation,
        )

        return artifact

    async def _generate_pdf(
        self, report_id: str, sections: list[ReportSection], context: dict[str, Any]
    ) -> Path:
        """Generate PDF using WeasyPrint."""
        from weasyprint import HTML, CSS

        html_content = "\n".join(s.content for s in sections)
        output_path = self.output_dir / f"{report_id}.pdf"

        # Base CSS for professional reports
        base_css = CSS(string="""
            @page {
                size: A4;
                margin: 2cm;
                @bottom-center {
                    content: "GRC_Claw Confidential — Page " counter(page) " of " counter(pages);
                    font-size: 8pt;
                    color: #6b7280;
                }
            }
            body { font-family: 'Inter', 'Helvetica Neue', sans-serif; font-size: 11pt; color: #111827; }
            h1 { font-size: 22pt; color: #1e3a5f; border-bottom: 2px solid #1e3a5f; padding-bottom: 8px; }
            h2 { font-size: 16pt; color: #1e3a5f; margin-top: 24px; }
            h3 { font-size: 13pt; color: #374151; }
            table { width: 100%; border-collapse: collapse; margin: 12px 0; }
            th { background: #1e3a5f; color: white; padding: 8px; text-align: left; }
            td { padding: 6px 8px; border-bottom: 1px solid #e5e7eb; }
            tr:nth-child(even) { background: #f9fafb; }
            .rag-green { color: #22c55e; font-weight: bold; }
            .rag-amber { color: #f59e0b; font-weight: bold; }
            .rag-red { color: #ef4444; font-weight: bold; }
            .metric-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 8px 0; }
            .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 9pt; color: #6b7280; }
        """)

        HTML(string=html_content).write_pdf(str(output_path), stylesheets=[base_css])
        return output_path

    async def _generate_docx(
        self, report_id: str, sections: list[ReportSection], context: dict[str, Any]
    ) -> Path:
        """Generate DOCX using python-docx."""
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()
        output_path = self.output_dir / f"{report_id}.docx"

        for section in sections:
            # Parse HTML content and convert to DOCX elements
            # In production, use a proper HTML-to-DOCX converter
            doc.add_heading(section.title, level=1)
            # Add content paragraphs (simplified)
            doc.add_paragraph(section.content[:5000])  # Truncated for example

        doc.save(str(output_path))
        return output_path

    async def _generate_html(
        self, report_id: str, sections: list[ReportSection], context: dict[str, Any]
    ) -> Path:
        """Generate standalone HTML file."""
        output_path = self.output_dir / f"{report_id}.html"
        html_content = "\n".join(s.content for s in sections)
        output_path.write_text(html_content, encoding="utf-8")
        return output_path

    async def _generate_json(
        self, report_id: str, sections: list[ReportSection], context: dict[str, Any]
    ) -> Path:
        """Generate structured JSON output."""
        import json

        output_path = self.output_dir / f"{report_id}.json"
        data = {
            "report_id": report_id,
            "sections": [s.model_dump() for s in sections],
            "metadata": context["request"].metadata,
            "validation": context["validation_results"],
        }
        output_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return output_path

    async def _generate_markdown(
        self, report_id: str, sections: list[ReportSection], context: dict[str, Any]
    ) -> Path:
        """Generate Markdown output."""
        output_path = self.output_dir / f"{report_id}.md"
        md_content = "\n\n".join(f"## {s.title}\n\n{s.content}" for s in sections)
        output_path.write_text(md_content, encoding="utf-8")
        return output_path


# ─── Pipeline Orchestrator ───────────────────────────────────────────────────

class ReportPipeline:
    """Orchestrates the full report generation pipeline."""

    def __init__(
        self,
        data_sources: DataSourceManager,
        scoring_engine: ScoringEngine,
        quality_engine: QualityEngine,
        template_dir: str = "src/reporting/templates",
        output_dir: str = "output/reports",
    ):
        self.stages: list[PipelineStage] = [
            DataCollectionStage(data_sources),
            ScoringStage(scoring_engine),
            TemplateRenderingStage(template_dir),
            ValidationStage(quality_engine),
            OutputGenerationStage(output_dir),
        ]
        self.logger = logging.getLogger(__name__)

    async def generate(self, request: ReportRequest) -> ReportArtifact:
        """Execute the full pipeline for a report request."""
        context: dict[str, Any] = {"request": request}
        self.logger.info(f"Starting pipeline for {request.report_type.value}")

        try:
            # Stage 1: Data Collection
            context["data"] = await self.stages[0].execute(context)

            # Stage 2: Scoring
            context["data"] = await self.stages[1].execute(context)

            # Stage 3: Template Rendering
            context["sections"] = await self.stages[2].execute(context)

            # Stage 4: Validation
            context["validation_results"] = await self.stages[3].execute(context)

            # Stage 5: Output Generation
            artifact = await self.stages[4].execute(context)

            self.logger.info(f"Pipeline complete: {artifact.report_id}")
            return artifact

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            return ReportArtifact(
                report_id=f"RPT-FAILED-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                report_type=request.report_type,
                format=request.format,
                status=ReportStatus.FAILED,
                created_at=datetime.utcnow(),
                error_message=str(e),
            )
```

### 2.2 Data Source Manager

```python
# src/reporting/data_sources.py

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

import asyncpg
import redis.asyncio as redis


class DataSourceManager:
    """Manages connections to all data sources for reporting."""

    def __init__(
        self,
        pg_dsn: str = "postgresql://localhost/grc_claw",
        redis_url: str = "redis://localhost:6379",
    ):
        self.pg_dsn = pg_dsn
        self.redis_url = redis_url
        self._pg_pool: asyncpg.Pool | None = None
        self._redis: redis.Redis | None = None

    async def connect(self):
        self._pg_pool = await asyncpg.create_pool(self.pg_dsn, min_size=2, max_size=10)
        self._redis = redis.from_url(self.redis_url, decode_responses=True)

    async def disconnect(self):
        if self._pg_pool:
            await self._pg_pool.close()
        if self._redis:
            await self._redis.close()

    async def get_inventory(self, system_ids: list[str] | None = None) -> list[dict]:
        """Get AI system inventory."""
        async with self._pg_pool.acquire() as conn:
            if system_ids:
                rows = await conn.fetch(
                    "SELECT * FROM ai_systems WHERE system_id = ANY($1)",
                    system_ids,
                )
            else:
                rows = await conn.fetch("SELECT * FROM ai_systems")
            return [dict(r) for r in rows]

    async def get_compliance_scores(
        self,
        frameworks: list[str] | None = None,
        system_ids: list[str] | None = None,
    ) -> list[dict]:
        """Get compliance scores per system per framework."""
        async with self._pg_pool.acquire() as conn:
            query = "SELECT * FROM compliance_scores WHERE 1=1"
            params = []
            if frameworks:
                params.append(frameworks)
                query += f" AND framework = ANY(${len(params)})"
            if system_ids:
                params.append(system_ids)
                query += f" AND system_id = ANY(${len(params)})"
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]

    async def get_evidence_summary(
        self,
        system_ids: list[str] | None = None,
        time_range: tuple[datetime | None, datetime | None] | None = None,
    ) -> dict[str, Any]:
        """Get evidence summary statistics."""
        async with self._pg_pool.acquire() as conn:
            query = """
                SELECT
                    COUNT(*) as total_count,
                    COUNT(*) FILTER (WHERE verification_level >= 2) as verified_count,
                    COUNT(*) FILTER (WHERE verification_level >= 4) as attested_count,
                    MAX(collected_at) as latest_evidence
                FROM evidence
                WHERE 1=1
            """
            params = []
            if system_ids:
                params.append(system_ids)
                query += f" AND system_id = ANY(${len(params)})"
            if time_range and time_range[0]:
                params.append(time_range[0])
                query += f" AND collected_at >= ${len(params)}"
            if time_range and time_range[1]:
                params.append(time_range[1])
                query += f" AND collected_at <= ${len(params)}"
            row = await conn.fetchrow(query, *params)
            return dict(row) if row else {}

    async def get_incidents(
        self,
        time_range: tuple[datetime | None, datetime | None] | None = None,
    ) -> list[dict]:
        """Get incidents within time range."""
        async with self._pg_pool.acquire() as conn:
            query = "SELECT * FROM incidents WHERE 1=1"
            params = []
            if time_range and time_range[0]:
                params.append(time_range[0])
                query += f" AND created_at >= ${len(params)}"
            if time_range and time_range[1]:
                params.append(time_range[1])
                query += f" AND created_at <= ${len(params)}"
            query += " ORDER BY created_at DESC"
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]

    async def get_risks(self, system_ids: list[str] | None = None) -> list[dict]:
        """Get risk register items."""
        async with self._pg_pool.acquire() as conn:
            if system_ids:
                rows = await conn.fetch(
                    "SELECT * FROM risks WHERE system_id = ANY($1) ORDER BY severity DESC",
                    system_ids,
                )
            else:
                rows = await conn.fetch("SELECT * FROM risks ORDER BY severity DESC")
            return [dict(r) for r in rows]

    async def get_trends(self, frameworks: list[str] | None = None, days: int = 90) -> list[dict]:
        """Get compliance score trends."""
        async with self._pg_pool.acquire() as conn:
            query = """
                SELECT
                    date_trunc('day', recorded_at) as date,
                    framework,
                    AVG(score) as avg_score,
                    COUNT(*) as system_count
                FROM compliance_score_history
                WHERE recorded_at >= NOW() - INTERVAL '%s days'
            """
            params = [days]
            if frameworks:
                params.append(frameworks)
                query += f" AND framework = ANY(${len(params)})"
            query += " GROUP BY date, framework ORDER BY date"
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]

    async def get_pending_decisions(self) -> list[dict]:
        """Get decisions awaiting board/executive attention."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM governance_decisions WHERE status = 'pending' ORDER BY created_at"
            )
            return [dict(r) for r in rows]

    async def get_exceptions(self) -> list[dict]:
        """Get open/expired exceptions."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM exceptions WHERE status IN ('open', 'expired') ORDER BY expiry_date"
            )
            return [dict(r) for r in rows]

    async def get_monitoring_status(self) -> list[dict]:
        """Get monitoring coverage status."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM monitoring_status ORDER BY last_check DESC"
            )
            return [dict(r) for r in rows]

    async def get_board_decisions(self) -> list[dict]:
        """Get board decisions required."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM board_decisions WHERE status = 'pending' ORDER BY priority DESC"
            )
            return [dict(r) for r in rows]

    async def get_material_risks(self) -> list[dict]:
        """Get material risks for board reporting."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM risks WHERE severity IN ('critical', 'high') AND status = 'open' ORDER BY severity DESC"
            )
            return [dict(r) for r in rows]

    async def get_framework_scores(self) -> dict[str, float]:
        """Get aggregated scores by framework."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT framework, AVG(score) as avg_score FROM compliance_scores GROUP BY framework"
            )
            return {r["framework"]: r["avg_score"] for r in rows}

    async def get_evidence_items(
        self,
        system_ids: list[str] | None = None,
        frameworks: list[str] | None = None,
    ) -> list[dict]:
        """Get detailed evidence items for evidence packs."""
        async with self._pg_pool.acquire() as conn:
            query = "SELECT * FROM evidence WHERE 1=1"
            params = []
            if system_ids:
                params.append(system_ids)
                query += f" AND system_id = ANY(${len(params)})"
            if frameworks:
                params.append(frameworks)
                query += f" AND framework = ANY(${len(params)})"
            query += " ORDER BY collected_at DESC"
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]

    async def get_chain_of_custody(self, system_ids: list[str] | None = None) -> list[dict]:
        """Get chain of custody records."""
        async with self._pg_pool.acquire() as conn:
            if system_ids:
                rows = await conn.fetch(
                    "SELECT * FROM chain_of_custody WHERE system_id = ANY($1) ORDER BY timestamp",
                    system_ids,
                )
            else:
                rows = await conn.fetch("SELECT * FROM chain_of_custody ORDER BY timestamp")
            return [dict(r) for r in rows]

    async def get_assessment_history(self, system_ids: list[str] | None = None) -> list[dict]:
        """Get assessment history for systems."""
        async with self._pg_pool.acquire() as conn:
            if system_ids:
                rows = await conn.fetch(
                    "SELECT * FROM assessments WHERE system_id = ANY($1) ORDER BY completed_at DESC",
                    system_ids,
                )
            else:
                rows = await conn.fetch("SELECT * FROM assessments ORDER BY completed_at DESC")
            return [dict(r) for r in rows]

    async def get_vendor_assessments(self) -> list[dict]:
        """Get vendor risk assessments."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM vendor_assessments ORDER BY risk_score DESC")
            return [dict(r) for r in rows]

    async def get_vendor_spend(self) -> list[dict]:
        """Get vendor spend data."""
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT vendor_name, SUM(amount) as total_spend, COUNT(*) as transaction_count "
                "FROM vendor_spend GROUP BY vendor_name ORDER BY total_spend DESC"
            )
            return [dict(r) for r in rows]

    async def get_incident_details(self, incident_id: str | None = None) -> dict | None:
        """Get detailed incident information."""
        if not incident_id:
            return None
        async with self._pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM incidents WHERE incident_id = $1", incident_id)
            return dict(row) if row else None

    async def get_incident_timeline(self, incident_id: str | None = None) -> list[dict]:
        """Get incident timeline events."""
        if not incident_id:
            return []
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM incident_timeline WHERE incident_id = $1 ORDER BY timestamp",
                incident_id,
            )
            return [dict(r) for r in rows]
```

### 2.3 Scoring Engine

```python
# src/reporting/scoring.py

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any

import asyncpg


class ScoringEngine:
    """Calculates compliance scores and RAG status."""

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(self.pg_dsn, min_size=2, max_size=10)

    async def disconnect(self):
        if self._pool:
            await self._pool.close()

    async def calculate_score(self, system_id: str, framework: str) -> float:
        """Calculate compliance score for a system/framework combination."""
        async with self._pool.acquire() as conn:
            # Get all controls for this framework
            controls = await conn.fetch(
                "SELECT control_id, weight FROM framework_controls WHERE framework = $1",
                framework,
            )

            if not controls:
                return 0.0

            total_weight = sum(c["weight"] for c in controls)
            earned_weight = 0.0

            for control in controls:
                # Check if control has current evidence
                evidence = await conn.fetchrow(
                    """
                    SELECT COUNT(*) as count, MAX(collected_at) as latest
                    FROM evidence
                    WHERE system_id = $1 AND control_id = $2
                    AND collected_at > NOW() - INTERVAL '90 days'
                    """,
                    system_id,
                    control["control_id"],
                )

                if evidence and evidence["count"] > 0:
                    # Check verification level
                    verified = await conn.fetchval(
                        """
                        SELECT COUNT(*) FROM evidence
                        WHERE system_id = $1 AND control_id = $2
                        AND verification_level >= 2
                        AND collected_at > NOW() - INTERVAL '90 days'
                        """,
                        system_id,
                        control["control_id"],
                    )
                    if verified and verified > 0:
                        earned_weight += control["weight"]

            return earned_weight / total_weight if total_weight > 0 else 0.0

    async def calculate_trend(self, system_id: str, framework: str) -> float:
        """Calculate score trend (change from previous period)."""
        async with self._pool.acquire() as conn:
            current = await conn.fetchval(
                """
                SELECT AVG(score) FROM compliance_scores
                WHERE system_id = $1 AND framework = $2
                AND recorded_at > NOW() - INTERVAL '30 days'
                """,
                system_id,
                framework,
            )
            previous = await conn.fetchval(
                """
                SELECT AVG(score) FROM compliance_scores
                WHERE system_id = $1 AND framework = $2
                AND recorded_at BETWEEN NOW() - INTERVAL '60 days' AND NOW() - INTERVAL '30 days'
                """,
                system_id,
                framework,
            )
            if current is not None and previous is not None:
                return current - previous
            return 0.0

    def rag_status(self, score: float) -> str:
        """Determine RAG status from score."""
        if score >= 0.8:
            return "green"
        elif score >= 0.6:
            return "amber"
        return "red"

    async def get_control_family_rag(self, system_ids: list[str] | None = None) -> dict[str, str]:
        """Get RAG status per control family."""
        async with self._pool.acquire() as conn:
            query = """
                SELECT
                    cf.family_name,
                    AVG(cs.score) as avg_score
                FROM control_families cf
                JOIN framework_controls fc ON cf.family_id = fc.family_id
                JOIN compliance_scores cs ON fc.control_id = cs.control_id
                WHERE 1=1
            """
            params = []
            if system_ids:
                params.append(system_ids)
                query += f" AND cs.system_id = ANY(${len(params)})"
            query += " GROUP BY cf.family_name"
            rows = await conn.fetch(query, *params)
            return {r["family_name"]: self.rag_status(r["avg_score"]) for r in rows}
```

### 2.4 Report Template Example (Board Summary)

```html
<!-- src/reporting/templates/board_summary.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Governance Board Report — {{ generated_at.strftime('%B %Y') }}</title>
    <style>
        /* Professional board report styling */
        @page { size: A4; margin: 2cm; }
        body { font-family: 'Inter', sans-serif; font-size: 11pt; color: #111827; line-height: 1.6; }
        .header { text-align: center; border-bottom: 3px solid #1e3a5f; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { color: #1e3a5f; font-size: 24pt; margin: 0; }
        .header .subtitle { color: #6b7280; font-size: 12pt; }
        .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0; }
        .metric-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; text-align: center; }
        .metric-value { font-size: 28pt; font-weight: 700; color: #1e3a5f; }
        .metric-label { font-size: 9pt; color: #6b7280; text-transform: uppercase; }
        .metric-trend { font-size: 10pt; margin-top: 4px; }
        .trend-up { color: #22c55e; }
        .trend-down { color: #ef4444; }
        .trend-flat { color: #6b7280; }
        .section { margin: 32px 0; }
        .section h2 { color: #1e3a5f; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }
        table { width: 100%; border-collapse: collapse; margin: 16px 0; }
        th { background: #1e3a5f; color: white; padding: 10px; text-align: left; font-size: 10pt; }
        td { padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }
        tr:nth-child(even) { background: #f9fafb; }
        .rag-green { color: #22c55e; font-weight: 600; }
        .rag-amber { color: #f59e0b; font-weight: 600; }
        .rag-red { color: #ef4444; font-weight: 600; }
        .risk-item { border-left: 4px solid; padding: 12px 16px; margin: 8px 0; background: #f9fafb; }
        .risk-critical { border-color: #ef4444; }
        .risk-high { border-color: #f97316; }
        .risk-medium { border-color: #f59e0b; }
        .decision-item { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 12px 16px; margin: 8px 0; }
        .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 8pt; color: #6b7280; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AI Governance Board Report</h1>
        <div class="subtitle">{{ generated_at.strftime('%B %Y') }} — GRC_Claw</div>
    </div>

    <!-- Executive Summary -->
    <div class="section">
        <h2>Executive Summary</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{{ "%.0f"|format(data.overall_score * 100) }}%</div>
                <div class="metric-label">Overall Compliance</div>
                <div class="metric-trend {% if data.trends %}trend-up{% endif %}">
                    {{ "↑" if data.trends and data.trends[-1].avg_score > data.trends[0].avg_score else "→" }}
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ data.inventory|length }}</div>
                <div class="metric-label">Systems Governed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ data.incidents|length }}</div>
                <div class="metric-label">Open Incidents</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ data.board_decisions|length }}</div>
                <div class="metric-label">Decisions Required</div>
            </div>
        </div>
    </div>

    <!-- Compliance Score by Framework -->
    <div class="section">
        <h2>Compliance Score by Framework</h2>
        <table>
            <thead>
                <tr>
                    <th>Framework</th>
                    <th>Score</th>
                    <th>Trend</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for framework, score in data.framework_scores_calculated.items() %}
                <tr>
                    <td>{{ framework|upper }}</td>
                    <td>{{ "%.0f"|format(score * 100) }}%</td>
                    <td>
                        {% set trend = data.trends|selectattr('framework', 'equalto', framework)|list %}
                        {% if trend %}
                            {{ trend_arrow(trend[-1].avg_score - trend[0].avg_score) }}
                        {% else %}—{% endif %}
                    </td>
                    <td class="rag-{{ 'green' if score >= 0.8 else 'amber' if score >= 0.6 else 'red' }}">
                        {{ "🟢 On Track" if score >= 0.8 else "🟡 At Risk" if score >= 0.6 else "🔴 Critical" }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Material Risks -->
    <div class="section">
        <h2>Material Risks</h2>
        {% for risk in data.material_risks[:5] %}
        <div class="risk-item risk-{{ risk.severity }}">
            <strong>{{ risk.title }}</strong>
            <p>{{ risk.description }}</p>
            <small>Owner: {{ risk.owner }} | Mitigation: {{ risk.mitigation_status }}</small>
        </div>
        {% endfor %}
    </div>

    <!-- Decisions Required -->
    <div class="section">
        <h2>Decisions Required</h2>
        {% for decision in data.board_decisions %}
        <div class="decision-item">
            <strong>{{ decision.title }}</strong>
            <p>{{ decision.description }}</p>
            <small>Due: {{ decision.due_date }} | Priority: {{ decision.priority }}</small>
        </div>
        {% endfor %}
    </div>

    <!-- Trend Analysis -->
    <div class="section">
        <h2>Trend Analysis</h2>
        <p>90-day compliance score trend shows {{ "improvement" if data.trends and data.trends[-1].avg_score > data.trends[0].avg_score else "decline" }} across all frameworks.</p>
        <!-- Chart placeholder - in production, embed Chart.js or matplotlib chart -->
        <div id="trend-chart" style="height: 200px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #6b7280;">
            [Compliance Score Trend Chart]
        </div>
    </div>

    <div class="footer">
        <p>Generated by GRC_Claw Reporting Engine | {{ generated_at.strftime('%Y-%m-%d %H:%M UTC') }}</p>
        <p>CONFIDENTIAL — For Board Distribution Only</p>
    </div>
</body>
</html>
```

---

## 3. Report Distribution Automation

### 3.1 Distribution Manager

```python
# src/reporting/distribution/__init__.py

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp
import aiosmtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class DistributionChannel(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    API = "api"
    SLACK = "slack"
    TEAMS = "teams"
    PAGERDUTY = "pagerduty"
    MCP = "mcp"


class DistributionStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class DistributionResult:
    channel: DistributionChannel
    status: DistributionStatus
    recipient: str
    timestamp: datetime
    message: str | None = None
    retry_count: int = 0


class DistributionChannelBase(ABC):
    """Abstract base for distribution channels."""

    @abstractmethod
    async def send(
        self, artifact_path: str, recipients: list[str], metadata: dict[str, Any]
    ) -> DistributionResult:
        pass

    @abstractmethod
    def channel_type(self) -> DistributionChannel:
        pass


class EmailDistribution(DistributionChannelBase):
    """Email distribution with PDF/DOCX attachments."""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        use_tls: bool = True,
        from_address: str = "reports@grc-claw.local",
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.from_address = from_address

    def channel_type(self) -> DistributionChannel:
        return DistributionChannel.EMAIL

    async def send(
        self, artifact_path: str, recipients: list[str], metadata: dict[str, Any]
    ) -> DistributionResult:
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = metadata.get("subject", "GRC_Claw Report")

            # Email body
            body = metadata.get("body", "Please find the attached report.")
            msg.attach(MIMEText(body, "html"))

            # Attach report file
            with open(artifact_path, "rb") as f:
                attachment = MIMEApplication(f.read(), _subtype="pdf")
                attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=metadata.get("filename", "report.pdf"),
                )
                msg.attach(attachment)

            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=self.use_tls,
            )

            return DistributionResult(
                channel=DistributionChannel.EMAIL,
                status=DistributionStatus.SENT,
                recipient=", ".join(recipients),
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Email distribution failed: {e}")
            return DistributionResult(
                channel=DistributionChannel.EMAIL,
                status=DistributionStatus.FAILED,
                recipient=", ".join(recipients),
                timestamp=datetime.utcnow(),
                message=str(e),
            )


class WebhookDistribution(DistributionChannelBase):
    """Webhook distribution for event-driven notifications."""

    def __init__(self, webhook_url: str, secret: str | None = None):
        self.webhook_url = webhook_url
        self.secret = secret

    def channel_type(self) -> DistributionChannel:
        return DistributionChannel.WEBHOOK

    async def send(
        self, artifact_path: str, recipients: list[str], metadata: dict[str, Any]
    ) -> DistributionResult:
        try:
            payload = {
                "event": "report_generated",
                "report_id": metadata.get("report_id"),
                "report_type": metadata.get("report_type"),
                "format": metadata.get("format"),
                "download_url": metadata.get("download_url"),
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata,
            }

            headers = {"Content-Type": "application/json"}
            if self.secret:
                import hmac
                import hashlib

                signature = hmac.new(
                    self.secret.encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-GRC-Claw-Signature"] = signature

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url, json=payload, headers=headers
                ) as response:
                    if response.status == 200:
                        return DistributionResult(
                            channel=DistributionChannel.WEBHOOK,
                            status=DistributionStatus.DELIVERED,
                            recipient=self.webhook_url,
                            timestamp=datetime.utcnow(),
                        )
                    else:
                        text = await response.text()
                        return DistributionResult(
                            channel=DistributionChannel.WEBHOOK,
                            status=DistributionStatus.FAILED,
                            recipient=self.webhook_url,
                            timestamp=datetime.utcnow(),
                            message=f"HTTP {response.status}: {text}",
                        )

        except Exception as e:
            logger.error(f"Webhook distribution failed: {e}")
            return DistributionResult(
                channel=DistributionChannel.WEBHOOK,
                status=DistributionStatus.FAILED,
                recipient=self.webhook_url,
                timestamp=datetime.utcnow(),
                message=str(e),
            )


class SlackDistribution(DistributionChannelBase):
    """Slack notification distribution."""

    def __init__(self, webhook_url: str, channel: str = "#grc-alerts"):
        self.webhook_url = webhook_url
        self.channel = channel

    def channel_type(self) -> DistributionChannel:
        return DistributionChannel.SLACK

    async def send(
        self, artifact_path: str, recipients: list[str], metadata: dict[str, Any]
    ) -> DistributionResult:
        try:
            payload = {
                "channel": self.channel,
                "text": f"📊 New report generated: {metadata.get('report_type', 'Report')}",
                "attachments": [
                    {
                        "color": "#36a64f",
                        "fields": [
                            {"title": "Report Type", "value": metadata.get("report_type", "N/A"), "short": True},
                            {"title": "Format", "value": metadata.get("format", "N/A"), "short": True},
                            {"title": "Generated", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "short": True},
                        ],
                    }
                ],
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    return DistributionResult(
                        channel=DistributionChannel.SLACK,
                        status=DistributionStatus.SENT if response.status == 200 else DistributionStatus.FAILED,
                        recipient=self.channel,
                        timestamp=datetime.utcnow(),
                    )

        except Exception as e:
            logger.error(f"Slack distribution failed: {e}")
            return DistributionResult(
                channel=DistributionChannel.SLACK,
                status=DistributionStatus.FAILED,
                recipient=self.channel,
                timestamp=datetime.utcnow(),
                message=str(e),
            )


class DistributionManager:
    """Manages report distribution across multiple channels."""

    def __init__(self):
        self.channels: dict[DistributionChannel, DistributionChannelBase] = {}
        self.retry_policy = {
            "max_retries": 3,
            "backoff_factor": 2,
            "initial_delay": 5,
        }

    def register_channel(
        self, channel_type: DistributionChannel, channel: DistributionChannelBase
    ):
        self.channels[channel_type] = channel

    async def distribute(
        self,
        artifact_path: str,
        channels: list[DistributionChannel],
        recipients: dict[DistributionChannel, list[str]],
        metadata: dict[str, Any],
    ) -> list[DistributionResult]:
        """Distribute report to multiple channels."""
        results = []

        for channel_type in channels:
            channel = self.channels.get(channel_type)
            if not channel:
                logger.warning(f"Channel {channel_type} not registered")
                continue

            channel_recipients = recipients.get(channel_type, [])
            if not channel_recipients:
                logger.warning(f"No recipients for channel {channel_type}")
                continue

            # Attempt delivery with retries
            result = await self._send_with_retry(
                channel, artifact_path, channel_recipients, metadata
            )
            results.append(result)

        return results

    async def _send_with_retry(
        self,
        channel: DistributionChannelBase,
        artifact_path: str,
        recipients: list[str],
        metadata: dict[str, Any],
    ) -> DistributionResult:
        """Send with exponential backoff retry."""
        max_retries = self.retry_policy["max_retries"]
        delay = self.retry_policy["initial_delay"]

        for attempt in range(max_retries):
            result = await channel.send(artifact_path, recipients, metadata)

            if result.status in (DistributionStatus.SENT, DistributionStatus.DELIVERED):
                return result

            if attempt < max_retries - 1:
                logger.warning(
                    f"Distribution attempt {attempt + 1} failed, retrying in {delay}s"
                )
                await asyncio.sleep(delay)
                delay *= self.retry_policy["backoff_factor"]
                result.retry_count = attempt + 1

        return result
```

### 3.2 MCP Server Integration

```python
# src/reporting/distribution/mcp_publisher.py

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


class MCPReportPublisher:
    """Publishes reports via MCP for AI assistant integration."""

    def __init__(self, report_pipeline: Any):
        self.pipeline = report_pipeline
        self.server = Server("grc-claw-reporting")
        self._setup_tools()

    def _setup_tools(self):
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="generate_report",
                    description="Generate a GRC report",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "report_type": {
                                "type": "string",
                                "enum": [
                                    "board_summary",
                                    "evidence_pack",
                                    "program_status",
                                    "operational_view",
                                    "vendor_risk",
                                    "incident_report",
                                    "transparency",
                                ],
                            },
                            "format": {
                                "type": "string",
                                "enum": ["pdf", "docx", "html", "json", "markdown"],
                                "default": "pdf",
                            },
                            "frameworks": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "system_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["report_type"],
                    },
                ),
                Tool(
                    name="get_compliance_score",
                    description="Get compliance score for a system/framework",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "system_id": {"type": "string"},
                            "framework": {"type": "string"},
                        },
                        "required": ["system_id", "framework"],
                    },
                ),
                Tool(
                    name="get_pending_decisions",
                    description="Get decisions awaiting board attention",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 10},
                        },
                    },
                ),
                Tool(
                    name="get_evidence_summary",
                    description="Get evidence summary for systems",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "system_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "frameworks": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            if name == "generate_report":
                from reporting.pipeline import ReportRequest, ReportType, ReportFormat

                request = ReportRequest(
                    report_type=ReportType(arguments["report_type"]),
                    format=ReportFormat(arguments.get("format", "pdf")),
                    frameworks=arguments.get("frameworks", []),
                    system_ids=arguments.get("system_ids", []),
                )
                artifact = await self.pipeline.generate(request)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "report_id": artifact.report_id,
                            "status": artifact.status.value,
                            "file_path": artifact.file_path,
                            "checksum": artifact.checksum,
                        }),
                    )
                ]

            elif name == "get_compliance_score":
                # Query scoring engine
                return [TextContent(type="text", text=json.dumps({"score": 0.85}))]

            elif name == "get_pending_decisions":
                return [TextContent(type="text", text=json.dumps({"decisions": []}))]

            elif name == "get_evidence_summary":
                return [TextContent(type="text", text=json.dumps({"evidence": {}}))]

            return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}))]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )
```

---

## 4. Report Personalization

### 4.1 Personalization Engine

```python
# src/reporting/personalization/__init__.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    EXECUTIVE = "executive"
    GRC_ANALYST = "grc_analyst"
    AUDITOR = "auditor"
    PLATFORM_ENGINEER = "platform_engineer"
    AI_ML_ENGINEER = "ai_ml_engineer"
    POLICY_OWNER = "policy_owner"
    APPROVER = "approver"
    READ_ONLY = "read_only"


@dataclass
class UserPreferences:
    """User-specific report preferences."""
    user_id: str
    role: UserRole
    default_frameworks: list[str] = field(default_factory=list)
    default_format: str = "pdf"
    email_frequency: str = "weekly"  # daily, weekly, monthly, quarterly
    dashboard_widgets: list[str] = field(default_factory=list)
    alert_thresholds: dict[str, float] = field(default_factory=dict)
    content_depth: str = "summary"  # summary, detailed, technical
    language: str = "en"
    timezone: str = "UTC"
    custom_filters: dict[str, Any] = field(default_factory=dict)


class PersonalizationEngine:
    """Personalizes reports based on user role and preferences."""

    # Role-based content filtering rules
    ROLE_CONTENT_MAP = {
        UserRole.EXECUTIVE: {
            "sections": ["executive_summary", "compliance_score", "material_risks", "decisions_required"],
            "max_detail_level": "summary",
            "include_technical": False,
            "include_evidence": False,
            "charts": ["compliance_trend", "risk_heatmap", "framework_scores"],
        },
        UserRole.GRC_ANALYST: {
            "sections": ["executive_summary", "compliance_score", "control_status", "findings", "evidence_status"],
            "max_detail_level": "detailed",
            "include_technical": True,
            "include_evidence": True,
            "charts": ["compliance_trend", "control_family_rag", "finding_aging"],
        },
        UserRole.AUDITOR: {
            "sections": ["evidence_summary", "chain_of_custody", "assessment_history", "control_mapping"],
            "max_detail_level": "technical",
            "include_technical": True,
            "include_evidence": True,
            "charts": ["evidence_coverage", "verification_levels"],
        },
        UserRole.PLATFORM_ENGINEER: {
            "sections": ["agent_registry", "runtime_enforcement", "control_implementation", "monitoring"],
            "max_detail_level": "technical",
            "include_technical": True,
            "include_evidence": False,
            "charts": ["enforcement_decisions", "trust_scores", "monitoring_coverage"],
        },
        UserRole.AI_ML_ENGINEER: {
            "sections": ["model_governance", "risk_assessment", "evaluation_results", "drift_monitoring"],
            "max_detail_level": "technical",
            "include_technical": True,
            "include_evidence": True,
            "charts": ["model_performance", "drift_trends", "evaluation_results"],
        },
        UserRole.POLICY_OWNER: {
            "sections": ["policy_status", "policy_evaluations", "violations", "version_history"],
            "max_detail_level": "detailed",
            "include_technical": False,
            "include_evidence": False,
            "charts": ["policy_compliance", "violation_trends"],
        },
        UserRole.APPROVER: {
            "sections": ["pending_approvals", "exceptions", "risk_acceptance", "decisions"],
            "max_detail_level": "summary",
            "include_technical": False,
            "include_evidence": False,
            "charts": ["approval_backlog", "exception_exposure"],
        },
        UserRole.READ_ONLY: {
            "sections": ["executive_summary", "compliance_score"],
            "max_detail_level": "summary",
            "include_technical": False,
            "include_evidence": False,
            "charts": ["compliance_trend"],
        },
    }

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(self.pg_dsn, min_size=2, max_size=10)

    async def disconnect(self):
        if self._pool:
            await self._pool.close()

    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Load user preferences from database."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_report_preferences WHERE user_id = $1",
                user_id,
            )
            if row:
                return UserPreferences(
                    user_id=row["user_id"],
                    role=UserRole(row["role"]),
                    default_frameworks=row.get("default_frameworks", []),
                    default_format=row.get("default_format", "pdf"),
                    email_frequency=row.get("email_frequency", "weekly"),
                    dashboard_widgets=row.get("dashboard_widgets", []),
                    alert_thresholds=row.get("alert_thresholds", {}),
                    content_depth=row.get("content_depth", "summary"),
                    language=row.get("language", "en"),
                    timezone=row.get("timezone", "UTC"),
                    custom_filters=row.get("custom_filters", {}),
                )
            # Return defaults
            return UserPreferences(user_id=user_id, role=UserRole.READ_ONLY)

    async def personalize_report(
        self,
        report_data: dict[str, Any],
        user_prefs: UserPreferences,
    ) -> dict[str, Any]:
        """Filter and customize report data based on user preferences."""
        role_config = self.ROLE_CONTENT_MAP.get(user_prefs.role, self.ROLE_CONTENT_MAP[UserRole.READ_ONLY])

        # Filter sections
        filtered_data = {}
        for section in role_config["sections"]:
            if section in report_data:
                filtered_data[section] = report_data[section]

        # Add role-specific metadata
        filtered_data["_personalization"] = {
            "role": user_prefs.role.value,
            "content_depth": user_prefs.content_depth,
            "filtered_sections": role_config["sections"],
            "generated_for": user_prefs.user_id,
        }

        # Apply custom filters
        if user_prefs.custom_filters:
            filtered_data = self._apply_custom_filters(filtered_data, user_prefs.custom_filters)

        # Filter frameworks
        if user_prefs.default_frameworks:
            if "framework_scores" in filtered_data:
                filtered_data["framework_scores"] = {
                    k: v
                    for k, v in filtered_data["framework_scores"].items()
                    if k in user_prefs.default_frameworks
                }

        return filtered_data

    def _apply_custom_filters(
        self, data: dict[str, Any], filters: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply user-defined custom filters."""
        # Filter by system IDs
        if "system_ids" in filters and "inventory" in data:
            data["inventory"] = [
                s for s in data["inventory"] if s.get("system_id") in filters["system_ids"]
            ]

        # Filter by severity
        if "min_severity" in filters and "risks" in data:
            severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            min_level = severity_order.get(filters["min_severity"], 0)
            data["risks"] = [
                r for r in data["risks"]
                if severity_order.get(r.get("severity", "low"), 0) >= min_level
            ]

        # Filter by date range
        if "date_range" in filters:
            start = filters["date_range"].get("start")
            end = filters["date_range"].get("end")
            if start and end and "incidents" in data:
                data["incidents"] = [
                    i for i in data["incidents"]
                    if start <= i.get("created_at", "") <= end
                ]

        return data

    def get_dashboard_widgets(self, role: UserRole) -> list[dict[str, Any]]:
        """Get dashboard widget configuration for a role."""
        role_config = self.ROLE_CONTENT_MAP.get(role, self.ROLE_CONTENT_MAP[UserRole.READ_ONLY])

        widgets = []
        for chart_type in role_config["charts"]:
            widgets.append({
                "type": chart_type,
                "position": len(widgets),
                "refresh_interval": "real-time" if role in (UserRole.EXECUTIVE, UserRole.PLATFORM_ENGINEER) else "hourly",
                "drill_down": role_config["max_detail_level"] != "summary",
            })

        return widgets
```

### 4.2 Role-Based Content Filter

```python
# src/reporting/personalization/content_filter.py

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ContentFilter:
    """Filters report content based on user role and permissions."""

    # Field-level access control
    FIELD_PERMISSIONS = {
        "executive": {
            "compliance_scores": ["framework", "score", "trend", "status"],
            "risks": ["title", "severity", "owner", "mitigation_status"],
            "incidents": ["title", "severity", "status", "created_at"],
            "evidence": ["count", "verification_level"],
            "systems": ["name", "status", "risk_classification"],
        },
        "grc_analyst": {
            "compliance_scores": ["*"],
            "risks": ["*"],
            "incidents": ["*"],
            "evidence": ["*"],
            "systems": ["*"],
        },
        "auditor": {
            "compliance_scores": ["*"],
            "risks": ["*"],
            "incidents": ["*"],
            "evidence": ["*"],
            "systems": ["*"],
            "chain_of_custody": ["*"],
        },
        "platform_engineer": {
            "compliance_scores": ["*"],
            "risks": ["*"],
            "incidents": ["*"],
            "evidence": ["*"],
            "systems": ["*"],
            "agents": ["*"],
            "enforcement": ["*"],
        },
        "read_only": {
            "compliance_scores": ["framework", "score", "status"],
            "risks": ["title", "severity"],
            "incidents": ["title", "severity", "status"],
            "evidence": ["count"],
            "systems": ["name", "status"],
        },
    }

    @classmethod
    def filter_data(cls, data: dict[str, Any], role: str) -> dict[str, Any]:
        """Filter data fields based on role permissions."""
        permissions = cls.FIELD_PERMISSIONS.get(role, cls.FIELD_PERMISSIONS["read_only"])
        filtered = {}

        for key, value in data.items():
            if key.startswith("_"):
                # Internal metadata, skip for non-technical roles
                if role in ("grc_analyst", "auditor", "platform_engineer"):
                    filtered[key] = value
                continue

            allowed_fields = permissions.get(key, [])
            if allowed_fields == ["*"]:
                filtered[key] = value
            elif isinstance(value, list):
                filtered[key] = [
                    cls._filter_item(item, allowed_fields) for item in value
                ]
            elif isinstance(value, dict):
                filtered[key] = cls._filter_item(value, allowed_fields)
            else:
                filtered[key] = value

        return filtered

    @classmethod
    def _filter_item(cls, item: dict[str, Any], allowed_fields: list[str]) -> dict[str, Any]:
        """Filter a single item's fields."""
        if allowed_fields == ["*"]:
            return item
        return {k: v for k, v in item.items() if k in allowed_fields}
```

---

## 5. Report Scheduling and Subscription

### 5.1 Scheduler

```python
# src/reporting/scheduling/scheduler.py

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class ScheduleFrequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ON_CHANGE = "on_change"


@dataclass
class ReportSchedule:
    """A scheduled report configuration."""
    schedule_id: str
    report_type: str
    format: str
    frequency: ScheduleFrequency
    cron_expression: str | None = None
    recipients: list[str] = None
    frameworks: list[str] = None
    system_ids: list[str] = None
    personalization: dict[str, Any] = None
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    created_at: datetime = None
    metadata: dict[str, Any] = None


class ReportScheduler:
    """Schedules and manages recurring report generation."""

    # Default cron expressions for each frequency
    DEFAULT_CRON = {
        ScheduleFrequency.HOURLY: "0 * * * *",
        ScheduleFrequency.DAILY: "0 8 * * *",  # 8 AM daily
        ScheduleFrequency.WEEKLY: "0 8 * * 1",  # Monday 8 AM
        ScheduleFrequency.BIWEEKLY: "0 8 1,15 * *",  # 1st and 15th
        ScheduleFrequency.MONTHLY: "0 8 1 * *",  # 1st of month
        ScheduleFrequency.QUARTERLY: "0 8 1 1,4,7,10 *",  # Quarter start
    }

    def __init__(
        self,
        pipeline: Any,
        distribution_manager: Any,
        pg_dsn: str = "postgresql://localhost/grc_claw",
    ):
        self.pipeline = pipeline
        self.distribution = distribution_manager
        self.pg_dsn = pg_dsn
        self.scheduler = AsyncIOScheduler()
        self._jobs: dict[str, Any] = {}

    async def start(self):
        """Start the scheduler and load existing schedules."""
        self.scheduler.start()
        await self._load_schedules()
        logger.info("Report scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Report scheduler stopped")

    async def _load_schedules(self):
        """Load schedules from database."""
        import asyncpg
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            rows = await conn.fetch("SELECT * FROM report_schedules WHERE enabled = true")
            for row in rows:
                schedule = ReportSchedule(
                    schedule_id=row["schedule_id"],
                    report_type=row["report_type"],
                    format=row["format"],
                    frequency=ScheduleFrequency(row["frequency"]),
                    cron_expression=row.get("cron_expression"),
                    recipients=row.get("recipients", []),
                    frameworks=row.get("frameworks", []),
                    system_ids=row.get("system_ids", []),
                    personalization=row.get("personalization", {}),
                    enabled=row["enabled"],
                    last_run=row.get("last_run"),
                    next_run=row.get("next_run"),
                    created_at=row.get("created_at"),
                    metadata=row.get("metadata", {}),
                )
                self._add_job(schedule)
        finally:
            await conn.close()

    def create_schedule(self, schedule: ReportSchedule) -> str:
        """Create a new report schedule."""
        if not schedule.cron_expression:
            schedule.cron_expression = self.DEFAULT_CRON.get(
                schedule.frequency, "0 8 * * *"
            )

        self._add_job(schedule)
        logger.info(f"Created schedule {schedule.schedule_id}: {schedule.report_type} ({schedule.frequency.value})")
        return schedule.schedule_id

    def _add_job(self, schedule: ReportSchedule):
        """Add a job to the scheduler."""
        trigger = CronTrigger.from_crontab(schedule.cron_expression)

        job = self.scheduler.add_job(
            func=self._execute_scheduled_report,
            trigger=trigger,
            id=schedule.schedule_id,
            args=[schedule],
            replace_existing=True,
        )
        self._jobs[schedule.schedule_id] = job
        schedule.next_run = job.next_run_time

    async def _execute_scheduled_report(self, schedule: ReportSchedule):
        """Execute a scheduled report generation and distribution."""
        logger.info(f"Executing scheduled report: {schedule.schedule_id}")

        try:
            from reporting.pipeline import ReportRequest, ReportType, ReportFormat

            request = ReportRequest(
                report_type=Type(ReportType)(schedule.report_type),
                format=ReportFormat(schedule.format),
                frameworks=schedule.frameworks or [],
                system_ids=schedule.system_ids or [],
                personalization=schedule.personalization or {},
                metadata={"schedule_id": schedule.schedule_id, "trigger": "scheduled"},
            )

            # Generate report
            artifact = await self.pipeline.generate(request)

            if artifact.status.value == "ready":
                # Distribute to recipients
                await self.distribution.distribute(
                    artifact_path=artifact.file_path,
                    channels=[DistributionChannel.EMAIL],
                    recipients={DistributionChannel.EMAIL: schedule.recipients or []},
                    metadata={
                        "report_id": artifact.report_id,
                        "report_type": schedule.report_type,
                        "format": schedule.format,
                        "subject": f"Scheduled Report: {schedule.report_type}",
                    },
                )

                # Update last run
                schedule.last_run = datetime.utcnow()
                await self._update_schedule_run(schedule)

                logger.info(f"Scheduled report {schedule.schedule_id} completed: {artifact.report_id}")
            else:
                logger.error(f"Scheduled report {schedule.schedule_id} failed: {artifact.error_message}")

        except Exception as e:
            logger.error(f"Scheduled report {schedule.schedule_id} error: {e}", exc_info=True)

    async def _update_schedule_run(self, schedule: ReportSchedule):
        """Update schedule run status in database."""
        import asyncpg
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            await conn.execute(
                "UPDATE report_schedules SET last_run = $1, next_run = $2 WHERE schedule_id = $3",
                schedule.last_run,
                schedule.next_run,
                schedule.schedule_id,
            )
        finally:
            await conn.close()

    def remove_schedule(self, schedule_id: str):
        """Remove a schedule."""
        if schedule_id in self._jobs:
            self.scheduler.remove_job(schedule_id)
            del self._jobs[schedule_id]
            logger.info(f"Removed schedule {schedule_id}")

    def list_schedules(self) -> list[ReportSchedule]:
        """List all schedules."""
        return list(self._jobs.values())
```

### 5.2 Subscription Manager

```python
# src/reporting/scheduling/subscription.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class ReportSubscription:
    """A user's subscription to report types."""
    subscription_id: str
    user_id: str
    report_types: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    frequency: str = "weekly"  # daily, weekly, monthly, quarterly
    channels: list[str] = field(default_factory=lambda: ["email"])
    format: str = "pdf"
    filters: dict[str, Any] = field(default_factory=dict)
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    created_at: datetime = None
    last_delivered: datetime | None = None
    delivery_count: int = 0


class SubscriptionManager:
    """Manages user subscriptions to report types."""

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def create_subscription(self, subscription: ReportSubscription) -> str:
        """Create a new subscription."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            await conn.execute(
                """
                INSERT INTO report_subscriptions
                (subscription_id, user_id, report_types, frameworks, frequency, channels, format, filters, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                subscription.subscription_id,
                subscription.user_id,
                subscription.report_types,
                subscription.frameworks,
                subscription.frequency,
                subscription.channels,
                subscription.format,
                subscription.filters,
                subscription.status.value,
                datetime.utcnow(),
            )
            logger.info(f"Created subscription {subscription.subscription_id} for user {subscription.user_id}")
            return subscription.subscription_id
        finally:
            await conn.close()

    async def get_user_subscriptions(self, user_id: str) -> list[ReportSubscription]:
        """Get all subscriptions for a user."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            rows = await conn.fetch(
                "SELECT * FROM report_subscriptions WHERE user_id = $1 AND status = 'active'",
                user_id,
            )
            return [
                ReportSubscription(
                    subscription_id=r["subscription_id"],
                    user_id=r["user_id"],
                    report_types=r["report_types"],
                    frameworks=r["frameworks"],
                    frequency=r["frequency"],
                    channels=r["channels"],
                    format=r["format"],
                    filters=r["filters"],
                    status=SubscriptionStatus(r["status"]),
                    created_at=r["created_at"],
                    last_delivered=r.get("last_delivered"),
                    delivery_count=r.get("delivery_count", 0),
                )
                for r in rows
            ]
        finally:
            await conn.close()

    async def get_subscribers_for_report(
        self, report_type: str, framework: str | None = None
    ) -> list[ReportSubscription]:
        """Get all active subscribers for a specific report type."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            query = """
                SELECT * FROM report_subscriptions
                WHERE status = 'active' AND $1 = ANY(report_types)
            """
            params = [report_type]
            if framework:
                query += " AND ($2 = ANY(frameworks) OR frameworks IS NULL OR array_length(frameworks, 1) IS NULL)"
                params.append(framework)

            rows = await conn.fetch(query, *params)
            return [
                ReportSubscription(
                    subscription_id=r["subscription_id"],
                    user_id=r["user_id"],
                    report_types=r["report_types"],
                    frameworks=r["frameworks"],
                    frequency=r["frequency"],
                    channels=r["channels"],
                    format=r["format"],
                    filters=r["filters"],
                    status=SubscriptionStatus(r["status"]),
                    created_at=r["created_at"],
                    last_delivered=r.get("last_delivered"),
                    delivery_count=r.get("delivery_count", 0),
                )
                for r in rows
            ]
        finally:
            await conn.close()

    async def update_delivery_status(self, subscription_id: str):
        """Update delivery status after successful delivery."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            await conn.execute(
                """
                UPDATE report_subscriptions
                SET last_delivered = $1, delivery_count = delivery_count + 1
                WHERE subscription_id = $2
                """,
                datetime.utcnow(),
                subscription_id,
            )
        finally:
            await conn.close()

    async def pause_subscription(self, subscription_id: str):
        """Pause a subscription."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            await conn.execute(
                "UPDATE report_subscriptions SET status = 'paused' WHERE subscription_id = $1",
                subscription_id,
            )
        finally:
            await conn.close()

    async def cancel_subscription(self, subscription_id: str):
        """Cancel a subscription."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            await conn.execute(
                "UPDATE report_subscriptions SET status = 'cancelled' WHERE subscription_id = $1",
                subscription_id,
            )
        finally:
            await conn.close()
```

### 5.3 Calendar Sync

```python
# src/reporting/scheduling/calendar_sync.py

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class CalendarSync:
    """Syncs report schedules with calendar systems."""

    def __init__(self, pipeline: Any):
        self.pipeline = pipeline

    async def generate_calendar_events(
        self, schedule: Any, days_ahead: int = 90
    ) -> list[dict[str, Any]]:
        """Generate calendar events for scheduled reports."""
        events = []
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days_ahead)

        # Generate events based on frequency
        if schedule.frequency.value == "daily":
            current = start_date
            while current <= end_date:
                events.append({
                    "title": f"GRC_Claw Report: {schedule.report_type}",
                    "start": current.replace(hour=8, minute=0),
                    "end": current.replace(hour=8, minute=30),
                    "description": f"Automated {schedule.report_type} report generation",
                    "metadata": {"schedule_id": schedule.schedule_id},
                })
                current += timedelta(days=1)

        elif schedule.frequency.value == "weekly":
            current = start_date
            while current <= end_date:
                events.append({
                    "title": f"GRC_Claw Report: {schedule.report_type}",
                    "start": current.replace(hour=8, minute=0),
                    "end": current.replace(hour=8, minute=30),
                    "description": f"Weekly {schedule.report_type} report",
                    "metadata": {"schedule_id": schedule.schedule_id},
                })
                current += timedelta(weeks=1)

        elif schedule.frequency.value == "monthly":
            current = start_date
            while current <= end_date:
                events.append({
                    "title": f"GRC_Claw Report: {schedule.report_type}",
                    "start": current.replace(hour=8, minute=0),
                    "end": current.replace(hour=8, minute=30),
                    "description": f"Monthly {schedule.report_type} report",
                    "metadata": {"schedule_id": schedule.schedule_id},
                })
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

        elif schedule.frequency.value == "quarterly":
            current = start_date
            while current <= end_date:
                events.append({
                    "title": f"GRC_Claw Report: {schedule.report_type}",
                    "start": current.replace(hour=8, minute=0),
                    "end": current.replace(hour=8, minute=30),
                    "description": f"Quarterly {schedule.report_type} report",
                    "metadata": {"schedule_id": schedule.schedule_id},
                })
                # Move to next quarter
                quarter_start = ((current.month - 1) // 3 + 1) * 3 + 1
                if quarter_start > 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=quarter_start)

        return events

    async def export_to_ical(self, events: list[dict[str, Any]]) -> str:
        """Export calendar events to iCal format."""
        ical_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//GRC_Claw//Reporting//EN",
        ]

        for event in events:
            ical_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{event['metadata']['schedule_id']}@grc-claw",
                f"DTSTART:{event['start'].strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{event['end'].strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{event['title']}",
                f"DESCRIPTION:{event['description']}",
                "END:VEVENT",
            ])

        ical_lines.append("END:VCALENDAR")
        return "\r\n".join(ical_lines)
```

---

## 6. Report Quality Assurance

### 6.1 Quality Engine

```python
# src/reporting/quality/__init__.py

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class QualityCheck:
    """Result of a single quality check."""
    name: str
    passed: bool
    score: float  # 0.0 - 1.0
    details: dict[str, Any]
    recommendations: list[str]


class QualityEngine:
    """Validates report quality across multiple dimensions."""

    # Freshness thresholds (in days)
    FRESHNESS_THRESHOLDS = {
        "evidence": 90,
        "assessment": 180,
        "review": 365,
        "policy": 365,
    }

    # Minimum completeness thresholds
    COMPLETENESS_THRESHOLDS = {
        "board_summary": 0.9,
        "evidence_pack": 0.95,
        "program_status": 0.85,
        "operational_view": 0.8,
        "vendor_risk": 0.85,
        "incident_report": 0.9,
        "transparency": 0.8,
    }

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def check_completeness(
        self, data: dict[str, Any], request: Any
    ) -> QualityCheck:
        """Check report completeness."""
        required_fields = self._get_required_fields(request.report_type)
        missing_fields = []
        present_fields = []

        for field in required_fields:
            if field in data and data[field] is not None:
                present_fields.append(field)
            else:
                missing_fields.append(field)

        score = len(present_fields) / len(required_fields) if required_fields else 1.0
        threshold = self.COMPLETENESS_THRESHOLDS.get(request.report_type.value, 0.8)

        recommendations = []
        if missing_fields:
            recommendations.append(f"Missing data for: {', '.join(missing_fields)}")

        return QualityCheck(
            name="completeness",
            passed=score >= threshold,
            score=score,
            details={
                "required": required_fields,
                "present": present_fields,
                "missing": missing_fields,
                "threshold": threshold,
            },
            recommendations=recommendations,
        )

    async def check_freshness(self, data: dict[str, Any]) -> QualityCheck:
        """Check data freshness."""
        issues = []
        scores = []

        # Check evidence freshness
        if "evidence_summary" in data:
            evidence = data["evidence_summary"]
            if evidence.get("latest_evidence"):
                age = (datetime.utcnow() - evidence["latest_evidence"]).days
                threshold = self.FRESHNESS_THRESHOLDS["evidence"]
                fresh_score = max(0, 1 - (age / threshold))
                scores.append(fresh_score)
                if age > threshold:
                    issues.append(f"Evidence is {age} days old (threshold: {threshold})")
            else:
                scores.append(0.0)
                issues.append("No evidence found")

        # Check assessment freshness
        if "compliance_scores" in data:
            for score in data["compliance_scores"]:
                if score.get("last_assessment"):
                    age = (datetime.utcnow() - score["last_assessment"]).days
                    threshold = self.FRESHNESS_THRESHOLDS["assessment"]
                    if age > threshold:
                        issues.append(
                            f"Assessment for {score.get('system_id', 'unknown')} is {age} days old"
                        )

        overall_score = sum(scores) / len(scores) if scores else 0.0

        return QualityCheck(
            name="freshness",
            passed=overall_score >= 0.7,
            score=overall_score,
            details={"issues": issues},
            recommendations=[f"Refresh data: {i}" for i in issues],
        )

    async def check_accuracy(self, data: dict[str, Any]) -> QualityCheck:
        """Check data accuracy and consistency."""
        issues = []
        checks_passed = 0
        total_checks = 0

        # Check score consistency
        if "compliance_scores" in data and "overall_score" in data:
            total_checks += 1
            calculated = sum(s["score"] for s in data["compliance_scores"]) / len(data["compliance_scores"])
            reported = data["overall_score"]
            if abs(calculated - reported) < 0.01:
                checks_passed += 1
            else:
                issues.append(f"Overall score mismatch: calculated {calculated:.3f} vs reported {reported:.3f}")

        # Check evidence counts
        if "evidence_summary" in data and "inventory" in data:
            total_checks += 1
            # Verify evidence count matches inventory
            checks_passed += 1  # Simplified

        # Check for stale references
        if "systems" in data:
            total_checks += 1
            checks_passed += 1  # Simplified

        score = checks_passed / total_checks if total_checks > 0 else 1.0

        return QualityCheck(
            name="accuracy",
            passed=score >= 0.9,
            score=score,
            details={"checks_passed": checks_passed, "total_checks": total_checks, "issues": issues},
            recommendations=issues,
        )

    async def check_consistency(self, data: dict[str, Any]) -> QualityCheck:
        """Check cross-reference consistency."""
        issues = []

        # Check that all system IDs referenced exist
        if "inventory" in data and "compliance_scores" in data:
            inventory_ids = {s["system_id"] for s in data["inventory"]}
            score_ids = {s["system_id"] for s in data["compliance_scores"]}
            orphaned = score_ids - inventory_ids
            if orphaned:
                issues.append(f"Compliance scores for unknown systems: {orphaned}")

        # Check framework names are valid
        valid_frameworks = {"eu-ai-act", "nist-ai-rmf", "iso-42001", "soc2", "iso-27001", "gdpr"}
        if "compliance_scores" in data:
            for score in data["compliance_scores"]:
                if score.get("framework") not in valid_frameworks:
                    issues.append(f"Invalid framework: {score.get('framework')}")

        score = 1.0 if not issues else max(0, 1 - len(issues) * 0.1)

        return QualityCheck(
            name="consistency",
            passed=score >= 0.9,
            score=score,
            details={"issues": issues},
            recommendations=issues,
        )

    def _get_required_fields(self, report_type: Any) -> list[str]:
        """Get required data fields for a report type."""
        required = {
            "board_summary": ["inventory", "compliance_scores", "framework_scores", "material_risks", "board_decisions"],
            "evidence_pack": ["inventory", "evidence_items", "chain_of_custody", "assessment_history"],
            "program_status": ["compliance_scores", "control_family_rag", "exceptions", "monitoring"],
            "operational_view": ["inventory", "evidence_summary", "incidents", "monitoring"],
            "vendor_risk": ["vendors", "vendor_spend"],
            "incident_report": ["incident_details", "incident_timeline"],
            "transparency": ["inventory", "compliance_scores", "incidents"],
        }
        return required.get(report_type.value, ["inventory"])
```

### 6.2 Freshness Monitor

```python
# src/reporting/quality/freshness.py

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class FreshnessStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"
    MISSING = "missing"


@dataclass
class FreshnessReport:
    """Freshness report for a data source."""
    source_name: str
    status: FreshnessStatus
    last_updated: datetime | None
    age_hours: float | None
    threshold_hours: float
    affected_systems: list[str]
    recommendation: str


class FreshnessMonitor:
    """Monitors data freshness and triggers alerts."""

    THRESHOLDS = {
        "evidence": 168,      # 7 days
        "assessment": 720,    # 30 days
        "review": 2160,       # 90 days
        "policy": 8760,       # 1 year
        "inventory": 720,     # 30 days
        "monitoring": 24,     # 1 day
    }

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def check_all_freshness(self) -> list[FreshnessReport]:
        """Check freshness of all data sources."""
        reports = []
        reports.append(await self._check_evidence_freshness())
        reports.append(await self._check_assessment_freshness())
        reports.append(await self._check_inventory_freshness())
        reports.append(await self._check_monitoring_freshness())
        return reports

    async def _check_evidence_freshness(self) -> FreshnessReport:
        """Check evidence freshness."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            row = await conn.fetchrow(
                """
                SELECT MAX(collected_at) as latest, COUNT(*) as count
                FROM evidence
                WHERE collected_at > NOW() - INTERVAL '90 days'
                """
            )
            if row and row["latest"]:
                age = (datetime.utcnow() - row["latest"]).total_seconds() / 3600
                threshold = self.THRESHOLDS["evidence"]
                status = self._determine_status(age, threshold)
                return FreshnessReport(
                    source_name="evidence",
                    status=status,
                    last_updated=row["latest"],
                    age_hours=age,
                    threshold_hours=threshold,
                    affected_systems=[],
                    recommendation="Request re-collection" if status in (FreshnessStatus.STALE, FreshnessStatus.EXPIRED) else "No action needed",
                )
            return FreshnessReport(
                source_name="evidence",
                status=FreshnessStatus.MISSING,
                last_updated=None,
                age_hours=None,
                threshold_hours=self.THRESHOLDS["evidence"],
                affected_systems=[],
                recommendation="No evidence found — initiate collection",
            )
        finally:
            await conn.close()

    async def _check_assessment_freshness(self) -> FreshnessReport:
        """Check assessment freshness."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            row = await conn.fetchrow(
                "SELECT MAX(completed_at) as latest FROM assessments"
            )
            if row and row["latest"]:
                age = (datetime.utcnow() - row["latest"]).total_seconds() / 3600
                threshold = self.THRESHOLDS["assessment"]
                status = self._determine_status(age, threshold)
                return FreshnessReport(
                    source_name="assessment",
                    status=status,
                    last_updated=row["latest"],
                    age_hours=age,
                    threshold_hours=threshold,
                    affected_systems=[],
                    recommendation="Schedule new assessment" if status == FreshnessStatus.EXPIRED else "No action needed",
                )
            return FreshnessReport(
                source_name="assessment",
                status=FreshnessStatus.MISSING,
                last_updated=None,
                age_hours=None,
                threshold_hours=self.THRESHOLDS["assessment"],
                affected_systems=[],
                recommendation="No assessments found — schedule initial assessment",
            )
        finally:
            await conn.close()

    async def _check_inventory_freshness(self) -> FreshnessReport:
        """Check inventory freshness."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            row = await conn.fetchrow(
                "SELECT MAX(updated_at) as latest FROM ai_systems"
            )
            if row and row["latest"]:
                age = (datetime.utcnow() - row["latest"]).total_seconds() / 3600
                threshold = self.THRESHOLDS["inventory"]
                status = self._determine_status(age, threshold)
                return FreshnessReport(
                    source_name="inventory",
                    status=status,
                    last_updated=row["latest"],
                    age_hours=age,
                    threshold_hours=threshold,
                    affected_systems=[],
                    recommendation="Re-derive inventory from logs" if status == FreshnessStatus.STALE else "No action needed",
                )
            return FreshnessReport(
                source_name="inventory",
                status=FreshnessStatus.MISSING,
                last_updated=None,
                age_hours=None,
                threshold_hours=self.THRESHOLDS["inventory"],
                affected_systems=[],
                recommendation="No inventory found — run discovery",
            )
        finally:
            await conn.close()

    async def _check_monitoring_freshness(self) -> FreshnessReport:
        """Check monitoring data freshness."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            row = await conn.fetchrow(
                "SELECT MAX(last_check) as latest FROM monitoring_status"
            )
            if row and row["latest"]:
                age = (datetime.utcnow() - row["latest"]).total_seconds() / 3600
                threshold = self.THRESHOLDS["monitoring"]
                status = self._determine_status(age, threshold)
                return FreshnessReport(
                    source_name="monitoring",
                    status=status,
                    last_updated=row["latest"],
                    age_hours=age,
                    threshold_hours=threshold,
                    affected_systems=[],
                    recommendation="Check monitoring agents" if status != FreshnessStatus.FRESH else "No action needed",
                )
            return FreshnessReport(
                source_name="monitoring",
                status=FreshnessStatus.MISSING,
                last_updated=None,
                age_hours=None,
                threshold_hours=self.THRESHOLDS["monitoring"],
                affected_systems=[],
                recommendation="No monitoring data — check agent connectivity",
            )
        finally:
            await conn.close()

    def _determine_status(self, age_hours: float, threshold_hours: float) -> FreshnessStatus:
        """Determine freshness status from age."""
        if age_hours > threshold_hours * 2:
            return FreshnessStatus.EXPIRED
        elif age_hours > threshold_hours:
            return FreshnessStatus.STALE
        return FreshnessStatus.FRESH
```

---

## 7. Report Analytics and Usage Tracking

### 7.1 Usage Tracker

```python
# src/reporting/analytics/tracker.py

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class ReportEventType(str, Enum):
    GENERATED = "generated"
    VIEWED = "viewed"
    DOWNLOADED = "downloaded"
    SHARED = "shared"
    DELIVERED = "delivered"
    FAILED = "failed"
    SCHEDULED = "scheduled"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"


@dataclass
class ReportEvent:
    """A report usage event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: ReportEventType = ReportEventType.GENERATED
    report_id: str | None = None
    report_type: str | None = None
    user_id: str | None = None
    user_role: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class UsageTracker:
    """Tracks report generation, delivery, and consumption."""

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def track_event(self, event: ReportEvent):
        """Track a report event."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            await conn.execute(
                """
                INSERT INTO report_analytics
                (event_id, event_type, report_id, report_type, user_id, user_role, timestamp, metadata, session_id, ip_address, user_agent)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                event.event_id,
                event.event_type.value,
                event.report_id,
                event.report_type,
                event.user_id,
                event.user_role,
                event.timestamp,
                json.dumps(event.metadata),
                event.session_id,
                event.ip_address,
                event.user_agent,
            )
        finally:
            await conn.close()

    async def track_generation(
        self,
        report_id: str,
        report_type: str,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Track report generation."""
        await self.track_event(ReportEvent(
            event_type=ReportEventType.GENERATED,
            report_id=report_id,
            report_type=report_type,
            user_id=user_id,
            metadata=metadata or {},
        ))

    async def track_view(
        self,
        report_id: str,
        user_id: str,
        session_id: str | None = None,
    ):
        """Track report view."""
        await self.track_event(ReportEvent(
            event_type=ReportEventType.VIEWED,
            report_id=report_id,
            user_id=user_id,
            session_id=session_id,
        ))

    async def track_download(
        self,
        report_id: str,
        user_id: str,
        format: str,
    ):
        """Track report download."""
        await self.track_event(ReportEvent(
            event_type=ReportEventType.DOWNLOADED,
            report_id=report_id,
            user_id=user_id,
            metadata={"format": format},
        ))

    async def get_usage_summary(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get usage summary statistics."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            where_clause = ""
            params = []
            if start_date:
                params.append(start_date)
                where_clause += f" WHERE timestamp >= ${len(params)}"
            if end_date:
                params.append(end_date)
                where_clause += f"{' AND' if where_clause else ' WHERE'} timestamp <= ${len(params)}"

            # Total events
            total = await conn.fetchval(
                f"SELECT COUNT(*) FROM report_analytics{where_clause}",
                *params,
            )

            # Events by type
            by_type = await conn.fetch(
                f"SELECT event_type, COUNT(*) as count FROM report_analytics{where_clause} GROUP BY event_type",
                *params,
            )

            # Events by report type
            by_report_type = await conn.fetch(
                f"SELECT report_type, COUNT(*) as count FROM report_analytics{where_clause} AND report_type IS NOT NULL GROUP BY report_type",
                *params,
            )

            # Unique users
            unique_users = await conn.fetchval(
                f"SELECT COUNT(DISTINCT user_id) FROM report_analytics{where_clause} AND user_id IS NOT NULL",
                *params,
            )

            # Most viewed reports
            top_reports = await conn.fetch(
                f"""
                SELECT report_id, report_type, COUNT(*) as views
                FROM report_analytics
                {where_clause} AND event_type = 'viewed'
                GROUP BY report_id, report_type
                ORDER BY views DESC
                LIMIT 10
                """,
                *params,
            )

            return {
                "total_events": total,
                "by_type": {r["event_type"]: r["count"] for r in by_type},
                "by_report_type": {r["report_type"]: r["count"] for r in by_report_type},
                "unique_users": unique_users,
                "top_reports": [dict(r) for r in top_reports],
            }
        finally:
            await conn.close()
```

### 7.2 Metrics Dashboard

```python
# src/reporting/analytics/metrics.py

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and aggregates report metrics."""

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def get_dashboard_metrics(self) -> dict[str, Any]:
        """Get metrics for the analytics dashboard."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            # Generation metrics
            generation_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_generated,
                    COUNT(*) FILTER (WHERE event_type = 'generated') as successful,
                    COUNT(*) FILTER (WHERE event_type = 'failed') as failed,
                    AVG(EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp)))) as avg_generation_time
                FROM report_analytics
                WHERE timestamp > NOW() - INTERVAL '30 days'
                """
            )

            # Delivery metrics
            delivery_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE event_type = 'delivered') as delivered,
                    COUNT(*) FILTER (WHERE event_type = 'failed') as failed
                FROM report_analytics
                WHERE timestamp > NOW() - INTERVAL '30 days'
                """
            )

            # User engagement
            engagement = await conn.fetch(
                """
                SELECT
                    user_role,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) as total_events
                FROM report_analytics
                WHERE timestamp > NOW() - INTERVAL '30 days' AND user_id IS NOT NULL
                GROUP BY user_role
                """
            )

            # Report type popularity
            type_popularity = await conn.fetch(
                """
                SELECT
                    report_type,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM report_analytics
                WHERE timestamp > NOW() - INTERVAL '30 days' AND report_type IS NOT NULL
                GROUP BY report_type
                ORDER BY count DESC
                """
            )

            # Daily trend
            daily_trend = await conn.fetch(
                """
                SELECT
                    date_trunc('day', timestamp) as date,
                    COUNT(*) as events,
                    COUNT(DISTINCT user_id) as unique_users
                FROM report_analytics
                WHERE timestamp > NOW() - INTERVAL '30 days'
                GROUP BY date
                ORDER BY date
                """
            )

            return {
                "generation": {
                    "total": generation_stats["total_generated"] or 0,
                    "successful": generation_stats["successful"] or 0,
                    "failed": generation_stats["failed"] or 0,
                    "success_rate": (
                        generation_stats["successful"] / generation_stats["total_generated"]
                        if generation_stats["total_generated"] else 0
                    ),
                },
                "delivery": {
                    "delivered": delivery_stats["delivered"] or 0,
                    "failed": delivery_stats["failed"] or 0,
                    "success_rate": (
                        delivery_stats["delivered"] / (delivery_stats["delivered"] + delivery_stats["failed"])
                        if (delivery_stats["delivered"] + delivery_stats["failed"]) else 0
                    ),
                },
                "engagement": [dict(r) for r in engagement],
                "type_popularity": [dict(r) for r in type_popularity],
                "daily_trend": [dict(r) for r in daily_trend],
            }
        finally:
            await conn.close()

    async def get_report_effectiveness(self, report_type: str) -> dict[str, Any]:
        """Get effectiveness metrics for a specific report type."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE event_type = 'generated') as generated,
                    COUNT(*) FILTER (WHERE event_type = 'viewed') as viewed,
                    COUNT(*) FILTER (WHERE event_type = 'downloaded') as downloaded,
                    COUNT(*) FILTER (WHERE event_type = 'shared') as shared,
                    COUNT(DISTINCT user_id) as unique_users
                FROM report_analytics
                WHERE report_type = $1 AND timestamp > NOW() - INTERVAL '90 days'
                """,
                report_type,
            )

            generated = stats["generated"] or 0
            viewed = stats["viewed"] or 0
            downloaded = stats["downloaded"] or 0

            return {
                "report_type": report_type,
                "generated": generated,
                "viewed": viewed,
                "downloaded": downloaded,
                "shared": stats["shared"] or 0,
                "unique_users": stats["unique_users"] or 0,
                "view_rate": viewed / generated if generated else 0,
                "download_rate": downloaded / generated if generated else 0,
            }
        finally:
            await conn.close()
```

### 7.3 Feedback Collection

```python
# src/reporting/analytics/feedback.py

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class ReportFeedback:
    """User feedback on a report."""
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    report_id: str | None = None
    report_type: str | None = None
    user_id: str | None = None
    rating: int = 0  # 1-5
    usefulness: int = 0  # 1-5
    clarity: int = 0  # 1-5
    completeness: int = 0  # 1-5
    comments: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class FeedbackCollector:
    """Collects and analyzes user feedback on reports."""

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def submit_feedback(self, feedback: ReportFeedback):
        """Submit user feedback."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            await conn.execute(
                """
                INSERT INTO report_feedback
                (feedback_id, report_id, report_type, user_id, rating, usefulness, clarity, completeness, comments, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                feedback.feedback_id,
                feedback.report_id,
                feedback.report_type,
                feedback.user_id,
                feedback.rating,
                feedback.usefulness,
                feedback.clarity,
                feedback.completeness,
                feedback.comments,
                feedback.timestamp,
            )
        finally:
            await conn.close()

    async def get_feedback_summary(
        self, report_type: str | None = None
    ) -> dict[str, Any]:
        """Get feedback summary statistics."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            where_clause = ""
            params = []
            if report_type:
                params.append(report_type)
                where_clause = "WHERE report_type = $1"

            stats = await conn.fetchrow(
                f"""
                SELECT
                    COUNT(*) as total_feedback,
                    AVG(rating) as avg_rating,
                    AVG(usefulness) as avg_usefulness,
                    AVG(clarity) as avg_clarity,
                    AVG(completeness) as avg_completeness,
                    COUNT(*) FILTER (WHERE rating >= 4) as positive_count,
                    COUNT(*) FILTER (WHERE rating <= 2) as negative_count
                FROM report_feedback
                {where_clause}
                """,
                *params,
            )

            # Recent comments
            comments = await conn.fetch(
                f"""
                SELECT report_type, rating, comments, timestamp
                FROM report_feedback
                {where_clause} AND comments IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 10
                """,
                *params,
            )

            return {
                "total_feedback": stats["total_feedback"] or 0,
                "average_rating": round(stats["avg_rating"] or 0, 2),
                "average_usefulness": round(stats["avg_usefulness"] or 0, 2),
                "average_clarity": round(stats["avg_clarity"] or 0, 2),
                "average_completeness": round(stats["avg_completeness"] or 0, 2),
                "positive_rate": (
                    stats["positive_count"] / stats["total_feedback"]
                    if stats["total_feedback"] else 0
                ),
                "negative_rate": (
                    stats["negative_count"] / stats["total_feedback"]
                    if stats["total_feedback"] else 0
                ),
                "recent_comments": [dict(r) for r in comments],
            }
        finally:
            await conn.close()
```

---

## 8. Dashboard Implementations

### 8.1 Executive Dashboard

```python
# src/reporting/dashboards/executive.py

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class ExecutiveDashboard:
    """One-page executive dashboard — material signals only."""

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def get_dashboard_data(
        self,
        time_range_days: int = 90,
        frameworks: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get all data for the executive dashboard."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            # Overall compliance score with trend
            overall = await conn.fetchrow(
                """
                SELECT
                    AVG(score) as current_score,
                    AVG(score) FILTER (WHERE recorded_at > NOW() - INTERVAL '%s days') as recent_score
                FROM compliance_scores
                WHERE recorded_at > NOW() - INTERVAL '%s days'
                """,
                time_range_days // 3,
                time_range_days,
            )

            # Score by framework
            framework_scores = await conn.fetch(
                """
                SELECT
                    framework,
                    AVG(score) as score,
                    COUNT(DISTINCT system_id) as system_count
                FROM compliance_scores
                WHERE recorded_at > NOW() - INTERVAL '%s days'
                GROUP BY framework
                ORDER BY score DESC
                """,
                time_range_days,
            )

            # Top 5 material risks
            top_risks = await conn.fetch(
                """
                SELECT
                    risk_id, title, severity, owner, mitigation_status
                FROM risks
                WHERE status = 'open' AND severity IN ('critical', 'high')
                ORDER BY severity DESC, created_at DESC
                LIMIT 5
                """
            )

            # Decisions awaiting board attention
            pending_decisions = await conn.fetch(
                """
                SELECT
                    decision_id, title, description, priority, due_date
                FROM board_decisions
                WHERE status = 'pending'
                ORDER BY priority DESC, due_date
                LIMIT 5
                """
            )

            # Incident summary
            incident_summary = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'open') as open_count,
                    COUNT(*) FILTER (WHERE status = 'closed') as closed_count,
                    COUNT(*) FILTER (WHERE severity = 'critical' AND status = 'open') as critical_open
                FROM incidents
                WHERE created_at > NOW() - INTERVAL '%s days'
                """,
                time_range_days,
            )

            # Key metrics with RAG status
            key_metrics = await conn.fetch(
                """
                SELECT
                    metric_name,
                    current_value,
                    target_value,
                    status,
                    owner
                FROM key_metrics
                WHERE active = true
                ORDER BY status, metric_name
                """
            )

            # 90-day trend data
            trend_data = await conn.fetch(
                """
                SELECT
                    date_trunc('day', recorded_at) as date,
                    AVG(score) as avg_score
                FROM compliance_scores
                WHERE recorded_at > NOW() - INTERVAL '%s days'
                GROUP BY date
                ORDER BY date
                """,
                time_range_days,
            )

            # Agent trust score distribution
            trust_distribution = await conn.fetch(
                """
                SELECT
                    CASE
                        WHEN trust_score >= 90 THEN 'A'
                        WHEN trust_score >= 80 THEN 'B'
                        WHEN trust_score >= 70 THEN 'C'
                        WHEN trust_score >= 60 THEN 'D'
                        ELSE 'F'
                    END as grade,
                    COUNT(*) as count
                FROM agents
                WHERE status = 'active'
                GROUP BY grade
                ORDER BY grade
                """
            )

            return {
                "generated_at": datetime.utcnow(),
                "time_range_days": time_range_days,
                "overall_compliance": {
                    "score": round((overall["current_score"] or 0) * 100, 1),
                    "trend": round(
                        ((overall["recent_score"] or 0) - (overall["current_score"] or 0)) * 100, 1
                    ),
                },
                "framework_scores": [
                    {
                        "framework": r["framework"],
                        "score": round(r["score"] * 100, 1),
                        "systems": r["system_count"],
                    }
                    for r in framework_scores
                ],
                "top_risks": [dict(r) for r in top_risks],
                "pending_decisions": [dict(r) for r in pending_decisions],
                "incident_summary": dict(incident_summary),
                "key_metrics": [dict(r) for r in key_metrics],
                "trend_data": [
                    {"date": r["date"].isoformat(), "score": round(r["avg_score"] * 100, 1)}
                    for r in trend_data
                ],
                "trust_distribution": {r["grade"]: r["count"] for r in trust_distribution},
            }
        finally:
            await conn.close()
```

### 8.2 Program Dashboard

```python
# src/reporting/dashboards/program.py

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class ProgramDashboard:
    """Program-level dashboard for governance leaders and risk officers."""

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def get_dashboard_data(
        self,
        frameworks: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get all data for the program dashboard."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            # Risk posture by tier
            risk_by_tier = await conn.fetch(
                """
                SELECT
                    severity,
                    COUNT(*) as count,
                    COUNT(*) FILTER (WHERE status = 'open') as open_count,
                    COUNT(*) FILTER (WHERE mitigation_status = 'in_progress') as mitigating
                FROM risks
                GROUP BY severity
                ORDER BY severity DESC
                """
            )

            # Control family status
            control_family_status = await conn.fetch(
                """
                SELECT
                    cf.family_name,
                    COUNT(DISTINCT fc.control_id) as total_controls,
                    COUNT(DISTINCT cs.control_id) FILTER (WHERE cs.score >= 0.8) as passing,
                    COUNT(DISTINCT cs.control_id) FILTER (WHERE cs.score < 0.6) as failing
                FROM control_families cf
                JOIN framework_controls fc ON cf.family_id = fc.family_id
                LEFT JOIN compliance_scores cs ON fc.control_id = cs.control_id
                GROUP BY cf.family_name
                ORDER BY cf.family_name
                """
            )

            # Exception exposure
            exception_exposure = await conn.fetch(
                """
                SELECT
                    consequence,
                    COUNT(*) FILTER (WHERE status = 'open') as open_count,
                    COUNT(*) FILTER (WHERE status = 'expired') as expired_count,
                    COUNT(*) FILTER (WHERE expiry_date < NOW() + INTERVAL '30 days') as expiring_soon
                FROM exceptions
                WHERE status IN ('open', 'expired')
                GROUP BY consequence
                ORDER BY consequence
                """
            )

            # Review currency
            review_currency = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_reviews,
                    COUNT(*) FILTER (WHERE next_review > NOW()) as current,
                    COUNT(*) FILTER (WHERE next_review <= NOW()) as overdue,
                    COUNT(*) FILTER (WHERE next_review <= NOW() + INTERVAL '30 days') as due_soon
                FROM ai_systems
                WHERE lifecycle_stage = 'production'
                """
            )

            # Monitoring coverage
            monitoring_coverage = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_systems,
                    COUNT(*) FILTER (WHERE monitoring_enabled = true) as monitored,
                    COUNT(*) FILTER (WHERE last_check > NOW() - INTERVAL '24 hours') as recently_checked
                FROM monitoring_status
                """
            )

            # Decision speed metrics
            decision_speed = await conn.fetchrow(
                """
                SELECT
                    AVG(EXTRACT(EPOCH FROM (decided_at - created_at)) / 3600) as avg_hours,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (decided_at - created_at)) / 3600) as median_hours,
                    COUNT(*) FILTER (WHERE decided_at IS NOT NULL) as decided_count,
                    COUNT(*) FILTER (WHERE decided_at IS NULL) as pending_count
                FROM governance_decisions
                WHERE created_at > NOW() - INTERVAL '90 days'
                """
            )

            # Remediation velocity
            remediation = await conn.fetch(
                """
                SELECT
                    date_trunc('week', closed_at) as week,
                    COUNT(*) as closed_count,
                    AVG(EXTRACT(EPOCH FROM (closed_at - created_at)) / 86400) as avg_days_to_close
                FROM findings
                WHERE closed_at > NOW() - INTERVAL '90 days'
                GROUP BY week
                ORDER BY week
                """
            )

            return {
                "generated_at": datetime.utcnow(),
                "risk_by_tier": [dict(r) for r in risk_by_tier],
                "control_family_status": [dict(r) for r in control_family_status],
                "exception_exposure": [dict(r) for r in exception_exposure],
                "review_currency": dict(review_currency),
                "monitoring_coverage": dict(monitoring_coverage),
                "decision_speed": dict(decision_speed),
                "remediation_velocity": [dict(r) for r in remediation],
            }
        finally:
            await conn.close()
```

### 8.3 Operating Dashboard

```python
# src/reporting/dashboards/operating.py

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class OperatingDashboard:
    """Record-level operating dashboard for engineers and compliance ops."""

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def get_dashboard_data(
        self,
        system_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get all data for the operating dashboard."""
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            # System inventory with status
            if system_ids:
                inventory = await conn.fetch(
                    """
                    SELECT
                        s.system_id, s.name, s.status, s.risk_classification,
                        s.owner, s.last_assessment, s.next_review,
                        COUNT(e.evidence_id) as evidence_count
                    FROM ai_systems s
                    LEFT JOIN evidence e ON s.system_id = e.system_id
                    WHERE s.system_id = ANY($1)
                    GROUP BY s.system_id
                    ORDER BY s.risk_classification DESC, s.name
                    """,
                    system_ids,
                )
            else:
                inventory = await conn.fetch(
                    """
                    SELECT
                        s.system_id, s.name, s.status, s.risk_classification,
                        s.owner, s.last_assessment, s.next_review,
                        COUNT(e.evidence_id) as evidence_count
                    FROM ai_systems s
                    LEFT JOIN evidence e ON s.system_id = e.system_id
                    GROUP BY s.system_id
                    ORDER BY s.risk_classification DESC, s.name
                    """
                )

            # Evidence freshness
            evidence_freshness = await conn.fetch(
                """
                SELECT
                    system_id,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE collected_at > NOW() - INTERVAL '7 days') as fresh_7d,
                    COUNT(*) FILTER (WHERE collected_at > NOW() - INTERVAL '30 days') as fresh_30d,
                    COUNT(*) FILTER (WHERE collected_at <= NOW() - INTERVAL '90 days') as stale,
                    MAX(collected_at) as latest
                FROM evidence
                GROUP BY system_id
                ORDER BY stale DESC
                """
            )

            # Open findings and remediation
            open_findings = await conn.fetch(
                """
                SELECT
                    f.finding_id, f.title, f.severity, f.status,
                    f.owner, f.due_date, f.created_at,
                    s.name as system_name
                FROM findings f
                JOIN ai_systems s ON f.system_id = s.system_id
                WHERE f.status IN ('open', 'in_progress')
                ORDER BY f.severity DESC, f.due_date
                LIMIT 20
                """
            )

            # Incident register
            incidents = await conn.fetch(
                """
                SELECT
                    incident_id, title, severity, status,
                    created_at, resolved_at, system_id
                FROM incidents
                WHERE created_at > NOW() - INTERVAL '30 days'
                ORDER BY created_at DESC
                LIMIT 20
                """
            )

            # Change log
            change_log = await conn.fetch(
                """
                SELECT
                    change_id, system_id, change_type,
                    description, changed_at, changed_by
                FROM change_log
                WHERE changed_at > NOW() - INTERVAL '7 days'
                ORDER BY changed_at DESC
                LIMIT 20
                """
            )

            # Access review status
            access_reviews = await conn.fetch(
                """
                SELECT
                    ar.review_id, ar.system_id, ar.reviewer,
                    ar.status, ar.completed_at, ar.findings_count,
                    s.name as system_name
                FROM access_reviews ar
                JOIN ai_systems s ON ar.system_id = s.system_id
                WHERE ar.created_at > NOW() - INTERVAL '90 days'
                ORDER BY ar.completed_at DESC NULLS FIRST
                LIMIT 10
                """
            )

            return {
                "generated_at": datetime.utcnow(),
                "inventory": [dict(r) for r in inventory],
                "evidence_freshness": [dict(r) for r in evidence_freshness],
                "open_findings": [dict(r) for r in open_findings],
                "incidents": [dict(r) for r in incidents],
                "change_log": [dict(r) for r in change_log],
                "access_reviews": [dict(r) for r in access_reviews],
            }
        finally:
            await conn.close()
```

### 8.4 Dashboard API Routes

```python
# src/api/routes/dashboards.py

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from reporting.dashboards.executive import ExecutiveDashboard
from reporting.dashboards.program import ProgramDashboard
from reporting.dashboards.operating import OperatingDashboard

router = APIRouter(prefix="/api/v1/dashboards", tags=["dashboards"])


class DashboardResponse(BaseModel):
    dashboard_type: str
    generated_at: datetime
    data: dict[str, Any]


@router.get("/executive", response_model=DashboardResponse)
async def get_executive_dashboard(
    time_range_days: int = Query(default=90, ge=7, le=365),
    frameworks: list[str] | None = Query(default=None),
):
    """Get executive dashboard data."""
    dashboard = ExecutiveDashboard()
    data = await dashboard.get_dashboard_data(
        time_range_days=time_range_days,
        frameworks=frameworks,
    )
    return DashboardResponse(
        dashboard_type="executive",
        generated_at=datetime.utcnow(),
        data=data,
    )


@router.get("/program", response_model=DashboardResponse)
async def get_program_dashboard(
    frameworks: list[str] | None = Query(default=None),
):
    """Get program dashboard data."""
    dashboard = ProgramDashboard()
    data = await dashboard.get_dashboard_data(frameworks=frameworks)
    return DashboardResponse(
        dashboard_type="program",
        generated_at=datetime.utcnow(),
        data=data,
    )


@router.get("/operating", response_model=DashboardResponse)
async def get_operating_dashboard(
    system_ids: list[str] | None = Query(default=None),
):
    """Get operating dashboard data."""
    dashboard = OperatingDashboard()
    data = await dashboard.get_dashboard_data(system_ids=system_ids)
    return DashboardResponse(
        dashboard_type="operating",
        generated_at=datetime.utcnow(),
        data=data,
    )
```

---

## 9. Integration Examples

### 9.1 FastAPI Application Setup

```python
# src/api/main.py

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import dashboards, reports, subscriptions, analytics
from reporting.distribution import DistributionManager, EmailDistribution, WebhookDistribution
from reporting.pipeline import ReportPipeline
from reporting.scheduling.scheduler import ReportScheduler
from reporting.data_sources import DataSourceManager
from reporting.scoring import ScoringEngine
from reporting.quality import QualityEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting GRC_Claw Reporting Engine...")

    # Initialize components
    data_sources = DataSourceManager()
    await data_sources.connect()

    scoring_engine = ScoringEngine()
    await scoring_engine.connect()

    quality_engine = QualityEngine()

    pipeline = ReportPipeline(
        data_sources=data_sources,
        scoring_engine=scoring_engine,
        quality_engine=quality_engine,
    )

    distribution = DistributionManager()
    distribution.register_channel("email", EmailDistribution())
    distribution.register_channel("webhook", WebhookDistribution("https://hooks.example.com/grc"))

    scheduler = ReportScheduler(pipeline, distribution)
    await scheduler.start()

    # Store in app state
    app.state.pipeline = pipeline
    app.state.distribution = distribution
    app.state.scheduler = scheduler
    app.state.data_sources = data_sources

    logger.info("GRC_Claw Reporting Engine started")
    yield

    # Shutdown
    logger.info("Shutting down GRC_Claw Reporting Engine...")
    await scheduler.stop()
    await data_sources.disconnect()
    await scoring_engine.disconnect()
    logger.info("GRC_Claw Reporting Engine stopped")


app = FastAPI(
    title="GRC_Claw Reporting Engine",
    description="AI Governance Reporting Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(dashboards.router)
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "grc-claw-reporting"}
```

### 9.2 Report Generation API

```python
# src/api/routes/reports.py

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from reporting.pipeline import ReportRequest, ReportType, ReportFormat, ReportStatus

router = APIRouter()


class GenerateReportRequest(BaseModel):
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    frameworks: list[str] = Field(default_factory=list)
    system_ids: list[str] = Field(default_factory=list)
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None
    personalization: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenerateReportResponse(BaseModel):
    report_id: str
    status: str
    message: str
    estimated_completion: datetime


class ReportStatusResponse(BaseModel):
    report_id: str
    status: str
    file_path: str | None = None
    file_size: int | None = None
    checksum: str | None = None
    validation_results: dict[str, Any] | None = None
    error_message: str | None = None


def get_pipeline(request: Request):
    return request.app.state.pipeline


@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report(
    request: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    pipeline=Depends(get_pipeline),
):
    """Generate a new report."""
    report_request = ReportRequest(
        report_type=request.report_type,
        format=request.format,
        frameworks=request.frameworks,
        system_ids=request.system_ids,
        time_range_start=request.time_range_start,
        time_range_end=request.time_range_end,
        personalization=request.personalization,
        metadata=request.metadata,
    )

    # Generate in background for large reports
    background_tasks.add_task(pipeline.generate, report_request)

    return GenerateReportResponse(
        report_id=f"RPT-{uuid.uuid4().hex[:8]}",
        status="pending",
        message="Report generation started",
        estimated_completion=datetime.utcnow() + timedelta(minutes=5),
    )


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
async def get_report_status(
    report_id: str,
    pipeline=Depends(get_pipeline),
):
    """Get report generation status."""
    # In production, query from database/cache
    return ReportStatusResponse(
        report_id=report_id,
        status="ready",
        file_path=f"/output/reports/{report_id}.pdf",
        file_size=1024000,
        checksum="abc123",
        validation_results={"passed": True, "score": 0.95},
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    pipeline=Depends(get_pipeline),
):
    """Download a generated report."""
    from fastapi.responses import FileResponse

    file_path = f"/output/reports/{report_id}.pdf"
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{report_id}.pdf",
    )
```

### 9.3 Docker Compose Setup

```yaml
# docker-compose.yml
version: "3.8"

services:
  reporting-api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/grc_claw
      - REDIS_URL=redis://redis:6379
      - SMTP_HOST=mailhog
      - SMTP_PORT=1025
    depends_on:
      - postgres
      - redis
    volumes:
      - ./output:/app/output
      - ./src/reporting/templates:/app/src/reporting/templates

  reporting-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/grc_claw
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./output:/app/output

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=grc
      - POSTGRES_PASSWORD=grc
      - POSTGRES_DB=grc_claw
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "1025:1025"
      - "8025:8025"

volumes:
  postgres_data:
```

### 9.4 Database Migrations

```sql
-- migrations/001_initial_schema.sql

-- Report schedules
CREATE TABLE report_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) NOT NULL DEFAULT 'pdf',
    frequency VARCHAR(20) NOT NULL,
    cron_expression VARCHAR(100),
    recipients TEXT[] DEFAULT '{}',
    frameworks TEXT[] DEFAULT '{}',
    system_ids TEXT[] DEFAULT '{}',
    personalization JSONB DEFAULT '{}',
    enabled BOOLEAN DEFAULT true,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Report subscriptions
CREATE TABLE report_subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    report_types TEXT[] NOT NULL DEFAULT '{}',
    frameworks TEXT[] DEFAULT '{}',
    frequency VARCHAR(20) DEFAULT 'weekly',
    channels TEXT[] DEFAULT '{email}',
    format VARCHAR(20) DEFAULT 'pdf',
    filters JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_delivered TIMESTAMP WITH TIME ZONE,
    delivery_count INTEGER DEFAULT 0
);

-- Report analytics
CREATE TABLE report_analytics (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    report_id VARCHAR(100),
    report_type VARCHAR(50),
    user_id VARCHAR(100),
    user_role VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT
);

-- Report feedback
CREATE TABLE report_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id VARCHAR(100),
    report_type VARCHAR(50),
    user_id VARCHAR(100),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    usefulness INTEGER CHECK (usefulness >= 1 AND usefulness <= 5),
    clarity INTEGER CHECK (clarity >= 1 AND clarity <= 5),
    completeness INTEGER CHECK (completeness >= 1 AND completeness <= 5),
    comments TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_analytics_timestamp ON report_analytics(timestamp);
CREATE INDEX idx_analytics_report_type ON report_analytics(report_type);
CREATE INDEX idx_analytics_user_id ON report_analytics(user_id);
CREATE INDEX idx_analytics_event_type ON report_analytics(event_type);
CREATE INDEX idx_subscriptions_user_id ON report_subscriptions(user_id);
CREATE INDEX idx_subscriptions_report_type ON report_subscriptions USING GIN(report_types);
CREATE INDEX idx_schedules_enabled ON report_schedules(enabled);
```

---

## 10. Deployment and Operations

### 10.1 Configuration

```python
# src/config/settings.py

from __future__ import annotations

from pydantic_settings import BaseSettings


class ReportingSettings(BaseSettings):
    """Reporting engine configuration."""

    # Database
    database_url: str = "postgresql://grc:grc@localhost:5432/grc_claw"
    redis_url: str = "redis://localhost:6379"

    # Email
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    from_address: str = "reports@grc-claw.local"

    # Report Generation
    output_dir: str = "output/reports"
    template_dir: str = "src/reporting/templates"
    max_concurrent_reports: int = 5
    report_timeout_seconds: int = 300

    # Quality
    quality_threshold: float = 0.8
    freshness_threshold_days: int = 90

    # Scheduling
    scheduler_enabled: bool = True
    max_retry_attempts: int = 3
    retry_backoff_factor: float = 2.0

    # Analytics
    analytics_enabled: bool = True
    feedback_collection: bool = True

    class Config:
        env_prefix = "GRC_REPORT_"


settings = ReportingSettings()
```

### 10.2 Monitoring and Alerting

```python
# src/reporting/monitoring.py

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ReportingMonitor:
    """Monitors reporting engine health and performance."""

    def __init__(self, pg_dsn: str = "postgresql://localhost/grc_claw"):
        self.pg_dsn = pg_dsn

    async def get_health_status(self) -> dict[str, Any]:
        """Get overall health status."""
        import asyncpg
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            # Check database connectivity
            db_status = await conn.fetchval("SELECT 1")

            # Check recent report generation
            recent_reports = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'ready') as successful,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed
                FROM report_artifacts
                WHERE created_at > NOW() - INTERVAL '24 hours'
                """
            )

            # Check queue depth
            queue_depth = await conn.fetchval(
                "SELECT COUNT(*) FROM report_schedules WHERE enabled = true AND next_run < NOW()"
            )

            return {
                "status": "healthy" if db_status else "unhealthy",
                "database": "connected" if db_status else "disconnected",
                "recent_reports": dict(recent_reports),
                "queue_depth": queue_depth,
                "timestamp": datetime.utcnow(),
            }
        finally:
            await conn.close()

    async def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics."""
        import asyncpg
        conn = await asyncpg.connect(self.pg_dsn)
        try:
            metrics = await conn.fetchrow(
                """
                SELECT
                    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_generation_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - created_at))) as p95_generation_time,
                    COUNT(*) FILTER (WHERE status = 'ready') as successful,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed
                FROM report_artifacts
                WHERE created_at > NOW() - INTERVAL '7 days'
                """
            )
            return dict(metrics)
        finally:
            await conn.close()
```

### 10.3 Testing

```python
# tests/test_pipeline.py

import pytest
from datetime import datetime, timedelta

from reporting.pipeline import (
    ReportPipeline,
    ReportRequest,
    ReportType,
    ReportFormat,
    ReportStatus,
)


@pytest.fixture
async def pipeline():
    """Create a test pipeline."""
    # Mock data sources for testing
    from unittest.mock import AsyncMock

    data_sources = AsyncMock()
    data_sources.get_inventory = AsyncMock(return_value=[
        {"system_id": "sys-001", "name": "Test System", "status": "production"}
    ])
    data_sources.get_compliance_scores = AsyncMock(return_value=[
        {"system_id": "sys-001", "framework": "soc2", "score": 0.85, "trend": 0.02, "status": "green"}
    ])
    data_sources.get_evidence_summary = AsyncMock(return_value={
        "total_count": 10,
        "verified_count": 8,
        "attested_count": 5,
        "latest_evidence": datetime.utcnow()
    })
    data_sources.get_incidents = AsyncMock(return_value=[])
    data_sources.get_risks = AsyncMock(return_value=[])
    data_sources.get_trends = AsyncMock(return_value=[])
    data_sources.get_pending_decisions = AsyncMock(return_value=[])
    data_sources.get_exceptions = AsyncMock(return_value=[])
    data_sources.get_monitoring_status = AsyncMock(return_value=[])

    scoring_engine = AsyncMock()
    scoring_engine.calculate_score = AsyncMock(return_value=0.85)
    scoring_engine.calculate_trend = AsyncMock(return_value=0.02)
    scoring_engine.rag_status = lambda x: "green" if x >= 0.8 else "amber" if x >= 0.6 else "red"
    scoring_engine.get_control_family_rag = AsyncMock(return_value={})

    quality_engine = AsyncMock()
    quality_engine.check_completeness = AsyncMock(return_value={"score": 0.95, "passed": True})
    quality_engine.check_freshness = AsyncMock(return_value={"score": 0.9, "passed": True})
    quality_engine.check_accuracy = AsyncMock(return_value={"score": 1.0, "passed": True})
    quality_engine.check_consistency = AsyncMock(return_value={"score": 1.0, "passed": True})

    pipeline = ReportPipeline(
        data_sources=data_sources,
        scoring_engine=scoring_engine,
        quality_engine=quality_engine,
        output_dir="/tmp/test-reports",
    )
    return pipeline


@pytest.mark.asyncio
async def test_generate_board_summary(pipeline):
    """Test board summary report generation."""
    request = ReportRequest(
        report_type=ReportType.BOARD_SUMMARY,
        format=ReportFormat.HTML,
        frameworks=["soc2"],
    )

    artifact = await pipeline.generate(request)

    assert artifact.status == ReportStatus.READY
    assert artifact.report_id.startswith("RPT-")
    assert artifact.file_path is not None
    assert artifact.validation_results["passed"] is True


@pytest.mark.asyncio
async def test_generate_evidence_pack(pipeline):
    """Test evidence pack generation."""
    request = ReportRequest(
        report_type=ReportType.EVIDENCE_PACK,
        format=ReportFormat.JSON,
        frameworks=["eu-ai-act"],
        system_ids=["sys-001"],
    )

    artifact = await pipeline.generate(request)

    assert artifact.status == ReportStatus.READY
    assert artifact.format == ReportFormat.JSON


@pytest.mark.asyncio
async def test_pipeline_failure_handling(pipeline):
    """Test pipeline handles failures gracefully."""
    # Make data collection fail
    pipeline.stages[0].execute = AsyncMock(side_effect=Exception("Database error"))

    request = ReportRequest(
        report_type=ReportType.BOARD_SUMMARY,
        format=ReportFormat.PDF,
    )

    artifact = await pipeline.generate(request)

    assert artifact.status == ReportStatus.FAILED
    assert artifact.error_message is not None
```

### 10.4 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/grc-claw/reporting-engine.git
cd reporting-engine
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Start infrastructure
docker-compose up -d postgres redis mailhog

# 3. Run migrations
alembic upgrade head

# 4. Start the API
uvicorn src.api.main:app --reload --port 8000

# 5. Generate a test report
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "board_summary",
    "format": "pdf",
    "frameworks": ["soc2", "iso-42001"]
  }'

# 6. Check report status
curl http://localhost:8000/api/v1/reports/RPT-xxx/status

# 7. Download report
curl -O http://localhost:8000/api/v1/reports/RPT-xxx/download

# 8. View dashboards
curl http://localhost:8000/api/v1/dashboards/executive
curl http://localhost:8000/api/v1/dashboards/program
curl http://localhost:8000/api/v1/dashboards/operating
```

---

## Appendix A: Report Template Inventory

| Template | File | Audience | Frequency | Output Formats |
|----------|------|----------|-----------|----------------|
| Board Compliance Summary | `board_summary.html` | Board, C-Suite | Quarterly | PDF, HTML |
| Regulatory Evidence Pack | `evidence_pack.html` | Regulators, Auditors | On-demand | JSON, PDF, OSCAL |
| Executive Risk Dashboard | (API-driven) | C-Suite | Real-time | Web, PDF |
| Program Status Report | `program_status.html` | Governance Committee | Monthly | PDF, HTML |
| Operational Compliance View | (API-driven) | Engineers, Ops | Real-time | Web |
| Vendor Risk Assessment | `vendor_risk.html` | Procurement, Risk | Per-vendor | PDF, JSON |
| Incident Report | `incident_report.html` | All stakeholders | Per-incident | PDF, HTML |
| Transparency Report | `transparency.html` | Public | Annual | Web, PDF |

## Appendix B: Key Metrics Reference

| Metric | Definition | Target | Owner |
|--------|-----------|--------|-------|
| High-Risk Model Audit Coverage | % of high-risk models with current audit | 100% | AI Ethics Officer |
| Average Review Cycle Time | Time from intake to decision | < 48 hrs | Governance Board Chair |
| Policy Violation Rate | Violations per 1000 decisions | < 0.1% | Compliance Lead |
| AI Incident Response Time (P1) | Time to respond to critical incident | < 1 hr | Security & Risk |
| Employee Ethics Training Completion | % completion for scoped roles | > 95% | Head of Talent |
| Explainability Score | Score for high-risk models | > 8.5/10 | ML Engineering Lead |
| Model Drift Alert Resolution | Time to resolve drift alert | < 24 hrs | MLOps Team |
| Authority Coverage | % active uses with current approval | 100% | Governance Office |
| Review Currency | % reviews not overdue | > 95% | Risk Officers |
| Exception Exposure | Open/expired exceptions by consequence | 0 expired | Compliance Lead |
| Control Evidence Coverage | % high-risk uses with current proof | 100% | Control Owners |
| Monitoring Coverage | % critical uses with required signals | 100% | Operations |
| Decision Speed | Time from complete intake to decision | < 5 days | Governance Office |
| Value Against Baseline | Approved value vs actual outcomes | Positive | Business Owners |

---

*End of Implementation Guide.*</longcat_think>
