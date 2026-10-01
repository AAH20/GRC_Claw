# GRC_Claw UI Specification — Advanced Patterns Deepening

**Version:** 2.0 (Extension of grc-claw-ui-specification.md v1.0)  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**References:** grc-claw-ui-specification.md v1.0, grc-claw-api-spec.md v1.0

---

## 1. Purpose & Scope

This document deepens the GRC_Claw UI specification with six advanced capability areas that transform the platform from a static dashboard into a real-time, adaptive, high-performance governance interface:

1. **Real-time dashboard updates** via WebSocket subscriptions
2. **Advanced data visualization** patterns for complex governance data
3. **Mobile-responsive design** with touch-first interactions
4. **Dark/light theme support** with system-aware switching
5. **Custom dashboard builder** for user-defined views
6. **UI performance optimization** for large-scale governance data

Each section builds on the existing spec's design principles (§2), roles (§3), and component library (§15) while introducing new patterns, components, and interaction models.

---

## 2. Real-Time Dashboard Updates

### 2.1 Architecture Overview

GRC_Claw uses a **WebSocket-first real-time architecture** backed by the GraphQL subscriptions defined in the API spec (§8.2). The system pushes governance events to connected clients the moment they occur, eliminating polling and ensuring sub-second alert delivery.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser Client                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Dashboard   │  │  Alert Feed  │  │  Activity Stream     │  │
│  │  Widgets     │  │  Panel       │  │  (Audit Trail)       │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         └─────────────────┼──────────────────────┘              │
│                           │                                     │
│                  ┌────────▼────────┐                            │
│                  │  WebSocket Mgr  │                            │
│                  │  (Connection,   │                            │
│                  │   Reconnect,    │                            │
│                  │   Heartbeat)    │                            │
│                  └────────┬────────┘                            │
└───────────────────────────┼─────────────────────────────────────┘
                            │ WSS (TLS 1.3)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     API Gateway (Kong/Envoy)                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              GraphQL Subscription Router                  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │   │
│  │  │ Enforcement│ │  Evidence  │ │  Compliance Posture│   │   │
│  │  │  Stream    │ │  Stream    │ │  Stream            │   │   │
│  │  └────────────┘ └────────────┘ └────────────────────┘   │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │   │
│  │  │  Policy    │ │   Agent    │ │  Audit Event       │   │   │
│  │  │  Stream    │ │  Trust     │ │  Stream            │   │   │
│  │  └────────────┘ └────────────┘ └────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 WebSocket Connection Lifecycle

#### 2.2.1 Connection Establishment

```
Client                              Server
  │                                   │
  │──── WSS Handshake ───────────────▶│
  │     (with JWT in subprotocol)     │
  │                                   │
  │◀─── Connection Accepted ──────────│
  │     (connection_ack)              │
  │                                   │
  │──── Subscribe (query) ───────────▶│
  │     subscription_id: "sub-001"    │
  │                                   │
  │◀─── Subscription Confirmed ───────│
  │     (next, subscription_id)       │
  │                                   │
  │◀─── Data Push (event) ────────────│
  │     (next, subscription_id)       │
  │                                   │
  │──── Keep-alive (ping) ───────────▶│  every 30s
  │◀─── Keep-alive (pong) ────────────│  every 30s
  │                                   │
```

**Connection parameters:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| Protocol | `graphql-ws` | WebSocket subprotocol |
| Endpoint | `wss://api.grc-claw.io/v1.0/graphql` | GraphQL WebSocket endpoint |
| Auth | JWT in `Authorization` header | OAuth 2.1 access token |
| Heartbeat | 30s ping/pong | Connection health check |
| Reconnect | Exponential backoff (1s → 30s max) | Automatic reconnection |
| Max reconnect | 10 attempts | Then surface offline indicator |

#### 2.2.2 Subscription Types

Each subscription maps to a GraphQL subscription from the API spec (§8.2):

| Subscription | Event Types | UI Consumer | Priority |
|-------------|-------------|-------------|----------|
| `enforcementDecisions(agentId)` | ALLOW, DENY, REQUIRE_APPROVAL, QUARANTINE, TRANSFORM | Technical dashboard, agent detail | Critical |
| `evidenceCollected(policyId)` | New evidence, verification level changes | Evidence viewer, operational dashboard | High |
| `policyChanged(tenantId)` | Created, updated, status changed, deprecated | Policy list, all dashboards | High |
| `compliancePostureChanged(frameworkId, targetId)` | Score changes, gap detection, control status | Executive dashboard, compliance mapping | High |
| `agentTrustScoreChanged(agentId)` | Score updates, grade changes, component breakdown | Agent registry, technical dashboard | Critical |
| `auditEventCreated` | All audit events | Activity stream, audit trail | Medium |

#### 2.2.3 Event Delivery Guarantees

| Guarantee | Implementation |
|-----------|---------------|
| **Ordering** | Events delivered in causal order per subscription channel |
| **Deduplication** | Client tracks `event_id`; server retries with same ID on redelivery |
| **At-least-once** | Server retries unacknowledged events up to 3 times with backoff |
| **Backpressure** | Client can throttle via `connection_init` `max_in_flight` parameter |
| **Offline queue** | Events queued server-side for 60s during client reconnection |

### 2.3 Real-Time UI Patterns

#### 2.3.1 Live Data Indicators

Every widget that receives real-time updates displays a connection status indicator:

```
┌─────────────────────────────────────────┐
│  Compliance Score          ● Live  2m ago│
│                                         │
│     87/100                              │
│     ▲ 3 pts                             │
│                                         │
│  ─────────────────────────────────────  │
│  Last event: CC6.1 evidence verified    │
│  (ev-001, L4 attested, 09:45:00)        │
└─────────────────────────────────────────┘
```

**Indicator states:**

| State | Visual | Meaning |
|-------|--------|---------|
| **Live** | Green pulse dot (●) | Connected, receiving events |
| **Stale** | Yellow dot (●) | Connected, no events in 60s |
| **Reconnecting** | Orange spinner (◌) | Connection lost, attempting reconnect |
| **Offline** | Red dot (●) | Disconnected, showing cached data |
| **Paused** | Gray dot (●) | User paused real-time updates |

#### 2.3.2 Incremental Widget Updates

Widgets update in-place without full re-render:

```
Before event:
┌──────────────────────┐
│  Open Findings       │
│  Critical:  3        │
│  High:      8        │
│  Medium:   15        │
│  Low:      22        │
└──────────────────────┘

Event received: finding.created (severity: critical)

After event (animated):
┌──────────────────────┐
│  Open Findings       │
│  Critical:  4   ▲    │  ← incremented with green flash
│  High:      8        │
│  Medium:   15        │
│  Low:      22        │
└──────────────────────┘
```

**Animation rules:**
- New value: green background flash (300ms ease-out)
- Increased value: green arrow indicator (▲)
- Decreased value: red arrow indicator (▼)
- No change: no animation
- Respects `prefers-reduced-motion`

#### 2.3.3 Alert Toast Pipeline

Real-time alerts flow through a multi-stage pipeline:

```
Event Source → Severity Filter → Throttling → Deduplication → Toast Queue → Display
```

**Toast display rules:**

| Severity | Display Duration | Position | Sound | Auto-Action |
|----------|-----------------|----------|-------|-------------|
| Critical | Until acknowledged | Top-right, stacked | Yes (if enabled) | Pulse header badge |
| High | 10 seconds | Top-right | No | — |
| Medium | 5 seconds | Top-right | No | — |
| Low | 3 seconds | Bottom-right | No | — |

