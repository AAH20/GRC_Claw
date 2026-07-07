import { createHash } from 'node:crypto';
import type {
  NemotronModel,
  ComplianceAssessment,
  ComplianceFramework,
  NemotronDeploymentConfig,
  ComplianceReport,
  AiBomEntry,
} from './types.js';
import { assessEuAiAct, getEuAiActGaps } from './eu-ai-act.js';
import { assessNistRmf, getNistGaps } from './nist-ai-rmf.js';
import { assessIso42001 } from './iso-42001.js';
import { generateAiBom, getBomSummary } from './ai-bom.js';

export class NemotronComplianceEngine {
  assessModelCompliance(
    model: NemotronModel,
    frameworks: ComplianceFramework[]
  ): ComplianceAssessment[] {
    const assessments: ComplianceAssessment[] = [];

    for (const framework of frameworks) {
      switch (framework) {
        case 'EU_AI_ACT': {
          const assessment = assessEuAiAct(model);
          const gaps = getEuAiActGaps(assessment);
          const passed = gaps.length === 0;
          const score = passed
            ? 100
            : Math.max(
                0,
                100 - gaps.reduce((sum, g) => {
                  const weight =
                    g.severity === 'critical'
                      ? 15
                      : g.severity === 'high'
                        ? 10
                        : g.severity === 'medium'
                          ? 5
                          : 2;
                  return sum + weight;
                }, 0)
              );
          assessments.push({
            framework: 'EU_AI_ACT',
            score,
            gaps,
            recommendations: [
              `Risk tier: ${assessment.riskTier}`,
              `Conformity assessment: ${assessment.conformityAssessment.passed ? 'PASSED' : 'NEEDS ATTENTION'}`,
              'Implement transparency labels for AI-generated content.',
              'Maintain technical documentation per EU AI Act requirements.',
            ],
            assessedAt: new Date().toISOString(),
          });
          break;
        }
        case 'NIST_AI_RMF': {
          const assessment = assessNistRmf(model);
          const gaps = getNistGaps(assessment);
          const score = assessment.overallScore;
          const recommendations = [
            `Overall NIST AI RMF score: ${score}%`,
            `Risk level: ${assessment.riskLevel}`,
            'Establish continuous monitoring pipeline.',
            'Document accountability assignments for each AI risk domain.',
          ];
          for (const func of assessment.functions) {
            if (func.score < 70) {
              recommendations.push(
                `Improve ${func.function} function controls (current: ${func.score}%).`
              );
            }
          }
          assessments.push({
            framework: 'NIST_AI_RMF',
            score,
            gaps,
            recommendations,
            assessedAt: new Date().toISOString(),
          });
          break;
        }
        case 'ISO_42001': {
          const assessment = assessIso42001(model);
          const score = assessment.overallScore;
          const recommendations = [
            `ISO 42001 Annex A compliance: ${score}%`,
            ...assessment.recommendations,
          ];
          assessments.push({
            framework: 'ISO_42001',
            score,
            gaps: assessment.gaps,
            recommendations,
            assessedAt: new Date().toISOString(),
          });
          break;
        }
      }
    }

    return assessments;
  }

  generateAiBom(model: NemotronModel): AiBomEntry {
    return generateAiBom(model);
  }

