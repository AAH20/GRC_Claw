"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "bordered" | "elevated";
  padding?: "none" | "sm" | "md" | "lg";
}

const variants = {
  default: "bg-white dark:bg-gray-800",
  bordered: "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
  elevated: "bg-white dark:bg-gray-800 shadow-lg",
};

const paddings = {
  none: "",
  sm: "p-3",
  md: "p-5",
  lg: "p-8",
};

export function Card({
  variant = "bordered",
  padding = "md",
  className,
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl transition-shadow duration-200",
        variants[variant],
        paddings[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center justify-between mb-4", className)}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-lg font-semibold text-gray-900 dark:text-gray-100", className)}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm text-gray-500 dark:text-gray-400", className)} {...props}>
      {children}
    </p>
  );
}

export function CardContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("", className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-700", className)}
      {...props}
    >
      {children}
    </div>
  );
}