**Toast component:**

```
┌─────────────────────────────────────────────────┐
│ 🔴 CRITICAL                              [×]    │
│ Agent 'prod-customer-bot' trust score dropped   │
│ to F (45)                                       │
│                                                 │
│ Trigger: Trust score < 60  |  Affected: 1 agent │
│                                                 │
│ [View Agent]  [Acknowledge]  [Escalate]         │
└─────────────────────────────────────────────────┘
```

#### 2.3.4 Activity Stream

The operational dashboard's "Recent Governance Activity" widget (§4.2) becomes a real-time streaming feed:

```
┌─────────────────────────────────────────────────────────────┐
│  RECENT GOVERNANCE ACTIVITY              [Live ●] [Pause]   │
│                                                             │
│  ┌──────────┬────────────┬──────────────┬──────────────┐   │
│  │ Time     │ Actor      │ Action       │ Target       │   │
│  ├──────────┼────────────┼──────────────┼──────────────┤   │
│  │ 09:42:15 │ agent-sent │ Policy eval  │ prod-bot     │   │  ← new row slides in
│  │ 09:38:02 │ analyst-jd │ Evidence upl │ AC-2.1       │   │
│  │ 09:15:44 │ system     │ Scan complete│ AU-6         │   │
│  │ 08:50:12 │ auditor-ex │ Attestation  │ CC6.1        │   │
│  │ 08:30:00 │ agent-sent │ Tool call    │ prod-bot     │   │
│  └──────────┴────────────┴──────────────┴──────────────┘   │
│                                                             │
│  [Load More]  [Filter ▼]  [Export]                         │
└─────────────────────────────────────────────────────────────┘
```

**Streaming behavior:**
- New rows slide in from top with 200ms animation
- Maximum 50 rows in viewport; older rows scroll off
- Pause button freezes the stream (events queue in background)
- Filter applies to both historical and real-time events
- Each row links to full detail view

### 2.4 WebSocket Reconnection Strategy

```
Connection Lost
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Attempt 1    │────▶│ Attempt 2    │────▶│ Attempt 3    │
│ Delay: 1s    │     │ Delay: 2s    │     │ Delay: 4s    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Attempt 4    │────▶│ Attempt 5    │────▶│ Attempt 6    │
│ Delay: 8s    │     │ Delay: 16s   │     │ Delay: 30s   │
└──────────────┘     └──────────────┘     └──────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │ Attempt 7-10 │
                                        │ Delay: 30s   │
                                        │ (max)        │
                                        └──────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │ Offline Mode │
                                        │ Show cached  │
                                        │ data + banner│
                                        └──────────────┘
```

**Reconnection behavior:**
- On reconnect: re-subscribe to all active subscriptions
- Server replays missed events (up to 60s buffer)
- UI shows "Reconnecting… (attempt N)" indicator
- After 10 failed attempts: switch to offline mode with cached data
- Manual "Retry Now" button available in offline mode

### 2.5 Real-Time Permission Scoping

WebSocket subscriptions respect the same RBAC + ABAC model as REST:

| Role | Real-Time Subscriptions Available |
|------|----------------------------------|
| Executive | `compliancePostureChanged`, `agentTrustScoreChanged` (org-wide) |
| GRC Analyst | All subscriptions within assigned frameworks |
| Auditor | `evidenceCollected`, `auditEventCreated`, `compliancePostureChanged` |
| Platform Engineer | `enforcementDecisions`, `agentTrustScoreChanged`, `evidenceCollected` |
| AI/ML Engineer | `enforcementDecisions` (own agents), `agentTrustScoreChanged` (own agents) |
| Policy Owner | `policyChanged`, `evidenceCollected` (own policies) |
| Approver | `policyChanged` (pending approvals), `compliancePostureChanged` |
| Read-Only | `compliancePostureChanged` (org-wide, read-only) |

---

## 3. Advanced Data Visualization Patterns

### 3.1 Visualization Component Library

Building on the base `ChartWidget` component (§15.1), GRC_Claw provides specialized visualization components for governance data:

#### 3.1.1 Compliance Heatmap

A matrix visualization showing control status across frameworks and control families:

```
┌─────────────────────────────────────────────────────────────────┐
│  COMPLIANCE HEATMAP                                             │
│                                                                 │
│              AC    AU    CA    CM    IA    MA    MP    PL    SC  │
│  NIST 800-53 ████  ███░  ████  ██░░  ████  ███░  ██░░  ████  ███░│
│  SOC 2        ████  ███░  ████  ████  ███░  ████  ███░  ████  ████│
│  ISO 27001    ███░  ██░░  ████  ███░  ████  ██░░  ██░░  ███░  ███░│
│  EU AI Act    ██░░  █░░░  ███░  ██░░  ███░  ██░░  █░░░  ██░░  ██░░│
│  HIPAA        ████  ████  ████  ████  ████  ████  ████  ████  ████│
│                                                                 │
│  ████  100%    ███░  75%    ██░░  50%    █░░░  25%    ░░░░  0%    │
│                                                                 │
│  [Filter by Family]  [Filter by Framework]  [Export]            │
└─────────────────────────────────────────────────────────────────┘
```

**Interactions:**
- Hover cell: tooltip with control count, pass rate, gap count
- Click cell: drill to control list filtered by framework + family
- Right-click: context menu (export, view details, run assessment)
- Pinch/scroll: zoom in/out on large matrices

#### 3.1.2 Trust Score Radar Chart

Multi-dimensional trust score visualization for agent comparison:

```
                    Identity
                      ▲
                     /|\
                    / | \
                   /  |  \
                  /   |   \
    Attestation ◄────┼────► Behavior
                  \   |   /
                   \  |  /
                    \ | /
                     \|/
                      ▼
                   Compliance

    ─── prod-cs-bot (A, 94)
    ─── prod-sales (B, 82)
    ─── staging-ml (C, 71)
```

**Dimensions:** Identity, Behavior, Compliance, Attestation, Evidence (5 axes, 0-20 each)

**Interactions:**
- Toggle agents on/off via legend
- Hover axis: show component breakdown
- Click agent: navigate to agent detail
- Time slider: animate trust score evolution

#### 3.1.3 Risk Trend Stream Graph

Stacked area chart showing risk distribution over time:

