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
    id: "influxdb-buckets",
    name: "InfluxDB Buckets",
    description: "Fetch InfluxDB Cloud bucket configurations and retention policies",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "influxdb-security",
    name: "Security Configurations",
    description: "Fetch InfluxDB tokens, org-level permissions, and TLS settings",
    evidenceCategories: ["access_control", "encryption"],
  },
  {
    id: "influxdb-monitoring",
    name: "Query Monitoring",
    description: "Fetch InfluxDB query performance and task execution logs",
    evidenceCategories: ["monitoring", "performance"],
  },
];

export class InfluxDBConnector implements IntegrationConnector {
  readonly id = "influxdb";
  readonly name = "InfluxDB";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.influxdb.cloud/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Token ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`InfluxDB API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/buckets?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const buckets = await this.fetchApi(config, "/buckets?limit=100").catch(() => ({ buckets: [] }));
    const bucketList = (buckets.buckets || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "influxdb-buckets",
      timestamp: now,
      hash: hashEvidence({ bucketCount: bucketList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "influxdb/buckets",
      status: bucketList.length > 0 ? "compliant" : "unknown",
      data: { bucketCount: bucketList.length },
      metadata: {},
    });

    return artifacts;
  }
}
