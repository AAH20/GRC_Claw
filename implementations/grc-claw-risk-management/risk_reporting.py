"""
GRC_Claw Risk Reporting
========================
Generates the six standard risk reports:
  1. Risk Dashboard (real-time)
  2. Risk Register Summary (weekly)
  3. Executive Risk Report (quarterly)
  4. Regulatory Risk Report (on-demand)
  5. Incident Risk Report (per incident)
  6. Annual Risk Report (annually)

References GRC-RISK-001 §9.1-9.5.

Usage:
    from risk_reporting import RiskReporter

    reporter = RiskReporter(register, workflow, monitor)
    dashboard = reporter.generate_dashboard()
    exec_report = reporter.generate_executive_report()
"""

from __future__ import annotations

import json
import csv
from datetime import datetime, date, timedelta
from typing import Optional
from io import StringIO


# ─── Report Types ────────────────────────────────────────────────────────────

REPORT_TYPES = {
    "dashboard": {"audience": "All stakeholders", "frequency": "Real-time", "format": "Web dashboard"},
    "register_summary": {"audience": "Risk owners, managers", "frequency": "Weekly", "format": "PDF + CSV"},
    "executive": {"audience": "C-suite, Board", "frequency": "Quarterly", "format": "PDF + interactive"},
    "regulatory": {"audience": "Regulators, auditors", "frequency": "On-demand", "format": "Evidence pack"},
    "incident": {"audience": "All stakeholders", "frequency": "Per incident", "format": "PDF + web"},
    "annual": {"audience": "Executive leadership, Board", "frequency": "Annually", "format": "PDF + presentation"},
}


# ─── Risk Reporter ───────────────────────────────────────────────────────────

