"""Reporting Agent - Generates attribution reports in multiple formats."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import structlog

from attribution.agents.attribution_engine import CampaignAttribution, CustomerJourney
from attribution.agents.data_collection import RawDataPoint

logger = structlog.get_logger(__name__)


class ReportFormat(str, Enum):
    """Supported report formats."""

    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


@dataclass
class ReportMetadata:
    """Metadata for a generated report."""

    report_id: str
    title: str
    created_at: datetime
    format: ReportFormat
    date_range_start: datetime
    date_range_end: datetime
    models_used: list[str]
    total_journeys: int
    total_campaigns: int


@dataclass
class Report:
    """A complete attribution report."""

    metadata: ReportMetadata
    content: str | bytes
    summary: dict[str, Any]


class ReportingAgent:
    """Agent for generating marketing attribution reports."""

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__).bind(agent="reporting")

    def generate_report(
        self,
        journeys: list[CustomerJourney],
        attribution_results: list[CampaignAttribution],
        data_points: list[RawDataPoint],
        report_format: ReportFormat = ReportFormat.JSON,
        title: str | None = None,
    ) -> Report:
        """Generate a report in the specified format."""
        report_id = f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        start_date = min((dp.timestamp for dp in data_points), default=datetime.utcnow())
        end_date = max((dp.timestamp for dp in data_points), default=datetime.utcnow())
        metadata = ReportMetadata(
            report_id=report_id,
            title=title or f"Attribution Report {datetime.utcnow():%Y-%m-%d}",
            created_at=datetime.utcnow(),
            format=report_format,
            date_range_start=start_date,
            date_range_end=end_date,
            models_used=list({ar.model.value for ar in attribution_results}),
            total_journeys=len(journeys),
            total_campaigns=len(attribution_results),
        )
        summary = self._build_summary(journeys, attribution_results, data_points)
        if report_format == ReportFormat.JSON:
            content = self._generate_json(metadata, summary, attribution_results)
        elif report_format == ReportFormat.CSV:
            content = self._generate_csv(metadata, summary, attribution_results)
        elif report_format == ReportFormat.PDF:
            content = self._generate_pdf(metadata, summary, attribution_results)
        else:
            raise ValueError(f"Unsupported report format: {report_format}")
        self.logger.info(
            "Report generated",
            report_id=report_id,
            format=report_format.value,
            campaigns=len(attribution_results),
        )
        return Report(metadata=metadata, content=content, summary=summary)

    def _build_summary(
        self,
        journeys: list[CustomerJourney],
        attribution_results: list[CampaignAttribution],
        data_points: list[RawDataPoint],
    ) -> dict[str, Any]:
        """Build summary statistics for the report."""
        total_spend = sum(dp.spend for dp in data_points)
        total_revenue = sum(dp.revenue for dp in data_points)
        total_conversions = sum(dp.conversions for dp in data_points)
        total_impressions = sum(dp.impressions for dp in data_points)
        total_clicks = sum(dp.clicks for dp in data_points)
        total_attributed_revenue = sum(ar.attributed_revenue for ar in attribution_results)
        total_attributed_conversions = sum(ar.attributed_conversions for ar in attribution_results)
        return {
            "totals": {
                "spend": round(total_spend, 2),
                "revenue": round(total_revenue, 2),
                "conversions": round(total_conversions, 2),
                "impressions": total_impressions,
                "clicks": total_clicks,
                "ctr": (
                    round(total_clicks / total_impressions * 100, 2)
                    if total_impressions > 0
                    else 0
                ),
                "cpa": round(total_spend / total_conversions, 2) if total_conversions > 0 else 0,
                "roas": round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
            },
            "attributed": {
                "revenue": round(total_attributed_revenue, 2),
                "conversions": round(total_attributed_conversions, 2),
            },
            "top_campaigns": [
                {
                    "campaign_id": ar.campaign_id,
                    "campaign_name": ar.campaign_name,
                    "source": ar.source,
                    "attributed_revenue": round(ar.attributed_revenue, 2),
                    "attributed_conversions": round(ar.attributed_conversions, 2),
                    "roas": round(ar.roas, 2),
                }
                for ar in sorted(
                    attribution_results, key=lambda x: x.attributed_revenue, reverse=True
                )[:10]
            ],
        }

    def _generate_json(
        self,
        metadata: ReportMetadata,
        summary: dict[str, Any],
        attribution_results: list[CampaignAttribution],
    ) -> str:
        """Generate JSON report."""
        return json.dumps(
            {
                "metadata": asdict(metadata),
                "summary": summary,
                "campaigns": [asdict(ar) for ar in attribution_results],
            },
            indent=2,
            default=str,
        )

    def _generate_csv(
        self,
        metadata: ReportMetadata,
        summary: dict[str, Any],
        attribution_results: list[CampaignAttribution],
    ) -> str:
        """Generate CSV report."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Report ID", metadata.report_id])
        writer.writerow(["Title", metadata.title])
        writer.writerow(["Created At", metadata.created_at.isoformat()])
        writer.writerow(["Format", metadata.format.value])
        writer.writerow([])
        writer.writerow(["Summary"])
        for key, value in summary["totals"].items():
            writer.writerow([key, value])
        writer.writerow([])
        writer.writerow(
            [
                "Campaign ID",
                "Campaign Name",
                "Source",
                "Attributed Conversions",
                "Attributed Revenue",
                "Attributed Spend",
                "ROAS",
                "Model",
            ]
        )
        for ar in attribution_results:
            writer.writerow(
                [
                    ar.campaign_id,
                    ar.campaign_name,
                    ar.source,
                    ar.attributed_conversions,
                    ar.attributed_revenue,
                    ar.attributed_spend,
                    ar.roas,
                    ar.model.value,
                ]
            )
        return output.getvalue()

    def _generate_pdf(
        self,
        metadata: ReportMetadata,
        summary: dict[str, Any],
        attribution_results: list[CampaignAttribution],
    ) -> bytes:
        """Generate a minimal valid PDF report."""
        lines = [
            f"Title: {metadata.title}",
            f"Report ID: {metadata.report_id}",
            f"Generated: {metadata.created_at.isoformat()}",
            "",
            "=== Summary ===",
        ]
        for key, value in summary["totals"].items():
            lines.append(f"{key}: {value}")
        lines.extend(["", "=== Top Campaigns ==="])
        for camp in summary["top_campaigns"]:
            lines.append(
                f"{camp['campaign_name']} ({camp['source']}): "
                f"ROAS={camp['roas']}, Revenue=${camp['attributed_revenue']}"
            )
        text_content = "\n".join(lines)
        pdf_parts = [
            b"%PDF-1.4\n",
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
            (
                b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
            ),
        ]
        stream = f"BT /F1 12 Tf 72 720 Td 14 TL\n{text_content}\nET".encode()
        pdf_parts.append(
            f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode()
            + stream
            + b"\nendstream\nendobj\n"
        )
        pdf_parts.append(
            b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        )
        xref_offset = sum(len(p) for p in pdf_parts)
        pdf_parts.append(
            (
                f"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n "
                f"\n0000000058 00000 n \n0000000115 00000 n "
                f"\n0000000{260 + len(stream)} 00000 n "
                f"\n0000000{350 + len(stream)} 00000 n \n"
            ).encode()
        )
        pdf_parts.append(
            f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode()
        )
        return b"".join(pdf_parts)
