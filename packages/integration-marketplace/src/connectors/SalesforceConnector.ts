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
    id: "sf-user-permissions",
    name: "User Permissions",
    description: "Fetch Salesforce user permission sets and profiles",
    evidenceCategories: ["access_control", "authorization"],
  },
  {
    id: "sf-field-security",
    name: "Field-Level Security",
    description: "Fetch field-level security configurations on sensitive objects",
    evidenceCategories: ["data_protection", "access_control"],
  },
];

export class SalesforceConnector implements IntegrationConnector {
  readonly id = "salesforce";
  readonly name = "Salesforce";
  readonly category = "hr" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "HIPAA"];

  private async getAccessToken(config: ConnectorConfig): Promise<string> {
    const resp = await fetch(
      `${config.baseUrl || "https://login.salesforce.com"}/services/oauth2/token`,
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "client_credentials",
          client_id: config.clientId || "",
          client_secret: config.clientSecret || "",
        }),
      }
    );
    if (!resp.ok) throw new Error(`Salesforce token ${resp.status}`);
    const data = (await resp.json()) as Record<string, unknown>;
    return data.access_token as string;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getAccessToken(config);
      const instanceUrl = config.extra?.instanceUrl || "https://your-instance.salesforce.com";
      const resp = await fetch(`${instanceUrl}/services/data/v59.0/limits`, {
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
    const instanceUrl = config.extra?.instanceUrl || "https://your-instance.salesforce.com";
    const headers = { Authorization: `Bearer ${token}` };

    const users = await fetch(
      `${instanceUrl}/services/data/v59.0/query?q=SELECT+Id,Username,ProfileId,IsActive+FROM+User+WHERE+IsActive=TRUE+LIMIT+200`,
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    const userList = (users.records || []) as Record<string, unknown>[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sf-user-permissions",
      timestamp: now,
      hash: hashEvidence({ userCount: userList.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "salesforce/users",
      status: "unknown",
      data: { activeUserCount: userList.length },
      metadata: { instanceUrl },
    });

    const fieldPerms = await fetch(
      `${instanceUrl}/services/data/v59.0/query?q=SELECT+ParentId,Field,Editable+FROM+FieldPermission+WHERE+Parent.Profile.Name='Standard+User'+LIMIT+100`,
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    const permRecords = (fieldPerms.records || []) as Record<string, unknown>[];
    const editableSensitive = permRecords.filter(
      (p) =>
        (p.Editable as boolean) === true &&
        ((p.Field as string) || "").includes("Email")
    );
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sf-field-security",
      timestamp: now,
      hash: hashEvidence({ permissionCount: permRecords.length }),
      framework: "ISO27001",
      controlId: "A.9.4.1",
      source: "salesforce/fieldPermissions",
      status: editableSensitive.length === 0 ? "compliant" : "partial",
      data: { fieldPermissionCount: permRecords.length, editableSensitiveFields: editableSensitive.length },
      metadata: { instanceUrl },
    });

    return artifacts;
  }
}
