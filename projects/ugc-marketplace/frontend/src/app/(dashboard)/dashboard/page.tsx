"use client";

import { useEffect, useState } from "react";
import { DollarSign, Users, FileText, ArrowLeftRight, TrendingUp, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { AnalyticsCard } from "@/components/analytics/AnalyticsCard";
import { TransactionList } from "@/components/transactions/TransactionList";
import { TopCreators } from "@/components/analytics/TopCreators";
import { PageSpinner } from "@/components/ui/Spinner";
import { useAuth } from "@/components/providers/AuthProvider";
import apiClient from "@/lib/api-client";
import type { AnalyticsData, Transaction } from "@/lib/types";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsData, txData] = await Promise.all([
          apiClient.get<AnalyticsData>("/analytics"),
          apiClient.get<Transaction[]>("/transactions?limit=5"),
        ]);
        setAnalytics(analyticsData);
        setTransactions(txData);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  if (isLoading) return <PageSpinner />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back, {user?.name}. Here&apos;s your overview.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <AnalyticsCard title="Total Revenue" value={`$${analytics?.total_revenue.toLocaleString() ?? 0}`} change={analytics?.revenue_growth ?? 0} icon={DollarSign} />
        <AnalyticsCard title="Active Creators" value={analytics?.active_creators.toString() ?? "0"} change={analytics?.creator_growth ?? 0} icon={Users} />
        <AnalyticsCard title="Total Content" value={analytics?.total_content.toString() ?? "0"} change={analytics?.content_growth ?? 0} icon={FileText} />
        <AnalyticsCard title="Transactions" value={analytics?.total_transactions.toString() ?? "0"} change={analytics?.transaction_growth ?? 0} icon={ArrowLeftRight} />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <TransactionList transactions={transactions} />
        <TopCreators creators={analytics?.top_creators ?? []} />
      </div>
    </div>
  );
}
