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
    id: "aad-conditional-access",
    name: "Conditional Access Policies",
    description: "Fetch Azure AD conditional access policies",
    evidenceCategories: ["access_control"],
  },
  {
    id: "aad-mfa-enrollment",
    name: "MFA Enrollment",
    description: "Fetch MFA enrollment statistics and per-user MFA status",
    evidenceCategories: ["authentication"],
  },
  {
    id: "aad-app-registrations",
    name: "App Registrations",
    description: "Fetch app registrations and service principals",
    evidenceCategories: ["access_control", "application_security"],
  },
];

export class AzureADConnector implements IntegrationConnector {
  readonly id = "azure-ad";
  readonly name = "Azure Active Directory";
  readonly category = "identity" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
  ];

  private async getAccessToken(config: ConnectorConfig): Promise<string> {
    const resp = await fetch(
      `https://login.microsoftonline.com/${config.tenantId}/oauth2/v2.0/token`,
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "client_credentials",
          client_id: config.clientId || "",
          client_secret: config.clientSecret || "",
          scope: "https://graph.microsoft.com/.default",
        }),
      }
    );
    if (!resp.ok) throw new Error(`Azure AD token ${resp.status}`);
    const data = (await resp.json()) as Record<string, unknown>;
    return data.access_token as string;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getAccessToken(config);
      const resp = await fetch("https://graph.microsoft.com/v1.0/$metadata", {
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
    const token = await this.getAccessToken(config);
    const headers = { Authorization: `Bearer ${token}` };

    const policies = await fetch(
      "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies",
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "aad-conditional-access",
      timestamp: now,
      hash: hashEvidence(policies),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "azure-ad/conditionalAccess/policies",
      status: ((policies.value as unknown[]) || []).length > 0 ? "compliant" : "non_compliant",
      data: { policyCount: ((policies.value as unknown[]) || []).length, policies: policies.value },
      metadata: { tenantId: config.tenantId || "" },
    });

    const mfaReport = await fetch(
      "https://graph.microsoft.com/v1.0/reports/authenticationMethods/userRegistrationDetails?$select=isMfaRegistered,isMfaCapable",
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    const users = (mfaReport.value || []) as Record<string, unknown>[];
    const mfaRegistered = users.filter((u) => u.isMfaRegistered === true).length;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "aad-mfa-enrollment",
      timestamp: now,
      hash: hashEvidence(mfaReport),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "azure-ad/authenticationMethods/userRegistrationDetails",
      status: users.length > 0 && mfaRegistered / users.length > 0.9 ? "compliant" : "partial",
      data: { totalUsers: users.length, mfaRegistered, mfaCapable: users.filter((u) => u.isMfaCapable === true).length },
      metadata: { tenantId: config.tenantId || "" },
    });

    const apps = await fetch("https://graph.microsoft.com/v1.0/applicationRegistrations", {
      headers,
    }).then((r) => r.json()) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "aad-app-registrations",
      timestamp: now,
      hash: hashEvidence(apps),
      framework: "ISO27001",
      controlId: "A.14.2.5",
      source: "azure-ad/applicationRegistrations",
      status: "unknown",
      data: { appCount: ((apps.value as unknown[]) || []).length, apps: apps.value },
      metadata: { tenantId: config.tenantId || "" },
    });

    return artifacts;
  }
}
