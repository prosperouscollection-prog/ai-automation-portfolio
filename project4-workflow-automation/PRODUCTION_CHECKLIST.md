# Project 4: AI Workflow Automation + Email — Production Checklist

This checklist ensures all components for Project 4 (AI Workflow Automation + Email) are switched from test/demo to live production mode.

## 1. Webhook Configuration
- [ ] **Primary webhook URL is set to:**
  - `https://n8n.genesisai.systems`
- [ ] All automation flows point to production n8n (on DigitalOcean)
- [ ] SSL/TLS and HTTPS enforced
- [ ] No test/demo endpoints remain in code, integrations, or documentation

## 2. Gmail / SendGrid Email
- [ ] Outgoing emails send from `info@genesisai.systems` only
- [ ] SendGrid API key is configured using production credentials (never hardcoded)
- [ ] SendGrid verified sender: `info@genesisai.systems`
- [ ] Reply-to is set to `info@genesisai.systems`
- [ ] Production alert and notification flows tested live
- [ ] All test email recipients removed; real recipient list used
- [ ] Unsubscribe and GDPR compliance links in production templates

## 3. Google Sheets Integration
- [ ] Connected to **production sheet only** (check Sheet ID & name)
- [ ] Sheet access granted to `info@genesisai.systems` service account
- [ ] Old/test sheets removed from code or integrations
- [ ] Sheet columns and structure match production requirements
- [ ] Live data is being written and updated as expected
- [ ] Sheets permissions: Only necessary accounts have edit access

## 4. Automation Pipeline
- [ ] Full lead flow: Capture → AI Score → Email Sent → Google Sheets log tested in production
- [ ] Automated failover or error alerts configured via n8n to founder (Trendell Fordham +13134002575)
- [ ] All steps show real-time success/failure logging
- [ ] Processing thresholds and rate limits set for production usage (not demo defaults)

## 5. Documentation & Security
- [ ] Environment variables verified (no `.env.test` in production)
- [ ] `.env.example` file updated for production keys
- [ ] Access restricted to `genesisai.systems` domain as needed
- [ ] Sensitive data like API keys, credentials, and OAuth secrets NEVER in codebase
- [ ] All error handling and fallback logic active and tested

## 6. Final QA
- [ ] End-to-end production test completed and all steps verified
- [ ] Sample live lead processed and confirmed in Sheets, Gmail (SendGrid), and webhook logs
- [ ] Genesis AI Systems branding present in all emails and docs
- [ ] All references to Trendell Fordham as contact/founder
- [ ] Links to `https://genesisai.systems` in all user-facing messages
- [ ] Checklist signed-off by dev and founder

---

**For support or escalation:**  
Trendell Fordham — Founder  
Phone: (313) 400-2575  
Email: info@genesisai.systems  
Website: https://genesisai.systems
