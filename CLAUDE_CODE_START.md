# Genesis AI Systems — Claude Code Master Build Document
## Version 2 — Updated March 30, 2026
## Paste contents of this file as your first message in Claude Code

---

You are the lead engineer for Genesis AI Systems.

**Repo:** /Users/genesisai/portfolio
**Branch:** main
**Live site:** genesisai.systems
**GitHub:** prosperouscollection-prog/ai-automation-portfolio
**Demo server:** genesis-ai-systems-demo.onrender.com
**Owner:** Trendell Fordham, Detroit MI

---

## Notification Stack — Source of Truth

| Channel | Purpose | Status |
|---|---|---|
| Telegram | ALL alerts, agent status, HOT leads, morning digest | ✅ Working |
| Resend | ALL outbound email — outreach, reports, client check-ins | ✅ Working |
| Twilio | DEPRECATED — remove from every agent and workflow | ❌ 866 can't SMS mobile — rip it out |

**Rule:** No agent should reference Twilio anywhere. Use `telegram_notify()` for alerts and `resend_email()` for email. Both helpers live in `notify.py`.

---

## Current Agent Status (11 total)

| Agent | Workflow File | Last Run | Issues |
|---|---|---|---|
| Lead Generator | lead_generator_agent.yml | ✅ success | Clean — Yelp → Sheets → HubSpot → Telegram |
| Sales Agent | sales_agent.yml | ✅ success | Clean — Sheets → Pipeline → HubSpot → Telegram |
| Marketing Agent | marketing_agent.yml | ✅ success | Clean — Claude → Marketing tab → Telegram + Resend |
| Client Success | client_success_agent.yml | ✅ success | Clean — HubSpot WON → Clients tab → Resend |
| Scraper Agent | scraper_agent.yml | ✅ success | Clean — Google Maps → Sheets → HubSpot → Telegram |
| Security Agent | security_agent.yml | ✅ success | ❌ Failure alerts use Twilio — replace with Telegram |
| QA Agent | qa_agent.yml | ✅ success | ❌ Failure alerts use Twilio — replace with Telegram |
| Evolution Agent | evolution_agent.yml | ✅ success | ❌ Failure alerts use Twilio — replace with Telegram |
| Master Orchestration | master_orchestration.yml | ✅ success | ❌ Morning digest uses Twilio — replace with Telegram |
| Deploy Agent | deploy_agent.yml | ✅ success | ❌ Failure alerts use Twilio — replace with Telegram |
| SMS Command Center | sms_command_center.yml | ✅ success | ❌ Entire agent built on Twilio — rebuild on Telegram |

---

## Task List — Priority Order

### TASK 1 — Strip Twilio from all 6 remaining agents/workflows
Replace every Twilio inline script block across these files:
- `.github/workflows/security_agent.yml`
- `.github/workflows/qa_agent.yml`
- `.github/workflows/evolution_agent.yml`
- `.github/workflows/master_orchestration.yml`
- `.github/workflows/deploy_agent.yml`
- `.github/workflows/sms_command_center.yml`

**Pattern to replace every time:**
```python
# OLD — Twilio inline block (delete this pattern everywhere)
pip install twilio -q
python3 - << 'PYEOF'
import os
from twilio.rest import Client
Client(...).messages.create(body=..., from_=..., to=...)
PYEOF

# NEW — Telegram inline block (use this pattern everywhere)
pip install requests -q
python3 - << 'PYEOF'
import os, requests
token = os.getenv('TELEGRAM_BOT_TOKEN', '')
chat = os.getenv('TELEGRAM_CHAT_ID', '')
msg = "YOUR MESSAGE HERE"
if token and chat:
    try:
        r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
            json={'chat_id': chat, 'text': msg}, timeout=10)
        print('✅ Telegram alert sent' if r.ok else f'⚠️ Telegram {r.status_code}')
    except Exception as e:
        print(f'⚠️ Telegram failed: {e}')
PYEOF
```

Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to the env block of every workflow that sends alerts.
Remove `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` from every workflow env block.

**Master Orchestration morning digest** — replace Twilio SMS with Telegram message showing:
- Leads today (from Sheets or demo server)
- HOT leads count
- Agent status
- Site status

**SMS Command Center** — rebuild as Telegram Command Center. It should:
- Accept commands via Telegram bot (already working)
- Replace any Twilio send logic with Telegram replies

After each workflow is updated, run it with `gh workflow run` and confirm ✅ in logs.

---

### TASK 2 — Verify all 14 portfolio projects are functional (not demo/mock)

Portfolio projects live in `/Users/genesisai/portfolio/` and on the demo server at `genesis-ai-systems-demo.onrender.com`.

**Audit each project:**

