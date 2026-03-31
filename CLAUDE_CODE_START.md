# Genesis AI Systems — Claude Code Master Build Document
## Version 5 — Updated March 31, 2026
## Paste this file as your first message in every Claude Code session

---

## VERSION HISTORY

| Version | Date | What Changed |
|---|---|---|
| v1 | March 30, 2026 | Initial handoff — 5 agents, live site, Sheets, HubSpot, Telegram, Stripe Starter |
| v2 | March 30, 2026 | Added full task list, Twilio removal plan, 14 project audit, n8n files |
| v3 | March 30, 2026 | n8n deployed to DigitalOcean, exit intent, robots.txt, sitemap expanded |
| v4 | March 30, 2026 | Twilio fully stripped from all 6 Python scripts, exit intent live, all 11 agents green |
| v5 | March 31, 2026 | Added agent brainstorm, approval framework, social posting plan, version history system |

---

## BUSINESS IDENTITY

**Business:** Genesis AI Systems
**Founder:** Trendell Fordham
**Location:** Detroit, MI
**Mission:** Done-for-you AI automation for local businesses
**Target clients:** Restaurants, dental offices, HVAC, salons, real estate agents, retail stores
**Tagline:** "Done-for-you AI automation for local businesses"
**Site:** genesisai.systems
**Email:** info@genesisai.systems
**Business phone:** (586) 636-9550 — Riley answers 24/7
**Brand colors:** Navy #0f172a + Electric Blue #2563eb

---

## REPO & INFRASTRUCTURE

**Repo:** /Users/genesisai/portfolio
**GitHub:** prosperouscollection-prog/ai-automation-portfolio
**Branch:** main
**Live site:** genesisai.systems (GitHub Pages + Cloudflare SSL)
**Demo server:** genesis-ai-systems-demo.onrender.com
**n8n:** n8n.genesisai.systems — DigitalOcean droplet 167.99.62.62, Docker + Caddy
**Remote access:** Tailscale (Mac mini)


---

## NOTIFICATION STACK — FINAL — DO NOT CHANGE

| Channel | Purpose | Status |
|---|---|---|
| Telegram | ALL agent alerts, HOT leads, morning digest, failures | ✅ Sole alert channel |
| Resend | ALL outbound email — reports, client check-ins, outreach | ✅ Working |
| Twilio | FULLY REMOVED — do not add back under any circumstances | ❌ Dead |

**Import pattern for all agents:**
```python
from notify import telegram_notify, resend_email
```

---

## WHAT IS FULLY DONE — DO NOT TOUCH

### Site
| Item | Status |
|---|---|
| genesisai.systems live | ✅ |
| Google Analytics G-Q072M40T9Y on all pages | ✅ |
| Starter ($500) + Growth ($3,500) Stripe Buy Now buttons | ✅ on all 8 demos |
| Full Stack / $39,500 tier | ✅ removed from all pages and config |
| robots.txt | ✅ blocks admin pages + AI scrapers |
| sitemap.xml | ✅ 13 URLs |
| Activity feed on homepage | ✅ pulls from /stats/recent-activity |
| Exit intent popup | ✅ Calendly CTA, 7-day cookie, on index.html + demos.html |
| Vapi /end-of-call webhook | ✅ endpoint on demo server + set in Vapi dashboard |
| Contact form | ✅ saves to Website Leads tab + HubSpot + Telegram + Resend |

### Agents — All 11 Green
| Agent | Schedule | Status |
|---|---|---|
| Lead Generator | Daily 6am | ✅ Yelp → Sheets → HubSpot → Telegram |
| Sales Agent | Every 6hrs | ✅ Sheets → Pipeline tab → HubSpot → Telegram |
| Marketing Agent | Daily 7am | ✅ Claude content → Marketing tab → Telegram + Resend |
| Client Success | Daily 9am | ✅ HubSpot WON → Clients tab → Resend milestones |
| Scraper Agent | Daily 5am | ✅ Google Maps → Sheets → HubSpot → Telegram |
| Security Agent | Hourly | ✅ Telegram alerts (Twilio removed) |
| QA Agent | On push | ✅ Telegram alerts (Twilio removed) |
| Evolution Agent | Daily 2am | ✅ Telegram alerts (Twilio removed) |
| Master Orchestration | Hourly + 8am | ✅ Morning digest via Telegram |
| Deploy Agent | On push | ✅ Telegram alerts (Twilio removed) |
| Telegram Command Center | On demand | ✅ Rebuilt on Telegram (Twilio removed) |

