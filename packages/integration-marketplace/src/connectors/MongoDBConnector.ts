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
    id: "mongodb-clusters",
    name: "Atlas Clusters",
    description: "Fetch MongoDB Atlas cluster configurations and backup status",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "mongodb-access",
    name: "Database Access",
    description: "Fetch MongoDB Atlas database user roles and IP whitelist entries",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "mongodb-audit",
    name: "Audit Logs",
    description: "Fetch MongoDB Atlas audit log events and authentication attempts",
    evidenceCategories: ["monitoring", "audit"],
  },
];

export class MongoDBConnector implements IntegrationConnector {
  readonly id = "mongodb";
  readonly name = "MongoDB Atlas";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://cloud.mongodb.com/api/public/v1.0";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`MongoDB API ${resp.status}: ${resp.statusText}`);
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
    const groupId = config.extra?.groupId || "default";

    const clusters = await this.fetchApi(config, `/groups/${groupId}/clusters`).catch(() => ({ results: [] }));
    const clusterList = (clusters.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "mongodb-clusters",
      timestamp: now,
      hash: hashEvidence({ clusterCount: clusterList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "mongodb/clusters",
      status: clusterList.length > 0 ? "compliant" : "unknown",
      data: { clusterCount: clusterList.length },
      metadata: { groupId },
    });

    const users = await this.fetchApi(config, `/groups/${groupId}/databaseUsers`).catch(() => ({ results: [] }));
    const userList = (users.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "mongodb-access",
      timestamp: now,
      hash: hashEvidence({ userCount: userList.length }),
      framework: "ISO27001",
      controlId: "A.9.2.1",
      source: "mongodb/databaseUsers",
      status: "unknown",
      data: { databaseUserCount: userList.length },
      metadata: { groupId },
    });

    return artifacts;
  }
}
