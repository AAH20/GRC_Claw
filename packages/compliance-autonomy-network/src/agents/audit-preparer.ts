import { randomBytes } from "node:crypto";
import { BaseAgent } from "./base-agent.js";
import type {
  SwarmTask,
  SwarmResult,
  AuditPackage,
  AuditSection,
  AuditGap,
  ControlStatus,
  EvidenceItem,
  ComplianceFramework,
  RiskLevel,
  AuditWindow,
} from "../types.js";

// ============================================================================
// AuditPreparer – assembles audit-ready packages from evidence and control statuses
// ============================================================================

export class AuditPreparer extends BaseAgent {
  private packages: Map<string, AuditPackage> = new Map();

  constructor(signingKey: string = randomBytes(32).toString("hex")) {
    super(
      "audit-preparer",
      "Audit Preparation Agent",
      "1.0.0",
      [
        {
          name: "prepare-audit",
          frameworks: ["SOC2", "ISO27001", "NIST_CSF", "PCI_DSS", "HIPAA", "GDPR", "CCPA", "SOX", "FedRAMP", "Custom"],
          confidenceLevel: 0.88,
        },
      ],
      signingKey,
    );
  }

  protected async doExecute(task: SwarmTask): Promise<SwarmResult["output"]> {
    const controlStatuses = (task.input.customParameters?.controlStatuses as ControlStatus[]) ?? [];
    const evidence = (task.input.customParameters?.evidence as EvidenceItem[]) ?? [];
    const auditWindow = task.input.auditWindow;

    const auditPackage = await this.buildAuditPackage(
      task.id,
      task.framework,
      controlStatuses,
      evidence,
      auditWindow,
    );
    this.packages.set(task.id, auditPackage);

    return {
      auditPackage,
      summary: `Audit package assembled for ${auditPackage.frameworks.join(", ")}: ${auditPackage.readinessLevel}. Compliance score: ${(auditPackage.complianceScore * 100).toFixed(1)}%. ${auditPackage.gaps.length} gap(s) identified.`,
      recommendations: this.generateAuditRecommendations(auditPackage),
    };
  }

  // ------------------------------------------------------------------
  // Package building
  // ------------------------------------------------------------------

  private async buildAuditPackage(
    taskId: string,
    framework: ComplianceFramework,
    controlStatuses: ControlStatus[],
    evidence: EvidenceItem[],
    auditWindow?: AuditWindow,
  ): Promise<AuditPackage> {
    const frameworks = auditWindow?.frameworks ?? [framework];
    const period = auditWindow
      ? { from: auditWindow.startDate, to: auditWindow.endDate }
      : { from: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(), to: new Date().toISOString() };

    const sections = this.buildSections(frameworks, controlStatuses, evidence);
    const gaps = this.identifyGaps(controlStatuses);
    const complianceScore = this.calculateComplianceScore(controlStatuses);
    const readinessLevel = this.assessReadiness(complianceScore, gaps);
    const executiveSummary = this.generateExecutiveSummary(frameworks, complianceScore, gaps, controlStatuses);

    return {
      id: `audit-pkg-${randomBytes(8).toString("hex")}`,
      title: `Compliance Audit Package – ${frameworks.join(" + ")}`,
      frameworks,
      period,
      sections,
      executiveSummary,
      complianceScore,
      readinessLevel,
      gaps,
      generatedAt: new Date().toISOString(),
      generatedBy: this.id,
    };
  }

  private buildSections(
    frameworks: ComplianceFramework[],
    controlStatuses: ControlStatus[],
    evidence: EvidenceItem[],
  ): AuditSection[] {
    const sections: AuditSection[] = [];

    for (const framework of frameworks) {
      const frameworkStatuses = controlStatuses.filter((s) => s.framework === framework);
      const frameworkEvidence = evidence.filter((e) => e.framework === framework);

      const controlFamilies = [...new Set(frameworkStatuses.map((s) => this.inferControlFamily(s.controlId)))];

      for (const family of controlFamilies.length > 0 ? controlFamilies : ["General"]) {
        const familyStatuses = frameworkStatuses.filter(
          (s) => this.inferControlFamily(s.controlId) === family,
        );
        const familyEvidence = frameworkEvidence.filter(
          (e) => familyStatuses.some((s) => s.controlId === e.controlId),
        );

        sections.push({
          title: `${framework} – ${family}`,
          framework,
          controlFamily: family,
          narrative: this.generateSectionNarrative(framework, family, familyStatuses),
          evidenceIds: familyEvidence.map((e) => e.id),
          controlStatuses: familyStatuses,
        });
      }
    }

    return sections;
  }

  private generateSectionNarrative(
    framework: ComplianceFramework,
    family: string,
    statuses: ControlStatus[],
  ): string {
    const compliant = statuses.filter((s) => s.status === "compliant").length;
    const nonCompliant = statuses.filter((s) => s.status === "non-compliant").length;
    const partial = statuses.filter((s) => s.status === "partial").length;
    const total = statuses.length;

    if (total === 0) {
      return `No controls assessed for ${framework} ${family} during this audit period.`;
    }

    const complianceRate = compliant / total;

    let assessment: string;
    if (complianceRate >= 0.9) {
      assessment = `${family} controls under ${framework} demonstrate strong compliance posture.`;
    } else if (complianceRate >= 0.7) {
      assessment = `${family} controls under ${framework} show partial compliance with identified gaps requiring attention.`;
    } else {
      assessment = `${family} controls under ${framework} show significant non-compliance requiring immediate remediation.`;
    }

    return `${assessment} Of ${total} controls assessed: ${compliant} compliant, ${nonCompliant} non-compliant, ${partial} partially compliant. Overall family compliance rate: ${(complianceRate * 100).toFixed(1)}%.`;
  }

