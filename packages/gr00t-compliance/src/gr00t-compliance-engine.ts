import crypto from 'crypto';
import type {
  Gr00tModel,
  RobotConfig,
  DeploymentConfig,
  MilitaryOperation,
  Cjadc2Component,
  ComplianceAssessment,
  ComplianceReport,
  ComplianceGap,
  ComplianceRecommendation,
  FrameworkType,
} from './types';

import { checkItarCompliance, generateItarComplianceReport } from './itar-compliance';
import { assessDodCompliance, mapGr00tToDodControls } from './dod-compliance';
import { assessCjadc2Compliance } from './cjadc2-framework';
import { assessAutonomousWeaponsCompliance } from './autonomous-weapons-policy';

interface FrameworkAssessmentResult {
  framework: FrameworkType;
  assessment: ComplianceAssessment;
}

export class Gr00tComplianceEngine {
  private assessments: Map<string, ComplianceAssessment[]> = new Map();
  private reports: Map<string, ComplianceReport> = new Map();

  assessModelCompliance(
    model: Gr00tModel,
    frameworks: FrameworkType[],
    config?: DeploymentConfig
  ): FrameworkAssessmentResult[] {
    const results: FrameworkAssessmentResult[] = [];

    for (const framework of frameworks) {
      let assessment: ComplianceAssessment;

      switch (framework) {
        case 'ITAR': {
          const itarResult = checkItarCompliance(model, config?.robot.authorizedCountries ?? []);
          assessment = {
            framework: 'ITAR',
            timestamp: new Date().toISOString(),
            modelId: model.id,
            overallScore: itarResult.compliant ? 100 : 0,
            status: itarResult.compliant ? 'PASS' : 'FAIL',
            gaps: itarResult.compliant ? [] : [{
              id: 'ITAR-GAP-001',
              controlId: 'ITAR-22-CFR-120',
              framework: 'ITAR',
              description: itarResult.findings.join('; '),
              riskLevel: 'CRITICAL',
              remediation: 'Address ITAR compliance gaps',
              deadline: 'IMMEDIATE',
            }],
            recommendations: [],
            controlsChecked: itarResult.restrictions.length,
            controlsPassed: itarResult.compliant ? itarResult.restrictions.length : 0,
            controlsFailed: itarResult.compliant ? 0 : itarResult.findings.length,
          };
          break;
        }

        case 'DOD_5200_21':
        case 'NIST_800_171': {
          const dodResult = assessDodCompliance(model, config ?? this.createDefaultConfig(model));
          assessment = {
            framework,
            timestamp: new Date().toISOString(),
            modelId: model.id,
            overallScore: Math.round((dodResult.controlsPassed / dodResult.controlsAssessed) * 100),
            status: dodResult.compliant ? 'PASS' : dodResult.controlsFailed > 0 ? 'FAIL' : 'PARTIAL',
            gaps: dodResult.controlsFailed > 0 ? [{
              id: 'DOD-GAP-001',
              controlId: 'NIST-800-171',
              framework,
              description: dodResult.findings.join('; '),
              riskLevel: 'HIGH',
              remediation: 'Address DoD compliance gaps',
              deadline: '30 days',
            }] : [],
            recommendations: [],
            controlsChecked: dodResult.controlsAssessed,
            controlsPassed: dodResult.controlsPassed,
            controlsFailed: dodResult.controlsFailed,
          };
          break;
        }

        case 'CMMC_L1':
        case 'CMMC_L2':
        case 'CMMC_L3': {
          const level = framework === 'CMMC_L1' ? 1 : framework === 'CMMC_L2' ? 2 : 3;
          const dodResult = assessDodCompliance(model, config ?? this.createDefaultConfig(model), level);
          assessment = {
            framework,
            timestamp: new Date().toISOString(),
            modelId: model.id,
            overallScore: Math.round((dodResult.controlsPassed / dodResult.controlsAssessed) * 100),
            status: dodResult.cmmcLevel >= level ? 'PASS' : 'FAIL',
            gaps: dodResult.cmmcLevel < level ? [{
              id: `CMMC-L${level}-GAP`,
              controlId: `CMMC-L${level}`,
              framework,
              description: `Does not meet CMMC Level ${level} requirements. Current level: ${dodResult.cmmcLevel}`,
              riskLevel: level >= 3 ? 'CRITICAL' : 'HIGH',
              remediation: `Implement additional controls for CMMC Level ${level}`,
              deadline: '60 days',
            }] : [],
            recommendations: [],
            controlsChecked: dodResult.controlsAssessed,
            controlsPassed: dodResult.controlsPassed,
            controlsFailed: dodResult.controlsFailed,
          };
          break;
        }

        case 'CJADC2': {
          const cjadc2Result = assessCjadc2Compliance(model, []);
          assessment = {
            framework: 'CJADC2',
            timestamp: new Date().toISOString(),
            modelId: model.id,
            overallScore: cjadc2Result.readiness.score,
            status: cjadc2Result.readiness.score >= 80 ? 'PASS' : cjadc2Result.readiness.score >= 50 ? 'PARTIAL' : 'FAIL',
            gaps: cjadc2Result.gaps,
            recommendations: cjadc2Result.recommendations,
            controlsChecked: cjadc2Result.readiness.score,
            controlsPassed: Math.round(cjadc2Result.readiness.score * 0.8),
            controlsFailed: Math.round(cjadc2Result.readiness.score * 0.2),
          };
          break;
        }

        default: {
          assessment = {
            framework,
            timestamp: new Date().toISOString(),
            modelId: model.id,
            overallScore: 0,
            status: 'NOT_APPLICABLE',
            gaps: [],
            recommendations: [],
            controlsChecked: 0,
            controlsPassed: 0,
            controlsFailed: 0,
          };
        }
      }

      results.push({ framework, assessment });
    }

    const modelAssessments = this.assessments.get(model.id) ?? [];
    modelAssessments.push(...results.map(r => r.assessment));
    this.assessments.set(model.id, modelAssessments);

    return results;
  }