```
┌─────────────────────────────────────────────────────────────────┐
│  RISK TREND (90 days)                                           │
│                                                                 │
│  High  ───╲                                                     │
│          ───╲────╲                                              │
│  Med  ───────────╲────╲                                         │
│  Low  ───────────────╲────╲────                                │
│                                                                 │
│  Jul 1    Jul 15    Aug 1    Aug 15    Sep 1    Sep 15         │
│                                                                 │
│  [7d] [30d] [90d] [12m] [Custom]                               │
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- Stacked areas: High (red), Medium (yellow), Low (green)
- Hover: exact counts per severity per day
- Brush: select time range to zoom
- Toggle: switch between absolute counts and percentage

#### 3.1.4 Evidence Verification Funnel

Funnel visualization showing evidence progression through verification levels:

```
┌─────────────────────────────────────────────────────────────────┐
│  EVIDENCE VERIFICATION FUNNEL                                   │
│                                                                 │
│  L0 Unverified    ████████████████████████████████  12          │
│       │                                                           │
│       ▼                                                           │
│  L1 Schema-valid  ████████████████████████████████████████  45    │
│       │                                                           │
│       ▼                                                           │
│  L2 Integrity     ████████████████████████████████████████████████████  120 │
│       │                                                           │
│       ▼                                                           │
│  L3 Cross-val     ████████████████████  20                         │
│       │                                                           │
│       ▼                                                           │
│  L4 Attested      ████  6                                          │
│                                                                 │
│  Conversion: L0→L1: 100%  L1→L2: 100%  L2→L3: 17%  L3→L4: 30%  │
└─────────────────────────────────────────────────────────────────┘
```

**Interactions:**
- Click level: filter evidence list to that level
- Hover: show conversion rate from previous level
- Time range selector: funnel for specific period

#### 3.1.5 Policy Dependency Graph

Force-directed graph showing policy inheritance and conflicts:

```
                    ┌──────────────┐
                    │ org-baseline │
                    │   v3.1.0     │
                    └──────┬───────┘
                           │ inherits
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌──────────────┐ ┌──────────┐ ┌──────────┐
     │ platform-sh  │ │ cs-bot   │ │ sales    │
     │   v2.3.1     │ │ v2.3.1   │ │ v2.3.1   │
     └──────┬───────┘ └────┬─────┘ └────┬─────┘
            │              │            │
            │              ▼            │
            │       ┌──────────┐        │
            └──────▶│ eu-ai    │◀───────┘
                    │ v1.0.0   │
                    └──────────┘
                         │
                         ▼ conflict
                    ┌──────────┐
                    │ hipaa    │
                    │ v2.0.0   │
                    └──────────┘
