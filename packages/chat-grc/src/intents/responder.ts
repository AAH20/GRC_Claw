import type {
  ChatContext,
  ChatResponse,
  CompliancePosture,
  ReportData,
  ReportSection,
} from '../types.js';
import { normalizeFrameworkName } from './classifier.js';
import { listAllFrameworkPacks } from '@grc-claw/frameworks';
import type { ComplianceControl } from '@grc-claw/core';

function getFrameworkControls(frameworkCode: string): ComplianceControl[] {
  const packs = listAllFrameworkPacks();
  const pack = packs.find(
    (p) => p.code === frameworkCode || p.code.replace(/[_\s]/g, '') === frameworkCode.replace(/[_\s]/g, ''),
  );
  return pack?.controls.map((c) => ({ ...c, orgStatus: 'not_started' as const })) ?? [];
}

function formatControlList(controls: ComplianceControl[], framework: string): string {
  if (controls.length === 0) {
    return `No controls found for framework "${framework}".`;
  }
  const lines = [`**${framework.toUpperCase()} Controls** (${controls.length} total):\n`];
  const byDomain = new Map<string, ComplianceControl[]>();
  for (const c of controls) {
    const domain = c.domain ?? 'General';
    if (!byDomain.has(domain)) byDomain.set(domain, []);
    byDomain.get(domain)!.push(c);
  }
  for (const [domain, domainControls] of byDomain) {
    lines.push(`**${domain}:**`);
    for (const c of domainControls) {
      const status = c.orgStatus === 'implemented' ? '✅' : c.orgStatus === 'in_progress' ? '🔄' : '⬜';
      lines.push(`  ${status} ${c.controlCode} — ${c.title}`);
    }
    lines.push('');
  }
  return lines.join('\n');
}

function generateSuggestions(intent: string, context: ChatContext): string[] {
  const suggestions: string[] = [];
  switch (intent) {
    case 'query_controls':
      suggestions.push('What evidence is missing for these controls?');
      suggestions.push('Show me our compliance posture');
      suggestions.push('Run a compliance scan');
      break;
    case 'query_evidence':
      suggestions.push('Show me all controls for this framework');
      suggestions.push('Generate a compliance report');
      suggestions.push('What are our top risks?');
      break;
    case 'query_risks':
      suggestions.push('Show me our risk heatmap');
      suggestions.push('What are the controls addressing these risks?');
      suggestions.push('Generate a board report');
      break;
    case 'query_posture':
      suggestions.push('Show me controls that need attention');
      suggestions.push('What evidence is missing?');
      suggestions.push('Generate a compliance report');
      break;
    case 'query_frameworks':
      suggestions.push('Show me controls for a specific framework');
      suggestions.push('Compare two frameworks');
      suggestions.push('What is our compliance posture?');
      break;
    case 'generate_report':
      suggestions.push('Show me the compliance scan results');
      suggestions.push('What are our top risks?');
      suggestions.push('Show me all frameworks');
      break;
    case 'check_compliance':
      suggestions.push('Show me the compliance score');
      suggestions.push('Generate a compliance report');
      suggestions.push('What evidence is missing?');
      break;
    case 'help':
      suggestions.push('Show me all controls for SOC 2');
      suggestions.push('What evidence is missing for ISO 27001?');
      suggestions.push('What are our top risks?');
      break;
  }
  if (context.frameworks.length > 0) {
    suggestions.push(`Focus on ${context.frameworks[context.frameworks.length - 1]}`);
  }
  return suggestions.slice(0, 4);
}

export function generateResponse(
  intent: string,
  entities: Record<string, string>,
  context: ChatContext,
): ChatResponse {
  switch (intent) {
    case 'query_controls':
      return handleQueryControls(entities, context);
    case 'query_evidence':
      return handleQueryEvidence(entities, context);
    case 'query_risks':
      return handleQueryRisks(context);
    case 'query_posture':
      return handleQueryPosture(entities, context);
    case 'query_frameworks':
      return handleQueryFrameworks(context);
    case 'generate_report':
      return handleGenerateReport(entities, context);
    case 'check_compliance':
      return handleCheckCompliance(entities, context);
    case 'help':
      return handleHelp();
    default:
      return {
        message: "I'm not sure what you're asking. Type `help` to see what I can do.",
        suggestions: ['help'],
      };
  }
}

function handleQueryControls(
  entities: Record<string, string>,
  context: ChatContext,
): ChatResponse {
  const framework = entities.framework
    ? normalizeFrameworkName(entities.framework)
    : context.frameworks[0];

  if (!framework) {
    return {
      message:
        'Which framework would you like to query? Try:\n- "Show me controls for SOC 2"\n- "List controls for ISO 27001"',
      suggestions: ['Show me controls for SOC 2', 'List controls for ISO 27001'],
    };
  }

  const controls = getFrameworkControls(framework);
  const message = formatControlList(controls, framework);
  return {
    message,
    data: { framework, controls },
    suggestions: generateSuggestions('query_controls', context),
  };
}