  assessRobotDeployment(config: DeploymentConfig): {
    compliance: ComplianceAssessment[];
    overallStatus: 'PASS' | 'FAIL' | 'PARTIAL';
    overallScore: number;
  } {
    const frameworks: FrameworkType[] = ['ITAR', 'DOD_5200_21', 'NIST_800_171'];

    if (config.classification === 'SECRET' || config.classification === 'TOP_SECRET') {
      frameworks.push('CMMC_L2');
    }

    const results = this.assessModelCompliance(config.model, frameworks, config);

    const overallScore = results.reduce((sum, r) => sum + r.assessment.overallScore, 0) / results.length;
    const hasFailure = results.some(r => r.assessment.status === 'FAIL');
    const hasPartial = results.some(r => r.assessment.status === 'PARTIAL');

    return {
      compliance: results.map(r => r.assessment),
      overallStatus: hasFailure ? 'FAIL' : hasPartial ? 'PARTIAL' : 'PASS',
      overallScore: Math.round(overallScore),
    };
  }

  assessCjadc2Integration(
    model: Gr00tModel,
    components: Cjadc2Component[]
  ): {
    readiness: ReturnType<typeof assessCjadc2Compliance>['readiness'];
    gaps: ComplianceGap[];
    recommendations: ComplianceRecommendation[];
  } {
    const result = assessCjadc2Compliance(model, components);

    return {
      readiness: result.readiness,
      gaps: result.gaps,
      recommendations: result.recommendations,
    };
  }