### Backend
| Item | Status |
|---|---|
| Google Sheets — 7 tabs with headers | ✅ Leads, Marketing, Pipeline, Clients, Outreach Log, Revenue, Website Leads |
| All 8 demo endpoints return real Claude responses | ✅ verified |
| HubSpot CRM receiving real data | ✅ |
| n8n deployed at n8n.genesisai.systems | ✅ |
| n8n workflow: HubSpot New Contact → Telegram + Resend | ✅ active, runs every 15 min |
| Lead scoring all-HOT bug | ✅ fixed |
| /stats/recent-activity | ✅ returns 10 real live items |


---

## AGENT VISION — WHAT EACH AGENT SHOULD DO (Brainstormed March 31, 2026)

This is the north star. Every build decision should move agents from "Today" toward "Complete."

### Governing Principle — Three Modes
- **Approval Mode** — agent plans/drafts, Trendell approves via Telegram, agent executes
- **Notify Mode** — agent executes, sends Telegram confirmation after
- **Auto Mode** — fully autonomous, Trendell reviews results weekly (only after 30+ days of clean operation)

**Anything that touches the outside world (emails to leads, social posts, proposals) starts in Approval Mode.**

### Agent 1 — Lead Generator
**Today:** Finds 25 Detroit businesses via Yelp, scores them, saves to Sheets, Telegram top 3, pushes to HubSpot. Leads sit in Sheets with no action.
**Complete:** Finds leads → pulls owner emails via Hunter.io → drafts personalized outreach email per lead → sends Telegram: "5 HOT leads ready, reply SEND to approve outreach" → Trendell approves → emails go out → logged to Outreach Log tab.
**Approval required:** Yes — before any email sends.

### Agent 2 — Sales Agent
**Today:** Reads HOT leads from Sheets, saves to Pipeline + HubSpot, sends Telegram + Resend report. Nothing actually contacts anyone.
**Complete:** Watches Pipeline for leads untouched 48hrs → flags in Telegram → Trendell confirms → follow-up email sends → tracks responses → flags replies immediately → triggers HoneyBook proposal when deal marked WON.
**Approval required:** Yes — before each outreach send.

### Agent 3 — Marketing Agent
**Today:** Claude writes LinkedIn post + Instagram captions + outreach email. Saves to Marketing tab. Sends Telegram preview + Resend email. Content sits in Sheets, nothing gets posted.
**Complete:** Sunday — generates weekly content plan → Trendell approves plan. Daily — writes that day's content → Trendell approves copy. Posts automatically to Instagram + TikTok once approved. Weekly engagement report. After 30 days clean → moves to Auto Mode.
**Approval required:** Yes — weekly plan AND each daily post, until Auto Mode earned.
**Note:** Instagram requires image (Canva API or branded template library). TikTok requires video file. Start with Instagram. TikTok = script generation only until video workflow built.

### Agent 4 — Client Success Agent
**Today:** Queries HubSpot WON clients, sends generic milestone emails at day 7/30/60/90, syncs Clients tab.
**Complete:** Personalized milestone emails with real metrics ("Your AI handled 47 after-hours calls this month"). Health monitoring — checks if Riley is answering, if chat widget works. Proactive client alerts before they notice issues. Review requests day 60. Referral program day 90. Upsell detection when usage exceeds Starter tier.
**Approval required:** Notify Mode — emails go out automatically, Trendell notified after.

