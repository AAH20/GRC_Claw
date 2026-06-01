export const OSS_SOURCES = ['wazuh', 'suricata', 'snort', 'elastic', 'ufw'] as const;

export const CLOUD_SOURCES = [
  'aws_guardduty',
  'aws_cloudwatch',
  'aws_securityhub',
  'aws_cloudtrail',
  'azure_sentinel',
  'azure_defender',
  'azure_monitor',
  'gcp_chronicle',
  'gcp_scc',
  'gcp_cloud_logging',
] as const;

export const CLAW_SKILL_TOOLS = [
  { name: 'claw.list_skills', tier: 'read' as const },
  { name: 'claw.get_skill', tier: 'read' as const },
  { name: 'claw.run_skill', tier: 'write' as const },
];

export const BUILTIN_TOOLS = [
  { name: 'grc.list_controls', tier: 'read' },
  { name: 'grc.get_compliance_score', tier: 'read' },
  { name: 'evidence.read', tier: 'read' },
  { name: 'soc.query_events', tier: 'read' },
  { name: 'evidence.attach', tier: 'write' },
  { name: 'control.update_status', tier: 'write' },
  { name: 'sentinel.get_incident', tier: 'read' },
  { name: 'aws.guardduty.list_findings', tier: 'read' },
  { name: 'soar.run_playbook', tier: 'destructive' },
  { name: 'firewall.apply_rule', tier: 'destructive' },
  { name: 'sentinel.run_playbook', tier: 'destructive' },
  { name: 'chronicle.soar.run_playbook', tier: 'destructive' },
] as const;

export const SAMPLE_PAYLOADS: Record<string, unknown> = {
  suricata: {
    timestamp: '2026-05-31T12:00:00Z',
    event_type: 'alert',
    src_ip: '10.1.1.1',
    dest_ip: '10.2.2.2',
    alert: { signature_id: 99, signature: 'ET TEST', severity: 1 },
  },
  wazuh: {
    rule: { id: 5710, level: 12, description: 'SSH brute force' },
    data: { srcip: '203.0.113.5', dstip: '192.168.0.1' },
  },
  aws_guardduty: {
    detail: {
      id: 'sample-finding',
      type: 'UnauthorizedAccess:EC2/SSHBruteForce',
      severity: 8,
      accountId: '123456789012',
      region: 'us-east-1',
    },
  },
  azure_sentinel: {
    id: '/subscriptions/demo/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws/providers/Microsoft.SecurityInsights/incidents/inc-1',
    properties: {
      title: 'Brute force attempt',
      severity: 'High',
      status: 'New',
    },
  },
};

export const VENDORS = ['anthropic', 'openai', 'cursor', 'openclaw'] as const;
