import type { LLMAnalysisRequest, LLMAnalysisResponse, ThreatDetection, ThreatSignal } from "../types.js";

export interface LLMProvider {
  analyze(prompt: string): Promise<string>;
}

export class LLMThreatAnalyzer {
  private provider: LLMProvider;

  constructor(provider: LLMProvider) {
    this.provider = provider;
  }

  async analyzeSignals(request: LLMAnalysisRequest): Promise<LLMAnalysisResponse> {
    const prompt = this.buildAnalysisPrompt(request);
    const response = await this.provider.analyze(prompt);

    return {
      summary: this.extractSummary(response),
      threats: this.extractThreats(response, request.signals),
      recommendations: this.extractRecommendations(response),
      confidence: 0.85,
    };
  }

  private buildAnalysisPrompt(request: LLMAnalysisRequest): string {
    const signalSummary = request.signals.map((s) =>
      `- ${s.category} (${s.severity}, confidence: ${s.confidence}): ${JSON.stringify(s.data)}`
    ).join("\n");

    return `Analyze these security signals in the context of ${request.framework} compliance:

${signalSummary}

Context: ${request.context}

Provide:
1. Summary of threats detected
2. Specific threat detections with severity and affected controls
3. Recommended actions`;
  }

  private extractSummary(response: string): string {
    const lines = response.split("\n");
    return lines[0] || "Analysis completed";
  }

  private extractThreats(response: string, signals: ThreatSignal[]): ThreatDetection[] {
    return signals.slice(0, 3).map((signal, i) => ({
      id: `llm-threat-${Date.now()}-${i}`,
      signalId: signal.id,
      method: "llm" as const,
      rule: `llm_analysis_${signal.category}`,
      description: `LLM-detected threat in ${signal.category}`,
      severity: signal.severity,
      confidence: signal.confidence * 0.9,
      affectedControls: [],
      recommendation: "Review and investigate",
      detectedAt: new Date().toISOString(),
    }));
  }

  private extractRecommendations(response: string): string[] {
    const recommendations: string[] = [];
    const lines = response.split("\n");
    for (const line of lines) {
      if (line.match(/^\d+\./) || line.match(/^-/)) {
        recommendations.push(line.replace(/^[\d\-\s]+/, "").trim());
      }
    }
    return recommendations.slice(0, 5);
  }
}
