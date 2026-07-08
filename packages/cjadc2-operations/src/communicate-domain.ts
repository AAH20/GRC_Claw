import {
  Cjadc2Domain,
  Cjadc2Component,
  ComponentType,
  DomainAssessment,
  AssessmentIssue,
  InteroperabilityStandard
} from './types';

export class CommunicateDomain {
  private readonly INTEROPERABILITY_STANDARDS = [
    InteroperabilityStandard.LINK_16,
    InteroperabilityStandard.LINK_22,
    InteroperabilityStandard.STANAG_4586,
    InteroperabilityStandard.STANAG_5500,
    InteroperabilityStandard.VMF
  ];

  assess(components: Cjadc2Component[]): DomainAssessment {
    const issues: AssessmentIssue[] = [];
    let score = 0;
    const maxScore = 100;

    const networkScore = this.checkNetworkSecurity(components, issues);
    score += networkScore * 25;

    const dataScore = this.checkDataSharing(components, issues);
    score += dataScore * 25;

    const interopScore = this.checkInteroperability(components, issues);
    score += interopScore * 25;

    const encryptionScore = this.checkEncryption(components, issues);
    score += encryptionScore * 25;

    return {
      domain: Cjadc2Domain.COMMUNICATE,
      score: Math.round(score),
      maxScore,
      status: score >= 80 ? 'compliant' : score >= 50 ? 'partial' : 'non_compliant',
      issues,
      recommendations: this.generateRecommendations(score, issues),
      componentsAssessed: components.length,
      timestamp: new Date()
    };
  }

