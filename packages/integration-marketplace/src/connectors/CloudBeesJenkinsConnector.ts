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
    id: "cloudbees-jenkins-jobs",
    name: "Jenkins Jobs",
    description: "Fetch CloudBees Jenkins job configurations and build history",
    evidenceCategories: ["ci_cd", "change_management"],
  },
  {
    id: "cloudbees-jenkins-agents",
    name: "Jenkins Agents",
    description: "Fetch Jenkins agent configurations and connection status",
    evidenceCategories: ["infrastructure", "monitoring"],
  },
  {
    id: "cloudbees-jenkins-security",
    name: "Jenkins Security",
    description: "Fetch Jenkins security realm configurations and credential scopes",
    evidenceCategories: ["access_control", "secret_management"],
  },
];

export class CloudBeesJenkinsConnector implements IntegrationConnector {
  readonly id = "cloudbees-jenkins";
  readonly name = "CloudBees Jenkins";
  readonly category = "ci_cd" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://jenkins.example.com";
    const resp = await fetch(`${base}/api/json${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Jenkins API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "?tree=name");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const jobs = await this.fetchApi(config, "?tree=jobs[name,url]{0,100}").catch(() => ({ jobs: [] }));
    const jobList = (jobs.jobs || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cloudbees-jenkins-jobs",
      timestamp: now,
      hash: hashEvidence({ jobCount: jobList.length }),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "cloudbees-jenkins/jobs",
      status: "unknown",
      data: { jobCount: jobList.length },
      metadata: {},
    });

    return artifacts;
  }
}
