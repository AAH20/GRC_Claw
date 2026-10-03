"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { CheckCircle, XCircle, AlertCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "error" | "warning" | "info";
interface Toast { id: string; type: ToastType; title: string; message?: string; }

interface ToastContextType { toast: (type: ToastType, title: string, message?: string) => void; }

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((type: ToastType, title: string, message?: string) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 5000);
  }, []);

  const icons = { success: CheckCircle, error: XCircle, warning: AlertCircle, info: Info };
  const colors = {
    success: "border-success/30 bg-success/10 text-success",
    error: "border-destructive/30 bg-destructive/10 text-destructive",
    warning: "border-warning/30 bg-warning/10 text-warning",
    info: "border-info/30 bg-info/10 text-info",
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] space-y-2" aria-live="polite" aria-atomic="false">
        {toasts.map((t) => {
          const Icon = icons[t.type];
          return (
            <div key={t.id} className={cn("flex items-start gap-3 rounded-lg border p-4 shadow-lg min-w-[300px] animate-in slide-in-from-right", colors[t.type])}>
              <Icon className="h-5 w-5 mt-0.5 shrink-0" />
              <div className="flex-1">
                <p className="font-medium text-sm">{t.title}</p>
                {t.message && <p className="text-xs mt-1 opacity-80">{t.message}</p>}
              </div>
              <button onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}>
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used within ToastProvider");
  return context;
}
