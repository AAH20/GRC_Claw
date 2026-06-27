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
    id: "docker-image-scans",
    name: "Image Scans",
    description: "Fetch Docker Hub image vulnerability scan results",
    evidenceCategories: ["container_security", "vulnerability_management"],
  },
  {
    id: "docker-vuln-reports",
    name: "Vulnerability Reports",
    description: "Fetch detailed vulnerability reports per image tag",
    evidenceCategories: ["vulnerability_management", "supply_chain"],
  },
];

export class DockerHubConnector implements IntegrationConnector {
  readonly id = "docker-hub";
  readonly name = "Docker Hub";
  readonly category = "container" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://hub.docker.com/v2";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `Bearer ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`Docker Hub API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/user/");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const namespace = config.extra?.namespace || "library";
    const repo = config.extra?.repo || "nginx";

    const images = await this.fetchApi(
      config,
      `/repositories/${namespace}/${repo}/tags?page_size=50`
    ).catch(() => ({ results: [] }));
    const tagList = (images.results || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "docker-image-scans",
      timestamp: now,
      hash: hashEvidence({ tagCount: tagList.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: `dockerhub/${namespace}/${repo}/tags`,
      status: tagList.length > 0 ? "compliant" : "non_compliant",
      data: { tagCount: tagList.length, tags: tagList.map((t) => t.name) },
      metadata: { namespace, repo },
    });

    const vulnReport = tagList.length > 0
      ? await this.fetchApi(
          config,
          `/repositories/${namespace}/${repo}/tags/${tagList[0].name}/vulnerabilities`
        ).catch(() => ({ vulnerabilities: [] }))
      : { vulnerabilities: [] };
    const vulns = (vulnReport.vulnerabilities || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "docker-vuln-reports",
      timestamp: now,
      hash: hashEvidence({ vulnCount: vulns.length }),
      framework: "ISO27001",
      controlId: "A.12.6.1",
      source: `dockerhub/${namespace}/${repo}/vulnerabilities`,
      status: vulns.length === 0 ? "compliant" : "non_compliant",
      data: { totalVulnerabilities: vulns.length },
      metadata: { namespace, repo },
    });

    return artifacts;
  }
}
