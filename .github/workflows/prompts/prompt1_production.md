You are a senior developer for Genesis AI Systems.
Create all requested files completely.
Return them as a JSON array as instructed.


# Genesis AI Systems — Prompt 1 of 4

Begin immediately. Write every file completely. Do not truncate.

## Founder Details
- Name: Trendell Fordham
- Phone: (313) 400-2575
- Email: info@genesisai.systems
- Alert phone: +13134002575
- GitHub username: prosperouscollection-prog
- Repo: ai-automation-portfolio
- Website: https://genesisai.systems
- Calendly: https://calendly.com/genesisai-info-ptmt/free-ai-demo-call
- Business name: Genesis AI Systems
- Location: Detroit, MI
- Brand colors: Navy `#0f172a` and Electric Blue `#2563eb`
- Tagline: "Done-for-you AI automation for local businesses"

## Mission
Customer Zero is Genesis AI Systems itself. Every system must work for our own agency first.

---

## PART 1: TEST MODE TO LIVE MODE CORRECTIONS

Audit every project and fix everything currently in test or demo mode to production-ready live mode.

### PROJECT 1: Lead Capture + AI Scoring
Directory: `/Users/genesisai/portfolio/project1-lead-capture/`

Fix these issues:
- Webhook URL must be `https://n8n.genesisai.systems/webhook/lead-incoming`
- Document that n8n must be deployed to DigitalOcean first
- Document Google Sheets production sheet vs test sheet connection
- Confirm Gmail sends from `info@genesisai.systems`
- Verify the lead scoring prompt works correctly
- Add a production `.env.example`
- Add `PRODUCTION_CHECKLIST.md`

Use this auto-response email template:

Subject: `Thanks for reaching out to Genesis AI Systems`

Body:

```text
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
```

### PROJECT 2: Voice Agent (Riley)
Directory: `/Users/genesisai/portfolio/project2-voice-agent/`

Fix these issues:
- Rename the assistant to a production-ready Genesis AI Systems name
- Update the first message to:

```text
Thank you for calling Genesis AI Systems.
This is Riley, your AI assistant.
How can I help you today?
```

- Update the system prompt with:

Identity:

```text
You are Riley, the AI voice assistant for Genesis AI Systems, an AI automation agency founded by Trendell Fordham in Detroit, Michigan.
```

Pricing response:

```text
I'd love to connect you with Trendell directly. Can I get your name and number so he can call you back?
```

Services response:

```text
Genesis AI Systems builds done-for-you AI systems for local businesses. Would you like to book a free demo call?
```

Website response:

```text
You can learn more at genesisai.systems
```

End-of-call response:

```text
Thank you for calling Genesis AI Systems. Have a wonderful day and we look forward to working with you!
```

- Collect from every caller:
  1. Full name
  2. Phone number
  3. Business name
  4. What they need help with
  5. Best time to call back
- Log all calls to Google Sheets:
  - Sheet name: `Genesis AI Systems — Inbound Calls`
  - Columns: `Name | Phone | Business | Need | Best Time | Call Date | Follow Up Sent`
- Add `VAPI_PRODUCTION_GUIDE.md` covering:
  - How to clone the assistant per client
  - How to connect the client phone number
  - How to update the system prompt per client
  - How to connect Vapi webhooks to n8n
  - Pricing note: Vapi charges `$0.07/min` and this cost should pass through to the client
- Add `PRODUCTION_CHECKLIST.md`

### PROJECT 3: RAG Knowledge Base Chatbot
Directory: `/Users/genesisai/portfolio/project3-rag-chatbot/`

Create `genesis_ai_systems_faq.md` with the following content:

