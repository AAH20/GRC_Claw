/**
 * @grc-claw/natural-language-compliance
 *
 * Natural language compliance querying — ask compliance questions in plain English
 * and get structured answers backed by mapped compliance controls.
 */

// ─── Types ────────────────────────────────────────────────────────────────────

/** Supported compliance frameworks. */
export type Framework =
  | "iso-27001"
  | "soc2"
  | "nist-csf"
  | "pci-dss"
  | "hipaa"
  | "gdpr"
  | "cis"
  | "custom";

/** Intent detected from a user query. */
export type QueryIntent =
  | "status"
  | "gap"
  | "requirement"
  | "evidence"
  | "remediation"
  | "comparison"
  | "report"
  | "general";

/** Severity of a control finding. */
export type Severity = "critical" | "high" | "medium" | "low" | "informational";

/** Compliance status of a control. */
export type ControlStatus =
  | "compliant"
  | "partially_compliant"
  | "non_compliant"
  | "not_applicable"
  | "not_assessed";

/** Language code for multi-language support. */
export type LanguageCode =
  | "en"
  | "es"
  | "fr"
  | "de"
  | "ja"
  | "zh"
  | "ar"
  | "pt";

/** A single compliance control. */
export interface ComplianceControl {
  id: string;
  framework: Framework;
  family: string;
  title: string;
  description: string;
  status: ControlStatus;
  severity: Severity;
  evidence?: string[];
  gaps?: string[];
  remediation?: string;
  metadata?: Record<string, unknown>;
}

/** A parsed question from the user. */
export interface ParsedQuestion {
  raw: string;
  intent: QueryIntent;
  frameworks: Framework[];
  controlIds: string[];
  keywords: string[];
  language: LanguageCode;
}

/** Maps a question to relevant controls. */
export interface ControlMapping {
  control: ComplianceControl;
  relevance: number;
  matchedKeywords: string[];
}

/** A structured answer returned to the user. */
export interface ComplianceAnswer {
  summary: string;
  details: string;
  controls: ControlMapping[];
  intent: QueryIntent;
  followUpSuggestions: string[];
  language: LanguageCode;
  generatedAt: string;
}

/** Context for a conversation session. */
export interface SessionContext {
  sessionId: string;
  history: ConversationTurn[];
  activeFrameworks: Framework[];
  lastIntent?: QueryIntent;
  createdAt: string;
  updatedAt: string;
}

/** A single turn in a conversation. */
export interface ConversationTurn {
  question: ParsedQuestion;
  answer: ComplianceAnswer;
  timestamp: string;
}

/** Multi-language translation map. */
export interface TranslationMap {
  [key: string]: string;
}

