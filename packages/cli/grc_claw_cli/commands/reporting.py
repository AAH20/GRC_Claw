"""Reporting commands for GRC_Claw CLI."""
import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from grc_claw_cli.utils.output import print_json, print_table, print_success, print_error, print_warning, print_info
from grc_claw_cli.utils.config import Config


REPORT_TYPES = ["board_summary", "risk_heatmap", "compliance_trend", "incident_summary", "audit_summary", "vendor_risk", "executive_dashboard"]


class ReportStore:
    """Store for generated reports."""

    def __init__(self):
        self.config = Config()
        self.reports = []
        self._load()

    def _load(self):
        path = self.config.CONFIG_DIR / "reports.json"
        if path.exists():
            try:
                with open(path) as f:
                    self.reports = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.reports = []

    def _save(self):
        self.config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        path = self.config.CONFIG_DIR / "reports.json"
        with open(path, "w") as f:
            json.dump(self.reports, f, indent=2, default=str)

    def generate(self, report_type, period, data=None):
        report = {
            "id": str(uuid.uuid4()),
            "title": self._title(report_type),
            "type": report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": period,
            "sections": self._sections(report_type, data),
            "summary": self._summary(report_type),
            "recommendations": self._recommendations(report_type),
        }
        self.reports.append(report)
        self._save()
        return report

    def get(self, report_id):
        return next((r for r in self.reports if r["id"] == report_id), None)

    def list(self, report_type=None):
        if report_type:
            return [r for r in self.reports if r["type"] == report_type]
        return self.reports

    def delete(self, report_id):
        report = self.get(report_id)
        if not report:
            return False
        self.reports = [r for r in self.reports if r["id"] != report_id]
        self._save()
        return True

    @staticmethod
    def _title(report_type):
        titles = {
            "board_summary": "Board Risk & Compliance Summary",
            "risk_heatmap": "Enterprise Risk Heatmap",
            "compliance_trend": "Compliance Posture Trend",
            "incident_summary": "Security Incident Summary",
            "audit_summary": "Audit Findings Summary",
            "vendor_risk": "Third-Party Risk Report",
            "executive_dashboard": "Executive GRC Dashboard",
        }
        return titles.get(report_type, report_type.replace("_", " ").title())

    @staticmethod
    def _sections(report_type, data):
        if data and "sections" in data:
            return data["sections"]
        return [
            {"title": "Executive Summary", "content": f"High-level overview of {report_type.replace('_', ' ')}."},
            {"title": "Key Metrics", "content": "Key performance indicators and trends."},
            {"title": "Recommendations", "content": "Actionable recommendations for the reporting period."},
        ]

    @staticmethod
    def _summary(report_type):
        return f"This {report_type.replace('_', ' ')} provides a comprehensive overview of the organization's GRC posture."

    @staticmethod
    def _recommendations(report_type):
        return [
            "Prioritize remediation of critical findings within 30 days",
            "Increase vendor assessment cadence for critical-tier vendors",
            "Implement automated evidence collection for compliance controls",
            "Schedule tabletop exercise for incident response plan",
        ]


def register(subparsers):
    """Register reporting subcommands."""
    parser = subparsers.add_parser("report", help="Reporting commands")
    rep_sub = parser.add_subparsers(dest="report_command", help="Report operations")

    # report generate
    gen_p = rep_sub.add_parser("generate", help="Generate a report")
    gen_p.add_argument("--type", required=True, choices=REPORT_TYPES, help="Report type")
    gen_p.add_argument("--period", default="Q4-2024", help="Reporting period")
    gen_p.add_argument("--data", help="JSON file with report data")
    gen_p.add_argument("--output", help="Output file path")
    gen_p.add_argument("--json", action="store_true", help="Output as JSON")

    # report list
    list_p = rep_sub.add_parser("list", help="List generated reports")
    list_p.add_argument("--type", choices=REPORT_TYPES, help="Filter by report type")
    list_p.add_argument("--json", action="store_true", help="Output as JSON")

    # report get
    get_p = rep_sub.add_parser("get", help="Get report details")
    get_p.add_argument("id", help="Report ID")
    get_p.add_argument("--json", action="store_true", help="Output as JSON")

    # report delete
    del_p = rep_sub.add_parser("delete", help="Delete a report")
    del_p.add_argument("id", help="Report ID")

    # report dashboard
    dash_p = rep_sub.add_parser("dashboard", help="Generate executive dashboard")
    dash_p.add_argument("--json", action="store_true", help="Output as JSON")


def handle(args, config: Config):
    """Handle reporting commands."""
    store = ReportStore()
    cmd = args.report_command

    if cmd == "generate":
        data = None
        if args.data:
            try:
                with open(args.data) as f:
                    data = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print_error(f"Failed to load data: {e}")
                return 1
        report = store.generate(args.type, args.period, data)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print_success(f"Report written to {args.output}")
        elif args.json:
            print_json(report)
        else:
            print_info(f"Report: {report['title']}")
            print(f"  Type: {report['type']}")
            print(f"  Period: {report['period']}")
            print(f"  Generated: {report['generated_at']}")
            print(f"\n  Summary: {report['summary']}")
            print("\n  Recommendations:")
            for rec in report["recommendations"]:
                print(f"    - {rec}")
        return 0

    elif cmd == "list":
        reports = store.list(report_type=args.type)
        if args.json:
            print_json(reports)
        else:
            if not reports:
                print_info("No reports found.")
            else:
                rows = [[r["id"][:8], r["type"], r["period"], r["generated_at"][:10]] for r in reports]
                print_table(["ID", "Type", "Period", "Date"], rows)
        return 0

    elif cmd == "get":
        report = store.get(args.id)
        if not report:
            print_error(f"Report not found: {args.id}")
            return 1
        print_json(report)
        return 0

    elif cmd == "delete":
        if store.delete(args.id):
            print_success(f"Report deleted: {args.id}")
            return 0
        print_error(f"Report not found: {args.id}")
        return 1

    elif cmd == "dashboard":
        dashboard = {
            "overall_risk_score": 72,
            "compliance_score": 88,
            "open_incidents": 3,
            "critical_findings": 2,
            "vendor_risk_score": 65,
            "upcoming_audits": 2,
            "policy_expirations": 4,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        if args.json:
            print_json(dashboard)
        else:
            print_info("Executive GRC Dashboard")
            print(f"  Overall Risk Score: {dashboard['overall_risk_score']}/100")
            print(f"  Compliance Score: {dashboard['compliance_score']}%")
            print(f"  Open Incidents: {dashboard['open_incidents']}")
            print(f"  Critical Findings: {dashboard['critical_findings']}")
            print(f"  Vendor Risk Score: {dashboard['vendor_risk_score']}/100")
            print(f"  Upcoming Audits: {dashboard['upcoming_audits']}")
            print(f"  Policy Expirations: {dashboard['policy_expirations']}")
        return 0

    else:
        print_error("No report subcommand specified. Use: grc report <generate|list|get|delete|dashboard>")
        return 1
