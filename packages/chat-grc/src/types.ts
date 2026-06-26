export type MessageRole = 'user' | 'assistant' | 'system';

export type IntentType =
  | 'query_controls'
  | 'query_evidence'
  | 'query_risks'
  | 'query_posture'
  | 'query_frameworks'
  | 'generate_report'
  | 'check_compliance'
  | 'help';

export interface ChatMessage {
  role: MessageRole;
  content: string;
  timestamp: string;
}

export interface ChatContext {
  frameworks: string[];
  controls: string[];
  evidence: string[];
  risks: string[];
  riskRegister?: {
    topRisks(count?: number): Array<{
      scenario: { id: string; name: string };
      riskScore: number;
      riskLevel: 'critical' | 'high' | 'medium' | 'low' | 'negligible';
      fairModel: { annualizedLossExpectancy: number };
    }>;
    portfolioMetrics(): {
      totalALE: number;
      meanRiskScore: number;
      criticalCount: number;
      highCount: number;
      scenarioCount: number;
    };
  };
  evidenceStore?: {
    listByControl(controlId: string): Array<{ id: string; controlId: string }>;
  };
  frameworkControls?: Record<string, Array<{ id: string; controlCode: string; title: string; domain?: string }>>;
}

export interface ChatResponse {
  message: string;
  data?: unknown;
  suggestions?: string[];
}

export interface IntentMatch {
  intent: IntentType;
  confidence: number;
  entities: Record<string, string>;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  context: ChatContext;
  createdAt: string;
  updatedAt: string;
}

export interface CompliancePosture {
  framework: string;
  totalControls: number;
  implemented: number;
  inProgress: number;
  notStarted: number;
  failed: number;
  scorePercent: number;
}

export interface ReportData {
  type: 'board' | 'compliance' | 'gap' | 'risk';
  framework?: string;
  generatedAt: string;
  summary: string;
  sections: ReportSection[];
}

export interface ReportSection {
  title: string;
  content: string;
  data?: unknown;
}
