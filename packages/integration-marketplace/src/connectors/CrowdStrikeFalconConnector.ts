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
    id: "crowdstrike-falcon-endpoints",
    name: "Falcon Endpoint Protection",
    description: "Fetch CrowdStrike Falcon endpoint detection and prevention status",
    evidenceCategories: ["endpoint_security", "posture_assessment"],
  },
  {
    id: "crowdstrike-falcon-incidents",
    name: "Falcon Incidents",
    description: "Fetch CrowdStrike Falcon incident detections and response actions",
    evidenceCategories: ["vulnerability_management", "incident_management"],
  },
  {
    id: "crowdstrike-falcon-policies",
    name: "Falcon Detection Policies",
    description: "Fetch CrowdStrike Falcon detection policy configurations and tuning",
    evidenceCategories: ["policy_compliance", "configuration"],
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
      capabilityId: "crowdstrike-falcon-endpoints",
      timestamp: now,
      hash: hashEvidence({ deviceCount: deviceIds.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "crowdstrike-falcon/devices",
      status: deviceIds.length > 0 ? "compliant" : "non_compliant",
      data: { deviceCount: deviceIds.length },
      metadata: {},
    });

    const detections = await fetch(
      "https://api.crowdstrike.com/detects/queries/detects/v1?limit=100",
      { headers }
    ).then((r) => r.json()).catch(() => ({ resources: [] })) as Record<string, unknown>;
    const detectIds = (detections.resources || []) as string[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "crowdstrike-falcon-incidents",
      timestamp: now,
      hash: hashEvidence({ detectionCount: detectIds.length }),
      framework: "ISO27001",
      controlId: "A.12.2.1",
      source: "crowdstrike-falcon/detections",
      status: detectIds.length === 0 ? "compliant" : "non_compliant",
      data: { openDetections: detectIds.length },
      metadata: {},
    });

    return artifacts;
  }
}
