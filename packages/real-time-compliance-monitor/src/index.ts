// ============================================================================
// @grc-claw/real-time-compliance-monitor
// Real-time compliance monitoring with live dashboards, alerts, and notifications
// ============================================================================

import { EventEmitter } from "events";

// ---------------------------------------------------------------------------
// Types & Enums
// ---------------------------------------------------------------------------

export type ComplianceStatus = "compliant" | "non_compliant" | "partial" | "unknown";
export type AlertSeverity = "critical" | "high" | "medium" | "low" | "info";
export type NotificationChannel = "email" | "slack" | "teams" | "webhook";
export type SLAStatus = "met" | "at_risk" | "breached";

export interface ComplianceRule {
  id: string;
  name: string;
  framework: string;
  description: string;
  check: () => Promise<ComplianceCheckResult>;
}

export interface ComplianceCheckResult {
  ruleId: string;
  status: ComplianceStatus;
  details: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface ComplianceSnapshot {
  timestamp: number;
  overallStatus: ComplianceStatus;
  score: number;
  rules: ComplianceCheckResult[];
  framework: string;
}

export interface Alert {
  id: string;
  ruleId: string;
  severity: AlertSeverity;
  message: string;
  details: string;
  timestamp: number;
  acknowledged: boolean;
  metadata?: Record<string, unknown>;
}

export interface DashboardWidget {
  id: string;
  type: "score" | "trend" | "rule_table" | "alert_list" | "sla_status" | "custom";
  title: string;
  config: Record<string, unknown>;
  refreshIntervalMs: number;
}

export interface DashboardConfig {
  id: string;
  name: string;
  description: string;
  widgets: DashboardWidget[];
  refreshIntervalMs: number;
}

export interface NotificationConfig {
  channel: NotificationChannel;
  endpoint: string;
  enabled: boolean;
  severityFilter?: AlertSeverity[];
}

export interface SLATarget {
  ruleId: string;
  requiredStatus: ComplianceStatus;
  maxResponseTimeMs: number;
  escalationContacts: string[];
}

export interface SLABreach {
  ruleId: string;
  target: SLATarget;
  breachTime: number;
  durationMs: number;
}

export interface TrendDataPoint {
  timestamp: number;
  score: number;
  overallStatus: ComplianceStatus;
  ruleId?: string;
}

// ---------------------------------------------------------------------------
// ComplianceTrendAnalyzer
// ---------------------------------------------------------------------------

export class ComplianceTrendAnalyzer {
  private dataPoints: TrendDataPoint[] = [];
  private readonly maxPoints: number;

  constructor(maxPoints = 1000) {
    this.maxPoints = maxPoints;
  }

  record(dataPoint: TrendDataPoint): void {
    this.dataPoints.push(dataPoint);
    if (this.dataPoints.length > this.maxPoints) {
      this.dataPoints.shift();
    }
  }

  getTrend(windowMs?: number): TrendDataPoint[] {
    if (!windowMs) return [...this.dataPoints];
    const cutoff = Date.now() - windowMs;
    return this.dataPoints.filter((dp) => dp.timestamp >= cutoff);
  }

  calculateAverageScore(windowMs?: number): number {
    const points = this.getTrend(windowMs);
    if (points.length === 0) return 0;
    return points.reduce((sum, p) => sum + p.score, 0) / points.length;
  }

  getScoreDirection(windowMs?: number): "improving" | "declining" | "stable" {
    const points = this.getTrend(windowMs);
    if (points.length < 2) return "stable";
    const recent = points.slice(-Math.max(2, Math.floor(points.length / 3)));
    const older = points.slice(0, Math.floor(points.length / 3));
    const recentAvg = recent.reduce((s, p) => s + p.score, 0) / recent.length;
    const olderAvg = older.reduce((s, p) => s + p.score, 0) / older.length;
    const delta = recentAvg - olderAvg;
    if (delta > 2) return "improving";
    if (delta < -2) return "declining";
    return "stable";
  }
}

// ---------------------------------------------------------------------------
// AlertEngine
// ---------------------------------------------------------------------------

export class AlertEngine extends EventEmitter {
  private alerts: Alert[] = [];
  private readonly maxAlerts: number;

  constructor(maxAlerts = 500) {
    super();
    this.maxAlerts = maxAlerts;
  }

