// Linear connector — pulls security/compliance issues as evidence
// Linear uses GraphQL API

export interface LinearConfig {
  apiKey: string;
  teamId?: string;
  labelFilter?: string; // e.g. "security" or "compliance"
}

export interface LinearEvidence {
  id: string;
  identifier: string; // e.g. SEC-123
  title: string;
  state: string;
  priority: number; // 0=none, 1=urgent, 2=high, 3=medium, 4=low
  assignee?: string;
  createdAt: string;
  updatedAt: string;
  url: string;
  labels: string[];
  mappedControls: string[];
}

const LINEAR_CONTROL_MAP: Record<string, string[]> = {
  'security': ['SOC2:CC6.1', 'SOC2:CC7.1'],
  'compliance': ['SOC2:CC1.4', 'ISO27001:A.5.1'],
  'access': ['SOC2:CC6.1', 'ISO27001:A.9.1'],
  'vulnerability': ['SOC2:CC7.1', 'NIST:DE.CM-8'],
  'encryption': ['SOC2:CC9.2', 'ISO27001:A.8.24'],
};

export async function fetchLinearSecurityIssues(config: LinearConfig): Promise<LinearEvidence[]> {
  const query = `
    query SecurityIssues($filter: IssueFilter) {
      issues(filter: $filter, first: 100) {
        nodes {
          id identifier title
          state { name }
          priority assignee { name }
          createdAt updatedAt url
          labels { nodes { name } }
        }
      }
    }
  `;
  const filter: any = { labels: { name: { in: ['security', 'compliance', 'soc2', 'iso27001', config.labelFilter].filter(Boolean) } } };
  if (config.teamId) filter.team = { id: { eq: config.teamId } };

  const res = await fetch('https://api.linear.app/graphql', {
    method: 'POST',
    headers: { Authorization: config.apiKey, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables: { filter } })
  });
  if (!res.ok) throw new Error(`Linear API error: ${res.status}`);
  const { data } = await res.json();

  return (data?.issues?.nodes || []).map((issue: any) => {
    const labels = issue.labels?.nodes?.map((l: any) => l.name) || [];
    const mappedControls = [...new Set(labels.flatMap((l: string) => LINEAR_CONTROL_MAP[l.toLowerCase()] || []))] as string[];
    return {
      id: issue.id, identifier: issue.identifier, title: issue.title,
      state: issue.state?.name || 'Unknown',
      priority: issue.priority,
      assignee: issue.assignee?.name,
      createdAt: issue.createdAt, updatedAt: issue.updatedAt,
      url: issue.url, labels, mappedControls
    };
  });
}
