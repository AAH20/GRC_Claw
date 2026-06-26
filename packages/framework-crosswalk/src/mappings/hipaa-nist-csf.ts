import type { CrossMapping } from '../types.js';

export const HIPAA_NISTCSF_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'hipaa', sourceControl: '§164.308(a)(1)', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'hipaa', sourceControl: '§164.308(a)(3)', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'hipaa', sourceControl: '§164.308(a)(4)', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'hipaa', sourceControl: '§164.308(a)(5)', targetFramework: 'nist_csf', targetControl: 'PR.AT', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'hipaa', sourceControl: '§164.308(a)(6)', targetFramework: 'nist_csf', targetControl: 'RS.RP', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'hipaa', sourceControl: '§164.308(a)(7)', targetFramework: 'nist_csf', targetControl: 'RC.RP', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'hipaa', sourceControl: '§164.310(a)(1)', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'hipaa', sourceControl: '§164.310(a)(2)(iii)', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'hipaa', sourceControl: '§164.310(b)', targetFramework: 'nist_csf', targetControl: 'PR.DS', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'hipaa', sourceControl: '§164.310(c)', targetFramework: 'nist_csf', targetControl: 'PR.IP', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'hipaa', sourceControl: '§164.310(d)(1)', targetFramework: 'nist_csf', targetControl: 'PR.DS', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'hipaa', sourceControl: '§164.312(a)(1)', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'hipaa', sourceControl: '§164.312(b)', targetFramework: 'nist_csf', targetControl: 'PR.DS', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'hipaa', sourceControl: '§164.312(c)(1)', targetFramework: 'nist_csf', targetControl: 'PR.DS', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'hipaa', sourceControl: '§164.312(d)', targetFramework: 'nist_csf', targetControl: 'PR.AC', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'hipaa', sourceControl: '§164.312(e)(1)', targetFramework: 'nist_csf', targetControl: 'PR.DS', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'hipaa', sourceControl: '§164.316(b)', targetFramework: 'nist_csf', targetControl: 'ID.GV', confidence: 0.8, relationship: 'partial' },
];

export const HIPAA_NISTCSF_PAIR = { source: 'hipaa', target: 'nist_csf' };
