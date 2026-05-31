import type { SecurityEventCanonical } from '@grc-claw/core';
import { guardDutyScore, labelToSeverity } from '../cloud-severity.js';
import { stableEventUuid } from '../uuid.js';

function base(
  sourceSystem: SecurityEventCanonical['sourceSystem'],
  eventType: string,
  severity: SecurityEventCanonical['severity'],
  tenantId: number,
  message: string,
  uuidParts: (string | number | undefined)[],
  extra: Record<string, unknown> = {}
): SecurityEventCanonical {
  const ts = String(extra['@timestamp'] ?? new Date().toISOString());
  return {
    eventUuid: stableEventUuid([sourceSystem, ...uuidParts]),
    eventType,
    severity,
    sourceSystem,
    tenantId,
    eventData: {
      '@timestamp': ts,
      message,
      rule: { category: 'cloud' },
      raw: extra.raw as Record<string, unknown> | undefined,
      ...extra,
    },
  };
}

export function normalizeAwsGuardDuty(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const detail = (raw.detail as Record<string, unknown>) ?? raw;
  const score = Number(detail.severity ?? 5);
  const id = String(detail.id ?? detail.findingId ?? 'gd-unknown');
  const type = String(detail.type ?? 'GuardDutyFinding');
  return base('aws_guardduty', 'identity.compromise', guardDutyScore(score), tenantId, type, [
    id,
    type,
    score,
  ], { raw, '@timestamp': detail.updatedAt as string });
}

export function normalizeAwsCloudWatch(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const alarm = (raw.alarmName as string) ?? (raw.AlarmName as string) ?? 'CloudWatch alarm';
  const state = String(raw.newStateValue ?? raw.state ?? 'ALARM');
  const sev = state === 'ALARM' ? 'high' : 'low';
  return base('aws_cloudwatch', 'host.anomaly', sev, tenantId, alarm, [alarm, state], { raw });
}

export function normalizeAwsSecurityHub(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const finding = (raw.Finding as Record<string, unknown>) ?? raw;
  const sev = labelToSeverity(
    String((finding.Severity as Record<string, unknown>)?.Label ?? finding.Severity ?? 'LOW')
  );
  const id = String(finding.Id ?? finding.id ?? 'sh-unknown');
  const title = String(finding.Title ?? finding.description ?? 'Security Hub finding');
  return base('aws_securityhub', 'cloud.misconfig', sev, tenantId, title, [id], { raw: finding });
}

export function normalizeAwsCloudTrail(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const eventName = String(raw.eventName ?? raw.EventName ?? 'CloudTrailEvent');
  const user = String((raw.userIdentity as Record<string, unknown>)?.arn ?? raw.userName ?? '');
  const sev =
    /Delete|PutBucketPolicy|AttachUserPolicy|CreateAccessKey/i.test(eventName) ? 'high' : 'medium';
  return base('aws_cloudtrail', 'cloud.api', sev, tenantId, eventName, [eventName, user], { raw });
}

export function normalizeAzureSentinel(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const props = (raw.properties as Record<string, unknown>) ?? raw;
  const sev = labelToSeverity(String(props.severity ?? props.Severity ?? 'Low'));
  const title = String(props.title ?? props.displayName ?? 'Sentinel incident');
  const id = String(raw.id ?? props.incidentNumber ?? 'sentinel-unknown');
  const eventType = /sign-?in|auth/i.test(title) ? 'auth.failure' : 'network.intrusion';
  return base('azure_sentinel', eventType, sev, tenantId, title, [id], { raw: props });
}

export function normalizeAzureDefender(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const props = (raw.properties as Record<string, unknown>) ?? raw;
  const sev = labelToSeverity(String(props.severity ?? 'Medium'));
  const title = String(props.alertDisplayName ?? props.title ?? 'Defender alert');
  return base('azure_defender', 'cloud.misconfig', sev, tenantId, title, [title], { raw: props });
}

