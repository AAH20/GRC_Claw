import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { SkillEntry } from './types.js';

export function parseSkillFrontmatter(content: string): { name?: string; description?: string } {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const block = match[1]!;
  const name = block.match(/^name:\s*(.+)$/m)?.[1]?.trim();
  const description = block.match(/^description:\s*(.+)$/m)?.[1]?.trim();
  return { name, description };
}

export function stripSkillFrontmatter(content: string): string {
  return content.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, '').trim();
}

function scanSkillsDir(skillsDir: string, scope: SkillEntry['scope']): SkillEntry[] {
  if (!existsSync(skillsDir)) return [];
  const entries: SkillEntry[] = [];
  for (const id of readdirSync(skillsDir, { withFileTypes: true })) {
    if (!id.isDirectory()) continue;
    const skillMd = join(skillsDir, id.name, 'SKILL.md');
    if (!existsSync(skillMd)) continue;
    const raw = readFileSync(skillMd, 'utf8');
    const meta = parseSkillFrontmatter(raw);
    entries.push({
      id: id.name,
      name: meta.name ?? id.name,
      description: meta.description ?? 'No description in SKILL.md frontmatter.',
      path: skillMd,
      scope,
    });
  }
  return entries.sort((a, b) => a.id.localeCompare(b.id));
}

/** Discover skills from `.cursor/skills` (GRC_Claw repo + parent workspace). */
export function discoverSkills(): SkillEntry[] {
  const dirs: { path: string; scope: SkillEntry['scope'] }[] = [];

  const fromEnv = (process.env.GRC_CLAW_SKILLS_DIRS ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  for (const p of fromEnv) {
    dirs.push({ path: p, scope: p.includes('GRC_Claw') ? 'grc_claw' : 'workspace' });
  }

  if (!dirs.length) {
    const cwd = process.cwd();
    dirs.push({ path: join(cwd, '.cursor/skills'), scope: 'grc_claw' });
    const parent = join(cwd, '..', '.cursor/skills');
    if (existsSync(parent)) {
      dirs.push({ path: parent, scope: 'workspace' });
    }
  }

  const seen = new Set<string>();
  const all: SkillEntry[] = [];
  for (const { path, scope } of dirs) {
    for (const skill of scanSkillsDir(path, scope)) {
      if (seen.has(skill.id)) continue;
      seen.add(skill.id);
      all.push(skill);
    }
  }
  return all;
}
