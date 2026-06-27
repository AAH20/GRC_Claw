import { createHash, randomUUID } from "node:crypto";

export type IntegrationCategory =
  | "version_control"
  | "cloud_provider"
  | "identity"
  | "siem"
  | "project_management"
  | "communication"
  | "incident_management"
  | "data_warehouse"
  | "monitoring"
  | "endpoint"
  | "vulnerability"
  | "iac"
  | "ci_cd"
  | "container"
  | "infrastructure"
  | "hr"
  | "documentation"
  | "workspace"
  | "document_management"
  | "file_storage"
  | "finance";

export type AuthType =
  | "api_key"
  | "oauth2"
  | "bearer_token"
  | "basic_auth"
  | "service_account"
  | "webhook";

export type ComplianceFramework =
  | "SOC2"
  | "ISO27001"
  | "NIST_CSF"
  | "HIPAA"
  | "PCI_DSS"
  | "GDPR"
  | "CIS";

export type EvidenceStatus =
  | "compliant"
  | "non_compliant"
  | "partial"
  | "unknown";

export interface IntegrationCapability {
  id: string;
  name: string;
  description: string;
  evidenceCategories: string[];
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
  status: EvidenceStatus;
  data: Record<string, unknown>;
  metadata: Record<string, string>;
}

export interface ConnectorConfig {
  baseUrl?: string;
  apiToken?: string;
  clientId?: string;
  clientSecret?: string;
  tenantId?: string;
  region?: string;
  accountId?: string;
  extra?: Record<string, string>;
}

export interface IntegrationConnector {
  readonly id: string;
  readonly name: string;
  readonly category: IntegrationCategory;
  readonly authType: AuthType;
  readonly capabilities: IntegrationCapability[];
  readonly frameworks: ComplianceFramework[];
  collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]>;
  testConnection(config: ConnectorConfig): Promise<boolean>;
}

export interface MarketplaceStats {
  totalConnectors: number;
  connectorsByCategory: Record<IntegrationCategory, number>;
  totalCapabilities: number;
  frameworksSupported: ComplianceFramework[];
}

export interface ConnectorRegistration {
  connector: IntegrationConnector;
  enabled: boolean;
  lastCollectedAt?: string;
  errorCount: number;
}

export function hashEvidence(data: Record<string, unknown>): string {
  const payload = JSON.stringify(data, Object.keys(data).sort());
  return `sha256:${createHash("sha256").update(payload).digest("hex")}`;
}

export function generateEvidenceId(): string {
  return `ev-${randomUUID()}`;
}
