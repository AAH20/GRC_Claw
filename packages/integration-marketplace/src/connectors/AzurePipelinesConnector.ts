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
    id: "azurepipelines-builds",
    name: "Build Pipelines",
    description: "Fetch Azure Pipelines build definitions and execution history",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "azurepipelines-releases",
    name: "Release Pipelines",
    description: "Fetch release pipeline configurations and approval gates",
    evidenceCategories: ["ci_cd", "access_control"],
  },
  {
    id: "azurepipelines-service-connections",
    name: "Service Connections",
    description: "Fetch service connection authorizations and shared variables",
    evidenceCategories: ["access_control", "secret_management"],
  },
];

export class AzurePipelinesConnector implements IntegrationConnector {
  readonly id = "azure-pipelines";
  readonly name = "Azure Pipelines";
  readonly category = "ci_cd" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const org = config.extra?.org || "default";
    const project = config.extra?.project || "default";
    const base = config.baseUrl || `https://dev.azure.com/${org}/${project}/_apis`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Azure Pipelines API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/build/builds?api-version=7.0&$top=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const builds = await this.fetchApi(
      config,
      "/build/builds?api-version=7.0&$top=100"
    ).catch(() => ({ value: [] }));
    const buildList = (builds.value || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "azurepipelines-builds",
      timestamp: now,
      hash: hashEvidence({ buildCount: buildList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "azure-pipelines/builds",
      status: "unknown",
      data: { buildCount: buildList.length },
      metadata: {},
    });

    return artifacts;
  }
}
