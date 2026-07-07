import { v4 as uuidv4 } from 'uuid';
import {
  NetworkComponent,
  ComplianceFramework,
  ControlMapping,
  SecurityAssessment,
  NetworkComplianceReport,
  FrameworkCompliance,
  ReportSummary,
  SecurityGap,
  Recommendation,
  ContinuousMonitoringConfig,
  MonitoringResult,
  MonitoringAlert,
  ChangeDetected,
  ControlStatus,
  RiskLevel,
  RemediationPlan
} from './types';
import { ThreeGPPControls } from './threegpp-controls';
import { NetworkSecurityAssessment } from './network-security-assessment';
import { ORANCompliance } from './oran-compliance';

export class SixGComplianceEngine {
  private threeGPP: ThreeGPPControls;
  private networkAssessment: NetworkSecurityAssessment;
  private oranCompliance: ORANCompliance;
  private monitoringConfig: ContinuousMonitoringConfig;
  private monitoringHistory: MonitoringResult[] = [];

  constructor(config?: Partial<ContinuousMonitoringConfig>) {
    this.threeGPP = new ThreeGPPControls();
    this.networkAssessment = new NetworkSecurityAssessment();
    this.oranCompliance = new ORANCompliance();
    this.monitoringConfig = {
      enabled: true,
      intervalMinutes: 5,
      alertsEnabled: true,
      thresholdScore: 80,
      autoRemediate: false,
      notificationChannels: [],
      ...config
    };
  }

  async assessNetwork(
    components: NetworkComponent[],
    frameworks: ComplianceFramework[]
  ): Promise<NetworkComplianceReport> {
    const assessments: SecurityAssessment[] = [];

    for (const component of components) {
      const assessment = await this.assessComponent(component, frameworks);
      assessments.push(assessment);
    }

    return this.generateReport(assessments);
  }

  async assessComponent(
    component: NetworkComponent,
    frameworks: ComplianceFramework[]
  ): Promise<SecurityAssessment> {
    const allControls: ControlMapping[] = [];

    for (const framework of frameworks) {
      const controls = await this.mapToControls(component, framework);
      allControls.push(...controls);
    }

    const score = this.calculateScore(allControls);
    const gaps = this.identifyGaps(allControls);
    const recommendations = this.generateRecommendations(gaps);

    return {
      id: uuidv4(),
      component,
      framework: frameworks[0],
      controls: allControls,
      score,
      gaps,
      assessedDate: new Date().toISOString(),
      assessor: 'automated',
      recommendations
    };
  }

  async mapToControls(
    component: NetworkComponent,
    framework: ComplianceFramework
  ): Promise<ControlMapping[]> {
    const controls: ControlMapping[] = [];

    if (framework.startsWith('3gpp')) {
      const threeGPPControls = this.threeGPP.getControlsForComponent(component, framework);
      controls.push(...threeGPPControls);
    }

    if (framework.startsWith('oran')) {
      const oranControls = this.oranCompliance.getControlsForComponent(component, framework);
      controls.push(...oranControls);
    }

    if (framework.startsWith('nist') || framework.startsWith('iso')) {
      const genericControls = this.getGenericControls(component, framework);
      controls.push(...genericControls);
    }

    if (framework === 'eu-ai-act' && component.type === 'ai-ml-engine') {
      const aiControls = this.getAIActControls(component);
      controls.push(...aiControls);
    }

    const networkControls = await this.networkAssessment.assessComponentSecurity(component, framework);
    controls.push(...networkControls);

    return this.deduplicateControls(controls);
  }

  async generateReport(assessments: SecurityAssessment[]): Promise<NetworkComplianceReport> {
    const allGaps = assessments.flatMap(a => a.gaps);
    const allRecommendations = assessments.flatMap(a => a.recommendations);
    const components = assessments.map(a => a.component);

    const complianceByFramework = this.calculateFrameworkCompliance(assessments);
    const overallScore = this.calculateOverallScore(assessments);
    const summary = this.generateSummary(assessments);

    return {
      id: uuidv4(),
      generatedAt: new Date().toISOString(),
      reportPeriod: {
        start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        end: new Date().toISOString()
      },
      components,
      assessments,
      overallScore,
      complianceByFramework,
      criticalGaps: allGaps.filter(g => g.severity === 'critical'),
      recommendations: allRecommendations,
      summary
    };
  }

  async monitorContinuous(
    components: NetworkComponent[]
  ): Promise<MonitoringResult[]> {
    const results: MonitoringResult[] = [];

    for (const component of components) {
      const result = await this.checkComponent(component);
      results.push(result);

      if (this.monitoringConfig.alertsEnabled) {
        await this.processAlerts(result);
      }
    }

    this.monitoringHistory.push(...results);
    return results;
  }

