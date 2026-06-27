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
    id: "mailchimp-lists",
    name: "Audience Lists",
    description: "Fetch Mailchimp audience lists, subscriber counts, and segmentation",
    evidenceCategories: ["data_protection", "configuration"],
  },
  {
    id: "mailchimp-security",
    name: "Security Settings",
    description: "Fetch Mailchimp API key permissions, 2FA status, and login history",
    evidenceCategories: ["access_control", "audit"],
  },
  {
    id: "mailchimp-campaigns",
    name: "Campaign Statistics",
    description: "Fetch email campaign performance and delivery metrics",
    evidenceCategories: ["monitoring", "configuration"],
  },
];

export class MailchimpConnector implements IntegrationConnector {
  readonly id = "mailchimp";
  readonly name = "Mailchimp";
  readonly category = "communication" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const dc = config.extra?.dc || "us1";
    const base = config.baseUrl || `https://${dc}.api.mailchimp.com/3.0`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Mailchimp API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/ping");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const lists = await this.fetchApi(config, "/lists?count=100").catch(() => ({ lists: [] }));
    const listList = (lists.lists || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "mailchimp-lists",
      timestamp: now,
      hash: hashEvidence({ listCount: listList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "mailchimp/lists",
      status: "unknown",
      data: { audienceCount: listList.length },
      metadata: {},
    });

    return artifacts;
  }
}
