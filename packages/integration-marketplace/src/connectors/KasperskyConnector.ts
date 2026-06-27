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
    id: "kaspersky-endpoints",
    name: "Endpoint Protection",
    description: "Fetch Kaspersky endpoint agent status and security level metrics",
    evidenceCategories: ["endpoint_security", "monitoring"],
  },
  {
    id: "kaspersky-detections",
    name: "Threat Detections",
    description: "Fetch threat detection events and malware neutralization records",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "kaspersky-policies",
    name: "Security Policies",
    description: "Fetch Kaspersky policy configurations and task schedules",
    evidenceCategories: ["policy_compliance", "configuration"],
  },
];

export class KasperskyConnector implements IntegrationConnector {
  readonly id = "kaspersky";
  readonly name = "Kaspersky";
  readonly category = "endpoint" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://cloud.securitycenter.kaspersky.com/api/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Kaspersky API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/hosts?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const hosts = await this.fetchApi(config, "/hosts?limit=100").catch(() => ({ items: [] }));
    const hostList = (hosts.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "kaspersky-endpoints",
      timestamp: now,
      hash: hashEvidence({ hostCount: hostList.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "kaspersky/hosts",
      status: hostList.length > 0 ? "compliant" : "unknown",
      data: { endpointCount: hostList.length },
      metadata: {},
    });

    return artifacts;
  }
}