```markdown
Q: What is Genesis AI Systems?
A: Genesis AI Systems is a done-for-you AI automation agency founded by Trendell Fordham in Detroit, MI. We build AI systems that capture leads, answer calls, and automate operations for local businesses 24/7.

Q: What services do you offer?
A: We offer 8 AI systems:
1. Lead Capture + AI Scoring ($500)
2. AI Voice Agent ($1,500)
3. RAG Knowledge Chatbot ($1,000)
4. Workflow Automation + Email ($2,000)
5. AI Chat Widget ($2,500)
6. Fine-tuned AI Model ($5,000)
7. Video Automation ($1,500)
8. Self-Healing Agent System ($10,000)

Q: How much does it cost?
A: Systems start at $500 setup + $150/month.

Q: How long does it take?
A: Most systems live within 5-7 days.

Q: Who is this for?
A: Local businesses — restaurants, salons, dental offices, HVAC, real estate, retail.

Q: How do I get started?
A: Book at calendly.com/genesisai-info-ptmt/free-ai-demo-call or email info@genesisai.systems

Q: Where are you located?
A: Detroit, MI. Serving businesses nationwide.

Q: Who founded Genesis AI Systems?
A: Trendell Fordham, Detroit, MI.

Q: What makes you different?
A: Every system runs on our own agency first. Visit genesisai.systems to see all 8 live.

Q: Do you offer a guarantee?
A: Yes — 30-day satisfaction guarantee.

Q: How do I contact you?
A: info@genesisai.systems | (313) 400-2575
genesisai.systems | Calendly link above
```

Also add:
- `RAG_PRODUCTION_GUIDE.md`
- `PRODUCTION_CHECKLIST.md`

### PROJECT 4: AI Workflow Automation + Email
Directory: `/Users/genesisai/portfolio/project4-workflow-automation/`

Fix these issues:
- Webhook URL must point to `https://n8n.genesisai.systems`
- Gmail must send as `info@genesisai.systems` through Resend
- Google Sheets must use the production sheet
- Add `PRODUCTION_CHECKLIST.md`

### PROJECT 5: AI Chat Widget
Directory: `/Users/genesisai/portfolio/project5-chat-widget/`

Fix these issues:
- Create a Node.js and Express backend proxy at `project5-chat-widget/server.js`
- The backend must:
  - Receive messages from the frontend
  - Call the OpenAI API server-side
  - Return the response to the frontend
  - Never expose the API key in the browser
  - Be ready to deploy to Railway
- Update `index.html` to call the proxy
- Update widget branding:
  - Header: `Genesis AI Systems`
  - Subtitle: `Ask us anything`
  - Powered by: `Genesis AI Systems`
  - Colors: Navy `#0f172a` and Electric Blue `#2563eb`
- Add `PRODUCTION_CHECKLIST.md`
- Add `RAILWAY_DEPLOY.md`

### PROJECT 6: Fine-tuning
Directory: `/Users/genesisai/portfolio/project6-fine-tuning/`

Add `FINE_TUNING_PRODUCTION_GUIDE.md` that covers:
- Step by step instructions to run actual fine-tuning
- Cost: `$0.01–0.05` for 10 examples
- Time: `15–30 minutes`
- How to use the fine-tuned model ID in production
- How to swap it into Project 5
- How to fine-tune per client vertical

Also add:
- `PRODUCTION_CHECKLIST.md`

### PROJECT 7: Video Automation
Directory: `/Users/genesisai/portfolio/project7-video-automation/`

Fix these issues:
- Webhook URL must point to `https://n8n.genesisai.systems`
- Google Sheets must use the production sheet
- Sheet name must be `Genesis AI Systems — Content Calendar`
- Columns must be:
  - `Week | Topic | Script | Captions | Hashtags | Thumbnail | Status | Posted`
- Default topics must rotate weekly:
  1. `5 ways AI automation saves local businesses time`
  2. `How AI voice agents never miss a call`
  3. `Why local businesses need AI lead capture`
  4. `Before and after AI automation for restaurants`
  5. `How Genesis AI Systems built 8 AI systems`