```

**Interactions:**
- Drag nodes to rearrange
- Click node: policy detail panel
- Hover edge: relationship description
- Zoom: scroll wheel or pinch
- Filter: show only conflicts, only inheritance, only active

#### 3.1.6 Agent Trust Score Distribution

Histogram with grade boundaries:

```
┌─────────────────────────────────────────────────────────────────┐
│  AGENT TRUST SCORE DISTRIBUTION                                 │
│                                                                 │
│  A (90-100)  ████████████████  12 agents                       │
│  B (80-89)   ████████████████████████████  18 agents           │
│  C (70-79)   ████████████  8 agents                            │
│  D (60-69)   ██████  4 agents                                  │
│  F (<60)     ███  3 agents                                     │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  0    10    20    30    40    50    60    70    80    90   100 │
│                                                                 │
│  Mean: 78.5  |  Median: 82  |  Std Dev: 12.3                   │
└─────────────────────────────────────────────────────────────────┘
```

**Interactions:**
- Click grade band: filter agent list
- Hover: show agent names in that range
- Time slider: animate distribution changes
- Compare mode: overlay two time periods

### 3.2 Dashboard-Specific Visualizations

#### 3.2.1 Executive Dashboard Visualizations

| Widget | Visualization Type | Real-Time | Drill-Down |
|--------|-------------------|-----------|------------|
| Compliance Score | Radial gauge with trend arrow | Yes | → Framework scores |
| Risk Posture | Severity donut chart | Yes | → Risk register |
| Audit Readiness | Progress ring with milestone markers | Hourly | → Evidence gaps |
| Agent Coverage | Stacked bar (governed/ungoverned/quarantined) | Yes | → Agent registry |
| Framework Scores | Horizontal bar chart with trend | Yes | → Compliance mapping |
| Risk Trend | Stacked area chart (stream graph) | Daily | → Risk detail |
| Open Findings | Treemap by severity × age | Yes | → Finding list |
| Audit Milestones | Gantt chart with readiness overlay | Daily | → Audit checklist |
| Trust Distribution | Histogram with grade bands | Yes | → Agent list |

#### 3.2.2 Operational Dashboard Visualizations

| Widget | Visualization Type | Real-Time | Actions |
|--------|-------------------|-----------|---------|
| Alerts & Notifications | Severity-grouped list with timeline | Yes | Acknowledge, dismiss, escalate |
| Open Findings | Stacked bar by severity | Yes | Create, assign, filter |
| Evidence Status | Funnel chart (L0→L4) | Hourly | Review, verify, attest |
| Active Assessments | Progress bars with status colors | Yes | View progress, add evidence |
| Agent Governance | Status donut + count badges | Yes | View agent, quarantine |
| Recent Activity | Streaming table with animations | Yes | View detail, verify integrity |

#### 3.2.3 Technical Dashboard Visualizations

| Widget | Visualization Type | Real-Time | Actions |
|--------|-------------------|-----------|---------|
| Agent Registry | Sortable table with trust score sparklines | Yes | Register, view, quarantine |
| Runtime Enforcement | Verdict distribution pie + trend line | Yes | View detail, override |
| Policy Evaluation Log | Streaming log with verdict badges | Yes | View detail, trace |
| Control Implementation | Status matrix with evidence counts | Hourly | View detail, run assessment |
| Trust Score Components | Radar chart per agent | Yes | View component breakdown |
| Policy Bundle Versions | Version timeline with agent counts | On change | View diff, rollback |

### 3.3 Visualization Accessibility

All visualizations comply with the accessibility requirements (§10.2) and provide:

| Requirement | Implementation |
|-------------|---------------|
| **Text alternative** | Every chart has a "View as Table" toggle showing the same data in tabular format |
| **Color independence** | Patterns (stripes, dots, crosshatch) in addition to color for all chart types |
| **Screen reader** | `aria-label` on chart container summarizing the data; `aria-describedby` linking to data table |
| **Keyboard navigation** | Tab through chart elements; arrow keys to move between data points; Enter to drill down |
| **Contrast** | All chart colors meet WCAG 2.1 AA contrast ratios (≥ 4.5:1) |
| **Reduced motion** | Static chart rendering when `prefers-reduced-motion: reduce` is set |
| **Zoom** | Charts remain readable at 200% browser zoom; SVG-based rendering |

---

## 4. Mobile-Responsive Design

### 4.1 Responsive Breakpoint System

Building on the base responsive design (§10.3), GRC_Claw implements a comprehensive mobile strategy:

| Breakpoint | Width | Target | Layout Pattern | Navigation |
|-----------|-------|--------|---------------|------------|
| **Mobile S** | < 375px | Small phones | Single column, stacked cards | Bottom tab bar |
| **Mobile M** | 375–414px | Standard phones | Single column, stacked cards | Bottom tab bar |
| **Mobile L** | 414–767px | Large phones / small tablets | Single column, expanded cards | Bottom tab bar |
| **Tablet** | 768–1023px | Tablets | Two-column grid, collapsible sidebar | Collapsible sidebar |
| **Laptop** | 1024–1439px | Laptops | Three-column grid, sidebar | Persistent sidebar |
| **Desktop** | 1440–1919px | Desktops | Full multi-column, sidebar | Persistent sidebar |
| **Wide** | ≥ 1920px | Large monitors | Full multi-column + extra space | Persistent sidebar |

### 4.2 Mobile Layout Patterns

#### 4.2.1 Mobile Navigation

```
┌─────────────────────────────┐
│  GRC_Claw                   │
│                             │
│  [Dashboard content area]   │
│                             │
│                             │
│                             │
├─────────────────────────────┤
│  🏠    📋    🔍    🔔    👤 │
│  Home  List  Search Alerts Me│
└─────────────────────────────┘
```

**Bottom tab bar (mobile only):**
- **Home:** Executive dashboard summary
- **List:** Quick access to findings, evidence, agents
- **Search:** Global search across all entities
- **Alerts:** Alert feed with badge count
- **Me:** User profile, settings, theme toggle

**Swipe gestures:**
- Swipe right: open sidebar navigation
- Swipe left on card: reveal quick actions
- Pull down: refresh data
- Pull up: load more items

#### 4.2.2 Mobile Dashboard Cards

Executive dashboard on mobile transforms into swipeable cards:

```
┌─────────────────────────────┐
│  GRC_Claw Executive         │
│  [Org ▼] [30d ▼]           │
├─────────────────────────────┤
│                             │
│  ┌───────────────────────┐  │
│  │ Compliance Score      │  │
│  │                       │  │
│  │     87/100            │  │
│  │     ▲ 3 pts           │  │
│  │                       │  │
│  │ [View Details →]      │  │
│  └───────────────────────┘  │
│                             │
│  ◀ ● ○ ○ ○ ○ ○ ○ ○ ○ ○ ▶   │
│                             │
│  Swipe for more widgets →   │
└─────────────────────────────┘
```

**Card carousel behavior:**
- One widget per screen on mobile
- Dot indicator shows position
- Swipe left/right to navigate between widgets
- Tap "View Details" to drill down
- Pull down to refresh all widgets

#### 4.2.3 Mobile Data Tables

Data tables transform into card lists on mobile:

**Desktop table:**
```
┌──────────────┬────────┬─────────┬──────────┬─────────┐
│ Agent ID     │ Trust  │ Status  │ Policy   │ Actions │
├──────────────┼────────┼─────────┼──────────┼─────────┤
│ prod-cs-bot  │ A (94) │ Active  │ v2.3.1   │ [View]  │
│ prod-sales   │ B (82) │ Active  │ v2.3.1   │ [View]  │
└──────────────┴────────┴─────────┴──────────┴─────────┘
```

**Mobile card list:**
```
┌─────────────────────────────┐
│ prod-cs-bot                 │
│ Trust: A (94)  ● Active     │
│ Policy: v2.3.1              │
│ [View]                      │
├─────────────────────────────┤
│ prod-sales                  │
│ Trust: B (82)  ● Active     │
│ Policy: v2.3.1              │
│ [View]                      │
└─────────────────────────────┘
```

**Transformation rules:**
- Primary identifier → card title
- Key attributes → card metadata rows
- Status → colored badge with icon
- Actions → card footer buttons
- Sort → dropdown selector above card list
- Pagination → infinite scroll with "Load More"

#### 4.2.4 Mobile Policy Editor

The policy editor (§5.2) adapts for mobile:

```
┌─────────────────────────────┐
│ ← Policy Editor             │
│ org-baseline v3.1.0         │
├─────────────────────────────┤
│                             │
│  [Metadata] [Rules] [Versions]│
│  ─────────────────────────  │
│                             │
│  Name: [org-baseline    ]   │
│  Version: [3.1.0        ]   │
│  Framework: [All ▼]         │
│  Owner: [CISO ▼]            │
│                             │
│  [Next: Rules →]            │
│                             │
└─────────────────────────────┘
```

**Mobile editor patterns:**
- Tab-based navigation between sections (Metadata, Rules, Versions)
- YAML editor with monospace font and syntax validation
- "Next" button advances to next section
- Save button always visible in header
- Test console accessible via floating action button

### 4.3 Touch Interaction Patterns

| Gesture | Action | Context |
|---------|--------|---------|
| **Tap** | Select / activate | All interactive elements |
| **Long press** | Context menu | List items, cards |
| **Swipe left** | Reveal actions | List items (edit, delete) |
| **Swipe right** | Open navigation | Any screen edge |
| **Swipe down** | Refresh | Dashboard, list views |
| **Swipe up** | Load more | Paginated lists |
| **Pinch** | Zoom | Charts, graphs, matrices |
| **Double tap** | Zoom in/out | Charts, detail views |

### 4.4 Mobile-Specific Components

#### 4.4.1 Floating Action Button (FAB)

```
┌─────────────────────────────┐
│                             │
│  [Content area]             │
│                             │
│                     ┌─────┐ │
│                     │  +  │ │  ← FAB
│                     └─────┘ │
└─────────────────────────────┘
```

**FAB actions by context:**
- Dashboard: Quick create (finding, evidence, agent)
- Evidence: Upload evidence
- Assessments: Add finding
- Policies: New policy

#### 4.4.2 Bottom Sheet

```
┌─────────────────────────────┐
│  ─── Drag handle ───        │
│                             │
│  Filter Results             │
│                             │
│  Framework                  │
│  [All ▼]                    │
│                             │
│  Status                     │
│  [All ▼]                    │
│                             │
│  Severity                   │
│  [All ▼]                    │
│                             │
│  [Reset]  [Apply Filters]   │
│                             │
└─────────────────────────────┘
```

**Usage:** Filters, quick settings, detail previews

#### 4.4.3 Pull-to-Refresh

All dashboard and list views support pull-to-refresh:
- Pull down 50px: trigger refresh indicator
- Release: fetch latest data
- Success: brief green check animation
- Failure: toast with retry option

### 4.5 Offline-First Mobile Support

| Capability | Implementation |
|-----------|---------------|
| **Cached data** | Last 50 items cached per view (IndexedDB) |
| **Offline indicator** | Banner showing "Offline — showing cached data" |
| **Queue actions** | Create/edit actions queued locally, synced on reconnect |
| **Background sync** | Service Worker syncs pending actions when connection restored |
| **Image caching** | Chart snapshots cached for offline viewing |

---

## 5. Dark/Light Theme Support

### 5.1 Theme Architecture

GRC_Claw implements a comprehensive theming system with three modes:

| Mode | Trigger | Use Case |
|------|---------|----------|
| **System** | Follows `prefers-color-scheme` | Default — respects OS setting |
| **Light** | Manual override | Bright environments, projectors |
| **Dark** | Manual override | Low-light environments, night shifts |

### 5.2 Theme Token System

Building on the base color palette (§15.2), the theme system uses CSS custom properties:

#### 5.2.1 Light Theme Tokens

```css
:root[data-theme="light"] {
  /* Backgrounds */
  --bg-primary: #ffffff;
  --bg-secondary: #f9fafb;
  --bg-tertiary: #f3f4f6;
  --bg-elevated: #ffffff;
  --bg-overlay: rgba(0, 0, 0, 0.5);

  /* Text */
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --text-tertiary: #9ca3af;
  --text-inverse: #ffffff;
  --text-link: #3b82f6;

  /* Borders */
  --border-primary: #e5e7eb;
  --border-secondary: #d1d5db;
  --border-focus: #3b82f6;

  /* Status colors */
  --color-success: #22c55e;
  --color-success-bg: #dcfce7;
  --color-warning: #f59e0b;
  --color-warning-bg: #fef3c7;
  --color-danger: #ef4444;
  --color-danger-bg: #fee2e2;
  --color-info: #3b82f6;
  --color-info-bg: #dbeafe;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

  /* Charts */
  --chart-grid: #e5e7eb;
  --chart-axis: #6b7280;
  --chart-series-1: #3b82f6;
  --chart-series-2: #22c55e;
  --chart-series-3: #f59e0b;
  --chart-series-4: #ef4444;
  --chart-series-5: #8b5cf6;
}
```

#### 5.2.2 Dark Theme Tokens

```css
:root[data-theme="dark"] {
  /* Backgrounds */
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --bg-elevated: #1e293b;
  --bg-overlay: rgba(0, 0, 0, 0.7);

  /* Text */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  --text-inverse: #0f172a;
  --text-link: #60a5fa;

  /* Borders */
  --border-primary: #334155;
  --border-secondary: #475569;
  --border-focus: #60a5fa;

  /* Status colors (adjusted for dark bg contrast) */
  --color-success: #4ade80;
  --color-success-bg: #14532d;
  --color-warning: #fbbf24;
  --color-warning-bg: #78350f;
  --color-danger: #f87171;
  --color-danger-bg: #7f1d1d;
  --color-info: #60a5fa;
  --color-info-bg: #1e3a5f;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5);

  /* Charts */
  --chart-grid: #334155;
  --chart-axis: #94a3b8;
  --chart-series-1: #60a5fa;
  --chart-series-2: #4ade80;
  --chart-series-3: #fbbf24;
  --chart-series-4: #f87171;
  --chart-series-5: #a78bfa;
}
```

### 5.3 Theme Switching UI

#### 5.3.1 Theme Toggle

```
┌─────────────────────────────────────┐
│  [☀️ Light]  [🌙 Dark]  [💻 System] │
│   ───────                           │
│   (active)                          │
└─────────────────────────────────────┘
```

**Location:** User menu → Theme, and Settings → Appearance

**Behavior:**
- Instant switch (no page reload)
- Preference persisted in localStorage
- "System" mode listens to `prefers-color-scheme` media query changes
- All charts, badges, and visualizations update immediately

#### 5.3.2 Theme Transition

```css
/* Smooth theme transition */
*, *::before, *::after {
  transition: background-color 200ms ease,
              color 200ms ease,
              border-color 200ms ease;
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    transition: none;
  }
}
```

### 5.4 Theme-Aware Components

#### 5.4.1 Status Badges

| Status | Light Theme | Dark Theme |
|--------|-------------|------------|
| Pass / Active / Verified | Green bg (#dcfce7), dark green text (#166534) | Dark green bg (#14532d), light green text (#4ade80) |
| Gap / Pending / L1 | Yellow bg (#fef3c7), dark yellow text (#92400e) | Dark yellow bg (#78350f), light yellow text (#fbbf24) |
| Fail / Critical / L0 | Red bg (#fee2e2), dark red text (#991b1b) | Dark red bg (#7f1d1d), light red text (#f87171) |
| Info / Neutral | Blue bg (#dbeafe), dark blue text (#1e40af) | Dark blue bg (#1e3a5f), light blue text (#60a5fa) |

#### 5.4.2 Charts

Charts automatically adapt to theme:
- Grid lines use `--chart-grid` color
- Axis labels use `--chart-axis` color
- Series colors use `--chart-series-*` tokens
- Tooltips use `--bg-elevated` background with `--text-primary` text
- Legends use `--text-secondary` text

#### 5.4.3 Syntax Highlighting (Policy Editor)

| Token | Light Theme | Dark Theme |
|-------|-------------|------------|
| Keyword | #7c3aed (purple) | #a78bfa (light purple) |
| String | #059669 (green) | #4ade80 (light green) |
| Comment | #6b7280 (gray) | #64748b (light gray) |
| Error | #dc2626 (red) | #f87171 (light red) |
| Background | #f9fafb | #1e293b |

### 5.5 Theme Persistence & Sync

| Scope | Storage | Sync |
|-------|---------|------|
| Theme preference | localStorage | Per-device |
| Custom theme colors | Server (user profile) | Cross-device |
| Dashboard layout | Server (user profile) | Cross-device |
| Widget visibility | Server (user profile) | Cross-device |

---

## 6. Custom Dashboard Builder

### 6.1 Overview

The custom dashboard builder allows users to create personalized dashboard views by selecting, arranging, and configuring widgets. This addresses the diverse needs of different roles while maintaining governance consistency.

### 6.2 Builder Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Dashboard Builder                                    [Save] [Preview] [Close]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ Widget Library ─────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ Compliance  │  │ Risk Trend  │  │ Agent Trust │  │ Evidence   │ │   │
│  │  │ Score       │  │             │  │ Distribution│  │ Funnel     │ │   │
│  │  │ [+ Add]     │  │ [+ Add]     │  │ [+ Add]     │  │ [+ Add]    │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │ Framework   │  │ Open        │  │ Assessment  │  │ Alert      │ │   │
│  │  │ Scores      │  │ Findings    │  │ Progress    │  │ Feed       │ │   │
│  │  │ [+ Add]     │  │ [+ Add]     │  │ [+ Add]     │  │ [+ Add]    │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  │                                                                     │   │
│  │  [Search widgets...]                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─ Canvas ────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Compliance   │  │ Risk Trend   │  │ Agent Trust  │              │   │
│  │  │ Score        │  │              │  │ Distribution │              │   │
│  │  │    87/100    │  │  ───╲        │  │  ████████    │              │   │
│  │  │  ▲ 3 pts     │  │  ────╲──╲    │  │  ████████████│              │   │
│  │  │ [⚙️] [🗑️]   │  │  [⚙️] [🗑️]   │  │  [⚙️] [🗑️]  │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ Framework    │  │ Open         │  │ Assessment   │              │   │
│  │  │ Scores       │  │ Findings     │  │ Progress     │              │   │
│  │  │ SOC 2  92%   │  │ Critical: 3  │  │ SOC 2  68%   │              │   │
│  │  │ [⚙️] [🗑️]   │  │ [⚙️] [🗑️]   │  │ [⚙️] [🗑️]  │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                                                                     │   │
│  │  [+ Add Widget]                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Widget Library

#### 6.3.1 Available Widgets

| Widget | Description | Data Source | Default Size | Configurable |
|--------|-------------|-------------|-------------|--------------|
| Compliance Score | Radial gauge with trend | Aggregated controls | Medium | Time range, frameworks |
| Risk Trend | Stacked area chart | Risk register | Large | Time range, severity |
| Agent Trust Distribution | Histogram | Trust scoring | Medium | Time range, grade filter |
| Evidence Funnel | Verification funnel | Evidence store | Medium | Time range, verification level |
| Framework Scores | Horizontal bar chart | Compliance mapping | Medium | Frameworks, time range |
| Open Findings | Treemap by severity | Finding management | Large | Severity, age, status |
| Assessment Progress | Progress bars | Assessment engine | Medium | Assessments, status |
| Alert Feed | Severity-grouped list | Alert engine | Medium | Severity, time range |
| Agent Registry Summary | Status donut + counts | Agent registry | Small | Environment, status |
| Policy Version Timeline | Version history | Policy management | Medium | Policy, versions |
| Control Implementation | Status matrix | Control status | Large | Framework, family |
| Recent Activity | Streaming table | Audit trail | Medium | Event types, actors |
| Enforcement Decisions | Verdict distribution | Enforcement engine | Small | Time range, agent |
| Trust Score Components | Radar chart | Trust scoring | Medium | Agent, components |
| Compliance Heatmap | Matrix visualization | Compliance mapping | Large | Frameworks, families |
| Audit Milestones | Gantt chart | Assessment engine | Medium | Time range |

#### 6.3.2 Widget Sizes

| Size | Grid Units | Dimensions (desktop) | Use Case |
|------|-----------|---------------------|----------|
| **Small** | 1×1 | 300×200px | Single metric, status badge |
| **Medium** | 2×1 | 600×200px | Standard chart, list |
| **Large** | 2×2 | 600×400px | Complex chart, matrix |
| **Full width** | 4×1 | 1200×200px | Activity stream, timeline |
| **Tall** | 1×2 | 300×400px | Funnel, vertical list |

### 6.4 Widget Configuration

Each widget has a configuration panel accessible via the gear icon (⚙️):

```
┌─────────────────────────────────────┐
│  Widget Settings                    │
│  Compliance Score                   │
├─────────────────────────────────────┤
│                                     │
│  Time Range: [Last 30 days ▼]       │
│                                     │
│  Frameworks:                        │
│  [✓] NIST 800-53                    │
│  [✓] SOC 2                          │
│  [ ] ISO 27001                      │
│  [ ] EU AI Act                      │
│                                     │
│  Display:                           │
│  (•) Radial gauge                   │
│  ( ) Number with trend              │
│  ( ) Number only                    │
│                                     │
│  Refresh:                           │
│  (•) Real-time                      │
│  ( ) Every 5 minutes                │
│  ( ) Every 15 minutes               │
│  ( ) Manual only                    │
│                                     │
│  [Cancel]  [Apply]                  │
└─────────────────────────────────────┘
```

### 6.5 Dashboard Layout System

#### 6.5.1 Grid System

```
┌─────────────────────────────────────────────────────────────┐
│  1   2   3   4   5   6   7   8   9   10  11  12           │
│  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐         │
│  │   │   │   │   │   │   │   │   │   │   │   │   │         │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤         │
│  │   │   │   │   │   │   │   │   │   │   │   │   │         │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤         │
│  │   │   │   │   │   │   │   │   │   │   │   │   │         │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤         │
│  │   │   │   │   │   │   │   │   │   │   │   │   │         │
│  └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘         │
│                                                             │
│  12-column grid, 8px gutters, responsive breakpoints       │
└─────────────────────────────────────────────────────────────┘
```

**Grid rules:**
- 12-column grid on desktop
- 6-column grid on tablet
- 4-column grid on mobile
- Widgets snap to grid
- Drag-and-drop reordering
- Resize handles on widget corners

#### 6.5.2 Layout Templates

Pre-defined layouts for common use cases:

| Template | Layout | Best For |
|----------|--------|----------|
| **Executive Overview** | 4 KPI cards + 2 large charts + 1 table | CISO, board meetings |
| **Operations Center** | Alert feed + findings + evidence + activity | GRC analysts |
| **Agent Monitor** | Trust distribution + registry + enforcement | Platform engineers |
| **Audit Ready** | Compliance scores + milestones + gaps | Auditors |
| **Custom** | User-defined | Any role |

### 6.6 Dashboard Sharing & Permissions

| Action | Permission | Behavior |
|--------|-----------|----------|
| Create dashboard | All roles | Personal dashboard visible only to creator |
| Share dashboard | GRC Analyst+ | Share with specific users or roles |
| Set as default | All roles | Replace default dashboard on login |
| Clone dashboard | All roles | Create copy of shared dashboard |
| Export layout | All roles | Export dashboard definition as JSON |
| Import layout | GRC Analyst+ | Import dashboard definition from JSON |

**Sharing model:**

```
┌─────────────────────────────────────┐
│  Share Dashboard: "SOC 2 Q4 Review" │
├─────────────────────────────────────┤
│                                     │
│  Visibility:                        │
│  ( ) Private (only me)              │
│  (•) Shared with roles              │
│  ( ) Shared with users              │
│  ( ) Public (all org members)       │
│                                     │
│  Share with Roles:                  │
│  [✓] GRC Analyst                    │
│  [✓] Auditor                        │
│  [ ] Executive                      │
│  [ ] Platform Engineer              │
│                                     │
│  Share with Users:                  │
│  [+ Add user]                       │
│  • analyst-jd (GRC Analyst)         │
│  • auditor-ex (Auditor)             │
│                                     │
│  Permissions:                       │
│  [✓] Can view                       │
│  [ ] Can edit                       │
│  [ ] Can share                      │
│                                     │
│  [Cancel]  [Share]                  │
└─────────────────────────────────────┘
```

### 6.7 Dashboard Version History

| Feature | Implementation |
|---------|---------------|
| Auto-save | Every 30 seconds during editing |
| Version snapshots | On save, create immutable version |
| Restore | Restore any previous version |
| Diff | Compare two versions side-by-side |
| Naming | Auto-name with timestamp; user can rename |

---

## 7. UI Performance Optimization

### 7.1 Performance Budgets

Building on the base performance requirements (§13), the deepened spec adds component-level budgets:

| Metric | Budget | Measurement |
|--------|--------|-------------|
| **Initial page load** | < 2s | First contentful paint |
| **Time to interactive** | < 3s | All event handlers attached |
| **Dashboard widget render** | < 500ms | Single widget visible |
| **Search/filter response** | < 200ms | Results displayed |
| **Evidence list (1000 items)** | < 1s | First 50 items visible |
| **Report generation** | < 10s | Download ready |
| **Real-time alert delivery** | < 1s | Event received → toast visible |
| **WebSocket reconnection** | < 3s | Reconnected + resubscribed |
| **Theme switch** | < 100ms | All colors updated |
| **Widget drag-and-drop** | < 16ms | 60fps during drag |
| **Chart render (1000 data points)** | < 300ms | Chart visible |
| **Chart render (10000 data points)** | < 1s | Chart visible |
| **List scroll (1000 items)** | 60fps | Smooth scrolling |
| **Modal open/close** | < 200ms | Animation complete |

### 7.2 Rendering Optimization

#### 7.2.1 Virtual Scrolling

For large lists (evidence, agents, audit trail), implement virtual scrolling:

```
┌─────────────────────────────────────┐
│  Evidence List (1,247 items)        │
├─────────────────────────────────────┤
│  ┌─────────────────────────────────┐│
│  │ ev-001  AC-2.1  L4  2h ago     ││  ← visible
│  │ ev-002  AU-6.1  L2  4h ago     ││  ← visible
│  │ ev-003  CC6.1   L3  6h ago     ││  ← visible
│  │ ev-004  AC-2.1  L1  1d ago     ││  ← visible
│  │ ev-005  AU-9.4  L0  2d ago     ││  ← visible
│  │ ev-006  AC-2.1  L4  2d ago     ││  ← visible
│  │ ev-007  CC6.1   L2  3d ago     ││  ← visible
│  │ ev-008  AU-6.1  L3  3d ago     ││  ← visible
│  │ ev-009  AC-2.1  L4  4d ago     ││  ← visible
│  └─────────────────────────────────┘│
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░  │  ← scrollbar
│  (only 10 items rendered in DOM)    │
└─────────────────────────────────────┘
```

**Implementation:**
- Render only visible items + 5 item buffer
- Total DOM nodes: ~15 regardless of list size
- Scrollbar represents full list height
- Smooth 60fps scrolling for 100,000+ items

#### 7.2.2 Lazy Loading

| Strategy | Implementation |
|----------|---------------|
| **Route-based** | Each page loaded on demand via code splitting |
| **Widget-based** | Dashboard widgets load data only when scrolled into view |
| **Image-based** | Chart snapshots loaded lazily; full chart on interaction |
| **Modal-based** | Modal content loaded on open, not on page load |
| **Tab-based** | Tab content loaded on first activation, cached after |

#### 7.2.3 Memoization & Caching

```javascript
// Widget data caching strategy
const cacheConfig = {
  // Static data: cache for 1 hour
  'frameworks': { ttl: 3600 },
  'control-list': { ttl: 3600 },
  
  // Semi-static data: cache for 5 minutes
  'policy-list': { ttl: 300 },
  'agent-registry': { ttl: 300 },
  
  // Dynamic data: cache for 30 seconds
  'compliance-score': { ttl: 30 },
  'open-findings': { ttl: 30 },
  
  // Real-time data: no cache
  'enforcement-log': { ttl: 0 },
  'alert-feed': { ttl: 0 },
};
```

**Memoization rules:**
- Widget components memoized with `React.memo` / `Vue.memo`
- Expensive computations (aggregations, filtering) memoized by input
- Chart data transformations cached until source data changes
- Search results cached by query string for 60 seconds

### 7.3 Network Optimization

#### 7.3.1 Data Fetching Strategy

| Data Type | Strategy | Rationale |
|-----------|----------|-----------|
| **Dashboard overview** | Single GraphQL query | Reduce round trips |
| **Widget data** | Parallel GraphQL queries | Load widgets independently |
| **Real-time updates** | WebSocket push | No polling |
| **Large lists** | Cursor-based pagination | Efficient incremental loading |
| **Reports** | Async generation + webhook | Don't block UI |
| **Search** | Debounced (300ms) + cached | Reduce server load |

#### 7.3.2 Request Batching

```
Before batching:
  GET /policies          → 50ms
  GET /agents           → 80ms
  GET /evidence         → 120ms
  GET /compliance       → 60ms
  Total: 310ms (4 requests)

