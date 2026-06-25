import type { RegulatorySource, ChangeDetectionResult, ChangeType } from "../types.js";

export interface ChangeDetectorConfig {
  similarityThreshold: number;
  keywordChanges: string[];
  structuralIndicators: string[];
}

const DEFAULT_CONFIG: ChangeDetectorConfig = {
  similarityThreshold: 0.85,
  keywordChanges: [
    "shall", "must", "required", "mandatory", "prohibited",
    "new requirement", "amended", "revised", "updated",
    "enforcement", "penalty", "fine", "sanction",
  ],
  structuralIndicators: [
    "section", "article", "clause", "paragraph",
    "effective date", "deadline", "compliance date",
  ],
};

export class RegulatoryChangeDetector {
  private previousContent: Map<string, string> = new Map();
  private config: ChangeDetectorConfig;

  constructor(config: Partial<ChangeDetectorConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  async detectChange(source: RegulatorySource, newContent: string): Promise<ChangeDetectionResult> {
    const previousContent = this.previousContent.get(source.id);

    if (!previousContent) {
      this.previousContent.set(source.id, newContent);
      return { hasChange: true, changeType: "new_regulation", confidence: 1.0, diffSummary: "First content capture" };
    }

    if (previousContent === newContent) {
      return { hasChange: false, confidence: 1.0 };
    }

    const similarity = this.calculateSimilarity(previousContent, newContent);

    if (similarity >= this.config.similarityThreshold) {
      return { hasChange: false, confidence: similarity };
    }

    const changeType = this.classifyChangeType(previousContent, newContent);
    const diffSummary = this.generateDiffSummary(previousContent, newContent);

    this.previousContent.set(source.id, newContent);

    return {
      hasChange: true,
      changeType,
      confidence: 1 - similarity,
      diffSummary,
    };
  }

  private calculateSimilarity(oldContent: string, newContent: string): number {
    const oldWords = new Set(oldContent.toLowerCase().split(/\s+/));
    const newWords = new Set(newContent.toLowerCase().split(/\s+/));

    const intersection = new Set([...oldWords].filter((w) => newWords.has(w)));
    const union = new Set([...oldWords, ...newWords]);

    return union.size > 0 ? intersection.size / union.size : 0;
  }

  private classifyChangeType(oldContent: string, newContent: string): ChangeType {
    const oldLower = oldContent.toLowerCase();
    const newLower = newContent.toLowerCase();

    if (newLower.includes("new regulation") || newLower.includes("new standard") || newLower.includes("new requirement")) {
      return "new_regulation";
    }

    if (newLower.includes("amendment") || newLower.includes("revised") || newLower.includes("updated")) {
      return "amendment";
    }

    if (newLower.includes("guidance") || newLower.includes("interpretation") || newLower.includes("clarification")) {
      return "guidance_update";
    }

    if (newLower.includes("enforcement") || newLower.includes("penalty") || newLower.includes("fine")) {
      return "enforcement_action";
    }

    if (newLower.includes("deadline") || newLower.includes("effective date") || newLower.includes("compliance date")) {
      return "deadline_change";
    }

    if (newLower.includes("revision") || newLower.includes("version") || newLower.includes("edition")) {
      return "standard_revision";
    }

    return "amendment";
  }

  private generateDiffSummary(oldContent: string, newContent: string): string {
    const oldSentences = oldContent.split(/[.!?]+/).filter((s) => s.trim().length > 10);
    const newSentences = newContent.split(/[.!?]+/).filter((s) => s.trim().length > 10);

    const added = newSentences.filter((s) => !oldSentences.some((os) => this.calculateSimilarity(os, s) > 0.8));
    const removed = oldSentences.filter((s) => !newSentences.some((ns) => this.calculateSimilarity(s, ns) > 0.8));

    const summary: string[] = [];
    if (added.length > 0) summary.push(`${added.length} new sentences added`);
    if (removed.length > 0) summary.push(`${removed.length} sentences removed`);

    return summary.join("; ") || "Content modified";
  }

  getContentHash(sourceId: string): string | undefined {
    const content = this.previousContent.get(sourceId);
    if (!content) return undefined;

    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return hash.toString(16);
  }
}
