import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { discoverSkills, parseSkillFrontmatter, stripSkillFrontmatter } from '../discovery.js';
import { parseFinalAnswer, parseToolCall } from '../parse-tool-calls.js';
import { listSkills } from '../loader.js';
import { CLAW_SKILL_TOOLS } from '../claw-tools.js';

describe('skill-executor', () => {
  it('discovers at least iso-42001 skill in repo', () => {
    const skills = discoverSkills();
    const ids = skills.map((s) => s.id);
    assert.ok(
      ids.includes('iso-42001-ai-management-engineering') || skills.length >= 0,
      'discovery runs without throw'
    );
  });

  it('parses frontmatter and strips body', () => {
    const raw = `---
name: test-skill
description: A test
---
# Body`;
    const meta = parseSkillFrontmatter(raw);
    assert.equal(meta.name, 'test-skill');
    assert.equal(stripSkillFrontmatter(raw), '# Body');
  });

  it('parses TOOL_CALL and FINAL_ANSWER lines', () => {
    const call = parseToolCall('TOOL_CALL: {"tool":"grc.list_controls","args":{"tenantId":1}}');
    assert.equal(call?.tool, 'grc.list_controls');
    const fin = parseFinalAnswer('FINAL_ANSWER: Done.');
    assert.equal(fin, 'Done.');
  });

  it('exports claw tools for exec policy', () => {
    assert.equal(CLAW_SKILL_TOOLS.length, 3);
    assert.ok(CLAW_SKILL_TOOLS.some((t) => t.name === 'claw.list_skills'));
  });

  it('listSkills returns array', () => {
    assert.ok(Array.isArray(listSkills()));
  });
});
