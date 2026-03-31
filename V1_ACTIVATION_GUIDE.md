# Genesis AI Systems — V1 Activation Guide
# Use this file to activate the locked V1 revenue corridor.
# Architecture is frozen. This is an activation checklist, not a design document.

**Source legend:**
- ✅ Confirmed in repo — exists in a committed or staged file
- 🔧 Manual setup required — you must do this; no code does it for you
- ⚠️ Unverified — verify before proceeding; do not assume

---

## Step 1 — Deploy n8n

**Files confirmed in repo:** `n8n/docker-compose.yml`, `n8n/Caddyfile`, `n8n/setup.sh`

### 1a. Provision the droplet
🔧 In DigitalOcean, create a droplet if one doesn't already exist:
- Ubuntu 22.04 LTS, minimum 1 GB RAM / 1 vCPU (Basic $6/mo works)
- Note the IP address

### 1b. Point DNS
🔧 In Cloudflare (where `genesisai.systems` is managed):
- Add an **A record**: `n8n` → your droplet IP
- Proxy status: **DNS only** (grey cloud), not proxied
- TTL: Auto

### 1c. Run setup on the droplet
✅ `n8n/setup.sh` does exactly this — SSH in and run it:
```
ssh root@<DROPLET_IP>
# paste the contents of n8n/setup.sh and run it
```
The script installs Docker, generates `N8N_PASSWORD` and `N8N_ENCRYPTION_KEY`,
saves them to `/opt/n8n/.env`, and prints credentials.

**Save the printed credentials immediately. They are only shown once.**

### 1d. Upload config files and start
🔧 From your Mac:
```
scp n8n/docker-compose.yml n8n/Caddyfile root@<DROPLET_IP>:/opt/n8n/
ssh root@<DROPLET_IP> "cd /opt/n8n && docker compose up -d"
```

### 1e. Set n8n environment variables
✅ `docker-compose.yml` sets n8n app config but does NOT set the API keys the
workflows use. Add these to `/opt/n8n/.env` on the droplet, then restart:
```
HUBSPOT_ACCESS_TOKEN=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```
Restart: `docker compose up -d`

**Do not add `HONEYBOOK_API_KEY`.** ⚠️ Unverified — HoneyBook API endpoint is
provisional. Omit until verified.

### Verify before moving on
- `https://n8n.genesisai.systems` loads a login page
- Login with `trendell` / generated password
- SSL certificate is active (Caddy handles this automatically)

**Likely blocker:** DNS propagation (up to 10 min). Verify:
`dig n8n.genesisai.systems` should return your droplet IP.

---

## Step 2 — Configure Credentials and Secrets

Two separate systems need keys: **GitHub Actions** (runs agents) and **n8n** (runs workflows).

### 2a. GitHub Actions secrets — exactly 6 required
🔧 `github.com/<your-repo>/settings/secrets/actions` → New repository secret

✅ Confirmed consumed by agents in the repo:

| Secret name | Where to get it | Consumed by |
|---|---|---|
| `HUBSPOT_ACCESS_TOKEN` | HubSpot → Settings → Private Apps → Create app → copy token | `sales_agent.py`, `crm_pipeline_agent.py`, `intake_agent.py` |
| `TELEGRAM_BOT_TOKEN` | Already have it (bot exists) | `telegram_bot.py`, `notify.py`, all agents |
| `TELEGRAM_CHAT_ID` | `https://api.telegram.org/bot<TOKEN>/getUpdates` → `chat.id` | `telegram_bot.py`, `notify.py`, all agents |
| `RESEND_API_KEY` | app.resend.com → API Keys | `sales_agent.py` |
| `STRIPE_SECRET_KEY` | Stripe → Developers → API keys → Secret key | `stripe_handler.py` |
| `STRIPE_WEBHOOK_SECRET` | Created in Step 5 after registering the webhook | `stripe_handler.py` |

**Note:** `N8N_WEBHOOK_URL` is a configuration value, not a secret.
Set it as a plain environment variable or GitHub Actions variable if needed —
do not add it to the secrets store.

**Do not add `HONEYBOOK_API_KEY`** until the API is verified.

### 2b. n8n Telegram credential
🔧 n8n UI → Settings → Credentials → New credential:

- Credential type: `Telegram`
- Access Token: your `TELEGRAM_BOT_TOKEN`
- Name it exactly: `Telegram Bot`
  (must match the credential name in `demo-done-to-proposal.json`)

### Verify before moving on
- All 6 GitHub Actions secrets are set (names visible, values hidden)
- `Telegram Bot` credential appears in n8n credentials list

**Likely blocker:** HubSpot Private App token scope. Required scopes:
`crm.objects.deals.read`, `crm.objects.deals.write`, `crm.schemas.deals.read`.
Missing scope = 403 response; agents silently skip.

---

## Step 3 — Create HubSpot Pipeline

✅ Stage names confirmed in `v1-revenue-system/hubspot_pipeline.py` (`Stage` enum)
and `V1_IMPLEMENTATION_PLAN.md`.

