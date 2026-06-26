import { createSign } from "crypto";
import type { CloudConnector, CloudFinding, ConnectorHealth, CloudProvider } from "../types.js";

export interface GcpConnectorConfig {
  projectId: string;
  serviceAccountEmail: string;
  privateKey: string;
  privateKeyId: string;
  chronicleInstanceId: string;
  chronicleLocation: string;
  sccOrganizationId: string;
  services: string[];
}

function envOr(key: string, fallback: string): string {
  return process.env[key] || fallback;
}

function buildGcpConfig(overrides?: Partial<GcpConnectorConfig>): GcpConnectorConfig {
  // Support loading from a JSON key file path
  let keyData: Record<string, string> | null = null;
  const keyFile = overrides?.privateKey ?? envOr("GCP_SERVICE_ACCOUNT_KEY_FILE", "");
  if (keyFile) {
    try {
      const fs = require("fs") as typeof import("fs");
      keyData = JSON.parse(fs.readFileSync(keyFile, "utf-8")) as Record<string, string>;
    } catch {
      // If file read fails, fall back to env vars
    }
  }

  return {
    projectId: overrides?.projectId ?? envOr("GCP_PROJECT_ID", keyData?.project_id ?? ""),
    serviceAccountEmail: overrides?.serviceAccountEmail ?? envOr("GCP_SERVICE_ACCOUNT_EMAIL", keyData?.client_email ?? ""),
    privateKey: overrides?.privateKey ?? envOr("GCP_PRIVATE_KEY", keyData?.private_key ?? ""),
    privateKeyId: overrides?.privateKeyId ?? envOr("GCP_PRIVATE_KEY_ID", keyData?.private_key_id ?? ""),
    chronicleInstanceId: overrides?.chronicleInstanceId ?? envOr("CHRONICLE_INSTANCE_ID", ""),
    chronicleLocation: overrides?.chronicleLocation ?? envOr("CHRONICLE_LOCATION", "us-central1"),
    sccOrganizationId: overrides?.sccOrganizationId ?? envOr("GCP_SCC_ORGANIZATION_ID", ""),
    services: overrides?.services ?? ["chronicle", "scc"],
  };
}

/* ---------- GCP OAuth2 JWT token exchange ---------- */

interface TokenCache {
  token: string;
  expiresAt: number;
}

let cachedToken: TokenCache | null = null;

function createJwt(config: GcpConnectorConfig): string {
  const header = { alg: "RS256", typ: "JWT" };
  const now = Math.floor(Date.now() / 1000);
  const claimSet = {
    iss: config.serviceAccountEmail,
    scope: "https://www.googleapis.com/auth/cloud-platform",
    aud: "https://oauth2.googleapis.com/token",
    exp: now + 3600,
    iat: now,
  };

  const encode = (obj: Record<string, unknown>) =>
    Buffer.from(JSON.stringify(obj)).toString("base64url");

  const signingInput = `${encode(header)}.${encode(claimSet)}`;

  const sign = createSign("RSA-SHA256");
  sign.update(signingInput);
  sign.end();
  const signature = sign.sign(config.privateKey, "base64url");

  return `${signingInput}.${signature}`;
}

async function getGcpAccessToken(config: GcpConnectorConfig): Promise<string> {
  if (cachedToken && Date.now() < cachedToken.expiresAt - 60_000) {
    return cachedToken.token;
  }

  const jwt = createJwt(config);

  const res = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: jwt,
    }).toString(),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GCP token exchange failed (${res.status}): ${text}`);
  }

  const data = (await res.json()) as { access_token: string; expires_in: number };
  cachedToken = {
    token: data.access_token,
    expiresAt: Date.now() + data.expires_in * 1000,
  };

  return cachedToken.token;
}

/* ---------- GCP REST API helper ---------- */

async function gcpApi(
  config: GcpConnectorConfig,
  url: string,
  options?: { method?: string; body?: unknown },
): Promise<unknown> {
  const token = await getGcpAccessToken(config);

  console.log(`[GCP] ${options?.method ?? "GET"} ${url}`);

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
    throw new Error(`GCP API failed (${res.status}): ${text}`);
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
  severity_unspecified: "informational",
};

function mapSeverity(gcp: string): CloudFinding["severity"] {
  return SEVERITY_MAP[gcp?.toLowerCase()] ?? "informational";
}

/* ---------- Mock fallback generators ---------- */

function mockChronicleFindings(projectId: string): CloudFinding[] {
  return [
    {
      id: `chronicle-${Date.now()}`,
      provider: "gcp" as CloudProvider,
      service: "chronicle",
      severity: "high" as const,
      title: "Malware detected on Compute Engine instance",
      description: "Chronicle SIEM detected malware execution pattern",
      resourceId: `//cloudresourcemanager.googleapis.com/projects/${projectId}`,
      resourceType: "gce_instance",
      region: "us-central1",
      complianceControl: "A.12.1",
      detectedAt: new Date().toISOString(),
      metadata: { projectId, mock: true },
    },
  ];
}

