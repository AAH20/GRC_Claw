import type { Meta, StoryObj } from '@storybook/react';
import { AgentChatWindow } from './AgentChatWindow';

const meta: Meta<typeof AgentChatWindow> = {
  title: 'Components/AgentChatWindow',
  component: AgentChatWindow,
  tags: ['autodocs'],
  argTypes: {
    llmProviderId: { control: 'text' },
    llmAvailable: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof AgentChatWindow>;

export const Default: Story = {
  args: {
    llmProviderId: 'gemini',
    llmAvailable: true,
  },
};

export const NoLlm: Story = {
  args: {
    llmProviderId: 'gemini',
    llmAvailable: false,
  },
};

export const CursorAutoMode: Story = {
  args: {
    llmProviderId: 'cursor-auto',
    llmAvailable: true,
  },
};
