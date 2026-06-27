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
    id: "namely-employees",
    name: "Employee Profiles",
    description: "Fetch employee directory and employment data",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "namely-pto",
    name: "Time Off Management",
    description: "Fetch PTO policies and approval workflows",
    evidenceCategories: ["compliance", "configuration"],
  },
  {
    id: "namely-performance",
    name: "Performance Reviews",
    description: "Fetch review cycle status and goal completion",
    evidenceCategories: ["compliance", "monitoring"],
  },
  {
    id: "namely-audit",
    name: "Audit Logs",
    description: "Fetch employee data change and access logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class NamelyConnector implements IntegrationConnector {
  readonly id = "namely";
  readonly name = "Namely";
  readonly category = "hr" as const;
  readonly authType = "api_key" as const;
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
    const base = config.baseUrl || "https://api.namely.com";
    const resp = await fetch(`${base}/api/v1${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Namely API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/employees?limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const employees = await this.fetchApi(config, "/employees?limit=100").catch(() => ({
      employees: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "namely-employees",
      timestamp: now,
      hash: hashEvidence(employees),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "namely/employees",
      status: (employees.employees as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { employeeCount: (employees.employees as unknown[])?.length || 0 },
      metadata: {},
    });

    const pto = await this.fetchApi(config, "/time_off/policies").catch(() => ({
      time_off_policies: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "namely-pto",
      timestamp: now,
      hash: hashEvidence(pto),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "namely/pto-policies",
      status: (pto.time_off_policies as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { ptoPolicies: (pto.time_off_policies as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
