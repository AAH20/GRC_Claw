# SEO / AI SEO Strategy V15

## 1. Technical SEO Checklist

### Sitemap Configuration

| Rule | Detail |
|------|--------|
| Source | `scripts/generate-sitemap.cjs` |
| Config | `scripts/seo/site-seo.config.cjs` |
| Exclude | Auth, workspace, owner ops, demo shells |
| Generate | `npm run gen:seo` then `npm run build` |
| Verify | `public/sitemap.xml` includes only public routes |

### Sitemap Exclusions (Never Index)

| Category | Paths |
|----------|-------|
| Auth | `/auth/*`, `/register`, `/invite` |
| Workspace | `/dashboard`, `/settings`, `/workspace` |
| Owner ops | `/marketing-command-center`, `/gtm-sprint`, `/distribution-hub`, `/campaigns` |
| Demo shells | SIEM dashboards, cloud demos (`DEMO_TOOL_NOINDEX`) |
| Redirect-only | `/welcome`, `/download-success`, `/instant-audit` |

### Canonical Rules

| Rule | Implementation |
|------|----------------|
| One URL per intent | `buildCanonical()` in `siteConfig.ts` |
| SPA routes | Per-page meta, no generic fallback |
| Duplicate prevention | `pageMetaRegistry.ts` unique titles |
| Verification | No duplicate `<loc>` in sitemap |

### Schema Markup

| Schema | Pages | Builder |
|--------|-------|---------|
| Organization/WebSite | Global | `GlobalSeo.tsx` |
| FAQ | Money pages | `MoneyPageCroSection.tsx` |
| HowTo | Kill chains | `KillChainDetail` |
| Article | Blog posts | `PageSEO.tsx` |

### robots.txt

| Rule | Path |
|------|------|
| Allow | Public content |
| Disallow | Private workspaces, auth |
| Source | `public/robots.txt` |
| Regenerate | `npm run gen:seo` |

---

## 2. AI SEO Rules

### llms.txt Configuration

| Rule | Detail |
|------|--------|
| Source | `scripts/generate-llms-txt.mjs` |
| Output | `public/llms.txt` |
| Edit method | Never hand-edit; always `npm run gen:seo` |
| Priority routes | `/free-domain-scan`, `/trust-center`, `/productized-services` |

### Entity Consistency

| Element | Value | Location |
|---------|-------|----------|
| Name | A2Z SOC | Schema, llms.txt, meta |
| URL | https://a2z-soc.com | Schema sameAs, llms.txt |
| Founder | Ahmed Hassan | Schema, llms.txt |
| Description | Unified GRC + CTI platform | Meta, llms.txt |

### Quotable Blocks

| Block Type | Example | Use Case |
|------------|---------|----------|
| Numbers | 867 controls across frameworks | Pricing, capability pages |
| Checklists | 12-item audit readiness checklist | Blog, trust center |
| TCO tables | Vanta vs A2Z cost comparison | Displacement plays |
| Tier comparison | Starter vs Pro vs Enterprise | Pricing pages |

### AI Citation Landing Pages

| Page | CTA | Attribution |
|------|-----|-------------|
| `/blog/a2z-soc-platform-monetization-guide-2026` | Trust center | Pricing queries |
| `/blog/comprehensive-grc-framework-catalog-2026` | Framework hub | Compliance queries |
| `/trust-center#tco-compare` | Checkout | Displacement queries |
| `/blog/a2z-vs-vanta-soc2-grc-2026` | Trust center | Vanta comparison |
| `/free-domain-scan` | Scan start | Security posture queries |

### Attribution UTMs

| Source | UTM Format |
|--------|------------|
| ChatGPT | `?utm_source=chatgpt&utm_medium=ai_referral` |
| Perplexity | `?utm_source=perplexity&utm_medium=ai_referral` |
| Claude | `?utm_source=claude&utm_medium=ai_referral` |
| Gemini | `?utm_source=gemini&utm_medium=ai_referral` |
| Copilot | `?utm_source=copilot&utm_medium=ai_referral` |

---

## 3. Kill Chain Alignment

### SEO Kill Chains

