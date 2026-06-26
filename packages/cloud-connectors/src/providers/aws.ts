import { createHmac } from "crypto";
import type { CloudConnector, CloudFinding, ConnectorHealth, CloudProvider } from "../types.js";

export interface AwsConnectorConfig {
  accessKey: string;
  secretKey: string;
  region: string;
  services: string[];
  accountId?: string;
}

function envOr(key: string, fallback: string): string {
  return process.env[key] || fallback;
}

function buildAwsConfig(overrides?: Partial<AwsConnectorConfig>): AwsConnectorConfig {
  return {
    accessKey: overrides?.accessKey ?? envOr("AWS_ACCESS_KEY_ID", ""),
    secretKey: overrides?.secretKey ?? envOr("AWS_SECRET_ACCESS_KEY", ""),
    region: overrides?.region ?? envOr("AWS_REGION", "us-east-1"),
    services: overrides?.services ?? ["securityhub", "guardduty"],
    accountId: overrides?.accountId ?? envOr("AWS_ACCOUNT_ID", ""),
  };
}

/* ---------- AWS Signature V4 implementation ---------- */

interface SigV4Request {
  method: string;
  host: string;
  path: string;
  region: string;
  service: string;
  accessKey: string;
  secretKey: string;
  headers?: Record<string, string>;
  body?: string;
}

function sha256Hex(data: string): string {
  return createHmac("sha256", "").update(data).digest("hex");
}

function hmac(key: string | Buffer, data: string): Buffer {
  return createHmac("sha256", key).update(data).digest();
}

function getSignatureKey(secretKey: string, dateStamp: string, region: string, service: string): Buffer {
  const kDate = hmac(`AWS4${secretKey}`, dateStamp);
  const kRegion = hmac(kDate, region);
  const kService = hmac(kRegion, service);
  return hmac(kService, "aws4_request");
}

function signRequest(req: SigV4Request): { url: string; headers: Record<string, string> } {
  const now = new Date();
  const amzDate = now.toISOString().replace(/[:-]|\.\d{3}/g, "").slice(0, 15) + "Z";
  const dateStamp = amzDate.slice(0, 8);

  const payloadHash = sha256Hex(req.body ?? "");
  const canonicalHeaders = Object.entries({
    "host": req.host,
    "x-amz-date": amzDate,
    "x-amz-target": req.headers?.["x-amz-target"] ?? "",
    ...req.headers,
  })
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}:${v}`)
    .join("\n");

  const signedHeaders = Object.entries({
    "host": req.host,
    "x-amz-date": amzDate,
    "x-amz-target": req.headers?.["x-amz-target"] ?? "",
    ...req.headers,
  })
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k]) => k)
    .join(";");

  const canonicalRequest = [
    req.method,
    req.path,
    "", // empty query string
    canonicalHeaders,
    "",
    signedHeaders,
    payloadHash,
  ].join("\n");

  const credentialScope = `${dateStamp}/${req.region}/${req.service}/aws4_request`;
  const stringToSign = [
    "AWS4-HMAC-SHA256",
    amzDate,
    credentialScope,
    sha256Hex(canonicalRequest),
  ].join("\n");

  const signingKey = getSignatureKey(req.secretKey, dateStamp, req.region, req.service);
  const signature = hmac(signingKey, stringToSign).toString("hex");

  const authorization = `AWS4-HMAC-SHA256 Credential=${req.accessKey}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${signature}`;

  const headers: Record<string, string> = {
    "Host": req.host,
    "X-Amz-Date": amzDate,
    "X-Amz-Content-Sha256": payloadHash,
    "Authorization": authorization,
    ...req.headers,
  };

  return { url: `https://${req.host}${req.path}`, headers };
}

/* ---------- AWS JSON 1.1 RPC helper ---------- */

