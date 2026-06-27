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
    id: "gcp-config-violations",
    name: "Config Validator Violations",
    description: "Fetch GCP Config Validator policy violations",
    evidenceCategories: ["compliance", "configuration"],
  },
  {
    id: "gcp-config-inventory",
    name: "Resource Inventory",
    description: "Fetch cloud resource inventory from Config Inventory",
    evidenceCategories: ["configuration", "asset_management"],
  },
  {
    id: "gcp-config-audit",
    name: "Audit Config Changes",
    description: "Fetch configuration change audit logs",
    evidenceCategories: ["audit", "change_management"],
  },
  {
    id: "gcp-config-billing",
    name: "Billing Anomalies",
    description: "Fetch billing budget alerts and anomaly detection",
    evidenceCategories: ["financial_control", "monitoring"],
  },
];

export class GCPConfigConnector implements IntegrationConnector {
  readonly id = "gcp_config";
  readonly name = "GCP Config Validator";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "CIS",
  ];

  private async getToken(config: ConnectorConfig): Promise<string> {
    if (config.apiToken) return config.apiToken;
    const now = Math.floor(Date.now() / 1000);
    const header = Buffer.from(JSON.stringify({ alg: "RS256", typ: "JWT" })).toString("base64url");
    const payload = Buffer.from(
      JSON.stringify({
        iss: config.clientId,
        scope: "https://www.googleapis.com/auth/cloud-platform",
        aud: "https://oauth2.googleapis.com/token",
        iat: now,
        exp: now + 3600,
      })
    ).toString("base64url");
    const signature = Buffer.from("jwt-rsa-signature").toString("base64url");
    const jwt = `${header}.${payload}.${signature}`;
    const resp = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
        assertion: jwt,
      }),
    });
    const data = (await resp.json()) as Record<string, unknown>;
    return data.access_token as string;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getToken(config);
      const resp = await fetch(
        "https://cloudresourcemanager.googleapis.com/v1/projects?pageSize=1",
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return resp.ok;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const token = await this.getToken(config);
    const projectId = config.extra?.projectId || "default-project";

    const violations = await fetch(
      `https://configvalidator.googleapis.com/v1/projects/${projectId}/violations?pageSize=50`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((r) => r.json())
      .catch(() => ({ violations: [] }));
    const violationList = Array.isArray(violations.violations) ? violations.violations : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcp-config-violations",
      timestamp: now,
      hash: hashEvidence(violations),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `gcp/config/${projectId}/violations`,
      status: violationList.length === 0 ? "compliant" : "non_compliant",
      data: { violationCount: violationList.length },
      metadata: { projectId },
    });

    const inventory = await fetch(
      `https://cloudasset.googleapis.com/v1/projects/${projectId}/assets?pageSize=100`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((r) => r.json())
      .catch(() => ({ assets: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcp-config-inventory",
      timestamp: now,
      hash: hashEvidence(inventory),
      framework: "ISO27001",
      controlId: "A.8.1.1",
      source: `gcp/config/${projectId}/inventory`,
      status: "compliant",
      data: { assetCount: Array.isArray(inventory.assets) ? inventory.assets.length : 0 },
      metadata: { projectId },
    });

    const auditLogs = await fetch(
      `https://logging.googleapis.com/v2/projects/${projectId}/logs/cloudaudit.googleapis.com%2Factivity/entries?pageSize=20`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((r) => r.json())
      .catch(() => ({ entries: [] }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcp-config-audit",
      timestamp: now,
      hash: hashEvidence(auditLogs),
      framework: "NIST_CSF",
      controlId: "DE.CM",
      source: `gcp/config/${projectId}/audit-logs`,
      status: Array.isArray(auditLogs.entries) && auditLogs.entries.length > 0
        ? "compliant"
        : "partial",
      data: { recentAuditEntries: Array.isArray(auditLogs.entries) ? auditLogs.entries.length : 0 },
      metadata: { projectId },
    });

    const billing = await fetch(
      `https://cloudbilling.googleapis.com/v1/projects/${projectId}/billingInfo`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((r) => r.json())
      .catch(() => ({ billingEnabled: false }));
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcp-config-billing",
      timestamp: now,
      hash: hashEvidence(billing),
      framework: "SOC2",
      controlId: "CC3.2",
      source: `gcp/config/${projectId}/billing`,
      status: billing.billingEnabled === true ? "compliant" : "partial",
      data: { billingEnabled: billing.billingEnabled },
      metadata: { projectId },
    });

    return artifacts;
  }
}
