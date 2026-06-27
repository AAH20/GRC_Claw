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
    id: "elasticsearch-clusters",
    name: "Elasticsearch Clusters",
    description: "Fetch Elasticsearch Cloud cluster configurations and index health",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "elasticsearch-security",
    name: "Security Configurations",
    description: "Fetch Elasticsearch security realms, TLS settings, and API key management",
    evidenceCategories: ["access_control", "encryption"],
  },
  {
    id: "elasticsearch-audit",
    name: "Audit Logging",
    description: "Fetch Elasticsearch audit log configurations and access events",
    evidenceCategories: ["monitoring", "audit"],
  },
];

export class ElasticsearchCloudConnector implements IntegrationConnector {
  readonly id = "elasticsearch-cloud";
  readonly name = "Elasticsearch Cloud";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.elastic-cloud.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `ApiKey ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Elasticsearch Cloud API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/deployments?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const deployments = await this.fetchApi(config, "/deployments?limit=100").catch(() => ({ deployments: [] }));
    const deployList = (deployments.deployments || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "elasticsearch-clusters",
      timestamp: now,
      hash: hashEvidence({ deploymentCount: deployList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "elasticsearch-cloud/deployments",
      status: deployList.length > 0 ? "compliant" : "unknown",
      data: { deploymentCount: deployList.length },
      metadata: {},
    });

    return artifacts;
  }
}
