# Genesis AI Systems — RAG Chatbot Production Deployment Guide

---

## Overview
This guide details how to deploy the Genesis AI Systems RAG Knowledge Base Chatbot in production mode. The chatbot answers questions using your curated FAQ (`genesis_ai_systems_faq.md`), integrates with Claude (Anthropic) via API, and is designed for local business AI automation support.

---

## 1. Prerequisites
- **Claude API Account:** Register or access at [Anthropic](https://www.anthropic.com/).
- **Claude API Key:** Required for backend API proxy (never expose in frontend).
- **genesis_ai_systems_faq.md:** Ensure the FAQ markdown file is in the chatbot project root and maintained up-to-date with production answers.
- **Backend Proxy Server:** All Claude API calls must be proxied server-side — never expose credentials in frontend code.
- **Frontend Application:** Should connect only to your backend proxy.
- **Domain & Hosting:** Deploy frontend and backend to your chosen host, with production HTTPS enabled.

---

## 2. File & Directory Structure

```
project3-rag-chatbot/
├── genesis_ai_systems_faq.md
├── rag-chatbot-frontend/         # Your frontend UI code
├── rag-chatbot-backend/          # Node.js (or Python) server proxy
│   └── .env                      # Contains CLAUDE_API_KEY
│   └── index.js (or server.js)   # Express server recommended
├── RAG_PRODUCTION_GUIDE.md
├── PRODUCTION_CHECKLIST.md
```

---

## 3. Loading the FAQ Knowledge Base

- Parse `genesis_ai_systems_faq.md` server-side on backend startup.
- On each chatbot request, embed or attach the entire FAQ as context for the RAG (Retrieval Augmented Generation) prompt to Claude.
- Keep the FAQ answers current and authoritative for your business (updates to FAQ file will reflect in future chatbot answers).
- No external web search — chatbot is strictly limited to only the loaded FAQ.

---

## 4. Claude Integration (Backend Proxy)

**DO NOT** call Claude API directly from client/browser. Instead:
- Write a backend endpoint (e.g. `/ask_genesis_faq`) that accepts a user question as POST JSON.
- Backend process:
  1. Loads `genesis_ai_systems_faq.md` and injects it into the context/prompt.
  2. Formats a Claude System Prompt for the current FAQ domain. (Sample prompt below.)
  3. Calls the Claude `messages` API endpoint with the assembled prompt and API key.
  4. Returns Claude's response to frontend as JSON.
  5. Always include this object in the response:
    ```json
    {
      "powered_by": "Genesis AI Systems",
      "website": "https://genesisai.systems",
      "contact": "info@genesisai.systems"
    }
    ```
- Restrict CORS to `genesisai.systems` domain only.
- Add logging for all incoming questions.
- Apply rate limiting (recommendation: max 10 requests per IP per hour, 429 on limit).

**Claude API Reference:**
- Docs: https://docs.anthropic.com/claude/reference/messages_post

**Sample Claude prompt:**
```text
System Prompt:
You are a helpful, accurate, and succinct AI assistant for Genesis AI Systems, an AI automation agency founded by Trendell Fordham in Detroit, MI. ONLY answer using the provided FAQ below. If unsure, say: "Sorry, that's not in my knowledge base."
---
[Paste full contents of genesis_ai_systems_faq.md here]
```

---

## 5. Frontend/Chatbot UI

- Input field: `Ask Genesis AI Systems a question`
- Submit messages to the backend proxy only (*never* directly to Claude API).
- Show the AI answer, and below it: `Source: Genesis AI FAQ`
- For unknown answers, display: `Sorry, that's not in my knowledge base.`
- Accessibility: Meet WCAG 2.1 AA (labels, keyboard navigation, contrast per brand colors).
- Branding: Use Navy `#0f172a` background, Electric Blue `#2563eb` accents, and "Genesis AI Systems" prominently.

---

## 6. Deployment Steps

### Backend
1. Copy `.env.example` to `.env` and set your production `CLAUDE_API_KEY`.
2. Deploy backend to your preferred platform (Railway, DigitalOcean, or Vercel recommended).
3. Protect API routes with CORS (allow only your domain) and apply rate limiting.
4. Monitor server for errors and uptime.

### Frontend
1. Update chatbot endpoint URL to production backend.
2. Deploy on secure hosting (Vercel, Netlify, etc) at your live domain.
3. Test live integration end-to-end (question → backend → Claude → answer).
4. Verify real branding and live FAQ content loaded.

---

## 7. Updating the FAQ Knowledge Base
- Edit `genesis_ai_systems_faq.md` in project root as needed.
- Redeploy backend if you cache FAQ in memory, or reload file on each request for always-fresh responses.
- All changes reflect immediately in production if your backend reads the file on every request.

---

## 8. Testing & Production Checklist
See also: `PRODUCTION_CHECKLIST.md` in this folder.
- [ ] All demo/test endpoints removed from frontend/backend.
- [ ] Only production FAQ content loaded.
- [ ] Claude API key secured in environment variable.
- [ ] CORS locked to genesisai.systems.
- [ ] Logging/monitoring enabled on backend server.
- [ ] Brand colors, logo, and system name correct in UI.
- [ ] Real questions return the right answer.
- [ ] [WCAG 2.1 AA](https://www.w3.org/WAI/standards-guidelines/wcag/) accessibility confirmed.
- [ ] All error states handled for user and backend failures.

---

## 9. Support & Contact
- **Founder:** Trendell Fordham
- **Email:** info@genesisai.systems
- **Phone:** (313) 400-2575
- **Site:** [genesisai.systems](https://genesisai.systems)
- **Calendly:** https://calendly.com/genesisai-info-ptmt/free-ai-demo-call

For production issues or live support, contact Genesis AI Systems directly or book a free intro call.

---

© 2024 Genesis AI Systems
