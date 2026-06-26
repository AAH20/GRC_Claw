import type {
  CrossMapping,
  CrosswalkReport,
  FrameworkOverlap,
  CrossMappingStore,
} from './types.js';
import {
  SOC2_ISO27001_MAPPINGS,
  NISTCSF_ISO27001_MAPPINGS,
  SOC2_NISTCSF_MAPPINGS,
  ISO27001_ISO42001_MAPPINGS,
  HIPAA_NISTCSF_MAPPINGS,
  PCIDSS_ISO27001_MAPPINGS,
  GDPR_ISO27701_MAPPINGS,
  FEDRAMP_NIST80053_MAPPINGS,
  CMMC_NIST800171_MAPPINGS,
  DORA_NISTCSF_MAPPINGS,
} from './mappings/index.js';

const FRAMEWORK_ALIASES: Record<string, string> = {
  'soc2': 'soc2', 'soc_2': 'soc2', 'soc_2.0': 'soc2',
  'iso27001': 'iso27001', 'iso_27001': 'iso27001', 'iso_27001:2022': 'iso27001',
  'nist_csf': 'nist_csf', 'nist csf': 'nist_csf',
  'iso42001': 'iso42001', 'iso_42001': 'iso42001',
  'hipaa': 'hipaa',
  'pci_dss': 'pci_dss', 'pci dss': 'pci_dss', 'pcidss': 'pci_dss',
  'gdpr': 'gdpr',
  'fedramp': 'fedramp',
  'cmmc': 'cmmc',
  'nist_800_53': 'nist_800_53', 'nist_800-53': 'nist_800_53', 'nist 800-53': 'nist_800_53',
  'nist_800_171': 'nist_800_171', 'nist_800-171': 'nist_800_171', 'nist 800-171': 'nist_800_171',
  'iso27701': 'iso27701', 'iso_27701': 'iso27701',
  'dora': 'dora',
};

function normalizeFramework(code: string): string {
  const key = code.trim().toLowerCase().replace(/[\s\-/]/g, '_');
  return FRAMEWORK_ALIASES[key] ?? key;
}

function pairKey(a: string, b: string): string {
  const [x, y] = [normalizeFramework(a), normalizeFramework(b)].sort();
  return `${x}__${y}`;
}

const ALL_MAPPINGS: CrossMapping[] = [
  ...SOC2_ISO27001_MAPPINGS,
  ...NISTCSF_ISO27001_MAPPINGS,
  ...SOC2_NISTCSF_MAPPINGS,
  ...ISO27001_ISO42001_MAPPINGS,
  ...HIPAA_NISTCSF_MAPPINGS,
  ...PCIDSS_ISO27001_MAPPINGS,
  ...GDPR_ISO27701_MAPPINGS,
  ...FEDRAMP_NIST80053_MAPPINGS,
  ...CMMC_NIST800171_MAPPINGS,
  ...DORA_NISTCSF_MAPPINGS,
];

function buildIndex(mappings: CrossMapping[]): Map<string, CrossMapping[]> {
  const idx = new Map<string, CrossMapping[]>();
  for (const m of mappings) {
    const key = pairKey(m.sourceFramework, m.targetFramework);
    if (!idx.has(key)) idx.set(key, []);
    idx.get(key)!.push(m);
  }
  return idx;
}

const MAPPING_INDEX = buildIndex(ALL_MAPPINGS);

export class FrameworkCrosswalk implements CrossMappingStore {
  private extraMappings: CrossMapping[] = [];

  getMappings(source: string, target: string): CrossMapping[] {
    const ns = normalizeFramework(source);
    const nt = normalizeFramework(target);
    const key = pairKey(ns, nt);
    const builtin = MAPPING_INDEX.get(key) ?? [];
    const extra = this.extraMappings.filter(
      (m) =>
        normalizeFramework(m.sourceFramework) === ns &&
        normalizeFramework(m.targetFramework) === nt,
    );
    return [...builtin, ...extra];
  }

  addMapping(mapping: CrossMapping): void {
    this.extraMappings.push(mapping);
  }

  getSupportedPairs(): Array<[string, string]> {
    const pairs = new Set<string>();
    for (const m of [...ALL_MAPPINGS, ...this.extraMappings]) {
      const key = pairKey(m.sourceFramework, m.targetFramework);
      pairs.add(key);
    }
    return [...pairs].map((k) => {
      const [a, b] = k.split('__');
      return [a, b] as [string, string];
    });
  }

