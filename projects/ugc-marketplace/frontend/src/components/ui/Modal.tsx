"use client";

import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./Button";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
}

export function Modal({ isOpen, onClose, title, children, size = "md" }: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
      const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
      document.addEventListener("keydown", handler);
      return () => { document.body.style.overflow = ""; document.removeEventListener("keydown", handler); };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;
  const sizes = { sm: "max-w-sm", md: "max-w-md", lg: "max-w-lg", xl: "max-w-xl" };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className={cn("relative z-50 w-full rounded-lg bg-card p-6 shadow-lg", sizes[size])}>
        <div className="flex items-center justify-between mb-4">
          {title && <h2 className="text-lg font-semibold">{title}</h2>}
          <Button variant="ghost" size="icon" onClick={onClose} className="ml-auto">
            <X className="h-4 w-4" />
          </Button>
        </div>
        {children}
      </div>
    </div>
  );
}
