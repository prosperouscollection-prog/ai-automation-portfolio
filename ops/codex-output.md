# Task 1 — Resolve Working Tree

## Commands run
- `git status --short`
- `git diff --name-only`

## Findings
- `git diff --name-only` returned nothing. There are no modified tracked files in the worktree right now.
- The worktree is entirely untracked files plus the handoff file currently being edited.
- Safe to commit blindly: none. Everything below is either local-only state, generated output, or an in-progress code/doc artifact that should be reviewed first.

## Uncommitted file audit

### Local-only or sensitive
- `.env.local` — local secrets/config. **Not safe to commit.**
- `.env.local.example` — example env file. **Safe only after review/sanitization.**
- `SECRETS_REGISTRY.md` — secret inventory. **Not safe to commit casually.**
- `SECRET_USAGE_MAPPING.md` — secret usage map. **Not safe to commit casually.**
- `shared_env.py` — shared env helper. **Code file; review before commit.**
- `.claude/worktrees/` — Claude worktree metadata. **Safe to ignore.**
- `.vscode/` — editor settings. **Safe to ignore.**

### Workflow drafts / CI experiments
- `.github/workflows/project10_detroit_send_window.yml` — project 10 workflow draft. **Unsafe without review.**
- `.github/workflows/project10_forced_pause_rollback.yml` — project 10 rollback workflow. **Unsafe without review.**
- `.github/workflows/project10_resume_gate.yml` — project 10 resume workflow. **Unsafe without review.**
- `.github/workflows/project10_state_transition.yml` — project 10 state workflow. **Unsafe without review.**
- `.github/workflows/resend_delivery_sync.yml` — resend sync workflow. **Unsafe without review.**
- `.github/workflows/scripts/email_acquisition.py` — active shared acquisition helper; current code is in-progress. **Do not treat as safe to commit in Task 1.**

### Archived/shared docs and assets
- `_archive/` — archive tree. **Safe to ignore unless explicitly needed.**
- `_shared/` — shared docs tree. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/CALL_ROUTING.md` — phone access doc. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/CLAUDE_PHONE_ACCESS_READY.md` — phone access readiness doc. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/CLOUDFLARE_TUNNEL.md` — tunnel doc. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/TAILSCALE_SETUP.md` — tailscale doc. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/TELEGRAM_DIAGNOSTIC.md` — Telegram diagnostic doc. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/TELEGRAM_SETUP.md` — Telegram setup doc. **Safe to ignore unless explicitly needed.**
- `claude-api-phone-access/TWILIO_FIX.md` — Twilio fix doc. **Safe to ignore unless explicitly needed.**
- `home-services.html` — generated HTML asset. **Safe to ignore unless explicitly needed.**
- `law-firm.html` — generated HTML asset. **Safe to ignore unless explicitly needed.**
- `med-spa.html` — generated HTML asset. **Safe to ignore unless explicitly needed.**

### Project 10 docs / scripts / state
- `project10-marketing-agent/DOCTRINE_REUSE_MAP.md` — project 10 doctrine doc. **Safe to ignore unless explicitly needed.**
- `project10-marketing-agent/LAUNCH_READINESS/` — project 10 readiness docs. **Safe to ignore unless explicitly needed.**
- `project10-marketing-agent/MIGRATION_FROM_P9_DOCTRINE.md` — migration doc. **Safe to ignore unless explicitly needed.**
- `project10-marketing-agent/NATIVE_CONTROL_CHECKLIST.md` — checklist doc. **Safe to ignore unless explicitly needed.**
- `project10-marketing-agent/NATIVE_CONTROL_DOCTRINE_AUDIT.md` — audit doc. **Safe to ignore unless explicitly needed.**
- `project10-marketing-agent/NATIVE_PAUSE_RESPONSE_PLAYBOOK.md` — playbook doc. **Safe to ignore unless explicitly needed.**
- `project10-marketing-agent/scripts/` — scripts directory. **Unsafe to bulk-commit without inspection.**
- `project10-marketing-agent/state/` — generated state outputs. **Safe to ignore unless explicitly needed.**

