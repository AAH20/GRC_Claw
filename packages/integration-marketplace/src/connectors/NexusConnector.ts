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
    id: "nexus-repos",
    name: "Repository Management",
    description: "Fetch repository configurations and proxy settings",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "nexus-components",
    name: "Component Security",
    description: "Fetch component vulnerability and license data",
    evidenceCategories: ["vulnerability_management", "data_protection"],
  },
  {
    id: "nexus-roles",
    name: "Role-Based Access",
    description: "Fetch roles, privileges, and user assignments",
    evidenceCategories: ["access_control"],
  },
  {
    id: "nexus-audit",
    name: "Task & Audit Logs",
    description: "Fetch scheduled tasks and access audit logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class NexusConnector implements IntegrationConnector {
  readonly id = "nexus";
  readonly name = "Sonatype Nexus";
  readonly category = "ci_cd" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://nexus.example.com";
    const resp = await fetch(`${base}/service/rest${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Nexus API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/v1/status");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const repos = await this.fetchApi(config, "/v1/repositories").catch(() => []);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "nexus-repos",
      timestamp: now,
      hash: hashEvidence(Array.isArray(repos) ? { count: repos.length } : repos as Record<string, unknown>),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "nexus/repositories",
      status: Array.isArray(repos) && repos.length > 0 ? "compliant" : "unknown",
      data: { repositoryCount: Array.isArray(repos) ? repos.length : 0 },
      metadata: {},
    });

    const roles = await this.fetchApi(config, "/v1/roles").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "nexus-roles",
      timestamp: now,
      hash: hashEvidence(roles),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "nexus/roles",
      status: (roles.items as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { roleCount: (roles.items as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
