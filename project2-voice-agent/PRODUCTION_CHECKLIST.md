## Genesis AI Systems — Project 2: Voice Agent (Riley) — Production Checklist

This checklist helps verify Project 2 (Voice Agent) is ready and live for Genesis AI Systems, fully branded, logging all calls, and collecting required data.

### Branding
- [ ] Assistant is named **Riley** throughout app, documentation, and call flows
- [ ] First message is:
  > Thank you for calling Genesis AI Systems.
  > This is Riley, your AI assistant.
  > How can I help you today?
- [ ] All system prompts reflect Genesis AI Systems branding and Detroit location
- [ ] Tagline: *"Done-for-you AI automation for local businesses"* used where applicable
- [ ] Colors match: Navy #0f172a and Electric Blue #2563eb

### System Prompt & Call Flow
- [ ] System prompt includes:
  > You are Riley, the AI voice assistant for Genesis AI Systems, an AI automation agency founded by Trendell Fordham in Detroit, Michigan.
- [ ] Pricing response:
  > I'd love to connect you with Trendell directly. Can I get your name and number so he can call you back?
- [ ] Services response:
  > Genesis AI Systems builds done-for-you AI systems for local businesses. Would you like to book a free demo call?
- [ ] Website response:
  > You can learn more at genesisai.systems
- [ ] End-of-call message:
  > Thank you for calling Genesis AI Systems. Have a wonderful day and we look forward to working with you!
- [ ] Every call collects the following from the caller:
  - [ ] Full Name
  - [ ] Phone Number
  - [ ] Business Name
  - [ ] What they need help with
  - [ ] Best time to call back
- [ ] If the caller asks about pricing or services, Riley delivers correct branded response above

### Logging & Sheets
- [ ] All inbound calls are logged to Google Sheets
- [ ] Sheet name: **Genesis AI Systems — Inbound Calls**
- [ ] Sheet columns:
  - Name
  - Phone
  - Business
  - Need
  - Best Time
  - Call Date
  - Follow Up Sent
- [ ] Google Sheets is set to production (NOT test sheet)
- [ ] Test call is confirmed logged with all required fields

### Technical (Vapi, Integration, and Monitoring)
- [ ] Vapi voice agent is in production (not sandbox) mode
- [ ] Public Vapi API key used appropriately (no API keys exposed in browser code)
- [ ] Webhooks for agent events are connected to n8n at https://n8n.genesisai.systems
- [ ] n8n flows for voice call logging, follow-up, and notification are live
- [ ] Alerting enabled to founder (Trendell Fordham: +13134002575) for missed/failed calls
- [ ] Calls auto-reply or escalate to human when needed

### Documentation & Live Demo
- [ ] `VAPI_PRODUCTION_GUIDE.md` is present and complete
- [ ] This `PRODUCTION_CHECKLIST.md` is present with all items
- [ ] Live demo for Riley agent listed and functional on genesisai.systems
- [ ] "LIVE" badge appears in demo with correct branding
- [ ] Rate limiting and error handling enabled in live demo
- [ ] Demo logged usage (10 requests per IP per hour max)
- [ ] Demo is WCAG 2.1 AA compliant and mobile responsive

### Security & Compliance
- [ ] No API keys exposed on frontend
- [ ] All personal data handled per privacy policy (link in demo footer)
- [ ] SSL enabled for all endpoints
- [ ] Privacy and terms links available in all end user-facing integrations

### Contact & Business Info
- [ ] Agent confirms business details as:
  - Founder: Trendell Fordham
  - Genesis AI Systems, Detroit, MI
  - (313) 400-2575
  - info@genesisai.systems
  - genesisai.systems
- [ ] If lead wants a call, agent asks for best time and confirms Trendell will call back
- [ ] Demo/website Calendly link: https://calendly.com/genesisai-info-ptmt/free-ai-demo-call

---

**PRODUCTION STATUS:** Fill all checkboxes before the Genesis AI Voice Agent (Riley) is live for real clients or demo.

Last updated: {{date}}
