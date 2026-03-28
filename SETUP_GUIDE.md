# Genesis AI Systems — Comprehensive Setup Guide

Welcome to the setup guide for the Genesis AI Systems agent automation and monitoring platform. This document will take you step-by-step through the setup of all required integrations (Twilio, Resend, Slack, Anthropic, OpenAI, GitHub Secrets, DigitalOcean n8n, Railway demo server), environment variables, local testing commands, and cost estimates.

**Founding Contact:**
- Name: Trendell Fordham
- Email: info@genesisai.systems
- Phone: (313) 400-2575
- Website: https://genesisai.systems

**Tagline:** Done-for-you AI automation for local businesses

---

## Section 1: Twilio Setup (SMS Alerts)

Twilio is used to send real-time SMS notifications for critical events and agent failures.

**Steps:**
1. Sign up at [twilio.com](https://twilio.com) (free account available).
2. Verify your main phone: `(313) 400-2575`
3. Purchase a Twilio phone number for alerts (about **$1/month**). Select a number with SMS capability.
4. In your Twilio Console, navigate to **Settings → API Keys**, and locate your **Account SID** and **Auth Token**.
5. Save the following values for later use:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_FROM_NUMBER` (your Twilio SMS number)
   - `ALERT_PHONE_NUMBER: +13134002575`

*Reference: [Twilio Getting Started](https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account)*

---

## Section 2: Resend Setup (Email Alerts)

Resend is used for branded transactional and notification emails sent by the agents. It is much simpler than SendGrid and works immediately after signup.

**Steps:**
1. Go to [resend.com](https://resend.com).
2. Sign up with `info@genesisai.systems`.
3. Click **API Keys → Create API Key**.
4. Name the key: `genesis-ai-systems`.
5. Set permission to **Full Access**.
6. Copy the key immediately and store it securely.
7. Save the following:
   - `RESEND_API_KEY`

**Notes:**
- Cost: Free for up to **3,000 emails/month**
- No DNS records are needed to get started
- Works immediately after signup

---

## Section 3: Slack Setup (Optional: System Alerts)

Slack can be integrated for instant notifications in the #system-alerts channel.

**Steps:**
1. [Create a Slack workspace](https://slack.com/get-started) called **Genesis AI Systems** (if not existing).
2. Add a public/private channel: `#system-alerts`.
3. [Create a Slack app at api.slack.com](https://api.slack.com/apps?new_app=1), select your workspace.
4. Under **Features → Incoming Webhooks**:
   - Activate Incoming Webhooks
   - Add a new webhook to `#system-alerts`
5. Copy your `SLACK_WEBHOOK_URL`
6. Archive this value; it is optional but recommended.

*Cost: Free plan is sufficient.*

---

## Section 4: Anthropic API Setup

Anthropic powers Claude-based agents for advanced AI functions.

**Steps:**
1. Go to [Anthropic Console](https://console.anthropic.com) (sign up if needed).
2. Under API Keys, create a key named: `genesis-ai-systems-agents`.
3. Copy the key: `ANTHROPIC_API_KEY`

*Estimated monthly cost: $5–10, depending on usage (pay-as-you-go).*

---

## Section 5: OpenAI API Setup

OpenAI powers GPT-4o and related AI workflows.

**Steps:**
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys).
2. Create a key and label it: `genesis-ai-systems-agents`.
3. In Account → Billing, set your usage spend limit (suggested: $20/month).
4. Copy the key: `OPENAI_API_KEY`

*Estimated monthly cost: $5–10, depending on usage (pay-as-you-go).*

---

## Section 6: Setting GitHub Actions Secrets

All credentials and API keys must be stored as encrypted secrets in GitHub.

**URL:**
```
github.com/prosperouscollection-prog/ai-automation-portfolio/settings/secrets/actions
```

**Required secrets (copy/paste):**
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `ALERT_PHONE_NUMBER` *(+13134002575)*
- `RESEND_API_KEY`
- `SLACK_WEBHOOK_URL` *(optional)*
- `SITE_URL` *(https://genesisai.systems)*
- `CALENDLY_URL` *(full Calendly URL, e.g. https://calendly.com/genesisai-info-ptmt/free-ai-demo-call)*
- `NOTIFICATION_EMAIL` *(info@genesisai.systems)*
- `N8N_WEBHOOK_BASE_URL` *(e.g. https://n8n.genesisai.systems)*
- `DEMO_SERVER_URL` *(from Railway deployment)*
- `VAPI_PUBLIC_KEY` *(from Vapi dashboard if applicable)*
- `RAILWAY_TOKEN` *(from Railway dashboard)*

> **Tip:** Click "New repository secret" for each one. Use the _SECRETS_CHECKLIST.md_ to keep track!

---

## Section 7: DigitalOcean n8n Setup

[n8n](https://n8n.io) is a workflow automation tool. Your self-hosted n8n gives flexibility and privacy.

**Steps:**
1. Create a [DigitalOcean](https://digitalocean.com) account.
2. Create a new **Droplet** with **Ubuntu 24.04 LTS** (recommended size: $12/month, 1GB+ RAM).
3. SSH into your droplet and update:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y nodejs npm nginx
   ```
4. [Install n8n globally:](https://docs.n8n.io/hosting/installation/)
   ```bash
   sudo npm install -g n8n
   ```
5. Configure **nginx** reverse proxy for domain `n8n.genesisai.systems` (update A record in Cloudflare to point to this droplet's IP).
6. Set up SSL with Certbot:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d n8n.genesisai.systems
   ```
7. Start n8n as a service and enable autostart (see n8n docs for details).
8. Test webhooks: open [https://n8n.genesisai.systems](https://n8n.genesisai.systems)

*Monthly cost: $12 for droplet. Remember to keep OS and n8n updated!*

---

## Section 8: Railway Demo Server Deployment

Railway is used for hosting the live backend demo server.

**Steps:**
1. Sign up/login at [railway.app](https://railway.app).
2. Connect your GitHub repository: `prosperouscollection-prog/ai-automation-portfolio`.
3. In Railway, create a new project and select the repo's `demo-server` folder for deployment.
4. Add all required environment variables in the Railway web UI:
   - Copy all relevant secrets/environment variables from above.
5. After deployment, copy the `DEMO_SERVER_URL` and store as secret.
6. Confirm server health in Railway's dashboard.

*Monthly cost: $5 (recommended plan for agent demo workloads).*

---

## Section 9: Local Testing (Verifying Integrations)

**Prepare local environment:**
1. Clone your repo and navigate to project root.
2. Copy `.env.template` to `.env` and fill in all required values.
3. Install Python dependencies:
   ```bash
   pip install -r .github/workflows/scripts/requirements.txt
   ```

**Test notification integrations:**
- Run these commands (from project root):
   ```bash
   python .github/workflows/scripts/notify.py --test-sms
   python .github/workflows/scripts/notify.py --test-email
   python .github/workflows/scripts/notify.py --test-slack
   ```
- Expected result:
  - SMS received at `(313) 400-2575`
  - Email received at `info@genesisai.systems`
  - Slack alert (if configured) in `#system-alerts`

*Note: If you encounter errors, check your `.env` for typos and your network/firewall settings.*

---

## Section 10: Monthly Costs (Estimate)

| Service         | Monthly Cost  |
|-----------------|--------------|
| GitHub Actions  | $0           |
| Twilio          | ~$1          |
| Resend          | $0           |
| Slack           | $0           |
| Anthropic       | $5–10        |
| OpenAI          | $5–10        |
| DigitalOcean    | $12          |
| Railway         | $5           |
| **Total**       | **$23–38**   |

---

## Additional Resources

- [Genesis AI Systems Website](https://genesisai.systems)
- [GitHub Repo](https://github.com/prosperouscollection-prog/ai-automation-portfolio)
- [Contact](mailto:info@genesisai.systems)

---

**Remember:**
- Keep all critical credentials in your GitHub repo secrets (never commit to source!).
- Refer to the `/SECRETS_CHECKLIST.md` file before running agents in production.
- All alerting pipelines protect the agency (Genesis AI Systems) first — "Customer Zero".
- For support, schedule a call: [Calendly Schedule](https://calendly.com/genesisai-info-ptmt/free-ai-demo-call)

---

### Branding
This platform and guide are provided and maintained by **Genesis AI Systems**, founded by Trendell Fordham in Detroit, MI.

> **Questions?** Email info@genesisai.systems or visit [genesisai.systems](https://genesisai.systems)
