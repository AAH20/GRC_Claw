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
    id: "databricks-workspaces",
    name: "Workspace Security",
    description: "Fetch workspace access controls and Unity Catalog permissions",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "databricks-jobs",
    name: "Job Configurations",
    description: "Fetch job definitions and cluster configurations",
    evidenceCategories: ["change_management", "configuration"],
  },
  {
    id: "databricks-data-governance",
    name: "Data Governance",
    description: "Fetch data lineage, classification tags, and access policies",
    evidenceCategories: ["data_protection", "compliance"],
  },
  {
    id: "databricks-audit",
    name: "Audit Logs",
    description: "Fetch workspace audit log events",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class DatabricksConnector implements IntegrationConnector {
  readonly id = "databricks";
  readonly name = "Databricks";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "PCI_DSS",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://adb-default.cloud.databricks.com";
    const resp = await fetch(`${base}/api/2.0${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Databricks API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/clusters/list");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const clusters = await this.fetchApi(config, "/clusters/list").catch(() => ({ clusters: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "databricks-workspaces",
      timestamp: now,
      hash: hashEvidence(clusters),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "databricks/clusters",
      status: (clusters.clusters as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { clusterCount: (clusters.clusters as unknown[])?.length || 0 },
      metadata: {},
    });

    const jobs = await this.fetchApi(config, "/jobs/list").catch(() => ({ jobs: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "databricks-jobs",
      timestamp: now,
      hash: hashEvidence(jobs),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: "databricks/jobs",
      status: (jobs.jobs as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { jobCount: (jobs.jobs as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