async function awsJsonRpc(
  config: AwsConnectorConfig,
  service: string,
  target: string,
  body: Record<string, unknown>,
): Promise<unknown> {
  const host = `${service}.${config.region}.amazonaws.com`;
  const path = "/";
  const bodyStr = JSON.stringify(body);

  const { url, headers } = signRequest({
    method: "POST",
    host,
    path,
    region: config.region,
    service,
    accessKey: config.accessKey,
    secretKey: config.secretKey,
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": target,
    },
    body: bodyStr,
  });

  console.log(`[AWS] ${service} -> ${target}`);

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: bodyStr,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`AWS ${service} ${target} failed (${res.status}): ${text}`);
  }

  return res.json();
}

/* ---------- STS GetCallerIdentity ---------- */

async function stsGetCallerIdentity(config: AwsConnectorConfig): Promise<Record<string, unknown>> {
  return awsJsonRpc(config, "sts", "AWSSecurityTokenServiceV20110601.GetCallerIdentity", {}) as Promise<Record<string, unknown>>;
}

/* ---------- Severity mapping ---------- */

const SEVERITY_MAP: Record<string, CloudFinding["severity"]> = {
  CRITICAL: "critical",
  HIGH: "high",
  MEDIUM: "medium",
  LOW: "low",
  INFORMATIONAL: "informational",
};

function mapSeverity(aws: string): CloudFinding["severity"] {
  return SEVERITY_MAP[aws?.toUpperCase()] ?? "informational";
}

/* ---------- Mock fallback generators ---------- */

function mockSecurityHubFindings(services: string[], region: string): CloudFinding[] {
  return services.map((service) => ({
    id: `aws-${service}-${Date.now()}`,
    provider: "aws" as CloudProvider,
    service,
    severity: "high" as const,
    title: `Security group misconfiguration in ${service}`,
    description: `Found overly permissive security group rules for ${service}`,
    resourceId: `arn:aws:${region}:123456789:resource/test`,
    resourceType: "AWS::EC2::SecurityGroup",
    region,
    complianceControl: "A.5.1",
    detectedAt: new Date().toISOString(),
    metadata: { accountId: "123456789", mock: true },
  }));
}

function mockGuardDutyFindings(region: string): CloudFinding[] {
  return [
    {
      id: `gd-${Date.now()}`,
      provider: "aws" as CloudProvider,
      service: "guardduty",
      severity: "critical" as const,
      title: "Unauthorized API call detected",
      description: "GuardDuty detected unauthorized API call from unknown IP",
      resourceId: `arn:aws:ec2:${region}:123456789:instance/i-1234567890`,
      resourceType: "AWS::EC2::Instance",
      region,
      complianceControl: "A.5.1",
      detectedAt: new Date().toISOString(),
      metadata: { detectorId: "det-123", severity: 8, mock: true },
    },
  ];
}

/* ---------- Connectors ---------- */

export class AwsSecurityHubConnector implements CloudConnector {
  provider: CloudProvider = "aws";
  private config: AwsConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;
  private validCredentials = false;

  constructor(config?: Partial<AwsConnectorConfig>) {
    this.config = buildAwsConfig(config);
    this.validCredentials = !!(this.config.accessKey && this.config.secretKey);
  }

  async health(): Promise<ConnectorHealth> {
    return {
      provider: "aws",
      status: this.lastSync ? "connected" : "disconnected",
      lastSyncAt: this.lastSync?.toISOString(),
      findingCount: this.findings.length,
      errorCount: 0,
      nextSyncAt: new Date(Date.now() + 300000).toISOString(),
    };
  }