**Critical:** `hubspot_pipeline.py` uses `"pipeline": "default"` hardcoded.
Customize the **default** pipeline's stages — do not create a new named pipeline.
A new pipeline means all deals go to the wrong pipeline silently.

### 3a. Customize the default pipeline stages
🔧 HubSpot → CRM → Deals → Manage Pipelines → Sales Pipeline (default) → Edit stages

Delete all existing default stages. Create these 7 forward stages in order:

| Display name | Internal stage ID | Probability |
|---|---|---|
| New Lead | `new_lead` | 10% |
| Outreach Sent | `outreach_sent` | 20% |
| Demo Booked | `demo_booked` | 40% |
| Proposal Sent | `proposal_sent` | 60% |
| Payment Received | `payment_received` | 80% |
| Intake Complete | `intake_complete` | 90% |
| Deployed | `deployed` | 100% |

Add the terminal outcome:

| Display name | Internal stage ID | Probability |
|---|---|---|
| Lost | `lost` | 0% |

### 3b. Create custom deal properties
🔧 HubSpot → Settings → Properties → Deal properties → Create property

✅ Confirmed in `hubspot_pipeline.py` lines 75–90:

| Display name | Internal name | Type |
|---|---|---|
| Lead Source | `lead_source` | Single-line text |
| Owner Email | `owner_email` | Single-line text |
| Proposal Type | `proposal_type` | Single-line text |
| Intake Completed | `intake_completed` | Single checkbox (boolean) |
| Stripe Payment ID | `stripe_payment_id` | Single-line text |
| Proposal Sent At | `proposal_sent_at` | Date/time |
| Lead Score | `lead_score` | Number |

### Verify before moving on
- Create one test deal manually
- Manually move it through each of the 7 stages
- Confirm each save succeeds

---

## Step 4 — Create HoneyBook Templates

⚠️ HoneyBook direct API is unverified. All sends in V1 are manual. These templates
exist so that when `/demo-done` fires and gives client details, you can send in under
2 minutes from the HoneyBook dashboard.

### 4a. Proposal templates
🔧 app.honeybook.com → Templates → New Template

- **Starter Proposal** — $500 setup + $150/mo
- **Growth Proposal** — $3,500 setup + varies

### 4b. Intake form template
🔧 app.honeybook.com → Templates → New Questionnaire/Form

Fields: business name, hours by day, services offered, primary phone number(s),
special instructions / FAQs.

### Verify before moving on
- Send a test proposal to your own email from the Starter template
- Confirm the email arrives with correct branding
- Fill the intake form yourself and confirm the response is visible in HoneyBook

---

## Step 5 — Import n8n Workflows and Register Webhooks

### 5a. Import workflows
🔧 n8n UI → Menu → Import Workflow

✅ All three files confirmed in repo — import in this order:

1. `n8n/workflows/calendly-to-hubspot.json`
2. `n8n/workflows/payment-to-intake.json`
3. `n8n/workflows/demo-done-to-proposal.json`

For `demo-done-to-proposal.json`: confirm the Telegram Trigger node uses the
`Telegram Bot` credential from Step 2b. Then **Activate** all three workflows.

### 5b. Register Calendly webhook
✅ URL confirmed in `n8n/workflows/README.md`

🔧 Calendly → Integrations → Webhooks → New Webhook:
- URL: `https://n8n.genesisai.systems/webhook/calendly-booked`
- Events: `invitee.created`

### 5c. Register Stripe webhook
✅ URL confirmed in `n8n/workflows/README.md`

🔧 Stripe → Developers → Webhooks → Add endpoint:
- URL: `https://n8n.genesisai.systems/webhook/stripe-payment`
- Events: `checkout.session.completed`, `payment_intent.succeeded`

After creating: copy the **Signing secret** → add to GitHub Actions secrets as
`STRIPE_WEBHOOK_SECRET` (this completes the 6th required secret).

### Verify before moving on
- All 3 workflows show Active (green) in n8n
- Calendly test webhook → execution appears in n8n history
- Stripe test event → execution appears in n8n history
- Send `/demo-done` (no deal ID) to your bot → usage hint reply arrives in Telegram

---

## Step 6 — Required Activation Gate: HubSpot Stage ID Verification

**This step is mandatory before any workflow test runs.**
Do not proceed to Step 7 until this check passes.

HubSpot may auto-assign stage IDs that differ from the display names you entered
in Step 3. The code writes `dealstage` values directly (e.g., `"new_lead"`,
`"demo_booked"`). If HubSpot's actual internal IDs differ, every stage transition
will silently fail — deals will not advance and no error will appear.

### 6a. Retrieve actual stage IDs from HubSpot API
Run this command with your token:
```
curl -s "https://api.hubapi.com/crm/v3/pipelines/deals/default/stages" \
  -H "Authorization: Bearer <HUBSPOT_ACCESS_TOKEN>" | python3 -m json.tool
```
This returns the real `stageId` values HubSpot is using for the default pipeline.

### 6b. Compare against the Stage enum
✅ Confirmed in `v1-revenue-system/hubspot_pipeline.py` lines 39–46:

