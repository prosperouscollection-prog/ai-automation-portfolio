# Genesis AI Systems — V1 Implementation Master Plan
## Phase 1: Lead-to-Live Revenue Corridor
## Date: March 31, 2026

---

## 1. Executive Summary

This plan converts the existing 11-agent system from a demonstration/alerting layer into a working revenue corridor. The core path: a qualified lead enters HubSpot, gets outreach, books a demo, receives a proposal, pays, gets onboarded, deployed, QA'd, and goes live — with the founder closing every deal manually.

**What exists today:** 11 agents running on GitHub Actions + Google Sheets + HubSpot + Telegram + Resend. Agents find leads and generate reports but do not take external action. No outreach sends. No proposal automation. No payment detection. No onboarding trigger.

**What V1 builds:** One clean end-to-end corridor from lead discovery to live client, with Telegram approval gates, HoneyBook proposals, Stripe payment detection, and automated onboarding triggers.

**What stays manual in V1:** Founder demo call, custom scope decisions, final deployment approval, failed QA decisions, exception handling.

---

## 2. Architecture Lock

```
SYSTEM OF RECORD RULES (immutable):
- HubSpot       = revenue pipeline system of record
- HoneyBook     = proposal / contract / intake system of record
- Stripe        = payment system of record
- GitHub Actions = deployment and agent execution runtime
- Render        = demo server runtime
- Google Sheets  = operational data layer for lead logs, agent logs (NOT CRM)
- Telegram      = alerting and approval at high-risk control points only
                  (never source of truth — read HubSpot for state)
- n8n           = async workflow glue between systems
- Resend        = transactional email (NOT used to bypass HoneyBook records)

ROLE OWNERSHIP (immutable):
- Sales Agent           owns outreach to leads
- Founder               owns demo calls and closing
- Proposal/Closing Agent owns HoneyBook proposal and contract send
- Intake Agent          owns post-payment HoneyBook intake trigger and completion tracking
- Deploy Agent          owns deployment execution and state tracking
- QA Agent              owns validation and failure reporting (results in Telegram + GitHub)
- Telegram              is alerting/control only — never source of truth

TELEGRAM APPROVAL GATES (only two in V1):
- Outreach email to a lead requires SEND/SKIP from founder
- Deployment start requires DEPLOY/HOLD from founder

AUTOMATED WITHOUT APPROVAL (do not add gates here):
- Lead Generator → HubSpot NEW_LEAD
- Calendly booking → HubSpot DEMO_BOOKED
- /demo-done command → Telegram proposal prep (n8n fetches client info, founder sends from HoneyBook manually, then manually advances HubSpot to PROPOSAL_SENT)
- Stripe payment received → HoneyBook intake form send (fully automated)
- HoneyBook intake complete → HubSpot INTAKE_COMPLETE
- QA pass → HubSpot DEPLOYED + Telegram alert
```

---

## 3. V1 Pipeline Stages (HubSpot)

Lean V1 path only. QA state is tracked in GitHub Actions + Render, not in the sales pipeline.

| Stage | HubSpot Stage ID | Owner | Trigger |
|-------|------------------|-------|---------|
| NEW_LEAD | new_lead | Lead Generator | Lead discovered and scored HOT |
| OUTREACH_SENT | outreach_sent | Sales Agent | Founder approved via Telegram SEND |
| DEMO_BOOKED | demo_booked | Founder | Calendly booking (n8n webhook) |
| PROPOSAL_SENT | proposal_sent | Founder (manual) | Founder sends from HoneyBook dashboard, then manually advances in HubSpot (HoneyBook API unverified in V1) |
| PAYMENT_RECEIVED | payment_received | Stripe | Stripe webhook → n8n (automated) |
| INTAKE_COMPLETE | intake_complete | Intake Agent | HoneyBook intake webhook → n8n |
| DEPLOYED | deployed | Deploy Agent | Founder approves /deploy, QA passes |
| LOST | lost | Founder | Manual, any stage |

**What is NOT a pipeline stage in V1:**
- Outreach drafted (internal Sales Agent state only)
- Reply received (flag in Telegram, no stage change needed)
- Demo completed (handled by /demo-done Telegram command inline)
- Contract signed (HoneyBook event, moves directly to PAYMENT_RECEIVED when paid)
- QA running (GitHub Actions job status, not a CRM stage)

---

## 4. V1 Build Order (14 Days)

### Day 1: Prove the Revenue Path
1. Create HubSpot custom deal pipeline with the 7 lean stages above
2. Enter one test lead manually at NEW_LEAD
3. Walk the test lead through the full path manually (no automation yet) to confirm each stage makes sense
4. Confirm Telegram alerts fire on manual HubSpot stage changes
5. Confirm Stripe test payment event reaches n8n (send test event from Stripe dashboard)

