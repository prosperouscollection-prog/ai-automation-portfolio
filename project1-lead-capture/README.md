# Lead Capture + AI Scoring

An AI-powered lead intake workflow that captures new inquiries, scores lead quality, and logs everything into Google Sheets for immediate follow-up.

## Problem It Solves

Many local businesses collect website leads but do not respond fast enough, which means promising inquiries go cold before anyone reaches out.

## Target Client

Any local business with a contact form or website.

## Tech Stack

- n8n (deployed on DigitalOcean)
- Webhook ([production endpoint](https://n8n.genesisai.systems/webhook/lead-incoming))
- OpenAI API
- Google Sheets (production and test sheets supported)
- Gmail (info@genesisai.systems)

---

## Deployment Guide

> **Every system must work for Genesis AI Systems itself before clients. The following are production-ready instructions used by Genesis AI Systems.**

### 1. n8n Deployment on DigitalOcean

- **Provision a DigitalOcean Droplet** (minimum 2GB RAM recommended). See [DigitalOcean instructions](https://docs.n8n.io/hosting/installation/digital-ocean/) for reference.
- Reserve a domain/subdomain. For production, we use: **n8n.genesisai.systems**
- Set up n8n using Docker or node/Nginx depending on stack preference.
- **Important:** Ensure SSL is enabled on the subdomain.
- Confirm that your webhook is accessible at:

  ```
  https://n8n.genesisai.systems/webhook/lead-incoming
  ```

- Restrict incoming connections to trusted IPs or protect webhook endpoint as needed for security.

### 2. Webhook URL — Production vs. Test

- **Production Webhook:**
  - `https://n8n.genesisai.systems/webhook/lead-incoming`
- **Test Webhook (for staging):**
  - Use a hidden or alternate n8n workflow or a staging subdomain
  - Example: `https://n8n.genesisai.systems/webhook/lead-test`
- **Client Integration:**
  - Connect the client's website or form POST/GET endpoint to the production webhook only after full testing. For demos or integration QA, use the test endpoint.

### 3. Google Sheets — Production vs. Test Instructions

- **Production Sheet:**
  - Use the actual client Google account and a secured production spreadsheet.
  - Sheet naming convention: `Genesis AI Systems — Leads` or similar, per client.
  - Grant edit access to `info@genesisai.systems` and limit sharing.
- **Test Sheet:**
  - Create a duplicate Sheet as a sandbox for initial integration and safe testing.
  - Only after successful test submissions should you change the n8n 'Google Sheets' node credentials and spreadsheet ID to the live/production sheet.
- **Switching from Test to Production:**
  1. Open the n8n workflow.
  2. In the 'Google Sheets' node, update the credentials (Service Account or OAuth2) to use the production account.
  3. Change the spreadsheet ID/URL to the production Sheet.
  4. Retest with a real (non-dummy) lead.
  5. Archive or delete the test Sheet after launch.

### 4. Gmail Sending Domain — Verified for Production

- **Sender:** info@genesisai.systems
- **Authentication:** Connect to n8n via OAuth2 or App Password, or use SendGrid SMTP relay (recommended for reliability and deliverability). 
- **Production Steps:**
  - Confirm the `info@genesisai.systems` mailbox is live and able to send/receive.
  - In n8n, use the 'Gmail' node or 'SMTP Email' node with the correct credentials.
  - Test sending to various domains (e.g., Gmail, Yahoo, Outlook) to verify delivery and domain authentication (SPF/DKIM/DMARC DNS records must be valid).

#### **Auto-response Email Template (Production)**

- **Subject:** Thanks for reaching out to Genesis AI Systems

- **Body:**

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



### 5. Lead Scoring Prompt

To ensure consistent scoring and maximize close rate, use the following prompt in OpenAI (gpt-3.5-turbo or gpt-4) within the n8n workflow "AI Lead Score" node:

**Prompt:**

    You are an expert at qualifying sales leads for a local business. For the following inquiry, reply with:
      - AI Auto-Response (short, friendly, personalized)
      - Lead Score (HIGH, MEDIUM, or LOW — based only on likelihood to become a paying customer)
    Inquiry:
    "{{message}}"

Expected Output (JSON):

    {
      "auto_response": "Thank you for reaching out! We'll get in touch soon.",
      "lead_score": "HIGH"
    }

**Scoring Guidance:**
- HIGH: Ready to buy, clears intent, leaves contact info
- MEDIUM: Interested, but may have questions or less urgent
- LOW: Not a fit, looking for something you don't offer, spam

*n8n workflow should parse the AI response and score, log to Google Sheets, and use the auto_response for the email reply.*

---

## Demo Instructions (for Owners & Clients)

1. Submit a sample GET/POST request to `https://n8n.genesisai.systems/webhook/lead-incoming` with a `message` field:  
   Example: `?message=I'm ready for a quote on AI automation.`
2. Monitor the workflow in the n8n UI for real-time handling.
3. Open the linked Google Sheet (production) — confirm a new row contains:
   - Original message
   - AI-generated auto-response
   - Lead score (HIGH/MEDIUM/LOW)
   - Timestamp, sender info
4. Confirm auto-reply email is sent from info@genesisai.systems using the template above.
5. Test multiple real-world sample messages to validate scoring consistency.

---

## Security and Compliance

- All sensitive keys/secrets must be stored in environment variables (see `.env.example`).
- Do not share your webhook URL publicly if possible. Protect with IP whitelisting or passphrase if needed for high-security productions.
- Gmail sending domain must pass email security checks (SPF/DKIM/DMARC).

---

## File Reference

- [`.env.example`](./.env.example) — follow this structure for required secrets in both test and production.
- [`PRODUCTION_CHECKLIST.md`](./PRODUCTION_CHECKLIST.md) — do not go live without ensuring every section is complete and every production credential is used.

---

## Pricing

- Setup Fee: $500
- Monthly Retainer: $150/month
- Total Year 1 Value: $2,300

===

## Why This Matters

A local business generating just 2 extra booked jobs per month from faster follow-up can cover this system many times over before the year is over.

---

## Book a Discovery Call

Ready to implement this system for your business?
[Schedule a free 15-minute call](https://calendly.com/genesisai-info-ptmt/free-ai-demo-call) — we'll show you a live demo and tell you exactly what it would cost to build this for you.

**Trendell Fordham | AI Automation Engineer, Genesis AI Systems**
📞 (313) 400-2575
📧 info@genesisai.systems
🌐 https://genesisai.systems
🔗 https://linkedin.com/in/trendell-fordham
📅 https://calendly.com/genesisai-info-ptmt/free-ai-demo-call
