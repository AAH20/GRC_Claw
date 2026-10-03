"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "./Button";

interface Props { children: ReactNode; fallback?: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-lg font-semibold">Something went wrong</h2>
          <p className="mt-1 text-sm text-muted-foreground max-w-sm">
            {this.state.error?.message || "An unexpected error occurred"}
          </p>
          <Button className="mt-4" onClick={() => this.setState({ hasError: false, error: null })}>
            <RefreshCw className="mr-2 h-4 w-4" /> Try again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
