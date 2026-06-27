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
    id: "azuredevops-pipelines",
    name: "Build Pipelines",
    description: "Fetch Azure DevOps pipeline definitions and run history",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "azuredevops-releases",
    name: "Release Pipelines",
    description: "Fetch release pipeline configurations and deployment approvals",
    evidenceCategories: ["ci_cd", "access_control"],
  },
  {
    id: "azuredevops-security",
    name: "Pipeline Security",
    description: "Fetch pipeline permissions, service connections, and variable groups",
    evidenceCategories: ["access_control", "secret_management"],
  },
];

export class AzureDevOpsPipelinesConnector implements IntegrationConnector {
  readonly id = "azuredevops-pipelines";
  readonly name = "Azure DevOps Pipelines";
  readonly category = "ci_cd" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const org = config.extra?.org || "default";
    const base = config.baseUrl || `https://dev.azure.com/${org}`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Azure DevOps API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/_apis/projects?api-version=7.0&$top=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const project = config.extra?.project || "default";

    const pipelines = await this.fetchApi(
      config,
      `/${project}/_apis/pipelines?api-version=7.0`
    ).catch(() => ({ value: [] }));
    const pipelineList = (pipelines.value || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "azuredevops-pipelines",
      timestamp: now,
      hash: hashEvidence({ pipelineCount: pipelineList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "azuredevops/pipelines",
      status: pipelineList.length > 0 ? "compliant" : "unknown",
      data: { pipelineCount: pipelineList.length },
      metadata: { project },
    });

    return artifacts;
  }
}
