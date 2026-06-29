/**
 * @grc-claw/oscal — STIX 2.1 bundle export helpers
 *
 * Transforms KEV data into a STIX 2.1 Bundle for threat intel platforms.
 * https://docs.oasis-open.org/cti/stix/v2.1/
 */

export interface KevEventRow {
  cve_id: string;
  short_description?: string;
  cvss_v3_score?: number;
  epss_score?: number;
  date_added?: string;
}

export interface StixVulnerability {
  type: 'vulnerability';
  id: string;
  spec_version: '2.1';
  created: string;
  modified: string;
  name: string;
  description?: string;
  external_references: Array<{
    source_name: string;
    external_id: string;
    url?: string;
  }>;
  labels: string[];
  x_epss_score?: number;
  x_cvss_base_score?: number;
}

export interface StixBundle {
  type: 'bundle';
  id: string;
  spec_version: '2.1';
  objects: StixVulnerability[];
}

/**
 * Transforms an array of kev_events rows into a STIX 2.1 Bundle.
 */
export function kevToStixBundle(kevEvents: KevEventRow[]): StixBundle {
  const now = new Date().toISOString();
  const objects: StixVulnerability[] = kevEvents.map((kev) => {
    const stixId = `vulnerability--${kev.cve_id
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, '-')}`;

    return {
      type: 'vulnerability',
      id: stixId,
      spec_version: '2.1',
      created: kev.date_added ?? now,
      modified: now,
      name: kev.cve_id,
      description: kev.short_description,
      external_references: [
        {
          source_name: 'cve',
          external_id: kev.cve_id,
          url: `https://nvd.nist.gov/vuln/detail/${kev.cve_id}`,
        },
        {
          source_name: 'cisa-kev',
          external_id: kev.cve_id,
        },
      ],
      labels: ['cisa-kev'],
      x_epss_score: kev.epss_score,
      x_cvss_base_score: kev.cvss_v3_score,
    };
  });

  return {
    type: 'bundle',
    id: `bundle--a2zsoc-${Date.now()}`,
    spec_version: '2.1',
    objects,
  };
}
