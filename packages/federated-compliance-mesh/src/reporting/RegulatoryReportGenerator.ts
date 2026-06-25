import type { FrameworkCode } from "../types.js";
import type {
  RegulatoryReport,
  ReportFormat,
  ReportMetadata,
  Jurisdiction,
  ComplianceLevel,
  CrossJurisdictionMapping,
} from "../types.js";

export interface ReportGeneratorConfig {
  defaultFormat: ReportFormat;
  includeEvidence: boolean;
  includeRemediation: boolean;
  templateDir?: string;
}

const JURISDICTION_FRAMEWORK_MAP: Record<Jurisdiction, FrameworkCode[]> = {
  global: ["iso27001", "soc2", "nist-csf"],
  eu: ["iso27001", "gdpr", "dora", "nis2", "eu-ai-act"],
  us: ["soc2", "nist-csf", "fedramp", "hipaa", "pci-dss"],
  uk: ["iso27001", "soc2"],
  apac: ["iso27001", "soc2"],
  latam: ["iso27001", "lgpd"],
  mena: ["iso27001", "soc2"],
};

const CROSS_JURISDICTION_MAPPINGS: CrossJurisdictionMapping[] = [
  { sourceFramework: "iso27001", sourceControl: "A.5.1", targetFramework: "soc2", targetControl: "CC6.1", relationship: "equivalent", confidence: 0.9, jurisdiction: "global" },
  { sourceFramework: "iso27001", sourceControl: "A.8.1", targetFramework: "nist-csf", targetControl: "PR.DS-1", relationship: "equivalent", confidence: 0.85, jurisdiction: "global" },
  { sourceFramework: "gdpr", sourceControl: "Art.32", targetFramework: "iso27001", targetControl: "A.14.1", relationship: "related", confidence: 0.8, jurisdiction: "eu" },
  { sourceFramework: "hipaa", sourceControl: "164.312(a)(1)", targetFramework: "iso27001", targetControl: "A.9.1", relationship: "equivalent", confidence: 0.85, jurisdiction: "us" },
  { sourceFramework: "dora", sourceControl: "Art.9", targetFramework: "iso27001", targetControl: "A.12.1", relationship: "related", confidence: 0.75, jurisdiction: "eu" },
];

export class RegulatoryReportGenerator {
  private reports: RegulatoryReport[] = [];
  private config: ReportGeneratorConfig;

  constructor(config: Partial<ReportGeneratorConfig> = {}) {
    this.config = {
      defaultFormat: "json",
      includeEvidence: true,
      includeRemediation: true,
      ...config,
    };
  }

  generateComplianceReport(
    orgId: string,
    jurisdiction: Jurisdiction,
    frameworkCode: FrameworkCode,
    controlScores: Map<string, number>,
    metadata: Partial<ReportMetadata> = {}
  ): RegulatoryReport {
    const compliantControls = Array.from(controlScores.values()).filter((s) => s >= 80).length;
    const totalControls = controlScores.size;
    const complianceLevel: ComplianceLevel =
      compliantControls / totalControls >= 0.9 ? "full" : compliantControls / totalControls >= 0.5 ? "partial" : "minimal";

    const report: RegulatoryReport = {
      id: `report-${Date.now()}`,
      orgId,
      jurisdiction,
      frameworkCode,
      reportType: "compliance",
      format: this.config.defaultFormat,
      generatedAt: new Date().toISOString(),
      content: this.formatReportContent(orgId, frameworkCode, controlScores, complianceLevel),
      metadata: {
        period: metadata.period || { from: new Date(Date.now() - 90 * 86400000).toISOString(), to: new Date().toISOString() },
        controlCount: totalControls,
        complianceLevel,
        ...metadata,
      },
    };

    this.reports.push(report);
    return report;
  }

  generateGapAnalysis(
    orgId: string,
    jurisdiction: Jurisdiction,
    frameworkCode: FrameworkCode,
    currentScores: Map<string, number>,
    targetScore: number = 80
  ): RegulatoryReport {
    const gaps = new Map<string, number>();
    for (const [controlId, score] of currentScores) {
      if (score < targetScore) {
        gaps.set(controlId, targetScore - score);
      }
    }

    const report: RegulatoryReport = {
      id: `gap-${Date.now()}`,
      orgId,
      jurisdiction,
      frameworkCode,
      reportType: "gap_analysis",
      format: this.config.defaultFormat,
      generatedAt: new Date().toISOString(),
      content: this.formatGapContent(orgId, frameworkCode, gaps, targetScore),
      metadata: {
        period: { from: new Date().toISOString(), to: new Date().toISOString() },
        controlCount: gaps.size,
        complianceLevel: "partial",
      },
    };

    this.reports.push(report);
    return report;
  }

  findCrossJurisdictionMappings(sourceFramework: FrameworkCode, targetJurisdiction: Jurisdiction): CrossJurisdictionMapping[] {
    return CROSS_JURISDICTION_MAPPINGS.filter(
      (m) => m.sourceFramework === sourceFramework && m.jurisdiction === targetJurisdiction
    );
  }

  getApplicableFrameworks(jurisdiction: Jurisdiction): FrameworkCode[] {
    return JURISDICTION_FRAMEWORK_MAP[jurisdiction] || [];
  }

  getReports(orgId?: string): RegulatoryReport[] {
    if (orgId) return this.reports.filter((r) => r.orgId === orgId);
    return this.reports;
  }

  private formatReportContent(
    orgId: string,
    frameworkCode: FrameworkCode,
    controlScores: Map<string, number>,
    complianceLevel: ComplianceLevel
  ): string {
    const totalScore = Array.from(controlScores.values()).reduce((a, b) => a + b, 0) / controlScores.size;
    return JSON.stringify({
      orgId,
      framework: frameworkCode,
      complianceLevel,
      overallScore: totalScore,
      controlScores: Object.fromEntries(controlScores),
      generatedAt: new Date().toISOString(),
    });
  }

  private formatGapContent(
    orgId: string,
    frameworkCode: FrameworkCode,
    gaps: Map<string, number>,
    targetScore: number
  ): string {
    return JSON.stringify({
      orgId,
      framework: frameworkCode,
      targetScore,
      gaps: Object.fromEntries(gaps),
      totalGaps: gaps.size,
      generatedAt: new Date().toISOString(),
    });
  }
}
