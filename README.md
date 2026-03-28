![Security](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/security_agent.yml/badge.svg)
![QA](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/qa_agent.yml/badge.svg)
![Deploy](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/deploy_agent.yml/badge.svg)

# Genesis AI Systems

**Tagline:** *Done-for-you AI automation for local businesses*

**Website:** [https://genesisai.systems](https://genesisai.systems)

**Founder:** Trendell Fordham  
**Email:** info@genesisai.systems  
**Phone:** (313) 400-2575  
**GitHub:** [prosperouscollection-prog/ai-automation-portfolio](https://github.com/prosperouscollection-prog/ai-automation-portfolio)  
**Location:** Detroit, MI  

---

## Overview
Genesis AI Systems provides done-for-you automation solutions for local businesses, using advanced AI operational agents to maximize uptime and security. This repository contains the self-hosted AI automation portfolio for the agency, monitored and maintained by a fully autonomous 4-agent system.

**Mission:** _Customer Zero is Genesis AI Systems itself. Our automation agents and monitoring pipeline always protect our agency and site first._

---

## System Health — Genesis AI Systems
Monitored 24/7 by autonomous 4-agent system:
- **Security Agent:** every hour · checks for credentials, malware, and exploits
- **QA Agent:** every hour · tests site speed, links, accessibility, and key features
- **Evolution Agent:** daily · catches dependency drift and new AI capabilities
- **Deploy Agent:** each deployment · ensures zero-regression production

Live: [https://genesisai.systems](https://genesisai.systems)

---

### Current Automation Pipeline

| Agent         | Schedule                 | Checks                                                            | Alerts/Badges                |
|---------------|--------------------------|-------------------------------------------------------------------|------------------------------|
| Security      | Hourly & on push         | Keys, credentials, scripts, XSS, HTTPS, `.env`, Bandit            | Badge, Report, SMS/email     |
| QA            | After Security, Hourly   | Uptime, speed, demos, links, meta, forms, 20+ checks              | Badge, Report, SMS/email     |
| Evolution     | Daily (2am UTC)          | Dependencies, model updates, API changelogs, demo performance     | Report, Issues               |
| Deploy        | After QA, on push        | Deploys to Pages, waits, verifies production                      | Badge, Log, SMS/email        |

### Health & Uptime Reporting
- **Overall System Score:** 0–100, updated hourly
- **Agent Status:** real-time pass/fail and summary per agent
- **Demo Server:** uptime and 8 live demo response times
- **Issues:** open issue count always visible
- **Notifications:** SMS & email for failures, silent when healthy

---

## Quick Links
- [Setup Guide](./SETUP_GUIDE.md)
- [Secrets Checklist](./SECRETS_CHECKLIST.md)
- [Automated Workflows](.github/workflows/)
- [Notification Scripts](.github/workflows/scripts/notify.py)

---

## Technology Used
- Python 3.11+, GitHub Actions, Playwright, Bandit, Semgrep, BeautifulSoup4, Anthropic & OpenAI APIs
- Secure notifications: Twilio (SMS), SendGrid (Email), Slack, GitHub Issues

---

### Branding
- Colors: Navy (#0f172a), Electric Blue (#2563eb)
- All notifications are branded and reference [Genesis AI Systems](https://genesisai.systems) and Trendell Fordham (Founder).

---

## Contact
- Website: [https://genesisai.systems](https://genesisai.systems)
- Email: info@genesisai.systems
- Phone: (313) 400-2575
- Calendly: [Free AI Demo Call](https://calendly.com/genesisai-info-ptmt/free-ai-demo-call)

---

> **Genesis AI Systems** — protecting your business with real autonomous AI automation.  
> _Powered by our own technology, 24/7_