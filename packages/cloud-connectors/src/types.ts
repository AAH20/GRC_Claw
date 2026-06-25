export type CloudProvider = "aws" | "azure" | "gcp";
export type ConnectorStatus = "connected" | "disconnected" | "error" | "syncing";

export interface CloudConnectorConfig {
  provider: CloudProvider;
  credentials: CloudCredentials;
  regions: string[];
  services: string[];
  syncIntervalMs: number;
}

export interface CloudCredentials {
  accessKey?: string;
  secretKey?: string;
  tenantId?: string;
  clientId?: string;
  clientSecret?: string;
  projectId?: string;
  keyFile?: string;
}

export interface CloudFinding {
  id: string;
  provider: CloudProvider;
  service: string;
  severity: "critical" | "high" | "medium" | "low" | "informational";
  title: string;
  description: string;
  resourceId: string;
  resourceType: string;
  region: string;
  complianceControl?: string;
  remediation?: string;
  detectedAt: string;
  metadata: Record<string, unknown>;
}

export interface ConnectorHealth {
  provider: CloudProvider;
  status: ConnectorStatus;
  lastSyncAt?: string;
  findingCount: number;
  errorCount: number;
  nextSyncAt?: string;
}

export interface CloudConnector {
  provider: CloudProvider;
  health(): Promise<ConnectorHealth>;
  fetchFindings(): Promise<CloudFinding[]>;
  testConnection(): Promise<boolean>;
}

export interface ConnectorRegistry {
  register(connector: CloudConnector): void;
  get(provider: CloudProvider): CloudConnector | undefined;
  list(): CloudConnector[];
}
