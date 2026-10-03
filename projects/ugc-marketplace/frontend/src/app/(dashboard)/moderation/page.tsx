"use client";

import { useEffect, useState } from "react";
import { Search, Filter } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { ModerationQueue } from "@/components/moderation/ModerationQueue";
import { useDebounce } from "@/hooks/useDebounce";
import apiClient from "@/lib/api-client";
import type { ModerationItem } from "@/lib/types";

export default function ModerationPage() {
  const [items, setItems] = useState<ModerationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    const fetchItems = async () => {
      setIsLoading(true);
      try {
        const params: Record<string, string> = {};
        if (debouncedSearch) params.search = debouncedSearch;
        if (status) params.status = status;
        if (priority) params.priority = priority;
        const data = await apiClient.get<ModerationItem[]>("/moderation", params);
        setItems(data);
      } catch (error) {
        console.error("Failed to fetch moderation items:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchItems();
  }, [debouncedSearch, status, priority]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Moderation</h1>
        <p className="text-muted-foreground">Review and manage reported content and users</p>
      </div>
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search reports..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} options={[{ value: "", label: "All Status" }, { value: "pending", label: "Pending" }, { value: "approved", label: "Approved" }, { value: "rejected", label: "Rejected" }, { value: "escalated", label: "Escalated" }]} />
        <Select value={priority} onChange={(e) => setPriority(e.target.value)} options={[{ value: "", label: "All Priority" }, { value: "low", label: "Low" }, { value: "medium", label: "Medium" }, { value: "high", label: "High" }, { value: "critical", label: "Critical" }]} />
      </div>
      <ModerationQueue items={items} isLoading={isLoading} />
    </div>
  );
}
