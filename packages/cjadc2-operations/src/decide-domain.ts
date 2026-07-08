import {
  Cjadc2Domain,
  Cjadc2Component,
  ComponentType,
  ComponentStatus,
  DomainAssessment,
  AssessmentIssue
} from './types';

export class DecideDomain {
  private readonly C2_REQUIREMENTS = {
    minCommandNodes: 1,
    redundancyRequired: true,
    chainOfCommand: true,
    authorityLevels: ['strategic', 'operational', 'tactical']
  };

  private readonly DECISION_SUPPORT_REQUIREMENTS = {
    aiAssistance: true,
    humanInTheLoop: true,
    decisionTimeMs: 30000,
    confidenceThreshold: 0.8
  };

  private readonly AI_DECISION_REQUIREMENTS = {
    explainabilityRequired: true,
    biasMonitoring: true,
    overrideCapability: true,
    auditLogging: true
  };

  private readonly HITL_REQUIREMENTS = {
    humanApprovalRequired: true,
    abortCapability: true,
    overrideAuthority: true,
    notificationSystem: true
  };

  assess(components: Cjadc2Component[]): DomainAssessment {
    const issues: AssessmentIssue[] = [];
    let score = 0;
    const maxScore = 100;

    const c2Score = this.checkCommandAndControl(components, issues);
    score += c2Score * 25;

    const decisionScore = this.checkDecisionSupport(components, issues);
    score += decisionScore * 25;

    const aiScore = this.checkAIDecision(components, issues);
    score += aiScore * 25;

    const hitlScore = this.checkHumanInTheLoop(components, issues);
    score += hitlScore * 25;

    return {
      domain: Cjadc2Domain.DECIDE,
      score: Math.round(score),
      maxScore,
      status: score >= 80 ? 'compliant' : score >= 50 ? 'partial' : 'non_compliant',
      issues,
      recommendations: this.generateRecommendations(score, issues),
      componentsAssessed: components.length,
      timestamp: new Date()
    };
  }