After batching (single GraphQL query):
  POST /graphql          → 150ms
  Total: 150ms (1 request)
```

#### 7.3.3 Payload Optimization

| Technique | Implementation | Savings |
|-----------|---------------|---------|
| **Compression** | Brotli for all API responses | ~70% reduction |
| **Field selection** | GraphQL field-level selection | ~40% reduction |
| **Pagination** | Cursor-based, 50 items/page | ~90% for large lists |
| **Delta updates** | Only changed fields in WebSocket events | ~80% for real-time |
| **Binary encoding** | Protocol Buffers for WebSocket | ~50% vs JSON |

### 7.4 WebSocket Performance

#### 7.4.1 Connection Pooling

| Scenario | Connections | Behavior |
|----------|-------------|----------|
| Single dashboard | 1 WebSocket | All subscriptions multiplexed |
| Multiple tabs | 1 WebSocket per tab | Shared via Service Worker |
| Mobile | 1 WebSocket | Reused across views |
| Background | 0 WebSocket | Disconnected when tab hidden |

#### 7.4.2 Event Throttling

```
Event Source → Throttle → Batch → Send to Client

High-frequency events (enforcement decisions):
  - Throttle: max 10 events/second per subscription
  - Batch: aggregate into single message
  - Client renders: animated counter update

