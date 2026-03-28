You are a senior developer for Genesis AI Systems.
Create all requested files completely.
Return them as a JSON array as instructed.


# Genesis AI Systems — Prompt 2 of 4

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
Customer Zero is Genesis AI Systems itself. Every monitoring and deployment system must protect our own agency first.

---

## PART 3: GITHUB ACTIONS AGENT PIPELINE

Save workflow files to `/Users/genesisai/portfolio/.github/workflows/`

Save Python scripts to `/Users/genesisai/portfolio/.github/workflows/scripts/`

### AGENT 1: SECURITY AGENT
File: `.github/workflows/security_agent.yml`

Triggers:
- `cron: '0 * * * *'` every hour
- push to `main`
- `workflow_dispatch`

Checks:
1. `PORTFOLIO_WEBSITE.html` for exposed keys
2. Hardcoded credentials anywhere
3. Insecure external scripts
4. Missing HTTPS links
5. XSS vulnerabilities
6. Bandit on all Python files
7. `.gitignore` protecting sensitive files
8. `.env` files accidentally committed

On `CRITICAL`:
- Fail workflow
- SMS to `+13134002575`
- Email to `info@genesisai.systems`
- Create GitHub issue

On `HIGH`:
- Email alert
- Warning annotation

On `LOW` or `MEDIUM`:
- Log to `security_report.json`
- Do not fail workflow

Output:
- `security_report.json`
- README badge

### AGENT 2: QA AGENT
File: `.github/workflows/qa_agent.yml`

Triggers:
- `cron: '0 * * * *'` every hour
- after security passes
- push to `main`
- `workflow_dispatch`

Checks:
1. `genesisai.systems` returns `200`
2. Page load under `3 seconds`
3. All internal links work
4. All external links work
5. Calendly button uses the correct URL
6. Contact email link works
7. HTML structure is valid
8. All 8 project cards present
9. All 8 live demos loading
10. Meta title and description set
11. Open Graph tags present
12. SSL certificate valid
13. Mobile viewport present
14. Basic WCAG accessibility
15. Demo server responding
16. Contact form present
17. Footer links working
18. Privacy policy page live
19. Terms page live
20. 404 page working

On failure:
- SMS and email immediately
- Create GitHub issue: `QA FAILED: [test name]`
- Fail workflow
- Block deploy agent

Output:
- `qa_report.json`
- README badge

### AGENT 3: EVOLUTION AGENT
File: `.github/workflows/evolution_agent.yml`

Triggers:
- `cron: '0 2 * * *'` daily at 2am
- `workflow_dispatch`

Checks:
1. Outdated dependencies
2. OpenAI changelog RSS
3. Anthropic changelog
4. Deprecated model names:
   - `gpt-4o-mini-2024-07-18`
   - `claude-sonnet-4-6`
   - `claude-haiku-4-5-20251001`
5. Copyright year should be `2026`
6. CDN library versions
7. Claude API improvement suggestions
8. Demo server performance
9. New AI capabilities to add

Output:
- `evolution_report.json`
- GitHub issues

### AGENT 4: DEPLOY AGENT
File: `.github/workflows/deploy_agent.yml`

Triggers:
- After QA passes on push to `main`
- `workflow_dispatch`

Steps:
1. Verify Security passed
2. Verify QA passed
3. Create deployment record
4. Deploy to GitHub Pages
5. Wait 60 seconds
6. Run post-deployment QA:
   - `genesisai.systems` returns `200`
   - Page title correct
   - Calendly button present
   - All 8 demos loading
7. SMS and email on success or failure
8. Log to `deployments.json`

Output:
- `deployments.json`
- deployment badge

### MASTER ORCHESTRATION
File: `.github/workflows/master_orchestration.yml`

Triggers:
- `cron: '0 * * * *'` every hour
- push to `main`
- `workflow_dispatch`

Flow:
- `Security → QA → Evolution (daily) → Deploy (on push)`

Health report must include:
- Overall score `0-100`
- All 4 agent statuses
- Demo server uptime
- All 8 demo response times
- Uptime percentage
- Open issues count

Notifications:
- `CRITICAL/FAILED` → SMS and email immediately
- Hourly pass → silent
- Daily digest → email at 8am always
- Weekly report → email Monday at 9am always
- Deployment → email always

### SHARED NOTIFICATION MODULE
File: `.github/workflows/scripts/notify.py`

Apply SOLID principles.

Abstract base class: `BaseNotifier`
- Method: `send(subject, message, priority)`
- Priority enum values:
  - `CRITICAL`
  - `HIGH`
  - `MEDIUM`
  - `LOW`
  - `INFO`

