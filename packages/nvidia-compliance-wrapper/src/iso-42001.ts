import type {
  NemotronModel,
  AnnexAControl,
  Iso42001Assessment,
  ComplianceGap,
} from './types.js';

function buildAnnexAControls(model: NemotronModel): AnnexAControl[] {
  return [
    {
      id: 'A.5.1.1',
      name: 'AI Policy',
      category: 'Organizational',
      description: 'Organization establishes an AI policy aligned with strategic objectives.',
      applicable: true,
      status: 'compliant',
      evidence: 'NVIDIA provides model card and usage policy with Nemotron.',
    },
    {
      id: 'A.5.1.2',
      name: 'AI Roles & Responsibilities',
      category: 'Organizational',
      description: 'AI-related roles and responsibilities are defined.',
      applicable: true,
      status: 'compliant',
      evidence: 'Deployment organization must define AI roles.',
    },
    {
      id: 'A.5.2.1',
      name: 'AI Risk Assessment Process',
      category: 'Organizational',
      description: 'Process for identifying and assessing AI risks.',
      applicable: true,
      status: model.parameters > 0 ? 'compliant' : 'non-compliant',
      evidence: `Model parameters: ${model.parameters}. Risk assessment required for models of this scale.`,
    },
    {
      id: 'A.5.2.2',
      name: 'AI Risk Treatment',
      category: 'Organizational',
      description: 'Process for treating identified AI risks.',
      applicable: true,
      status: 'partial',
      evidence: 'Risk treatment plan required post-assessment.',
    },
    {
      id: 'A.6.1.1',
      name: 'Competence',
      category: 'People',
      description: 'Personnel with AI responsibilities are competent.',
      applicable: true,
      status: 'compliant',
      evidence: 'NVIDIA Nemotron provides documentation for developer onboarding.',
    },
    {
      id: 'A.6.2.1',
      name: 'AI Awareness',
      category: 'People',
      description: 'Personnel are aware of AI policy and responsibilities.',
      applicable: true,
      status: 'partial',
      evidence: 'Organization must implement awareness training.',
    },
    {
      id: 'A.7.1.1',
      name: 'AI System Resources',
      category: 'Technology',
      description: 'Sufficient resources are allocated for AI management.',
      applicable: true,
      status: model.parameters >= 7_000_000_000 ? 'compliant' : 'partial',
      evidence: `Nemotron ${model.name} with ${model.parameters} parameters requires significant compute resources.`,
    },
    {
      id: 'A.7.2.1',
      name: 'AI System Development',
      category: 'Technology',
      description: 'AI system development lifecycle follows defined processes.',
      applicable: true,
      status: 'compliant',
      evidence: 'NVIDIA follows structured development lifecycle for Nemotron.',
    },
    {
      id: 'A.7.3.1',
      name: 'AI System Verification',
      category: 'Technology',
      description: 'AI systems are verified before deployment.',
      applicable: true,
      status: 'partial',
      evidence: 'Deployment verification required by the deploying organization.',
    },
    {
      id: 'A.7.4.1',
      name: 'AI System Monitoring',
      category: 'Technology',
      description: 'AI systems are monitored for performance and drift.',
      applicable: true,
      status: 'partial',
      evidence: 'Monitoring infrastructure required at deployment.',
    },
    {
      id: 'A.7.5.1',
      name: 'AI System Logging',
      category: 'Technology',
      description: 'AI system activities are logged for audit purposes.',
      applicable: true,
      status: 'partial',
      evidence: 'Logging must be configured in deployment infrastructure.',
    },
    {
      id: 'A.7.6.1',
      name: 'AI Model Transparency',
      category: 'Technology',
      description: 'AI models provide transparency into decisions.',
      applicable: true,
      status: model.capabilities.some((c) => c.toLowerCase().includes('explainability')) ? 'compliant' : 'partial',
      evidence: model.capabilities.some((c) => c.toLowerCase().includes('explainability'))
        ? 'Model includes explainability capabilities.'
        : 'Explainability may require additional tooling.',
    },
    {
      id: 'A.8.1.1',
      name: 'AI Data Management',
      category: 'Data',
      description: 'Training and input data are properly managed.',
      applicable: true,
      status: model.trainingDataSources.length > 0 ? 'compliant' : 'non-compliant',
      evidence: `${model.trainingDataSources.length} training data source(s) documented.`,
    },
    {
      id: 'A.8.2.1',
      name: 'AI Data Quality',
      category: 'Data',
      description: 'Data quality is ensured for AI training and operations.',
      applicable: true,
      status: 'partial',
      evidence: 'Data quality validation required during training pipeline.',
    },
    {
      id: 'A.8.3.1',
      name: 'AI Data Provenance',
      category: 'Data',
      description: 'Data lineage and provenance are tracked.',
      applicable: true,
      status: model.trainingDataSources.length > 0 ? 'compliant' : 'non-compliant',
      evidence: 'Training data sources tracked in model documentation.',
    },
  ];
}

export function assessIso42001(model: NemotronModel): Iso42001Assessment {
  const controls = buildAnnexAControls(model);

  const applicableControls = controls.filter((c) => c.applicable);
  const compliantCount = applicableControls.filter(
    (c) => c.status === 'compliant'
  ).length;
  const overallScore =
    applicableControls.length > 0
      ? Math.round((compliantCount / applicableControls.length) * 100)
      : 0;

  const gaps: ComplianceGap[] = [];
  const recommendations: string[] = [];

  for (const control of controls) {
    if (control.status === 'non-compliant') {
      gaps.push({
        controlId: control.id,
        description: `[${control.category}] ${control.name}: ${control.description}`,
        severity: control.category === 'Technology' ? 'high' : 'medium',
        remediation: `Implement controls for ${control.id} to achieve compliance.`,
      });
      recommendations.push(
        `Address non-compliance for control ${control.id} (${control.name}).`
      );
    } else if (control.status === 'partial') {
      gaps.push({
        controlId: control.id,
        description: `[${control.category}] ${control.name}: Partially implemented`,
        severity: 'low',
        remediation: `Complete implementation of control ${control.id}.`,
      });
      recommendations.push(
        `Complete partial implementation of control ${control.id}.`
      );
    }
  }

  if (overallScore < 80) {
    recommendations.push(
      'Implement an AI Management System (AIMS) aligned with ISO 42001 clause requirements.'
    );
  }

  return {
    controls,
    overallScore,
    gaps,
    recommendations,
  };
}