| Chain | Stage | SEOD Focus |
|-------|-------|------------|
| `ai-seo` | Entity establishment | llms.txt, JSON-LD, entity consistency |
| `ai-seo` | Evidence density | FAQ schema, quotable blocks |
| `ai-seo` | Capture | Citation landing CVR, AI UTM |
| `programmatic-seo` | Inventory/template | Glossary, learning center, hub templates |
| `programmatic-seo` | Link graph | Internal links to money pages |
| `demand-gen` | Recon | Sitemap, meta registry, CWV, GSC |
| `community-devrel` | Answer | Long-tail replies linking one pillar URL |

### Kill Chain Cross-Links

| SEOD Task | Kill Chain Stage |
|-----------|------------------|
| Fix sitemap/meta | demand-gen -> recon |
| Glossary hub expansion | programmatic-seo -> inventory/template |
| llms.txt + entity | ai-seo -> entity establishment |
| FAQ on trust center | ai-seo -> evidence density |
| AI UTM sharing | ai-seo -> capture |
| Community one-link replies | community-devrel -> answer |

### Kill Chain Library

| Resource | Path |
|----------|------|
| Kill chain index | `/marketing-kill-chains` |
| AI SEO chain | `/kill-chains/ai-seo` |
| Programmatic SEO | `/kill-chains/programmatic-seo` |
| Source file | `src/lib/seo/marketingKillChains.ts` |

---

## 4. Money Page Optimization

### Money Pages (Conversion Targets)

| Page | Path | Persona |
|------|------|---------|
| Homepage | `/` | All |
| Start | `/start` | Founder/SMB |
| Free scan | `/free-domain-scan` | All personas |
| Productized services | `/productized-services` | PE/enterprise |
| Consultation | `/consultation` | GRC lead |
| Contact | `/contact` | All |
| Cyber insurance | `/cyber-insurance-blueprint` | Broker |
| Risk calculator | `/tools/cyber-risk-calculator` | Founder/SMB |

### CRO Block Rules

| Rule | Detail |
|------|--------|
| Primary CTA | One per hero; secondary = human help or deep dive |
| CRO section | `MoneyPageCroSection` at page bottom |
| FAQ schema | On money pages via `MoneyPageCroSection` |
| HowTo schema | On kill chain detail pages |
| No re-enable | `CatalogListStrip`, `RoutePlgHydration` on money pages |

### CRO Configuration

| Concern | Location |
|---------|----------|
| CRO config | `src/lib/seo/moneyPageCro.ts` |
| CRO component | `src/components/seo/MoneyPageCroSection.tsx` |
| FAQ schema | `src/lib/seo/schemaBuilders.ts` |
| Page meta | `src/lib/seo/pageMetaRegistry.ts` |

### Money Page Checklist

- [ ] Above-fold CTA with one default next step
- [ ] `MoneyPageCroSection` at bottom
- [ ] FAQ schema with 3-5 questions
- [ ] Internal links from at least one hub
- [ ] Canonical URL set correctly
- [ ] Title/description in pageMetaRegistry
- [ ] Not in SITEMAP_EXCLUDE
- [ ] In sitemap after `gen:seo`

---

## 5. Internal Linking Strategy

### Link Architecture

```
Hub -> Pillar -> Money Page
  |         |         |
  v         v         v
/blog     /trust-center  /free-domain-scan
/glossary /productized   /consultation
/learning /cyber-insur   /contact
```

### Hub Pages

| Hub | Path | Links To |
|-----|------|----------|
| Blog | `/blog` | All cluster articles -> money pages |
| Glossary | `/glossary` | Framework terms -> trust center |
| Learning center | `/learning-center` | SOC analyst path -> scan |
| Kill chains | `/marketing-kill-chains` | Playbooks -> productized services |

### Internal Link Rules

| Rule | Detail |
|------|--------|
| Minimum links | 3 contextual links per new content |
| Hub requirement | Every public page linked from hubNav |
| Money page link | Every cluster article -> at least one money page |
| Anchor text | Descriptive, not "click here" |
| Verification | `npm run gen:seo` updates sitemap |

### hubNav Section Order (Do Not Reorder)

`hub` -> `solutions` -> `posture` -> `evidence` -> `audit-packs` -> `methodology` -> `platform-moat` -> `enterprise` -> `architecture` -> `developers` -> `trust` -> `crosswalk` -> `channel` -> `operations` -> `kill-chains`

---

## 6. Backlink Strategy

### LinkedIn Syndication

