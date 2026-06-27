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
    id: "qualys-scan-results",
    name: "Vulnerability Scan Results",
    description: "Fetch Qualys vulnerability scan results and QID findings",
    evidenceCategories: ["vulnerability_management", "asset_management"],
  },
  {
    id: "qualys-compliance",
    name: "Policy Compliance",
    description: "Fetch Qualys policy compliance scan results and benchmarks",
    evidenceCategories: ["compliance", "configuration"],
  },
  {
    id: "qualys-host-detection",
    name: "Host Detection Results",
    description: "Fetch host-based vulnerability detection results",
    evidenceCategories: ["vulnerability_management", "asset_management"],
  },
  {
    id: "qualys-scan-schedule",
    name: "Scan Schedule Status",
    description: "Fetch scheduled scan status and completion verification",
    evidenceCategories: ["monitoring", "change_management"],
  },
];

export class QualysScannerConnector implements IntegrationConnector {
  readonly id = "qualys_scanner";
  readonly name = "Qualys Scanner";
  readonly category = "vulnerability" as const;
  readonly authType = "basic_auth" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
    "HIPAA",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string,
    body?: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://qualysapi.qualys.com";
    const resp = await fetch(`${base}${endpoint}`, {
      method: body ? "POST" : "GET",
      headers: {
        Authorization: `Basic ${Buffer.from(`${config.clientId}:${config.clientSecret}`).toString("base64")}`,
        "Content-Type": body ? "application/x-www-form-urlencoded" : "application/json",
        Accept: "application/json",
      },
      body,
    });
    if (!resp.ok) throw new Error(`Qualys API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/api/2.0/fo/asset/?action=list&output_format=JSON&limit=1");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const scanRef = config.extra?.scanRef || "";

    const scanResults = await this.fetchApi(
      config,
      `/api/2.0/fo/scan/?action=list&output_format=JSON&limit=10`
    ).catch(() => ({ scan_list: [] }));
    const scans = Array.isArray(scanResults.scan_list) ? scanResults.scan_list : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "qualys-scan-results",
      timestamp: now,
      hash: hashEvidence(scanResults),
      framework: "SOC2",
      controlId: "CC6.6",
      source: "qualys/scan-results",
      status: scans.length > 0 ? "compliant" : "partial",
      data: { recentScans: scans.length },
      metadata: { scanRef },
    });

    const compliance = await this.fetchApi(
      config,
      `/api/2.0/fo/compliance/policy/?action=list&output_format=JSON`
    ).catch(() => ({ policy_list: [] }));
    const policies = Array.isArray(compliance.policy_list) ? compliance.policy_list : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "qualys-compliance",
      timestamp: now,
      hash: hashEvidence(compliance),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: "qualys/compliance-policies",
      status: policies.length > 0 ? "compliant" : "partial",
      data: { compliancePolicies: policies.length },
      metadata: { scanRef },
    });

    const hosts = await this.fetchApi(
      config,
      `/api/2.0/fo/asset/?action=list&output_format=JSON&vm_scan_timestamp_after=${new Date(Date.now() - 7 * 86400000).toISOString().split("T")[0]}`
    ).catch(() => ({ asset_list: [] }));
    const hostList = Array.isArray(hosts.asset_list) ? hosts.asset_list : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "qualys-host-detection",
      timestamp: now,
      hash: hashEvidence(hosts),
      framework: "NIST_CSF",
      controlId: "DE.CM",
      source: "qualys/host-detections",
      status: hostList.length > 0 ? "compliant" : "partial",
      data: { scannedHosts: hostList.length },
      metadata: { scanRef },
    });

    const schedule = await this.fetchApi(
      config,
      `/api/2.0/fo/scan/?action=list&output_format=JSON&state=Completed&limit=5`
    ).catch(() => ({ scan_list: [] }));
    const completedScans = Array.isArray(schedule.scan_list) ? schedule.scan_list : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "qualys-scan-schedule",
      timestamp: now,
      hash: hashEvidence(schedule),
      framework: "PCI_DSS",
      controlId: "11.2",
      source: "qualys/scan-schedule",
      status: completedScans.length > 0 ? "compliant" : "non_compliant",
      data: { completedRecentScans: completedScans.length },
      metadata: { scanRef },
    });

    return artifacts;
  }
}
