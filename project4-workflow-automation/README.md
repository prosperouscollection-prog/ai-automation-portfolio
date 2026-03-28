# AI Workflow Automation + Email

An automated lead-response system that captures inquiries, updates Google Sheets, and sends follow-up emails within seconds.

## Problem It Solves

In high-volume service businesses, slow response time kills conversion because leads arrive faster than staff can reply manually.

## Target Client

Service businesses with high lead volume.

## Tech Stack

- n8n (production instance at [https://n8n.genesisai.systems](https://n8n.genesisai.systems))
- OpenAI API
- Webhooks
- Google Sheets (production sheet)
- SendGrid (for transactional email via Gmail sender)

---

## Production Configuration & Deployment

### 1. Webhook Setup (Production)
- **Webhook URL:** All live workflow automations must POST to:
  
  `https://n8n.genesisai.systems/webhook/workflow-automation`
  
- **Notice:** n8n must be deployed and SSL-enabled on a DigitalOcean Droplet (see [MASTER_PRODUCTION_CHECKLIST.md](../../MASTER_PRODUCTION_CHECKLIST.md)). Demo/test webhooks **must not** be used in production.
- **Authentication:** Secure webhooks for production. Require a secret header or token as appropriate.

### 2. Google Sheets (Production)
- Connect to the **production Google Sheet** (NOT test or personal sheets!).
- Sheet must be titled for the client or as:
  
  `Genesis AI Systems — Workflow Automation Leads`
  
- **Required Columns:**
  - `Timestamp`
  - `Full Name`
  - `Business Name`
  - `Email`
  - `Phone Number`
  - `Inquiry / Message`
  - `Lead Score` (if used)
  - `Email Sent?`
- All updates from n8n must write directly to this production sheet—double check integration in n8n's Google Sheets node.
- Ensure that proper permissions and service account management are used in production (least-privilege principle).

### 3. Outbound Email (Gmail via SendGrid)
- **Sender:** All outbound emails must use `info@genesisai.systems` as the sender, authenticated and delivered via **SendGrid** using the official API for deliverability, not via basic SMTP or direct Gmail.
- **SendGrid Setup:**
  - DNS verified for `genesisai.systems` domain.
  - API key scoped for transactional sends only, stored securely in `.env` (never committed).
- **Reply-To:** Set as `info@genesisai.systems`.
- **Template:**
    - Personalize emails with merge fields for name and inquiry.
    - See Project 1 for the auto-response copy.
    - Emails are sent via n8n's SendGrid node, not via basic email nodes.
- **Compliance:** Always include Genesis AI Systems branding, physical business address (Detroit, MI), and opt-out link if required.

### 4. n8n Workflow (Example Overview)
```
Lead received via webhook →
✦ Validate/parse data
✦ Lookup/enrich via OpenAI (optional scoring)
✦ Insert row into production Google Sheet
✦ Auto-generate personalized email message
✦ Send via SendGrid (from info@genesisai.systems)
✦ Write log/status to Sheet
✦ Optional: Slack notification/SMS to Sales
```

## Demo & Testing Instructions

1. Trigger a sample lead submission to `https://n8n.genesisai.systems/webhook/workflow-automation`.
2. Verify the lead appears instantly in the **production** Google Sheet.
3. Check the prospect's email inbox for an email sent from `info@genesisai.systems` (delivered via SendGrid).
4. Confirm the flow is logged step-by-step in n8n's execution view.
5. Document results and mark pipeline as tested in the checklist.

---

## Pricing
- **Setup Fee:** $2,000
- **Monthly Retainer:** $400/month
- **Total Year 1 Value:** $6,800

## Why This Matters
If better speed to lead helps close just 1 additional job per month, this system can generate a return that dwarfs its annual cost.

---

## Book a Discovery Call
Ready to implement this system for your business?
[Schedule a free 15-minute call](https://calendly.com/genesisai-info-ptmt/free-ai-demo-call) — we'll show you a live demo and tell you exactly what it would cost to build this for you.

**Trendell Fordham | Founder, Genesis AI Systems**  
📞 (313) 400-2575  
📧 info@genesisai.systems  
🌐 https://genesisai.systems  
🔗 https://linkedin.com/in/trendell-fordham  
📅 https://calendly.com/genesisai-info-ptmt/free-ai-demo-call

---

## Production Checklist (Required for Go-Live)
- [ ] n8n production instance deployed and SSL (n8n.genesisai.systems)
- [ ] Webhook URL updated to production endpoint
- [ ] SendGrid verified and tested for info@genesisai.systems
- [ ] Google Sheet production connection verified
- [ ] .env set up and committed (no secrets!)
- [ ] End-to-end pipeline live tested
- [ ] Results and settings documented in `PRODUCTION_CHECKLIST.md`

For questions or production issues, contact Founder Trendell Fordham at info@genesisai.systems.
