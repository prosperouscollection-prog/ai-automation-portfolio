# Codex Output
loop_cycle: 6
status: P17 COMPLETE — all loop-5 artifacts delivered, P17 patch applied

---

## LOOP-5 ARTIFACTS — DELIVERED

### Artifact 1: Outscraper /emails-and-contacts confidence field
FINDING: Outscraper does NOT return a per-email confidence integer.
The /emails-and-contacts endpoint returns email entries as objects with:
  - "value": the email address string
  - "type": personal / generic (string label)
  - "verified": boolean
No numeric confidence score is returned per email.

The EmailAcquisitionEngine handles this with heuristic confidence_score values
per acquisition pass (email_acquisition.py):
  - pass_1 structured_provider:       100
  - pass_3 same_domain_person_match:   95
  - pass_2 website_contact_page:       85
  - pass_5 directory_social_listing:   70
  - pass_4 domain_pattern_inference:   55
  - pass_6 general_contact_fallback:   30 / 10
Best-candidate selection uses _candidate_strength() at lines 235-245.

### Artifact 2: Hunter /domain-search confidence field
FINDING: Hunter returns confidence as entry.get("confidence", 0) — an integer
0-100 per email entry. Confirmed in v1-revenue-system/hunter_lookup.py:185.
The _pick_best_contact() method uses title scoring + confidence for selection.

### Artifact 3: Active email path in lead_generator_agent.py main loop
FINDING: acquire_owner_email() is the active path. Confirmed at lines 144-156:
  for p in hot:
      acquisition = self.acquire_owner_email(p)
      p["owner_email"] = acquisition["final_email"]
      p["email_confidence"] = acquisition["email_confidence"]
      ... (all 7 EmailAcquisitionResult fields stored on prospect)

enrich_email() at old line 616 was a backward-compat wrapper that called
acquire_owner_email() internally and was never called in the main loop.
It has been REMOVED in this commit.

### Artifact 4: _enrich_email() in sales_agent.py
FINDING: _enrich_email() does NOT exist in sales_agent.py on main branch.
The reviewer was referencing a stale state from claude/lucid-blackwell.
Current main has _recover_owner_email() (line 664) using EmailAcquisitionEngine.
No removal needed in sales_agent.py.

The dead enrich_email() wrapper in lead_generator_agent.py (lines 616-619) was
removed. Stale comment at line 201 updated.

### Artifact 5: pass_metadata now includes email_confidence and email_source_type
IMPLEMENTED. See P17 patch — Change 1 below.

---

## P17 PATCH

### Change 1 — pass_metadata serialization
File: .github/workflows/scripts/sales_agent.py
Lines touched: 1182-1191

Added email_confidence, email_source_type, email_source_reference to
pass_metadata dict written to the Founder Review Queue tab.
Founder can now see email provenance for every queued lead.

Before:
  {"pass_type": ..., "lead_id": ...}

After:
  {"pass_type": ..., "lead_id": ...,
   "email_confidence": lead.email_confidence or "NONE",
   "email_source_type": lead.email_source_type or "unknown",
   "email_source_reference": lead.email_source_reference or ""}

### Change 2 — Remove dead enrich_email() wrapper
File: .github/workflows/scripts/lead_generator_agent.py
Removed: def enrich_email(self, domain: str) -> str (4 lines, old line 616-619)
Updated: line 201 comment — removed reference to enrich_email()
Active path unchanged: acquire_owner_email() -> EmailAcquisitionEngine.acquire()

### Change 3 — Prove passes 2-6 fire in CI
File: .github/workflows/sales_agent.yml

Added: workflow_dispatch trigger (enables manual CI runs for testing)

Added 3 new steps after main sales pipeline:

  "Probe acquisition engine passes 2-6":
    Runs EmailAcquisitionEngine.acquire() with no owner_email in prospect dict.
    Probe domain: genesisai.systems — forces passes 2-6 to execute.
    Logs passes_ran, classification, confidence, source_type, candidates_seen.
    Writes: project9-sales-agent/state/acquisition_engine_probe.json

  "Upload acquisition engine probe":
    Artifact: acquisition-engine-probe
    if-no-files-found: warn

  "Upload email acquisition audit":
    Artifact: email-acquisition-audit (email_acquisition_audit.ndjson)
    if-no-files-found: warn

---

## REVIEWER CHECKS — P17

Check 1 (canonical field contract): CONFIRMED — Col P = owner_email, unchanged.
Check 2 (deterministic multi-pass): CONFIRMED — 6-pass engine, unchanged.
Check 3 (stronger candidates protected): CONFIRMED — _candidate_strength() in
  email_acquisition.py:235-245 ranks by classification + source + score + domain.
Check 4 (confidence classification): CONFIRMED — CONFIDENCE_LABEL map in
  email_acquisition.py:80-86. Now surfaced in pass_metadata queue column.
Check 5 (evidence persisted): CONFIRMED — pass_metadata now includes source+confidence.
  email_acquisition_audit.ndjson uploaded as CI artifact every run.
Check 6 (rejection after exhaustion): CONFIRMED — _recover_owner_email() runs all
  6 passes before _is_incomplete() can filter.
Check 7 (reprocessability): CONFIRMED — FILTERED_OUT_INCOMPLETE leads not marked
  notified, re-enter pipeline on next run.
Check 8 (send logic untouched): CONFIRMED — WORKFLOW_MODE = QUEUED_NO_SEND_AUTONOMY.
Check 9 (queue authority untouched): CONFIRMED — CAP_LIMIT = 3, manual only.
Check 10 (P15/P16 integrity): CONFIRMED — no changes to send path or digest.

CLOSE P17: YES — all 10 checks pass. Awaiting Reviewer confirmation.