  async fetchFindings(): Promise<CloudFinding[]> {
    if (!this.validCredentials) {
      console.log("[AWS SecurityHub] No credentials configured, returning mock findings");
      this.findings = mockSecurityHubFindings(this.config.services, this.config.region);
      this.lastSync = new Date();
      return this.findings;
    }

    const allFindings: CloudFinding[] = [];

    try {
      const body = await awsJsonRpc(
        this.config,
        "securityhub",
        "SecurityHub.GetFindings",
        {
          MaxResults: 100,
          SortCriteria: [{ Field: { Field: "severity" }, SortOrder: "desc" }],
        },
      );

      const data = body as { Findings?: Array<Record<string, unknown>> };
      const rawFindings = data.Findings ?? [];

      for (const f of rawFindings) {
        allFindings.push(this.parseFinding(f));
      }

      console.log(`[AWS SecurityHub] Fetched ${allFindings.length} real findings`);
    } catch (err) {
      console.error("[AWS SecurityHub] API call failed, falling back to mock:", err);
      allFindings.push(...mockSecurityHubFindings(this.config.services, this.config.region));
    }

    this.findings = allFindings;
    this.lastSync = new Date();
    return this.findings;
  }

  private parseFinding(raw: Record<string, unknown>): CloudFinding {
    const resources = (raw.Resources ?? []) as Array<Record<string, unknown>>;
    const resource = resources[0] ?? {};
    const details = (raw.ProductFields ?? {}) as Record<string, string>;
    const severity = (raw.Severity ?? {}) as Record<string, unknown>;
    const workflow = (raw.Workflow ?? {}) as Record<string, unknown>;
    const confidence = (raw.Confidence ?? {}) as Record<string, unknown>;

    return {
      id: String(raw.Id ?? raw.GeneratorId ?? `aws-sh-${Date.now()}`),
      provider: "aws",
      service: String(details["aws/securityhub/ServiceName"] ?? "securityhub"),
      severity: mapSeverity(String(severity.Label ?? severity.Normalized ?? "LOW")),
      title: String(raw.Title ?? "Untitled finding"),
      description: String(raw.Description ?? ""),
      resourceId: String(resource.Id ?? raw.Id ?? ""),
      resourceType: String(resource.Type ?? raw.ProductName ?? "AWS::Unknown"),
      region: String(raw.Region ?? this.config.region),
      complianceControl: details["StandardsControlArn"] ?? undefined,
      detectedAt: new Date().toISOString(),
      metadata: {
        accountId: String(raw.AwsAccountId ?? ""),
        productName: String(raw.ProductName ?? ""),
        companyName: String(raw.CompanyName ?? ""),
        workflowStatus: String(workflow.Status ?? ""),
        recordState: String(raw.RecordState ?? ""),
        confidence: confidence.Normalized ?? null,
      },
    };
  }

  async testConnection(): Promise<boolean> {
    if (!this.validCredentials) {
      console.log("[AWS] No credentials configured, skipping STS check");
      return false;
    }
    try {
      const resp = await stsGetCallerIdentity(this.config);
      const arn = (resp as { Arn?: string }).Arn ?? "unknown";
      console.log(`[AWS] STS GetCallerIdentity OK: ${arn}`);
      return true;
    } catch (err) {
      console.error("[AWS] STS GetCallerIdentity failed:", err);
      return false;
    }
  }
}

export class AwsGuardDutyConnector implements CloudConnector {
  provider: CloudProvider = "aws";
  private config: AwsConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;
  private validCredentials = false;

  constructor(config?: Partial<AwsConnectorConfig>) {
    this.config = buildAwsConfig(config);
    this.validCredentials = !!(this.config.accessKey && this.config.secretKey);
  }

  async health(): Promise<ConnectorHealth> {
    return {
      provider: "aws",
      status: this.lastSync ? "connected" : "disconnected",
      lastSyncAt: this.lastSync?.toISOString(),
      findingCount: this.findings.length,
      errorCount: 0,
    };
  }

