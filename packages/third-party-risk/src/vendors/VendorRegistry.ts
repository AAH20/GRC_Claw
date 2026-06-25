import { randomUUID } from "node:crypto";
import type { Vendor, VendorRiskScore, VendorRiskTier, VendorMonitoring, VendorAlert, FrameworkCode, VendorAssessment, AssessmentQuestion } from "../types.js";

export class VendorRegistry {
  private vendors: Map<string, Vendor> = new Map();
  private monitoring: Map<string, VendorMonitoring> = new Map();

  registerVendor(input: {
    name: string;
    domain: string;
    categories: string[];
    frameworks: FrameworkCode[];
    contacts: { name: string; email: string; role: string; isPrimary: boolean }[];
  }): Vendor {
    const vendor: Vendor = {
      id: randomUUID(),
      name: input.name,
      domain: input.domain,
      status: "prospect",
      riskTier: "medium",
      overallScore: 50,
      categories: input.categories,
      frameworks: input.frameworks,
      contacts: input.contacts,
      contracts: [],
      assessments: [],
      documents: [],
      riskFactors: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.vendors.set(vendor.id, vendor);
    return vendor;
  }

  getVendor(id: string): Vendor | undefined { return this.vendors.get(id); }
  listVendors(): Vendor[] { return Array.from(this.vendors.values()); }
  getVendorsByTier(tier: VendorRiskTier): Vendor[] { return this.listVendors().filter((v) => v.riskTier === tier); }

  updateVendorStatus(id: string, status: Vendor["status"]): boolean {
    const vendor = this.vendors.get(id);
    if (!vendor) return false;
    vendor.status = status;
    vendor.updatedAt = new Date().toISOString();
    return true;
  }

  calculateRiskScore(vendorId: string): VendorRiskScore | null {
    const vendor = this.vendors.get(vendorId);
    if (!vendor) return null;

    const cybersecurityScore = this.calculateCybersecurityScore(vendor);
    const complianceScore = this.calculateComplianceScore(vendor);
    const operationalScore = 70;
    const financialScore = 75;
    const reputationalScore = 80;

    const overallScore = Math.round(
      cybersecurityScore * 0.3 + complianceScore * 0.25 + operationalScore * 0.2 + financialScore * 0.15 + reputationalScore * 0.1
    );

    const riskTier: VendorRiskTier = overallScore >= 80 ? "low" : overallScore >= 60 ? "medium" : overallScore >= 40 ? "high" : "critical";

    vendor.overallScore = overallScore;
    vendor.riskTier = riskTier;
    vendor.updatedAt = new Date().toISOString();

    return {
      vendorId,
      overallScore,
      cybersecurityScore,
      complianceScore,
      operationalScore,
      financialScore,
      reputationalScore,
      riskTier,
      calculatedAt: new Date().toISOString(),
    };
  }

  private calculateCybersecurityScore(vendor: Vendor): number {
    let score = 50;
    if (vendor.documents.some((d) => d.type === "soc2")) score += 20;
    if (vendor.documents.some((d) => d.type === "iso27001")) score += 15;
    if (vendor.documents.some((d) => d.type === "penetration_test")) score += 10;
    return Math.min(100, score);
  }

  private calculateComplianceScore(vendor: Vendor): number {
    const completedAssessments = vendor.assessments.filter((a) => a.status === "completed");
    if (completedAssessments.length === 0) return 30;
    const avgScore = completedAssessments.reduce((sum, a) => sum + a.score, 0) / completedAssessments.length;
    return Math.round(avgScore);
  }

  startMonitoring(vendorId: string): void {
    this.monitoring.set(vendorId, {
      vendorId,
      lastCheckedAt: new Date().toISOString(),
      alerts: [],
      continuousScore: 50,
      trend: "stable",
    });
  }

  getMonitoring(vendorId: string): VendorMonitoring | undefined { return this.monitoring.get(vendorId); }
}
