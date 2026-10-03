"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  size?: "sm" | "md" | "lg" | "xl";
  fallback?: string;
}

const sizes = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-12 w-12 text-base",
  xl: "h-16 w-16 text-lg",
};

export function Avatar({
  src,
  alt = "",
  size = "md",
  fallback,
  className,
  ...props
}: AvatarProps) {
  const [error, setError] = React.useState(false);

  const initials = fallback || alt.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);

  if (!src || error) {
    return (
      <div
        className={cn(
          "inline-flex items-center justify-center rounded-full bg-primary-100 text-primary-700 font-medium dark:bg-primary-900/30 dark:text-primary-400",
          sizes[size],
          className
        )}
        {...props}
      >
        {initials}
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className={cn("rounded-full object-cover", sizes[size], className)}
      onError={() => setError(true)}
      {...props}
    />
  );
}
