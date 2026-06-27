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
    id: "fortinet-firewall",
    name: "FortiGate Firewall",
    description: "Fetch FortiGate firewall policies and interfaces",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "fortinet-ips",
    name: "IPS Signatures",
    description: "Fetch intrusion prevention signature status",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "fortinet-webfilter",
    name: "Web Filtering",
    description: "Fetch web filter profiles and URL categories",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "fortinet-logs",
    name: "Security Logs",
    description: "Fetch FortiGate event and traffic logs",
    evidenceCategories: ["monitoring"],
  },
];

export class FortinetConnector implements IntegrationConnector {
  readonly id = "fortinet";
  readonly name = "Fortinet FortiGate";
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
    const base = config.baseUrl || "https://fortigate.example.com";
    const resp = await fetch(`${base}/api/v2${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Fortinet API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/monitor/system/status");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const policies = await this.fetchApi(config, "/monitor/firewall/policy").catch(() => ({
      results: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "fortinet-firewall",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "fortinet/firewall/policies",
      status: (policies.results as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { policyCount: (policies.results as unknown[])?.length || 0 },
      metadata: {},
    });

    const ips = await this.fetchApi(config, "/monitor/ips/signature").catch(() => ({
      results: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "fortinet-ips",
      timestamp: now,
      hash: hashEvidence(ips),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "fortinet/ips/signatures",
      status: (ips.results as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { signatureCount: (ips.results as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