  evaluate(
    previous: ComplianceCheckResult | undefined,
    current: ComplianceCheckResult,
    framework: string
  ): Alert | null {
    const statusChanged = previous && previous.status !== current.status;
    const becameNonCompliant = current.status === "non_compliant";
    const becamePartial = current.status === "partial";

    if (!statusChanged && previous) return null;

    let severity: AlertSeverity = "info";
    if (becameNonCompliant) {
      severity = previous?.status === "compliant" ? "critical" : "high";
    } else if (becamePartial) {
      severity = "medium";
    } else if (current.status === "compliant" && previous?.status !== "compliant") {
      severity = "info";
    }

    const alert: Alert = {
      id: this.generateId(),
      ruleId: current.ruleId,
      severity,
      message: this.buildMessage(previous, current, framework),
      details: current.details,
      timestamp: Date.now(),
      acknowledged: false,
      metadata: current.metadata,
    };

    this.alerts.push(alert);
    if (this.alerts.length > this.maxAlerts) {
      this.alerts.shift();
    }

    this.emit("alert", alert);
    return alert;
  }

  private buildMessage(
    previous: ComplianceCheckResult | undefined,
    current: ComplianceCheckResult,
    framework: string
  ): string {
    if (!previous) {
      return `[${framework}] Rule ${current.ruleId} initial status: ${current.status}`;
    }
    return `[${framework}] Rule ${current.ruleId} changed from ${previous.status} to ${current.status}`;
  }

  getAlerts(filter?: { severity?: AlertSeverity; acknowledged?: boolean }): Alert[] {
    let result = this.alerts;
    if (filter?.severity) result = result.filter((a) => a.severity === filter.severity);
    if (filter?.acknowledged !== undefined)
      result = result.filter((a) => a.acknowledged === filter.acknowledged);
    return [...result];
  }

  acknowledge(alertId: string): boolean {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (!alert) return false;
    alert.acknowledged = true;
    this.emit("acknowledged", alert);
    return true;
  }

