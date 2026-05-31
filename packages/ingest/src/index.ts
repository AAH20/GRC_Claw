export * from './severity.js';
export * from './cloud-severity.js';
export * from './uuid.js';
export { normalizeWazuh, type WazuhAlert } from './normalizers/wazuh.js';
export { normalizeSuricata, type SuricataEveAlert } from './normalizers/suricata.js';
export { normalizeSnort, type SnortAlertJson } from './normalizers/snort.js';
export { normalizeElastic, type ElasticAlertDoc } from './normalizers/elastic.js';
export { normalizeUfwLine } from './normalizers/ufw.js';
export {
  normalizeCloud,
  normalizeAwsGuardDuty,
  normalizeAzureSentinel,
  normalizeGcpChronicle,
  CLOUD_INGEST_SOURCES,
  type CloudIngestSource,
} from './normalizers/cloud.js';

import type { SecurityEventCanonical } from '@grc-claw/core';
import {
  CLOUD_INGEST_SOURCES,
  normalizeCloud,
  type CloudIngestSource,
} from './normalizers/cloud.js';
import { normalizeElastic } from './normalizers/elastic.js';
import { normalizeSnort } from './normalizers/snort.js';
import { normalizeSuricata } from './normalizers/suricata.js';
import { normalizeUfwLine } from './normalizers/ufw.js';
import { normalizeWazuh } from './normalizers/wazuh.js';

export type OssIngestSource = 'wazuh' | 'suricata' | 'snort' | 'elastic' | 'ufw';
export type IngestSource = OssIngestSource | CloudIngestSource;

export function isCloudSource(source: string): source is CloudIngestSource {
  return (CLOUD_INGEST_SOURCES as readonly string[]).includes(source);
}

export function normalizeBySource(
  source: IngestSource,
  payload: unknown,
  tenantId: number
): SecurityEventCanonical | null {
  if (isCloudSource(source)) {
    return normalizeCloud(source, payload, tenantId);
  }
  switch (source) {
    case 'wazuh':
      return normalizeWazuh(payload as Parameters<typeof normalizeWazuh>[0], tenantId);
    case 'suricata':
      return normalizeSuricata(payload as Parameters<typeof normalizeSuricata>[0], tenantId);
    case 'snort':
      return normalizeSnort(payload as Parameters<typeof normalizeSnort>[0], tenantId);
    case 'elastic':
      return normalizeElastic(payload as Parameters<typeof normalizeElastic>[0], tenantId);
    case 'ufw':
      return typeof payload === 'string' ? normalizeUfwLine(payload, tenantId) : null;
    default:
      return null;
  }
}
