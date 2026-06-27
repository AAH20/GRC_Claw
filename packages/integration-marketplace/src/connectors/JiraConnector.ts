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
    id: "jira-projects",
    name: "Jira Projects",
    description: "Fetch Jira project configurations and permissions",
    evidenceCategories: ["project_management", "access_control"],
  },
  {
    id: "jira-workflows",
    name: "Workflows",
    description: "Fetch workflow configurations and approval gates",
    evidenceCategories: ["change_management"],
  },
  {
    id: "jira-sla",
    name: "SLA Compliance",
    description: "Fetch SLA compliance metrics and breach history",
    evidenceCategories: ["service_management"],
  },
];

export class JiraConnector implements IntegrationConnector {
  readonly id = "jira";
  readonly name = "Jira";
  readonly category = "project_management" as const;
  readonly authType = "basic_auth" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://your-domain.atlassian.net";
    const resp = await fetch(`${base}/rest/api/3${endpoint}`, {
      headers: {
        Authorization: `Basic ${Buffer.from(`${config.clientId}:${config.apiToken}`).toString("base64")}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Jira API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/myself");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const projects = await this.fetchApi(config, "/project");
    const projectList = Array.isArray(projects) ? projects : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "jira-projects",
      timestamp: now,
      hash: hashEvidence({ projects: projectList.map((p: Record<string, unknown>) => ({ id: p.id, key: p.key })) }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "jira/projects",
      status: "unknown",
      data: { projectCount: projectList.length },
      metadata: { domain: config.baseUrl || "" },
    });

    const workflows = await fetch(
      `${config.baseUrl || "https://your-domain.atlassian.net"}/rest/api/3/workflow`,
      {
        headers: {
          Authorization: `Basic ${Buffer.from(`${config.clientId}:${config.apiToken}`).toString("base64")}`,
          Accept: "application/json",
        },
      }
    ).then((r) => r.json()) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "jira-workflows",
      timestamp: now,
      hash: hashEvidence(workflows),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "jira/workflows",
      status: "unknown",
      data: { workflows },
      metadata: { domain: config.baseUrl || "" },
    });

    const issues = await this.fetchApi(
      config,
      "/search?jql=issuetype=Story&maxResults=0&expand=names"
    ).catch(() => ({ total: 0 }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "jira-sla",
      timestamp: now,
      hash: hashEvidence(issues),
      framework: "ISO27001",
      controlId: "A.12.1.4",
      source: "jira/search",
      status: "unknown",
      data: { totalIssues: issues.total || 0 },
      metadata: { domain: config.baseUrl || "" },
    });

    return artifacts;
  }
}
