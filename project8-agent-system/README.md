# Project 8: Self-Healing, Self-Deploying 4-Agent System

This project is a portfolio-grade autonomous engineering system built with **CrewAI + Claude API + GitHub Actions**.

It runs four agents in sequence:

1. `SecurityAgent`
2. `QAAgent`
3. `EvolutionAgent`
4. `DeployAgent`

The system is designed to scan code, validate quality, monitor upstream model/platform changes, and deploy only when the prior stages pass.

## Architecture

The design intentionally separates:

- **deterministic operational services** for scanning, testing, Git, email, and Google Sheets
- **CrewAI agents** for role-based reasoning, decision framing, and structured reporting

This makes the system easier to trust, easier to test, and easier to extend.

## What Each Agent Does

### SecurityAgent

- runs Bandit against the target repo
- runs Semgrep against the target repo
- scans for exposed API keys and dangerous patterns
- classifies findings into `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
- auto-fixes supported `LOW` severity issues
- blocks deployment if unresolved `HIGH` or `CRITICAL` issues remain

### QAAgent

- runs dynamic Pytest smoke tests across Python files
- validates n8n workflow JSON files
- tests configured webhook endpoints
- reports specific pass/fail details
- asks Claude for fix suggestions when tests fail

### EvolutionAgent

- fetches OpenAI and Anthropic RSS feeds
- inventories model references in the codebase
- asks Claude to suggest model and prompt upgrades
- optionally applies safe model-string replacements
- appends an entry to `EVOLUTION_CHANGELOG.md`

### DeployAgent

- validates that Security, QA, and Evolution stages passed
- creates a Git commit for approved changes
- triggers GitHub Actions when running outside CI
- sends deployment summary via Gmail SMTP
- rolls back the automated commit if push, trigger, or downstream workflow execution fails

## Project Structure

```text
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

## Setup

### Python version

Use **Python 3.11 or 3.12** for this project. The GitHub Actions workflow is pinned to Python `3.11`, and CrewAI currently does not install cleanly on Python `3.14`.

### 1. Create and activate a virtual environment

```bash
python3.11 --version
cd project8-agent-system
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your environment file

```bash
cp .env.example .env
```

Fill in at minimum:

- `ANTHROPIC_API_KEY`
- `TARGET_REPO_PATH`
- `GITHUB_TOKEN`
- `GITHUB_REPOSITORY`
- `CLAUDE_MODEL` and `CREWAI_MODEL` if you want to override the defaults

Optional but recommended:

- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GMAIL_SMTP_USERNAME`
- `GMAIL_SMTP_PASSWORD`
- `GMAIL_TO`
- `WEBHOOK_URLS`
- `DEPLOY_POLL_SECONDS`
- `DEPLOY_TIMEOUT_MINUTES`

## Running Locally

### Standard run

```bash
python main.py
```

### Dry run without deployment

```bash
python main.py --no-deploy
```

### Manual CI-style run

```bash
python main.py --source manual-webhook
```

## Mock Demo Mode

If you want to demo Project 8 without live credentials, use the mock runner instead of `main.py`.

### Happy-path demo

```bash
python mock_run.py --scenario success
```

### Blocked deployment demo

```bash
python mock_run.py --scenario blocked
```

### Rollback demo

```bash
python mock_run.py --scenario rollback
```

### JSON output for screenshots or Loom demos

```bash
python mock_run.py --scenario success --json
```

The mock runner does not call Claude, CrewAI, GitHub, Gmail, or Google Sheets. It simply renders realistic portfolio-safe run summaries for the three most useful demo scenarios.

## Manual Trigger via GitHub Webhook

This project supports manual trigger through GitHub `repository_dispatch`.

Example:

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/your-org/your-repo/dispatches \
  -d '{"event_type":"manual-agent-run","client_payload":{"source":"manual-webhook"}}'
```

## GitHub Actions

The workflow file runs:

- daily at `2:00 AM UTC`
- on `workflow_dispatch`
- on `repository_dispatch` with event `manual-agent-run`

When the system is launched outside GitHub Actions, `DeployAgent` will:

1. push the approved automated changes
2. trigger the GitHub Actions workflow through `repository_dispatch`
3. poll the workflow run until it finishes
4. create and push a revert commit automatically if the workflow concludes with failure

## Google Sheets Logging

If Google credentials are configured, the run logger appends one row per execution with:

- timestamp
- trigger source
- per-agent status
- key findings summary
- CrewAI executive summary
- deployment metadata

## Safety Notes

- `ALLOW_AUTO_DEPLOY=false` by default
- `EVOLUTION_AUTO_APPLY=false` by default
- `HIGH` and `CRITICAL` security findings block deployment
- scanner outages also block deployment instead of silently passing
- rollback only targets commits created by this system during the current run

## SOLID Design Notes

- `config.py` only loads settings
- `models.py` only defines data contracts
- each `services/` file does one integration job
- each `agents/` file does one stage of the sequence
- `orchestrator.py` only coordinates the flow
- `main.py` only handles CLI entrypoint concerns

## Recommended Demo Flow

When showing this project to technical clients:

1. explain the 4-agent sequence
2. show the GitHub Actions schedule
3. show how security and QA block deployment
4. show the evolution changelog concept
5. show how results are logged to Google Sheets
6. explain why deployment is off by default for safety
