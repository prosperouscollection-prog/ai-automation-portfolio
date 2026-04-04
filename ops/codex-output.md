```python
        try:
            for lead in leads:
                if summary["leads_touched"] >= CAP_LIMIT:
                    summary["cap_status"] = "AT_CAP"
                    print(f"ℹ️  Reached {CAP_LIMIT}-lead limit for this run")
                    break

                result = self._process_candidate(
                    lead,
                    summary=summary,
                    queue_index=queue_index,
                    lead_ids_this_run=lead_ids_this_run,
                )

                if result.get("halt_run"):
                    summary["log_write_status"] = result.get("log_write_status", summary["log_write_status"])
                    summary["fail_safe_usage_status"] = result.get(
                        "fail_safe_usage_status",
                        summary["fail_safe_usage_status"],
                    )
                    if result.get("anomaly_category"):
                        anomaly_categories.add(str(result["anomaly_category"]))
                    if result.get("selected"):
                        summary["leads_touched"] += 1
                        terminal_state = result["terminal_state"]
                        summary_key = {
                            "QUEUED_FOR_REVIEW": "total_queued",
                            "SKIPPED": "total_skipped",
                            "TIMEOUT_UNRESOLVED": "total_timeout_unresolved",
                            "ERROR_RETRY_LOGGED": "total_errors",
                        }.get(terminal_state)
                        if summary_key is not None:
                            summary[summary_key] += 1
                    if result.get("halt_reason") == "CAP_BREACH_BLOCKED":
                        summary["cap_status"] = "CAP_BREACH_BLOCKED"
                    break

                summary["log_write_status"] = result.get("log_write_status", summary["log_write_status"])
                summary["fail_safe_usage_status"] = result.get(
                    "fail_safe_usage_status",
                    summary["fail_safe_usage_status"],
                )
                if result.get("anomaly_category"):
                    anomaly_categories.add(str(result["anomaly_category"]))
                if result.get("selected"):
                    summary["leads_touched"] += 1
                    terminal_state = result["terminal_state"]
                    summary_key = {
                        "QUEUED_FOR_REVIEW": "total_queued",
                        "SKIPPED": "total_skipped",
                        "TIMEOUT_UNRESOLVED": "total_timeout_unresolved",
                        "ERROR_RETRY_LOGGED": "total_errors",
                    }.get(terminal_state)
                    if summary_key is not None:
                        summary[summary_key] += 1
                    if terminal_state == "QUEUED_FOR_REVIEW":
                        digest_entries.append(
                            self._build_digest_entry(
                                lead=lead,
                                result=result,
                                sequence=len(digest_entries) + 1,
                            )
                        )
                else:
                    if result.get("filter_summary_key"):
                        summary["total_leads_evaluated_for_this_run"] += 1
                    summary_key = result.get("filter_summary_key")
                    if summary_key is not None:
                        summary[summary_key] += 1

                if result.get("terminal_state") == "CAP_BREACH_BLOCKED":
                    summary["cap_status"] = "CAP_BREACH_BLOCKED"
                    break

        except RuntimeError as exc:
            summary["cap_status"] = "CAP_BREACH_BLOCKED" if "CAP_BREACH_BLOCKED" in str(exc) else summary["cap_status"]
            print(f"⛔ {exc}")
            telegram_notify(
                "Sales Agent halted",
                f"{exc}\nrun_id={self.run_id}",
                "CRITICAL",
            )
```
