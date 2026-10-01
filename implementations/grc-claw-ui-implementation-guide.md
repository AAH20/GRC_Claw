# GRC_Claw UI Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Stack:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui  
**References:** grc-claw-ui-specification.md, grc-claw-api-spec.md

---

## Table of Contents

1. [Project Setup](#1-project-setup)
2. [Component Library (30+ Components)](#2-component-library)
3. [Executive Dashboard](#3-executive-dashboard)
4. [Operational Dashboard](#4-operational-dashboard)
5. [Technical Dashboard](#5-technical-dashboard)
6. [Policy Management Interface](#6-policy-management-interface)
7. [Evidence Viewer](#7-evidence-viewer)
8. [Alerting Interface](#8-alerting-interface)

---

## 1. Project Setup

### 1.1 Initialize Vite + React + TypeScript

```bash
npm create vite@latest grc-claw-ui -- --template react-ts
cd grc-claw-ui
npm install
```

### 1.2 Install Dependencies

```bash
# Core UI
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tabs
npm install @radix-ui/react-select @radix-ui/react-checkbox @radix-ui/react-switch
npm install @radix-ui/react-popover @radix-ui/react-tooltip @radix-ui/react-separator
npm install class-variance-authority clsx tailwind-merge lucide-react

# Data fetching & state
npm install @tanstack/react-query axios zustand

# Routing
npm install react-router-dom

# Charts
npm install recharts

# Code editor (for policy YAML)
npm install @monaco-editor/react

# Date handling
npm install date-fns

# Export
npm install jspdf jspdf-autotable
```

### 1.3 Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // GRC semantic colors
        success: "#22c55e",
        warning: "#f59e0b",
        danger: "#ef4444",
        info: "#3b82f6",
        neutral: "#6b7280",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};
export default config;
```

### 1.4 Project Structure

```
grc-claw-ui/
├── src/
│   ├── components/
│   │   ├── ui/                    # Base shadcn/ui primitives
│   │   ├── layout/                # App shell, sidebar, header
│   │   ├── dashboards/            # Dashboard-specific widgets
│   │   ├── policies/              # Policy management components
│   │   ├── evidence/              # Evidence viewer components
│   │   ├── assessments/           # Assessment workflow components
│   │   ├── compliance/            # Compliance mapping components
│   │   ├── alerts/                # Alert feed and config
│   │   └── agents/                # Agent registry components
│   ├── hooks/                     # Custom React hooks
│   ├── lib/                       # Utilities, API client, auth
│   ├── pages/                     # Route-level page components
│   ├── stores/                    # Zustand state stores
│   ├── types/                     # TypeScript type definitions
│   └── App.tsx
├── public/
├── index.html
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

### 1.5 API Client Setup

```typescript
// src/lib/api-client.ts
import axios from "axios";
import { useAuthStore } from "../stores/auth";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "https://api.grc-claw.io/v1.0",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor — attach JWT
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle errors uniformly
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 1.6 Authentication Store

```typescript
// src/stores/auth.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: string;
  name: string;
  email: string;
  role: "executive" | "grc_analyst" | "auditor" | "platform_engineer" | "ai_ml_engineer" | "policy_owner" | "approver" | "read_only";
  organizationId: string;
  permissions: string[];
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
      hasPermission: (permission) => {
        const { user } = get();
        return user?.permissions.includes(permission) ?? false;
      },
    }),
    { name: "grc-claw-auth" }
  )
);
```

### 1.7 Route Configuration

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "./stores/auth";
import AppShell from "./components/layout/AppShell";

// Pages
import ExecutiveDashboard from "./pages/dashboards/ExecutiveDashboard";
import OperationalDashboard from "./pages/dashboards/OperationalDashboard";
import TechnicalDashboard from "./pages/dashboards/TechnicalDashboard";
import PolicyList from "./pages/policies/PolicyList";
import PolicyEditor from "./pages/policies/PolicyEditor";
import PolicyTestConsole from "./pages/policies/PolicyTestConsole";
import EvidenceList from "./pages/evidence/EvidenceList";
import EvidenceDetail from "./pages/evidence/EvidenceDetail";
import AssessmentList from "./pages/assessments/AssessmentList";
import AssessmentDetail from "./pages/assessments/AssessmentDetail";
import FindingDetail from "./pages/assessments/FindingDetail";
import ComplianceMapping from "./pages/compliance/ComplianceMapping";
import AlertFeed from "./pages/alerts/AlertFeed";
import AlertConfig from "./pages/alerts/AlertConfig";
import AgentRegistry from "./pages/agents/AgentRegistry";
import Login from "./pages/Login";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 2, refetchOnWindowFocus: false },
  },
});

function ProtectedRoute({ children, requiredPermission }: { children: React.ReactNode; requiredPermission?: string }) {
  const { isAuthenticated, hasPermission } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (requiredPermission && !hasPermission(requiredPermission)) return <Navigate to="/unauthorized" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<AppShell />}>
            <Route path="/" element={<Navigate to="/dashboard/executive" replace />} />
            <Route path="/dashboard/executive" element={<ProtectedRoute><ExecutiveDashboard /></ProtectedRoute>} />
            <Route path="/dashboard/operational" element={<ProtectedRoute><OperationalDashboard /></ProtectedRoute>} />
            <Route path="/dashboard/technical" element={<ProtectedRoute><TechnicalDashboard /></ProtectedRoute>} />
            <Route path="/policies" element={<ProtectedRoute><PolicyList /></ProtectedRoute>} />
            <Route path="/policies/:policyId/edit" element={<ProtectedRoute requiredPermission="policies:write"><PolicyEditor /></ProtectedRoute>} />
            <Route path="/policies/:policyId/test" element={<ProtectedRoute requiredPermission="policies:write"><PolicyTestConsole /></ProtectedRoute>} />
            <Route path="/evidence" element={<ProtectedRoute><EvidenceList /></ProtectedRoute>} />
            <Route path="/evidence/:evidenceId" element={<ProtectedRoute><EvidenceDetail /></ProtectedRoute>} />
            <Route path="/assessments" element={<ProtectedRoute><AssessmentList /></ProtectedRoute>} />
            <Route path="/assessments/:assessmentId" element={<ProtectedRoute><AssessmentDetail /></ProtectedRoute>} />
            <Route path="/assessments/:assessmentId/findings/:findingId" element={<ProtectedRoute><FindingDetail /></ProtectedRoute>} />
            <Route path="/compliance" element={<ProtectedRoute><ComplianceMapping /></ProtectedRoute>} />
            <Route path="/alerts" element={<ProtectedRoute><AlertFeed /></ProtectedRoute>} />
            <Route path="/alerts/configure" element={<ProtectedRoute requiredPermission="alerts:configure"><AlertConfig /></ProtectedRoute>} />
            <Route path="/agents" element={<ProtectedRoute><AgentRegistry /></ProtectedRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

---

## 2. Component Library (30+ Components)

All components follow the shadcn/ui pattern: Radix primitives + Tailwind + CVA for variants.

### 2.1 StatusBadge

```tsx
// src/components/ui/StatusBadge.tsx
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const statusBadgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        success: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
        warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
        danger: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
        info: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
        neutral: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400",
      },
    },
    defaultVariants: { variant: "neutral" },
  }
);

interface StatusBadgeProps extends VariantProps<typeof statusBadgeVariants> {
  children: React.ReactNode;
  className?: string;
}

export function StatusBadge({ variant, children, className }: StatusBadgeProps) {
  return (
    <span className={cn(statusBadgeVariants({ variant }), className)}>
      {children}
    </span>
  );
}
```

### 2.2 SeverityIndicator

```tsx
// src/components/ui/SeverityIndicator.tsx
import { AlertCircle, AlertTriangle, Info, XCircle } from "lucide-react";
import { cn } from "../../lib/utils";

type Severity = "critical" | "high" | "medium" | "low" | "info";

const severityConfig: Record<Severity, { icon: React.ElementType; color: string; bg: string; label: string }> = {
  critical: { icon: XCircle, color: "text-red-600", bg: "bg-red-50 dark:bg-red-950/30", label: "Critical" },
  high: { icon: AlertTriangle, color: "text-orange-600", bg: "bg-orange-50 dark:bg-orange-950/30", label: "High" },
  medium: { icon: AlertCircle, color: "text-yellow-600", bg: "bg-yellow-50 dark:bg-yellow-950/30", label: "Medium" },
  low: { icon: Info, color: "text-blue-600", bg: "bg-blue-50 dark:bg-blue-950/30", label: "Low" },
  info: { icon: Info, color: "text-gray-600", bg: "bg-gray-50 dark:bg-gray-800", label: "Info" },
};

