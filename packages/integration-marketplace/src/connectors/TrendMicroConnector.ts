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
    id: "trendmicro-endpoints",
    name: "Deep Security",
    description: "Fetch Deep Security agent status and protection modules",
    evidenceCategories: ["endpoint", "monitoring"],
  },
  {
    id: "trendmicro-policies",
    name: "Security Policies",
    description: "Fetch firewall, IPS, and anti-malware policy configs",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "trendmicro-alerts",
    name: "Integrity Monitoring",
    description: "Fetch file integrity monitoring and intrusion alerts",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "trendmicro-logs",
    name: "Inspection Logs",
    description: "Fetch log inspection results and compliance findings",
    evidenceCategories: ["monitoring", "compliance"],
  },
];

export class TrendMicroConnector implements IntegrationConnector {
  readonly id = "trendmicro";
  readonly name = "Trend Micro";
  readonly category = "endpoint" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "PCI_DSS",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://deepsecurity.trendmicro.com";
    const resp = await fetch(`${base}/api${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
        "API-Version": "v1",
      },
    });
    if (!resp.ok) throw new Error(`Trend Micro API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/computers");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const computers = await this.fetchApi(config, "/computers").catch(() => ({ computers: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "trendmicro-endpoints",
      timestamp: now,
      hash: hashEvidence(computers),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "trendmicro/computers",
      status: (computers.computers as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { protectedEndpoints: (computers.computers as unknown[])?.length || 0 },
      metadata: {},
    });

    const policies = await this.fetchApi(config, "/policies").catch(() => ({ policies: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "trendmicro-policies",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "trendmicro/policies",
      status: (policies.policies as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { policyCount: (policies.policies as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
