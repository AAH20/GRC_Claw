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
    id: "cs-spotlight-vulns",
    name: "Spotlight Vulnerabilities",
    description: "Fetch CrowdSpotlight vulnerability findings with risk scores",
    evidenceCategories: ["vulnerability_management", "threat_detection"],
  },
  {
    id: "cs-spotlight-cves",
    name: "CVE Intelligence",
    description: "Fetch CVE-based vulnerability intelligence and exploit status",
    evidenceCategories: ["vulnerability_management", "threat_intelligence"],
  },
  {
    id: "cs-spotlight-remediations",
    name: "Remediation Recommendations",
    description: "Fetch CrowdStrike remediation guidance and prioritized fixes",
    evidenceCategories: ["vulnerability_management", "change_management"],
  },
  {
    id: "cs-spotlight-hosts",
    name: "Affected Hosts",
    description: "Fetch hosts affected by Spotlight vulnerabilities",
    evidenceCategories: ["asset_management", "vulnerability_management"],
  },
];

export class CrowdStrikeSpotlightConnector implements IntegrationConnector {
  readonly id = "crowdstrike_spotlight";
  readonly name = "CrowdStrike Spotlight";
  readonly category = "endpoint" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
  ];

  private async getToken(config: ConnectorConfig): Promise<string> {
    const base = config.baseUrl || "https://api.crowdstrike.com";
    const resp = await fetch(`${base}/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: config.clientId || "",
        client_secret: config.clientSecret || "",
      }),
    });
    const data = (await resp.json()) as Record<string, unknown>;
    return data.access_token as string;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getToken(config);
      const base = config.baseUrl || "https://api.crowdstrike.com";
      const resp = await fetch(`${base}/spotlight/queries/vulnerabilities/v1?limit=1`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return resp.ok;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const token = await this.getToken(config);
    const base = config.baseUrl || "https://api.crowdstrike.com";
    const headers = { Authorization: `Bearer ${token}` };

    const vulnQuery = await fetch(
      `${base}/spotlight/queries/vulnerabilities/v1?limit=100&filter=severity:%27Critical%27+OR+severity:%27High%27`,
      { headers }
    )
      .then((r) => r.json())
      .catch(() => ({ resources: [] }));
    const vulnResources = Array.isArray(vulnQuery.resources) ? vulnQuery.resources : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cs-spotlight-vulns",
      timestamp: now,
      hash: hashEvidence(vulnQuery),
      framework: "SOC2",
      controlId: "CC6.6",
      source: "crowdstrike/spotlight/vulnerabilities",
      status: vulnResources.length === 0 ? "compliant" : "non_compliant",
      data: { criticalHighVulns: vulnResources.length },
      metadata: {},
    });

    const cveIntel = await fetch(
      `${base}/spotlight/queries/vulnerabilities/v1?limit=20&filter=cve.id:!%27%27`,
      { headers }
    )
      .then((r) => r.json())
      .catch(() => ({ resources: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cs-spotlight-cves",
      timestamp: now,
      hash: hashEvidence(cveIntel),
      framework: "NIST_CSF",
      controlId: "ID.RA",
      source: "crowdstrike/spotlight/cve-intel",
      status: "compliant",
      data: { cveFindings: Array.isArray(cveIntel.resources) ? cveIntel.resources.length : 0 },
      metadata: {},
    });

    const remediations = await fetch(
      `${base}/spotlight/queries/vulnerabilities/v1?limit=50&filter=remediation.guidance:!%27%27`,
      { headers }
    )
      .then((r) => r.json())
      .catch(() => ({ resources: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cs-spotlight-remediations",
      timestamp: now,
      hash: hashEvidence(remediations),
      framework: "ISO27001",
      controlId: "A.12.6.1",
      source: "crowdstrike/spotlight/remediations",
      status: "compliant",
      data: { remediationsAvailable: Array.isArray(remediations.resources) ? remediations.resources.length : 0 },
      metadata: {},
    });

    const affectedHosts = await fetch(
      `${base}/spotlight/queries/vulnerabilities/v1?limit=1&filter=host_info.hostname:!%27%27`,
      { headers }
    )
      .then((r) => r.json())
      .catch(() => ({ resources: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cs-spotlight-hosts",
      timestamp: now,
      hash: hashEvidence(affectedHosts),
      framework: "PCI_DSS",
      controlId: "2.2.1",
      source: "crowdstrike/spotlight/affected-hosts",
      status: "compliant",
      data: { hostsWithVulns: Array.isArray(affectedHosts.resources) ? affectedHosts.resources.length : 0 },
      metadata: {},
    });

    return artifacts;
  }
}
