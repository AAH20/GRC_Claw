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
    id: "buildkite-pipelines",
    name: "Pipeline Configurations",
    description: "Fetch pipeline definitions and step configurations",
    evidenceCategories: ["change_management", "configuration"],
  },
  {
    id: "buildkite-builds",
    name: "Build Results",
    description: "Fetch build history and test results",
    evidenceCategories: ["change_management", "monitoring"],
  },
  {
    id: "buildkite-agents",
    name: "Agent Pools",
    description: "Fetch agent pool configurations and fleet status",
    evidenceCategories: ["infrastructure", "configuration"],
  },
  {
    id: "buildkite-secrets",
    name: "Secret Management",
    description: "Fetch encrypted secrets and environment configurations",
    evidenceCategories: ["data_protection", "access_control"],
  },
];

export class BuildkiteConnector implements IntegrationConnector {
  readonly id = "buildkite";
  readonly name = "Buildkite";
  readonly category = "ci_cd" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.buildkite.com/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Buildkite API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/organizations");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const org = config.extra?.org || "default";
    const pipeline = config.extra?.pipeline || "main";

    const builds = await this.fetchApi(
      config,
      `/organizations/${org}/pipelines/${pipeline}/builds?per_page=10`
    ).catch(() => []);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "buildkite-pipelines",
      timestamp: now,
      hash: hashEvidence(Array.isArray(builds) ? { builds: builds.length } : builds),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `buildkite.com/${org}/${pipeline}`,
      status: Array.isArray(builds) && builds.length > 0 ? "compliant" : "unknown",
      data: { recentBuilds: Array.isArray(builds) ? builds.length : 0 },
      metadata: { org, pipeline },
    });

    const agents = await this.fetchApi(
      config,
      `/organizations/${org}/agent-groups`
    ).catch(() => []);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "buildkite-agents",
      timestamp: now,
      hash: hashEvidence(Array.isArray(agents) ? { groups: agents.length } : agents),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: `buildkite.com/${org}/agents`,
      status: "partial",
      data: { agentGroups: Array.isArray(agents) ? agents.length : 0 },
      metadata: { org },
    });

    return artifacts;
  }
}
