# UI/UX Standards V15

## 1. Navigation Architecture (Four Layers)

### Layer 1: Global Shell

| Component | File | Purpose |
|-----------|------|---------|
| MainLayout | `src/components/layout/MainLayout.tsx` | Page shell (~320 callers) |
| Sidebar | `src/components/layout/Sidebar.tsx` | Global navigation |
| Sidebar data | `src/lib/navigation/siteNavigation.tsx` | Nav config |
| ProfileMenu | `src/components/layout/ProfileMenu.tsx` | Account/settings |

### Layer 2: Silo Hub Nav

| Silo | Nav Source | Shell |
|------|-----------|-------|
| GRC / moat / enterprise | `src/lib/grc/hubNav.ts` -> `GrcHubNav` | `MainLayout` full chrome |
| Storefront / PLG | `siteNavigation.tsx` -> `Sidebar` | `MainLayout` full chrome |
| AgenticAds workspace | `AgenticAdsNav` + `AgenticAdsMobileNav` | `MainLayout minimalChrome` |
| Investor OS embed | `InvestorNavigatorNav` | `MainLayout minimalChrome` |

**Rule:** Hub links live in one config file per silo; never hardcode nav arrays inside page components.

### Layer 3: In-Page Wayfinding

| Element | Usage |
|---------|-------|
| Breadcrumbs | Multi-level navigation |
| Pillar cards | Related modules |
| Kill-chain links | Playbook navigation |
| Related modules | Cross-silo linking |

### Layer 4: Discovery Graph

| Element | Usage |
|---------|-------|
| SEO internal links | Hub -> pillar -> money page |
| Moat atlas | Platform barrier pages |
| Kill chains | Playbook index |
| llms.txt | AI citation surfaces |

---

## 2. Page Templates

### Platform Moat

| Component | Detail |
|-----------|--------|
| Template | `Platform*MoatPage.tsx` |
| Reference | `src/pages/PlatformSchemaValidationMoatPage.tsx` |
| Shell | `MainLayout` -> `GrcHubNav compact` -> badge -> h1 -> pillar cards -> `MoneyPageCroSection` |
| hubNav section | `platform-moat` |

### Enterprise Hub

| Component | Detail |
|-----------|--------|
| Template | `Enterprise*Page.tsx` |
| Shell | `MainLayout` -> `GrcHubNav` -> enterprise section |
| hubNav section | `enterprise` |

### Developer Contract

| Component | Detail |
|-----------|--------|
| Template | `Developers*Page.tsx` |
| Shell | `GrcHubNav` developers section + link to platform moat twin |
| hubNav section | `developers` |

### Marketing Hub

| Component | Detail |
|-----------|--------|
| Template | `HubPageShell` |
| Shell | Hero + feature grid + CTAs + optional `moneyPageKey` |
| hubNav section | `hub` |

### Kill Chain Detail

| Component | Detail |
|-----------|--------|
| Template | `KillChainDetail` pattern |
| Shell | HowTo schema + stage links |
| hubNav section | `kill-chains` |

### Workspace / Auth-Gated

| Component | Detail |
|-----------|--------|
| Template | Route policy `required` |
| Shell | Lock icon in sidebar; `GrcEntitlementGuard` in layout |
| hubNav section | N/A (sidebar-only) |

---

## 3. New Route Wire Checklist (12 Items)

Every new public route requires:

```
- [ ] Content export in methodologyContent.ts (or auditPackContent.ts)
- [ ] Page component (correct template class)
- [ ] src/app/lazyPages.tsx lazy import
- [ ] src/App.tsx Route
- [ ] src/lib/seo/pageMetaRegistry.ts
- [ ] scripts/seo/site-seo.config.cjs (sitemap + llms if cite-worthy)
- [ ] src/lib/grc/hubNav.ts (correct section id)
- [ ] src/lib/seo/killChainMoatLinks.ts (if moat-related)
- [ ] src/lib/seo/marketingKillChains.ts (insert BEFORE omnichannel-gtm-sprint)
- [ ] src/lib/seo/moneyPageCro.ts (audit-pack or page CRO key)
- [ ] methodologyContent.ts MOAT_ATLAS_SECTIONS (platform moat batches)
- [ ] npm run gen:seo && npm run build:dev
```