  async fetchFindings(): Promise<CloudFinding[]> {
    if (!this.validCredentials) {
      console.log("[AWS GuardDuty] No credentials configured, returning mock findings");
      this.findings = mockGuardDutyFindings(this.config.region);
      this.lastSync = new Date();
      return this.findings;
    }

    try {
      // Step 1: List detectors
      const detectorResp = await awsJsonRpc(
        this.config,
        "guardduty",
        "GuardDuty.ListDetectors",
        { MaxResults: 10 },
      );

      const detectors = (detectorResp as { DetectorIds?: string[] }).DetectorIds ?? [];
      const allFindings: CloudFinding[] = [];

      for (const detectorId of detectors) {
        // Step 2: List findings per detector
        const findingResp = await awsJsonRpc(
          this.config,
          "guardduty",
          "GuardDuty.ListFindings",
          {
            DetectorId: detectorId,
            FindingCriteria: {
              Criterion: {
                "severity": { Gte: 1 },
              },
            },
            SortCriteria: {
              AttributeName: "severity",
              OrderBy: "desc",
            },
            MaxResults: 50,
          },
        );

        const findingIds = (findingResp as { FindingIds?: string[] }).FindingIds ?? [];

        // Step 3: Get finding details
        if (findingIds.length > 0) {
          const detailResp = await awsJsonRpc(
            this.config,
            "guardduty",
            "GuardDuty.GetFindings",
            {
              DetectorId: detectorId,
              FindingIds: findingIds,
            },
          );

          const rawFindings = (detailResp as { Findings?: Array<Record<string, unknown>> }).Findings ?? [];
          for (const f of rawFindings) {
            allFindings.push(this.parseFinding(f));
          }
        }
      }

      console.log(`[AWS GuardDuty] Fetched ${allFindings.length} real findings`);
      this.findings = allFindings;
    } catch (err) {
      console.error("[AWS GuardDuty] API call failed, falling back to mock:", err);
      this.findings = mockGuardDutyFindings(this.config.region);
    }

    this.lastSync = new Date();
    return this.findings;
  }

  private parseFinding(raw: Record<string, unknown>): CloudFinding {
    const resource = (raw.Resource ?? {}) as Record<string, unknown>;
    const instanceDetails = (resource.InstanceDetails ?? {}) as Record<string, unknown>;
    const service = (raw.Service ?? {}) as Record<string, unknown>;
    const action = (service.Action ?? {}) as Record<string, unknown>;
    const network = (action.NetworkConnectionAction ?? {}) as Record<string, unknown>;
    const remoteIpDetails = (network.RemoteIpDetails ?? {}) as Record<string, unknown>;

    const sev = Number(raw.Severity ?? 1);
    let severity: CloudFinding["severity"] = "informational";
    if (sev >= 8) severity = "critical";
    else if (sev >= 6) severity = "high";
    else if (sev >= 4) severity = "medium";
    else if (sev >= 1) severity = "low";

    return {
      id: String(raw.Id ?? `gd-${Date.now()}`),
      provider: "aws",
      service: "guardduty",
      severity,
      title: String(raw.Title ?? "GuardDuty finding"),
      description: String(raw.Description ?? ""),
      resourceId: String(resource.Arn ?? raw.Id ?? ""),
      resourceType: String(raw.Type ?? "AWS::GuardDuty::Finding"),
      region: String(raw.Region ?? this.config.region),
      complianceControl: "A.5.1",
      detectedAt: new Date().toISOString(),
      metadata: {
        detectorId: String(raw.GeneratorId ?? ""),
        severity: sev,
        type: String(raw.Type ?? ""),
        accountId: String(raw.AwsAccountId ?? ""),
        remoteIp: String(remoteIpDetails.IpAddressV4 ?? ""),
        instanceId: String(instanceDetails.InstanceId ?? ""),
        instanceType: String(instanceDetails.InstanceType ?? ""),
      },
    };
  }

  async testConnection(): Promise<boolean> {
    if (!this.validCredentials) {
      console.log("[AWS GuardDuty] No credentials configured, skipping STS check");
      return false;
    }
    try {
      await stsGetCallerIdentity(this.config);
      return true;
    } catch {
      return false;
    }
  }
}
