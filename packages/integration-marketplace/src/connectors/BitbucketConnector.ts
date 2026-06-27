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
    id: "bitbucket-repos",
    name: "Repository Settings",
    description: "Fetch repo access controls and branch permissions",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "bitbucket-pipelines",
    name: "Pipelines",
    description: "Fetch CI/CD pipeline configurations and run history",
    evidenceCategories: ["change_management", "configuration"],
  },
  {
    id: "bitbucket-code-insight",
    name: "Code Insights",
    description: "Fetch code quality and security scan results",
    evidenceCategories: ["vulnerability_management", "change_management"],
  },
  {
    id: "bitbucket-ip-allow",
    name: "IP Allowlisting",
    description: "Fetch IP allowlist configurations for workspace",
    evidenceCategories: ["access_control", "configuration"],
  },
];

export class BitbucketConnector implements IntegrationConnector {
  readonly id = "bitbucket";
  readonly name = "Bitbucket";
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
    const base = config.baseUrl || "https://api.bitbucket.org/2.0";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Bitbucket API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/user");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const workspace = config.extra?.workspace || "default";
    const repoSlug = config.extra?.repo || "main-repo";

    const repo = await this.fetchApi(config, `/repositories/${workspace}/${repoSlug}`).catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "bitbucket-repos",
      timestamp: now,
      hash: hashEvidence(repo as Record<string, unknown>),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `bitbucket.org/${workspace}/${repoSlug}`,
      status: (repo as Record<string, unknown>).is_private === true ? "compliant" : "partial",
      data: {
        isPrivate: (repo as Record<string, unknown>).is_private,
        defaultBranch: (repo as Record<string, unknown>).default_branch,
        hasIssues: (repo as Record<string, unknown>).has_issues,
      },
      metadata: { workspace, repoSlug },
    });

    const pipelines = await this.fetchApi(
      config,
      `/repositories/${workspace}/${repoSlug}/pipelines/?max_length=10`
    ).catch(() => ({ values: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "bitbucket-pipelines",
      timestamp: now,
      hash: hashEvidence(pipelines),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `bitbucket.org/${workspace}/${repoSlug}/pipelines`,
      status: "partial",
      data: { recentPipelines: (pipelines.values as unknown[])?.length || 0 },
      metadata: { workspace, repoSlug },
    });

    return artifacts;
  }
}
