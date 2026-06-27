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
    id: "zscaler-zpa",
    name: "Zero Trust Access",
    description: "Fetch ZPA application segments and policies",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "zscaler-zia",
    name: "Internet Access",
    description: "Fetch ZIA URL filtering and cloud firewall policies",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "zscaler-dlp",
    name: "Data Loss Prevention",
    description: "Fetch DLP policies and incident counts",
    evidenceCategories: ["data_protection", "monitoring"],
  },
  {
    id: "zscaler-sandbox",
    name: "Cloud Sandbox",
    description: "Fetch sandbox malware analysis reports",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
];

export class ZscalerConnector implements IntegrationConnector {
  readonly id = "zscaler";
  readonly name = "Zscaler";
  readonly category = "cloud_provider" as const;
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
    const base = config.baseUrl || "https://api.zscaler.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Zscaler API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/api/v1/adminUsers");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const urlPolicies = await this.fetchApi(config, "/api/v1/policies/urlFiltering").catch(() => ({
      policies: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "zscaler-zia",
      timestamp: now,
      hash: hashEvidence(urlPolicies),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "zscaler/url-filtering",
      status: (urlPolicies.policies as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { urlFilteringPolicies: (urlPolicies.policies as unknown[])?.length || 0 },
      metadata: {},
    });

    const dlp = await this.fetchApi(config, "/api/v1/policies/dlp").catch(() => ({ rules: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "zscaler-dlp",
      timestamp: now,
      hash: hashEvidence(dlp),
      framework: "ISO27001",
      controlId: "A.8.3.1",
      source: "zscaler/dlp-policies",
      status: (dlp.rules as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { dlpRules: (dlp.rules as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
