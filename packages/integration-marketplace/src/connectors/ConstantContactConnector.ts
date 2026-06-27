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
    id: "constantcontact-contacts",
    name: "Contact Lists",
    description: "Fetch Constant Contact contact lists and segmentation data",
    evidenceCategories: ["data_protection", "configuration"],
  },
  {
    id: "constantcontact-security",
    name: "Account Security",
    description: "Fetch Constant Contact API key permissions and user access controls",
    evidenceCategories: ["access_control", "audit"],
  },
  {
    id: "constantcontact-campaigns",
    name: "Campaign Performance",
    description: "Fetch email campaign delivery and engagement metrics",
    evidenceCategories: ["monitoring", "configuration"],
  },
];

export class ConstantContactConnector implements IntegrationConnector {
  readonly id = "constantcontact";
  readonly name = "Constant Contact";
  readonly category = "communication" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.constantcontact.com/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Constant Contact API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/accounts?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const lists = await this.fetchApi(config, "/lists?limit=100").catch(() => ({ lists: [] }));
    const listList = (lists.lists || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "constantcontact-contacts",
      timestamp: now,
      hash: hashEvidence({ listCount: listList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "constantcontact/lists",
      status: "unknown",
      data: { contactListCount: listList.length },
      metadata: {},
    });

    return artifacts;
  }
}
