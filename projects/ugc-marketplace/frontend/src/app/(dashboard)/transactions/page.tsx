"use client";

import { useEffect, useState } from "react";
import { Search, Download } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { TransactionChart } from "@/components/transactions/TransactionChart";
import { TransactionList } from "@/components/transactions/TransactionList";
import { useDebounce } from "@/hooks/useDebounce";
import apiClient from "@/lib/api-client";
import type { Transaction } from "@/lib/types";

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    const fetchTransactions = async () => {
      setIsLoading(true);
      try {
        const params: Record<string, string> = {};
        if (debouncedSearch) params.search = debouncedSearch;
        if (type) params.type = type;
        if (status) params.status = status;
        const data = await apiClient.get<Transaction[]>("/transactions", params);
        setTransactions(data);
      } catch (error) {
        console.error("Failed to fetch transactions:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchTransactions();
  }, [debouncedSearch, type, status]);

  const chartData = [
    { month: "Jan", revenue: 12000 }, { month: "Feb", revenue: 15000 },
    { month: "Mar", revenue: 18000 }, { month: "Apr", revenue: 14000 },
    { month: "May", revenue: 22000 }, { month: "Jun", revenue: 19000 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Transactions</h1>
          <p className="text-muted-foreground">Track all financial activity</p>
        </div>
        <Button variant="outline"><Download className="mr-2 h-4 w-4" />Export</Button>
      </div>
      <TransactionChart data={chartData} />
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search transactions..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={type} onChange={(e) => setType(e.target.value)} options={[{ value: "", label: "All Types" }, { value: "sale", label: "Sales" }, { value: "purchase", label: "Purchases" }, { value: "refund", label: "Refunds" }, { value: "payout", label: "Payouts" }, { value: "fee", label: "Fees" }]} />
        <Select value={status} onChange={(e) => setStatus(e.target.value)} options={[{ value: "", label: "All Status" }, { value: "pending", label: "Pending" }, { value: "completed", label: "Completed" }, { value: "failed", label: "Failed" }, { value: "cancelled", label: "Cancelled" }]} />
      </div>
      <TransactionList transactions={transactions} isLoading={isLoading} />
    </div>
  );
}
