export interface ClauseMapping {
  clause: string;
  title: string;
  implementationAnchor: string;
}

export const ISO_42001_CLAUSE_MAP: ClauseMapping[] = [
  { clause: '4', title: 'Context of the organization', implementationAnchor: 'AIMS scope doc, interested parties' },
  { clause: '5', title: 'Leadership', implementationAnchor: 'AI policy, roles, management commitment' },
  { clause: '6', title: 'Planning', implementationAnchor: 'AI risk register, objectives' },
  { clause: '7', title: 'Support', implementationAnchor: 'Competence, awareness, documented information' },
  { clause: '8', title: 'Operation', implementationAnchor: 'Gateway, exec policy, suppliers' },
  { clause: '9', title: 'Performance evaluation', implementationAnchor: 'KPIs, audit, management review' },
  { clause: '10', title: 'Improvement', implementationAnchor: 'Nonconformity, corrective action' },
];

export function listClauseMap(): ClauseMapping[] {
  return [...ISO_42001_CLAUSE_MAP];
}
