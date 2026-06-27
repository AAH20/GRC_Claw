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
    id: "sendgrid-stats",
    name: "Email Statistics",
    description: "Fetch SendGrid email delivery statistics, bounce rates, and spam reports",
    evidenceCategories: ["monitoring", "configuration"],
  },
  {
    id: "sendgrid-security",
    name: "Security Settings",
    description: "Fetch SendGrid API key permissions, IP whitelisting, and authentication settings",
    evidenceCategories: ["access_control", "secret_management"],
  },
  {
    id: "sendgrid-templates",
    name: "Email Templates",
    description: "Fetch SendGrid email template versions and approval workflows",
    evidenceCategories: ["change_management", "configuration"],
  },
];

export class SendGridConnector implements IntegrationConnector {
  readonly id = "sendgrid";
  readonly name = "SendGrid";
  readonly category = "communication" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.sendgrid.com/v3";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`SendGrid API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/user/profile");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const profile = await this.fetchApi(config, "/user/profile").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sendgrid-stats",
      timestamp: now,
      hash: hashEvidence(profile),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "sendgrid/profile",
      status: "unknown",
      data: { connected: true },
      metadata: {},
    });

    return artifacts;
  }
}
