# Task 1 — Resolve Working Tree

## Commands Run
- `git status --short`
- `git diff --name-only`

## Findings
- `git diff --name-only` returned nothing. There are no modified tracked files in the worktree right now.
- The worktree is entirely untracked files and directories. None of them should be bulk-committed blindly.

## Untracked Files Audit

### Local-only / environment-sensitive
- `.env.local` — local secrets/config file. **Not safe to commit.**
- `.env.local.example` — example env file. **Safe only if intentionally sanitized; otherwise review before commit.**
- `shared_env.py` — shared env helper. **Code file; review before commit.**
- `SECRETS_REGISTRY.md` — secrets inventory. **Sensitive; do not commit casually.**
- `SECRET_USAGE_MAPPING.md` — maps secrets to usage. **Sensitive; do not commit casually.**

### Local editor / agent workspace noise
- `.claude/worktrees/` — Claude worktree metadata. **Safe to ignore.**
- `.vscode/` — editor config. **Safe to ignore.**

### Workflow drafts / CI experiments
- `.github/workflows/project10_detroit_send_window.yml` — project 10 workflow draft. **Unsafe to commit without review.**
- `.github/workflows/project10_forced_pause_rollback.yml` — project 10 rollback workflow draft. **Unsafe to commit without review.**
- `.github/workflows/project10_resume_gate.yml` — project 10 resume workflow draft. **Unsafe to commit without review.**
- `.github/workflows/project10_state_transition.yml` — project 10 state workflow draft. **Unsafe to commit without review.**
- `.github/workflows/resend_delivery_sync.yml` — resend sync workflow. **Unsafe to commit without review.**
- `.github/workflows/scripts/email_acquisition.py` — shared email acquisition helper. **Code file; intentionally in-progress, not safe to commit as part of Task 1.**

### Archived / shared content and docs
- `_archive/` — archive directory. **Safe to ignore unless explicitly needed.**
- `_shared/` — shared reference docs. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/CALL_ROUTING.md` — phone access routing doc. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/CLAUDE_PHONE_ACCESS_READY.md` — readiness note. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/CLOUDFLARE_TUNNEL.md` — tunnel note. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/TAILSCALE_SETUP.md` — setup note. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/TELEGRAM_DIAGNOSTIC.md` — diagnostic note. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/TELEGRAM_SETUP.md` — setup note. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/TWILIO_FIX.md` — Twilio fix note. **Safe to ignore unless explicitly needed.**

### Generated or project docs/assets
- `home-services.html` — generated HTML asset. **Safe to ignore unless intentionally part of deliverable.**
- `law-firm.html` — generated HTML asset. **Safe to ignore unless intentionally part of deliverable.**
- `med-spa.html` — generated HTML asset. **Safe to ignore unless intentionally part of deliverable.**
- `project10-marketing-agent/DOCTRINE_REUSE_MAP.md` — project 10 doc. **Safe to ignore unless explicitly targeted.**
- `project10-marketing-agent/LAUNCH_READINESS/` — project 10 launch-readiness docs. **Safe to ignore unless explicitly targeted.**
- `project10-marketing-agent/MIGRATION_FROM_P9_DOCTRINE.md` — migration doc. **Safe to ignore unless explicitly targeted.**
- `project10-marketing-agent/NATIVE_CONTROL_CHECKLIST.md` — checklist doc. **Safe to ignore unless explicitly targeted.**
- `project10-marketing-agent/NATIVE_CONTROL_DOCTRINE_AUDIT.md` — audit doc. **Safe to ignore unless explicitly targeted.**
- `project10-marketing-agent/NATIVE_PAUSE_RESPONSE_PLAYBOOK.md` — playbook doc. **Safe to ignore unless explicitly targeted.**
- `project10-marketing-agent/scripts/` — project 10 scripts. **Unsafe to bulk-commit without inspection.**
- `project10-marketing-agent/state/` — project 10 state outputs. **Usually generated; safe to ignore unless specifically required.**
- `project11-client-success/01_CLIENT_ONBOARDING_INTAKE_FORM.md` — client-success doc. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/02_KICKOFF_SOP.md` — client-success doc. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/03_DEPLOYMENT_CHECKLIST.md` — client-success doc. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/04_ROLLBACK_SOP.md` — client-success doc. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/05_QA_ACCEPTANCE_CHECKLIST.md` — client-success doc. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/06_TESTIMONIAL_CAPTURE_WORKFLOW.md` — client-success doc. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/07_14_DAY_UPSELL_TRIGGER_WORKFLOW.md` — client-success doc. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/08_RETENTION_EXPANSION_MONETIZATION/` — retention docs folder. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/CLIENT_ONBOARDING_CHECKLIST.md` — client-success doc. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/DISCOVERY_CALL_QUESTIONNAIRE.md` — client-success doc. **Safe to ignore unless explicitly targeted.**
- `project11-client-success/PROJECT_11_COMPLETE_AUDIT.md` — audit doc. **Safe to ignore unless explicitly targeted.**
- `project12-client-success/` — project 12 content. **Safe to ignore unless explicitly targeted.**
- `project13-internal-governor-dashboard/` — project 13 content. **Safe to ignore unless explicitly targeted.**
- `project14-growth-engine/` — project 14 content. **Safe to ignore unless explicitly targeted.**
- `project15-shared-scale-core/` — project 15 content. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/FOUNDER_LAUNCH_SIGNOFF_RUNBOOK.md` — project 9 runbook. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/OUTBOUND_CONTROL_CHAIN_WORKFLOW_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/OUTBOUND_DRY_RUN_GUARD_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/OUTBOUND_DRY_RUN_GUARD_WORKFLOW_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/OUTBOUND_FIRST_10_MONITOR_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/OUTBOUND_LAUNCH_AUTOMATION_PLAN.md` — project 9 plan. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/OUTBOUND_LAUNCH_CHECKLIST.md` — project 9 checklist. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/OUTBOUND_LAUNCH_STATE_TRANSITION_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/OUTBOUND_RESUME_GATE_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/OUTREACH_SCRIPTS.md` — project 9 outreach doc. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/prompts/` — prompt assets. **Safe to ignore unless explicitly targeted.**
- `project9-sales-agent/scripts/resend_delivery_sync.py` — project 9 script. **Unsafe to commit without inspection.**
- `project9-sales-agent/state/email_acquisition_audit.ndjson` — generated audit log. **Safe to ignore.**
- `project9-sales-agent/state/outbound_dedup_hash_log.ndjson` — generated audit log. **Safe to ignore.**
- `project9-sales-agent/state/outbound_first_10_send_events.ndjson` — generated audit log. **Safe to ignore.**
- `project9-sales-agent/state/suppression_list.ndjson` — generated audit log. **Safe to ignore.**
- `shared-docs/` — shared docs directory. **Safe to ignore unless explicitly targeted.**
- `v1-revenue-system/lead_revenue_pipeline.py` — live pipeline code. **Unsafe to commit without inspection.**
- `v1-revenue-system/proof_artifacts/` — proof artifacts. **Safe to ignore unless explicitly targeted.**
- `v1-revenue-system/scripts/` — repo scripts. **Unsafe to bulk-commit without inspection.**
- `v1-revenue-system/state/` — state outputs. **Safe to ignore unless explicitly targeted.**
- `v1-revenue-system/tests/` — test suite additions. **Safe to inspect and possibly commit later, but not part of Task 1.**

## Task 1 Decision
- Safe to proceed with Task 1 using only `ops/codex-output.md` for the commit.
- Unsafe to include the active code files or any broad untracked directories in the Task 1 commit.
