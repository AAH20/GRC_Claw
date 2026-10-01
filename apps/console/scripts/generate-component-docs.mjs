#!/usr/bin/env node
/**
 * Component documentation generator for GRC_Claw console.
 *
 * Scans all .tsx files in src/components/, extracts TypeScript interfaces,
 * JSDoc comments, and prop types, then generates Markdown documentation.
 *
 * Usage:
 *   node scripts/generate-component-docs.mjs [--output=docs/components] [--watch]
 */

import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname, basename, relative } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ─── Args ────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const OUTPUT_DIR = args.find((a) => a.startsWith('--output='))?.split('=')[1] ?? join(ROOT, 'docs', 'components');
const WATCH = args.includes('--watch');

// ─── Helpers ──────────────────────────────────────────────────────────────────
function log(msg) { console.log(`[docs-gen] ${msg}`); }

function extractInterfaces(content) {
  const interfaces = [];
  const regex = /interface\s+(\w+)(?:\s+extends\s+([\w<>,\s]+?))?\s*\{([^}]+)\}/gs;
  let match;
  while ((match = regex.exec(content)) !== null) {
    const [, name, extendsClause, body] = match;
    const props = [];
    for (const line of body.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('//') || trimmed.startsWith('*')) continue;
      const propMatch = trimmed.match(/^(\w+)(\?)?:\s*(.+?);?$/);
      if (propMatch) {
        props.push({
          name: propMatch[1],
          optional: propMatch[2] === '?',
          type: propMatch[3].replace(/;$/, '').trim(),
        });
      }
    }
    interfaces.push({ name, extends: extendsClause?.trim() || null, props });
  }
  return interfaces;
}

function extractJSDoc(content) {
  const comments = [];
  const regex = /\/\*\*([\s\S]*?)\*\//g;
  let match;
  while ((match = regex.exec(content)) !== null) {
    const text = match[1]
      .split('\n')
      .map((l) => l.replace(/^\s*\*\s?/, '').trim())
      .filter(Boolean)
      .join('\n');
    if (text) comments.push(text);
  }
  return comments;
}

function extractExports(content) {
  const exports = [];
  const regex = /export\s+(?:function|const|class|interface|type|enum)\s+(\w+)/g;
  let match;
  while ((match = regex.exec(content)) !== null) {
    exports.push(match[1]);
  }
  return exports;
}

function extractImports(content) {
  const imports = [];
  const regex = /import\s+(?:type\s+)?\{([^}]+)\}\s+from\s+['"]([^'"]+)['"]/g;
  let match;
  while ((match = regex.exec(content)) !== null) {
    const names = match[1].split(',').map((s) => s.trim()).filter(Boolean);
    imports.push({ names, source: match[2] });
  }
  return imports;
}

function extractComponentBody(content, componentName) {
  // Find the function body and extract a summary
  const regex = new RegExp(`export\\s+function\\s+${componentName}\\s*\\([^)]*\\)\\s*\\{([\\s\\S]*?)\\n\\}`, 'm');
  const match = content.match(regex);
  if (!match) return null;
  const body = match[1];
  const lines = body.split('\n').filter((l) => l.trim());
  return {
    lineCount: lines.length,
    hasReturn: body.includes('return ('),
    hasState: body.includes('useState'),
    hasEffect: body.includes('useEffect'),
    hasRef: body.includes('useRef'),
    hasCallback: body.includes('useCallback'),
  };
}

