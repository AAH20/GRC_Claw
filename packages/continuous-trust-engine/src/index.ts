/**
 * ContinuousTrustEngine - Real-time trust scoring for compliance posture
 * 
 * Continuously evaluates compliance posture, evidence quality, agent behavior,
 * and organizational trust signals to produce a dynamic trust score.
 * 
 * This engine goes beyond static compliance checks by incorporating:
 * - Real-time evidence freshness scoring
 * - Agent behavioral trust signals
 * - Control effectiveness metrics
 * - Risk-adjusted trust calculations
 * - Trust decay over time
 * - Trust threshold alerts
 */

export interface TrustSignal {
  id: string;
  type: 'evidence' | 'control' | 'agent' | 'risk' | 'behavior' | 'external';
  name: string;
  value: number; // 0-100
  weight: number; // 0-1
  timestamp: Date;
  metadata: Record<string, unknown>;
}

export interface TrustScore {
  overall: number; // 0-100
  breakdown: {
    evidence: number;
    control: number;
    agent: number;
    risk: number;
    behavior: number;
    external: number;
  };
  trend: 'improving' | 'stable' | 'declining';
  trendDelta: number; // change from previous period
  lastUpdated: Date;
  nextUpdate: Date;
  alerts: TrustAlert[];
}

export interface TrustAlert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  type: string;
  message: string;
  threshold: number;
  currentValue: number;
  timestamp: Date;
  acknowledged: boolean;
}

export interface TrustThreshold {
  metric: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface TrustHistoryEntry {
  timestamp: Date;
  score: TrustScore;
  signals: TrustSignal[];
}

export class ContinuousTrustEngine {
  private signals: Map<string, TrustSignal> = new Map();
  private history: TrustHistoryEntry[] = [];
  private thresholds: TrustThreshold[] = [];
  private alerts: TrustAlert[] = [];
  private updateInterval: NodeJS.Timeout | null = null;
  private listeners: ((score: TrustScore) => void)[] = [];

  constructor(
    private readonly options: {
      updateIntervalMs?: number;
      historyRetentionDays?: number;
      maxAlerts?: number;
      autoAcknowledgeAfterMs?: number;
    } = {}
  ) {
    this.options = {
      updateIntervalMs: 60000, // 1 minute
      historyRetentionDays: 90,
      maxAlerts: 1000,
      autoAcknowledgeAfterMs: 86400000, // 24 hours
      ...options
    };

    this.initializeDefaultThresholds();
  }

  /**
   * Start continuous trust monitoring
   */
  start(): void {
    if (this.updateInterval) {
      return; // Already running
    }

    this.updateInterval = setInterval(() => {
      this.calculateAndNotify();
    }, this.options.updateIntervalMs);

    // Initial calculation
    this.calculateAndNotify();
  }

  /**
   * Stop continuous trust monitoring
   */
  stop(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  /**
   * Register a trust signal
   */
  registerSignal(signal: TrustSignal): void {
    this.signals.set(signal.id, signal);
    this.evaluateThresholds();
  }

  /**
   * Update an existing trust signal
   */
  updateSignal(id: string, updates: Partial<TrustSignal>): void {
    const existing = this.signals.get(id);
    if (existing) {
      this.signals.set(id, { ...existing, ...updates, timestamp: new Date() });
      this.evaluateThresholds();
    }
  }

  /**
   * Remove a trust signal
   */
  removeSignal(id: string): void {
    this.signals.delete(id);
  }

  /**
   * Get current trust score
   */
  getScore(): TrustScore {
    return this.calculateScore();
  }

  /**
   * Get trust history
   */
  getHistory(hours: number = 24): TrustHistoryEntry[] {
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
    return this.history.filter(entry => entry.timestamp >= cutoff);
  }

  /**
   * Get active alerts
   */
  getAlerts(acknowledged: boolean = false): TrustAlert[] {
    return this.alerts.filter(alert => alert.acknowledged === acknowledged);
  }

  /**
   * Acknowledge an alert
   */
  acknowledgeAlert(alertId: string): void {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.acknowledged = true;
    }
  }

