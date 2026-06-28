/**
 * RegulatoryChangeManagement - Automated tracking of regulatory changes
 * 
 * Monitors regulatory sources, detects changes, and maps them to existing controls.
 * Provides impact analysis and remediation recommendations.
 * 
 * Features:
 * - Multi-source regulatory monitoring (RSS, API, web scraping)
 * - Change detection and classification
 * - Impact analysis on existing controls
 * - Automated remediation recommendations
 * - Compliance gap identification
 * - Regulatory timeline tracking
 */

export interface RegulatorySource {
  id: string;
  name: string;
  type: 'rss' | 'api' | 'webhook' | 'manual';
  url: string;
  framework: string;
  frequency: 'realtime' | 'daily' | 'weekly' | 'monthly';
  lastChecked: Date;
  enabled: boolean;
}

export interface RegulatoryChange {
  id: string;
  sourceId: string;
  title: string;
  description: string;
  effectiveDate: Date;
  publishedDate: Date;
  framework: string;
  changeType: 'new_regulation' | 'amendment' | 'guidance' | 'enforcement' | 'deadline';
  severity: 'critical' | 'high' | 'medium' | 'low';
  affectedControls: string[];
  impactAnalysis?: ImpactAnalysis;
  status: 'detected' | 'analyzed' | 'acknowledged' | 'in_remediation' | 'completed';
}

export interface ImpactAnalysis {
  affectedControls: AffectedControl[];
  overallImpact: 'critical' | 'high' | 'medium' | 'low' | 'none';
  estimatedEffort: string;
  recommendedActions: string[];
  deadlineImplications: string[];
}

export interface AffectedControl {
  controlId: string;
  framework: string;
  impact: 'critical' | 'high' | 'medium' | 'low' | 'none';
  gapDescription: string;
  remediationRequired: boolean;
  estimatedEffort: string;
}

export interface RegulatoryTimeline {
  changeId: string;
  milestones: TimelineMilestone[];
  currentPhase: string;
  daysRemaining?: number;
}

export interface TimelineMilestone {
  name: string;
  date: Date;
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  description: string;
}

export interface ComplianceGap {
  id: string;
  changeId: string;
  controlId: string;
  framework: string;
  gapType: 'new_requirement' | 'strengthened_requirement' | 'new_evidence' | 'deadline_change';
  description: string;
  remediationPlan?: RemediationPlan;
  status: 'open' | 'in_remediation' | 'closed';
}

export interface RemediationPlan {
  steps: RemediationStep[];
  estimatedEffort: string;
  assignedTo?: string;
  deadline?: Date;
  status: 'not_started' | 'in_progress' | 'completed';
}

export interface RemediationStep {
  name: string;
  description: string;
  estimatedHours: number;
  dependencies: string[];
  status: 'pending' | 'in_progress' | 'completed';
}

export class RegulatoryChangeManagement {
  private sources: Map<string, RegulatorySource> = new Map();
  private changes: Map<string, RegulatoryChange> = new Map();
  private gaps: Map<string, ComplianceGap> = new Map();
  private timelines: Map<string, RegulatoryTimeline> = new Map();

  constructor(
    private readonly options: {
      checkIntervalMs?: number;
      maxChanges?: number;
      autoAnalyze?: boolean;
    } = {}
  ) {
    this.options = {
      checkIntervalMs: 3600000, // 1 hour
      maxChanges: 1000,
      autoAnalyze: true,
      ...options
    };
  }

  /**
   * Register a regulatory source
   */
  registerSource(source: RegulatorySource): void {
    this.sources.set(source.id, source);
  }

  /**
   * Check for regulatory changes
   */
  async checkForChanges(): Promise<RegulatoryChange[]> {
    const newChanges: RegulatoryChange[] = [];

    for (const source of this.sources.values()) {
      if (!source.enabled) continue;

      try {
        const changes = await this.fetchChanges(source);
        for (const change of changes) {
          if (!this.changes.has(change.id)) {
            this.changes.set(change.id, change);
            newChanges.push(change);

            // Auto-analyze if enabled
            if (this.options.autoAnalyze) {
              await this.analyzeChange(change.id);
            }
          }
        }

        source.lastChecked = new Date();
      } catch (error) {
        console.error(`Failed to check source ${source.name}:`, error);
      }
    }

    return newChanges;
  }

