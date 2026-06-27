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
    id: "cyberark-safe",
    name: "Safe Management",
    description: "Fetch safe configurations and access policies",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "cyberark-accounts",
    name: "Account Management",
    description: "Fetch managed accounts and rotation status",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "cyberark-psm",
    name: "Session Monitoring",
    description: "Fetch PSM session recordings and access logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
  {
    id: "cyberark-policies",
    name: "Password Policies",
    description: "Fetch password complexity and rotation policies",
    evidenceCategories: ["data_protection", "configuration"],
  },
];

export class CyberArkConnector implements IntegrationConnector {
  readonly id = "cyberark";
  readonly name = "CyberArk";
  readonly category = "identity" as const;
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
    const base = config.baseUrl || "https://cyberark.example.com";
    const resp = await fetch(`${base}/PasswordVault/API${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`CyberArk API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/ Vaults");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const safes = await this.fetchApi(config, "/Vaults").catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cyberark-safe",
      timestamp: now,
      hash: hashEvidence(safes),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "cyberark/safes",
      status: (safes.value as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { safeCount: (safes.value as unknown[])?.length || 0 },
      metadata: {},
    });

    const accounts = await this.fetchApi(config, "/Accounts").catch(() => ({ value: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cyberark-accounts",
      timestamp: now,
      hash: hashEvidence(accounts),
      framework: "ISO27001",
      controlId: "A.9.2.6",
      source: "cyberark/accounts",
      status: (accounts.value as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { managedAccounts: (accounts.value as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
