# Monetization Strategy V15

## 1. SKU Matrix

| SKU | ID | $/mo | $/yr | Entitlement | Primary Motion |
|-----|-----|------|------|-------------|----------------|
| GRC Starter | `grc-starter-monthly` | 79 | 790 | `grc_starter` | Scan to trust-center nurture |
| GRC Pro | `grc-pro-monthly` | 199 | 1,990 | `grc_pro` | Audit season + Vanta/Drata displacement |
| Platform Pro | `platform-pro-bundle` | 229 | -- | GRC Pro + LibreMap Pro | CISO GRC + CTI one invoice |
| GRC Enterprise | `grc-enterprise-monthly` | 499 | 4,990 | `grc_enterprise` | PE diligence + board narrative |
| LibreMap Pro | `libremap-pro` | 49 | -- | CTI tier | Threat intel analyst + bundle upsell |
| LibreMap Enterprise | `libremap-enterprise` | 149-199 | -- | CTI enterprise tier | SOC teams + MSSP |
| Threat Cluster Team | `threat-cluster-team` | 199 | -- | CTI addon | Collaborative threat analysis |
| Operator Playbook Pass | `learning-pro` | 12 | -- | Learning | Upsell from Starter |

### Add-on SKUs

| Add-on | ID | $/mo | Bundle with |
|--------|-----|------|-------------|
| Questionnaire | `grc-questionnaire` | 59 | GRC Pro+ |
| Crosswalk | `grc-crosswalk` | 39 | GRC Pro+ |
| Vendor Risk | `grc-vendor-risk` | 49 | GRC Pro+ |
| Auditor Pack | `grc-auditor-pack` | 49 | GRC Pro+ |

### One-time Cash (not MRR)

| Service | Price | Purpose |
|---------|-------|---------|
| Instant Audit | ~499 | Tripwire to subscription |
| CDD Pack | 99/export | Per-export evidence |
| TDD Sprints | 25K-150K | Deep diligence |
| vCISO Retainer | 5K/mo | Services MRR if contracted monthly |

Source: `src/lib/grc/entitlements.ts`, `src/lib/settings/accountPlatformConfig.ts`

---

## 2. MRR Math: $30K Target in 30 Days

### Scenario A: SMB Volume (Default Sprint)

| Line | Units | MRR |
|------|-------|-----|
| GRC Pro | 80 | 15,920 |
| Platform Pro | 40 | 9,160 |
| GRC Starter | 40 | 3,160 |
| Add-ons (blended $50) | 30 | 1,500 |
| LibreMap Pro | 20 | 980 |
| **Total** | **210** | **30,720** |

### Scenario B: Enterprise-Heavy (Fewer Logos)

| Line | Units | MRR |
|------|-------|-----|
| GRC Enterprise | 40 | 19,960 |
| Platform Pro | 25 | 5,725 |
| GRC Pro | 20 | 3,980 |
| Add-ons | 15 | 750 |
| **Total** | **100** | **30,415** |

### Scenario C: Broker Batch (One Partner Week)

| Event | Units | MRR |
|-------|-------|-----|
| 3 brokers x 10 clients GRC Pro | 30 | 5,970 |
| 2 MSPs x 15 Platform Pro | 30 | 6,870 |
| Organic + displacement (remainder) | 90 mixed | ~17,880 |
| **Total** | **150** | **~30,720** |

### Unit Economics

| Metric | Value |
|--------|-------|
| Average ACV | ~$147 (blended SKU mix) |
| Gross margin | ~90% (SaaS) |
| CAC target | <$200 per subscriber |
| Payback period | <2 months |
| LTV:CAC ratio | >5:1 |

### Weekly MRR Checkpoints

| Day | Cumulative MRR |
|-----|----------------|
| 7 | $2,000 |
| 14 | $10,000 |
| 21 | $20,000 |
| 30 | $30,000 |

---

## 3. Broker/MGA Channel Playbook (B2B2B Motion)

### Channel Mechanics