  private async checkComponent(component: NetworkComponent): Promise<MonitoringResult> {
    const frameworks: ComplianceFramework[] = [
      '3gpp-ts33501',
      'nist-csf',
      'oran-sds'
    ];

    const assessment = await this.assessComponent(component, frameworks);
    const alerts = this.generateAlerts(assessment);
    const changes = await this.detectChanges(component);

    return {
      timestamp: new Date().toISOString(),
      componentId: component.id,
      score: assessment.score,
      status: assessment.score >= this.monitoringConfig.thresholdScore
        ? 'compliant'
        : 'non-compliant',
      alerts,
      changes
    };
  }

  private async processAlerts(result: MonitoringResult): Promise<void> {
    for (const alert of result.alerts) {
      if (alert.severity === 'critical' || alert.severity === 'high') {
        await this.sendNotification(alert);
      }
    }
  }

  private async sendNotification(alert: MonitoringAlert): Promise<void> {
    for (const channel of this.monitoringConfig.notificationChannels) {
      if (channel.severityFilter.includes(alert.severity)) {
        console.log(`Alert sent to ${channel.type}: ${alert.message}`);
      }
    }
  }

  private async detectChanges(component: NetworkComponent): Promise<ChangeDetected[]> {
    const changes: ChangeDetected[] = [];
    const previousResults = this.monitoringHistory
      .filter(r => r.componentId === component.id)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    if (previousResults.length > 0) {
      const lastResult = previousResults[0];
      const scoreDiff = Math.abs(lastResult.score - 0);

      if (scoreDiff > 10) {
        changes.push({
          type: 'config-change',
          description: `Score changed by ${scoreDiff.toFixed(2)}%`,
          timestamp: new Date().toISOString(),
          details: {
            previousScore: lastResult.score,
            currentScore: 0
          }
        });
      }
    }

    return changes;
  }

  private generateAlerts(assessment: SecurityAssessment): MonitoringAlert[] {
    const alerts: MonitoringAlert[] = [];

    if (assessment.score < this.monitoringConfig.thresholdScore) {
      alerts.push({
        id: uuidv4(),
        severity: assessment.score < 60 ? 'critical' : 'high',
        message: `Component ${assessment.component.name} score ${assessment.score.toFixed(2)}% is below threshold ${this.monitoringConfig.thresholdScore}%`,
        detectedAt: new Date().toISOString()
      });
    }

    for (const gap of assessment.gaps) {
      if (gap.severity === 'critical') {
        alerts.push({
          id: uuidv4(),
          severity: 'critical',
          message: `Critical gap detected: ${gap.description}`,
          controlId: gap.controlId,
          detectedAt: new Date().toISOString()
        });
      }
    }

    return alerts;
  }

  private getGenericControls(
    component: NetworkComponent,
    framework: ComplianceFramework
  ): ControlMapping[] {
    const controls: ControlMapping[] = [];

    const genericMappings: Record<string, { title: string; description: string; category: string }[]> = {
      'nist-csf': [
        { title: 'Identify', description: 'Asset management and risk assessment', category: 'Identify' },
        { title: 'Protect', description: 'Access control and data security', category: 'Protect' },
        { title: 'Detect', description: 'Anomaly detection and monitoring', category: 'Detect' },
        { title: 'Respond', description: 'Response planning and communications', category: 'Respond' },
        { title: 'Recover', description: 'Recovery planning and improvements', category: 'Recover' }
      ],
      'iso-27001': [
        { title: 'Information Security Policies', description: 'Management direction for information security', category: 'A.5' },
        { title: 'Organization of Information Security', description: 'Internal organization', category: 'A.6' },
        { title: 'Human Resource Security', description: 'Prior to, during, and after employment', category: 'A.7' },
        { title: 'Asset Management', description: 'Classification and handling of assets', category: 'A.8' },
        { title: 'Access Control', description: 'Business requirements of access control', category: 'A.9' },
        { title: 'Cryptography', description: 'Cryptographic controls', category: 'A.10' },
        { title: 'Physical and Environmental Security', description: 'Secure areas', category: 'A.11' },
        { title: 'Operations Security', description: 'Operational procedures and responsibilities', category: 'A.12' }
      ],
      'iso-27002': [
        { title: 'Information Security Controls', description: 'Reference controls for information security', category: 'Controls' },
        { title: 'Organizational Controls', description: 'Organizational context and roles', category: 'A.5' },
        { title: 'People Controls', description: 'Human resource security', category: 'A.6' },
        { title: 'Physical Controls', description: 'Physical security perimeters', category: 'A.7' },
        { title: 'Technological Controls', description: 'Access control and system security', category: 'A.8' }
      ],
      'nist-800-53': [
        { title: 'Access Control', description: 'AC family controls', category: 'AC' },
        { title: 'Audit and Accountability', description: 'AU family controls', category: 'AU' },
        { title: 'Configuration Management', description: 'CM family controls', category: 'CM' },
        { title: 'Identification and Authentication', description: 'IA family controls', category: 'IA' },
        { title: 'System and Communications Protection', description: 'SC family controls', category: 'SC' }
      ],
      'etsi-nfvi': [
        { title: 'NFVI Security', description: 'Network Functions Virtualization Infrastructure security', category: 'NFVI' },
        { title: 'VNF Security', description: 'Virtual Network Function security', category: 'VNF' },
        { title: 'MANO Security', description: 'Management and Orchestration security', category: 'MANO' }
      ],
      'gsma-iris': [
        { title: 'Network Security', description: 'Network infrastructure security', category: 'Network' },
        { title: 'Device Security', description: 'Endpoint device security', category: 'Device' },
        { title: 'Application Security', description: 'Application layer security', category: 'Application' }
      ]
    };

    const mappings = genericMappings[framework] || [];

    for (let i = 0; i < mappings.length; i++) {
      const mapping = mappings[i];
      const status = this.assessGenericControl(component, mapping.title);

      controls.push({
        id: uuidv4(),
        framework,
        controlId: `${framework.toUpperCase()}-${String(i + 1).padStart(3, '0')}`,
        title: mapping.title,
        description: mapping.description,
        category: mapping.category,
        status,
        evidence: [],
        assessedDate: new Date().toISOString(),
        risk: status === 'compliant' ? 'informational' : 'medium'
      });
    }

    return controls;
  }