- Always include these hashtags:
  - `#GenesisAISystems #AIAutomation #DetroitBusiness #DoneForYouAI #LocalBusinessAI #TrendellFordham`
- Add `PRODUCTION_CHECKLIST.md`

### PROJECT 8: Self-Healing Agent System
Directory: `/Users/genesisai/portfolio/project8-agent-system/`

Fix these issues:
- Verify all GitHub Actions workflows
- Verify all secrets are referenced correctly
- Make the notification system production-ready
- Add `PRODUCTION_CHECKLIST.md`
- Set status to active on `genesisai.systems`

### MASTER PRODUCTION CHECKLIST
File: `/Users/genesisai/portfolio/MASTER_PRODUCTION_CHECKLIST.md`

Create or update this file with:

```markdown
## Infrastructure
- [ ] DigitalOcean Droplet ($12/month)
- [ ] n8n at n8n.genesisai.systems
- [ ] SSL on n8n subdomain
- [ ] Railway account created
- [ ] Project 5 proxy on Railway
- [ ] Vercel account created

## Project 1
- [ ] Webhook → n8n.genesisai.systems
- [ ] Gmail → info@genesisai.systems
- [ ] Google Sheets production connected
- [ ] Lead scoring verified
- [ ] SMS via Twilio connected
- [ ] Full pipeline tested

## Project 2
- [ ] Riley branded + production mode
- [ ] First message updated
- [ ] System prompt updated
- [ ] Test call completed
- [ ] Calls logged to Sheets

## Project 3
- [ ] genesis_ai_systems_faq.md loaded
- [ ] Production deployment documented
- [ ] Test questions answered correctly

## Project 4
- [ ] Webhook → n8n.genesisai.systems
- [ ] Resend connected
- [ ] Full pipeline tested

## Project 5
- [ ] Backend proxy built
- [ ] Deployed to Railway
- [ ] Frontend calling proxy
- [ ] API key not in browser
- [ ] Widget tested live

## Project 6
- [ ] Fine-tuning job run
- [ ] Model ID saved
- [ ] Model tested
- [ ] Integrated into Project 5

## Project 7
- [ ] Webhook → n8n.genesisai.systems
- [ ] Sheets production connected
- [ ] Pipeline tested end to end

## Project 8
- [ ] All GitHub secrets added
- [ ] All 5 workflows active
- [ ] SMS tested
- [ ] Email tested
- [ ] All badges passing

## Website
- [ ] All 8 project cards showing
- [ ] All 8 live demos working
- [ ] Contact form working
- [ ] Calendly button working
- [ ] Mobile responsive
- [ ] Page speed under 3 seconds
- [ ] SSL green padlock
- [ ] Privacy policy live
- [ ] Terms live
- [ ] 404 tested
- [ ] Thank you page tested
- [ ] PWA installable
```

---

## PART 2: DEPLOY ALL 8 PROJECTS AS LIVE DEMOS

Update `PORTFOLIO_WEBSITE.html` to include live interactive demos for all 8 projects.

Add a `DEMOS` section after the projects section.

### DEMO DESIGN STANDARDS
- Each demo in its own card
- Background: Navy `#0f172a`
- Accents: Electric Blue `#2563eb`
- `LIVE` badge in the top right
- Loading spinner while waiting
- Error handling if a demo fails
- Mobile responsive
- WCAG 2.1 AA compliant
- Header: `Genesis AI Systems — Live Demo`
- Footer: `Powered by Genesis AI Systems`
- Rate limit: `10 requests per IP per hour`

### PROJECT 1 DEMO
- Input placeholder: `Type a message to test the AI`
- Button label: `Send Lead`
- Must call the live n8n webhook
- Must show the AI response and lead score
- Must show `Logged to Google Sheets ✅`
- Must show the label: `Live — saved to a real Google Sheet`

### PROJECT 2 DEMO
- Button label: `Call Riley (AI Demo)`
- Use the Vapi web SDK:

