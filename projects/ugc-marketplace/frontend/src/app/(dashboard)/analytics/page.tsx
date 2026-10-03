"use client";

import { useEffect, useState } from "react";
import { DollarSign, Users, FileText, ArrowLeftRight, Download } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { AnalyticsCard } from "@/components/analytics/AnalyticsCard";
import { TransactionChart } from "@/components/transactions/TransactionChart";
import { TopCreators } from "@/components/analytics/TopCreators";
import { ContentPerformance } from "@/components/analytics/ContentPerformance";
import { PageSpinner } from "@/components/ui/Spinner";
import apiClient from "@/lib/api-client";
import type { AnalyticsData } from "@/lib/types";

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const data = await apiClient.get<AnalyticsData>("/analytics");
        setAnalytics(data);
      } catch (error) {
        console.error("Failed to fetch analytics:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (isLoading) return <PageSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">Deep insights into your marketplace performance</p>
        </div>
        <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export Report</Button>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <AnalyticsCard title="Total Revenue" value={`$${analytics?.total_revenue.toLocaleString() ?? 0}`} change={analytics?.revenue_growth ?? 0} icon={DollarSign} />
        <AnalyticsCard title="Active Creators" value={analytics?.active_creators.toString() ?? "0"} change={analytics?.creator_growth ?? 0} icon={Users} />
        <AnalyticsCard title="Total Content" value={analytics?.total_content.toString() ?? "0"} change={analytics?.content_growth ?? 0} icon={FileText} />
        <AnalyticsCard title="Transactions" value={analytics?.total_transactions.toString() ?? "0"} change={analytics?.transaction_growth ?? 0} icon={ArrowLeftRight} />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <TransactionChart data={analytics?.revenue_by_month ?? []} />
        <TopCreators creators={analytics?.top_creators ?? []} />
      </div>
      <ContentPerformance data={analytics?.content_performance ?? []} />
    </div>
  );
}
