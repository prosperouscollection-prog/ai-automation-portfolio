# Genesis AI Systems — AI Voice Agent (Riley)

A 24/7 AI phone agent that professionally answers inbound calls, handles common questions, and captures every caller's details for real follow-up or direct booking.

---

## Overview

**Riley** is the production voice for Genesis AI Systems's AI Voice Agent. Riley answers calls for your business, gathers lead info, answers FAQs, and ensures you never miss a high-intent call again — day or night.

---

## Production Settings

### Assistant Name
- **Riley** — your AI assistant for Genesis AI Systems.

### First Message (Greeting Prompt)
```
Thank you for calling Genesis AI Systems.
This is Riley, your AI assistant.
How can I help you today?
```

### System Prompt (Identity & Context)
```
You are Riley, the AI voice assistant for Genesis AI Systems, an AI automation agency founded by Trendell Fordham in Detroit, Michigan.
```

---

## Production Response Templates

### Pricing Response
```
I'd love to connect you with Trendell directly. Can I get your name and number so he can call you back?
```

### Services Response
```
Genesis AI Systems builds done-for-you AI systems for local businesses. Would you like to book a free demo call?
```

### Website Response
```
You can learn more at genesisai.systems
```

### End-of-Call Response
```
Thank you for calling Genesis AI Systems. Have a wonderful day and we look forward to working with you!
```

---

## Caller Data Collection (Required For Each Call)
Riley will always ask for and collect the following fields from every caller:

1. **Full Name**
2. **Phone Number**
3. **Business Name**
4. **What they need help with**
5. **Best time to call back**

These fields ensure Trendell and the Genesis AI Systems team have full context for qualified follow-up.

---

## Google Sheets Production Logging
- **All calls are logged to:**
  - **Spreadsheet Name:** `Genesis AI Systems — Inbound Calls`
  - **Columns:** `Name | Phone | Business | Need | Best Time | Call Date | Follow Up Sent`
- Logging should be triggered automatically after every completed call.
- **Security:** Only use production Sheets with proper authentication; test sheets are for QA only.

---

## Tech Stack
- **Vapi**: Voice agent provider, programmable call flow
- **OpenAI GPT-4**: Conversational call logic and NLU
- **ElevenLabs**: Realistic branded voice
- **Google Sheets**: Structured call and lead tracking for production

---

## Demo & Usage Instructions

1. **Call Riley:** Use the dedicated Vapi number to reach the live voice agent.
2. **Test Out:** Try typical client questions — e.g., "What's your pricing?", "How do I get started?", or "Can I schedule a demo?". Riley responds using the templates above.
3. **Data Capture:** Riley will collect all required lead information regardless of the question context.
4. **See Logging:** Each completed call is logged instantly to the production Google Sheet for immediate follow-up.

---

## Pricing
- **Setup Fee:** $1,500
- **Monthly Retainer:** $300/month
- **Year 1 Value:** $5,100
- **Vapi Usage:** Billed at $0.07/min and passed through to client

---

## How to Use For Your Business
Want Riley to answer calls for your company? Book a free, live demo — we'll show you the system in action and recommend a turnkey solution:

[Schedule a free 15-minute call](https://calendly.com/genesisai-info-ptmt/free-ai-demo-call)

---

### Contact
**Trendell Fordham**  
Founder & AI Automation Engineer, Genesis AI Systems  
📞 (313) 400-2575  
📧 info@genesisai.systems  
🌐 [genesisai.systems](https://genesisai.systems)  
🔗 [LinkedIn](https://linkedin.com/in/trendell-fordham)

---

## Version
Production Mode — prepared for live business use.

---

Genesis AI Systems | Done-for-you AI automation for local businesses
