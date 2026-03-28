# Genesis AI Systems Demo Server — Railway Deployment Guide

This guide shows how to deploy the Genesis AI Systems demo server live on [Railway](https://railway.app) for production use.

---

## 💡 Prerequisites
- Railway account: https://railway.app
- GitHub repo: https://github.com/prosperouscollection-prog/ai-automation-portfolio
- All server code is in `/Users/genesisai/portfolio/demo-server/`
- Node.js 18.x or later
- (Recommended) Use the Railway web UI for setup

---

## 1. Fork/Clone the Repo
If you haven't already, push the project to your own GitHub under `prosperouscollection-prog/ai-automation-portfolio`.

---

## 2. Create a New Railway Project
- Go to https://railway.app
- Click **New Project**
- Choose **Deploy from GitHub repo**
- Select `ai-automation-portfolio` and the `demo-server` directory as your app root (set Railway's working directory to `demo-server`).

---

## 3. Configure Environment Variables
1. In Railway, open **Settings → Variables** for your project.
2. Add the following environment variables (copy from `.env.example` in the repo):

```
PORT=3000
OPENAI_API_KEY=xxxxxx      # Your production OpenAI key
CLAUDE_API_KEY=xxxxxx      # Optional: Claude API Key
N8N_LEAD_WEBHOOK=https://n8n.genesisai.systems/webhook/lead-incoming
N8N_GENESIS_WEBHOOK=https://n8n.genesisai.systems/webhook/genesis-lead
SENDGRID_API_KEY=xxxxxx    # Only if used for email
VAPI_API_KEY=xxxxxx        # Vapi production API key (if needed by server)
G_SHEETS_CREDENTIALS=xxxxx # If using Google Sheets API
NODE_ENV=production
ALLOWED_ORIGIN=https://genesisai.systems
LOG_LEVEL=info
```

- **Never commit real secrets to GitHub! Use Railway's Variables UI or CLI.**

---

## 4. Deploy to Railway
- Railway will detect your `package.json` and auto-install dependencies.
- It will run `npm start` or `node server.js` by default. If not, specify `Start Command` as `node server.js` in Railway settings.
- On first deploy, approve all prompts and wait for the build logs to complete.

---

## 5. Configure CORS Security
- The server restricts CORS by the `ALLOWED_ORIGIN` env variable.
- **Default:** Only https://genesisai.systems is allowed in production.

---

## 6. Confirm Live Server & API Endpoints
1. After deploy, Railway provides a live URL, e.g. `https://genesis-ai-demo.up.railway.app`.
2. Test the health endpoint:
    - Go to: `https://<your-railway-url>/health`
    - You should see:
    
    ```json
    {"status":"ok","powered_by":"Genesis AI Systems","website":"https://genesisai.systems","contact":"info@genesisai.systems"}
    ```
3. Test all required API endpoints (see server.js for the full list).
4. The production frontend at https://genesisai.systems should call your live Railway backend for all demos.

---

## 7. Enable Rate Limiting
- The server enforces **10 requests per IP per hour** by default, set in the code.
- Adjust via the relevant middleware section in `server.js` if you need a custom limit.

---

## 8. Logging and Monitoring
- All demo usage is logged to console. For advanced logging, connect to Railway Log Stream or add a logging platform (Datadog, etc).
- Railway shows live service status and logs.

---

## 9. Production Checks
- Ensure all `.env` variables are set correctly.
- Test all 8 endpoints with real data (n8n, Vapi, OpenAI, Google Sheets).
- Validate CORS is enforced (frontend JS from any origin except genesisai.systems should be blocked).
- Review logs regularly for unauthorized or excess usage.

---

## 10. Troubleshooting
- Check Railway build and runtime logs for errors.
- Restart deploy after adding or changing vars.
- Double-check all API connection keys and URLs in your variables.
- Confirm that the port is set to `3000` or the value provided in Railway's `PORT` var.

---

## 11. Updating or Redeploying
- Push code changes to GitHub main branch.
- Railway will auto-trigger redeployment.

```bash
git add .
git commit -m "Update demo server for production on Railway"
git push origin main
```
- Optionally, trigger a manual deploy in the Railway dashboard.

---

## 12. Useful Links
- [Railway Docs](https://docs.railway.app/)
- [Genesis AI Systems](https://genesisai.systems)
- [Trendell Fordham](https://genesisai.systems/#about)
- [Support: info@genesisai.systems](mailto:info@genesisai.systems)

---

# ✅ After Launch: Live Check List
- [ ] `https://<your-railway-url>/health` returns status ok
- [ ] All rate limits work as expected
- [ ] Only `https://genesisai.systems` requests are allowed (CORS)
- [ ] All demo endpoints proxy requests correctly to OpenAI, Claude, n8n, and Vapi
- [ ] Production `.env` secrets are NOT in GitHub
- [ ] All API keys, webhook URLs set to production
- [ ] Site connects to this server for all portfolio demos

---

> **Genesis AI Systems — Automated Live Demo Backend**
> 
> Founder: Trendell Fordham (Detroit, MI)
> <https://genesisai.systems>  |  info@genesisai.systems
> 
> This file last updated: {{date}}
