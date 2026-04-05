# Codex Output
loop_cycle: lucid-blackwell-audit

## Task 3 — Doctrine Violation Report

### Direct locked-doctrine violations

- `.github/workflows/sales_agent.yml` — **REJECT**
  - Reintroduces live-send wiring and external delivery secrets.
  - Removes the no-send proof / digest upload path.
  - Violates: live send doctrine, Telegram gate evidence, no-send integrity.

- `.github/workflows/scripts/sales_agent.py` — **REJECT**
  - Rewrites the workflow into auto-send mode.
  - Removes `CAP_LIMIT`, `WORKFLOW_MODE`, `ApprovalFlow`, queue semantics, and founder review behavior.
  - Violates: live send doctrine, founder approval gate, Telegram command interface requirement, CAP_LIMIT removal, WORKFLOW_MODE removal, ApprovalFlow removal.

- `v1-revenue-system/approval_flow.py` — **REJECT**
  - Changes the approval keywords and prompt text from `QUEUE/SKIP` to `SEND/SKIP`.
  - Violates: founder approval gate and Telegram command interface requirement.

- `CLAUDE_CODE_START.md` — **REJECT**
  - Documents Sales Agent as auto-send with no approval gating.
  - Violates: live send doctrine and founder approval gate by instruction drift.

### Gate-enforcement removals tied to the same doctrine boundary

- `.github/workflows/outbound_dry_run_guard.yml` — **REJECT**
- `.github/workflows/outbound_first_10_monitor.yml` — **REJECT**
- `.github/workflows/outbound_launch_state_transition.yml` — **REJECT**
- `.github/workflows/outbound_resume_gate.yml` — **REJECT**
- `project9-sales-agent/scripts/outbound_dry_run_guard.py` — **REJECT**
- `project9-sales-agent/scripts/outbound_first_10_monitor.py` — **REJECT**
- `project9-sales-agent/scripts/outbound_launch_state_transition.py` — **REJECT**
- `project9-sales-agent/scripts/outbound_resume_gate.py` — **REJECT**
- `project9-sales-agent/state/outbound_launch_state.json` — **REJECT**

These deletions remove the dry-run / first-10 / transition / resume control plane that supports the locked launch doctrine. They are not merge-safe as-is.

# New Loop — Task Status

## Task 1 — Confirm Active Email Path
- **Result**: No-op. `acquire_owner_email()` is the active call at `lead_generator_agent.py:146`.
- No `enrich_email()` exists anywhere in `lead_generator_agent.py`.
- No code change required.

## Task 2 — Prove Passes 2-6 in CI

### Test file
`/Users/genesisai/portfolio/.github/workflows/scripts/test_acquisition_passes.py`

### How it works
- Runs `EmailAcquisitionEngine.acquire()` with a prospect that has no `owner_email`, `contact_email`, or `staff_email`.
- Asserts all 6 pass names appear in `passes_ran` (guaranteed by the engine: `passes_ran.append(pass_name)` fires before the pass method is called — `email_acquisition.py:328`).
- Asserts `pass_1` produced zero candidates (no structured email supplied).
- Exits with code 1 if any assertion fails.

### Local run result
```
=== EmailAcquisitionEngine passes 2-6 reachability test ===
PASS: all six passes present in passes_ran
PASS: pass_1 produced zero candidates (no structured email supplied)
PASS: passes 2-6 are reachable and were attempted

RESULT: PASS — 3/3 assertions passed
```

### CI integration
Added step "Assert acquisition engine passes 2-6 reachable" to `sales_agent.yml` immediately before the existing probe step. Runs `test_acquisition_passes.py` and fails CI if exit code is non-zero.

## Task 3 — Surface Email Provenance in Queue
- **Result**: No-op. `pass_metadata` already includes `email_confidence`, `email_source_type`, and `email_source_reference` at `sales_agent.py:1182-1188` (fixed in bb4d464).
- No code change required.

## Task 4 — Review lead_revenue_pipeline.py

### File
`v1-revenue-system/lead_revenue_pipeline.py` — 1224 lines

### Hardcoded identifiers found

| Line | Item | Risk |
|------|------|------|
| 53 | `DEFAULT_LIVE_GOOGLE_SHEET_ID = "1ORElwpEZN23jzPR9v_-Wu_qVG2g8xKGIkw_g41JoAPw"` | MEDIUM — production Sheet ID in source. Overridable via `--google-sheet-id` or `GOOGLE_SHEETS_SPREADSHEET_ID` env var. |
| 54–56 | `DEFAULT_LIVE_SERVICE_ACCOUNT_FILE = Path("/Users/genesisai/Downloads/n8n-integration-491503-9e7222cb0016.json")` | HIGH — absolute local path to a credentials file. Filename exposes GCP project number `491503` and a service account credential ID. This path will not resolve in CI. Overridable via `--google-service-account-file` or `GOOGLE_SERVICE_ACCOUNT_JSON` env var. |
| 815 | `"Trendell Fordham"` — founder name in draft template | LOW — business info, intentional |
| 816 | `"(313) 400-2575"` — founder phone in draft template | LOW — business info, intentional |
| 817–818 | `"info@genesisai.systems"`, `"genesisai.systems"` — contact info in draft template | LOW — business info, intentional |
| 819 | `"calendly.com/genesisai-info-ptmt/free-ai-demo-call"` — Calendly link in draft template | LOW — business info, intentional |
| 1117–1126 | `_default_sample_payload()` — Northline HVAC test payload with fake phone/email | LOW — sample/test data only, not production |

### Summary
- Two items warrant attention before committing to a shared repo: the hardcoded Sheet ID (line 53) and the local credentials path (lines 54-56).
- The credentials path `n8n-integration-491503-9e7222cb0016.json` exposes a GCP project identifier. Safe to commit if the path is understood as a local-only default that is always overridden in CI.
- All other hardcoded strings are business contact details or test fixtures — intentional and safe.
- **File NOT committed.** Pending founder review of the two flagged items.