Low-frequency events (policy changes):
  - No throttling
  - Immediate delivery
  - Client renders: toast notification
```

#### 7.4.3 Subscription Management

```javascript
// Automatic subscription lifecycle
const subscriptionManager = {
  // Subscribe when widget becomes visible
  onWidgetVisible: (widgetId, subscription) => {
    subscribe(subscription);
  },
  
  // Unsubscribe when widget is hidden
  onWidgetHidden: (widgetId) => {
    unsubscribe(widgetId);
  },
  
  // Pause when tab is hidden
  onTabHidden: () => {
    pauseAll();
    // Server queues events for 60s
  },
  
  // Resume when tab becomes visible
  onTabVisible: () => {
    resumeAll();
    // Server replays queued events
  },
};
```

### 7.5 Rendering Performance

#### 7.5.1 Chart Rendering

| Data Points | Rendering Strategy | Target FPS |
|-------------|-------------------|------------|
| < 100 | SVG (full interactivity) | 60 |
| 100–1,000 | Canvas (full interactivity) | 60 |
| 1,000–10,000 | Canvas (simplified) | 30 |
| 10,000–100,000 | WebGL (aggregated) | 30 |
| > 100,000 | Server-side rendering (image) | N/A |

#### 7.5.2 Animation Performance

| Animation | Technique | Budget |
|-----------|-----------|--------|
| Widget value change | CSS transition (opacity, transform) | 300ms |
| Row insert/remove | CSS animation (transform) | 200ms |
| Modal open/close | CSS transition (opacity, scale) | 200ms |
| Page route change | CSS transition (opacity) | 150ms |
| Chart data update | Canvas redraw | 100ms |
| Toast slide-in | CSS transition (transform) | 200ms |
| Drag and drop | Direct DOM manipulation | 16ms (60fps) |

**Animation rules:**
- Use `transform` and `opacity` only (GPU-accelerated)
- Avoid animating `width`, `height`, `top`, `left`
- Use `will-change` sparingly for complex animations
- Respect `prefers-reduced-motion` (disable all animations)
- Debounce rapid successive animations

#### 7.5.3 Bundle Optimization

| Technique | Implementation | Impact |
|-----------|---------------|--------|
| **Code splitting** | Route-level + widget-level | Initial bundle < 200KB |
| **Tree shaking** | Remove unused components | ~30% reduction |
| **Lazy chunks** | Load heavy charts on demand | Defer 500KB+ |
| **Preload** | Preload critical resources | Faster FCP |
| **Prefetch** | Prefetch likely next routes | Instant navigation |
| **Service Worker** | Cache static assets | Instant repeat visits |

**Bundle size budget:**

| Chunk | Size | Load |
|-------|------|------|
| Core (router, auth, layout) | < 150KB | Initial |
| Dashboard widgets | < 100KB | On dashboard load |
| Charts library | < 200KB | On first chart render |
| Policy editor | < 100KB | On editor open |
| Evidence viewer | < 80KB | On viewer open |
| **Total initial** | **< 200KB** | **< 2s on 4G** |

### 7.6 Performance Monitoring

#### 7.6.1 Real User Monitoring (RUM)

| Metric | Collection | Alert Threshold |
|--------|-----------|-----------------|
| First Contentful Paint | Performance API | > 2s |
| Largest Contentful Paint | Performance API | > 3s |
| Time to Interactive | Performance API | > 3s |
| Cumulative Layout Shift | Performance API | > 0.1 |
| First Input Delay | Performance API | > 100ms |
| WebSocket latency | Custom timing | > 500ms |
| Widget render time | Custom timing | > 500ms |
| API response time | Performance API | > 1s |

#### 7.6.2 Performance Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  UI PERFORMANCE MONITORING                                      │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  FCP         │  │  LCP         │  │  TTI         │          │
│  │  1.2s ✅     │  │  2.1s ✅     │  │  2.8s ✅     │          │
│  │  < 2s budget │  │  < 3s budget │  │  < 3s budget │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  CLS         │  │  FID         │  │  WS Latency  │          │
│  │  0.02 ✅     │  │  45ms ✅     │  │  120ms ✅    │          │
│  │  < 0.1 budget│  │  < 100ms     │  │  < 500ms     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  P95 API Response: 180ms  |  P99: 450ms  |  Error Rate: 0.02%  │
│                                                                 │
│  [View Details]  [Export Report]  [Set Alerts]                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.7 Performance Checklist

| Category | Check | Verification |
|----------|-------|-------------|
| **Loading** | All routes code-split | Lighthouse audit |
| **Loading** | Images lazy-loaded | Network tab |
| **Loading** | Critical CSS inlined | Page source |
| **Rendering** | Virtual scrolling for lists > 50 items | DOM inspector |
| **Rendering** | Charts use Canvas for > 1000 points | Performance tab |
| **Rendering** | Animations use transform/opacity | DevTools |
| **Network** | GraphQL for complex queries | Network tab |
| **Network** | WebSocket for real-time | Network tab |
| **Network** | Brotli compression enabled | Response headers |
| **Caching** | Service Worker caching static assets | Application tab |
| **Caching** | API responses cached appropriately | Network tab |
| **Bundle** | Initial JS < 200KB | Build output |
| **Bundle** | No unused dependencies | Bundle analyzer |

---

## 8. Integration with Existing Spec

### 8.1 Component Library Extensions

The deepened spec extends the base component library (§15.1) with new components:

| Component | Description | Used In |
|-----------|-------------|---------|
| `LiveIndicator` | Connection status dot (Live/Stale/Reconnecting/Offline) | All real-time widgets |
| `IncrementalCounter` | Animated number with trend arrow | Dashboard KPI cards |
| `ComplianceHeatmap` | Matrix visualization | Executive dashboard, compliance mapping |
| `TrustRadarChart` | Multi-axis radar chart | Agent detail, technical dashboard |
| `RiskStreamGraph` | Stacked area chart | Executive dashboard |
| `EvidenceFunnel` | Funnel visualization | Operational dashboard |
| `PolicyDependencyGraph` | Force-directed graph | Policy management |
| `TrustHistogram` | Distribution histogram | Executive dashboard |
| `WidgetCard` | Draggable, resizable widget container | Dashboard builder |
| `ThemeToggle` | Light/Dark/System switcher | Header, settings |
| `MobileCardList` | Card-based list for mobile | All list views |
| `BottomSheet` | Slide-up panel | Mobile filters, quick actions |
| `FloatingActionButton` | Contextual action button | Mobile, dashboard builder |
| `VirtualList` | Virtual scrolling container | Evidence list, agent registry |
| `SkeletonWidget` | Widget-specific loading placeholder | All widgets |
| `OfflineBanner` | Offline mode indicator | All pages |

### 8.2 Interaction Pattern Extensions

The deepened spec extends the base interaction patterns (§12.1):

| Pattern | Extension | Context |
|---------|-----------|---------|
| **Real-time Updates** | WebSocket push with visual indicators | All dashboards, alerts, activity |
| **Drag and Drop** | Widget reordering in dashboard builder | Custom dashboard builder |
| **Swipe Gestures** | Mobile navigation and actions | Mobile views |
| **Pull-to-Refresh** | Data refresh on mobile | Mobile dashboards, lists |
| **Infinite Scroll** | Lazy loading for large lists | Evidence, agents, audit |
| **Optimistic UI** | Immediate feedback for actions | Finding status, alert acknowledge |
| **Progressive Enhancement** | Graceful degradation without WebSocket | All real-time features |

### 8.3 Accessibility Extensions

The deepened spec extends the base accessibility requirements (§10.2):

| Feature | Extension | Implementation |
|---------|-----------|---------------|
| **Live regions** | Real-time update announcements | `aria-live="polite"` for widget updates; `aria-live="assertive"` for critical alerts |
| **Focus management** | Modal and drawer focus trap | Focus trapped within modal; returns to trigger on close |
| **Skip links** | Skip to main content, skip to alerts | Visible on first Tab press |
| **Reduced motion** | Disable all animations | `prefers-reduced-motion` media query |
| **High contrast** | Windows High Contrast mode support | `forced-colors` media query |
| **Touch targets** | Minimum 44×44px touch targets | All interactive elements on mobile |
| **Screen reader charts** | Data table alternative for every chart | "View as Table" toggle on all visualizations |

---

## 9. Implementation Priorities

### 9.1 Phase 1: Foundation (Weeks 1–4)

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | WebSocket connection manager | Medium | Enables all real-time features |
| P0 | Real-time alert delivery | Medium | Critical for governance operations |
| P0 | Theme token system | Low | Foundation for dark/light mode |
| P0 | Virtual scrolling | Medium | Enables large lists |
| P0 | Code splitting | Medium | Foundation for performance |

### 9.2 Phase 2: Core Features (Weeks 5–8)

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | Dark/light theme | Medium | User preference, accessibility |
| P0 | Mobile-responsive layouts | High | Mobile access for executives |
| P1 | Advanced chart components | High | Better data comprehension |
| P1 | Widget data caching | Medium | Performance improvement |
| P1 | WebSocket reconnection | Medium | Reliability |

### 9.3 Phase 3: Advanced Features (Weeks 9–12)

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P1 | Custom dashboard builder | High | Role-specific views |
| P1 | Real-time activity stream | Medium | Operational awareness |
| P2 | Compliance heatmap | Medium | Cross-framework insight |
| P2 | Policy dependency graph | Medium | Policy impact analysis |
| P2 | Performance monitoring | Medium | Continuous improvement |

### 9.4 Phase 4: Polish (Weeks 13–16)

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P2 | Mobile offline support | High | Field audits |
| P2 | Dashboard sharing | Medium | Collaboration |
| P3 | WebGL chart rendering | High | Large dataset performance |
| P3 | Advanced animations | Low | User experience polish |
| P3 | Performance dashboard | Low | Monitoring visibility |

---

## 10. Appendix: WebSocket Message Protocol

### 10.1 Connection Initialization

```json
// Client → Server
{
  "type": "connection_init",
  "payload": {
    "Authorization": "Bearer eyJhbG...",
    "max_in_flight": 100
  }
}

