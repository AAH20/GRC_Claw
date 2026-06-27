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
    id: "kafka-clusters",
    name: "Kafka Clusters",
    description: "Fetch Kafka cluster configurations and topic inventory",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "kafka-security",
    name: "Security Configurations",
    description: "Fetch Kafka SASL/SSL settings and ACL configurations",
    evidenceCategories: ["access_control", "encryption"],
  },
  {
    id: "kafka-consumers",
    name: "Consumer Groups",
    description: "Fetch consumer group lag metrics and partition assignments",
    evidenceCategories: ["monitoring", "performance"],
  },
];

export class KafkaConnector implements IntegrationConnector {
  readonly id = "kafka";
  readonly name = "Apache Kafka";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.kafka.example.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Kafka API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/clusters?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const clusters = await this.fetchApi(config, "/clusters?limit=100").catch(() => ({ items: [] }));
    const clusterList = (clusters.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "kafka-clusters",
      timestamp: now,
      hash: hashEvidence({ clusterCount: clusterList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "kafka/clusters",
      status: clusterList.length > 0 ? "compliant" : "unknown",
      data: { clusterCount: clusterList.length },
      metadata: {},
    });

    return artifacts;
  }
}
