import { randomUUID, createHash } from "node:crypto";
import type {
  EvidenceItem,
  ComplianceFramework,
  SystemAdapter,
  NetworkSecurityEvidence,
} from "../types.js";

export class NetworkSecurityCollector {
  private adapter: SystemAdapter;

  constructor(adapter: SystemAdapter) {
    this.adapter = adapter;
  }

  async collect(
    framework: ComplianceFramework,
    controlId: string
  ): Promise<EvidenceItem> {
    const data = await this.adapter.queryNetworkSecurity();
    const evidenceData = {
      firewallEnabled: data.firewallEnabled,
      segmentationEnabled: data.segmentationEnabled,
      totalRules: data.totalRules,
      openPorts: data.openPorts,
      lastAuditAt: data.lastAuditAt,
    };

    return {
      id: randomUUID(),
      category: "network_security",
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
    data: NetworkSecurityEvidence
  ): "compliant" | "non_compliant" | "partial" | "unknown" {
    if (!data.firewallEnabled) return "non_compliant";
    if (!data.segmentationEnabled) return "partial";
    if (data.openPorts > 10) return "partial";
    if (data.firewallEnabled && data.segmentationEnabled && data.openPorts <= 5)
      return "compliant";
    return "partial";
  }
}
