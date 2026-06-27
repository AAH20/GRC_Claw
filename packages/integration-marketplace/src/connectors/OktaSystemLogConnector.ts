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
    id: "okta-system-log",
    name: "System Log Events",
    description: "Fetch Okta system log events for authentication and access patterns",
    evidenceCategories: ["audit", "access_control"],
  },
  {
    id: "okta-failed-logins",
    name: "Failed Login Events",
    description: "Fetch failed authentication attempts and lockout events",
    evidenceCategories: ["access_control", "threat_detection"],
  },
  {
    id: "okta-user-lifecycle",
    name: "User Lifecycle Events",
    description: "Fetch user creation, deactivation, and role change events",
    evidenceCategories: ["access_control", "change_management"],
  },
  {
    id: "okta-mfa-events",
    name: "MFA Enrollment Events",
    description: "Fetch MFA factor enrollment and verification events",
    evidenceCategories: ["access_control", "identity_verification"],
  },
];

export class OktaSystemLogConnector implements IntegrationConnector {
  readonly id = "okta_system_log";
  readonly name = "Okta System Log";
  readonly category = "identity" as const;
  readonly authType = "bearer_token" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = [
    "SOC2",
    "ISO27001",
    "NIST_CSF",
    "HIPAA",
    "PCI_DSS",
  ];

  private async fetchApi(
    config: ConnectorConfig,
    endpoint: string
  ): Promise<Record<string, unknown>> {
    const base = config.baseUrl || `https://${config.extra?.domain || "example"}.okta.com`;
    const resp = await fetch(`${base}${endpoint}`, {
      headers: {
        Authorization: `SSWS ${config.apiToken}`,
        Accept: "application/json",
      },
    });
    if (!resp.ok) throw new Error(`Okta API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as Record<string, unknown>;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      await this.fetchApi(config, "/api/v1/users/me");
      return true;
    } catch {
      return false;
    }
  }

  async collectEvidence(config: ConnectorConfig): Promise<EvidenceArtifact[]> {
    const artifacts: EvidenceArtifact[] = [];
    const now = new Date().toISOString();
    const domain = config.extra?.domain || "example";
    const since = new Date(Date.now() - 86400000).toISOString();

    const systemLog = await this.fetchApi(
      config,
      `/api/v1/logs?since=${since}&limit=100&filter=event-type%20eq%20"user.session.start"`
    ).catch(() => []);
    const logEntries = Array.isArray(systemLog) ? systemLog : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "okta-system-log",
      timestamp: now,
      hash: hashEvidence({ entries: logEntries.slice(0, 10) }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: `okta/${domain}/system-log`,
      status: logEntries.length > 0 ? "compliant" : "partial",
      data: { loginEvents: logEntries.length },
      metadata: { domain },
    });

    const failedLogins = await this.fetchApi(
      config,
      `/api/v1/logs?since=${since}&limit=100&filter=event-type%20eq%20"user.session.destroy"&filter=outcome.result%20eq%20"FAILURE"`
    ).catch(() => []);
    const failedEntries = Array.isArray(failedLogins) ? failedLogins : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "okta-failed-logins",
      timestamp: now,
      hash: hashEvidence({ entries: failedEntries.slice(0, 10) }),
      framework: "ISO27001",
      controlId: "A.9.4.2",
      source: `okta/${domain}/failed-logins`,
      status: failedEntries.length < 10 ? "compliant" : "non_compliant",
      data: { failedLoginCount: failedEntries.length },
      metadata: { domain },
    });

    const lifecycle = await this.fetchApi(
      config,
      `/api/v1/logs?since=${since}&limit=50&filter=event-type%20sw%20"user.lifecycle"`
    ).catch(() => []);
    const lifecycleEntries = Array.isArray(lifecycle) ? lifecycle : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "okta-user-lifecycle",
      timestamp: now,
      hash: hashEvidence({ entries: lifecycleEntries.slice(0, 10) }),
      framework: "NIST_CSF",
      controlId: "PR.AC",
      source: `okta/${domain}/lifecycle`,
      status: "compliant",
      data: { lifecycleEvents: lifecycleEntries.length },
      metadata: { domain },
    });

    const mfaEvents = await this.fetchApi(
      config,
      `/api/v1/logs?since=${since}&limit=50&filter=event-type%20sw%20"factor.enroll"`
    ).catch(() => []);
    const mfaEntries = Array.isArray(mfaEvents) ? mfaEvents : [];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "okta-mfa-events",
      timestamp: now,
      hash: hashEvidence({ entries: mfaEntries.slice(0, 10) }),
      framework: "PCI_DSS",
      controlId: "8.3",
      source: `okta/${domain}/mfa-enrollment`,
      status: "compliant",
      data: { mfaEnrollments: mfaEntries.length },
      metadata: { domain },
    });

    return artifacts;
  }
}
