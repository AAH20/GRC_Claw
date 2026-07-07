import type {
  NemotronModel,
  NistRmfAssessment,
  NistFunctionAssessment,
  NistControl,
  AccountabilityCheck,
  ComplianceGap,
} from './types.js';

const GOVERN_CONTROLS: NistControl[] = [
  { id: 'GV-01', name: 'AI Risk Management Process', met: false, description: 'Organization establishes and maintains an AI risk management process.' },
  { id: 'GV-02', name: 'Roles & Responsibilities', met: false, description: 'AI risk management roles and responsibilities are defined.' },
  { id: 'GV-03', name: 'AI Risk Tolerance', met: false, description: 'Organization determines AI risk tolerance levels.' },
  { id: 'GV-04', name: 'Legal & Regulatory Compliance', met: false, description: 'Legal and regulatory requirements for AI are identified and tracked.' },
  { id: 'GV-05', name: 'AI Risk Culture', met: false, description: 'Organization promotes a culture of AI risk awareness.' },
  { id: 'GV-06', name: 'Stakeholder Engagement', met: false, description: 'Stakeholders are engaged in AI risk management.' },
];

const MAP_CONTROLS: NistControl[] = [
  { id: 'MAP-01', name: 'Context Establishment', met: false, description: 'AI system context and purpose are established.' },
  { id: 'MAP-02', name: 'Impact Assessment', met: false, description: 'Potential impacts of the AI system are identified.' },
  { id: 'MAP-03', name: 'Risk Identification', met: false, description: 'AI risks are identified across the lifecycle.' },
  { id: 'MAP-04', name: 'Risk Analysis', met: false, description: 'Identified risks are analyzed for likelihood and impact.' },
  { id: 'MAP-05', name: 'Risk Prioritization', met: false, description: 'Risks are prioritized based on analysis results.' },
  { id: 'MAP-06', name: 'Impact Characterization', met: false, description: 'Potential impacts are characterized and evaluated.' },
];

const MEASURE_CONTROLS: NistControl[] = [
  { id: 'MSR-01', name: 'Performance Metrics', met: false, description: 'AI system performance metrics are established and tracked.' },
  { id: 'MSR-02', name: 'Reliability & Robustness', met: false, description: 'System reliability and robustness are measured.' },
  { id: 'MSR-03', name: 'Fairness & Bias', met: false, description: 'Fairness and bias metrics are monitored.' },
  { id: 'MSR-04', name: 'Transparency', met: false, description: 'Transparency of AI system decisions is measured.' },
  { id: 'MSR-05', name: 'Privacy', met: false, description: 'Privacy impacts are measured and monitored.' },
  { id: 'MSR-06', name: 'Cybersecurity', met: false, description: 'Cybersecurity risks are measured.' },
];

const MANAGE_CONTROLS: NistControl[] = [
  { id: 'MNG-01', name: 'Risk Response', met: false, description: 'Selected risk responses are implemented.' },
  { id: 'MNG-02', name: 'Risk Monitoring', met: false, description: 'AI risks are continuously monitored.' },
  { id: 'MNG-03', name: 'Incident Response', met: false, description: 'AI-related incidents are managed.' },
  { id: 'MNG-04', name: 'Communication', met: false, description: 'AI risk information is communicated to stakeholders.' },
  { id: 'MNG-05', name: 'Continuous Improvement', met: false, description: 'AI risk management practices are improved.' },
];

export function evaluateNistFunction(
  controls: NistControl[],
  model: NemotronModel,
  functionId: string
): NistFunctionAssessment {
  const evaluated = controls.map((control) => {
    let met = control.met;

    switch (functionId) {
      case 'GOVERN':
        if (control.id === 'GV-04') met = model.license !== '';
        if (control.id === 'GV-01') met = model.name !== '' && model.version !== '';
        if (control.id === 'GV-02') met = true;
        break;
      case 'MAP':
        if (control.id === 'MAP-01') met = model.capabilities.length > 0;
        if (control.id === 'MAP-02') met = model.parameters > 0;
        if (control.id === 'MAP-03') met = model.trainingDataSources.length > 0;
        break;
      case 'MEASURE':
        if (control.id === 'MSR-01') met = model.parameters > 0;
        if (control.id === 'MSR-04') met = true;
        if (control.id === 'MSR-06') met = true;
        break;
      case 'MANAGE':
        if (control.id === 'MNG-02') met = true;
        if (control.id === 'MNG-05') met = true;
        break;
    }

    return { ...control, met };
  });

  const passed = evaluated.filter((c) => c.met).length;
  const score = evaluated.length > 0 ? Math.round((passed / evaluated.length) * 100) : 0;

  return {
    function: functionId as 'GOVERN' | 'MAP' | 'MEASURE' | 'MANAGE',
    score,
    controls: evaluated,
  };
}

export function assessNistRmf(model: NemotronModel): NistRmfAssessment {
  const functions: NistFunctionAssessment[] = [
    evaluateNistFunction(GOVERN_CONTROLS, model, 'GOVERN'),
    evaluateNistFunction(MAP_CONTROLS, model, 'MAP'),
    evaluateNistFunction(MEASURE_CONTROLS, model, 'MEASURE'),
    evaluateNistFunction(MANAGE_CONTROLS, model, 'MANAGE'),
  ];

  const overallScore = Math.round(
    functions.reduce((sum, f) => sum + f.score, 0) / functions.length
  );

  const riskLevel =
    overallScore >= 80 ? 'low' : overallScore >= 50 ? 'medium' : 'high';

  const accountabilityChecks: AccountabilityCheck[] = [
    {
      requirement: 'AI system ownership is assigned',
      met: true,
      responsible: 'AI System Owner',
    },
    {
      requirement: 'Model cards and documentation are maintained',
      met: model.name !== '',
      responsible: 'ML Engineering Lead',
    },
    {
      requirement: 'Training data provenance is tracked',
      met: model.trainingDataSources.length > 0,
      responsible: 'Data Engineering Lead',
    },
    {
      requirement: 'Ongoing monitoring and evaluation',
      met: true,
      responsible: 'ML Operations',
    },
    {
      requirement: 'Incident response procedures are defined',
      met: true,
      responsible: 'Security Operations',
    },
  ];

  return {
    functions,
    overallScore,
    riskLevel,
    accountabilityChecks,
  };
}

export function getNistGaps(assessment: NistRmfAssessment): ComplianceGap[] {
  const gaps: ComplianceGap[] = [];

  for (const func of assessment.functions) {
    for (const control of func.controls) {
      if (!control.met) {
        gaps.push({
          controlId: control.id,
          description: `[${func.function}] ${control.name}: ${control.description}`,
          severity:
            func.function === 'GOVERN' || func.function === 'MAP'
              ? 'high'
              : 'medium',
          remediation: `Implement controls for ${control.id} - ${control.name}.`,
        });
      }
    }
  }

  for (const check of assessment.accountabilityChecks) {
    if (!check.met) {
      gaps.push({
        controlId: 'ACCOUNTABILITY',
        description: check.requirement,
        severity: 'high',
        remediation: `Assign responsibility: ${check.responsible}`,
      });
    }
  }

  return gaps;
}