```html
<script src="https://cdn.jsdelivr.net/npm/@vapi-ai/web/dist/vapi.js"></script>
```

- Initialize with the Vapi public key
- Label: `Talk to our AI voice agent live`

### PROJECT 3 DEMO
- Input: `Ask Genesis AI Systems a question`
- Calls Claude API via backend proxy
- Pre-loaded with `genesis_ai_systems_faq.md`
- Shows the answer and `Source: Genesis AI FAQ`
- Label: `This AI only knows what we told it`

### PROJECT 4 DEMO
- Input: message field
- Animated pipeline visualization:
  - `Lead Captured → AI Scored → Email Sent`
- Each step lights up as it completes
- Shows final score and response
- Label: `Full automation in under 5 seconds`

### PROJECT 5 DEMO
- Embed the actual chat widget
- Label: `Embeddable on any website`
- Show the embed code snippet below the widget

### PROJECT 6 DEMO
- Input: `Ask our trained AI a question`
- Show a side-by-side comparison:
  - Left: `Base GPT`
  - Right: `Genesis AI Trained`
- Label: `See the difference training makes`

### PROJECT 7 DEMO
- Input: `Enter a topic for your video`
- Button: `Generate Content`
- Returns:
  - Script
  - Captions
  - Hashtags
  - Thumbnail
- Show each section as it generates
- Label: `Full content package in 30 seconds`

### PROJECT 8 DEMO
- Show live GitHub Actions badges
- Show last scan timestamp
- Show uptime percentage
- Add link text: `View live runs on GitHub`
- Label: `These agents ran in the last hour`

### CONTACT FORM
Add this to `PORTFOLIO_WEBSITE.html`:

Fields:
- Full Name (required)
- Business Name (required)
- Email Address (required)
- Phone Number (required)
- What do you need? dropdown (required):
  - Lead Capture System
  - AI Voice Agent
  - AI Chatbot
  - Workflow Automation
  - Full Agency Package
  - Not sure yet
- Message (optional)
- Submit button: `Book My Free Demo`

Form behavior:
- POST to `https://n8n.genesisai.systems/webhook/genesis-lead`
- Success message:

```text
Thanks [Name]! Trendell will contact you within 24 hours. Or book instantly:
```

- Include a Calendly button on success
- Redirect to Calendly after 3 seconds
- Validate required fields, email format, and phone format
- Must be WCAG 2.1 AA compliant

### DEMO BACKEND SERVER
Create directory: `/Users/genesisai/portfolio/demo-server/`

Required files:
- `demo-server/server.js`
- `demo-server/package.json`
- `demo-server/README.md`
- `demo-server/.env.example`
- `demo-server/RAILWAY_DEPLOY.md`

The Node.js and Express demo server must:
- Handle all 8 demo API calls
- Proxy to OpenAI, Claude, n8n, and Vapi
- Apply rate limiting of `10 requests per IP per hour`
- Log all demo usage
- Return clean JSON
- Restrict CORS to `genesisai.systems` only
- Include this object in every response:

```json
{
  "powered_by": "Genesis AI Systems",
  "website": "https://genesisai.systems",
  "contact": "info@genesisai.systems"
}
```

- Be ready for Railway deployment

---

## PUSH TO GITHUB

Generate these commands exactly at the end:

```bash
git add .
git commit -m "Prompt 1 of 4: Production mode corrections + 8 live demos — Genesis AI Systems
genesisai.systems by Trendell Fordham"
git push origin main
```

---

## QUALITY STANDARDS

Every file must:
- Use SOLID principles where Python is involved
- Never expose API keys in frontend code
- Be mobile responsive for HTML output
- Meet WCAG 2.1 AA accessibility
- Include error handling in all code
- Include Genesis AI Systems branding
- Reference Trendell Fordham as founder
- Link to `genesisai.systems`

Do not skip any section. Do not truncate any file. Complete everything fully.
