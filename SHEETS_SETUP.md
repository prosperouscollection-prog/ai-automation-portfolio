# Genesis AI Systems — Google Sheets Master Dashboard Setup

## Overview
This guide documents the master operations dashboard for Genesis AI Systems, located in Google Sheets. It details the required spreadsheet, tab names, formatting, branding, and config recommendations to ensure compliance with Genesis AI Systems standards and operational requirements.

---

## Spreadsheet Information
- **Spreadsheet Name:** `Genesis AI Systems — Operations`
- **Owner:** Genesis AI Systems (info@genesisai.systems)
- **Location:** Google Drive (suggested: Genesis AI Systems → Operations folder)
- **Access:**
  - Owner: Trendell Fordham (Founder)
  - Editors: Team as needed
  - Viewers: Read-only to certain agents if required

---

## Branding Requirements
- **Header Row Background:** Navy `#0f172a`
- **Header Row Text:** White
- **Accent Color:** Electric Blue `#2563eb`
- **Sheet Names:** Prefix every tab with `Genesis AI Systems — ` followed by tab function (see below)
- **Logo (optional):** Insert in top-left of each tab if desired
- **Font Recommendation:** Google Sheets default or use Montserrat/Sans-serif for closer branding
- **Tagline:** Done-for-you AI automation for local businesses
- **Contact:** info@genesisai.systems | (313) 400-2575

---

## Required Tabs & Layouts

### 1. Genesis AI Systems — Website Leads
- **Purpose:** Track all web form, chat, and email-captured leads.
- **Sample Columns**:
  - Date Captured
  - Full Name
  - Email
  - Phone
  - Business Name
  - Source (e.g. Website, Chat, Demo Form)
  - AI Score
  - Status (New, Contacted, Qualified, Won, Lost)
  - Notes

### 2. Genesis AI Systems — Inbound Calls
- **Purpose:** Log inbound calls, callers, timestamps, outcomes.
- **Sample Columns**:
  - Date/Time
  - Caller Name
  - Caller Number
  - Call Duration
  - Call Recording Link
  - Disposition (Answered, Missed, Callback Needed)
  - Assigned Agent
  - Notes

### 3. Genesis AI Systems — Content Calendar
- **Purpose:** Plan and track all social/email/video posts.
- **Sample Columns**:
  - Scheduled Date
  - Content Type (Video, Email, LinkedIn, etc)
  - Title/Topic
  - Status (Draft, Scheduled, Published)
  - Owner
  - Channel/Platform
  - Asset Link

### 4. Genesis AI Systems — Client Roster
- **Purpose:** List all active and past clients.
- **Sample Columns**:
  - Client Name
  - Contact Name
  - Email
  - Phone
  - Business Address
  - Status (Active, Paused, Past)
  - Start Date
  - Systems Delivered
  - Notes

### 5. Genesis AI Systems — Revenue Tracker
- **Purpose:** Track revenue by month and system.
- **Sample Columns**:
  - Date Received
  - Client Name
  - System/Service
  - Amount (USD)
  - Payment Method
  - Invoice Number
  - Status (Paid, Unpaid, Overdue)

### 6. Genesis AI Systems — Outreach CRM
- **Purpose:** Organize all cold/warm outbound sales efforts and pipeline.
- **Sample Columns**:
  - Company Name
  - Contact Name
  - Email
  - Phone
  - Outreach Date
  - Last Contact
  - Status (Contacted, Discovery, Demo, Proposal, Closed Won/Lost)
  - Assigned Rep
  - Next Action
  - Notes

### 7. Genesis AI Systems — Agent Health Log
- **Purpose:** Record AI agent uptime, health, and incident response.
- **Sample Columns**:
  - Date/Time
  - Agent Name
  - Incident Type
  - Duration/Affected
  - Root Cause
  - Resolution
  - Logged By
  - Preventative Actions
  - Status (Resolved, Investigating)

### 8. Genesis AI Systems — Financial Summary
- **Purpose:** High-level snapshot of cash flow, costs, and key metrics.
- **Sample Columns**:
  - Month
  - Total Revenue
  - Total Expenses
  - Gross Margin
  - Net Profit
  - Active Clients
  - Churn Rate (%)
  - MRR (Monthly Recurring Revenue)
  - Runway (if relevant)

---

## Formatting & Styling Tips
- **Freeze header row** on every tab
- Use conditional formatting for statuses (e.g. green for Paid/Won/Active, red for Overdue/Lost/Paused, blue for In-Progress)
- Use alternating row colors (light gray or white/very light blue) for readability
- Left-align text, right-align numerical columns
- Use data validation for select-value columns (dropdowns: Status, System/Service, etc)
- Number and currency columns should use Google Sheets number/currency formatting
- Sheet tab color: use Electric Blue `#2563eb` for active/important tabs

---

## Automation & API Integration
- **Automation examples:**
  - New "Website Leads" automatically triggers Slack/Email alert, updates Outreach CRM tab, and timestamps
  - Inbound Calls tab integrates with Vapi/telephony provider for auto-log
  - Content Calendar can be synced to Notion or social schedulers
- **Security:**
  - Only share with authorized personnel
  - Use Google Workspace 2FA
  - Protect summary or critical formula cells (use Sheet protection settings)

---

## Sharing & Permissions
- **Who should edit:** Genesis AI Systems team members
- **Who can view:** Others as needed (e.g., auditing, client view)
- **Owner should be:** info@genesisai.systems
- Protect summary/critical formula cells from unintentional edits

---

## Example Tab Setup (Screenshot Reference)
_Include visual examples in future iterations as needed (contact Trendell Fordham to request screenshots or templates)_

---

## Maintenance
- Review tabs monthly for data quality
- Archive completed or old data annually (move to separate tabs or sheets)
- Regularly audit sharing settings
- Keep branding updated if logo/colors are changed

---

## Additional Genesis AI Systems Branding & Compliance
- Always use full name: **Genesis AI Systems** in sheet and tab titles
- Tagline (optional, recommended in header area): "Done-for-you AI automation for local businesses"
- Footer row (optional): `genesisai.systems | info@genesisai.systems | (313) 400-2575`
- For reports/exports: header must show Genesis AI Systems, footer and signature by "Trendell Fordham, Founder"

---

## Questions or Support
For help with setup or automations, contact:

**Trendell Fordham**  
Founder, Genesis AI Systems  
info@genesisai.systems  
(313) 400-2575

---

**Genesis AI Systems** — Done-for-you AI automation for local businesses  
https://genesisai.systems