| Element | Detail |
|---------|--------|
| Motion | Broker recommends GRC to portfolio clients |
| Value prop | Single invoice, bundle discount, co-branded trust center |
| Seats per intro | 5-15 GRC Pro or Platform Pro |
| Broker rev share | 10-20% first-year referral fee |
| Enablement | `/broker-os`, `/cyber-insurance-blueprint`, trust-center co-brand |

### Broker Persona

| Attribute | Value |
|-----------|-------|
| Pain | Client questionnaires eat audit team time |
| Trigger | Audit season or renewal cycle |
| Close path | `/trust-center#tco-compare` + blueprint card |
| Batch potential | High (1 broker = 5-15 seats) |

### Broker Playbook Steps

1. **Identify** insurance brokers, MGAs, CPAs in SMB-to-mid-market
2. **Forward** `/trust-center#tco-compare` + blueprint card via email
3. **Demo** co-branded trust center with client portal
4. **Close** broker signs up 5-15 clients on GRC Pro
5. **Expand** broker upsells to Platform Pro, add-ons

### Nurture Sequence

| Day | Email | CTA |
|-----|-------|-----|
| 0 | Broker blueprint card | `/cyber-insurance-blueprint` |
| 3 | TCO comparison story | `/trust-center#tco-compare` |
| 7 | Case study: MSP onboarded 12 clients | `/broker-os` |
| 14 | Add-on catalog + pricing | `/trust-center#grc-pricing` |
| 21 | Co-brand trust center offer | `/partner-dashboard` |

---

## 4. PE Diligence Motion (100-Day Cyber)

### Motion Definition

| Element | Detail |
|---------|--------|
| Trigger | PE firm acquires portfolio company |
| Timeline | 100-day post-close cyber standardization |
| SKU | GRC Enterprise ($499/mo) or Platform Pro ($229/mo) |
| Batch potential | Medium (port cos across portfolio) |
| Close path | `/productized-services` then `/settings?tab=billing` |

### PE Diligence Steps

1. **Pre-close** PE advisor requests cyber posture report
2. **Diligence** GRC Enterprise runs 867-control baseline
3. **Close** PE approves budget for post-close GRC
4. **Standardize** All portfolio companies on GRC Pro or Enterprise
5. **Expand** Add-ons: crosswalk, vendor risk, auditor pack

### PE Package

| Package | SKU | Price | Includes |
|---------|-----|-------|----------|
| Diligence Sprint | Instant Audit | 499 one-time | Baseline report |
| Portfolio Standard | GRC Pro x 5 | 199 x 5 = 995/mo | Standardized framework |
| Board Narrative | GRC Enterprise | 499/mo | Executive reporting + evidence vault |

---

## 5. vCISO White-Label Pricing

### Tiered Pricing

| Tier | Seats | Price/mo | Includes |
|------|-------|----------|----------|
| Solo | 1-3 | 5K | GRC Pro + audit packs |
| Team | 4-10 | 12K | GRC Enterprise + crosswalk + vendor risk |
| Enterprise | 11-25 | 25K | Platform Pro + full add-on suite |
| MSSP | 26+ | Custom | Volume pricing + co-brand |

### White-Label Features

| Feature | Detail |
|---------|--------|
| Co-branded trust center | Broker/client sees MSP brand |
| Evidence vault access | Client evidence shared with MSP |
| Reporting dashboard | MSP aggregates portfolio compliance |
| Audit pack export | PDF/CSV for client audits |
| Revenue share | MSP keeps 80%, platform takes 20% |

### vCISO Enablement

| Resource | Path |
|----------|------|
| Partner dashboard | `/partner-dashboard` |
| White-label guide | `/partner-onboarding` |
| Co-brand builder | `/trust-center/customize` |
| Revenue calculator | `/partner-revenue-estimator` |

---

## 6. Compliance API Economy (Metered Tiers)

### API Pricing Tiers

| Tier | Requests/mo | Price/mo | Overage |
|------|-------------|----------|---------|
| Free | 1,000 | 0 | N/A |
| Starter | 10,000 | 79 | $0.008/request |
| Pro | 100,000 | 199 | $0.005/request |
| Enterprise | Unlimited | 499 | N/A |