### Agent 5 — Scraper Agent
**Today:** Attempts Google Maps scrape via Playwright (unreliable on GitHub Actions), falls back to mock. Overlaps with Lead Generator.
**Complete:** Repurposed as on-demand targeted research tool (not daily). "Find every HVAC company within 3 blocks of Comerica Park." Different purpose from Lead Generator — surgical vs. broad.
**Approval required:** No — research only, no external actions.

### Agent 6 — Security Agent
**Today:** Monitors GitHub Actions hourly, Telegram on failure.
**Complete:** Monitors everything — site 200 response, demo server alive, Riley active in Vapi, last Sheets write within 24hrs, HubSpot API reachable, Resend API reachable, all 11 agents ran successfully in last 24hrs. Weekly security scan for exposed secrets.
**Approval required:** No — alerts only.

### Agent 7 — QA Agent
**Today:** Checks 2 URLs return 200 on every push.
**Complete:** All 13 sitemap URLs return 200. All 8 demo endpoints return real Claude responses. All Stripe links valid. Contact form submits and lead appears in Sheets. Riley answering (ping Vapi API). Pass/fail Telegram after every deploy.
**Approval required:** No — alerts only.

### Agent 8 — Evolution Agent
**Today:** Generates generic suggestions with no real data access.
**Complete:** Reads real data from Sheets, HubSpot, social metrics. Identifies patterns (which industry converts best, which content performs). Recommends specific actions. Weekly strategy email — plain English, actionable.
**Approval required:** No — advisory only.

### Agent 9 — Master Orchestration
**Today:** Sends morning Telegram digest with mock data from demo server.
**Complete:** Real 8am briefing — leads found overnight, outreach sent, responses received, pipeline value, social post status, agent health, Riley status, ONE action item for the day ("Call Slows Bar BQ — 3 days no response: (313) 962-9828").
**Approval required:** No — informational.

### Agent 10 — Telegram Command Center
**Today:** Commands return mock/demo data. No real actions triggered.
**Complete:** Full mobile control panel. /leads = today's HOT leads. /pipeline = deal summary. /send [name] = approve outreach. /post = publish today's content. /report = weekly summary. /client [name] = client system status. /revenue = MRR + setup fees. All sends require CONFIRM reply before executing.
**Approval required:** Yes — for all outbound actions via CONFIRM flow.

### Agent 11 — Deploy Agent
**Today:** Checks 2 URLs return 200 after push.
**Complete:** Checks all 13 sitemap URLs, demo server alive, key site text present, Stripe links reachable, Cloudflare caching. Connects to QA Agent instead of running checks independently.
**Approval required:** No — alerts only.


---

## DECISIONS MADE — DO NOT REVISIT UNLESS NOTED

| Decision | Choice | Reason |
|---|---|---|
| Lead outreach channel | Email only, Trendell follows up with call | No cold texting — $500+ service needs human touch |
| Social posting — Phase 1 | Instagram first | Business owners on Instagram, text + image posts |
| Social posting — Phase 2 | TikTok script generation, Trendell records | TikTok API requires video file, can't auto-post text |
| Social posting — Phase 3 | Full TikTok auto-post with AI video | Requires Runway/HeyGen ($50-150/mo) — future |
| LinkedIn | Lower priority than Instagram/TikTok | Not where Detroit local business owners spend time |
| Apollo.io | Free tier only until 2-3 clients closed | Paid plan ($49/mo) not justified yet — Yelp handles lead discovery |
| Instantly.ai | Waiting — no email list yet | Yelp leads have no emails. Activate when Hunter.io wired |
| Lindy AI | Waiting — activate with first inbound leads | No email addresses to follow up yet |
| HoneyBook | Build templates now — use on first close | 30 min setup, ready to send day 1 |
| Hunter.io | Wire into Lead Generator — gets owner emails from domains | Free tier: 25/mo. Paid: $34/mo for 500 |
| Twilio | Fully removed — never use again | 866 toll-free can't SMS mobile phones |
| Full Stack tier | Removed from site entirely | No Stripe link, overwhelming for cold visitors |
| Approval flow | Telegram SEND/CONFIRM replies | Simplest mobile-first approval before any external action |
| n8n | DigitalOcean $6/mo droplet, Docker + Caddy | Workflow automation layer between agents and external services |

