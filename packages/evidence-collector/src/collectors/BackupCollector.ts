import { randomUUID, createHash } from "node:crypto";
import type {
  EvidenceItem,
  ComplianceFramework,
  SystemAdapter,
  BackupEvidence,
} from "../types.js";

export class BackupCollector {
  private adapter: SystemAdapter;

  constructor(adapter: SystemAdapter) {
    this.adapter = adapter;
  }

  async collect(
    framework: ComplianceFramework,
    controlId: string
  ): Promise<EvidenceItem> {
    const data = await this.adapter.queryBackup();
    const evidenceData = {
      configured: data.configured,
      frequency: data.frequency,
      lastBackupAt: data.lastBackupAt,
      retentionDays: data.retentionDays,
      testedAt: data.testedAt,
      testPassed: data.testPassed,
      daysSinceLastBackup: data.lastBackupAt
        ? Math.floor(
            (Date.now() - new Date(data.lastBackupAt).getTime()) /
              (1000 * 60 * 60 * 24)
          )
        : null,
    };

    return {
      id: randomUUID(),
      category: "backup",
      controlId,
      framework,
      source: "backup-api",
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
    data: BackupEvidence
  ): "compliant" | "non_compliant" | "partial" | "unknown" {
    if (!data.configured) return "non_compliant";
    if (!data.testPassed) return "non_compliant";
    if (data.retentionDays < 30) return "partial";
    if (data.configured && data.testPassed && data.retentionDays >= 90)
      return "compliant";
    return "partial";
  }
}
