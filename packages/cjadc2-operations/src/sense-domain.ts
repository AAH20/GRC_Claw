import {
  Cjadc2Domain,
  Cjadc2Component,
  ComponentType,
  ComponentStatus,
  DomainAssessment,
  AssessmentIssue
} from './types';

export class SenseDomain {
  private readonly ISR_REQUIREMENTS = {
    minSensors: 2,
    sensorTypes: ['radar', 'electro_optical', 'infrared', 'sigint', 'masint'],
    fusionCapability: true,
    realTimeProcessing: true
  };

  private readonly SENSOR_FUSION_REQUIREMENTS = {
    minDataSources: 2,
    correlationAccuracy: 0.85,
    trackManagement: true,
    multiDomain: true
  };

  assess(components: Cjadc2Component[]): DomainAssessment {
    const issues: AssessmentIssue[] = [];
    let score = 0;
    const maxScore = 100;

    const isCompliant = this.checkISRCompliance(components, issues);
    if (isCompliant) score += 25;

    const fusionScore = this.checkSensorFusion(components, issues);
    score += fusionScore * 25;

    const processingScore = this.checkDataProcessing(components, issues);
    score += processingScore * 25;

    const analysisScore = this.checkRealTimeAnalysis(components, issues);
    score += analysisScore * 25;

    return {
      domain: Cjadc2Domain.SENSE,
      score: Math.round(score),
      maxScore,
      status: score >= 80 ? 'compliant' : score >= 50 ? 'partial' : 'non_compliant',
      issues,
      recommendations: this.generateRecommendations(score, issues),
      componentsAssessed: components.length,
      timestamp: new Date()
    };
  }

  private checkISRCompliance(components: Cjadc2Component[], issues: AssessmentIssue[]): boolean {
    const sensors = components.filter(c => c.type === ComponentType.SENSOR);
    const operationalSensors = sensors.filter(c => c.status === ComponentStatus.OPERATIONAL);

    if (operationalSensors.length < this.ISR_REQUIREMENTS.minSensors) {
      issues.push({
        severity: 'high',
        description: `Insufficient operational sensors: ${operationalSensors.length}/${this.ISR_REQUIREMENTS.minSensors} required`,
        standard: 'ISR-001',
        remediation: 'Deploy additional sensor assets to meet minimum requirements'
      });
      return false;
    }

    const sensorTypes = new Set(operationalSensors.map(s => this.classifySensorType(s)));
    const hasRequiredTypes = this.ISR_REQUIREMENTS.sensorTypes.some(type => sensorTypes.has(type));

    if (!hasRequiredTypes) {
      issues.push({
        severity: 'medium',
        description: 'Missing required sensor types for comprehensive ISR coverage',
        standard: 'ISR-002',
        remediation: 'Diversify sensor types to include radar, EO/IR, SIGINT, and MASINT'
      });
    }

    return operationalSensors.length >= this.ISR_REQUIREMENTS.minSensors;
  }

