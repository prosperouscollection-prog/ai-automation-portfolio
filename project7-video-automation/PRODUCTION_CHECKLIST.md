# Genesis AI Systems — Project 7: Video Automation

## PRODUCTION CHECKLIST

**Project Owner:** Trendell Fordham  
**Contact:** info@genesisai.systems | (313) 400-2575  
**Website:** https://genesisai.systems

---

### 1. Webhook Verification
- [ ] Webhook endpoint set to: `https://n8n.genesisai.systems`
- [ ] All incoming content triggers routed via live n8n workflow
- [ ] Webhook tested with real data and error handling verified
- [ ] HTTPS/SSL working on all endpoints

### 2. Google Sheets Production Sheet
- [ ] Google Sheets connected to production account only
- [ ] Sheet name: `Genesis AI Systems — Content Calendar`
- [ ] Sheet shared with all required team/service accounts
- [ ] No links or credentials to test or development sheets remain
- [ ] Sheets integration tested successfully end-to-end

#### Required Columns:
- [ ] Week
- [ ] Topic
- [ ] Script
- [ ] Captions
- [ ] Hashtags
- [ ] Thumbnail
- [ ] Status
- [ ] Posted

### 3. Content Calendar
- [ ] Default topics rotate weekly for 5 weeks
    - [ ] 5 ways AI automation saves local businesses time
    - [ ] How AI voice agents never miss a call
    - [ ] Why local businesses need AI lead capture
    - [ ] Before and after AI automation for restaurants
    - [ ] How Genesis AI Systems built 8 AI systems
- [ ] Calendar auto-generates topics each week
- [ ] Hashtags include:
    - #GenesisAISystems
    - #AIAutomation
    - #DetroitBusiness
    - #DoneForYouAI
    - #LocalBusinessAI
    - #TrendellFordham
- [ ] Captions and thumbnails generated or uploaded as required

### 4. Demo Generation
- [ ] Demo supports input: `Enter a topic for your video`
- [ ] Output includes:
    - [ ] Script
    - [ ] Captions
    - [ ] Hashtags
    - [ ] Thumbnail
- [ ] Each section visibly updates as generation completes (for demo UX)
- [ ] Status messaging: `Full content package in 30 seconds`
- [ ] End-to-end test: Demo input to Sheets log to webhook event completed

### 5. QA & Branding
- [ ] All system labels/branding reflect Genesis AI Systems
- [ ] All hosted URLs and credits point to genesisai.systems
- [ ] Demo and sheet spellchecks completed
- [ ] Ownership attribution: Trendell Fordham, founder Detroit, MI

### 6. Security & Permissions
- [ ] Only production service accounts have write access to production sheet
- [ ] All API keys and secrets handled server-side (never exposed on frontend)
- [ ] Demo respects rate limit (10 requests/IP/hour)

### 7. Production Go-Live
- [ ] All tests passed — webhook, Sheets, demo, content calendar
- [ ] Demo listed on portfolio site under Project 7
- [ ] Master checklist updated
- [ ] Stakeholder sign-off: _____________________________

---

**Last updated:** {{DATE}}

---
For setup, customization, or troubleshooting, contact Trendell Fordham at info@genesisai.systems or visit [genesisai.systems](https://genesisai.systems)
