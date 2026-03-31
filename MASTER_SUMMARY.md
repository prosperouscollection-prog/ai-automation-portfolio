# Genesis AI Systems — Master Summary
# Trendell Fordham | Detroit, MI
# genesisai.systems | info@genesisai.systems
# Version: V1 Revenue Corridor | March 31, 2026

---

## What We Are

A real freelance AI agency building done-for-you AI systems for local businesses in Detroit.
Founded March 2026. Customer Zero: Genesis AI Systems itself.

V1 mission: close the first paying client through a verified, end-to-end revenue corridor.

---

## V1 Revenue Corridor

The full path from lead discovery to live client:

```
Lead discovered → Outreach approved → Demo booked → Proposal sent →
Payment received → Intake form sent → Intake complete → Deployed
```

Every stage is tracked in HubSpot. Every failure alerts the founder via Telegram.

---

## V1 Pipeline Stages (HubSpot)

| Stage | What it means |
|-------|---------------|
| NEW_LEAD | HOT lead found and scored by Lead Generator |
| OUTREACH_SENT | Outreach approved by founder via Telegram SEND/SKIP gate |
| DEMO_BOOKED | Calendly booking confirmed (automated via n8n webhook) |
| PROPOSAL_SENT | Founder sent proposal from HoneyBook dashboard, then manually advanced |
| PAYMENT_RECEIVED | Stripe payment event received (automated via n8n webhook) |
| INTAKE_COMPLETE | Client completed HoneyBook intake form (webhook → n8n → HubSpot) |
| DEPLOYED | Founder approved /deploy, QA passed |
| LOST | Founder manually moved, any stage |

---

## V1 Tool Stack (locked — do not add without founder decision)

| Tool | Role | Status |
|------|------|--------|
| HubSpot | Pipeline system of record | Active |
| HoneyBook | Proposals, contracts, intake forms — system of record | Active (manual send — API unverified) |
| Stripe | Payment system of record | Active |
| GitHub Actions | Agent execution runtime | Active |
| Render | Demo server runtime | Active |
| n8n | Async workflow glue (Calendly → HubSpot, Stripe → HubSpot, Telegram Trigger) | Pending deployment |
| Resend | Transactional email — outreach, reports | Active |
| Telegram | Founder alerts and approval gates — NOT source of truth | Active |

**Not in V1 locked stack:** Apollo.io, Lindy AI, Instantly.ai, Twilio, Hunter.io (optional, quarantined).

---

## Two Approval Gates in V1

These are the only two actions that require founder approval before execution:

1. **Outreach email** — Sales Agent sends a SEND/SKIP request via Telegram. No email sends without founder response. Timeout 10 minutes per lead.
2. **Deployment start** — Deploy Agent sends a DEPLOY/HOLD request. No deployment without founder approval.

Everything else in the corridor runs automatically or is triggered by the founder via Telegram command.

---

## Agents Built (GitHub Actions)

| Agent | Schedule | Purpose |
|-------|----------|---------|
| Lead Generator | Daily 6am | Scrapes and scores HOT leads, pushes to HubSpot |
| Sales Agent | Every 6hrs | Reads HOT leads from Sheets, sends outreach with approval gate |
| CRM Pipeline Agent | Every 2hrs | Stale deal detection, pipeline summary to Telegram |
| Intake Agent | Every 2.5hrs | Sends HoneyBook intake form after payment, tracks completion |
| Deploy Agent | On push + founder /deploy | Deploys client site after DEPLOY approval |
| QA Agent | Hourly | Validates site health, alerts on failures |
| Marketing Agent | Daily 7am | Content creation (triggered by /content Telegram command) |
| Orchestration Agent | Hourly | Morning digest, system health |
| Telegram Bot | On demand (via GitHub workflow_dispatch or n8n) | Routes Telegram commands |

---

## HoneyBook — Manual Until Verified

HoneyBook is the system of record for all proposals, contracts, and intake forms.
**The HoneyBook direct REST API is unverified** — `https://api.honeybook.com/v1` is provisional.

V1 behavior:
- Proposals are sent manually from app.honeybook.com (triggered by `/demo-done` Telegram command which provides client details)
- Intake forms are attempted via `honeybook_client.py`; on failure, founder receives Telegram alert to send manually
- HubSpot advances to PROPOSAL_SENT only after the founder manually confirms by updating the deal in HubSpot

**Before automating HoneyBook sends:** verify API access at app.honeybook.com/app/settings/integrations.

---

## n8n Workflows Built

| Workflow | Trigger | Path |
|----------|---------|------|
| calendly-to-hubspot | Calendly webhook | Calendly booking → HubSpot DEMO_BOOKED |
| demo-done-to-proposal | Telegram Trigger (/demo-done) | Validate stage, send founder proposal prep instructions |
| payment-to-intake | Stripe webhook | Payment received → HubSpot PAYMENT_RECEIVED + intake form |

**n8n is not yet deployed.** All three workflows are imported and ready. Deploy to n8n.genesisai.systems before activating.

---

## Telegram Commands (telegram_bot.py)

`/status` `/leads` `/agents` `/deploy` `/prospects` `/followup` `/content` `/revenue` `/pipeline` `/report` `/clients` `/help`

`/demo-done <deal_id>` — handled directly by n8n Telegram Trigger workflow (not telegram_bot.py)

---

## What Is and Is Not Automated in V1

**Automated (no founder action needed):**
- Lead discovery and scoring
- HubSpot stage updates from Calendly, Stripe, HoneyBook intake webhook
- Telegram alerts on every stage transition and failure
- Outreach email sends (after SEND approval)
- Intake form send attempt (alerts founder if HoneyBook fails)

**Manual (founder action required):**
- Demo calls
- Proposal send (from HoneyBook dashboard)
- HubSpot advance to PROPOSAL_SENT
- Final deployment approval
- All exception handling flagged by Telegram alerts

---

## Current Status (March 31, 2026)

**Built and ready:**
- All Python agents and GitHub Actions YMLs
- V1 HubSpot pipeline definition (7 forward stages + LOST terminal outcome)
- n8n workflow JSON templates (3 workflows)
- Approval flow module
- HoneyBook client module (with verified-API gate)
- Stripe handler
- Telegram bot

**Pending before first lead can run the full corridor:**
1. Deploy n8n to n8n.genesisai.systems and import 3 workflows
2. Configure n8n credentials (HubSpot, Telegram, Stripe)
3. Register Calendly and Stripe webhook URLs in their dashboards
4. Add all GitHub secrets: `HUBSPOT_ACCESS_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `RESEND_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
5. Create HubSpot custom pipeline with the 7 lean stages
6. Create HoneyBook proposal templates (Starter, Growth) and intake form template

**First revenue target:** $500 setup + $150/mo (Starter plan) — first client this month.
