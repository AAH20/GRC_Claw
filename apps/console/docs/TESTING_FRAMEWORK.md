# Frontend Testing & Documentation Framework

This directory contains the complete testing and documentation framework for the GRC_Claw console.

## Overview

| Tool | Purpose | Script |
|------|---------|--------|
| **Storybook** | Component isolation, visual docs, interaction testing | `npm run storybook` |
| **Visual Regression** | Pixel-perfect screenshot comparison | `node scripts/visual-regression.mjs` |
| **Component Docs** | Auto-generated Markdown from source | `node scripts/generate-component-docs.mjs` |
| **Accessibility Audit** | axe-core WCAG compliance | `node scripts/accessibility-audit.mjs` |
| **Performance Budget** | Bundle size & chunk analysis | `node scripts/performance-budget.mjs` |

## Quick Start

### 1. Install Dependencies

```bash
cd apps/console

# Storybook
npm install --save-dev @storybook/react-vite @storybook/react \
  @storybook/addon-essentials @storybook/addon-a11y @storybook/addon-interactions

# Visual regression
npm install --save-dev playwright pixelmatch pngjs

# Accessibility audit
npm install --save-dev axe-core @axe-core/playwright

# Performance budget (uses built-in zlib, no extra deps)
```

### 2. Start Storybook

```bash
npm run storybook
# → http://localhost:6006
```

### 3. Run Tests

```bash
# Visual regression (captures baselines first time)
node scripts/visual-regression.mjs --update
node scripts/visual-regression.mjs

# Component documentation
node scripts/generate-component-docs.mjs

# Accessibility audit
node scripts/accessibility-audit.mjs

# Performance budget
node scripts/performance-budget.mjs --build
```

## File Structure

```
apps/console/
├── .storybook/
│   ├── main.ts              # Storybook configuration
│   └── preview.ts           # Global decorators, a11y config, viewports
├── scripts/
│   ├── visual-regression.mjs       # Screenshot comparison
│   ├── generate-component-docs.mjs # Markdown doc generator
│   ├── accessibility-audit.mjs     # axe-core WCAG checks
│   └── performance-budget.mjs       # Bundle size analysis
├── src/components/
│   ├── MetricCard.stories.tsx
│   ├── ComplianceGauge.stories.tsx
│   ├── RiskHeatmap.stories.tsx
│   ├── TimeSeriesChart.stories.tsx
│   ├── A2ZTrustBadge.stories.tsx
│   ├── JsonBlock.stories.tsx
│   ├── PageShell.stories.tsx
│   ├── Layout.stories.tsx
│   └── CursorAutoPanel.stories.tsx
├── docs/components/          # Auto-generated Markdown docs
├── visual-baselines/         # Screenshot baselines (git-committed)
├── visual-diffs/             # Diff images on failure
├── a11y-reports/             # Accessibility audit reports
├── perf-reports/             # Performance budget reports
└── perf-budget.json          # Configurable size budgets
```

## Configuration

### Storybook (`.storybook/main.ts`)

- **Stories**: `src/**/*.stories.@(ts|tsx|mdx)`
- **Addons**: essentials, a11y, interactions
- **Viewports**: mobile (375px), tablet (768px), desktop (1280px)
- **Backgrounds**: dark (#0b1220), light (#f8fafc)

### Visual Regression (`scripts/visual-regression.mjs`)

| Flag | Default | Description |
|------|---------|-------------|
| `--update` | false | Capture new baselines |
| `--threshold=` | 0.1 | Max pixel diff ratio (10%) |
| `--port=` | 6006 | Storybook port |

### Accessibility Audit (`scripts/accessibility-audit.mjs`)

| Flag | Default | Description |
|------|---------|-------------|
| `--severity=` | minor | Minimum severity to report |
| `--port=` | 6006 | Storybook port |
| `--json-only` | false | Suppress console output |

Severity levels: `critical` > `serious` > `moderate` > `minor`

### Performance Budget (`perf-budget.json`)

| Budget | Default | Description |
|--------|---------|-------------|
| `initialJS` | 300 KB | Gzipped JS loaded on first paint |
| `initialCSS` | 20 KB | Gzipped CSS loaded on first paint |
| `totalJS` | 500 KB | Total gzipped JS |
| `totalCSS` | 50 KB | Total gzipped CSS |
| `maxChunkSize` | 150 KB | Largest single JS chunk |
| `maxChunks` | 10 | Maximum JS chunk count |

## CI Integration

```yaml
# .github/workflows/frontend-tests.yml
name: Frontend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npm run build
      - run: npm run storybook &  # Start Storybook in background
      - run: sleep 10  # Wait for Storybook
      - run: node scripts/visual-regression.mjs
      - run: node scripts/accessibility-audit.mjs
      - run: node scripts/performance-budget.mjs
      - run: node scripts/generate-component-docs.mjs
```

## Writing Stories

```tsx
// src/components/MyComponent.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { MyComponent } from './MyComponent';

const meta: Meta<typeof MyComponent> = {
  title: 'Components/MyComponent',
  component: MyComponent,
  tags: ['autodocs'],
  argTypes: {
    // Define controls
  },
};

export default meta;
type Story = StoryObj<typeof MyComponent>;

export const Default: Story = {
  args: {
    // Default props
  },
};

export const Variant: Story = {
  args: {
    // Variant props
  },
};
```

## Component Documentation

The documentation generator scans `src/components/*.tsx` and extracts:
- TypeScript interfaces and prop types
- JSDoc comments
- Export signatures
- Import dependencies
- Component metadata (hooks used, line count)

Output: `docs/components/*.md` with a `README.md` index.

## Troubleshooting

**Storybook not starting**: Ensure `@storybook/react-vite` is installed and `vite.config.ts` is compatible.

**Visual regression false positives**: Increase `--threshold` or use `--update` after intentional UI changes.

**Accessibility audit timeouts**: Increase the `waitUntil` timeout in the script for slow-rendering components.

**Performance budget failures**: Check `perf-reports/` for detailed chunk analysis. Use `React.lazy()` for code splitting.
