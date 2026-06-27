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
    id: "box-folders",
    name: "Folders & Structure",
    description: "Fetch Box folder hierarchy and shared folder configurations",
    evidenceCategories: ["document_management", "data_protection"],
  },
  {
    id: "box-collaborations",
    name: "Collaborations",
    description: "Fetch collaboration invitations and access permissions",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "box-retention-policies",
    name: "Retention Policies",
    description: "Fetch Box retention and disposal policy configurations",
    evidenceCategories: ["data_protection", "compliance"],
  },
  {
    id: "box-events",
    name: "File Events",
    description: "Fetch recent file upload, download, and access events",
    evidenceCategories: ["audit_logging", "data_protection"],
  },
];

export class BoxConnector implements IntegrationConnector {
  readonly id = "box";
  readonly name = "Box";
  readonly category = "document_management" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "HIPAA", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.box.com/2.0";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: { Authorization: `Bearer ${config.apiToken}` },
    });
    if (!resp.ok) throw new Error(`Box API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/users/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const folders = await this.fetchApi(config, "/folders/0/items?limit=100").catch(() => ({ entries: [] }));
    const folderList = (folders.entries || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "box-folders",
      timestamp: now,
      hash: hashEvidence({ itemCount: folderList.length }),
      framework: "SOC2",
      controlId: "CC6.4",
      source: "box/folders",
      status: folderList.length > 0 ? "compliant" : "non_compliant",
      data: { itemCount: folderList.length },
      metadata: {},
    });

    const collaborations = await this.fetchApi(config, "/collaborations?limit=100").catch(() => ({ entries: [] }));
    const collabList = (collaborations.entries || []) as Record<string, unknown>[];
    const externalCollabs = collabList.filter((c) => {
      const access = (c.access_level || {}) as Record<string, unknown>;
      return access.is_externally_managed === true;
    });
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "box-collaborations",
      timestamp: now,
      hash: hashEvidence({ total: collabList.length, external: externalCollabs.length }),
      framework: "ISO27001",
      controlId: "A.9.2.5",
      source: "box/collaborations",
      status: externalCollabs.length === 0 ? "compliant" : "non_compliant",
      data: { totalCollaborations: collabList.length, externalCollaborations: externalCollabs.length },
      metadata: {},
    });

    const retentionPolicies = await this.fetchApi(config, "/retention_policies").catch(() => ({ entries: [] }));
    const policyList = (retentionPolicies.entries || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "box-retention-policies",
      timestamp: now,
      hash: hashEvidence({ policyCount: policyList.length }),
      framework: "ISO27001",
      controlId: "A.8.3.2",
      source: "box/retention_policies",
      status: policyList.length > 0 ? "compliant" : "non_compliant",
      data: { retentionPolicyCount: policyList.length },
      metadata: {},
    });

    const events = await this.fetchApi(config, "/events?stream_type=admin_logs&limit=100").catch(() => ({ entries: [] }));
    const eventList = (events.entries || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "box-events",
      timestamp: now,
      hash: hashEvidence({ eventCount: eventList.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "box/events",
      status: "unknown",
      data: { eventCount: eventList.length },
      metadata: {},
    });

    return artifacts;
  }
}
