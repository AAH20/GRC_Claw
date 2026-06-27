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
    id: "snow-incidents",
    name: "Incident Records",
    description: "Fetch ServiceNow ITSM incident records and resolution metrics",
    evidenceCategories: ["incident_management", "change_management"],
  },
  {
    id: "snow-change-requests",
    name: "Change Requests",
    description: "Fetch change request records including approval workflows",
    evidenceCategories: ["change_management"],
  },
  {
    id: "snow-problems",
    name: "Problem Records",
    description: "Fetch problem management records and root cause analysis",
    evidenceCategories: ["incident_management", "risk_management"],
  },
  {
    id: "snow-configuration",
    name: "CMDB Configuration",
    description: "Fetch CMDB configuration items and relationships",
    evidenceCategories: ["configuration", "asset_management"],
  },
];

export class ServiceNowConnector implements IntegrationConnector {
  readonly id = "servicenow";
  readonly name = "ServiceNow";
  readonly category = "incident_management" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA", "PCI_DSS"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || `https://${config.extra?.instance || "instance"}.service-now.com/api/now`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${config.apiToken}`,
      },
    });
    if (!resp.ok) throw new Error(`ServiceNow API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/table/sys_user?sysparm_limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const incidents = await this.fetchApi(
      config,
      "/table/incident?sysparm_limit=100&sysparm_fields=number,state,severity,assigned_to,opened_at,resolved_at"
    ).catch(() => ({ result: [] }));
    const incidentList = (incidents.result || []) as Record<string, unknown>[];
    const resolved = incidentList.filter((i) => i.state === "6" || i.state === "7");
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snow-incidents",
      timestamp: now,
      hash: hashEvidence({ total: incidentList.length, resolved: resolved.length }),
      framework: "SOC2",
      controlId: "CC7.3",
      source: "servicenow/incident",
      status: "unknown",
      data: { incidentCount: incidentList.length, resolvedCount: resolved.length },
      metadata: { instance: config.extra?.instance || "" },
    });

    const changes = await this.fetchApi(
      config,
      "/table/change_request?sysparm_limit=100&sysparm_fields=number,state,risk,approval"
    ).catch(() => ({ result: [] }));
    const changeList = (changes.result || []) as Record<string, unknown>[];
    const approved = changeList.filter((c) => c.approval === "approved");
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snow-change-requests",
      timestamp: now,
      hash: hashEvidence({ total: changeList.length, approved: approved.length }),
      framework: "ISO27001",
      controlId: "A.12.1.4",
      source: "servicenow/change_request",
      status: "unknown",
      data: { changeCount: changeList.length, approvedCount: approved.length },
      metadata: { instance: config.extra?.instance || "" },
    });

    const problems = await this.fetchApi(
      config,
      "/table/problem?sysparm_limit=100&sysparm_fields=number,state,priority,known_error"
    ).catch(() => ({ result: [] }));
    const problemList = (problems.result || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snow-problems",
      timestamp: now,
      hash: hashEvidence({ total: problemList.length }),
      framework: "ISO27001",
      controlId: "A.12.1.4",
      source: "servicenow/problem",
      status: "unknown",
      data: { problemCount: problemList.length },
      metadata: { instance: config.extra?.instance || "" },
    });

    const cmdb = await this.fetchApi(
      config,
      "/table/cmdb_ci?sysparm_limit=100&sysparm_fields=name,sys_class_name,operational_status"
    ).catch(() => ({ result: [] }));
    const cmdbList = (cmdb.result || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "snow-configuration",
      timestamp: now,
      hash: hashEvidence({ total: cmdbList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "servicenow/cmdb_ci",
      status: "unknown",
      data: { ciCount: cmdbList.length },
      metadata: { instance: config.extra?.instance || "" },
    });

    return artifacts;
  }
}
