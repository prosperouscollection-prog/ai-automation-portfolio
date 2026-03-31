# n8n Workflow Templates — Genesis AI V1 Revenue Corridor

These JSON files are importable into n8n at n8n.genesisai.systems.
Import each one via: Settings > Import Workflow > paste JSON.

## Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| `calendly-to-hubspot.json` | Calendly webhook | Update deal to DEMO_BOOKED + Telegram alert |
| `demo-done-to-proposal.json` | **n8n Telegram Trigger** (single entry point) | Validate stage → PROPOSAL_SENT + manual HoneyBook instructions |
| `payment-to-intake.json` | Stripe webhook | Update deal to PAYMENT_RECEIVED + Telegram alert |

**Single orchestration owner — no second trigger path**: `demo-done-to-proposal.json`
uses an n8n Telegram Trigger node as its only entry point. `telegram_bot.py` does NOT
handle `/demo-done` — the command goes directly from Telegram to n8n.

**HoneyBook proposal is manual**: The n8n workflow validates HubSpot stage, advances
to PROPOSAL_SENT, then sends the founder client details + instructions to send the
proposal from the HoneyBook dashboard. No direct HoneyBook API call is made.
HoneyBook direct API access is unverified — see `honeybook_client.py`.

## Webhook URLs

| Service | URL to register |
|---------|----------------|
| Calendly | `https://n8n.genesisai.systems/webhook/calendly-booked` |
| Stripe | `https://n8n.genesisai.systems/webhook/stripe-payment` |
| Telegram bot (`/demo-done`) | `https://n8n.genesisai.systems/webhook/demo-done-proposal` |

## Required n8n Credentials

Configure these in n8n Settings → Credentials before activating workflows:

| Credential | Used by |
|-----------|---------|
| `HUBSPOT_ACCESS_TOKEN` | All workflows — set as env var in n8n |
| `TELEGRAM_BOT_TOKEN` | All workflows — set as env var in n8n |
| `TELEGRAM_CHAT_ID` | All workflows — set as env var in n8n |
| `HONEYBOOK_API_KEY` | demo-done-to-proposal only |

## Setup Order

1. Deploy n8n at `n8n.genesisai.systems`
2. Set env vars: `HUBSPOT_ACCESS_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `HONEYBOOK_API_KEY`
3. Import all 3 workflow JSONs via Settings > Import Workflow
4. Activate each workflow (toggle ON)
5. Register Calendly webhook URL in Calendly dashboard
6. Register Stripe webhook URL in Stripe dashboard (events: `checkout.session.completed`, `payment_intent.succeeded`)
7. Add `N8N_WEBHOOK_URL=https://n8n.genesisai.systems` to GitHub secrets (used by `telegram_bot.py`)
8. Test each with a synthetic event before going live

## ⚠️ Telegram Entry Point — Required Action

`telegram_bot.py` only processes updates when called. For `/demo-done` to work in
production, Telegram must be able to reach it. There are two options:

**Option A (recommended for V1): n8n Telegram Trigger node**
- Replace the current `telegram_bot.py` webhook pattern with an n8n Telegram Trigger node
- n8n polls Telegram, parses commands, and routes `/demo-done` to the proposal workflow
- No GitHub Actions cron needed for Telegram polling

**Option B: Webhook receiver on demo server**
- Register `https://genesis-ai-systems-demo.onrender.com/telegram/webhook` with Telegram
  via `setWebhook` API call
- Demo server must forward POST bodies to `telegram_bot.py` subprocess
- Current demo server does NOT have this endpoint — must be built

Until one of these is live, `/demo-done` requires manual n8n trigger as a workaround.
