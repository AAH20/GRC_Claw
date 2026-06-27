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
    id: "confluence-spaces",
    name: "Spaces",
    description: "Fetch Confluence spaces and their configurations",
    evidenceCategories: ["documentation", "configuration"],
  },
  {
    id: "confluence-pages",
    name: "Pages",
    description: "Fetch recently updated pages for policy and procedure documentation evidence",
    evidenceCategories: ["documentation", "policy_management"],
  },
  {
    id: "confluence-permissions",
    name: "Space Permissions",
    description: "Fetch space-level permission and access configurations",
    evidenceCategories: ["access_control", "data_protection"],
  },
];

export class ConfluenceConnector implements IntegrationConnector {
  readonly id = "confluence";
  readonly name = "Confluence";
  readonly category = "documentation" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.atlassian.com/ex/confluence";
    const cloudId = config.extra?.cloudId || "";
    const resp = await fetch(`${base}/wiki/api/v2${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Confluence API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/space?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const spaces = await this.fetchApi(config, "/space?limit=50").catch(() => ({ results: [] }));
    const spaceList = (spaces.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "confluence-spaces",
      timestamp: now,
      hash: hashEvidence({ spaceCount: spaceList.length }),
      framework: "ISO27001",
      controlId: "A.7.2.2",
      source: "confluence/space",
      status: spaceList.length > 0 ? "compliant" : "non_compliant",
      data: { spaceCount: spaceList.length },
      metadata: { cloudId: config.extra?.cloudId || "" },
    });

    const pages = await this.fetchApi(config, "/pages?limit=50&sort=-modified_date").catch(() => ({ results: [] }));
    const pageList = (pages.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "confluence-pages",
      timestamp: now,
      hash: hashEvidence({ pageCount: pageList.length }),
      framework: "SOC2",
      controlId: "CC7.1",
      source: "confluence/pages",
      status: "unknown",
      data: { pageCount: pageList.length },
      metadata: { cloudId: config.extra?.cloudId || "" },
    });

    const permissions = await this.fetchApi(config, "/space?limit=50").catch(() => ({ results: [] }));
    const permList = (permissions.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "confluence-permissions",
      timestamp: now,
      hash: hashEvidence({ spaceCount: permList.length }),
      framework: "ISO27001",
      controlId: "A.9.1.2",
      source: "confluence/permissions",
      status: "unknown",
      data: { spaceCount: permList.length },
      metadata: { cloudId: config.extra?.cloudId || "" },
    });

    return artifacts;
  }
}
