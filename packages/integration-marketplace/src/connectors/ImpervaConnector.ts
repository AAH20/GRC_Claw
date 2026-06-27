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
    id: "imperva-waf",
    name: "Imperva WAF",
    description: "Fetch WAF policies and custom rules",
    evidenceCategories: ["vulnerability_management", "configuration"],
  },
  {
    id: "imperva-ddos",
    name: "DDoS Protection",
    description: "Fetch DDoS mitigation profiles and activation status",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "imperva-api",
    name: "API Security",
    description: "Fetch API discovery and protection policies",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "imperva-bi",
    name: "Security Analytics",
    description: "Fetch attack analytics and traffic insights",
    evidenceCategories: ["monitoring"],
  },
];

export class ImpervaConnector implements IntegrationConnector {
  readonly id = "imperva";
  readonly name = "Imperva";
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
    const base = config.baseUrl || "https://api.imperva.com";
    const resp = await fetch(`${base}/api/v1${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Imperva API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/sites");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const sites = await this.fetchApi(config, "/sites").catch(() => ({ sites: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "imperva-waf",
      timestamp: now,
      hash: hashEvidence(sites),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "imperva/sites",
      status: (sites.sites as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { protectedSites: (sites.sites as unknown[])?.length || 0 },
      metadata: {},
    });

    const policies = await this.fetchApi(config, "/policies").catch(() => ({ policies: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "imperva-api",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "ISO27001",
      controlId: "A.8.3.1",
      source: "imperva/policies",
      status: (policies.policies as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { wafPolicies: (policies.policies as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
