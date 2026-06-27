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
    id: "sentinel-incidents",
    name: "Sentinel Incidents",
    description: "Fetch Microsoft Sentinel security incidents",
    evidenceCategories: ["incident_management", "siem"],
  },
  {
    id: "sentinel-alerts",
    name: "Sentinel Alerts",
    description: "Fetch Sentinel alert rules and recent alerts",
    evidenceCategories: ["monitoring", "detection"],
  },
];

export class AzureSentinelConnector implements IntegrationConnector {
  readonly id = "azure-sentinel";
  readonly name = "Microsoft Sentinel";
  readonly category = "siem" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

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
          scope: "https://management.azure.com/.default",
        }),
      }
    );
    if (!resp.ok) throw new Error(`Azure token ${resp.status}`);
    const data = (await resp.json()) as Record<string, unknown>;
    return data.access_token as string;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getAccessToken(config);
      const workspace = config.extra?.workspace || "default";
      const resp = await fetch(
        `https://management.azure.com/subscriptions/${config.accountId}/resourceGroups/${config.extra?.resourceGroup || "default"}/providers/Microsoft.OperationalInsights/workspaces/${workspace}?api-version=2023-09-01`,
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
    const workspace = config.extra?.workspace || "default";
    const rg = config.extra?.resourceGroup || "default";
    const base = `https://management.azure.com/subscriptions/${config.accountId}/resourceGroups/${rg}/providers/Microsoft.OperationalInsights/workspaces/${workspace}`;

    const incidents = await fetch(
      `${base}/providers/Microsoft.SecurityInsights/incidents?api-version=2024-01-01&$top=100`,
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sentinel-incidents",
      timestamp: now,
      hash: hashEvidence(incidents),
      framework: "SOC2",
      controlId: "CC7.3",
      source: "azure-sentinel/incidents",
      status: "unknown",
      data: { incidentCount: ((incidents.value as unknown[]) || []).length, incidents: incidents.value },
      metadata: { workspace },
    });

    const alerts = await fetch(
      `${base}/providers/Microsoft.SecurityInsights/alertRules?api-version=2024-01-01`,
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "sentinel-alerts",
      timestamp: now,
      hash: hashEvidence(alerts),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "azure-sentinel/alertRules",
      status: ((alerts.value as unknown[]) || []).length > 0 ? "compliant" : "non_compliant",
      data: { alertRuleCount: ((alerts.value as unknown[]) || []).length },
      metadata: { workspace },
    });

    return artifacts;
  }
}
