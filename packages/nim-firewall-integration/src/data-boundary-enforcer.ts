import type { NimRequest, NimResponse, DataBoundary } from './types.js';

const DEFAULT_BOUNDARIES: DataBoundary[] = [
  {
    type: 'CUI',
    classification: 'Controlled Unclassified Information',
    allowedModels: ['*'],
    requiresSandbox: false,
    requiresApproval: false,
    redactionPatterns: [],
  },
  {
    type: 'PHI',
    classification: 'Protected Health Information (HIPAA)',
    allowedModels: [],
    requiresSandbox: true,
    requiresApproval: true,
    redactionPatterns: [
      '\\b\\d{3}-\\d{2}-\\d{4}\\b',
      '\\b[A-Z]{2,3}\\d{6,10}\\b',
      '\\bpatient\\s+id\\b.*\\b\\w+\\b',
    ],
  },
  {
    type: 'PCI',
    classification: 'Payment Card Industry Data',
    allowedModels: [],
    requiresSandbox: true,
    requiresApproval: true,
    redactionPatterns: [
      '\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b',
      '\\b\\d{3}\\b',
      '\\bcvv\\b.*\\b\\d{3,4}\\b',
      '\\bcard\\s+number\\b',
    ],
  },
  {
    type: 'PII',
    classification: 'Personally Identifiable Information',
    allowedModels: ['*'],
    requiresSandbox: false,
    requiresApproval: false,
    redactionPatterns: [
      '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b',
      '\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b',
      '\\b\\d{3}-\\d{2}-\\d{4}\\b',
    ],
  },
];

const CUI_KEYWORDS = [
  'controlled unclassified', 'cui', 'fouo', 'for official use only',
  'law enforcement sensitive', 'les', 'export controlled', 'itar',
];

const PHI_KEYWORDS = [
  'patient', 'diagnosis', 'medical record', 'health information',
  'hipaa', 'treatment', 'prescription', 'clinical', 'healthcare',
  'medical history', 'lab result', 'vital signs', 'icd-10', 'cpt code',
];

const PCI_KEYWORDS = [
  'credit card', 'card number', 'cvv', 'cvv2', 'expiry date',
  'cardholder', 'payment card', 'pan', 'primary account number',
  ' magnetic stripe', 'chip data', 'emv',
];

export class DataBoundaryEnforcer {
  private boundaries: DataBoundary[];
  private enabledBoundaries: Set<string>;

  constructor(boundaries?: DataBoundary[]) {
    this.boundaries = boundaries ?? [...DEFAULT_BOUNDARIES];
    this.enabledBoundaries = new Set(this.boundaries.map((b) => b.type));
  }

  enableBoundary(type: DataBoundary['type']): void {
    this.enabledBoundaries.add(type);
  }

  disableBoundary(type: DataBoundary['type']): void {
    this.enabledBoundaries.delete(type);
  }

  addBoundary(boundary: DataBoundary): void {
    this.boundaries.push(boundary);
    this.enabledBoundaries.add(boundary.type);
  }

  detectBoundaries(text: string): DataBoundary[] {
    const detected: DataBoundary[] = [];
    const lowerText = text.toLowerCase();

    for (const boundary of this.boundaries) {
      if (!this.enabledBoundaries.has(boundary.type)) continue;

      const keywords = this.getKeywordsForType(boundary.type);
      if (keywords.some((kw) => lowerText.includes(kw))) {
        detected.push(boundary);
        continue;
      }

      if (this.matchesRegexPatterns(text, boundary.redactionPatterns)) {
        detected.push(boundary);
      }
    }

    return detected;
  }

  enforceRequest(request: NimRequest): {
    allowed: boolean;
    violations: string[];
    detectedBoundaries: DataBoundary[];
    requiresSandbox: boolean;
    requiresApproval: boolean;
    redactedPrompt: string;
    redactedSystemPrompt?: string;
  } {
    const violations: string[] = [];
    const detectedBoundaries: DataBoundary[] = [];
    let requiresSandbox = false;
    let requiresApproval = false;

    const fullText = [request.prompt, request.systemPrompt ?? ''].join('\n');
    const boundaries = this.detectBoundaries(fullText);

    for (const boundary of boundaries) {
      detectedBoundaries.push(boundary);

      if (boundary.allowedModels.length > 0 && !boundary.allowedModels.includes('*')) {
        if (!boundary.allowedModels.includes(request.model)) {
          violations.push(
            `Model '${request.model}' not allowed for ${boundary.type} data (${boundary.classification})`
          );
        }
      }

      if (boundary.requiresSandbox) requiresSandbox = true;
      if (boundary.requiresApproval) requiresApproval = true;
    }

    const redactedPrompt = this.redactSensitiveData(request.prompt, detectedBoundaries);
    const redactedSystemPrompt = request.systemPrompt
      ? this.redactSensitiveData(request.systemPrompt, detectedBoundaries)
      : undefined;

    return {
      allowed: violations.length === 0,
      violations,
      detectedBoundaries,
      requiresSandbox,
      requiresApproval,
      redactedPrompt,
      redactedSystemPrompt,
    };
  }

  enforceResponse(response: NimResponse, boundaries: DataBoundary[]): {
    allowed: boolean;
    violations: string[];
    redactedText: string;
  } {
    const violations: string[] = [];
    const redactedText = this.redactSensitiveData(response.text, boundaries);

    const detected = this.detectBoundaries(response.text);
    for (const boundary of detected) {
      if (!boundaries.some((b) => b.type === boundary.type)) {
        violations.push(
          `Response contains unexpected ${boundary.type} data not present in request`
        );
      }
    }

    return {
      allowed: violations.length === 0,
      violations,
      redactedText,
    };
  }

  redactSensitiveData(text: string, boundaries: DataBoundary[]): string {
    let redacted = text;

    for (const boundary of boundaries) {
      for (const pattern of boundary.redactionPatterns) {
        try {
          const regex = new RegExp(pattern, 'gi');
          redacted = redacted.replace(regex, `[REDACTED-${boundary.type}]`);
        } catch {
          continue;
        }
      }
    }

    const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/gi;
    if (boundaries.some((b) => b.type === 'PII')) {
      redacted = redacted.replace(emailRegex, '[REDACTED-EMAIL]');
    }

    const ssnRegex = /\b\d{3}-\d{2}-\d{4}\b/g;
    if (boundaries.some((b) => b.type === 'PII' || b.type === 'PHI')) {
      redacted = redacted.replace(ssnRegex, '[REDACTED-SSN]');
    }

    const phoneRegex = /\b\(\d{3}\)\s*\d{3}-\d{4}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g;
    if (boundaries.some((b) => b.type === 'PII')) {
      redacted = redacted.replace(phoneRegex, '[REDACTED-PHONE]');
    }

    return redacted;
  }

  private getKeywordsForType(type: DataBoundary['type']): string[] {
    switch (type) {
      case 'CUI': return CUI_KEYWORDS;
      case 'PHI': return PHI_KEYWORDS;
      case 'PCI': return PCI_KEYWORDS;
      case 'PII': return [];
      default: return [];
    }
  }

  private matchesRegexPatterns(text: string, patterns: string[]): boolean {
    for (const pattern of patterns) {
      try {
        if (new RegExp(pattern, 'i').test(text)) return true;
      } catch {
        continue;
      }
    }
    return false;
  }
}
