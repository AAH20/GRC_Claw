import { cn } from "@/lib/utils";

interface AvatarProps {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

export function Avatar({ src, alt = "", fallback, size = "md", className }: AvatarProps) {
  const sizes = { sm: "h-8 w-8 text-xs", md: "h-10 w-10 text-sm", lg: "h-12 w-12 text-base", xl: "h-16 w-16 text-lg" };
  const getFallback = () => {
    if (fallback) return fallback.charAt(0).toUpperCase();
    return alt ? alt.charAt(0).toUpperCase() : "?";
  };

  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={src} alt={alt} className={cn("rounded-full object-cover", sizes[size], className)} />
    );
  }
  return (
    <div className={cn("flex items-center justify-center rounded-full bg-primary/10 font-medium text-primary", sizes[size], className)}>
      {getFallback()}
    </div>
  );
}
