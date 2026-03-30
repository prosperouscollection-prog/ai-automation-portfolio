# Genesis AI Systems — Claude Code Handoff Prompt
## Paste this as your first message when opening Claude Code in this repo

---

You are the lead engineer for Genesis AI Systems.

**Repo:** /Users/genesisai/portfolio
**Live site:** genesisai.systems (GitHub Pages + Cloudflare)
**GitHub:** prosperouscollection-prog/ai-automation-portfolio
**Demo server:** genesis-ai-systems-demo.onrender.com
**Owner:** Trendell Fordham, Detroit MI

---

## Current Infrastructure — What's Live

| Item | Status |
|---|---|
| genesisai.systems | ✅ Live |
| Yelp lead generator | ✅ 25 real Detroit leads/day → Sheets → HubSpot → Telegram |
| Sales agent | ✅ Reads Sheets → Pipeline tab → HubSpot — syntax fix committed (5c87d05), needs re-run |
| Marketing agent | ✅ Claude content → Marketing tab → Telegram + Resend |
| Client Success agent | ✅ Pulls WON clients from HubSpot → Clients tab |
| Scraper agent | ✅ Telegram alerts working |
| notify.py | ✅ telegram_notify() + resend_email() helpers available to all agents |
| Google Sheets | ✅ 6 tabs with headers: Leads, Marketing, Pipeline, Clients, Outreach Log, Revenue |
| Riley voice agent | ✅ Vapi (586) 636-9550 |
| Telegram bot | ✅ Working |
| Stripe | ✅ Starter link live — Growth link pending (Stripe site was down) |
| Full Stack / $39,500 tier | ✅ Removed from all public pages |

---

## Tech Stack

| Purpose | Tool |
|---|---|
| Voice agent | Vapi (Riley) |
| Alerts | Telegram (primary) — Twilio SMS (fallback, 866 toll-free, can't SMS mobile) |
| Email | Resend (info@genesisai.systems) |
| CRM | HubSpot free |
| Lead search | Yelp Fusion API (free, 500/day) |
| Sales follow-up | Lindy AI |
| Payments | Stripe |
| Sheets auth | Google Service Account (n8n-integration-491503) |
| Remote access | Tailscale (Mac mini) |

---

## Key File Locations

| File | Purpose |
|---|---|
| assets/site-config.js | All Stripe URLs, Calendly, contact info — edit here first |
| assets/homepage-data.js | Pricing cards, product library, FAQ — edit here |
| assets/homepage.js | Renders pricing cards — checkout logic lives here |
| .github/workflows/scripts/notify.py | Shared Telegram + Resend helpers — import in every agent |
| .github/workflows/scripts/lead_generator_agent.py | Yelp search → score → Sheets → HubSpot → Telegram |
| .github/workflows/scripts/sales_agent.py | Sheets read → Pipeline tab → HubSpot → Resend outreach |
| .github/workflows/scripts/marketing_agent.py | Claude content → Marketing tab → Telegram + Resend |
| .github/workflows/scripts/client_success_agent.py | HubSpot WON clients → Clients tab → Resend milestone emails |
| .github/workflows/scripts/scraper_agent.py | Google Maps scrape → Sheets → HubSpot → Telegram |
| demo-server/server.js | Render demo server — chat widget, lead capture, demo endpoints |

---

## Google Sheets

**Sheet ID:** 1ORElwpEZN23jzPR9v_-Wu_qVG2g8xKGIkw_g41JoAPw
**Service account:** genesis-ai-systems-operations@n8n-integration-491503.iam.gserviceaccount.com

| Tab | Fed By |
|---|---|
| Leads | Lead Generator (daily 6am) |
| Marketing | Marketing Agent (daily 7am) |
| Pipeline | Sales Agent — HOT leads auto-added |
| Clients | Client Success Agent — syncs from HubSpot WON |
| Outreach Log | Manual |
| Revenue | Manual |

---

## Notification Rules

- **Telegram first** — always working, use for all alerts
- **Resend** — for outbound emails to leads and clients
- **Twilio** — fallback only, 866 toll-free cannot SMS mobile phones
- Import pattern: `from notify import telegram_notify, resend_email`

---

## Public-Facing Copy Rules

- Plain English only — no tech jargon
- Must pass the test: would a 55-year-old Detroit restaurant owner understand this?
- Preferred phrases: "answers your phone", "books appointments", "sends a text", "captures leads", "responds automatically"
- No fake testimonials, reviews, customer counts, or live activity numbers

---

## Next Tasks — In Priority Order

1. **Re-run sales agent** — confirm Pipeline tab gets populated with real Detroit business names
2. **Add Growth Stripe link** — when Stripe comes back online, add to site-config.js and flip growth card secondaryType to "checkout"
3. **Add Buy Now buttons to demos.html** — one Starter "Reserve — $500" button after each demo
4. **Wire Vapi end-of-call webhook** — point to demo-server/server.js so Riley's calls get logged
5. **Google Analytics** — replace placeholder in site-config.js with real measurement ID
6. **Wire Apollo** — free plan blocks search endpoints, either upgrade or keep Yelp as primary
7. **Deploy n8n** — DigitalOcean droplet needed for workflow automation

---

## Rules for This Repo

1. Inspect actual files before suggesting changes — never assume
2. Work from existing code, not rewrites
3. No fake trust elements — no invented testimonials, reviews, or live data
4. Telegram over Twilio for all alerts
5. Resend for all outbound email
6. All Sheets writes go to the correct named tab
7. Commit messages: descriptive, lowercase, format: `fix:` / `feat:` / `remove:`
8. Run `python3 -m py_compile` on any Python file before committing
9. Test every agent with `gh workflow run` after changes
10. Check logs with `gh run view [id] --log` and filter with `grep -E "(✅|❌|⚠️)"`
