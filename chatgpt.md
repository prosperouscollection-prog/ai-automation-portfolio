# Genesis AI Systems — Project Context Log
# Use this file to restore full context at the start of any new session.
# Update the "Current Session" section and append to "History" after each session.

---

## Project Identity

**Business:** Genesis AI Systems
**Founder:** Trendell Fordham | Detroit, MI
**Site:** genesisai.systems | info@genesisai.systems
**Purpose:** Done-for-you AI systems for local businesses. Freelance agency.
**Stack repo:** github.com/prosperouscollection-prog/ai-automation-portfolio

---

## V1 Architecture Snapshot (as of March 31, 2026)

### Revenue Corridor
```
NEW_LEAD → OUTREACH_SENT → DEMO_BOOKED → PROPOSAL_SENT →
PAYMENT_RECEIVED → INTAKE_COMPLETE → DEPLOYED → LOST
```

### System of Record Rules (immutable)
- **HubSpot** = pipeline SOR
- **HoneyBook** = proposals / contracts / intake SOR (API unverified — manual send in V1)
- **Stripe** = payment SOR
- **GitHub Actions** = agent execution runtime
- **Telegram** = alerting and approval gates only (never source of truth)
- **n8n** = async workflow glue between systems
- **Resend** = transactional email

### Approval Gates (only two)
1. Outreach email → founder SEND/SKIP via Telegram (10-min timeout)
2. Deployment start → founder DEPLOY/HOLD via Telegram

### Not in V1 Stack
Apollo.io, Lindy AI, Instantly.ai, Twilio, Hunter.io (quarantined as optional)

---

## What Was Built — Session: March 31, 2026

### New files created (untracked — not yet committed)
| File | Purpose |
|------|---------|
| `V1_IMPLEMENTATION_PLAN.md` | Master architecture plan, pipeline stages, day-by-day build order |
| `v1-revenue-system/approval_flow.py` | Telegram SEND/SKIP/DEPLOY/HOLD approval gate module |
| `v1-revenue-system/hubspot_pipeline.py` | HubSpot pipeline stage enum + deal update helpers |
| `v1-revenue-system/honeybook_client.py` | HoneyBook client (API unverified — returns None on failure, caller alerts founder) |
| `v1-revenue-system/stripe_handler.py` | Stripe payment link creation and webhook parsing |
| `v1-revenue-system/hunter_lookup.py` | Hunter.io email lookup (quarantined — not in V1 critical path) |
| `v1-revenue-system/__init__.py` | Package init |
| `.github/workflows/scripts/crm_pipeline_agent.py` | Stale deal detection, pipeline summary to Telegram |
| `.github/workflows/scripts/intake_agent.py` | HoneyBook intake form send after payment, completion tracking |
| `.github/workflows/crm_pipeline_agent.yml` | Runs crm_pipeline_agent every 2 hours |
| `.github/workflows/intake_agent.yml` | Runs intake_agent every 2.5 hours |
| `n8n/workflows/calendly-to-hubspot.json` | Calendly booking → HubSpot DEMO_BOOKED |
| `n8n/workflows/demo-done-to-proposal.json` | /demo-done Telegram command → proposal prep instructions (n8n Telegram Trigger) |
| `n8n/workflows/payment-to-intake.json` | Stripe payment → HubSpot PAYMENT_RECEIVED + intake trigger |
| `n8n/workflows/README.md` | n8n setup instructions, credential requirements |

### Modified files
| File | What changed |
|------|-------------|
| `.github/workflows/scripts/sales_agent.py` | Added Telegram SEND/SKIP approval gate before every outreach email send |
| `.github/workflows/scripts/telegram_bot.py` | Registered /demo-done comment (n8n handles it), removed handle_demo_done() method |
| `.env.example` | Added all V1 revenue keys; removed GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT; Hunter.io commented |

### Architecture corrections applied this session
1. Pipeline reduced from 14 stages to 7 forward stages + LOST terminal outcome
2. Sheets drift removed — HubSpot is the only CRM SOR, no Sheets syncs in agents
3. HoneyBook email fallback removed — failure returns None, founder is alerted for manual send
4. Approval gates scoped to two only (outreach + deploy)
5. Hunter.io quarantined as optional — not on V1 critical path
6. Telegram entry point for /demo-done: n8n Telegram Trigger (not telegram_bot.py webhook)
7. **PROPOSAL_SENT timing fixed**: HubSpot no longer advances automatically on /demo-done. Stage only advances after founder manually confirms proposal was sent from HoneyBook dashboard.
8. HoneyBook direct API marked UNVERIFIED — demo-done-to-proposal.json removed HoneyBook API call

---

## Current Blockers

| Blocker | Impact | Resolution |
|---------|--------|------------|
| n8n not deployed | /demo-done Telegram command, Calendly→HubSpot, Stripe→HubSpot all inactive | Deploy n8n to n8n.genesisai.systems |
| HoneyBook API unverified | Proposal and intake sends are manual | Verify at app.honeybook.com/app/settings/integrations; test endpoint; update honeybook_client.py if confirmed |
| GitHub secrets not set | All agents will fail silently or skip their core actions | Add HUBSPOT_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, RESEND_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET |
| HubSpot pipeline not created | No stages to advance deals through | Create custom deal pipeline with 7 forward stages + LOST terminal outcome in HubSpot dashboard |
| HoneyBook templates not created | Proposal and intake sends have no template to reference | Create Starter proposal, Growth proposal, and intake form templates in HoneyBook |
| Calendly + Stripe webhooks not registered | Bookings and payments don't reach n8n | Register webhook URLs after n8n is live |

---

## Next Priority (in order)

1. **Deploy n8n** — import 3 workflow JSONs, set env vars, activate workflows
2. **Set GitHub secrets** — enables all agents to connect to real services
3. **Create HubSpot pipeline** — 7 forward stages + LOST terminal outcome, exactly as defined in V1_IMPLEMENTATION_PLAN.md
4. **Test Day 1 path manually** — enter test lead, walk all 7 forward stages by hand, confirm Telegram alerts fire
5. **Verify or rule out HoneyBook API** — determines whether proposal/intake can eventually be automated

---

## Session History

### Session 1 — March 31, 2026
**Scope:** Full V1 revenue corridor build from scratch
**Built:** V1_IMPLEMENTATION_PLAN.md, approval_flow.py, hubspot_pipeline.py, honeybook_client.py, stripe_handler.py, hunter_lookup.py, crm_pipeline_agent.py, intake_agent.py, all n8n workflow JSONs, GitHub Actions YMLs
**Corrections applied:** 8 architecture corrections (pipeline, Sheets, HoneyBook, approvals, Hunter, Telegram entry point, PROPOSAL_SENT timing, HoneyBook API status)
**Status at close:** All files built, untracked in git, not yet committed. n8n not deployed. GitHub secrets not set. HoneyBook API unverified. No live revenue path yet.
**Commit range:** No new commits — all work is in the worktree as untracked files
