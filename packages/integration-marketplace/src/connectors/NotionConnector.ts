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
    id: "notion-databases",
    name: "Databases",
    description: "Fetch Notion databases used for policy tracking and compliance documentation",
    evidenceCategories: ["documentation", "policy_management"],
  },
  {
    id: "notion-pages",
    name: "Pages",
    description: "Fetch recently modified pages for documentation evidence",
    evidenceCategories: ["documentation", "knowledge_management"],
  },
  {
    id: "notion-members",
    name: "Workspace Members",
    description: "Fetch workspace member list and role assignments",
    evidenceCategories: ["access_control", "identity_management"],
  },
];

export class NotionConnector implements IntegrationConnector {
  readonly id = "notion";
  readonly name = "Notion";
  readonly category = "workspace" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string,
    body?: Record<string, unknown>
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.notion.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      method: body ? "POST" : "GET",
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!resp.ok) throw new Error(`Notion API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/search", { page_size: 1 });
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const databases = await this.fetchApi(config, "/search", {
      filter: { property: "object", value: "database" },
      page_size: 50,
    }).catch(() => ({ results: [] }));
    const dbList = (databases.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "notion-databases",
      timestamp: now,
      hash: hashEvidence({ databaseCount: dbList.length }),
      framework: "SOC2",
      controlId: "CC7.1",
      source: "notion/databases",
      status: dbList.length > 0 ? "compliant" : "non_compliant",
      data: { databaseCount: dbList.length },
      metadata: {},
    });

    const pages = await this.fetchApi(config, "/search", {
      filter: { property: "object", value: "page" },
      page_size: 50,
    }).catch(() => ({ results: [] }));
    const pageList = (pages.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "notion-pages",
      timestamp: now,
      hash: hashEvidence({ pageCount: pageList.length }),
      framework: "ISO27001",
      controlId: "A.7.2.2",
      source: "notion/pages",
      status: "unknown",
      data: { pageCount: pageList.length },
      metadata: {},
    });

    const users = await this.fetchApi(config, "/users").catch(() => ({ results: [] }));
    const userList = (users.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "notion-members",
      timestamp: now,
      hash: hashEvidence({ memberCount: userList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "notion/users",
      status: "unknown",
      data: { memberCount: userList.length },
      metadata: {},
    });

    return artifacts;
  }
}