  assessDeployment(config: NemotronDeploymentConfig): {
    compliant: boolean;
    score: number;
    issues: string[];
    recommendations: string[];
  } {
    const issues: string[] = [];
    const recommendations: string[] = [];
    let score = 100;

    if (config.security.authRequired && config.security.authMethod === 'api_key') {
      if (config.hardware.gpus >= 4) {
        issues.push('API key authentication on large GPU clusters should be supplemented with mTLS.');
        score -= 5;
      }
    }

    if (!config.security.authRequired) {
      issues.push('Authentication is required for production deployments.');
      score -= 25;
      recommendations.push('Enable authentication immediately.');
    }

    if (!config.security.inputValidation) {
      issues.push('Input validation is not enabled.');
      score -= 10;
      recommendations.push('Enable input validation to prevent prompt injection attacks.');
    }

    if (!config.security.outputFiltering) {
      issues.push('Output filtering is not enabled.');
      score -= 10;
      recommendations.push('Enable output filtering to prevent harmful content generation.');
    }

    if (!config.network.tlsVersion.startsWith('1.3') && !config.network.tlsVersion.startsWith('1.2')) {
      issues.push('TLS version must be 1.2 or higher.');
      score -= 15;
      recommendations.push('Upgrade to TLS 1.3 for maximum security.');
    }

    if (config.security.dataEncryption === 'at-rest' && config.network.exposed) {
      issues.push('Data in transit is not encrypted for externally exposed deployment.');
      score -= 15;
      recommendations.push('Enable in-transit encryption for externally exposed deployments.');
    }

    if (!config.security.auditTrail) {
      issues.push('Audit trail is not enabled.');
      score -= 10;
      recommendations.push('Enable audit trail for compliance and incident response.');
    }

    if (config.hardware.precision === 'int4' && config.model.parameters >= 70_000_000_000) {
      issues.push('INT4 quantization on very large models may significantly degrade accuracy.');
      score -= 5;
      recommendations.push('Consider FP8 or BF16 precision for very large Nemotron models.');
    }

    if (!config.network.rateLimiting && config.network.exposed) {
      issues.push('Rate limiting is not enabled on externally exposed deployment.');
      score -= 10;
      recommendations.push('Enable rate limiting to prevent abuse and DoS.');
    }

    if (config.environment === 'production' && config.hardware.gpus < 2) {
      issues.push('Production deployments should use multiple GPUs for redundancy.');
      score -= 5;
      recommendations.push('Scale to multiple GPUs for production reliability.');
    }

    if (config.security.loggingEnabled && config.security.auditTrail && config.security.authRequired) {
      score = Math.min(100, score + 5);
    }

    score = Math.max(0, Math.min(100, score));

    return {
      compliant: score >= 80 && issues.length <= 2,
      score,
      issues,
      recommendations,
    };
  }

  mapToControls(
    model: NemotronModel,
    framework: ComplianceFramework
  ): { controlId: string; description: string; met: boolean }[] {
    switch (framework) {
      case 'EU_AI_ACT':
        return mapModelToEuAiActControls(model);
      case 'NIST_AI_RMF':
        return mapModelToNistControls(model);
      case 'ISO_42001':
        return mapModelToIsoControls(model);
      default:
        return [];
    }
  }

