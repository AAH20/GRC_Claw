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
    id: "akamai-waf",
    name: "Web Application Firewall",
    description: "Fetch WAF policies and attack group configurations",
    evidenceCategories: ["vulnerability_management", "configuration"],
  },
  {
    id: "akamai-bot",
    name: "Bot Manager",
    description: "Fetch bot detection policies and blocked requests",
    evidenceCategories: ["access_control", "monitoring"],
  },
  {
    id: "akamai-edge",
    name: "Edge Security",
    description: "Fetch edge configuration and mPulse data",
    evidenceCategories: ["configuration", "monitoring"],
  },
  {
    id: "akamai-api",
    name: "API Gateway",
    description: "Fetch API endpoint security and rate limiting rules",
    evidenceCategories: ["access_control", "data_protection"],
  },
];

export class AkamaiConnector implements IntegrationConnector {
  readonly id = "akamai";
  readonly name = "Akamai";
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
    const base = config.baseUrl || "https://akab-akabapi.luna.akamaiapis.net";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Akamai API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/config/v1/security-policies");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const policies = await this.fetchApi(config, "/config/v1/security-policies").catch(() => ({
      policies: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "akamai-waf",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "akamai/security-policies",
      status: (policies.policies as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { securityPolicies: (policies.policies as unknown[])?.length || 0 },
      metadata: {},
    });

    const bot = await this.fetchApi(config, "/config/v1/bot-managers").catch(() => ({
      managers: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "akamai-bot",
      timestamp: now,
      hash: hashEvidence(bot),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "akamai/bot-managers",
      status: (bot.managers as unknown[])?.length > 0 ? "compliant" : "partial",
      data: { botManagers: (bot.managers as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
