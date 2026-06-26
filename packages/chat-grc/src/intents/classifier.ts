import type { IntentMatch, IntentType } from '../types.js';

interface IntentPattern {
  intent: IntentType;
  patterns: RegExp[];
  entityExtractors: Record<string, RegExp>;
}

const INTENT_PATTERNS: IntentPattern[] = [
  {
    intent: 'query_controls',
    patterns: [
      /show\s+(?:me\s+)?(?:all\s+)?controls?\s+(?:for|of|in)\s+(.+)/i,
      /list\s+(?:all\s+)?controls?\s+(?:for|of|in)\s+(.+)/i,
      /what\s+controls?\s+(?:does|are)\s+(.+)/i,
      /(?:get|find|search)\s+controls?\s+(?:for|of|in)\s+(.+)/i,
      /controls?\s+(?:for|of|in)\s+(.+)/i,
    ],
    entityExtractors: {
      framework: /(?:SOC\s*2|ISO\s*27001|NIST\s*CSF|HIPAA|PCI\s*DSS|GDPR|FedRAMP|CMMC|ISO\s*42001|DORA|NIST\s*800[\-\.]53|NIST\s*800[\-\.]171|ISO\s*27701)/i,
    },
  },
  {
    intent: 'query_evidence',
    patterns: [
      /what\s+evidence\s+(?:is\s+)?missing\s+(?:for|of|in)\s+(.+)/i,
      /evidence\s+(?:status|coverage)\s+(?:for|of|in)\s+(.+)/i,
      /show\s+(?:me\s+)?evidence\s+(?:for|of|in)\s+(.+)/i,
      /which\s+controls?\s+(?:are\s+)?(?:missing|lacking)\s+evidence/i,
      /evidence\s+(?:gap|missing|deficiency)/i,
    ],
    entityExtractors: {
      framework: /(?:SOC\s*2|ISO\s*27001|NIST\s*CSF|HIPAA|PCI\s*DSS|GDPR|FedRAMP|CMMC|ISO\s*42001|DORA)/i,
    },
  },
  {
    intent: 'query_risks',
    patterns: [
      /what\s+are\s+(?:our\s+)?(?:top\s+)?risks?/i,
      /show\s+(?:me\s+)?(?:the\s+)?risk\s+register/i,
      /list\s+(?:the\s+)?(?:top\s+)?risks?/i,
      /risk\s+(?:register|assessment|analysis)/i,
      /what\s+are\s+the\s+highest\s+risks?/i,
    ],
    entityExtractors: {},
  },
  {
    intent: 'query_posture',
    patterns: [
      /(?:compliance|security)\s+posture/i,
      /overall\s+(?:compliance|security)\s+(?:score|status|rating)/i,
      /how\s+(?:are|is)\s+we\s+(?:doing|compliant)/i,
      /show\s+(?:me\s+)?(?:our\s+)?compliance\s+(?:score|status|rating)/i,
      /what\s+(?:is|are)\s+(?:our\s+)?compliance\s+score/i,
    ],
    entityExtractors: {
      framework: /(?:SOC\s*2|ISO\s*27001|NIST\s*CSF|HIPAA|PCI\s*DSS|GDPR|FedRAMP|CMMC|ISO\s*42001|DORA)/i,
    },
  },
  {
    intent: 'query_frameworks',
    patterns: [
      /which\s+frameworks?\s+(?:are|is)\s+(?:supported|available|enabled)/i,
      /list\s+(?:all\s+)?(?:supported\s+)?frameworks?/i,
      /show\s+(?:me\s+)?(?:all\s+)?frameworks?/i,
      /what\s+frameworks?\s+(?:are|is)\s+(?:supported|available)/i,
    ],
    entityExtractors: {},
  },
  {
    intent: 'generate_report',
    patterns: [
      /generate\s+(?:a\s+)?(?:board|compliance|gap|risk)\s+report/i,
      /create\s+(?:a\s+)?(?:board|compliance|gap|risk)\s+report/i,
      /show\s+(?:me\s+)?(?:a\s+)?(?:board|compliance|gap|risk)\s+report/i,
    ],
    entityExtractors: {
      reportType: /board|compliance|gap|risk/i,
    },
  },
  {
    intent: 'check_compliance',
    patterns: [
      /(?:run|execute)\s+(?:a\s+)?compliance\s+scan/i,
      /check\s+compliance\s+(?:for|of|in)\s+(.+)/i,
      /am\s+we?\s+(?:compliant|in\s+compliance)\s+(?:with|for)\s+(.+)/i,
      /are\s+we?\s+(?:compliant|in\s+compliance)\s+(?:with|for)\s+(.+)/i,
    ],
    entityExtractors: {
      framework: /(?:SOC\s*2|ISO\s*27001|NIST\s*CSF|HIPAA|PCI\s*DSS|GDPR|FedRAMP|CMMC|ISO\s*42001|DORA)/i,
    },
  },
  {
    intent: 'help',
    patterns: [
      /^help$/i,
      /^help\s+me$/i,
      /what\s+can\s+you\s+do/i,
      /what\s+commands?\s+(?:are|is)\s+(?:available|supported)/i,
      /how\s+(?:do\s+I|can\s+I|to)\s+/i,
    ],
    entityExtractors: {},
  },
];

