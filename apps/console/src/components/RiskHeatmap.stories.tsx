import type { Meta, StoryObj } from '@storybook/react';
import { RiskHeatmap } from './RiskHeatmap';

const meta: Meta<typeof RiskHeatmap> = {
  title: 'Components/RiskHeatmap',
  component: RiskHeatmap,
  tags: ['autodocs'],
  argTypes: {
    cells: { control: 'object' },
  },
};

export default meta;
type Story = StoryObj<typeof RiskHeatmap>;

const sampleCells = [
  { likelihood: 1, impact: 1, count: 2 },
  { likelihood: 1, impact: 2, count: 1 },
  { likelihood: 2, impact: 1, count: 3 },
  { likelihood: 2, impact: 3, count: 5 },
  { likelihood: 3, impact: 2, count: 4 },
  { likelihood: 3, impact: 4, count: 8 },
  { likelihood: 4, impact: 3, count: 6 },
  { likelihood: 4, impact: 5, count: 12 },
  { likelihood: 5, impact: 4, count: 9 },
  { likelihood: 5, impact: 5, count: 15 },
];

export const Default: Story = {
  args: { cells: sampleCells },
};

export const Empty: Story = {
  args: { cells: [] },
};

export const SingleCell: Story = {
  args: { cells: [{ likelihood: 3, impact: 3, count: 1 }] },
};

export const AllCells: Story = {
  args: {
    cells: Array.from({ length: 25 }, (_, i) => ({
      likelihood: Math.floor(i / 5) + 1,
      impact: (i % 5) + 1,
      count: Math.floor(Math.random() * 20),
    })),
  },
};

export const CriticalOnly: Story = {
  args: {
    cells: [
      { likelihood: 5, impact: 5, count: 25 },
      { likelihood: 5, impact: 4, count: 18 },
      { likelihood: 4, impact: 5, count: 22 },
    ],
  },
};
