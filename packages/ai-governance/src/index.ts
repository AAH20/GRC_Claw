/**
 * AIGovernance - EU AI Act compliance and AI risk management
 * 
 * Provides comprehensive AI governance capabilities including:
 * - AI system registration and inventory
 * - Risk classification per EU AI Act
 * - Model risk scoring
 * - Bias detection and monitoring
 * - Transparency and explainability tracking
 * - Regulatory compliance mapping
 */

export interface AISystem {
  id: string;
  name: string;
  description: string;
  owner: string;
  department: string;
  useCase: string;
  riskClass: 'unacceptable' | 'high' | 'limited' | 'minimal';
  status: 'registered' | 'assessed' | 'approved' | 'deployed' | 'retired';
  registrationDate: Date;
  lastAssessment?: Date;
  nextAssessment?: Date;
  models: AIModel[];
  documentation: AIDocumentation;
}

export interface AIModel {
  id: string;
  name: string;
  type: 'llm' | 'ml' | 'dl' | 'rule_based' | 'hybrid';
  version: string;
  provider: string;
  trainingData?: TrainingData;
  performanceMetrics: ModelMetrics;
  biasMetrics?: BiasMetrics;
  explainabilityScore?: number; // 0-100
  lastUpdated: Date;
}

export interface TrainingData {
  source: string;
  size: string;
  dateRange: { start: Date; end: Date };
  demographics: Record<string, number>;
  consentObtained: boolean;
  dataProcessingAgreement: boolean;
}

export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  latencyMs: number;
  throughput: number;
  lastEvaluated: Date;
}

export interface BiasMetrics {
  demographicParity: number;
  equalizedOdds: number;
  calibration: number;
  individualFairness: number;
  lastEvaluated: Date;
  protectedAttributes: string[];
}

export interface AIDocumentation {
  purposeStatement: string;
  intendedUse: string;
  limitations: string[];
  risksAndMitigations: RiskItem[];
  monitoringPlan: string;
  humanOversight: string;
  dataGovernance: string;
  technicalDocumentation: string;
}

export interface RiskItem {
  id: string;
  description: string;
  likelihood: 'high' | 'medium' | 'low';
  impact: 'high' | 'medium' | 'low';
  mitigation: string;
  status: 'open' | 'mitigated' | 'accepted';
}

export interface ComplianceAssessment {
  id: string;
  systemId: string;
  assessmentDate: Date;
  assessor: string;
  overallScore: number; // 0-100
  requirements: RequirementAssessment[];
  findings: AssessmentFinding[];
  recommendations: string[];
  nextAssessmentDate: Date;
}

export interface RequirementAssessment {
  requirementId: string;
  description: string;
  status: 'compliant' | 'partially_compliant' | 'non_compliant' | 'not_applicable';
  evidence: string[];
  notes?: string;
}

export interface AssessmentFinding {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  description: string;
  recommendation: string;
  status: 'open' | 'in_remediation' | 'closed';
}

export interface AIUsageLog {
  id: string;
  systemId: string;
  modelId: string;
  timestamp: Date;
  input: string;
  output: string;
  decision?: string;
  humanReview: boolean;
  outcome: 'approved' | 'rejected' | 'flagged' | 'pending';
}

export class AIGovernance {
  private systems: Map<string, AISystem> = new Map();
  private assessments: Map<string, ComplianceAssessment[]> = new Map();
  private usageLogs: Map<string, AIUsageLog[]> = new Map();

  constructor(
    private readonly options: {
      maxSystems?: number;
      assessmentFrequencyDays?: number;
      autoClassify?: boolean;
    } = {}
  ) {
    this.options = {
      maxSystems: 1000,
      assessmentFrequencyDays: 90,
      autoClassify: true,
      ...options
    };
  }