### hubNav Section IDs

| id | title |
|----|-------|
| `hub` | Hub |
| `solutions` | Solutions |
| `posture` | Posture |
| `evidence` | Evidence & reports |
| `audit-packs` | Audit readiness packs |
| `methodology` | Methodology loops |
| `platform-moat` | Platform moat |
| `enterprise` | Enterprise & procurement |
| `architecture` | Architecture |
| `developers` | Developers & API moat |
| `trust` | Trust center |
| `crosswalk` | Crosswalk & catalog |
| `channel` | Channel & partners |
| `operations` | Operations |
| `kill-chains` | GRC moat kill chains |

Add links to the lowest correct section; platform moat pages go under `platform-moat`, not `hub`.

---

## 4. Auth & Entitlement UX

### Auth Modes

| Mode | UX Behavior |
|------|-------------|
| `guest` | No lock; full browse |
| `soft` | Browse as guest; sign-in card when `softPrompt` (not on learning surfaces) |
| `required` | Lock icon in sidebar; redirect or gate on page |
| `owner` | Marketing operator tools only |

### Auth Policy Source

| Concern | Location |
|---------|----------|
| Route policy | `src/lib/auth/routePolicy.ts` |
| Sidebar lock | `getRouteAuthPolicy(path).mode === 'required'` |
| Entitlement gate | `src/components/grc/GrcEntitlementGuard.tsx` |

### Auth UX Rules

| Rule | Detail |
|------|--------|
| No duplicate logic | Extend `routePolicy.ts`, do not add auth in pages |
| Lock icon | Visible in sidebar for `required` routes |
| Soft prompt | Sign-in card, not redirect, on learning surfaces |
| Owner tools | Only visible to `MARKETING_OWNER_EMAIL` |

---

## 5. Responsive Rules

### Breakpoint Behaviors

| Breakpoint | Behavior |
|------------|----------|
| `< lg` | Hamburger -> overlay `Sidebar`; skip desktop sidebar DOM |
| `>= lg` | Fixed 64-width sidebar; `lg:ml-64` content offset |
| AgenticAds | `AgenticAdsMobileNav` horizontal pills; sidebar tree on desktop |
| Print | `print-hide` on chrome; `print:` overrides on main |

### Mobile-First Rules

| Rule | Detail |
|------|--------|
| DOM savings | Never mount full desktop sidebar on mobile initial load (~1.5k DOM nodes saved) |
| Sidebar lazy | Use `useDesktopSidebar` hook |
| Touch targets | Minimum 44x44px for mobile tap |
| Content priority | Hero CTA first, then pillar cards |

### Responsive CSS

| Silo | File |
|------|------|
| Global | Tailwind breakpoints |
| AgenticAds | `src/styles/agentic-ads-responsive.css` |
| Sidebar | `md:hidden lg:block` on nav item text |

### Breakpoint Classes

| Class | Width |
|-------|-------|
| default | mobile |
| `md:` | 768px |
| `lg:` | 1024px (sidebar breakpoint) |
| `xl:` | 1280px |

---

## 6. CRO Placement Rules

### CRO Block Placement

| Rule | Detail |
|------|--------|
| Primary CTA | One per hero; secondary = human help or deep dive |
| MoneyPageCroSection | At page bottom; never above pillar content |
| FAQ schema | On money pages via `MoneyPageCroSection` |
| HowTo schema | On kill chain detail pages |

### CRO Configuration

| Concern | Location |
|---------|----------|
| CRO config | `src/lib/seo/moneyPageCro.ts` |
| CRO component | `src/components/seo/MoneyPageCroSection.tsx` |
| Visitor perks | `src/components/visitor/FirstVisitorPerksStrip.tsx` (layout-owned) |

### CRO Anti-Patterns

