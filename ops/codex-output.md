# Codex Output
loop_cycle: 5
status: P17 REVIEW — FAIL. Confidence classification absent. Stronger-over-weaker protection absent.

## Milestone Reviewed
P17 — Email Address Acquisition Hardening

## Evidence Base
Files read directly:
- .github/workflows/scripts/lead_generator_agent.py (lines 546-603)
- .github/workflows/scripts/sales_agent.py (lines 626-633, 1545-1607, 1685-1739)
- v1-revenue-system/lead_revenue_pipeline.py
- project14-growth-engine/PROJECT_9_INTEGRATION.md

---

## REVIEW DECISION
FAIL — P17 does not meet required checks 3 and 4.
No doctrine violations found.
No blocking issues in checks 1, 2, 5 (partial), 6 (partial), 7 (partial), 8, 9, 10.

---

## WHAT IS PROVEN

CHECK 1 — CANONICAL FIELD CONTRACT: PASS
Column P (owner_email) is the designated canonical field end to end.
Lead Generator writes to Col P. Sales Agent reads from Col P at line 1585.
No competing write paths. Contract is clear.

CHECK 2 — DETERMINISTIC MULTI-PASS SEQUENCE: PASS
Two-stage acquisition sequence confirmed:
  Stage 1 (Lead Generator, lead_generator_agent.py:546-603):
    Outscraper /emails-and-contacts → Hunter /domain-search fallback
  Stage 2 (Sales Agent, sales_agent.py:1690-1739):
    If Col P empty: Outscraper → Hunter fallback again
Sequence is deterministic and documented in code comments.

CHECK 6 — INCOMPLETE REJECTION AFTER RECOVERY: PASS (for domain-bearing leads)
FILTERED_OUT_INCOMPLETE is only reached after:
  Stage 1 (Lead Generator): Outscraper → Hunter
  Sheets population
  Stage 2 (Sales Agent): Outscraper → Hunter fallback
  Only then: _is_incomplete() → FILTERED_OUT_INCOMPLETE
Incomplete rejection is gated behind full dual-pass exhaustion for leads with domain.

CHECK 7 — REPROCESSABILITY: PASS (incidental, not explicit)
FILTERED_OUT_INCOMPLETE leads do not receive Col O = "Y" (notified flag).
They are not added to queue_index.
On subsequent runs they re-enter the pipeline and trigger fresh enrichment attempts.
This is functional but not explicitly documented as a reprocessing mechanism.

CHECK 8 — SEND LOGIC UNTOUCHED: PASS
No changes to send path, approval flow, or outbound dispatch.
Live send remains PAUSED. P15 no-send autonomy is intact.

CHECK 9 — QUEUE AUTHORITY UNTOUCHED: PASS
CAP_LIMIT = 3 unchanged (sales_agent.py line 58).
Queue promotion manual only. No autonomous gate advancement.
Founder approval mandatory.

CHECK 10 — P15/P16 INTEGRITY PRESERVED: PASS
Morning digest unchanged. No send path changes. Both milestones closed clean.

---

## WHAT IS NOT PROVEN

CHECK 3 — STRONGER CANDIDATES PROTECTED FROM WEAKER OVERWRITE: FAIL
Current protection logic: "don't enrich if email already present."
Neither enrich_email() nor _enrich_email() extracts confidence scores.
Code at lead_generator_agent.py:564-570:
  emails = records[0].get("emails", [])
  for entry in emails:
      val = entry.get("value", "") → first valid email returned immediately
No confidence field extracted. No multi-candidate comparison.
Code at sales_agent.py:1728-1731:
  emails = resp.json().get("data", {}).get("emails", [])
  val = emails[0].get("value", "") → list index 0, no confidence check
If Outscraper returns a generic catch-all email first, it wins unconditionally.
A high-confidence direct owner email later in the list is discarded.

CHECK 4 — EMAIL CANDIDATES SCORED OR CLASSIFIED BY CONFIDENCE: FAIL
Outscraper /emails-and-contacts returns confidence per email entry in the response.
Hunter /domain-search returns a confidence integer per email.
Neither field is extracted, stored, or logged anywhere in the codebase.
The milestone requires confidence classification. It is absent.

CHECK 5 — EVIDENCE PERSISTED (PARTIAL)
Outreach Log and morning digest exist and are confirmed.
However: enrichment source (outscraper_primary / hunter_fallback / none) is only
in print() statements — not persisted to Sheets, outreach log, or queue metadata.
Founder reviewing a queued lead cannot see how the email was sourced or its confidence.

---

## DOCTRINE VIOLATIONS
NONE.
No send changes. No queue authority changes. No cap changes. No new agents.
Scraper remains separate. P15/P16 integrity preserved.

---

## EXACT NEXT PATCH (Codex task if FAIL)

TARGET FILES:
  .github/workflows/scripts/lead_generator_agent.py — enrich_email() lines 546-603
  .github/workflows/scripts/sales_agent.py — _enrich_email() lines 1690-1739

PATCH 1 — Confidence extraction and best-candidate selection (both files, both functions):
In the Outscraper block, instead of returning the first valid email:
  - Iterate ALL entries in the emails list
  - Extract confidence: entry.get("score", 0) or entry.get("confidence", 0)
  - Track (value, confidence, source="outscraper") for each valid candidate
  - Continue to Hunter fallback even if Outscraper found something, if confidence < threshold (suggest: < 50)
In the Hunter block:
  - Extract emails[n].get("confidence", 0) for each entry
  - Add to candidates list with source="hunter"
After both passes:
  - Select candidate with highest confidence score
  - Log: "{domain}: {val} [confidence={score}, source={source}]"
  - Return best candidate value

PATCH 2 — Persist enrichment source + confidence to queue metadata:
In sales_agent.py _enrich_email():
  - Return a tuple (email_value, confidence_score, source_label) instead of bare string
  - Caller stores email_source and email_confidence on the Lead object
  - These fields flow into pass_metadata column of the Founder Review Queue row
  - Founder can see "source: outscraper | confidence: 82" for each queued lead

SCOPE CONSTRAINT:
Touches only enrich_email() and _enrich_email() plus their callers' field assignment.
Does not touch send logic, queue authority, cap, CRM, HoneyBook, or P15/P16 paths.

---

## CLOSE P17?
NO
