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
    id: "jira-projects",
    name: "Project Configuration",
    description: "Fetch project settings, schemes, and workflow configurations",
    evidenceCategories: ["configuration", "access_control"],
  },
  {
    id: "jira-permissions",
    name: "Permission Schemes",
    description: "Fetch permission schemes and role assignments",
    evidenceCategories: ["access_control"],
  },
  {
    id: "jira-audit-log",
    name: "Audit Log",
    description: "Fetch audit trail of administrative and issue changes",
    evidenceCategories: ["audit", "change_management"],
  },
  {
    id: "jira-security-issues",
    name: "Security Issue Tracking",
    description: "Fetch security-labeled issues and SLA compliance",
    evidenceCategories: ["vulnerability_management", "incident_management"],
  },
];

export class AtlassianJiraConnector implements IntegrationConnector {
  readonly id = "atlassian_jira";
  readonly name = "Atlassian Jira";
  readonly category = "project_management" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://your-domain.atlassian.net";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Jira API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/rest/api/3/myself");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const projectKey = config.extra?.projectKey || "SEC";

    const myself = await this.fetchApi(config, "/rest/api/3/myself");
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "jira-projects",
      timestamp: now,
      hash: hashEvidence(myself),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `jira/${projectKey}/projects`,
      status: "compliant",
      data: {
        user: myself.emailAddress,
        locale: myself.locale,
        active: myself.active,
      },
      metadata: { projectKey },
    });

    const permissions = await this.fetchApi(
      config,
      `/rest/api/3/permissionscheme`
    ).catch(() => ({ values: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "jira-permissions",
      timestamp: now,
      hash: hashEvidence(permissions),
      framework: "SOC2",
      controlId: "CC6.3",
      source: `jira/${projectKey}/permissions`,
      status: Array.isArray(permissions.values) && permissions.values.length > 0
        ? "compliant"
        : "partial",
      data: { schemeCount: Array.isArray(permissions.values) ? permissions.values.length : 0 },
      metadata: { projectKey },
    });

    const auditLog = await this.fetchApi(
      config,
      `/rest/api/3/audit/record?limit=20`
    ).catch(() => ({ records: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "jira-audit-log",
      timestamp: now,
      hash: hashEvidence(auditLog),
      framework: "ISO27001",
      controlId: "A.12.4.1",
      source: `jira/${projectKey}/audit`,
      status: Array.isArray(auditLog.records) && auditLog.records.length > 0
        ? "compliant"
        : "partial",
      data: { recordCount: Array.isArray(auditLog.records) ? auditLog.records.length : 0 },
      metadata: { projectKey },
    });

    const securityIssues = await this.fetchApi(
      config,
      `/rest/api/3/search?jql=project=${projectKey}%20AND%20labels=security&maxResults=10`
    ).catch(() => ({ issues: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "jira-security-issues",
      timestamp: now,
      hash: hashEvidence(securityIssues),
      framework: "NIST_CSF",
      controlId: "RS.AN",
      source: `jira/${projectKey}/security-issues`,
      status: Array.isArray(securityIssues.issues)
        ? securityIssues.issues.length === 0
          ? "compliant"
          : "non_compliant"
        : "unknown",
      data: { openSecurityIssues: Array.isArray(securityIssues.issues) ? securityIssues.issues.length : 0 },
      metadata: { projectKey },
    });

    return artifacts;
  }
}
