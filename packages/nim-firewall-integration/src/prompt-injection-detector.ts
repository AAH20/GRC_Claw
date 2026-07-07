import type { InjectionDetectionResult } from './types.js';

const INJECTION_PATTERNS: Array<{ pattern: RegExp; weight: number; name: string }> = [
  { pattern: /ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)/i, weight: 0.9, name: 'ignore-instructions' },
  { pattern: /you\s+are\s+now\s+(a|an)\s+/i, weight: 0.85, name: 'role-hijack' },
  { pattern: /disregard\s+(all\s+)?(previous|your|prior)/i, weight: 0.9, name: 'disregard-prior' },
  { pattern: /system\s*prompt\s*override/i, weight: 0.95, name: 'system-override' },
  { pattern: /pretend\s+(you\s+are|to\s+be|you're)\s+(a\s+)?(different|new|another)/i, weight: 0.8, name: 'role-impersonation' },
  { pattern: /\bDAN\b.*\bmode\b|\bdo\s+anything\s+now\b/i, weight: 0.95, name: 'dan-mode' },
  { pattern: /jailbreak|bypass\s+(safety|security|filter|restriction)/i, weight: 0.9, name: 'jailbreak-attempt' },
  { pattern: /\[INST\]|\[\/INST\]|<<SYS>>|<<\/SYS>>/i, weight: 0.85, name: 'token-injection' },
  { pattern: /<\|im_start\|>|<\|im_end\|>|<\|system\|>|<\|user\|>|<\|assistant\|>/i, weight: 0.9, name: 'chatml-injection' },
  { pattern: /override|overrule|countermand|supersede/i, weight: 0.6, name: 'override-keyword' },
  { pattern: /reveal\s+(your|the)\s+(system\s+)?prompt/i, weight: 0.8, name: 'prompt-extraction' },
  { pattern: /what\s+(are|is)\s+your\s+(system\s+)?(instructions?|prompts?|rules?)/i, weight: 0.75, name: 'prompt-revelation' },
  { pattern: /repeat\s+(everything|all|the)\s+(above|before|from|start)/i, weight: 0.7, name: 'repetition-extract' },
  { pattern: /translate\s+(to|into)\s+(spanish|french|chinese|arabic|rot13|base64)\s*(and|then)/i, weight: 0.65, name: 'encoding-bypass' },
  { pattern: /write\s+a?\s?(story|poem|code|script|essay)\s+(about|where|that|containing)\s+(ignore|override|disregard)/i, weight: 0.8, name: 'creative-injection' },
  { pattern: /\b(drop|delete|remove|truncate)\s+(all|the|your)\s+(tables?|data|instructions?|rules?|constraints?)/i, weight: 0.85, name: 'data-destruction' },
  { pattern: /act\s+as\s+if\s+(there|you)\s+(are|have)\s+no\s+(restrictions?|rules?|limitations?|filters?)/i, weight: 0.9, name: 'restriction-removal' },
  { pattern: /developer\s+mode|debug\s+mode|admin\s+mode|root\s+mode|sudo\s+mode/i, weight: 0.85, name: 'privilege-escalation' },
  { pattern: /from\s+now\s+on\s+(ignore|forget|override|disregard)/i, weight: 0.85, name: 'temporal-override' },
  { pattern: /\b(exec|eval|execScript|Function)\s*\(/i, weight: 0.7, name: 'code-execution' },
];

const ENCODING_BYPASS_PATTERNS: Array<{ pattern: RegExp; weight: number; name: string }> = [
  { pattern: /base64[\s:=]+[A-Za-z0-9+/]{20,}/i, weight: 0.6, name: 'base64-encoded' },
  { pattern: /hex[\s:=]+[0-9a-fA-F]{20,}/i, weight: 0.5, name: 'hex-encoded' },
  { pattern: /rot13[\s:=]+[a-zA-Z]{10,}/i, weight: 0.5, name: 'rot13-encoded' },
  { pattern: /\\x[0-9a-fA-F]{2}/i, weight: 0.4, name: 'hex-escape-sequence' },
];

const INJECTION_SCORE_THRESHOLD_FLAG = 0.5;
const INJECTION_SCORE_THRESHOLD_BLOCK = 0.8;

export class PromptInjectionDetector {
  private customPatterns: Array<{ pattern: RegExp; weight: number; name: string }> = [];

  addPattern(pattern: RegExp, weight: number, name: string): void {
    this.customPatterns.push({ pattern, weight, name: this.sanitizeName(name) });
  }

  removePattern(name: string): void {
    this.customPatterns = this.customPatterns.filter((p) => p.name !== name);
  }

  detect(prompt: string, systemPrompt?: string): InjectionDetectionResult {
    const allPatterns = [...INJECTION_PATTERNS, ...ENCODING_BYPASS_PATTERNS, ...this.customPatterns];
    const matchedPatterns: string[] = [];
    let totalScore = 0;
    let maxWeight = 0;

    for (const { pattern, weight, name } of allPatterns) {
      if (pattern.test(prompt)) {
        matchedPatterns.push(name);
        totalScore += weight;
        maxWeight = Math.max(maxWeight, weight);
      }
    }

    if (systemPrompt) {
      for (const { pattern, weight, name } of allPatterns) {
        if (pattern.test(systemPrompt)) {
          matchedPatterns.push(`system:${name}`);
          totalScore += weight * 0.5;
        }
      }
    }

    const normalizedScore = this.normalizeScore(totalScore, matchedPatterns.length);
    const action = this.determineAction(normalizedScore, maxWeight);

    return {
      detected: matchedPatterns.length > 0,
      score: normalizedScore,
      patterns: matchedPatterns,
      action,
    };
  }

  private normalizeScore(rawScore: number, matchCount: number): number {
    const weighted = rawScore * (1 + matchCount * 0.1);
    return Math.min(1, weighted);
  }

  private determineAction(
    score: number,
    maxWeight: number
  ): 'allow' | 'flag' | 'block' {
    if (score >= INJECTION_SCORE_THRESHOLD_BLOCK || maxWeight >= 0.9) {
      return 'block';
    }
    if (score >= INJECTION_SCORE_THRESHOLD_FLAG) {
      return 'flag';
    }
    return 'allow';
  }

  private sanitizeName(name: string): string {
    return name.replace(/[^a-zA-Z0-9_-]/g, '_');
  }
}
