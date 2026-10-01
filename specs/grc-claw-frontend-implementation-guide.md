# GRC_Claw Frontend Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Stack:** React 18+ / TypeScript / Vite / Zustand / React Query / Tailwind CSS

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [Component Library (30+ Components)](#2-component-library)
3. [Dashboard Implementations](#3-dashboard-implementations)
4. [State Management](#4-state-management)
5. [API Client Implementation](#5-api-client-implementation)
6. [Authentication Flow](#6-authentication-flow)
7. [Testing Framework](#7-testing-framework)

---

## 1. Project Structure

```
grc-claw-ui/
├── public/
│   ├── favicon.svg
│   └── locales/
│       ├── en.json
│       └── ar.json
├── src/
│   ├── api/                          # API client layer
│   │   ├── client.ts                 # Axios/fetch wrapper
│   │   ├── graphql.ts                # GraphQL client
│   │   ├── websocket.ts              # WebSocket subscriptions
│   │   ├── policies.ts               # Policy API calls
│   │   ├── evidence.ts               # Evidence API calls
│   │   ├── assessments.ts            # Assessment API calls
│   │   ├── compliance.ts             # Compliance API calls
│   │   ├── agents.ts                 # Agent registry API calls
│   │   ├── audit.ts                  # Audit trail API calls
│   │   └── alerts.ts                 # Alert API calls
│   ├── components/                   # Reusable UI components
│   │   ├── ui/                       # Primitive components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Select.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Drawer.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Tooltip.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Toast.tsx
│   │   │   ├── Dropdown.tsx
│   │   │   ├── Checkbox.tsx
│   │   │   ├── Radio.tsx
│   │   │   ├── Switch.tsx
│   │   │   ├── Accordion.tsx
│   │   │   ├── Avatar.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Divider.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── Pagination.tsx
│   │   │   ├── Breadcrumb.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── SearchInput.tsx
│   │   ├── domain/                   # Domain-specific components
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── SeverityIndicator.tsx
│   │   │   ├── VerificationLevel.tsx
│   │   │   ├── TrustScoreGauge.tsx
│   │   │   ├── ComplianceScoreBar.tsx
│   │   │   ├── EvidenceTimeline.tsx
│   │   │   ├── ControlMatrix.tsx
│   │   │   ├── AgentCard.tsx
│   │   │   ├── PolicyEditor.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── ChartWidget.tsx
│   │   │   ├── AlertToast.tsx
│   │   │   ├── FindingCard.tsx
│   │   │   ├── AssessmentProgress.tsx
│   │   │   ├── ComplianceHeatmap.tsx
│   │   │   ├── AuditTrailList.tsx
│   │   │   └── PolicyTestConsole.tsx
│   │   ├── layout/                   # Layout components
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── PageContainer.tsx
│   │   └── charts/                   # Chart components
│   │       ├── LineChart.tsx
│   │       ├── BarChart.tsx
│   │       ├── PieChart.tsx
│   │       ├── Histogram.tsx
│   │       └── Heatmap.tsx
│   ├── features/                     # Feature modules
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── CallbackPage.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   └── PermissionGate.tsx
│   │   ├── dashboard/
│   │   │   ├── ExecutiveDashboard.tsx
│   │   │   ├── OperationalDashboard.tsx
│   │   │   └── TechnicalDashboard.tsx
│   │   ├── policies/
│   │   │   ├── PolicyListPage.tsx
│   │   │   ├── PolicyEditorPage.tsx
│   │   │   ├── PolicyTestPage.tsx
│   │   │   └── PolicyVersionHistory.tsx
│   │   ├── evidence/
│   │   │   ├── EvidenceListPage.tsx
│   │   │   ├── EvidenceDetailPage.tsx
│   │   │   ├── EvidenceUploadPage.tsx
│   │   │   └── EvidenceExportPage.tsx
│   │   ├── assessments/
│   │   │   ├── AssessmentListPage.tsx
│   │   │   ├── AssessmentDetailPage.tsx
│   │   │   └── FindingDetailPage.tsx
│   │   ├── compliance/
│   │   │   ├── ComplianceMappingPage.tsx
│   │   │   ├── ControlDetailPage.tsx
│   │   │   └── CoverageSummaryPage.tsx
│   │   ├── alerts/
│   │   │   ├── AlertFeedPage.tsx
│   │   │   ├── AlertConfigPage.tsx
│   │   │   └── AlertDetailPage.tsx
│   │   ├── agents/
│   │   │   ├── AgentRegistryPage.tsx
│   │   │   ├── AgentDetailPage.tsx
│   │   │   └── TrustScoreDetail.tsx
│   │   └── audit/
│   │       ├── AuditTrailPage.tsx
│   │       └── ChainOfCustodyPage.tsx
│   ├── hooks/                        # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── usePermissions.ts
│   │   ├── useWebSocket.ts
│   │   ├── useDebounce.ts
│   │   ├── usePagination.ts
│   │   ├── useFilters.ts
│   │   ├── useExport.ts
│   │   └── useToast.ts
│   ├── store/                        # Zustand stores
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   ├── filterStore.ts
│   │   └── notificationStore.ts
│   ├── types/                        # TypeScript types
│   │   ├── api.ts                    # API response types
│   │   ├── domain.ts                 # Domain model types
│   │   ├── auth.ts                   # Auth types
│   │   └── ui.ts                     # UI component types
│   ├── utils/                        # Utility functions
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   ├── constants.ts
│   │   └── test-helpers.tsx
│   ├── styles/
│   │   ├── globals.css
│   │   └── tokens.css                # Design tokens
│   ├── App.tsx
│   ├── main.tsx
│   └── router.tsx
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── jest.config.ts
└── .env.example
```

### Package Dependencies

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.25.0",
    "@tanstack/react-query": "^5.50.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0",
    "recharts": "^2.12.0",
    "react-hook-form": "^7.52.0",
    "zod": "^3.23.0",
    "date-fns": "^3.6.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.4.0",
    "lucide-react": "^0.400.0",
    "react-hot-toast": "^2.4.0",
    "react-i18next": "^14.1.0",
    "i18next": "^23.12.0",
    "@monaco-editor/react": "^4.6.0",
    "react-window": "^1.8.10",
    "uuid": "^10.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "jest": "^29.7.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/user-event": "^14.5.0",
    "msw": "^2.3.0",
    "cypress": "^13.13.0",
    "eslint": "^8.57.0",
    "prettier": "^3.3.0"
  }
}
```

---

## 2. Component Library

### 2.1 Design Tokens

```typescript
// src/styles/tokens.css
:root {
  /* Color Palette */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  --color-info: #3b82f6;
  --color-neutral: #6b7280;
  --color-background: #ffffff;
  --color-surface: #f9fafb;
  --color-text-primary: #111827;
  --color-text-secondary: #6b7280;

  /* Severity Colors */
  --severity-critical: #ef4444;
  --severity-high: #f97316;
  --severity-medium: #eab308;
  --severity-low: #22c55e;

  /* Verification Level Colors */
  --verification-l0: #ef4444;
  --verification-l1: #f59e0b;
  --verification-l2: #3b82f6;
  --verification-l3: #8b5cf6;
  --verification-l4: #22c55e;

  /* Typography */
  --font-size-h1: 24px;
  --font-size-h2: 20px;
  --font-size-h3: 16px;
  --font-size-body: 14px;
  --font-size-small: 12px;
  --font-size-code: 13px;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 350ms ease;
}
```

### 2.2 Core UI Components

#### Button

```typescript
// src/components/ui/Button.tsx
import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: React.ReactNode;
}

const variantStyles: Record<Variant, string> = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
  secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
  outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500',
};

const sizeStyles: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, icon, className, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={clsx(
          'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
        {children}
      </button>
    );
  }
);
```

#### Input

```typescript
// src/components/ui/Input.tsx
import { forwardRef, type InputHTMLAttributes } from 'react';
import { clsx } from 'clsx';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
            {label}
            {props.required && <span className="text-red-500 ml-0.5">*</span>}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            'w-full rounded-lg border px-3 py-2 text-sm transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'disabled:bg-gray-50 disabled:text-gray-500',
            error ? 'border-red-500' : 'border-gray-300',
            className
          )}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="mt-1 text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={`${inputId}-hint`} className="mt-1 text-sm text-gray-500">
            {hint}
          </p>
        )}
      </div>
    );
  }
);
```

#### Select

```typescript
// src/components/ui/Select.tsx
import { forwardRef, type SelectHTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { ChevronDown } from 'lucide-react';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: SelectOption[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, placeholder, className, id, ...props }, ref) => {
    const selectId = id || props.name;
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={selectId} className="block text-sm font-medium text-gray-700 mb-1">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={clsx(
              'w-full appearance-none rounded-lg border px-3 py-2 pr-10 text-sm transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              'disabled:bg-gray-50 disabled:text-gray-500',
              error ? 'border-red-500' : 'border-gray-300',
              className
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((opt) => (
              <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                {opt.label}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
        </div>
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      </div>
    );
  }
);
```

#### Modal

```typescript
// src/components/ui/Modal.tsx
import { useEffect, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { clsx } from 'clsx';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeStyles = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

export function Modal({ open, onClose, title, children, footer, size = 'md' }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEsc);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-in fade-in"
      onClick={(e) => e.target === overlayRef.current && onClose()}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div className={clsx('w-full bg-white rounded-xl shadow-xl', sizeStyles[size])}>
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}
        <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">{children}</div>
        {footer && <div className="px-6 py-4 border-t bg-gray-50 rounded-b-xl">{footer}</div>}
      </div>
    </div>,
    document.body
  );
}
```

#### Drawer

```typescript
// src/components/ui/Drawer.tsx
import { useEffect, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
  width?: string;
}

export function Drawer({ open, onClose, title, children, footer, width = '480px' }: DrawerProps) {
  useEffect(() => {
    if (!open) return;
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div
        className="absolute right-0 top-0 h-full bg-white shadow-xl flex flex-col"
        style={{ width }}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}
        <div className="flex-1 overflow-y-auto px-6 py-4">{children}</div>
        {footer && <div className="px-6 py-4 border-t bg-gray-50">{footer}</div>}
      </div>
    </div>,
    document.body
  );
}
```

#### Tabs

```typescript
// src/components/ui/Tabs.tsx
import { useState, type ReactNode } from 'react';
import { clsx } from 'clsx';

interface Tab {
  id: string;
  label: string;
  icon?: ReactNode;
  content: ReactNode;
  badge?: string | number;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
  onChange?: (tabId: string) => void;
}

