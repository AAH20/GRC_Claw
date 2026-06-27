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
    id: "adp-employees",
    name: "Employee Records",
    description: "Fetch employee data, status, and org hierarchy",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "adp-compliance",
    name: "Compliance Management",
    description: "Fetch I-9, W-4, and tax compliance statuses",
    evidenceCategories: ["compliance", "monitoring"],
  },
  {
    id: "adp-access",
    name: "User Permissions",
    description: "Fetch ADP account permissions and role assignments",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "adp-audit",
    name: "Change Audit",
    description: "Fetch payroll and employee data change logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class ADPConnector implements IntegrationConnector {
  readonly id = "adp";
  readonly name = "ADP";
  readonly category = "hr" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.adp.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`ADP API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/hr/v2/workers?$top=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const workers = await this.fetchApi(config, "/hr/v2/workers?$top=100").catch(() => ({
      workers: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "adp-employees",
      timestamp: now,
      hash: hashEvidence(workers),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "adp/workers",
      status: (workers.workers as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { workerCount: (workers.workers as unknown[])?.length || 0 },
      metadata: {},
    });

    const users = await this.fetchApi(config, "/admin/v1/users").catch(() => ({ resources: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "adp-access",
      timestamp: now,
      hash: hashEvidence(users),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "adp/users",
      status: (users.resources as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { adminUsers: (users.resources as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