---

## TOOLS & STACK — SOURCE OF TRUTH

| Purpose | Tool | Status |
|---|---|---|
| Voice agent | Vapi — Riley on (586) 636-9550 | ✅ Answering 24/7 |
| Agent alerts | Telegram (@GenesisaisystemsBot) | ✅ All 11 agents wired |
| Outbound email | Resend (info@genesisai.systems) | ✅ Working — DNS verify trendell@ pending |
| CRM | HubSpot free | ✅ Receiving real data |
| Lead discovery | Yelp Fusion API (free, 500/day) | ✅ 25 leads/day |
| Lead emails | Hunter.io | ❌ Not wired yet |
| Content posting | Instagram Graph API | ❌ Not built yet |
| Content posting | TikTok Content API | ❌ Not built yet — script gen only |
| Proposals/contracts | HoneyBook | ⏳ Templates not built yet |
| Sales sequences | Lindy AI | ⏳ Waiting for inbound leads |
| Cold email | Instantly.ai | ⏳ Waiting for email list |
| Workflow automation | n8n (n8n.genesisai.systems) | ✅ 1 workflow live |
| Payments | Stripe — Starter + Growth links live | ✅ |
| Remote access | Tailscale | ✅ Mac mini |
| Hosting | GitHub Pages + Cloudflare | ✅ |
| Demo server | Render | ✅ |

---

## KEY CONFIG — ALL IN ONE PLACE

**Google Sheet ID:** 1ORElwpEZN23jzPR9v_-Wu_qVG2g8xKGIkw_g41JoAPw
**Sheet tabs:** Leads, Marketing, Pipeline, Clients, Outreach Log, Revenue, Website Leads
**Service account:** genesis-ai-systems-operations@n8n-integration-491503.iam.gserviceaccount.com
**Service account JSON:** /Users/genesisai/Downloads/n8n-integration-491503-9e7222cb0016.json
**Calendly:** https://calendly.com/genesisai-info-ptmt/free-ai-demo-call
**n8n URL:** https://n8n.genesisai.systems
**n8n login:** trendell@genesisai.systems / AKktNLmC75l7qK3WzzvLrQ==
**n8n API key label:** genesis-automation
**Droplet IP:** 167.99.62.62
**Telegram bot:** @GenesisaisystemsBot (secrets.TELEGRAM_BOT_TOKEN)
**Telegram chat ID:** secrets.TELEGRAM_CHAT_ID

**GitHub Secrets (all set):**
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, RESEND_API_KEY, GOOGLE_SHEET_ID,
GOOGLE_SERVICE_ACCOUNT, HUBSPOT_ACCESS_TOKEN, YELP_API_KEY, ANTHROPIC_API_KEY,
VAPI_PUBLIC_KEY, STRIPE_STARTER_LINK, STRIPE_GROWTH_LINK, CALENDLY_URL,
NOTIFICATION_EMAIL, DEMO_SERVER_URL


---

## CURRENT TASK LIST — PRIORITY ORDER (as of March 31, 2026)

### 🔴 IMMEDIATE — Before Any New Features

**TASK 1 — Strip Twilio from 5 remaining workflow YMLs**
These YMLs still have Twilio env vars + pip install. Python scripts are clean but YMLs are not.
Files: sales_agent.yml, marketing_agent.yml, client_success_agent.yml, lead_generator_agent.yml, scraper_agent.yml
Remove from each: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER from env blocks + twilio from pip install
After each: `gh workflow run [agent] && gh run list --workflow=[agent].yml --limit 1`
Confirm all 5 still pass green.

**TASK 2 — Resend domain verification**
Add DNS records to Cloudflare to authorize trendell@genesisai.systems sending domain.
1. Resend dashboard → Domains → Add Domain → genesisai.systems
2. Copy DKIM + SPF + DMARC records
3. Add in Cloudflare → genesisai.systems → DNS
4. Click Verify in Resend → confirm green

