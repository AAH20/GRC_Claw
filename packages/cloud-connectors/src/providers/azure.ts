import type { CloudConnector, CloudFinding, ConnectorHealth, CloudProvider } from "../types.js";

export interface AzureConnectorConfig {
  tenantId: string;
  clientId: string;
  clientSecret: string;
  subscriptionId: string;
  resourceGroup: string;
  workspaceName: string;
  services: string[];
}

function envOr(key: string, fallback: string): string {
  return process.env[key] || fallback;
}

function buildAzureConfig(overrides?: Partial<AzureConnectorConfig>): AzureConnectorConfig {
  return {
    tenantId: overrides?.tenantId ?? envOr("AZURE_TENANT_ID", ""),
    clientId: overrides?.clientId ?? envOr("AZURE_CLIENT_ID", ""),
    clientSecret: overrides?.clientSecret ?? envOr("AZURE_CLIENT_SECRET", ""),
    subscriptionId: overrides?.subscriptionId ?? envOr("AZURE_SUBSCRIPTION_ID", ""),
    resourceGroup: overrides?.resourceGroup ?? envOr("AZURE_RESOURCE_GROUP", "rg-soc"),
    workspaceName: overrides?.workspaceName ?? envOr("AZURE_WORKSPACE_NAME", "law-soc"),
    services: overrides?.services ?? ["sentinel", "defender"],
  };
}

/* ---------- Azure AD OAuth2 token acquisition ---------- */

interface TokenCache {
  token: string;
  expiresAt: number;
}

let cachedToken: TokenCache | null = null;