// Server → Client
{
  "type": "connection_ack",
  "payload": {
    "connection_id": "conn-abc123",
    "max_in_flight": 100
  }
}
```

### 10.2 Subscription Messages

```json
// Client → Server: Subscribe
{
  "id": "sub-001",
  "type": "subscribe",
  "payload": {
    "query": "subscription { agentTrustScoreChanged(agentId: \"agent-42\") { id trustScore { value grade } } }"
  }
}

// Server → Client: Subscription confirmed
{
  "id": "sub-001",
  "type": "next",
  "payload": {
    "data": {
      "agentTrustScoreChanged": {
        "id": "agent-42",
        "trustScore": { "value": 82, "grade": "B" }
      }
    }
  }
}

// Client → Server: Unsubscribe
{
  "id": "sub-001",
  "type": "complete"
}
```

### 10.3 Error Handling

```json
// Server → Client: Subscription error
{
  "id": "sub-001",
  "type": "error",
  "payload": [
    {
      "message": "Agent not found: agent-999",
      "extensions": { "code": "AGENT_NOT_FOUND" }
    }
  ]
}

// Server → Client: Connection error
{
  "type": "connection_error",
  "payload": {
    "message": "Rate limit exceeded for WebSocket subscriptions",
    "retry_after": 30
  }
}
```

### 10.4 Keep-Alive

```json
// Server → Client: Ping (every 30s)
{ "type": "ping" }

// Client → Server: Pong
{ "type": "pong" }
```

---

*End of deepened specification.*
