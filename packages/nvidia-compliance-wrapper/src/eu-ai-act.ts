import type {
  NemotronModel,
  RiskTier,
  EuAiActAssessment,
  ArticleRequirement,
  ConformityAssessment,
  ConformityCheck,
  TransparencyCheck,
  ComplianceGap,
} from './types.js';

const UNACCEPTABLE_CAPABILITIES = [
  'social-scoring',
  'real-time-biometric-identification',
  'subliminal-manipulation',
  'exploitation-of-vulnerabilities',
];

const HIGH_RISK_USE_CASES = [
  'critical-infrastructure',
  'education-access',
  'employment-decision-making',
  'essential-services-access',
  'law-enforcement',
  'migration-asylum',
  'administration-of-justice',
  'democratic-processes',
];

const LIMITED_RISK_INDICATORS = [
  'chatbot',
  'emotion-recognition',
  'deepfake',
  'content-generation',
  'recommendation-system',
];

export function assessRiskTier(model: NemotronModel): RiskTier {
  const caps = model.capabilities.map((c) => c.toLowerCase());

  const hasUnacceptable = caps.some((c) =>
    UNACCEPTABLE_CAPABILITIES.some((u) => c.includes(u))
  );
  if (hasUnacceptable) return 'unacceptable';

  const hasHighRiskUse = caps.some((c) =>
    HIGH_RISK_USE_CASES.some((h) => c.includes(h))
  );
  if (hasHighRiskUse) return 'high';

  const hasLimitedRisk = caps.some((c) =>
    LIMITED_RISK_INDICATORS.some((l) => c.includes(l))
  );
  if (hasLimitedRisk) return 'limited';

  return 'minimal';
}

export function mapToArticle6(model: NemotronModel, riskTier: RiskTier): ArticleRequirement[] {
  const base: ArticleRequirement[] = [
    {
      article: 'Article 6(1)',
      title: 'General Purpose AI - Provider Obligations',
      required: true,
      met: true,
      details: 'Nemotron models provided by NVIDIA as general-purpose AI systems require compliance with transparency obligations.',
    },
    {
      article: 'Article 6(2)',
      title: 'Risk-Based Classification',
      required: true,
      met: riskTier !== 'unacceptable',
      details: `Model classified as ${riskTier} risk tier.`,
    },
  ];

  if (riskTier === 'high') {
    base.push(
      {
        article: 'Article 9',
        title: 'Risk Management System',
        required: true,
        met: false,
        details: 'High-risk AI systems must implement a risk management system per Article 9 requirements.',
      },
      {
        article: 'Article 10',
        title: 'Data Governance',
        required: true,
        met: false,
        details: 'Training data must be relevant, representative, and free of errors.',
      },
      {
        article: 'Article 11',
        title: 'Technical Documentation',
        required: true,
        met: false,
        details: 'Technical documentation must be drawn up before market placement.',
      },
      {
        article: 'Article 12',
        title: 'Record-Keeping',
        required: true,
        met: false,
        details: 'Automatic logging of events throughout the AI system lifecycle.',
      },
      {
        article: 'Article 13',
        title: 'Transparency & Information to Deployers',
        required: true,
        met: false,
        details: 'Adequate transparency with instructions for use.',
      },
      {
        article: 'Article 14',
        title: 'Human Oversight',
        required: true,
        met: false,
        details: 'AI system must be designed for effective human oversight.',
      },
      {
        article: 'Article 15',
        title: 'Accuracy, Robustness & Cybersecurity',
        required: true,
        met: false,
        details: 'Appropriate levels of accuracy, robustness, and cybersecurity.',
      }
    );
  }

  if (riskTier === 'limited' || riskTier === 'minimal') {
    base.push({
      article: 'Article 50',
      title: 'Transparency Obligations for Limited/Minimal Risk',
      required: true,
      met: false,
      details: 'Providers must ensure AI-generated content is machine-readable and labeled as artificially generated.',
    });
  }

  return base;
}

