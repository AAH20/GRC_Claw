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
    id: "sailpoint-identity",
    name: "Identity Governance",
    description: "Fetch identity lifecycle and access certification campaigns",
    evidenceCategories: ["access_control", "compliance"],
  },
  {
    id: "sailpoint-provisioning",
    name: "Provisioning",
    description: "Fetch automated provisioning and deprovisioning policies",
    evidenceCategories: ["access_control", "change_management"],
  },
  {
    id: "sailpoint-access",
    name: "Access Reviews",
    description: "Fetch access review campaigns and certification results",
    evidenceCategories: ["access_control", "monitoring"],
  },
  {
    id: "sailpoint-compliance",
    name: "Compliance Score",
    description: "Fetch compliance scores and policy violations",
    evidenceCategories: ["compliance", "monitoring"],
  },
];

export class SailPointConnector implements IntegrationConnector {
  readonly id = "sailpoint";
  readonly name = "SailPoint";
  readonly category = "identity" as const;
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
    const base = config.baseUrl || "https://sailpoint.example.com";
    const resp = await fetch(`${base}/v3${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`SailPoint API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/accounts?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const accounts = await this.fetchApi(config, "/accounts?limit=100").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sailpoint-identity",
      timestamp: now,
      hash: hashEvidence(accounts),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "sailpoint/accounts",
      status: (accounts.items as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { identityCount: (accounts.items as unknown[])?.length || 0 },
      metadata: {},
    });

    const campaigns = await this.fetchApi(config, "/certifications?limit=10").catch(() => ({
      items: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sailpoint-access",
      timestamp: now,
      hash: hashEvidence(campaigns),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "sailpoint/certifications",
      status: (campaigns.items as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { activeCampaigns: (campaigns.items as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
