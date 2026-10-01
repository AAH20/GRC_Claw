import type { Meta, StoryObj } from '@storybook/react';
import { CopyBlock } from './CursorAutoPanel';

const meta: Meta<typeof CopyBlock> = {
  title: 'Components/CopyBlock',
  component: CopyBlock,
  tags: ['autodocs'],
  argTypes: {
    text: { control: 'text' },
    label: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof CopyBlock>;

export const Default: Story = {
  args: {
    text: 'curl -X GET http://localhost:18791/health',
    label: 'Health check',
  },
};

export const WithoutLabel: Story = {
  args: {
    text: '{"status": "ok"}',
  },
};

export const LongText: Story = {
  args: {
    text: JSON.stringify(
      {
        service: 'grc-claw-gateway',
        endpoints: [
          { method: 'GET', path: '/health', auth: false },
          { method: 'GET', path: '/api/connectors', auth: true },
          { method: 'POST', path: '/api/agent/invoke', auth: true },
          { method: 'GET', path: '/api/frameworks', auth: true },
          { method: 'POST', path: '/api/ingest', auth: true },
        ],
      },
      null,
      2
    ),
    label: 'API Reference',
  },
};

export const Empty: Story = {
  args: { text: '', label: 'Empty' },
};