### Project 11+ docs / folders
- `project11-client-success/01_CLIENT_ONBOARDING_INTAKE_FORM.md` — client-success doc. **Safe to ignore unless explicitly needed.**
- `project11-client-success/02_KICKOFF_SOP.md` — client-success doc. **Safe to ignore unless explicitly needed.**
- `project11-client-success/03_DEPLOYMENT_CHECKLIST.md` — client-success doc. **Safe to ignore unless explicitly needed.**
- `project11-client-success/04_ROLLBACK_SOP.md` — client-success doc. **Safe to ignore unless explicitly needed.**
- `project11-client-success/05_QA_ACCEPTANCE_CHECKLIST.md` — client-success doc. **Safe to ignore unless explicitly needed.**
- `project11-client-success/06_TESTIMONIAL_CAPTURE_WORKFLOW.md` — client-success doc. **Safe to ignore unless explicitly needed.**
- `project11-client-success/07_14_DAY_UPSELL_TRIGGER_WORKFLOW.md` — client-success doc. **Safe to ignore unless explicitly needed.**
- `project11-client-success/08_RETENTION_EXPANSION_MONETIZATION/` — client-success folder. **Safe to ignore unless explicitly needed.**
- `project11-client-success/CLIENT_ONBOARDING_CHECKLIST.md` — client-success doc. **Safe to ignore unless explicitly needed.**
- `project11-client-success/DISCOVERY_CALL_QUESTIONNAIRE.md` — client-success doc. **Safe to ignore unless explicitly needed.**
- `project11-client-success/PROJECT_11_COMPLETE_AUDIT.md` — client-success audit doc. **Safe to ignore unless explicitly needed.**
- `project12-client-success/` — project 12 folder. **Safe to ignore unless explicitly needed.**
- `project13-internal-governor-dashboard/` — project 13 folder. **Safe to ignore unless explicitly needed.**
- `project14-growth-engine/` — project 14 folder. **Safe to ignore unless explicitly needed.**
- `project15-shared-scale-core/` — project 15 folder. **Safe to ignore unless explicitly needed.**

### Project 9 artifacts / scripts / state
- `project9-sales-agent/FOUNDER_LAUNCH_SIGNOFF_RUNBOOK.md` — project 9 runbook. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/OUTBOUND_CONTROL_CHAIN_WORKFLOW_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/OUTBOUND_DRY_RUN_GUARD_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/OUTBOUND_DRY_RUN_GUARD_WORKFLOW_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/OUTBOUND_FIRST_10_MONITOR_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/OUTBOUND_LAUNCH_AUTOMATION_PLAN.md` — project 9 plan. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/OUTBOUND_LAUNCH_CHECKLIST.md` — project 9 checklist. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/OUTBOUND_LAUNCH_STATE_TRANSITION_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/OUTBOUND_RESUME_GATE_SPEC.md` — project 9 spec. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/OUTREACH_SCRIPTS.md` — project 9 outreach doc. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/prompts/` — prompt assets. **Safe to ignore unless explicitly needed.**
- `project9-sales-agent/scripts/resend_delivery_sync.py` — project 9 script. **Unsafe to commit without inspection.**
- `project9-sales-agent/state/email_acquisition_audit.ndjson` — generated audit log. **Safe to ignore.**
- `project9-sales-agent/state/outbound_dedup_hash_log.ndjson` — generated audit log. **Safe to ignore.**
- `project9-sales-agent/state/outbound_first_10_send_events.ndjson` — generated audit log. **Safe to ignore.**
- `project9-sales-agent/state/suppression_list.ndjson` — generated audit log. **Safe to ignore.**

### Shared / v1-revenue-system / agent docs
- `shared-docs/` — shared docs tree. **Safe to ignore unless explicitly needed.**
- `v1-revenue-system/lead_revenue_pipeline.py` — live pipeline code. **Unsafe to bulk-commit without inspection.**
- `v1-revenue-system/proof_artifacts/` — proof artifacts. **Safe to ignore unless explicitly needed.**
- `v1-revenue-system/scripts/` — repo scripts. **Unsafe to bulk-commit without inspection.**
- `v1-revenue-system/state/` — generated state outputs. **Safe to ignore unless explicitly needed.**
- `v1-revenue-system/tests/` — test additions. **Safe to inspect and commit later if required.**

## Task 1 decision
- Commit scope is limited to `ops/codex-output.md` only.
- Nothing else in the untracked tree is safe to scoop into the Task 1 commit.

# Task 2 — Validate Confidence Fix Targets

## Hunter confidence references
- There are no remaining `confidence_score` references in `.github/workflows/scripts/email_acquisition.py`.
- Current Hunter-aware ranking now uses `confidence`:
  - `.github/workflows/scripts/email_acquisition.py:235-245`
  - `.github/workflows/scripts/email_acquisition.py:400-416`
  - `.github/workflows/scripts/email_acquisition.py:527-533`
  - `.github/workflows/scripts/email_acquisition.py:582-587`
  - `.github/workflows/scripts/email_acquisition.py:607-624`
- Current code:
  - `_candidate_strength()` reads `candidate.get("confidence", 0)`.
  - `_normalize_candidate()` stores `candidate["confidence"]`.
  - All six acquisition passes emit `confidence`, not `confidence_score`.

## Outscraper score references
- The only remaining `score` references in `.github/workflows/scripts/email_acquisition.py` are the canonical Sheets row fields, not ranking logic:
  - `.github/workflows/scripts/email_acquisition.py:31`
  - `.github/workflows/scripts/email_acquisition.py:148-151`
  - `.github/workflows/scripts/email_acquisition.py:172`
- Current code:
  - `build_canonical_sheet_row()` reads `record.get("score")` only to preserve the sheet row.
  - Acquisition ranking does not use `score` anywhere in `_candidate_strength()` or the email acquisition passes.

## Validation result
- Validation passed for the current worktree state: Hunter ranking now uses the real `confidence` field, and Outscraper acquisition logic does not depend on a confidence-score field.
- No code was changed for this validation step.
