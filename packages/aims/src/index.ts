export {
  listVendorGaps,
  listVendorGapSummary,
  VENDOR_GAP_MATRIX,
  type VendorGapRow,
  type VendorId,
} from './vendor-gaps.js';
export { listTechnicalControls, AIMS_TECHNICAL_CONTROLS, type AimsTechnicalControl } from './technical-controls.js';
export { listClauseMap, ISO_42001_CLAUSE_MAP, type ClauseMapping } from './clause-map.js';

export const AIMS_SCOPE_TEMPLATE = {
  standard: 'ISO/IEC 42001:2023',
  product: 'GRC_Claw (OpenClaw for GRC)',
  productionSoc: 'https://a2zsoc.com',
  inScope: [
    'GRC_Claw gateway and agent-runtime',
    'Framework packs including ISO 42001 AIMS controls',
    'Customer deployments integrated with a2zsoc.com',
  ],
  outOfScope: [
    'Customer-owned LLM training data',
    'Third-party model weights (Anthropic, OpenAI, etc.) — documented as suppliers',
  ],
};
