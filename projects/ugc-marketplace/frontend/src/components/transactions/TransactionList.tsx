"use client";

import { ArrowUpRight, ArrowDownLeft, RefreshCw, CreditCard, DollarSign } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import type { Transaction } from "@/lib/types";

interface TransactionListProps {
  transactions: Transaction[];
  isLoading?: boolean;
}

export function TransactionList({ transactions, isLoading }: TransactionListProps) {
  const statusColors = { pending: "warning", completed: "success", failed: "destructive", cancelled: "secondary" } as const;
  const typeIcons = { sale: ArrowUpRight, purchase: ArrowDownLeft, refund: RefreshCw, payout: DollarSign, fee: CreditCard };

  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Recent Transactions</CardTitle></CardHeader>
        <CardContent><div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 animate-pulse rounded-lg bg-muted" />)}</div></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader><CardTitle>Recent Transactions</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-3">
          {transactions.map((tx) => {
            const Icon = typeIcons[tx.type];
            const isIncoming = tx.type === "sale" || tx.type === "refund";
            return (
              <div key={tx.id} className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/50">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full ${isIncoming ? "bg-green-100 text-green-600 dark:bg-green-900/30" : "bg-red-100 text-red-600 dark:bg-red-900/30"}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{tx.description}</p>
                    <p className="text-xs text-muted-foreground">{tx.from_user} → {tx.to_user}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-semibold ${isIncoming ? "text-green-600" : "text-red-600"}`}>
                    {isIncoming ? "+" : "-"}{formatCurrency(tx.amount, tx.currency)}
                  </p>
                  <div className="flex items-center justify-end gap-2">
                    <Badge variant={statusColors[tx.status]}>{tx.status}</Badge>
                    <span className="text-xs text-muted-foreground">{formatDateTime(tx.created_at)}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
