import {
  MFACollector,
  EncryptionCollector,
  AccessControlCollector,
  LoggingCollector,
  PatchManagementCollector,
  NetworkSecurityCollector,
  BackupCollector,
} from "./collectors/index.js";
import type {
  EvidenceItem,
  EvidenceCategory,
  ComplianceFramework,
  SystemAdapter,
  CollectorStatus,
} from "./types.js";

export interface EvidenceCollectionRequest {
  category: EvidenceCategory;
  framework: ComplianceFramework;
  controlId: string;
}

export interface EvidenceCollectionResult {
  items: EvidenceItem[];
  status: CollectorStatus;
  collectedAt: string;
  errors: string[];
}

export class EvidenceCollectorEngine {
  private adapter: SystemAdapter;
  private mfaCollector: MFACollector;
  private encryptionCollector: EncryptionCollector;
  private accessControlCollector: AccessControlCollector;
  private loggingCollector: LoggingCollector;
  private patchCollector: PatchManagementCollector;
  private networkCollector: NetworkSecurityCollector;
  private backupCollector: BackupCollector;
  private evidenceStore: Map<string, EvidenceItem> = new Map();

  constructor(adapter: SystemAdapter) {
    this.adapter = adapter;
    this.mfaCollector = new MFACollector(adapter);
    this.encryptionCollector = new EncryptionCollector(adapter);
    this.accessControlCollector = new AccessControlCollector(adapter);
    this.loggingCollector = new LoggingCollector(adapter);
    this.patchCollector = new PatchManagementCollector(adapter);
    this.networkCollector = new NetworkSecurityCollector(adapter);
    this.backupCollector = new BackupCollector(adapter);
  }

  async collect(
    requests: EvidenceCollectionRequest[]
  ): Promise<EvidenceCollectionResult> {
    const items: EvidenceItem[] = [];
    const errors: string[] = [];

    for (const request of requests) {
      try {
        const item = await this.collectSingle(request);
        items.push(item);
        this.evidenceStore.set(item.id, item);
      } catch (err) {
        errors.push(
          `Failed to collect ${request.category} for ${request.controlId}: ${
            err instanceof Error ? err.message : String(err)
          }`
        );
      }
    }

    return {
      items,
      status: errors.length > 0 ? (items.length > 0 ? "completed" : "error") : "completed",
      collectedAt: new Date().toISOString(),
      errors,
    };
  }

  async collectSingle(
    request: EvidenceCollectionRequest
  ): Promise<EvidenceItem> {
    const { category, framework, controlId } = request;

    switch (category) {
      case "mfa":
        return this.mfaCollector.collect(framework, controlId);
      case "encryption":
        return this.encryptionCollector.collectAtRest(framework, controlId);
      case "access_control":
        return this.accessControlCollector.collect(framework, controlId);
      case "logging":
        return this.loggingCollector.collect(framework, controlId);
      case "patch_management":
        return this.patchCollector.collect(framework, controlId);
      case "network_security":
        return this.networkCollector.collect(framework, controlId);
      case "backup":
        return this.backupCollector.collect(framework, controlId);
      default:
        throw new Error(`Unknown evidence category: ${category}`);
    }
  }

  getEvidence(id: string): EvidenceItem | undefined {
    return this.evidenceStore.get(id);
  }

  getAllEvidence(): EvidenceItem[] {
    return Array.from(this.evidenceStore.values());
  }

  getEvidenceByFramework(
    framework: ComplianceFramework
  ): EvidenceItem[] {
    return this.getAllEvidence().filter((e) => e.framework === framework);
  }

  getEvidenceByCategory(
    category: EvidenceCategory
  ): EvidenceItem[] {
    return this.getAllEvidence().filter((e) => e.category === category);
  }

  getComplianceSummary(
    framework: ComplianceFramework
  ): {
    total: number;
    compliant: number;
    nonCompliant: number;
    partial: number;
    unknown: number;
    compliancePercentage: number;
  } {
    const evidence = this.getEvidenceByFramework(framework);
    const compliant = evidence.filter((e) => e.status === "compliant").length;
    const nonCompliant = evidence.filter((e) => e.status === "non_compliant").length;
    const partial = evidence.filter((e) => e.status === "partial").length;
    const unknown = evidence.filter((e) => e.status === "unknown").length;

    return {
      total: evidence.length,
      compliant,
      nonCompliant,
      partial,
      unknown,
      compliancePercentage:
        evidence.length > 0
          ? Math.round((compliant / evidence.length) * 100)
          : 0,
    };
  }

  clearEvidence(): void {
    this.evidenceStore.clear();
  }
}
