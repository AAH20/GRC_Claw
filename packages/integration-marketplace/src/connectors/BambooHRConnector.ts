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
    id: "bhr-onboarding",
    name: "Employee Onboarding",
    description: "Fetch recent employee onboarding records and access provisioning",
    evidenceCategories: ["hr", "access_provisioning"],
  },
  {
    id: "bhr-offboarding",
    name: "Employee Offboarding",
    description: "Fetch employee offboarding records and access revocations",
    evidenceCategories: ["hr", "access_revocation"],
  },
];

export class BambooHRConnector implements IntegrationConnector {
  readonly id = "bamboohr";
  readonly name = "BambooHR";
  readonly category = "hr" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const domain = config.extra?.domain || "yourcompany";
    const base = config.baseUrl || `https://api.bamboohr.com/api/gate.php/${domain}`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `Basic ${Buffer.from(`${config.apiToken}:x`).toString("base64")}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`BambooHR API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/v1/meta/fields");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0];

    const employees = await this.fetchApi(
      config,
      `/v1/employees/directory?fields=id,employmentEndDate,employmentStatus,hireDate`
    ).catch(() => ({ employees: [] }));
    const empList = (employees.employees || []) as Record<string, unknown>[];
    const terminated = empList.filter(
      (e) =>
        e.employmentStatus === "Terminated" &&
        (e.employmentEndDate as string) >= thirtyDaysAgo
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "bhr-offboarding",
      timestamp: now,
      hash: hashEvidence({ totalEmployees: empList.length, recentTerminations: terminated.length }),
      framework: "SOC2",
      controlId: "CC6.2",
      source: "bamboohr/directory",
      status: "unknown",
      data: { totalEmployees: empList.length, recentTerminations: terminated.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    const newHires = empList.filter(
      (e) => (e.hireDate as string) >= thirtyDaysAgo
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "bhr-onboarding",
      timestamp: now,
      hash: hashEvidence({ newHires: newHires.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "bamboohr/directory",
      status: "unknown",
      data: { newHiresLast30Days: newHires.length },
      metadata: { domain: config.extra?.domain || "" },
    });

    return artifacts;
  }
}
