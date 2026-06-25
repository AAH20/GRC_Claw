export type CloudProvider = "aws" | "azure" | "gcp" | "github" | "okta" | "cloudflare";
export type EvidenceType = "configuration" | "policy" | "log" | "certificate" | "assessment" | "screenshot";
export type CollectorStatus = "idle" | "collecting" | "completed" | "error";

export interface EvidenceCollector {
  id: string;
  provider: CloudProvider;
  resourceType: string;
  controlId: string;
  status: CollectorStatus;
  lastCollectedAt?: string;
  schedule: string;
  evidence: CollectedEvidence[];
}

export interface CollectedEvidence {
  id: string;
  collectorId: string;
  type: EvidenceType;
  name: string;
  content: string;
  sha256: string;
  collectedAt: string;
  metadata: Record<string, unknown>;
}

export interface CloudIntegration {
  provider: CloudProvider;
  connected: boolean;
  accountId: string;
  regions: string[];
  lastSyncAt?: string;
  collectors: EvidenceCollector[];
}

export interface EvidenceInventory {
  totalEvidence: number;
  byProvider: Record<CloudProvider, number>;
  byType: Record<EvidenceType, number>;
  staleEvidence: number;
  coverage: number;
}

export interface CollectorTemplate {
  provider: CloudProvider;
  resourceType: string;
  controlId: string;
  name: string;
  description: string;
  apiCall: string;
}
