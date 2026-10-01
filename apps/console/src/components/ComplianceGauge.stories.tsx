import type { Meta, StoryObj } from '@storybook/react';
import { ComplianceGauge } from './ComplianceGauge';

const meta: Meta<typeof ComplianceGauge> = {
  title: 'Components/ComplianceGauge',
  component: ComplianceGauge,
  tags: ['autodocs'],
  argTypes: {
    score: { control: { type: 'range', min: 0, max: 100 } },
  },
};

export default meta;
type Story = StoryObj<typeof ComplianceGauge>;

export const Default: Story = {
  args: { score: 87 },
};

export const LowScore: Story = {
  args: { score: 45 },
};

export const MediumScore: Story = {
  args: { score: 72 },
};

export const HighScore: Story = {
  args: { score: 95 },
};

export const Zero: Story = {
  args: { score: 0 },
};

export const Perfect: Story = {
  args: { score: 100 },
};

export const ClampedHigh: Story = {
  args: { score: 150 },
};

export const ClampedLow: Story = {
  args: { score: -10 },
};
