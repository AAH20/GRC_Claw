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
    id: "fsecure-endpoints",
    name: "Endpoint Protection",
    description: "Fetch F-Secure endpoint agent deployment and protection status",
    evidenceCategories: ["endpoint_security", "monitoring"],
  },
  {
    id: "fsecure-detections",
    name: "Threat Detections",
    description: "Fetch F-Secure threat detection and malware quarantine events",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "fsecure-policies",
    name: "Security Policies",
    description: "Fetch policy configurations and scan schedule compliance",
    evidenceCategories: ["policy_compliance", "configuration"],
  },
];

export class FSecureConnector implements IntegrationConnector {
  readonly id = "fsecure";
  readonly name = "F-Secure";
  readonly category = "endpoint" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://cloud.f-secure.com/api/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`F-Secure API ${resp.status}: ${resp.statusText}`);
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
      capabilityId: "fsecure-endpoints",
      timestamp: now,
      hash: hashEvidence({ computerCount: computerList.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "fsecure/computers",
      status: computerList.length > 0 ? "compliant" : "unknown",
      data: { endpointCount: computerList.length },
      metadata: {},
    });

    return artifacts;
  }
}
