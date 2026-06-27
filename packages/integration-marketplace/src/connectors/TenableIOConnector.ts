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
    id: "tenable-vulns",
    name: "Vulnerability Findings",
    description: "Fetch Tenable.io vulnerability findings and severity breakdown",
    evidenceCategories: ["vulnerability_management", "asset_management"],
  },
  {
    id: "tenable-scans",
    name: "Scan Results",
    description: "Fetch scan history and completion status",
    evidenceCategories: ["vulnerability_management", "monitoring"],
  },
  {
    id: "tenable-assets",
    name: "Asset Inventory",
    description: "Fetch discovered assets and vulnerability counts per host",
    evidenceCategories: ["asset_management", "vulnerability_management"],
  },
  {
    id: "tenable-compliance",
    name: "Compliance Checks",
    description: "Fetch CIS and DISA STIG compliance scan results",
    evidenceCategories: ["compliance", "configuration"],
  },
];

export class TenableIOConnector implements IntegrationConnector {
  readonly id = "tenable_io";
  readonly name = "Tenable.io";
  readonly category = "vulnerability" as const;
  readonly authType = "api_key" as const;
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
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://cloud.tenable.com";
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        "X-ApiKeys": `accessKey=${config.clientId}; secretKey=${config.clientSecret}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Tenable API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/server/properties");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();

    const vulns = await this.fetchApi(
      config,
      "/vulns/export?filters.state=active&filters.severity=critical,high&limit=100"
    ).catch(() => ({ vulnerabilities: [] }));
    const vulnList = Array.isArray(vulns.vulnerabilities) ? vulns.vulnerabilities : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tenable-vulns",
      timestamp: now,
      hash: hashEvidence({ count: vulnList.length }),
      framework: "SOC2",
      controlId: "CC6.6",
      source: "tenable/vulnerabilities",
      status: vulnList.length === 0 ? "compliant" : "non_compliant",
      data: { criticalHighVulns: vulnList.length },
      metadata: {},
    });

    const scans = await this.fetchApi(
      config,
      "/scans?limit=10&sort=creation_date:desc"
    ).catch(() => ({ scans: [] }));
    const scanList = Array.isArray(scans.scans) ? scans.scans : [];
    const completedScans = scanList.filter(
      (s: Record<string, unknown>) => s.status === "completed"
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tenable-scans",
      timestamp: now,
      hash: hashEvidence({ scans: scanList.slice(0, 5) }),
      framework: "NIST_CSF",
      controlId: "DE.CM",
      source: "tenable/scans",
      status: completedScans.length > 0 ? "compliant" : "non_compliant",
      data: { recentScans: scanList.length, completed: completedScans.length },
      metadata: {},
    });

    const assets = await this.fetchApi(
      config,
      "/assets?limit=100"
    ).catch(() => ({ assets: [] }));
    const assetList = Array.isArray(assets.assets) ? assets.assets : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tenable-assets",
      timestamp: now,
      hash: hashEvidence({ count: assetList.length }),
      framework: "ISO27001",
      controlId: "A.8.1.1",
      source: "tenable/assets",
      status: assetList.length > 0 ? "compliant" : "partial",
      data: { discoveredAssets: assetList.length },
      metadata: {},
    });

    const compliance = await this.fetchApi(
      config,
      "/compliance/scan/export?limit=20"
    ).catch(() => ({ compliance_results: [] }));
    const compResults = Array.isArray(compliance.compliance_results)
      ? compliance.compliance_results
      : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "tenable-compliance",
      timestamp: now,
      hash: hashEvidence({ count: compResults.length }),
      framework: "PCI_DSS",
      controlId: "2.2.1",
      source: "tenable/compliance",
      status: compResults.length > 0 ? "compliant" : "partial",
      data: { complianceResults: compResults.length },
      metadata: {},
    });

    return artifacts;
  }
}
