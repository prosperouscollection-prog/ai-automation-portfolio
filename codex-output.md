A. FILES CHANGED
- [/.github/workflows/scripts/sales_agent.py](/Users/genesisai/portfolio/.github/workflows/scripts/sales_agent.py)
- [/.github/workflows/sales_agent.yml](/Users/genesisai/portfolio/.github/workflows/sales_agent.yml)

B. EXACT DIGEST GENERATION LOGIC ADDED
- A post-run digest is now generated inside `sales_agent.py` at the end of every scheduled Sales Agent run.
- The digest file path is `project9-sales-agent/state/founder_morning_digest_[run_id].md`.
- The workflow now uploads that digest as a GitHub Actions artifact named `founder-morning-digest`.
- The digest is built only from existing run data:
  - current run summary
  - founder review queue entries returned during the run
  - existing terminal states
  - existing anomaly/failure signals
  - existing queue metadata such as priority, reason_selected, recommended_draft, run_id, and timestamps
- The digest is written in `sales_agent.py` by `_write_morning_digest(...)` and finalized from `run()` through `_finalize_run_outputs(...)`.
- The code prunes older `founder_morning_digest_*.md` files before writing the current run’s digest so the artifact step only captures the current run file.

C. EXACT DIGEST FORMAT
- Top Line
  - `run_id`
  - `workflow_duration_seconds`
  - `cap_status`
  - `total_queued`
  - `anomaly_count`
  - `fail_safe_usage_status`
  - `no_send_integrity`
  - `summary_integrity`
- Immediate Decisions
  - Queued leads only, ordered by priority metadata:
    - HIGH
    - MEDIUM
    - LOW
  - For each lead:
    - `business_name`
    - `priority`
    - `reason_selected`
    - `owner_email`
    - `recommended_draft_preview` limited to the first 1 to 2 lines
    - `lead_id` if available
    - `terminal_state`
- Filtered Summary
  - `total_filtered_out_chain`
  - `total_filtered_out_corporate`
  - `total_filtered_out_duplicate`
  - `total_filtered_out_incomplete`
- Anomalies
  - Only actual anomalies surfaced in the run are shown.
  - If none occurred, the digest prints `anomalies: none`.
- Human-Locked Reminders
  - `live send still paused`
  - `founder approval required for every queued lead`
  - `no gate changes occurred in this run`

D. HOW PRIORITY ORDERING IS PRESERVED WITHOUT CHANGING AUTHORITY
- The digest display sorts already-queued leads by existing priority metadata only for readability.
- That ordering is HIGH, then MEDIUM, then LOW.
- No queue states are changed.
- No lead is auto-approved, auto-skipped, auto-held, or auto-promoted.
- The workflow still treats founder approval as mandatory and manual only.
- The digest is a read-only formatter on top of the existing P15 run output.

E. HOW ANOMALIES ARE DETECTED AND COUNTED
- `anomaly_count` is computed from actual surfaced anomaly categories only.
- The implementation collects anomaly categories from:
  - run summary signals such as fail-safe usage, summary integrity mismatch, unresolved timeouts, total errors, and cap breach blocks
  - candidate-level anomaly markers such as queue corruption
  - callback ambiguity
  - log persistence failure
  - founder-stop blocked run
- Each anomaly category is counted once, even if it occurs more than once in the run.
- Normal suppression filtering is not counted as an anomaly.
- The digest never invents a failure signal that was not present in the run output.

F. EXACT LOCAL TEST STEPS
1. Syntax check the Python workflow:
```bash
python3 -m py_compile /Users/genesisai/portfolio/.github/workflows/scripts/sales_agent.py
```
2. Run a local digest smoke test from the workflow script directory:
```bash
cd /Users/genesisai/portfolio/.github/workflows/scripts && python3 - <<'PY'
from sales_agent import SalesAgent

agent = SalesAgent()
summary = {
    'run_id': '20260404_120000',
    'workflow_duration_seconds': 12.3,
    'cap_status': 'UNDER_CAP',
    'total_queued': 2,
    'fail_safe_usage_status': 'NOT_USED',
    'no_send_integrity': 'VERIFIED',
    'summary_integrity': 'VERIFIED',
    'total_filtered_out_chain': 1,
    'total_filtered_out_corporate': 0,
    'total_filtered_out_duplicate': 0,
    'total_filtered_out_incomplete': 1,
}
digest_entries = [
    {
        'sequence': 1,
        'business_name': 'Alpha Shop',
        'priority': 'HIGH',
        'reason_selected': 'passed suppression filters',
        'owner_email': 'alpha@example.com',
        'recommended_draft_preview': ['Subject: Quick question', 'Body: Hello'],
        'lead_id': 'lead-abc123',
        'terminal_state': 'QUEUED_FOR_REVIEW',
    },
    {
        'sequence': 2,
        'business_name': 'Beta Dental',
        'priority': 'MEDIUM',
        'reason_selected': 'passed suppression filters',
        'owner_email': 'beta@example.com',
        'recommended_draft_preview': ['Subject: Follow up', 'Body: Hi there'],
        'lead_id': 'lead-def456',
        'terminal_state': 'QUEUED_FOR_REVIEW',
    },
]
path = agent._write_morning_digest(summary, digest_entries, set())
print(path)
PY
```
- That smoke test confirmed the digest file is written and the printed metrics include the run ID, queued lead count, anomaly count, `no_send_integrity`, and `summary_integrity`.

G. EXACT GITHUB ACTIONS EVIDENCE TO VERIFY
- The workflow now shows an artifact step named `Upload Founder Morning Digest`.
- The artifact name is `founder-morning-digest`.
- The run output prints:
  - `✅ Founder morning digest written → ...`
  - `📦 Founder morning digest metrics: run_id=... queued_leads=... anomaly_count=... no_send_integrity=... summary_integrity=...`
- The digest artifact is produced without invoking any send path.
- The existing run summary remains intact and still reports the no-send and integrity fields.
- No queue states, cap logic, or approval authority are changed by the digest layer.

H. WHAT REMAINS HUMAN-LOCKED AFTER P16
- Live send is still paused.
- Founder approval remains mandatory for every queued lead.
- Queue promotion remains manual only.
- The 3-lead cap remains unchanged.
- Scheduled run remains the only trigger.
- No autonomous gate advancement is introduced.
- No new triggers, agents, or scraper behavior were added.
- The digest is only a read-only decision package layered on top of the existing P15 run output.
