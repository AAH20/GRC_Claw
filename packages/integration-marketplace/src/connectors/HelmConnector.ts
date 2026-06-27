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
    id: "helm-releases",
    name: "Helm Releases",
    description: "Fetch Helm release status, revisions, and values",
    evidenceCategories: ["change_management", "configuration"],
  },
  {
    id: "helm-repositories",
    name: "Chart Repositories",
    description: "Fetch configured chart repositories and access controls",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "helm-values",
    name: "Values Security",
    description: "Fetch Helm values for sensitive configuration detection",
    evidenceCategories: ["data_protection", "configuration"],
  },
  {
    id: "helm-history",
    name: "Release History",
    description: "Fetch release rollback history and upgrade patterns",
    evidenceCategories: ["change_management", "monitoring"],
  },
];

export class HelmConnector implements IntegrationConnector {
  readonly id = "helm";
  readonly name = "Helm";
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
    const base = config.baseUrl || "https://helm.example.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Helm API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/api/releases");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const ns = config.extra?.namespace || "default";

    const releases = await this.fetchApi(
      config,
      `/api/releases?namespace=${ns}`
    ).catch(() => ({ releases: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "helm-releases",
      timestamp: now,
      hash: hashEvidence(releases),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `helm/${ns}/releases`,
      status: (releases.releases as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { releaseCount: (releases.releases as unknown[])?.length || 0 },
      metadata: { namespace: ns },
    });

    const repos = await this.fetchApi(config, "/api/repositories").catch(() => ({ repositories: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "helm-repositories",
      timestamp: now,
      hash: hashEvidence(repos),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "helm/repositories",
      status: (repos.repositories as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { repositoryCount: (repos.repositories as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
