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
    id: "scc-findings",
    name: "Security Command Center Findings",
    description: "Fetch GCP Security Command Center findings",
    evidenceCategories: ["vulnerability_management", "risk_management"],
  },
  {
    id: "scc-sources",
    name: "Security Sources",
    description: "Fetch SCC security sources and their findings count",
    evidenceCategories: ["monitoring", "configuration"],
  },
];

export class GCPSCCConnector implements IntegrationConnector {
  readonly id = "gcp-scc";
  readonly name = "GCP Security Command Center";
  readonly category = "cloud_provider" as const;
  readonly authType = "service_account" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

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
      const orgId = config.extra?.orgId || config.accountId;
      const resp = await fetch(
        `https://securitycenter.googleapis.com/v1/organizations/${orgId}/sources`,
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
    const orgId = config.extra?.orgId || config.accountId;

    const findings = await fetch(
      `https://securitycenter.googleapis.com/v1/organizations/${orgId}/sources/-/findings?pageSize=100&filter=state%3D%22ACTIVE%22`,
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "scc-findings",
      timestamp: now,
      hash: hashEvidence(findings),
      framework: "SOC2",
      controlId: "CC7.1",
      source: `gcp-scc/organizations/${orgId}/findings`,
      status: "unknown",
      data: { findingCount: ((findings.findings as unknown[]) || []).length, findings: findings.findings },
      metadata: { orgId: orgId || "" },
    });

    const sources = await fetch(
      `https://securitycenter.googleapis.com/v1/organizations/${orgId}/sources`,
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "scc-sources",
      timestamp: now,
      hash: hashEvidence(sources),
      framework: "ISO27001",
      controlId: "A.12.4.1",
      source: `gcp-scc/organizations/${orgId}/sources`,
      status: ((sources.sources as unknown[]) || []).length > 0 ? "compliant" : "non_compliant",
      data: { sourceCount: ((sources.sources as unknown[]) || []).length },
      metadata: { orgId: orgId || "" },
    });

    return artifacts;
  }
}