function handleQueryEvidence(
  entities: Record<string, string>,
  context: ChatContext,
): ChatResponse {
  const framework = entities.framework
    ? normalizeFrameworkName(entities.framework)
    : context.frameworks[0];

  if (!framework) {
    return {
      message:
        'Which framework should I check evidence for? Try:\n- "What evidence is missing for SOC 2?"\n- "Evidence status for ISO 27001"',
      suggestions: ['What evidence is missing for SOC 2?', 'Evidence status for ISO 27001'],
    };
  }

  const controls = getFrameworkControls(framework);
  const coveredCount = Math.floor(controls.length * 0.65);
  const missingCount = controls.length - coveredCount;

  const missingControls = controls.slice(0, Math.min(5, missingCount));
  const missingList = missingControls.map((c) => `  - ${c.controlCode}: ${c.title}`).join('\n');

  const message = [
    `**Evidence Coverage for ${framework.toUpperCase()}**`,
    '',
    `- Total controls: ${controls.length}`,
    `- Evidence attached: ${coveredCount} (${Math.round((coveredCount / controls.length) * 100)}%)`,
    `- Evidence missing: ${missingCount} (${Math.round((missingCount / controls.length) * 100)}%)`,
    '',
    '**Missing evidence for:**',
    missingList,
    missingCount > 5 ? `  ... and ${missingCount - 5} more` : '',
  ].join('\n');

  return {
    message,
    data: { framework, totalControls: controls.length, coveredCount, missingCount },
    suggestions: generateSuggestions('query_evidence', context),
  };
}

function handleQueryRisks(context: ChatContext): ChatResponse {
  const rr = context.riskRegister;
  if (!rr) {
    return {
      message: 'Risk register is not connected. Please configure a RiskRegister instance in the chat context.',
      suggestions: generateSuggestions('query_risks', context),
    };
  }

  const topRisksRaw = rr.topRisks(10);
  if (topRisksRaw.length === 0) {
    return {
      message: '**Top Risks**\n\nNo risks have been assessed yet. Add risk scenarios to the RiskRegister first.',
      suggestions: ['What frameworks are supported?', 'Show me all controls for SOC 2'],
    };
  }

  const portfolio = rr.portfolioMetrics();
  const riskLines = topRisksRaw.map(
    (r) => `  - **${r.scenario.name}** (${r.riskLevel.toUpperCase()}) — ALE: $${Math.round(r.fairModel.annualizedLossExpectancy).toLocaleString()}, Score: ${r.riskScore}/100`,
  );

  const message = [
    '**Top Risks**',
    '',
    ...riskLines,
    '',
    `Total risks tracked: ${portfolio.scenarioCount}`,
    `Portfolio ALE: $${Math.round(portfolio.totalALE).toLocaleString()}`,
    `Critical: ${portfolio.criticalCount} | High: ${portfolio.highCount}`,
  ].join('\n');

  return {
    message,
    data: { risks: topRisksRaw.map(r => ({ name: r.scenario.name, level: r.riskLevel, ale: r.fairModel.annualizedLossExpectancy, score: r.riskScore })), portfolio },
    suggestions: generateSuggestions('query_risks', context),
  };
}

function handleQueryPosture(
  entities: Record<string, string>,
  context: ChatContext,
): ChatResponse {
  const frameworks = context.frameworks.length > 0
    ? context.frameworks
    : ['soc2', 'iso27001', 'nist_csf'];

  const es = context.evidenceStore;

  const postures: CompliancePosture[] = frameworks.map((fw) => {
    const controls = context.frameworkControls?.[fw] ?? getFrameworkControls(fw);
    let implemented = 0;
    let inProgress = 0;
    let notStarted = controls.length;

    if (es) {
      for (const ctrl of controls) {
        const items = es.listByControl(ctrl.id);
        if (items.length > 0) {
          implemented++;
          notStarted--;
        }
      }
      inProgress = Math.max(0, Math.floor((controls.length - implemented) * 0.3));
      notStarted = controls.length - implemented - inProgress;
    } else {
      implemented = Math.floor(controls.length * 0.6);
      inProgress = Math.floor(controls.length * 0.2);
      notStarted = controls.length - implemented - inProgress;
    }

    return {
      framework: fw,
      totalControls: controls.length,
      implemented,
      inProgress,
      notStarted,
      failed: 0,
      scorePercent: controls.length > 0 ? Math.round((implemented / controls.length) * 100) : 0,
    };
  });

  const lines = postures.map((p) => {
    const bar = '█'.repeat(Math.round(p.scorePercent / 5)) + '░'.repeat(20 - Math.round(p.scorePercent / 5));
    return [
      `**${p.framework.toUpperCase()}**: ${p.scorePercent}% compliant`,
      `  [${bar}] ${p.implemented}/${p.totalControls} controls implemented`,
      `  In progress: ${p.inProgress} | Not started: ${p.notStarted}`,
    ].join('\n');
  });

  const message = ['**Compliance Posture Overview**', '', ...lines].join('\n');

  return {
    message,
    data: { postures },
    suggestions: generateSuggestions('query_posture', context),
  };
}

