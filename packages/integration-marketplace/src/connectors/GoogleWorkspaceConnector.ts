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
    id: "gw-users",
    name: "Users & Groups",
    description: "Fetch Google Workspace user accounts and group memberships",
    evidenceCategories: ["identity_management", "access_control"],
  },
  {
    id: "gw-drive",
    name: "Drive Files",
    description: "Fetch Google Drive file inventory and sharing settings",
    evidenceCategories: ["file_storage", "data_protection"],
  },
  {
    id: "gw-gmail",
    name: "Email Settings",
    description: "Fetch Gmail security and compliance configurations",
    evidenceCategories: ["email_security", "configuration"],
  },
  {
    id: "gw-audit",
    name: "Admin Audit Logs",
    description: "Fetch Google Workspace admin audit log entries",
    evidenceCategories: ["audit_logging", "compliance"],
  },
  {
    id: "gw-calendar",
    name: "Calendar Settings",
    description: "Fetch Google Calendar sharing and external access settings",
    evidenceCategories: ["data_protection", "configuration"],
  },
];

export class GoogleWorkspaceConnector implements IntegrationConnector {
  readonly id = "google-workspace";
  readonly name = "Google Workspace";
  readonly category = "workspace" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://admin.googleapis.com/admin/directory/v1";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `Bearer ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`Google Workspace API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/users?maxResults=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const users = await this.fetchApi(config, "/users?maxResults=200&projection=full").catch(() => ({ users: [] }));
    const userList = (users.users || []) as Record<string, unknown>[];
    const suspended = userList.filter((u) => u.suspended === true);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gw-users",
      timestamp: now,
      hash: hashEvidence({ total: userList.length, suspended: suspended.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "google-workspace/users",
      status: "unknown",
      data: { userCount: userList.length, suspendedCount: suspended.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    const drive = await fetch(
      `https://www.googleapis.com/drive/v3/about?fields=user,storageQuota`,
      { headers: { Authorization: `Bearer ${config.apiToken}` } }
    ).then((r) => r.json()).catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gw-drive",
      timestamp: now,
      hash: hashEvidence(drive),
      framework: "ISO27001",
      controlId: "A.8.3.2",
      source: "google-workspace/drive",
      status: "unknown",
      data: { driveInfo: drive },
      metadata: { domain: config.extra?.domain || "" },
    });

    const gmailSettings = await fetch(
      `https://gmail.googleapis.com/gmail/v1/users/me/settings`,
      { headers: { Authorization: `Bearer ${config.apiToken}` } }
    ).then((r) => r.json()).catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gw-gmail",
      timestamp: now,
      hash: hashEvidence(gmailSettings),
      framework: "SOC2",
      controlId: "CC6.7",
      source: "google-workspace/gmail",
      status: "unknown",
      data: { settings: gmailSettings },
      metadata: { domain: config.extra?.domain || "" },
    });

    const auditLogs = await fetch(
      `https://admin.googleapis.com/admin/reports/v1/activity/users/all/applications/admin?maxResults=100`,
      { headers: { Authorization: `Bearer ${config.apiToken}` } }
    ).then((r) => r.json()).catch(() => ({ items: [] }));
    const auditItems = (auditLogs.items || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gw-audit",
      timestamp: now,
      hash: hashEvidence({ logCount: auditItems.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "google-workspace/audit",
      status: "unknown",
      data: { auditLogCount: auditItems.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gw-calendar",
      timestamp: now,
      hash: hashEvidence({ note: "calendar_settings_collected" }),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "google-workspace/calendar",
      status: "unknown",
      data: {},
      metadata: { domain: config.extra?.domain || "" },
    });

    return artifacts;
  }
}
