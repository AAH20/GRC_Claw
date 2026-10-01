import type { Meta, StoryObj } from '@storybook/react';
import { PageShell } from './PageShell';
import type { PageMeta } from '../lib/pageMeta';

const meta: Meta<typeof PageShell> = {
  title: 'Components/PageShell',
  component: PageShell,
  tags: ['autodocs'],
  argTypes: {
    meta: { control: 'object' },
    actions: { control: 'object' },
  },
};

export default meta;
type Story = StoryObj<typeof PageShell>;

const sampleMeta: PageMeta = {
  id: 'storybook-demo',
  title: 'Storybook Demo Page',
  subtitle: 'Demonstrating PageShell layout',
  explain: {
    what: 'This is a demo page showing how PageShell wraps content with consistent headers, explain cards, and A2Z integration.',
    why: 'Consistent page structure reduces cognitive load and ensures every page has proper context for operators.',
    how: [
      'Navigate to the page',
      'Read the explain cards for context',
      'Use the main content area',
      'Check the A2Z SOC integration panel',
    ],
    a2zRole: 'This page syncs compliance data to A2Z SOC for continuous monitoring and trust scoring.',
  },
  cursor: {
    method: 'GET',
    endpoint: '/api/demo',
    auth: false,
    agentInstruction: 'Fetch demo data for testing',
  },
};

export const Default: Story = {
  args: {
    meta: sampleMeta,
    children: (
      <div className="card">
        <h2>Main Content</h2>
        <p className="explain-lead">
          This is the main content area where page-specific components and data are rendered.
        </p>
      </div>
    ),
  },
};

export const WithActions: Story = {
  args: {
    meta: sampleMeta,
    actions: (
      <>
        <button type="button" className="primary">Primary Action</button>
        <button type="button">Secondary Action</button>
      </>
    ),
    children: (
      <div className="card">
        <h2>Page with Actions</h2>
        <p className="explain-lead">The actions area appears in the page header.</p>
      </div>
    ),
  },
};

export const Minimal: Story = {
  args: {
    meta: { ...sampleMeta, title: 'Minimal Page' },
    children: null,
  },
};
