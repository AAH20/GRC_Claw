import {
  Cjadc2Domain,
  Cjadc2Component,
  Cjadc2Operation,
  ComponentStatus,
  DomainAssessment,
  InteroperabilityAssessment,
  SecurityAssessment,
  OperationReport,
  Gr00tAssessment,
  Gr00tMapping,
  Gr00tCapability,
  AssessmentIssue,
  ProtocolIssue,
  ProtocolCompliance,
  ControlStatus,
  Vulnerability
} from './types';
import { SenseDomain } from './sense-domain';
import { DecideDomain } from './decide-domain';
import { ActDomain } from './act-domain';
import { CommunicateDomain } from './communicate-domain';

export class Cjadc2Engine {
  private senseDomain: SenseDomain;
  private decideDomain: DecideDomain;
  private actDomain: ActDomain;
  private communicateDomain: CommunicateDomain;

  constructor() {
    this.senseDomain = new SenseDomain();
    this.decideDomain = new DecideDomain();
    this.actDomain = new ActDomain();
    this.communicateDomain = new CommunicateDomain();
  }

  assessDomain(domain: Cjadc2Domain, components: Cjadc2Component[]): DomainAssessment {
    const domainComponents = components.filter(c => c.domain.includes(domain));

    switch (domain) {
      case Cjadc2Domain.SENSE:
        return this.senseDomain.assess(domainComponents);
      case Cjadc2Domain.DECIDE:
        return this.decideDomain.assess(domainComponents);
      case Cjadc2Domain.ACT:
        return this.actDomain.assess(domainComponents);
      case Cjadc2Domain.COMMUNICATE:
        return this.communicateDomain.assess(domainComponents);
      case Cjadc2Domain.MOVE:
        return this.assessMoveDomain(domainComponents);
      case Cjadc2Domain.PROTECT:
        return this.assessProtectDomain(domainComponents);
      default:
        return this.createEmptyAssessment(domain);
    }
  }

  assessInteroperability(components: Cjadc2Component[]): InteroperabilityAssessment {
    const issues: ProtocolIssue[] = [];
    const compliance: ProtocolCompliance[] = [];
    let totalScore = 0;
    let maxScore = 0;

    const protocolMap = new Map<string, { standard: string; version: string; components: string[] }>();

    components.forEach(component => {
      component.interoperability.forEach(req => {
        const key = `${req.standard}-${req.version}`;
        if (!protocolMap.has(key)) {
          protocolMap.set(key, {
            standard: req.standard,
            version: req.version,
            components: []
          });
        }
        protocolMap.get(key)!.components.push(component.id);

        maxScore += 10;
        if (req.required) {
          if (component.status === ComponentStatus.OFFLINE) {
            issues.push({
              protocol: req.standard,
              component: component.id,
              issue: `Component offline, cannot verify protocol support`,
              severity: 'high'
            });
          } else {
            totalScore += 10;
          }
        } else {
          totalScore += 5;
        }
      });
    });

    protocolMap.forEach((value, key) => {
      compliance.push({
        standard: value.standard as any,
        compliant: value.components.length > 1,
        components: value.components,
        version: value.version
      });
    });

    const score = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0;

    return {
      score,
      maxScore,
      status: score >= 80 ? 'compliant' : score >= 50 ? 'partial' : 'non_compliant',
      protocolIssues: issues,
      compliance,
      timestamp: new Date()
    };
  }

  assessSecurity(components: Cjadc2Component[]): SecurityAssessment {
    const vulnerabilities: Vulnerability[] = [];
    const controlStatusMap = new Map<string, ControlStatus>();
    let totalScore = 0;
    let maxScore = 0;

    components.forEach(component => {
      component.security.forEach(req => {
        maxScore += 10;

        const existing = controlStatusMap.get(req.control);
        if (existing) {
          existing.total += 1;
          if (req.status === 'met') existing.met += 1;
        } else {
          controlStatusMap.set(req.control, {
            control: req.control,
            level: req.level,
            met: req.status === 'met' ? 1 : 0,
            total: 1,
            percentage: 0
          });
        }

        if (req.status === 'not_met') {
          vulnerabilities.push({
            id: `vuln-${component.id}-${req.control}`,
            severity: req.level === 'critical' ? 'critical' : req.level === 'high' ? 'high' : 'medium',
            component: component.id,
            control: req.control,
            description: `${req.control} control not met at ${req.level} level`,
            remediation: `Implement ${req.control} control at ${req.level} level`
          });
        } else if (req.status === 'partial') {
          totalScore += 5;
        } else {
          totalScore += 10;
        }
      });
    });

    controlStatusMap.forEach(value => {
      value.percentage = value.total > 0 ? Math.round((value.met / value.total) * 100) : 0;
    });

    const score = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0;

    return {
      score,
      maxScore,
      status: score >= 80 ? 'compliant' : score >= 50 ? 'partial' : 'non_compliant',
      controlStatus: Array.from(controlStatusMap.values()),
      vulnerabilities,
      timestamp: new Date()
    };
  }

