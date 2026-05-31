import type { Severity } from '@grc-claw/core';

export function wazuhLevelToSeverity(level: number): Severity {
  if (level >= 12) return 'critical';
  if (level >= 8) return 'high';
  if (level >= 5) return 'medium';
  return 'low';
}

export function suricataSeverityToSeverity(sev: number): Severity {
  if (sev <= 1) return 'critical';
  if (sev === 2) return 'high';
  if (sev === 3) return 'medium';
  return 'low';
}

export function snortPriorityToSeverity(priority: number): Severity {
  if (priority <= 1) return 'critical';
  if (priority === 2) return 'high';
  if (priority === 3) return 'medium';
  return 'low';
}

export function firewallActionToSeverity(action: string): Severity {
  const a = action.toUpperCase();
  if (a.includes('BLOCK') || a.includes('DROP') || a.includes('REJECT')) return 'medium';
  return 'low';
}
