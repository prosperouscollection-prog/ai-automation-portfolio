# Genesis AI Systems — Claude Code Master Build Document
## Version 3 — Updated March 30, 2026
## Paste contents of this file as your first message in Claude Code

---

You are the lead engineer for Genesis AI Systems.

**Repo:** /Users/genesisai/portfolio
**Branch:** main
**Live site:** genesisai.systems
**GitHub:** prosperouscollection-prog/ai-automation-portfolio
**Demo server:** genesis-ai-systems-demo.onrender.com
**n8n:** n8n.genesisai.systems (DigitalOcean droplet — provisioned, needs setup.sh run)
**Owner:** Trendell Fordham, Detroit MI

---

## What Is Fully Done — Do Not Touch

| Item | Status |
|---|---|
| All 11 agents running green | ✅ confirmed |
| Twilio removed from all agents | ✅ Telegram is primary, Resend for email |
| Google Sheets — 6 tabs with headers | ✅ Leads, Marketing, Pipeline, Clients, Outreach Log, Revenue |
| All 8 demo endpoints wired to Claude API | ✅ real responses |
| Google Analytics on all 9 pages | ✅ G-Q072M40T9Y |
| Starter + Growth Stripe Buy Now buttons | ✅ live |
| Full Stack / $39,500 removed | ✅ everywhere |
| robots.txt | ✅ live — blocks admin pages + AI scrapers |
| sitemap.xml | ✅ expanded to 13 URLs |
| Activity feed on homepage | ✅ live — pulls from demo server |
| Vapi /end-of-call webhook endpoint | ✅ on demo server |
| Vapi webhook URL set in Vapi dashboard | ✅ done by Trendell |
| n8n docker-compose + Caddyfile + setup.sh | ✅ files committed to /n8n/ |
| DigitalOcean droplet | ✅ provisioned by Trendell |
| Contact form | ✅ saves to Sheets (Website Leads tab) + HubSpot + Telegram + Resend |
| Lead scoring all-HOT bug | ✅ fixed |

---

## Notification Stack — Final

| Channel | Purpose |
|---|---|
| Telegram | ALL agent alerts, HOT leads, morning digest, failures |
| Resend | ALL outbound email — reports, client check-ins, outreach |
| Twilio | FULLY REMOVED — do not add back |

---

## Task List — Next Session Priority Order

### TASK 1 — Deploy n8n on the DigitalOcean droplet

The droplet is provisioned. The config files are at `/Users/genesisai/portfolio/n8n/`.

Steps:
1. SSH into droplet: `ssh root@[DROPLET_IP]`
2. Run: `bash <(curl -s https://raw.githubusercontent.com/prosperouscollection-prog/ai-automation-portfolio/main/n8n/setup.sh)`
3. Verify n8n is live at `n8n.genesisai.systems`
4. Inside n8n, create credentials for: HubSpot, Google Sheets, Resend, Telegram
5. Build first workflow: New HubSpot contact (lead status = NEW) → Telegram alert → Resend welcome email

Ask Trendell for the droplet IP before starting.

---

### TASK 2 — Add "Website Leads" tab to Google Sheets

The contact form on contact.html writes to a tab called `Website Leads` which does not exist yet.

Run this Python snippet locally to create it with the correct headers:
```python
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

with open('/Users/genesisai/Downloads/n8n-integration-491503-9e7222cb0016.json') as f:
    creds_dict = json.load(f)

creds = service_account.Credentials.from_service_account_info(
    creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
service = build("sheets", "v4", credentials=creds)
SHEET_ID = "1ORElwpEZN23jzPR9v_-Wu_qVG2g8xKGIkw_g41JoAPw"

service.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range="Website Leads!A1",
    valueInputOption="RAW",
    body={"values": [["Timestamp","Name","Business","Phone","Email","Business Type","Pain Point","Score","Reason","Status","Follow-up Date","Source"]]}
).execute()
print("✅ Website Leads tab ready")
```

---

