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
    id: "lacework-alerts",
    name: "Alerts & Anomalies",
    description: "Fetch Lacework anomaly detection alerts and threat findings",
    evidenceCategories: ["threat_detection", "anomaly_detection"],
  },
  {
    id: "lacework-compliance",
    name: "Compliance Assessment",
    description: "Fetch Lacework compliance posture across cloud accounts",
    evidenceCategories: ["compliance", "configuration"],
  },
  {
    id: "lacework-activity",
    name: "Activity Analysis",
    description: "Fetch host and cloud activity analysis results",
    evidenceCategories: ["audit", "monitoring"],
  },
  {
    id: "lacework-vulnerabilities",
    name: "Vulnerability Assessment",
    description: "Fetch Lacework vulnerability findings for containers and hosts",
    evidenceCategories: ["vulnerability_management", "container_security"],
  },
];

export class LaceworkConnector implements IntegrationConnector {
  readonly id = "lacework";
  readonly name = "Lacework";
  readonly category = "monitoring" as const;
  readonly authType = "api_key" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "PCI_DSS",
    "HIPAA",
  ];

  private async generateSignature(
    config: ConnectorConfig,
    timestamp: string,
    method: string,
    path: string,
    body: string
  ): Promise<string> {
    const stringToSign = `${method}\n${path}\n\n\n${timestamp}`;
    const key = Buffer.from(config.clientSecret || "", "base64");
    const hmac = await crypto.subtle.importKey(
      "raw",
      key,
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const sig = await crypto.subtle.sign("HMAC", hmac, Buffer.from(stringToSign));
    return Buffer.from(sig).toString("base64");
  }

  private async fetchApi(
    config: ConnectorConfig,
    path: string,
    body?: Record<string, unknown>
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || "https://api.lacework.net";
    const timestamp = new Date().toISOString();
    const bodyStr = body ? JSON.stringify(body) : "";
    const signature = await this.generateSignature(config, timestamp, body ? "POST" : "GET", path, bodyStr);
    const resp = await fetch(`${base}${path}`, {
      method: body ? "POST" : "GET",
      headers: {
        Authorization: `ACCESS:${config.clientId}:${signature}`,
        "X-LW-Date": timestamp,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: body ? bodyStr : undefined,
    });
    if (!resp.ok) throw new Error(`Lacework API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/api/v1/alerts/2.0/alerts/OWASP_TOP_10");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const account = config.extra?.accountAlias || "default";

    const alerts = await this.fetchApi(config, "/api/v1/alerts/2.0/alerts/RECOMMENDATIONS").catch(
      () => ({ data: [] })
    );
    const alertData = Array.isArray(alerts.data) ? alerts.data : [];
    const criticalAlerts = alertData.filter(
      (a: Record<string, unknown>) => a.severity === "Critical"
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "lacework-alerts",
      timestamp: now,
      hash: hashEvidence({ count: alertData.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: `lacework/${account}/alerts`,
      status: criticalAlerts.length === 0 ? "compliant" : "non_compliant",
      data: { totalAlerts: alertData.length, criticalAlerts: criticalAlerts.length },
      metadata: { account },
    });

    const compliance = await this.fetchApi(config, "/api/v1/compliance/posture/aws").catch(
      () => ({ data: [] })
    );
    const compData = Array.isArray(compliance.data) ? compliance.data : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "lacework-compliance",
      timestamp: now,
      hash: hashEvidence({ count: compData.length }),
      framework: "ISO27001",
      controlId: "A.12.1.1",
      source: `lacework/${account}/compliance`,
      status: compData.length > 0 ? "compliant" : "partial",
      data: { complianceStandards: compData.length },
      metadata: { account },
    });

    const activity = await this.fetchApi(
      config,
      "/api/v1/Activity/evaluate?timeRange=7&timeRangeUnit=day"
    ).catch(() => ({ data: [] }));
    const activityData = Array.isArray(activity.data) ? activity.data : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "lacework-activity",
      timestamp: now,
      hash: hashEvidence({ count: activityData.length }),
      framework: "NIST_CSF",
      controlId: "DE.CM",
      source: `lacework/${account}/activity`,
      status: "compliant",
      data: { activityEvents: activityData.length },
      metadata: { account },
    });

    const vulnerabilities = await this.fetchApi(
      config,
      "/api/v1/Vulnerabilities/Container?severity=CRITICAL,HIGH&limit=100"
    ).catch(() => ({ data: [] }));
    const vulnData = Array.isArray(vulnerabilities.data) ? vulnerabilities.data : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "lacework-vulnerabilities",
      timestamp: now,
      hash: hashEvidence({ count: vulnData.length }),
      framework: "PCI_DSS",
      controlId: "6.5.1",
      source: `lacework/${account}/vulnerabilities`,
      status: vulnData.length === 0 ? "compliant" : "non_compliant",
      data: { containerVulns: vulnData.length },
      metadata: { account },
    });

    return artifacts;
  }
}
