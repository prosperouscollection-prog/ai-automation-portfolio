WORKFLOW_DISPATCH REMOVAL
[state: REMOVED]
2bd0b57

RUN LOG EXCERPT
sales-pipeline	Run sales pipeline	2026-04-04T20:46:09.3991198Z 📨 Approval requested: 9196de96 (outreach → Shops On Top)
sales-pipeline	Run sales pipeline	2026-04-04T20:46:09.3992021Z   🔍 _wait_for_callback() started — timeout=600s message_id=545
sales-pipeline	Run sales pipeline	2026-04-04T20:46:09.3992693Z   🔍 poll loop tick — elapsed=0.0s
sales-pipeline	Run sales pipeline	2026-04-04T20:46:09.3993229Z   🔍 process_updates() — updates=1
sales-pipeline	Run sales pipeline	2026-04-04T20:46:09.3993860Z   🔍 cq_chat='***' vs chat='***' match=True
sales-pipeline	Run sales pipeline	2026-04-04T20:46:09.3994670Z   📋 Founder review queue: Shops On Top → QUEUED_FOR_REVIEW (run_id=20260404_164527)
sales-pipeline	Run sales pipeline	2026-04-04T20:46:09.3995475Z   📤 queue action complete: QUEUED_FOR_REVIEW
sales-pipeline	Run sales pipeline	2026-04-04T20:46:09.3996728Z   🔍 Telegram send_telegram() called — token=SET chat=SET

RUN SUMMARY
{
  "cap_status": "AT_CAP",
  "fail_safe_usage_status": "NOT_USED",
  "log_write_status": "WRITTEN",
  "no_send_integrity": "VERIFIED",
  "run_id": "20260404_164527",
  "summary_integrity": "VERIFIED",
  "total_candidates_seen": 34,
  "total_errors": 0,
  "total_filtered_out_chain": 1,
  "total_filtered_out_corporate": 0,
  "total_filtered_out_duplicate": 0,
  "total_filtered_out_incomplete": 3,
  "total_leads_evaluated_for_this_run": 7,
  "total_queued": 3,
  "total_skipped": 0,
  "total_timeout_unresolved": 0,
  "workflow_duration_seconds": 42.1
}
[state: GATE CLOSES]

QUEUE ROW
NOT PRESENT IN THIS RUN: The Detroit Shoppe did not appear in the completed run log or queue tab for run_id=20260404_164527.
