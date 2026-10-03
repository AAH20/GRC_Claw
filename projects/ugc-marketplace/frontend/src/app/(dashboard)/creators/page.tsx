"use client";

import { useEffect, useState } from "react";
import { Search, Filter, UserPlus } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { CreatorGrid } from "@/components/creators/CreatorGrid";
import { useDebounce } from "@/hooks/useDebounce";
import apiClient from "@/lib/api-client";
import type { Creator } from "@/lib/types";

export default function CreatorsPage() {
  const [creators, setCreators] = useState<Creator[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    const fetchCreators = async () => {
      setIsLoading(true);
      try {
        const params: Record<string, string> = {};
        if (debouncedSearch) params.search = debouncedSearch;
        if (status) params.status = status;
        if (category) params.category = category;
        const data = await apiClient.get<Creator[]>("/creators", params);
        setCreators(data);
      } catch (error) {
        console.error("Failed to fetch creators:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCreators();
  }, [debouncedSearch, status, category]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Creators</h1>
          <p className="text-muted-foreground">Discover and manage content creators</p>
        </div>
        <Button><UserPlus className="mr-2 h-4 w-4" />Invite Creator</Button>
      </div>
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search creators..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} options={[{ value: "", label: "All Status" }, { value: "active", label: "Active" }, { value: "pending", label: "Pending" }, { value: "suspended", label: "Suspended" }]} />
        <Select value={category} onChange={(e) => setCategory(e.target.value)} options={[{ value: "", label: "All Categories" }, { value: "fashion", label: "Fashion" }, { value: "tech", label: "Tech" }, { value: "food", label: "Food" }, { value: "travel", label: "Travel" }]} />
      </div>
      <CreatorGrid creators={creators} isLoading={isLoading} />
    </div>
  );
}
