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
    id: "jenkins-jobs",
    name: "Build Jobs",
    description: "Fetch Jenkins job configurations and build history",
    evidenceCategories: ["change_management", "configuration"],
  },
  {
    id: "jenkins-plugins",
    name: "Plugins & Security",
    description: "Fetch installed plugins and security configurations",
    evidenceCategories: ["vulnerability_management", "configuration"],
  },
  {
    id: "jenkins-credentials",
    name: "Credential Management",
    description: "Fetch credential store configurations and usage",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "jenkins-audit",
    name: "Audit Trail",
    description: "Fetch Jenkins audit log and user activity",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class JenkinsConnector implements IntegrationConnector {
  readonly id = "jenkins";
  readonly name = "Jenkins";
  readonly category = "ci_cd" as const;
  readonly authType = "api_key" as const;
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
    const base = config.baseUrl || "https://jenkins.example.com";
    const resp = await fetch(`${base}${endpoint}`, {
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
      await this.fetchApi(config, "/api/json");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const jobs = await this.fetchApi(config, "/api/json?tree=jobs[name,url,color]").catch(() => ({
      jobs: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "jenkins-jobs",
      timestamp: now,
      hash: hashEvidence(jobs),
      framework: "SOC2",
      controlId: "CC8.1",
      source: "jenkins/jobs",
      status: (jobs.jobs as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { jobCount: (jobs.jobs as unknown[])?.length || 0 },
      metadata: {},
    });

    const plugins = await this.fetchApi(config, "/pluginManager/api/json?tree=shortName,version").catch(
      () => ({ plugins: [] })
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "jenkins-plugins",
      timestamp: now,
      hash: hashEvidence(plugins),
      framework: "ISO27001",
      controlId: "A.12.6.1",
      source: "jenkins/plugins",
      status: "partial",
      data: { installedPlugins: (plugins.plugins as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