Concrete classes:
- `EmailNotifier` using SendGrid
- `SMSNotifier` using Twilio
- `SlackNotifier` using webhook
- `GitHubNotifier` using issues

Class: `NotificationOrchestrator`
- `CRITICAL` → all channels
- `HIGH` → email + SMS
- `MEDIUM` → email only
- `LOW` → daily digest
- `INFO` → weekly report

SMS failure format:

```text
🚨 Genesis AI Systems Alert
Agent: [Name]
Status: FAILED
Issue: [Description]
Time: [timestamp]
Fix: github.com/prosperouscollection-prog/ai-automation-portfolio/actions
```

SMS recovery format:

```text
✅ Genesis AI Systems
Agent: [Name]
Status: RECOVERED
All systems operational
Time: [timestamp]
```

Daily digest subject:

```text
Genesis AI Systems — Daily Health [date]
```

Weekly report subject:

```text
Genesis AI Systems — Weekly Report [dates]
```

Branded HTML email template requirements:
- Navy `#0f172a` header
- `Genesis AI Systems` in white
- Electric blue `#2563eb` accents
- Clean professional layout
- Footer:
  - `genesisai.systems | info@genesisai.systems | (313) 400-2575`

All API responses must include:

```json
{
  "powered_by": "Genesis AI Systems",
  "website": "https://genesisai.systems",
  "contact": "info@genesisai.systems"
}
```

Also create:
- `.github/workflows/scripts/report_generator.py`
  - HTML email reports
  - SMS short messages
  - Slack blocks
  - GitHub issue markdown
- `.github/workflows/scripts/requirements.txt`
  - `anthropic`
  - `openai`
  - `twilio`
  - `sendgrid`
  - `requests`
  - `beautifulsoup4`
  - `lxml`
  - `bandit`
  - `semgrep`
  - `pytest`
  - `playwright`
  - `python-dotenv`

### README BADGES
Update `/Users/genesisai/portfolio/README.md`

Add at the top:

```markdown
![Security](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/security_agent.yml/badge.svg)
![QA](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/qa_agent.yml/badge.svg)
![Deploy](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/deploy_agent.yml/badge.svg)
```

Add this section:

```markdown
## System Health — Genesis AI Systems
Monitored 24/7 by autonomous 4-agent system:
- Security Agent: every hour
- QA Agent: every hour
- Evolution Agent: daily
- Deploy Agent: every deployment
Live: https://genesisai.systems
```

---

## PART 4: SETUP GUIDE AND AUTOMATION

### SETUP_GUIDE.md
File: `/Users/genesisai/portfolio/SETUP_GUIDE.md`

Create the full guide with these sections:

#### Section 1: Twilio Setup
- `twilio.com` → free account
- Verify `(313) 400-2575`
- Get a Twilio phone number
- Find SID and Auth Token
- Cost: about `$1/month`

Collect:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `ALERT_PHONE_NUMBER: +13134002575`

#### Section 2: SendGrid Setup
- `sendgrid.com` → free account with `100/day` free
- Verify `info@genesisai.systems`
- Create API key with Mail Send scope
- Add DNS to Cloudflare
- Cost: `Free`

Collect:
- `SENDGRID_API_KEY`
- `SENDGRID_FROM_EMAIL: info@genesisai.systems`
- `SENDGRID_FROM_NAME: Genesis AI Systems`

#### Section 3: Slack Setup (optional)
- Create workspace: `Genesis AI Systems`
- Channel: `#system-alerts`
- Create app at `api.slack.com`
- Enable Incoming Webhooks
- Cost: `Free`

Collect:
- `SLACK_WEBHOOK_URL`

#### Section 4: Anthropic API
- `console.anthropic.com`
- Create key: `genesis-ai-systems-agents`
- Cost: about `$5–10/month`

Collect:
- `ANTHROPIC_API_KEY`

#### Section 5: OpenAI API
- `platform.openai.com/api-keys`
- Create key: `genesis-ai-systems-agents`
- Set spend limit: `$20/month`
- Cost: about `$5–10/month`

Collect:
- `OPENAI_API_KEY`

#### Section 6: GitHub Secrets
URL:

```text
github.com/prosperouscollection-prog/ai-automation-portfolio/settings/secrets/actions
```

