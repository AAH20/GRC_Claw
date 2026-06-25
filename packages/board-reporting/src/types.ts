export type ReportType = "board_summary" | "risk_heatmap" | "compliance_trend" | "incident_summary" | "audit_summary" | "vendor_risk" | "executive_dashboard";
export type RiskLevel = "critical" | "high" | "medium" | "low" | "minimal";

export interface BoardReport {
  id: string;
  title: string;
  type: ReportType;
  generatedAt: string;
  period: string;
  sections: ReportSection[];
  summary: string;
  recommendations: string[];
  riskHeatmap: RiskHeatmap;
  complianceTrend: ComplianceTrend;
}

export interface ReportSection {
  title: string;
  content: string;
  metrics: Metric[];
  charts: ChartData[];
}

export interface Metric {
  label: string;
  value: string | number;
  trend?: "up" | "down" | "stable";
  benchmark?: string;
}

export interface ChartData {
  type: "bar" | "line" | "pie" | "heatmap" | "gauge";
  title: string;
  data: Record<string, unknown>;
}

export interface RiskHeatmap {
  title: string;
  data: RiskHeatmapCell[];
}

export interface RiskHeatmapCell {
  category: string;
  likelihood: number;
  impact: number;
  level: RiskLevel;
  count: number;
}

export interface ComplianceTrend {
  title: string;
  data: ComplianceTrendPoint[];
}

export interface ComplianceTrendPoint {
  date: string;
  score: number;
  controls: number;
  gaps: number;
}

export interface ExecutiveDashboard {
  overallRiskScore: number;
  complianceScore: number;
  openIncidents: number;
  criticalFindings: number;
  vendorRiskScore: number;
  upcomingAudits: number;
  policyExpirations: number;
}
