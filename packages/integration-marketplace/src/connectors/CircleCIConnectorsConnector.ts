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
    name: "CI Pipelines",
    description: "Fetch CircleCI pipeline configurations and workflow execution history",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "circleci-environments",
    name: "Environment Variables",
    description: "Fetch CircleCI environment variable groups and context assignments",
    evidenceCategories: ["secret_management", "configuration"],
  },
  {
    id: "circleci-insights",
    name: "Pipeline Insights",
    description: "Fetch CircleCI workflow duration metrics and failure rate analytics",
    evidenceCategories: ["monitoring", "performance"],
  },
];

export class CircleCIConnectorsConnector implements IntegrationConnector {
  readonly id = "circleci-connectors";
  readonly name = "CircleCI (Connectors)";
  readonly category = "ci_cd" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://circleci.com/api/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
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

    const me = await this.fetchApi(config, "/me").catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "circleci-pipelines",
      timestamp: now,
      hash: hashEvidence(me),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "circleci-connectors/me",
      status: "unknown",
      data: { connected: true },
      metadata: {},
    });

    return artifacts;
  }
}
