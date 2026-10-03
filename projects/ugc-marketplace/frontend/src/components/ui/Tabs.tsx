"use client";

import { cn } from "@/lib/utils";

interface TabsProps {
  tabs: { id: string; label: string; count?: number; icon?: React.ComponentType<{ className?: string }> }[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className }: TabsProps) {
  return (
    <div role="tablist" className={cn("flex space-x-1 rounded-lg bg-muted p-1", className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          aria-controls={`panel-${tab.id}`}
          id={`tab-${tab.id}`}
          onClick={() => onChange(tab.id)}
          className={cn(
            "flex-1 rounded-md px-3 py-2 text-sm font-medium transition-all",
            activeTab === tab.id
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          {tab.icon && <tab.icon className="h-4 w-4" />}
          {tab.label}
          {tab.count !== undefined && (
            <span className="ml-2 rounded-full bg-primary/10 px-2 py-0.5 text-xs">{tab.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}
