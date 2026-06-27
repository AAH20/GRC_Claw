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
    name: "Monitored Vulnerabilities",
    description: "Fetch Snyk monitor vulnerability findings across projects",
    evidenceCategories: ["vulnerability_management", "supply_chain"],
  },
  {
    id: "snyk-licenses",
    name: "License Compliance",
    description: "Fetch license compliance results and policy violations",
    evidenceCategories: ["compliance", "supply_chain"],
  },
  {
    id: "snyk-issues",
    name: "Open Issues",
    description: "Fetch open Snyk issues with fix availability",
    evidenceCategories: ["vulnerability_management", "change_management"],
  },
  {
    id: "snyk-org",
    name: "Organization Settings",
    description: "Fetch Snyk org settings, RBAC, and integrations",
    evidenceCategories: ["access_control", "configuration"],
  },
];

export class SnykMonitorConnector implements IntegrationConnector {
  readonly id = "snyk_monitor";
  readonly name = "Snyk Monitor";
  readonly category = "vulnerability" as const;
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
    const base = config.baseUrl || "https://api.snyk.io/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `token ${config.apiToken}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Snyk API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/orgs");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const orgId = config.extra?.orgId || "default-org";
    const projectId = config.extra?.projectId || "";

    const issues = await this.fetchApi(
      config,
      `/orgs/${orgId}/issues?limit=100&severity=high,critical`
    ).catch(() => ({ issues: [] }));
    const issueList = Array.isArray(issues.issues) ? issues.issues : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snyk-vulns",
      timestamp: now,
      hash: hashEvidence({ count: issueList.length }),
      framework: "SOC2",
      controlId: "CC6.6",
      source: `snyk/${orgId}/vulnerabilities`,
      status: issueList.length === 0 ? "compliant" : "non_compliant",
      data: { highCriticalIssues: issueList.length },
      metadata: { orgId },
    });

    const licenses = await this.fetchApi(
      config,
      `/orgs/${orgId}/licenses?limit=50`
    ).catch(() => ({ licenses: [] }));
    const licenseList = Array.isArray(licenses.licenses) ? licenses.licenses : [];
    const deniedLicenses = licenseList.filter(
      (l: Record<string, unknown>) => l.compatibility === "not_compatible"
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snyk-licenses",
      timestamp: now,
      hash: hashEvidence({ count: licenseList.length, denied: deniedLicenses.length }),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: `snyk/${orgId}/licenses`,
      status: deniedLicenses.length === 0 ? "compliant" : "non_compliant",
      data: { totalLicenses: licenseList.length, denied: deniedLicenses.length },
      metadata: { orgId },
    });

    const openIssues = projectId
      ? await this.fetchApi(
          config,
          `/orgs/${orgId}/projects/${projectId}/issues?limit=50`
        ).catch(() => ({ issues: [] }))
      : { issues: [] };
    const openList = Array.isArray(openIssues.issues) ? openIssues.issues : [];
    const fixable = openList.filter(
      (i: Record<string, unknown>) => i.fixable === true
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snyk-issues",
      timestamp: now,
      hash: hashEvidence({ open: openList.length, fixable: fixable.length }),
      framework: "NIST_CSF",
      controlId: "ID.RA",
      source: `snyk/${orgId}/issues`,
      status: openList.length === 0 ? "compliant" : "non_compliant",
      data: { openIssues: openList.length, fixableIssues: fixable.length },
      metadata: { orgId },
    });

    const org = await this.fetchApi(config, `/orgs/${orgId}`).catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snyk-org",
      timestamp: now,
      hash: hashEvidence(org),
      framework: "PCI_DSS",
      controlId: "7.2.1",
      source: `snyk/${orgId}/settings`,
      status: "compliant",
      data: org,
      metadata: { orgId },
    });

    return artifacts;
  }
}
