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
    id: "checkpoint-firewall",
    name: "Firewall Policies",
    description: "Fetch firewall rule base and policy compliance",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "checkpoint-vpn",
    name: "VPN Configuration",
    description: "Fetch VPN tunnel status and encryption settings",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "checkpoint-threat",
    name: "Threat Prevention",
    description: "Fetch threat prevention profiles andblade status",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "checkpoint-logs",
    name: "Security Logs",
    description: "Fetch security gateway logs and traffic analysis",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class CheckPointConnector implements IntegrationConnector {
  readonly id = "checkpoint";
  readonly name = "Check Point";
  readonly category = "cloud_provider" as const;
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
    const base = config.baseUrl || "https://cp-management.example.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Check Point API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/api/v1/show-gateways");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const gateways = await this.fetchApi(config, "/api/v1/show-gateways").catch(() => ({
      objects: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "checkpoint-firewall",
      timestamp: now,
      hash: hashEvidence(gateways),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "checkpoint/gateways",
      status: (gateways.objects as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { gateways: (gateways.objects as unknown[])?.length || 0 },
      metadata: {},
    });

    const threats = await this.fetchApi(config, "/api/v1/show-threat-profiles").catch(() => ({
      objects: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "checkpoint-threat",
      timestamp: now,
      hash: hashEvidence(threats),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "checkpoint/threat-profiles",
      status: (threats.objects as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { threatProfiles: (threats.objects as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
