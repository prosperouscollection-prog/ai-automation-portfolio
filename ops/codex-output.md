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

# lucid-blackwell Extraction Loop

## Task 1 — index.html Copy Extraction
**Commit:** `2480b03` — `extract: homepage copy improvements from lucid-blackwell`

Copy hunks extracted (marketing copy only):
- Hero h1: new headline
- Hero body paragraph: founder-led positioning
- Hero microcopy: moved below CTA buttons, new text
- Primary CTA: "See What I'd Build First →" → "Book Your Free 15-Minute Call"
- Secondary CTA: href `#start-here`, new label
- start-here section h2 + body + section-note: rewritten
- examples section: removed dedicated-pages section-note
- Restaurant/salon/real estate/retail CTAs: `#contact` → Calendly direct booking
- Demos section CTA: "Book Your Free AI Growth Audit" → "Book a Free Call"
- Removed proof-blocks section entirely
- Pricing h2 + p: rewritten
- About paragraph + outline button: "free founder audit" → "free founder call" framing

Not extracted: form field additions, live activity feed script fallback.

## Task 2 — sales_agent.py Prompt Copy Extraction
**Commit:** `59ab728` — `extract: H.O.O.K. copy and phrase hygiene from lucid-blackwell`

Copy hunks extracted (prompt/template only):
- `VARIANT_OPENERS` (5-item) → `HOOK_VARIANTS` (3-item per industry)
- `DEFAULT_OPENERS` (5) → `DEFAULT_HOOKS` (3)
- Added: `LEAK_VARIANTS`, `OUTCOME_VARIANTS`, `PROOF_VARIANTS`, `CTA_VARIANTS`, `EMAIL_SIGNATURE`
- Added: `SalesAgent._select_framework_variants()` — deterministic H.O.O.K. selector
- `_draft_email` prompt: replaced with full H.O.O.K. 5-part structure
  - Greeting rule: "Hi there," only, no personal names
  - Voice: first-person singular only, no "we/our/our team"
  - Hard sentence stop: 5 sentences max before signature
  - Scenario hook constraint: 2 sentences max for scene openings
  - Paragraph format: 2-3 sentences per paragraph, not text-thread style
  - Repetition control: vary entry points, not batch-templated
  - Placeholder ban: no `[Token]` placeholders
  - Phone ban: no phone numbers in body
  - Plain language lock: no "overflow inquiries", "qualified leads", etc.
  - CTA time lock: exactly "10 minutes"
  - Expanded banned phrases: + synergy, I couldn't help but notice, etc.
  - Banned trust-clichés: "without changing how you..."
  - Banned filler: "slips/falls through the cracks"
  - 19-point quality checklist
- max_tokens: 450 → 500
- pass_type: "first_pass" → "hook_v1:{label}"

Not extracted: `_enrich_email()` method, HubSpot field name change, any send/Resend/WORKFLOW_MODE changes.

## Task 3 — Doctrine Verification

Verification run after both extractions. All doctrine lines confirmed on main:

| Check | Status | Evidence |
|-------|--------|---------|
| `WORKFLOW_MODE = "QUEUED_NO_SEND_AUTONOMY"` | PASS | `sales_agent.py:64` |
| `CAP_LIMIT = 3` | PASS | `sales_agent.py:63` |
| `ApprovalFlow` import present | PASS | `sales_agent.py:44` |
| `ApprovalFlow` instantiated | PASS | `sales_agent.py:285` |
| QUEUE/SKIP semantics in approval_flow.py | PASS | `v1-revenue-system/approval_flow.py:55,87,190,226-230` |
| `outbound_dry_run_guard.yml` present | PASS | `.github/workflows/outbound_dry_run_guard.yml` |
| `outbound_first_10_monitor.yml` present | PASS | `.github/workflows/outbound_first_10_monitor.yml` |
| `outbound_launch_state_transition.yml` present | PASS | `.github/workflows/outbound_launch_state_transition.yml` |
| `outbound_resume_gate.yml` present | PASS | `.github/workflows/outbound_resume_gate.yml` |

**Doctrine: INTACT. All 9 checks passed.**
