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
    id: "zenefits-employees",
    name: "Employee Directory",
    description: "Fetch employee profiles and organizational hierarchy",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "zenefits-policies",
    name: "Benefits Policies",
    description: "Fetch benefits enrollment and policy compliance",
    evidenceCategories: ["compliance", "configuration"],
  },
  {
    id: "zenefits-onboarding",
    name: "Onboarding Compliance",
    description: "Fetch new hire onboarding task completion status",
    evidenceCategories: ["compliance", "change_management"],
  },
  {
    id: "zenefits-timeoff",
    name: "Time Off Policies",
    description: "Fetch PTO policies and accrual compliance",
    evidenceCategories: ["compliance", "monitoring"],
  },
];

export class ZenefitsConnector implements IntegrationConnector {
  readonly id = "zenefits";
  readonly name = "Zenefits";
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
    const base = config.baseUrl || "https://rest.zenefits.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${config.apiToken}`,
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Zenefits API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/core/people");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const people = await this.fetchApi(config, "/core/people").catch(() => ({ data: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "zenefits-employees",
      timestamp: now,
      hash: hashEvidence(people),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "zenefits/people",
      status: (people.data as unknown[])?.length > 0 ? "compliant" : "unknown",
      data: { employeeCount: (people.data as unknown[])?.length || 0 },
      metadata: {},
    });

    const benefits = await this.fetchApi(config, "/benefits/plans").catch(() => ({ data: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "zenefits-policies",
      timestamp: now,
      hash: hashEvidence(benefits),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: "zenefits/benefits",
      status: (benefits.data as unknown[])?.length > 0 ? "compliant" : "non_compliant",
      data: { benefitPlans: (benefits.data as unknown[])?.length || 0 },
      metadata: {},
    });

    return artifacts;
  }
}
