import { api } from './api';
import { loadSettings } from './settings';
import { GATEWAY_JOBS, wantsJobCatalog } from './schedulableJobs';
import { wantsSkillsQuery } from './skillsCatalog';

export interface OperatorToolResult {
  tool: string;
  ok: boolean;
  summary: string;
  data?: unknown;
}

const AUTOMATION_KEYWORDS =
  /\b(cron|crontab|daemon|background\s+agent|schedule|scheduled|automation|watchdog|systemd)\b/i;

/** Gateway actions the in-browser operator can run (not OS/Cursor IDE processes). */
export async function runOperatorTools(userText: string): Promise<OperatorToolResult[]> {
  const results: OperatorToolResult[] = [];
  const tenantId = loadSettings().tenantId;

  const wantsFrameworks = /\b(framework|iso|nist|soc\s*2|control\s+pack)/i.test(userText);
  const wantsSync = /\b(sync|a2z|pull\s+events|bridge)/i.test(userText);
  const wantsControls = /\b(control|compliance|score|grc\.)/i.test(userText);
  const wantsAutomation = AUTOMATION_KEYWORDS.test(userText);
  const wantsCatalog = wantsJobCatalog(userText);
  const wantsSkills = wantsSkillsQuery(userText);
  const wantsHealth =
    /\b(health|status|capabilities|up\b)/i.test(userText) ||
    (!wantsFrameworks &&
      !wantsSync &&
      !wantsControls &&
      !wantsAutomation &&
      !wantsCatalog &&
      !wantsSkills);

  if (
    wantsHealth ||
    (!wantsFrameworks && !wantsSync && !wantsControls && !wantsAutomation && !wantsCatalog && !wantsSkills)
  ) {
    try {
      const h = await api.health();
      results.push({
        tool: 'GET /health',
        ok: true,
        summary: `Gateway ok — A2Z mode ${String(h.a2z_soc_mode)}, ${String(h.llm_providers)} LLM(s), ${String(h.mcp_servers)} MCP.`,
        data: h,
      });
    } catch (e) {
      results.push({
        tool: 'GET /health',
        ok: false,
        summary: e instanceof Error ? e.message : 'health failed',
      });
    }
  }

  if (wantsFrameworks) {
    try {
      const f = await api.frameworks();
      results.push({
        tool: 'GET /api/frameworks',
        ok: true,
        summary: `${f.packs.length} framework pack(s): ${f.packs.map((p) => (p as { code: string }).code).join(', ')}.`,
        data: f.packs,
      });
    } catch (e) {
      results.push({
        tool: 'GET /api/frameworks',
        ok: false,
        summary: e instanceof Error ? e.message : 'frameworks failed',
      });
    }
  }

  if (wantsSync) {
    try {
      const s = await api.a2zSync();
      results.push({
        tool: 'POST /api/a2z/sync',
        ok: true,
        summary: 'A2Z SOC bridge sync completed.',
        data: s,
      });
    } catch (e) {
      results.push({
        tool: 'POST /api/a2z/sync',
        ok: false,
        summary: e instanceof Error ? e.message : 'sync failed (need token + A2Z_SOC_MODE=private)',
      });
    }
  }

  if (wantsControls) {
    try {
      const inv = await api.agentInvoke({
        sessionId: 'dashboard-operator',
        tool: 'grc.list_controls',
        args: { tenantId },
      });
      results.push({
        tool: 'agent grc.list_controls',
        ok: Boolean(inv.ok),
        summary: 'Listed controls via gated agent (read tier).',
        data: inv,
      });
    } catch (e) {
      results.push({
        tool: 'agent grc.list_controls',
        ok: false,
        summary: e instanceof Error ? e.message : 'agent invoke failed',
      });
    }
  }

  if (wantsSkills) {
    results.push({
      tool: 'GET /api/cursor-skills',
      ok: true,
      summary: 'Skill catalog via GET /api/cursor-skills (also claw.list_skills).',
    });
  }

  if (wantsAutomation || wantsCatalog) {
    results.push({
      tool: 'automation.catalog',
      ok: true,
      summary: `${GATEWAY_JOBS.length} gateway jobs catalogued (1 long-running daemon + ${GATEWAY_JOBS.filter((j) => j.type === 'cron-friendly').length} cron-friendly APIs).`,
      data: { jobs: GATEWAY_JOBS, listRequest: wantsJobCatalog(userText) },
    });
  }

  return results;
}

export function formatToolResultsForPrompt(results: OperatorToolResult[]): string {
  if (!results.length) return '';
  return (
    '\n\n--- Gateway tool results (live) ---\n' +
    results
      .map((r) => `[${r.ok ? 'OK' : 'ERR'}] ${r.tool}: ${r.summary}`)
      .join('\n') +
    '\n--- End tool results ---\n'
  );
}
