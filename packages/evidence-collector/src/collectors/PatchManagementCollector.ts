import { randomUUID, createHash } from "node:crypto";
import type {
  EvidenceItem,
  ComplianceFramework,
  SystemAdapter,
  PatchEvidence,
} from "../types.js";

export class PatchManagementCollector {
  private adapter: SystemAdapter;

  constructor(adapter: SystemAdapter) {
    this.adapter = adapter;
  }

  async collect(
    framework: ComplianceFramework,
    controlId: string
  ): Promise<EvidenceItem> {
    const data = await this.adapter.queryPatchManagement();
    const daysSincePatch = Math.floor(
      (Date.now() - new Date(data.lastPatchDate).getTime()) / (1000 * 60 * 60 * 24)
    );
    const evidenceData = {
      lastPatchDate: data.lastPatchDate,
      daysSinceLastPatch: daysSincePatch,
      pendingPatches: data.pendingPatches,
      criticalPatches: data.criticalPatches,
      autoUpdateEnabled: data.autoUpdateEnabled,
      details: data.details,
    };

    return {
      id: randomUUID(),
      category: "patch_management",
      controlId,
      framework,
      source: "patch-api",
      timestamp: new Date().toISOString(),
      hash: this.computeHash(evidenceData),
      data: evidenceData,
      status: this.determineStatus(data, daysSincePatch),
    };
  }

  private computeHash(data: Record<string, unknown>): string {
    const payload = JSON.stringify(data);
    const hash = createHash("sha256").update(payload).digest("hex");
    return `sha256:${hash}`;
  }

  private determineStatus(
    data: PatchEvidence,
    daysSincePatch: number
  ): "compliant" | "non_compliant" | "partial" | "unknown" {
    if (data.criticalPatches > 0) return "non_compliant";
    if (daysSincePatch > 30) return "non_compliant";
    if (data.autoUpdateEnabled && daysSincePatch <= 14) return "compliant";
    if (daysSincePatch <= 30) return "partial";
    return "non_compliant";
  }
}
