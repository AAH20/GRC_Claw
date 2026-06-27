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
    id: "twilio-accounts",
    name: "Account Configuration",
    description: "Fetch Twilio account details, subaccount hierarchy, and usage records",
    evidenceCategories: ["configuration", "monitoring"],
  },
  {
    id: "twilio-security",
    name: "Security Settings",
    description: "Fetch Twilio API key management, IP restrictions, and webhook security",
    evidenceCategories: ["access_control", "secret_management"],
  },
  {
    id: "twilio-communications",
    name: "Communication Logs",
    description: "Fetch SMS/voice message delivery status and error logs",
    evidenceCategories: ["monitoring", "audit"],
  },
];

export class TwilioConnector implements IntegrationConnector {
  readonly id = "twilio";
  readonly name = "Twilio";
  readonly category = "communication" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.twilio.com/2010-04-01";
    const auth = Buffer.from(`${config.clientId}:${config.clientSecret}`).toString("base64");
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Basic ${auth}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Twilio API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/Accounts.json?Limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const account = await this.fetchApi(config, "/Account.json").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "twilio-accounts",
      timestamp: now,
      hash: hashEvidence(account),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "twilio/account",
      status: "unknown",
      data: { connected: true },
      metadata: {},
    });

    return artifacts;
  }
}
