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
    id: "gcpbigquery-datasets",
    name: "BigQuery Datasets",
    description: "Fetch BigQuery dataset configurations and access controls",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "gcpbigquery-iam",
    name: "Dataset IAM Policies",
    description: "Fetch IAM bindings and authorized views on BigQuery datasets",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "gcpbigquery-audit",
    name: "Query Audit Logs",
    description: "Fetch BigQuery data access audit logs and query history",
    evidenceCategories: ["monitoring", "audit"],
  },
];

export class GCPBigQueryConnector implements IntegrationConnector {
  readonly id = "gcp-bigquery";
  readonly name = "GCP BigQuery";
  readonly category = "data_warehouse" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const project = config.extra?.project || "default";
    const base = config.baseUrl || `https://bigquery.googleapis.com/bigquery/v2/projects/${project}`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`GCP BigQuery API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/datasets?maxResults=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const datasets = await this.fetchApi(config, "/datasets?maxResults=100").catch(() => ({ datasets: [] }));
    const datasetList = (datasets.datasets || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcpbigquery-datasets",
      timestamp: now,
      hash: hashEvidence({ datasetCount: datasetList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "gcp-bigquery/datasets",
      status: datasetList.length > 0 ? "compliant" : "unknown",
      data: { datasetCount: datasetList.length },
      metadata: {},
    });

    return artifacts;
  }
}
