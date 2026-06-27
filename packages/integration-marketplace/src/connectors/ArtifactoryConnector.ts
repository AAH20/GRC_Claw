import type {
  IntegrationConnector,
  ConnectorConfig,
  EvidenceArtifact,
  IntegrationCapability,
  ComplianceFramework,
} from "../types.js";
import { hashEvidence, generateEvidenceId } from "../types.js";

const capabilities: IntegrationCapability[] = [
  {
    id: "artifactory-repos",
    name: "Repository Management",
    description: "Fetch repository types, permissions, and replication settings",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "artifactory-artifacts",
    name: "Artifact Security",
    description: "Fetch artifact scan results and checksum verification",
    evidenceCategories: ["data_protection", "vulnerability_management"],
  },
  {
    id: "artifactory-audit",
    name: "Access Audit",
    description: "Fetch artifact access logs and user activity",
    evidenceCategories: ["monitoring", "access_control"],
  },
  {
    id: "artifactory-licenses",
    name: "License Compliance",
    description: "Fetch license policy violations and component analysis",
    evidenceCategories: ["compliance", "vulnerability_management"],
  },
];

export class ArtifactoryConnector implements IntegrationConnector {
  readonly id = "artifactory";
  readonly name = "JFrog Artifactory";
  readonly category = "ci_cd" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://artifactory.example.com";
    const resp = await fetch(`${base}/artifactory/api${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Artifactory API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/system/ping");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const repos = await this.fetchApi(config, "/repositories?type=local").catch(() => []);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "artifactory-repos",
      timestamp: now,
      hash: hashEvidence(Array.isArray(repos) ? { count: repos.length } : repos as Record<string, unknown>),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "artifactory/repositories",
      status: Array.isArray(repos) && repos.length > 0 ? "compliant" : "unknown",
      data: { repositoryCount: Array.isArray(repos) ? repos.length : 0 },
      metadata: {},
    });

    const storage = await this.fetchApi(config, "/storage").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "artifactory-artifacts",
      timestamp: now,
      hash: hashEvidence(storage),
      framework: "ISO27001",
      controlId: "A.8.3.1",
      source: "artifactory/storage",
      status: "partial",
      data: storage as Record<string, unknown>,
      metadata: {},
    });

    return artifacts;
  }
}