  private getAIActControls(component: NetworkComponent): ControlMapping[] {
    const controls: ControlMapping[] = [];

    const aiRequirements = [
      { title: 'Risk Management System', description: 'Establish and maintain risk management system for AI', category: 'Article 9' },
      { title: 'Data Governance', description: 'Training, validation, and testing datasets governance', category: 'Article 10' },
      { title: 'Technical Documentation', description: 'Create and maintain technical documentation', category: 'Article 11' },
      { title: 'Record-Keeping', description: 'Automatic logging of events for traceability', category: 'Article 12' },
      { title: 'Transparency', description: 'Provide information to deployers', category: 'Article 13' },
      { title: 'Human Oversight', description: 'Enable human oversight during use', category: 'Article 14' },
      { title: 'Accuracy and Robustness', description: 'Appropriate levels of accuracy and robustness', category: 'Article 15' },
      { title: 'Cybersecurity', description: 'Resilient against attempts by unauthorized third parties', category: 'Article 15(4)' }
    ];

    for (let i = 0; i < aiRequirements.length; i++) {
      const req = aiRequirements[i];
      const status = this.assessAIControl(component, req.title);

      controls.push({
        id: uuidv4(),
        framework: 'eu-ai-act',
        controlId: `AI-ACT-${String(i + 1).padStart(3, '0')}`,
        title: req.title,
        description: req.description,
        category: req.category,
        status,
        evidence: [],
        assessedDate: new Date().toISOString(),
        risk: status === 'compliant' ? 'informational' : 'high'
      });
    }

    return controls;
  }

  private assessGenericControl(
    component: NetworkComponent,
    controlName: string
  ): ControlStatus {
    if (controlName.toLowerCase().includes('access') && component.type === 'security-gateway') {
      return 'compliant';
    }
    if (controlName.toLowerCase().includes('cryptography') && component.type === 'core-network') {
      return 'compliant';
    }
    return 'pending-assessment';
  }

  private assessAIControl(
    component: NetworkComponent,
    controlName: string
  ): ControlStatus {
    if (component.type !== 'ai-ml-engine') {
      return 'not-applicable';
    }

    if (controlName === 'Risk Management System' && component.version >= '1.0.0') {
      return 'compliant';
    }

    return 'pending-assessment';
  }

  private calculateScore(controls: ControlMapping[]): number {
    if (controls.length === 0) return 0;

    const weights: Record<ControlStatus, number> = {
      'compliant': 1.0,
      'partially-compliant': 0.5,
      'non-compliant': 0.0,
      'not-applicable': 1.0,
      'pending-assessment': 0.25,
      'remediation-in-progress': 0.75
    };

    let totalWeight = 0;
    let achievedWeight = 0;

    for (const control of controls) {
      const weight = 1.0;
      totalWeight += weight;
      achievedWeight += weight * (weights[control.status] || 0);
    }

    return totalWeight > 0 ? (achievedWeight / totalWeight) * 100 : 0;
  }