### TASK 3 — Audit all 14 portfolio projects end-to-end

For each project, verify the demo endpoint returns a real Claude-generated response (not hardcoded mock).

Test each endpoint:
```bash
curl -s -X POST https://genesis-ai-systems-demo.onrender.com/demo/lead-capture \
  -H "Content-Type: application/json" -d '{"message":"I need help with my restaurant"}'

curl -s -X POST https://genesis-ai-systems-demo.onrender.com/demo/faq-bot \
  -H "Content-Type: application/json" -d '{"question":"What are your hours?"}'

curl -s -X POST https://genesis-ai-systems-demo.onrender.com/demo/workflow \
  -H "Content-Type: application/json" -d '{"business_type":"restaurant","pain_point":"missing calls"}'

curl -s -X POST https://genesis-ai-systems-demo.onrender.com/demo/rag-chatbot \
  -H "Content-Type: application/json" -d '{"question":"How much does the starter plan cost?"}'

curl -s -X POST https://genesis-ai-systems-demo.onrender.com/demo/follow-up \
  -H "Content-Type: application/json" -d '{"lead_name":"John","business":"Auto shop","pain_point":"missed calls"}'

curl -s -X POST https://genesis-ai-systems-demo.onrender.com/demo/chat \
  -H "Content-Type: application/json" -d '{"message":"Tell me about your services"}'

curl -s -X POST https://genesis-ai-systems-demo.onrender.com/demo/video-content \
  -H "Content-Type: application/json" -d '{"business_type":"dental","topic":"after hours coverage"}'

curl -s https://genesis-ai-systems-demo.onrender.com/stats/recent-activity
```

Fix any that return hardcoded strings or empty responses.

Also verify Riley (Vapi 586-636-9550) is answering calls.

---

### TASK 4 — Exit Intent Popup

Add to `index.html` and `demos.html`.

Requirements:
- Trigger: mouse moves toward top of viewport (exit intent)
- Offer: "Before you go — book a free 15-minute call"
- Primary CTA: Calendly link (use `window.GenesisSiteConfig.urls.calendly`)
- Secondary: "No thanks" dismiss button
- Cookie: do not show again for 7 days (key: `genesis_exit_shown`)
- No email capture
- Mobile: disable on mobile (exit intent doesn't work on touch devices)
- Plain English copy only
- Matches brand colors: navy #0f172a, electric blue #2563eb

---

### TASK 5 — Clean remaining Twilio fallback code

These files still have Twilio as a fallback in the code (not the workflows — those are clean).
The fallback never fires because Telegram runs first, but clean it out:

- `.github/workflows/scripts/lead_generator_agent.py` — remove Twilio fallback in `notify_trendell()`
- `.github/workflows/scripts/scraper_agent.py` — remove Twilio fallback in `send_sms()`
- `.github/workflows/scripts/notify.py` — remove `SMSNotifier` class and all Twilio imports
- `.github/workflows/scripts/balance_checker.py` — audit and remove Twilio
- `.github/workflows/scripts/prompt_deployer.py` — audit and remove Twilio
- `.github/workflows/scripts/run_all_prompts.py` — audit and remove Twilio

After cleaning each file run `python3 -m py_compile [file]` to confirm no syntax errors.
Then run `gh workflow run` on the affected agent and confirm ✅.

---

### TASK 6 — Demo server /stats/recent-activity endpoint

The activity feed on homepage pulls from `/stats/recent-activity`.
Verify this endpoint:
1. Returns real recent actions (not hardcoded)
2. Pulls from `memory.activity` array in server.js
3. Falls back gracefully when array is empty

If it returns hardcoded data, wire it to pull from the last 5 entries in Google Sheets `Leads` tab instead.

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
**Service account:** genesis-ai-systems-operations@n8n-integration-491503.iam.gserviceaccount.com
**Calendly:** https://calendly.com/genesisai-info-ptmt/free-ai-demo-call
**Business phone:** (586) 636-9550
**Brand:** Navy #0f172a + Electric Blue #2563eb
