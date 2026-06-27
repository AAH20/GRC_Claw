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
    id: "qualys-vuln-scans",
    name: "Vulnerability Scans",
    description: "Fetch Qualys vulnerability scan results and host detections",
    evidenceCategories: ["vulnerability_management"],
  },
  {
    id: "qualys-compliance-scans",
    name: "Compliance Scans",
    description: "Fetch Qualys policy compliance scan results",
    evidenceCategories: ["compliance", "configuration"],
  },
];

export class QualysConnector implements IntegrationConnector {
  readonly id = "qualys";
  readonly name = "Qualys";
  readonly category = "vulnerability" as const;
  readonly authType = "basic_auth" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "PCI_DSS", "NIST_CSF"];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string,
    body?: string
  ): Promise<string> {
    const base = config.baseUrl || "https://qualysapi.qualys.com";
    const resp = await fetch(`${base}${endpoint}`, {
      method: body ? "POST" : "GET",
      headers: {
        Authorization: `Basic ${Buffer.from(`${config.clientId}:${config.apiToken}`).toString("base64")}`,
        "Content-Type": body ? "application/x-www-form-urlencoded" : "text/xml",
        Accept: "application/json",
      },
      body,
    });
    if (!resp.ok) throw new Error(`Qualys API ${resp.status}: ${resp.statusText}`);
    return resp.text();
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/api/2.0/fo/user/?action=list");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const vulnScan = await this.fetchApi(
      config,
      "/api/2.0/fo/scan/?action=list&output_format=JSON&truncate_limit=100"
    ).catch(() => '{"response":{"scan_list":[]}}');
    let vulnData: Record<string, unknown> = {};
    try {
      vulnData = JSON.parse(vulnScan);
    } catch {
      vulnData = { raw: vulnScan.substring(0, 500) };
    }
    const scanList = (vulnData.response as Record<string, unknown>)?.scan_list || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "qualys-vuln-scans",
      timestamp: now,
      hash: hashEvidence({ scanCount: Array.isArray(scanList) ? scanList.length : 0 }),
      framework: "SOC2",
      controlId: "CC7.1",
      source: "qualys/scans",
      status: "unknown",
      data: { scanCount: Array.isArray(scanList) ? scanList.length : 0 },
      metadata: {},
    });

    const compScan = await this.fetchApi(
      config,
      "/api/2.0/compliance_policy/?action=list&output_format=JSON"
    ).catch(() => '{"response":{"policy_list":[]}}');
    let compData: Record<string, unknown> = {};
    try {
      compData = JSON.parse(compScan);
    } catch {
      compData = { raw: compScan.substring(0, 500) };
    }
    const policyList = (compData.response as Record<string, unknown>)?.policy_list || [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "qualys-compliance-scans",
      timestamp: now,
      hash: hashEvidence({ policyCount: Array.isArray(policyList) ? policyList.length : 0 }),
      framework: "ISO27001",
      controlId: "A.12.6.1",
      source: "qualys/compliance",
      status: "unknown",
      data: { policyCount: Array.isArray(policyList) ? policyList.length : 0 },
      metadata: {},
    });

    return artifacts;
  }
}
