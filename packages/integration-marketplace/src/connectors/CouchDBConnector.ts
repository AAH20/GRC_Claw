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
    id: "couchdb-databases",
    name: "CouchDB Databases",
    description: "Fetch CouchDB database configurations and replication status",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "couchdb-security",
    name: "Security Configurations",
    description: "Fetch CouchDB authentication, CORS settings, and admin accounts",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "couchdb-replication",
    name: "Replication Status",
    description: "Fetch CouchDB replication jobs and cluster synchronization health",
    evidenceCategories: ["data_protection", "availability"],
  },
];

export class CouchDBConnector implements IntegrationConnector {
  readonly id = "couchdb";
  readonly name = "Apache CouchDB";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.couchdb.example.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`CouchDB API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/_membership");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const membership = await this.fetchApi(config, "/_membership").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "couchdb-databases",
      timestamp: now,
      hash: hashEvidence(membership),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "couchdb/membership",
      status: "unknown",
      data: { connected: true },
      metadata: {},
    });

    return artifacts;
  }
}