class RiskReporter:
    """
    Generates all standard GRC_Claw risk reports.
    Consumes data from RiskRegister, TreatmentWorkflow, and RiskMonitor.
    """

    def __init__(self, register, workflow=None, monitor=None):
        self.register = register
        self.workflow = workflow
        self.monitor = monitor

    # ── 1. Risk Dashboard ──────────────────────────────────────────────

    def generate_dashboard(self) -> dict:
        """
        Real-time executive risk dashboard (GRC-RISK-001 §9.2).
        One-page principle: overall score, tier counts, top risks, domain posture.
        """
        risks = self.register.all()
        active = [r for r in risks if r.risk_status.value not in ("closed", "retired")]

        # Overall risk score
        scores = [(r.residual_score or r.inherent_score) for r in active
                  if (r.residual_score or r.inherent_score)]
        overall_mdrs = round(sum(s.mdrs for s in scores) / len(scores), 2) if scores else 0.0

        # Tier counts
        tier_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Minimal": 0}
        for s in scores:
            tier_counts[s.tier.value] = tier_counts.get(s.tier.value, 0) + 1

        # Top 5 material risks
        sorted_risks = sorted(active, key=lambda r: (r.residual_score or r.inherent_score).mdrs, reverse=True)
        top_risks = []
        for r in sorted_risks[:5]:
            s = r.residual_score or r.inherent_score
            top_risks.append({
                "risk_id": r.risk_id,
                "category": r.risk_category,
                "title": r.risk_title,
                "mdrs": s.mdrs,
                "tier": s.tier.value,
                "status": r.risk_status.value,
            })

        # Risk posture by domain
        domain_scores: dict[str, list[float]] = {}
        for r in active:
            s = r.residual_score or r.inherent_score
            if s:
                domain_scores.setdefault(r.risk_domain, []).append(s.mdrs)
        domain_posture = {
            d: round(sum(v) / len(v), 2) for d, v in domain_scores.items()
        }

        # Decisions required (critical + high without treatment plan)
        decisions_required = len([
            r for r in active
            if (r.residual_score or r.inherent_score)
            and (r.residual_score or r.inherent_score).tier.value in ("Critical", "High")
            and not r.treatment_plan
        ])

        # Overdue treatments
        overdue = len(self.register.overdue_reviews())

        return {
            "report_type": "Risk Dashboard",
            "generated_at": datetime.utcnow().isoformat(),
            "overall_risk_score": overall_mdrs,
            "overall_tier": self._mdrs_to_tier(overall_mdrs),
            "tier_counts": tier_counts,
            "top_5_material_risks": top_risks,
            "risk_posture_by_domain": domain_posture,
            "decisions_required": decisions_required,
            "overdue_treatments": overdue,
            "total_active_risks": len(active),
        }

    # ── 2. Risk Register Summary ────────────────────────────────────────

    def generate_register_summary(self, format: str = "json") -> str:
        """
        Weekly risk register summary for risk owners and managers.
        """
        risks = self.register.all()
        summary = self.register.summary()

        if format == "json":
            return json.dumps({
                "report_type": "Risk Register Summary",
                "generated_at": datetime.utcnow().isoformat(),
                "summary": summary,
                "risks": [r.to_dict() for r in risks],
            }, indent=2, default=str)

        elif format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "Risk ID", "Title", "Domain", "Category", "Status",
                "Owner", "MDRS", "Tier", "Review Date",
            ])
            for r in risks:
                s = r.residual_score or r.inherent_score
                writer.writerow([
                    r.risk_id, r.risk_title, r.risk_domain, r.risk_category,
                    r.risk_status.value, r.risk_owner,
                    s.mdrs if s else "", s.tier.value if s else "",
                    r.review_date,
                ])
            return output.getvalue()

        else:
            raise ValueError(f"Unsupported format: {format}")

    # ── 3. Executive Risk Report ────────────────────────────────────────

    def generate_executive_report(self, period: str = "Q4 2026") -> str:
        """
        Quarterly executive risk report (GRC-RISK-001 §9.3).
        Markdown format suitable for board presentation.
        """
        dashboard = self.generate_dashboard()
        summary = self.register.summary()

        # Treatment summary
        treatment_stats = {}
        if self.workflow:
            treatment_stats = self.workflow.summary()

        # Control effectiveness
        controls_tested = 0
        controls_passed = 0
        if self.workflow:
            for plan in self.workflow._plans.values():
                for ctrl in plan.controls:
                    if ctrl.status.value == "verified":
                        controls_tested += 1
                        controls_passed += 1
                    elif ctrl.status.value == "failed":
                        controls_tested += 1

        report = f"""# Executive AI Risk Report — {period}

## 1. Risk Posture Summary
- **Overall Risk Score:** {dashboard['overall_risk_score']} ({dashboard['overall_tier']})
- **Trend:** ↔ Stable (requires historical comparison)
- **Risks by tier:** Critical {dashboard['tier_counts'].get('Critical', 0)}, High {dashboard['tier_counts'].get('High', 0)}, Medium {dashboard['tier_counts'].get('Medium', 0)}, Low {dashboard['tier_counts'].get('Low', 0)}, Minimal {dashboard['tier_counts'].get('Minimal', 0)}
- **Risks by domain:** {', '.join(f'{d} {s}' for d, s in dashboard['risk_posture_by_domain'].items())}

## 2. Material Risks (Top 5)
"""
        for i, risk in enumerate(dashboard['top_5_material_risks'], 1):
            report += f"{i}. [{risk['category']}] {risk['title']} — MDRS {risk['mdrs']} ({risk['tier']})\n"

        report += f"""
## 3. Risk Treatment Summary
- New risks identified: {summary.get('by_status', {}).get('identified', 0)}
- Risks treated this period: {treatment_stats.get('by_status', {}).get('verified', 0)}
- Risks escalated: {treatment_stats.get('by_status', {}).get('overdue', 0)}
- Risks closed: {summary.get('by_status', {}).get('closed', 0)}
- Overdue treatments: {dashboard['overdue_treatments']}

## 4. Control Effectiveness
- Controls tested: {controls_tested}
- Controls passed: {controls_passed} ({round(controls_passed / controls_tested * 100, 1) if controls_tested else 0}%)
- Controls failed: {controls_tested - controls_passed}

## 5. Compliance Posture
- EU AI Act: Mapped via MDRS-to-EU tier classification
- NIST AI RMF: GOVERN-MAP-MEASURE-MANAGE alignment
- ISO 42001: AIMS clauses 6.1, 8.2, 8.5

## 6. Key Risk Indicators
"""
        if self.monitor:
            kri_status = self.monitor.kri_tracker.summary()
            for name, status in kri_status.items():
                emoji = "🔴" if status['status'] == 'breached' else "🟢"
                report += f"- {emoji} {status['name']}: {status['current']} (target: {status['target']}, threshold: {status['threshold']})\n"

        report += f"""
## 7. Decisions Required
- {dashboard['decisions_required']} critical/high risks require treatment decisions

## 8. Recommendations
1. Prioritize treatment for Critical and High tier risks
2. Review overdue assessments within 7 days
3. Update risk appetite thresholds if posture shifts

---
*Generated by GRC_Claw Risk Reporting Engine*
"""
        return report

    # ── 4. Regulatory Risk Report ───────────────────────────────────────

    def generate_regulatory_report(self, system_id: str) -> dict:
        """
        Regulatory risk report (evidence pack) for EU AI Act submission.
        References GRC-RISK-001 §9.4.
        """
        risks = self.register.find_by_category(system_id) if system_id else self.register.all()

        return {
            "report_type": "Regulatory Risk Report",
            "system_id": system_id,
            "generated_at": datetime.utcnow().isoformat(),
            "sections": {
                "1_system_identification": {
                    "system_id": system_id,
                    "provider": "GRC_Claw",
                    "deployer": list(set(r.risk_owner for r in risks)),
                    "classification": "See MDRS-to-EU mapping",
                },
                "2_risk_assessment": {
                    "methodology": "MDRS (Multi-Dimensional Risk Score)",
                    "identified_risks": len(risks),
                    "mdrs_scores": [
                        {
                            "risk_id": r.risk_id,
                            "category": r.risk_category,
                            "mdrs": (r.residual_score or r.inherent_score).mdrs if (r.residual_score or r.inherent_score) else None,
                            "tier": (r.residual_score or r.inherent_score).tier.value if (r.residual_score or r.inherent_score) else None,
                        }
                        for r in risks
                    ],
                    "eu_ai_act_reference": "Art. 9(2)(a)",
                },
                "3_risk_treatment": {
                    "mitigation_measures": [
                        {
                            "risk_id": r.risk_id,
                            "strategy": r.treatment_plan.get("strategy") if r.treatment_plan else None,
                            "residual_mdrs": r.residual_score.mdrs if r.residual_score else None,
                        }
                        for r in risks if r.treatment_plan
                    ],
                    "eu_ai_act_reference": "Art. 9(4)",
                },
                "4_conformity_assessment": {
                    "assessment_results": "See treatment plans",
                    "eu_ai_act_reference": "Art. 43",
                },
                "5_post_market_monitoring": {
                    "monitoring_data": "See Risk Monitor output",
                    "eu_ai_act_reference": "Art. 72, Art. 73",
                },
                "6_technical_documentation": {
                    "model_cards": "See model registry",
                    "eu_ai_act_reference": "Art. 11, Annex IV",
                },
                "7_change_log": {
                    "changes": "See audit trails",
                    "eu_ai_act_reference": "Art. 11(2)",
                },
            },
        }

    # ── 5. Incident Risk Report ─────────────────────────────────────────

    def generate_incident_report(
        self, incident_id: str, risk_ids: list[str],
        severity: str, description: str,
    ) -> str:
        """
        Per-incident risk report.
        """
        report = f"""# Incident Risk Report — {incident_id}

## Incident Summary
- **Incident ID:** {incident_id}
- **Severity:** {severity}
- **Date:** {datetime.utcnow().isoformat()}
- **Description:** {description}

## Affected Risks
"""
        for rid in risk_ids:
            risk = self.register.get(rid)
            if risk:
                s = risk.residual_score or risk.inherent_score
                report += f"- [{risk.risk_id}] {risk.risk_title} (MDRS: {s.mdrs if s else 'N/A'}, Tier: {s.tier.value if s else 'N/A'})\n"

        report += """
## Response Actions
1. Affected risks escalated per escalation matrix
2. Treatment plans reviewed and updated
3. Residual risk recalculated
4. Lessons learned documented

## Root Cause Analysis
- To be completed within 48 hours per OPS-02

## Follow-up
- Post-incident review scheduled
- Risk register updated with lessons learned
"""
        return report

    # ── 6. Annual Risk Report ───────────────────────────────────────────

    def generate_annual_report(self, year: int) -> str:
        """
        Annual comprehensive risk report.
        """
        dashboard = self.generate_dashboard()
        summary = self.register.summary()

        report = f"""# Annual AI Risk Report — {year}

## Executive Summary
- **Overall Risk Score:** {dashboard['overall_risk_score']} ({dashboard['overall_tier']})
- **Total Active Risks:** {dashboard['total_active_risks']}
- **Risks by Tier:** Critical {dashboard['tier_counts'].get('Critical', 0)}, High {dashboard['tier_counts'].get('High', 0)}, Medium {dashboard['tier_counts'].get('Medium', 0)}, Low {dashboard['tier_counts'].get('Low', 0)}, Minimal {dashboard['tier_counts'].get('Minimal', 0)}

## Risk Posture by Domain
"""
        for domain, score in dashboard['risk_posture_by_domain'].items():
            report += f"- **{domain}:** {score}\n"

        report += f"""
## Key Achievements
- Risk assessment coverage: {summary.get('by_status', {}).get('assessed', 0)} risks assessed
- Treatment plans executed: {summary.get('by_status', {}).get('treated', 0)}
- Risks closed: {summary.get('by_status', {}).get('closed', 0)}

## Framework Compliance
- NIST AI RMF 1.0: GOVERN-MAP-MEASURE-MANAGE implemented
- ISO/IEC 42001:2023: AIMS clauses mapped
- EU AI Act: 4-tier classification integrated

## Recommendations for {year + 1}
1. Mature agentic AI risk metrics (AG-001 to AG-012)
2. Enhance cascading risk modeling
3. Automate evidence collection
4. Expand third-party risk coverage

---
*Generated by GRC_Claw Risk Reporting Engine*
"""
        return report

    # ── Helper Methods ─────────────────────────────────────────────────

    @staticmethod
    def _mdrs_to_tier(mdrs: float) -> str:
        if mdrs >= 4.50:
            return "Critical"
        elif mdrs >= 3.50:
            return "High"
        elif mdrs >= 2.50:
            return "Medium"
        elif mdrs >= 1.50:
            return "Low"
        else:
            return "Minimal"


