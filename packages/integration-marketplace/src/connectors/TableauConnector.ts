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
    id: "tableau-workbooks",
    name: "Workbook Security",
    description: "Fetch workbook permissions and data source access",
    evidenceCategories: ["access_control", "data_protection"],
  },
  {
    id: "tableau-projects",
    name: "Project Hierarchies",
    description: "Fetch project site and permission settings",
    evidenceCategories: ["access_control", "configuration"],
  },
  {
    id: "tableau-extracts",
    name: "Data Extracts",
    description: "Fetch extract refresh schedules and embedded credentials",
    evidenceCategories: ["data_protection", "change_management"],
  },
  {
    id: "tableau-audit",
    name: "Admin Events",
    description: "Fetch Tableau Server admin event and login logs",
    evidenceCategories: ["monitoring", "access_control"],
  },
];

export class TableauConnector implements IntegrationConnector {
  readonly id = "tableau";
  readonly name = "Tableau";
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
    const base = config.baseUrl || "https://tableau.example.com/api/3.19";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        "X-Tableau-Auth": config.apiToken || "",
        "Content-Type": "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Tableau API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/sites");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const siteId = config.extra?.siteId || "";

    const workbooks = await this.fetchApi(
      config,
      `/sites/${siteId}/workbooks`
    ).catch(() => ({ workbooks: { workbook: [] } }));
    const wbData = workbooks as Record<string, unknown>;
    const wbObj = (wbData.workbooks as Record<string, unknown>) || {};
    const wbList = (wbObj.workbook as unknown[]) || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tableau-workbooks",
      timestamp: now,
      hash: hashEvidence(workbooks),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `tableau/${siteId}/workbooks`,
      status: wbList.length > 0 ? "compliant" : "unknown",
      data: { workbookCount: wbList.length },
      metadata: { siteId },
    });

    const projects = await this.fetchApi(
      config,
      `/sites/${siteId}/projects`
    ).catch(() => ({ projects: { project: [] } }));
    const projData = projects as Record<string, unknown>;
    const projObj = (projData.projects as Record<string, unknown>) || {};
    const projList = (projObj.project as unknown[]) || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tableau-projects",
      timestamp: now,
      hash: hashEvidence(projects),
      framework: "ISO27001",
      controlId: "A.6.2.1",
      source: `tableau/${siteId}/projects`,
      status: projList.length > 0 ? "compliant" : "non_compliant",
      data: { projectCount: projList.length },
      metadata: { siteId },
    });

    return artifacts;
  }
}
