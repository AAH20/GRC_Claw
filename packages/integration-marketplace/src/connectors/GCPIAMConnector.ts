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
    id: "gcp-iam-bindings",
    name: "IAM Bindings",
    description: "Fetch GCP project IAM policy bindings",
    evidenceCategories: ["access_control"],
  },
  {
    id: "gcp-iam-audit",
    name: "IAM Audit Logs",
    description: "Fetch admin activity and data access audit logs",
    evidenceCategories: ["logging", "audit"],
  },
];

export class GCPIAMConnector implements IntegrationConnector {
  readonly id = "gcp-iam";
  readonly name = "GCP IAM";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
  ];

  private async getAccessToken(config: ConnectorConfig): Promise<string> {
    const now = Math.floor(Date.now() / 1000);
    const header = Buffer.from(JSON.stringify({ alg: "RS256", typ: "JWT" })).toString("base64url");
    const payload = Buffer.from(
      JSON.stringify({
        iss: config.clientId,
        scope: "https://www.googleapis.com/auth/cloud-platform",
        aud: "https://oauth2.googleapis.com/token",
        exp: now + 3600,
        iat: now,
      })
    ).toString("base64url");
    const jwt = `${header}.${payload}.signature`;
    const resp = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
        assertion: jwt,
      }),
    });
    if (!resp.ok) throw new Error(`GCP token ${resp.status}`);
    const data = (await resp.json()) as Record<string, unknown>;
    return data.access_token as string;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getAccessToken(config);
      const resp = await fetch(
        `https://cloudresourcemanager.googleapis.com/v1/projects/${config.accountId}`,
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
    const token = await this.getAccessToken(config);
    const headers = { Authorization: `Bearer ${token}` };

    const iam = await fetch(
      `https://cloudresourcemanager.googleapis.com/v1/projects/${config.accountId}:getIamPolicy`,
      { method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: "{}" }
    ).then((r) => r.json()) as Record<string, unknown>;
    const bindings = (iam.bindings || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcp-iam-bindings",
      timestamp: now,
      hash: hashEvidence(iam),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `gcp/${config.accountId}/getIamPolicy`,
      status: bindings.length > 0 ? "compliant" : "non_compliant",
      data: { bindingCount: bindings.length, bindings },
      metadata: { projectId: config.accountId || "" },
    });

    const auditLogs = await fetch(
      `https://logging.googleapis.com/v2/entries:list?filter=logName%3D%22projects%2F${config.accountId}%2Flogs%2Fcloudaudit.googleapis.com%252Factivity%22&pageSize=50`,
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "gcp-iam-audit",
      timestamp: now,
      hash: hashEvidence(auditLogs),
      framework: "SOC2",
      controlId: "CC7.1",
      source: `gcp/${config.accountId}/auditLogs`,
      status: ((auditLogs.entries as unknown[]) || []).length > 0 ? "compliant" : "non_compliant",
      data: { logCount: ((auditLogs.entries as unknown[]) || []).length },
      metadata: { projectId: config.accountId || "" },
    });

    return artifacts;
  }
}
