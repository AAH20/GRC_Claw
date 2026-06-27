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
    id: "netsuite-financial",
    name: "Financial Controls",
    description: "Fetch financial reporting access and approval workflows",
    evidenceCategories: ["access_control", "compliance"],
  },
  {
    id: "netsuite-roles",
    name: "Role-Based Access",
    description: "Fetch NetSuite roles and permission configurations",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "netsuite-audit",
    name: "System Notes",
    description: "Fetch data change audit trails and system notes",
    evidenceCategories: ["monitoring", "access_control"],
  },
  {
    id: "netsuite-approvals",
    name: "Approval Policies",
    description: "Fetch purchase order and expense approval rules",
    evidenceCategories: ["change_management", "compliance"],
  },
];

export class NetSuiteConnector implements IntegrationConnector {
  readonly id = "netsuite";
  readonly name = "NetSuite";
  readonly category = "finance" as const;
  readonly authType = "api_key" as const;
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
    const base = config.baseUrl || "https://rest.netsuite.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`NetSuite API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/app/site/hosting/restlet.nl");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const roles = await this.fetchApi(config, "/app/site/hosting/restlet.nl?script=roles").catch(
      () => ({ roles: [] })
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "netsuite-roles",
      timestamp: now,
      hash: hashEvidence(roles),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "netsuite/roles",
      status: (roles.roles as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { roleCount: (roles.roles as unknown[])?.length || 0 },
      metadata: {},
    });

    const audit = await this.fetchApi(config, "/app/site/hosting/restlet.nl?script=audit").catch(
      () => ({ records: [] })
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "netsuite-audit",
      timestamp: now,
      hash: hashEvidence(audit),
      framework: "ISO27001",
      controlId: "A.12.4.1",
      source: "netsuite/audit",
      status: "partial",
      data: { auditRecords: (audit.records as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