# ─── Demo / Self-Test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from risk_register import RiskRegister
    from risk_treatment_workflow import TreatmentWorkflow, TreatmentStrategy, ControlStatus
    from risk_monitoring import RiskMonitor

    # Setup
    register = RiskRegister()
    workflow = TreatmentWorkflow()
    monitor = RiskMonitor()
    reporter = RiskReporter(register, workflow, monitor)

    # Create sample risks
    r1 = register.create_risk(
        title="Agent goal hijacking vulnerability",
        domain="SEC", category="SEC-02",
        likelihood=3, impact=5, detectability=4, velocity=5, persistence=3,
        owner="security-lead@org.com",
    )
    r2 = register.create_risk(
        title="Bias in loan approval model",
        domain="DAT", category="DAT-03",
        likelihood=4, impact=4, detectability=3, velocity=3, persistence=4,
        owner="data-science-lead@org.com",
    )
    r3 = register.create_risk(
        title="Vendor model silent update",
        domain="TPR", category="TPR-03",
        likelihood=3, impact=3, detectability=3, velocity=2, persistence=3,
        owner="vendor-mgmt@org.com",
    )

    # Create treatment plan
    from risk_treatment_workflow import RiskTier
    plan = workflow.create_treatment_plan(
        risk_id=r1.risk_id,
        strategy=TreatmentStrategy.MITIGATE,
        risk_category="SEC-02",
        risk_tier=RiskTier.HIGH,
    )

    # Generate reports
    dashboard = reporter.generate_dashboard()
    print("=== Risk Dashboard ===")
    print(json.dumps(dashboard, indent=2))

    print("\n=== Executive Report (excerpt) ===")
    exec_report = reporter.generate_executive_report()
    print(exec_report[:1500] + "...")

    print("\n=== Regulatory Report (excerpt) ===")
    reg_report = reporter.generate_regulatory_report("SEC-02")
    print(json.dumps(reg_report, indent=2)[:1500] + "...")
