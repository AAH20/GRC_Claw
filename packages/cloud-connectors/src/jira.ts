// Jira connector — pulls issues tagged as security/compliance tickets
// and maps them to GRC controls as evidence

export interface JiraConfig {
  baseUrl: string; // e.g. https://acme.atlassian.net
  email: string;
  apiToken: string;
  projectKey: string;
  securityLabelOrType?: string; // filter: label or issue type to pull
}

export interface JiraEvidence {
  issueKey: string;
  summary: string;
  status: string;
  assignee?: string;
  created: string;
  updated: string;
  labels: string[];
  url: string;
  mappedControls: string[]; // inferred from labels
}

const JIRA_CONTROL_LABEL_MAP: Record<string, string[]> = {
  'soc2': ['SOC2:CC6.1', 'SOC2:CC7.1'],
  'iso27001': ['ISO27001:A.5.1', 'ISO27001:A.8.1'],
  'access-control': ['SOC2:CC6.1', 'ISO27001:A.9.1'],
  'encryption': ['SOC2:CC9.2', 'ISO27001:A.8.24'],
  'vulnerability': ['SOC2:CC7.1', 'NIST:DE.CM-8'],
  'incident': ['SOC2:CC7.3', 'ISO27001:A.5.26'],
  'change-management': ['SOC2:CC8.1', 'ISO27001:A.8.32'],
};

export async function fetchJiraSecurityEvidence(config: JiraConfig): Promise<JiraEvidence[]> {
  const auth = Buffer.from(`${config.email}:${config.apiToken}`).toString('base64');
  const jql = config.securityLabelOrType
    ? `project=${config.projectKey} AND (labels="${config.securityLabelOrType}" OR issuetype="${config.securityLabelOrType}") ORDER BY updated DESC`
    : `project=${config.projectKey} AND labels in ("security","compliance","soc2","iso27001") ORDER BY updated DESC`;

  const res = await fetch(`${config.baseUrl}/rest/api/3/search?jql=${encodeURIComponent(jql)}&maxResults=100&fields=summary,status,assignee,created,updated,labels`, {
    headers: { Authorization: `Basic ${auth}`, Accept: 'application/json' }
  });
  if (!res.ok) throw new Error(`Jira API error: ${res.status}`);
  const { issues } = await res.json();

  return (issues || []).map((issue: any) => {
    const labels: string[] = issue.fields.labels || [];
    const mappedControls = [...new Set(labels.flatMap((l: string) => JIRA_CONTROL_LABEL_MAP[l.toLowerCase()] || []))] as string[];
    return {
      issueKey: issue.key,
      summary: issue.fields.summary,
      status: issue.fields.status?.name || 'Unknown',
      assignee: issue.fields.assignee?.displayName,
      created: issue.fields.created,
      updated: issue.fields.updated,
      labels,
      url: `${config.baseUrl}/browse/${issue.key}`,
      mappedControls
    };
  });
}
