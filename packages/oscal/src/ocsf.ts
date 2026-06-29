/**
 * @grc-claw/oscal — OCSF 1.1 transformation helpers
 *
 * Transforms A2Z SOC internal event rows into OCSF 1.1 schema objects.
 * https://schema.ocsf.io/1.1.0/
 */

export interface SiemEventRow {
  id: string;
  event_type: string;
  severity?: number;
  details?: unknown;
  created_at: string;
  source?: string;
}

export interface KevEventRow {
  cve_id: string;
  short_description?: string;
  cvss_v3_score?: number;
  epss_score?: number;
  date_added?: string;
}

export interface OcsfDetectionFinding {
  class_uid: 1001;
  class_name: 'Detection Finding';
  category_uid: 2;
  category_name: 'Findings';
  activity_id: number;
  activity_name: string;
  time: number;
  severity_id: number;
  severity: string;
  status_id: number;
  status: string;
  message: string;
  metadata: {
    version: string;
    product: { name: string; vendor_name: string; version: string };
    uid: string;
  };
  finding: { uid: string; title: string; types: string[] };
}

export interface OcsfVulnerabilityFinding {
  class_uid: 2002;
  class_name: 'Vulnerability Finding';
  category_uid: 2;
  category_name: 'Findings';
  activity_id: 1;
  activity_name: 'Create';
  time: number;
  severity_id: number;
  severity: string;
  status_id: 1;
  status: 'New';
  message: string;
  metadata: {
    version: string;
    product: { name: string; vendor_name: string; version: string };
    uid: string;
  };
  vulnerabilities: Array<{
    cve: { uid: string; desc?: string; cvss?: { base_score?: number } };
    epss?: { score?: number };
    kb_articles: string[];
  }>;
}

const SEVERITY_MAP: Record<number, string> = {
  0: 'Unknown',
  1: 'Informational',
  2: 'Low',
  3: 'Medium',
  4: 'High',
  5: 'Critical',
};

function severityFromCvss(score?: number): { id: number; name: string } {
  if (!score) return { id: 0, name: 'Unknown' };
  if (score >= 9) return { id: 5, name: 'Critical' };
  if (score >= 7) return { id: 4, name: 'High' };
  if (score >= 4) return { id: 3, name: 'Medium' };
  return { id: 2, name: 'Low' };
}

/**
 * Transform a siem_events row into an OCSF 1.1 Detection Finding (class_uid=1001).
 */
export function siemEventToOcsf(event: SiemEventRow): OcsfDetectionFinding {
  const sevId = Math.min(5, Math.max(0, event.severity ?? 3));
  return {
    class_uid: 1001,
    class_name: 'Detection Finding',
    category_uid: 2,
    category_name: 'Findings',
    activity_id: 1,
    activity_name: 'Create',
    time: new Date(event.created_at).getTime(),
    severity_id: sevId,
    severity: SEVERITY_MAP[sevId] ?? 'Medium',
    status_id: 1,
    status: 'New',
    message: event.event_type,
    metadata: {
      version: '1.1.0',
      product: { name: 'A2Z SOC', vendor_name: 'A2Z SOC', version: '10.0' },
      uid: event.id,
    },
    finding: {
      uid: event.id,
      title: event.event_type,
      types: [event.source ?? 'a2zsoc'],
    },
  };
}

/**
 * Transform a kev_events row into an OCSF 1.1 Vulnerability Finding (class_uid=2002).
 */
export function kevToOcsfVulnerability(kev: KevEventRow): OcsfVulnerabilityFinding {
  const { id: severity_id, name: severity } = severityFromCvss(kev.cvss_v3_score);
  return {
    class_uid: 2002,
    class_name: 'Vulnerability Finding',
    category_uid: 2,
    category_name: 'Findings',
    activity_id: 1,
    activity_name: 'Create',
    time: kev.date_added ? new Date(kev.date_added).getTime() : Date.now(),
    severity_id,
    severity,
    status_id: 1,
    status: 'New',
    message: kev.short_description ?? kev.cve_id,
    metadata: {
      version: '1.1.0',
      product: { name: 'A2Z SOC', vendor_name: 'A2Z SOC', version: '10.0' },
      uid: kev.cve_id,
    },
    vulnerabilities: [
      {
        cve: {
          uid: kev.cve_id,
          desc: kev.short_description,
          cvss: { base_score: kev.cvss_v3_score },
        },
        epss: { score: kev.epss_score },
        kb_articles: ['cisa-kev'],
      },
    ],
  };
}
