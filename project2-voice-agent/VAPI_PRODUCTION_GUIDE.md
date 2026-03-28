# VAPI Voice Agent (Riley) — Production Deployment Guide

## Overview
This guide covers the complete production setup of the Genesis AI Systems Voice Agent (Riley) using Vapi, including: cloning the assistant for new clients, connecting client phone numbers, updating system prompts, integrating Vapi webhooks with n8n, and advising clients on pricing. This process ensures every client receives a fully branded and functional AI voice agent configured for their business.

---

## 1. Clone the Assistant Per Client
Each client needs their own dedicated voice assistant instance. This ensures prompt, branding, and call logging are unique per business.

### Steps:
1. **Login to Vapi Dashboard**
   - Visit [Vapi Dashboard](https://app.vapi.ai/).
   - Authenticate with your Genesis AI Systems admin credentials.

2. **Clone Production Riley Assistant**
   - Locate the "Riley" (Genesis AI Systems) assistant in your list.
   - Use the "Clone" or "Duplicate" function to copy the existing production assistant.
   - Rename the new assistant to: `Riley – [Client Business Name]` (e.g., "Riley – Detroit HVAC Solutions").

3. **Assign to Client Workspace (if applicable)**
   - Move or share the cloned assistant to the client-specific workspace/team within Vapi.

4. **Customize Avatar & Branding**
   - Update the voice style, avatar, or greet message for client branding (as needed).

---

## 2. Connect Client Phone Number
You must assign a unique phone number for each client's AI voice assistant.

### Steps:
1. **Buy a Phone Number in Vapi**
   - In the assistant settings, go to the **Phone Numbers** section.
   - Search for an available number (pick local area code, if possible).
   - Purchase and assign to the new assistant.

2. **Test Number Assignment**
   - Call the number to confirm it reaches your cloned assistant and plays the correct greeting.

---

## 3. Update System Prompts Per Client
For each client assistant, customize greetings and prompt context. Use these templates as a base and tailor the company name, founder, and services.

### Templates (Replace fields in square brackets)

#### Greeting:
```
Thank you for calling [Client Business Name].
This is Riley, your AI assistant.
How can I help you today?
```

#### System Identity Prompt:
```
You are Riley, the AI voice assistant for [Client Business Name], an AI automation agency founded by [Owner Name] in [City, State].
```

#### Pricing Response (Generic):
```
I'd love to connect you with [Owner Name] directly. Can I get your name and number so they can call you back?
```

#### Services Response:
```
[Client Business Name] builds done-for-you AI systems for local businesses. Would you like to book a free demo call?
```

#### Website Response:
```
You can learn more at [business website]
```

#### End-of-Call Response:
```
Thank you for calling [Client Business Name]. Have a wonderful day and we look forward to working with you!
```

### Steps to Update in Vapi:
1. Open the new assistant instance for the client.
2. Find the "Prompts" or "Instructions" tab.
3. Replace default Genesis AI Systems content with client-specific info.
4. Save changes and test with a live call.

---

## 4. Collect and Log Caller Data
Riley must collect these fields on every call:
1. Full name
2. Phone number
3. Business name
4. What the caller needs help with
5. Best time to call back

### Google Sheets Logging (Production Setup)
- **Sheet Name:** `Genesis AI Systems — Inbound Calls` (use a unique sheet for each client if desired)
- **Columns:** `Name | Phone | Business | Need | Best Time | Call Date | Follow Up Sent`

#### How to Connect Logging:
- Use the Vapi webhook system to POST call data to an n8n workflow.
- Map Vapi webhook fields to Google Sheets columns in n8n.

---

## 5. Integrate Vapi Webhooks with n8n
### Steps:
1. In Vapi assistant settings, go to **Webhooks**.
2. Set the webhook URL to your production n8n endpoint (example):
   - `https://n8n.genesisai.systems/webhook/voice-incoming`
3. In n8n, create a new workflow to:
   - Receive POST requests from Vapi.
   - Extract call data (name, phone, business, need, best time, call date).
   - Log information to the correct Google Sheet.
   - Trigger follow-up automations (optional: e.g., email/SMS to Trendell or the client).
4. Test with a live call and confirm data reaches Google Sheets.

**Note:** n8n must be deployed to DigitalOcean and reachable on a secure (https) public URL.

---

## 6. Pricing Advisory
- **Vapi Usage Cost:** $0.07/minute (as of 2024)
- **Client Billing:** Always pass this usage cost directly to the client along with any Genesis AI Systems markup, setup, or subscription fees.
- **Advise Clients:** Include this per-minute charge in client agreements. Consider using n8n to send monthly usage reports and automate client invoicing.

---

## 7. Best Practices for Reliability & Quality
- Use dedicated workspace/team per client in Vapi.
- Always use production Gmail/account for notifications (info@genesisai.systems).
- Secure API keys and webhook URLs—never expose in frontend code.
- Test all flows end-to-end before going live.
- Ensure prompt content, sheets, and phone number are unique per client.
- Use Genesis AI Systems branding in all client deliverables.

---

## 8. Support & Resources
- [genesisai.systems](https://genesisai.systems) — Official site
- Email: info@genesisai.systems
- Founder: Trendell Fordham — Detroit, MI
- Calendly: [Book a demo](https://calendly.com/genesisai-info-ptmt/free-ai-demo-call)
- Vapi Docs: https://docs.vapi.ai/
- n8n Docs: https://docs.n8n.io/

---

**Genesis AI Systems**
"Done-for-you AI automation for local businesses"