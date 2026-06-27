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
    id: "beyondtrust-privilege",
    name: "Privilege Management",
    description: "Fetch privileged account policies and session recordings",
    evidenceCategories: ["access_control", "monitoring"],
  },
  {
    id: "beyondtrust-endpoint",
    name: "Endpoint Security",
    description: "Fetch endpoint privilege delegation and application control",
    evidenceCategories: ["endpoint", "access_control"],
  },
  {
    id: "beyondtrust-password",
    name: "Password Safe",
    description: "Fetch password vault configurations and checkout policies",
    evidenceCategories: ["data_protection", "access_control"],
  },
  {
    id: "beyondtrust-audit",
    name: "Audit Reports",
    description: "Fetch privileged access audit trails and compliance reports",
    evidenceCategories: ["monitoring", "compliance"],
  },
];

export class BeyondTrustConnector implements IntegrationConnector {
  readonly id = "beyondtrust";
  readonly name = "BeyondTrust";
  readonly category = "identity" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://beyondtrust.example.com";
    const resp = await fetch(`${base}/api${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`BeyondTrust API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/configuration/system");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const systems = await this.fetchApi(config, "/managed-systems").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "beyondtrust-privilege",
      timestamp: now,
      hash: hashEvidence(systems),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "beyondtrust/managed-systems",
      status: (systems.items as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { managedSystems: (systems.items as unknown[])?.length || 0 },
      metadata: {},
    });

    const accounts = await this.fetchApi(config, "/accounts").catch(() => ({ items: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "beyondtrust-password",
      timestamp: now,
      hash: hashEvidence(accounts),
      framework: "ISO27001",
      controlId: "A.9.2.6",
      source: "beyondtrust/accounts",
      status: (accounts.items as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { privilegedAccounts: (accounts.items as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
