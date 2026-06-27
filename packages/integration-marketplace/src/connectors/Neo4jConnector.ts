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
    id: "neo4j-databases",
    name: "Neo4j Databases",
    description: "Fetch Neo4j database configurations and graph statistics",
    evidenceCategories: ["data_protection", "cloud_configuration"],
  },
  {
    id: "neo4j-security",
    name: "Security Configurations",
    description: "Fetch Neo4j authentication, role-based access, and TLS settings",
    evidenceCategories: ["access_control", "encryption"],
  },
  {
    id: "neo4j-queries",
    name: "Query Audit",
    description: "Fetch Neo4j query logs and slow query monitoring",
    evidenceCategories: ["monitoring", "audit"],
  },
];

export class Neo4jConnector implements IntegrationConnector {
  readonly id = "neo4j";
  readonly name = "Neo4j";
  readonly category = "data_warehouse" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.neo4j.example.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Neo4j API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/instances?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const instances = await this.fetchApi(config, "/instances?limit=100").catch(() => ({ items: [] }));
    const instanceList = (instances.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "neo4j-databases",
      timestamp: now,
      hash: hashEvidence({ instanceCount: instanceList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "neo4j/instances",
      status: instanceList.length > 0 ? "compliant" : "unknown",
      data: { instanceCount: instanceList.length },
      metadata: {},
    });

    return artifacts;
  }
}