**Day 1 does NOT include:** Twilio cleanup, DNS cleanup, Hunter.io. Those are cleanup tasks that belong later in the week.

### Day 2-3: Sales Corridor
6. Upgrade Sales Agent with outreach drafting + Telegram SEND/SKIP approval flow
7. Wire Calendly webhook → n8n → HubSpot DEMO_BOOKED
8. CRM Pipeline Agent: stale deal detection + pipeline summary to Telegram

### Day 5-6: Proposal + Payment
9. Create HoneyBook proposal templates (Starter $500, Growth $3500)
10. Deploy n8n, import demo-done-to-proposal.json, activate Telegram Trigger (already built)
11. Wire Stripe webhook → n8n → HubSpot PAYMENT_RECEIVED
12. Build payment detection notification to Telegram

### Day 7-8: Onboarding + Intake
13. Create HoneyBook intake form template
14. Build n8n workflow: PAYMENT_RECEIVED → send intake form
15. Build Intake Agent to monitor form completion
16. Wire intake completion → HubSpot INTAKE_COMPLETE stage

### Day 9-10: Deploy + QA
17. Upgrade Deploy Agent to handle client deployments
18. Build founder approval gate for deployment start
19. Upgrade QA Agent with client-specific checks
20. Wire QA pass → HubSpot DEPLOYED + Telegram celebration

### Day 11-12: Command Center + Orchestration
21. Wire Telegram commands to real data (/leads, /pipeline, /revenue)
22. Build Master Orchestration real morning digest
23. Wire /approve and /send commands to approval flow
24. End-to-end corridor test with synthetic lead

### Day 13-14: Stabilization
25. Run full corridor test (lead → live)
26. Fix broken handoffs
27. Document all workflows
28. Confirm V1 stability criteria

---

## 5. V1 Role-by-Role Specs

---

### 5.1 Lead Generator Agent

**Purpose:** Find local businesses, score them, push HOT leads to HubSpot as NEW_LEAD.

**Current state:** Finds 25 businesses via Yelp, scores with Claude, saves to Sheets + HubSpot. Working.

**V1 changes (minimal):**
- Ensure HOT leads create HubSpot deals at NEW_LEAD stage with phone number
- Telegram summary: "X HOT leads found today — [industry]"
- Sheets Leads tab write continues as before (operational log, not CRM)

**Note on email:** Hunter.io is optional support infrastructure, not required for V1 core path. Sales outreach can start with a phone call or Calendly link if email is not available.

**Inputs:**
- Yelp API (business discovery, existing)
- Claude API (lead scoring, existing)

**Outputs:**
- HubSpot: new deal at NEW_LEAD stage
- Google Sheets: Leads tab updated (agent log)
- Telegram: daily HOT lead summary

**Trigger:** Daily 6am via GitHub Actions (existing — no changes to schedule)

**Success criteria:**
- HOT leads appear in HubSpot at NEW_LEAD
- Telegram summary fires daily
- No duplicate deals created for same business

---

### 5.2 CRM / Pipeline Agent

**Purpose:** Keep HubSpot pipeline stages accurate. Sync between Sheets, HubSpot, and agent actions. Detect stale deals.

**Current state:** Does not exist as a distinct agent. Sales Agent partially covers this.

**V1 implementation:**
- New lightweight agent that runs every 2 hours
- Reads HubSpot deals, checks for stage inconsistencies
- Flags deals stuck >48hrs in any pre-demo stage
- Ensures Sheets Pipeline tab matches HubSpot
- Does NOT take external actions — reporting only

**Inputs:**
- HubSpot API (deal stages)
- Google Sheets Pipeline tab

**Outputs:**
- Sheets Pipeline tab synced
- Telegram alert for stale deals
- HubSpot deal properties updated (last_checked timestamp)

**Trigger:** Every 2 hours via GitHub Actions

**Success criteria:**
- Sheets and HubSpot pipeline match within 15 min
- Stale deals flagged in Telegram within 2 hours

**Files to create:**
- ADD: `.github/workflows/scripts/crm_pipeline_agent.py`
- ADD: `.github/workflows/crm_pipeline_agent.yml`

---

### 5.3 Sales Agent

**Purpose:** Draft personalized outreach for HOT leads, get founder approval via Telegram, send email, track replies.

**Current state:** Reads HOT leads from Sheets, saves to Pipeline + HubSpot, sends Telegram + Resend report. Does not contact anyone.

**V1 upgrade:**
- For each HOT lead with email: draft personalized outreach using Claude
- Send draft to Telegram with approval prompt
- On SEND reply: send email via Resend, log to Outreach Log, update HubSpot to OUTREACH_SENT
- On SKIP reply: mark as skipped, move to next
- Monitor for replies (Resend inbound webhook or periodic inbox check)
- On reply detected: send Telegram alert only — no HubSpot stage change (REPLIED is not a pipeline stage)

