import { randomUUID } from "node:crypto";
import type { CloudProvider, EvidenceCollector, CollectedEvidence, CloudIntegration, EvidenceInventory, CollectorTemplate } from "../types.js";

const COLLECTOR_TEMPLATES: CollectorTemplate[] = [
  { provider: "aws", resourceType: "iam", controlId: "A.9.2.1", name: "IAM Password Policy", description: "Collect IAM password policy settings", apiCall: "iam:GetAccountPasswordPolicy" },
  { provider: "aws", resourceType: "s3", controlId: "A.13.2.1", name: "S3 Bucket Encryption", description: "Check S3 bucket encryption settings", apiCall: "s3:GetBucketEncryption" },
  { provider: "aws", resourceType: "ec2", controlId: "A.13.1.1", name: "Security Groups", description: "Collect security group rules", apiCall: "ec2:DescribeSecurityGroups" },
  { provider: "aws", resourceType: "cloudtrail", controlId: "A.12.4.1", name: "CloudTrail Logging", description: "Verify CloudTrail is enabled", apiCall: "cloudtrail:GetTrailStatus" },
  { provider: "aws", resourceType: "kms", controlId: "A.10.1.1", name: "KMS Key Rotation", description: "Check KMS key rotation status", apiCall: "kms:GetKeyRotationStatus" },
  { provider: "aws", resourceType: "rds", controlId: "A.14.1.2", name: "RDS Encryption", description: "Check RDS encryption at rest", apiCall: "rds:DescribeDBInstances" },
  { provider: "azure", resourceType: "storage", controlId: "A.13.2.1", name: "Storage Encryption", description: "Check Azure Storage encryption", apiCall: "Microsoft.Storage/storageAccounts/listKeys" },
  { provider: "azure", resourceType: "network", controlId: "A.13.1.1", name: "NSG Rules", description: "Collect Network Security Group rules", apiCall: "Microsoft.Network/networkSecurityGroups/list" },
  { provider: "azure", resourceType: "ad", controlId: "A.9.4.2", name: "Conditional Access", description: "Collect conditional access policies", apiCall: "Microsoft.Graph/policies/conditionalAccessPolicies" },
  { provider: "gcp", resourceType: "iam", controlId: "A.9.2.1", name: "IAM Bindings", description: "Collect IAM policy bindings", apiCall: "cloudresourcemanager.projects.getIamPolicy" },
  { provider: "gcp", resourceType: "storage", controlId: "A.13.2.1", name: "Bucket IAM", description: "Check bucket IAM configuration", apiCall: "storage.buckets.getIamPolicy" },
  { provider: "gcp", resourceType: "compute", controlId: "A.13.1.1", name: "Firewall Rules", description: "Collect firewall rules", apiCall: "compute.firewalls.list" },
  { provider: "github", resourceType: "repo", controlId: "A.14.2.1", name: "Branch Protection", description: "Check branch protection rules", apiCall: "repos/getBranchProtection" },
  { provider: "github", resourceType: "actions", controlId: "A.14.2.1", name: "CI/CD Workflows", description: "Collect GitHub Actions workflows", apiCall: "actions/listWorkflowRuns" },
  { provider: "okta", resourceType: "factor", controlId: "A.9.4.2", name: "MFA Enrollment", description: "Check MFA enrollment status", apiCall: "/api/v1/users" },
  { provider: "cloudflare", resourceType: "zone", controlId: "A.13.1.1", name: "WAF Rules", description: "Collect WAF rule configuration", apiCall: "/zones/{zone_id}/firewall/rules" },
];

export class AutoEvidenceCollector {
  private collectors: Map<string, EvidenceCollector> = new Map();
  private integrations: Map<CloudProvider, CloudIntegration> = new Map();

  getTemplates(provider?: CloudProvider): CollectorTemplate[] {
    if (provider) return COLLECTOR_TEMPLATES.filter((t) => t.provider === provider);
    return [...COLLECTOR_TEMPLATES];
  }

  connectProvider(provider: CloudProvider, accountId: string, regions: string[]): CloudIntegration {
    const integration: CloudIntegration = {
      provider,
      connected: true,
      accountId,
      regions,
      collectors: [],
    };
    this.integrations.set(provider, integration);
    return integration;
  }

  createCollector(provider: CloudProvider, resourceType: string, controlId: string, schedule: string): EvidenceCollector {
    const collector: EvidenceCollector = {
      id: randomUUID(),
      provider,
      resourceType,
      controlId,
      status: "idle",
      schedule,
      evidence: [],
    };
    this.collectors.set(collector.id, collector);
    const integration = this.integrations.get(provider);
    if (integration) integration.collectors.push(collector);
    return collector;
  }

  collectEvidence(collectorId: string): CollectedEvidence | null {
    const collector = this.collectors.get(collectorId);
    if (!collector) return null;

    collector.status = "collecting";
    const template = COLLECTOR_TEMPLATES.find((t) => t.provider === collector.provider && t.resourceType === collector.resourceType);

    const evidence: CollectedEvidence = {
      id: randomUUID(),
      collectorId,
      type: "configuration",
      name: template?.name || `${collector.provider}-${collector.resourceType}`,
      content: JSON.stringify({ provider: collector.provider, resource: collector.resourceType, controlId: collector.controlId, apiCall: template?.apiCall, collectedAt: new Date().toISOString() }),
      sha256: `sha256-${Date.now()}`,
      collectedAt: new Date().toISOString(),
      metadata: { provider: collector.provider, region: "us-east-1" },
    };

    collector.evidence.push(evidence);
    collector.status = "completed";
    collector.lastCollectedAt = new Date().toISOString();
    return evidence;
  }

  getInventory(): EvidenceInventory {
    const allEvidence = Array.from(this.collectors.values()).flatMap((c) => c.evidence);
    const byProvider: Record<string, number> = {};
    const byType: Record<string, number> = {};
    for (const e of allEvidence) {
      const collector = this.collectors.get(e.collectorId);
      if (collector) byProvider[collector.provider] = (byProvider[collector.provider] || 0) + 1;
      byType[e.type] = (byType[e.type] || 0) + 1;
    }
    return {
      totalEvidence: allEvidence.length,
      byProvider: byProvider as Record<CloudProvider, number>,
      byType: byType as Record<string, number>,
      staleEvidence: allEvidence.filter((e) => new Date(e.collectedAt) < new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)).length,
      coverage: this.collectors.size > 0 ? Math.round((allEvidence.length / this.collectors.size) * 100) : 0,
    };
  }

  autoDeployCollectors(provider: CloudProvider): EvidenceCollector[] {
    const templates = this.getTemplates(provider);
    return templates.map((t) => this.createCollector(provider, t.resourceType, t.controlId, "daily"));
  }
}
