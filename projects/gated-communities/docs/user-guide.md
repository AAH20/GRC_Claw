# User Guide

## Gated Communities — User Guide

---

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Dashboard](#dashboard)
- [Managing Tiers](#managing-tiers)
- [Moderation Queue](#moderation-queue)
- [Access Control](#access-control)
- [Member Verification](#member-verification)
- [Reputation System](#reputation-system)
- [Compliance Monitoring](#compliance-monitoring)
- [Analytics](#analytics)
- [Community Governance](#community-governance)
- [Settings](#settings)
- [Troubleshooting](#troubleshooting)

---

## Introduction

Gated Communities is a unified platform for managing gated online communities. This guide walks you through the key features and how to use them effectively.

---

## Getting Started

### Accessing the Platform

1. Open your browser and navigate to the platform URL
2. Log in with your credentials
3. You will be directed to the Dashboard

> **Screenshot Description:** *Login page with email and password fields, "Sign In" button, and "Forgot Password" link. The page has a clean, modern design with the platform logo at the top.*

### Initial Setup

After first login, complete the setup wizard:

1. **Create your first tier** — Define membership levels
2. **Configure access policies** — Set up gating rules
3. **Invite members** — Add your first community members
4. **Set up moderation** — Configure auto-moderation thresholds

> **Screenshot Description:** *Setup wizard with 4 steps, progress indicator at the top, and "Next" / "Back" navigation buttons. Each step has a form with relevant fields and helpful tooltips.*

---

## Dashboard

The Dashboard provides an at-a-glance view of your community health.

> **Screenshot Description:** *Dashboard page with:*
> - *Top row: 4 stat cards showing "Total Members" (1,234), "Active Today" (567), "Pending Moderation" (12), "Health Score" (87/100)*
> - *Middle row: Line chart showing "Member Growth" over 30 days, and a pie chart showing "Tier Distribution"*
> - *Bottom row: "Recent Activity" feed with timestamps and action descriptions*

### Key Metrics

| Metric | Description |
|--------|-------------|
| **Total Members** | All registered community members |
| **Active Today** | Members who performed any action today |
| **Pending Moderation** | Items awaiting review |
| **Health Score** | Overall community health (0-100) |

---

## Managing Tiers

### Viewing Tiers

Navigate to **Tiers** in the main menu.

> **Screenshot Description:** *Tiers list page showing a table with columns: Tier Name, Level (with colored badges — Bronze, Silver, Gold, Platinum, Diamond), Status, Members Count, Monthly Fee, and Actions (Edit, Delete). A "Create Tier" button is in the top-right corner.*

### Creating a Tier

1. Click **Create Tier**
2. Fill in the tier details:

| Field | Description | Required |
|-------|-------------|----------|
| Name | Display name for the tier | Yes |
| Level | Hierarchy level (bronze → diamond) | Yes |
| Description | Brief description | No |
| Requirements | Criteria to achieve this tier | No |
| Benefits | List of benefit identifiers | No |
| Max Members | Maximum members allowed | No |
| Monthly Fee | Subscription fee | No |

> **Screenshot Description:** *Tier creation form with fields listed above. The "Level" field is a dropdown with color-coded options. The "Benefits" field is a multi-select with checkboxes. A "Save" button is at the bottom.*

### Editing a Tier

1. Click the **Edit** icon next to a tier
2. Modify the fields
3. Click **Save**

> **Screenshot Description:** *Tier edit modal with pre-filled fields. The modal has a dark overlay on the tiers list page. "Save" and "Cancel" buttons at the bottom.*

### Deleting a Tier

1. Click the **Delete** icon next to a tier
2. Confirm the deletion in the dialog

> **Screenshot Description:** *Confirmation dialog with warning icon, text "Are you sure you want to delete this tier? This action cannot be undone.", and "Delete" / "Cancel" buttons.*

---

## Moderation Queue

### Viewing the Queue

Navigate to **Moderation** in the main menu.

> **Screenshot Description:** *Moderation queue page with:*
> - *Filter bar at the top: Status dropdown (All, Pending, In Review, Resolved), Priority dropdown (All, Low, Medium, High, Critical)*
> - *Table with columns: Content Preview, Status (colored badge), Priority (colored badge), Age, Assigned To, Actions*
> - *Bulk actions bar: "Approve Selected", "Reject Selected", "Escalate Selected"*

### Reviewing an Item

1. Click on a queue item to open the review panel
2. View the content, context, and AI analysis
3. Take action:

| Action | Description |
|--------|-------------|
| **Approve** | Content is acceptable |
| **Reject** | Content violates policies |
| **Escalate** | Send to human reviewer |
| **Request Info** | Ask for more context |

> **Screenshot Description:* *Review panel sliding in from the right. Shows: content text at top, AI analysis section with toxicity score and flagged keywords, action buttons at the bottom (Approve in green, Reject in red, Escalate in orange).*

### Auto-Moderation

The system automatically flags content based on:
- Toxicity detection (threshold: 0.8)
- Spam patterns
- Prohibited content lists
- User reports

> **Screenshot Description:** *Auto-moderation settings page with toggles for each detection type, threshold sliders, and a "Test" button to simulate detection on sample content.*

---

## Access Control

### Checking Access

Navigate to **Access Control** → **Access Checker**.

> **Screenshot Description:** *Access checker page with:*
> - *Input fields: Member ID (with autocomplete), Resource (dropdown), Action (dropdown)*
> - *"Check Access" button*
> - *Result panel showing: Decision (Allowed/Denied with green/red icon), Reason, Matching Policy, Member's Tier*

### Managing Policies

Navigate to **Access Control** → **Policies**.

> **Screenshot Description:** *Policies list page with table: Policy Name, Tier, Resource, Action, Effect (Allow/Deny), Priority, Status (Active/Inactive toggle), Actions (Edit, Delete). "Create Policy" button in top-right.*

### Creating a Policy

1. Click **Create Policy**
2. Configure the policy:

| Field | Description | Required |
|-------|-------------|----------|
| Name | Policy name | Yes |
| Tier | Which tier this applies to | Yes |
| Resource | Resource being gated | Yes |
| Action | Action being controlled | Yes |
| Effect | Allow or Deny | Yes |
| Conditions | Additional conditions | No |
| Priority | Policy priority (0-100) | No |

> **Screenshot Description:** *Policy creation form with the fields above. The "Conditions" section has an "Add Condition" button that reveals additional fields for time-based rules, quota limits, etc.*

---

## Member Verification

### Verification Dashboard

Navigate to **Verification** in the main menu.

> **Screenshot Description:** *Verification dashboard with:*
> - *Stats row: "Pending Verifications" (5), "Verified Today" (12), "Rejected" (2), "Average Confidence" (92%)*
> - *Table: Member Name, Document Type, Status (Pending/Verified/Rejected), Confidence Score, Risk Level, Submitted Date, Actions*

### Reviewing a Verification

1. Click on a pending verification
2. Review the submitted documents
3. View AI analysis:

| Field | Description |
|-------|-------------|
| **Identity Match** | Confidence score for identity match |
| **Document Authenticity** | Whether document appears genuine |
| **Fraud Indicators** | Any fraud signals detected |
| **Risk Level** | Overall risk assessment (low/medium/high) |

> **Screenshot Description:** *Verification review page with document preview on the left, AI analysis panel on the right showing confidence scores with progress bars, fraud indicators list, and action buttons (Approve, Reject, Request Additional Info).*

---

## Reputation System

### Viewing Reputation

Navigate to **Reputation** in the main menu.

> **Screenshot Description:** *Reputation page with:*
> - *Member search bar at top*
> - *Reputation score gauge (0-100) with color coding*
> - *Trust tier badge*
> - *Badges earned (displayed as icons with tooltips)*
> - *Reputation history table: Date, Action, Points, Running Total*

### Reputation Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Contributions | 30% | Quality and quantity of contributions |
| Engagement | 25% | Community participation level |
| Tenure | 20% | Length of membership |
| Peer Reviews | 15% | Feedback from other members |
| Violations | -10% | Penalty for policy violations |

> **Screenshot Description:** *Reputation factors breakdown page with a weighted bar chart showing each factor's contribution to the overall score, and a detailed table with per-factor scores.*

---

## Compliance Monitoring

### Compliance Dashboard

Navigate to **Compliance** in the main menu.

> **Screenshot Description:** *Compliance dashboard with:*
> - *Compliance score gauge (0-100)*
> - *Active policies count*
> - *Recent violations table: Date, Policy, Member, Severity, Status*
> - *Audit log section with filterable entries*

### Managing Policies

> **Screenshot Description:** *Compliance policies page with:*
> - *Policy list: Name, Description, Rules count, Status (Active/Inactive), Last Updated*
> - *Policy detail view: Rules list with severity levels, violation count per rule, "Edit" and "Deactivate" buttons*

### Audit Log

> **Screenshot Description:** *Audit log page with:*
> - *Filter bar: Date range, Severity (Info/Warning/Error/Critical), Policy, Member*
> - *Table: Timestamp, Action, Actor, Target, Details*
> - *Export button (CSV, JSON)*

---

## Analytics

### Moderation Analytics

Navigate to **Analytics** → **Moderation**.

> **Screenshot Description:** *Moderation analytics page with:*
> - *Date range selector*
> - *Key metrics cards: Total Items, Resolved Items, Avg Resolution Time, Auto-Resolution Rate*
> - *Line chart: Items over time (submitted vs resolved)*
> - *Bar chart: Top violations by type*
> - *Table: Moderator performance (Items handled, Avg time, Accuracy)*

### Community Health Analytics

Navigate to **Analytics** → **Health**.

> **Screenshot Description:** *Health analytics page with:*
> - *Health score trend line chart*
> - *Toxicity level gauge*
> - *Engagement rate chart*
> - *Heatmap: Activity by hour of day and day of week*

---

## Community Governance

### Disputes

Navigate to **Governance** → **Disputes**.

> **Screenshot Description:** *Disputes page with:*
> - *Stats: Open Disputes (3), Resolved This Week (5), Avg Resolution Time (2.3 days)*
> - *Disputes table: Title, Parties, Status (Open/In Review/Resolved), Created Date, Assigned To*
> - *Dispute detail view: Conversation thread, evidence, resolution options*

### Resolving a Dispute

1. Open a dispute
2. Review the conversation and evidence
3. Choose a resolution:

| Resolution | Description |
|------------|-------------|
| **Mediate** | Facilitate discussion between parties |
| **Rule in Favor** | Decide in favor of one party |
| **Escalate** | Send to higher authority |
| **Dismiss** | Close without resolution |

> **Screenshot Description:** *Dispute resolution page with:*
> - *Left panel: Conversation thread between parties*
> - *Right panel: Evidence submitted, AI analysis of the dispute*
> - *Bottom: Resolution options with text area for decision explanation*

---

## Settings

### General Settings

Navigate to **Settings** → **General**.

> **Screenshot Description:** *General settings page with:*
> - *Community name and description fields*
> - *Timezone selector*
> - *Language selector*
> - *Save button*

### Notification Settings

Navigate to **Settings** → **Notifications**.

> **Screenshot Description:** *Notification settings page with:*
> - *Toggle switches for each notification type: Escalation Alerts, Queue Alerts, Review Reminders, Compliance Reports*
> - *Channel configuration: Slack webhook URL, Email address, PagerDuty integration key*
> - *"Test Notification" button*

### API Keys

Navigate to **Settings** → **API Keys**.

> **Screenshot Description:** *API keys management page with:*
> - *Table of existing keys: Name, Created, Last Used, Expires, Actions (Revoke)*
> - *"Generate New Key" button*
> - *Key creation dialog: Name, Expiry period, Scopes (checkboxes for each API module)*

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Cannot log in** | Check credentials; contact admin if account is locked |
| **Moderation queue not updating** | Refresh the page; check WebSocket connection |
| **Verification stuck in pending** | Check document quality; contact support |
| **Access check returns denied** | Verify tier assignment and policy configuration |
| **Analytics not loading** | Check date range; verify data exists for period |

### Getting Help

- **Documentation:** [API Reference](api-reference.md) | [Architecture](architecture.md) | [Deployment Guide](deployment-guide.md)
- **Support:** Contact your system administrator
- **Issue Tracker:** GitHub Issues
