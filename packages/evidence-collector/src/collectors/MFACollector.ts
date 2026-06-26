import { randomUUID, createHash } from "node:crypto";
import type {
  EvidenceItem,
  ComplianceFramework,
  SystemAdapter,
  MFAEvidence,
} from "../types.js";

export class MFACollector {
  private adapter: SystemAdapter;

  constructor(adapter: SystemAdapter) {
    this.adapter = adapter;
  }

  async collect(
    framework: ComplianceFramework,
    controlId: string
  ): Promise<EvidenceItem> {
    const mfaData = await this.adapter.queryMFA();
    const evidenceData = {
      enforced: mfaData.enforced,
      totalUsers: mfaData.totalUsers,
      mfaEnabledUsers: mfaData.mfaEnabledUsers,
      methods: mfaData.methods,
      lastEnforcedAt: mfaData.lastEnforcedAt,
      compliancePercentage:
        mfaData.totalUsers > 0
          ? Math.round((mfaData.mfaEnabledUsers / mfaData.totalUsers) * 100)
          : 0,
    };

    return {
      id: randomUUID(),
      category: "mfa",
      controlId,
      framework,
      source: "idp-api",
      timestamp: new Date().toISOString(),
      hash: this.computeHash(evidenceData),
      data: evidenceData,
      status: this.determineStatus(mfaData),
    };
  }

  private computeHash(data: Record<string, unknown>): string {
    const payload = JSON.stringify(data);
    const hash = createHash("sha256").update(payload).digest("hex");
    return `sha256:${hash}`;
  }

  private determineStatus(
    data: MFAEvidence
  ): "compliant" | "non_compliant" | "partial" | "unknown" {
    if (!data.enforced) return "non_compliant";
    if (data.totalUsers === 0) return "unknown";
    const ratio = data.mfaEnabledUsers / data.totalUsers;
    if (ratio >= 0.95) return "compliant";
    if (ratio >= 0.8) return "partial";
    return "non_compliant";
  }
}
