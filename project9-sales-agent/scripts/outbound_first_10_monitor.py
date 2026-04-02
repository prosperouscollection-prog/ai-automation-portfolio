#!/usr/bin/env python3
"""First-10 outbound monitoring controller for Project 9."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_STATE_FILE = REPO_ROOT / "state" / "outbound_launch_state.json"
DEFAULT_DRY_RUN_EVIDENCE = REPO_ROOT / "state" / "outbound_dry_run_guard_evidence.json"
DEFAULT_RESUME_EVIDENCE = REPO_ROOT / "state" / "outbound_resume_gate_evidence.json"
DEFAULT_TRANSITION_EVIDENCE = (
    REPO_ROOT / "state" / "outbound_launch_state_transition_evidence.json"
)
DEFAULT_EVENTS_FILE = REPO_ROOT / "state" / "outbound_first_10_send_events.ndjson"
DEFAULT_OUTPUT_FILE = REPO_ROOT / "state" / "outbound_first_10_monitor_evidence.json"
DEFAULT_PAUSE_RECORD = REPO_ROOT / "state" / "outbound_first_10_monitor_pause.json"
HOOK_NAME = "outbound_first_10_monitor"
ALERT_CHANNEL_PLACEHOLDER = "Telegram"
REPLAY_WINDOW = timedelta(hours=6)
ALLOWED_WINDOW_STATE = "LIVE_ALLOWED"
ALLOWED_WINDOW_STATUS = "READY"
REQUIRED_STATE_FIELDS = (
    "launch_mode",
    "launch_status",
    "verified_by",
    "verified_at",
    "correlation_id",
    "source",
    "notes",
)
SEND_EVENT_FIELDS = (
    "hook_name",
    "verification_result",
    "launch_correlation_id",
    "campaign_id",
    "window_name",
    "attempt_number",
    "send_number",
    "recipient_hash",
    "message_hash",
    "provider_message_id",
    "provider_accepted",
    "delivery_status",
    "bounce_count",
    "complaint_count",
    "wrong_recipient_count",
    "wrong_copy_count",
    "authentication_failure_count",
    "threshold_breached",
    "failure_reason",
    "next_action",
    "checked_at",
    "checked_by",
    "source_of_truth_path",
)
FAILURE_STATUSES = {
    "delivery_failed",
    "failed",
    "bounced",
    "complaint",
    "spam",
    "spam_complaint",
    "wrong_recipient",
    "wrong_copy",
    "authentication_failed",
    "auth_failed",
}


@dataclass(frozen=True)
class MonitorResult:
    monitor_result: str
    verification_result: str
    recommendation: str
    failure_reason: str | None
    threshold_breached: bool
    observed_provider_accepted_count: int
    hard_bounce_count: int
    complaint_count: int
    wrong_recipient_count: int
    wrong_copy_count: int
    authentication_failure_count: int
    consecutive_delivery_failures: int
    last_safe_send_number: int
    current_window_complete: bool
    launch_mode_before: str | None
    launch_status_before: str | None
    launch_mode_after: str | None
    launch_status_after: str | None
    next_action: str
    campaign_id: str | None
    launch_correlation_id: str | None
    send_records: list[dict[str, Any]]
    safe_state_snapshot: dict[str, Any] | None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _normalize(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    value = str(value).strip()
    return value or None


def _load_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"file unreadable: {exc.strerror or exc.__class__.__name__}"

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"file malformed: {exc.msg}"

    if not isinstance(payload, dict):
        return None, "file malformed: root JSON value must be an object"

    return payload, None


def _parse_iso_timestamp(value: Any) -> datetime | None:
    normalized = _normalize(value)
    if normalized is None:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_fresh(timestamp: datetime | None, max_age: timedelta = REPLAY_WINDOW) -> bool:
    if timestamp is None:
        return False
    now = _utc_now()
    if timestamp > now + timedelta(minutes=5):
        return False
    return now - timestamp <= max_age


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
        temp_path = Path(handle.name)

    try:
        os.replace(temp_path, path)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
        temp_path = Path(handle.name)

    try:
        os.replace(temp_path, path)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_records(path: Path, inline_json: str | None) -> list[dict[str, Any]]:
    if inline_json:
        payload = json.loads(inline_json)
    else:
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            return []
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            records: list[dict[str, Any]] = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if isinstance(item, dict):
                    records.append(item)
            return records

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        maybe_records = payload.get("records") or payload.get("events")
        if isinstance(maybe_records, list):
            return [item for item in maybe_records if isinstance(item, dict)]
        return [payload]
    raise ValueError("monitor events malformed: root JSON value must be an object or array")


def _validate_state(state: dict[str, Any]) -> tuple[str, str, str]:
    missing = [field for field in REQUIRED_STATE_FIELDS if _normalize(state.get(field)) is None]
    if missing:
        raise ValueError(f"incomplete launch state: missing fields {', '.join(missing)}")

    launch_mode = _normalize(state.get("launch_mode"))
    launch_status = _normalize(state.get("launch_status"))
    correlation_id = _normalize(state.get("correlation_id"))

    if launch_mode != ALLOWED_WINDOW_STATE:
        raise ValueError(f"monitor window not active: launch_mode must be {ALLOWED_WINDOW_STATE}, found {launch_mode}")
    if launch_status != ALLOWED_WINDOW_STATUS:
        raise ValueError(f"monitor window not ready: launch_status must be {ALLOWED_WINDOW_STATUS}, found {launch_status}")
    if correlation_id is None:
        raise ValueError("missing launch correlation id")

    return launch_mode, launch_status, correlation_id


def _validate_evidence(
    *,
    evidence_path: Path,
    expected_hook_name: str,
    result_field: str,
    expected_result_value: str,
    current_correlation_id: str,
    expected_next_action: str,
) -> dict[str, Any]:
    payload, load_error = _load_json_file(evidence_path)
    if load_error is not None:
        raise ValueError(f"{expected_hook_name} evidence {load_error}")

    hook_name = _normalize(payload.get("hook_name"))
    if hook_name != expected_hook_name:
        raise ValueError(f"{expected_hook_name} evidence has unexpected hook_name: {hook_name}")

    result_value = _normalize(payload.get(result_field))
    if result_value != expected_result_value:
        raise ValueError(
            f"{expected_hook_name} evidence {result_field} must be {expected_result_value}, found {result_value}"
        )

    evidence_correlation_id = _normalize(payload.get("correlation_id"))
    if evidence_correlation_id != current_correlation_id:
        raise ValueError(
            f"{expected_hook_name} evidence correlation mismatch: expected {current_correlation_id}, found {evidence_correlation_id}"
        )

    checked_at = _parse_iso_timestamp(payload.get("checked_at"))
    if not _is_fresh(checked_at):
        raise ValueError(f"{expected_hook_name} evidence is stale or missing checked_at")

    next_action = _normalize(payload.get("next_action"))
    if next_action != expected_next_action:
        raise ValueError(
            f"{expected_hook_name} evidence next_action must be {expected_next_action}, found {next_action}"
        )

    return payload


def _validate_transition_evidence(
    *,
    evidence_path: Path,
    current_correlation_id: str,
) -> dict[str, Any]:
    payload, load_error = _load_json_file(evidence_path)
    if load_error is not None:
        raise ValueError(f"outbound_launch_state_transition evidence {load_error}")

    hook_name = _normalize(payload.get("hook_name"))
    if hook_name != "outbound_launch_state_transition":
        raise ValueError(f"transition evidence has unexpected hook_name: {hook_name}")

    transition_result = _normalize(payload.get("transition_result"))
    if transition_result != "PASS":
        raise ValueError(f"transition evidence transition_result must be PASS, found {transition_result}")

    evidence_correlation_id = _normalize(payload.get("correlation_id"))
    if evidence_correlation_id != current_correlation_id:
        raise ValueError(
            f"transition evidence correlation mismatch: expected {current_correlation_id}, found {evidence_correlation_id}"
        )

    checked_at = _parse_iso_timestamp(payload.get("checked_at"))
    if not _is_fresh(checked_at):
        raise ValueError("transition evidence is stale or missing checked_at")

    target_state = _normalize(payload.get("target_state_requested"))
    if target_state != "LIVE_ALLOWED":
        raise ValueError(f"transition evidence target_state_requested must be LIVE_ALLOWED, found {target_state}")

    launch_mode_after = _normalize(payload.get("launch_mode_after"))
    if launch_mode_after != "LIVE_ALLOWED":
        raise ValueError(
            f"transition evidence launch_mode_after must be LIVE_ALLOWED, found {launch_mode_after}"
        )

    provisional = payload.get("provisional_live_allowed_window")
    if provisional is not True:
        raise ValueError("transition evidence must mark provisional_live_allowed_window true")

    next_action = _normalize(payload.get("next_action"))
    if next_action != "observe_first_10_sends":
        raise ValueError(
            f"transition evidence next_action must be observe_first_10_sends, found {next_action}"
        )

    return payload


def _required_event_fields_missing(payload: dict[str, Any]) -> list[str]:
    return [field for field in SEND_EVENT_FIELDS if field not in payload]


def _to_int(value: Any, field_name: str) -> int:
    normalized = _normalize(value)
    if normalized is None:
        raise ValueError(f"monitor event missing numeric field: {field_name}")
    try:
        return int(normalized)
    except ValueError as exc:
        raise ValueError(f"monitor event invalid numeric field {field_name}: {normalized}") from exc


def _evaluate_events(
    *,
    records: list[dict[str, Any]],
    expected_correlation_id: str,
) -> MonitorResult:
    accepted_count = 0
    hard_bounces = 0
    complaints = 0
    wrong_recipient = 0
    wrong_copy = 0
    auth_failures = 0
    consecutive_delivery_failures = 0
    last_safe_send_number = 0
    send_records: list[dict[str, Any]] = []
    seen_provider_message_ids: set[str] = set()
    seen_event_fingerprints: set[str] = set()
    failure_reason: str | None = None
    threshold_breached = False

    for record in records:
        missing = _required_event_fields_missing(record)
        if missing:
            raise ValueError(f"monitor event incomplete: missing fields {', '.join(missing)}")

        hook_name = _normalize(record.get("hook_name"))
        if hook_name != "outbound_first_10_send_event":
            raise ValueError(f"monitor event has unexpected hook_name: {hook_name}")

        event_correlation_id = _normalize(record.get("launch_correlation_id"))
        if event_correlation_id != expected_correlation_id:
            raise ValueError(
                f"monitor event correlation mismatch: expected {expected_correlation_id}, found {event_correlation_id}"
            )

        checked_at = _parse_iso_timestamp(record.get("checked_at"))
        if not _is_fresh(checked_at):
            raise ValueError("monitor event is stale or missing checked_at")

        provider_accepted = record.get("provider_accepted")
        if not isinstance(provider_accepted, bool):
            raise ValueError("monitor event provider_accepted must be a boolean")

        delivery_status = _normalize(record.get("delivery_status"))
        if delivery_status not in FAILURE_STATUSES and delivery_status != "accepted":
            raise ValueError(f"monitor event has unsupported delivery_status: {delivery_status}")

        provider_message_id = _normalize(record.get("provider_message_id"))
        if provider_message_id and provider_message_id in seen_provider_message_ids:
            raise ValueError(f"replay detected: provider_message_id already consumed ({provider_message_id})")
        if provider_message_id:
            seen_provider_message_ids.add(provider_message_id)

        event_fingerprint = _hash_text(
            "|".join(
                [
                    event_correlation_id or "",
                    str(record.get("attempt_number", "")),
                    str(record.get("send_number", "")),
                    _normalize(record.get("recipient_hash")) or "",
                    _normalize(record.get("message_hash")) or "",
                    provider_message_id or "",
                ]
            )
        )
        if event_fingerprint in seen_event_fingerprints:
            raise ValueError("replay detected: duplicate monitoring evidence consumed")
        seen_event_fingerprints.add(event_fingerprint)

        bounce_count = _to_int(record.get("bounce_count"), "bounce_count")
        complaint_count = _to_int(record.get("complaint_count"), "complaint_count")
        wrong_recipient_count = _to_int(record.get("wrong_recipient_count"), "wrong_recipient_count")
        wrong_copy_count = _to_int(record.get("wrong_copy_count"), "wrong_copy_count")
        auth_failure_count = _to_int(record.get("authentication_failure_count"), "authentication_failure_count")

        hard_bounces += max(0, bounce_count)
        complaints += max(0, complaint_count)
        wrong_recipient += max(0, wrong_recipient_count)
        wrong_copy += max(0, wrong_copy_count)
        auth_failures += max(0, auth_failure_count)

        if provider_accepted:
            accepted_count += 1

        if delivery_status == "accepted":
            consecutive_delivery_failures = 0
        else:
            consecutive_delivery_failures += 1

        send_records.append(
            {
                "attempt_number": _to_int(record.get("attempt_number"), "attempt_number"),
                "send_number": _to_int(record.get("send_number"), "send_number")
                if _normalize(record.get("send_number")) is not None
                else None,
                "provider_accepted": provider_accepted,
                "delivery_status": delivery_status,
                "provider_message_id": provider_message_id,
                "bounce_count": bounce_count,
                "complaint_count": complaint_count,
                "wrong_recipient_count": wrong_recipient_count,
                "wrong_copy_count": wrong_copy_count,
                "authentication_failure_count": auth_failure_count,
                "threshold_breached": bool(record.get("threshold_breached")),
                "failure_reason": _normalize(record.get("failure_reason")),
                "recipient_hash": _normalize(record.get("recipient_hash")),
                "message_hash": _normalize(record.get("message_hash")),
                "checked_at": _normalize(record.get("checked_at")),
            }
        )

        if complaints >= 1:
            failure_reason = "complaint or spam signal detected"
            threshold_breached = True
            break
        if wrong_recipient >= 1:
            failure_reason = "wrong recipient detected"
            threshold_breached = True
            break
        if wrong_copy >= 1:
            failure_reason = "wrong copy detected"
            threshold_breached = True
            break
        if auth_failures >= 1:
            failure_reason = "delivery/authentication failure detected"
            threshold_breached = True
            break
        if consecutive_delivery_failures >= 2:
            failure_reason = "two consecutive provider delivery failures"
            threshold_breached = True
            break
        if accepted_count <= 10:
            bounce_rate = hard_bounces / accepted_count if accepted_count else 0.0
            if hard_bounces >= 2:
                failure_reason = "hard bounce threshold reached"
                threshold_breached = True
                break
            if accepted_count > 0 and bounce_rate >= 0.05:
                failure_reason = "bounce rate threshold reached"
                threshold_breached = True
                break
        if provider_accepted and not threshold_breached:
            last_safe_send_number = accepted_count

        if accepted_count >= 10:
            break

    current_window_complete = accepted_count >= 10
    recommendation = "force_paused" if threshold_breached else "keep_allowed"
    monitor_result = "FAIL" if threshold_breached else "PASS"
    verification_result = monitor_result
    next_action = recommendation

    return MonitorResult(
        monitor_result=monitor_result,
        verification_result=verification_result,
        recommendation=recommendation,
        failure_reason=failure_reason,
        threshold_breached=threshold_breached,
        observed_provider_accepted_count=accepted_count,
        hard_bounce_count=hard_bounces,
        complaint_count=complaints,
        wrong_recipient_count=wrong_recipient,
        wrong_copy_count=wrong_copy,
        authentication_failure_count=auth_failures,
        consecutive_delivery_failures=consecutive_delivery_failures,
        last_safe_send_number=last_safe_send_number,
        current_window_complete=current_window_complete,
        launch_mode_before=None,
        launch_status_before=None,
        launch_mode_after=None,
        launch_status_after=None,
        next_action=next_action,
        campaign_id=None,
        launch_correlation_id=None,
        send_records=send_records,
        safe_state_snapshot=None,
    )


def _build_evidence(
    *,
    result: MonitorResult,
    launch_state: dict[str, Any],
    correlation_id: str,
    checked_by: str,
    state_file_path: Path,
    dry_run_evidence_path: Path,
    resume_evidence_path: Path,
    transition_evidence_path: Path,
    events_file_path: Path,
    campaign_id: str | None,
) -> dict[str, Any]:
    launch_mode_before = _normalize(launch_state.get("launch_mode"))
    launch_status_before = _normalize(launch_state.get("launch_status"))
    launch_mode_after = launch_mode_before if not result.threshold_breached else "PAUSED"
    launch_status_after = launch_status_before if not result.threshold_breached else "PAUSED"
    safe_snapshot = {
        "launch_mode": launch_mode_before,
        "launch_status": launch_status_before,
        "verified_by": _normalize(launch_state.get("verified_by")),
        "verified_at": _normalize(launch_state.get("verified_at")),
        "correlation_id": _normalize(launch_state.get("correlation_id")),
        "source": _normalize(launch_state.get("source")),
        "notes": _normalize(launch_state.get("notes")),
    }
    return {
        "hook_name": HOOK_NAME,
        "monitor_result": result.monitor_result,
        "verification_result": result.verification_result,
        "launch_correlation_id": correlation_id,
        "campaign_id": campaign_id or correlation_id,
        "window_name": "first_10",
        "send_number": result.last_safe_send_number,
        "recipient_hash": result.send_records[-1]["recipient_hash"] if result.send_records else None,
        "message_hash": result.send_records[-1]["message_hash"] if result.send_records else None,
        "provider_message_id": result.send_records[-1]["provider_message_id"] if result.send_records else None,
        "delivery_status": result.send_records[-1]["delivery_status"] if result.send_records else "no_events",
        "bounce_count": result.hard_bounce_count,
        "complaint_count": result.complaint_count,
        "wrong_recipient_count": result.wrong_recipient_count,
        "wrong_copy_count": result.wrong_copy_count,
        "authentication_failure_count": result.authentication_failure_count,
        "threshold_breached": result.threshold_breached,
        "failure_reason": result.failure_reason,
        "next_action": result.next_action,
        "checked_at": _utc_now_iso(),
        "checked_by": checked_by,
        "source_of_truth_path": str(state_file_path),
        "state_file_path": str(state_file_path),
        "dry_run_guard_evidence": str(dry_run_evidence_path),
        "resume_gate_evidence": str(resume_evidence_path),
        "transition_evidence": str(transition_evidence_path),
        "events_file_path": str(events_file_path),
        "observed_provider_accepted_count": result.observed_provider_accepted_count,
        "current_window_complete": result.current_window_complete,
        "last_safe_send_number": result.last_safe_send_number,
        "launch_mode_before": launch_mode_before,
        "launch_status_before": launch_status_before,
        "launch_mode_after": launch_mode_after,
        "launch_status_after": launch_status_after,
        "recommendation": result.recommendation,
        "safe_state_snapshot": safe_snapshot,
        "send_records": result.send_records,
        "alert_channel_placeholder": ALERT_CHANNEL_PLACEHOLDER if result.monitor_result == "FAIL" else None,
    }


def _pause_launch_state(
    *,
    state_file_path: Path,
    launch_state: dict[str, Any],
    correlation_id: str,
    checked_by: str,
    failure_reason: str,
    last_safe_send_number: int,
) -> dict[str, Any]:
    updated_state = {
        "launch_mode": "PAUSED",
        "launch_status": "PAUSED",
        "verified_by": checked_by,
        "verified_at": _utc_now_iso(),
        "correlation_id": correlation_id,
        "source": str(state_file_path),
        "notes": (
            f"Paused by first-10 monitor after send {last_safe_send_number}. "
            f"Reason: {failure_reason}"
        ),
        "pause_reason": failure_reason,
        "last_safe_send_number": last_safe_send_number,
    }
    _atomic_write_json(state_file_path, updated_state)
    return updated_state


def _emit_summary(result: MonitorResult, evidence_path: Path) -> None:
    if result.monitor_result == "PASS":
        print(
            f"[PASS] First-10 monitor recommends keep_allowed: {result.observed_provider_accepted_count} accepted send(s) observed"
        )
        print(f"Evidence written to: {evidence_path}")
    else:
        print(f"[FAIL] First-10 monitor forced pause: {result.failure_reason}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor the first 10 outbound sends.")
    parser.add_argument(
        "--state-file",
        default=os.environ.get("OUTBOUND_LAUNCH_STATE_PATH", str(DEFAULT_STATE_FILE)),
        help="Path to the current launch-state JSON.",
    )
    parser.add_argument(
        "--dry-run-evidence",
        default=os.environ.get("OUTBOUND_DRY_RUN_EVIDENCE_PATH", str(DEFAULT_DRY_RUN_EVIDENCE)),
        help="Path to dry-run guard evidence.",
    )
    parser.add_argument(
        "--resume-evidence",
        default=os.environ.get("OUTBOUND_RESUME_GUARD_EVIDENCE_PATH", str(DEFAULT_RESUME_EVIDENCE)),
        help="Path to resume gate evidence.",
    )
    parser.add_argument(
        "--transition-evidence",
        default=os.environ.get(
            "OUTBOUND_TRANSITION_EVIDENCE_PATH", str(DEFAULT_TRANSITION_EVIDENCE)
        ),
        help="Path to the launch-state transition evidence.",
    )
    parser.add_argument(
        "--events-file",
        default=os.environ.get("OUTBOUND_FIRST_10_EVENT_FEED_PATH", str(DEFAULT_EVENTS_FILE)),
        help="Path to the first-10 send event feed.",
    )
    parser.add_argument(
        "--events-json",
        default=os.environ.get("OUTBOUND_FIRST_10_EVENTS_JSON"),
        help="Inline JSON array/object of first-10 send events.",
    )
    parser.add_argument(
        "--campaign-id",
        default=os.environ.get("OUTBOUND_CAMPAIGN_ID"),
        help="Approved campaign or batch id.",
    )
    parser.add_argument(
        "--correlation-id",
        default=os.environ.get("OUTBOUND_CORRELATION_ID"),
        help="Launch correlation id.",
    )
    parser.add_argument(
        "--checked-by",
        default=os.environ.get("OUTBOUND_GUARD_ACTOR", "python"),
        help="Actor label for the monitor run.",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("OUTBOUND_OUTPUT_FILE", str(DEFAULT_OUTPUT_FILE)),
        help="Optional path to write the monitoring evidence JSON.",
    )
    parser.add_argument(
        "--pause-record",
        default=os.environ.get("OUTBOUND_PAUSE_RECORD_PATH", str(DEFAULT_PAUSE_RECORD)),
        help="Path for the pause record JSON written when thresholds trip.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state_path = Path(args.state_file)
    dry_run_evidence_path = Path(args.dry_run_evidence)
    resume_evidence_path = Path(args.resume_evidence)
    transition_evidence_path = Path(args.transition_evidence)
    events_file_path = Path(args.events_file)
    pause_record_path = Path(args.pause_record)
    output_path = Path(args.output) if args.output else None
    checked_by = _normalize(args.checked_by) or "python"
    correlation_id = _normalize(args.correlation_id)
    campaign_id = _normalize(args.campaign_id)

    try:
        launch_state, load_error = _load_json_file(state_path)
        if load_error is not None:
            raise ValueError(f"current launch state {load_error}")

        launch_mode_before, launch_status_before, state_correlation_id = _validate_state(launch_state)
        correlation_id = correlation_id or state_correlation_id
        if correlation_id is None:
            raise ValueError("missing launch correlation id")

        if _normalize(launch_state.get("correlation_id")) != correlation_id:
            raise ValueError(
                f"launch state correlation mismatch: expected {correlation_id}, found {_normalize(launch_state.get('correlation_id'))}"
            )

        _validate_evidence(
            evidence_path=dry_run_evidence_path,
            expected_hook_name="outbound_dry_run_guard",
            result_field="verification_result",
            expected_result_value="PASS",
            current_correlation_id=correlation_id,
            expected_next_action="proceed_to_resume_gate",
        )
        _validate_evidence(
            evidence_path=resume_evidence_path,
            expected_hook_name="outbound_resume_gate",
            result_field="authorization_result",
            expected_result_value="PASS",
            current_correlation_id=correlation_id,
            expected_next_action="advance_to_later_launch_steps",
        )
        transition_evidence = _validate_transition_evidence(
            evidence_path=transition_evidence_path,
            current_correlation_id=correlation_id,
        )
        campaign_id = campaign_id or _normalize(transition_evidence.get("campaign_id"))

        records = _read_records(events_file_path, args.events_json)
        result = _evaluate_events(records=records, expected_correlation_id=correlation_id)
        object.__setattr__(result, "launch_mode_before", launch_mode_before)
        object.__setattr__(result, "launch_status_before", launch_status_before)
        object.__setattr__(result, "launch_mode_after", launch_mode_before)
        object.__setattr__(result, "launch_status_after", launch_status_before)
        object.__setattr__(result, "campaign_id", campaign_id or correlation_id)
        object.__setattr__(result, "launch_correlation_id", correlation_id)
        object.__setattr__(
            result,
            "safe_state_snapshot",
            {
                "launch_mode": launch_mode_before,
                "launch_status": launch_status_before,
                "verified_by": _normalize(launch_state.get("verified_by")),
                "verified_at": _normalize(launch_state.get("verified_at")),
                "correlation_id": _normalize(launch_state.get("correlation_id")),
                "source": _normalize(launch_state.get("source")),
                "notes": _normalize(launch_state.get("notes")),
            },
        )

        if result.threshold_breached:
            paused_state = _pause_launch_state(
                state_file_path=state_path,
                launch_state=launch_state,
                correlation_id=correlation_id,
                checked_by=checked_by,
                failure_reason=result.failure_reason or "first-10 threshold breached",
                last_safe_send_number=result.last_safe_send_number,
            )
            object.__setattr__(result, "launch_mode_after", _normalize(paused_state.get("launch_mode")))
            object.__setattr__(result, "launch_status_after", _normalize(paused_state.get("launch_status")))

        evidence = _build_evidence(
            result=result,
            launch_state=launch_state,
            correlation_id=correlation_id,
            checked_by=checked_by,
            state_file_path=state_path,
            dry_run_evidence_path=dry_run_evidence_path,
            resume_evidence_path=resume_evidence_path,
            transition_evidence_path=transition_evidence_path,
            events_file_path=events_file_path,
            campaign_id=campaign_id,
        )

        if output_path is not None:
            _atomic_write_json(output_path, evidence)
        _atomic_write_json(Path(pause_record_path), evidence)

        print(json.dumps(evidence, indent=2, sort_keys=True))
        _emit_summary(result, output_path or Path(pause_record_path))
        return 0 if result.monitor_result == "PASS" else 1

    except ValueError as exc:
        failure_reason = str(exc)
        evidence = {
            "hook_name": HOOK_NAME,
            "monitor_result": "FAIL",
            "verification_result": "FAIL",
            "launch_correlation_id": correlation_id or "unknown",
            "campaign_id": campaign_id or correlation_id or "unknown",
            "window_name": "first_10",
            "send_number": 0,
            "recipient_hash": None,
            "message_hash": None,
            "provider_message_id": None,
            "delivery_status": "invalid",
            "bounce_count": 0,
            "complaint_count": 0,
            "wrong_recipient_count": 0,
            "wrong_copy_count": 0,
            "authentication_failure_count": 0,
            "threshold_breached": True,
            "failure_reason": failure_reason,
            "next_action": "force_paused",
            "checked_at": _utc_now_iso(),
            "checked_by": checked_by,
            "source_of_truth_path": str(state_path),
            "state_file_path": str(state_path),
            "dry_run_guard_evidence": str(dry_run_evidence_path),
            "resume_gate_evidence": str(resume_evidence_path),
            "transition_evidence": str(transition_evidence_path),
            "events_file_path": str(events_file_path),
            "observed_provider_accepted_count": 0,
            "current_window_complete": False,
            "last_safe_send_number": 0,
            "launch_mode_before": None,
            "launch_status_before": None,
            "launch_mode_after": None,
            "launch_status_after": None,
            "recommendation": "force_paused",
            "safe_state_snapshot": None,
            "send_records": [],
            "alert_channel_placeholder": ALERT_CHANNEL_PLACEHOLDER,
        }
        if output_path is not None:
            _atomic_write_json(output_path, evidence)
        _atomic_write_json(Path(pause_record_path), evidence)
        print(json.dumps(evidence, indent=2, sort_keys=True))
        _emit_summary(
            MonitorResult(
                monitor_result="FAIL",
                verification_result="FAIL",
                recommendation="force_paused",
                failure_reason=failure_reason,
                threshold_breached=True,
                observed_provider_accepted_count=0,
                hard_bounce_count=0,
                complaint_count=0,
                wrong_recipient_count=0,
                wrong_copy_count=0,
                authentication_failure_count=0,
                consecutive_delivery_failures=0,
                last_safe_send_number=0,
                current_window_complete=False,
                launch_mode_before=None,
                launch_status_before=None,
                launch_mode_after=None,
                launch_status_after=None,
                next_action="force_paused",
                campaign_id=campaign_id,
                launch_correlation_id=correlation_id,
                send_records=[],
                safe_state_snapshot=None,
            ),
            output_path or Path(pause_record_path),
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
