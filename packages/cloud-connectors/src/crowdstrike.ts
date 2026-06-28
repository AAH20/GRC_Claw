// CrowdStrike Falcon connector — pulls detections and vulnerabilities
// Maps to SIEM events and compliance controls

export interface CrowdStrikeConfig {
  clientId: string;
  clientSecret: string;
  baseUrl?: string; // default: https://api.crowdstrike.com
}

interface CsToken { access_token: string; expires_in: number; }

async function getCsToken(config: CrowdStrikeConfig): Promise<string> {
  const base = config.baseUrl || 'https://api.crowdstrike.com';
  const res = await fetch(`${base}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `client_id=${config.clientId}&client_secret=${config.clientSecret}&grant_type=client_credentials`
  });
  if (!res.ok) throw new Error(`CrowdStrike auth error: ${res.status}`);
  const token: CsToken = await res.json();
  return token.access_token;
}

export interface CsDetection {
  id: string;
  status: string;
  severity: number; // 1-4 (critical=4)
  tactic: string;
  technique: string;
  hostname: string;
  created_timestamp: string;
  cve_id?: string;
  mappedControls: string[];
}

const TACTIC_CONTROL_MAP: Record<string, string[]> = {
  'Credential Access': ['SOC2:CC6.1', 'ISO27001:A.9.4'],
  'Privilege Escalation': ['SOC2:CC6.2', 'ISO27001:A.9.2'],
  'Lateral Movement': ['SOC2:CC6.6', 'ISO27001:A.8.20'],
  'Exfiltration': ['SOC2:CC9.2', 'ISO27001:A.8.12'],
  'Persistence': ['SOC2:CC6.8', 'ISO27001:A.8.18'],
  'Defense Evasion': ['SOC2:CC7.2', 'ISO27001:A.8.16'],
};

export async function fetchCrowdStrikeDetections(config: CrowdStrikeConfig): Promise<CsDetection[]> {
  const base = config.baseUrl || 'https://api.crowdstrike.com';
  const token = await getCsToken(config);

  // Get detection IDs from last 7 days
  const filter = `created_timestamp:>='${new Date(Date.now() - 7 * 86400000).toISOString()}'`;
  const idsRes = await fetch(`${base}/detects/queries/detects/v1?filter=${encodeURIComponent(filter)}&limit=100`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!idsRes.ok) return [];
  const { resources: ids } = await idsRes.json();
  if (!ids?.length) return [];

  // Get full detection details
  const detRes = await fetch(`${base}/detects/entities/summaries/GET/v1`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids: ids.slice(0, 100) })
  });
  if (!detRes.ok) return [];
  const { resources: detections } = await detRes.json();

  return (detections || []).map((d: any) => ({
    id: d.detection_id,
    status: d.status,
    severity: d.max_severity_displayname === 'Critical' ? 4 : d.max_severity_displayname === 'High' ? 3 : 2,
    tactic: d.behaviors?.[0]?.tactic || 'Unknown',
    technique: d.behaviors?.[0]?.technique || 'Unknown',
    hostname: d.device?.hostname || 'Unknown',
    created_timestamp: d.created_timestamp,
    mappedControls: TACTIC_CONTROL_MAP[d.behaviors?.[0]?.tactic] || ['SOC2:CC7.1']
  }));
}
