import { randomUUID, createHash } from "node:crypto";
import type {
  EvidenceItem,
  ComplianceFramework,
  SystemAdapter,
  LoggingEvidence,
} from "../types.js";

export class LoggingCollector {
  private adapter: SystemAdapter;

  constructor(adapter: SystemAdapter) {
    this.adapter = adapter;
  }

  async collect(
    framework: ComplianceFramework,
    controlId: string
  ): Promise<EvidenceItem> {
    const data = await this.adapter.queryLogging();
    const evidenceData = {
      enabled: data.enabled,
      logTypes: data.logTypes,
      retentionDays: data.retentionDays,
      alertingEnabled: data.alertingEnabled,
      lastConfiguredAt: data.lastConfiguredAt,
      hasAuditLogs: data.logTypes.includes("audit"),
      hasSecurityLogs: data.logTypes.includes("security"),
    };

    return {
      id: randomUUID(),
      category: "logging",
      controlId,
      framework,
      source: "logging-api",
      timestamp: new Date().toISOString(),
      hash: this.computeHash(evidenceData),
      data: evidenceData,
      status: this.determineStatus(data),
    };
  }

  private computeHash(data: Record<string, unknown>): string {
    const payload = JSON.stringify(data);
    const hash = createHash("sha256").update(payload).digest("hex");
    return `sha256:${hash}`;
  }

  private determineStatus(
    data: LoggingEvidence
  ): "compliant" | "non_compliant" | "partial" | "unknown" {
    if (!data.enabled) return "non_compliant";
    if (data.retentionDays < 90) return "non_compliant";
    const hasAudit = data.logTypes.includes("audit");
    const hasSecurity = data.logTypes.includes("security");
    if (hasAudit && hasSecurity && data.alertingEnabled && data.retentionDays >= 365)
      return "compliant";
    if (hasAudit || hasSecurity) return "partial";
    return "non_compliant";
  }
}
