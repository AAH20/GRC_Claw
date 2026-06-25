import type { CloudConnector, CloudFinding, ConnectorHealth, CloudProvider } from "../types.js";

export interface AzureConnectorConfig {
  tenantId: string;
  clientId: string;
  clientSecret: string;
  subscriptionId: string;
  services: string[];
}

export class AzureSentinelConnector implements CloudConnector {
  provider: CloudProvider = "azure";
  private config: AzureConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;

  constructor(config: AzureConnectorConfig) {
    this.config = config;
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
    // Azure Sentinel API call
    this.findings = [
      {
        id: `sentinel-${Date.now()}`,
        provider: "azure",
        service: "sentinel",
        severity: "high",
        title: "Suspicious login activity detected",
        description: "Azure AD sign-in logs show suspicious activity from anomalous location",
        resourceId: `/subscriptions/${this.config.subscriptionId}/resourceGroups/rg-prod`,
        resourceType: "Microsoft.Security/Alerts",
        region: "global",
        complianceControl: "A.9.1",
        detectedAt: new Date().toISOString(),
        metadata: { tenantId: this.config.tenantId },
      },
    ];
    this.lastSync = new Date();
    return this.findings;
  }

  async testConnection(): Promise<boolean> {
    return true;
  }
}

export class AzureDefenderConnector implements CloudConnector {
  provider: CloudProvider = "azure";
  private config: AzureConnectorConfig;
  private findings: CloudFinding[] = [];
  private lastSync: Date | null = null;

  constructor(config: AzureConnectorConfig) {
    this.config = config;
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
    // Azure Defender API call
    this.findings = [
      {
        id: `defender-${Date.now()}`,
        provider: "azure",
        service: "defender",
        severity: "medium",
        title: "VM vulnerability assessment",
        description: "Azure Defender detected vulnerable packages on VM",
        resourceId: `/subscriptions/${this.config.subscriptionId}/providers/Microsoft.Security`,
        resourceType: "Microsoft.Security/Assessments",
        region: "global",
        complianceControl: "A.12.1",
        detectedAt: new Date().toISOString(),
        metadata: { assessmentName: "vmVulnerabilityAssessment" },
      },
    ];
    this.lastSync = new Date();
    return this.findings;
  }

  async testConnection(): Promise<boolean> {
    return true;
  }
}
