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
    id: "powerbi-workspaces",
    name: "Workspace Access",
    description: "Fetch workspace membership and role assignments",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "powerbi-datasets",
    name: "Dataset Governance",
    description: "Fetch dataset sensitivity labels and certification status",
    evidenceCategories: ["data_protection", "compliance"],
  },
  {
    id: "powerbi-gateway",
    name: "On-Premises Gateway",
    description: "Fetch gateway cluster status and data source credentials",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "powerbi-admin",
    name: "Admin API",
    description: "Fetch activity logs and tenant settings",
    evidenceCategories: ["monitoring", "configuration"],
  },
];

export class PowerBIConnector implements IntegrationConnector {
  readonly id = "powerbi";
  readonly name = "Microsoft Power BI";
  readonly category = "data_warehouse" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "GDPR",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.powerbi.com/v1.0/myorg";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Power BI API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/groups");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const groups = await this.fetchApi(config, "/groups").catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "powerbi-workspaces",
      timestamp: now,
      hash: hashEvidence(groups),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "powerbi/groups",
      status: (groups.value as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { workspaceCount: (groups.value as unknown[])?.length || 0 },
      metadata: {},
    });

    const datasets = await this.fetchApi(config, "/datasets").catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "powerbi-datasets",
      timestamp: now,
      hash: hashEvidence(datasets),
      framework: "ISO27001",
      controlId: "A.8.3.1",
      source: "powerbi/datasets",
      status: (datasets.value as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { datasetCount: (datasets.value as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
