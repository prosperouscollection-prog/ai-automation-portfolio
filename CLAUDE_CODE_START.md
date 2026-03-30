# Genesis AI Systems — Claude Code Master Build Document
## Version 4 — Updated March 30, 2026
## Paste contents of this file as your first message in Claude Code

---

You are the lead engineer for Genesis AI Systems.

**Repo:** /Users/genesisai/portfolio
**Branch:** main
**Live site:** genesisai.systems
**GitHub:** prosperouscollection-prog/ai-automation-portfolio
**Demo server:** genesis-ai-systems-demo.onrender.com
**n8n:** n8n.genesisai.systems — live on DigitalOcean (167.99.62.62), Docker + Caddy
**Owner:** Trendell Fordham, Detroit MI

---

## What Is Fully Done — Do Not Touch

| Item | Status |
|---|---|
| All 11 agents running green | ✅ confirmed |
| Twilio removed — all agents + all 6 Python scripts | ✅ Telegram is sole alert channel |
| Google Sheets — 7 tabs with headers | ✅ Leads, Marketing, Pipeline, Clients, Outreach Log, Revenue, Website Leads |
| All 8 demo endpoints return real Claude responses | ✅ verified March 30 2026 |
| Google Analytics on all pages | ✅ G-Q072M40T9Y |
| Starter + Growth Stripe Buy Now buttons | ✅ live on all 8 demos |
| Full Stack / $39,500 removed | ✅ everywhere |
| robots.txt | ✅ blocks admin pages + artifact dirs |
| sitemap.xml | ✅ 13 URLs — all industry pages, contact, faq, roi-calculator |
| Activity feed on homepage | ✅ pulls from /stats/recent-activity on demo server |
| Exit intent popup | ✅ Calendly CTA, 7-day cookie (genesis_exit_shown), no email capture, on index.html + demos.html |
| Vapi /end-of-call webhook endpoint | ✅ on demo server |
| Vapi webhook URL set in Vapi dashboard | ✅ done by Trendell |
| n8n deployed | ✅ live at n8n.genesisai.systems |
| n8n first workflow | ✅ "HubSpot New Contact → Telegram + Resend" active, runs every 15 min |
| n8n API key | ✅ label: genesis-automation, stored in /tmp/n8n_patch2.json on droplet |
| Contact form | ✅ saves to Website Leads tab + HubSpot + Telegram + Resend |
| Lead scoring all-HOT bug | ✅ fixed |
| /stats/recent-activity | ✅ returns 10 real live items from memory.activity |

---

## Notification Stack — Final

| Channel | Purpose |
|---|---|
| Telegram | ALL agent alerts, HOT leads, morning digest, failures |
| Resend | ALL outbound email — reports, client check-ins, outreach |
| Twilio | FULLY REMOVED — do not add back |

---

## n8n Config

**URL:** https://n8n.genesisai.systems
**Login:** trendell@genesisai.systems / AKktNLmC75l7qK3WzzvLrQ==
**API key label:** genesis-automation (ends ...tMZo)
**Workflow ID:** dYwzj3Kd94NCr9pu — "HubSpot New Contact → Telegram + Resend"
**Droplet IP:** 167.99.62.62
**Encryption key:** stored in /opt/n8n/.env on droplet

Tokens wired into workflow:
- HubSpot: secrets.HUBSPOT_ACCESS_TOKEN
- Telegram bot: secrets.TELEGRAM_BOT_TOKEN (Genesis AI Systems bot)
- Telegram chat ID: 8023833224
- Resend: secrets.RESEND_API_KEY

Note: Resend email node currently bounces — trendell@genesisai.systems needs 3 Resend DNS records added to Cloudflare to verify the sending domain. Telegram node works fine.

---

## Task List — Next Session Priority Order

### TASK 1 — Run agents after Twilio cleanup

All 6 Python scripts had Twilio stripped (commit c7cc212). Verify each agent runs clean:

```bash
gh workflow run security_agent.yml
gh workflow run qa_agent.yml
gh workflow run lead_generator_agent.yml
gh workflow run scraper_agent.yml
gh workflow run master_orchestration.yml
gh workflow run sms_command_center.yml
```

For each: `gh run list --workflow=[name].yml --limit 1` then `gh run view [id] --log | tail -30`

---

### TASK 2 — Block AI scrapers in robots.txt

Add these User-agent blocks above the `User-agent: *` section in robots.txt:

```
User-agent: GPTBot
Disallow: /

User-agent: ChatGPT-User
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: anthropic-ai
Disallow: /

User-agent: Claude-Web
Disallow: /

User-agent: Google-Extended
Disallow: /
```

---

### TASK 3 — Resend domain verification

Add 3 DNS records to Cloudflare to authorize Resend to send from genesisai.systems:
1. Resend dashboard → Domains → Add Domain → genesisai.systems
2. Copy the DKIM + SPF records Resend provides
3. Add them in Cloudflare → genesisai.systems → DNS
4. Click Verify in Resend — should go green within minutes

Once verified, the Resend email node in the n8n workflow will deliver correctly.

---

### TASK 4 — Build second n8n workflow

**Name:** "New HOT Lead → Telegram Alert"

Logic:
- Trigger: Schedule (every 30 min) OR webhook from lead_generator_agent
- GET Google Sheets Leads tab — filter rows where Score = HOT and Status = NEW
- For each match: POST Telegram message with lead name, business, phone
- Mark row Status = NOTIFIED

Use the n8n API key (genesis-automation) and the workflow PUT endpoint pattern already established.

---

### TASK 5 — Verify Riley answers calls

Call (586) 636-9550 and confirm:
- Riley answers within 2 rings
- Handles a restaurant inquiry correctly
- Logs the call to Google Sheets (Inbound Calls tab or Voice Agent tab)
- Sends Telegram alert to 8023833224

If Riley doesn't answer, check Vapi dashboard → Assistants → Riley → check phone number assignment.

---

## Rules — Never Violate

1. Inspect files before editing — never assume
2. `python3 -m py_compile` every Python file before committing
3. `gh workflow run` every agent after changes — check with `gh run view [id] --log`
4. No Twilio anywhere — Telegram alerts, Resend email
5. No fake data in public UI — demos must return real Claude responses
6. All Sheets writes use correct tab names: Leads, Marketing, Pipeline, Clients, Outreach Log, Revenue, Website Leads
7. Plain English in all public copy — no jargon
8. Commit format: `fix:` / `feat:` / `remove:` / `chore:`
9. Never publish +13134002575 — private alert number only

---

## Key Config

**Google Sheet ID:** 1ORElwpEZN23jzPR9v_-Wu_qVG2g8xKGIkw_g41JoAPw
**Service account JSON:** /Users/genesisai/Downloads/n8n-integration-491503-9e7222cb0016.json
**Service account email:** genesis-ai-systems-operations@n8n-integration-491503.iam.gserviceaccount.com
**Calendly:** https://calendly.com/genesisai-info-ptmt/free-ai-demo-call
**Business phone:** (586) 636-9550
**Brand:** Navy #0f172a + Electric Blue #2563eb
**Genesis AI Telegram bot:** secrets.TELEGRAM_BOT_TOKEN
**Telegram chat ID:** 8023833224
**Prosperous agent bot:** [prosperous-agent-bot-token] (different bot — do not use for GAS)