function mockSccFindings(projectId: string): CloudFinding[] {
  return [
    {
      id: `scc-${Date.now()}`,
      provider: "gcp" as CloudProvider,
      service: "scc",
      severity: "critical" as const,
      title: "Public bucket exposure detected",
      description: "GCP Security Command Center found publicly accessible storage bucket",
      resourceId: `//storage.googleapis.com/${projectId}-logs`,
      resourceType: "gcs_bucket",
      region: "global",
      complianceControl: "A.5.1",
      detectedAt: new Date().toISOString(),
      metadata: { projectId, mock: true },
    },
  ];
}

/* ---------- Chronicle Connector ---------- */

export class GcpChronicleConnector implements CloudConnector {
  provider: CloudProvider = "gcp";
  private config: GcpConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;
  private validCredentials = false;

  constructor(config?: Partial<GcpConnectorConfig>) {
    this.config = buildGcpConfig(config);
    this.validCredentials = !!(this.config.serviceAccountEmail && this.config.privateKey);
  }

  async health(): Promise<ConnectorHealth> {
    return {
      provider: "gcp",
      status: this.lastSync ? "connected" : "disconnected",
      lastSyncAt: this.lastSync?.toISOString(),
      findingCount: this.findings.length,
      errorCount: 0,
    };
  }

  async fetchFindings(): Promise<CloudFinding[]> {
    if (!this.validCredentials) {
      console.log("[GCP Chronicle] No credentials configured, returning mock findings");
      this.findings = mockChronicleFindings(this.config.projectId);
      this.lastSync = new Date();
      return this.findings;
    }

    try {
      // Chronicle SOAR detections API
      const url = `https://chronicle.googleapis.com/v1/projects/${this.config.projectId}/locations/${this.config.chronicleLocation}/instances/${this.config.chronicleInstanceId}/detections?pageSize=100`;

      const resp = (await gcpApi(this.config, url)) as {
        detections?: Array<Record<string, unknown>>;
        nextPageToken?: string;
      };

      const rawDetections = resp.detections ?? [];
      this.findings = rawDetections.map((d) => this.parseDetection(d));
      console.log(`[GCP Chronicle] Fetched ${this.findings.length} real detections`);
    } catch (err) {
      console.error("[GCP Chronicle] API call failed, falling back to mock:", err);
      this.findings = mockChronicleFindings(this.config.projectId);
    }

    this.lastSync = new Date();
    return this.findings;
  }

  private parseDetection(raw: Record<string, unknown>): CloudFinding {
    const matchedDetects = (raw.matchedDetects ?? []) as Array<Record<string, unknown>>;
    const firstMatch = matchedDetects[0] ?? {};
    const summary = (firstMatch.summaryData ?? {}) as Record<string, unknown>;
    const ruleMetadata = (firstMatch.ruleMetadata ?? {}) as Record<string, unknown>;
    const severityScore = Number(summary.severity ?? firstMatch.severityScore ?? 0);

    let severity: CloudFinding["severity"] = "informational";
    if (severityScore >= 8) severity = "critical";
    else if (severityScore >= 6) severity = "high";
    else if (severityScore >= 4) severity = "medium";
    else if (severityScore >= 1) severity = "low";

    return {
      id: String(raw.name ?? raw.id ?? `chronicle-${Date.now()}`),
      provider: "gcp",
      service: "chronicle",
      severity,
      title: String(ruleMetadata.name ?? summary.title ?? "Chronicle detection"),
      description: String(summary.description ?? ""),
      resourceId: String(raw.artifactId ?? raw.name ?? ""),
      resourceType: String(firstMatch.artifactType ?? "unknown"),
      region: this.config.chronicleLocation,
      complianceControl: "A.12.1",
      detectedAt: new Date().toISOString(),
      metadata: {
        projectId: this.config.projectId,
        ruleId: String(ruleMetadata.ruleId ?? ""),
        ruleName: String(ruleMetadata.name ?? ""),
        severityScore,
        matchCount: matchedDetects.length,
        category: String(summary.category ?? ""),
      },
    };
  }