  /**
   * Analyze impact of a regulatory change
   */
  async analyzeChange(changeId: string): Promise<ImpactAnalysis | null> {
    const change = this.changes.get(changeId);
    if (!change) return null;

    // Analyze impact on controls
    const affectedControls = await this.analyzeAffectedControls(change);
    
    const impactAnalysis: ImpactAnalysis = {
      affectedControls,
      overallImpact: this.calculateOverallImpact(affectedControls),
      estimatedEffort: this.estimateRemediationEffort(affectedControls),
      recommendedActions: this.generateRecommendations(change, affectedControls),
      deadlineImplications: this.analyzeDeadlineImplications(change)
    };

    change.impactAnalysis = impactAnalysis;
    change.status = 'analyzed';

    // Create compliance gaps
    this.createComplianceGaps(change, affectedControls);

    // Create timeline
    this.createTimeline(change);

    return impactAnalysis;
  }

  /**
   * Get all regulatory changes
   */
  getChanges(filters?: {
    framework?: string;
    severity?: string;
    status?: string;
    fromDate?: Date;
    toDate?: Date;
  }): RegulatoryChange[] {
    let changes = Array.from(this.changes.values());

    if (filters) {
      if (filters.framework) {
        changes = changes.filter(c => c.framework === filters.framework);
      }
      if (filters.severity) {
        changes = changes.filter(c => c.severity === filters.severity);
      }
      if (filters.status) {
        changes = changes.filter(c => c.status === filters.status);
      }
      if (filters.fromDate) {
        changes = changes.filter(c => c.publishedDate >= filters.fromDate!);
      }
      if (filters.toDate) {
        changes = changes.filter(c => c.publishedDate <= filters.toDate!);
      }
    }

    return changes.sort((a, b) => b.publishedDate.getTime() - a.publishedDate.getTime());
  }

  /**
   * Get compliance gaps
   */
  getGaps(filters?: {
    framework?: string;
    status?: string;
    changeId?: string;
  }): ComplianceGap[] {
    let gaps = Array.from(this.gaps.values());

    if (filters) {
      if (filters.framework) {
        gaps = gaps.filter(g => g.framework === filters.framework);
      }
      if (filters.status) {
        gaps = gaps.filter(g => g.status === filters.status);
      }
      if (filters.changeId) {
        gaps = gaps.filter(g => g.changeId === filters.changeId);
      }
    }

    return gaps;
  }

  /**
   * Get timeline for a change
   */
  getTimeline(changeId: string): RegulatoryTimeline | undefined {
    return this.timelines.get(changeId);
  }

  /**
   * Update gap status
   */
  updateGapStatus(gapId: string, status: ComplianceGap['status']): void {
    const gap = this.gaps.get(gapId);
    if (gap) {
      gap.status = status;
    }
  }

  /**
   * Create remediation plan for a gap
   */
  createRemediationPlan(gapId: string, plan: RemediationPlan): void {
    const gap = this.gaps.get(gapId);
    if (gap) {
      gap.remediationPlan = plan;
      gap.status = 'in_remediation';
    }
  }

  /**
   * Get regulatory sources
   */
  getSources(): RegulatorySource[] {
    return Array.from(this.sources.values());
  }

  /**
   * Fetch changes from a source (stub - would integrate with real APIs)
   */
  private async fetchChanges(source: RegulatorySource): Promise<RegulatoryChange[]> {
    // In a real implementation, this would fetch from RSS/API/webhook
    // For now, return empty array
    return [];
  }

