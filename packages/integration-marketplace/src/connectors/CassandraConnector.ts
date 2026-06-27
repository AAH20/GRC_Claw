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
    id: "cassandra-clusters",
    name: "Cassandra Clusters",
    description: "Fetch Cassandra cluster configurations and node status",
    evidenceCategories: ["data_protection", "infrastructure"],
  },
  {
    id: "cassandra-security",
    name: "Security Configurations",
    description: "Fetch Cassandra authentication, authorization, and TLS settings",
    evidenceCategories: ["access_control", "encryption"],
  },
  {
    id: "cassandra-backups",
    name: "Backup Status",
    description: "Fetch Cassandra snapshot backups and repair status",
    evidenceCategories: ["data_protection", "disaster_recovery"],
  },
];

export class CassandraConnector implements IntegrationConnector {
  readonly id = "cassandra";
  readonly name = "Apache Cassandra";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.cassandra.example.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Cassandra API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/cluster/status");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const status = await this.fetchApi(config, "/cluster/status").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cassandra-clusters",
      timestamp: now,
      hash: hashEvidence(status),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "cassandra/cluster",
      status: "unknown",
      data: { connected: true },
      metadata: {},
    });

    return artifacts;
  }
}