  private checkSensorFusion(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    const sensors = components.filter(c => c.type === ComponentType.SENSOR);

    let score = 0;

    if (sensors.length >= this.SENSOR_FUSION_REQUIREMENTS.minDataSources) {
      score += 0.4;
    } else {
      issues.push({
        severity: 'high',
        description: `Insufficient data sources for fusion: ${sensors.length}/${this.SENSOR_FUSION_REQUIREMENTS.minDataSources}`,
        standard: 'SF-001',
        remediation: 'Increase sensor count to enable multi-source fusion'
      });
    }

    const hasFusionCapability = components.some(c =>
      c.capabilities.includes('fusion') || c.capabilities.includes('data_correlation')
    );
    if (hasFusionCapability) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'medium',
        description: 'No fusion capability detected in sensor network',
        standard: 'SF-002',
        remediation: 'Deploy sensor fusion processing capability'
      });
    }

    const hasTrackManagement = components.some(c =>
      c.capabilities.includes('track_management') || c.capabilities.includes('multi_track')
    );
    if (hasTrackManagement) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Track management capability not detected',
        standard: 'SF-003',
        remediation: 'Implement automated track management and correlation'
      });
    }

    return score;
  }

  private checkDataProcessing(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    const hasRealTimeProcessing = components.some(c =>
      c.capabilities.includes('real_time_processing') || c.capabilities.includes('stream_processing')
    );
    if (hasRealTimeProcessing) {
      score += 0.35;
    } else {
      issues.push({
        severity: 'high',
        description: 'Real-time data processing capability not detected',
        standard: 'DP-001',
        remediation: 'Implement real-time data processing pipelines'
      });
    }

    const hasCompression = components.some(c =>
      c.capabilities.includes('data_compression') || c.capabilities.includes('compression')
    );
    if (hasCompression) {
      score += 0.25;
    } else {
      issues.push({
        severity: 'low',
        description: 'Data compression capability not detected',
        standard: 'DP-002',
        remediation: 'Enable data compression for bandwidth optimization'
      });
    }

    const hasDataRetention = components.some(c =>
      c.capabilities.includes('data_retention') || c.capabilities.includes('storage')
    );
    if (hasDataRetention) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'low',
        description: 'Data retention capability not detected',
        standard: 'DP-003',
        remediation: 'Implement data retention policies and storage'
      });
    }

    const hasQualityAssurance = components.some(c =>
      c.capabilities.includes('data_quality') || c.capabilities.includes('validation')
    );
    if (hasQualityAssurance) {
      score += 0.2;
    } else {
      issues.push({
        severity: 'low',
        description: 'Data quality assurance not detected',
        standard: 'DP-004',
        remediation: 'Implement data quality validation checks'
      });
    }

    return score;
  }

  private checkRealTimeAnalysis(components: Cjadc2Component[], issues: AssessmentIssue[]): number {
    let score = 0;

    const hasAutomatedClassification = components.some(c =>
      c.capabilities.includes('automated_classification') || c.capabilities.includes('ml_classification')
    );
    if (hasAutomatedClassification) {
      score += 0.35;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Automated classification capability not detected',
        standard: 'RTA-001',
        remediation: 'Deploy ML-based automated classification systems'
      });
    }

    const hasThreatAssessment = components.some(c =>
      c.capabilities.includes('threat_assessment') || c.capabilities.includes('threat_detection')
    );
    if (hasThreatAssessment) {
      score += 0.35;
    } else {
      issues.push({
        severity: 'high',
        description: 'Threat assessment capability not detected',
        standard: 'RTA-002',
        remediation: 'Implement automated threat assessment capabilities'
      });
    }

    const hasRealTimeAlerting = components.some(c =>
      c.capabilities.includes('real_time_alerting') || c.capabilities.includes('alerting')
    );
    if (hasRealTimeAlerting) {
      score += 0.3;
    } else {
      issues.push({
        severity: 'medium',
        description: 'Real-time alerting capability not detected',
        standard: 'RTA-003',
        remediation: 'Implement real-time alerting for critical events'
      });
    }

    return score;
  }

  private classifySensorType(sensor: Cjadc2Component): string {
    const name = sensor.name.toLowerCase();
    const capabilities = sensor.capabilities.join(' ').toLowerCase();

    if (name.includes('radar') || capabilities.includes('radar')) return 'radar';
    if (name.includes('eo') || name.includes('electro') || capabilities.includes('electro_optical')) return 'electro_optical';
    if (name.includes('ir') || name.includes('infrared') || capabilities.includes('infrared')) return 'infrared';
    if (name.includes('sigint') || capabilities.includes('sigint')) return 'sigint';
    if (name.includes('masint') || capabilities.includes('masint')) return 'masint';

    return 'unknown';
  }

  private generateRecommendations(score: number, issues: AssessmentIssue[]): string[] {
    const recommendations: string[] = [];

    if (score < 50) {
      recommendations.push('Critical: Establish minimum ISR capability with diverse sensor types');
      recommendations.push('Deploy multi-sensor fusion processing capability');
    }

    if (score < 80) {
      recommendations.push('Enhance sensor network with additional operational assets');
      recommendations.push('Implement real-time data processing and analysis pipelines');
    }

    const highIssues = issues.filter(i => i.severity === 'high');
    if (highIssues.length > 0) {
      recommendations.push(`Address ${highIssues.length} high-severity issues immediately`);
    }

    return recommendations;
  }
}
