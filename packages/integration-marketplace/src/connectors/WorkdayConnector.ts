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
    id: "workday-employees",
    name: "Employee Data",
    description: "Fetch employee records, org hierarchy, and status",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "workday-access",
    name: "Access Reviews",
    description: "Fetch role-based access and access certification status",
    evidenceCategories: ["access_control", "compliance"],
  },
  {
    id: "workday-compliance",
    name: "Compliance Tasks",
    description: "Fetch policy compliance assignments and completion status",
    evidenceCategories: ["compliance", "monitoring"],
  },
  {
    id: "workday-separation",
    name: "Segregation of Duties",
    description: "Fetch SoD conflict detection and mitigation status",
    evidenceCategories: ["access_control", "compliance"],
  },
];

export class WorkdayConnector implements IntegrationConnector {
  readonly id = "workday";
  readonly name = "Workday";
  readonly category = "hr" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "GDPR",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://www.workday.com";
    const tenant = config.extra?.tenant || "wd1";
    const resp = await fetch(`${base}/api/v1/${tenant}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Workday API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const employees = await this.fetchApi(config, "/workers?limit=100").catch(() => ({
      data: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "workday-employees",
      timestamp: now,
      hash: hashEvidence(employees),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "workday/workers",
      status: (employees.data as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { employeeCount: (employees.data as unknown[])?.length || 0 },
      metadata: {},
    });

    const accessReviews = await this.fetchApi(config, "/access-reviews").catch(() => ({
      data: [],
    }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "workday-access",
      timestamp: now,
      hash: hashEvidence(accessReviews),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "workday/access-reviews",
      status: (accessReviews.data as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { activeReviews: (accessReviews.data as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
