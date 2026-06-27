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
    id: "gha-workflow-runs",
    name: "Workflow Runs",
    description: "Fetch GitHub Actions workflow run history and statuses",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "gha-security-alerts",
    name: "Security Alerts",
    description: "Fetch Dependabot alerts from GitHub Actions",
    evidenceCategories: ["vulnerability_management", "supply_chain"],
  },
  {
    id: "gha-dependency-reviews",
    name: "Dependency Reviews",
    description: "Fetch dependency review advisories on pull requests",
    evidenceCategories: ["supply_chain", "vulnerability_management"],
  },
];

export class GitHubActionsConnector implements IntegrationConnector {
  readonly id = "github-actions";
  readonly name = "GitHub Actions";
  readonly category = "ci_cd" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

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
    if (!resp.ok) throw new Error(`GitHub API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/user");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const org = config.extra?.org || "default";
    const repo = config.extra?.repo || "main-repo";

    const runs = await this.fetchApi(
      config,
      `/repos/${org}/${repo}/actions/runs?per_page=100&status=completed`
    ).catch(() => ({ workflow_runs: [] }));
    const runList = (runs.workflow_runs || []) as Record<string, unknown>[];
    const failed = runList.filter((r) => r.conclusion === "failure");
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gha-workflow-runs",
      timestamp: now,
      hash: hashEvidence({ totalRuns: runList.length, failedRuns: failed.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `github.com/${org}/${repo}/actions/runs`,
      status: failed.length === 0 ? "compliant" : "partial",
      data: { totalRuns: runList.length, failedRuns: failed.length, successRate: runList.length > 0 ? ((runList.length - failed.length) / runList.length * 100).toFixed(1) + "%" : "N/A" },
      metadata: { org, repo },
    });

    const alerts = await this.fetchApi(
      config,
      `/repos/${org}/${repo}/vulnerability-alerts`
    ).catch(() => ({ enabled: false }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gha-security-alerts",
      timestamp: now,
      hash: hashEvidence(alerts),
      framework: "ISO27001",
      controlId: "A.12.6.1",
      source: `github.com/${org}/${repo}/vulnerability-alerts`,
      status: alerts.enabled === true ? "compliant" : "non_compliant",
      data: { vulnerabilityAlertsEnabled: alerts.enabled },
      metadata: { org, repo },
    });

    const depReview = await this.fetchApi(
      config,
      `/repos/${org}/${repo}/dependency-graph/dependency-review?per_page=50`
    ).catch(() => ({ dependencies: [] }));
    const depList = (depReview.dependencies || []) as Record<string, unknown>[];
    const vulnerable = depList.filter(
      (d) => (d.severity as string) === "critical" || (d.severity as string) === "high"
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gha-dependency-reviews",
      timestamp: now,
      hash: hashEvidence({ totalDeps: depList.length, vulnerableDeps: vulnerable.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `github.com/${org}/${repo}/dependency-review`,
      status: vulnerable.length === 0 ? "compliant" : "non_compliant",
      data: { totalDeps: depList.length, vulnerableDeps: vulnerable.length },
      metadata: { org, repo },
    });

    return artifacts;
  }
}