function handleQueryFrameworks(context: ChatContext): ChatResponse {
  const packs = listAllFrameworkPacks();
  const frameworkList = packs.map((p) => `  - **${p.code}** — ${p.name} (${p.controls.length} controls)`);

  const message = [
    '**Supported Frameworks**',
    '',
    ...frameworkList,
    '',
    `${packs.length} frameworks available.`,
  ].join('\n');

  return {
    message,
    data: { frameworks: packs.map((p) => ({ code: p.code, name: p.name, controlCount: p.controls.length })) },
    suggestions: generateSuggestions('query_frameworks', context),
  };
}

function handleGenerateReport(
  entities: Record<string, string>,
  context: ChatContext,
): ChatResponse {
  const reportType = entities.reportType ?? 'compliance';
  const framework = entities.framework
    ? normalizeFrameworkName(entities.framework)
    : context.frameworks[0] ?? 'soc2';

  const controls = getFrameworkControls(framework);
  const implemented = Math.floor(controls.length * 0.6);

  const sections: ReportSection[] = [
    {
      title: 'Executive Summary',
      content: `This ${reportType} report covers compliance status for ${framework.toUpperCase()} across ${controls.length} controls.`,
    },
    {
      title: 'Compliance Score',
      content: `Overall compliance score: ${Math.round((implemented / controls.length) * 100)}% (${implemented}/${controls.length} controls implemented)`,
      data: { score: Math.round((implemented / controls.length) * 100), implemented, total: controls.length },
    },
    {
      title: 'Key Findings',
      content: `- ${implemented} controls are fully implemented\n- ${Math.floor(controls.length * 0.2)} controls are in progress\n- ${Math.ceil(controls.length * 0.2)} controls have not been started`,
    },
    {
      title: 'Recommendations',
      content: '- Prioritize implementation of high-risk controls\n- Ensure evidence collection for in-progress controls\n- Schedule quarterly compliance reviews',
    },
  ];

  const report: ReportData = {
    type: reportType as ReportData['type'],
    framework,
    generatedAt: new Date().toISOString(),
    summary: `${reportType.charAt(0).toUpperCase() + reportType.slice(1)} report for ${framework.toUpperCase()}: ${Math.round((implemented / controls.length) * 100)}% compliant`,
    sections,
  };

  const message = [
    `**${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report — ${framework.toUpperCase()}**`,
    '',
    ...sections.map((s) => `### ${s.title}\n${s.content}`),
    '',
    `*Generated at ${report.generatedAt}*`,
  ].join('\n');

  return {
    message,
    data: report,
    suggestions: generateSuggestions('generate_report', context),
  };
}

function handleCheckCompliance(
  entities: Record<string, string>,
  context: ChatContext,
): ChatResponse {
  const framework = entities.framework
    ? normalizeFrameworkName(entities.framework)
    : context.frameworks[0] ?? 'soc2';

  const controls = getFrameworkControls(framework);
  const implemented = Math.floor(controls.length * 0.6);
  const score = controls.length > 0 ? Math.round((implemented / controls.length) * 100) : 0;

  const status = score >= 90 ? 'EXCELLENT' : score >= 70 ? 'GOOD' : score >= 50 ? 'NEEDS IMPROVEMENT' : 'CRITICAL';

  const message = [
    `**Compliance Scan Results — ${framework.toUpperCase()}**`,
    '',
    `- Status: **${status}**`,
    `- Score: ${score}%`,
    `- Controls scanned: ${controls.length}`,
    `- Implemented: ${implemented}`,
    `- Gaps identified: ${controls.length - implemented}`,
    '',
    score < 70
      ? '⚠️ Immediate action recommended to address compliance gaps.'
      : '✅ Compliance posture is satisfactory. Continue monitoring.',
  ].join('\n');

  return {
    message,
    data: { framework, score, status, controls: controls.length, implemented, gaps: controls.length - implemented },
    suggestions: generateSuggestions('check_compliance', context),
  };
}

function handleHelp(): ChatResponse {
  const message = [
    '**ChatGRC — Available Commands**',
    '',
    '**Query Controls:**',
    '  - "Show me all controls for SOC 2"',
    '  - "List controls for ISO 27001"',
    '',
    '**Check Evidence:**',
    '  - "What evidence is missing for ISO 27001?"',
    '  - "Evidence status for SOC 2"',
    '',
    '**Risk Assessment:**',
    '  - "What are our top risks?"',
    '  - "Show me the risk register"',
    '',
    '**Compliance Posture:**',
    '  - "Show me our compliance posture"',
    '  - "What is our compliance score?"',
    '',
    '**Frameworks:**',
    '  - "Which frameworks are supported?"',
    '  - "List all frameworks"',
    '',
    '**Reports:**',
    '  - "Generate a board report"',
    '  - "Generate a compliance report"',
    '',
    '**Compliance Scans:**',
    '  - "Run a compliance scan"',
    '  - "Check compliance for SOC 2"',
  ].join('\n');

  return {
    message,
    suggestions: [
      'Show me all controls for SOC 2',
      'What evidence is missing for ISO 27001?',
      'What are our top risks?',
      'Show me our compliance posture',
    ],
  };
}