  private generateId(): string {
    return `alert_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  }
}

// ---------------------------------------------------------------------------
// NotificationRouter
// ---------------------------------------------------------------------------

export interface NotificationTransport {
  send(params: {
    channel: NotificationChannel;
    endpoint: string;
    subject: string;
    body: string;
    severity: AlertSeverity;
  }): Promise<void>;
}

export class NotificationRouter {
  private configs: NotificationConfig[] = [];
  private transport: NotificationTransport;

  constructor(transport: NotificationTransport) {
    this.transport = transport;
  }

  addConfig(config: NotificationConfig): void {
    this.configs.push(config);
  }

  removeConfig(channel: NotificationChannel): void {
    this.configs = this.configs.filter((c) => c.channel !== channel);
  }

  async route(alert: Alert): Promise<void> {
    const matchingConfigs = this.configs.filter(
      (c) =>
        c.enabled &&
        (!c.severityFilter || c.severityFilter.includes(alert.severity))
    );

    const results = await Promise.allSettled(
      matchingConfigs.map((config) =>
        this.transport.send({
          channel: config.channel,
          endpoint: config.endpoint,
          subject: `Compliance Alert [${alert.severity.toUpperCase()}]`,
          body: `${alert.message}\n\nDetails: ${alert.details}`,
          severity: alert.severity,
        })
      )
    );

    const failures = results.filter((r) => r.status === "rejected");
    if (failures.length > 0) {
      const errors = failures.map((r) => (r as PromiseRejectedResult).reason);
      throw new NotificationError(
        `Failed to send ${failures.length} notification(s)`,
        errors
      );
    }
  }
}

export class NotificationError extends Error {
  public readonly causes: unknown[];
  constructor(message: string, causes: unknown[]) {
    super(message);
    this.name = "NotificationError";
    this.causes = causes;
  }
}

// ---------------------------------------------------------------------------
// SLAMonitor
// ---------------------------------------------------------------------------

export class SLAMonitor extends EventEmitter {
  private targets: Map<string, SLATarget> = new Map();
  private breaches: SLABreach[] = [];
  private activeTimers: Map<string, ReturnType<typeof setTimeout>> = new Map();

  addTarget(target: SLATarget): void {
    this.targets.set(target.ruleId, target);
  }

  removeTarget(ruleId: string): void {
    this.targets.delete(ruleId);
    const timer = this.activeTimers.get(ruleId);
    if (timer) {
      clearTimeout(timer);
      this.activeTimers.delete(ruleId);
    }
  }

  startMonitoring(): void {
    for (const [ruleId, target] of this.targets) {
      this.startTimer(ruleId, target);
    }
  }

  stopMonitoring(): void {
    for (const [ruleId, timer] of this.activeTimers) {
      clearTimeout(timer);
    }
    this.activeTimers.clear();
  }

  private startTimer(ruleId: string, target: SLATarget): void {
    const existing = this.activeTimers.get(ruleId);
    if (existing) clearTimeout(existing);

    const timer = setTimeout(() => {
      const breach: SLABreach = {
        ruleId,
        target,
        breachTime: Date.now(),
        durationMs: target.maxResponseTimeMs,
      };
      this.breaches.push(breach);
      this.emit("breach", breach);
    }, target.maxResponseTimeMs);

    this.activeTimers.set(ruleId, timer);
  }

  recordComplianceResult(ruleId: string, result: ComplianceCheckResult): void {
    const target = this.targets.get(ruleId);
    if (!target) return;

    const timer = this.activeTimers.get(ruleId);
    if (!timer) return;

    if (result.status === target.requiredStatus) {
      clearTimeout(timer);
      this.activeTimers.delete(ruleId);
      this.emit("met", { ruleId, result });
      this.startTimer(ruleId, target);
    }
  }

  getStatus(): Map<string, SLAStatus> {
    const statusMap = new Map<string, SLAStatus>();
    for (const [ruleId, _target] of this.targets) {
      if (this.breaches.some((b) => b.ruleId === ruleId && !b.target)) {
        statusMap.set(ruleId, "breached");
      } else if (this.activeTimers.has(ruleId)) {
        statusMap.set(ruleId, "at_risk");
      } else {
        statusMap.set(ruleId, "met");
      }
    }
    return statusMap;
  }

  getBreaches(): SLABreach[] {
    return [...this.breaches];
  }
}

// ---------------------------------------------------------------------------
// ComplianceDashboard
// ---------------------------------------------------------------------------

export class ComplianceDashboard {
  private dashboards: Map<string, DashboardConfig> = new Map();
  private widgetData: Map<string, unknown> = new Map();

  createDashboard(config: DashboardConfig): void {
    this.dashboards.set(config.id, config);
  }

  removeDashboard(id: string): boolean {
    return this.dashboards.delete(id);
  }

  getDashboard(id: string): DashboardConfig | undefined {
    return this.dashboards.get(id);
  }

  listDashboards(): DashboardConfig[] {
    return Array.from(this.dashboards.values());
  }

  updateWidgetData(widgetId: string, data: unknown): void {
    this.widgetData.set(widgetId, data);
  }

  getWidgetData<T = unknown>(widgetId: string): T | undefined {
    return this.widgetData.get(widgetId) as T | undefined;
  }

  renderDashboard(
    id: string,
    snapshot: ComplianceSnapshot,
    alerts: Alert[],
    slaStatus: Map<string, SLAStatus>,
    trendAnalyzer: ComplianceTrendAnalyzer
  ): Record<string, unknown> | undefined {
    const config = this.dashboards.get(id);
    if (!config) return undefined;

    const result: Record<string, unknown> = {
      id: config.id,
      name: config.name,
      renderedAt: Date.now(),
      widgets: {} as Record<string, unknown>,
    };

    for (const widget of config.widgets) {
      switch (widget.type) {
        case "score":
          (result.widgets as Record<string, unknown>)[widget.id] = {
            title: widget.title,
            score: snapshot.score,
            status: snapshot.overallStatus,
          };
          break;

        case "trend":
          (result.widgets as Record<string, unknown>)[widget.id] = {
            title: widget.title,
            trend: trendAnalyzer.getTrend(widget.config["windowMs"] as number),
            direction: trendAnalyzer.getScoreDirection(
              widget.config["windowMs"] as number
            ),
            averageScore: trendAnalyzer.calculateAverageScore(
              widget.config["windowMs"] as number
            ),
          };
          break;

        case "rule_table":
          (result.widgets as Record<string, unknown>)[widget.id] = {
            title: widget.title,
            rules: snapshot.rules,
          };
          break;

        case "alert_list":
          (result.widgets as Record<string, unknown>)[widget.id] = {
            title: widget.title,
            alerts: alerts.slice(0, (widget.config["limit"] as number) ?? 20),
          };
          break;

        case "sla_status":
          (result.widgets as Record<string, unknown>)[widget.id] = {
            title: widget.title,
            status: Object.fromEntries(slaStatus),
          };
          break;

        case "custom":
          (result.widgets as Record<string, unknown>)[widget.id] = {
            title: widget.title,
            data: this.widgetData.get(widget.id),
          };
          break;
      }
    }

    return result;
  }
}

// ---------------------------------------------------------------------------
// RealTimeComplianceMonitor (main orchestrator)
// ---------------------------------------------------------------------------

export class RealTimeComplianceMonitor extends EventEmitter {
  private rules: Map<string, ComplianceRule> = new Map();
  private previousResults: Map<string, ComplianceCheckResult> = new Map();
  private framework: string;
  private pollTimer: ReturnType<typeof setInterval> | null = null;

  readonly alertEngine: AlertEngine;
  readonly notificationRouter: NotificationRouter;
  readonly slaMonitor: SLAMonitor;
  readonly dashboard: ComplianceDashboard;
  readonly trendAnalyzer: ComplianceTrendAnalyzer;

  private latestSnapshot: ComplianceSnapshot | null = null;

  constructor(options: {
    framework: string;
    notificationTransport?: NotificationTransport;
    maxAlerts?: number;
    maxTrendPoints?: number;
  }) {
    super();
    this.framework = options.framework;
    this.alertEngine = new AlertEngine(options.maxAlerts);
    this.notificationRouter = new NotificationRouter(
      options.notificationTransport ?? {
        async send(): Promise<void> {
          /* noop default transport */
        },
      }
    );
    this.slaMonitor = new SLAMonitor();
    this.dashboard = new ComplianceDashboard();
    this.trendAnalyzer = new ComplianceTrendAnalyzer(options.maxTrendPoints);

    this.alertEngine.on("alert", (alert: Alert) => {
      this.emit("alert", alert);
      this.notificationRouter.route(alert).catch((err) => {
        this.emit("notification_error", err);
      });
    });

    this.slaMonitor.on("breach", (breach: SLABreach) => {
      this.emit("sla_breach", breach);
    });
  }

  registerRule(rule: ComplianceRule): void {
    this.rules.set(rule.id, rule);
  }

  unregisterRule(ruleId: string): void {
    this.rules.delete(ruleId);
    this.previousResults.delete(ruleId);
  }

  async evaluateAll(): Promise<ComplianceSnapshot> {
    const results: ComplianceCheckResult[] = [];

    const checks = Array.from(this.rules.values()).map(async (rule) => {
      try {
        return await rule.check();
      } catch (err) {
        return {
          ruleId: rule.id,
          status: "unknown" as ComplianceStatus,
          details: err instanceof Error ? err.message : "Check failed",
          timestamp: Date.now(),
        } satisfies ComplianceCheckResult;
      }
    });

    const outcomes = await Promise.all(checks);
    for (const result of outcomes) {
      results.push(result);
      const previous = this.previousResults.get(result.ruleId);
      this.alertEngine.evaluate(previous, result, this.framework);
      this.previousResults.set(result.ruleId, result);
      this.slaMonitor.recordComplianceResult(result.ruleId, result);
    }

    const score = this.calculateScore(results);
    const overallStatus = this.determineOverallStatus(results);

    const snapshot: ComplianceSnapshot = {
      timestamp: Date.now(),
      overallStatus,
      score,
      rules: results,
      framework: this.framework,
    };

    this.latestSnapshot = snapshot;
    this.trendAnalyzer.record({
      timestamp: snapshot.timestamp,
      score: snapshot.score,
      overallStatus: snapshot.overallStatus,
    });

    this.emit("snapshot", snapshot);
    return snapshot;
  }

  getLatestSnapshot(): ComplianceSnapshot | null {
    return this.latestSnapshot;
  }

  startPolling(intervalMs: number): void {
    if (this.pollTimer) this.stopPolling();
    this.pollTimer = setInterval(() => {
      this.evaluateAll().catch((err) => {
        this.emit("error", err);
      });
    }, intervalMs);
    this.pollTimer.unref?.();
    this.emit("polling_started", { intervalMs });
  }

  stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
      this.emit("polling_stopped");
    }
    this.slaMonitor.stopMonitoring();
  }

  async destroy(): Promise<void> {
    this.stopPolling();
    this.alertEngine.removeAllListeners();
    this.removeAllListeners();
  }

  private calculateScore(results: ComplianceCheckResult[]): number {
    if (results.length === 0) return 0;
    const weights: Record<ComplianceStatus, number> = {
      compliant: 100,
      partial: 50,
      non_compliant: 0,
      unknown: 0,
    };
    const total = results.reduce((sum, r) => sum + weights[r.status], 0);
    return Math.round((total / results.length) * 100) / 100;
  }

  private determineOverallStatus(results: ComplianceCheckResult[]): ComplianceStatus {
    if (results.length === 0) return "unknown";
    if (results.every((r) => r.status === "compliant")) return "compliant";
    if (results.some((r) => r.status === "non_compliant")) return "non_compliant";
    if (results.some((r) => r.status === "partial")) return "partial";
    return "unknown";
  }
}
