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
    id: "eset-protection",
    name: "Endpoint Protection",
    description: "Fetch ESET PROTECT agent status and detection events",
    evidenceCategories: ["endpoint", "monitoring"],
  },
  {
    id: "eset-policies",
    name: "Security Policies",
    description: "Fetch anti-malware and firewall policy assignments",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "eset-licensing",
    name: "License Management",
    description: "Fetch license status and seat utilization",
    evidenceCategories: ["compliance", "monitoring"],
  },
  {
    id: "eset-compliance",
    name: "Compliance Reports",
    description: "Fetch compliance scan results and audit logs",
    evidenceCategories: ["compliance", "monitoring"],
  },
];

export class ESETConnector implements IntegrationConnector {
  readonly id = "eset";
  readonly name = "ESET";
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
    const base = config.baseUrl || "https://protect.eset.com";
    const resp = await fetch(`${base}/api/v1${endpoint}`, {
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
      await this.fetchApi(config, "/computers");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const computers = await this.fetchApi(config, "/computers").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "eset-protection",
      timestamp: now,
      hash: hashEvidence(computers),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "eset/computers",
      status: (computers.items as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { protectedEndpoints: (computers.items as unknown[])?.length || 0 },
      metadata: {},
    });

    const policies = await this.fetchApi(config, "/policies").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "eset-policies",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "eset/policies",
      status: (policies.items as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { policyCount: (policies.items as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
