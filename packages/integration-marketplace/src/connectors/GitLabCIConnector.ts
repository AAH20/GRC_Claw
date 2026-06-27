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
    id: "gitlabci-pipelines",
    name: "CI Pipelines",
    description: "Fetch GitLab CI/CD pipeline definitions, stages, and run history",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "gitlabci-artifacts",
    name: "Build Artifacts",
    description: "Fetch pipeline artifact configurations and retention policies",
    evidenceCategories: ["data_protection", "configuration"],
  },
  {
    id: "gitlabci-secrets",
    name: "CI/CD Variables",
    description: "Fetch protected variables and secret management in pipelines",
    evidenceCategories: ["secret_management", "access_control"],
  },
];

export class GitLabCIConnector implements IntegrationConnector {
  readonly id = "gitlab-ci";
  readonly name = "GitLab CI/CD";
  readonly category = "ci_cd" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const project = config.extra?.project || "default%2Fproject";
    const base = config.baseUrl || "https://gitlab.com/api/v4";
    const resp = await fetch(`${base}/projects/${project}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`GitLab CI API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const pipelines = await this.fetchApi(config, "/pipelines?per_page=100").catch(() => []);
    const pipelineList = Array.isArray(pipelines) ? pipelines : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gitlabci-pipelines",
      timestamp: now,
      hash: hashEvidence({ pipelineCount: pipelineList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "gitlab-ci/pipelines",
      status: "unknown",
      data: { pipelineCount: pipelineList.length },
      metadata: {},
    });

    return artifacts;
  }
}
