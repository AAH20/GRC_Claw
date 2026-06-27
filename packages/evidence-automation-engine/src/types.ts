import { createHash, randomUUID } from "node:crypto";

export type ComplianceFramework =
  | "SOC2"
  | "ISO27001"
  | "NIST_CSF"
  | "HIPAA"
  | "PCI_DSS"
  | "GDPR"
  | "CIS";

export type ScheduleFrequency =
  | "hourly"
  | "daily"
  | "weekly"
  | "monthly"
  | "quarterly";

export type JobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type EvidenceFreshness =
  | "fresh"
  | "stale"
  | "expired"
  | "missing";

export interface ScheduleConfig {
  frequency: ScheduleFrequency;
  interval?: number;
  dayOfWeek?: number;
  dayOfMonth?: number;
  hourOfDay?: number;
  timezone?: string;
}

export interface EvidenceArtifact {
  id: string;
  connectorId: string;
  capabilityId: string;
  timestamp: string;
  hash: string;
  framework: ComplianceFramework;
  controlId: string;
  source: string;
  status: "compliant" | "non_compliant" | "partial" | "unknown";
  data: Record<string, unknown>;
  metadata: Record<string, string>;
  expiresAt?: string;
}

export interface EvidenceStore {
  artifacts: Map<string, EvidenceArtifact>;
  add(artifact: EvidenceArtifact): void;
  get(id: string): EvidenceArtifact | undefined;
  getAll(): EvidenceArtifact[];
  getByConnector(connectorId: string): EvidenceArtifact[];
  getByControl(controlId: string): EvidenceArtifact[];
  getByFramework(framework: ComplianceFramework): EvidenceArtifact[];
  remove(id: string): boolean;
  size: number;
}

export interface CollectionSchedule {
  id: string;
  connectorId: string;
  config: ScheduleConfig;
  enabled: boolean;
  lastRunAt?: string;
  nextRunAt?: string;
  lastJobId?: string;
}

export interface CollectionJob {
  id: string;
  connectorId: string;
  scheduleId?: string;
  startedAt: string;
  completedAt?: string;
  status: JobStatus;
  artifacts: EvidenceArtifact[];
  error?: string;
  duration?: number;
}

export interface EvidenceGap {
  controlId: string;
  framework: ComplianceFramework;
  requiredBy: string[];
  lastCollectedAt?: string;
  freshness: EvidenceFreshness;
  connectors: string[];
  recommendation: string;
}

export interface EvidenceSummaryReport {
  generatedAt: string;
  totalArtifacts: number;
  artifactsByFramework: Record<ComplianceFramework, number>;
  artifactsByStatus: Record<string, number>;
  gaps: EvidenceGap[];
  totalGaps: number;
  freshness: {
    fresh: number;
    stale: number;
    expired: number;
    missing: number;
  };
  coveragePercentage: number;
}

export function hashData(data: Record<string, unknown>): string {
  const payload = JSON.stringify(data, Object.keys(data).sort());
  return `sha256:${createHash("sha256").update(payload).digest("hex")}`;
}

export function generateId(prefix: string): string {
  return `${prefix}-${randomUUID()}`;
}

export function computeNextRun(
  config: ScheduleConfig,
  lastRun?: string
): string {
  const now = new Date();
  const base = lastRun ? new Date(lastRun) : now;
  const next = new Date(base);

  switch (config.frequency) {
    case "hourly":
      next.setHours(next.getHours() + (config.interval || 1));
      break;
    case "daily":
      next.setDate(next.getDate() + (config.interval || 1));
      next.setHours(config.hourOfDay ?? 9, 0, 0, 0);
      break;
    case "weekly":
      next.setDate(next.getDate() + 7 * (config.interval || 1));
      next.setHours(config.hourOfDay ?? 9, 0, 0, 0);
      break;
    case "monthly":
      next.setMonth(next.getMonth() + (config.interval || 1));
      next.setDate(config.dayOfMonth ?? 1);
      next.setHours(config.hourOfDay ?? 9, 0, 0, 0);
      break;
    case "quarterly":
      next.setMonth(next.getMonth() + 3 * (config.interval || 1));
      next.setDate(config.dayOfMonth ?? 1);
      next.setHours(config.hourOfDay ?? 9, 0, 0, 0);
      break;
  }

  if (next <= now) return now.toISOString();
  return next.toISOString();
}

export function assessFreshness(
  artifact: EvidenceArtifact,
  maxAgeHours: number = 24 * 30
): EvidenceFreshness {
  if (!artifact.timestamp) return "missing";
  const age = Date.now() - new Date(artifact.timestamp).getTime();
  const maxAgeMs = maxAgeHours * 60 * 60 * 1000;
  if (age <= maxAgeMs * 0.5) return "fresh";
  if (age <= maxAgeMs) return "stale";
  return "expired";
}

export function getControlFrameworkMap(): Record<string, ComplianceFramework[]> {
  return {
    "CC6.1": ["SOC2"],
    "CC6.2": ["SOC2"],
    "CC6.3": ["SOC2"],
    "CC6.4": ["SOC2"],
    "CC6.6": ["SOC2"],
    "CC6.8": ["SOC2"],
    "CC7.1": ["SOC2"],
    "CC7.2": ["SOC2"],
    "CC7.3": ["SOC2"],
    "CC8.1": ["SOC2"],
    "A.9.2.5": ["ISO27001"],
    "A.9.4.1": ["ISO27001"],
    "A.10.1.1": ["ISO27001"],
    "A.12.1.4": ["ISO27001"],
    "A.12.3.1": ["ISO27001"],
    "A.12.4.1": ["ISO27001"],
    "A.12.6.1": ["ISO27001"],
    "A.13.1.1": ["ISO27001"],
    "A.14.2.1": ["ISO27001"],
    "A.14.2.5": ["ISO27001"],
    "A.16.1.4": ["ISO27001"],
    "A.18.1.5": ["ISO27001"],
    "PR.AC": ["NIST_CSF"],
    "PR.DS": ["NIST_CSF"],
    "DE.CM": ["NIST_CSF"],
    "RS.AN": ["NIST_CSF"],
  };
}
