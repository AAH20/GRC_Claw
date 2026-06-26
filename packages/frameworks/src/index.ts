import type { ComplianceControl } from '@grc-claw/core';

export interface FrameworkPack {
  code: string;
  name: string;
  version: string;
  controls: Omit<ComplianceControl, 'orgStatus'>[];
}

export const iso27001StarterPack: FrameworkPack = {
  code: 'iso27001',
  name: 'ISO/IEC 27001 (starter)',
  version: '2026.1',
  controls: [
    {
      id: 'iso-a.5.1',
      controlCode: 'A.5.1',
      title: 'Policies for information security',
      frameworkCode: 'iso27001',
      domain: 'Organizational',
    },
    {
      id: 'iso-a.8.15',
      controlCode: 'A.8.15',
      title: 'Logging',
      frameworkCode: 'iso27001',
      domain: 'Technological',
    },
    {
      id: 'iso-a.8.16',
      controlCode: 'A.8.16',
      title: 'Monitoring activities',
      frameworkCode: 'iso27001',
      domain: 'Technological',
    },
  ],
};

export const nistCsfStarterPack: FrameworkPack = {
  code: 'nist_csf',
  name: 'NIST CSF 2.0 (starter)',
  version: '2026.1',
  controls: [
    {
      id: 'nist-de.ae',
      controlCode: 'DE.AE',
      title: 'Adverse Event Analysis',
      frameworkCode: 'nist_csf',
      domain: 'Detect',
    },
    {
      id: 'nist-rs.ma',
      controlCode: 'RS.MA',
      title: 'Incident Management',
      frameworkCode: 'nist_csf',
      domain: 'Respond',
    },
  ],
};

export const soc2StarterPack: FrameworkPack = {
  code: 'soc2',
  name: 'SOC 2 Trust Services (starter)',
  version: '2026.1',
  controls: [
    {
      id: 'soc2-cc6.1',
      controlCode: 'CC6.1',
      title: 'Logical access security',
      frameworkCode: 'soc2',
      domain: 'Common Criteria',
    },
    {
      id: 'soc2-cc7.2',
      controlCode: 'CC7.2',
      title: 'System monitoring',
      frameworkCode: 'soc2',
      domain: 'Common Criteria',
    },
  ],
};

import { iso42001StarterPack } from './iso42001.js';
import { EXPANDED_FRAMEWORK_PACKS } from './expanded-packs.js';

export { iso42001StarterPack } from './iso42001.js';
export { EXPANDED_FRAMEWORK_PACKS } from './expanded-packs.js';

export function listFrameworkPacks(): FrameworkPack[] {
  return [iso27001StarterPack, nistCsfStarterPack, soc2StarterPack, iso42001StarterPack, ...EXPANDED_FRAMEWORK_PACKS];
}

export {
  iso27001ExpandedPack, nistCsfExpandedPack, soc2ExpandedPack, iso42001ExpandedPack,
  gdprPack, hipaaPack, pciDssPack, fedrampPack, cmmcPack, nist80053Pack, nist800171Pack,
  cisControlsPack, cobitPack, csaCcmPack, iso27701Pack, iso27017Pack, iso27018Pack,
  soc1Pack, doraPack, nis2Pack, ccpaPack, lgpdPack, pipedaPack,
  apraCps234Pack, masTrmPack, sgpdpaPack, japanAppiPack,
} from './expanded-packs.js';

export function listAllFrameworkPacks(): FrameworkPack[] {
  return listFrameworkPacks();
}
