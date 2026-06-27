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
    id: "eset-endpoints",
    name: "Endpoint Security",
    description: "Fetch ESET endpoint agent status and detection statistics",
    evidenceCategories: ["endpoint_security", "monitoring"],
  },
  {
    id: "eset-policies",
    name: "Security Policies",
    description: "Fetch ESET policy configurations and compliance status",
    evidenceCategories: ["policy_compliance", "configuration"],
  },
  {
    id: "eset-threats",
    name: "Threat Events",
    description: "Fetch threat detection events and quarantine history",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
];

export class ESETConnector implements IntegrationConnector {
  readonly id = "eset";
  readonly name = "ESET";
  readonly category = "endpoint" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://protect.eset.com/api/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`ESET API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/computers?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const computers = await this.fetchApi(config, "/computers?limit=100").catch(() => ({ items: [] }));
    const computerList = (computers.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "eset-endpoints",
      timestamp: now,
      hash: hashEvidence({ computerCount: computerList.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "eset/computers",
      status: computerList.length > 0 ? "compliant" : "unknown",
      data: { endpointCount: computerList.length },
      metadata: {},
    });

    return artifacts;
  }
}
