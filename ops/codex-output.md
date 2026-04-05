# Codex Output
loop_cycle: lucid-blackwell-audit

## Task 2 — Diff Against `main`

`git diff main..claude/lucid-blackwell --name-only` reports 26 differing paths.

### Merge-safe or low-risk changes

- `.github/workflows/qa_agent.yml`
  - Removed diagnostic `echo "checking: ..."` lines before `grep -q` checks.
  - Doctrine conflict: none.
  - Verdict: **MERGE SAFE**.

- `index.html`
  - Marketing/hero copy, CTA wording, and section layout changed.
  - Doctrine conflict: none with live send / approval / CAP / WORKFLOW_MODE / ApprovalFlow.
  - Verdict: **MERGE SAFE** from doctrine perspective.

### Changes that need modification before merge

- `.github/workflows/scripts/lead_generator_agent.py`
  - Removes the canonical email-acquisition helper import, the internal-record filter, and the shared `CHAIN_EXCLUSION_KEYWORDS` block.
  - Swaps away from the hardened `owner_email` acquisition pipeline and falls back to direct email handling.
  - Conflicts with canonical owner-email handling and the hardened lead-quality path.
  - Verdict: **NEEDS MODIFICATION**.

- `.github/workflows/scripts/email_acquisition.py`
  - Deleted the entire canonical acquisition engine.
  - This removes the multi-pass email recovery / classification layer that downstream scripts depend on.
  - Not a direct live-send violation, but it breaks the email-hardening architecture.
  - Verdict: **NEEDS MODIFICATION**.

- `shared_env.py`
  - Deleted the shared environment bootstrap/helper.
  - This is infrastructure churn, not a direct doctrine breach, but it is broad and likely to break multiple scripts if merged as-is.
  - Verdict: **NEEDS MODIFICATION**.

- `codex-output.md`
  - Deleted a repo-root audit artifact.
  - No locked-doctrine violation by itself, but it removes evidence/history and is not safe as a random deletion.
  - Verdict: **NEEDS MODIFICATION**.

### Changes that must be rejected

- `.github/workflows/sales_agent.yml`
  - Reintroduces live-send wiring: `OUTSCRAPER_API_KEY`, `HUNTER_API_KEY`, `RESEND_API_KEY`, and `HUBSPOT_ACCESS_TOKEN`.
  - Switches the job back to `resend` installation and removes the no-send digest / proof artifact steps.
  - Doctrine conflict: live send, Telegram gate, no-send integrity, gate evidence.
  - Verdict: **REJECT**.

- `.github/workflows/scripts/sales_agent.py`
  - Rewrites the workflow from queued no-send autonomy into auto-send mode.
  - Removes the approval flow, founder queue semantics, `CAP_LIMIT`, `WORKFLOW_MODE`, and the no-send / digest / queue protections.
  - Reintroduces Resend delivery and live outreach behavior.
  - Doctrine conflict: live send, founder approval gate, Telegram command interface, CAP_LIMIT removal, WORKFLOW_MODE removal, ApprovalFlow removal.
  - Verdict: **REJECT**.

- `v1-revenue-system/approval_flow.py`
  - Changes approval semantics from `QUEUE/SKIP` to `SEND/SKIP`.
  - Changes Telegram keywords and prompt language to send-outreach behavior.
  - Doctrine conflict: founder approval gate and Telegram command interface requirement.
  - Verdict: **REJECT**.

- `CLAUDE_CODE_START.md`
  - Updates the master build document to describe Sales Agent auto-send, removal of approval gating, and Resend tracking.
  - Doctrine conflict: it documents the same live-send / gate removal that the code changes implement.
  - Verdict: **REJECT**.

- `ops/REVIEWER_ROLE.md`
  - Deleted the reviewer protocol / checkpoint file.
  - This does not directly flip live-send code, but it removes the governance role the loop relies on.
  - Verdict: **REJECT**.

- `ops/agent_handoff.md`
  - Deleted the handoff file that carries the task list and loop state.
  - This removes the control-plane used to enforce the loop.
  - Verdict: **REJECT**.

- `ops/codex-output.md`
  - Deleted the ops output trail from the repo.
  - This is not a runtime doctrine violation, but it removes audit history and loop continuity.
  - Verdict: **REJECT**.

- `ops/send_imessage.sh`
  - Deleted the notification helper used by the loop protocol.
  - This is a governance/control-plane removal, not a safe cleanup.
  - Verdict: **REJECT**.

- `project9-sales-agent/scripts/outbound_dry_run_guard.py`
  - Deleted the dry-run gate verifier.
  - Doctrine conflict: gate enforcement and launch-state control.
  - Verdict: **REJECT**.

- `project9-sales-agent/scripts/outbound_first_10_monitor.py`
  - Deleted the first-10 outbound monitor / evidence collector.
  - Doctrine conflict: gate evidence and controlled launch monitoring.
  - Verdict: **REJECT**.

- `project9-sales-agent/scripts/outbound_launch_state_transition.py`
  - Deleted the controlled launch-state transition controller.
  - Doctrine conflict: launch-state governance and gate control.
  - Verdict: **REJECT**.

- `project9-sales-agent/scripts/outbound_resume_gate.py`
  - Deleted the founder-only resume gate.
  - Doctrine conflict: founder approval / gate control / resume authority.
  - Verdict: **REJECT**.

- `project9-sales-agent/state/outbound_launch_state.json`
  - Deleted the sample launch-state JSON used for dry-run validation.
  - Doctrine conflict: launch-state control path.
  - Verdict: **REJECT**.

- `v1-revenue-system/scripts/audit_genesis_env.py`
  - Deleted the environment audit script.
  - Not a direct live-send toggle, but it removes a preflight safety check.
  - Verdict: **REJECT**.

- `v1-revenue-system/scripts/run_founder_inbox_verification.py`
  - Deleted the founder inbox verification runner.
  - This removes a controlled proof path and widens the gap between docs and runtime.
  - Verdict: **REJECT**.

- `v1-revenue-system/scripts/run_v1_release_gate.py`
  - Deleted the V1 release-gate proof runner.
  - This is a control / validation path removal.
  - Verdict: **REJECT**.