async function getAzureAdToken(config: AzureConnectorConfig): Promise<string> {
  if (cachedToken && Date.now() < cachedToken.expiresAt - 60_000) {
    return cachedToken.token;
  }

  const tokenUrl = `https://login.microsoftonline.com/${config.tenantId}/oauth2/v2.0/token`;
  const body = new URLSearchParams({
    client_id: config.clientId,
    client_secret: config.clientSecret,
    scope: "https://management.azure.com/.default",
    grant_type: "client_credentials",
  });

  const res = await fetch(tokenUrl, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Azure AD token acquisition failed (${res.status}): ${text}`);
  }

  const data = (await res.json()) as { access_token: string; expires_in: number };
  cachedToken = {
    token: data.access_token,
    expiresAt: Date.now() + data.expires_in * 1000,
  };

  return cachedToken.token;
}

/* ---------- Azure REST API helper ---------- */

async function azureApi(
  config: AzureConnectorConfig,
  path: string,
  apiVersion: string,
  options?: { method?: string; body?: unknown },
): Promise<unknown> {
  const token = await getAzureAdToken(config);
  const separator = path.includes("?") ? "&" : "?";
  const url = `https://management.azure.com${path}${separator}api-version=${apiVersion}`;

  console.log(`[Azure] ${options?.method ?? "GET"} ${path}`);

  const res = await fetch(url, {
    method: options?.method ?? "GET",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: options?.body ? JSON.stringify(options.body) : undefined,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Azure API ${path} failed (${res.status}): ${text}`);
  }

  return res.json();
}

/* ---------- Severity mapping ---------- */

const SEVERITY_MAP: Record<string, CloudFinding["severity"]> = {
  critical: "critical",
  high: "high",
  medium: "medium",
  low: "low",
  informational: "informational",
  unknown: "informational",
};

function mapSeverity(azure: string): CloudFinding["severity"] {
  return SEVERITY_MAP[azure?.toLowerCase()] ?? "informational";
}

/* ---------- Mock fallback generators ---------- */

function mockSentinelFindings(subscriptionId: string, tenantId: string): CloudFinding[] {
  return [
    {
      id: `sentinel-${Date.now()}`,
      provider: "azure" as CloudProvider,
      service: "sentinel",
      severity: "high" as const,
      title: "Suspicious login activity detected",
      description: "Azure AD sign-in logs show suspicious activity from anomalous location",
      resourceId: `/subscriptions/${subscriptionId}/resourceGroups/rg-prod`,
      resourceType: "Microsoft.Security/Alerts",
      region: "global",
      complianceControl: "A.9.1",
      detectedAt: new Date().toISOString(),
      metadata: { tenantId, mock: true },
    },
  ];
}

function mockDefenderFindings(subscriptionId: string): CloudFinding[] {
  return [
    {
      id: `defender-${Date.now()}`,
      provider: "azure" as CloudProvider,
      service: "defender",
      severity: "medium" as const,
      title: "VM vulnerability assessment",
      description: "Azure Defender detected vulnerable packages on VM",
      resourceId: `/subscriptions/${subscriptionId}/providers/Microsoft.Security`,
      resourceType: "Microsoft.Security/Assessments",
      region: "global",
      complianceControl: "A.12.1",
      detectedAt: new Date().toISOString(),
      metadata: { assessmentName: "vmVulnerabilityAssessment", mock: true },
    },
  ];
}

/* ---------- Sentinel Connector ---------- */

export class AzureSentinelConnector implements CloudConnector {
  provider: CloudProvider = "azure";
  private config: AzureConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;
  private validCredentials = false;

  constructor(config?: Partial<AzureConnectorConfig>) {
    this.config = buildAzureConfig(config);
    this.validCredentials = !!(this.config.tenantId && this.config.clientId && this.config.clientSecret);
  }

  async health(): Promise<ConnectorHealth> {
    return {
      provider: "azure",
      status: this.lastSync ? "connected" : "disconnected",
      lastSyncAt: this.lastSync?.toISOString(),
      findingCount: this.findings.length,
      errorCount: 0,
    };
  }

  async fetchFindings(): Promise<CloudFinding[]> {
    if (!this.validCredentials) {
      console.log("[Azure Sentinel] No credentials configured, returning mock findings");
      this.findings = mockSentinelFindings(this.config.subscriptionId, this.config.tenantId);
      this.lastSync = new Date();
      return this.findings;
    }

    try {
      const path = `/subscriptions/${this.config.subscriptionId}/resourceGroups/${this.config.resourceGroup}/providers/Microsoft.OperationalInsights/workspaces/${this.config.workspaceName}/providers/Microsoft.SecurityInsights/incidents`;
      const resp = (await azureApi(this.config, path, "2023-03-01-preview")) as {
        value?: Array<Record<string, unknown>>;
      };

      const rawIncidents = resp.value ?? [];
      this.findings = rawIncidents.map((inc) => this.parseIncident(inc));
      console.log(`[Azure Sentinel] Fetched ${this.findings.length} real incidents`);
    } catch (err) {
      console.error("[Azure Sentinel] API call failed, falling back to mock:", err);
      this.findings = mockSentinelFindings(this.config.subscriptionId, this.config.tenantId);
    }

    this.lastSync = new Date();
    return this.findings;
  }

  private parseIncident(raw: Record<string, unknown>): CloudFinding {
    const properties = (raw.properties ?? {}) as Record<string, unknown>;
    const severity = String(properties.severity ?? "Unknown");

    // Map Azure severity labels
    const severityOrder: Record<string, number> = {
      critical: 5,
      high: 4,
      medium: 3,
      low: 2,
      informational: 1,
    };

    const title = String(properties.title ?? "Untitled incident");
    const description = String(properties.description ?? "");
    const status = String(properties.status ?? "");
    const owner = (properties.owner ?? {}) as Record<string, unknown>;
    const ownerName = String(owner.name ?? "unassigned");

    return {
      id: String(raw.name ?? raw.id ?? `sentinel-${Date.now()}`),
      provider: "azure",
      service: "sentinel",
      severity: mapSeverity(severity),
      title,
      description: description || `Incident status: ${status}, Owner: ${ownerName}`,
      resourceId: String(raw.id ?? ""),
      resourceType: "Microsoft.SecurityInsights/Incidents",
      region: "global",
      complianceControl: "A.9.1",
      detectedAt: new Date().toISOString(),
      metadata: {
        tenantId: this.config.tenantId,
        status,
        severity,
        owner: ownerName,
        incidentNumber: (properties as Record<string, unknown>).number ?? null,
        additionalData: (properties as Record<string, unknown>).additionalData ?? null,
      },
    };
  }

  async testConnection(): Promise<boolean> {
    if (!this.validCredentials) {
      console.log("[Azure Sentinel] No credentials configured");
      return false;
    }
    try {
      await getAzureAdToken(this.config);
      console.log("[Azure Sentinel] Token acquisition successful");
      return true;
    } catch (err) {
      console.error("[Azure Sentinel] Token acquisition failed:", err);
      return false;
    }
  }
}

/* ---------- Defender Connector ---------- */

export class AzureDefenderConnector implements CloudConnector {
  provider: CloudProvider = "azure";
  private config: AzureConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;
  private validCredentials = false;

  constructor(config?: Partial<AzureConnectorConfig>) {
    this.config = buildAzureConfig(config);
    this.validCredentials = !!(this.config.tenantId && this.config.clientId && this.config.clientSecret);
  }

  async health(): Promise<ConnectorHealth> {
    return {
      provider: "azure",
      status: this.lastSync ? "connected" : "disconnected",
      lastSyncAt: this.lastSync?.toISOString(),
      findingCount: this.findings.length,
      errorCount: 0,
    };
  }

  async fetchFindings(): Promise<CloudFinding[]> {
    if (!this.validCredentials) {
      console.log("[Azure Defender] No credentials configured, returning mock findings");
      this.findings = mockDefenderFindings(this.config.subscriptionId);
      this.lastSync = new Date();
      return this.findings;
    }

    try {
      // Fetch Defender security statuses
      const path = `/subscriptions/${this.config.subscriptionId}/providers/Microsoft.Security/securityStatuses`;
      const resp = (await azureApi(this.config, path, "2015-06-01-preview")) as {
        value?: Array<Record<string, unknown>>;
      };

      const rawStatuses = resp.value ?? [];
      this.findings = rawStatuses
        .filter((s) => {
          const sProps = (s.properties ?? {}) as Record<string, unknown>;
          const status = String(sProps.status ?? "").toLowerCase();
          return status !== "healthy" && status !== "notapplicable";
        })
        .map((s) => this.parseSecurityStatus(s));

      // Also fetch active security alerts
      try {
        const alertPath = `/subscriptions/${this.config.subscriptionId}/providers/Microsoft.Security/alerts`;
        const alertResp = (await azureApi(this.config, alertPath, "2015-05-01")) as {
          value?: Array<Record<string, unknown>>;
        };
        const alertFindings = (alertResp.value ?? []).map((a) => this.parseAlert(a));
        this.findings.push(...alertFindings);
      } catch {
        // alerts API may not be available in all tenants
      }

      console.log(`[Azure Defender] Fetched ${this.findings.length} real findings`);
    } catch (err) {
      console.error("[Azure Defender] API call failed, falling back to mock:", err);
      this.findings = mockDefenderFindings(this.config.subscriptionId);
    }

    this.lastSync = new Date();
    return this.findings;
  }

  private parseSecurityStatus(raw: Record<string, unknown>): CloudFinding {
    const props = (raw.properties ?? {}) as Record<string, unknown>;
    const status = String(props.status ?? "Unknown");

    let severity: CloudFinding["severity"] = "medium";
    if (status.includes("critical") || status.includes("high")) severity = "high";
    else if (status.includes("medium")) severity = "medium";
    else if (status.includes("low")) severity = "low";

    return {
      id: String(raw.id ?? `defender-${Date.now()}`),
      provider: "azure",
      service: "defender",
      severity,
      title: String(raw.name ?? "Defender security status"),
      description: `Security status: ${status}`,
      resourceId: String(raw.id ?? ""),
      resourceType: "Microsoft.Security/securityStatuses",
      region: "global",
      complianceControl: "A.12.1",
      detectedAt: new Date().toISOString(),
      metadata: {
        subscriptionId: this.config.subscriptionId,
        status,
        displayName: String(raw.name ?? ""),
      },
    };
  }

  private parseAlert(raw: Record<string,unknown>): CloudFinding {
    const props = (raw.properties ?? {}) as Record<string, unknown>;
    return {
      id: String(raw.name ?? raw.id ?? `defender-alert-${Date.now()}`),
      provider: "azure",
      service: "defender",
      severity: mapSeverity(String(props.severity ?? "medium")),
      title: String(props.alertName ?? props.description ?? "Defender alert"),
      description: String(props.description ?? ""),
      resourceId: String(raw.id ?? ""),
      resourceType: "Microsoft.Security/alerts",
      region: "global",
      complianceControl: "A.12.1",
      detectedAt: String(props.startTimeUtc ?? new Date().toISOString()),
      metadata: {
        subscriptionId: this.config.subscriptionId,
        compromisedEntity: String(props.compromisedEntity ?? ""),
        attackTechniques: props.attackTechniques ?? [],
      },
    };
  }

  async testConnection(): Promise<boolean> {
    if (!this.validCredentials) {
      console.log("[Azure Defender] No credentials configured");
      return false;
    }
    try {
      await getAzureAdToken(this.config);
      console.log("[Azure Defender] Token acquisition successful");
      return true;
    } catch {
      return false;
    }
  }
}