  generateOperationReport(operation: Cjadc2Operation, components: Cjadc2Component[]): OperationReport {
    const relevantComponents = components.filter(c =>
      operation.components.includes(c.id)
    );

    const domainScores: DomainAssessment[] = [];
    for (const domain of operation.domain) {
      domainScores.push(this.assessDomain(domain, relevantComponents));
    }

    const interoperability = this.assessInteroperability(relevantComponents);
    const security = this.assessSecurity(relevantComponents);

    const overallScore = this.calculateOverallScore(domainScores, interoperability, security);
    const riskLevel = this.determineRiskLevel(overallScore, security);
    const readinessStatus = this.determineReadinessStatus(overallScore, security, interoperability);

    return {
      operation,
      overallScore,
      domainScores,
      interoperability,
      security,
      riskLevel,
      readinessStatus,
      summary: this.generateSummary(overallScore, riskLevel, readinessStatus, domainScores),
      generatedAt: new Date()
    };
  }

  mapToGr00t(components: Cjadc2Component[]): Gr00tAssessment {
    const mappings: Gr00tMapping[] = [];
    const allCapabilities = Object.values(Gr00tCapability);
    const coveredCapabilities = new Set<Gr00tCapability>();

    components.forEach(component => {
      const capabilities = this.mapComponentCapabilities(component);
      const gaps = allCapabilities.filter(cap => !capabilities.includes(cap));

      mappings.push({
        component: component.id,
        domain: component.domain[0] || Cjadc2Domain.SENSE,
        capabilities,
        coverageScore: Math.round((capabilities.length / allCapabilities.length) * 100),
        gaps
      });

      capabilities.forEach(cap => coveredCapabilities.add(cap));
    });

    const overallCoverage = Math.round((coveredCapabilities.size / allCapabilities.length) * 100);
    const capabilityGaps = allCapabilities.filter(cap => !coveredCapabilities.has(cap));

    return {
      mappings,
      overallCoverage,
      capabilityGaps,
      recommendations: this.generateGr00tRecommendations(capabilityGaps),
      timestamp: new Date()
    };
  }

  private assessMoveDomain(components: Cjadc2Component[]): DomainAssessment {
    const issues: AssessmentIssue[] = [];
    let score = 0;
    const maxScore = 100;

    const operationalComponents = components.filter(c => c.status === ComponentStatus.OPERATIONAL);
    score += Math.min(50, (operationalComponents.length / Math.max(1, components.length)) * 50);

    const classifiedComponents = components.filter(c =>
      c.classification !== 'unclassified'
    );
    if (classifiedComponents.length > 0) {
      score += 30;
    }

    score += 20;

    return {
      domain: Cjadc2Domain.MOVE,
      score: Math.round(score),
      maxScore,
      status: score >= 80 ? 'compliant' : score >= 50 ? 'partial' : 'non_compliant',
      issues,
      recommendations: this.generateMoveRecommendations(score, components),
      componentsAssessed: components.length,
      timestamp: new Date()
    };
  }

  private assessProtectDomain(components: Cjadc2Component[]): DomainAssessment {
    const issues: AssessmentIssue[] = [];
    let score = 0;
    const maxScore = 100;

    const securityIssues = components.filter(c =>
      c.security.some(s => s.status === 'not_met')
    );
    if (securityIssues.length === 0) {
      score += 40;
    } else {
      issues.push({
        severity: 'high',
        description: `${securityIssues.length} components have unmet security requirements`
      });
    }

    const encryptedComponents = components.filter(c =>
      c.security.some(s => s.control === 'encryption' && s.status === 'met')
    );
    score += Math.min(30, (encryptedComponents.length / Math.max(1, components.length)) * 30);

    const classifiedComponents = components.filter(c =>
      c.classification !== 'unclassified'
    );
    if (classifiedComponents.length > 0) {
      score += 30;
    }

    return {
      domain: Cjadc2Domain.PROTECT,
      score: Math.round(score),
      maxScore,
      status: score >= 80 ? 'compliant' : score >= 50 ? 'partial' : 'non_compliant',
      issues,
      recommendations: this.generateProtectRecommendations(score, components),
      componentsAssessed: components.length,
      timestamp: new Date()
    };
  }

  private calculateOverallScore(
    domainScores: DomainAssessment[],
    interoperability: InteroperabilityAssessment,
    security: SecurityAssessment
  ): number {
    const domainAvg = domainScores.reduce((sum, d) => sum + d.score, 0) / Math.max(1, domainScores.length);
    const interopScore = interoperability.score;
    const securityScore = security.score;

    return Math.round((domainAvg * 0.4 + interopScore * 0.3 + securityScore * 0.3));
  }

  private determineRiskLevel(
    overallScore: number,
    security: SecurityAssessment
  ): 'critical' | 'high' | 'medium' | 'low' {
    const hasCriticalVulns = security.vulnerabilities.some(v => v.severity === 'critical');

    if (hasCriticalVulns || overallScore < 30) return 'critical';
    if (overallScore < 50) return 'high';
    if (overallScore < 70) return 'medium';
    return 'low';
  }

