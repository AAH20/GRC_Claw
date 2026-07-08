import {
  Cjadc2Domain,
  Cjadc2Component,
  DomainAssessment,
  AssessmentIssue
} from './types';

export class ActDomain {
  private readonly LETHAL_AUTONOMY_POLICY = {
    allowed: false,
    requiresHumanControl: true,
    exceptionProcess: true,
    reviewBoard: true
  };

  assess(components: Cjadc2Component[]): DomainAssessment {
    const issues: AssessmentIssue[] = [];
    let score = 0;
    const maxScore = 100;

    const authorityScore = this.checkEngagementAuthority(components, issues);
    score += authorityScore * 25;

    const autonomousScore = this.checkAutonomousAction(components, issues);
    score += autonomousScore * 25;

    const lethalScore = this.checkLethalAutonomy(components, issues);
    score += lethalScore * 25;

    const responseScore = this.checkResponseTime(components, issues);
    score += responseScore * 25;

    return {
      domain: Cjadc2Domain.ACT,
      score: Math.round(score),
      maxScore,
      status: score >= 80 ? 'compliant' : score >= 50 ? 'partial' : 'non_compliant',
      issues,
      recommendations: this.generateRecommendations(score, issues),
      componentsAssessed: components.length,
      timestamp: new Date()
    };
  }

  private checkEngagementAuthority(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    const hasAuthorization = components.some(c =>
      c.capabilities.includes('engagement_authorization') || c.capabilities.includes('authorization')
    );
    if (hasAuthorization) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'critical',
        description: 'Engagement authorization capability not detected',
        standard: 'EA-001',
        remediation: 'Implement engagement authorization workflows'
      });
    }

    const hasPID = components.some(c =>
      c.capabilities.includes('positive_identification') || c.capabilities.includes('pid')
    );
    if (hasPID) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'critical',
        description: 'Positive identification (PID) capability not detected',
        standard: 'EA-002',
        remediation: 'Implement positive identification procedures'
      });
    }

    const hasProportionality = components.some(c =>
      c.capabilities.includes('proportionality') || c.capabilities.includes('proportionality_assessment')
    );
    if (hasProportionality) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'high',
        description: 'Proportionality assessment capability not detected',
        standard: 'EA-003',
        remediation: 'Implement proportionality assessment for engagements'
      });
    }

    const hasDiscrimination = components.some(c =>
      c.capabilities.includes('discrimination') || c.capabilities.includes('combatant_discrimination')
    );
    if (hasDiscrimination) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'high',
        description: 'Combatant discrimination capability not detected',
        standard: 'EA-004',
        remediation: 'Implement combatant discrimination procedures'
      });
    }

    return score;
  }

  private checkAutonomousAction(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    const hasSupervision = components.some(c =>
      c.capabilities.includes('supervised_autonomy') || c.capabilities.includes('human_supervision')
    );
    if (hasSupervision) {
      score += 0.35;
    } else {
      issues.push({
        severity: 'high',
        description: 'Supervised autonomy capability not detected',
        standard: 'AA-001',
        remediation: 'Implement human supervision for autonomous actions'
      });
    }

    const hasAbortCapability = components.some(c =>
      c.capabilities.includes('abort') || c.capabilities.includes('emergency_stop')
    );
    if (hasAbortCapability) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'critical',
        description: 'Abort capability not detected for autonomous actions',
        standard: 'AA-002',
        remediation: 'Implement abort capability for all autonomous actions'
      });
    }

    const hasRestrictions = this.checkAutonomyRestrictions(components);
    if (hasRestrictions) {
      score += 0.35;
    } else {
      issues.push({
        severity: 'high',
        description: 'Autonomy restrictions not properly implemented',
        standard: 'AA-003',
        remediation: 'Implement restrictions on lethal and strategic autonomous actions'
      });
    }

    return score;
  }

  private checkLethalAutonomy(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    if (!this.LETHAL_AUTONOMY_POLICY.allowed) {
      score += 0.3;
    }

    const hasHumanControl = components.some(c =>
      c.capabilities.includes('human_control') || c.capabilities.includes('human_in_loop')
    );
    if (hasHumanControl) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'critical',
        description: 'Human control for lethal actions not detected',
        standard: 'LA-001',
        remediation: 'Implement human control requirements for lethal actions'
      });
    }

    const hasExceptionProcess = components.some(c =>
      c.capabilities.includes('exception_process') || c.capabilities.includes('exception_handling')
    );
    if (hasExceptionProcess) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Exception process for lethal autonomy not detected',
        standard: 'LA-002',
        remediation: 'Implement exception process for autonomous lethal actions'
      });
    }

    const hasReviewBoard = components.some(c =>
      c.capabilities.includes('review_board') || c.capabilities.includes('ethics_review')
    );
    if (hasReviewBoard) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Review board for lethal autonomy not detected',
        standard: 'LA-003',
        remediation: 'Establish review board for autonomous lethal action exceptions'
      });
    }

    return score;
  }

  private checkResponseTime(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    const hasRealTimeResponse = components.some(c =>
      c.capabilities.includes('real_time_response') || c.capabilities.includes('fast_response')
    );
    if (hasRealTimeResponse) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'high',
        description: 'Real-time response capability not detected',
        standard: 'RT-001',
        remediation: 'Implement real-time response capabilities'
      });
    }

    const hasFastEngagement = components.some(c =>
      c.capabilities.includes('fast_engagement') || c.capabilities.includes('rapid_engagement')
    );
    if (hasFastEngagement) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Fast engagement capability not detected',
        standard: 'RT-002',
        remediation: 'Implement rapid engagement capabilities'
      });
    }

    const hasAbortResponse = components.some(c =>
      c.capabilities.includes('abort_response') || c.capabilities.includes('quick_abort')
    );
    if (hasAbortResponse) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'high',
        description: 'Quick abort response capability not detected',
        standard: 'RT-003',
        remediation: 'Implement quick abort response capabilities'
      });
    }

    const hasMonitoring = components.some(c =>
      c.capabilities.includes('performance_monitoring') || c.capabilities.includes('response_monitoring')
    );
    if (hasMonitoring) {
      score += 0.15;
    } else {
      issues.push({
        severity: 'low',
        description: 'Response time monitoring not detected',
        standard: 'RT-004',
        remediation: 'Implement response time monitoring and alerting'
      });
    }

    return score;
  }

  private checkAutonomyRestrictions(components: Cjadc2Component[]): boolean {
    const hasLethalRestriction = components.some(c =>
      c.capabilities.includes('lethal_restriction') || c.capabilities.includes('no_lethal_autonomy')
    );
    const hasStrategicRestriction = components.some(c =>
      c.capabilities.includes('strategic_restriction') || c.capabilities.includes('no_strategic_autonomy')
    );

    return hasLethalRestriction && hasStrategicRestriction;
  }

  private generateRecommendations(score: number, issues: AssessmentIssue[]): string[] {
    const recommendations: string[] = [];

    if (score < 50) {
      recommendations.push('Critical: Establish minimum engagement authority controls');
      recommendations.push('Implement human-in-the-loop for all lethal actions');
    }

    if (score < 80) {
      recommendations.push('Enhance autonomous action restrictions and oversight');
      recommendations.push('Improve response time capabilities');
    }

    const criticalIssues = issues.filter(i => i.severity === 'critical');
    if (criticalIssues.length > 0) {
      recommendations.push(`Address ${criticalIssues.length} critical issues immediately`);
    }

    return recommendations;
  }
}
