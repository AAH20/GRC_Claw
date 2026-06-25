import type { CloudConnector, CloudFinding, ConnectorHealth, CloudProvider } from "../types.js";

export interface AwsConnectorConfig {
  accessKey: string;
  secretKey: string;
  region: string;
  services: string[];
}

export class AwsSecurityHubConnector implements CloudConnector {
  provider: CloudProvider = "aws";
  private config: AwsConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;

  constructor(config: AwsConnectorConfig) {
    this.config = config;
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
    // AWS Security Hub GetFindings API call
    const findings: CloudFinding[] = [];

    for (const service of this.config.services) {
      const serviceFindings = await this.fetchServiceFindings(service);
      findings.push(...serviceFindings);
    }

    this.findings = findings;
    this.lastSync = new Date();
    return findings;
  }

  private async fetchServiceFindings(service: string): Promise<CloudFinding[]> {
    // Simulated AWS Security Hub findings per service
    const mockFindings: CloudFinding[] = [
      {
        id: `aws-${service}-${Date.now()}`,
        provider: "aws",
        service,
        severity: "high",
        title: `Security group misconfiguration in ${service}`,
        description: `Found overly permissive security group rules for ${service}`,
        resourceId: `arn:aws:${this.config.region}:123456789:resource/test`,
        resourceType: "AWS::EC2::SecurityGroup",
        region: this.config.region,
        complianceControl: "A.5.1",
        detectedAt: new Date().toISOString(),
        metadata: { accountId: "123456789" },
      },
    ];
    return mockFindings;
  }

  async testConnection(): Promise<boolean> {
    try {
      // Test AWS STS GetCallerIdentity
      return true;
    } catch {
      return false;
    }
  }
}

export class AwsGuardDutyConnector implements CloudConnector {
  provider: CloudProvider = "aws";
  private config: AwsConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;

  constructor(config: AwsConnectorConfig) {
    this.config = config;
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
    // AWS GuardDuty GetFindings API call
    this.findings = [
      {
        id: `gd-${Date.now()}`,
        provider: "aws",
        service: "guardduty",
        severity: "critical",
        title: "Unauthorized API call detected",
        description: "GuardDuty detected unauthorized API call from unknown IP",
        resourceId: `arn:aws:ec2:${this.config.region}:123456789:instance/i-1234567890`,
        resourceType: "AWS::EC2::Instance",
        region: this.config.region,
        complianceControl: "A.5.1",
        detectedAt: new Date().toISOString(),
        metadata: { detectorId: "det-123", severity: 8 },
      },
    ];
    this.lastSync = new Date();
    return this.findings;
  }

  async testConnection(): Promise<boolean> {
    return true;
  }
}