**TASK 3 — Verify all 14 demo endpoints return real Claude responses**
```bash
for endpoint in lead-capture rag-chatbot video-automation faq-bot workflow follow-up chat video-content; do
  echo "--- $endpoint ---"
  curl -s --max-time 20 -X POST https://genesis-ai-systems-demo.onrender.com/demo/$endpoint \
    -H "Content-Type: application/json" -d '{"message":"test","question":"test","topic":"test"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','') or d.get('answer','') or d.get('script','') or str(d)[:100])"
done
```
Flag any that return hardcoded fallback strings. Fix by ensuring callClaude() is wired correctly.

---

### 🟡 THIS WEEK — Make Agents Actually Do Things

**TASK 4 — Wire Hunter.io into Lead Generator**
Lead Generator finds businesses via Yelp but gets no email addresses.
Hunter.io free tier: 25 searches/month. Paid: $34/mo for 500.
Wire: for each HOT lead, take primary_domain from Yelp → POST to Hunter domain search → get owner email → add to lead record before saving to Sheets + sending outreach draft.
Add HUNTER_API_KEY to GitHub secrets.

**TASK 5 — Build Sales Agent outreach approval flow**
When Lead Generator finds HOT leads with emails (from Hunter.io):
1. Sales Agent drafts personalized email per lead
2. Sends Telegram to Trendell: "[Business name] — [email] — Draft: [first 100 chars of email]. Reply SEND to approve or SKIP."
3. Telegram bot listens for reply
4. SEND → Resend sends email → logged to Outreach Log tab with timestamp
5. SKIP → lead stays in Pipeline as "Pending Approval"
This is the core mechanism. Nothing external happens without Trendell's SEND reply.

**TASK 6 — Marketing Agent approval flow + Instagram posting**
Stage 1 — Plan approval (Sunday):
Agent generates 7-day content plan → sends to Trendell via Telegram + Resend → Trendell replies APPROVE
Stage 2 — Daily post approval:
Agent writes that day's content → sends preview to Trendell → Trendell replies POST
Stage 3 — Instagram posting:
On POST reply → agent calls Instagram Graph API → publishes to @genesisaisystems
Requires: INSTAGRAM_ACCESS_TOKEN + INSTAGRAM_ACCOUNT_ID in GitHub secrets
Image: use Canva API (CANVA_API_KEY) or pre-made branded template library
Note: Trendell must switch @genesisaisystems to Business account + create Meta developer app first.

---

### 🟢 NEXT PHASE — Deepen Agent Intelligence

**TASK 7 — Master Orchestration real data digest**
Replace mock data with real aggregated data:
- Pull last 24hr rows from Leads tab (count HOT)
- Pull Pipeline tab (count by status)
- Pull Outreach Log (emails sent yesterday)
- Pull Revenue tab (current MRR)
- Ping all 11 agents via gh run list (confirm all passed)
- Ping Riley via Vapi API (confirm active)
- Format as one clean Telegram message with ONE action item

**TASK 8 — Security Agent expanded monitoring**
Add to existing hourly check:
- curl genesisai.systems → confirm 200
- curl genesis-ai-systems-demo.onrender.com/stats/health → confirm alive
- Vapi API → confirm Riley assistant is active and phone number assigned
- Google Sheets API → confirm last write to Leads tab was within 24hrs
- All checks log pass/fail. Any fail → immediate Telegram alert with which check failed.

**TASK 9 — Client Success real metrics**
Pull actual Vapi call logs via Vapi API → count calls handled for each client
Include in milestone emails: "Your AI handled X calls this month"
Wire health check: confirm Riley is still assigned and active for each client's number

**TASK 10 — Telegram Command Center real actions**
Wire /leads → pull from Sheets Pipeline tab (real data)
Wire /send [name] → trigger outreach approval flow (Task 5)
Wire /post → trigger Marketing Agent to send today's content for approval
Wire /report → pull and format weekly summary from all Sheets tabs
Wire /revenue → pull Revenue tab totals