  generateComplianceReport(
    model: Gr00tModel,
    config: DeploymentConfig,
    operation?: MilitaryOperation
  ): ComplianceReport {
    const frameworks: FrameworkType[] = ['ITAR', 'DOD_5200_21', 'NIST_800_171'];

    if (config.classification === 'SECRET' || config.classification === 'TOP_SECRET') {
      frameworks.push('CMMC_L2', 'CJADC2');
    }

    if (config.classification === 'TOP_SECRET') {
      frameworks.push('CMMC_L3');
    }

    const frameworkResults = this.assessModelCompliance(model, frameworks, config);

    let weaponCompliance = null;
    if (operation) {
      weaponCompliance = assessAutonomousWeaponsCompliance(model, operation);
    }

    const itarReport = generateItarComplianceReport(model, config.robot.authorizedCountries);

    const summary = {
      totalControls: frameworkResults.reduce((sum, r) => sum + r.assessment.controlsChecked, 0),
      passed: frameworkResults.reduce((sum, r) => sum + r.assessment.controlsPassed, 0),
      failed: frameworkResults.reduce((sum, r) => sum + r.assessment.controlsFailed, 0),
      partial: 0,
      notApplicable: 0,
    };

    const overallScore = frameworkResults.length > 0
      ? Math.round(frameworkResults.reduce((sum, r) => sum + r.assessment.overallScore, 0) / frameworkResults.length)
      : 0;

    const hasCriticalFailure = frameworkResults.some(r => r.assessment.status === 'FAIL');
    const overallStatus = hasCriticalFailure ? 'FAIL' : overallScore >= 80 ? 'PASS' : 'PARTIAL';

    const criticalFindings: ComplianceGap[] = [
      ...itarReport.gaps,
      ...(weaponCompliance?.gaps.filter(g => g.riskLevel === 'CRITICAL') ?? []),
      ...frameworkResults.flatMap(r => r.assessment.gaps.filter(g => g.riskLevel === 'CRITICAL')),
    ];

    let deploymentRecommendation = 'APPROVED';
    if (hasCriticalFailure) {
      deploymentRecommendation = 'DENIED - Critical compliance failures detected';
    } else if (overallScore < 80) {
      deploymentRecommendation = 'CONDITIONAL - Requires remediation before deployment';
    }

    const report: ComplianceReport = {
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      modelId: model.id,
      robotId: config.robot.id,
      overallStatus,
      overallScore,
      frameworkResults: frameworkResults.map(r => r.assessment),
      summary,
      criticalFindings,
      exportControlStatus: {
        itarCompliant: itarReport.result.compliant,
        earCompliant: true,
        exportLicenseRequired: itarReport.result.licenseRequired,
        restrictedCountries: config.robot.authorizedCountries,
        classification: model.exportClassification,
      },
      CJADC2Readiness: frameworkResults.find(r => r.framework === 'CJADC2')?.assessment
        ? { score: overallScore, domainScores: { SENSE: 0, DECIDE: 0, ACT: 0, COMMUNICATE: 0 }, interoperabilityLevel: 'Partial', securityPosture: 'Adequate' }
        : { score: 0, domainScores: { SENSE: 0, DECIDE: 0, ACT: 0, COMMUNICATE: 0 }, interoperabilityLevel: 'Not Assessed', securityPosture: 'Unknown' },
      deploymentRecommendation,
    };

    this.reports.set(report.id, report);

    return report;
  }

  mapToMilitaryControls(
    model: Gr00tModel,
    framework: FrameworkType
  ): {
    dodControls: ReturnType<typeof mapGr00tToDodControls>;
    itarControls: ReturnType<typeof checkItarCompliance>;
    cjadc2Controls: ReturnType<typeof assessCjadc2Compliance>;
    weaponPolicy: ReturnType<typeof assessAutonomousWeaponsCompliance>;
  } {
    const defaultConfig = this.createDefaultConfig(model);
    const defaultOperation: MilitaryOperation = {
      id: 'DEFAULT-OP',
      name: 'Default Assessment',
      type: 'assessment',
      domain: 'LAND',
      classification: model.exportClassification,
      permittedEmbodiments: [model.embodimentTag],
      humanOversightRequired: true,
      engagementAuthority: 'Defensive',
      rulesOfEngagement: 'Standard ROE',
    };

    return {
      dodControls: mapGr00tToDodControls(model, defaultConfig),
      itarControls: checkItarCompliance(model, defaultConfig.robot.authorizedCountries),
      cjadc2Controls: assessCjadc2Compliance(model, []),
      weaponPolicy: assessAutonomousWeaponsCompliance(model, defaultOperation),
    };
  }

  getAssessment(modelId: string): ComplianceAssessment[] {
    return this.assessments.get(modelId) ?? [];
  }

  getReport(reportId: string): ComplianceReport | undefined {
    return this.reports.get(reportId);
  }

  listReports(): ComplianceReport[] {
    return Array.from(this.reports.values());
  }

  private createDefaultConfig(model: Gr00tModel): DeploymentConfig {
    return {
      model,
      robot: {
        id: `robot-${model.id}`,
        name: `Robot for ${model.name}`,
        type: 'MANIPULATOR',
        embodiment: model.embodimentTag,
        location: 'US',
        network: {
          isolated: true,
          vpnRequired: true,
          encryptionStandard: 'AES-256',
          classification: 'UNCLASSIFIED',
        },
        operators: [],
        authorizedCountries: ['US'],
      },
      network: {
        type: 'isolated',
        classification: 'UNCLASSIFIED',
        encryption: 'AES-256',
        monitoring: true,
        intrusionDetection: true,
      },
      security: {
        accessControl: 'RBAC',
        auditLogging: true,
        keyManagement: 'FIPS-140-2',
        patchManagement: 'automated',
        incidentResponse: true,
      },
      classification: 'UNCLASSIFIED',
    };
  }
}

export {
  checkItarCompliance,
  generateItarComplianceReport,
} from './itar-compliance';
export { assessDodCompliance, mapGr00tToDodControls } from './dod-compliance';
export { assessCjadc2Compliance } from './cjadc2-framework';
export { assessAutonomousWeaponsCompliance } from './autonomous-weapons-policy';
