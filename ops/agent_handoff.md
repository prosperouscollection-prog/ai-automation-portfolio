# Agent Handoff — Genesis AI Systems
repo: prosperouscollection-prog/ai-automation-portfolio
branch: main

## FOUNDER REQUIRED CHECKPOINT
status: NONE
reason: P17 review returned FAIL on checks 3 and 4 only. No doctrine violations.
  No authority boundary touched. Next patch is within milestone scope.
  Loop continues to Codex for patch implementation.

## LOOP STATE
current_milestone: P17 — Email Address Acquisition Hardening
current_run_id: —
artifact_refs:
  - outbound-first-10-send-events (run 23987234915)
  - founder-morning-digest (artifact 6273852812, run 23990078311)
loop_cycle: 5
open_risks:
  - p17_confidence_absent: Outscraper and Hunter confidence fields not extracted.
    First valid email wins unconditionally regardless of confidence score.
    enrich_email() in lead_generator_agent.py:546-603 and _enrich_email() in
    sales_agent.py:1690-1739 both need patch. See codex-output.md for exact patch.
  - p17_evidence_not_persisted: Enrichment source only in print() statements.
    Not written to queue metadata, outreach log, or Sheets. Founder cannot
    see email provenance for queued leads.
last_reviewer_action: CONTINUE
next_codex_task: |
  MILESTONE: P17 — Email Address Acquisition Hardening
  STATUS: FAIL — implement confidence extraction patch only. Do not change scope.

  FAILING CHECKS: 3 and 4.
  NO DOCTRINE VIOLATIONS.

  TASK:
  Patch these two functions to add confidence extraction and best-candidate selection:
    1. lead_generator_agent.py — enrich_email() (lines 546-603)
    2. sales_agent.py — _enrich_email() (lines 1690-1739)

  For each function:
  - Iterate ALL email candidates from Outscraper (not just the first)
  - Extract confidence: entry.get("score", 0) or entry.get("confidence", 0)
  - Track all valid (value, confidence, source) tuples
  - Also run Hunter if Outscraper confidence best candidate is below 50
  - Select the highest-confidence candidate across all passes
  - Log: "{domain}: {val} [confidence={score}, source={source}]"

  For sales_agent.py _enrich_email() only:
  - Return a tuple (email_value, confidence_score, source_label)
  - Update caller to store email_source and email_confidence on the Lead object
  - Pass those two fields into pass_metadata when writing the queue row

  CONSTRAINTS (do not touch):
  - No send logic changes
  - No queue authority changes
  - No cap changes
  - No new agents
  - No CRM or HoneyBook
  - No P15/P16 paths
  - Scraper remains separate

  After patching, write a brief summary to ops/codex-output.md confirming:
  - Which confidence field name Outscraper actually returns
  - Which confidence field name Hunter actually returns
  - That enrich_email() now selects best-confidence candidate
  - That _enrich_email() now returns a tuple with source+confidence
  - That pass_metadata is populated in queue rows
  Commit: "p17: confidence extraction + best-candidate selection"
  Push to main.

## RESOLVED RISKS
- digest_not_produced: RESOLVED (loop-4)
  run_id 23990078311, artifact_id 6273852812, VERIFIED
- qa_contactform_transient: RESOLVED (loop-4)
  id="contactForm" confirmed present. Prior failures were transient deploy state.

## LOCKED DOCTRINE REMINDERS
- live send: PAUSED
- founder approval: MANDATORY
- queue promotion: MANUAL ONLY
- 3-lead cap: UNCHANGED
- scheduled trigger: ONLY trigger
- no autonomous gate advancement
- Codex must not modify FOUNDER REQUIRED CHECKPOINT

## MILESTONE SCOREBOARD
CLOSED: P9, P15, P16
IN PROGRESS: P17 — FAIL, patch pending (confidence extraction)
QUEUED: HoneyBook Templates, Email Address Acquisition, Instagram Automation
BLOCKED: Live Send / RESUME AUTO, V2 Agents
BACKLOG: Apollo.io Upgrade, Sentence Cap Truncation, Instantly + Lindy Activation