/** Configuration options for the main class. */
export interface NaturalLanguageComplianceOptions {
  defaultLanguage?: LanguageCode;
  defaultFrameworks?: Framework[];
  maxHistory?: number;
  customControls?: ComplianceControl[];
  translations?: Partial<Record<LanguageCode, TranslationMap>>;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const INTENT_KEYWORDS: Record<QueryIntent, string[]> = {
  status: ["status", "current", "how are we doing", "compliance status", "where do we stand"],
  gap: ["gap", "missing", "not compliant", "fail", "failing", "shortcoming", "deficiency"],
  requirement: ["require", "requirement", "must", "need", "shall", "what does", "tell me about"],
  evidence: ["evidence", "proof", "artifact", "documentation", "document", "show me"],
  remediation: ["fix", "remediate", "remediation", "how to", "what should", "improve", "action"],
  comparison: ["compare", "difference", "versus", "vs", "between", "how does"],
  report: ["report", "summary", "overview", "executive", "dashboard", "generate"],
  general: ["what", "explain", "help", "define", "tell me", "describe"],
};

const FRAMEWORK_KEYWORDS: Record<Framework, string[]> = {
  "iso-27001": ["iso 27001", "iso27001", "27001", "isms"],
  soc2: ["soc 2", "soc2", "soc type", "trust services"],
  "nist-csf": ["nist", "nist csf", "cybersecurity framework"],
  "pci-dss": ["pci", "pci dss", "payment card"],
  hipaa: ["hipaa", "health", "phi", "medical"],
  gdpr: ["gdpr", "general data protection", "privacy", "data protection"],
  cis: ["cis", "cis benchmark", "center for internet security"],
  custom: [],
};

const SUPPORTED_LANGUAGES: LanguageCode[] = ["en", "es", "fr", "de", "ja", "zh", "ar", "pt"];

const DEFAULT_TRANSLATIONS: Record<LanguageCode, TranslationMap> = {
  en: {},
  es: {
    "compliance status": "estado de cumplimiento",
    "gap analysis": "análisis de brechas",
    "controls": "controles",
    "evidence": "evidencia",
    "remediation": "remediación",
    "framework": "marco",
    "compliant": "cumplimiento",
    "non_compliant": "no cumplimiento",
    "partially_compliant": "cumplimiento parcial",
  },
  fr: {
    "compliance status": "état de conformité",
    "gap analysis": "analyse des écarts",
    "controls": "contrôles",
    "evidence": "preuve",
    "remediation": "remédiation",
    "framework": "cadre",
    "compliant": "conforme",
    "non_compliant": "non conforme",
    "partially_compliant": "partiellement conforme",
  },
  de: {
    "compliance status": "Compliance-Status",
    "gap analysis": "Lückenanalyse",
    "controls": "Kontrollen",
    "evidence": "Nachweis",
    "remediation": "Abhilfe",
    "framework": "Rahmenwerk",
    "compliant": "konform",
    "non_compliant": "nicht konform",
    "partially_compliant": "teilweise konform",
  },
  ja: {
    "compliance status": "コンプライアンス状況",
    "gap analysis": "ギャップ分析",
    "controls": "管理策",
    "evidence": "エビデンス",
    "remediation": "是正",
    "framework": "フレームワーク",
    "compliant": "準拠",
    "non_compliant": "非準拠",
    "partially_compliant": "一部準拠",
  },
  zh: {
    "compliance status": "合规状态",
    "gap analysis": "差距分析",
    "controls": "控制措施",
    "evidence": "证据",
    "remediation": "整改",
    "framework": "框架",
    "compliant": "合规",
    "non_compliant": "不合规",
    "partially_compliant": "部分合规",
  },
  ar: {
    "compliance status": "حالة الامتثال",
    "gap analysis": "تحليل الفجوات",
    "controls": "ضوابط",
    "evidence": "أدلة",
    "remediation": "العلاج",
    "framework": "إطار",
    "compliant": "ممتثل",
    "non_compliant": "غير ممتثل",
    "partially_compliant": "ممتثل جزئياً",
  },
  pt: {
    "compliance status": "status de conformidade",
    "gap analysis": "análise de lacunas",
    "controls": "controles",
    "evidence": "evidência",
    "remediation": "remediação",
    "framework": "estrutura",
    "compliant": "conforme",
    "non_compliant": "não conforme",
    "partially_compliant": "parcialmente conforme",
  },
};

// ─── Utilities ────────────────────────────────────────────────────────────────

function generateId(): string {
  return `nlc-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function normalise(text: string): string {
  return text.toLowerCase().trim().replace(/[\s]+/g, " ");
}

// ─── QueryParser ──────────────────────────────────────────────────────────────

/**
 * Parses a natural language compliance question into structured data.
 *
 * Extracts intent, frameworks, control IDs, keywords, and language from the
 * raw text of a user's question.
 */
export class QueryParser {
  private readonly frameworkKeywords: Map<string, Framework[]>;

  constructor() {
    this.frameworkKeywords = new Map();
    for (const [fw, keywords] of Object.entries(FRAMEWORK_KEYWORDS)) {
      for (const kw of keywords) {
        const existing = this.frameworkKeywords.get(kw) ?? [];
        existing.push(fw as Framework);
        this.frameworkKeywords.set(kw, existing);
      }
    }
  }

  /**
   * Detect the language of the input text.
   *
   * Simple heuristic: check for script-specific characters or known words.
   */
  detectLanguage(text: string): LanguageCode {
    if (/[\u0600-\u06FF]/.test(text)) return "ar";
    if (/[\u3040-\u309F\u30A0-\u30FF]/.test(text)) return "ja";
    if (/[\u4E00-\u9FFF]/.test(text)) return "zh";
    if (/\b(el|la|los|las|de|del|por|con|que|en)\b/.test(text)) return "es";
    if (/\b(le|la|les|des|de|du|et|est|que|en)\b/.test(text)) return "fr";
    if (/\b(der|die|das|und|ist|den|dem|des)\b/.test(text)) return "de";
    if (/\b(o|a|os|as|do|da|de|em|para|com|que)\b/.test(text)) return "pt";
    return "en";
  }

  /**
   * Extract the intent from the normalised text.
   */
  detectIntent(text: string): QueryIntent {
    const normalised = normalise(text);
    for (const [intent, keywords] of Object.entries(INTENT_KEYWORDS)) {
      if (keywords.some((kw) => normalised.includes(kw))) {
        return intent as QueryIntent;
      }
    }
    return "general";
  }

  /**
   * Extract compliance frameworks referenced in the text.
   */
  detectFrameworks(text: string): Framework[] {
    const normalised = normalise(text);
    const found = new Set<Framework>();
    for (const [kw, frameworks] of this.frameworkKeywords) {
      if (normalised.includes(kw)) {
        for (const fw of frameworks) found.add(fw);
      }
    }
    return Array.from(found);
  }

  /**
   * Extract explicit control IDs (e.g. A.5.1.1, CC6.1, PR.AC-1).
   */
  detectControlIds(text: string): string[] {
    const patterns = [
      /A\.\d+\.\d+/gi,
      /CC\d+\.\d+/gi,
      /PR\.[A-Z]{2,4}-\d+/gi,
      /DE\.[A-Z]{2,4}-\d+/gi,
      /ID\.[A-Z]{2,4}-\d+/gi,
      /SC\.\d+[a-z]?/gi,
      /SI\.\d+[a-z]?/gi,
      /PE\.\d+[a-z]?/gi,
      /\d+\.\d+\.\d+/g,
    ];
    const ids = new Set<string>();
    for (const pattern of patterns) {
      const matches = text.matchAll(pattern);
      for (const match of matches) {
        ids.add(match[0].toUpperCase());
      }
    }
    return Array.from(ids);
  }

  /**
   * Extract significant keywords from the text, stripping stop words.
   */
  extractKeywords(text: string): string[] {
    const stopWords = new Set([
      "a",
      "an",
      "the",
      "is",
      "are",
      "was",
      "were",
      "be",
      "been",
      "being",
      "have",
      "has",
      "had",
      "do",
      "does",
      "did",
      "will",
      "would",
      "could",
      "should",
      "may",
      "might",
      "shall",
      "can",
      "need",
      "must",
      "to",
      "of",
      "in",
      "for",
      "on",
      "with",
      "at",
      "by",
      "from",
      "it",
      "this",
      "that",
      "about",
      "how",
      "what",
      "which",
      "who",
      "where",
      "when",
      "why",
      "tell",
      "me",
      "show",
      "give",
      "our",
      "your",
      "we",
      "do",
      "i",
      "they",
    ]);
    const words = normalise(text)
      .replace(/[^a-z0-9\s.-]/g, " ")
      .split(/\s+/)
      .filter((w) => w.length > 2 && !stopWords.has(w));
    return Array.from(new Set(words));
  }

  /**
   * Parse a raw question string into a structured `ParsedQuestion`.
   */
  parse(raw: string, defaultLanguage: LanguageCode = "en"): ParsedQuestion {
    const language = this.detectLanguage(raw);
    return {
      raw,
      intent: this.detectIntent(raw),
      frameworks: this.detectFrameworks(raw),
      controlIds: this.detectControlIds(raw),
      keywords: this.extractKeywords(raw),
      language,
    };
  }
}

// ─── ControlMapper ────────────────────────────────────────────────────────────

/**
 * Maps a parsed question to relevant compliance controls.
 *
 * Uses keyword and framework matching to rank controls by relevance.
 */
export class ControlMapper {
  private controls: ComplianceControl[];

  constructor(controls: ComplianceControl[] = []) {
    this.controls = controls;
  }

  /** Replace the control set. */
  setControls(controls: ComplianceControl[]): void {
    this.controls = controls;
  }

  /** Add a single control. */
  addControl(control: ComplianceControl): void {
    this.controls.push(control);
  }

  /** Remove a control by ID. */
  removeControl(id: string): void {
    this.controls = this.controls.filter((c) => c.id !== id);
  }

  /** Get all controls. */
  getAllControls(): ComplianceControl[] {
    return [...this.controls];
  }

  /**
   * Compute a relevance score between a control and a parsed question.
   *
   * Returns a number between 0 and 1 where 1 is a perfect match.
   */
  scoreControl(control: ComplianceControl, question: ParsedQuestion): number {
    let score = 0;

    // Framework match — strong signal
    if (question.frameworks.length > 0) {
      if (question.frameworks.includes(control.framework)) {
        score += 0.4;
      } else {
        return 0;
      }
    }

    // Direct control ID match
    if (question.controlIds.length > 0) {
      if (question.controlIds.includes(control.id)) {
        return 1;
      }
    }

    // Keyword overlap
    const controlText = normalise(
      `${control.title} ${control.description} ${control.family} ${control.id}`
    );
    let matchedKeywords = 0;
    for (const kw of question.keywords) {
      if (controlText.includes(kw)) {
        matchedKeywords++;
      }
    }
    if (question.keywords.length > 0) {
      score += (matchedKeywords / question.keywords.length) * 0.5;
    }

    // Intent-specific boosts
    if (question.intent === "status" || question.intent === "gap") {
      if (control.status === "non_compliant") score += 0.1;
      if (control.severity === "critical" || control.severity === "high") score += 0.05;
    }
    if (question.intent === "evidence") {
      if (control.evidence && control.evidence.length > 0) score += 0.1;
    }
    if (question.intent === "remediation") {
      if (control.remediation) score += 0.1;
    }

    return Math.min(score, 1);
  }

  /**
   * Map a parsed question to relevant controls, ranked by relevance.
   */
  map(question: ParsedQuestion, minRelevance = 0.1): ControlMapping[] {
    const mappings: ControlMapping[] = [];

    for (const control of this.controls) {
      const relevance = this.scoreControl(control, question);
      if (relevance >= minRelevance) {
        const controlText = normalise(
          `${control.title} ${control.description} ${control.family}`
        );
        const matchedKeywords = question.keywords.filter((kw) =>
          controlText.includes(kw)
        );
        mappings.push({ control, relevance, matchedKeywords });
      }
    }

    mappings.sort((a, b) => b.relevance - a.relevance);
    return mappings;
  }

  /**
   * Find a specific control by ID.
   */
  findById(id: string): ComplianceControl | undefined {
    return this.controls.find((c) => c.id === id);
  }

  /**
   * Get controls filtered by framework.
   */
  getByFramework(framework: Framework): ComplianceControl[] {
    return this.controls.filter((c) => c.framework === framework);
  }

  /**
   * Get controls filtered by status.
   */
  getByStatus(status: ControlStatus): ComplianceControl[] {
    return this.controls.filter((c) => c.status === status);
  }

  /**
   * Get a compliance summary for a given set of frameworks.
   */
  getSummary(frameworks?: Framework[]): {
    total: number;
    compliant: number;
    partiallyCompliant: number;
    nonCompliant: number;
    notApplicable: number;
    notAssessed: number;
  } {
    const subset = frameworks
      ? this.controls.filter((c) => frameworks.includes(c.framework))
      : this.controls;

    return {
      total: subset.length,
      compliant: subset.filter((c) => c.status === "compliant").length,
      partiallyCompliant: subset.filter((c) => c.status === "partially_compliant")
        .length,
      nonCompliant: subset.filter((c) => c.status === "non_compliant").length,
      notApplicable: subset.filter((c) => c.status === "not_applicable").length,
      notAssessed: subset.filter((c) => c.status === "not_assessed").length,
    };
  }
}

// ─── AnswerGenerator ──────────────────────────────────────────────────────────

/**
 * Generates structured natural-language answers from compliance data.
 */
export class AnswerGenerator {
  private translations: Record<LanguageCode, TranslationMap>;

  constructor(
    translations: Partial<Record<LanguageCode, TranslationMap>> = {}
  ) {
    this.translations = { ...DEFAULT_TRANSLATIONS };
    for (const [lang, map] of Object.entries(translations)) {
      if (map) {
        this.translations[lang as LanguageCode] = {
          ...this.translations[lang as LanguageCode],
          ...map,
        };
      }
    }
  }

  /**
   * Return a translated label if a translation exists, otherwise the English
   * label.
   */
  private t(key: string, language: LanguageCode): string {
    return this.translations[language]?.[key] ?? this.translations.en[key] ?? key;
  }

  private statusLabel(status: ControlStatus, language: LanguageCode): string {
    const key = status.replace(/ /g, "_");
    return this.t(key, language);
  }

  /**
   * Generate a follow-up question based on the current answer.
   */
  private buildFollowUps(
    intent: QueryIntent,
    mappings: ControlMapping[],
    language: LanguageCode
  ): string[] {
    const suggestions: string[] = [];
    const hasGaps = mappings.some(
      (m) =>
        m.control.status === "non_compliant" ||
        m.control.status === "partially_compliant"
    );

    if (intent !== "status") {
      suggestions.push(
        language === "en"
          ? "What is our current compliance status?"
          : this.t("compliance status", language) + "?"
      );
    }
    if (hasGaps && intent !== "remediation") {
      suggestions.push(
        language === "en"
          ? "How can we remediate these gaps?"
          : this.t("remediation", language) + "?"
      );
    }
    if (intent !== "evidence" && mappings.length > 0) {
      suggestions.push(
        language === "en"
          ? "Show me the evidence for these controls."
          : this.t("evidence", language) + "?"
      );
    }
    if (intent !== "report") {
      suggestions.push(
        language === "en"
          ? "Generate a compliance report."
          : `Generate ${this.t("compliance status", language)} report.`
      );
    }

    return suggestions.slice(0, 3);
  }

  /**
   * Generate a structured answer for the given question and control mappings.
   */
  generate(
    question: ParsedQuestion,
    mappings: ControlMapping[]
  ): ComplianceAnswer {
    const lang = question.language;

    if (mappings.length === 0) {
      return {
        summary: "No matching controls found for your question.",
        details:
          "Try rephrasing your question, specifying a framework (e.g. ISO 27001, SOC 2), or providing a control ID.",
        controls: [],
        intent: question.intent,
        followUpSuggestions: [
          "What frameworks are supported?",
          "Show me all non-compliant controls.",
          "What is our compliance status for ISO 27001?",
        ],
        language: lang,
        generatedAt: new Date().toISOString(),
      };
    }

    const top = mappings.slice(0, 5);
    let summary = "";
    let details = "";

    switch (question.intent) {
      case "status": {
        const compliant = mappings.filter(
          (m) => m.control.status === "compliant"
        ).length;
        const total = mappings.length;
        summary = `${compliant} of ${total} matched controls are compliant.`;
        details = top
          .map(
            (m) =>
              `- ${m.control.id} (${m.control.title}): ${this.statusLabel(m.control.status, lang)}`
          )
          .join("\n");
        break;
      }
      case "gap": {
        const gaps = mappings.filter(
          (m) =>
            m.control.status === "non_compliant" ||
            m.control.status === "partially_compliant"
        );
        summary = `${gaps.length} gap(s) identified among ${mappings.length} matched controls.`;
        details = gaps
          .map(
            (m) =>
              `- ${m.control.id} (${m.control.title}): ${this.statusLabel(m.control.status, lang)}${
                m.control.gaps?.length
                  ? ` — Gaps: ${m.control.gaps.join("; ")}`
                  : ""
              }`
          )
          .join("\n");
        break;
      }
      case "requirement": {
        summary = `Found ${mappings.length} matching requirement(s).`;
        details = top
          .map(
            (m) =>
              `- ${m.control.id} (${m.control.title}): ${m.control.description}`
          )
          .join("\n");
        break;
      }
      case "evidence": {
        const withEvidence = mappings.filter(
          (m) => m.control.evidence && m.control.evidence.length > 0
        );
        summary = `${withEvidence.length} control(s) have evidence on file.`;
        details = withEvidence
          .map(
            (m) =>
              `- ${m.control.id}: ${m.control.evidence?.join(", ")}`
          )
          .join("\n");
        break;
      }
      case "remediation": {
        const needRemediation = mappings.filter(
          (m) => m.control.remediation
        );
        summary = `${needRemediation.length} control(s) have remediation guidance.`;
        details = needRemediation
          .map(
            (m) =>
              `- ${m.control.id} (${m.control.title}): ${m.control.remediation}`
          )
          .join("\n");
        break;
      }
      case "comparison": {
        summary = `Comparing ${mappings.length} matched controls.`;
        details = top
          .map(
            (m) =>
              `- ${m.control.id} [${m.control.framework}]: ${m.control.title} — ${this.statusLabel(m.control.status, lang)}`
          )
          .join("\n");
        break;
      }
      case "report": {
        const summary_ = this.computeReportSummary(mappings, lang);
        summary = summary_.summary;
        details = summary_.details;
        break;
      }
      default: {
        summary = `Found ${mappings.length} related control(s).`;
        details = top
          .map(
            (m) =>
              `- ${m.control.id} (${m.control.framework}): ${m.control.title} — ${this.statusLabel(m.control.status, lang)}`
          )
          .join("\n");
      }
    }

    return {
      summary,
      details,
      controls: top,
      intent: question.intent,
      followUpSuggestions: this.buildFollowUps(question.intent, mappings, lang),
      language: lang,
      generatedAt: new Date().toISOString(),
    };
  }

  private computeReportSummary(
    mappings: ControlMapping[],
    language: LanguageCode
  ): { summary: string; details: string } {
    const total = mappings.length;
    const compliant = mappings.filter(
      (m) => m.control.status === "compliant"
    ).length;
    const nonCompliant = mappings.filter(
      (m) => m.control.status === "non_compliant"
    ).length;
    const partial = mappings.filter(
      (m) => m.control.status === "partially_compliant"
    ).length;
    const pct = total > 0 ? Math.round((compliant / total) * 100) : 0;

    const frameworks = [...new Set(mappings.map((m) => m.control.framework))];

    const summary = `Compliance report: ${pct}% compliant across ${frameworks.join(", ")} (${compliant}/${total} controls).`;
    const details = [
      `Total matched controls: ${total}`,
      `Compliant: ${compliant}`,
      `Partially compliant: ${partial}`,
      `Non-compliant: ${nonCompliant}`,
      "",
      "Top concerns:",
      ...mappings
        .filter(
          (m) =>
            m.control.status === "non_compliant" ||
            m.control.status === "partially_compliant"
        )
        .slice(0, 5)
        .map(
          (m) =>
            `- ${m.control.id} (${m.control.title}): ${this.statusLabel(m.control.status, language)}`
        ),
    ].join("\n");

    return { summary, details };
  }
}

// ─── ContextManager ───────────────────────────────────────────────────────────

/**
 * Manages conversation context across multiple queries.
 *
 * Tracks session history, maintains active frameworks, and provides
 * conversation-aware follow-up support.
 */
export class ContextManager {
  private sessions: Map<string, SessionContext>;
  private maxHistory: number;

  constructor(maxHistory: number = 50) {
    this.sessions = new Map();
    this.maxHistory = maxHistory;
  }

  /**
   * Create or retrieve a session context.
   */
  getSession(sessionId: string): SessionContext {
    let session = this.sessions.get(sessionId);
    if (!session) {
      session = {
        sessionId,
        history: [],
        activeFrameworks: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      this.sessions.set(sessionId, session);
    }
    return session;
  }

  /**
   * Record a question-answer turn in the session.
   */
  recordTurn(
    sessionId: string,
    question: ParsedQuestion,
    answer: ComplianceAnswer
  ): void {
    const session = this.getSession(sessionId);

    session.history.push({
      question,
      answer,
      timestamp: new Date().toISOString(),
    });

    // Enforce max history size
    if (session.history.length > this.maxHistory) {
      session.history = session.history.slice(-this.maxHistory);
    }

    // Merge detected frameworks into active set
    for (const fw of question.frameworks) {
      if (!session.activeFrameworks.includes(fw)) {
        session.activeFrameworks.push(fw);
      }
    }

    session.lastIntent = question.intent;
    session.updatedAt = new Date().toISOString();
  }

  /**
   * Get the last N turns from a session.
   */
  getRecentHistory(sessionId: string, count: number = 5): ConversationTurn[] {
    const session = this.sessions.get(sessionId);
    if (!session) return [];
    return session.history.slice(-count);
  }

  /**
   * Detect if a follow-up question is referencing prior context.
   */
  isFollowUp(question: ParsedQuestion, sessionId: string): boolean {
    const session = this.sessions.get(sessionId);
    if (!session || session.history.length === 0) return false;

    // Heuristic: short questions with pronouns or references to prior topics
    const words = question.raw.trim().split(/\s+/);
    if (words.length <= 5) return true;

    const followUpIndicators = [
      "those",
      "them",
      "these",
      "that",
      "it",
      "same",
      "also",
      "more",
      "others",
      "another",
    ];
    const lower = normalise(question.raw);
    return followUpIndicators.some((indicator) => lower.includes(indicator));
  }

  /**
   * Merge context from the previous turn into the current question to aid
   * interpretation.
   */
  enrichQuestion(question: ParsedQuestion, sessionId: string): ParsedQuestion {
    const session = this.sessions.get(sessionId);
    if (!session || session.history.length === 0) return question;

    const lastTurn = session.history[session.history.length - 1];
    const enriched = { ...question };

    // Inherit frameworks from previous turn if none detected
    if (enriched.frameworks.length === 0) {
      enriched.frameworks = [...lastTurn.question.frameworks];
    }

    // Inherit keywords when question is very short
    if (enriched.keywords.length < 2 && lastTurn.question.keywords.length > 0) {
      enriched.keywords = [
        ...enriched.keywords,
        ...lastTurn.question.keywords.slice(0, 3),
      ];
    }

    return enriched;
  }

  /**
   * Clear a session's history.
   */
  clearSession(sessionId: string): void {
    this.sessions.delete(sessionId);
  }

  /**
   * Get all active session IDs.
   */
  listSessions(): string[] {
    return Array.from(this.sessions.keys());
  }
}

// ─── NaturalLanguageCompliance ────────────────────────────────────────────────

/**
 * Main entry point for natural-language compliance querying.
 *
 * Composes `QueryParser`, `ControlMapper`, `AnswerGenerator`, and
 * `ContextManager` to process plain-English compliance questions and return
 * structured answers.
 *
 * @example
 * ```ts
 * const nlc = new NaturalLanguageCompliance({
 *   defaultFrameworks: ["iso-27001", "soc2"],
 * });
 *
 * nlc.addControl({
 *   id: "A.5.1.1",
 *   framework: "iso-27001",
 *   family: "A.5",
 *   title: "Policies for information security",
 *   description: "Information security policy and topic-specific policies shall be defined...",
 *   status: "compliant",
 *   severity: "high",
 * });
 *
 * const answer = nlc.ask("Are we compliant with ISO 27001?", "session-1");
 * console.log(answer.summary);
 * ```
 */
export class NaturalLanguageCompliance {
  readonly parser: QueryParser;
  readonly mapper: ControlMapper;
  readonly generator: AnswerGenerator;
  readonly context: ContextManager;

  private defaultLanguage: LanguageCode;
  private defaultFrameworks: Framework[];

  constructor(options: NaturalLanguageComplianceOptions = {}) {
    this.defaultLanguage = options.defaultLanguage ?? "en";
    this.defaultFrameworks = options.defaultFrameworks ?? [];
    this.parser = new QueryParser();
    this.mapper = new ControlMapper(options.customControls ?? []);
    this.generator = new AnswerGenerator(options.translations);
    this.context = new ContextManager(options.maxHistory);
  }

  /**
   * Add a compliance control to the knowledge base.
   */
  addControl(control: ComplianceControl): void {
    this.mapper.addControl(control);
  }

  /**
   * Bulk-load compliance controls.
   */
  loadControls(controls: ComplianceControl[]): void {
    for (const c of controls) this.mapper.addControl(c);
  }

  /**
   * Replace all controls.
   */
  setControls(controls: ComplianceControl[]): void {
    this.mapper.setControls(controls);
  }

  /**
   * Ask a compliance question in natural language.
   *
   * @param question - The plain-English question.
   * @param sessionId - Optional session ID for context tracking.
   * @returns A structured compliance answer.
   */
  ask(question: string, sessionId?: string): ComplianceAnswer {
    // 1. Parse
    const parsed = this.parser.parse(question, this.defaultLanguage);

    // 2. Enrich with context
    let finalQuestion = parsed;
    if (sessionId) {
      finalQuestion = this.context.enrichQuestion(parsed, sessionId);
      // If the user didn't specify a framework but defaults exist, use them
      if (finalQuestion.frameworks.length === 0 && this.defaultFrameworks.length > 0) {
        finalQuestion.frameworks = [...this.defaultFrameworks];
      }
    } else if (finalQuestion.frameworks.length === 0 && this.defaultFrameworks.length > 0) {
      finalQuestion.frameworks = [...this.defaultFrameworks];
    }

    // 3. Map to controls
    const mappings = this.mapper.map(finalQuestion);

    // 4. Generate answer
    const answer = this.generator.generate(finalQuestion, mappings);

    // 5. Record in context
    if (sessionId) {
      this.context.recordTurn(sessionId, finalQuestion, answer);
    }

    return answer;
  }

  /**
   * Ask a follow-up question that relies on prior session context.
   */
  followUp(question: string, sessionId: string): ComplianceAnswer {
    const isFollowUp = this.context.isFollowUp(
      this.parser.parse(question, this.defaultLanguage),
      sessionId
    );

    if (!isFollowUp) {
      // Treat as a fresh question
      return this.ask(question, sessionId);
    }

    // Parse, enrich from context, then proceed normally
    const parsed = this.parser.parse(question, this.defaultLanguage);
    const enriched = this.context.enrichQuestion(parsed, sessionId);

    if (enriched.frameworks.length === 0 && this.defaultFrameworks.length > 0) {
      enriched.frameworks = [...this.defaultFrameworks];
    }

    const mappings = this.mapper.map(enriched);
    const answer = this.generator.generate(enriched, mappings);
    this.context.recordTurn(sessionId, enriched, answer);

    return answer;
  }

  /**
   * Generate a compliance report for the given (or active) frameworks.
   */
  generateReport(
    frameworks?: Framework[],
    sessionId?: string
  ): ComplianceAnswer {
    const fws = frameworks ?? this.defaultFrameworks;
    const questionText =
      fws.length > 0
        ? `Generate a compliance report for ${fws.join(", ")}.`
        : "Generate a compliance report for all frameworks.";
    return this.ask(questionText, sessionId);
  }

  /**
   * Get a summary of compliance status.
   */
  getComplianceSummary(frameworks?: Framework[]): {
    total: number;
    compliant: number;
    partiallyCompliant: number;
    nonCompliant: number;
    notApplicable: number;
    notAssessed: number;
  } {
    return this.mapper.getSummary(frameworks ?? this.defaultFrameworks);
  }

  /**
   * Get all controls matching a framework.
   */
  getControlsByFramework(framework: Framework): ComplianceControl[] {
    return this.mapper.getByFramework(framework);
  }

  /**
   * Get all non-compliant controls.
   */
  getNonCompliantControls(): ComplianceControl[] {
    return this.mapper.getByStatus("non_compliant");
  }

  /**
   * Get a control by ID.
   */
  getControl(id: string): ComplianceControl | undefined {
    return this.mapper.findById(id);
  }
}