interface SeverityIndicatorProps {
  severity: Severity;
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function SeverityIndicator({ severity, showLabel = true, size = "md", className }: SeverityIndicatorProps) {
  const config = severityConfig[severity];
  const Icon = config.icon;
  const iconSize = size === "sm" ? 14 : size === "lg" ? 20 : 16;

  return (
    <span className={cn("inline-flex items-center gap-1.5", config.color, className)}>
      <Icon size={iconSize} aria-label={config.label} />
      {showLabel && <span className={cn("font-medium", size === "sm" ? "text-xs" : "text-sm")}>{config.label}</span>}
    </span>
  );
}
```

### 2.3 VerificationLevel

```tsx
// src/components/ui/VerificationLevel.tsx
import { CheckCircle, AlertTriangle, XCircle, Clock, Shield } from "lucide-react";
import { cn } from "../../lib/utils";

type VerificationLevel = "L0" | "L1" | "L2" | "L3" | "L4";

const levelConfig: Record<VerificationLevel, { icon: React.ElementType; color: string; label: string; description: string }> = {
  L0: { icon: XCircle, color: "text-red-500", label: "L0", description: "Unverified" },
  L1: { icon: AlertTriangle, color: "text-yellow-500", label: "L1", description: "Schema-valid" },
  L2: { icon: CheckCircle, color: "text-blue-500", label: "L2", description: "Integrity-verified" },
  L3: { icon: Shield, color: "text-indigo-500", label: "L3", description: "Cross-validated" },
  L4: { icon: CheckCircle, color: "text-green-500", label: "L4", description: "Attested" },
};

interface VerificationLevelProps {
  level: VerificationLevel;
  showDescription?: boolean;
  size?: "sm" | "md";
  className?: string;
}

export function VerificationLevel({ level, showDescription = false, size = "md", className }: VerificationLevelProps) {
  const config = levelConfig[level];
  const Icon = config.icon;

  return (
    <span className={cn("inline-flex items-center gap-1.5", className)} title={config.description}>
      <Icon size={size === "sm" ? 14 : 16} className={config.color} aria-label={`${config.label}: ${config.description}`} />
      <span className={cn("font-mono font-medium", config.color, size === "sm" ? "text-xs" : "text-sm")}>{config.label}</span>
      {showDescription && <span className="text-xs text-gray-500">({config.description})</span>}
    </span>
  );
}
```

### 2.4 TrustScoreGauge

```tsx
// src/components/ui/TrustScoreGauge.tsx
import { cn } from "../../lib/utils";

interface TrustScoreGaugeProps {
  score: number; // 0-100
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

function getGrade(score: number): { grade: string; color: string; bgColor: string } {
  if (score >= 90) return { grade: "A", color: "text-green-600", bgColor: "bg-green-500" };
  if (score >= 80) return { grade: "B", color: "text-blue-600", bgColor: "bg-blue-500" };
  if (score >= 70) return { grade: "C", color: "text-yellow-600", bgColor: "bg-yellow-500" };
  if (score >= 60) return { grade: "D", color: "text-orange-600", bgColor: "bg-orange-500" };
  return { grade: "F", color: "text-red-600", bgColor: "bg-red-500" };
}

export function TrustScoreGauge({ score, size = "md", showLabel = true, className }: TrustScoreGaugeProps) {
  const { grade, color, bgColor } = getGrade(score);
  const dimensions = size === "sm" ? "w-12 h-12" : size === "lg" ? "w-24 h-24" : "w-16 h-16";
  const strokeWidth = size === "sm" ? 3 : size === "lg" ? 5 : 4;
  const radius = size === "lg" ? 40 : size === "sm" ? 20 : 28;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className={cn("relative inline-flex items-center justify-center", dimensions, className)}>
      <svg className="transform -rotate-90" viewBox={`0 0 ${radius * 2 + strokeWidth * 2} ${radius * 2 + strokeWidth * 2}`}>
        <circle
          cx={radius + strokeWidth}
          cy={radius + strokeWidth}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-200 dark:text-gray-700"
        />
        <circle
          cx={radius + strokeWidth}
          cy={radius + strokeWidth}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={cn("transition-all duration-500", bgColor)}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("font-bold", color, size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-lg")}>
          {score}
        </span>
        {showLabel && (
          <span className={cn("font-medium", color, size === "lg" ? "text-sm" : "text-xs")}>{grade}</span>
        )}
      </div>
    </div>
  );
}
```

### 2.5 ComplianceScoreBar

```tsx
// src/components/ui/ComplianceScoreBar.tsx
import { cn } from "../../lib/utils";

interface ComplianceScoreBarProps {
  score: number; // 0-100
  label?: string;
  showPercentage?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function ComplianceScoreBar({ score, label, showPercentage = true, size = "md", className }: ComplianceScoreBarProps) {
  const barColor = score >= 80 ? "bg-green-500" : score >= 60 ? "bg-yellow-500" : score >= 40 ? "bg-orange-500" : "bg-red-500";
  const height = size === "sm" ? "h-1.5" : size === "lg" ? "h-4" : "h-2.5";

  return (
    <div className={cn("w-full", className)}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>}
          {showPercentage && <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{score}%</span>}
        </div>
      )}
      <div className={cn("w-full rounded-full bg-gray-200 dark:bg-gray-700", height)}>
        <div
          className={cn("rounded-full transition-all duration-500", barColor, height)}
          style={{ width: `${score}%` }}
          role="progressbar"
          aria-valuenow={score}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}
```

### 2.6 EvidenceTimeline

```tsx
// src/components/ui/EvidenceTimeline.tsx
import { CheckCircle, Clock, Shield, Upload, FileSearch } from "lucide-react";
import { cn } from "../../lib/utils";

interface CustodyEvent {
  action: string;
  actor: string;
  timestamp: string;
  hash?: string;
  signature?: string;
}

interface EvidenceTimelineProps {
  events: CustodyEvent[];
  className?: string;
}

const actionIcons: Record<string, React.ElementType> = {
  collected: Upload,
  verified: FileSearch,
  attested: CheckCircle,
  reviewed: Clock,
  default: Shield,
};

export function EvidenceTimeline({ events, className }: EvidenceTimelineProps) {
  return (
    <div className={cn("relative pl-6", className)}>
      <div className="absolute left-2 top-0 bottom-0 w-px bg-gray-200 dark:bg-gray-700" />
      {events.map((event, index) => {
        const Icon = actionIcons[event.action] || actionIcons.default;
        return (
          <div key={index} className="relative flex items-start gap-3 pb-4 last:pb-0">
            <div className="absolute -left-[17px] flex h-8 w-8 items-center justify-center rounded-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
              <Icon size={14} className="text-gray-600 dark:text-gray-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium capitalize text-gray-900 dark:text-gray-100">{event.action}</span>
                <span className="text-xs text-gray-500">{event.actor}</span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">{new Date(event.timestamp).toLocaleString()}</p>
              {event.hash && (
                <p className="text-xs font-mono text-gray-400 mt-0.5 truncate">Hash: {event.hash}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

### 2.7 ControlMatrix

```tsx
// src/components/ui/ControlMatrix.tsx
import { CheckCircle, XCircle, AlertTriangle, Clock } from "lucide-react";
import { cn } from "../../lib/utils";

type ControlStatus = "pass" | "fail" | "gap" | "pending";

interface ControlItem {
  id: string;
  controlId: string;
  title: string;
  status: ControlStatus;
  evidenceCount: number;
  lastAssessed?: string;
}

interface ControlMatrixProps {
  controls: ControlItem[];
  onControlClick?: (control: ControlItem) => void;
  className?: string;
}

const statusConfig: Record<ControlStatus, { icon: React.ElementType; color: string; label: string }> = {
  pass: { icon: CheckCircle, color: "text-green-500", label: "Pass" },
  fail: { icon: XCircle, color: "text-red-500", label: "Fail" },
  gap: { icon: AlertTriangle, color: "text-yellow-500", label: "Gap" },
  pending: { icon: Clock, color: "text-gray-400", label: "Pending" },
};

export function ControlMatrix({ controls, onControlClick, className }: ControlMatrixProps) {
  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Control ID</th>
            <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Title</th>
            <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Status</th>
            <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Evidence</th>
            <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Last Assessed</th>
          </tr>
        </thead>
        <tbody>
          {controls.map((control) => {
            const config = statusConfig[control.status];
            const Icon = config.icon;
            return (
              <tr
                key={control.id}
                className={cn(
                  "border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors",
                  onControlClick && "cursor-pointer"
                )}
                onClick={() => onControlClick?.(control)}
              >
                <td className="py-2 px-3 font-mono text-xs">{control.controlId}</td>
                <td className="py-2 px-3">{control.title}</td>
                <td className="py-2 px-3">
                  <span className={cn("inline-flex items-center gap-1", config.color)}>
                    <Icon size={14} />
                    {config.label}
                  </span>
                </td>
                <td className="py-2 px-3">{control.evidenceCount} items</td>
                <td className="py-2 px-3 text-gray-500 text-xs">
                  {control.lastAssessed ? new Date(control.lastAssessed).toLocaleDateString() : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
```

### 2.8 AgentCard

```tsx
// src/components/ui/AgentCard.tsx
import { Bot, Shield, AlertTriangle } from "lucide-react";
import { TrustScoreGauge } from "./TrustScoreGauge";
import { StatusBadge } from "./StatusBadge";
import { cn } from "../../lib/utils";

interface AgentCardProps {
  agent: {
    id: string;
    name: string;
    trustScore: number;
    status: "active" | "quarantined" | "pending" | "ungoverned";
    policyVersion: string;
    lastEvaluation: string;
  };
  onClick?: () => void;
  className?: string;
}

const statusVariant = {
  active: "success",
  pending: "warning",
  quarantined: "danger",
  ungoverned: "neutral",
} as const;

export function AgentCard({ agent, onClick, className }: AgentCardProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-4 p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:shadow-md transition-shadow",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      <div className="flex-shrink-0">
        <TrustScoreGauge score={agent.trustScore} size="sm" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <Bot size={16} className="text-gray-500" />
          <span className="font-medium text-gray-900 dark:text-gray-100 truncate">{agent.name}</span>
          <StatusBadge variant={statusVariant[agent.status]}>{agent.status}</StatusBadge>
        </div>
        <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
          <span className="flex items-center gap-1"><Shield size={12} /> Policy {agent.policyVersion}</span>
          <span>Eval: {new Date(agent.lastEvaluation).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
```

### 2.9 FilterBar

```tsx
// src/components/ui/FilterBar.tsx
import { Search, SlidersHorizontal } from "lucide-react";

interface FilterOption {
  value: string;
  label: string;
}

interface FilterBarProps {
  searchValue: string;
  onSearchChange: (value: string) => void;
  filters: {
    key: string;
    label: string;
    value: string;
    options: FilterOption[];
    onChange: (value: string) => void;
  }[];
  className?: string;
}

export function FilterBar({ searchValue, onSearchChange, filters, className }: FilterBarProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-3", className)}>
      <div className="relative flex-1 min-w-[200px]">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search..."
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-9 pr-3 py-2 text-sm rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      {filters.map((filter) => (
        <div key={filter.key} className="flex items-center gap-2">
          <label className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">{filter.label}:</label>
          <select
            value={filter.value}
            onChange={(e) => filter.onChange(e.target.value)}
            className="text-sm rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {filter.options.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}
```

### 2.10 DataTable

```tsx
// src/components/ui/DataTable.tsx
import { ChevronUp, ChevronDown, ChevronsLeft, ChevronsRight, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";

interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  sortable?: boolean;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
    onPageSizeChange?: (size: number) => void;
  };
  sortable?: boolean;
  onRowClick?: (item: T) => void;
  className?: string;
}

export function DataTable<T>({ columns, data, keyExtractor, pagination, onRowClick, className }: DataTableProps<T>) {
  return (
    <div className={cn("w-full", className)}>
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              {columns.map((col) => (
                <th key={col.key} className={cn("text-left py-3 px-4 font-medium text-gray-600 dark:text-gray-400", col.className)}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr
                key={keyExtractor(item)}
                className={cn(
                  "border-t border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors",
                  onRowClick && "cursor-pointer"
                )}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((col) => (
                  <td key={col.key} className={cn("py-3 px-4", col.className)}>
                    {col.render(item)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pagination && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-gray-500">
            Showing {(pagination.page - 1) * pagination.pageSize + 1}–{Math.min(pagination.page * pagination.pageSize, pagination.total)} of {pagination.total}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => pagination.onPageChange(1)}
              disabled={pagination.page === 1}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
            >
              <ChevronsLeft size={16} />
            </button>
            <button
              onClick={() => pagination.onPageChange(pagination.page - 1)}
              disabled={pagination.page === 1}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-sm">Page {pagination.page}</span>
            <button
              onClick={() => pagination.onPageChange(pagination.page + 1)}
              disabled={pagination.page * pagination.pageSize >= pagination.total}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
            >
              <ChevronRight size={16} />
            </button>
            <button
              onClick={() => pagination.onPageChange(Math.ceil(pagination.total / pagination.pageSize))}
              disabled={pagination.page * pagination.pageSize >= pagination.total}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
            >
              <ChevronsRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

### 2.11 ChartWidget

```tsx
// src/components/ui/ChartWidget.tsx
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

type ChartType = "line" | "bar" | "pie";

interface ChartWidgetProps {
  type: ChartType;
  data: Record<string, any>[];
  xKey?: string;
  yKey?: string;
  series?: { key: string; color: string; name: string }[];
  title?: string;
  height?: number;
  className?: string;
}

const COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316", "#ec4899"];

export function ChartWidget({ type, data, xKey = "name", yKey = "value", series, title, height = 300, className }: ChartWidgetProps) {
  return (
    <div className={className}>
      {title && <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        {type === "line" && (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {(series || [{ key: yKey, color: COLORS[0], name: yKey }]).map((s) => (
              <Line key={s.key} type="monotone" dataKey={s.key} stroke={s.color} name={s.name} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        )}
        {type === "bar" && (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {(series || [{ key: yKey, color: COLORS[0], name: yKey }]).map((s) => (
              <Bar key={s.key} dataKey={s.key} fill={s.color} name={s.name} radius={[4, 4, 0, 0]} />
            ))}
          </BarChart>
        )}
        {type === "pie" && (
          <PieChart>
            <Pie data={data} dataKey={yKey} nameKey={xKey} cx="50%" cy="50%" outerRadius={100} label>
              {data.map((_, index) => (
                <Cell key={index} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
```

### 2.12 AlertToast

```tsx
// src/components/ui/AlertToast.tsx
import { AlertTriangle, CheckCircle, XCircle, Info, X } from "lucide-react";
import { cn } from "../../lib/utils";

type ToastVariant = "success" | "error" | "warning" | "info";

interface AlertToastProps {
  variant: ToastVariant;
  title: string;
  message?: string;
  onDismiss?: () => void;
  action?: { label: string; onClick: () => void };
  className?: string;
}

const toastConfig: Record<ToastVariant, { icon: React.ElementType; bg: string; border: string }> = {
  success: { icon: CheckCircle, bg: "bg-green-50 dark:bg-green-950/30", border: "border-green-200 dark:border-green-800" },
  error: { icon: XCircle, bg: "bg-red-50 dark:bg-red-950/30", border: "border-red-200 dark:border-red-800" },
  warning: { icon: AlertTriangle, bg: "bg-yellow-50 dark:bg-yellow-950/30", border: "border-yellow-200 dark:border-yellow-800" },
  info: { icon: Info, bg: "bg-blue-50 dark:bg-blue-950/30", border: "border-blue-200 dark:border-blue-800" },
};

export function AlertToast({ variant, title, message, onDismiss, action, className }: AlertToastProps) {
  const config = toastConfig[variant];
  const Icon = config.icon;

  return (
    <div className={cn("flex items-start gap-3 p-4 rounded-lg border shadow-lg", config.bg, config.border, className)} role="alert">
      <Icon size={20} className="flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</p>
        {message && <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{message}</p>}
        {action && (
          <button onClick={action.onClick} className="text-sm font-medium text-blue-600 hover:text-blue-700 mt-2">
            {action.label}
          </button>
        )}
      </div>
      {onDismiss && (
        <button onClick={onDismiss} className="flex-shrink-0 text-gray-400 hover:text-gray-600">
          <X size={16} />
        </button>
      )}
    </div>
  );
}
```

### 2.13 ModalDialog

```tsx
// src/components/ui/ModalDialog.tsx
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

interface ModalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

const sizeClasses = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
};

export function ModalDialog({ open, onOpenChange, title, description, children, footer, size = "md", className }: ModalDialogProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content className={cn("fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full bg-white dark:bg-gray-900 rounded-lg shadow-xl p-6 max-h-[90vh] overflow-y-auto", sizeClasses[size], className)}>
          <div className="flex items-start justify-between mb-4">
            <div>
              <Dialog.Title className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</Dialog.Title>
              {description && <Dialog.Description className="text-sm text-gray-500 mt-1">{description}</Dialog.Description>}
            </div>
            <Dialog.Close className="text-gray-400 hover:text-gray-600">
              <X size={20} />
            </Dialog.Close>
          </div>
          {children}
          {footer && <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">{footer}</div>}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

### 2.14 DrawerPanel

```tsx
// src/components/ui/DrawerPanel.tsx
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

interface DrawerPanelProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  side?: "right" | "left";
  width?: string;
  className?: string;
}

export function DrawerPanel({ open, onClose, title, children, footer, side = "right", width = "w-full max-w-lg", className }: DrawerPanelProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div
        className={cn(
          "absolute top-0 bottom-0 bg-white dark:bg-gray-900 shadow-xl flex flex-col",
          side === "right" ? "right-0" : "left-0",
          width,
          className
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">{children}</div>
        {footer && <div className="p-4 border-t border-gray-200 dark:border-gray-700">{footer}</div>}
      </div>
    </div>
  );
}
```

### 2.15 TabBar

```tsx
// src/components/ui/TabBar.tsx
import * as Tabs from "@radix-ui/react-tabs";
import { cn } from "../../lib/utils";

interface Tab {
  value: string;
  label: string;
  icon?: React.ElementType;
  count?: number;
}

interface TabBarProps {
  tabs: Tab[];
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
}

export function TabBar({ tabs, value, onValueChange, className }: TabBarProps) {
  return (
    <Tabs.Root value={value} onValueChange={onValueChange} className={className}>
      <Tabs.List className="flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <Tabs.Trigger
              key={tab.value}
              value={tab.value}
              className={cn(
                "flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors",
                value === tab.value
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              )}
            >
              {Icon && <Icon size={16} />}
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                  {tab.count}
                </span>
              )}
            </Tabs.Trigger>
          );
        })}
      </Tabs.List>
    </Tabs.Root>
  );
}
```

### 2.16 Breadcrumb

```tsx
// src/components/ui/Breadcrumb.tsx
import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "../../lib/utils";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center gap-1 text-sm", className)}>
      {items.map((item, index) => (
        <span key={index} className="flex items-center gap-1">
          {index > 0 && <ChevronRight size={14} className="text-gray-400" />}
          {item.href ? (
            <Link to={item.href} className="text-blue-600 hover:text-blue-700 dark:text-blue-400">
              {item.label}
            </Link>
          ) : (
            <span className="text-gray-900 dark:text-gray-100 font-medium">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
```

### 2.17 EmptyState

```tsx
// src/components/ui/EmptyState.tsx
import { Inbox } from "lucide-react";
import { cn } from "../../lib/utils";

interface EmptyStateProps {
  icon?: React.ElementType;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  className?: string;
}

export function EmptyState({ icon: Icon = Inbox, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-12 px-4 text-center", className)}>
      <Icon size={48} className="text-gray-300 dark:text-gray-600 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">{title}</h3>
      {description && <p className="text-sm text-gray-500 mt-1 max-w-sm">{description}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
```

### 2.18 SkeletonLoader

```tsx
// src/components/ui/SkeletonLoader.tsx
import { cn } from "../../lib/utils";

interface SkeletonLoaderProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
}

export function SkeletonLoader({ className, variant = "text", width, height }: SkeletonLoaderProps) {
  return (
    <div
      className={cn(
        "animate-pulse bg-gray-200 dark:bg-gray-700",
        variant === "text" && "h-4 rounded",
        variant === "circular" && "rounded-full",
        variant === "rectangular" && "rounded-md",
        className
      )}
      style={{ width, height }}
    />
  );
}

export function SkeletonTable({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: columns }).map((_, j) => (
            <SkeletonLoader key={j} className="flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}
```

### 2.19 PolicyEditor (Monaco-based)

```tsx
// src/components/ui/PolicyEditor.tsx
import Editor from "@monaco-editor/react";
import { Play, Save, FileText } from "lucide-react";

interface PolicyEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSave?: () => void;
  onValidate?: () => void;
  onTest?: () => void;
  height?: string;
  readOnly?: boolean;
  className?: string;
}

export function PolicyEditor({ value, onChange, onSave, onValidate, onTest, height = "400px", readOnly = false, className }: PolicyEditorProps) {
  return (
    <div className={className}>
      <div className="flex items-center gap-2 mb-2">
        {onSave && (
          <button onClick={onSave} className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
            <Save size={14} /> Save
          </button>
        )}
        {onValidate && (
          <button onClick={onValidate} className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300">
            <FileText size={14} /> Validate
          </button>
        )}
        {onTest && (
          <button onClick={onTest} className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300">
            <Play size={14} /> Test
          </button>
        )}
      </div>
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <Editor
          height={height}
          defaultLanguage="yaml"
          value={value}
          onChange={(v) => onChange(v || "")}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            readOnly,
            automaticLayout: true,
          }}
          theme="vs-dark"
        />
      </div>
    </div>
  );
}
```

### 2.20 ProgressBar

```tsx
// src/components/ui/ProgressBar.tsx
import { cn } from "../../lib/utils";

interface ProgressBarProps {
  value: number; // 0-100
  label?: string;
  showPercentage?: boolean;
  size?: "sm" | "md" | "lg";
  color?: "auto" | "blue" | "green" | "yellow" | "red";
  className?: string;
}

export function ProgressBar({ value, label, showPercentage = true, size = "md", color = "auto", className }: ProgressBarProps) {
  const barColor =
    color === "auto"
      ? value >= 80 ? "bg-green-500" : value >= 60 ? "bg-yellow-500" : value >= 40 ? "bg-orange-500" : "bg-red-500"
      : color === "blue" ? "bg-blue-500" : color === "green" ? "bg-green-500" : color === "yellow" ? "bg-yellow-500" : "bg-red-500";
  const height = size === "sm" ? "h-1.5" : size === "lg" ? "h-4" : "h-2.5";

  return (
    <div className={cn("w-full", className)}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>}
          {showPercentage && <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{value}%</span>}
        </div>
      )}
      <div className={cn("w-full rounded-full bg-gray-200 dark:bg-gray-700", height)}>
        <div className={cn("rounded-full transition-all duration-300", barColor, height)} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
```

### 2.21 StatCard

```tsx
// src/components/ui/StatCard.tsx
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "../../lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ElementType;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export function StatCard({ title, value, change, changeLabel, icon: Icon, trend, className }: StatCardProps) {
  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor = trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-gray-400";

  return (
    <div className={cn("p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900", className)}>
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500 dark:text-gray-400">{title}</span>
        {Icon && <Icon size={18} className="text-gray-400" />}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</span>
        {change !== undefined && (
          <span className={cn("flex items-center gap-0.5 text-sm font-medium", trendColor)}>
            <TrendIcon size={14} />
            {change > 0 ? "+" : ""}{change}
            {changeLabel && <span className="text-gray-500 font-normal ml-1">{changeLabel}</span>}
          </span>
        )}
      </div>
    </div>
  );
}
```

### 2.22 Accordion

```tsx
// src/components/ui/Accordion.tsx
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import { cn } from "../../lib/utils";

interface AccordionItem {
  value: string;
  title: string;
  content: React.ReactNode;
  badge?: React.ReactNode;
}

interface AccordionProps {
  items: AccordionItem[];
  type?: "single" | "multiple";
  className?: string;
}

export function Accordion({ items, type = "single", className }: AccordionProps) {
  return (
    <AccordionPrimitive.Root type={type} className={cn("divide-y divide-gray-200 dark:divide-gray-700", className)}>
      {items.map((item) => (
        <AccordionPrimitive.Item key={item.value} value={item.value}>
          <AccordionPrimitive.Header>
            <AccordionPrimitive.Trigger className="flex items-center justify-between w-full py-3 text-left text-sm font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 transition-colors group">
              <span className="flex items-center gap-2">
                {item.title}
                {item.badge}
              </span>
              <ChevronDown size={16} className="text-gray-400 transition-transform group-data-[state=open]:rotate-180" />
            </AccordionPrimitive.Trigger>
          </AccordionPrimitive.Header>
          <AccordionPrimitive.Content className="pb-3 text-sm text-gray-600 dark:text-gray-400 overflow-hidden data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down">
            {item.content}
          </AccordionPrimitive.Content>
        </AccordionPrimitive.Item>
      ))}
    </AccordionPrimitive.Root>
  );
}
```

### 2.23 Avatar

```tsx
// src/components/ui/Avatar.tsx
import { cn } from "../../lib/utils";

interface AvatarProps {
  name: string;
  src?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = { sm: "w-6 h-6 text-xs", md: "w-8 h-8 text-sm", lg: "w-12 h-12 text-base" };

export function Avatar({ name, src, size = "md", className }: AvatarProps) {
  const initials = name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);

  if (src) {
    return <img src={src} alt={name} className={cn("rounded-full object-cover", sizeClasses[size], className)} />;
  }

  return (
    <div className={cn("rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 flex items-center justify-center font-medium", sizeClasses[size], className)}>
      {initials}
    </div>
  );
}
```

### 2.24 Tooltip

```tsx
// src/components/ui/Tooltip.tsx
import * as TooltipPrimitive from "@radix-ui/react-tooltip";

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  side?: "top" | "right" | "bottom" | "left";
}

export function Tooltip({ content, children, side = "top" }: TooltipProps) {
  return (
    <TooltipPrimitive.Provider>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side={side}
            className="z-50 px-2.5 py-1.5 text-xs font-medium text-white bg-gray-900 dark:bg-gray-700 rounded-md shadow-lg"
          >
            {content}
            <TooltipPrimitive.Arrow className="fill-gray-900 dark:fill-gray-700" />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}
```

### 2.25 DropdownMenu

```tsx
// src/components/ui/DropdownMenu.tsx
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { Check, ChevronRight, Circle } from "lucide-react";
import { cn } from "../../lib/utils";

export const DropdownMenu = DropdownMenuPrimitive.Root;
export const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;
export const DropdownMenuGroup = DropdownMenuPrimitive.Group;
export const DropdownMenuPortal = DropdownMenuPrimitive.Portal;

export function DropdownMenuContent({ children, className, ...props }: React.ComponentProps<typeof DropdownMenuPrimitive.Content>) {
  return (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.Content
        className={cn(
          "z-50 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-1 shadow-md",
          className
        )}
        {...props}
      >
        {children}
      </DropdownMenuPrimitive.Content>
    </DropdownMenuPrimitive.Portal>
  );
}

export function DropdownMenuItem({ children, className, ...props }: React.ComponentProps<typeof DropdownMenuPrimitive.Item>) {
  return (
    <DropdownMenuPrimitive.Item
      className={cn(
        "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-gray-100 dark:focus:bg-gray-800 data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </DropdownMenuPrimitive.Item>
  );
}

export function DropdownMenuCheckboxItem({ children, checked, ...props }: React.ComponentProps<typeof DropdownMenuPrimitive.CheckboxItem>) {
  return (
    <DropdownMenuPrimitive.CheckboxItem
      checked={checked}
      className="relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-gray-100 dark:focus:bg-gray-800"
      {...props}
    >
      <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
        <DropdownMenuPrimitive.ItemIndicator>
          <Check size={14} />
        </DropdownMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </DropdownMenuPrimitive.CheckboxItem>
  );
}

export function DropdownMenuLabel({ children, className, ...props }: React.ComponentProps<typeof DropdownMenuPrimitive.Label>) {
  return <DropdownMenuPrimitive.Label className={cn("px-2 py-1.5 text-sm font-semibold", className)} {...props}>{children}</DropdownMenuPrimitive.Label>;
}

export function DropdownMenuSeparator({ className, ...props }: React.ComponentProps<typeof DropdownMenuPrimitive.Separator>) {
  return <DropdownMenuPrimitive.Separator className={cn("-mx-1 my-1 h-px bg-gray-200 dark:bg-gray-700", className)} {...props} />;
}
```

### 2.26 Card

```tsx
// src/components/ui/Card.tsx
import { cn } from "../../lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      className={cn("rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm", onClick && "cursor-pointer hover:shadow-md transition-shadow", className)}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={cn("text-lg font-semibold leading-none tracking-tight text-gray-900 dark:text-gray-100", className)}>{children}</h3>;
}

export function CardDescription({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={cn("text-sm text-gray-500 dark:text-gray-400", className)}>{children}</p>;
}

export function CardContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("p-6 pt-0", className)}>{children}</div>;
}

export function CardFooter({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("flex items-center p-6 pt-0", className)}>{children}</div>;
}
```

### 2.27 Button

```tsx
// src/components/ui/Button.tsx
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-blue-600 text-white hover:bg-blue-700",
        destructive: "bg-red-600 text-white hover:bg-red-700",
        outline: "border border-gray-200 dark:border-gray-700 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800",
        secondary: "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 hover:bg-gray-200 dark:hover:bg-gray-700",
        ghost: "hover:bg-gray-100 dark:hover:bg-gray-800",
        link: "text-blue-600 underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

export function Button({ className, variant, size, loading, children, disabled, ...props }: ButtonProps) {
  return (
    <button className={cn(buttonVariants({ variant, size }), className)} disabled={disabled || loading} {...props}>
      {loading && <Loader2 size={16} className="mr-2 animate-spin" />}
      {children}
    </button>
  );
}
```

### 2.28 Input

```tsx
// src/components/ui/Input.tsx
import { cn } from "../../lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export function Input({ className, error, ...props }: InputProps) {
  return (
    <div className="w-full">
      <input
        className={cn(
          "flex h-10 w-full rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50",
          error && "border-red-500 focus:ring-red-500",
          className
        )}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}
```

### 2.29 Badge

```tsx
// src/components/ui/Badge.tsx
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
        secondary: "border-transparent bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400",
        destructive: "border-transparent bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
        outline: "text-gray-700 dark:text-gray-300",
        success: "border-transparent bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
        warning: "border-transparent bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
```

### 2.30 Separator

```tsx
// src/components/ui/Separator.tsx
import { cn } from "../../lib/utils";

interface SeparatorProps {
  orientation?: "horizontal" | "vertical";
  className?: string;
}

export function Separator({ orientation = "horizontal", className }: SeparatorProps) {
  return (
    <div
      role="separator"
      className={cn(
        "shrink-0 bg-gray-200 dark:bg-gray-700",
        orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
        className
      )}
    />
  );
}
```

### 2.31 Switch

```tsx
// src/components/ui/Switch.tsx
import * as SwitchPrimitives from "@radix-ui/react-switch";
import { cn } from "../../lib/utils";

interface SwitchProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export function Switch({ checked, onCheckedChange, disabled, className }: SwitchProps) {
  return (
    <SwitchPrimitives.Root
      checked={checked}
      onCheckedChange={onCheckedChange}
      disabled={disabled}
      className={cn(
        "peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-blue-600 data-[state=unchecked]:bg-gray-200 dark:data-[state=unchecked]:bg-gray-700",
        className
      )}
    >
      <SwitchPrimitives.Thumb
        className={cn(
          "pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0"
        )}
      />
    </SwitchPrimitives.Root>
  );
}
```

### 2.32 Kbd (Keyboard Shortcut)

```tsx
// src/components/ui/Kbd.tsx
import { cn } from "../../lib/utils";

interface KbdProps {
  children: React.ReactNode;
  className?: string;
}

export function Kbd({ children, className }: KbdProps) {
  return (
    <kbd className={cn(
      "pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-1.5 font-mono text-xs font-medium text-gray-500 dark:text-gray-400",
      className
    )}>
      {children}
    </kbd>
  );
}
```

### 2.33 ScrollArea

```tsx
// src/components/ui/ScrollArea.tsx
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";
import { cn } from "../../lib/utils";

interface ScrollAreaProps {
  children: React.ReactNode;
  className?: string;
}

export function ScrollArea({ children, className }: ScrollAreaProps) {
  return (
    <ScrollAreaPrimitive.Root className={cn("relative overflow-hidden", className)}>
      <ScrollAreaPrimitive.Viewport className="h-full w-full rounded-[inherit]">{children}</ScrollAreaPrimitive.Viewport>
      <ScrollAreaPrimitive.Scrollbar orientation="vertical" className="flex touch-none select-none transition-colors hover:bg-gray-200 dark:hover:bg-gray-700">
        <ScrollAreaPrimitive.Thumb className="relative flex-1 rounded-full bg-gray-300 dark:bg-gray-600" />
      </ScrollAreaPrimitive.Scrollbar>
      <ScrollAreaPrimitive.Scrollbar orientation="horizontal" className="flex touch-none select-none transition-colors hover:bg-gray-200 dark:hover:bg-gray-700">
        <ScrollAreaPrimitive.Thumb className="relative flex-1 rounded-full bg-gray-300 dark:bg-gray-600" />
      </ScrollAreaPrimitive.Scrollbar>
      <ScrollAreaPrimitive.Corner className="bg-gray-100 dark:bg-gray-800" />
    </ScrollAreaPrimitive.Root>
  );
}
```

### 2.34 Popover

```tsx
// src/components/ui/Popover.tsx
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { cn } from "../../lib/utils";

export const Popover = PopoverPrimitive.Root;
export const PopoverTrigger = PopoverPrimitive.Trigger;

export function PopoverContent({ children, className, ...props }: React.ComponentProps<typeof PopoverPrimitive.Content>) {
  return (
    <PopoverPrimitive.Portal>
      <PopoverPrimitive.Content
        className={cn(
          "z-50 w-72 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 shadow-md outline-none",
          className
        )}
        {...props}
      >
        {children}
      </PopoverPrimitive.Content>
    </PopoverPrimitive.Portal>
  );
}
```

### 2.35 HoverCard

```tsx
// src/components/ui/HoverCard.tsx
import * as HoverCardPrimitive from "@radix-ui/react-hover-card";
import { cn } from "../../lib/utils";

export const HoverCard = HoverCardPrimitive.Root;
export const HoverCardTrigger = HoverCardPrimitive.Trigger;

export function HoverCardContent({ children, className, ...props }: React.ComponentProps<typeof HoverCardPrimitive.Content>) {
  return (
    <HoverCardPrimitive.Portal>
      <HoverCardPrimitive.Content
        className={cn(
          "z-50 w-64 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 shadow-md outline-none",
          className
        )}
        {...props}
      >
        {children}
      </HoverCardPrimitive.Content>
    </HoverCardPrimitive.Portal>
  );
}
```

### 2.36 ContextMenu

```tsx
// src/components/ui/ContextMenu.tsx
import * as ContextMenuPrimitive from "@radix-ui/react-context-menu";
import { Check, ChevronRight, Circle } from "lucide-react";
import { cn } from "../../lib/utils";

export const ContextMenu = ContextMenuPrimitive.Root;
export const ContextMenuTrigger = ContextMenuPrimitive.Trigger;
export const ContextMenuGroup = ContextMenuPrimitive.Group;
export const ContextMenuPortal = ContextMenuPrimitive.Portal;
export const ContextMenuSub = ContextMenuPrimitive.Sub;
export const ContextMenuRadioGroup = ContextMenuPrimitive.RadioGroup;

export function ContextMenuContent({ children, className, ...props }: React.ComponentProps<typeof ContextMenuPrimitive.Content>) {
  return (
    <ContextMenuPrimitive.Portal>
      <ContextMenuPrimitive.Content
        className={cn(
          "z-50 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-1 shadow-md",
          className
        )}
        {...props}
      >
        {children}
      </ContextMenuPrimitive.Content>
    </ContextMenuPrimitive.Portal>
  );
}

export function ContextMenuItem({ children, className, ...props }: React.ComponentProps<typeof ContextMenuPrimitive.Item>) {
  return (
    <ContextMenuPrimitive.Item
      className={cn(
        "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-gray-100 dark:focus:bg-gray-800 data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </ContextMenuPrimitive.Item>
  );
}

export function ContextMenuCheckboxItem({ children, checked, ...props }: React.ComponentProps<typeof ContextMenuPrimitive.CheckboxItem>) {
  return (
    <ContextMenuPrimitive.CheckboxItem
      checked={checked}
      className="relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-gray-100 dark:focus:bg-gray-800"
      {...props}
    >
      <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
        <ContextMenuPrimitive.ItemIndicator><Check size={14} /></ContextMenuPrimitive.ItemIndicator>
      </span>
      {children}
    </ContextMenuPrimitive.CheckboxItem>
  );
}

export function ContextMenuLabel({ children, className, ...props }: React.ComponentProps<typeof ContextMenuPrimitive.Label>) {
  return <ContextMenuPrimitive.Label className={cn("px-2 py-1.5 text-sm font-semibold", className)} {...props}>{children}</ContextMenuPrimitive.Label>;
}

export function ContextMenuSeparator({ className, ...props }: React.ComponentProps<typeof ContextMenuPrimitive.Separator>) {
  return <ContextMenuPrimitive.Separator className={cn("-mx-1 my-1 h-px bg-gray-200 dark:bg-gray-700", className)} {...props} />;
}
```

### 2.37 Toggle

```tsx
// src/components/ui/Toggle.tsx
import * as TogglePrimitive from "@radix-ui/react-toggle";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const toggleVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-gray-100 dark:hover:bg-gray-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-gray-200 dark:data-[state=on]:bg-gray-700",
  {
    variants: {
      variant: {
        default: "bg-transparent",
        outline: "border border-gray-200 dark:border-gray-700 bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800",
      },
      size: {
        default: "h-10 px-3",
        sm: "h-8 px-2",
        lg: "h-12 px-4",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

interface ToggleProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof toggleVariants> {}

export function Toggle({ className, variant, size, ...props }: ToggleProps) {
  return <TogglePrimitive.Root className={cn(toggleVariants({ variant, size }), className)} {...props} />;
}
```

### 2.38 ToggleGroup

```tsx
// src/components/ui/ToggleGroup.tsx
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const toggleGroupVariants = cva("inline-flex items-center justify-center rounded-md text-sm font-medium", {
  variants: {
    variant: {
      default: "bg-transparent",
      outline: "border border-gray-200 dark:border-gray-700 bg-transparent",
    },
    size: {
      default: "h-10 px-3",
      sm: "h-8 px-2",
      lg: "h-12 px-4",
    },
  },
  defaultVariants: { variant: "default", size: "default" },
});

interface ToggleGroupProps extends React.ComponentProps<typeof ToggleGroupPrimitive.Root>, VariantProps<typeof toggleGroupVariants> {}

export function ToggleGroup({ className, variant, size, ...props }: ToggleGroupProps) {
  return <ToggleGroupPrimitive.Root className={cn(toggleGroupVariants({ variant, size }), className)} {...props} />;
}

export function ToggleGroupItem({ className, variant, size, ...props }: React.ComponentProps<typeof ToggleGroupPrimitive.Item> & VariantProps<typeof toggleGroupVariants>) {
  return <ToggleGroupPrimitive.Item className={cn(toggleGroupVariants({ variant, size }), className)} {...props} />;
}
```

### 2.39 AspectRatio

```tsx
// src/components/ui/AspectRatio.tsx
import * as AspectRatioPrimitive from "@radix-ui/react-aspect-ratio";

interface AspectRatioProps {
  ratio: number;
  children: React.ReactNode;
  className?: string;
}

export function AspectRatio({ ratio, children, className }: AspectRatioProps) {
  return (
    <AspectRatioPrimitive.Root ratio={ratio} className={className}>
      {children}
    </AspectRatioPrimitive.Root>
  );
}
```

### 2.40 Collapsible

```tsx
// src/components/ui/Collapsible.tsx
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";

export const Collapsible = CollapsiblePrimitive.Root;
export const CollapsibleTrigger = CollapsiblePrimitive.CollapsibleTrigger;
export const CollapsibleContent = CollapsiblePrimitive.CollapsibleContent;
```

---

## 3. Executive Dashboard

### 3.1 Page Component

```tsx
// src/pages/dashboards/ExecutiveDashboard.tsx
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card";
import { StatCard } from "../../components/ui/StatCard";
import { ComplianceScoreBar } from "../../components/ui/ComplianceScoreBar";
import { ChartWidget } from "../../components/ui/ChartWidget";
import { TrustScoreGauge } from "../../components/ui/TrustScoreGauge";
import { SeverityIndicator } from "../../components/ui/SeverityIndicator";
import { SkeletonTable } from "../../components/ui/SkeletonLoader";
import apiClient from "../../lib/api-client";
import { Shield, AlertTriangle, FileCheck, Bot } from "lucide-react";

interface ExecutiveData {
  complianceScore: number;
  complianceChange: number;
  riskPosture: { level: string; trend: string };
  auditReadiness: number;
  agentCoverage: { governed: number; total: number };
  frameworkScores: { name: string; score: number }[];
  riskTrend: { date: string; high: number; medium: number; low: number }[];
  topFindings: { id: string; severity: string; title: string; control: string }[];
  auditMilestones: { name: string; daysUntil: number; readiness: number }[];
  trustDistribution: { grade: string; count: number }[];
}

async function fetchExecutiveData(): Promise<ExecutiveData> {
  const { data } = await apiClient.get("/v1.0/compliance/posture");
  return data;
}

export default function ExecutiveDashboard() {
  const { data, isLoading } = useQuery({ queryKey: ["executive-dashboard"], queryFn: fetchExecutiveData });

  if (isLoading) {
    return <div className="p-6"><SkeletonTable rows={8} columns={4} /></div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Executive Dashboard</h1>
        <div className="flex items-center gap-3">
          <select className="text-sm rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2">
            <option>Last 30 days</option>
            <option>Last 90 days</option>
            <option>Last 12 months</option>
          </select>
          <button className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
            Export PDF
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Compliance Score"
          value={`${data?.complianceScore ?? 0}/100`}
          change={data?.complianceChange ?? 0}
          changeLabel="pts"
          icon={Shield}
          trend={data && data.complianceChange > 0 ? "up" : "down"}
        />
        <StatCard
          title="Risk Posture"
          value={data?.riskPosture?.level ?? "Unknown"}
          icon={AlertTriangle}
          trend={data?.riskPosture?.trend === "improving" ? "up" : "down"}
        />
        <StatCard
          title="Audit Readiness"
          value={`${data?.auditReadiness ?? 0}%`}
          icon={FileCheck}
        />
        <StatCard
          title="Agent Coverage"
          value={`${data?.agentCoverage?.governed ?? 0}/${data?.agentCoverage?.total ?? 0}`}
          icon={Bot}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Compliance Score by Framework</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(data?.frameworkScores || []).map((fw) => (
                <ComplianceScoreBar key={fw.name} score={fw.score} label={fw.name} />
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Trend (90 days)</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartWidget
              type="line"
              data={data?.riskTrend || []}
              xKey="date"
              series={[
                { key: "high", color: "#ef4444", name: "High" },
                { key: "medium", color: "#f59e0b", name: "Medium" },
                { key: "low", color: "#22c55e", name: "Low" },
              ]}
              height={250}
            />
          </CardContent>
        </Card>
      </div>

      {/* Findings & Milestones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top 5 Open Findings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(data?.topFindings || []).map((finding, i) => (
                <div key={finding.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <span className="text-sm font-medium text-gray-400 w-6">{i + 1}.</span>
                  <SeverityIndicator severity={finding.severity as any} size="sm" />
                  <span className="text-sm text-gray-700 dark:text-gray-300 flex-1">{finding.title}</span>
                  <span className="text-xs text-gray-500">{finding.control}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Upcoming Audit Milestones</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(data?.auditMilestones || []).map((milestone) => (
                <div key={milestone.name} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{milestone.name}</p>
                    <p className="text-xs text-gray-500">{milestone.daysUntil} days remaining</p>
                  </div>
                  <span className={`text-sm font-semibold ${milestone.readiness >= 80 ? "text-green-600" : milestone.readiness >= 60 ? "text-yellow-600" : "text-red-600"}`}>
                    {milestone.readiness}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trust Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Trust Score Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {(data?.trustDistribution || []).map((item) => (
              <div key={item.grade} className="flex flex-col items-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <TrustScoreGauge score={item.grade === "A" ? 95 : item.grade === "B" ? 85 : item.grade === "C" ? 75 : item.grade === "D" ? 65 : 45} size="sm" showLabel={false} />
                <span className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">Grade {item.grade}</span>
                <span className="text-xs text-gray-500">{item.count} agents</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## 5. Technical Dashboard

### 5.1 Page Component

```tsx
// src/pages/dashboards/TechnicalDashboard.tsx
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card";
import { AgentCard } from "../../components/ui/AgentCard";
import { ControlMatrix } from "../../components/ui/ControlMatrix";
import { TrustScoreGauge } from "../../components/ui/TrustScoreGauge";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Button } from "../../components/ui/Button";
import { SkeletonTable } from "../../components/ui/SkeletonLoader";
import apiClient from "../../lib/api-client";
import { Bot, Shield, Activity, Plus, Download } from "lucide-react";

interface TechnicalData {
  agents: { id: string; name: string; trustScore: number; status: string; policyVersion: string; lastEvaluation: string }[];
  enforcement: { allow: number; deny: number; requireApproval: number; quarantine: number; transform: number };
  policyEvaluations: { time: string; agent: string; decision: string; policy: string; rule: string; reason?: string }[];
  controls: { id: string; controlId: string; title: string; status: string; evidenceCount: number; lastAssessed: string }[];
  trustComponents: { agentName: string; identity: number; behavior: number; compliance: number; attestation: number; evidence: number }[];
  policyVersions: { version: string; agentCount: number; status: string }[];
}

async function fetchTechnicalData(): Promise<TechnicalData> {
  const { data } = await apiClient.get("/v1.0/agents");
  return data;
}

export default function TechnicalDashboard() {
  const { data, isLoading } = useQuery({ queryKey: ["technical-dashboard"], queryFn: fetchTechnicalData });

  if (isLoading) {
    return <div className="p-6"><SkeletonTable rows={8} columns={4} /></div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Technical Dashboard</h1>
        <div className="flex items-center gap-3">
          <select className="text-sm rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2">
            <option>Production</option>
            <option>Staging</option>
            <option>Development</option>
          </select>
          <Button variant="outline" size="sm"><Plus size={14} className="mr-1" /> Register Agent</Button>
          <Button variant="outline" size="sm"><Download size={14} className="mr-1" /> Export</Button>
        </div>
      </div>

      {/* Agent Registry */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot size={18} className="text-blue-500" />
            Agent Registry
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {(data?.agents || []).map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Enforcement & Policy Eval */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield size={18} className="text-green-500" />
              Runtime Enforcement (24h)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950/30 text-center">
                <p className="text-2xl font-bold text-green-600">{data?.enforcement.allow ?? 0}</p>
                <p className="text-sm text-green-700 dark:text-green-400">ALLOW</p>
              </div>
              <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/30 text-center">
                <p className="text-2xl font-bold text-red-600">{data?.enforcement.deny ?? 0}</p>
                <p className="text-sm text-red-700 dark:text-red-400">DENY</p>
              </div>
              <div className="p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950/30 text-center">
                <p className="text-2xl font-bold text-yellow-600">{data?.enforcement.requireApproval ?? 0}</p>
                <p className="text-sm text-yellow-700 dark:text-yellow-400">REQUIRE_APPROVAL</p>
              </div>
              <div className="p-4 rounded-lg bg-orange-50 dark:bg-orange-950/30 text-center">
                <p className="text-2xl font-bold text-orange-600">{data?.enforcement.quarantine ?? 0}</p>
                <p className="text-sm text-orange-700 dark:text-orange-400">QUARANTINE</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity size={18} className="text-purple-500" />
              Policy Evaluation Log
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(data?.policyEvaluations || []).map((eval_, i) => (
                <div key={i} className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{eval_.agent}</span>
                    <StatusBadge variant={eval_.decision === "ALLOW" ? "success" : "danger"}>{eval_.decision}</StatusBadge>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{eval_.time} — {eval_.policy}</p>
                  {eval_.reason && <p className="text-xs text-gray-400 mt-0.5">Reason: {eval_.reason}</p>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Control Implementation */}
      <Card>
        <CardHeader>
          <CardTitle>Control Implementation Status</CardTitle>
        </CardHeader>
        <CardContent>
          <ControlMatrix controls={data?.controls || []} />
        </CardContent>
      </Card>

      {/* Trust Components & Policy Versions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Trust Score Components</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(data?.trustComponents || []).map((comp) => (
                <div key={comp.agentName} className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <div className="flex items-center gap-3 mb-3">
                    <TrustScoreGauge score={Math.round((comp.identity + comp.behavior + comp.compliance + comp.attestation + comp.evidence) / 5)} size="sm" />
                    <span className="font-medium text-gray-900 dark:text-gray-100">{comp.agentName}</span>
                  </div>
                  <div className="space-y-2">
                    {[
                      { label: "Identity", value: comp.identity },
                      { label: "Behavior", value: comp.behavior },
                      { label: "Compliance", value: comp.compliance },
                      { label: "Attestation", value: comp.attestation },
                      { label: "Evidence", value: comp.evidence },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 w-20">{item.label}</span>
                        <div className="flex-1 h-2 rounded-full bg-gray-200 dark:bg-gray-700">
                          <div className="h-full rounded-full bg-blue-500" style={{ width: `${(item.value / 20) * 100}%` }} />
                        </div>
                        <span className="text-xs text-gray-500 w-8 text-right">{item.value}/20</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Policy Bundle Versions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(data?.policyVersions || []).map((ver) => (
                <div key={ver.version} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <div>
                    <span className="font-mono font-medium text-gray-900 dark:text-gray-100">{ver.version}</span>
                    <span className="text-sm text-gray-500 ml-2">{ver.agentCount} agents</span>
                  </div>
                  <StatusBadge variant={ver.status === "Current" ? "success" : "neutral"}>{ver.status}</StatusBadge>
                </div>
              ))}
            </div>
            <Button variant="outline" size="sm" className="mt-4">Create New Version</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

## 4. Operational Dashboard

### 4.1 Page Component

```tsx
// src/pages/dashboards/OperationalDashboard.tsx
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card";
import { StatCard } from "../../components/ui/StatCard";
import { SeverityIndicator } from "../../components/ui/SeverityIndicator";
import { VerificationLevel } from "../../components/ui/VerificationLevel";
import { ProgressBar } from "../../components/ui/ProgressBar";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Button } from "../../components/ui/Button";
import { SkeletonTable } from "../../components/ui/SkeletonLoader";
import apiClient from "../../lib/api-client";
import { AlertTriangle, FileText, Activity, Bot, Plus, Check } from "lucide-react";

interface OperationalData {
  alerts: { id: string; severity: string; message: string; time: string }[];
  findings: { critical: number; high: number; medium: number; low: number };
  evidence: { L0: number; L1: number; L2: number; L3: number; L4: number };
  assessments: { name: string; progress: number; status: string }[];
  agents: { governed: number; ungoverned: number; quarantined: number; pending: number };
  recentActivity: { time: string; actor: string; action: string; target: string; outcome: string }[];
}

async function fetchOperationalData(): Promise<OperationalData> {
  const { data } = await apiClient.get("/v1.0/compliance/posture");
  return data;
}

export default function OperationalDashboard() {
  const { data, isLoading } = useQuery({ queryKey: ["operational-dashboard"], queryFn: fetchOperationalData });

  if (isLoading) {
    return <div className="p-6"><SkeletonTable rows={8} columns={4} /></div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Operational Dashboard</h1>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm"><Check size={14} className="mr-1" /> Mark All Read</Button>
          <Button size="sm"><Plus size={14} className="mr-1" /> New Finding</Button>
        </div>
      </div>

      {/* Alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle size={18} className="text-yellow-500" />
            Alerts & Notifications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {(data?.alerts || []).map((alert) => (
              <div key={alert.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                <SeverityIndicator severity={alert.severity as any} size="sm" />
                <span className="text-sm text-gray-700 dark:text-gray-300 flex-1">{alert.message}</span>
                <span className="text-xs text-gray-500">{alert.time}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Findings & Evidence */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Open Findings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(["critical", "high", "medium", "low"] as const).map((sev) => (
                <div key={sev} className="flex items-center justify-between">
                  <SeverityIndicator severity={sev} size="sm" />
                  <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {data?.findings[sev] ?? 0}
                  </span>
                </div>
              ))}
            </div>
            <Button variant="outline" size="sm" className="mt-4 w-full">
              <Plus size={14} className="mr-1" /> Create Finding
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Evidence Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(["L0", "L1", "L2", "L3", "L4"] as const).map((level) => (
                <div key={level} className="flex items-center justify-between">
                  <VerificationLevel level={level} showDescription />
                  <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {data?.evidence[level] ?? 0}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Assessments & Agents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Active Assessments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(data?.assessments || []).map((assessment) => (
                <div key={assessment.name}>
                  <ProgressBar value={assessment.progress} label={assessment.name} />
                </div>
              ))}
            </div>
            <Button variant="outline" size="sm" className="mt-4">View All Assessments</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Agent Governance Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950/30 text-center">
                <p className="text-2xl font-bold text-green-600">{data?.agents.governed ?? 0}</p>
                <p className="text-sm text-green-700 dark:text-green-400">Governed</p>
              </div>
              <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800 text-center">
                <p className="text-2xl font-bold text-gray-600">{data?.agents.ungoverned ?? 0}</p>
                <p className="text-sm text-gray-500">Ungoverned</p>
              </div>
              <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/30 text-center">
                <p className="text-2xl font-bold text-red-600">{data?.agents.quarantined ?? 0}</p>
                <p className="text-sm text-red-700 dark:text-red-400">Quarantined</p>
              </div>
              <div className="p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950/30 text-center">
                <p className="text-2xl font-bold text-yellow-600">{data?.agents.pending ?? 0}</p>
                <p className="text-sm text-yellow-700 dark:text-yellow-400">Pending</p>
              </div>
            </div>
            <Button variant="outline" size="sm" className="mt-4">View Agent Registry</Button>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity size={18} className="text-blue-500" />
            Recent Governance Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
          <table className="w-full text-sm">
          <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
          <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Time</th>
          <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Actor</th>
          <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Action</th>
          <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Target</th>
          <th className="text-left py-2 px-3 font-medium text-gray-600 dark:text-gray-400">Outcome</th>
          </tr>
          </thead>
          <tbody>
          {(data?.recentActivity || []).map((activity, i) => (
          <tr key={i} className="border-b border-gray-100 dark:border-gray-800">
            <td className="py-2 px-3 text-gray-500">{activity.time}</td>
            <td className="py-2 px-3 font-medium">{activity.actor}</td>
            <td className="py-2 px-3">{activity.action}</td>
            <td className="py-2 px-3">{activity.target}</td>
            <td className="py-2 px-3"><StatusBadge variant="success">{activity.outcome}</StatusBadge></td>
          </tr>
          ))}
          </tbody>
          </table>
          </div>
          </CardContent>
          </Card>
          </div>
          );
          }
          ```

          ---

          ## 6. Policy Management Interface

          ### 6.1 Policy List View

          ```tsx
          // src/pages/policies/PolicyList.tsx
          import { useQuery } from "@tanstack/react-query";
          import { Card, CardContent } from "../../components/ui/Card";
          import { Button } from "../../components/ui/Button";
          import { StatusBadge } from "../../components/ui/StatusBadge";
          import { FilterBar } from "../../components/ui/FilterBar";
          import { DataTable } from "../../components/ui/DataTable";
          import { SkeletonTable } from "../../components/ui/SkeletonLoader";
          import apiClient from "../../lib/api-client";
          import { useNavigate } from "react-router-dom";
          import { Plus, Upload } from "lucide-react";
          import { useState } from "react";

          interface Policy {
          id: string;
          name: string;
          framework: string;
          version: string;
          status: "active" | "draft" | "deprecated" | "archived";
          owner: string;
          }

          async function fetchPolicies(): Promise<Policy[]> {
          const { data } = await apiClient.get("/v1.0/policies");
          return data.data;
          }

          export default function PolicyList() {
          const navigate = useNavigate();
          const { data: policies, isLoading } = useQuery({ queryKey: ["policies"], queryFn: fetchPolicies });
          const [search, setSearch] = useState("");
          const [frameworkFilter, setFrameworkFilter] = useState("all");
          const [statusFilter, setStatusFilter] = useState("all");

          if (isLoading) return <div className="p-6"><SkeletonTable rows={5} columns={6} /></div>;

          const columns = [
          { key: "name", header: "Policy Name", render: (p: Policy) => <span className="font-medium">{p.name}</span> },
          { key: "framework", header: "Framework", render: (p: Policy) => p.framework },
          { key: "version", header: "Version", render: (p: Policy) => <span className="font-mono text-xs">{p.version}</span> },
          {
          key: "status",
          header: "Status",
          render: (p: Policy) => (
          <StatusBadge variant={p.status === "active" ? "success" : p.status === "draft" ? "warning" : "neutral"}>
          {p.status}
          </StatusBadge>
          ),
          },
          { key: "owner", header: "Owner", render: (p: Policy) => p.owner },
          {
          key: "actions",
          header: "Actions",
          render: (p: Policy) => (
          <Button variant="ghost" size="sm" onClick={() => navigate(`/policies/${p.id}/edit`)}>Edit</Button>
          ),
          },
          ];

          return (
          <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Policy Management</h1>
          <div className="flex gap-3">
          <Button variant="outline" size="sm"><Upload size={14} className="mr-1" /> Import</Button>
          <Button size="sm"><Plus size={14} className="mr-1" /> New Policy</Button>
          </div>
          </div>

          <FilterBar
          searchValue={search}
          onSearchChange={setSearch}
          filters={[
          { key: "framework", label: "Framework", value: frameworkFilter, onChange: setFrameworkFilter, options: [{ value: "all", label: "All" }, { value: "SOC2", label: "SOC 2" }, { value: "ISO-27001", label: "ISO 27001" }, { value: "NIST-800-53", label: "NIST 800-53" }] },
          { key: "status", label: "Status", value: statusFilter, onChange: setStatusFilter, options: [{ value: "all", label: "All" }, { value: "active", label: "Active" }, { value: "draft", label: "Draft" }, { value: "deprecated", label: "Deprecated" }] },
          ]}
          />

          <Card>
          <CardContent className="p-0">
          <DataTable
          columns={columns}
          data={(policies || []).filter((p) => p.name.toLowerCase().includes(search.toLowerCase()))}
          keyExtractor={(p) => p.id}
          />
          </CardContent>
          </Card>
          </div>
          );
          }
          ```

          ### 6.2 Policy Editor

          ```tsx
          // src/pages/policies/PolicyEditor.tsx
          import { useState } from "react";
          import { useParams } from "react-router-dom";
          import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card";
          import { Button } from "../../components/ui/Button";
          import { Input } from "../../components/ui/Input";
          import { PolicyEditor } from "../../components/ui/PolicyEditor";
          import { TabBar } from "../../components/ui/TabBar";
          import { Accordion } from "../../components/ui/Accordion";
          import apiClient from "../../lib/api-client";
          import { useQuery } from "@tanstack/react-query";

          const defaultPolicyYaml = `apiVersion: governance.toolkit/v1
          name: org-baseline
          default_action: deny
          on_timeout: deny
          rules:
          - name: block-pii-export
          condition: "action.type == 'export' && data.contains_pii"
          action: deny
          priority: 1000
          description: "PII data must never leave the system"
          - name: audit-everything
          condition: "true"
          action: log
          priority: 0
          `;

          export default function PolicyEditorPage() {
          const { policyId } = useParams();
          const [activeTab, setActiveTab] = useState("editor");
          const [policyYaml, setPolicyYaml] = useState(defaultPolicyYaml);
          const [metadata, setMetadata] = useState({ name: "", version: "1.0.0", framework: "All", owner: "", status: "draft", description: "" });

          const { data: policy } = useQuery({
          queryKey: ["policy", policyId],
          queryFn: async () => {
          const { data } = await apiClient.get(`/v1.0/policies/${policyId}`);
          return data;
          },
          enabled: !!policyId,
          });

          const handleSave = async () => {
          await apiClient.put(`/v1.0/policies/${policyId}`, { ...metadata, cedar_policy: policyYaml });
          };

          const handleValidate = async () => {
          await apiClient.post(`/v1.0/policies/${policyId}/compile`);
          };

          return (
          <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Policy Editor: {metadata.name || "New Policy"}
          </h1>
          <div className="flex gap-3">
          <Button variant="outline" onClick={handleValidate}>Validate</Button>
          <Button onClick={handleSave}>Save</Button>
          </div>
          </div>

          <TabBar
          tabs={[
          { value: "editor", label: "Rules Editor" },
          { value: "metadata", label: "Metadata" },
          { value: "inheritance", label: "Inheritance" },
          { value: "history", label: "Version History" },
          ]}
          value={activeTab}
          onValueChange={setActiveTab}
          />

          {activeTab === "editor" && (
          <Card>
          <CardHeader><CardTitle>Policy Rules (YAML)</CardTitle></CardHeader>
          <CardContent>
          <PolicyEditor value={policyYaml} onChange={setPolicyYaml} onSave={handleSave} onValidate={handleValidate} height="500px" />
          </CardContent>
          </Card>
          )}

          {activeTab === "metadata" && (
          <Card>
          <CardHeader><CardTitle>Metadata</CardTitle></CardHeader>
          <CardContent>
          <div className="grid grid-cols-2 gap-4">
          <Input label="Name" value={metadata.name} onChange={(e) => setMetadata({ ...metadata, name: e.target.value })} />
          <Input label="Version" value={metadata.version} onChange={(e) => setMetadata({ ...metadata, version: e.target.value })} />
          <Input label="Framework" value={metadata.framework} onChange={(e) => setMetadata({ ...metadata, framework: e.target.value })} />
          <Input label="Owner" value={metadata.owner} onChange={(e) => setMetadata({ ...metadata, owner: e.target.value })} />
          </div>
          </CardContent>
          </Card>
          )}

          {activeTab === "inheritance" && (
          <Card>
          <CardHeader><CardTitle>Inheritance</CardTitle></CardHeader>
          <CardContent>
          <p className="text-sm text-gray-500">Configure policy inheritance relationships here.</p>
          </CardContent>
          </Card>
          )}

          {activeTab === "history" && (
          <Card>
          <CardHeader><CardTitle>Version History</CardTitle></CardHeader>
          <CardContent>
          <Accordion items={[
          { value: "v1", title: "v1.0.0 (Current)", content: "Initial policy creation" },
          ]} />
          </CardContent>
          </Card>
          )}
          </div>
          );
          }
          ```

          ### 6.3 Policy Test Console

          ```tsx
          // src/pages/policies/PolicyTestConsole.tsx
          import { useState } from "react";
          import { useParams } from "react-router-dom";
          import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card";
          import { Button } from "../../components/ui/Button";
          import { PolicyEditor } from "../../components/ui/PolicyEditor";
          import { StatusBadge } from "../../components/ui/StatusBadge";
          import apiClient from "../../lib/api-client";

          const defaultTestInput = `{
          "action": {
          "type": "export",
          "data": { "contains_pii": true }
          },
          "agent_id": "prod-cs-bot",
          "resource": { "type": "database" }
          }`;

          export default function PolicyTestConsole() {
          const { policyId } = useParams();
          const [testInput, setTestInput] = useState(defaultTestInput);
          const [result, setResult] = useState<any>(null);
          const [loading, setLoading] = useState(false);

          const handleRunTest = async () => {
          setLoading(true);
          try {
          const { data } = await apiClient.post(`/v1.0/policies/${policyId}/dry-run`, {
          test_inputs: [JSON.parse(testInput)],
          });
          setResult(data.dry_run_results[0]);
          } catch (error) {
          console.error("Test failed:", error);
          } finally {
          setLoading(false);
          }
          };

          return (
          <div className="p-6 space-y-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Policy Test Console</h1>

          <Card>
          <CardHeader><CardTitle>Test Input (JSON)</CardTitle></CardHeader>
          <CardContent>
          <PolicyEditor value={testInput} onChange={setTestInput} height="200px" />
          <Button className="mt-4" onClick={handleRunTest} loading={loading}>Run Test</Button>
          </CardContent>
          </Card>

          {result && (
          <Card>
          <CardHeader><CardTitle>Result</CardTitle></CardHeader>
          <CardContent>
          <div className="space-y-3">
          <div className="flex items-center gap-3">
          <span className="text-sm font-medium">Decision:</span>
          <StatusBadge variant={result.decision === "ALLOW" ? "success" : "danger"}>{result.decision}</StatusBadge>
          </div>
          <div><span className="text-sm font-medium">Matched Rule:</span> <span className="font-mono text-sm">{result.matched_rules?.[0]}</span></div>
          <div><span className="text-sm font-medium">Reason:</span> <span className="text-sm text-gray-600">{result.reason}</span></div>
          <div><span className="text-sm font-medium">Evaluation Time:</span> <span className="text-sm">{result.evaluation_time_ms}ms</span></div>
          </div>
          </CardContent>
          </Card>
          )}
          </div>
          );
          }
          ```

          ---

          ## 7. Evidence Viewer

          ### 7.1 Evidence List View

          ```tsx
          // src/pages/evidence/EvidenceList.tsx
          import { useQuery } from "@tanstack/react-query";
          import { Card, CardContent } from "../../components/ui/Card";
          import { Button } from "../../components/ui/Button";
          import { VerificationLevel } from "../../components/ui/VerificationLevel";
          import { FilterBar } from "../../components/ui/FilterBar";
          import { DataTable } from "../../components/ui/DataTable";
          import { SkeletonTable } from "../../components/ui/SkeletonLoader";
          import apiClient from "../../lib/api-client";
          import { useNavigate } from "react-router-dom";
          import { Plus, Download } from "lucide-react";
          import { useState } from "react";

          interface Evidence {
          id: string;
          control: string;
          type: string;
          verificationLevel: "L0" | "L1" | "L2" | "L3" | "L4";
          collectedAt: string;
          }

          async function fetchEvidence(): Promise<Evidence[]> {
          const { data } = await apiClient.get("/v1.0/evidence");
          return data.data;
          }

          export default function EvidenceList() {
          const navigate = useNavigate();
          const { data: evidence, isLoading } = useQuery({ queryKey: ["evidence"], queryFn: fetchEvidence });
          const [search, setSearch] = useState("");
          const [controlFilter, setControlFilter] = useState("all");
          const [typeFilter, setTypeFilter] = useState("all");
          const [verificationFilter, setVerificationFilter] = useState("all");

          if (isLoading) return <div className="p-6"><SkeletonTable rows={5} columns={6} /></div>;

          const columns = [
          { key: "id", header: "Evidence ID", render: (e: Evidence) => <span className="font-mono text-xs">{e.id}</span> },
          { key: "control", header: "Control", render: (e: Evidence) => e.control },
          { key: "type", header: "Type", render: (e: Evidence) => e.type },
          { key: "verification", header: "Verification", render: (e: Evidence) => <VerificationLevel level={e.verificationLevel} /> },
          { key: "collected", header: "Collected", render: (e: Evidence) => new Date(e.collectedAt).toLocaleString() },
          {
          key: "actions",
          header: "Actions",
          render: (e: Evidence) => (
          <Button variant="ghost" size="sm" onClick={() => navigate(`/evidence/${e.id}`)}>View</Button>
          ),
          },
          ];

          return (
          <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Evidence Viewer</h1>
          <div className="flex gap-3">
          <Button variant="outline" size="sm"><Download size={14} className="mr-1" /> Export</Button>
          <Button size="sm"><Plus size={14} className="mr-1" /> Upload</Button>
          </div>
          </div>

          <FilterBar
          searchValue={search}
          onSearchChange={setSearch}
          filters={[
          { key: "control", label: "Control", value: controlFilter, onChange: setControlFilter, options: [{ value: "all", label: "All" }, { value: "AC-2.1", label: "AC-2.1" }, { value: "AU-6.1", label: "AU-6.1" }, { value: "CC6.1", label: "CC6.1" }] },
          { key: "type", label: "Type", value: typeFilter, onChange: setTypeFilter, options: [{ value: "all", label: "All" }, { value: "artifact", label: "Artifact" }, { value: "log", label: "Log" }, { value: "observation", label: "Observation" }] },
          { key: "verification", label: "Verification", value: verificationFilter, onChange: setVerificationFilter, options: [{ value: "all", label: "All" }, { value: "L0", label: "L0" }, { value: "L1", label: "L1" }, { value: "L2", label: "L2" }, { value: "L3", label: "L3" }, { value: "L4", label: "L4" }] },
          ]}
          />

          <Card>
          <CardContent className="p-0">
          <DataTable
          columns={columns}
          data={(evidence || []).filter((e) => e.id.toLowerCase().includes(search.toLowerCase()))}
          keyExtractor={(e) => e.id}
          />
          </CardContent>
          </Card>
          </div>
          );
          }
          ```

          ### 7.2 Evidence Detail View

          ```tsx
          // src/pages/evidence/EvidenceDetail.tsx
          import { useParams } from "react-router-dom";
          import { useQuery } from "@tanstack/react-query";
          import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card";
          import { Button } from "../../components/ui/Button";
          import { VerificationLevel } from "../../components/ui/VerificationLevel";
          import { EvidenceTimeline } from "../../components/ui/EvidenceTimeline";
          import { TabBar } from "../../components/ui/TabBar";
          import { SkeletonLoader } from "../../components/ui/SkeletonLoader";
          import apiClient from "../../lib/api-client";
          import { useState } from "react";
          import { CheckCircle, Shield, FileText } from "lucide-react";

          export default function EvidenceDetail() {
          const { evidenceId } = useParams();
          const [activeTab, setActiveTab] = useState("content");

          const { data: evidence, isLoading } = useQuery({
          queryKey: ["evidence", evidenceId],
          queryFn: async () => {
          const { data } = await apiClient.get(`/v1.0/evidence/${evidenceId}`);
          return data;
          },
          enabled: !!evidenceId,
          });

          if (isLoading) return <div className="p-6"><SkeletonLoader className="h-64" /></div>;

          return (
          <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Evidence: {evidenceId}</h1>
          <div className="flex gap-3">
          <Button variant="outline" size="sm"><CheckCircle size={14} className="mr-1" /> Verify</Button>
          <Button size="sm"><Shield size={14} className="mr-1" /> Attest</Button>
          </div>
          </div>

          {/* Metadata */}
          <Card>
          <CardHeader><CardTitle>Metadata</CardTitle></CardHeader>
          <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-gray-500">Control:</span> <span className="font-medium">{evidence?.control_mapping?.control_id}</span></div>
          <div><span className="text-gray-500">Framework:</span> <span className="font-medium">{evidence?.control_mapping?.framework}</span></div>
          <div><span className="text-gray-500">Type:</span> <span className="font-medium">{evidence?.evidence_type}</span></div>
          <div><span className="text-gray-500">Verification:</span> <VerificationLevel level={evidence?.verification_level} /></div>
          <div><span className="text-gray-500">Collected by:</span> <span className="font-medium">{evidence?.source?.system}</span></div>
          <div><span className="text-gray-500">Collected at:</span> <span className="font-medium">{new Date(evidence?.created_at).toLocaleString()}</span></div>
          <div><span className="text-gray-500">Environment:</span> <span className="font-medium">{evidence?.context?.environment}</span></div>
          <div><span className="text-gray-500">SHA-256:</span> <span className="font-mono text-xs">{evidence?.content?.hash}</span></div>
          </div>
          </CardContent>
          </Card>

          <TabBar
          tabs={[
          { value: "content", label: "Content", icon: FileText },
          { value: "custody", label: "Chain of Custody", icon: Shield },
          ]}
          value={activeTab}
          onValueChange={setActiveTab}
          />

          {activeTab === "content" && (
          <Card>
          <CardHeader><CardTitle>Evidence Content</CardTitle></CardHeader>
          <CardContent>
          <pre className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800 text-sm font-mono overflow-x-auto">
          {JSON.stringify(JSON.parse(evidence?.content?.data || "{}"), null, 2)}
          </pre>
          </CardContent>
          </Card>
          )}

          {activeTab === "custody" && (
          <Card>
          <CardHeader><CardTitle>Chain of Custody</CardTitle></CardHeader>
          <CardContent>
          <EvidenceTimeline events={evidence?.chain_of_custody || []} />
          </CardContent>
          </Card>
          )}
          </div>
          );
          }
          ```

          ---

          ## 8. Alerting Interface

          ### 8.1 Alert Feed

          ```tsx
          // src/pages/alerts/AlertFeed.tsx
          import { useQuery } from "@tanstack/react-query";
          import { Card, CardContent } from "../../components/ui/Card";
          import { Button } from "../../components/ui/Button";
          import { SeverityIndicator } from "../../components/ui/SeverityIndicator";
          import { StatCard } from "../../components/ui/StatCard";
          import { SkeletonTable } from "../../components/ui/SkeletonLoader";
          import apiClient from "../../lib/api-client";
          import { useState } from "react";

          interface Alert {
          id: string;
          severity: "critical" | "high" | "medium" | "low";
          message: string;
          time: string;
          trigger: string;
          affected: string;
          }

          async function fetchAlerts(): Promise<Alert[]> {
          const { data } = await apiClient.get("/v1.0/alerts");
          return data.data;
          }

          export default function AlertFeed() {
          const { data: alerts, isLoading } = useQuery({ queryKey: ["alerts"], queryFn: fetchAlerts });
          const [filter, setFilter] = useState<string>("all");

          if (isLoading) return <div className="p-6"><SkeletonTable rows={5} columns={4} /></div>;

          const filteredAlerts = (alerts || []).filter((a) => filter === "all" || a.severity === filter);

          return (
          <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Alert Feed</h1>
          <div className="flex gap-3">
          <Button variant="outline" size="sm">Mark All Read</Button>
          <Button variant="outline" size="sm">Settings</Button>
          </div>
          </div>

          {/* Alert Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard title="Critical" value={(alerts || []).filter((a) => a.severity === "critical").length} />
          <StatCard title="High" value={(alerts || []).filter((a) => a.severity === "high").length} />
          <StatCard title="Medium" value={(alerts || []).filter((a) => a.severity === "medium").length} />
          <StatCard title="Low" value={(alerts || []).filter((a) => a.severity === "low").length} />
          </div>

          {/* Filter */}
          <div className="flex gap-2">
          {["all", "critical", "high", "medium", "low"].map((sev) => (
          <Button key={sev} variant={filter === sev ? "default" : "outline"} size="sm" onClick={() => setFilter(sev)}>
          {sev.charAt(0).toUpperCase() + sev.slice(1)}
          </Button>
          ))}
          </div>

          {/* Alert List */}
          <div className="space-y-3">
          {filteredAlerts.map((alert) => (
          <Card key={alert.id}>
          <CardContent className="p-4">
          <div className="flex items-start gap-4">
          <SeverityIndicator severity={alert.severity} size="lg" />
          <div className="flex-1">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{alert.message}</p>
          <p className="text-xs text-gray-500 mt-1">Trigger: {alert.trigger} | Affected: {alert.affected}</p>
          <p className="text-xs text-gray-400 mt-0.5">{alert.time}</p>
          </div>
          <div className="flex gap-2">
          <Button variant="ghost" size="sm">Acknowledge</Button>
          <Button variant="ghost" size="sm">Escalate</Button>
          </div>
          </div>
          </CardContent>
          </Card>
          ))}
          </div>
          </div>
          );
          }
          ```

          ### 8.2 Alert Configuration

          ```tsx
          // src/pages/alerts/AlertConfig.tsx
          import { useState } from "react";
          import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card";
          import { Button } from "../../components/ui/Button";
          import { Input } from "../../components/ui/Input";
          import { Switch } from "../../components/ui/Switch";
          import { StatusBadge } from "../../components/ui/StatusBadge";
          import { SeverityIndicator } from "../../components/ui/SeverityIndicator";
          import apiClient from "../../lib/api-client";
          import { Plus } from "lucide-react";

          interface AlertRule {
          id: string;
          name: string;
          trigger: string;
          severity: string;
          channel: string;
          status: "active" | "paused";
          }

          export default function AlertConfig() {
          const [showCreateForm, setShowCreateForm] = useState(false);
          const [rules, setRules] = useState<AlertRule[]>([
          { id: "1", name: "Trust drop", trigger: "Score < 60", severity: "critical", channel: "Email+Slack", status: "active" },
          { id: "2", name: "Evidence exp", trigger: "> 7 days", severity: "high", channel: "Email", status: "active" },
          { id: "3", name: "Policy viol", trigger: "Any deny", severity: "medium", channel: "Slack", status: "active" },
          ]);

          const [newRule, setNewRule] = useState({ name: "", metric: "Agent Trust Score", condition: "Less than", value: "60", severity: "critical" as string, channels: ["email"] });

          const handleCreateRule = async () => {
          await apiClient.post("/v1.0/alerts/rules", newRule);
          setShowCreateForm(false);
          };

          return (
          <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Alert Configuration</h1>
          <Button size="sm" onClick={() => setShowCreateForm(!showCreateForm)}>
          <Plus size={14} className="mr-1" /> New Alert Rule
          </Button>
          </div>

          {/* Create Rule Form */}
          {showCreateForm && (
          <Card>
          <CardHeader><CardTitle>Create Alert Rule</CardTitle></CardHeader>
          <CardContent>
          <div className="space-y-4">
          <Input label="Rule Name" value={newRule.name} onChange={(e) => setNewRule({ ...newRule, name: e.target.value })} />

          <div className="grid grid-cols-3 gap-4">
          <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Metric</label>
          <select className="w-full mt-1 text-sm rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2">
            <option>Agent Trust Score</option>
            <option>Evidence Age</option>
            <option>Policy Violations</option>
          </select>
          </div>
          <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Condition</label>
          <select className="w-full mt-1 text-sm rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2">
            <option>Less than</option>
            <option>Greater than</option>
            <option>Equals</option>
          </select>
          </div>
          <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Value</label>
          <Input type="number" value={newRule.value} onChange={(e) => setNewRule({ ...newRule, value: e.target.value })} />
          </div>
          </div>

          <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Severity</label>
          <div className="flex gap-4 mt-2">
          {(["critical", "high", "medium", "low"] as const).map((sev) => (
            <label key={sev} className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="severity" value={sev} checked={newRule.severity === sev} onChange={(e) => setNewRule({ ...newRule, severity: e.target.value })} className="text-blue-600" />
              <SeverityIndicator severity={sev} size="sm" />
            </label>
          ))}
          </div>
          </div>

          <div>
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Notification Channels</label>
          <div className="flex gap-4 mt-2">
          {["email", "slack", "pagerduty", "webhook"].map((ch) => (
            <label key={ch} className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={newRule.channels.includes(ch)} onChange={(e) => {
                if (e.target.checked) setNewRule({ ...newRule, channels: [...newRule.channels, ch] });
                else setNewRule({ ...newRule, channels: newRule.channels.filter((c) => c !== ch) });
              }} className="rounded text-blue-600" />
              <span className="text-sm capitalize">{ch}</span>
            </label>
          ))}
          </div>
          </div>

          <div className="flex gap-3">
          <Button onClick={handleCreateRule}>Save Rule</Button>
          <Button variant="outline" onClick={() => setShowCreateForm(false)}>Cancel</Button>
          </div>
          </div>
          </CardContent>
          </Card>
          )}

          {/* Rules List */}
          <Card>
          <CardHeader><CardTitle>Alert Rules</CardTitle></CardHeader>
          <CardContent>
          <div className="space-y-3">
          {rules.map((rule) => (
          <div key={rule.id} className="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-center gap-4">
          <SeverityIndicator severity={rule.severity as any} size="sm" />
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{rule.name}</p>
            <p className="text-xs text-gray-500">Trigger: {rule.trigger} | Channel: {rule.channel}</p>
          </div>
          </div>
          <div className="flex items-center gap-3">
          <StatusBadge variant={rule.status === "active" ? "success" : "neutral"}>{rule.status}</StatusBadge>
          <Switch checked={rule.status === "active"} onCheckedChange={(checked) => {
            setRules(rules.map((r) => r.id === rule.id ? { ...r, status: checked ? "active" : "paused" } : r));
          }} />
          </div>
          </div>
          ))}
          </div>
          </CardContent>
          </Card>
          </div>
          );
          }
          ```

          ---

          *End of GRC_Claw UI Implementation Guide.*
