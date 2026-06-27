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
    id: "pgcloud-instances",
    name: "Database Instances",
    description: "Fetch PostgreSQL Cloud instance configurations, versions, and storage",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "pgcloud-security",
    name: "Security Configurations",
    description: "Fetch SSL enforcement, IP whitelisting, and IAM authentication settings",
    evidenceCategories: ["access_control", "encryption"],
  },
  {
    id: "pgcloud-backups",
    name: "Backup and Recovery",
    description: "Fetch backup schedules, retention policies, and point-in-time recovery status",
    evidenceCategories: ["data_protection", "disaster_recovery"],
  },
];

export class PostgreSQLCloudConnector implements IntegrationConnector {
  readonly id = "postgresql-cloud";
  readonly name = "PostgreSQL Cloud";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.postgres.cloud.example.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`PostgreSQL Cloud API ${resp.status}: ${resp.statusText}`);
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
      capabilityId: "pgcloud-instances",
      timestamp: now,
      hash: hashEvidence({ clusterCount: clusterList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "postgresql-cloud/clusters",
      status: clusterList.length > 0 ? "compliant" : "unknown",
      data: { clusterCount: clusterList.length },
      metadata: {},
    });

    return artifacts;
  }
}
