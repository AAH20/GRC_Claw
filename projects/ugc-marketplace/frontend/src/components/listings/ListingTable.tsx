"use client";

import { Eye, MousePointer, ShoppingCart, TrendingUp, MoreVertical } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { formatCurrency, formatNumber, formatDate } from "@/lib/utils";
import type { Listing } from "@/lib/types";

interface ListingTableProps {
  listings: Listing[];
  isLoading?: boolean;
  onView?: (id: string) => void;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function ListingTable({ listings, isLoading, onView, onEdit, onDelete }: ListingTableProps) {
  const statusColors = {
    draft: "secondary",
    active: "success",
    paused: "warning",
    sold: "default",
    expired: "destructive",
  } as const;

  if (isLoading) {
    return <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />)}</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Listings</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="pb-3 font-medium">Title</th>
                <th className="pb-3 font-medium">Creator</th>
                <th className="pb-3 font-medium">Price</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Performance</th>
                <th className="pb-3 font-medium">Revenue</th>
                <th className="pb-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {listings.map((listing) => (
                <tr key={listing.id} className="border-b last:border-0 hover:bg-accent/50">
                  <td className="py-3 pr-4">
                    <div>
                      <p className="font-medium">{listing.title}</p>
                      <p className="text-xs text-muted-foreground">{listing.category}</p>
                    </div>
                  </td>
                  <td className="py-3 pr-4">{listing.creator_name}</td>
                  <td className="py-3 pr-4 font-medium">{formatCurrency(listing.price, listing.currency)}</td>
                  <td className="py-3 pr-4"><Badge variant={statusColors[listing.status]}>{listing.status}</Badge></td>
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><Eye className="h-3 w-3" />{formatNumber(listing.impressions)}</span>
                      <span className="flex items-center gap-1"><MousePointer className="h-3 w-3" />{formatNumber(listing.clicks)}</span>
                      <span className="flex items-center gap-1"><ShoppingCart className="h-3 w-3" />{formatNumber(listing.conversions)}</span>
                    </div>
                  </td>
                  <td className="py-3 pr-4 font-medium">{formatCurrency(listing.revenue)}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon" onClick={() => onView?.(listing.id)}><Eye className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="icon" onClick={() => onEdit?.(listing.id)}><TrendingUp className="h-4 w-4" /></Button>
                      <Button variant="ghost" size="icon" onClick={() => onDelete?.(listing.id)}><MoreVertical className="h-4 w-4" /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
