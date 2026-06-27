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
    id: "gh-repo-settings",
    name: "Repository Settings",
    description: "Fetch repo visibility, default branch, and security settings",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "gh-branch-protection",
    name: "Branch Protection Rules",
    description: "Fetch branch protection policies and required reviews",
    evidenceCategories: ["access_control", "change_management"],
  },
  {
    id: "gh-secret-scanning",
    name: "Secret Scanning",
    description: "Fetch secret scanning alerts and push protection status",
    evidenceCategories: ["data_protection", "vulnerability_management"],
  },
  {
    id: "gh-dependabot",
    name: "Dependabot Alerts",
    description: "Fetch dependency vulnerability alerts and auto-fix PRs",
    evidenceCategories: ["vulnerability_management", "supply_chain"],
  },
];

export class GitHubConnector implements IntegrationConnector {
  readonly id = "github";
  readonly name = "GitHub";
  readonly category = "version_control" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
  ];

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

    const repoData = await this.fetchApi(config, `/repos/${org}/${repo}`);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gh-repo-settings",
      timestamp: now,
      hash: hashEvidence(repoData),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `github.com/${org}/${repo}`,
      status: repoData.private === true ? "compliant" : "partial",
      data: {
        private: repoData.private,
        defaultBranch: repoData.default_branch,
        hasSecurityPolicy: repoData.security_policy_url != null,
        hasVulnerabilityAlerts: (repoData as Record<string, unknown>).security_and_analysis != null,
      },
      metadata: { org, repo },
    });

    const protection = await this.fetchApi(
      config,
      `/repos/${org}/${repo}/branches/main/protection`
    ).catch(() => null);
    if (protection) {
      artifacts.push({
        id: generateEvidenceId(),
        connectorId: this.id,
        capabilityId: "gh-branch-protection",
        timestamp: now,
        hash: hashEvidence(protection),
        framework: "SOC2",
        controlId: "CC8.1",
        source: `github.com/${org}/${repo}/branches/main/protection`,
        status: "compliant",
        data: {
          requiredPullRequestReviews:
            (protection.required_pull_request_reviews as Record<string, unknown>) || null,
          enforceAdmins: (protection.enforce_admins as Record<string, unknown>) || null,
        },
        metadata: { org, repo },
      });
    }

    const secretScanning = await this.fetchApi(
      config,
      `/repos/${org}/${repo}/secret-scanning/alerts?state=open&per_page=10`
    ).catch(() => ({ total_count: 0 }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gh-secret-scanning",
      timestamp: now,
      hash: hashEvidence(secretScanning),
      framework: "SOC2",
      controlId: "CC6.6",
      source: `github.com/${org}/${repo}/secret-scanning`,
      status:
        (secretScanning.total_count as number) === 0 ? "compliant" : "non_compliant",
      data: { openAlerts: secretScanning.total_count },
      metadata: { org, repo },
    });

    const dependabot = await this.fetchApi(
      config,
      `/repos/${org}/${repo}/vulnerability-alerts`
    ).catch(() => ({ enabled: false }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gh-dependabot",
      timestamp: now,
      hash: hashEvidence(dependabot),
      framework: "ISO27001",
      controlId: "A.12.6.1",
      source: `github.com/${org}/${repo}/dependabot`,
      status: dependabot.enabled === true ? "compliant" : "non_compliant",
      data: { enabled: dependabot.enabled },
      metadata: { org, repo },
    });

    return artifacts;
  }
}
