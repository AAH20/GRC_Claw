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
    id: "dropbox-files",
    name: "File Inventory",
    description: "Fetch Dropbox file and folder inventory with sharing status",
    evidenceCategories: ["file_storage", "data_protection"],
  },
  {
    id: "dropbox-sharing",
    name: "Shared Links",
    description: "Fetch shared links and external access configurations",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "dropbox-members",
    name: "Team Members",
    description: "Fetch Dropbox team members and role assignments",
    evidenceCategories: ["identity_management", "access_control"],
  },
  {
    id: "dropbox-events",
    name: "File Events",
    description: "Fetch recent file activity and access audit events",
    evidenceCategories: ["audit_logging", "data_protection"],
  },
];

export class DropboxConnector implements IntegrationConnector {
  readonly id = "dropbox";
  readonly name = "Dropbox";
  readonly category = "file_storage" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "HIPAA"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string,
    body?: Record<string, unknown>
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.dropboxapi.com/2";
    const resp = await fetch(`${base}${endpoint}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : "{}",
    });
    if (!resp.ok) throw new Error(`Dropbox API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/users/get_current_account");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const files = await this.fetchApi(config, "/files/list_folder", { path: "", recursive: false }).catch(() => ({ entries: [] }));
    const fileList = (files.entries || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "dropbox-files",
      timestamp: now,
      hash: hashEvidence({ fileCount: fileList.length }),
      framework: "SOC2",
      controlId: "CC6.4",
      source: "dropbox/files",
      status: fileList.length > 0 ? "compliant" : "non_compliant",
      data: { fileCount: fileList.length },
      metadata: {},
    });

    const sharedLinks = await this.fetchApi(config, "/sharing/list_shared_links", { limit: 100 }).catch(() => ({ links: [] }));
    const linkList = (sharedLinks.links || []) as Record<string, unknown>[];
    const publicLinks = linkList.filter((l) => {
      const policy = (l.link_permissions || {}) as Record<string, unknown>;
      return policy.resolved_visibility === "public";
    });
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "dropbox-sharing",
      timestamp: now,
      hash: hashEvidence({ total: linkList.length, public: publicLinks.length }),
      framework: "ISO27001",
      controlId: "A.9.2.5",
      source: "dropbox/sharing",
      status: publicLinks.length === 0 ? "compliant" : "non_compliant",
      data: { totalLinks: linkList.length, publicLinks: publicLinks.length },
      metadata: {},
    });

    const members = await this.fetchApi(config, "/team/members/list", { limit: 100 }).catch(() => ({ members: [] }));
    const memberList = (members.members || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "dropbox-members",
      timestamp: now,
      hash: hashEvidence({ memberCount: memberList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "dropbox/members",
      status: "unknown",
      data: { memberCount: memberList.length },
      metadata: {},
    });

    const events = await this.fetchApi(config, "https://api.dropboxapi.com/2/team_log/get_events", { limit: 100 }).catch(() => ({ events: [] }));
    const eventList = (events.events || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "dropbox-events",
      timestamp: now,
      hash: hashEvidence({ eventCount: eventList.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "dropbox/events",
      status: "unknown",
      data: { eventCount: eventList.length },
      metadata: {},
    });

    return artifacts;
  }
}
