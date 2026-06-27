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
    id: "rediscloud-databases",
    name: "Redis Databases",
    description: "Fetch Redis Cloud database configurations and memory usage",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "rediscloud-security",
    name: "Security Configurations",
    description: "Fetch TLS enforcement, ACL configurations, and network security rules",
    evidenceCategories: ["access_control", "encryption"],
  },
  {
    id: "rediscloud-metrics",
    name: "Performance Metrics",
    description: "Fetch Redis Cloud performance metrics and connection statistics",
    evidenceCategories: ["monitoring", "performance"],
  },
];

export class RedisCloudConnector implements IntegrationConnector {
  readonly id = "redis-cloud";
  readonly name = "Redis Cloud";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.redislabs.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Redis Cloud API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/subscriptions");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const subscriptions = await this.fetchApi(config, "/subscriptions").catch(() => ({ subscriptions: [] }));
    const subList = (subscriptions.subscriptions || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "rediscloud-databases",
      timestamp: now,
      hash: hashEvidence({ subscriptionCount: subList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "redis-cloud/subscriptions",
      status: subList.length > 0 ? "compliant" : "unknown",
      data: { subscriptionCount: subList.length },
      metadata: {},
    });

    return artifacts;
  }
}
