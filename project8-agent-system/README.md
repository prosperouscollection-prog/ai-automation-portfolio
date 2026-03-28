# Project 8: Self-Healing, Self-Deploying Agent System

This system is Genesis AI Systems' portfolio-grade, production-ready, self-healing agent platform. It fully automates code audits, QA, evolution tracking, and deployment using **CrewAI, Claude API, and GitHub Actions**. All engineering automations run live on our actual agency repository and infrastructure, supporting Customer Zero: Genesis AI Systems itself.

---

## System Overview

**Agents Sequence (runs in order):**

1. **SecurityAgent** — Code security scans and secrets checks
2. **QAAgent** — Automated testing and workflow/endpoint validation
3. **EvolutionAgent** — LLM/provider model drift scanning; suggests/auto-updates model refs
4. **DeployAgent** — Deploys if prior 3 agents pass, triggers GitHub Actions, notifies, rolls back on error

**Architecture**
- Separation of concerns: operational services vs. agentic reasoning
- Deterministic, auditable actions for trust, testability, and extensibility
- All code, workflow, and notification paths are production-grade and live

---

## System Readiness
- **Current Status:** Active / Production
- **Monitoring:** All agent runs and workflow states visible on GitHub and Google Sheets
- **Master production readiness:** Verified as per `/Users/genesisai/portfolio/MASTER_PRODUCTION_CHECKLIST.md` project 8 criteria
- **All GitHub Actions workflows live and triggered nightly + manual/manual dispatch**

---

## GitHub Actions Workflows

**Workflow file:** `.github/workflows/agent_system.yml`

**Triggers:**
- Scheduled: every night at `2:00 AM UTC`
- Manual: `workflow_dispatch` (button in GitHub UI)
- Manual: `repository_dispatch` (for API/manual triggers, e.g. demo server)

**Jobs in workflow:**
- **Checkout and Setup:** Sets up Python and installs requirements
- **Run Agent System:** Invokes the agent sequence (with logs)
- **Notification:** Notifies via email/SMS on completion/failure
- **Badges:** Live badges reported for workflow status, last run timestamp, and uptime

**Live demo:** Project 8 launch page in the portfolio shows real-time badge, timestamp, health, and recent activity from the workflow.

---

## Secret Validation & Security

- **GitHub Secrets checked:**
  - `ANTHROPIC_API_KEY` (Claude)
  - `GITHUB_TOKEN` (deploy/rollback, workflow dispatch)
  - `GOOGLE_SERVICE_ACCOUNT_JSON` (Google Sheets — logging)
  - `GOOGLE_SHEETS_SPREADSHEET_ID` (Storage of agent runs)
  - `GMAIL_SMTP_USERNAME` & `GMAIL_SMTP_PASSWORD` (Deployment notification)
  - `DEPLOY_AGENT_SMS_PHONE` (SMS alerts for failed/risky deployments)
- **Validation:**
  - At program start, all required secrets checked by `config.py` and graceful exit with error logging if missing
  - GitHub Actions checks for secrets before run, failing fast if missing
  - All notification and logging services validate their own required credentials
- **Audit:** All agent/worfklow actions, notification results, and errors are logged for monitoring and auditability.

---

## Live Agent Monitoring

- **Continuous Monitoring:**
  - All agent system runs (daily and manual) are logged to Google Sheets and visible in the production sheet
  - GitHub Actions status badges are shown live in the Project 8 portfolio demo, including last run time, workflow health, and uptime % for real transparency
- **Notifications:**
  - SMS/email alerts sent on completion, failure, or rollback events to founder/ops phone: `+13134002575` and `info@genesisai.systems`
- **Live audit record:**
  - All runs: timestamp, triggering method, agent pass/fail details, scan findings, summary, and deployment result
  - Rollbacks and error conditions logged and surfaced in both sheets and email/SMS notifications

---

## Project Structure

