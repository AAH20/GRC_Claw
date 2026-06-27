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
    id: "looker-projects",
    name: "Project Security",
    description: "Fetch LookML project permissions and Git connection settings",
    evidenceCategories: ["access_control", "change_management"],
  },
  {
    id: "looker-roles",
    name: "Role-Based Access",
    description: "Fetch roles, model sets, and permission sets",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "looker-content",
    name: "Content Access",
    description: "Fetch dashboard and look permissions and scheduling",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "looker-queries",
    name: "Query History",
    description: "Fetch user query history and data access patterns",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class LookerConnector implements IntegrationConnector {
  readonly id = "looker";
  readonly name = "Looker";
  readonly category = "data_warehouse" as const;
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
    const base = config.baseUrl || "https://looker.example.com/api/4.0";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Looker API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/user");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const roles = await this.fetchApi(config, "/roles").catch(() => []);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "looker-roles",
      timestamp: now,
      hash: hashEvidence(Array.isArray(roles) ? { count: roles.length } : roles as Record<string, unknown>),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "looker/roles",
      status: Array.isArray(roles) && roles.length > 0 ? "compliant" : "unknown",
      data: { roleCount: Array.isArray(roles) ? roles.length : 0 },
      metadata: {},
    });

    const projects = await this.fetchApi(config, "/projects").catch(() => []);
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "looker-projects",
      timestamp: now,
      hash: hashEvidence(Array.isArray(projects) ? { count: projects.length } : projects as Record<string, unknown>),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "looker/projects",
      status: Array.isArray(projects) && projects.length > 0 ? "compliant" : "non_compliant",
      data: { projectCount: Array.isArray(projects) ? projects.length : 0 },
      metadata: {},
    });

    return artifacts;
  }
}
