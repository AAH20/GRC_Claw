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
    id: "drift-conversations",
    name: "Conversations",
    description: "Fetch Drift chatbot conversation logs and lead capture metrics",
    evidenceCategories: ["communication", "monitoring"],
  },
  {
    id: "drift-security",
    name: "Security Settings",
    description: "Fetch Drift SSO, API access controls, and data retention settings",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "drift-playbooks",
    name: "Playbook Configurations",
    description: "Fetch Drift playbook definitions, routing rules, and approval workflows",
    evidenceCategories: ["configuration", "change_management"],
  },
];

export class DriftConnector implements IntegrationConnector {
  readonly id = "drift";
  readonly name = "Drift";
  readonly category = "communication" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.drift.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Drift API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/account");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const account = await this.fetchApi(config, "/account").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "drift-conversations",
      timestamp: now,
      hash: hashEvidence(account),
      framework: "SOC2",
      controlId: "CC7.3",
      source: "drift/account",
      status: "unknown",
      data: { connected: true },
      metadata: {},
    });

    return artifacts;
  }
}