Add all secrets:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `ALERT_PHONE_NUMBER (+13134002575)`
- `SENDGRID_API_KEY`
- `SENDGRID_FROM_EMAIL (info@genesisai.systems)`
- `SENDGRID_FROM_NAME (Genesis AI Systems)`
- `SLACK_WEBHOOK_URL (optional)`
- `SITE_URL (https://genesisai.systems)`
- `CALENDLY_URL (full Calendly URL)`
- `NOTIFICATION_EMAIL (info@genesisai.systems)`
- `N8N_WEBHOOK_BASE_URL (https://n8n.genesisai.systems)`
- `DEMO_SERVER_URL (Railway URL after deploy)`
- `VAPI_PUBLIC_KEY (from Vapi dashboard)`
- `RAILWAY_TOKEN (from Railway dashboard)`

#### Section 7: DigitalOcean n8n Setup
- `digitalocean.com` → create a `$12/month` Droplet
- Ubuntu 24.04
- Install n8n with npm
- Set up nginx reverse proxy
- Point `n8n.genesisai.systems` to the Droplet
- Add SSL with Certbot
- Cost: `$12/month`

#### Section 8: Railway Demo Server
- `railway.app` → create account
- Connect GitHub repo
- Deploy `demo-server` folder
- Add environment variables
- Cost: about `$5/month`

#### Section 9: Local Testing
Add `.env` template and these test commands:

```bash
python .github/workflows/scripts/notify.py --test-sms
python .github/workflows/scripts/notify.py --test-email
python .github/workflows/scripts/notify.py --test-slack
```

#### Section 10: Monthly Costs
- GitHub Actions: `$0`
- Twilio: about `$1/month`
- SendGrid: `$0`
- Slack: `$0`
- Anthropic: about `$5–10/month`
- OpenAI: about `$5–10/month`
- DigitalOcean: `$12/month`
- Railway: `$5/month`
- Total: about `$23–38/month`

### SETUP SCRIPT
File: `/Users/genesisai/portfolio/setup.sh`

Create an interactive Bash script that:
1. Checks Python, pip, git, and node
2. Installs Python dependencies
3. Creates a `.env` template
4. Opens signup URLs in the browser
5. Guides the user through each step
6. Tests each connection
7. Confirms everything is ready
8. Prints `Step X of 10 complete`
9. Uses green success and red failure colors

### SECRETS CHECKLIST
File: `/Users/genesisai/portfolio/SECRETS_CHECKLIST.md`

Required:
- [ ] `ANTHROPIC_API_KEY`
- [ ] `OPENAI_API_KEY`
- [ ] `TWILIO_ACCOUNT_SID`
- [ ] `TWILIO_AUTH_TOKEN`
- [ ] `TWILIO_FROM_NUMBER`
- [ ] `ALERT_PHONE_NUMBER`
- [ ] `SENDGRID_API_KEY`
- [ ] `SENDGRID_FROM_EMAIL`
- [ ] `SENDGRID_FROM_NAME`
- [ ] `SITE_URL`
- [ ] `NOTIFICATION_EMAIL`
- [ ] `CALENDLY_URL`
- [ ] `N8N_WEBHOOK_BASE_URL`
- [ ] `DEMO_SERVER_URL`
- [ ] `VAPI_PUBLIC_KEY`
- [ ] `RAILWAY_TOKEN`

Optional:
- [ ] `SLACK_WEBHOOK_URL`

Verification:
- [ ] Test SMS at `(313) 400-2575`
- [ ] Test email at `info@genesisai.systems`
- [ ] Security agent passing
- [ ] QA agent passing
- [ ] All 8 demos working
- [ ] `genesisai.systems` loading correctly

### TEST NOTIFICATIONS SCRIPT
File: `.github/workflows/scripts/test_notifications.py`

Use SOLID principles.

Requirements:
- SMS to `+13134002575`
- Email to `info@genesisai.systems`
- Slack if webhook exists
- Clear pass/fail per channel

Test SMS body:

```text
✅ Genesis AI Systems
Test notification successful!
Your agent monitoring is active.
- Trendell Fordham
  genesisai.systems
```

Test email subject:

```text
✅ Genesis AI Systems — Notification Test
```

Test email body:

```text
This is a test from Genesis AI Systems agent monitoring system.

If you received this, notifications work.

Monitoring: https://genesisai.systems

Trendell Fordham
Founder, Genesis AI Systems
info@genesisai.systems
(313) 400-2575
```

---

## QUALITY STANDARDS

Every file must:
- Use SOLID principles in Python
- Never expose API keys in frontend code
- Include docstrings for classes and functions
- Use pinned GitHub Action versions
- Include Genesis AI Systems branding
- Reference Trendell Fordham as founder
- Link back to `https://genesisai.systems`
- Use reliable error handling and safe notification fallbacks

Do not skip any section. Do not truncate any file. Complete everything fully.
