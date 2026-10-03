"use client";

import { useState, useRef, useEffect, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface DropdownProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: "left" | "right";
}

export function Dropdown({ trigger, children, align = "right" }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <div onClick={() => setIsOpen(!isOpen)} aria-expanded={isOpen} aria-haspopup="menu">{trigger}</div>
      {isOpen && (
        <div role="menu" className={cn("absolute z-50 mt-1 min-w-[160px] rounded-md border bg-card p-1 shadow-lg", align === "right" ? "right-0" : "left-0")}>
          {children}
        </div>
      )}
    </div>
  );
}

export function DropdownItem({ children, onClick, variant }: { children: ReactNode; onClick?: () => void; variant?: "default" | "destructive" }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent",
        variant === "destructive" && "text-destructive"
      )}
    >
      {children}
    </button>
  );
}
