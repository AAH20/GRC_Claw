import { randomUUID, createHash } from "node:crypto";
import type {
  EvidenceItem,
  ComplianceFramework,
  SystemAdapter,
  EncryptionEvidence,
} from "../types.js";

export class EncryptionCollector {
  private adapter: SystemAdapter;

  constructor(adapter: SystemAdapter) {
    this.adapter = adapter;
  }

  async collectAtRest(
    framework: ComplianceFramework,
    controlId: string
  ): Promise<EvidenceItem> {
    const data = await this.adapter.queryEncryptionAtRest();
    const evidenceData = {
      atRest: true,
      enabled: data.enabled,
      algorithm: data.algorithm,
      keyRotationDays: data.keyRotationDays,
      lastRotatedAt: data.lastRotatedAt,
      details: data.details,
    };

    return {
      id: randomUUID(),
      category: "encryption",
      controlId,
      framework,
      source: "cloud-api",
      timestamp: new Date().toISOString(),
      hash: this.computeHash(evidenceData),
      data: evidenceData,
      status: this.determineStatus(data),
    };
  }

  async collectInTransit(
    framework: ComplianceFramework,
    controlId: string
  ): Promise<EvidenceItem> {
    const data = await this.adapter.queryEncryptionInTransit();
    const evidenceData = {
      inTransit: true,
      enabled: data.enabled,
      algorithm: data.algorithm,
      details: data.details,
    };

    return {
      id: randomUUID(),
      category: "encryption",
      controlId,
      framework,
      source: "network-api",
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
    data: EncryptionEvidence
  ): "compliant" | "non_compliant" | "partial" | "unknown" {
    if (!data.enabled) return "non_compliant";
    if (data.algorithm && data.keyRotationDays) return "compliant";
    if (data.algorithm || data.keyRotationDays) return "partial";
    return "compliant";
  }
}
