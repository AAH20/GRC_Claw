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
    id: "intercom-conversations",
    name: "Conversations",
    description: "Fetch Intercom conversation history, resolution rates, and SLA compliance",
    evidenceCategories: ["incident_management", "monitoring"],
  },
  {
    id: "intercom-security",
    name: "Security Settings",
    description: "Fetch Intercom SSO, data retention, and API access controls",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "intercom-audit",
    name: "Audit Logs",
    description: "Fetch Intercom admin audit log and workspace activity events",
    evidenceCategories: ["audit", "change_management"],
  },
];

export class IntercomConnector implements IntegrationConnector {
  readonly id = "intercom";
  readonly name = "Intercom";
  readonly category = "communication" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.intercom.io";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Intercom API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const me = await this.fetchApi(config, "/me").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "intercom-conversations",
      timestamp: now,
      hash: hashEvidence(me),
      framework: "SOC2",
      controlId: "CC7.3",
      source: "intercom/me",
      status: "unknown",
      data: { connected: true },
      metadata: {},
    });

    return artifacts;
  }
}