  private identifyGaps(controlStatuses: ControlStatus[]): AuditGap[] {
    const gaps: AuditGap[] = [];

    for (const status of controlStatuses) {
      if (status.status === "non-compliant" || status.status === "partial") {
        gaps.push({
          controlId: status.controlId,
          framework: status.framework,
          gapDescription: status.status === "non-compliant"
            ? `Control ${status.controlId} is fully non-compliant. ${status.findings.map((f) => f.description).join(" ")}`
            : `Control ${status.controlId} is partially compliant. Implementation gaps remain.`,
          severity: status.status === "non-compliant" ? "critical" : "high",
          remediation: `Implement or complete control ${status.controlId} to satisfy ${status.framework} requirements`,
          estimatedEffort: status.status === "non-compliant" ? "2-4 weeks" : "1-2 weeks",
        });
      }
    }

    return gaps;
  }

  private calculateComplianceScore(controlStatuses: ControlStatus[]): number {
    if (controlStatuses.length === 0) return 0;

    const compliant = controlStatuses.filter((s) => s.status === "compliant").length;
    const partial = controlStatuses.filter((s) => s.status === "partial").length;

    return (compliant + partial * 0.5) / controlStatuses.length;
  }

  private assessReadiness(
    complianceScore: number,
    gaps: AuditGap[],
  ): AuditPackage["readinessLevel"] {
    const criticalGaps = gaps.filter((g) => g.severity === "critical").length;

    if (complianceScore >= 0.95 && criticalGaps === 0) return "ready";
    if (complianceScore >= 0.8 && criticalGaps <= 1) return "mostly-ready";
    if (complianceScore >= 0.5) return "gaps-identified";
    return "not-ready";
  }

  private generateExecutiveSummary(
    frameworks: ComplianceFramework[],
    complianceScore: number,
    gaps: AuditGap[],
    controlStatuses: ControlStatus[],
  ): string {
    const total = controlStatuses.length;
    const compliant = controlStatuses.filter((s) => s.status === "compliant").length;
    const criticalGaps = gaps.filter((g) => g.severity === "critical").length;
    const highGaps = gaps.filter((g) => g.severity === "high").length;

    return (
      `EXECUTIVE SUMMARY\n` +
      `Frameworks: ${frameworks.join(", ")}\n` +
      `Overall Compliance Score: ${(complianceScore * 100).toFixed(1)}%\n` +
      `Total Controls Assessed: ${total}\n` +
      `Controls Compliant: ${compliant}\n` +
      `Gaps Identified: ${gaps.length} (${criticalGaps} critical, ${highGaps} high)\n` +
      `Audit Readiness: ${complianceScore >= 0.95 ? "READY" : complianceScore >= 0.8 ? "MOSTLY READY" : "GAPS EXIST – REMEDIATION REQUIRED"}\n\n` +
      `RECOMMENDATION: ${
        complianceScore >= 0.95
          ? "Proceed with audit engagement. Organization demonstrates sufficient control maturity."
          : complianceScore >= 0.8
            ? "Address identified gaps before audit engagement to improve readiness."
            : "Significant remediation required before audit readiness. Prioritize critical gaps."
      }`
    );
  }

  private generateAuditRecommendations(auditPackage: AuditPackage): string[] {
    const recs: string[] = [];

    switch (auditPackage.readinessLevel) {
      case "ready":
        recs.push("Organization is audit-ready – schedule external audit engagement");
        recs.push("Maintain current control posture through continuous monitoring");
        break;
      case "mostly-ready":
        recs.push(`${auditPackage.gaps.length} gap(s) to close before audit – prioritize critical gaps`);
        recs.push("Conduct internal pre-audit review focusing on partial-compliance areas");
        break;
      case "gaps-identified":
        recs.push(`${auditPackage.gaps.length} gap(s) identified – remediation required before audit`);
        recs.push("Create remediation plan with target completion before audit window");
        recs.push("Consider engaging external consultants for complex gap remediation");
        break;
      case "not-ready":
        recs.push("Organization is NOT audit-ready – comprehensive remediation program required");
        recs.push("Develop 90-day remediation roadmap addressing all critical gaps");
        recs.push("Engage executive leadership to allocate resources for compliance program");
        break;
    }

    const criticalGaps = auditPackage.gaps.filter((g) => g.severity === "critical");
    if (criticalGaps.length > 0) {
      recs.push(`${criticalGaps.length} critical gap(s) require immediate attention: ${criticalGaps.map((g) => g.controlId).join(", ")}`);
    }

    return recs;
  }

  private inferControlFamily(controlId: string): string {
    const prefix = controlId.split(".")[0];
    const families: Record<string, string> = {
      CC1: "Control Environment",
      CC2: "Communication and Information",
      CC3: "Risk Assessment",
      CC4: "Monitoring Activities",
      CC5: "Control Activities",
      CC6: "Logical and Physical Access Controls",
      CC7: "System Operations",
      CC8: "Change Management",
      CC9: "Risk Mitigation",
      A5: "Organizational Controls",
      A6: "People Controls",
      A7: "Physical Controls",
      A8: "Technological Controls",
      PR: "Protect",
      DE: "Detect",
      RS: "Respond",
      RC: "Recover",
      ID: "Identify",
    };
    return families[prefix] ?? "General";
  }

  getAuditPackage(taskId: string): AuditPackage | undefined {
    return this.packages.get(taskId);
  }
}
