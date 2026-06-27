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
    id: "quickbooks-users",
    name: "User Access",
    description: "Fetch QuickBooks user roles and access permissions",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "quickbooks-transactions",
    name: "Transaction Audit",
    description: "Fetch financial transaction logs and change history",
    evidenceCategories: ["monitoring", "access_control"],
  },
  {
    id: "quickbooks-classes",
    name: "Class Tracking",
    description: "Fetch class and department tracking configurations",
    evidenceCategories: ["configuration", "compliance"],
  },
  {
    id: "quickbooks-backup",
    name: "Backup Status",
    description: "Fetch automatic backup configurations and status",
    evidenceCategories: ["data_protection", "configuration"],
  },
];

export class QuickBooksConnector implements IntegrationConnector {
  readonly id = "quickbooks";
  readonly name = "QuickBooks";
  readonly category = "finance" as const;
  readonly authType = "oauth2" as const;
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
    const base = config.baseUrl || "https://quickbooks.api.intuit.com/v3";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`QuickBooks API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/companyinfo/1?minorversion=65");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const companyId = config.extra?.companyId || "1";

    const users = await this.fetchApi(
      config,
      `/company/${companyId}/users`
    ).catch(() => ({ QueryResponse: { User: [] } }));
    const userList = users as Record<string, unknown>;
    const qr = (userList.QueryResponse as Record<string, unknown>) || {};
    const userListArr = (qr.User as unknown[]) || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "quickbooks-users",
      timestamp: now,
      hash: hashEvidence(users),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `quickbooks/${companyId}/users`,
      status: userListArr.length > 0 ? "compliant" : "unknown",
      data: { userCount: userListArr.length },
      metadata: { companyId },
    });

    const company = await this.fetchApi(
      config,
      `/company/${companyId}/companyinfo/${companyId}`
    ).catch(() => ({}));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "quickbooks-classes",
      timestamp: now,
      hash: hashEvidence(company as Record<string, unknown>),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: `quickbooks/${companyId}/companyinfo`,
      status: "partial",
      data: company as Record<string, unknown>,
      metadata: { companyId },
    });

    return artifacts;
  }
}