  /**
   * Analyze affected controls
   */
  private async analyzeAffectedControls(change: RegulatoryChange): Promise<AffectedControl[]> {
    // In a real implementation, this would analyze the change against the control framework
    // For now, return empty array
    return [];
  }

  /**
   * Calculate overall impact
   */
  private calculateOverallImpact(controls: AffectedControl[]): ImpactAnalysis['overallImpact'] {
    if (controls.length === 0) return 'none';
    
    const hasCritical = controls.some(c => c.impact === 'critical');
    const hasHigh = controls.some(c => c.impact === 'high');
    const hasMedium = controls.some(c => c.impact === 'medium');

    if (hasCritical) return 'critical';
    if (hasHigh) return 'high';
    if (hasMedium) return 'medium';
    return 'low';
  }

  /**
   * Estimate remediation effort
   */
  private estimateRemediationEffort(controls: AffectedControl[]): string {
    const totalHours = controls.reduce((sum, c) => {
      const hours = parseInt(c.estimatedEffort) || 0;
      return sum + hours;
    }, 0);

    if (totalHours === 0) return 'Minimal';
    if (totalHours < 40) return `${totalHours} hours`;
    if (totalHours < 160) return `${Math.round(totalHours / 40)} weeks`;
    return `${Math.round(totalHours / 160)} months`;
  }

  /**
   * Generate recommendations
   */
  private generateRecommendations(
    change: RegulatoryChange, 
    controls: AffectedControl[]
  ): string[] {
    const recommendations: string[] = [];

    if (controls.length > 0) {
      recommendations.push(`Review and update ${controls.length} affected controls`);
    }

    if (change.severity === 'critical' || change.severity === 'high') {
      recommendations.push('Prioritize remediation for high-impact changes');
    }

    if (change.effectiveDate) {
      const daysUntilEffective = Math.ceil(
        (change.effectiveDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
      );
      if (daysUntilEffective < 90) {
        recommendations.push(`Deadline approaching: ${daysUntilEffective} days remaining`);
      }
    }

    return recommendations;
  }

  /**
   * Analyze deadline implications
   */
  private analyzeDeadlineImplications(change: RegulatoryChange): string[] {
    const implications: string[] = [];

    if (change.effectiveDate) {
      const daysUntilEffective = Math.ceil(
        (change.effectiveDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
      );

      if (daysUntilEffective < 30) {
        implications.push('CRITICAL: Less than 30 days to compliance deadline');
      } else if (daysUntilEffective < 90) {
        implications.push('WARNING: Less than 90 days to compliance deadline');
      } else if (daysUntilEffective < 180) {
        implications.push('PLANNING: Less than 180 days to compliance deadline');
      }
    }

    return implications;
  }

  /**
   * Create compliance gaps
   */
  private createComplianceGaps(
    change: RegulatoryChange, 
    controls: AffectedControl[]
  ): void {
    for (const control of controls) {
      if (control.remediationRequired) {
        const gap: ComplianceGap = {
          id: `gap-${change.id}-${control.controlId}`,
          changeId: change.id,
          controlId: control.controlId,
          framework: control.framework,
          gapType: 'new_requirement',
          description: control.gapDescription,
          status: 'open'
        };
        this.gaps.set(gap.id, gap);
      }
    }
  }

  /**
   * Create timeline
   */
  private createTimeline(change: RegulatoryChange): void {
    const timeline: RegulatoryTimeline = {
      changeId: change.id,
      milestones: [
        {
          name: 'Detection',
          date: change.publishedDate,
          status: 'completed',
          description: 'Regulatory change detected'
        },
        {
          name: 'Analysis',
          date: new Date(),
          status: 'in_progress',
          description: 'Impact analysis in progress'
        },
        {
          name: 'Remediation',
          date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days from now
          status: 'pending',
          description: 'Implement required changes'
        },
        {
          name: 'Compliance',
          date: change.effectiveDate,
          status: 'pending',
          description: 'Full compliance achieved'
        }
      ],
      currentPhase: 'Analysis'
    };

    this.timelines.set(change.id, timeline);
  }
}
