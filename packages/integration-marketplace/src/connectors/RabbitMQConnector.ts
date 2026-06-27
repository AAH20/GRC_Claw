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
    id: "rabbitmq-queues",
    name: "Queue Configurations",
    description: "Fetch RabbitMQ queue definitions, bindings, and message rates",
    evidenceCategories: ["data_protection", "monitoring"],
  },
  {
    id: "rabbitmq-security",
    name: "Access Controls",
    description: "Fetch RabbitMQ user permissions, vhost policies, and TLS settings",
    evidenceCategories: ["access_control", "encryption"],
  },
  {
    id: "rabbitmq-health",
    name: "Cluster Health",
    description: "Fetch RabbitMQ cluster health, node status, and memory usage",
    evidenceCategories: ["monitoring", "availability"],
  },
];

export class RabbitMQConnector implements IntegrationConnector {
  readonly id = "rabbitmq";
  readonly name = "RabbitMQ";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.rabbitmq.example.com/api";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`RabbitMQ API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/overview");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const overview = await this.fetchApi(config, "/overview").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "rabbitmq-health",
      timestamp: now,
      hash: hashEvidence(overview),
      framework: "SOC2",
      controlId: "CC6.6",
      source: "rabbitmq/overview",
      status: "unknown",
      data: { connected: true },
      metadata: {},
    });

    return artifacts;
  }
}
