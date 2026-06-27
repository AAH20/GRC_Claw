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
    id: "snyk-vulns",
    name: "Vulnerabilities",
    description: "Fetch Snyk project vulnerabilities by severity",
    evidenceCategories: ["vulnerability_management", "application_security"],
  },
  {
    id: "snyk-license",
    name: "License Compliance",
    description: "Fetch open-source license compliance issues",
    evidenceCategories: ["license_compliance", "supply_chain"],
  },
];

export class SnykConnector implements IntegrationConnector {
  readonly id = "snyk";
  readonly name = "Snyk";
  readonly category = "vulnerability" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.snyk.io/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `token ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`Snyk API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/user/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const orgId = config.extra?.orgId || "";
    const projectId = config.extra?.projectId || "";

    const issues = await this.fetchApi(
      config,
      `/orgs/${orgId}/projects/${projectId}/issues?severityThreshold=low`
    ).catch(() => ({ issues: [] }));
    const issueList = (issues.issues || []) as Record<string, unknown>[];
    const bySeverity = {
      critical: issueList.filter((i) => (i.severity as string) === "critical").length,
      high: issueList.filter((i) => (i.severity as string) === "high").length,
      medium: issueList.filter((i) => (i.severity as string) === "medium").length,
      low: issueList.filter((i) => (i.severity as string) === "low").length,
    };
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snyk-vulns",
      timestamp: now,
      hash: hashEvidence({ issueCount: issueList.length, bySeverity }),
      framework: "ISO27001",
      controlId: "A.12.6.1",
      source: `snyk/orgs/${orgId}/projects/${projectId}/issues`,
      status: bySeverity.critical === 0 ? "compliant" : "non_compliant",
      data: { totalIssues: issueList.length, bySeverity },
      metadata: { orgId, projectId },
    });

    const licenses = await this.fetchApi(
      config,
      `/orgs/${orgId}/projects/${projectId}/issues?severityThreshold=low&types=license`
    ).catch(() => ({ issues: [] }));
    const licenseIssues = (licenses.issues || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snyk-license",
      timestamp: now,
      hash: hashEvidence({ licenseIssueCount: licenseIssues.length }),
      framework: "ISO27001",
      controlId: "A.18.1.5",
      source: `snyk/orgs/${orgId}/projects/${projectId}/licenses`,
      status: licenseIssues.length === 0 ? "compliant" : "non_compliant",
      data: { licenseIssues: licenseIssues.length },
      metadata: { orgId, projectId },
    });

    return artifacts;
  }
}
