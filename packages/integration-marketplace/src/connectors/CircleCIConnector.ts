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
    id: "circleci-pipelines",
    name: "Pipeline Runs",
    description: "Fetch CircleCI pipeline and workflow run history",
    evidenceCategories: ["ci_cd", "monitoring"],
  },
  {
    id: "circleci-config",
    name: "Pipeline Configuration",
    description: "Fetch CircleCI pipeline configuration and orb usage",
    evidenceCategories: ["ci_cd", "configuration"],
  },
  {
    id: "circleci-insights",
    name: "Pipeline Insights",
    description: "Fetch CircleCI pipeline performance and failure metrics",
    evidenceCategories: ["monitoring", "change_management"],
  },
  {
    id: "circleci-contexts",
    name: "Contexts & Secrets",
    description: "Fetch CircleCI context and environment variable configurations",
    evidenceCategories: ["access_control", "data_protection"],
  },
];

export class CircleCIConnector implements IntegrationConnector {
  readonly id = "circleci";
  readonly name = "CircleCI";
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
    const base = config.baseUrl || "https://circleci.com/api/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        "Circle-Token": config.apiToken || "",
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`CircleCI API ${resp.status}: ${resp.statusText}`);
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
    const projectSlug = config.extra?.projectSlug || "gh/default/project";

    const pipelines = await this.fetchApi(
      config,
      `/project/${encodeURIComponent(projectSlug)}/pipeline?limit=10`
    ).catch(() => ({ items: [] }));
    const pipelineList = Array.isArray(pipelines.items) ? pipelines.items : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "circleci-pipelines",
      timestamp: now,
      hash: hashEvidence({ count: pipelineList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `circleci/${projectSlug}/pipelines`,
      status: pipelineList.length > 0 ? "compliant" : "partial",
      data: { recentPipelines: pipelineList.length },
      metadata: { projectSlug },
    });

    const configData = await this.fetchApi(
      config,
      `/project/${encodeURIComponent(projectSlug)}/config`
    ).catch(() => ({ output: "" }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "circleci-config",
      timestamp: now,
      hash: hashEvidence({ hasConfig: !!configData.output }),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: `circleci/${projectSlug}/config`,
      status: configData.output ? "compliant" : "partial",
      data: { hasConfig: !!configData.output },
      metadata: { projectSlug },
    });

    const insights = await this.fetchApi(
      config,
      `/insights/${encodeURIComponent(projectSlug)}/workflows?limit=10`
    ).catch(() => ({ items: [] }));
    const insightList = Array.isArray(insights.items) ? insights.items : [];
    const failedWorkflows = insightList.filter(
      (w: Record<string, unknown>) => w.status === "failed"
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "circleci-insights",
      timestamp: now,
      hash: hashEvidence({ total: insightList.length, failed: failedWorkflows.length }),
      framework: "NIST_CSF",
      controlId: "DE.CM",
      source: `circleci/${projectSlug}/insights`,
      status: failedWorkflows.length === 0 ? "compliant" : "partial",
      data: {
        recentWorkflows: insightList.length,
        failedWorkflows: failedWorkflows.length,
      },
      metadata: { projectSlug },
    });

    const contexts = await this.fetchApi(config, "/context").catch(() => ({ items: [] }));
    const contextList = Array.isArray(contexts.items) ? contexts.items : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "circleci-contexts",
      timestamp: now,
      hash: hashEvidence({ count: contextList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `circleci/${projectSlug}/contexts`,
      status: contextList.length > 0 ? "compliant" : "partial",
      data: { contextCount: contextList.length },
      metadata: { projectSlug },
    });

    return artifacts;
  }
}
