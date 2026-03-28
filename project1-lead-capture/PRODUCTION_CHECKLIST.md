## Genesis AI Systems — Project 1: Lead Capture + AI Scoring
PRODUCTION CHECKLIST

Project owner: Trendell Fordham (info@genesisai.systems)
Location: Detroit, MI

---

### 1. Webhook Integration
- [ ] Webhook URL is set to: `https://n8n.genesisai.systems/webhook/lead-incoming`
- [ ] No test/demo endpoints are referenced
- [ ] n8n is deployed and accessible at DigitalOcean before going live (See deployment documentation)
- [ ] CORS configured to allow only approved domains

### 2. Google Sheets Connection
- [ ] Connected to production Google Sheet (not test sheet)
- [ ] Sheet location and name documented
- [ ] API service account permissions verified
- [ ] Sheet logging tested live ("Logged to Google Sheets ✅" is visible in demo)

### 3. Email (Gmail) Integration
- [ ] Outgoing sender verified as `info@genesisai.systems`
- [ ] Production OAuth credentials in use
- [ ] No test Gmail accounts referenced
- [ ] Sending tested (receive confirmation email in live inbox)

### 4. Auto-Response Email Template
- [ ] Email subject: `Thanks for reaching out to Genesis AI Systems`
- [ ] Email body matches approved template (see below)
- [ ] Name auto-merges
- [ ] Calendly link present: https://calendly.com/genesisai-info-ptmt/free-ai-demo-call
- [ ] Sent only when a new (valid) lead is captured
- [ ] Reply email is `info@genesisai.systems`

**Approved Template:**

Hi [Name],

Thanks for contacting Genesis AI Systems!

I'm Trendell Fordham, founder of Genesis AI Systems.
I build done-for-you AI automation systems for local businesses starting at $500.

Book a free 15-minute demo:
calendly.com/genesisai-info-ptmt/free-ai-demo-call

Or reply with any questions.

Trendell Fordham
Founder, Genesis AI Systems
(313) 400-2575
info@genesisai.systems
genesisai.systems

---

### 5. Lead Scoring
- [ ] AI scoring prompt is production-validated (no test prompts or models)
- [ ] Test data returns expected scores
- [ ] Scores are logged to both Sheets and n8n
- [ ] AI responses match client requirements (reviewed by Trendell)

### 6. Twilio SMS Integration (if enabled)
- [ ] SMS notifications trigger on real leads
- [ ] Sender ID shown as Genesis AI Systems
- [ ] Twilio number configured to production standard

### 7. .env.example File
- [ ] Production-ready .env.example is present in the project root
- [ ] Only required variables are listed and documented
- [ ] No real credentials or secrets included

### 8. Pipeline Testing
- [ ] End-to-end flow tested live (submit, score, email, sheet, SMS)
- [ ] Error handling in place: user-facing and developer logs
- [ ] Rate limit in place as per DEMOS spec

### 9. Documentation
- [ ] Steps to switch between test and production documented
- [ ] n8n setup/deployment instructions included (`n8n.genesisai.systems` hosted on DigitalOcean, SSL enabled)
- [ ] Google Sheets connection: production sheet and permissions specified
- [ ] All contacts for support/alerts listed (Trendell Fordham, info@genesisai.systems, +13134002575)
- [ ] Support escalation process documented

### 10. Branding & Legal
- [ ] All emails and screens use Genesis AI Systems name, colors (Navy #0f172a, Electric Blue #2563eb), and branding
- [ ] Tagline: "Done-for-you AI automation for local businesses" visible where appropriate
- [ ] All links point to https://genesisai.systems
- [ ] Privacy and terms links available if required

### 11. Demo Compliance
- [ ] Live demo POSTs to production webhook
- [ ] Shows real AI score and response
- [ ] Confirms Google Sheets logging ("Logged to Google Sheets ✅")
- [ ] Label: "Live — saved to a real Google Sheet" present
- [ ] Demo is rate-limited and error-resistant

---

### Final Review Checklist
- [ ] All production credentials and URLs in place
- [ ] Demo and live environment 100% match (no references to test or demo systems)
- [ ] Founder (Trendell Fordham) has tested and verified all flows
- [ ] Monitoring and logging in place
- [ ] Alerting system points to +13134002575 (SMS)
- [ ] Backup and restore procedures documented

---

**PRODUCTION GO LIVE APPROVAL:**
- [ ] Checked and signed off by Trendell Fordham (Founder)
- [ ] All tests logged, evidence stored, and demo validated

---

For questions or support, contact info@genesisai.systems or (313) 400-2575

Genesis AI Systems | https://genesisai.systems
"Done-for-you AI automation for local businesses" — Detroit, MI