| Enum value in code | Must match HubSpot `stageId` |
|---|---|
| `"new_lead"` | `new_lead` |
| `"outreach_sent"` | `outreach_sent` |
| `"demo_booked"` | `demo_booked` |
| `"proposal_sent"` | `proposal_sent` |
| `"payment_received"` | `payment_received` |
| `"intake_complete"` | `intake_complete` |
| `"deployed"` | `deployed` |
| `"lost"` | `lost` |

### 6c. If they do not match — required correction before proceeding
🔧 You have two options. Choose one:

**Option A (preferred):** Rename the stages in HubSpot to match the code.
Go back to Manage Pipelines and correct the stage IDs to match the enum values.

**Option B:** Update the enum values in `hubspot_pipeline.py` to match what
HubSpot assigned. This is a code change — commit it before running any tests.

**Do not proceed to Step 7 until every stage ID in the API response matches the
corresponding enum value in `hubspot_pipeline.py` exactly.**

---

## Step 7 — One Manual End-to-End Test Lead

**Prerequisite:** Step 6 must pass completely. Stage IDs must be verified.

Run a synthetic lead through all 7 forward stages before any real outreach.

### Stage 1 → 2: NEW_LEAD → OUTREACH_SENT
🔧 Create a deal in HubSpot manually:
- Name: `TEST LEAD — [today's date]`
- Stage: `New Lead`
- `owner_email`: your own email
- `proposal_type`: `starter`

✅ Trigger `sales_agent.yml` manually via GitHub Actions → Run workflow.

Verify:
- Telegram receives SEND/SKIP approval message
- Reply **SEND**
- Test email arrives in your inbox
- HubSpot deal is at `outreach_sent`

### Stage 2 → 3: OUTREACH_SENT → DEMO_BOOKED
🔧 Book a test Calendly appointment using the deal's email address.

Verify:
- n8n execution log shows `calendly-to-hubspot` ran
- HubSpot deal is at `demo_booked`
- Telegram alert fired

### Stage 3 → 4: DEMO_BOOKED → PROPOSAL_SENT
🔧 Send `/demo-done <deal_id>` to your Telegram bot.

Verify:
- Telegram returns client name, email, and plan within 30 seconds
- HubSpot deal is still at `demo_booked` (must NOT advance automatically)

🔧 Create a test project in HoneyBook for your own email using the Starter template.
🔧 Manually move the HubSpot deal to `proposal_sent`.

Verify: deal is at `proposal_sent` in HubSpot.

### Stage 4 → 5: PROPOSAL_SENT → PAYMENT_RECEIVED
🔧 Stripe → Developers → Webhooks → your endpoint → Send test event →
`checkout.session.completed`. Set `customer_email` to match the deal's `owner_email`.

Verify:
- n8n `payment-to-intake` execution appears
- HubSpot deal is at `payment_received`
- Telegram alert fired

### Stage 5 → 6: PAYMENT_RECEIVED → INTAKE_COMPLETE
✅ Trigger `intake_agent.yml` manually via GitHub Actions → Run workflow.

Verify:
- Telegram alert fires (either "intake form sent" or "send manually from HoneyBook"
  — both are expected; API is unverified)

🔧 Fill the HoneyBook intake form yourself to simulate completion.
🔧 Manually move HubSpot deal to `intake_complete`.

### Stage 6 → 7: INTAKE_COMPLETE → DEPLOYED
🔧 Send `/deploy` to Telegram bot. Reply **DEPLOY** to the approval prompt.

Verify:
- Deploy Agent runs
- Telegram confirms deployment start
- HubSpot deal moves to `deployed`

---

## V1 Activation Standard

**V1 is active only when all of the following are true:**

1. All setup steps (1–6) are complete
2. One end-to-end test lead has passed through all 7 forward HubSpot stages
3. HubSpot stage integrity is confirmed — each stage advanced at exactly the right trigger, no earlier
4. Telegram alert fired at every stage transition
5. No workflow failures in n8n execution history
6. No GitHub Actions workflow failures

Completing the setup checklist alone does not mean V1 is active.
The test lead is not optional — it is the activation proof.

---

## Setup Checklist

```
[ ] n8n accessible at https://n8n.genesisai.systems
[ ] All 6 GitHub Actions secrets set (HUBSPOT_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID, RESEND_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET)
[ ] n8n env vars set (HUBSPOT_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
[ ] Telegram Bot n8n credential created
[ ] HubSpot default pipeline has 7 forward stages + LOST with correct internal IDs
[ ] HubSpot stage IDs verified against Stage enum via API (Step 6 gate passed)
[ ] HubSpot custom properties created (7 properties)
[ ] HoneyBook Starter + Growth proposal templates exist
[ ] HoneyBook intake form template exists
[ ] All 3 n8n workflows active
[ ] Calendly webhook registered and test event passes
[ ] Stripe webhook registered, STRIPE_WEBHOOK_SECRET added to GitHub secrets
[ ] End-to-end test lead completed all 7 forward stages
[ ] Telegram alert confirmed at every stage transition
[ ] No workflow failures in n8n or GitHub Actions
```
