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
    id: "xero-users",
    name: "User Access",
    description: "Fetch Xero user roles and organisation permissions",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "xero-contacts",
    name: "Contact Management",
    description: "Fetch contact access controls and sharing settings",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "xero-approvals",
    name: "Approval Workflows",
    description: "Fetch purchase order and invoice approval rules",
    evidenceCategories: ["change_management", "compliance"],
  },
  {
    id: "xero-audit",
    name: "Audit Trail",
    description: "Fetch change history and user activity logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class XeroConnector implements IntegrationConnector {
  readonly id = "xero";
  readonly name = "Xero";
  readonly category = "finance" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "GDPR",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.xero.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Xero API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/connections");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const tenantId = config.extra?.tenantId || "";

    const users = await this.fetchApi(
      config,
      `/api.xro/2.0/users`
    ).catch(() => ({ Users: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "xero-users",
      timestamp: now,
      hash: hashEvidence(users),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `xero/${tenantId}/users`,
      status: (users.Users as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { userCount: (users.Users as unknown[])?.length || 0 },
      metadata: { tenantId },
    });

    const org = await this.fetchApi(
      config,
      `/api.xro/2.0/organisation`
    ).catch(() => ({ Organisations: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "xero-approvals",
      timestamp: now,
      hash: hashEvidence(org),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: `xero/${tenantId}/organisation`,
      status: "partial",
      data: org as Record<string, unknown>,
      metadata: { tenantId },
    });

    return artifacts;
  }
}