| Anti-Pattern | Why It Fails |
|--------------|--------------|
| Multiple CTAs in hero | Decision paralysis |
| CRO above pillar content | Interrupts information flow |
| Duplicating visitor strip | Layout owns it; pages do not |
| Re-enabling `CatalogListStrip` | Not on MainLayout or money pages |
| Re-enabling `RoutePlgHydration` | Not on MainLayout or money pages |

---

## 7. Cross-Silo Linking Rules

### Link Patterns

| From | To | Pattern |
|------|-----|---------|
| Platform moat | Developer contract | Hero button `-> /developers/...` |
| Platform moat | Kill chain | Hero outline button `-> /kill-chains/...` |
| Developer page | Platform moat | "Production barrier" link up |
| Any GRC page | Moat atlas | `GrcHubNav` footer links |
| Storefront | AgenticAds | Sidebar section; not inside GrcHubNav |

### Cross-Silo Rules

| Rule | Detail |
|------|--------|
| Hub navigation | Use `GrcHubNav` for GRC silo links |
| Sidebar sections | Use `siteNavigation.tsx` for cross-silo |
| No iframe embeds | AgenticAds must stay native |
| Exact labels | Never paraphrase user-provided nav labels |

---

## 8. Design Tokens (Cyber Theme)

| Token | Usage |
|-------|-------|
| `bg-cyber-dark` | App background |
| `bg-cyber-darker` | Cards, hub nav |
| `border-cyber-accent` | Active nav, highlights |
| `text-cyber-accent` | Links, icons |
| `bg-cyber-gray` | Hover states |

Compose with shadcn/ui primitives from `src/components/ui/`. Prefer existing `Card`, `Badge`, `Button` patterns over new primitives.

---

## 9. Graph Hotspots (Codebase)

After indexing, expect high fan-in on:

| Symbol | Role | Callers |
|--------|------|---------|
| `MainLayout` | Page shell | ~320 |
| `GrcHubNav` | GRC hub nav | ~240 |
| `MoneyPageCroSection` | Bottom CRO | ~250 |
| `useSeo` | Per-page meta | ~296 |
| `lazyPages.tsx` | Route lazy registry | ~100+ |

### Graph-First Workflow

Before wiring new routes, run graph queries:

1. `search_graph` for orphan content (`in_degree: 0` on `*_MOAT_PILLARS`, `*_CONTROLS`)
2. `get_architecture` hotspots (`GrcHubNav`, `lazyPages.tsx`)
3. `trace_path` for impact analysis

---

## 10. Implementation Workflow

1. **Classify** the page (moat / enterprise / developer / hub / workspace)
2. **Graph query** -- confirm no duplicate path; find content export; trace `GrcHubNav` callers
3. **Clone** nearest template page; swap content export + SEO strings
4. **Wire** full 12-item checklist
5. **Verify** active state in `GrcHubNav` (`pathname === link.path`)
6. **Build** -- confirm sitemap URL count increased; no duplicate titles in registry

---

## 11. Weekly UX Hygiene

- [ ] `search_graph` for `*_MOAT_PILLARS` with `in_degree: 0` -> schedule next batch
- [ ] Spot-check mobile nav on `/platform/moat-atlas` and one enterprise hub
- [ ] Compare `pageMetaRegistry` paths to `hubNav` paths for drift
- [ ] After large batch: re-index repo (`index_repository`) for graph accuracy

---

## 12. Anti-Patterns (Reject)

| Anti-Pattern | Why It Fails |
|--------------|--------------|
| Route in `App.tsx` without `hubNav.ts` entry | Orphan route |
| Nav links only in blog prose | Must be in hub or sidebar |
| Ten CTAs in hero row | Decision paralysis |
| `GrcHubNav` full on long moat pages | Use `compact` |
| New expandable sidebar sections without review | `siteNavigation.tsx` drift |
| iframe embeds for first-party modules | AgenticAds must stay native |
| Paraphrasing user-provided nav labels | Use exact wording |

---

## 13. Scripts

```bash
npm run gen:seo              # Regenerate sitemap, llms.txt, site stats
npm run build:dev            # Verify routes compile
npm run marketing:organic-bootstrap  # SEO + sitemap QA bundle
```
