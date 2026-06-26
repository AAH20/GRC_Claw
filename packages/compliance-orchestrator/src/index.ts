import { RegulationASTCompiler } from './compiler/RegulationASTCompiler.js';
import { NeuroSymbolicReasoner } from './reasoner/NeuroSymbolicReasoner.js';
import { UnifiedComplianceGraph } from './graph/UnifiedComplianceGraph.js';
import type {
  FrameworkCode,
  ComplianceState,
  CompliancePlan,
  ComplianceAudit,
  RegulationAST,
  ControlStatus,
  DriftEvent,
  RiskAssessment,
} from './types.js';

export * from './types.js';
export { RegulationASTCompiler, getEvidenceDeduplicationMap } from './compiler/RegulationASTCompiler.js';
export { NeuroSymbolicReasoner } from './reasoner/NeuroSymbolicReasoner.js';
export { UnifiedComplianceGraph } from './graph/UnifiedComplianceGraph.js';
export type { ReasoningResult, ReasoningContext, ReasoningContext as NeuroSymbolicContext } from './reasoner/NeuroSymbolicReasoner.js';
export type { GraphNode, GraphEdge, AttackPath, BlastRadius, CompliancePosture, Recommendation } from './graph/UnifiedComplianceGraph.js';

export interface ComplianceOrchestratorConfig {
  orgId: string;
  enabledFrameworks: FrameworkCode[];
  riskTolerance: 'low' | 'medium' | 'high';
  autoRemediate: boolean;
  continuousScanInterval: number;
}

export interface ContinuousComplianceResult {
  orgId: string;
  timestamp: string;
  states: ComplianceState[];
  drift: DriftEvent[];
  risks: RiskAssessment[];
  graphHash: string;
  overallScore: number;
}

export class ComplianceSuperOrchestrator {
  private compiler: RegulationASTCompiler;
  private reasoner: NeuroSymbolicReasoner;
  private graph: UnifiedComplianceGraph;
  private config: ComplianceOrchestratorConfig;
  private states: Map<FrameworkCode, ComplianceState> = new Map();

  constructor(config: ComplianceOrchestratorConfig) {
    this.config = config;
    this.compiler = new RegulationASTCompiler();
    const asts = this.compiler.getAllASTs();
    this.reasoner = new NeuroSymbolicReasoner(new Map(asts.map((a) => [a.framework, a])));
    this.graph = new UnifiedComplianceGraph(asts);
  }

  async continuousComplianceLoop(
    reasoningContexts: Map<FrameworkCode, import('./reasoner/NeuroSymbolicReasoner.js').ReasoningContext>
  ): Promise<ContinuousComplianceResult> {
    const states: ComplianceState[] = [];
    const allDrift: DriftEvent[] = [];
    const allRisks: RiskAssessment[] = [];

    for (const [framework, context] of reasoningContexts) {
      const previousState = this.states.get(framework);
      const enrichedContext = { ...context, previousState };
      const state = await this.reasoner.reason(enrichedContext);
      states.push(state);
      allDrift.push(...state.drift);
      allRisks.push(...state.risks);
      this.states.set(framework, state);
    }

    const compliant = states.reduce(
      (acc, s) => acc + s.controlStatuses.filter((c) => c.status === 'compliant').length,
      0
    );
    const total = states.reduce((acc, s) => acc + s.controlStatuses.length, 0);
    const overallScore = total > 0 ? (compliant / total) * 100 : 0;

    return {
      orgId: this.config.orgId,
      timestamp: new Date().toISOString(),
      states,
      drift: allDrift,
      risks: allRisks,
      graphHash: this.graph.getGraphHash(),
      overallScore,
    };
  }

  compileNaturalLanguage(framework: FrameworkCode, text: string): string {
    const control = this.compiler.compileNaturalLanguage(framework, text);
    return control.id;
  }

  async synthesizePlan(
    framework: FrameworkCode,
    currentState: ComplianceState,
    targetScore: number
  ): Promise<CompliancePlan> {
    const nonCompliant = currentState.controlStatuses.filter((s) => s.status !== 'compliant');
    const actions = nonCompliant.map((nc, idx) => ({
      id: `action-${idx}-${Date.now()}`,
      controlId: nc.controlId,
      action: 'remediate' as const,
      resource: nc.controlId,
      evidenceRequired: ['scan', 'config'],
      sla: '4h',
    }));

    const estimatedCost = actions.length * 500;

    return {
      id: `plan-${framework}-${Date.now()}`,
      orgId: this.config.orgId,
      framework,
      createdAt: new Date().toISOString(),
      actions,
      estimatedCost,
      estimatedDuration: `${Math.ceil(actions.length / 4)} days`,
    };
  }

  async executeAudit(
    framework: FrameworkCode,
    reasoningContext: import('./reasoner/NeuroSymbolicReasoner.js').ReasoningContext
  ): Promise<ComplianceAudit> {
    const state = await this.reasoner.reason(reasoningContext);
    const controls = state.controlStatuses.map((cs) => ({
      controlId: cs.controlId,
      status: cs.status === 'compliant' ? 'pass' as const : 'fail' as const,
      evidence: [],
      issues: cs.issues,
      duration: 0,
    }));

    const passed = controls.filter((c) => c.status === 'pass').length;
    const failed = controls.filter((c) => c.status === 'fail').length;

    return {
      id: `audit-${framework}-${Date.now()}`,
      orgId: this.config.orgId,
      framework,
      startedAt: new Date().toISOString(),
      completedAt: new Date().toISOString(),
      controls,
      summary: {
        totalControls: controls.length,
        passed,
        failed,
        skipped: 0,
        errors: 0,
        complianceScore: controls.length > 0 ? (passed / controls.length) * 100 : 0,
        criticalFindings: failed,
        highFindings: 0,
      },
    };
  }

  findCrosswalk(framework: FrameworkCode, controlCode: string): CrosswalkEntry[] {
    return this.compiler.findEquivalent(framework, controlCode);
  }

  getState(framework: FrameworkCode): ComplianceState | undefined {
    return this.states.get(framework);
  }

  getGraph(): UnifiedComplianceGraph {
    return this.graph;
  }

  getCompiler(): RegulationASTCompiler {
    return this.compiler;
  }

  getReasoner(): NeuroSymbolicReasoner {
    return this.reasoner;
  }
}

type CrosswalkEntry = import('./types.js').CrosswalkEntry;
