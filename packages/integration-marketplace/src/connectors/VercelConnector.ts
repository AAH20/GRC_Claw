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
    id: "vercel-projects",
    name: "Vercel Projects",
    description: "Fetch Vercel project configurations, domains, and deployment settings",
    evidenceCategories: ["cloud_configuration", "ci_cd"],
  },
  {
    id: "vercel-deployments",
    name: "Deployment History",
    description: "Fetch recent deployment history, build logs, and rollback status",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "vercel-security",
    name: "Security Headers",
    description: "Fetch Vercel security headers, CSP policies, and firewall rules",
    evidenceCategories: ["network_security", "configuration"],
  },
];

export class VercelConnector implements IntegrationConnector {
  readonly id = "vercel";
  readonly name = "Vercel";
  readonly category = "ci_cd" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.vercel.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Vercel API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/v9/projects?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const projects = await this.fetchApi(config, "/v9/projects?limit=100").catch(() => ({ projects: [] }));
    const projectList = (projects.projects || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "vercel-projects",
      timestamp: now,
      hash: hashEvidence({ projectCount: projectList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "vercel/projects",
      status: "unknown",
      data: { projectCount: projectList.length },
      metadata: {},
    });

    return artifacts;
  }
}
