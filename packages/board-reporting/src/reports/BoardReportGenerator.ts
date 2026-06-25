import { randomUUID } from "node:crypto";
import type { BoardReport, ReportType, ReportSection, Metric, RiskHeatmap, ComplianceTrend, RiskHeatmapCell, ComplianceTrendPoint, ExecutiveDashboard, RiskLevel } from "../types.js";

export class BoardReportGenerator {
  private reports: Map<string, BoardReport> = new Map();

  generateReport(type: ReportType, period: string): BoardReport {
    const sections = this.generateSections(type);
    const report: BoardReport = {
      id: randomUUID(),
      title: this.getReportTitle(type),
      type,
      generatedAt: new Date().toISOString(),
      period,
      sections,
      summary: this.generateSummary(type),
      recommendations: this.generateRecommendations(type),
      riskHeatmap: this.generateRiskHeatmap(),
      complianceTrend: this.generateComplianceTrend(),
    };
    this.reports.set(report.id, report);
    return report;
  }

  private getReportTitle(type: ReportType): string {
    const titles: Record<ReportType, string> = {
      board_summary: "Board Risk & Compliance Summary",
      risk_heatmap: "Enterprise Risk Heatmap",
      compliance_trend: "Compliance Posture Trend",
      incident_summary: "Security Incident Summary",
      audit_summary: "Audit Findings Summary",
      vendor_risk: "Third-Party Risk Report",
      executive_dashboard: "Executive GRC Dashboard",
    };
    return titles[type];
  }

  private generateSections(type: ReportType): ReportSection[] {
    return [
      { title: "Executive Summary", content: "High-level overview of current GRC posture.", metrics: [{ label: "Overall Risk Score", value: 72, trend: "down", benchmark: "Industry avg: 65" }, { label: "Compliance Score", value: "88%", trend: "up" }], charts: [] },
      { title: "Key Risks", content: "Top risks requiring board attention.", metrics: [{ label: "Critical Risks", value: 3 }, { label: "High Risks", value: 7 }, { label: "Mitigated This Quarter", value: 12 }], charts: [] },
      { title: "Open Actions", content: "Outstanding remediation items.", metrics: [{ label: "Overdue", value: 2 }, { label: "Due This Month", value: 5 }, { label: "On Track", value: 15 }], charts: [] },
    ];
  }

  private generateSummary(type: ReportType): string {
    return `This ${type.replace(/_/g, " ")} provides a comprehensive overview of the organization's governance, risk, and compliance posture for the reporting period.`;
  }

  private generateRecommendations(type: ReportType): string[] {
    return [
      "Prioritize remediation of critical findings within 30 days",
      "Increase vendor assessment cadence for critical-tier vendors",
      "Implement automated evidence collection for SOC 2 controls",
      "Schedule tabletop exercise for incident response plan",
    ];
  }

  private generateRiskHeatmap(): RiskHeatmap {
    const categories = ["Cybersecurity", "Compliance", "Operational", "Financial", "Strategic", "Third-Party"];
    const data: RiskHeatmapCell[] = categories.map((category) => {
      const likelihood = Math.floor(Math.random() * 5) + 1;
      const impact = Math.floor(Math.random() * 5) + 1;
      const level: RiskLevel = likelihood * impact >= 20 ? "critical" : likelihood * impact >= 12 ? "high" : likelihood * impact >= 6 ? "medium" : likelihood * impact >= 2 ? "low" : "minimal";
      return { category, likelihood, impact, level, count: Math.floor(Math.random() * 10) + 1 };
    });
    return { title: "Risk Heatmap", data };
  }

  private generateComplianceTrend(): ComplianceTrend {
    const data: ComplianceTrendPoint[] = [];
    for (let i = 5; i >= 0; i--) {
      const date = new Date();
      date.setMonth(date.getMonth() - i);
      data.push({ date: date.toISOString().substring(0, 7), score: 80 + Math.floor(Math.random() * 10), controls: 200 + i * 5, gaps: 30 - i * 3 });
    }
    return { title: "Compliance Score Trend", data };
  }

  getReport(id: string): BoardReport | undefined { return this.reports.get(id); }
  listReports(): BoardReport[] { return Array.from(this.reports.values()); }

  getExecutiveDashboard(): ExecutiveDashboard {
    return { overallRiskScore: 72, complianceScore: 88, openIncidents: 3, criticalFindings: 2, vendorRiskScore: 65, upcomingAudits: 2, policyExpirations: 4 };
  }
}
