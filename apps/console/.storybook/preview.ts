import type { Preview } from '@storybook/react';
import '../src/styles/globals.css';

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    a11y: {
      element: '#root',
      config: {
        rules: [
          { id: 'color-contrast', enabled: true },
          { id: 'heading-order', enabled: true },
          { id: 'label', enabled: true },
        ],
      },
    },
    backgrounds: {
      default: 'dark',
      values: [
        { name: 'dark', value: '#0b1220' },
        { name: 'light', value: '#f8fafc' },
      ],
    },
    viewport: {
      viewports: {
        mobile: { name: 'Mobile', styles: { width: '375px', height: '667px' } },
        tablet: { name: 'Tablet', styles: { width: '768px', height: '1024px' } },
        desktop: { name: 'Desktop', styles: { width: '1280px', height: '800px' } },
      },
    },
  },
  decorators: [
    (Story) => (
      <div style={{ padding: '1rem', minHeight: '100vh' }}>
        <Story />
      </div>
    ),
  ],
};

export default preview;
