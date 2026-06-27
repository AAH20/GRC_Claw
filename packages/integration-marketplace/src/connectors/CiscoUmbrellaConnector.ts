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
    id: "umbrella-dns",
    name: "DNS Security",
    description: "Fetch DNS-layer security policies and block lists",
    evidenceCategories: ["access_control", "vulnerability_management"],
  },
  {
    id: "umbrella-sig",
    name: "Secure Internet Gateway",
    description: "Fetch SIG proxy and URL filtering policies",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "umbrella-dga",
    name: "DGA Detection",
    description: "Fetch domain generation algorithm detection alerts",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "umbrella-roaming",
    name: "Roaming Security",
    description: "Fetch roaming client compliance and coverage",
    evidenceCategories: ["endpoint", "access_control"],
  },
];

export class CiscoUmbrellaConnector implements IntegrationConnector {
  readonly id = "cisco-umbrella";
  readonly name = "Cisco Umbrella";
  readonly category = "cloud_provider" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
    "HIPAA",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api Umbrella.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Cisco Umbrella API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/deployments/org");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const orgId = config.extra?.orgId || "default";

    const policies = await this.fetchApi(
      config,
      `/policies/v2/policies?orgId=${orgId}`
    ).catch(() => ({ data: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "umbrella-dns",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `umbrella/${orgId}/policies`,
      status: (policies.data as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { policyCount: (policies.data as unknown[])?.length || 0 },
      metadata: { orgId },
    });

    const destinations = await this.fetchApi(
      config,
      `/deployments/v2/destinations?orgId=${orgId}`
    ).catch(() => ({ data: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "umbrella-roaming",
      timestamp: now,
      hash: hashEvidence(destinations),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: `umbrella/${orgId}/destinations`,
      status: "partial",
      data: { destinations: (destinations.data as unknown[])?.length || 0 },
      metadata: { orgId },
    });

    return artifacts;
  }
}