  private determineReadinessStatus(
    overallScore: number,
    security: SecurityAssessment,
    interoperability: InteroperabilityAssessment
  ): 'ready' | 'conditionally_ready' | 'not_ready' {
    if (overallScore >= 80 && security.status === 'compliant' && interoperability.status === 'compliant') {
      return 'ready';
    }
    if (overallScore >= 50) {
      return 'conditionally_ready';
    }
    return 'not_ready';
  }

  private generateSummary(
    overallScore: number,
    riskLevel: string,
    readinessStatus: string,
    domainScores: DomainAssessment[]
  ): string {
    const domainSummary = domainScores.map(d =>
      `${d.domain}: ${d.score}/${d.maxScore}`
    ).join(', ');

    return `CJADC2 Operation Assessment: Score ${overallScore}/100. ` +
      `Risk Level: ${riskLevel}. Readiness: ${readinessStatus}. ` +
      `Domain Scores: ${domainSummary}.`;
  }

  private mapComponentCapabilities(component: Cjadc2Component): Gr00tCapability[] {
    const capabilities: Gr00tCapability[] = [];

    if (component.type === 'sensor') {
      capabilities.push(Gr00tCapability.SENSE_FUSION);
      capabilities.push(Gr00tCapability.THREAT_DETECTION);
      capabilities.push(Gr00tCapability.SITUATIONAL_AWARENESS);
    }
    if (component.type === 'decision_aid' || component.type === 'ai_system') {
      capabilities.push(Gr00tCapability.DECISION_SUPPORT);
      capabilities.push(Gr00tCapability.SITUATIONAL_AWARENESS);
    }
    if (component.type === 'weapon') {
      capabilities.push(Gr00tCapability.AUTONOMOUS_ACTION);
    }
    if (component.type === 'network' || component.type === 'data_link') {
      capabilities.push(Gr00tCapability.SECURE_COMMS);
      capabilities.push(Gr00tCapability.NETWORK_RESILIENCE);
      capabilities.push(Gr00tCapability.DATA_SHARING);
    }
    if (component.type === 'command') {
      capabilities.push(Gr00tCapability.DECISION_SUPPORT);
      capabilities.push(Gr00tCapability.SECURE_COMMS);
      capabilities.push(Gr00tCapability.SITUATIONAL_AWARENESS);
    }

    return [...new Set(capabilities)];
  }

  private generateGr00tRecommendations(gaps: Gr00tCapability[]): string[] {
    const recommendations: string[] = [];

    gaps.forEach(gap => {
      switch (gap) {
        case Gr00tCapability.SENSE_FUSION:
          recommendations.push('Deploy multi-sensor fusion capabilities for integrated sensing');
          break;
        case Gr00tCapability.DECISION_SUPPORT:
          recommendations.push('Implement AI-assisted decision support systems');
          break;
        case Gr00tCapability.AUTONOMOUS_ACTION:
          recommendations.push('Consider autonomous engagement capabilities with appropriate safeguards');
          break;
        case Gr00tCapability.SECURE_COMMS:
          recommendations.push('Establish encrypted communication channels');
          break;
        case Gr00tCapability.NETWORK_RESILIENCE:
          recommendations.push('Implement redundant network paths and failover mechanisms');
          break;
        case Gr00tCapability.THREAT_DETECTION:
          recommendations.push('Deploy advanced threat detection and classification systems');
          break;
        case Gr00tCapability.DATA_SHARING:
          recommendations.push('Enable cross-domain data sharing with appropriate controls');
          break;
        case Gr00tCapability.SITUATIONAL_AWARENESS:
          recommendations.push('Implement comprehensive situational awareness displays');
          break;
      }
    });

    return recommendations;
  }

  private generateMoveRecommendations(score: number, components: Cjadc2Component[]): string[] {
    const recommendations: string[] = [];

    if (score < 80) {
      recommendations.push('Increase component operational readiness');
      recommendations.push('Implement mobility tracking and logistics support');
    }

    const offlineComponents = components.filter(c => c.status === ComponentStatus.OFFLINE);
    if (offlineComponents.length > 0) {
      recommendations.push(`Address ${offlineComponents.length} offline components`);
    }

    return recommendations;
  }

  private generateProtectRecommendations(score: number, components: Cjadc2Component[]): string[] {
    const recommendations: string[] = [];

    if (score < 80) {
      recommendations.push('Strengthen security controls across all components');
      recommendations.push('Implement defense-in-depth strategies');
    }

    const unencryptedComponents = components.filter(c =>
      !c.security.some(s => s.control === 'encryption' && s.status === 'met')
    );
    if (unencryptedComponents.length > 0) {
      recommendations.push('Enable encryption on all sensitive components');
    }

    return recommendations;
  }

  private createEmptyAssessment(domain: Cjadc2Domain): DomainAssessment {
    return {
      domain,
      score: 0,
      maxScore: 100,
      status: 'non_compliant',
      issues: [],
      recommendations: ['No components found for this domain'],
      componentsAssessed: 0,
      timestamp: new Date()
    };
  }
}
