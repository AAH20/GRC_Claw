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
    id: "cs-device-posture",
    name: "Device Posture",
    description: "Fetch CrowdStrike device posture assessments and compliance",
    evidenceCategories: ["endpoint_security", "device_management"],
  },
  {
    id: "cs-threat-detections",
    name: "Threat Detections",
    description: "Fetch CrowdStrike Falcon threat detections",
    evidenceCategories: ["threat_detection", "incident_management"],
  },
];

export class CrowdStrikeConnector implements IntegrationConnector {
  readonly id = "crowdstrike";
  readonly name = "CrowdStrike Falcon";
  readonly category = "endpoint" as const;
  readonly authType = "oauth2" as const;
  readonly capabilities = capabilities;
  readonly frameworks: ComplianceFramework[] = ["SOC2", "ISO27001", "NIST_CSF"];

  private async getAccessToken(config: ConnectorConfig): Promise<string> {
    const resp = await fetch("https://api.crowdstrike.com/oauth2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: config.clientId || "",
        client_secret: config.clientSecret || "",
      }),
    });
    if (!resp.ok) throw new Error(`CrowdStrike token ${resp.status}`);
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
      capabilityId: "cs-device-posture",
      timestamp: now,
      hash: hashEvidence({ deviceCount: deviceIds.length }),
      framework: "SOC2",
      controlId: "CC6.8",
      source: "crowdstrike/devices",
      status: deviceIds.length > 0 ? "compliant" : "non_compliant",
      data: { deviceCount: deviceIds.length },
      metadata: {},
    });

    const detections = await fetch(
      "https://api.crowdstrike.com/detects/queries/detects/v1?limit=100&sort=created_timestamp|desc",
      { headers }
    ).then((r) => r.json()) as Record<string, unknown>;
    const detectionIds = (detections.resources || []) as string[];
    artifacts.push({
      id: generateEvidenceId(),
      connectorId: this.id,
      capabilityId: "cs-threat-detections",
      timestamp: now,
      hash: hashEvidence({ detectionCount: detectionIds.length }),
      framework: "SOC2",
      controlId: "CC7.2",
      source: "crowdstrike/detects",
      status: "unknown",
      data: { detectionCount: detectionIds.length },
      metadata: {},
    });

    return artifacts;
  }
}