**Inputs:**
- HubSpot deals at NEW_LEAD stage (with contact email)
- Claude API (draft personalization)
- Telegram (approval responses)

**Outputs:**
- Outreach email sent via Resend
- HubSpot stage: NEW_LEAD → OUTREACH_SENT (OUTREACH_DRAFTED is internal Sales Agent state only; REPLIED is a Telegram signal only — neither is a HubSpot stage)
- Sheets Outreach Log updated
- Telegram alerts for approvals and replies

**Trigger:** Every 6 hours via GitHub Actions (existing schedule)

**Approval required:** YES — Telegram SEND/SKIP for every outreach email

**Success criteria:**
- No email sends without founder SEND approval
- Outreach logged to both HubSpot and Sheets
- Reply detection within 1 hour

**File changes:**
- EDIT: `.github/workflows/scripts/sales_agent.py` — add draft + approval + send flow
- DEPENDS ON: `approval_flow.py` module

---

### 5.4 Proposal / Closing Agent

**Purpose:** Support founder in sending HoneyBook proposal after demo and detecting payment.

**Current state:** `/demo-done` Telegram command built. HoneyBook direct API is unverified — proposal send is manual.

**V1 implementation:**
- Founder types `/demo-done <deal_id>` in Telegram (n8n Telegram Trigger receives it)
- n8n validates HubSpot stage is `demo_booked`
- n8n sends founder client details (name, email, plan) + HoneyBook instructions via Telegram
- **Founder sends proposal manually from app.honeybook.com**
- Founder manually advances HubSpot deal to `proposal_sent` after confirming send
- Stripe webhook on payment → n8n → HubSpot PAYMENT_RECEIVED (automated)
- Telegram notification at each step

**Note on CONTRACT_SIGNED:** Not a V1 pipeline stage. HoneyBook contract signing is tracked in HoneyBook. HubSpot advances directly from PROPOSAL_SENT to PAYMENT_RECEIVED when Stripe payment is received.

**Inputs:**
- HubSpot deal at DEMO_BOOKED (set by Calendly webhook via n8n)
- Founder `/demo-done <deal_id>` Telegram command
- Stripe webhooks (payment detection — automated)

**Outputs:**
- Telegram: client details + HoneyBook send instructions
- HubSpot PROPOSAL_SENT (manual — founder sets after sending)
- HubSpot PAYMENT_RECEIVED (automated — Stripe webhook → n8n)
- Stripe payment recorded

