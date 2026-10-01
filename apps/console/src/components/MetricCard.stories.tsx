import type { Meta, StoryObj } from '@storybook/react';
import { MetricCard } from './MetricCard';

const meta: Meta<typeof MetricCard> = {
  title: 'Components/MetricCard',
  component: MetricCard,
  tags: ['autodocs'],
  argTypes: {
    name: { control: 'text' },
    value: { control: 'text' },
    trend: { control: 'object' },
    sparkline: { control: 'object' },
  },
};

export default meta;
type Story = StoryObj<typeof MetricCard>;

export const Default: Story = {
  args: {
    name: 'Total Requests',
    value: 1234,
  },
};

export const WithTrend: Story = {
  args: {
    name: 'Agent Invocations',
    value: 567,
    trend: { direction: 'up', percentage: 12 },
  },
};

export const WithSparkline: Story = {
  args: {
    name: 'Request Volume',
    value: 890,
    trend: { direction: 'up', percentage: 8 },
    sparkline: [10, 25, 18, 42, 35, 58, 47, 72, 65, 89],
  },
};

export const NegativeTrend: Story = {
  args: {
    name: 'Error Rate',
    value: 2.3,
    trend: { direction: 'down', percentage: 15 },
  },
};

export const StringValue: Story = {
  args: {
    name: 'Gateway Status',
    value: 'Operational',
  },
};

export const LargeNumber: Story = {
  args: {
    name: 'Total Findings',
    value: 1234567,
    trend: { direction: 'up', percentage: 23 },
  },
};