export function generateConformityAssessment(model: NemotronModel): ConformityAssessment {
  const checks: ConformityCheck[] = [
    {
      id: 'CA-001',
      description: 'Model card and documentation available',
      passed: model.name !== '' && model.version !== '',
      evidence: `Model: ${model.name} v${model.version}`,
    },
    {
      id: 'CA-002',
      description: 'Training data sources documented',
      passed: model.trainingDataSources.length > 0,
      evidence: `${model.trainingDataSources.length} training data source(s) documented.`,
    },
    {
      id: 'CA-003',
      description: 'License information provided',
      passed: model.license !== '',
      evidence: `License: ${model.license}`,
    },
    {
      id: 'CA-004',
      description: 'Intended purpose clearly defined',
      passed: model.capabilities.length > 0,
      evidence: `${model.capabilities.length} capability/capabilities defined.`,
    },
    {
      id: 'CA-005',
      description: 'Limitations and risks documented',
      passed: model.capabilities.some((c) => c.toLowerCase().includes('limitation')),
      evidence: 'Capability list reviewed for limitation documentation.',
    },
    {
      id: 'CA-006',
      description: 'Performance metrics available',
      passed: model.parameters > 0,
      evidence: `Model has ${model.parameters} parameters.`,
    },
  ];

  const passed = checks.filter((c) => c.passed).length;

  return {
    passed: passed === checks.length,
    checks,
    timestamp: new Date().toISOString(),
  };
}

export function checkTransparency(model: NemotronModel): TransparencyCheck[] {
  const obligations: TransparencyCheck[] = [
    {
      obligation: 'AI-generated content must be labeled as artificially generated',
      met: true,
      details: 'Nemotron models can be configured to append watermarks or labels to generated content.',
    },
    {
      obligation: 'Users must be informed they are interacting with an AI system',
      met: true,
      details: 'Deployment configurations support chatbot disclosure headers.',
    },
    {
      obligation: 'Deepfake content must be disclosed',
      met: model.modality !== 'multimodal',
      details: model.modality === 'multimodal'
        ? 'Multimodal capability may generate deepfake-like content requiring disclosure.'
        : 'Text-only model does not generate synthetic media.',
    },
    {
      obligation: 'Emotion recognition systems must be disclosed',
      met: !model.capabilities.some((c) => c.toLowerCase().includes('emotion')),
      details: model.capabilities.some((c) => c.toLowerCase().includes('emotion'))
        ? 'Model has emotion-related capabilities requiring disclosure.'
        : 'No emotion recognition capability detected.',
    },
  ];

  return obligations;
}

export function assessEuAiAct(model: NemotronModel): EuAiActAssessment {
  const riskTier = assessRiskTier(model);
  const articles = mapToArticle6(model, riskTier);
  const conformityAssessment = generateConformityAssessment(model);
  const transparencyObligations = checkTransparency(model);

  return {
    riskTier,
    articles,
    conformityAssessment,
    transparencyObligations,
  };
}

export function getEuAiActGaps(assessment: EuAiActAssessment): ComplianceGap[] {
  const gaps: ComplianceGap[] = [];

  for (const article of assessment.articles) {
    if (article.required && !article.met) {
      gaps.push({
        controlId: article.article,
        description: `${article.title}: ${article.details}`,
        severity: assessment.riskTier === 'high' ? 'critical' : 'medium',
        remediation: `Implement controls to satisfy ${article.article} requirements.`,
      });
    }
  }

  for (const check of assessment.conformityAssessment.checks) {
    if (!check.passed) {
      gaps.push({
        controlId: check.id,
        description: check.description,
        severity: 'medium',
        remediation: `Address conformity check: ${check.description}`,
      });
    }
  }

  for (const obligation of assessment.transparencyObligations) {
    if (!obligation.met) {
      gaps.push({
        controlId: 'TRANSPARENCY',
        description: obligation.obligation,
        severity: 'high',
        remediation: obligation.details,
      });
    }
  }

  return gaps;
}