export function normalizeAzureMonitor(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const data = (raw.data as Record<string, unknown>) ?? raw;
  const essentials = (data.essentials as Record<string, unknown>) ?? data;
  const sev = labelToSeverity(String(essentials.severity ?? 'Sev3'));
  const alert = String(essentials.alertRule ?? essentials.alertId ?? 'Azure Monitor alert');
  return base('azure_monitor', 'host.anomaly', sev, tenantId, alert, [alert], { raw: data });
}

export function normalizeGcpChronicle(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const results = (raw.security_result as Record<string, unknown>[]) ?? [];
  const first = results[0] ?? {};
  const sev = labelToSeverity(String(first.severity ?? 'LOW'));
  const summary = String(first.summary ?? first.description ?? 'Chronicle alert');
  const principal = raw.principal as Record<string, unknown> | undefined;
  const src = Array.isArray(principal?.ip) ? principal.ip[0] : principal?.ip;
  return base('gcp_chronicle', 'network.intrusion', sev, tenantId, summary, [summary, src], {
    raw,
    source: src ? { ip: String(src) } : undefined,
  });
}

export function normalizeGcpScc(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const finding = (raw.finding as Record<string, unknown>) ?? raw;
  const sev = labelToSeverity(String(finding.severity ?? 'SEVERITY_UNSPECIFIED'));
  const category = String(finding.category ?? 'SCC finding');
  return base('gcp_scc', 'cloud.misconfig', sev, tenantId, category, [category], { raw: finding });
}

export function normalizeGcpCloudLogging(raw: Record<string, unknown>, tenantId: number): SecurityEventCanonical {
  const proto = (raw.protoPayload as Record<string, unknown>) ?? raw;
  const method = String(proto.methodName ?? proto.method ?? 'logging.event');
  const sev = /delete|setIamPolicy/i.test(method) ? 'high' : 'medium';
  return base('gcp_cloud_logging', 'cloud.api', sev, tenantId, method, [method], { raw: proto });
}

export type CloudIngestSource =
  | 'aws_cloudwatch'
  | 'aws_guardduty'
  | 'aws_securityhub'
  | 'aws_cloudtrail'
  | 'azure_sentinel'
  | 'azure_defender'
  | 'azure_monitor'
  | 'gcp_chronicle'
  | 'gcp_scc'
  | 'gcp_cloud_logging';

export function normalizeCloud(
  source: CloudIngestSource,
  payload: unknown,
  tenantId: number
): SecurityEventCanonical | null {
  if (!payload || typeof payload !== 'object') return null;
  const raw = payload as Record<string, unknown>;
  switch (source) {
    case 'aws_guardduty':
      return normalizeAwsGuardDuty(raw, tenantId);
    case 'aws_cloudwatch':
      return normalizeAwsCloudWatch(raw, tenantId);
    case 'aws_securityhub':
      return normalizeAwsSecurityHub(raw, tenantId);
    case 'aws_cloudtrail':
      return normalizeAwsCloudTrail(raw, tenantId);
    case 'azure_sentinel':
      return normalizeAzureSentinel(raw, tenantId);
    case 'azure_defender':
      return normalizeAzureDefender(raw, tenantId);
    case 'azure_monitor':
      return normalizeAzureMonitor(raw, tenantId);
    case 'gcp_chronicle':
      return normalizeGcpChronicle(raw, tenantId);
    case 'gcp_scc':
      return normalizeGcpScc(raw, tenantId);
    case 'gcp_cloud_logging':
      return normalizeGcpCloudLogging(raw, tenantId);
    default:
      return null;
  }
}

export const CLOUD_INGEST_SOURCES: CloudIngestSource[] = [
  'aws_cloudwatch',
  'aws_guardduty',
  'aws_securityhub',
  'aws_cloudtrail',
  'azure_sentinel',
  'azure_defender',
  'azure_monitor',
  'gcp_chronicle',
  'gcp_scc',
  'gcp_cloud_logging',
];
