# Genesis AI Systems — Changelog
# Verifiable entries only. Session dates and scope based on git commit history.
# For full context per session, see chatgpt.md.

---

## [Unreleased] — V1 Revenue Corridor Build
**Date:** March 31, 2026
**Session type:** Architecture + implementation build
**Commits this session:** None (all work untracked in worktree — not yet committed)

### Added
- `V1_IMPLEMENTATION_PLAN.md` — master architecture plan, 7-stage forward pipeline + LOST terminal outcome, role ownership, build order, agent specs
- `v1-revenue-system/approval_flow.py` — Telegram SEND/SKIP/DEPLOY/HOLD approval gate; `ApprovalFlow`, `ApprovalRequest`, `ApprovalStatus`
- `v1-revenue-system/hubspot_pipeline.py` — 7-stage forward pipeline enum + LOST terminal outcome, deal update helpers
- `v1-revenue-system/honeybook_client.py` — HoneyBook client module (API unverified; returns None on failure; no email bypass)
- `v1-revenue-system/stripe_handler.py` — Stripe payment link creation, webhook event parsing
- `v1-revenue-system/hunter_lookup.py` — Hunter.io email lookup (quarantined; not in V1 critical path)
- `.github/workflows/scripts/crm_pipeline_agent.py` — stale deal detection, pipeline summary to Telegram
- `.github/workflows/scripts/intake_agent.py` — HoneyBook intake form trigger, completion tracking, Telegram failure alerts
- `.github/workflows/crm_pipeline_agent.yml` — runs crm_pipeline_agent on cron (every 2 hours)
- `.github/workflows/intake_agent.yml` — runs intake_agent on cron (every 2.5 hours)
- `n8n/workflows/calendly-to-hubspot.json` — Calendly webhook → HubSpot DEMO_BOOKED + Telegram alert
- `n8n/workflows/demo-done-to-proposal.json` — n8n Telegram Trigger (/demo-done) → stage validation → proposal prep instructions (no HoneyBook API call; HubSpot not auto-advanced)
- `n8n/workflows/payment-to-intake.json` — Stripe payment webhook → HubSpot PAYMENT_RECEIVED + intake trigger
- `n8n/workflows/README.md` — setup instructions, credential table, Telegram entry point documentation
- `chatgpt.md` — project context log for session continuity
- `CHANGELOG.md` — this file

### Modified
- `.github/workflows/scripts/sales_agent.py` — added Telegram SEND/SKIP outreach approval gate; added `approval_flow` imports; outreach emails require explicit founder approval before send
- `.github/workflows/scripts/telegram_bot.py` — removed `/demo-done` from COMMANDS dict (n8n Telegram Trigger handles it); removed `handle_demo_done()` method
- `.env.example` — added all V1 revenue keys (Telegram, HubSpot, HoneyBook, Stripe, n8n); removed GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT; Hunter.io commented as optional
- `v1-revenue-system/honeybook_client.py` — updated module docstring to declare API as UNVERIFIED; corrected stale Resend fallback reference; marked API_BASE as provisional
- `V1_IMPLEMENTATION_PLAN.md` — corrected PROPOSAL_SENT trigger description; corrected Architecture Lock /demo-done entry
- `MASTER_SUMMARY.md` — full rewrite to match V1 locked architecture (see below)

### Removed from MASTER_SUMMARY.md (stale pre-V1 content)
- Apollo.io, Lindy AI, Instantly.ai references (not in locked V1 stack)
- 14-product list and $39,500 full-stack tier (removed from public pages in commit `34f9fa2`)
- Stale "tonight" to-do list (predates V1 build)
- Replaced with: V1 pipeline stages, locked tool stack, approval gates, what is/isn't automated, current status, activation blockers

### Architecture decisions documented this session
- `PROPOSAL_SENT` must only represent a real sent proposal. `/demo-done` does not advance HubSpot — it provides the founder with client details to send from HoneyBook. Founder manually advances HubSpot after confirming send.
- HoneyBook direct API is unverified. No automated proposal or intake sends until verified.
- n8n Telegram Trigger is the sole runtime entry point for `/demo-done`. No webhook path, no second trigger.
- Approval gates are scoped to exactly two: outreach email (SEND/SKIP) and deployment (DEPLOY/HOLD).
- Google Sheets removed from locked V1 stack. HubSpot is the only pipeline SOR.

---

## [0.9.0] — Pre-V1 Stabilization
**Date range:** March 30–31, 2026
**Commits:** `4197415`, `8117deb`, `87e25ff`, `25b01aa`, `c7cc212`, `af6bde7`, `39e199c`, `95ad756`, `0bcd93f`, `31e8dc5`, `357fa69`, `b5b2fa9`, `03e0390`, `dfa4fba`, `5c87d05`, `ebb17f3`, `cd202a7`, `a155182`, `6eeb071`, `34f9fa2`

### Notable changes (from commit messages)
- Stripped Twilio from all agents — replaced with Telegram for failure alerts (`357fa69`, `c7cc212`, `8117deb`)
- Fixed lead scoring all-HOT bug, fixed outreach missing from Sheets (`0bcd93f`)
- Wired Claude API to all 8 demo endpoints (`31e8dc5`)
- Added n8n Docker + Caddy config for DigitalOcean deploy (`95ad756`)
- Added live activity feed, fixed robots.txt + sitemap (`39e199c`)
- Added GA tracking, Growth Stripe link, Buy Now buttons, Vapi webhook (`03e0390`)
- Removed Full Stack / $39,500 tier from all public pages and config (`34f9fa2`)
- CLAUDE_CODE_START.md updated to v3, v4, v5 across sessions
- Exit intent popup reworked — Calendly CTA, 7-day cookie, no email capture (`25b01aa`)

---

## [0.8.0] — Initial Build + Rebrand
**Date range:** March 27–29, 2026
**Commits:** `bb33d46`, `3e61825`, `dc8725c`, `f8d2b11`, `1b66e8a`, `d965ff8`, `e6860bd`, `76dc7fa`, `291842d`, `5656481`, `f36664e`, `68ae5d0`, `5bebc8b`, `2cbf032`, `70aa32c`, `770b4d7`, `5842f3c`, `bc204e3`, `c48dc72`, `0b60141`

### Notable changes (from commit messages)
- Initial commit — AI Automation Portfolio, 7 projects (`0b60141`)
- Rebrand to Genesis AI Systems (`bc204e3`)
- Complete Genesis AI Systems build — 49+ files, all 4 prompts deployed, live demos, agents, branding (`770b4d7`)
- Added Resend email — verified genesisai.systems domain (`70aa32c`)
- Added 8 live demos to genesisai.systems, demo server on Render (`5bebc8b`)
- Added founder dashboard + client dashboard, PIN protected (`76dc7fa`)
- Added 14 projects + Telegram bot + Scraper agent + Command dashboard (`d965ff8`)
- Fixed Telegram bot — pure JavaScript on Render Node.js (`1b66e8a`)
- Comprehensive codebase fixes: API models, workflows, Twilio optional, homepage optimization (`f8d2b11`)
- Complete website rebuild — all gaps fixed (`bb33d46`)
