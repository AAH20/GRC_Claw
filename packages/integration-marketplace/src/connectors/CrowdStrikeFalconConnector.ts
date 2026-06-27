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
    id: "csf-endpoint-posture",
    name: "Endpoint Security Posture",
    description: "Fetch CrowdStrike Falcon endpoint security posture scores and compliance status",
    evidenceCategories: ["endpoint_security", "posture_assessment"],
  },
  {
    id: "csf-policy-evaluations",
    name: "Policy Evaluations",
    description: "Fetch device policy evaluation results and remediation status",
    evidenceCategories: ["policy_compliance", "device_management"],
  },
  {
    id: "csf-vulnerability-assessments",
    name: "Vulnerability Assessments",
    description: "Fetch endpoint vulnerability scan results and severity distribution",
    evidenceCategories: ["vulnerability_management", "risk_assessment"],
  },
  {
    id: "csf-prevention-settings",
    name: "Prevention Settings",
    description: "Fetch Falcon prevention policy configurations across sensor groups",
    evidenceCategories: ["configuration", "endpoint_protection"],
  },
];

export class CrowdStrikeFalconConnector implements IntegrationConnector {
  readonly id = "crowdstrike-falcon";
  readonly name = "CrowdStrike Falcon";
  readonly category = "endpoint" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF", "HIPAA", "PCI_DSS"];

  private async getAccessToken(config: ConnectorConfig): Promise<string> {
    const resp = await fetch("https://api.crowdstrike.com/oauth2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: config.clientId || "",
        client_secret: config.clientSecret || "",
      }),
    });
    if (!resp.ok) throw new Error(`CrowdStrike Falcon token ${resp.status}`);
    const data = (await resp.json()) as Record<string, unknown>;
    return data.access_token as string;
  }

  async testConnection(config: ConnectorConfig): Promise<boolean> {
    try {
      const token = await this.getAccessToken(config);
      const resp = await fetch("https://api.crowdstrike.com/devices/queries/devices/v1?limit=1", {
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

    const devices = await fetch(
      "https://api.crowdstrike.com/devices/queries/devices/v1?limit=100",
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    const deviceIds = (devices.resources || []) as string[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "csf-endpoint-posture",
      timestamp: now,
      hash: hashEvidence({ deviceCount: deviceIds.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "crowdstrike-falcon/devices",
      status: deviceIds.length > 0 ? "compliant" : "non_compliant",
      data: { deviceCount: deviceIds.length },
      metadata: {},
    });

    const policies = await fetch(
      "https://api.crowdstrike.com/device-policy/v1/queries/policy-ids",
      { headers }
    ).then((r) => r.json()).catch(() => ({ resources: [] })) as Record<string, unknown>;
    const policyIds = (policies.resources || []) as string[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "csf-policy-evaluations",
      timestamp: now,
      hash: hashEvidence({ policyCount: policyIds.length }),
      framework: "ISO27001",
      controlId: "A.12.6.1",
      source: "crowdstrike-falcon/device-policy",
      status: "unknown",
      data: { policyCount: policyIds.length },
      metadata: {},
    });

    const vulnerabilities = await fetch(
      "https://api.crowdstrike.com/spotlight/queries/vulnerabilities/v1?limit=100",
      { headers }
    ).then((r) => r.json()).catch(() => ({ resources: [] })) as Record<string, unknown>;
    const vulnIds = (vulnerabilities.resources || []) as string[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "csf-vulnerability-assessments",
      timestamp: now,
      hash: hashEvidence({ vulnCount: vulnIds.length }),
      framework: "NIST_CSF",
      controlId: "DE.CM-1",
      source: "crowdstrike-falcon/spotlight",
      status: vulnIds.length === 0 ? "compliant" : "non_compliant",
      data: { vulnerabilityCount: vulnIds.length },
      metadata: {},
    });

    const preventionPolicies = await fetch(
      "https://api.crowdstrike.com/device-policy/v1/queries/prevention-policies/v1",
      { headers }
    ).then((r) => r.json()).catch(() => ({ resources: [] })) as Record<string, unknown>;
    const preventionIds = (preventionPolicies.resources || []) as string[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "csf-prevention-settings",
      timestamp: now,
      hash: hashEvidence({ preventionCount: preventionIds.length }),
      framework: "SOC2",
      controlId: "CC6.1",
      source: "crowdstrike-falcon/prevention-policies",
      status: "unknown",
      data: { preventionPolicyCount: preventionIds.length },
      metadata: {},
    });

    return artifacts;
  }
}