### API Endpoints (Revenue-Generating)

| Endpoint | Tier Required | Usage |
|----------|---------------|-------|
| `/api/v1/controls` | Starter+ | Framework control lookup |
| `/api/v1/evidence` | Pro+ | Evidence ingestion + validation |
| `/api/v1/crosswalk` | Pro+ | Framework crosswalk mapping |
| `/api/v1/audit-pack` | Enterprise | Full audit pack generation |
| `/api/v1/vendor-risk` | Pro+ | Third-party risk assessment |

### Metering Implementation

| Component | Location |
|-----------|----------|
| Rate limiter | `api/lib/rateLimiter.ts` |
| Usage tracking | `api/lib/apiUsage.ts` |
| Billing integration | `api/lib/grcEntitlements.ts` |
| Dashboard | `/settings?tab=api-usage` |

---

## 7. Data Syndication Pricing (Crosswalk Corpus Licensing)

### Licensing Model

| License Type | Price | Includes |
|-------------|-------|----------|
| Single framework | 5K/yr | One crosswalk matrix |
| Multi-framework | 15K/yr | All 867 controls + crosswalk |
| Enterprise | 30K/yr | Full corpus + API + support |
| Reseller | Custom | Revenue share on downstream |

### Syndication Targets

| Target | Value Prop |
|--------|------------|
| Audit firms | Pre-mapped crosswalks reduce engagement time |
| GRC platforms | License corpus for native integrations |
| Insurance carriers | Risk scoring data for underwriting |
| Consulting firms | Framework mapping for client engagements |

### Data Products

| Product | Format | Delivery |
|---------|--------|----------|
| Crosswalk matrix | CSV/JSON | Download |
| Control corpus | API | REST endpoints |
| Audit pack templates | PDF/DOCX | Export |
| Risk scoring data | JSON | Webhook |

---

## 8. PLG Funnel: Scan to Trust-Center to Checkout to Expand

### Funnel Stages

| Stage | Action | Conversion Target |
|-------|--------|-------------------|
| Recon | `/free-domain-scan` | 35-45% scan to email |
| Nurture | Email sequence | 3-5% email to checkout |
| Checkout | PayPal hosted link | 25-30% Starter to Pro (30d) |
| Expand | Add-ons + bundles | 15-20% Pro to Enterprise |

### PLG Entry Points

| Entry Point | Path | Persona |
|-------------|------|---------|
| Free scan | `/free-domain-scan` | Founder/SMB |
| Trust center | `/trust-center` | GRC lead |
| Cyber insurance | `/cyber-insurance-blueprint` | Broker |
| Threat intel | `/threat-cluster` | CTI analyst |
| Productized services | `/productized-services` | PE/enterprise |

### Nurture Sequence

| Day | Email | CTA |
|-----|-------|-----|
| 0 | Scan results + value prop | `/trust-center` |
| 3 | Framework gap analysis | `/trust-center#grc-pricing` |
| 7 | Case study | `/productized-services` |
| 14 | Add-on catalog | `/trust-center#add-ons` |
| 21 | Urgency: audit season | `/consultation` |

### Entitlement Flow

```
Scan -> Email capture -> Starter checkout -> Pro upsell -> Enterprise
  |           |                |               |              |
  v           v                v               v              v
/domain_scans  email_leads  subscriptions  subscriptions  subscriptions
                                            + addons       + addons
```

---

## 9. Competitive Displacement Playbook

### vs Vanta

| Vanta Weakness | A2Z Advantage | Close Path |
|----------------|---------------|------------|
| Per-framework pricing | 867 controls, one price | `/trust-center#tco-compare` |
| Manual evidence collection | Automated evidence vault | `/trust-center` |
| No CTI integration | LibreMap Pro bundled | `/libre-threat-intel` |
| Slow audit prep | 30-day sprint to SOC 2 | `/productized-services` |

