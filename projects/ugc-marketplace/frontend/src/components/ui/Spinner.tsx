import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-6 w-6 animate-spin", className)} />;
}

export function PageSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <Spinner className="h-8 w-8 text-primary" />
    </div>
  );
}
