## Genesis AI Systems — Project 5: AI Chat Widget Production Checklist

This checklist confirms the Genesis AI Systems AI Chat Widget is fully live and production-ready. Each item must be verified before marking as complete.

### Backend & Proxy
- [ ] Node.js Express backend (`server.js`) created for proxying chat requests
- [ ] Backend receives messages from frontend widget
- [ ] Backend calls OpenAI API securely (API key **never** in the browser)
- [ ] Backend returns OpenAI response to the frontend
- [ ] Error handling for proxy/network/OpenAI errors implemented
- [ ] CORS restricted to genesisai.systems
- [ ] Environment variables loaded securely (API key, etc.)

### Deployment
- [ ] Backend prepared for Railway deployment
- [ ] Railway project created and backend deployed
- [ ] Production environment variables set in Railway
- [ ] Backend endpoint live and responding to requests
- [ ] Railway logs show successful proxy calls
- [ ] Fallback/maintenance handling enabled if Railway is down

### Frontend Integration
- [ ] Frontend widget updated to call the backend proxy (not OpenAI direct)
- [ ] Widget branding matches Genesis AI Systems:
  - [ ] Header: `Genesis AI Systems`
  - [ ] Subtitle: `Ask us anything`
  - [ ] Powered by: `Genesis AI Systems`
  - [ ] Navy (#0f172a) and Electric Blue (#2563eb) colors
- [ ] API endpoint URL switched to live Railway backend
- [ ] All network errors surface as user-friendly error messages
- [ ] Widget responsive on mobile and desktop
- [ ] Widget fully accessible (WCAG 2.1 AA compliant, focusable, labeled)

### Security & Compliance
- [ ] OpenAI API key **never** put in any frontend code or sent to browsers
- [ ] No secrets hardcoded in repo
- [ ] All dependencies up to date
- [ ] Logging omits sensitive data from user chats
- [ ] Privacy policy link live in footer or widget

### Testing & Live Verification
- [ ] Test chat responses returned in under 3 seconds
- [ ] Widget embedded on portfolio site and demo page
- [ ] End-to-end tests with at least 5 queries (confirmed response, no errors)
- [ ] Rate limiting enabled (at proxy/backend level, 10 req/IP/hr)
- [ ] Long conversations (10+ turns) tested without failure
- [ ] Live on genesisai.systems/demo and embed code tested on other sites

### Documentation
- [ ] `RAILWAY_DEPLOY.md` documents exact steps for production deploys
- [ ] README files updated with proxy and deployment instructions
- [ ] Embed code snippet ready for clients/partners
- [ ] Onboarding instructions for embedding widget shared with clients

---

**Signoffs:**

- [ ] Backend Proxy — _Checked by:_ __________________ Date: ________
- [ ] Frontend Integration — _Checked by:_ __________________ Date: ________
- [ ] Live Demo Tested — _Checked by:_ __________________ Date: ________
- [ ] Project Owner Review — _Checked by:_ __________________ Date: ________

**Genesis AI Systems**  
Trendell Fordham, Founder · <info@genesisai.systems>  
https://genesisai.systems  