export function Tabs({ tabs, defaultTab, onChange }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    onChange?.(tabId);
  };

  return (
    <div>
      <div className="border-b border-gray-200" role="tablist">
        <nav className="flex gap-1 -mb-px" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`panel-${tab.id}`}
              onClick={() => handleTabChange(tab.id)}
              className={clsx(
                'flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              )}
            >
              {tab.icon}
              {tab.label}
              {tab.badge !== undefined && (
                <span className="px-1.5 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>
      <div className="pt-4">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            role="tabpanel"
            id={`panel-${tab.id}`}
            hidden={activeTab !== tab.id}
            aria-labelledby={tab.id}
          >
            {activeTab === tab.id && tab.content}
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### Badge

```typescript
// src/components/ui/Badge.tsx
import { type ReactNode } from 'react';
import { clsx } from 'clsx';

type Variant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline';

interface BadgeProps {
  variant?: Variant;
  children: ReactNode;
  icon?: ReactNode;
  className?: string;
}

const variantStyles: Record<Variant, string> = {
  default: 'bg-gray-100 text-gray-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-yellow-100 text-yellow-700',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-700',
  outline: 'border border-gray-300 text-gray-700',
};

export function Badge({ variant = 'default', children, icon, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
        variantStyles[variant],
        className
      )}
    >
      {icon}
      {children}
    </span>
  );
}
```

#### Skeleton

```typescript
// src/components/ui/Skeleton.tsx
import { clsx } from 'clsx';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export function Skeleton({ className, variant = 'text', width, height }: SkeletonProps) {
  return (
    <div
      className={clsx(
        'animate-pulse bg-gray-200',
        variant === 'text' && 'h-4 rounded',
        variant === 'circular' && 'rounded-full',
        variant === 'rectangular' && 'rounded-lg',
        className
      )}
      style={{ width, height }}
      aria-hidden="true"
    />
  );
}

export function SkeletonTable({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="space-y-3" aria-label="Loading">
      <div className="flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: columns }).map((_, j) => (
            <Skeleton key={j} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}
```

#### Toast

```typescript
// src/components/ui/Toast.tsx
import { useEffect } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import { clsx } from 'clsx';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastProps {
  type: ToastType;
  message: string;
  onClose: () => void;
  duration?: number;
  action?: { label: string; onClick: () => void };
}

const icons: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle className="h-5 w-5 text-green-500" />,
  error: <XCircle className="h-5 w-5 text-red-500" />,
  warning: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
  info: <Info className="h-5 w-5 text-blue-500" />,
};

const bgStyles: Record<ToastType, string> = {
  success: 'bg-green-50 border-green-200',
  error: 'bg-red-50 border-red-200',
  warning: 'bg-yellow-50 border-yellow-200',
  info: 'bg-blue-50 border-blue-200',
};

export function Toast({ type, message, onClose, duration = 5000, action }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div
      className={clsx(
        'flex items-start gap-3 p-4 rounded-lg border shadow-lg min-w-[320px] max-w-[480px]',
        'animate-in slide-in-from-right',
        bgStyles[type]
      )}
      role="alert"
    >
      {icons[type]}
      <p className="flex-1 text-sm text-gray-900">{message}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="text-sm font-medium text-blue-600 hover:text-blue-800"
        >
          {action.label}
        </button>
      )}
      <button onClick={onClose} className="text-gray-400 hover:text-gray-600" aria-label="Dismiss">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
```

#### EmptyState

```typescript
// src/components/ui/EmptyState.tsx
import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="mb-4 text-gray-400">{icon || <Inbox className="h-12 w-12" />}</div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
      {description && <p className="text-sm text-gray-500 max-w-sm mb-4">{description}</p>}
      {action}
    </div>
  );
}
```

#### Pagination

```typescript
// src/components/ui/Pagination.tsx
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalItems?: number;
  pageSize?: number;
}

export function Pagination({ currentPage, totalPages, onPageChange, totalItems, pageSize }: PaginationProps) {
  const pages = getPageNumbers(currentPage, totalPages);

  return (
    <nav className="flex items-center justify-between" aria-label="Pagination">
      <div className="text-sm text-gray-500">
        {totalItems !== undefined && pageSize !== undefined && (
          <>
            Showing {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, totalItems)} of {totalItems}
          </>
        )}
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        {pages.map((page, i) =>
          page === '...' ? (
            <span key={`ellipsis-${i}`} className="px-2 text-gray-400">…</span>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange(page as number)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                page === currentPage
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
              aria-current={page === currentPage ? 'page' : undefined}
            >
              {page}
            </button>
          )
        )}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </nav>
  );
}

function getPageNumbers(current: number, total: number): (number | string)[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  if (current <= 3) return [1, 2, 3, 4, '...', total];
  if (current >= total - 2) return [1, '...', total - 3, total - 2, total - 1, total];
  return [1, '...', current - 1, current, current + 1, '...', total];
}
```

#### SearchInput

```typescript
// src/components/ui/SearchInput.tsx
import { Search, X } from 'lucide-react';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  debounceMs?: number;
}

export function SearchInput({ value, onChange, placeholder = 'Search...', className }: SearchInputProps) {
  return (
    <div className={className}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-10 pr-8 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        aria-label={placeholder}
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
```

#### ProgressBar

```typescript
// src/components/ui/ProgressBar.tsx
import { clsx } from 'clsx';

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  size?: 'sm' | 'md' | 'lg';
  color?: 'auto' | 'blue' | 'green' | 'red' | 'yellow';
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showValue = true,
  size = 'md',
  color = 'auto',
  className,
}: ProgressBarProps) {
  const percentage = Math.min(Math.round((value / max) * 100), 100);

  const getColor = () => {
    if (color !== 'auto') {
      return { blue: 'bg-blue-500', green: 'bg-green-500', red: 'bg-red-500', yellow: 'bg-yellow-500' }[color];
    }
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const heights = { sm: 'h-1.5', md: 'h-2.5', lg: 'h-4' };

  return (
    <div className={className}>
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-sm text-gray-700">{label}</span>}
          {showValue && <span className="text-sm font-medium text-gray-900">{percentage}%</span>}
        </div>
      )}
      <div className={clsx('w-full bg-gray-200 rounded-full overflow-hidden', heights[size])}>
        <div
          className={clsx('h-full rounded-full transition-all duration-500', getColor())}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
}
```

#### Accordion

```typescript
// src/components/ui/Accordion.tsx
import { useState, type ReactNode } from 'react';
import { ChevronDown } from 'lucide-react';
import { clsx } from 'clsx';

interface AccordionItem {
  id: string;
  title: string;
  content: ReactNode;
  badge?: string;
}

interface AccordionProps {
  items: AccordionItem[];
  allowMultiple?: boolean;
}

export function Accordion({ items, allowMultiple = false }: AccordionProps) {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    setOpenItems((prev) => {
      const next = new Set(allowMultiple ? prev : []);
      if (prev.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div className="divide-y divide-gray-200 border border-gray-200 rounded-lg">
      {items.map((item) => {
        const isOpen = openItems.has(item.id);
        return (
          <div key={item.id}>
            <button
              onClick={() => toggle(item.id)}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50"
              aria-expanded={isOpen}
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-900">{item.title}</span>
                {item.badge && (
                  <span className="px-1.5 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                    {item.badge}
                  </span>
                )}
              </div>
              <ChevronDown
                className={clsx('h-4 w-4 text-gray-400 transition-transform', isOpen && 'rotate-180')}
              />
            </button>
            {isOpen && <div className="px-4 pb-3 text-sm text-gray-600">{item.content}</div>}
          </div>
        );
      })}
    </div>
  );
}
```

#### Avatar

```typescript
// src/components/ui/Avatar.tsx
import { clsx } from 'clsx';

interface AvatarProps {
  name: string;
  src?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizes = { sm: 'h-6 w-6 text-xs', md: 'h-8 w-8 text-sm', lg: 'h-10 w-10 text-base' };

export function Avatar({ name, src, size = 'md', className }: AvatarProps) {
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={clsx('rounded-full object-cover', sizes[size], className)}
      />
    );
  }

  return (
    <div
      className={clsx(
        'rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-medium',
        sizes[size],
        className
      )}
      aria-label={name}
    >
      {initials}
    </div>
  );
}
```

#### Card

```typescript
// src/components/ui/Card.tsx
import { type ReactNode } from 'react';
import { clsx } from 'clsx';

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
};

export function Card({ children, className, padding = 'md', hover }: CardProps) {
  return (
    <div
      className={clsx(
        'bg-white rounded-xl border border-gray-200 shadow-sm',
        paddingStyles[padding],
        hover && 'transition-shadow hover:shadow-md',
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}

export function CardHeader({ title, subtitle, action }: CardHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-base font-semibold text-gray-900">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
```

#### Divider

```typescript
// src/components/ui/Divider.tsx
import { clsx } from 'clsx';

interface DividerProps {
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

export function Divider({ orientation = 'horizontal', className }: DividerProps) {
  return (
    <div
      className={clsx(
        'bg-gray-200',
        orientation === 'horizontal' ? 'h-px w-full' : 'w-px h-full',
        className
      )}
      role="separator"
    />
  );
}
```

#### Checkbox

```typescript
// src/components/ui/Checkbox.tsx
import { forwardRef, type InputHTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { Check } from 'lucide-react';

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div className="flex items-start gap-2">
        <div className="relative flex items-center">
          <input
            ref={ref}
            type="checkbox"
            className={clsx(
              'h-4 w-4 rounded border-gray-300 text-blue-600',
              'focus:ring-2 focus:ring-blue-500 focus:ring-offset-0',
              'disabled:opacity-50',
              className
            )}
            {...props}
          />
        </div>
        {label && (
          <label htmlFor={props.id} className="text-sm text-gray-700 cursor-pointer">
            {label}
          </label>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    );
  }
);
```

#### Switch

```typescript
// src/components/ui/Switch.tsx
import { clsx } from 'clsx';

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  size?: 'sm' | 'md';
}

export function Switch({ checked, onChange, label, disabled, size = 'md' }: SwitchProps) {
  return (
    <label className={clsx('inline-flex items-center gap-2', disabled && 'opacity-50 cursor-not-allowed')}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={clsx(
          'relative inline-flex rounded-full transition-colors',
          size === 'sm' ? 'h-5 w-9' : 'h-6 w-11',
          checked ? 'bg-blue-600' : 'bg-gray-300'
        )}
      >
        <span
          className={clsx(
            'inline-block rounded-full bg-white shadow transition-transform',
            size === 'sm' ? 'h-3 w-3' : 'h-4 w-4',
            checked
              ? size === 'sm'
                ? 'translate-x-5'
                : 'translate-x-6'
              : 'translate-x-1',
            'mt-0.5'
          )}
        />
      </button>
      {label && <span className="text-sm text-gray-700">{label}</span>}
    </label>
  );
}
```

#### Tooltip

```typescript
// src/components/ui/Tooltip.tsx
import { useState, type ReactNode } from 'react';
import { clsx } from 'clsx';

interface TooltipProps {
  content: string;
  children: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

const positionStyles = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

export function Tooltip({ content, children, position = 'top' }: TooltipProps) {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          className={clsx(
            'absolute z-50 px-2 py-1 text-xs text-white bg-gray-900 rounded whitespace-nowrap',
            positionStyles[position]
          )}
          role="tooltip"
        >
          {content}
        </div>
      )}
    </div>
  );
}
```

#### Spinner

```typescript
// src/components/ui/Spinner.tsx
import { clsx } from 'clsx';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizes = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' };

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <svg
      className={clsx('animate-spin text-blue-600', sizes[size], className)}
      viewBox="0 0 24 24"
      fill="none"
      aria-label="Loading"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
```

#### Dropdown

```typescript
// src/components/ui/Dropdown.tsx
import { useState, useRef, useEffect, type ReactNode } from 'react';
import { clsx } from 'clsx';

interface DropdownItem {
  label: string;
  onClick: () => void;
  icon?: ReactNode;
  danger?: boolean;
  disabled?: boolean;
}

interface DropdownProps {
  trigger: ReactNode;
  items: DropdownItem[];
  align?: 'left' | 'right';
}

export function Dropdown({ trigger, items, align = 'right' }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div ref={ref} className="relative inline-block">
      <div onClick={() => setOpen(!open)}>{trigger}</div>
      {open && (
        <div
          className={clsx(
            'absolute z-50 mt-1 min-w-[180px] bg-white rounded-lg border border-gray-200 shadow-lg py-1',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {items.map((item, i) => (
            <button
              key={i}
              onClick={() => {
                item.onClick();
                setOpen(false);
              }}
              disabled={item.disabled}
              className={clsx(
                'w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-gray-50',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                item.danger ? 'text-red-600' : 'text-gray-700'
              )}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### Radio

```typescript
// src/components/ui/Radio.tsx
import { forwardRef, type InputHTMLAttributes } from 'react';
import { clsx } from 'clsx';

interface RadioProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
}

export const Radio = forwardRef<HTMLInputElement, RadioProps>(
  ({ label, className, ...props }, ref) => {
    return (
      <label className="inline-flex items-center gap-2 cursor-pointer">
        <input
          ref={ref}
          type="radio"
          className={clsx(
            'h-4 w-4 border-gray-300 text-blue-600',
            'focus:ring-2 focus:ring-blue-500 focus:ring-offset-0',
            className
          )}
          {...props}
        />
        {label && <span className="text-sm text-gray-700">{label}</span>}
      </label>
    );
  }
);
```

#### Breadcrumb

```typescript
// src/components/ui/Breadcrumb.tsx
import { ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';

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
    <nav aria-label="Breadcrumb" className={className}>
      <ol className="flex items-center gap-1 text-sm">
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="h-3 w-3 text-gray-400" />}
            {item.href ? (
              <a href={item.href} className="text-blue-600 hover:text-blue-800 hover:underline">
                {item.label}
              </a>
            ) : (
              <span className={clsx(i === items.length - 1 ? 'text-gray-900 font-medium' : 'text-gray-500')}>
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
```

#### ErrorBoundary

```typescript
// src/components/ui/ErrorBoundary.tsx
import { Component, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-red-500 mb-4" />
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-sm text-gray-500 mb-4">{this.state.error?.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              Try again
            </button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
```

### 2.3 Domain Components

#### StatusBadge

```typescript
// src/components/domain/StatusBadge.tsx
import { clsx } from 'clsx';
import { CheckCircle, XCircle, AlertTriangle, Clock, MinusCircle } from 'lucide-react';

type Status = 'pass' | 'fail' | 'gap' | 'pending' | 'exempt' | 'not_assessed';

interface StatusBadgeProps {
  status: Status;
  showIcon?: boolean;
  className?: string;
}

const statusConfig: Record<Status, { icon: React.ReactNode; label: string; className: string }> = {
  pass: { icon: <CheckCircle className="h-3.5 w-3.5" />, label: 'Pass', className: 'bg-green-100 text-green-700' },
  fail: { icon: <XCircle className="h-3.5 w-3.5" />, label: 'Fail', className: 'bg-red-100 text-red-700' },
  gap: { icon: <AlertTriangle className="h-3.5 w-3.5" />, label: 'Gap', className: 'bg-yellow-100 text-yellow-700' },
  pending: { icon: <Clock className="h-3.5 w-3.5" />, label: 'Pending', className: 'bg-blue-100 text-blue-700' },
  exempt: { icon: <MinusCircle className="h-3.5 w-3.5" />, label: 'Exempt', className: 'bg-gray-100 text-gray-700' },
  not_assessed: { icon: <MinusCircle className="h-3.5 w-3.5" />, label: 'Not Assessed', className: 'bg-gray-100 text-gray-500' },
};

export function StatusBadge({ status, showIcon = true, className }: StatusBadgeProps) {
  const config = statusConfig[status];
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
        config.className,
        className
      )}
    >
      {showIcon && config.icon}
      {config.label}
    </span>
  );
}
```

#### SeverityIndicator

```typescript
// src/components/domain/SeverityIndicator.tsx
import { clsx } from 'clsx';

type Severity = 'critical' | 'high' | 'medium' | 'low';

interface SeverityIndicatorProps {
  severity: Severity;
  showLabel?: boolean;
  className?: string;
}

const severityConfig: Record<Severity, { icon: string; label: string; className: string }> = {
  critical: { icon: '🔴', label: 'Critical', className: 'text-red-600' },
  high: { icon: '🟠', label: 'High', className: 'text-orange-600' },
  medium: { icon: '🟡', label: 'Medium', className: 'text-yellow-600' },
  low: { icon: '🟢', label: 'Low', className: 'text-green-600' },
};

export function SeverityIndicator({ severity, showLabel = true, className }: SeverityIndicatorProps) {
  const config = severityConfig[severity];
  return (
    <span className={clsx('inline-flex items-center gap-1', config.className, className)}>
      <span aria-hidden="true">{config.icon}</span>
      {showLabel && <span className="text-sm font-medium">{config.label}</span>}
    </span>
  );
}
```

#### VerificationLevel

```typescript
// src/components/domain/VerificationLevel.tsx
import { clsx } from 'clsx';
import { CheckCircle, XCircle, AlertTriangle, Shield, ShieldCheck } from 'lucide-react';

type VerificationLevel = 'L0' | 'L1' | 'L2' | 'L3' | 'L4';

interface VerificationLevelProps {
  level: VerificationLevel;
  showLabel?: boolean;
  showProgress?: boolean;
  className?: string;
}

const levelConfig: Record<VerificationLevel, { icon: React.ReactNode; label: string; className: string; color: string }> = {
  L0: { icon: <XCircle className="h-4 w-4" />, label: 'Unverified', className: 'bg-red-100 text-red-700', color: '#ef4444' },
  L1: { icon: <AlertTriangle className="h-4 w-4" />, label: 'Schema-valid', className: 'bg-yellow-100 text-yellow-700', color: '#f59e0b' },
  L2: { icon: <Shield className="h-4 w-4" />, label: 'Integrity-verified', className: 'bg-blue-100 text-blue-700', color: '#3b82f6' },
  L3: { icon: <ShieldCheck className="h-4 w-4" />, label: 'Cross-validated', className: 'bg-purple-100 text-purple-700', color: '#8b5cf6' },
  L4: { icon: <CheckCircle className="h-4 w-4" />, label: 'Attested', className: 'bg-green-100 text-green-700', color: '#22c55e' },
};

export function VerificationLevel({ level, showLabel = true, showProgress, className }: VerificationLevelProps) {
  const config = levelConfig[level];
  const levelNum = parseInt(level[1]);

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      <span className={clsx('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', config.className)}>
        {config.icon}
        {showLabel && config.label}
      </span>
      {showProgress && (
        <div className="flex gap-0.5">
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: i <= levelNum ? config.color : '#e5e7eb' }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

#### TrustScoreGauge

```typescript
// src/components/domain/TrustScoreGauge.tsx
import { clsx } from 'clsx';

interface TrustScoreGaugeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

function getGrade(score: number): { grade: string; color: string } {
  if (score >= 90) return { grade: 'A', color: '#22c55e' };
  if (score >= 80) return { grade: 'B', color: '#3b82f6' };
  if (score >= 70) return { grade: 'C', color: '#f59e0b' };
  if (score >= 60) return { grade: 'D', color: '#f97316' };
  return { grade: 'F', color: '#ef4444' };
}

const sizes = { sm: 64, md: 96, lg: 128 };

export function TrustScoreGauge({ score, size = 'md', showLabel = true, className }: TrustScoreGaugeProps) {
  const { grade, color } = getGrade(score);
  const dimension = sizes[size];
  const strokeWidth = size === 'sm' ? 6 : size === 'md' ? 8 : 10;
  const radius = (dimension - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className={clsx('flex flex-col items-center', className)}>
      <svg width={dimension} height={dimension} className="-rotate-90">
        <circle
          cx={dimension / 2}
          cy={dimension / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={dimension / 2}
          cy={dimension / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ width: dimension, height: dimension }}>
        <span className="text-2xl font-bold" style={{ color }}>{score}</span>
        {showLabel && <span className="text-sm font-medium text-gray-500">Grade {grade}</span>}
      </div>
    </div>
  );
}
```

#### ComplianceScoreBar

```typescript
// src/components/domain/ComplianceScoreBar.tsx
import { clsx } from 'clsx';

interface ComplianceScoreBarProps {
  score: number;
  label?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ComplianceScoreBar({ score, label, showPercentage = true, size = 'md', className }: ComplianceScoreBarProps) {
  const getColor = () => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const heights = { sm: 'h-2', md: 'h-3', lg: 'h-4' };

  return (
    <div className={clsx('w-full', className)}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-1">
          {label && <span className="text-sm text-gray-700">{label}</span>}
          {showPercentage && <span className="text-sm font-semibold text-gray-900">{score}%</span>}
        </div>
      )}
      <div className={clsx('w-full bg-gray-200 rounded-full overflow-hidden', heights[size])}>
        <div
          className={clsx('h-full rounded-full transition-all duration-500', getColor())}
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

#### EvidenceTimeline

```typescript
// src/components/domain/EvidenceTimeline.tsx
import { clsx } from 'clsx';
import { CheckCircle, Circle } from 'lucide-react';

interface CustodyEvent {
  action: string;
  actor: string;
  timestamp: string;
  hash: string;
  signatureValid: boolean;
}

interface EvidenceTimelineProps {
  events: CustodyEvent[];
  className?: string;
}

export function EvidenceTimeline({ events, className }: EvidenceTimelineProps) {
  return (
    <div className={clsx('relative', className)}>
      <div className="absolute left-4 top-0 bottom-0 w-px bg-gray-200" />
      <div className="space-y-4">
        {events.map((event, i) => (
          <div key={i} className="relative flex items-start gap-3 pl-8">
            <div className="absolute left-2.5 top-1">
              {event.signatureValid ? (
                <CheckCircle className="h-3.5 w-3.5 text-green-500" />
              ) : (
                <Circle className="h-3.5 w-3.5 text-gray-300" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-900 capitalize">{event.action}</span>
                <span className="text-xs text-gray-500">{event.actor}</span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                {new Date(event.timestamp).toLocaleString()}
              </p>
              <p className="text-xs text-gray-400 font-mono mt-0.5 truncate">{event.hash}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

#### ControlMatrix

```typescript
// src/components/domain/ControlMatrix.tsx
import { StatusBadge } from './StatusBadge';
import { clsx } from 'clsx';

interface Control {
  id: string;
  title: string;
  status: 'pass' | 'fail' | 'gap' | 'pending';
  evidenceCount: number;
  lastReviewed?: string;
}

interface ControlMatrixProps {
  controls: Control[];
  onControlClick?: (control: Control) => void;
  className?: string;
}

export function ControlMatrix({ controls, onControlClick, className }: ControlMatrixProps) {
  return (
    <div className={clsx('overflow-x-auto', className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 px-3 font-medium text-gray-500">Control ID</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Title</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Status</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Evidence</th>
            <th className="text-left py-2 px-3 font-medium text-gray-500">Last Review</th>
          </tr>
        </thead>
        <tbody>
          {controls.map((control) => (
            <tr
              key={control.id}
              onClick={() => onControlClick?.(control)}
              className={clsx(
                'border-b border-gray-100 hover:bg-gray-50',
                onControlClick && 'cursor-pointer'
              )}
            >
              <td className="py-2 px-3 font-mono text-xs">{control.id}</td>
              <td className="py-2 px-3">{control.title}</td>
              <td className="py-2 px-3"><StatusBadge status={control.status} /></td>
              <td className="py-2 px-3">{control.evidenceCount}</td>
              <td className="py-2 px-3 text-gray-500">
                {control.lastReviewed ? new Date(control.lastReviewed).toLocaleDateString() : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

#### AgentCard

```typescript
// src/components/domain/AgentCard.tsx
import { clsx } from 'clsx';
import { TrustScoreGauge } from './TrustScoreGauge';
import { Badge } from '../ui/Badge';

interface Agent {
  id: string;
  name: string;
  trustScore: number;
  status: 'active' | 'quarantined' | 'pending';
  policyVersion: string;
  lastEvaluated: string;
}

interface AgentCardProps {
  agent: Agent;
  onClick?: (agent: Agent) => void;
  className?: string;
}

const statusStyles = {
  active: 'bg-green-100 text-green-700',
  quarantined: 'bg-red-100 text-red-700',
  pending: 'bg-yellow-100 text-yellow-700',
};

export function AgentCard({ agent, onClick, className }: AgentCardProps) {
  return (
    <div
      onClick={() => onClick?.(agent)}
      className={clsx(
        'flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200',
        onClick && 'cursor-pointer hover:shadow-md transition-shadow',
        className
      )}
    >
      <TrustScoreGauge score={agent.trustScore} size="sm" showLabel={false} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-semibold text-gray-900 truncate">{agent.name}</h4>
          <span className={clsx('px-1.5 py-0.5 rounded-full text-xs font-medium capitalize', statusStyles[agent.status])}>
            {agent.status}
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-0.5">
          Policy: {agent.policyVersion} · Last eval: {new Date(agent.lastEvaluated).toLocaleString()}
        </p>
      </div>
    </div>
  );
}
```

#### FilterBar

```typescript
// src/components/domain/FilterBar.tsx
import { SearchInput } from '../ui/SearchInput';
import { Select } from '../ui/Select';
import { Button } from '../ui/Button';
import { Filter, X } from 'lucide-react';

interface FilterOption {
  value: string;
  label: string;
}

interface FilterConfig {
  name: string;
  placeholder?: string;
  options: FilterOption[];
}

interface FilterBarProps {
  filters: FilterConfig[];
  values: Record<string, string>;
  onChange: (name: string, value: string) => void;
  onReset: () => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  className?: string;
}

export function FilterBar({
  filters,
  values,
  onChange,
  onReset,
  searchValue,
  onSearchChange,
  searchPlaceholder = 'Search...',
  className,
}: FilterBarProps) {
  const hasActiveFilters = Object.values(values).some(Boolean) || !!searchValue;

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[200px]">
          <SearchInput
            value={searchValue}
            onChange={onSearchChange}
            placeholder={searchPlaceholder}
          />
        </div>
        {filters.map((filter) => (
          <Select
            key={filter.name}
            name={filter.name}
            options={[{ value: '', label: filter.placeholder || 'All' }, ...filter.options]}
            value={values[filter.name] || ''}
            onChange={(e) => onChange(filter.name, e.target.value)}
            className="w-40"
          />
        ))}
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={onReset} icon={<X className="h-3.5 w-3.5" />}>
            Clear
          </Button>
        )}
      </div>
    </div>
  );
}
```

#### DataTable

```typescript
// src/components/domain/DataTable.tsx
import { useState } from 'react';
import { clsx } from 'clsx';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import { Pagination } from '../ui/Pagination';
import { SkeletonTable } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';

interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  loading?: boolean;
  emptyMessage?: string;
  pagination?: {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    pageSize: number;
    onPageChange: (page: number) => void;
  };
  onRowClick?: (item: T) => void;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  loading,
  emptyMessage = 'No data available',
  pagination,
  onRowClick,
  className,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  if (loading) return <SkeletonTable rows={5} columns={columns.length} />;

  if (data.length === 0) return <EmptyState title={emptyMessage} />;

  return (
    <div className={className}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className="text-left py-3 px-3 font-medium text-gray-500"
                  style={{ width: col.width }}
                  aria-sort={sortKey === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined}
                >
                  {col.sortable ? (
                    <button
                      onClick={() => handleSort(col.key)}
                      className="flex items-center gap-1 hover:text-gray-700"
                    >
                      {col.header}
                      {sortKey === col.key ? (
                        sortDir === 'asc' ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />
                      ) : (
                        <ChevronsUpDown className="h-3.5 w-3.5 text-gray-300" />
                      )}
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr
                key={keyExtractor(item)}
                onClick={() => onRowClick?.(item)}
                className={clsx(
                  'border-b border-gray-100 hover:bg-gray-50',
                  onRowClick && 'cursor-pointer'
                )}
              >
                {columns.map((col) => (
                  <td key={col.key} className="py-3 px-3">
                    {col.render(item)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pagination && (
        <div className="mt-4">
          <Pagination {...pagination} />
        </div>
      )}
    </div>
  );
}
```

#### ChartWidget

```typescript
// src/components/domain/ChartWidget.tsx
import { Card, CardHeader } from '../ui/Card';
import { Skeleton } from '../ui/Skeleton';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

type ChartType = 'line' | 'bar' | 'pie';

interface ChartWidgetProps {
  title: string;
  subtitle?: string;
  type: ChartType;
  data: Record<string, any>[];
  dataKey: string;
  xKey?: string;
  yKey?: string;
  colors?: string[];
  loading?: boolean;
  height?: number;
  className?: string;
}

const defaultColors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export function ChartWidget({
  title,
  subtitle,
  type,
  data,
  dataKey,
  xKey = 'name',
  yKey = 'value',
  colors = defaultColors,
  loading,
  height = 250,
  className,
}: ChartWidgetProps) {
  return (
    <Card className={className}>
      <CardHeader title={title} subtitle={subtitle} />
      {loading ? (
        <Skeleton style={{ height }} />
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          {type === 'line' ? (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey={dataKey} stroke={colors[0]} strokeWidth={2} dot={false} />
            </LineChart>
          ) : type === 'bar' ? (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey={dataKey} fill={colors[0]} radius={[4, 4, 0, 0]} />
            </BarChart>
          ) : (
            <PieChart>
              <Pie data={data} dataKey={yKey} nameKey={xKey} cx="50%" cy="50%" outerRadius={80} label>
                {data.map((_, i) => (
                  <Cell key={i} fill={colors[i % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          )}
        </ResponsiveContainer>
      )}
    </Card>
  );
}
```

#### AlertToast

```typescript
// src/components/domain/AlertToast.tsx
import { clsx } from 'clsx';
import { SeverityIndicator } from './SeverityIndicator';
import { AlertTriangle, X } from 'lucide-react';

interface Alert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

interface AlertToastProps {
  alert: Alert;
  onDismiss: (id: string) => void;
  onAcknowledge: (id: string) => void;
  onClick: (alert: Alert) => void;
  className?: string;
}

export function AlertToast({ alert, onDismiss, onAcknowledge, onClick, className }: AlertToastProps) {
  return (
    <div
      onClick={() => onClick(alert)}
      className={clsx(
        'flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-shadow hover:shadow-md',
        alert.severity === 'critical' && 'bg-red-50 border-red-200',
        alert.severity === 'high' && 'bg-orange-50 border-orange-200',
        alert.severity === 'medium' && 'bg-yellow-50 border-yellow-200',
        alert.severity === 'low' && 'bg-green-50 border-green-200',
        className
      )}
    >
      <AlertTriangle className="h-5 w-5 mt-0.5 flex-shrink-0 text-gray-600" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <SeverityIndicator severity={alert.severity} />
          <span className="text-xs text-gray-500">
            {new Date(alert.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <h4 className="text-sm font-medium text-gray-900">{alert.title}</h4>
        <p className="text-sm text-gray-600 mt-0.5 line-clamp-2">{alert.message}</p>
      </div>
      <div className="flex items-center gap-1">
        {!alert.acknowledged && (
          <button
            onClick={(e) => { e.stopPropagation(); onAcknowledge(alert.id); }}
            className="px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-100 rounded"
          >
            Ack
          </button>
        )}
        <button
          onClick={(e) => { e.stopPropagation(); onDismiss(alert.id); }}
          className="p-1 text-gray-400 hover:text-gray-600"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
```

#### FindingCard

```typescript
// src/components/domain/FindingCard.tsx
import { clsx } from 'clsx';
import { SeverityIndicator } from './SeverityIndicator';
import { StatusBadge } from './StatusBadge';
import { Badge } from '../ui/Badge';

interface Finding {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  control: string;
  framework: string;
  identifiedAt: string;
  dueDate: string;
  assignee: string;
}

interface FindingCardProps {
  finding: Finding;
  onClick?: (finding: Finding) => void;
  className?: string;
}

export function FindingCard({ finding, onClick, className }: FindingCardProps) {
  return (
    <div
      onClick={() => onClick?.(finding)}
      className={clsx(
        'p-4 bg-white rounded-lg border border-gray-200',
        onClick && 'cursor-pointer hover:shadow-md transition-shadow',
        className
      )}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <SeverityIndicator severity={finding.severity} />
          <StatusBadge status={finding.status === 'open' ? 'fail' : finding.status === 'in_progress' ? 'pending' : 'pass'} />
        </div>
        <span className="text-xs text-gray-500 font-mono">{finding.id}</span>
      </div>
      <h4 className="text-sm font-medium text-gray-900 mb-1">{finding.title}</h4>
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <Badge variant="outline">{finding.control}</Badge>
        <span>{finding.framework}</span>
      </div>
      <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
        <span>Assigned: {finding.assignee}</span>
        <span>Due: {new Date(finding.dueDate).toLocaleDateString()}</span>
      </div>
    </div>
  );
}
```

#### AssessmentProgress

```typescript
// src/components/domain/AssessmentProgress.tsx
import { ProgressBar } from '../ui/ProgressBar';
import { clsx } from 'clsx';

interface Assessment {
  id: string;
  name: string;
  framework: string;
  progress: number;
  status: 'active' | 'completed' | 'planned';
  dueDate?: string;
}

interface AssessmentProgressProps {
  assessments: Assessment[];
  onAssessmentClick?: (assessment: Assessment) => void;
  className?: string;
}

export function AssessmentProgress({ assessments, onAssessmentClick, className }: AssessmentProgressProps) {
  return (
    <div className={clsx('space-y-3', className)}>
      {assessments.map((assessment) => (
        <div
          key={assessment.id}
          onClick={() => onAssessmentClick?.(assessment)}
          className={clsx('space-y-1', onAssessmentClick && 'cursor-pointer')}
        >
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-gray-900">{assessment.name}</span>
              <span className="text-xs text-gray-500 ml-2">{assessment.framework}</span>
            </div>
            <span className="text-xs text-gray-500">
              {assessment.dueDate && `Due: ${new Date(assessment.dueDate).toLocaleDateString()}`}
            </span>
          </div>
          <ProgressBar value={assessment.progress} size="sm" showValue />
        </div>
      ))}
    </div>
  );
}
```

#### ComplianceHeatmap

```typescript
// src/components/domain/ComplianceHeatmap.tsx
import { clsx } from 'clsx';

interface HeatmapCell {
  framework: string;
  control: string;
  status: 'pass' | 'fail' | 'gap' | 'pending' | 'not_assessed';
}

interface ComplianceHeatmapProps {
  data: HeatmapCell[];
  frameworks: string[];
  controls: string[];
  onCellClick?: (cell: HeatmapCell) => void;
  className?: string;
}

const statusColors: Record<string, string> = {
  pass: 'bg-green-500',
  fail: 'bg-red-500',
  gap: 'bg-yellow-500',
  pending: 'bg-blue-500',
  not_assessed: 'bg-gray-200',
};

export function ComplianceHeatmap({ data, frameworks, controls, onCellClick, className }: ComplianceHeatmapProps) {
  const getCellStatus = (framework: string, control: string) => {
    return data.find((d) => d.framework === framework && d.control === control)?.status || 'not_assessed';
  };

  return (
    <div className={clsx('overflow-x-auto', className)}>
      <table className="text-xs">
        <thead>
          <tr>
            <th className="text-left py-1 px-2 font-medium text-gray-500">Control</th>
            {frameworks.map((fw) => (
              <th key={fw} className="py-1 px-2 font-medium text-gray-500 text-center">
                {fw}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {controls.map((control) => (
            <tr key={control}>
              <td className="py-1 px-2 font-mono text-gray-700">{control}</td>
              {frameworks.map((fw) => {
                const status = getCellStatus(fw, control);
                return (
                  <td key={`${fw}-${control}`} className="py-1 px-2 text-center">
                    <div
                      onClick={() => onCellClick?.({ framework: fw, control, status })}
                      className={clsx(
                        'w-6 h-6 rounded mx-auto',
                        statusColors[status],
                        onCellClick && 'cursor-pointer hover:ring-2 hover:ring-blue-300'
                      )}
                      title={`${fw} / ${control}: ${status}`}
                    />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

#### AuditTrailList

```typescript
// src/components/domain/AuditTrailList.tsx
import { clsx } from 'clsx';
import { CheckCircle, XCircle } from 'lucide-react';

interface AuditEvent {
  id: string;
  eventType: string;
  actor: string;
  resource: string;
  timestamp: string;
  outcome: string;
  integrityValid: boolean;
}

interface AuditTrailListProps {
  events: AuditEvent[];
  onEventClick?: (event: AuditEvent) => void;
  className?: string;
}

export function AuditTrailList({ events, onEventClick, className }: AuditTrailListProps) {
  return (
    <div className={clsx('space-y-2', className)}>
      {events.map((event) => (
        <div
          key={event.id}
          onClick={() => onEventClick?.(event)}
          className={clsx(
            'flex items-center gap-3 p-3 rounded-lg border border-gray-200 bg-white',
            onEventClick && 'cursor-pointer hover:bg-gray-50'
          )}
        >
          {event.integrityValid ? (
            <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
          ) : (
            <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900">{event.eventType}</span>
              <span className="text-xs text-gray-500">{event.actor}</span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              {event.resource} · {event.outcome}
            </p>
          </div>
          <span className="text-xs text-gray-400 flex-shrink-0">
            {new Date(event.timestamp).toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
}
```

#### PolicyTestConsole

```typescript
// src/components/domain/PolicyTestConsole.tsx
import { useState } from 'react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { VerificationLevel } from './VerificationLevel';
import { Play } from 'lucide-react';

interface TestResult {
  decision: 'ALLOW' | 'DENY' | 'REQUIRE_APPROVAL' | 'QUARANTINE';
  matchedRules: string[];
  reason: string;
  evaluationTimeMs: number;
  policyVersion: string;
}

interface PolicyTestConsoleProps {
  policyId: string;
  policyVersion: string;
  onRunTest: (input: string) => Promise<TestResult>;
  className?: string;
}

export function PolicyTestConsole({ policyId, policyVersion, onRunTest, className }: PolicyTestConsoleProps) {
  const [testInput, setTestInput] = useState('{\n  "action": {\n    "type": "export",\n    "data": { "contains_pii": true }\n  },\n  "agent_id": "prod-cs-bot",\n  "resource": { "type": "database" }\n}');
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRunTest = async () => {
    setLoading(true);
    try {
      const testResult = await onRunTest(testInput);
      setResult(testResult);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={className}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Test Input (JSON)">
          <textarea
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
            className="w-full h-64 p-3 font-mono text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            spellCheck={false}
            aria-label="Test input JSON"
          />
          <div className="mt-3">
            <Button onClick={handleRunTest} loading={loading} icon={<Play className="h-4 w-4" />}>
              Run Test
            </Button>
          </div>
        </Card>
        <Card title="Result">
          {result ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">Decision:</span>
                <span className={`px-2 py-0.5 rounded text-sm font-bold ${
                  result.decision === 'ALLOW' ? 'bg-green-100 text-green-700' :
                  result.decision === 'DENY' ? 'bg-red-100 text-red-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>
                  {result.decision}
                </span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-700">Matched Rules:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {result.matchedRules.map((rule) => (
                    <span key={rule} className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-mono">
                      {rule}
                    </span>
                  ))}
                </div>
              </div>
              {result.reason && (
                <div>
                  <span className="text-sm font-medium text-gray-700">Reason:</span>
                  <p className="text-sm text-gray-600 mt-0.5">{result.reason}</p>
                </div>
              )}
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Evaluation: {result.evaluationTimeMs}ms</span>
                <span>Policy: {result.policyVersion}</span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Run a test to see results</p>
          )}
        </Card>
      </div>
    </div>
  );
}
```

#### PolicyEditor

```typescript
// src/components/domain/PolicyEditor.tsx
import { useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Card } from '../ui/Card';
import { Tabs } from '../ui/Tabs';
import { Play, Save, History } from 'lucide-react';

interface PolicyRule {
  name: string;
  condition: string;
  action: string;
  priority: number;
  description: string;
}

interface PolicyEditorProps {
  initialValue?: string;
  onSave: (policy: string) => void;
  onValidate: (policy: string) => Promise<{ valid: boolean; errors: string[] }>;
  onTest: (policy: string) => void;
  className?: string;
}

export function PolicyEditor({ initialValue = '', onSave, onValidate, onTest, className }: PolicyEditorProps) {
  const [policyYaml, setPolicyYaml] = useState(initialValue);
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; errors: string[] } | null>(null);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(policyYaml);
    } finally {
      setSaving(false);
    }
  };

  const handleValidate = async () => {
    setValidating(true);
    try {
      const result = await onValidate(policyYaml);
      setValidationResult(result);
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className={className}>
      <div className="flex items-center gap-2 mb-4">
        <Button onClick={handleSave} loading={saving} icon={<Save className="h-4 w-4" />}>
          Save
        </Button>
        <Button variant="outline" onClick={handleValidate} loading={validating}>
          Validate
        </Button>
        <Button variant="outline" onClick={() => onTest(policyYaml)} icon={<Play className="h-4 w-4" />}>
          Test Policy
        </Button>
      </div>

      {validationResult && (
        <div className={`mb-4 p-3 rounded-lg ${validationResult.valid ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          {validationResult.valid ? (
            <p className="text-sm text-green-700">Policy is valid</p>
          ) : (
            <ul className="text-sm text-red-700 list-disc list-inside">
              {validationResult.errors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <Card>
        <textarea
          value={policyYaml}
          onChange={(e) => setPolicyYaml(e.target.value)}
          className="w-full h-[500px] p-4 font-mono text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          spellCheck={false}
          aria-label="Policy YAML editor"
          placeholder="apiVersion: governance.toolkit/v1&#10;name: my-policy&#10;default_action: deny&#10;rules:&#10;  - name: ..."
        />
      </Card>
    </div>
  );
}
```

### 2.4 Layout Components

#### AppShell

```typescript
// src/components/layout/AppShell.tsx
import { type ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
```

#### Sidebar

```typescript
// src/components/layout/Sidebar.tsx
import { NavLink } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  LayoutDashboard, Shield, FileText, ClipboardList,
  Map, Bell, Bot, History, Settings
} from 'lucide-react';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/policies', icon: Shield, label: 'Policies' },
  { to: '/evidence', icon: FileText, label: 'Evidence' },
  { to: '/assessments', icon: ClipboardList, label: 'Assessments' },
  { to: '/compliance', icon: Map, label: 'Compliance' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/audit', icon: History, label: 'Audit Trail' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-gray-200">
        <Shield className="h-6 w-6 text-blue-600 mr-2" />
        <span className="text-lg font-bold text-gray-900">GRC_Claw</span>
      </div>
      <nav className="flex-1 py-4 px-3 space-y-1" aria-label="Main navigation">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
```

#### Header

```typescript
// src/components/layout/Header.tsx
import { Bell, Search, User, ChevronDown } from 'lucide-react';
import { Avatar } from '../ui/Avatar';
import { Dropdown } from '../ui/Dropdown';
import { useAuthStore } from '../../store/authStore';

export function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="search"
            placeholder="Search policies, evidence, agents..."
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Global search"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button className="relative p-2 text-gray-400 hover:text-gray-600" aria-label="Notifications">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        <Dropdown
          trigger={
            <button className="flex items-center gap-2 hover:bg-gray-50 rounded-lg px-2 py-1">
              <Avatar name={user?.name || 'User'} size="sm" />
              <span className="text-sm font-medium text-gray-700">{user?.name}</span>
              <ChevronDown className="h-4 w-4 text-gray-400" />
            </button>
          }
          items={[
            { label: 'Profile', onClick: () => {} },
            { label: 'Settings', onClick: () => {} },
            { label: 'Sign out', onClick: logout, danger: true },
          ]}
        />
      </div>
    </header>
  );
}
```

---

## 3. Dashboard Implementations

### 3.1 Executive Dashboard

```typescript
// src/features/dashboard/ExecutiveDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader } from '../../components/ui/Card';
import { ComplianceScoreBar } from '../../components/domain/ComplianceScoreBar';
import { TrustScoreGauge } from '../../components/domain/TrustScoreGauge';
import { ChartWidget } from '../../components/domain/ChartWidget';
import { FindingCard } from '../../components/domain/FindingCard';
import { ProgressBar } from '../../components/ui/ProgressBar';
import { Skeleton } from '../../components/ui/Skeleton';
import { api } from '../../api/client';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export function ExecutiveDashboard() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ['executive-overview'],
    queryFn: () => api.get('/v1.0/compliance/posture?target_type=organization&target_id=all'),
  });

  const { data: riskTrend } = useQuery({
    queryKey: ['risk-trend'],
    queryFn: () => api.get('/v1.0/compliance/posture?target_type=organization&target_id=all&trend=90d'),
  });

  const { data: findings } = useQuery({
    queryKey: ['top-findings'],
    queryFn: () => api.get('/v1.0/assessments?status=in_progress&limit=5'),
  });

  if (isLoading) {
    return <ExecutiveDashboardSkeleton />;
  }

  const kpis = [
    { title: 'Compliance Score', value: '87/100', change: '+3 pts', trend: 'up' },
    { title: 'Risk Posture', value: 'Medium', change: 'Low', trend: 'down' },
    { title: 'Audit Readiness', value: '92%', change: 'Ready', trend: 'up' },
    { title: 'Agent Coverage', value: '45/50', change: '90%', trend: 'up' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Executive Dashboard</h1>
        <div className="flex items-center gap-2">
          <select className="text-sm border border-gray-300 rounded-lg px-3 py-2">
            <option>Last 90 days</option>
            <option>Last 30 days</option>
            <option>Last 7 days</option>
            <option>Last 12 months</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <Card key={kpi.title}>
            <p className="text-sm text-gray-500 mb-1">{kpi.title}</p>
            <div className="flex items-end justify-between">
              <span className="text-2xl font-bold text-gray-900">{kpi.value}</span>
              <span className={`flex items-center gap-1 text-sm font-medium ${
                kpi.trend === 'up' ? 'text-green-600' : kpi.trend === 'down' ? 'text-red-600' : 'text-gray-500'
              }`}>
                {kpi.trend === 'up' && <TrendingUp className="h-4 w-4" />}
                {kpi.trend === 'down' && <TrendingDown className="h-4 w-4" />}
                {kpi.change}
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartWidget
          title="Compliance Score by Framework"
          type="bar"
          data={[
            { name: 'SOC 2', value: 92 },
            { name: 'ISO 27001', value: 85 },
            { name: 'NIST AI', value: 78 },
            { name: 'EU AI Act', value: 71 },
            { name: 'HIPAA', value: 95 },
          ]}
          dataKey="value"
          xKey="name"
        />
        <ChartWidget
          title="Risk Trend (90 days)"
          type="line"
          data={riskTrend?.data || []}
          dataKey="score"
          xKey="date"
        />
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Top 5 Open Findings" action={
            <button className="text-sm text-blue-600 hover:text-blue-800">View All</button>
          } />
          <div className="space-y-3">
            {findings?.data?.map((finding: any) => (
              <FindingCard key={finding.id} finding={finding} />
            ))}
          </div>
        </Card>
        <Card>
          <CardHeader title="Upcoming Audit Milestones" />
          <div className="space-y-4">
            {[
              { name: 'SOC 2 Type II', days: 45, readiness: 92 },
              { name: 'ISO 27001 Surveillance', days: 90, readiness: 78 },
              { name: 'EU AI Act Report', days: 120, readiness: 65 },
              { name: 'Internal Audit', days: 30, readiness: 88 },
            ].map((milestone) => (
              <div key={milestone.name} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">{milestone.name}</span>
                  <span className="text-xs text-gray-500">{milestone.days} days</span>
                </div>
                <ProgressBar value={milestone.readiness} size="sm" showValue={false} />
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Trust Distribution */}
      <Card>
        <CardHeader title="Agent Trust Score Distribution" />
        <div className="grid grid-cols-5 gap-4">
          {[
            { grade: 'A (90-100)', count: 12, color: 'bg-green-500' },
            { grade: 'B (80-89)', count: 18, color: 'bg-blue-500' },
            { grade: 'C (70-79)', count: 8, color: 'bg-yellow-500' },
            { grade: 'D (60-69)', count: 4, color: 'bg-orange-500' },
            { grade: 'F (<60)', count: 3, color: 'bg-red-500' },
          ].map((bucket) => (
            <div key={bucket.grade} className="text-center">
              <div className="flex items-end justify-center h-24 gap-1">
                <div
                  className={`w-8 ${bucket.color} rounded-t`}
                  style={{ height: `${(bucket.count / 18) * 100}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">{bucket.grade}</p>
              <p className="text-sm font-semibold text-gray-900">{bucket.count}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function ExecutiveDashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24" variant="rectangular" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Skeleton className="h-64" variant="rectangular" />
        <Skeleton className="h-64" variant="rectangular" />
      </div>
    </div>
  );
}
```

### 3.2 Operational Dashboard

```typescript
// src/features/dashboard/OperationalDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader } from '../../components/ui/Card';
import { AlertToast } from '../../components/domain/AlertToast';
import { FindingCard } from '../../components/domain/FindingCard';
import { AssessmentProgress } from '../../components/domain/AssessmentProgress';
import { VerificationLevel } from '../../components/domain/VerificationLevel';
import { SeverityIndicator } from '../../components/domain/SeverityIndicator';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { api } from '../../api/client';
import { Plus, Settings, Check } from 'lucide-react';

export function OperationalDashboard() {
  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => api.get('/v1.0/alerts?status=active&limit=10'),
    refetchInterval: 30000,
  });

  const { data: findings } = useQuery({
    queryKey: ['open-findings'],
    queryFn: () => api.get('/v1.0/assessments?status=in_progress'),
  });

  const { data: evidence } = useQuery({
    queryKey: ['evidence-status'],
    queryFn: () => api.get('/v1.0/evidence?limit=1'),
  });

  const { data: assessments } = useQuery({
    queryKey: ['active-assessments'],
    queryFn: () => api.get('/v1.0/assessments?status=in_progress'),
  });

  const { data: agents } = useQuery({
    queryKey: ['agent-status'],
    queryFn: () => api.get('/v1.0/agents?limit=50'),
  });

  const evidenceStats = [
    { level: 'L0' as const, label: 'Unverified', count: 12, action: 'Review' },
    { level: 'L1' as const, label: 'Schema-valid', count: 45 },
    { level: 'L2' as const, label: 'Integrity', count: 120 },
    { level: 'L3' as const, label: 'Cross-val', count: 20 },
    { level: 'L4' as const, label: 'Attested', count: 6, action: 'Attest' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Operational Dashboard</h1>
        <div className="flex items-center gap-2">
          <Button variant="outline" icon={<Plus className="h-4 w-4" />}>New Finding</Button>
        </div>
      </div>

      {/* Alerts */}
      <Card>
        <CardHeader
          title="Alerts & Notifications"
          action={
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" icon={<Check className="h-3.5 w-3.5" />}>
                Mark All Read
              </Button>
              <Button variant="ghost" size="sm" icon={<Settings className="h-3.5 w-3.5" />} />
            </div>
          }
        />
        <div className="space-y-3">
          {alertsLoading ? (
            <Skeleton className="h-20" variant="rectangular" />
          ) : (
            alerts?.data?.map((alert: any) => (
              <AlertToast
                key={alert.id}
                alert={alert}
                onDismiss={() => {}}
                onAcknowledge={() => {}}
                onClick={() => {}}
              />
            ))
          )}
        </div>
      </Card>

      {/* Findings & Evidence Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Open Findings" action={
            <Button variant="ghost" size="sm" icon={<Plus className="h-3.5 w-3.5" />}>
              Create Finding
            </Button>
          } />
          <div className="space-y-3">
            {(['critical', 'high', 'medium', 'low'] as const).map((severity) => (
              <div key={severity} className="flex items-center justify-between">
                <SeverityIndicator severity={severity} />
                <span className="text-sm font-medium text-gray-900">
                  {findings?.data?.filter((f: any) => f.severity === severity).length || 0}
                </span>
                <Button variant="ghost" size="sm">View</Button>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title="Evidence Status" />
          <div className="space-y-3">
            {evidenceStats.map((stat) => (
              <div key={stat.level} className="flex items-center justify-between">
                <VerificationLevel level={stat.level} />
                <span className="text-sm font-medium text-gray-900">{stat.count}</span>
                {stat.action && (
                  <Button variant="ghost" size="sm">{stat.action}</Button>
                )}
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Assessments & Agent Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Active Assessments" action={
            <Button variant="ghost" size="sm">View All</Button>
          } />
          <AssessmentProgress
            assessments={assessments?.data?.map((a: any) => ({
              id: a.id,
              name: a.title,
              framework: a.methodology,
              progress: a.score || 0,
              status: a.status,
              dueDate: a.nextAssessmentAt,
            })) || []}
          />
        </Card>

        <Card>
          <CardHeader title="Agent Governance Status" action={
            <Button variant="ghost" size="sm">View Registry</Button>
          } />
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Governed</span>
              <span className="text-sm font-medium text-green-600">42 agents</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Ungoverned</span>
              <span className="text-sm font-medium text-red-600">5 agents</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Quarantined</span>
              <span className="text-sm font-medium text-orange-600">2 agents</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Pending</span>
              <span className="text-sm font-medium text-yellow-600">1 agent</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader title="Recent Governance Activity" />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-3 font-medium text-gray-500">Time</th>
                <th className="text-left py-2 px-3 font-medium text-gray-500">Actor</th>
                <th className="text-left py-2 px-3 font-medium text-gray-500">Action</th>
                <th className="text-left py-2 px-3 font-medium text-gray-500">Target</th>
                <th className="text-left py-2 px-3 font-medium text-gray-500">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {[
                { time: '09:42', actor: 'agent-sent', action: 'Policy eval', target: 'prod-bot', outcome: 'ALLOW' },
                { time: '09:38', actor: 'analyst-jd', action: 'Evidence upl', target: 'AC-2.1', outcome: 'L2 verified' },
                { time: '09:15', actor: 'system', action: 'Scan complete', target: 'AU-6', outcome: '3 findings' },
                { time: '08:50', actor: 'auditor-ex', action: 'Attestation', target: 'CC6.1', outcome: 'L4 attested' },
                { time: '08:30', actor: 'agent-sent', action: 'Tool call', target: 'prod-bot', outcome: 'DENIED' },
              ].map((event, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-2 px-3 text-gray-500">{event.time}</td>
                  <td className="py-2 px-3 font-mono text-xs">{event.actor}</td>
                  <td className="py-2 px-3">{event.action}</td>
                  <td className="py-2 px-3">{event.target}</td>
                  <td className="py-2 px-3">
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                      event.outcome === 'ALLOW' ? 'bg-green-100 text-green-700' :
                      event.outcome === 'DENIED' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {event.outcome}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
```

### 3.3 Technical Dashboard

```typescript
// src/features/dashboard/TechnicalDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader } from '../../components/ui/Card';
import { AgentCard } from '../../components/domain/AgentCard';
import { TrustScoreGauge } from '../../components/domain/TrustScoreGauge';
import { StatusBadge } from '../../components/domain/StatusBadge';
import { DataTable } from '../../components/domain/DataTable';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { api } from '../../api/client';
import { Plus, Upload, Download } from 'lucide-react';

export function TechnicalDashboard() {
  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get('/v1.0/agents?limit=50'),
  });

  const { data: enforcement } = useQuery({
    queryKey: ['enforcement-stats'],
    queryFn: () => api.get('/v1.0/enforcement/decisions?limit=1&date_from=2026-10-01'),
  });

  const { data: controls } = useQuery({
    queryKey: ['control-status'],
    queryFn: () => api.get('/v1.0/compliance/posture?target_type=organization&target_id=all'),
  });

  const enforcementStats = [
    { label: 'ALLOW', count: 1247, color: 'text-green-600' },
    { label: 'DENY', count: 12, color: 'text-red-600' },
    { label: 'REQUIRE_APPROVAL', count: 3, color: 'text-yellow-600' },
    { label: 'QUARANTINE', count: 1, color: 'text-orange-600' },
    { label: 'TRANSFORM', count: 0, color: 'text-gray-500' },
  ];

  const controlColumns = [
    { key: 'id', header: 'Control ID', render: (c: any) => <span className="font-mono text-xs">{c.controlKey}</span> },
    { key: 'framework', header: 'Framework', render: (c: any) => c.framework?.name },
    { key: 'status', header: 'Status', render: (c: any) => <StatusBadge status={c.status === 'COMPLIANT' ? 'pass' : c.status === 'NON_COMPLIANT' ? 'fail' : 'gap'} /> },
    { key: 'evidence', header: 'Evidence', render: (c: any) => `${c.evidenceCount || 0} items` },
    { key: 'lastCheck', header: 'Last Check', render: (c: any) => c.lastAssessed ? new Date(c.lastAssessed).toLocaleDateString() : '—' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Technical Dashboard</h1>
        <div className="flex items-center gap-2">
          <select className="text-sm border border-gray-300 rounded-lg px-3 py-2">
            <option>Production</option>
            <option>Staging</option>
            <option>Development</option>
          </select>
        </div>
      </div>

      {/* Agent Registry */}
      <Card>
        <CardHeader
          title="Agent Registry"
          action={
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" icon={<Plus className="h-3.5 w-3.5" />}>
                Register Agent
              </Button>
              <Button variant="outline" size="sm" icon={<Upload className="h-3.5 w-3.5" />}>
                Bulk Import
              </Button>
              <Button variant="outline" size="sm" icon={<Download className="h-3.5 w-3.5" />}>
                Export
              </Button>
            </div>
          }
        />
        {agentsLoading ? (
          <Skeleton className="h-48" variant="rectangular" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents?.data?.slice(0, 6).map((agent: any) => (
              <AgentCard
                key={agent.id}
                agent={{
                  id: agent.id,
                  name: agent.name,
                  trustScore: agent.trustScore?.value || 0,
                  status: agent.lifecycleStage === 'active' ? 'active' : agent.lifecycleStage === 'quarantined' ? 'quarantined' : 'pending',
                  policyVersion: 'v2.3.1',
                  lastEvaluated: agent.trustScore?.lastEvaluated || agent.updatedAt,
                }}
              />
            ))}
          </div>
        )}
      </Card>

      {/* Enforcement & Policy Log */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Runtime Enforcement" action={
            <Button variant="ghost" size="sm">View Detail</Button>
          } />
          <div className="space-y-3">
            {enforcementStats.map((stat) => (
              <div key={stat.label} className="flex items-center justify-between">
                <span className="text-sm text-gray-700">{stat.label}</span>
                <span className={`text-lg font-bold ${stat.color}`}>{stat.count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader title="Policy Evaluation Log" action={
            <Button variant="ghost" size="sm">View Full Log</Button>
          } />
          <div className="space-y-3">
            {[
              { time: '09:42', agent: 'prod-cs-bot', decision: 'ALLOW', rule: 'allow-read-tickets' },
              { time: '09:38', agent: 'prod-sales', decision: 'DENY', rule: 'block-refund-over-500' },
              { time: '09:15', agent: 'prod-ml', decision: 'DENY', rule: 'block-external-network' },
            ].map((log, i) => (
              <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-gray-50">
                <span className="text-xs text-gray-500 w-12">{log.time}</span>
                <span className="text-sm font-medium text-gray-900 flex-1">{log.agent}</span>
                <span className={`px-1.5 py-0.5 rounded text-xs font-bold ${
                  log.decision === 'ALLOW' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {log.decision}
                </span>
                <span className="text-xs text-gray-500 font-mono">{log.rule}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Control Implementation Status */}
      <Card>
        <CardHeader title="Control Implementation Status" action={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">Run Assessment</Button>
            <Button variant="outline" size="sm">Export</Button>
          </div>
        } />
        <DataTable
          columns={controlColumns}
          data={controls?.gaps?.slice(0, 10) || []}
          keyExtractor={(item) => item.control?.id || item.controlKey}
        />
      </Card>

      {/* Trust Score & Policy Versions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Trust Score Components" action={
            <Button variant="ghost" size="sm">View Detail</Button>
          } />
          <div className="flex items-center gap-6">
            <TrustScoreGauge score={94} size="lg" />
            <div className="flex-1 space-y-2">
              {[
                { name: 'Identity', score: 20, max: 20 },
                { name: 'Behavior', score: 18, max: 20 },
                { name: 'Compliance', score: 19, max: 20 },
                { name: 'Attestation', score: 17, max: 20 },
                { name: 'Evidence', score: 20, max: 20 },
              ].map((component) => (
                <div key={component.name} className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-20">{component.name}</span>
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${(component.score / component.max) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-700 w-10 text-right">{component.score}/{component.max}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="Policy Bundle Versions" action={
            <Button variant="ghost" size="sm">Create New Version</Button>
          } />
          <div className="space-y-3">
            {[
              { version: 'v2.3.1', agents: 38, status: 'Current' },
              { version: 'v2.3.0', agents: 5, status: 'Deprecated' },
              { version: 'v2.2.0', agents: 2, status: 'Deprecated' },
            ].map((bundle) => (
              <div key={bundle.version} className="flex items-center justify-between p-3 rounded-lg border border-gray-200">
                <div>
                  <span className="text-sm font-medium text-gray-900">{bundle.version}</span>
                  <span className="text-xs text-gray-500 ml-2">{bundle.agents} agents</span>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  bundle.status === 'Current' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {bundle.status}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
```

---

## 4. State Management

### 4.1 Auth Store (Zustand)

```typescript
// src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '../api/client';

interface User {
  id: string;
  name: string;
  email: string;
  roles: string[];
  tenantId: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const response = await api.post('/oauth/token', {
            grant_type: 'password',
            username: email,
            password,
          });
          const { access_token, refresh_token } = response.data;
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

          const userResponse = await api.get('/v1.0/users/me');
          set({
            user: userResponse.data,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        api.defaults.headers.common['Authorization'] = '';
        set({ user: null, token: null, isAuthenticated: false });
      },

      refreshToken: async () => {
        try {
          const response = await api.post('/oauth/token', {
            grant_type: 'refresh_token',
            refresh_token: get().token,
          });
          const { access_token } = response.data;
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          set({ token: access_token });
        } catch {
          get().logout();
        }
      },

      hasPermission: (permission) => {
        const { user } = get();
        if (!user) return false;
        // Check role-based permissions
        const rolePermissions: Record<string, string[]> = {
          admin: ['*'],
          assessor: ['assessments:read', 'assessments:write', 'evidence:read'],
          auditor: ['audit:read', 'evidence:read', 'compliance:read'],
          operator: ['policies:read', 'evidence:read', 'evidence:write', 'enforcement:decide'],
          viewer: ['policies:read', 'evidence:read', 'compliance:read'],
        };
        return user.roles.some((role) =>
          rolePermissions[role]?.includes('*') || rolePermissions[role]?.includes(permission)
        );
      },
    }),
    {
      name: 'grc-auth',
      partialize: (state) => ({ token: state.token, user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
```

### 4.2 UI Store

```typescript
// src/store/uiStore.ts
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toasts: Array<{ id: string; type: string; message: string }>;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  addToast: (toast: { id: string; type: string; message: string }) => void;
  removeToast: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  toasts: [],
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
  addToast: (toast) => set((s) => ({ toasts: [...s.toasts, toast] })),
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
```

### 4.3 Filter Store

```typescript
// src/store/filterStore.ts
import { create } from 'zustand';

interface FilterState {
  timeRange: string;
  framework: string;
  environment: string;
  status: string;
  setTimeRange: (range: string) => void;
  setFramework: (framework: string) => void;
  setEnvironment: (env: string) => void;
  setStatus: (status: string) => void;
  resetFilters: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  timeRange: '90d',
  framework: 'all',
  environment: 'all',
  status: 'all',
  setTimeRange: (timeRange) => set({ timeRange }),
  setFramework: (framework) => set({ framework }),
  setEnvironment: (environment) => set({ environment }),
  setStatus: (status) => set({ status }),
  resetFilters: () => set({ timeRange: '90d', framework: 'all', environment: 'all', status: 'all' }),
}));
```

### 4.4 Notification Store

```typescript
// src/store/notificationStore.ts
import { create } from 'zustand';

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  timestamp: string;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, 'id' | 'read' | 'timestamp'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
  addNotification: (notification) =>
    set((s) => ({
      notifications: [
        {
          ...notification,
          id: crypto.randomUUID(),
          read: false,
          timestamp: new Date().toISOString(),
        },
        ...s.notifications,
      ],
      unreadCount: s.unreadCount + 1,
    })),
  markAsRead: (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
      unreadCount: Math.max(0, s.unreadCount - 1),
    })),
  markAllAsRead: () =>
    set((s) => ({
      notifications: s.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),
  clearAll: () => set({ notifications: [], unreadCount: 0 }),
}));
```

---

## 5. API Client Implementation

### 5.1 Base Client

```typescript
// src/api/client.ts
import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/authStore';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.grc-claw.io';

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 - try refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        await useAuthStore.getState().refreshToken();
        const token = useAuthStore.getState().token;
        if (token) {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }
      } catch {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }

    // Handle 429 - rate limit
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'] || 30;
      // Could implement exponential backoff here
      console.warn(`Rate limited. Retry after ${retryAfter}s`);
    }

    // Normalize error
    const apiError = {
      status: error.response?.status || 0,
      code: (error.response?.data as any)?.code || 'UNKNOWN_ERROR',
      message: (error.response?.data as any)?.detail || error.message,
      errors: (error.response?.data as any)?.errors || [],
    };

    return Promise.reject(apiError);
  }
);
```

### 5.2 Policy API

```typescript
// src/api/policies.ts
import { api } from './client';

export interface Policy {
  id: string;
  policyKey: string;
  name: string;
  description: string;
  category: 'ethics' | 'safety' | 'privacy' | 'fairness';
  status: 'draft' | 'review' | 'active' | 'deprecated' | 'archived';
  version: string;
  frameworkTags: string[];
  cedarPolicy: string;
  regoPolicy?: string;
  ownerId: string;
  agentBindings: string[];
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface PolicyInput {
  policyKey: string;
  name: string;
  description?: string;
  category: string;
  frameworkTags: string[];
  cedarPolicy: string;
  metadata?: Record<string, any>;
}

export const policyApi = {
  list: (params?: { status?: string; category?: string; framework?: string; limit?: number; cursor?: string }) =>
    api.get<{ data: Policy[]; pagination: { next_cursor: string; has_next: boolean; total: number } }>('/v1.0/policies', { params }),

  get: (id: string) => api.get<Policy>(`/v1.0/policies/${id}`),

  create: (input: PolicyInput) => api.post<Policy>('/v1.0/policies', input),

  update: (id: string, input: Partial<PolicyInput>) => api.put<Policy>(`/v1.0/policies/${id}`, input),

  delete: (id: string, force?: boolean) => api.delete(`/v1.0/policies/${id}`, { params: { force } }),

  compile: (id: string) => api.post(`/v1.0/policies/${id}/compile`),

  dryRun: (id: string, testInputs: any[]) => api.post(`/v1.0/policies/${id}/dry-run`, { test_inputs: testInputs }),

  versions: (id: string) => api.get(`/v1.0/policies/${id}/versions`),

  dependencies: (id: string) => api.get(`/v1.0/policies/${id}/dependencies`),
};
```

### 5.3 Evidence API

```typescript
// src/api/evidence.ts
import { api } from './client';

export interface Evidence {
  id: string;
  policyId: string;
  assessmentId?: string;
  source: { type: string; system: string; collectionMethod: string };
  evidenceType: 'artifact' | 'observation' | 'interview' | 'analysis' | 'log';
  content: { format: string; data: string; hash: string };
  context: { environment: string; region?: string; timestamp: string; metadata: Record<string, any> };
  validation: { status: string; validatedBy?: string; validatedAt?: string; confidenceScore: number };
  verificationLevel: 'L0' | 'L1' | 'L2' | 'L3' | 'L4';
  chainOfCustody: Array<{ action: string; actor: string; timestamp: string; hash: string }>;
  retentionClass: string;
  createdAt: string;
  expiresAt?: string;
}

export const evidenceApi = {
  list: (params?: Record<string, any>) =>
    api.get<{ data: Evidence[]; pagination: any }>('/v1.0/evidence', { params }),

  get: (id: string) => api.get<Evidence>(`/v1.0/evidence/${id}`),

  submit: (input: any) => api.post<Evidence>('/v1.0/evidence', input),

  verify: (id: string) => api.post(`/v1.0/evidence/${id}/verify`),

  export: (input: { framework: string; timeRange: { start: string; end: string }; format: string; includeChainOfCustody: boolean }) =>
    api.post('/v1.0/evidence/export', input),

  getExport: (packageId: string) => api.get(`/v1.0/evidence/export/${packageId}`),
};
```

### 5.4 Assessment API

```typescript
// src/api/assessments.ts
import { api } from './client';

export interface Assessment {
  id: string;
  assessmentKey: string;
  title: string;
  description: string;
  assessmentType: 'risk' | 'compliance' | 'maturity' | 'readiness';
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled';
  methodology: string;
  score?: number;
  riskLevel?: string;
  findings: any[];
  createdAt: string;
  updatedAt: string;
}

export const assessmentApi = {
  list: (params?: Record<string, any>) =>
    api.get<{ data: Assessment[]; pagination: any }>('/v1.0/assessments', { params }),

  get: (id: string) => api.get<Assessment>(`/v1.0/assessments/${id}`),

  create: (input: any) => api.post<Assessment>('/v1.0/assessments', input),

  update: (id: string, input: any) => api.put<Assessment>(`/v1.0/assessments/${id}`, input),

  addFinding: (id: string, input: any) => api.post(`/v1.0/assessments/${id}/findings`, input),

  generateReport: (id: string, format: string) =>
    api.post(`/v1.0/assessments/${id}/report`, { format, include_evidence: true }),
};
```

### 5.5 Compliance API

```typescript
// src/api/compliance.ts
import { api } from './client';

export const complianceApi = {
  frameworks: () => api.get('/v1.0/compliance/frameworks'),

  controls: (frameworkId: string, params?: Record<string, any>) =>
    api.get(`/v1.0/compliance/frameworks/${frameworkId}/controls`, { params }),

  posture: (params: { framework?: string; targetId?: string; targetType?: string }) =>
    api.get('/v1.0/compliance/posture', { params }),

  createMapping: (input: any) => api.post('/v1.0/compliance/mappings', input),

  generateReport: (input: any) => api.post('/v1.0/compliance/reports', input),

  crosswalk: (params: { controlId?: string; framework?: string; targetFramework?: string }) =>
    api.get('/v1.0/compliance/crosswalk', { params }),
};
```

### 5.6 Agent API

```typescript
// src/api/agents.ts
import { api } from './client';

export interface Agent {
  id: string;
  name: string;
  type: string;
  framework: string;
  lifecycleStage: string;
  riskTier: string;
  trustScore: { value: number; grade: string; lastEvaluated: string };
  policyBindings: string[];
  createdAt: string;
  updatedAt: string;
}

export const agentApi = {
  list: (params?: Record<string, any>) =>
    api.get<{ data: Agent[]; pagination: any }>('/v1.0/agents', { params }),

  get: (id: string) => api.get<Agent>(`/v1.0/agents/${id}`),

  register: (input: any) => api.post<Agent>('/v1.0/agents', input),

  update: (id: string, input: any) => api.put<Agent>(`/v1.0/agents/${id}`, input),

  updateTrustScore: (id: string, value: number, grade: string, reason: string) =>
    api.post(`/v1.0/agents/${id}/trust-score`, { value, grade, reason }),

  bindPolicy: (id: string, policyIds: string[]) =>
    api.post(`/v1.0/agents/${id}/policy-bindings`, { policy_ids: policyIds }),
};
```

### 5.7 WebSocket Client

```typescript
// src/api/websocket.ts
import { useAuthStore } from '../store/authStore';

type EventHandler = (data: any) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect() {
    const token = useAuthStore.getState().token;
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'wss://api.grc-claw.io'}/v1.0/graphql`;

    this.ws = new WebSocket(wsUrl, ['graphql-ws']);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.ws?.send(JSON.stringify({
        type: 'connection_init',
        payload: { Authorization: `Bearer ${token}` },
      }));
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private handleMessage(message: any) {
    switch (message.type) {
      case 'connection_ack':
        console.log('WebSocket connected');
        break;
      case 'data':
        const handlers = this.handlers.get(message.payload?.subscription);
        handlers?.forEach((handler) => handler(message.payload.data));
        break;
      case 'error':
        console.error('WebSocket subscription error:', message.payload);
        break;
    }
  }

  subscribe(subscription: string, query: string, variables: Record<string, any>, handler: EventHandler) {
    if (!this.handlers.has(subscription)) {
      this.handlers.set(subscription, new Set());
    }
    this.handlers.get(subscription)!.add(handler);

    this.ws?.send(JSON.stringify({
      type: 'start',
      id: subscription,
      payload: { query, variables },
    }));

    return () => this.unsubscribe(subscription, handler);
  }

  private unsubscribe(subscription: string, handler: EventHandler) {
    this.handlers.get(subscription)?.delete(handler);
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    setTimeout(() => this.connect(), delay);
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}

export const wsClient = new WebSocketClient();
```

---

## 6. Authentication Flow

### 6.1 Login Page

```typescript
// src/features/auth/LoginPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Card } from '../../components/ui/Card';
import { Shield } from 'lucide-react';

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <div className="text-center mb-8">
          <Shield className="h-12 w-12 text-blue-600 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900">GRC_Claw</h1>
          <p className="text-sm text-gray-500 mt-1">Governance, Risk & Compliance</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700" role="alert">
              {error}
            </div>
          )}

          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            placeholder="you@company.com"
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            placeholder="Enter your password"
          />

          <Button type="submit" loading={isLoading} className="w-full">
            Sign In
          </Button>
        </form>

        <div className="mt-6 text-center">
          <a href="/forgot-password" className="text-sm text-blue-600 hover:text-blue-800">
            Forgot password?
          </a>
        </div>
      </Card>
    </div>
  );
}
```

### 6.2 Protected Route

```typescript
// src/features/auth/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Spinner } from '../../components/ui/Spinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermission?: string;
}

export function ProtectedRoute({ children, requiredPermission }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, hasPermission } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
        <p className="text-gray-500">You don't have permission to access this page.</p>
      </div>
    );
  }

  return <>{children}</>;
}
```

### 6.3 Permission Gate

```typescript
// src/features/auth/PermissionGate.tsx
import { useAuthStore } from '../../store/authStore';

interface PermissionGateProps {
  permission: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionGate({ permission, children, fallback = null }: PermissionGateProps) {
  const { hasPermission } = useAuthStore();

  if (!hasPermission(permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
```

### 6.4 Auth Callback (OAuth)

```typescript
// src/features/auth/CallbackPage.tsx
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Spinner } from '../../components/ui/Spinner';

export function CallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuthStore();

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (code) {
      // Exchange code for token
      exchangeCode(code, state);
    }
  }, [searchParams]);

  const exchangeCode = async (code: string, state: string | null) => {
    try {
      const response = await fetch('/oauth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant_type: 'authorization_code',
          code,
          redirect_uri: window.location.origin + '/callback',
        }),
      });

      const data = await response.json();
      // Store token and redirect
      navigate('/dashboard');
    } catch (error) {
      navigate('/login?error=auth_failed');
    }
  };

  return (
    <div className="flex items-center justify-center h-screen">
      <Spinner size="lg" />
    </div>
  );
}
```

---

## 7. Testing Framework

### 7.1 Jest Configuration

```typescript
// jest.config.ts
import type { Config } from 'jest';

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/tests/setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\.tsx?$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        '@babel/preset-typescript',
        ['@babel/preset-react', { runtime: 'automatic' }],
      ],
    }],
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};

export default config;
```

### 7.2 Test Setup

```typescript
// tests/setup.ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as any;

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as any;
```

### 7.3 Test Helpers

```typescript
// src/utils/test-helpers.tsx
import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { type ReactElement } from 'react';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string;
  queryClient?: QueryClient;
}

export function renderWithProviders(
  ui: ReactElement,
  { route = '/', queryClient = createTestQueryClient(), ...options }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...options }),
    queryClient,
  };
}

// Mock data factories
export const createMockPolicy = (overrides = {}) => ({
  id: 'pol-001',
  policyKey: 'AI-ETHICS-001',
  name: 'Data Access Control Policy',
  description: 'Controls agent access to data classifications',
  category: 'privacy',
  status: 'active',
  version: '1.2.0',
  frameworkTags: ['SOC2', 'ISO-27001'],
  cedarPolicy: 'permit(principal, action, resource) when { ... }',
  ownerId: 'user-001',
  agentBindings: ['agent-42'],
  metadata: {},
  createdAt: '2026-10-01T14:30:00Z',
  updatedAt: '2026-10-01T14:30:00Z',
  ...overrides,
});

export const createMockEvidence = (overrides = {}) => ({
  id: 'evd-001',
  policyId: 'pol-001',
  source: { type: 'scan', system: 'aws-config', collectionMethod: 'api-query' },
  evidenceType: 'config',
  content: { format: 'json', data: '{"encryption":"AES-256"}', hash: 'sha256:abc123' },
  context: { environment: 'prod', timestamp: '2026-10-01T14:30:00Z', metadata: {} },
  validation: { status: 'pending', confidenceScore: 0 },
  verificationLevel: 'L0',
  chainOfCustody: [],
  retentionClass: 'standard',
  createdAt: '2026-10-01T14:30:00Z',
  ...overrides,
});

export const createMockAgent = (overrides = {}) => ({
  id: 'agent-42',
  name: 'Data Analyst Agent',
  type: 'agent',
  framework: 'langchain',
  lifecycleStage: 'active',
  riskTier: 'limited',
  trustScore: { value: 85, grade: 'B', lastEvaluated: '2026-10-01T12:00:00Z' },
  policyBindings: ['pol-001'],
  createdAt: '2026-08-01T10:00:00Z',
  updatedAt: '2026-10-01T12:00:00Z',
  ...overrides,
});

export const createMockAssessment = (overrides = {}) => ({
  id: 'asm-001',
  assessmentKey: 'RISK-2026-Q4-001',
  title: 'Q4 2026 AI Risk Assessment',
  description: 'Quarterly risk assessment',
  assessmentType: 'risk',
  status: 'in_progress',
  methodology: 'NIST-AI-RMF',
  score: 78.5,
  riskLevel: 'medium',
  findings: [],
  createdAt: '2026-09-25T10:00:00Z',
  updatedAt: '2026-10-01T14:30:00Z',
  ...overrides,
});
```

### 7.4 Component Tests

```typescript
// tests/unit/components/StatusBadge.test.tsx
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '../../src/components/domain/StatusBadge';

describe('StatusBadge', () => {
  it('renders pass status correctly', () => {
    render(<StatusBadge status="pass" />);
    expect(screen.getByText('Pass')).toBeInTheDocument();
  });

  it('renders fail status correctly', () => {
    render(<StatusBadge status="fail" />);
    expect(screen.getByText('Fail')).toBeInTheDocument();
  });

  it('renders without icon when showIcon is false', () => {
    render(<StatusBadge status="pass" showIcon={false} />);
    expect(screen.getByText('Pass')).toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<StatusBadge status="pass" className="custom-class" />);
    expect(screen.getByText('Pass').parentElement).toHaveClass('custom-class');
  });
});
```

```typescript
// tests/unit/components/TrustScoreGauge.test.tsx
import { render } from '@testing-library/react';
import { TrustScoreGauge } from '../../src/components/domain/TrustScoreGauge';

describe('TrustScoreGauge', () => {
  it('renders with score', () => {
    const { container } = render(<TrustScoreGauge score={85} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('shows grade label', () => {
    render(<TrustScoreGauge score={85} />);
    expect(screen.getByText('Grade B')).toBeInTheDocument();
  });

  it('hides label when showLabel is false', () => {
    render(<TrustScoreGauge score={85} showLabel={false} />);
    expect(screen.queryByText('Grade B')).not.toBeInTheDocument();
  });
});
```

```typescript
// tests/unit/components/DataTable.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { DataTable } from '../../src/components/domain/DataTable';

const mockData = [
  { id: '1', name: 'Item 1', status: 'active' },
  { id: '2', name: 'Item 2', status: 'inactive' },
];

const columns = [
  { key: 'name', header: 'Name', render: (item: any) => item.name },
  { key: 'status', header: 'Status', render: (item: any) => item.status },
];

describe('DataTable', () => {
  it('renders data rows', () => {
    render(<DataTable columns={columns} data={mockData} keyExtractor={(item) => item.id} />);
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  it('shows empty state when no data', () => {
    render(<DataTable columns={columns} data={[]} keyExtractor={(item) => item.id} emptyMessage="No items" />);
    expect(screen.getByText('No items')).toBeInTheDocument();
  });

  it('calls onRowClick when row is clicked', () => {
    const onRowClick = jest.fn();
    render(<DataTable columns={columns} data={mockData} keyExtractor={(item) => item.id} onRowClick={onRowClick} />);
    fireEvent.click(screen.getByText('Item 1'));
    expect(onRowClick).toHaveBeenCalledWith(mockData[0]);
  });

  it('shows loading skeleton when loading', () => {
    render(<DataTable columns={columns} data={[]} keyExtractor={(item) => item.id} loading />);
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });
});
```

### 7.5 Hook Tests

```typescript
// tests/unit/hooks/useAuth.test.tsx
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from '../../src/store/authStore';

describe('useAuthStore', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, token: null, isAuthenticated: false });
  });

  it('starts unauthenticated', () => {
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('hasPermission returns false for unauthenticated user', () => {
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.hasPermission('policies:read')).toBe(false);
  });

  it('hasPermission returns true for admin role', () => {
    useAuthStore.setState({
      user: { id: '1', name: 'Admin', email: 'admin@test.com', roles: ['admin'], tenantId: 'org-1' },
      isAuthenticated: true,
    });
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.hasPermission('policies:write')).toBe(true);
  });

  it('logout clears auth state', () => {
    useAuthStore.setState({
      user: { id: '1', name: 'User', email: 'user@test.com', roles: ['viewer'], tenantId: 'org-1' },
      token: 'token123',
      isAuthenticated: true,
    });
    const { result } = renderHook(() => useAuthStore());
    act(() => result.current.logout());
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });
});
```

### 7.6 Integration Tests

```typescript
// tests/integration/PolicyList.test.tsx
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { renderWithProviders } from '../../src/utils/test-helpers';
import { createMockPolicy } from '../../src/utils/test-helpers';

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Policy List Integration', () => {
  it('renders policy list from API', async () => {
    server.use(
      rest.get('/v1.0/policies', (req, res, ctx) => {
        return res(ctx.json({
          data: [createMockPolicy(), createMockPolicy({ id: 'pol-002', name: 'Second Policy' })],
          pagination: { has_next: false, total: 2 },
        }));
      })
    );

    renderWithProviders(<div>Policy List</div>, { route: '/policies' });

    await waitFor(() => {
      expect(screen.getByText('Data Access Control Policy')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    server.use(
      rest.get('/v1.0/policies', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ detail: 'Internal server error' }));
      })
    );

    renderWithProviders(<div>Policy List</div>, { route: '/policies' });

    await waitFor(() => {
      // Should show error state
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
```

### 7.7 E2E Test Example (Cypress)

```typescript
// tests/e2e/dashboard.cy.ts
describe('Dashboard', () => {
  beforeEach(() => {
    cy.login('admin@test.com', 'password');
    cy.visit('/dashboard');
  });

  it('displays executive dashboard KPIs', () => {
    cy.contains('Compliance Score').should('be.visible');
    cy.contains('Risk Posture').should('be.visible');
    cy.contains('Audit Readiness').should('be.visible');
    cy.contains('Agent Coverage').should('be.visible');
  });

  it('navigates between dashboards', () => {
    cy.contains('Operational').click();
    cy.contains('Open Findings').should('be.visible');
    cy.contains('Evidence Status').should('be.visible');

    cy.contains('Technical').click();
    cy.contains('Agent Registry').should('be.visible');
    cy.contains('Runtime Enforcement').should('be.visible');
  });

  it('filters evidence by verification level', () => {
    cy.visit('/evidence');
    cy.get('[data-testid="verification-filter"]').select('L4');
    cy.get('[data-testid="evidence-row"]').should('have.length.at.least', 1);
  });
});
```

---

## Appendix: Environment Configuration

```bash
# .env.example
VITE_API_BASE_URL=https://api.grc-claw.io
VITE_WS_URL=wss://api.grc-claw.io
VITE_AUTH_URL=https://auth.grc-claw.io
VITE_DEFAULT_LOCALE=en
VITE_ENABLE_MOCK=false
```

---

*End of implementation guide.*</longcat_think>