  private checkCommandAndControl(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    const commandNodes = components.filter(c => c.type === ComponentType.COMMAND);
    const operationalNodes = commandNodes.filter(c => c.status === ComponentStatus.OPERATIONAL);

    let score = 0;

    if (operationalNodes.length >= this.C2_REQUIREMENTS.minCommandNodes) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'critical',
        description: `Insufficient command nodes: ${operationalNodes.length}/${this.C2_REQUIREMENTS.minCommandNodes}`,
        standard: 'C2-001',
        remediation: 'Establish minimum command and control nodes'
      });
    }

    const hasRedundancy = this.checkC2Redundancy(commandNodes);
    if (hasRedundancy) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'high',
        description: 'C2 redundancy not established',
        standard: 'C2-002',
        remediation: 'Implement redundant command and control capabilities'
      });
    }

    const hasChainOfCommand = this.checkChainOfCommand(components);
    if (hasChainOfCommand) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'high',
        description: 'Chain of command not properly established',
        standard: 'C2-003',
        remediation: 'Define and implement clear chain of command structure'
      });
    }

    const hasAuthorityLevels = this.checkAuthorityLevels(components);
    if (hasAuthorityLevels) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Authority levels not fully defined',
        standard: 'C2-004',
        remediation: 'Establish strategic, operational, and tactical authority levels'
      });
    }

    return score;
  }

  private checkDecisionSupport(components: Cjadc2Component[]): number {
    let score = 0;

    const hasDecisionAids = components.some(c =>
      c.type === ComponentType.DECISION_AID || c.type === ComponentType.AI_SYSTEM
    );
    if (hasDecisionAids) {
      score += 0.4;
    }

    const hasSituationalAwareness = components.some(c =>
      c.capabilities.includes('situational_awareness') || c.capabilities.includes('sa_display')
    );
    if (hasSituationalAwareness) {
      score += 0.3;
    }

    const hasDecisionTimeCompliance = this.checkDecisionTime(components);
    if (hasDecisionTimeCompliance) {
      score += 0.3;
    }

    return score;
  }

  private checkAIDecision(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    const aiComponents = components.filter(c => c.type === ComponentType.AI_SYSTEM);

    if (aiComponents.length === 0) {
      issues.push({
        severity: 'low',
        description: 'No AI decision support systems detected',
        standard: 'AI-001',
        remediation: 'Consider deploying AI-assisted decision support capabilities'
      });
      return 0.5;
    }

    let score = 0;

    const hasExplainability = aiComponents.some(c =>
      c.capabilities.includes('explainability') || c.capabilities.includes('xai')
    );
    if (hasExplainability) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'high',
        description: 'AI explainability capability not detected',
        standard: 'AI-002',
        remediation: 'Implement explainable AI (XAI) capabilities'
      });
    }

    const hasBiasMonitoring = aiComponents.some(c =>
      c.capabilities.includes('bias_monitoring') || c.capabilities.includes('fairness')
    );
    if (hasBiasMonitoring) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'medium',
        description: 'AI bias monitoring not detected',
        standard: 'AI-003',
        remediation: 'Implement AI bias monitoring and mitigation'
      });
    }

    const hasOverride = aiComponents.some(c =>
      c.capabilities.includes('override') || c.capabilities.includes('manual_override')
    );
    if (hasOverride) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'high',
        description: 'AI override capability not detected',
        standard: 'AI-004',
        remediation: 'Implement human override capability for AI decisions'
      });
    }

    const hasAuditLogging = aiComponents.some(c =>
      c.capabilities.includes('audit_logging') || c.capabilities.includes('logging')
    );
    if (hasAuditLogging) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'medium',
        description: 'AI audit logging not detected',
        standard: 'AI-005',
        remediation: 'Implement comprehensive AI decision audit logging'
      });
    }

    return score;
  }

  private checkHumanInTheLoop(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    const hasHumanApproval = components.some(c =>
      c.capabilities.includes('human_approval') || c.capabilities.includes('approval_workflow')
    );
    if (hasHumanApproval) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'high',
        description: 'Human approval workflow not detected',
        standard: 'HITL-001',
        remediation: 'Implement human approval workflow for critical decisions'
      });
    }

    const hasAbortCapability = components.some(c =>
      c.capabilities.includes('abort') || c.capabilities.includes('emergency_stop')
    );
    if (hasAbortCapability) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'critical',
        description: 'Abort capability not detected',
        standard: 'HITL-002',
        remediation: 'Implement emergency abort capability for all operations'
      });
    }

    const hasOverrideAuthority = components.some(c =>
      c.capabilities.includes('override_authority') || c.capabilities.includes('command_override')
    );
    if (hasOverrideAuthority) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'high',
        description: 'Override authority not established',
        standard: 'HITL-003',
        remediation: 'Establish clear override authority and procedures'
      });
    }

    const hasNotification = components.some(c =>
      c.capabilities.includes('notification') || c.capabilities.includes('alerting')
    );
    if (hasNotification) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Notification system not detected',
        standard: 'HITL-004',
        remediation: 'Implement notification system for decision alerts'
      });
    }

    return score;
  }

  private checkC2Redundancy(commandNodes: Cjadc2Component[]): boolean {
    return commandNodes.length >= 2;
  }

  private checkChainOfCommand(components: Cjadc2Component[]): boolean {
    const hasCommandStructure = components.some(c =>
      c.capabilities.includes('command_structure') || c.type === ComponentType.COMMAND
    );
    return hasCommandStructure;
  }

  private checkAuthorityLevels(components: Cjadc2Component[]): boolean {
    const hasStrategic = components.some(c =>
      c.capabilities.includes('strategic') || c.capabilities.includes('strategic_authority')
    );
    const hasOperational = components.some(c =>
      c.capabilities.includes('operational') || c.capabilities.includes('operational_authority')
    );
    const hasTactical = components.some(c =>
      c.capabilities.includes('tactical') || c.capabilities.includes('tactical_authority')
    );
    return hasStrategic && hasOperational && hasTactical;
  }

  private checkDecisionTime(components: Cjadc2Component[]): boolean {
    return components.some(c =>
      c.capabilities.includes('fast_decision') || c.capabilities.includes('low_latency')
    );
  }

  private generateRecommendations(score: number, issues: AssessmentIssue[]): string[] {
    const recommendations: string[] = [];

    if (score < 50) {
      recommendations.push('Critical: Establish minimum C2 capability with redundancy');
      recommendations.push('Implement human-in-the-loop decision workflows');
    }

    if (score < 80) {
      recommendations.push('Enhance decision support with AI assistance');
      recommendations.push('Improve situational awareness displays');
    }

    const criticalIssues = issues.filter(i => i.severity === 'critical');
    if (criticalIssues.length > 0) {
      recommendations.push(`Address ${criticalIssues.length} critical issues immediately`);
    }

    return recommendations;
  }
}
