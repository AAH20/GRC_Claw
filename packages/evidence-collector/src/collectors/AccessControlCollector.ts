import { randomUUID, createHash } from "node:crypto";
import type {
  EvidenceItem,
  ComplianceFramework,
  SystemAdapter,
  AccessControlEvidence,
} from "../types.js";

export class AccessControlCollector {
  private adapter: SystemAdapter;

  constructor(adapter: SystemAdapter) {
    this.adapter = adapter;
  }

  async collect(
    framework: ComplianceFramework,
    controlId: string
  ): Promise<EvidenceItem> {
    const data = await this.adapter.queryAccessControl();
    const evidenceData = {
      leastPrivilege: data.leastPrivilege,
      totalRoles: data.totalRoles,
      excessiveRoles: data.excessiveRoles,
      lastAuditAt: data.lastAuditAt,
      excessiveRolePercentage:
        data.totalRoles > 0
          ? Math.round((data.excessiveRoles / data.totalRoles) * 100)
          : 0,
      details: data.details,
    };

    return {
      id: randomUUID(),
      category: "access_control",
      controlId,
      framework,
      source: "iam-api",
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
    data: AccessControlEvidence
  ): "compliant" | "non_compliant" | "partial" | "unknown" {
    if (!data.leastPrivilege) return "non_compliant";
    if (data.excessiveRoles === 0) return "compliant";
    if (data.totalRoles > 0) {
      const ratio = data.excessiveRoles / data.totalRoles;
      if (ratio <= 0.1) return "partial";
    }
    return "non_compliant";
  }
}
