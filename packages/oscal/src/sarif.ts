/**
 * @grc-claw/oscal — SARIF 2.1.0 export helpers
 *
 * Transforms IaC scan results into SARIF 2.1.0 format for GitHub Advanced Security
 * and other SARIF-compatible tools.
 * https://docs.oasis-open.org/sarif/sarif/v2.1.0/
 */

export interface IacScanResult {
  rule_id?: string;
  rule_title?: string;
  severity?: string;
  file_path?: string;
  line_number?: number;
  description?: string;
  framework?: string;
}

export interface SarifRule {
  id: string;
  name: string;
  shortDescription: { text: string };
  defaultConfiguration: { level: 'error' | 'warning' | 'note' };
  properties: { tags: string[]; 'security-severity': string };
}

export interface SarifResult {
  ruleId: string;
  level: 'error' | 'warning' | 'note';
  message: { text: string };
  locations: Array<{
    physicalLocation: {
      artifactLocation: { uri: string };
      region?: { startLine: number };
    };
  }>;
}

export interface SarifLog {
  version: '2.1.0';
  $schema: string;
  runs: Array<{
    tool: {
      driver: {
        name: string;
        version: string;
        informationUri: string;
        rules: SarifRule[];
      };
    };
    results: SarifResult[];
    invocations: Array<{ executionSuccessful: boolean; endTimeUtc: string }>;
  }>;
}

function severityToLevel(severity?: string): 'error' | 'warning' | 'note' {
  if (severity === 'critical' || severity === 'high') return 'error';
  if (severity === 'medium') return 'warning';
  return 'note';
}

function severityToScore(severity?: string): string {
  if (severity === 'critical') return '9.0';
  if (severity === 'high') return '7.0';
  if (severity === 'medium') return '4.0';
  return '1.0';
}

/**
 * Transforms an array of IaC scan results into a SARIF 2.1.0 log.
 */
export function iacScanToSarif(results: IacScanResult[]): SarifLog {
  const ruleMap = new Map<string, SarifRule>();

  for (const r of results) {
    const id = r.rule_id ?? 'UNKNOWN';
    if (!ruleMap.has(id)) {
      ruleMap.set(id, {
        id,
        name: id.replace(/-/g, '_'),
        shortDescription: { text: r.rule_title ?? id },
        defaultConfiguration: { level: severityToLevel(r.severity) },
        properties: {
          tags: [r.framework ?? 'grc'],
          'security-severity': severityToScore(r.severity),
        },
      });
    }
  }

  const sarifResults: SarifResult[] = results.map((r) => {
    const location: SarifResult['locations'][0] = {
      physicalLocation: {
        artifactLocation: { uri: r.file_path ?? 'unknown' },
        ...(r.line_number ? { region: { startLine: r.line_number } } : {}),
      },
    };

    return {
      ruleId: r.rule_id ?? 'UNKNOWN',
      level: severityToLevel(r.severity),
      message: { text: r.description ?? r.rule_title ?? r.rule_id ?? 'No description' },
      locations: [location],
    };
  });

  return {
    version: '2.1.0',
    $schema:
      'https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json',
    runs: [
      {
        tool: {
          driver: {
            name: 'A2Z SOC IaC Scanner',
            version: '10.0',
            informationUri: 'https://a2zsoc.com',
            rules: [...ruleMap.values()],
          },
        },
        results: sarifResults,
        invocations: [
          { executionSuccessful: true, endTimeUtc: new Date().toISOString() },
        ],
      },
    ],
  };
}