```
project8-agent-system/
├── .env.example
├── .python-version
├── README.md
├── requirements.txt
├── main.py
├── mock_run.py
├── EVOLUTION_CHANGELOG.md
├── .github/
│   └── workflows/
│       └── agent_system.yml
└── agent_system/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── mock_scenarios.py
    ├── crew_factory.py
    ├── orchestrator.py
    ├── agents/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── security_agent.py
    │   ├── qa_agent.py
    │   ├── evolution_agent.py
    │   └── deploy_agent.py
    └── services/
        ├── __init__.py
        ├── command_runner.py
        ├── claude_advisor.py
        ├── google_sheets_logger.py
        ├── gmail_notifier.py
        ├── git_service.py
        └── rss_monitor.py
```

---

## Agent Roles & Flow

### 1. SecurityAgent
- Bandit & Semgrep codebase scan
- Direct API key/dangerous pattern search
- Classifies and remediates `LOW` severity issues, blocks on `HIGH/CRITICAL`

### 2. QAAgent
- Runs Pytest/CI tests
- Validates n8n workflow JSON
- Tests webhooks and API endpoints
- Calls Claude for fix ideas if anything is broken

### 3. EvolutionAgent
- Scrapes OpenAI and Anthropic RSS feeds
- Searches code for provider/model drift/upgrade possibilities
- Asks Claude for recommended updates
- Can auto-update model strings and logs to `EVOLUTION_CHANGELOG.md`

### 4. DeployAgent
- Checks previous agent status
- Git commit for any approved, auto-fixed changes
- If not running in CI, triggers workflow using `repository_dispatch` and polls to completion
- If downstream failed, reverts auto commit(s) and logs notification with rollback reason

---

## Setup Instructions

### Python Environment
- **Python 3.11 or 3.12 REQUIRED**  
  - Use: `python3.11 --version` (CrewAI not yet 3.14+ safe)

### 1. Virtual Environment
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Fill required secrets in .env
```
See `Secret Validation & Security` above for required variables.

---

## Running the Agent System

### Normal Run
```bash
python main.py
```

### Dry Run / No Deploy
```bash
python main.py --no-deploy
```

### Manual CI-Style Run
```bash
python main.py --source manual-webhook
```

### Mock Demo Mode (Safe for Demos)
```bash
python mock_run.py --scenario success
python mock_run.py --scenario blocked
python mock_run.py --scenario rollback
python mock_run.py --scenario success --json
```

---

## Manual GitHub Workflow Trigger

Trigger via GitHub API:
```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/prosperouscollection-prog/ai-automation-portfolio/dispatches \
  -d '{"event_type":"manual-agent-run","client_payload":{"source":"manual-webhook"}}'
```

---

## Monitoring & Logging
- **Google Sheets Production Connection**
  - Logs: timestamp, source, agent pass/fail, findings, summary, deploy result
  - Sheet: Production, shared with genesisai.systems founding ops email
- **Notifications**
  - All deployments/failures/rollbacks alert `info@genesisai.systems` and founder's alert number by SMS/email

---

## Safety & Design Principles
- **All critical actions require validation** — No silent operations
- **Scanners and agent fail blocks downstream** — No silent skips
- **Rollback deletes only system-owned commits**
- **SOLID Principles** — Strict modularity in configuration, models, orchestration, agent, and integration code
- **No API keys or secrets in logs or code**
- **System defaults are safe** — Deploy and evolution changes require explicit toggle

---

## Demo
- Portfolio live demo shows:
  - Real workflow status badges
  - Uptime, health, and last run timestamp
  - Link: [View live runs on GitHub](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions)
  - Label: `These agents ran in the last hour`

---

## Credits
**Genesis AI Systems**
- Founder: [Trendell Fordham](https://genesisai.systems) — (313) 400-2575 — info@genesisai.systems
- Website: https://genesisai.systems
- Contact: info@genesisai.systems — [Book a call](https://calendly.com/genesisai-info-ptmt/free-ai-demo-call)
- Uptime and safety validated for Customer Zero, runs daily for the agency and can be cloned and parameterized per client.

---

For full production launch steps, see `PRODUCTION_CHECKLIST.md` in this folder.
