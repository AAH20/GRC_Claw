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
    id: "successfactors-employees",
    name: "Employee Central",
    description: "Fetch employee records and organizational data",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "successfactors-governance",
    name: "Governance Risk",
    description: "Fetch risk assessment and policy compliance status",
    evidenceCategories: ["compliance", "monitoring"],
  },
  {
    id: "successfactors-access",
    name: "Role Management",
    description: "Fetch role assignments and permission configurations",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "successfactors-audit",
    name: "Audit Trail",
    description: "Fetch employee data change audit logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class SAPSuccessFactorsConnector implements IntegrationConnector {
  readonly id = "sap-successfactors";
  readonly name = "SAP SuccessFactors";
  readonly category = "hr" as const;
  readonly authType = "api_key" as const;
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
    const base = config.baseUrl || "https://api.successfactors.com";
    const resp = await fetch(`${base}/odata/v2${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`SAP SuccessFactors API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/User?$top=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const users = await this.fetchApi(config, "/User?$top=100&$select=userId,status").catch(
      () => ({ d: { results: [] } })
    );
    const userData = users as Record<string, unknown>;
    const userD = (userData.d as Record<string, unknown>) || {};
    const userResults = (userD.results as unknown[]) || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "successfactors-employees",
      timestamp: now,
      hash: hashEvidence(users),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "successfactors/users",
      status: userResults.length > 0 ? "compliant" : "unknown",
      data: { userCount: userResults.length },
      metadata: {},
    });

    const roles = await this.fetchApi(config, "/RoleManagement/Roles").catch(() => ({
      d: { results: [] },
    }));
    const roleData = roles as Record<string, unknown>;
    const roleD = (roleData.d as Record<string, unknown>) || {};
    const roleResults = (roleD.results as unknown[]) || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "successfactors-access",
      timestamp: now,
      hash: hashEvidence(roles),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "successfactors/roles",
      status: roleResults.length > 0 ? "compliant" : "non_compliant",
      data: { roleCount: roleResults.length },
      metadata: {},
    });

    return artifacts;
  }
}