  generateCrosswalk(source: string, target: string): CrosswalkReport {
    const mappings = this.getMappings(source, target);
    const ns = normalizeFramework(source);
    const nt = normalizeFramework(target);

    const sourceControls = new Set(mappings.map((m) => m.sourceControl));
    const targetControls = new Set(mappings.map((m) => m.targetControl));

    const highConfidenceMappings = mappings.filter((m) => m.confidence >= 0.8);
    const coverage =
      mappings.length > 0
        ? highConfidenceMappings.length / mappings.length
        : 0;

    const gaps: string[] = [];
    if (mappings.length === 0) {
      gaps.push(`No cross-mappings found between ${source} and ${target}`);
    }
    const lowConfidence = mappings.filter((m) => m.confidence < 0.7);
    if (lowConfidence.length > 0) {
      gaps.push(
        `${lowConfidence.length} control(s) have low-confidence mappings (< 0.7)`,
      );
    }

    const unmatchedSource = [...sourceControls].filter(
      (sc) =>
        !mappings.some(
          (m) => m.sourceControl === sc && m.confidence >= 0.8,
        ),
    );
    if (unmatchedSource.length > 0) {
      gaps.push(
        `${unmatchedSource.length} source control(s) lack high-confidence target mappings`,
      );
    }

    return {
      sourceFramework: ns,
      targetFramework: nt,
      mappings,
      coverage: Math.round(coverage * 100) / 100,
      gaps,
    };
  }

  findOverlaps(framework1: string, framework2: string): FrameworkOverlap {
    const mappings = this.getMappings(framework1, framework2);
    const nf1 = normalizeFramework(framework1);
    const nf2 = normalizeFramework(framework2);

    const overlapping = new Set<string>();
    for (const m of mappings) {
      if (m.confidence >= 0.7) {
        overlapping.add(`${m.sourceControl}->${m.targetControl}`);
      }
    }

    const allSourceControls = new Set(
      mappings.map((m) => m.sourceControl),
    );
    const allTargetControls = new Set(
      mappings.map((m) => m.targetControl),
    );

    const totalControls = allSourceControls.size + allTargetControls.size;

    return {
      framework1: nf1,
      framework2: nf2,
      overlappingControls: overlapping.size,
      totalControls,
      overlapPercentage:
        totalControls > 0
          ? Math.round((overlapping.size / totalControls) * 10000) / 100
          : 0,
    };
  }

  findEquivalentControls(controlId: string): CrossMapping[] {
    const results: CrossMapping[] = [];
    const normalizedId = controlId.trim();

    for (const m of ALL_MAPPINGS) {
      if (
        m.sourceControl.toLowerCase().includes(normalizedId.toLowerCase()) ||
        m.targetControl.toLowerCase().includes(normalizedId.toLowerCase())
      ) {
        results.push(m);
      }
    }

    return results.sort((a, b) => b.confidence - a.confidence);
  }

  calculateMultiFrameworkCoverage(
    controlIds: string[],
    frameworks: string[],
  ): number {
    if (controlIds.length === 0 || frameworks.length === 0) return 0;

    let totalCoverage = 0;
    let pairCount = 0;

    for (let i = 0; i < frameworks.length; i++) {
      for (let j = i + 1; j < frameworks.length; j++) {
        const mappings = this.getMappings(frameworks[i], frameworks[j]);
        if (mappings.length === 0) continue;

        pairCount++;
        const matchedControls = new Set<string>();

        for (const controlId of controlIds) {
          for (const m of mappings) {
            if (
              m.sourceControl.toLowerCase().includes(controlId.toLowerCase()) ||
              m.targetControl.toLowerCase().includes(controlId.toLowerCase())
            ) {
              matchedControls.add(controlId);
            }
          }
        }

        totalCoverage += matchedControls.size / controlIds.length;
      }
    }

    return pairCount > 0
      ? Math.round((totalCoverage / pairCount) * 100) / 100
      : 0;
  }

  listAllMappings(): CrossMapping[] {
    return [...ALL_MAPPINGS, ...this.extraMappings];
  }
}
