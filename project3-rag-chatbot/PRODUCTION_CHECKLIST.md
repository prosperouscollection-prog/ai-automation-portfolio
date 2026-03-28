## Project 3: RAG Knowledge Base Chatbot — Production Checklist

This checklist ensures the Genesis AI Systems RAG Chatbot is production-ready, sources are live, and the demo operates correctly.

---

### 1. Deployment & Environment
- [ ] Deployed to live production server
- [ ] Environment variables set for production (API keys, endpoints, CORS)
- [ ] Backend proxy does **not** expose API keys to the frontend
- [ ] HTTPS/SSL enforced for all services
- [ ] CORS restricted to `genesisai.systems`

### 2. FAQ Knowledge Source & Content
- [ ] `genesis_ai_systems_faq.md` loaded as the only RAG knowledge base file
- [ ] All answers sourced exclusively from FAQ
- [ ] FAQ content matches the latest Genesis AI Systems offerings, pricing, and policies
- [ ] Branding updated to Genesis AI Systems (navy #0f172a, electric blue #2563eb)

### 3. Chatbot Behavior
- [ ] Demo input placeholder: "Ask Genesis AI Systems a question"
- [ ] Calls backend proxy (not Claude API directly from frontend)
- [ ] Answers reference: "Source: Genesis AI FAQ"
- [ ] The disclaimer "This AI only knows what we told it" is visible
- [ ] WCAG 2.1 AA compliance checked
- [ ] Mobile responsiveness tested
- [ ] Loading and error states implemented with clear messaging
- [ ] Rate limit: 10 requests per IP per hour enforced

### 4. Demo Integration
- [ ] Demo live on portfolio website under DEMOS section
- [ ] Demo card styled per brand guidelines (navy + electric blue, LIVE badge, powered by Genesis AI Systems)
- [ ] All responses have required legal and attribution footer (powered_by/website/contact object)
- [ ] Success, loading, and error states handled gracefully

### 5. Backend & Security
- [ ] Backend logs each demo request (timestamp, IP, question, answer, success/error)
- [ ] No API keys exposed in client code
- [ ] CORS/Origin restrictions validated
- [ ] Rate-limiting tested
- [ ] Only genesisai.systems allowed origin

### 6. Documentation
- [ ] `RAG_PRODUCTION_GUIDE.md` added with deployment, setup, and FAQ updating steps
- [ ] FAQ update process documented (when services or pricing change)

### 7. Production Verification
- [ ] Sample test questions return correct, FAQ-sourced answers:
  - "Who is Genesis AI Systems?"
  - "How much does the chatbot cost?"
  - "Do you serve real estate businesses?"
  - "How do I contact you?"
  - "What guarantee do you offer?"
- [ ] Source attribution correctly shown on every answer
- [ ] No hallucinated or non-FAQ answers provided
- [ ] At least 5 manual QA tests passed

### 8. Compliance
- [ ] Privacy and terms referenced/linked on portfolio site
- [ ] Contact info displayed per brand policy
- [ ] Accessibility tested (screen reader, focus state, contrast)

### 9. Final Sign-Off
- [ ] Trendell Fordham (Founder) review completed
- [ ] Live demo functions for public users
- [ ] Checklist archived for compliance

---

For questions or issues, contact info@genesisai.systems.

**Genesis AI Systems — Production Complete**
