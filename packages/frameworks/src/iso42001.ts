import type { FrameworkPack } from './index.js';

export const iso42001StarterPack: FrameworkPack = {
  code: 'iso42001',
  name: 'ISO/IEC 42001 AIMS (starter)',
  version: '2026.1',
  controls: [
    {
      id: 'aims-a.2.1',
      controlCode: 'A.2.1',
      title: 'AI policy',
      frameworkCode: 'iso42001',
      domain: 'Policies',
    },
    {
      id: 'aims-a.9.1',
      controlCode: 'A.9.1',
      title: 'Third-party AI services and suppliers',
      frameworkCode: 'iso42001',
      domain: 'Third-party',
    },
    {
      id: 'aims-a.10.1',
      controlCode: 'A.10.1',
      title: 'Monitoring and measurement of AI systems',
      frameworkCode: 'iso42001',
      domain: 'Monitoring',
    },
    {
      id: 'aims-a.12.1',
      controlCode: 'A.12.1',
      title: 'AI system security — gateway access',
      frameworkCode: 'iso42001',
      domain: 'Security',
    },
    {
      id: 'aims-a.12.2',
      controlCode: 'A.12.2',
      title: 'AI system security — tool mediation',
      frameworkCode: 'iso42001',
      domain: 'Security',
    },
    {
      id: 'aims-a.12.3',
      controlCode: 'A.12.3',
      title: 'Human oversight of agent tools',
      frameworkCode: 'iso42001',
      domain: 'Security',
    },
    {
      id: 'aims-a.14.1',
      controlCode: 'A.14.1',
      title: 'Safety — destructive action approval',
      frameworkCode: 'iso42001',
      domain: 'Safety',
    },
  ],
};
