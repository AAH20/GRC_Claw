import { randomUUID } from "node:crypto";
import type { Audit, Finding, Workpaper, AuditReport, CAPA, AuditStatus, FindingSeverity } from "../types.js";

export class AuditManager {
  private audits: Map<string, Audit> = new Map();
  private capas: Map<string, CAPA> = new Map();

  createAudit(input: { name: string; type: Audit["type"]; scope: string[]; framework: string; leadAuditor: string; team: string[]; startDate: string; endDate: string }): Audit {
    const audit: Audit = {
      id: randomUUID(),
      name: input.name,
      type: input.type,
      status: "planning",
      scope: input.scope,
      framework: input.framework,
      leadAuditor: input.leadAuditor,
      team: input.team,
      startDate: input.startDate,
      endDate: input.endDate,
      findings: [],
      workpapers: [],
      createdAt: new Date().toISOString(),
    };
    this.audits.set(audit.id, audit);
    return audit;
  }

  getAudit(id: string): Audit | undefined { return this.audits.get(id); }
  listAudits(): Audit[] { return Array.from(this.audits.values()); }

  transitionAudit(id: string, status: AuditStatus): boolean {
    const audit = this.audits.get(id);
    if (!audit) return false;
    audit.status = status;
    return true;
  }

  addFinding(auditId: string, finding: Omit<Finding, "id">): Finding | null {
    const audit = this.audits.get(auditId);
    if (!audit) return null;
    const newFinding: Finding = { ...finding, id: randomUUID() };
    audit.findings.push(newFinding);
    return newFinding;
  }

  addWorkpaper(auditId: string, wp: Omit<Workpaper, "id">): Workpaper | null {
    const audit = this.audits.get(auditId);
    if (!audit) return null;
    const newWp: Workpaper = { ...wp, id: randomUUID() };
    audit.workpapers.push(newWp);
    return newWp;
  }

  generateReport(auditId: string): AuditReport | null {
    const audit = this.audits.get(auditId);
    if (!audit) return null;
    const findings = audit.findings;
    const criticalFindings = findings.filter((f) => f.severity === "critical").length;
    const highFindings = findings.filter((f) => f.severity === "high").length;
    const mediumFindings = findings.filter((f) => f.severity === "medium").length;
    const lowFindings = findings.filter((f) => f.severity === "low").length;

    let opinion: AuditReport["overallOpinion"] = "unqualified";
    if (criticalFindings > 0) opinion = "qualified";
    if (criticalFindings > 3) opinion = "adverse";

    const report: AuditReport = {
      id: randomUUID(),
      executiveSummary: `Audit of ${audit.name} completed. ${findings.length} findings identified.`,
      totalFindings: findings.length,
      criticalFindings,
      highFindings,
      mediumFindings,
      lowFindings,
      overallOpinion: opinion,
      generatedAt: new Date().toISOString(),
    };
    audit.report = report;
    return report;
  }

  createCAPA(findingId: string, type: CAPA["type"], description: string, owner: string, dueDate: string): CAPA {
    const capa: CAPA = { id: randomUUID(), findingId, type, description, owner, dueDate, status: "open" };
    this.capas.set(capa.id, capa);
    return capa;
  }

  getCAPAs(): CAPA[] { return Array.from(this.capas.values()); }

  getAuditStats(auditId: string): { totalFindings: number; bySeverity: Record<FindingSeverity, number>; openFindings: number; closedFindings: number } | null {
    const audit = this.audits.get(auditId);
    if (!audit) return null;
    const findings = audit.findings;
    return {
      totalFindings: findings.length,
      bySeverity: {
        critical: findings.filter((f) => f.severity === "critical").length,
        high: findings.filter((f) => f.severity === "high").length,
        medium: findings.filter((f) => f.severity === "medium").length,
        low: findings.filter((f) => f.severity === "low").length,
      },
      openFindings: findings.filter((f) => f.status === "open").length,
      closedFindings: findings.filter((f) => f.status === "closed").length,
    };
  }
}
