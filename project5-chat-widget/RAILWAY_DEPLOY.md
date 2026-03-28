# Deploying Project 5: AI Chat Widget Backend Proxy to Railway

This guide covers how to deploy the Node.js + Express backend (located in `server.js`) for the Genesis AI Systems AI Chat Widget to [Railway](https://railway.app/).

---

## Purpose
- **Never expose the OpenAI API key in the browser.**
- Handle all frontend chat requests server-side, call OpenAI securely, and proxy the response.
- Production-ready deployment for real client demos and embed.

---

## 1. Prerequisites

- Railway account ([sign up here](https://railway.app/))
- Node.js 18+ and npm if running locally
- OpenAI API key (production, not test)
- Access to your GitHub repo (recommended for auto-deploy)
- This project structure:
  - `/Users/genesisai/portfolio/project5-chat-widget/server.js`
  - `package.json`
  - `.env.example`

---

## 2. Configure Environment Variables

1. **Copy `.env.example` to `.env` (locally):**
   ```bash
   cp .env.example .env
   ```
2. **Set these variables:**
   - `OPENAI_API_KEY=sk-...` (from OpenAI dashboard)
   - Any other variables your code requires (see `.env.example`)
   
3. **On Railway:**
   - Go to `Settings > Variables` and add the same variables, matching your local `.env` (do not push your actual `.env` to GitHub).

---

## 3. Deploying to Railway (GitHub Integration — Recommended)

### Steps:

1. **Push all code to your GitHub repo.**

2. **Create a New Project on Railway**
   - Click `New Project`
   - Select `Deploy from GitHub repo`
   - Choose your repo (`ai-automation-portfolio` on `prosperouscollection-prog`)
   - (If prompted) Set the directory to `/Users/genesisai/portfolio/project5-chat-widget` or ensure `server.js` and `package.json` are in the root folder for the Railway service

3. **Set the Start Command**  
   - Railway auto-detects from `package.json` (`npm start` or `node server.js`).
   - Confirm in the Railway dashboard > Service > Settings > Deployments.

4. **Set Environment Variables**  
   - Settings > Variables > add all variables from `.env.example` (at minimum: `OPENAI_API_KEY`).

5. **Deploy**
   - Railway will auto-build and deploy.
   - Wait for build to finish (1-2 mins). Check for logs/errors under `Deployments`.

6. **Get the Live URL**
   - After successful deploy, your backend will be accessible at e.g. `https://project5-chat-widget-production.up.railway.app`

7. **Update Frontend API URL**
   - In your `index.html` or frontend code, update the fetch/axios URL to point to your Railway backend (not `localhost`).

---

## 4. Live/Production Checks

**Test all endpoints after deploy:**
- Send a sample request from the frontend and verify responses.
- Confirm that the response includes the actual OpenAI reply.
- Confirm the API key is never exposed in the network tab or page source.
- Ensure proper CORS settings (Factory CORS, restrict to your frontend domain for production).
- Endpoint should log errors and handle failed requests gracefully.
- Confirm Railway service shows status `⚡️ Running`.

---

## 5. Going Live

- Add your production Railway URL to the frontend widget embed code.
- Test end-to-end: send a message, receive an AI response, with branding for Genesis AI Systems.
- Confirm performance and latency are acceptable for demo use.

---

## 6. Troubleshooting

- **"Missing API key"**: Check that Railway env vars are set and re-deploy.
- **CORS errors**: Add your production frontend domain to CORS allowlist in the Express server.
- **504/Timeouts**: Confirm Railway service is running. Review `server.js` for async issues.
- **OpenAI errors**: Ensure your OpenAI API key has production quota and no IP restrictions.

---

## 7. Monitoring and Logs

- Railway dashboard → Service → Deployments → Logs — view all API call logs and errors.
- Add extra `console.log()` or logging middleware as needed.
- Use Railway's web inspector to visually verify env vars, health, and traffic.

---

## 8. Updating your Service

- Commit & push changes to GitHub; Railway auto-redeploys.
- For critical live hotfixes, use `railway up` locally (if installed) or [deploy manually](https://docs.railway.app/deployment/deploy-from-local).

---

## 9. Genesis AI Systems Support

For help deploying or debugging:
- Email: [info@genesisai.systems](mailto:info@genesisai.systems)
- Website: [https://genesisai.systems](https://genesisai.systems)
- Founder: Trendell Fordham

---

## 10. Reference
- [Railway Docs](https://docs.railway.app/deployment/deploy-from-github)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

---

**Genesis AI Systems — Done-for-you AI automation for local businesses**  
[genesisai.systems](https://genesisai.systems) · Founded by Trendell Fordham · Detroit, MI