export function classifyIntent(message: string): IntentMatch {
  const normalized = message.trim().toLowerCase();

  let bestMatch: IntentMatch = {
    intent: 'help',
    confidence: 0,
    entities: {},
  };

  for (const intentPattern of INTENT_PATTERNS) {
    for (const pattern of intentPattern.patterns) {
      const regexMatch = normalized.match(pattern);
      if (regexMatch) {
        const entities: Record<string, string> = {};

        for (const [key, extractor] of Object.entries(intentPattern.entityExtractors)) {
          const entityMatch = message.match(extractor);
          if (entityMatch) {
            entities[key] = entityMatch[0].trim();
          }
        }

        const confidence = Object.keys(entities).length > 0 ? 0.95 : 0.85;

        if (confidence > bestMatch.confidence) {
          bestMatch = {
            intent: intentPattern.intent,
            confidence,
            entities,
          };
        }
      }
    }
  }

  if (bestMatch.confidence === 0) {
    if (/control|polic(?:y|ies)|requirement|comply/i.test(normalized)) {
      bestMatch = { intent: 'query_controls', confidence: 0.6, entities: {} };
    } else if (/evidence|document|artifact|proof/i.test(normalized)) {
      bestMatch = { intent: 'query_evidence', confidence: 0.6, entities: {} };
    } else if (/risk|threat|vulnerability|likelihood/i.test(normalized)) {
      bestMatch = { intent: 'query_risks', confidence: 0.6, entities: {} };
    } else if (/posture|score|rating|status|overall/i.test(normalized)) {
      bestMatch = { intent: 'query_posture', confidence: 0.6, entities: {} };
    } else if (/report|summary|brief|dashboard/i.test(normalized)) {
      bestMatch = { intent: 'generate_report', confidence: 0.6, entities: {} };
    } else if (/scan|check|audit|verify/i.test(normalized)) {
      bestMatch = { intent: 'check_compliance', confidence: 0.6, entities: {} };
    }
  }

  return bestMatch;
}

export function normalizeFrameworkName(input: string): string {
  const map: Record<string, string> = {
    'soc2': 'soc2',
    'soc 2': 'soc2',
    'soc 2.0': 'soc2',
    'iso27001': 'iso27001',
    'iso 27001': 'iso27001',
    'iso/iec 27001': 'iso27001',
    'iso27001:2022': 'iso27001',
    'nist csf': 'nist_csf',
    'nist_csf': 'nist_csf',
    'nist csf 2.0': 'nist_csf',
    'hipaa': 'hipaa',
    'pci dss': 'pci_dss',
    'pcidss': 'pci_dss',
    'pci-dss': 'pci_dss',
    'gdpr': 'gdpr',
    'fedramp': 'fedramp',
    'cmmc': 'cmmc',
    'iso42001': 'iso42001',
    'iso 42001': 'iso42001',
    'iso/iec 42001': 'iso42001',
    'dora': 'dora',
    'nist 800-53': 'nist_800_53',
    'nist800-53': 'nist_800_53',
    'nist 800 53': 'nist_800_53',
    'nist 800-171': 'nist_800_171',
    'nist800-171': 'nist_800_171',
    'iso 27701': 'iso27701',
    'iso27701': 'iso27701',
  };
  const key = input.trim().toLowerCase();
  return map[key] ?? key;
}
