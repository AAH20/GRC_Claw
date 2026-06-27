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
    id: "radware-waf",
    name: "Radware WAF",
    description: "Fetch WAF profiles and policy configurations",
    evidenceCategories: ["vulnerability_management", "configuration"],
  },
  {
    id: "radware-ddos",
    name: "DDoS Mitigation",
    description: "Fetch DDoS protection profiles and attack logs",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "radware-bot",
    name: "Bot Management",
    description: "Fetch bot detection and mitigation policies",
    evidenceCategories: ["access_control", "monitoring"],
  },
  {
    id: "radware-api",
    name: "API Protection",
    description: "Fetch API security profiles and rate limiting",
    evidenceCategories: ["access_control", "data_protection"],
  },
];

export class RadwareConnector implements IntegrationConnector {
  readonly id = "radware";
  readonly name = "Radware";
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
    const base = config.baseUrl || "https://radware-cloud.example.com";
    const resp = await fetch(`${base}/api${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Radware API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/wafProfiles");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const profiles = await this.fetchApi(config, "/wafProfiles").catch(() => ({ profiles: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "radware-waf",
      timestamp: now,
      hash: hashEvidence(profiles),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "radware/waf-profiles",
      status: (profiles.profiles as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { wafProfiles: (profiles.profiles as unknown[])?.length || 0 },
      metadata: {},
    });

    const ddos = await this.fetchApi(config, "/ddos/profiles").catch(() => ({ profiles: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "radware-ddos",
      timestamp: now,
      hash: hashEvidence(ddos),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "radware/ddos-profiles",
      status: (ddos.profiles as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { ddosProfiles: (ddos.profiles as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
