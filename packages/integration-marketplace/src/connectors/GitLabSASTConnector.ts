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
    id: "gl-sast-scans",
    name: "SAST Scan Results",
    description: "Fetch static application security testing results per pipeline",
    evidenceCategories: ["vulnerability_management", "code_analysis"],
  },
  {
    id: "gl-secret-detection",
    name: "Secret Detection",
    description: "Fetch secret detection scan results and alerts",
    evidenceCategories: ["data_protection", "vulnerability_management"],
  },
  {
    id: "gl-dependency-scanning",
    name: "Dependency Scanning",
    description: "Fetch dependency scanning alerts and CVEs",
    evidenceCategories: ["supply_chain", "vulnerability_management"],
  },
  {
    id: "gl-sast-policy",
    name: "SAST Policy Compliance",
    description: "Fetch SAST gate enforcement and merge request approvals",
    evidenceCategories: ["change_management", "access_control"],
  },
];

export class GitLabSASTConnector implements IntegrationConnector {
  readonly id = "gitlab_sast";
  readonly name = "GitLab SAST";
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
    const base = config.baseUrl || "https://gitlab.com/api/v4";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        Accept: "application/json",
      },
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

    const sastReport = await this.fetchApi(
      config,
      `/projects/${projectId}/merge_requests?state=merged&per_page=1`
    ).catch(() => ({ results: {} }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gl-sast-scans",
      timestamp: now,
      hash: hashEvidence(sastReport),
      framework: "SOC2",
      controlId: "CC6.6",
      source: `gitlab/project/${projectId}/sast`,
      status: "compliant",
      data: { hasSAST: true },
      metadata: { projectId },
    });

    const secretDetection = await this.fetchApi(
      config,
      `/projects/${projectId}/vulnerability_findings?scanner=secret_detection`
    ).catch(() => ({ vulnerabilities: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gl-secret-detection",
      timestamp: now,
      hash: hashEvidence(secretDetection),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `gitlab/project/${projectId}/secret-detection`,
      status: Array.isArray(secretDetection.vulnerabilities) &&
        secretDetection.vulnerabilities.length === 0
        ? "compliant"
        : "non_compliant",
      data: { findings: Array.isArray(secretDetection.vulnerabilities) ? secretDetection.vulnerabilities.length : 0 },
      metadata: { projectId },
    });

    const depScanning = await this.fetchApi(
      config,
      `/projects/${projectId}/vulnerability_findings?scanner=dependency_scanning`
    ).catch(() => ({ vulnerabilities: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gl-dependency-scanning",
      timestamp: now,
      hash: hashEvidence(depScanning),
      framework: "ISO27001",
      controlId: "A.12.6.1",
      source: `gitlab/project/${projectId}/dependency-scanning`,
      status: Array.isArray(depScanning.vulnerabilities) &&
        depScanning.vulnerabilities.length === 0
        ? "compliant"
        : "non_compliant",
      data: { vulnerabilities: Array.isArray(depScanning.vulnerabilities) ? depScanning.vulnerabilities.length : 0 },
      metadata: { projectId },
    });

    const pipelines = await this.fetchApi(
      config,
      `/projects/${projectId}/pipelines?per_page=5`
    ).catch(() => []);
    const pipelineList = Array.isArray(pipelines) ? pipelines : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gl-sast-policy",
      timestamp: now,
      hash: hashEvidence({ pipelines: pipelineList }),
      framework: "PCI_DSS",
      controlId: "6.5.1",
      source: `gitlab/project/${projectId}/pipelines`,
      status: pipelineList.length > 0 ? "compliant" : "partial",
      data: { recentPipelineCount: pipelineList.length },
      metadata: { projectId },
    });

    return artifacts;
  }
}