  private identifyGaps(controls: ControlMapping[]): SecurityGap[] {
    const gaps: SecurityGap[] = [];

    for (const control of controls) {
      if (control.status === 'non-compliant' || control.status === 'partially-compliant') {
        gaps.push({
          id: uuidv4(),
          controlId: control.controlId,
          description: `${control.title} is ${control.status}`,
          severity: this.determineSeverity(control),
          impact: `Non-compliance with ${control.framework} ${control.controlId}`,
          remediation: this.createRemediationPlan(control)
        });
      }
    }

    return gaps;
  }

  private determineSeverity(control: ControlMapping): RiskLevel {
    if (control.framework.startsWith('3gpp') || control.framework.startsWith('oran')) {
      return 'high';
    }
    if (control.framework === 'eu-ai-act') {
      return 'critical';
    }
    return 'medium';
  }

  private createRemediationPlan(control: ControlMapping): RemediationPlan {
    return {
      id: uuidv4(),
      description: `Remediate ${control.title} non-compliance`,
      steps: [
        {
          order: 1,
          description: 'Review current configuration and identify root cause',
          completed: false
        },
        {
          order: 2,
          description: 'Implement required changes',
          completed: false
        },
        {
          order: 3,
          description: 'Validate changes meet control requirements',
          completed: false
        },
        {
          order: 4,
          description: 'Document evidence for compliance',
          completed: false
        }
      ],
      priority: this.determineSeverity(control),
      targetDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      status: 'planned'
    };
  }

  private generateRecommendations(gaps: SecurityGap[]): Recommendation[] {
    const recommendations: Recommendation[] = [];

    for (const gap of gaps) {
      recommendations.push({
        id: uuidv4(),
        priority: gap.severity,
        title: `Address ${gap.controlId} gap`,
        description: gap.remediation.description,
        affectedControls: [gap.controlId],
        estimatedEffort: gap.severity === 'critical' ? 'high' : 'medium',
        estimatedImpact: gap.severity === 'critical' ? 'high' : 'medium'
      });
    }

    return recommendations;
  }

  private calculateFrameworkCompliance(
    assessments: SecurityAssessment[]
  ): Record<ComplianceFramework, FrameworkCompliance> {
    const compliance: Record<string, FrameworkCompliance> = {};

    for (const assessment of assessments) {
      const framework = assessment.framework;
      if (!compliance[framework]) {
        compliance[framework] = {
          framework,
          score: 0,
          totalControls: 0,
          compliantControls: 0,
          nonCompliantControls: 0,
          gaps: []
        };
      }

      const fc = compliance[framework];
      fc.totalControls += assessment.controls.length;
      fc.compliantControls += assessment.controls.filter(c => c.status === 'compliant').length;
      fc.nonCompliantControls += assessment.controls.filter(c => c.status === 'non-compliant').length;
      fc.gaps.push(...assessment.gaps);
      fc.score = (fc.compliantControls / fc.totalControls) * 100;
    }

    return compliance as Record<ComplianceFramework, FrameworkCompliance>;
  }

  private calculateOverallScore(assessments: SecurityAssessment[]): number {
    if (assessments.length === 0) return 0;

    const totalScore = assessments.reduce((sum, a) => sum + a.score, 0);
    return totalScore / assessments.length;
  }

  private generateSummary(assessments: SecurityAssessment[]): ReportSummary {
    const totalComponents = assessments.length;
    const assessedComponents = assessments.filter(a => a.controls.length > 0).length;
    const compliantComponents = assessments.filter(a => a.score >= 90).length;
    const partiallyCompliantComponents = assessments.filter(a => a.score >= 50 && a.score < 90).length;
    const nonCompliantComponents = assessments.filter(a => a.score < 50).length;

    const allGaps = assessments.flatMap(a => a.gaps);
    const criticalGapsCount = allGaps.filter(g => g.severity === 'critical').length;
    const highGapsCount = allGaps.filter(g => g.severity === 'high').length;
    const mediumGapsCount = allGaps.filter(g => g.severity === 'medium').length;
    const lowGapsCount = allGaps.filter(g => g.severity === 'low').length;

    return {
      totalComponents,
      assessedComponents,
      compliantComponents,
      partiallyCompliantComponents,
      nonCompliantComponents,
      criticalGapsCount,
      highGapsCount,
      mediumGapsCount,
      lowGapsCount,
      averageScore: this.calculateOverallScore(assessments)
    };
  }

  private deduplicateControls(controls: ControlMapping[]): ControlMapping[] {
    const seen = new Set<string>();
    return controls.filter(control => {
      const key = `${control.framework}-${control.controlId}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }
}
