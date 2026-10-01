import type { Meta, StoryObj } from '@storybook/react';
import { A2ZTrustBadge } from './A2ZTrustBadge';

const meta: Meta<typeof A2ZTrustBadge> = {
  title: 'Components/A2ZTrustBadge',
  component: A2ZTrustBadge,
  tags: ['autodocs'],
  argTypes: {
    compact: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof A2ZTrustBadge>;

export const Default: Story = {
  args: {},
};

export const Compact: Story = {
  args: { compact: true },
};

export const FullSize: Story = {
  args: { compact: false },
};