| Element | Detail |
|---------|--------|
| Tool | linkedctl MCP |
| Frequency | 1 post/day minimum |
| Content | Trust center, TCO comparisons, framework catalogs |
| UTM | `?utm_source=linkedin&utm_medium=social` |
| Automation | `docs/marketing/DISTRIBUTION-RUNBOOK.md` |

### Partner Forwards

| Partner Type | Forward Content | Expected Links |
|--------------|-----------------|----------------|
| Brokers | `/cyber-insurance-blueprint` | 5-15 per broker |
| MSPs | `/partner-dashboard` | Co-branded trust center |
| Audit firms | `/productized-services` | Audit pack references |
| PE advisors | `/productized-services` | Diligence templates |

### Community Backlinks

| Community | Strategy | Link Target |
|-----------|----------|-------------|
| Reddit (r/cybersecurity, r/netsec) | Answer questions, link pillar | `/trust-center` |
| Hacker News | Technical content, show HN | `/developers` |
| Slack/Discord communities | Value-first answers | `/free-domain-scan` |
| GitHub | Open source contributions | `/developers` |
| LinkedIn groups | Framework discussions | `/blog` |

### Backlink Targets

| Page | Backlink Goal | Source |
|------|---------------|--------|
| `/trust-center` | 50 backlinks/quarter | Partners, community |
| `/blog` | 100 backlinks/quarter | Syndication, guest posts |
| `/free-domain-scan` | 30 backlinks/quarter | Community, tools |
| `/productized-services` | 20 backlinks/quarter | PE advisors, audit firms |

---

## 7. Measurement

### GSC Metrics

| Metric | Tool | Target |
|--------|------|--------|
| Coverage errors | GSC | 0 on money pages |
| Indexed pages | GSC | All public routes |
| CTR | GSC | >3% on target queries |
| Core Web Vitals | GSC | Pass on `/`, `/trust-center`, `/free-domain-scan` |
| Manual actions | GSC | 0 |
| Security issues | GSC | 0 |

### AI Attribution Touchpoints

| Signal | Source | Location |
|--------|--------|----------|
| AI sessions 30d | `attribution_touchpoints` | Supabase |
| AI sources | `chatgpt`, `perplexity`, `claude`, `gemini`, `copilot`, `bing_chat` | `AI_UTM_SOURCES` |
| Money-page sessions | `attribution_touchpoints.landing_path` | `MONEY_PATHS` |
| Scan starts from AI | `product_events` -> `scan_start` | Supabase |

### Supabase Signals

| Signal | Table/Field |
|--------|-------------|
| AI sessions | `attribution_touchpoints` where `utm_source` matches AI sources |
| Money-page traffic | `attribution_touchpoints.landing_path` in `MONEY_PATHS` |
| Scan starts | `product_events` -> `scan_start` |
| SEO assist | Blog/glossary landings -> same-session money page |

### Weekly Rhythm

| Day | Task |
|-----|------|
| Monday | Technical + deploy: `npm run marketing:organic-bootstrap`, GSC coverage, deploy + request indexing |
| Wednesday | Link graph: hub pass, 3+ contextual links to money pages, verify sitemap |
| Friday | AI citation: 2 AI replies with pillar URL + UTM, check AI SEO scorecard |

### SEO Command Center

| Resource | Path |
|----------|------|
| SEO health scorecard | `/seo-command-center` |
| AI SEO scorecard | `/ai-seo-command-center` |
| Kill chain library | `/marketing-kill-chains` |
| Growth playbook | `/growth-playbook` |

### gen:seo Chain

```bash
npm run gen:seo
# runs: gen:llms -> gen:sitemap -> gen:stats
npm run build   # build also runs gen:seo
```

Verify after run:
- `public/llms.txt` includes new pillar paths
- `public/sitemap.xml` excludes auth/demo/owner routes
- No duplicate `<loc>` for same intent

---

## 8. Anti-Patterns

- Publishing blog posts with zero internal links to money pages
- Adding owner-only routes to sitemap
- Indexing thin demo dashboards
- AI citation without UTM tags
- Optimizing for traffic that never reaches `/free-domain-scan` or `/trust-center`
- Hand-editing `public/sitemap.xml` or `public/llms.txt`
- Counting impressions without GSC CTR and pipeline follow-through
- `VITE_PLG_LIVE_DATA_UI=true` on customer pages
- Adding `*` and `#` in publishable content (banned characters)
