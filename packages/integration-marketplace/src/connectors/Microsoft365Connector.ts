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
    id: "m365-users",
    name: "Users & Groups",
    description: "Fetch Microsoft 365 user accounts, licenses, and group memberships",
    evidenceCategories: ["identity_management", "access_control"],
  },
  {
    id: "m365-sharepoint",
    name: "SharePoint Sites",
    description: "Fetch SharePoint site inventory and sharing configurations",
    evidenceCategories: ["document_management", "data_protection"],
  },
  {
    id: "m365-teams",
    name: "Teams Settings",
    description: "Fetch Microsoft Teams policies and external access configurations",
    evidenceCategories: ["communication", "data_protection"],
  },
  {
    id: "m365-exchange",
    name: "Exchange Online",
    description: "Fetch Exchange Online mail flow and security configurations",
    evidenceCategories: ["email_security", "configuration"],
  },
  {
    id: "m365-audit",
    name: "Unified Audit Log",
    description: "Fetch Microsoft 365 unified audit log entries",
    evidenceCategories: ["audit_logging", "compliance"],
  },
];

export class Microsoft365Connector implements IntegrationConnector {
  readonly id = "microsoft-365";
  readonly name = "Microsoft 365";
  readonly category = "workspace" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA", "PCI_DSS"];

  private async fetchGraph(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://graph.microsoft.com/v1.0";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `Bearer ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`Microsoft Graph ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchGraph(config, "/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const users = await this.fetchGraph(config, "/users?$top=100&$select=id,displayName,accountEnabled,assignedLicenses").catch(() => ({ value: [] }));
    const userList = (users.value || []) as Record<string, unknown>[];
    const disabled = userList.filter((u) => u.accountEnabled === false);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "m365-users",
      timestamp: now,
      hash: hashEvidence({ total: userList.length, disabled: disabled.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "microsoft365/users",
      status: "unknown",
      data: { userCount: userList.length, disabledCount: disabled.length },
      metadata: { tenantId: config.tenantId || "" },
    });

    const sites = await this.fetchGraph(config, "/sites?$top=50").catch(() => ({ value: [] }));
    const siteList = (sites.value || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "m365-sharepoint",
      timestamp: now,
      hash: hashEvidence({ siteCount: siteList.length }),
      framework: "ISO27001",
      controlId: "A.8.3.2",
      source: "microsoft365/sites",
      status: "unknown",
      data: { siteCount: siteList.length },
      metadata: { tenantId: config.tenantId || "" },
    });

    const teams = await this.fetchGraph(config, "/teams?$top=50").catch(() => ({ value: [] }));
    const teamList = (teams.value || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "m365-teams",
      timestamp: now,
      hash: hashEvidence({ teamCount: teamList.length }),
      framework: "SOC2",
      controlId: "CC6.4",
      source: "microsoft365/teams",
      status: "unknown",
      data: { teamCount: teamList.length },
      metadata: { tenantId: config.tenantId || "" },
    });

    const mailConfig = await this.fetchGraph(
      config,
      "/admin.exchange/settings?%24select=mailFlowConfiguration"
    ).catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "m365-exchange",
      timestamp: now,
      hash: hashEvidence(mailConfig),
      framework: "SOC2",
      controlId: "CC6.7",
      source: "microsoft365/exchange",
      status: "unknown",
      data: { mailConfig },
      metadata: { tenantId: config.tenantId || "" },
    });

    const audit = await this.fetchGraph(
      config,
      "/audit/dimensions/logs/activities?%24top=100&%24orderby=activityDateTime%20desc"
    ).catch(() => ({ value: [] }));
    const auditItems = (audit.value || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "m365-audit",
      timestamp: now,
      hash: hashEvidence({ logCount: auditItems.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "microsoft365/audit",
      status: "unknown",
      data: { auditLogCount: auditItems.length },
      metadata: { tenantId: config.tenantId || "" },
    });

    return artifacts;
  }
}
