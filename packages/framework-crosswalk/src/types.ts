export type MappingRelationship = 'equivalent' | 'partial' | 'supports';

export interface CrossMapping {
  sourceFramework: string;
  sourceControl: string;
  targetFramework: string;
  targetControl: string;
  confidence: number;
  relationship: MappingRelationship;
}

export interface CrosswalkReport {
  sourceFramework: string;
  targetFramework: string;
  mappings: CrossMapping[];
  coverage: number;
  gaps: string[];
}

export interface FrameworkOverlap {
  framework1: string;
  framework2: string;
  overlappingControls: number;
  totalControls: number;
  overlapPercentage: number;
}

export interface CrossMappingStore {
  getMappings(source: string, target: string): CrossMapping[];
  addMapping(mapping: CrossMapping): void;
  getSupportedPairs(): Array<[string, string]>;
}
