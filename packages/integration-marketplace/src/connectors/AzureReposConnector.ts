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
    id: "azure-repos-policies",
    name: "Repository Policies",
    description: "Fetch branch policies and merge strategies",
    evidenceCategories: ["access_control", "change_management"],
  },
  {
    id: "azure-repos-builds",
    name: "Build Definitions",
    description: "Fetch CI/CD build pipeline configurations",
    evidenceCategories: ["change_management", "configuration"],
  },
  {
    id: "azure-repos-pr",
    name: "Pull Request Policies",
    description: "Fetch PR approval requirements and work item linking",
    evidenceCategories: ["change_management", "access_control"],
  },
  {
    id: "azure-repos-audit",
    name: "Audit Events",
    description: "Fetch repository audit log events",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class AzureReposConnector implements IntegrationConnector {
  readonly id = "azure-repos";
  readonly name = "Azure Repos";
  readonly category = "version_control" as const;
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
    const org = config.extra?.org || "default";
    const base = config.baseUrl || `https://dev.azure.com/${org}`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Basic ${Buffer.from(`:${config.apiToken}`).toString("base64")}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Azure Repos API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/_apis/projects?api-version=7.0");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const project = config.extra?.project || "default";

    const repos = await this.fetchApi(
      config,
      `/${project}/_apis/git/repositories?api-version=7.0`
    ).catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "azure-repos-policies",
      timestamp: now,
      hash: hashEvidence(repos),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `dev.azure.com/${project}/repositories`,
      status: (repos.value as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { repositoryCount: (repos.value as unknown[])?.length || 0 },
      metadata: { project },
    });

    const builds = await this.fetchApi(
      config,
      `/${project}/_apis/build/builds?top=10&api-version=7.0`
    ).catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "azure-repos-builds",
      timestamp: now,
      hash: hashEvidence(builds),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `dev.azure.com/${project}/builds`,
      status: "partial",
      data: { recentBuilds: (builds.value as unknown[])?.length || 0 },
      metadata: { project },
    });

    return artifacts;
  }
}