  /**
   * Register an AI system
   */
  registerSystem(system: AISystem): void {
    if (this.systems.size >= this.options.maxSystems!) {
      throw new Error('Maximum system limit reached');
    }

    // Auto-classify if enabled
    if (this.options.autoClassify && !system.riskClass) {
      system.riskClass = this.classifyRisk(system);
    }

    system.status = 'registered';
    system.registrationDate = new Date();
    this.systems.set(system.id, system);
  }

  /**
   * Update an AI system
   */
  updateSystem(id: string, updates: Partial<AISystem>): void {
    const system = this.systems.get(id);
    if (system) {
      this.systems.set(id, { ...system, ...updates });
    }
  }

  /**
   * Get an AI system
   */
  getSystem(id: string): AISystem | undefined {
    return this.systems.get(id);
  }

  /**
   * Get all AI systems
   */
  getSystems(filters?: {
    riskClass?: string;
    status?: string;
    department?: string;
  }): AISystem[] {
    let systems = Array.from(this.systems.values());

    if (filters) {
      if (filters.riskClass) {
        systems = systems.filter(s => s.riskClass === filters.riskClass);
      }
      if (filters.status) {
        systems = systems.filter(s => s.status === filters.status);
      }
      if (filters.department) {
        systems = systems.filter(s => s.department === filters.department);
      }
    }

    return systems;
  }

