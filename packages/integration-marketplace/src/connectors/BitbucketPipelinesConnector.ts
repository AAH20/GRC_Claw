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
    id: "bitbucket-pipelines-config",
    name: "Pipeline Configuration",
    description: "Fetch Bitbucket Pipelines YAML configurations and default branches",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "bitbucket-pipelines-runs",
    name: "Pipeline Runs",
    description: "Fetch pipeline execution history and failure rates",
    evidenceCategories: ["ci_cd", "monitoring"],
  },
  {
    id: "bitbucket-pipelines-deployments",
    name: "Deployment Environments",
    description: "Fetch deployment environment configurations and approval rules",
    evidenceCategories: ["access_control", "change_management"],
  },
];

export class BitbucketPipelinesConnector implements IntegrationConnector {
  readonly id = "bitbucket-pipelines";
  readonly name = "Bitbucket Pipelines";
  readonly category = "ci_cd" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const workspace = config.extra?.workspace || "default";
    const repo = config.extra?.repo || "main-repo";
    const base = config.baseUrl || "https://api.bitbucket.org/2.0";
    const resp = await fetch(`${base}/repositories/${workspace}/${repo}${endpoint}`, {
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
      await this.fetchApi(config, "");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const pipelines = await this.fetchApi(config, "/pipelines/?pagelen=100").catch(() => ({ values: [] }));
    const pipelineList = (pipelines.values || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "bitbucket-pipelines-runs",
      timestamp: now,
      hash: hashEvidence({ runCount: pipelineList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "bitbucket-pipelines/runs",
      status: "unknown",
      data: { pipelineRunCount: pipelineList.length },
      metadata: {},
    });

    return artifacts;
  }
}