  private checkNetworkSecurity(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    const hasEncryption = components.some(c =>
      c.security.some(s => s.control === 'encryption' && s.status === 'met')
    );
    if (hasEncryption) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'critical',
        description: 'Network encryption not detected',
        standard: 'NS-001',
        remediation: 'Implement network encryption for all communications'
      });
    }

    const hasAuthentication = components.some(c =>
      c.security.some(s => s.control === 'authentication' && s.status === 'met')
    );
    if (hasAuthentication) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'critical',
        description: 'Network authentication not detected',
        standard: 'NS-002',
        remediation: 'Implement network authentication for all users and devices'
      });
    }

    const hasAccessControl = components.some(c =>
      c.security.some(s => s.control === 'access_control' && s.status === 'met')
    );
    if (hasAccessControl) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'high',
        description: 'Network access control not detected',
        standard: 'NS-003',
        remediation: 'Implement network access control mechanisms'
      });
    }

    const hasIntrusionDetection = components.some(c =>
      c.security.some(s => s.control === 'intrusion_detection' && s.status === 'met')
    );
    if (hasIntrusionDetection) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Intrusion detection not detected',
        standard: 'NS-004',
        remediation: 'Implement network intrusion detection systems'
      });
    }

    const hasSegmentation = components.some(c =>
      c.security.some(s => s.control === 'network_segmentation' && s.status === 'met')
    );
    if (hasSegmentation) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'high',
        description: 'Network segmentation not detected',
        standard: 'NS-005',
        remediation: 'Implement network segmentation for security zones'
      });
    }

    return score;
  }

  private checkDataSharing(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    const hasCrossDomain = components.some(c =>
      c.capabilities.includes('cross_domain') || c.capabilities.includes('cross_domain_solution')
    );
    if (hasCrossDomain) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'high',
        description: 'Cross-domain data sharing capability not detected',
        standard: 'DS-001',
        remediation: 'Implement cross-domain data sharing solutions'
      });
    }

    const hasSemanticInterop = components.some(c =>
      c.capabilities.includes('semantic_interop') || c.capabilities.includes('data_model')
    );
    if (hasSemanticInterop) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Semantic interoperability not detected',
        standard: 'DS-002',
        remediation: 'Implement semantic data models for interoperability'
      });
    }

    const hasFormatCompliance = components.some(c =>
      c.capabilities.includes('stanag_format') || c.capabilities.includes('nato_format')
    );
    if (hasFormatCompliance) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'medium',
        description: 'NATO format compliance not detected',
        standard: 'DS-003',
        remediation: 'Implement NATO STANAG data format compliance'
      });
    }

    const hasDisseminationControl = components.some(c =>
      c.capabilities.includes('dissemination_control') || c.capabilities.includes('need_to_know')
    );
    if (hasDisseminationControl) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Dissemination control not detected',
        standard: 'DS-004',
        remediation: 'Implement dissemination control and need-to-know policies'
      });
    }

    return score;
  }

  private checkInteroperability(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;
    let standardsMet = 0;

    const networkComponents = components.filter(c =>
      c.type === ComponentType.NETWORK || c.type === ComponentType.DATA_LINK
    );

    const supportedStandards = new Set<InteroperabilityStandard>();
    networkComponents.forEach(c => {
      c.interoperability.forEach(i => {
        supportedStandards.add(i.standard);
      });
    });

    this.INTEROPERABILITY_STANDARDS.forEach(standard => {
      if (supportedStandards.has(standard)) {
        standardsMet++;
      }
    });

    const standardsRatio = standardsMet / this.INTEROPERABILITY_STANDARDS.length;
    score += standardsRatio * 0.4;

    if (standardsRatio < 0.5) {
      issues.push({
        severity: 'high',
        description: `Insufficient interoperability standards: ${standardsMet}/${this.INTEROPERABILITY_STANDARDS.length}`,
        standard: 'IO-001',
        remediation: 'Implement additional interoperability standards'
      });
    }

    const hasMultiLink = networkComponents.some(c =>
      c.capabilities.includes('multi_link') || c.capabilities.includes('link_aggregation')
    );
    if (hasMultiLink) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Multi-link capability not detected',
        standard: 'IO-002',
        remediation: 'Implement multi-link communication capabilities'
      });
    }

    const hasProtocolAdaptation = networkComponents.some(c =>
      c.capabilities.includes('protocol_adaptation') || c.capabilities.includes('protocol_translation')
    );
    if (hasProtocolAdaptation) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Protocol adaptation capability not detected',
        standard: 'IO-003',
        remediation: 'Implement protocol adaptation and translation capabilities'
      });
    }

    return score;
  }

  private checkEncryption(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    const hasStrongEncryption = components.some(c =>
      c.capabilities.includes('aes256') || c.capabilities.includes('strong_encryption')
    );
    if (hasStrongEncryption) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'high',
        description: 'Strong encryption (AES-256+) not detected',
        standard: 'ENC-001',
        remediation: 'Implement AES-256 or stronger encryption'
      });
    }

    const hasKeyManagement = components.some(c =>
      c.capabilities.includes('key_management') || c.capabilities.includes('pki')
    );
    if (hasKeyManagement) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'high',
        description: 'Key management capability not detected',
        standard: 'ENC-002',
        remediation: 'Implement robust key management systems'
      });
    }

    const hasForwardSecrecy = components.some(c =>
      c.capabilities.includes('forward_secrecy') || c.capabilities.includes('perfect_forward_secrecy')
    );
    if (hasForwardSecrecy) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Forward secrecy not detected',
        standard: 'ENC-003',
        remediation: 'Implement perfect forward secrecy'
      });
    }

    const hasQuantumReadiness = components.some(c =>
      c.capabilities.includes('quantum_resistant') || c.capabilities.includes('post_quantum')
    );
    if (hasQuantumReadiness) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'low',
        description: 'Quantum-resistant encryption not detected',
        standard: 'ENC-004',
        remediation: 'Consider implementing quantum-resistant encryption algorithms'
      });
    }

    return score;
  }

  private generateRecommendations(score: number, issues: AssessmentIssue[]): string[] {
    const recommendations: string[] = [];

    if (score < 50) {
      recommendations.push('Critical: Establish minimum network security controls');
      recommendations.push('Implement encryption for all communications');
    }

    if (score < 80) {
      recommendations.push('Enhance interoperability standards compliance');
      recommendations.push('Implement cross-domain data sharing capabilities');
    }

    const criticalIssues = issues.filter(i => i.severity === 'critical');
    if (criticalIssues.length > 0) {
      recommendations.push(`Address ${criticalIssues.length} critical issues immediately`);
    }

    return recommendations;
  }
}