---

### 🔵 BACKLOG — When Ready

**TASK 11 — TikTok content generation**
Marketing Agent generates script + hook + caption for TikTok daily.
Trendell records video using the script.
Once video file exists → agent posts via TikTok Content Posting API.
Requires: TIKTOK_ACCESS_TOKEN + business account verification.

**TASK 12 — Evolution Agent real data analysis**
Connect to Sheets — read Leads, Pipeline, Outreach Log, Revenue tabs.
Identify top-performing industry (which converts to Pipeline fastest).
Identify best-performing outreach copy (which gets replies).
Weekly Resend email to Trendell with 3 specific recommendations.

**TASK 13 — HoneyBook proposal trigger**
When Trendell marks a deal WON in HubSpot → n8n workflow fires → HoneyBook API creates and sends proposal automatically.
Requires: HoneyBook API key (HONEYBOOK_API_KEY).
Proposal templates (Starter + Growth) are already written — stored in genesis_ai_proposals.md.

**TASK 14 — Scraper Agent repurpose**
Remove daily schedule. Convert to on-demand research tool.
Add Telegram command: /research [industry] [area] → triggers scraper for that specific target.
Keeps Playwright but runs on demand only, not as a scheduled job.

---

## RULES — NEVER VIOLATE

1. Inspect actual files before editing — never assume
2. `python3 -m py_compile` every Python file before committing
3. `gh workflow run` every agent after changes — verify with `gh run view [id] --log`
4. No Twilio anywhere — Telegram for alerts, Resend for email
5. No fake/hardcoded data in public UI — all demos must return real Claude responses
6. All Sheets writes use correct tab names exactly: Leads, Marketing, Pipeline, Clients, Outreach Log, Revenue, Website Leads
7. Plain English in all public copy — if a 55-year-old Detroit restaurant owner wouldn't understand it, rewrite it
8. Commit format: `fix:` / `feat:` / `remove:` / `chore:`
9. Never publish +13134002575 — private alert number, internal use only
10. Approval Mode first — any agent action that touches the outside world needs Trendell's explicit SEND/CONFIRM before executing
11. Update CLAUDE_CODE_START.md with version number + what changed at the end of every session

---

## SITE SCORE HISTORY

| Date | Score | Key Changes |
|---|---|---|
| Pre-session | 77/100 | Baseline — site live, partial setup |
| March 30 AM | 84/100 | 11 agents green, Sheets wired, Twilio removed from scripts |
| March 30 PM | 88/100 | Exit intent live, GA confirmed, Buy Now on all demos |
| March 30 EOD | 91/100 | Exit intent polished, Twilio removed from all Python scripts |
| Target | 95/100 | Needs: founder photo, Twilio gone from 5 YMLs, all demos verified |

---

## PATH TO FIRST REAL OUTREACH — THE SEQUENCE

Before Genesis AI sends its first automated outreach email to a real Detroit business:

1. ✅ Lead Generator finds real HOT leads daily (done)
2. ❌ Hunter.io wired → leads get owner emails automatically (Task 4)
3. ❌ Sales Agent drafts personalized email per HOT lead (Task 5)
4. ❌ Telegram approval flow — Trendell replies SEND (Task 5)
5. ❌ Resend sends email from info@genesisai.systems (requires Task 2 DNS)
6. ❌ Outreach logged to Outreach Log tab automatically (Task 5)
7. ✅ Trendell follows up with phone call (manual — intentional)

**Marketing runs in parallel:**
8. ❌ Instagram posts daily (Task 6) — builds brand so leads recognize Genesis AI when they get the email

**When someone replies:**
9. ❌ Sales Agent flags reply in Telegram immediately (Task 5 extended)
10. Trendell books a call via Calendly
11. ✅ HoneyBook sends proposal (templates ready, API trigger = Task 13)
12. ✅ Client Success Agent takes over at day 1 (done — just needs real clients)