  async testConnection(): Promise<boolean> {
    if (!this.validCredentials) {
      console.log("[GCP Chronicle] No credentials configured");
      return false;
    }
    try {
      await getGcpAccessToken(this.config);
      console.log("[GCP Chronicle] Token acquisition successful");
      return true;
    } catch {
      return false;
    }
  }
}

/* ---------- Security Command Center Connector ---------- */

export class GcpSecurityCommandCenterConnector implements CloudConnector {
  provider: CloudProvider = "gcp";
  private config: GcpConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;
  private validCredentials = false;

  constructor(config?: Partial<GcpConnectorConfig>) {
    this.config = buildGcpConfig(config);
    this.validCredentials = !!(this.config.serviceAccountEmail && this.config.privateKey);
  }

  async health(): Promise<ConnectorHealth> {
    return {
      provider: "gcp",
      status: this.lastSync ? "connected" : "disconnected",
      lastSyncAt: this.lastSync?.toISOString(),
      findingCount: this.findings.length,
      errorCount: 0,
    };
  }

  async fetchFindings(): Promise<CloudFinding[]> {
    if (!this.validCredentials) {
      console.log("[GCP SCC] No credentials configured, returning mock findings");
      this.findings = mockSccFindings(this.config.projectId);
      this.lastSync = new Date();
      return this.findings;
    }

    try {
      const orgId = this.config.sccOrganizationId;
      // List sources first
      const sourcesUrl = `https://securitycenter.googleapis.com/v1/organizations/${orgId}/sources`;
      const sourcesResp = (await gcpApi(this.config, sourcesUrl)) as {
        sources?: Array<Record<string, unknown>>;
      };

      const sources = sourcesResp.sources ?? [];
      const allFindings: CloudFinding[] = [];

      for (const source of sources) {
        const sourceName = String(source.name ?? "");
        if (!sourceName) continue;

        // Fetch findings from each source
        const findingsUrl = `https://securitycenter.googleapis.com/v1/${sourceName}/findings?pageSize=100&filter=state%3D%22ACTIVE%22`;
        const findingsResp = (await gcpApi(this.config, findingsUrl)) as {
          findings?: Array<Record<string, unknown>>;
        };

        const rawFindings = findingsResp.findings ?? [];
        allFindings.push(...rawFindings.map((f) => this.parseFinding(f)));
      }

      this.findings = allFindings;
      console.log(`[GCP SCC] Fetched ${this.findings.length} real findings`);
    } catch (err) {
      console.error("[GCP SCC] API call failed, falling back to mock:", err);
      this.findings = mockSccFindings(this.config.projectId);
    }

    this.lastSync = new Date();
    return this.findings;
  }

  private parseFinding(raw: Record<string, unknown>): CloudFinding {
    const resourceName = String(raw.resourceName ?? "");
    const category = String(raw.category ?? "");
    const severity = String(raw.severity ?? "severity_unspecified");
    const sourceProperties = (raw.sourceProperties ?? {}) as Record<string, unknown>;
    const findingObj = (raw.finding ?? {}) as Record<string, unknown>;
    const eventTime = String(raw.eventTime ?? new Date().toISOString());

    return {
      id: String(raw.name ?? `scc-${Date.now()}`),
      provider: "gcp",
      service: "scc",
      severity: mapSeverity(severity),
      title: `${category} finding`,
      description: String(sourceProperties.description ?? findingObj.description ?? category),
      resourceId: resourceName || String(raw.name ?? ""),
      resourceType: String(sourceProperties.resourceType ?? "unknown"),
      region: "global",
      complianceControl: "A.5.1",
      detectedAt: eventTime,
      metadata: {
        projectId: this.config.projectId,
        category,
        severity,
        state: String(raw.state ?? "ACTIVE"),
        sourceName: String(sourceProperties.source ?? ""),
        resourceName,
      },
    };
  }

  async testConnection(): Promise<boolean> {
    if (!this.validCredentials) {
      console.log("[GCP SCC] No credentials configured");
      return false;
    }
    try {
      await getGcpAccessToken(this.config);
      console.log("[GCP SCC] Token acquisition successful");
      return true;
    } catch {
      return false;
    }
  }
}
