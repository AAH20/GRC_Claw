import { createHash } from 'node:crypto';
import type {
  NemotronModel,
  AiBomEntry,
  TrainingDataRecord,
  VulnerabilityRecord,
} from './types.js';

const TRAINING_DOMAIN_LICENSES: Record<string, string> = {
  'common-crawl': 'CC-BY-4.0',
  wikipedia: 'CC-BY-SA-3.0',
  arxiv: 'arXiv non-exclusive license',
  stackoverflow: 'CC-BY-SA-4.0',
  books: 'Various (commercial-use restricted)',
  code: 'MIT/Apache-2.0',
  news: 'various',
  social: 'various (PII-sensitive)',
};

const NEMOTRON_KNOWN_VULNERABILITIES: VulnerabilityRecord[] = [
  {
    id: 'NEM-VULN-001',
    severity: 'medium',
    description: 'Large language models may generate plausible but factually incorrect information (hallucinations).',
    mitigation: 'Implement output validation and fact-checking layers.',
  },
  {
    id: 'NEM-VULN-002',
    severity: 'medium',
    description: 'Models may leak training data through carefully crafted prompts.',
    mitigation: 'Apply differential privacy techniques and input/output filtering.',
  },
  {
    id: 'NEM-VULN-003',
    severity: 'low',
    description: 'Models may exhibit bias reflective of training data composition.',
    mitigation: 'Run bias evaluation suites and implement bias mitigation pipelines.',
  },
  {
    id: 'NEM-VULN-004',
    severity: 'high',
    description: 'Adversarial inputs may cause unexpected model behavior.',
    mitigation: 'Implement adversarial input detection and guardrails.',
  },
  {
    id: 'NEM-VULN-005',
    severity: 'medium',
    description: 'Model weights may be extracted through model inversion attacks.',
    mitigation: 'Deploy behind secure enclaves and restrict API access.',
  },
];

function hashData(data: string): string {
  return createHash('sha256').update(data).digest('hex');
}

function generateTrainingDataRecords(model: NemotronModel): TrainingDataRecord[] {
  const records: TrainingDataRecord[] = [];

  for (const source of model.trainingDataSources) {
    const normalizedSource = source.toLowerCase().replace(/[\s_]/g, '-');
    let domain = 'general';
    let license = 'unknown';

    for (const [key, value] of Object.entries(TRAINING_DOMAIN_LICENSES)) {
      if (normalizedSource.includes(key)) {
        domain = key;
        license = value;
        break;
      }
    }

    const piiFlagged =
      normalizedSource.includes('social') ||
      normalizedSource.includes('email') ||
      normalizedSource.includes('personal');

    records.push({
      source,
      domain,
      sizeBytes: 0,
      license,
      piiFlagged,
    });
  }

  if (records.length === 0) {
    records.push({
      source: 'NVIDIA Nemotron Training Corpus',
      domain: 'general',
      sizeBytes: 0,
      license: 'NVIDIA Model License',
      piiFlagged: false,
    });
  }

  return records;
}

function assessVulnerabilities(model: NemotronModel): VulnerabilityRecord[] {
  const vulns = [...NEMOTRON_KNOWN_VULNERABILITIES];

  if (model.parameters >= 70_000_000_000) {
    vulns.push({
      id: 'NEM-VULN-006',
      severity: 'high',
      description: 'Very large models have increased attack surface for model extraction.',
      mitigation: 'Implement rate limiting, query monitoring, and access controls.',
    });
  }

  if (model.capabilities.some((c) => c.toLowerCase().includes('code'))) {
    vulns.push({
      id: 'NEM-VULN-007',
      severity: 'medium',
      description: 'Code generation capability may produce vulnerable or malicious code.',
      mitigation: 'Implement code security scanning in output pipeline.',
    });
  }

  if (model.modality === 'multimodal') {
    vulns.push({
      id: 'NEM-VULN-008',
      severity: 'medium',
      description: 'Multimodal input channels may be used for prompt injection.',
      mitigation: 'Implement input sanitization for all modalities.',
    });
  }

  return vulns;
}

function checkLicenseCompliance(records: TrainingDataRecord[]): string[] {
  const warnings: string[] = [];

  for (const record of records) {
    if (record.license === 'various (PII-sensitive)') {
      warnings.push(`Training source '${record.source}' contains PII-sensitive data requiring special handling.`);
    }
    if (record.license === 'Various (commercial-use restricted)') {
      warnings.push(`Training source '${record.source}' has commercial-use restrictions that may affect downstream deployment.`);
    }
    if (record.license === 'unknown') {
      warnings.push(`Training source '${record.source}' has unknown license - verify before commercial deployment.`);
    }
  }

  return warnings;
}

export function generateAiBom(model: NemotronModel): AiBomEntry {
  const trainingData = generateTrainingDataRecords(model);
  const vulnerabilities = assessVulnerabilities(model);

  const licenseWarnings = checkLicenseCompliance(trainingData);

  const bomData = [
    model.id,
    model.name,
    model.version,
    model.license,
    ...trainingData.map((t) => t.source),
    ...vulnerabilities.map((v) => v.id),
  ].join('|');

  const sbomHash = hashData(bomData);

  return {
    modelId: model.id,
    modelName: model.name,
    version: model.version,
    trainingData,
    license: model.license,
    vulnerabilities,
    sbomHash,
    generatedAt: new Date().toISOString(),
  };
}

export function validateBomIntegrity(bom: AiBomEntry): boolean {
  const regenerated = hashData(
    [
      bom.modelId,
      bom.modelName,
      bom.version,
      bom.license,
      ...bom.trainingData.map((t) => t.source),
      ...bom.vulnerabilities.map((v) => v.id),
    ].join('|')
  );

  return regenerated === bom.sbomHash;
}

export function getBomSummary(bom: AiBomEntry): {
  totalVulnerabilities: number;
  criticalVulns: number;
  highVulns: number;
  mediumVulns: number;
  lowVulns: number;
  piiSources: number;
  unknownLicenses: number;
  commercialRestricted: number;
} {
  const vulnCounts = { critical: 0, high: 0, medium: 0, low: 0 };
  for (const v of bom.vulnerabilities) {
    vulnCounts[v.severity]++;
  }

  let unknownLicenses = 0;
  let commercialRestricted = 0;
  for (const t of bom.trainingData) {
    if (t.license === 'unknown') unknownLicenses++;
    if (t.license === 'Various (commercial-use restricted)') commercialRestricted++;
  }

  return {
    totalVulnerabilities: bom.vulnerabilities.length,
    criticalVulns: vulnCounts.critical,
    highVulns: vulnCounts.high,
    mediumVulns: vulnCounts.medium,
    lowVulns: vulnCounts.low,
    piiSources: bom.trainingData.filter((t) => t.piiFlagged).length,
    unknownLicenses,
    commercialRestricted,
  };
}
