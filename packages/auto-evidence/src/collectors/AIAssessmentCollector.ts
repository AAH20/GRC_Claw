import { createHash, randomUUID } from "node:crypto";
import type { CollectedEvidence } from "../types.js";

// ─── AI-Native Control Assessment (#3) ────────────────────────────────────────
// Calls Claude claude-sonnet-4-6 to assess whether a compliance control is
// satisfied given raw evidence. Returns decision + reasoning chain + confidence.
// No human reviewer required — 10x faster than manual GRC assessment.

export interface ControlDefinition {
  controlId: string;
  framework: string;
  title: string;
  description: string;
  testingProcedure?: string;
  expectedEvidence?: string[];
}

export interface AIAssessmentResult {
  controlId: string;
  framework: string;
  decision: "pass" | "fail" | "partial" | "insufficient_evidence";
  confidence: number;
  reasoning: string;
  gaps: string[];
  remediationSteps: string[];
  evidence: CollectedEvidence;
  assessedAt: string;
  modelId: string;
}

interface ClaudeMessage {
  role: "user" | "assistant";
  content: string;
}

interface ClaudeResponse {
  content: Array<{ type: string; text: string }>;
  model: string;
  usage: { input_tokens: number; output_tokens: number };
}

function buildSystemPrompt(): string {
  return `You are a certified ISO 27001 Lead Auditor and SOC 2 assessor with 15 years of experience.
Your task: assess whether a GRC compliance control is satisfied based on provided evidence.

STRICT OUTPUT FORMAT (respond ONLY with valid JSON, no markdown fences):
{
  "decision": "pass" | "fail" | "partial" | "insufficient_evidence",
  "confidence": 0.0-1.0,
  "reasoning": "1-3 sentence explanation of your decision",
  "gaps": ["gap1", "gap2"],
  "remediationSteps": ["step1", "step2"]
}

Rules:
- "pass": evidence clearly demonstrates the control is implemented and effective
- "partial": evidence shows partial implementation — gaps exist
- "fail": evidence shows the control is not implemented or ineffective
- "insufficient_evidence": cannot assess — not enough information provided
- confidence must be between 0.0 and 1.0
- gaps and remediationSteps should be empty arrays for "pass"
- Be strict but fair — assume good faith when evidence is ambiguous`;
}

function buildUserPrompt(control: ControlDefinition, evidenceSnippets: string[]): string {
  const evidenceBlock = evidenceSnippets.length > 0
    ? evidenceSnippets.map((e, i) => `Evidence ${i + 1}:\n${e.slice(0, 800)}`).join("\n\n")
    : "No evidence provided.";

  return `CONTROL TO ASSESS:
Framework: ${control.framework}
Control ID: ${control.controlId}
Title: ${control.title}
Description: ${control.description}
${control.testingProcedure ? `Testing Procedure: ${control.testingProcedure}` : ""}
${control.expectedEvidence ? `Expected Evidence Types: ${control.expectedEvidence.join(", ")}` : ""}

EVIDENCE PROVIDED:
${evidenceBlock}

Assess this control and respond with JSON only.`;
}

async function callClaude(messages: ClaudeMessage[], apiKey: string): Promise<string> {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-6",
      max_tokens: 512,
      system: buildSystemPrompt(),
      messages,
    }),
    signal: AbortSignal.timeout(30_000),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Claude API error ${res.status}: ${err.slice(0, 200)}`);
  }

  const data = await res.json() as ClaudeResponse;
  return data.content[0]?.text ?? "";
}

export class AIAssessmentCollector {
  private apiKey: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey ?? process.env.ANTHROPIC_API_KEY ?? "";
    if (!this.apiKey) throw new Error("ANTHROPIC_API_KEY not set — AIAssessmentCollector requires Claude API access");
  }

  async assessControl(
    control: ControlDefinition,
    evidence: CollectedEvidence[],
  ): Promise<AIAssessmentResult> {
    const evidenceSnippets = evidence.map((e) => {
      const parsed = (() => {
        try { return JSON.parse(e.content) as Record<string, unknown>; }
        catch { return e.content; }
      })();
      return `[${e.name}] ${typeof parsed === "object" ? JSON.stringify(parsed, null, 2) : String(parsed)}`;
    });

    const userPrompt = buildUserPrompt(control, evidenceSnippets);
    const raw = await callClaude([{ role: "user", content: userPrompt }], this.apiKey);

    let parsed: {
      decision: "pass" | "fail" | "partial" | "insufficient_evidence";
      confidence: number;
      reasoning: string;
      gaps: string[];
      remediationSteps: string[];
    };

    try {
      const jsonText = raw.trim().replace(/^```json?\s*/i, "").replace(/```\s*$/, "");
      parsed = JSON.parse(jsonText) as typeof parsed;
    } catch {
      parsed = {
        decision: "insufficient_evidence",
        confidence: 0.1,
        reasoning: `AI response parsing failed. Raw: ${raw.slice(0, 200)}`,
        gaps: ["AI assessment unavailable — raw response not parseable"],
        remediationSteps: [],
      };
    }

    const assessmentPayload = {
      controlId: control.controlId,
      framework: control.framework,
      decision: parsed.decision,
      confidence: parsed.confidence,
      reasoning: parsed.reasoning,
      gaps: parsed.gaps,
      remediationSteps: parsed.remediationSteps,
      evidenceCount: evidence.length,
      assessedAt: new Date().toISOString(),
    };

    const contentStr = JSON.stringify(assessmentPayload);
    const collectedEvidence: CollectedEvidence = {
      id: randomUUID(),
      collectorId: randomUUID(),
      type: "configuration",
      name: `AI Assessment — ${control.framework}/${control.controlId}`,
      content: contentStr,
      sha256: createHash("sha256").update(contentStr).digest("hex"),
      collectedAt: new Date().toISOString(),
      metadata: {
        collector: "AIAssessmentCollector",
        version: "3.0",
        model: "claude-sonnet-4-6",
        framework: control.framework,
        controlId: control.controlId,
      },
    };

    return {
      ...assessmentPayload,
      evidence: collectedEvidence,
      modelId: "claude-sonnet-4-6",
    };
  }

  async assessBatch(
    controls: ControlDefinition[],
    evidenceMap: Map<string, CollectedEvidence[]>,
    concurrency = 3,
  ): Promise<AIAssessmentResult[]> {
    const results: AIAssessmentResult[] = [];
    for (let i = 0; i < controls.length; i += concurrency) {
      const batch = controls.slice(i, i + concurrency);
      const batchResults = await Promise.all(
        batch.map((c) => this.assessControl(c, evidenceMap.get(c.controlId) ?? []).catch((err) => ({
          controlId: c.controlId,
          framework: c.framework,
          decision: "insufficient_evidence" as const,
          confidence: 0,
          reasoning: `Assessment failed: ${err instanceof Error ? err.message : String(err)}`,
          gaps: [],
          remediationSteps: [],
          evidence: {
            id: randomUUID(), collectorId: randomUUID(), type: "configuration" as const,
            name: `Failed: ${c.controlId}`, content: "{}", sha256: "",
            collectedAt: new Date().toISOString(), metadata: {},
          },
          assessedAt: new Date().toISOString(),
          modelId: "claude-sonnet-4-6",
        })))
      );
      results.push(...batchResults);
    }
    return results;
  }
}
