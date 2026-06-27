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
    id: "zendesk-tickets",
    name: "Support Tickets",
    description: "Fetch Zendesk ticket queue, SLA compliance, and resolution metrics",
    evidenceCategories: ["incident_management", "monitoring"],
  },
  {
    id: "zendesk-security",
    name: "Security Settings",
    description: "Fetch Zendesk SSO, 2FA enforcement, and API access controls",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "zendesk-audit",
    name: "Audit Logs",
    description: "Fetch Zendesk audit log events for ticket and user changes",
    evidenceCategories: ["audit", "change_management"],
  },
];

export class ZendeskConnector implements IntegrationConnector {
  readonly id = "zendesk";
  readonly name = "Zendesk";
  readonly category = "incident_management" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const subdomain = config.extra?.subdomain || "default";
    const base = config.baseUrl || `https://${subdomain}.zendesk.com/api/v2`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Zendesk API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/users/me.json");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const tickets = await this.fetchApi(
      config,
      "/tickets.json?per_page=100&sort_by=created_at&sort_order=desc"
    ).catch(() => ({ tickets: [] }));
    const ticketList = (tickets.tickets || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "zendesk-tickets",
      timestamp: now,
      hash: hashEvidence({ ticketCount: ticketList.length }),
      framework: "SOC2",
      controlId: "CC7.3",
      source: "zendesk/tickets",
      status: "unknown",
      data: { recentTickets: ticketList.length },
      metadata: {},
    });

    return artifacts;
  }
}
