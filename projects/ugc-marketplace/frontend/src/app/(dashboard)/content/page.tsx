"use client";

import { useEffect, useState } from "react";
import { Search, Plus, Filter } from "lucide-react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Tabs } from "@/components/ui/Tabs";
import { ContentGrid } from "@/components/content/ContentGrid";
import { useDebounce } from "@/hooks/useDebounce";
import apiClient from "@/lib/api-client";
import type { Content } from "@/lib/types";

export default function ContentPage() {
  const [content, setContent] = useState<Content[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    const fetchContent = async () => {
      setIsLoading(true);
      try {
        const params: Record<string, string> = {};
        if (debouncedSearch) params.search = debouncedSearch;
        if (status) params.status = status;
        if (type) params.type = type;
        if (activeTab !== "all") params.status = activeTab;
        const data = await apiClient.get<Content[]>("/content", params);
        setContent(data);
      } catch (error) {
        console.error("Failed to fetch content:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchContent();
  }, [debouncedSearch, status, type, activeTab]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Content</h1>
          <p className="text-muted-foreground">Manage all user-generated content</p>
        </div>
        <Button><Plus className="mr-2 h-4 w-4" />Create Content</Button>
      </div>
      <Tabs tabs={[{ id: "all", label: "All" }, { id: "published", label: "Published" }, { id: "pending_review", label: "Pending" }, { id: "draft", label: "Drafts" }]} activeTab={activeTab} onChange={setActiveTab} />
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input name="search" placeholder="Search content..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select name="status" value={status} onChange={(e) => setStatus(e.target.value)} options={[{ value: "", label: "All Status" }, { value: "published", label: "Published" }, { value: "pending_review", label: "Pending" }, { value: "draft", label: "Draft" }, { value: "rejected", label: "Rejected" }]} />
        <Select name="type" value={type} onChange={(e) => setType(e.target.value)} options={[{ value: "", label: "All Types" }, { value: "video", label: "Video" }, { value: "image", label: "Image" }, { value: "story", label: "Story" }, { value: "reel", label: "Reel" }, { value: "blog", label: "Blog" }]} />
      </div>
      <ContentGrid content={content} isLoading={isLoading} />
    </div>
  );
}