  generateComplianceReport(
    model: NemotronModel,
    config: NemotronDeploymentConfig
  ): ComplianceReport {
    const assessments = this.assessModelCompliance(model, [
      'EU_AI_ACT',
      'NIST_AI_RMF',
      'ISO_42001',
    ]);

    const aiBom = this.generateAiBom(model);

    const deploymentAssessment = this.assessDeployment(config);

    const avgScore =
      assessments.reduce((sum, a) => sum + a.score, 0) / assessments.length;
    const combinedGaps = assessments.flatMap((a) => a.gaps);

    const criticalGaps = combinedGaps.filter((g) => g.severity === 'critical').length;
    const highGaps = combinedGaps.filter((g) => g.severity === 'high').length;

    const euAiActAssessment = assessments.find((a) => a.framework === 'EU_AI_ACT');
    const euAiActRiskTier = euAiActAssessment
      ? (euAiActAssessment.recommendations.find((r) => r.startsWith('Risk tier:'))?.split(': ')[1] ?? 'minimal')
      : 'minimal';

    let riskScore = 100;
    riskScore -= criticalGaps * 15;
    riskScore -= highGaps * 10;
    riskScore -= deploymentAssessment.score < 80 ? 20 : 0;

    if (euAiActRiskTier === 'unacceptable') riskScore = 0;
    else if (euAiActRiskTier === 'high') riskScore = Math.min(riskScore, 30);

    riskScore = Math.max(0, Math.min(100, riskScore));

    const riskTier =
      riskScore >= 80 ? 'minimal' : riskScore >= 60 ? 'limited' : riskScore >= 30 ? 'high' : 'unacceptable';

    const recommendations = [
      ...assessments.flatMap((a) => a.recommendations),
      ...deploymentAssessment.recommendations,
    ];

    if (criticalGaps > 0) {
      recommendations.unshift(
        `CRITICAL: ${criticalGaps} critical compliance gap(s) require immediate attention.`
      );
    }

    const bomSummary = getBomSummary(aiBom);
    if (bomSummary.criticalVulns > 0 || bomSummary.highVulns > 0) {
      recommendations.push(
        `AI BOM: ${bomSummary.criticalVulns} critical and ${bomSummary.highVulns} high vulnerabilities identified.`
      );
    }

    const reportId = createHash('sha256')
      .update(`${model.id}:${model.version}:${Date.now()}`)
      .digest('hex')
      .slice(0, 16);

    return {
      model,
      assessments,
      aiBom,
      riskScore,
      riskTier,
      recommendations: [...new Set(recommendations)],
      generatedAt: new Date().toISOString(),
      reportId,
    };
  }
}

function mapModelToEuAiActControls(
  model: NemotronModel
): { controlId: string; description: string; met: boolean }[] {
  return [
    {
      controlId: 'Art.6(1)',
      description: 'General-purpose AI model provider obligations',
      met: true,
    },
    {
      controlId: 'Art.50',
      description: 'Transparency obligations - label AI-generated content',
      met: true,
    },
    {
      controlId: 'Art.52',
      description: 'Disclosure of AI-generated content for certain use cases',
      met: model.capabilities.length > 0,
    },
    {
      controlId: 'Art.53',
      description: 'Technical documentation for GPAI models',
      met: model.name !== '' && model.version !== '',
    },
    {
      controlId: 'Art.54',
      description: 'Information and documentation for downstream providers',
      met: model.trainingDataSources.length > 0,
    },
    {
      controlId: 'Art.55',
      description: 'Policy for copyright compliance',
      met: model.license !== '',
    },
  ];
}

function mapModelToNistControls(
  model: NemotronModel
): { controlId: string; description: string; met: boolean }[] {
  return [
    {
      controlId: 'GOVERN-1',
      description: 'Legal and regulatory requirements are identified',
      met: model.license !== '',
    },
    {
      controlId: 'GOVERN-2',
      description: 'Roles and responsibilities for AI risk management',
      met: true,
    },
    {
      controlId: 'MAP-1',
      description: 'Intended purpose and context established',
      met: model.capabilities.length > 0,
    },
    {
      controlId: 'MAP-3',
      description: 'AI risks identified',
      met: model.trainingDataSources.length > 0,
    },
    {
      controlId: 'MEASURE-1',
      description: 'Performance metrics established',
      met: model.parameters > 0,
    },
    {
      controlId: 'MEASURE-4',
      description: 'Transparency metrics tracked',
      met: true,
    },
    {
      controlId: 'MANAGE-1',
      description: 'Risk response implemented',
      met: true,
    },
  ];
}

function mapModelToIsoControls(
  model: NemotronModel
): { controlId: string; description: string; met: boolean }[] {
  return [
    {
      controlId: 'A.5.1.1',
      description: 'AI policy established',
      met: true,
    },
    {
      controlId: 'A.7.2.1',
      description: 'AI system development lifecycle',
      met: model.name !== '',
    },
    {
      controlId: 'A.8.1.1',
      description: 'AI data management',
      met: model.trainingDataSources.length > 0,
    },
    {
      controlId: 'A.8.3.1',
      description: 'AI data provenance',
      met: model.trainingDataSources.length > 0,
    },
  ];
}
