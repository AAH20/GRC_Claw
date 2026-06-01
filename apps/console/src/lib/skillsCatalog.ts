import { api } from './api';
import { BUILTIN_TOOLS, CLAW_SKILL_TOOLS } from './constants';

export interface CursorSkillEntry {
  id: string;
  name: string;
  description: string;
  path?: string;
  scope?: string;
}

export function wantsSkillsQuery(userText: string): boolean {
  return /\b(skill|skills)\b/i.test(userText) && /\b(list|show|all|what|which|your|available|have)\b/i.test(userText);
}

async function loadSkills(): Promise<CursorSkillEntry[]> {
  try {
    const res = await api.cursorSkills();
    return (res.skills as CursorSkillEntry[]) ?? [];
  } catch {
    const res = await fetch('/skills-manifest.json');
    if (!res.ok) return [];
    const data = (await res.json()) as { skills: CursorSkillEntry[] };
    return data.skills ?? [];
  }
}

export async function formatSkillsCatalog(): Promise<string> {
  const skills = await loadSkills();

  let out =
    '## Cursor IDE skills (GRC_Claw + A2Z SOC workspace)\n\n' +
    'Skills are markdown playbooks under `.cursor/skills/`. The gateway executes them via **`claw.list_skills`**, **`claw.get_skill`**, and **`claw.run_skill`** (exec policy + BYOC LLM).\n\n' +
    '**Invoke:** `POST /api/agent/invoke` with `tool: "claw.list_skills"` or `POST /api/skills/run` with `{ skillId, task, idempotencyKey }`.\n\n';

  if (skills.length === 0) {
    out += '_No skills discovered — ensure gateway runs from repo root or set `GRC_CLAW_SKILLS_DIRS`._\n\n';
  } else {
    out += '| Skill ID | Scope | Description |\n';
    out += '|----------|-------|-------------|\n';
    for (const s of skills) {
      out += `| \`${s.id}\` | ${s.scope ?? '—'} | ${s.description} |\n`;
    }
    out += '\n';
    const grcClaw = skills.filter((s) => s.scope === 'grc_claw');
    const workspace = skills.filter((s) => s.scope === 'workspace');
    if (grcClaw.length) {
      out += `**In GRC_Claw repo:** ${grcClaw.map((s) => s.id).join(', ')}\n\n`;
    }
    if (workspace.length) {
      out += `**In A2Z SOC workspace:** ${workspace.map((s) => s.id).join(', ')}\n\n`;
    }
  }

  out += '## Claw skill tools\n\n| Tool | Tier |\n|------|------|\n';
  for (const t of CLAW_SKILL_TOOLS) {
    out += `| \`${t.name}\` | ${t.tier} |\n`;
  }

  out += '\n## Other gateway agent tools\n\n| Tool | Tier |\n|------|------|\n';
  for (const t of BUILTIN_TOOLS) {
    out += `| \`${t.name}\` | ${t.tier} |\n`;
  }

  out +=
    '\n## How to use skills\n\n' +
    '- **Gateway executor:** `claw.run_skill` or `POST /api/skills/run` with `skillId`, `task`, and `idempotencyKey`.\n' +
    '- **Cursor IDE:** agents auto-load `.cursor/skills/` when relevant.\n' +
    '- **Dashboard:** Agent page → `claw.list_skills` / `claw.run_skill`, or agent chat “list skills”.\n';

  return out;
}
