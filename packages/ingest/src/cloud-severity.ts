import type { Severity } from '@grc-claw/core';

export function labelToSeverity(label: string | undefined): Severity {
  const v = (label ?? 'low').toUpperCase();
  if (v.includes('CRIT')) return 'critical';
  if (v === 'HIGH' || v === '4') return 'high';
  if (v === 'MEDIUM' || v === '3') return 'medium';
  return 'low';
}

/** GuardDuty 0.1–8.0 */
export function guardDutyScore(score: number): Severity {
  if (score >= 7) return 'critical';
  if (score >= 4) return 'high';
  if (score >= 2) return 'medium';
  return 'low';
}
