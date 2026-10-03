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
    success: "border-green-200 bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-100",
    error: "border-red-200 bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-100",
    warning: "border-yellow-200 bg-yellow-50 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-100",
    info: "border-blue-200 bg-blue-50 text-blue-800 dark:bg-blue-900/20 dark:text-blue-100",
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] space-y-2">
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