| # | Project Name | Demo Endpoint | Check |
|---|---|---|---|
| 1 | Never Miss a Customer Again | /demo/lead-capture | Returns real response? |
| 2 | Answer Your Phone 24/7 (Riley) | Vapi 586-636-9550 | Riley answering? |
| 3 | Answer Customer Questions 24/7 | /demo/faq-bot | Returns real response? |
| 4 | Your Business Runs Itself | /demo/workflow | Returns real response? |
| 5 | AI Trained on YOUR Business | /demo/rag-chatbot | Returns real response? |
| 6 | Someone Watching Your Tech 24/7 | Security agent | Running hourly? |
| 7 | Never Let a Hot Lead Go Cold | /demo/follow-up | Returns real response? |
| 8 | Social Media on Autopilot | Marketing agent | Running daily? |
| 9 | Keep Every Client Happy | Client success agent | Running daily? |
| 10 | Control Everything From Phone | Telegram bot | Responding to commands? |
| 11 | Private Chat App for Business | /demo/chat | Returns real response? |
| 12 | Full Video Content in 30 Seconds | /demo/video-content | Returns real response? |
| 13 | Find New Customers Every Morning | Lead generator | Running daily 6am? |
| 14 | Get Everything — Full Stack | REMOVED from site | N/A |

For each demo endpoint: `curl -s -X POST https://genesis-ai-systems-demo.onrender.com/demo/[endpoint] -H "Content-Type: application/json" -d '{"question":"test"}'`

Flag any that return mock/hardcoded data. Fix by wiring real API calls (Anthropic, HubSpot, Sheets).

---

### TASK 3 — Tech stack operational check

Run this full audit:
```bash
# 1. Demo server alive
curl -s -o /dev/null -w "%{http_code}" https://genesis-ai-systems-demo.onrender.com/health

# 2. Site alive
curl -s -o /dev/null -w "%{http_code}" https://genesisai.systems

# 3. Vapi webhook wired
# Check demo-server/server.js has /vapi/end-of-call endpoint
grep -n "vapi" /Users/genesisai/portfolio/demo-server/server.js

# 4. All 11 agents last run status
gh run list --repo prosperouscollection-prog/ai-automation-portfolio --limit 20

# 5. Sheets accessible
# Run lead generator and confirm rows appear in Leads tab

# 6. HubSpot receiving data
# Check HubSpot dashboard for companies created today

# 7. Telegram bot responding
# Send /status to your Telegram bot and confirm response
```

Fix anything that fails.

---

### TASK 4 — n8n on DigitalOcean

Deploy n8n for workflow automation:
1. Create a $6/mo DigitalOcean droplet (Ubuntu 22.04)
2. Install n8n via Docker
3. Point subdomain `n8n.genesisai.systems` at it via Cloudflare
4. Connect HubSpot, Google Sheets, Resend, Telegram as credentials
5. Build first workflow: new HubSpot contact → Telegram alert → Resend welcome email

---

### TASK 5 — robots.txt

Check current state:
```bash
curl https://genesisai.systems/robots.txt
```

Create or update `/Users/genesisai/portfolio/robots.txt`:
```
User-agent: *
Allow: /
Disallow: /dashboard
Disallow: /command
Disallow: /client-dashboard

Sitemap: https://genesisai.systems/sitemap.xml
```

---

### TASK 6 — Activity Feed on Homepage

Add a live activity feed section to `index.html` that pulls from the demo server.
- Endpoint: `GET /stats/activity` on demo server
- Shows: last 5 actions (lead captured, call answered, follow-up sent)
- Label everything as "Example" or "Demo" — no fake live data
- Falls back gracefully if demo server is cold/sleeping

Wire the demo server `/stats/activity` endpoint to return real data from Google Sheets activity log.

---

### TASK 7 — Exit Intent Popup

Add to `index.html` and `demos.html`:
- Triggers when mouse moves toward top of browser (exit intent)
- Offer: "Before you go — book a free 15-minute call"
- Primary CTA: Calendly link
- Secondary: dismiss
- One cookie: don't show again for 7 days
- No email capture — just the booking CTA
- Plain English copy only

---

## Rules for This Repo

1. Inspect actual files before editing — never assume
2. `python3 -m py_compile` every Python file before committing
3. `gh workflow run` every agent after changes, check logs with `gh run view [id] --log`
4. No Twilio anywhere — Telegram for alerts, Resend for email
5. No fake data in public UI — label demos as demos, remove mock fallbacks from production paths
6. All Sheets writes go to correct named tab: Leads, Marketing, Pipeline, Clients, Outreach Log, Revenue
7. Plain English in all public-facing copy
8. Commit format: `fix:` / `feat:` / `remove:` / `chore:`
9. Never touch the private alert phone number (+13134002575) — never publish it

---

## Key Credentials (all in GitHub Secrets)

| Secret | Used For |
|---|---|
| TELEGRAM_BOT_TOKEN | All agent alerts |
| TELEGRAM_CHAT_ID | All agent alerts |
| RESEND_API_KEY | All outbound email |
| GOOGLE_SHEET_ID | 1ORElwpEZN23jzPR9v_-Wu_qVG2g8xKGIkw_g41JoAPw |
| GOOGLE_SERVICE_ACCOUNT | Sheets auth (n8n-integration-491503) |
| HUBSPOT_ACCESS_TOKEN | CRM saves |
| YELP_API_KEY | Lead generator search |
| ANTHROPIC_API_KEY | Marketing agent content |
| VAPI_PUBLIC_KEY | Riley voice agent |
| STRIPE_STARTER_LINK | Buy Now — $500 |
| STRIPE_GROWTH_LINK | Buy Now — $3,500 |
| CALENDLY_URL | All booking CTAs |
