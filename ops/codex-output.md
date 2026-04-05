# Codex Output
loop_cycle: lucid-blackwell-extraction

## Task 1 — Safe Extraction Candidates

Only isolated copy/text hunks qualify here. Whole-file cherry-picks are not safe if they carry live-send or control-plane logic with them.

### Safe extraction candidates

- `index.html`
  - Homepage copy changes only:
    - hero headline / hero body rewrite
    - CTA wording changes
    - section intro / note wording changes
    - removed proof-block marketing section
  - Why safe: marketing copy only; no send architecture, approval flow, or control plane.

- `.github/workflows/scripts/sales_agent.py` — isolated draft-copy hunks only
  - Copy improvements only:
    - H.O.O.K. drafting framework text
    - phrase hygiene / plain-language guardrails
    - first-person voice lock
    - sentence-cap / anti-repetition wording
    - placeholder / greeting / phone-number bans in the prompt text
  - Why safe only as isolated hunks: these are prompt and template strings, but the branch tip file also contains auto-send and control-plane rewrites. Do not extract the file wholesale.

### Not safe as extraction candidates

- QA self-check additions: none in this branch tip.
  - The only QA change visible in lucid-blackwell is removal of `echo "checking: ..."` diagnostics from `.github/workflows/qa_agent.yml`.
  - That is not a safe extraction candidate because it removes visibility rather than adding self-checks.

## Task 2 — What Stays on the Branch

Everything below is entangled with send wiring, approval flow, WORKFLOW_MODE/CAP_LIMIT removal, ApprovalFlow changes, or control-plane deletions. These stay on `claude/lucid-blackwell` and should not be extracted.

- `.github/workflows/sales_agent.yml`
  - Live-send wiring restored
  - `RESEND_API_KEY`, `OUTSCRAPER_API_KEY`, `HUNTER_API_KEY`, `HUBSPOT_ACCESS_TOKEN`
  - `resend` install added
  - no-send proof / digest artifact steps removed

- `.github/workflows/scripts/sales_agent.py`
  - Auto-send rewrite
  - `CAP_LIMIT` removal
  - `WORKFLOW_MODE` removal
  - `ApprovalFlow` removal
  - founder review queue / Telegram approval loop removed
  - Resend delivery and tracking logic added

- `v1-revenue-system/approval_flow.py`
  - `QUEUE/SKIP` semantics changed to `SEND/SKIP`
  - Telegram command interface changed from queue approval to send approval

- `CLAUDE_CODE_START.md`
  - Auto-send documentation added
  - Approval gating described as removed
  - Resend tracking / reporting behavior documented

- Control-plane deletions that stay on branch
  - `.github/workflows/outbound_dry_run_guard.yml`
  - `.github/workflows/outbound_first_10_monitor.yml`
  - `.github/workflows/outbound_launch_state_transition.yml`
  - `.github/workflows/outbound_resume_gate.yml`
  - `project9-sales-agent/scripts/outbound_dry_run_guard.py`
  - `project9-sales-agent/scripts/outbound_first_10_monitor.py`
  - `project9-sales-agent/scripts/outbound_launch_state_transition.py`
  - `project9-sales-agent/scripts/outbound_resume_gate.py`
  - `project9-sales-agent/state/outbound_launch_state.json`
  - `ops/REVIEWER_ROLE.md`
  - `ops/agent_handoff.md`
  - `ops/codex-output.md`
  - `ops/send_imessage.sh`

These are all control-plane, governance, or release-gate removals. They are not safe extractions.
