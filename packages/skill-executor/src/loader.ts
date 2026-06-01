import { readFileSync } from 'node:fs';
import { discoverSkills, parseSkillFrontmatter, stripSkillFrontmatter } from './discovery.js';
import type { LoadedSkill, SkillEntry } from './types.js';

export function listSkills(): SkillEntry[] {
  return discoverSkills();
}

export function getSkillById(skillId: string): LoadedSkill | null {
  const entry = discoverSkills().find((s) => s.id === skillId);
  if (!entry) return null;
  const raw = readFileSync(entry.path, 'utf8');
  const body = stripSkillFrontmatter(raw);
  const meta = parseSkillFrontmatter(raw);
  return {
    ...entry,
    name: meta.name ?? entry.name,
    description: meta.description ?? entry.description,
    body,
    contentLength: body.length,
  };
}