  /**
   * Assess compliance for a system
   */
  assessCompliance(
    systemId: string, 
    assessor: string,
    requirements: RequirementAssessment[]
  ): ComplianceAssessment {
    const system = this.systems.get(systemId);
    if (!system) {
      throw new Error(`System ${systemId} not found`);
    }

    const compliantCount = requirements.filter(r => r.status === 'compliant').length;
    const partialCount = requirements.filter(r => r.status === 'partially_compliant').length;
    const overallScore = ((compliantCount + partialCount * 0.5) / requirements.length) * 100;

    const assessment: ComplianceAssessment = {
      id: `assessment-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      systemId,
      assessmentDate: new Date(),
      assessor,
      overallScore,
      requirements,
      findings: this.generateFindings(requirements),
      recommendations: this.generateRecommendations(requirements),
      nextAssessmentDate: new Date(
        Date.now() + this.options.assessmentFrequencyDays! * 24 * 60 * 60 * 1000
      )
    };

    // Store assessment
    const assessments = this.assessments.get(systemId) || [];
    assessments.push(assessment);
    this.assessments.set(systemId, assessments);

    // Update system
    system.lastAssessment = new Date();
    system.nextAssessment = assessment.nextAssessmentDate;
    system.status = overallScore >= 80 ? 'approved' : 'assessed';

    return assessment;
  }

  /**
   * Get assessments for a system
   */
  getAssessments(systemId: string): ComplianceAssessment[] {
    return this.assessments.get(systemId) || [];
  }

  /**
   * Log AI usage
   */
  logUsage(log: AIUsageLog): void {
    const logs = this.usageLogs.get(log.systemId) || [];
    logs.push(log);
    this.usageLogs.set(log.systemId, logs);
  }

  /**
   * Get usage logs for a system
   */
  getUsageLogs(
    systemId: string, 
    filters?: {
      fromDate?: Date;
      toDate?: Date;
      outcome?: string;
    }
  ): AIUsageLog[] {
    let logs = this.usageLogs.get(systemId) || [];

    if (filters) {
      if (filters.fromDate) {
        logs = logs.filter(l => l.timestamp >= filters.fromDate!);
      }
      if (filters.toDate) {
        logs = logs.filter(l => l.timestamp <= filters.toDate!);
      }
      if (filters.outcome) {
        logs = logs.filter(l => l.outcome === filters.outcome);
      }
    }

    return logs;
  }

  /**
   * Get AI governance dashboard data
   */
  getDashboardData(): {
    totalSystems: number;
    byRiskClass: Record<string, number>;
    byStatus: Record<string, number>;
    complianceStats: {
      assessed: number;
      compliant: number;
      needsRemediation: number;
    };
    recentAssessments: ComplianceAssessment[];
    upcomingAssessments: { systemId: string; systemName: string; date: Date }[];
  } {
    const systems = Array.from(this.systems.values());

    // Count by risk class
    const byRiskClass: Record<string, number> = {};
    systems.forEach(s => {
      byRiskClass[s.riskClass] = (byRiskClass[s.riskClass] || 0) + 1;
    });

    // Count by status
    const byStatus: Record<string, number> = {};
    systems.forEach(s => {
      byStatus[s.status] = (byStatus[s.status] || 0) + 1;
    });

    // Compliance stats
    const assessedSystems = systems.filter(s => s.lastAssessment);
    const compliantSystems = assessedSystems.filter(s => {
      const assessments = this.assessments.get(s.id) || [];
      const latest = assessments[assessments.length - 1];
      return latest && latest.overallScore >= 80;
    });

    // Recent assessments
    const allAssessments = Array.from(this.assessments.values()).flat();
    const recentAssessments = allAssessments
      .sort((a, b) => b.assessmentDate.getTime() - a.assessmentDate.getTime())
      .slice(0, 10);

    // Upcoming assessments
    const upcomingAssessments = systems
      .filter(s => s.nextAssessment)
      .map(s => ({
        systemId: s.id,
        systemName: s.name,
        date: s.nextAssessment!
      }))
      .sort((a, b) => a.date.getTime() - b.date.getTime())
      .slice(0, 10);

    return {
      totalSystems: systems.length,
      byRiskClass,
      byStatus,
      complianceStats: {
        assessed: assessedSystems.length,
        compliant: compliantSystems.length,
        needsRemediation: assessedSystems.length - compliantSystems.length
      },
      recentAssessments,
      upcomingAssessments
    };
  }

  /**
   * Classify risk level for an AI system
   */
  private classifyRisk(system: AISystem): AISystem['riskClass'] {
    // EU AI Act risk classification logic
    const highRiskUseCases = [
      'credit_scoring',
      'hiring',
      'law_enforcement',
      'migration',
      'justice',
      'democracy',
      'safety',
      'critical_infrastructure'
    ];

    const limitedRiskUseCases = [
      'chatbot',
      'emotion_recognition',
      'biometric',
      'deepfake'
    ];

    const useCaseLower = system.useCase.toLowerCase();

    if (highRiskUseCases.some(uc => useCaseLower.includes(uc))) {
      return 'high';
    }

    if (limitedRiskUseCases.some(uc => useCaseLower.includes(uc))) {
      return 'limited';
    }

    return 'minimal';
  }

  /**
   * Generate findings from requirements
   */
  private generateFindings(requirements: RequirementAssessment[]): AssessmentFinding[] {
    const findings: AssessmentFinding[] = [];

    requirements.forEach(req => {
      if (req.status === 'non_compliant') {
        findings.push({
          id: `finding-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          severity: 'high',
          category: 'compliance',
          description: `Non-compliant with requirement: ${req.description}`,
          recommendation: `Address gap for requirement ${req.requirementId}`,
          status: 'open'
        });
      } else if (req.status === 'partially_compliant') {
        findings.push({
          id: `finding-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          severity: 'medium',
          category: 'compliance',
          description: `Partially compliant with requirement: ${req.description}`,
          recommendation: `Complete implementation for requirement ${req.requirementId}`,
          status: 'open'
        });
      }
    });

    return findings;
  }

  /**
   * Generate recommendations
   */
  private generateRecommendations(requirements: RequirementAssessment[]): string[] {
    const recommendations: string[] = [];

    const nonCompliant = requirements.filter(r => r.status === 'non_compliant');
    const partial = requirements.filter(r => r.status === 'partially_compliant');

    if (nonCompliant.length > 0) {
      recommendations.push(`Address ${nonCompliant.length} non-compliant requirements immediately`);
    }

    if (partial.length > 0) {
      recommendations.push(`Complete implementation for ${partial.length} partially compliant requirements`);
    }

    if (requirements.length > 0) {
      recommendations.push('Schedule follow-up assessment within 90 days');
    }

    return recommendations;
  }
}