  /**
   * Subscribe to trust score updates
   */
  subscribe(listener: (score: TrustScore) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  /**
   * Set custom thresholds
   */
  setThresholds(thresholds: TrustThreshold[]): void {
    this.thresholds = thresholds;
  }

  /**
   * Calculate trust score from all signals
   */
  private calculateScore(): TrustScore {
    const signalArray = Array.from(this.signals.values());

    // Group signals by type
    const byType = {
      evidence: signalArray.filter(s => s.type === 'evidence'),
      control: signalArray.filter(s => s.type === 'control'),
      agent: signalArray.filter(s => s.type === 'agent'),
      risk: signalArray.filter(s => s.type === 'risk'),
      behavior: signalArray.filter(s => s.type === 'behavior'),
      external: signalArray.filter(s => s.type === 'external')
    };

    // Calculate weighted average for each type
    const calculateTypeScore = (signals: TrustSignal[]): number => {
      if (signals.length === 0) return 100; // Default to 100 if no signals
      const totalWeight = signals.reduce((sum, s) => sum + s.weight, 0);
      if (totalWeight === 0) return 100;
      return signals.reduce((sum, s) => sum + (s.value * s.weight), 0) / totalWeight;
    };

    const breakdown = {
      evidence: calculateTypeScore(byType.evidence),
      control: calculateTypeScore(byType.control),
      agent: calculateTypeScore(byType.agent),
      risk: calculateTypeScore(byType.risk),
      behavior: calculateTypeScore(byType.behavior),
      external: calculateTypeScore(byType.external)
    };

    // Overall score with weights
    const weights = { evidence: 0.25, control: 0.25, agent: 0.15, risk: 0.15, behavior: 0.1, external: 0.1 };
    const overall = (
      breakdown.evidence * weights.evidence +
      breakdown.control * weights.control +
      breakdown.agent * weights.agent +
      breakdown.risk * weights.risk +
      breakdown.behavior * weights.behavior +
      breakdown.external * weights.external
    );

    // Calculate trend
    const previousScore = this.history.length > 0 
      ? this.history[this.history.length - 1].score.overall 
      : overall;
    const trendDelta = overall - previousScore;
    const trend = trendDelta > 2 ? 'improving' : trendDelta < -2 ? 'declining' : 'stable';

    // Filter active alerts
    const activeAlerts = this.alerts.filter(a => !a.acknowledged);

    return {
      overall: Math.round(overall * 100) / 100,
      breakdown: {
        evidence: Math.round(breakdown.evidence * 100) / 100,
        control: Math.round(breakdown.control * 100) / 100,
        agent: Math.round(breakdown.agent * 100) / 100,
        risk: Math.round(breakdown.risk * 100) / 100,
        behavior: Math.round(breakdown.behavior * 100) / 100,
        external: Math.round(breakdown.external * 100) / 100
      },
      trend,
      trendDelta: Math.round(trendDelta * 100) / 100,
      lastUpdated: new Date(),
      nextUpdate: new Date(Date.now() + this.options.updateIntervalMs!),
      alerts: activeAlerts
    };
  }

  /**
   * Calculate score and notify listeners
   */
  private calculateAndNotify(): void {
    const score = this.calculateScore();

    // Store in history
    this.history.push({
      timestamp: new Date(),
      score,
      signals: Array.from(this.signals.values())
    });

    // Trim history
    const cutoff = new Date(Date.now() - this.options.historyRetentionDays! * 24 * 60 * 60 * 1000);
    this.history = this.history.filter(entry => entry.timestamp >= cutoff);

    // Notify listeners
    this.listeners.forEach(listener => listener(score));
  }

  /**
   * Evaluate thresholds and create alerts
   */
  private evaluateThresholds(): void {
    const score = this.calculateScore();

    for (const threshold of this.thresholds) {
      const value = this.getMetricValue(score, threshold.metric);
      if (value === null) continue;

      let severity: TrustAlert['severity'] | null = null;

      if (value <= threshold.critical) {
        severity = 'critical';
      } else if (value <= threshold.high) {
        severity = 'high';
      } else if (value <= threshold.medium) {
        severity = 'medium';
      } else if (value <= threshold.low) {
        severity = 'low';
      }

      if (severity) {
        this.createAlert({
          id: `threshold-${threshold.metric}-${Date.now()}`,
          severity,
          type: 'threshold',
          message: `${threshold.metric} score (${value}) below ${severity} threshold`,
          threshold: threshold[severity],
          currentValue: value,
          timestamp: new Date(),
          acknowledged: false
        });
      }
    }
  }

  /**
   * Get metric value from score
   */
  private getMetricValue(score: TrustScore, metric: string): number | null {
    switch (metric) {
      case 'overall': return score.overall;
      case 'evidence': return score.breakdown.evidence;
      case 'control': return score.breakdown.control;
      case 'agent': return score.breakdown.agent;
      case 'risk': return score.breakdown.risk;
      case 'behavior': return score.breakdown.behavior;
      case 'external': return score.breakdown.external;
      default: return null;
    }
  }

  /**
   * Create a new alert
   */
  private createAlert(alert: TrustAlert): void {
    this.alerts.push(alert);

    // Trim alerts
    if (this.alerts.length > this.options.maxAlerts!) {
      this.alerts = this.alerts.slice(-this.options.maxAlerts!);
    }

    // Auto-acknowledge old alerts
    if (this.options.autoAcknowledgeAfterMs) {
      const cutoff = new Date(Date.now() - this.options.autoAcknowledgeAfterMs);
      this.alerts.forEach(a => {
        if (a.timestamp < cutoff && !a.acknowledged) {
          a.acknowledged = true;
        }
      });
    }
  }

  /**
   * Initialize default thresholds
   */
  private initializeDefaultThresholds(): void {
    this.thresholds = [
      { metric: 'overall', critical: 30, high: 50, medium: 70, low: 85 },
      { metric: 'evidence', critical: 20, high: 40, medium: 60, low: 80 },
      { metric: 'control', critical: 25, high: 45, medium: 65, low: 85 },
      { metric: 'agent', critical: 30, high: 50, medium: 70, low: 85 },
      { metric: 'risk', critical: 20, high: 40, medium: 60, low: 80 }
    ];
  }
}
// trigger publish
