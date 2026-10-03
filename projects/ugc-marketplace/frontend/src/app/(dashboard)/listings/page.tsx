"use client";

import { useEffect, useState } from "react";
import { Plus, Search } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { ListingTable } from "@/components/listings/ListingTable";
import { useDebounce } from "@/hooks/useDebounce";
import apiClient from "@/lib/api-client";
import type { Listing } from "@/lib/types";

export default function ListingsPage() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    const fetchListings = async () => {
      setIsLoading(true);
      try {
        const params: Record<string, string> = {};
        if (debouncedSearch) params.search = debouncedSearch;
        if (status) params.status = status;
        const data = await apiClient.get<Listing[]>("/listings", params);
        setListings(data);
      } catch (error) {
        console.error("Failed to fetch listings:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchListings();
  }, [debouncedSearch, status]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Listings</h1>
          <p className="text-muted-foreground">Manage marketplace listings</p>
        </div>
        <Button><Plus className="mr-2 h-4 w-4" />Create Listing</Button>
      </div>
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input name="search" placeholder="Search listings..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select name="status" value={status} onChange={(e) => setStatus(e.target.value)} options={[{ value: "", label: "All Status" }, { value: "active", label: "Active" }, { value: "draft", label: "Draft" }, { value: "paused", label: "Paused" }, { value: "sold", label: "Sold" }, { value: "expired", label: "Expired" }]} />
      </div>
      <ListingTable listings={listings} isLoading={isLoading} />
    </div>
  );
}
