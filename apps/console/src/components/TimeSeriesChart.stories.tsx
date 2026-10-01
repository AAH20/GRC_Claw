import type { Meta, StoryObj } from '@storybook/react';
import { TimeSeriesChart } from './TimeSeriesChart';

const meta: Meta<typeof TimeSeriesChart> = {
  title: 'Components/TimeSeriesChart',
  component: TimeSeriesChart,
  tags: ['autodocs'],
  argTypes: {
    data: { control: 'object' },
    height: { control: { type: 'range', min: 100, max: 400 } },
  },
};

export default meta;
type Story = StoryObj<typeof TimeSeriesChart>;

export const Default: Story = {
  args: {
    data: [
      { label: '0s', value: 10 },
      { label: '15s', value: 25 },
      { label: '30s', value: 18 },
      { label: '45s', value: 42 },
      { label: '60s', value: 35 },
      { label: '75s', value: 58 },
      { label: '90s', value: 47 },
      { label: '105s', value: 72 },
      { label: '120s', value: 65 },
      { label: 'Now', value: 89 },
    ],
    height: 150,
  },
};

export const Empty: Story = {
  args: { data: [], height: 150 },
};

export const SinglePoint: Story = {
  args: {
    data: [{ label: 'Now', value: 42 }],
    height: 150,
  },
};

export const ManyPoints: Story = {
  args: {
    data: Array.from({ length: 30 }, (_, i) => ({
      label: `${i * 5}s`,
      value: Math.floor(Math.random() * 100),
    })),
    height: 200,
  },
};

export const TallChart: Story = {
  args: {
    data: [
      { label: 'Jan', value: 30 },
      { label: 'Feb', value: 45 },
      { label: 'Mar', value: 28 },
      { label: 'Apr', value: 62 },
      { label: 'May', value: 55 },
      { label: 'Jun', value: 78 },
    ],
    height: 300,
  },
};

export const FlatLine: Story = {
  args: {
    data: [
      { label: 'A', value: 50 },
      { label: 'B', value: 50 },
      { label: 'C', value: 50 },
      { label: 'D', value: 50 },
    ],
    height: 150,
  },
};
