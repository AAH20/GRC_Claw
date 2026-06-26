import type { CrossMapping } from '../types.js';

export const PCIDSS_ISO27001_MAPPINGS: CrossMapping[] = [
  { sourceFramework: 'pci_dss', sourceControl: 'Req 1', targetFramework: 'iso27001', targetControl: 'A.8.20', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 2', targetFramework: 'iso27001', targetControl: 'A.8.9', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 3', targetFramework: 'iso27001', targetControl: 'A.8.24', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 4', targetFramework: 'iso27001', targetControl: 'A.8.24', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 5', targetFramework: 'iso27001', targetControl: 'A.8.7', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 6', targetFramework: 'iso27001', targetControl: 'A.8.25', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 6.2', targetFramework: 'iso27001', targetControl: 'A.8.8', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 7', targetFramework: 'iso27001', targetControl: 'A.5.15', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 8', targetFramework: 'iso27001', targetControl: 'A.8.5', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 8.2', targetFramework: 'iso27001', targetControl: 'A.5.16', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 8.3', targetFramework: 'iso27001', targetControl: 'A.8.5', confidence: 0.9, relationship: 'supports' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 9', targetFramework: 'iso27001', targetControl: 'A.7.1', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 10', targetFramework: 'iso27001', targetControl: 'A.8.15', confidence: 0.9, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 11', targetFramework: 'iso27001', targetControl: 'A.8.8', confidence: 0.85, relationship: 'partial' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 12.1', targetFramework: 'iso27001', targetControl: 'A.5.1', confidence: 0.85, relationship: 'equivalent' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 12.3', targetFramework: 'iso27001', targetControl: 'A.5.7', confidence: 0.8, relationship: 'partial' },
  { sourceFramework: 'pci_dss', sourceControl: 'Req 12.10', targetFramework: 'iso27001', targetControl: 'A.5.24', confidence: 0.85, relationship: 'equivalent' },
];

export const PCIDSS_ISO27001_PAIR = { source: 'pci_dss', target: 'iso27001' };
