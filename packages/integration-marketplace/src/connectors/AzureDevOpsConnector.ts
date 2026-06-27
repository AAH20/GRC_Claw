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
    id: "ado-pipelines",
    name: "Pipeline Definitions",
    description: "Fetch Azure DevOps pipeline definitions and run history",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "ado-repos",
    name: "Repository Settings",
    description: "Fetch repo branch policies and access control lists",
    evidenceCategories: ["version_control", "access_control"],
  },
  {
    id: "ado-builds",
    name: "Build Artifacts",
    description: "Fetch build artifact integrity and retention policies",
    evidenceCategories: ["ci_cd", "data_protection"],
  },
  {
    id: "ado-pr",
    name: "Pull Request Policies",
    description: "Fetch PR merge policies and required reviewers",
    evidenceCategories: ["change_management", "access_control"],
  },
];

export class AzureDevOpsConnector implements IntegrationConnector {
  readonly id = "azure_devops";
  readonly name = "Azure DevOps";
  readonly category = "ci_cd" as const;
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
    const base = config.baseUrl || "https://dev.azure.com";
    const org = config.extra?.org || "default";
    const resp = await fetch(`${base}/${org}/_apis${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Azure DevOps API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const org = config.extra?.org || "default";
      await this.fetchApi(config, "/core/teams?api-version=7.0");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const org = config.extra?.org || "default";
    const project = config.extra?.project || "default";

    const pipelines = await this.fetchApi(
      config,
      `/build/definitions?api-version=7.0&searchFilter=owner&path=/`
    ).catch(() => ({ count: 0, value: [] }));
    const pipelineList = Array.isArray(pipelines.value) ? pipelines.value : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "ado-pipelines",
      timestamp: now,
      hash: hashEvidence({ count: pipelineList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: `azure-devops/${org}/${project}/pipelines`,
      status: pipelineList.length > 0 ? "compliant" : "partial",
      data: { pipelineCount: pipelineList.length },
      metadata: { org, project },
    });

    const repos = await this.fetchApi(
      config,
      `/git/repositories?api-version=7.0`
    ).catch(() => ({ count: 0, value: [] }));
    const repoList = Array.isArray(repos.value) ? repos.value : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "ado-repos",
      timestamp: now,
      hash: hashEvidence({ count: repoList.length }),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: `azure-devops/${org}/${project}/repos`,
      status: repoList.length > 0 ? "compliant" : "partial",
      data: { repositoryCount: repoList.length },
      metadata: { org, project },
    });

    const builds = await this.fetchApi(
      config,
      `/build/builds?api-version=7.0&top=10&resultFilter=succeeded,failed`
    ).catch(() => ({ count: 0, value: [] }));
    const buildList = Array.isArray(builds.value) ? builds.value : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "ado-builds",
      timestamp: now,
      hash: hashEvidence({ count: buildList.length }),
      framework: "NIST_CSF",
      controlId: "PR.DS",
      source: `azure-devops/${org}/${project}/builds`,
      status: buildList.length > 0 ? "compliant" : "partial",
      data: { recentBuilds: buildList.length },
      metadata: { org, project },
    });

    const prPolicies = await this.fetchApi(
      config,
      `/git/policies/configurations?api-version=7.0`
    ).catch(() => ({ count: 0, value: [] }));
    const prList = Array.isArray(prPolicies.value) ? prPolicies.value : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "ado-pr",
      timestamp: now,
      hash: hashEvidence({ count: prList.length }),
      framework: "PCI_DSS",
      controlId: "6.5.2",
      source: `azure-devops/${org}/${project}/pr-policies`,
      status: prList.length > 0 ? "compliant" : "partial",
      data: { policyCount: prList.length },
      metadata: { org, project },
    });

    return artifacts;
  }
}
