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
    id: "gl-project-settings",
    name: "Project Settings",
    description: "Fetch project visibility, push rules, and container protection",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "gl-mr-approvals",
    name: "Merge Request Approvals",
    description: "Fetch MR approval rules and required reviewers",
    evidenceCategories: ["change_management"],
  },
  {
    id: "gl-sast-results",
    name: "SAST Results",
    description: "Fetch Static Application Security Testing results",
    evidenceCategories: ["vulnerability_management", "application_security"],
  },
];

export class GitLabConnector implements IntegrationConnector {
  readonly id = "gitlab";
  readonly name = "GitLab";
  readonly category = "version_control" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://gitlab.com/api/v4";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `Bearer ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`GitLab API ${resp.status}: ${resp.statusText}`);
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
    const projectId = config.extra?.projectId || "1";

    const project = await this.fetchApi(config, `/projects/${projectId}`);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gl-project-settings",
      timestamp: now,
      hash: hashEvidence(project),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `gitlab.com/projects/${projectId}`,
      status: project.visibility === "private" ? "compliant" : "partial",
      data: {
        visibility: project.visibility,
        requestAccessEnabled: project.request_access_enabled,
        mergeRequestsEnabled: project.merge_requests_enabled,
        jobsEnabled: project.jobs_enabled,
      },
      metadata: { projectId: String(projectId) },
    });

    const approvals = await this.fetchApi(
      config,
      `/projects/${projectId}/approval_rules`
    ).catch(() => []);
    const rules = Array.isArray(approvals) ? approvals : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gl-mr-approvals",
      timestamp: now,
      hash: hashEvidence({ rules }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `gitlab.com/projects/${projectId}/approval_rules`,
      status: rules.length > 0 ? "compliant" : "non_compliant",
      data: { approvalRules: rules },
      metadata: { projectId: String(projectId) },
    });

    const sast = await this.fetchApi(
      config,
      `/projects/${projectId}/security/scans`
    ).catch(() => ({ vulnerabilities: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gl-sast-results",
      timestamp: now,
      hash: hashEvidence(sast),
      framework: "ISO27001",
      controlId: "A.14.2.1",
      source: `gitlab.com/projects/${projectId}/security/scans`,
      status: "unknown",
      data: { scans: sast },
      metadata: { projectId: String(projectId) },
    });

    return artifacts;
  }
}