**Trigger:** n8n Telegram Trigger (listens for /demo-done from founder's chat_id)

**Success criteria:**
- /demo-done sends founder Telegram with correct client name, email, and plan within 30 seconds
- Founder can open HoneyBook and send proposal in under 2 minutes
- After founder manually advances HubSpot to PROPOSAL_SENT, stage is correct
- Payment detected by Stripe webhook → n8n → HubSpot PAYMENT_RECEIVED (automated)
- Telegram notified at each step

**Files to create:**
- ADD: n8n workflow: `proposal-flow` (HubSpot → HoneyBook → Stripe)
- ADD: `.github/workflows/scripts/proposal_agent.py` (fallback/monitoring)

---

### 5.5 Intake / Onboarding Agent

**Purpose:** Send intake form on payment, monitor completion, prepare client for deployment.

**Current state:** Does not exist.

**V1 implementation:**
- n8n workflow: PAYMENT_RECEIVED → send HoneyBook intake form
- Intake form collects: business name, hours, services, phone numbers, special requests
- On form completion: update HubSpot to INTAKE_COMPLETE, alert Telegram
- Telegram to founder: "[Company] intake complete. Use /deploy to start deployment."

**Inputs:**
- HubSpot deal at PAYMENT_RECEIVED
- HoneyBook intake form completion webhook → n8n

**Outputs:**
- HoneyBook intake form sent (or Telegram alert for manual send if HoneyBook fails)
- HubSpot stage: INTAKE_COMPLETE
- Telegram notification with /deploy prompt to founder

**Trigger:** n8n webhook from Stripe payment confirmation

**Approval required:** YES — founder must reply DEPLOY before deployment starts

**Success criteria:**
- Intake form sent within 10 minutes of payment
- Form responses captured in Sheets + HubSpot
- Founder notified and can trigger deployment

**Files to create:**
- ADD: n8n workflow: `intake-flow` (Stripe → HoneyBook intake → Sheets)
- ADD: `.github/workflows/scripts/intake_agent.py`

---

### 5.6 Deploy Agent

**Purpose:** Execute client deployment after founder approval.

**Current state:** Checks 2 URLs after push. No client deployment logic.

**V1 upgrade:**
- On founder DEPLOY approval: execute deployment checklist (provision services, configure Vapi, etc.)
- On QA pass: update HubSpot to DEPLOYED, send Telegram confirmation
- Telegram progress updates during deployment

**Manual in V1:** Actual service provisioning is manual (Vapi setup, chat widget config, etc.). Deploy Agent tracks status and coordinates handoffs, not the provisioning itself. DEPLOYING and QA_RUNNING are not HubSpot stages — they are GitHub Actions job states.

**Inputs:**
- HubSpot deal at INTAKE_COMPLETE
- Founder DEPLOY approval via Telegram

**Outputs:**
- HubSpot stage: DEPLOYED (set on QA pass)
- Telegram progress updates and final "Client is LIVE!" alert

**Trigger:** Founder Telegram DEPLOY command

**Success criteria:**
- Deployment tracked end-to-end in HubSpot
- QA automatically triggered post-deployment
- Telegram updates at each deployment step

**File changes:**
- EDIT: `project8-agent-system/agent_system/agents/deploy_agent.py` — add client deployment tracking
- ADD: `.github/workflows/scripts/client_deploy_agent.py`

---

### 5.7 QA Agent

**Purpose:** Run checks on deployed client systems, report pass/fail.

**Current state:** Checks 2 URLs return 200 on push.

**V1 upgrade:**
- Client-specific QA: check client's Vapi agent responds, chat widget loads, endpoints return real data
- Standard checks: all 13 sitemap URLs, demo endpoints, Stripe links
- On all pass: update HubSpot to DEPLOYED, Telegram "Client is LIVE!" celebration
- On fail: Telegram alert with which check failed, founder decides next step

**Inputs:**
- Client deployment details from Sheets
- Vapi API (agent health)
- HTTP checks (endpoints)

**Outputs:**
- HubSpot stage: DEPLOYED (on pass) or stays at INTAKE_COMPLETE with Telegram failure alert (on fail)
- Telegram: pass/fail report with details
- Sheets: QA log

**Trigger:** Automatic after Deploy Agent completes

**Success criteria:**
- All client-specific checks run within 5 minutes of deploy completion
- Clear pass/fail report in Telegram
- HubSpot stage accurately reflects QA result

**File changes:**
- EDIT: `project8-agent-system/agent_system/agents/qa_agent.py` — add client-specific checks
- ADD: QA check registry for per-client configurations

---

### 5.8 Telegram Command Center

**Purpose:** Founder's mobile control panel for the entire revenue system.

**Current state:** Commands return mock data. No real actions.

**V1 upgrade — real commands:**

| Command | Action | Data Source |
|---------|--------|-------------|
| /leads | Today's HOT leads with emails | Sheets Leads tab |
| /pipeline | Deal summary by stage | HubSpot API |
| /send [name] | Approve outreach for named lead | Approval flow module |
| /skip [name] | Skip outreach for named lead | Approval flow module |
| /demo-done [name] | Mark demo completed, trigger proposal | HubSpot + n8n |
| /deploy [name] | Approve deployment start | Deploy Agent trigger |
| /revenue | MRR + setup fees collected | Sheets Revenue tab |
| /status | All agent health + last run times | GitHub Actions API |
| /help | List all commands | Static |

**Inputs:**
- Telegram messages from founder (chat ID verified)
- HubSpot, Sheets, GitHub Actions APIs

**Outputs:**
- Telegram responses with real data
- Triggers to approval flow, deploy agent, proposal agent

**Trigger:** Real-time Telegram webhook (or polling)

**Success criteria:**
- All commands return real data within 5 seconds
- /send and /deploy require CONFIRM follow-up
- No action without explicit founder command

**File changes:**
- EDIT: `.github/workflows/scripts/sms_command_center.py` — wire real data sources
- EDIT: `.github/workflows/scripts/telegram_bot.py` — add new commands

---

### 5.9 Minimal Master Orchestration

**Purpose:** Daily briefing + system health monitoring.

**Current state:** Morning Telegram with mock data from demo server.

**V1 upgrade:**
- 8am daily briefing with real data:
  - Leads found overnight (count + top 3)
  - Outreach sent yesterday (count + any replies)
  - Pipeline value by stage
  - Revenue collected this month
  - All agent health (last run pass/fail)
  - ONE specific action item for the day
- Hourly: check all agents ran successfully, alert on failure

**Inputs:**
- Sheets: all tabs
- HubSpot: pipeline summary
- GitHub Actions: workflow run status
- Demo server: /stats/health

**Outputs:**
- 8am Telegram briefing
- Hourly health check (alert only on failure)

**Trigger:** 8am daily + hourly (existing schedule)

**Success criteria:**
- Morning briefing contains zero mock data
- Action item is specific and actionable
- Failures detected and alerted within 1 hour

**File changes:**
- EDIT: `.github/workflows/scripts/` master orchestration script
- EDIT: `.github/workflows/master_orchestration.yml`

---

### 5.10 Founder Role

**Purpose:** Human closer, approver, exception handler.

**Manual actions in V1:**
1. Review and approve/skip outreach emails (Telegram SEND/SKIP)
2. Conduct demo calls (Calendly bookings)
3. Mark demos as completed (Telegram /demo-done)
4. Approve deployment start (Telegram /deploy)
5. Handle failed QA decisions
6. Handle exceptions and edge cases
7. Custom scope decisions for non-standard deals

**Founder does NOT need to:**
- Check HubSpot manually (pipeline synced automatically)
- Send proposals (auto after demo-done)
- Send intake forms (auto after payment)
- Check QA results (Telegram alerts)
- Update deal stages manually (agents handle this)

---

## 6. V1 Tool Configuration Plan

### 6.1 HubSpot Setup

```
ACTION: Create custom deal pipeline "Genesis Revenue Pipeline"
STAGES (in order):
  new_lead → outreach_drafted → outreach_sent → replied →
  demo_booked → demo_completed → proposal_sent →
  contract_signed → payment_received → onboarding →
  deploying → qa_running → live → lost

CUSTOM PROPERTIES to add:
  - lead_source (Yelp, Google Maps, Website, Referral)
  - lead_score (HOT, WARM, COLD)
  - owner_email (from Hunter.io)
  - proposal_type (Starter, Growth)
  - stripe_payment_id
  - honeybook_project_id
  - intake_completed (boolean)
  - deploy_approved_at (datetime)
  - qa_result (pass, fail)
  - client_go_live_date (datetime)
```

### 6.2 Hunter.io Setup

```
ACTION: Create account, add API key to GitHub secrets
SECRET: HUNTER_API_KEY
TIER: Free (25 lookups/mo) — upgrade to $34/mo at 3+ leads/day
USAGE: Lead Generator calls POST /v2/domain-search for each HOT lead domain
```

### 6.3 HoneyBook Setup

```
ACTION: Create 3 templates
TEMPLATES:
  1. Proposal — Starter ($500 setup + $150/mo)
  2. Proposal — Growth ($3,500 setup + $300/mo)
  3. Intake Form — client onboarding questionnaire

INTAKE FORM FIELDS:
  - Business name
  - Business type / industry
  - Business hours
  - Services offered
  - Phone numbers to forward
  - Current website URL
  - Special requests / notes
  - Preferred AI greeting style

API INTEGRATION:
  - HONEYBOOK_API_KEY → GitHub secrets
  - Webhook URL for contract signed: n8n.genesisai.systems/webhook/honeybook-signed
```

### 6.4 Stripe Webhook Setup

```
ACTION: Configure Stripe webhook endpoint
ENDPOINT: n8n.genesisai.systems/webhook/stripe-payment
EVENTS: checkout.session.completed, payment_intent.succeeded
SECRET: STRIPE_WEBHOOK_SECRET → GitHub secrets

EXISTING: Starter + Growth buy links already on site
NEW: Create payment links for proposals (different from site links)
  - Proposal Starter: $500 one-time
  - Proposal Growth: $3,500 one-time
  - Monthly Starter: $150/mo recurring
  - Monthly Growth: $300/mo recurring
```

### 6.5 n8n Workflow Plan

```
WORKFLOW 1: "Calendly → HubSpot" (NEW)
  Trigger: Calendly webhook (invitee.created)
  Action: Find matching HubSpot deal by email → update to DEMO_BOOKED

WORKFLOW 2: "Demo Done → Proposal" (BUILT — demo-done-to-proposal.json)
  Trigger: n8n Telegram Trigger (/demo-done <deal_id> from founder)
  Action: Validate HubSpot stage == demo_booked → send founder client details + HoneyBook instructions
  Note: HubSpot does NOT auto-advance. Founder sends from HoneyBook manually, then advances HubSpot to PROPOSAL_SENT.
  Note: CONTRACT_SIGNED is not a V1 pipeline stage. HubSpot moves directly PROPOSAL_SENT → PAYMENT_RECEIVED.

WORKFLOW 3: "Payment → Intake" (BUILT — payment-to-intake.json)
  Trigger: Stripe webhook (payment succeeded)
  Action: Update HubSpot to PAYMENT_RECEIVED → send HoneyBook intake form (or Telegram alert if HoneyBook fails) → Telegram alert

WORKFLOW 4: "Intake Complete" (NOT BUILT — n8n webhook to be built when HoneyBook webhooks verified)
  Trigger: HoneyBook webhook (form.completed) → n8n
  Action: Update HubSpot to INTAKE_COMPLETE → Telegram DEPLOY prompt to founder
  Note: This transition is currently handled by intake_agent.py (GitHub Actions, polls every 2.5hrs)

NOT BUILT (removed from V1):
  - "Contract Signed" workflow — CONTRACT_SIGNED stage removed from V1 lean pipeline
  - Sheets population on intake complete — Sheets removed from V1 locked stack
```

### 6.6 Calendly Webhook Setup

```
ACTION: Configure Calendly webhook
ENDPOINT: n8n.genesisai.systems/webhook/calendly-booked
EVENT: invitee.created
PURPOSE: Auto-update HubSpot deal to DEMO_BOOKED when lead books via Calendly
```

---

## 7. V1 Workflow Trigger Map

```
Lead Generator (6am daily)
  └─→ HOT lead with email → HubSpot NEW_LEAD
       └─→ Sales Agent (6hr cycle) drafts outreach
            └─→ Telegram: "SEND or SKIP?"
                 └─→ SEND → Resend email → HubSpot OUTREACH_SENT
                      └─→ Reply detected → Telegram alert only (no HubSpot stage change)
                           └─→ Lead books Calendly → n8n → HubSpot DEMO_BOOKED
                                └─→ Founder conducts demo (MANUAL)
                                     └─→ /demo-done → n8n → Telegram: client details + HoneyBook instructions
                                          └─→ Founder sends proposal from HoneyBook (manual)
                                               └─→ Founder advances HubSpot → PROPOSAL_SENT (manual)
                                                    └─→ Stripe payment → n8n → PAYMENT_RECEIVED (automated)
                                                         └─→ n8n → intake form attempt → completion → INTAKE_COMPLETE
                                                              └─→ /deploy approval → Deploy Agent → DEPLOYED
                                                                   └─→ QA Agent → pass → Telegram: "Client is LIVE!"

CRM/Pipeline Agent (2hr) — monitors all stages, flags stale deals
Master Orchestration (8am + hourly) — daily briefing + health checks
Telegram Command Center (real-time) — founder mobile control
```

---

## 8. New Files to Create

```
portfolio/
├── v1-revenue-system/
│   ├── README.md                          # V1 system overview
│   ├── approval_flow.py                   # Telegram SEND/SKIP/CONFIRM module
│   ├── hubspot_pipeline.py                # HubSpot deal stage management
│   ├── hunter_lookup.py                   # Hunter.io email lookup wrapper
│   ├── stripe_handler.py                  # Stripe webhook + payment link helpers
│   └── honeybook_client.py                # HoneyBook API wrapper
│
├── .github/workflows/scripts/
│   ├── crm_pipeline_agent.py              # NEW — pipeline sync + stale detection
│   ├── intake_agent.py                    # NEW — onboarding form monitoring
│   ├── proposal_agent.py                  # NEW — proposal monitoring/fallback
│   ├── client_deploy_agent.py             # NEW — client deployment tracking
│   ├── lead_generator_agent.py            # EDIT — add Hunter.io
│   ├── sales_agent.py                     # EDIT — add outreach + approval
│   ├── sms_command_center.py              # EDIT — real commands
│   └── telegram_bot.py                    # EDIT — new commands
│
├── .github/workflows/
│   ├── crm_pipeline_agent.yml             # NEW — every 2 hours
│   └── (existing YMLs edited as needed)
│
├── n8n/workflows/
│   ├── calendly-to-hubspot.json           # NEW
│   ├── demo-done-to-proposal.json         # NEW
│   ├── contract-signed.json               # NEW
│   ├── payment-to-intake.json             # NEW
│   └── intake-complete.json               # NEW
```

---

## 9. V1 Acceptance Criteria

### Corridor Test (must pass before V1 = stable)

- [ ] Lead Generator finds a lead with a valid owner email
- [ ] Sales Agent drafts personalized outreach for that lead
- [ ] Founder receives Telegram with draft, replies SEND
- [ ] Email delivers via Resend from info@genesisai.systems
- [ ] HubSpot deal moves to OUTREACH_SENT
- [ ] Outreach logged in Sheets Outreach Log tab
- [ ] (Simulated) Reply detected, Telegram alert fires — confirm HubSpot stage does NOT change
- [ ] Calendly booking creates DEMO_BOOKED in HubSpot
- [ ] /demo-done command sends Telegram with correct client details within 30 seconds
- [ ] Founder sends proposal from HoneyBook dashboard and manually advances HubSpot to PROPOSAL_SENT
- [ ] Stripe payment detected, HubSpot auto-advances to PAYMENT_RECEIVED
- [ ] Intake form send attempted via HoneyBook (or Telegram alert to send manually if fails)
- [ ] Intake completion triggers INTAKE_COMPLETE stage
- [ ] /deploy command triggers deployment tracking
- [ ] QA checks run automatically post-deploy
- [ ] QA pass moves deal to DEPLOYED
- [ ] Telegram reports every stage change
- [ ] Morning briefing shows real pipeline data
- [ ] /pipeline command returns accurate stage counts
- [ ] /revenue command returns real numbers

### System Health (must pass)

- [ ] All agents run without error for 48 consecutive hours
- [ ] No Twilio references in any YML or Python file
- [ ] HubSpot and Sheets pipeline data match
- [ ] Telegram commands return real data, not mock
- [ ] Resend domain verified and emails delivering

---

## 10. Definition of V1 Stability

V1 is stable when ALL of the following are true:

1. **One full corridor tested:** A lead has moved from NEW_LEAD through DEPLOYED (can be synthetic)
2. **Pipeline stages reliable:** HubSpot stages update correctly at every transition
3. **No leaking handoffs:** Every stage transition triggers the next step without manual intervention (except founder approval gates)
4. **QA working:** Deploy → QA → pass/fail → correct HubSpot update + Telegram alert
5. **Telegram alerts working:** Every stage change produces a Telegram notification
6. **Founder can see status:** /pipeline, /revenue, /leads, /status all return real data
7. **48-hour clean run:** All agents pass for 48 consecutive hours
8. **Morning briefing real:** 8am digest contains zero mock data

---

## 11. 14-Day V1 Execution Plan

### Day 1 (Foundation)
- [ ] Strip Twilio from 5 remaining workflow YMLs (existing Task 1)
- [ ] Verify Resend domain DNS — SPF/DKIM/DMARC in Cloudflare (existing Task 2)
- [ ] Create HubSpot custom deal pipeline with 14 stages
- [ ] Add HubSpot custom properties (lead_source, owner_email, etc.)
- [ ] Sign up for Hunter.io, add HUNTER_API_KEY to GitHub secrets

### Day 2 (Lead Generator Upgrade)
- [ ] Add Hunter.io lookup to lead_generator_agent.py
- [ ] Create hunter_lookup.py wrapper module
- [ ] Test: Lead Generator finds leads with emails
- [ ] Verify leads appear in HubSpot at NEW_LEAD stage with email
- [ ] Confirm Telegram summary includes email status

### Day 3 (Approval Flow)
- [ ] Build approval_flow.py — Telegram SEND/SKIP/CONFIRM module
- [ ] Integrate with telegram_bot.py for listening to replies
- [ ] Test: send approval prompt, receive SEND, confirm callback fires
- [ ] Test: send approval prompt, receive SKIP, confirm skip logged

### Day 4 (Sales Agent Upgrade)
- [ ] Add outreach drafting to sales_agent.py (Claude personalization)
- [ ] Wire approval flow: draft → Telegram → SEND → Resend
- [ ] Add Outreach Log tab writing
- [ ] Confirm HubSpot advances to OUTREACH_SENT on SEND (OUTREACH_DRAFTED is internal agent state only — not written to HubSpot)
- [ ] Test full flow: lead with email → draft → approve → send → logged

### Day 5 (CRM Pipeline Agent)
- [ ] Create crm_pipeline_agent.py
- [ ] Create crm_pipeline_agent.yml (every 2 hours)
- [ ] Wire HubSpot ↔ Sheets Pipeline tab sync
- [ ] Add stale deal detection (>48hr in pre-demo stage)
- [ ] Test: create deal, wait, confirm stale alert fires

### Day 6 (Calendly + Reply Detection)
- [ ] Configure Calendly webhook → n8n
- [ ] Build n8n workflow: Calendly booking → HubSpot DEMO_BOOKED
- [ ] Build reply detection in Sales Agent (Resend inbound webhook or polling)
- [ ] Test: book Calendly → confirm HubSpot updates
- [ ] Test: reply to outreach email → confirm Telegram alert fires and HubSpot stage does NOT change

### Day 7 (HoneyBook Setup)
- [ ] Create HoneyBook Starter proposal template
- [ ] Create HoneyBook Growth proposal template
- [ ] Create HoneyBook intake form template
- [ ] Verify HoneyBook API access at app.honeybook.com/app/settings/integrations
- [ ] If API confirmed: add HONEYBOOK_API_KEY to GitHub secrets and test honeybook_client.py endpoint
- [ ] If API not available: document manual send process, keep current V1 flow

### Day 8 (Proposal Flow)
- [ ] Deploy n8n, import demo-done-to-proposal.json, configure Telegram Bot credential, activate
- [ ] Test: /demo-done <deal_id> → Telegram returns correct client details
- [ ] Send test proposal from HoneyBook, manually advance HubSpot to PROPOSAL_SENT, confirm stage

### Day 9 (Payment + Intake Flow)
- [ ] Configure Stripe webhook → n8n endpoint
- [ ] Build n8n workflow: Stripe payment → HubSpot PAYMENT_RECEIVED
- [ ] Build n8n workflow: payment → send HoneyBook intake form
- [ ] Build intake_agent.py for form completion monitoring
- [ ] Test: Stripe test payment → intake form sends → completion → INTAKE_COMPLETE

### Day 10 (Deploy + QA)
- [ ] Create client_deploy_agent.py with deployment tracking
- [ ] Wire /deploy Telegram command → deployment start
- [ ] Add client-specific QA checks to qa_agent.py
- [ ] Wire QA pass → HubSpot DEPLOYED
- [ ] Test: /deploy → deploy tracking → QA runs → pass/fail → correct HubSpot stage

### Day 11 (Command Center)
- [ ] Wire /leads to Sheets real data
- [ ] Wire /pipeline to HubSpot real data
- [ ] Wire /revenue to Sheets Revenue tab
- [ ] Wire /status to GitHub Actions run status
- [ ] Add /demo-done, /deploy, /send, /skip commands
- [ ] Test all commands return real, accurate data

### Day 12 (Master Orchestration)
- [ ] Replace mock data in morning digest with real sources
- [ ] Add pipeline value by stage
- [ ] Add outreach stats from Outreach Log
- [ ] Add ONE specific action item logic
- [ ] Test: 8am briefing fires with real data, action item makes sense

### Day 13 (Full Corridor Test)
- [ ] Create synthetic lead in HubSpot at NEW_LEAD
- [ ] Walk through entire corridor: outreach → demo → proposal → payment → intake → deploy → QA → live
- [ ] Document every failure point
- [ ] Fix broken handoffs
- [ ] Re-run corridor test until clean

### Day 14 (Stabilization)
- [ ] Start 48-hour stability monitoring
- [ ] Verify all acceptance criteria pass
- [ ] Update CLAUDE_CODE_START.md with V1 status
- [ ] Document all n8n workflows
- [ ] Final Telegram command audit

---

## 12. Risks, Assumptions, and Blockers

### Assumptions
- Hunter.io free tier (25/mo) is sufficient for initial lead volume
- HoneyBook has API access for proposal creation (verify before Day 7)
- Stripe webhook can be routed through n8n on existing DigitalOcean droplet
- Calendly free tier supports webhooks (verify)
- Resend domain verification will complete within 24 hours

### Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| HoneyBook API doesn't support programmatic proposal send | Blocks proposal automation | Fall back to email template with Stripe link |
| Hunter.io free tier exhausted | Leads without emails | Upgrade to paid ($34/mo) or add Apollo.io fallback |
| n8n droplet can't handle webhook volume | Missed events | Monitor with uptime check, upgrade droplet if needed |
| Calendly free doesn't support webhooks | No auto DEMO_BOOKED | Founder manually runs /demo-booked [name] |
| Resend inbound not available on current plan | No reply detection | Periodic inbox polling via IMAP or manual /replied command |

### Blockers (must resolve before starting)
1. Resend domain verification (Day 1)
2. HoneyBook API access confirmation (before Day 7)
3. Stripe webhook secret configured (before Day 9)

---

## 13. Founder Operating Rules for V1

1. **Check Telegram 3x/day** — morning briefing, midday pipeline check, evening outreach approvals
2. **Approve outreach within 4 hours** — SEND or SKIP. Unanswered drafts block the pipeline
3. **Mark demos done immediately** — /demo-done [name] triggers proposal. Delay = lost deal momentum
4. **Approve deployments within 24 hours** — /deploy [name] after intake complete
5. **Review failed QA** — decide retry or manual fix. QA failures don't auto-resolve
6. **Do not update HubSpot stages manually** — agents own stage transitions. Manual overrides cause sync issues
7. **Exception: Lost deals** — founder can mark deals as LOST at any stage via /lost [name]

---

## 14. Change-Control Rules

1. **No new tools without a role gap** — if the current stack can do it, use the current stack
2. **No new agents without a handoff gap** — if an existing agent can own the task, extend it
3. **Pipeline stages are frozen** — no adding/removing/renaming stages without full corridor retest
4. **System-of-record rules are immutable** — HubSpot = pipeline, HoneyBook = proposals, Stripe = payments
5. **Every n8n workflow must have a Telegram failure alert** — silent failures are unacceptable
6. **Every agent edit requires:** (a) py_compile check (b) workflow run test (c) log review
7. **Approval mode cannot be downgraded to auto mode** in V1 — that's a V2 decision after 30+ clean days
