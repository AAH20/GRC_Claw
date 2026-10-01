import type { Meta, StoryObj } from '@storybook/react';
import { JsonBlock } from './JsonBlock';

const meta: Meta<typeof JsonBlock> = {
  title: 'Components/JsonBlock',
  component: JsonBlock,
  tags: ['autodocs'],
  argTypes: {
    data: { control: 'object' },
  },
};

export default meta;
type Story = StoryObj<typeof JsonBlock>;

export const Default: Story = {
  args: {
    data: {
      service: 'grc-claw-gateway',
      status: 'healthy',
      uptime: '3d 14h 22m',
      version: '1.2.0',
    },
  },
};

export const Nested: Story = {
  args: {
    data: {
      connectors: {
        llm: [
          { id: 'gemini', apiKeyConfigured: true },
          { id: 'openai', apiKeyConfigured: false },
        ],
        mcp: [
          { id: 'filesystem', status: 'connected' },
        ],
      },
      metrics: {
        requests: 1234,
        errors: 12,
        latency: { p50: 45, p95: 120, p99: 250 },
      },
    },
  },
};

export const Null: Story = {
  args: { data: null },
};

export const Array: Story = {
  args: {
    data: [
      { id: 1, name: 'ISO 27001', status: 'active' },
      { id: 2, name: 'SOC 2', status: 'pending' },
      { id: 3, name: 'CMMC', status: 'active' },
    ],
  },
};

export const EmptyObject: Story = {
  args: { data: {} },
};

export const String: Story = {
  args: { data: 'Simple string value' },
};

export const Number: Story = {
  args: { data: 42 },
};