function generateMarkdown(filePath, content) {
  const interfaces = extractInterfaces(content);
  const jsdoc = extractJSDoc(content);
  const exports = extractExports(content);
  const imports = extractImports(content);
  const componentName = exports.find((e) => /^[A-Z]/.test(e));
  const bodyInfo = componentName ? extractComponentBody(content, componentName) : null;

  const relPath = relative(ROOT, filePath);
  const title = basename(filePath, '.tsx');

  let md = `# ${title}\n\n`;
  md += `> Auto-generated from \`${relPath}\`\n\n`;

  if (jsdoc.length > 0) {
    md += `## Description\n\n${jsdoc.join('\n\n')}\n\n`;
  }

  // Component info
  if (componentName) {
    md += `## Component\n\n`;
    md += `| Property | Value |\n|----------|-------|\n`;
    md += `| Name | \`${componentName}\` |\n`;
    if (bodyInfo) {
      md += `| Lines | ${bodyInfo.lineCount} |\n`;
      md += `| Hooks | ${[
        bodyInfo.hasState && 'useState',
        bodyInfo.hasEffect && 'useEffect',
        bodyInfo.hasRef && 'useRef',
        bodyInfo.hasCallback && 'useCallback',
      ].filter(Boolean).join(', ') || 'none'} |\n`;
    }
    md += `\n`;
  }

  // Props / Interfaces
  if (interfaces.length > 0) {
    md += `## Props & Types\n\n`;
    for (const iface of interfaces) {
      md += `### \`${iface.name}\`\n\n`;
      if (iface.extends) md += `Extends: \`${iface.extends}\`\n\n`;
      if (iface.props.length > 0) {
        md += `| Prop | Type | Required | Description |\n|------|------|----------|-------------|\n`;
        for (const prop of iface.props) {
          md += `| \`${prop.name}\` | \`${prop.type}\` | ${prop.optional ? 'No' : 'Yes'} | |\n`;
        }
        md += `\n`;
      }
    }
  }

  // Exports
  if (exports.length > 0) {
    md += `## Exports\n\n`;
    for (const exp of exports) {
      md += `- \`${exp}\`\n`;
    }
    md += `\n`;
  }

  // Imports
  if (imports.length > 0) {
    md += `## Dependencies\n\n`;
    for (const imp of imports) {
      md += `- \`${imp.source}\`: ${imp.names.map((n) => `\`${n}\``).join(', ')}\n`;
    }
    md += `\n`;
  }

  // Usage example
  if (componentName) {
    md += `## Usage\n\n\`\`\`tsx\nimport { ${componentName} } from './${title}';\n\n// Example usage\n<${componentName} />\n\`\`\`\n\n`;
  }

  md += `---\n\n*Generated by \`scripts/generate-component-docs.mjs\`*\n`;
  return md;
}

function scanComponents() {
  const componentsDir = join(ROOT, 'src', 'components');
  if (!existsSync(componentsDir)) {
    log('No src/components/ directory found.');
    return [];
  }

  const files = [];
  function walk(dir) {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith('.tsx') && !entry.name.endsWith('.stories.tsx')) {
        files.push(full);
      }
    }
  }
  walk(componentsDir);
  return files;
}

// ─── Main ─────────────────────────────────────────────────────────────────────
function generate() {
  if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true });

  const files = scanComponents();
  log(`Scanning ${files.length} component files...`);

  const indexEntries = [];

  for (const file of files) {
    const content = readFileSync(file, 'utf-8');
    const md = generateMarkdown(file, content);
    const outName = basename(file, '.tsx') + '.md';
    const outPath = join(OUTPUT_DIR, outName);
    writeFileSync(outPath, md);
    indexEntries.push({ name: basename(file, '.tsx'), file: outName });
    log(`  → ${outName}`);
  }

  // Generate index
  let index = '# Component Documentation\n\n';
  index += '> Auto-generated by `scripts/generate-component-docs.mjs`\n\n';
  index += '## Components\n\n';
  for (const entry of indexEntries.sort((a, b) => a.name.localeCompare(b.name))) {
    index += `- [${entry.name}](./${entry.file})\n`;
  }
  writeFileSync(join(OUTPUT_DIR, 'README.md'), index);
  log(`  → README.md (index)`);

  log(`\nGenerated ${indexEntries.length} component docs in ${relative(ROOT, OUTPUT_DIR)}/`);
}

if (WATCH) {
  log('Watching for changes...');
  generate();
  const { watch } = require('fs');
  watch(join(ROOT, 'src', 'components'), { recursive: true }, () => {
    log('Change detected, regenerating...');
    generate();
  });
} else {
  generate();
}