### vs Drata

| Drata Weakness | A2Z Advantage | Close Path |
|----------------|---------------|------------|
| Limited framework support | ISO 42001, NIST AI RMF native | `/blog/comprehensive-grc-framework-catalog-2026` |
| No white-label | Broker/MSP white-label | `/broker-os` |
| Generic compliance | GRC + CTI + SIEM in one | `/trust-center` |
| Enterprise-only pricing | SMB entry at $79/mo | `/trust-center#grc-pricing` |

### vs ServiceNow

| ServiceNow Weakness | A2Z Advantage | Close Path |
|---------------------|---------------|------------|
| Enterprise lock-in | SMB-friendly pricing | `/trust-center#grc-pricing` |
| Complex implementation | Self-serve setup | `/start` |
| No PLG motion | Free scan entry | `/free-domain-scan` |
| High TCO | 60% cost savings | `/trust-center#tco-compare` |

### vs Wiz

| Wiz Weakness | A2Z Advantage | Close Path |
|--------------|---------------|------------|
| CNAPP only | Full GRC + compliance | `/trust-center` |
| No audit readiness | Audit packs + crosswalk | `/productized-services` |
| Cloud-only | Hybrid + on-prem | `/developers` |
| No evidence vault | Evidence vault included | `/trust-center` |

### Displacement Plays

| Play | Trigger | Offer |
|------|---------|-------|
| Renewal objection | "Vanta too expensive" | GRC Pro at 40% savings |
| Audit failure | "Failed SOC 2 audit" | Enterprise + audit sprint |
| PE diligence | "Need portfolio standard" | GRC Pro x 5 bundle |
| CTI gap | "No threat intel" | Platform Pro bundle |

---

## 10. Revenue Verification

### Supabase Signals

| Signal | Table/Field |
|--------|-------------|
| New subscription | `subscriptions`, `products` |
| GRC tier | `organizations.plan_tier`, `metadata.grc_addons` |
| CTI tier | org metadata / plg libre entitlements API |
| Scan lead | `domain_scans`, `email_leads` |
| Consult | `consultation_requests` |
| Attribution | `attribution_touchpoints`, `product_events` |
| Orders (one-time) | `orders`, `payments` |

### Code Touchpoints

| Concern | Location |
|---------|----------|
| Subscription catalog UI | `SettingsSubscriptionPanel.tsx`, `accountPlatformConfig.ts` |
| GRC checkout | `src/lib/grc/checkout.ts`, `openGrcCheckout` |
| Generic PayPal | `src/lib/monetization.ts`, `openOfferCheckout` |
| Entitlements API | `api/lib/grcEntitlements.ts`, `api/lib/handlers/plg/grc.ts` |
| Nurture routing | `api/lib/emailNurture.ts`, `api/lib/distributionAutomation.ts` |
| Kill chains | `src/lib/seo/marketingKillChains.ts` |
| Competitive TCO | `TrustCenterTcoCompare.tsx`, comparison blogs |

### Env Prerequisites (Revenue)

| Variable | Purpose |
|----------|---------|
| `VITE_PAYPAL_GRC_*_PAYMENT_LINK` | Hosted checkout per tier |
| `VITE_PAYPAL_PLATFORM_PRO_PAYMENT_LINK` | Bundle |
| `VITE_PAYPAL_LIBREMAP_*` | CTI |
| `SUPABASE_*` | Entitlements persistence |
| `RESEND_*`, `CRON_SECRET` | Nurture to checkout |
| `MARKETING_OWNER_EMAIL` | Ops surfaces |

---

## 11. Anti-Patterns

- Counting one-time audit revenue toward MRR target
- Broad LinkedIn-only motion with no email, broker, or community lanes
- Ten SKUs in one DM
- Fake logos, fabricated payment confirmed walls
- `VITE_PLG_LIVE_DATA_UI=true` on customer pages
- Announcing $30K MRR without Supabase subscription proof
- Ignoring same-email rule (checkout email = auth email)
- Showing pricing menus instead of single-path offers
