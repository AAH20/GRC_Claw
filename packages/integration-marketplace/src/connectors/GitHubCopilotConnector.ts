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
    id: "github-copilot-usage",
    name: "Copilot Usage",
    description: "Fetch GitHub Copilot usage statistics and acceptance rates",
    evidenceCategories: ["monitoring", "configuration"],
  },
  {
    id: "github-copilot-policies",
    name: "Copilot Policies",
    description: "Fetch GitHub Copilot content exclusions and organization policies",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "github-copilot-security",
    name: "Code Suggestions Audit",
    description: "Fetch audit events for Copilot code suggestion acceptances and blocks",
    evidenceCategories: ["audit", "data_protection"],
  },
];

export class GitHubCopilotConnector implements IntegrationConnector {
  readonly id = "github-copilot";
  readonly name = "GitHub Copilot";
  readonly category = "version_control" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.github.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
      },
    });
    if (!resp.ok) throw new Error(`GitHub Copilot API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const org = config.extra?.org || "default";
      await this.fetchApi(config, `/orgs/${org}/copilot/usage`);
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const org = config.extra?.org || "default";

    const usage = await this.fetchApi(
      config,
      `/orgs/${org}/copilot/usage`
    ).catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "github-copilot-usage",
      timestamp: now,
      hash: hashEvidence(usage),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "github-copilot/usage",
      status: "unknown",
      data: { connected: true },
      metadata: { org },
    });

    return artifacts;
  }
}
