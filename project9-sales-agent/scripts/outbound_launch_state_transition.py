#!/usr/bin/env python3
"""Controlled launch-state transition controller for Project 9."""

from __future__ import annotations

import argparse
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
DEFAULT_TRANSITION_RECORD = REPO_ROOT / "state" / "outbound_launch_state_transition.json"
DEFAULT_TARGET_STATE = "PAUSED"
DEFAULT_WRITE_STRATEGY = "atomic_replace"
HOOK_NAME = "outbound_launch_state_transition"
ALERT_CHANNEL_PLACEHOLDER = "Telegram"
REQUIRED_STATE_FIELDS = (
    "launch_mode",
    "launch_status",
    "verified_by",
    "verified_at",
    "correlation_id",
    "source",
    "notes",
)
ALLOWED_SOURCE_STATES = {
    "DRY_RUN",
    "PAUSED",
    "RESUME_PENDING",
}
ALLOWED_TARGET_STATES = {
    "PAUSED",
}
TRANSITION_MATRIX = {
    "DRY_RUN": {"PAUSED"},
    "PAUSED": {"PAUSED"},
    "RESUME_PENDING": {"PAUSED"},
}
VALID_LAUNCH_STATUSES = {
    "READY",
    "PAUSED",
    "PREPARED",
    "VERIFIED",
    "DRY_RUN_READY",
}
REPLAY_WINDOW = timedelta(hours=24)


@dataclass(frozen=True)
class TransitionResult:
    transition_result: str
    failure_reason: str | None
    source_state_before: str | None
    source_status_before: str | None
    target_state_requested: str | None
    target_status_written: str | None
    launch_mode_after: str | None
    launch_status_after: str | None
    next_action: str


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


def _validate_current_state(state: dict[str, Any]) -> tuple[str, str, str]:
    missing = [field for field in REQUIRED_STATE_FIELDS if _normalize(state.get(field)) is None]
    if missing:
        raise ValueError(f"incomplete launch state: missing fields {', '.join(missing)}")

    source_state = _normalize(state.get("launch_mode"))
    source_status = _normalize(state.get("launch_status"))
    correlation_id = _normalize(state.get("correlation_id"))

    if source_state not in ALLOWED_SOURCE_STATES:
        raise ValueError(f"source state not eligible for transition: {source_state}")

    if source_status not in VALID_LAUNCH_STATUSES:
        raise ValueError(f"source launch_status not eligible for transition: {source_status}")

    if correlation_id is None:
        raise ValueError("missing launch correlation id")

    return source_state, source_status, correlation_id


def _validate_requested_target_state(target_state: str) -> str:
    if target_state not in ALLOWED_TARGET_STATES:
        raise ValueError(f"target state not allowed by this controller: {target_state}")

    return target_state


def _expected_target_status(target_state: str) -> str:
    if target_state == "PAUSED":
        return "PAUSED"
    raise ValueError(f"unsupported target state: {target_state}")


def _validate_evidence_artifact(
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


def _build_updated_state(
    *,
    current_state: dict[str, Any],
    target_state: str,
    checked_by: str,
    correlation_id: str,
    state_file_path: Path,
) -> dict[str, Any]:
    target_status = _expected_target_status(target_state)
    return {
        "launch_mode": target_state,
        "launch_status": target_status,
        "verified_by": checked_by,
        "verified_at": _utc_now_iso(),
        "correlation_id": correlation_id,
        "source": str(state_file_path),
        "notes": (
            f"Transitioned from {current_state.get('launch_mode')} to {target_state} "
            f"after upstream evidence PASS."
        ),
    }


def _build_evidence(
    *,
    result: TransitionResult,
    correlation_id: str,
    checked_by: str,
    state_file_path: Path,
    transition_record_path: Path,
    dry_run_evidence_path: Path,
    resume_evidence_path: Path,
) -> dict[str, Any]:
    return {
        "hook_name": HOOK_NAME,
        "correlation_id": correlation_id,
        "source_state_before": result.source_state_before,
        "source_status_before": result.source_status_before,
        "target_state_requested": result.target_state_requested,
        "target_status_written": result.target_status_written,
        "transition_result": result.transition_result,
        "failure_reason": result.failure_reason,
        "dry_run_guard_evidence": str(dry_run_evidence_path),
        "resume_gate_evidence": str(resume_evidence_path),
        "state_file_path": str(state_file_path),
        "transition_record_path": str(transition_record_path),
        "checked_at": _utc_now_iso(),
        "checked_by": checked_by,
        "next_action": result.next_action,
        "launch_mode_after": result.launch_mode_after,
        "launch_status_after": result.launch_status_after,
        "transition_write_strategy": DEFAULT_WRITE_STRATEGY,
        "alert_channel_placeholder": ALERT_CHANNEL_PLACEHOLDER
        if result.transition_result == "FAIL"
        else None,
    }


def _emit_summary(result: TransitionResult, state_path: Path, transition_record_path: Path) -> None:
    if result.transition_result == "PASS":
        print(f"[PASS] Launch state transition written: {state_path}")
        print(f"Transition record written to: {transition_record_path}")
    else:
        print(f"[FAIL] Launch state transition blocked: {result.failure_reason}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Perform a controlled launch-state transition.")
    parser.add_argument(
        "--state-file",
        default=os.environ.get("OUTBOUND_LAUNCH_STATE_PATH", str(DEFAULT_STATE_FILE)),
        help="Path to the current launch-state JSON.",
    )
    parser.add_argument(
        "--dry-run-evidence",
        default=os.environ.get("OUTBOUND_DRY_RUN_EVIDENCE_PATH"),
        help="Path to dry-run guard evidence.",
    )
    parser.add_argument(
        "--resume-evidence",
        default=os.environ.get("OUTBOUND_RESUME_GUARD_EVIDENCE_PATH"),
        help="Path to resume gate evidence.",
    )
    parser.add_argument(
        "--target-state",
        default=os.environ.get("OUTBOUND_TARGET_STATE", DEFAULT_TARGET_STATE),
        help="Requested next launch state.",
    )
    parser.add_argument(
        "--transition-record",
        default=os.environ.get("OUTBOUND_TRANSITION_RECORD_PATH", str(DEFAULT_TRANSITION_RECORD)),
        help="Path to the transition record JSON.",
    )
    parser.add_argument(
        "--correlation-id",
        default=os.environ.get("OUTBOUND_CORRELATION_ID"),
        help="Launch correlation id.",
    )
    parser.add_argument(
        "--checked-by",
        default=os.environ.get("OUTBOUND_GUARD_ACTOR", "python"),
        help="Actor label for the transition run.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write the evidence JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state_path = Path(args.state_file)
    transition_record_path = Path(args.transition_record)
    dry_run_evidence_path = Path(args.dry_run_evidence) if args.dry_run_evidence else None
    resume_evidence_path = Path(args.resume_evidence) if args.resume_evidence else None
    output_path = Path(args.output) if args.output else None
    checked_by = _normalize(args.checked_by) or "python"
    requested_target_state = _normalize(args.target_state) or DEFAULT_TARGET_STATE

    original_state_bytes: bytes | None = None
    current_state: dict[str, Any] | None = None
    source_state_before: str | None = None
    source_status_before: str | None = None
    correlation_id: str | None = _normalize(args.correlation_id)
    result: TransitionResult | None = None

    try:
        current_state, load_error = _load_json_file(state_path)
        if load_error is not None:
            raise ValueError(f"current launch state {load_error}")

        source_state_before, source_status_before, state_correlation_id = _validate_current_state(current_state)
        correlation_id = correlation_id or state_correlation_id
        if correlation_id is None:
            raise ValueError("missing launch correlation id")

        if requested_target_state not in ALLOWED_TARGET_STATES:
            raise ValueError(f"target state not allowed by this controller: {requested_target_state}")

        if requested_target_state not in TRANSITION_MATRIX[source_state_before]:
            raise ValueError(
                f"unsupported transition: {source_state_before} -> {requested_target_state}"
            )

        if dry_run_evidence_path is None:
            raise ValueError("missing dry-run evidence path")
        if resume_evidence_path is None:
            raise ValueError("missing resume gate evidence path")

        dry_run_evidence = _validate_evidence_artifact(
            evidence_path=dry_run_evidence_path,
            expected_hook_name="outbound_dry_run_guard",
            result_field="verification_result",
            expected_result_value="PASS",
            current_correlation_id=correlation_id,
            expected_next_action="proceed_to_resume_gate",
        )
        resume_evidence = _validate_evidence_artifact(
            evidence_path=resume_evidence_path,
            expected_hook_name="outbound_resume_gate",
            result_field="authorization_result",
            expected_result_value="PASS",
            current_correlation_id=correlation_id,
            expected_next_action="advance_to_later_launch_steps",
        )

        dry_checked_at = _parse_iso_timestamp(dry_run_evidence.get("checked_at"))
        resume_checked_at = _parse_iso_timestamp(resume_evidence.get("checked_at"))
        if not _is_fresh(dry_checked_at):
            raise ValueError("dry-run guard evidence is stale or missing checked_at")
        if not _is_fresh(resume_checked_at):
            raise ValueError("resume gate evidence is stale or missing checked_at")
        if dry_checked_at and resume_checked_at and dry_checked_at > resume_checked_at:
            raise ValueError("evidence order invalid: dry-run guard must precede resume gate")

        updated_state = _build_updated_state(
            current_state=current_state,
            target_state=requested_target_state,
            checked_by=checked_by,
            correlation_id=correlation_id,
            state_file_path=state_path,
        )

        original_state_bytes = state_path.read_bytes()
        state_bytes = (json.dumps(updated_state, indent=2, sort_keys=True) + "\n").encode("utf-8")

        _atomic_write_bytes(state_path, state_bytes)

        result = TransitionResult(
            transition_result="PASS",
            failure_reason=None,
            source_state_before=source_state_before,
            source_status_before=source_status_before,
            target_state_requested=requested_target_state,
            target_status_written=updated_state["launch_status"],
            launch_mode_after=updated_state["launch_mode"],
            launch_status_after=updated_state["launch_status"],
            next_action="hold_for_first_10_monitor",
        )

        evidence = _build_evidence(
            result=result,
            correlation_id=correlation_id,
            checked_by=checked_by,
            state_file_path=state_path,
            transition_record_path=transition_record_path,
            dry_run_evidence_path=dry_run_evidence_path,
            resume_evidence_path=resume_evidence_path,
        )

        try:
            _atomic_write_json(transition_record_path, evidence)
        except Exception as exc:
            if original_state_bytes is not None:
                try:
                    _atomic_write_bytes(state_path, original_state_bytes)
                except Exception:
                    pass
            raise ValueError(f"transition record write failed: {exc}") from exc

        if output_path is not None:
            _atomic_write_json(output_path, evidence)

        print(json.dumps(evidence, indent=2, sort_keys=True))
        _emit_summary(result, state_path, transition_record_path)
        return 0

    except ValueError as exc:
        failure_reason = str(exc)
        result = TransitionResult(
            transition_result="FAIL",
            failure_reason=failure_reason,
            source_state_before=source_state_before,
            source_status_before=source_status_before,
            target_state_requested=requested_target_state,
            target_status_written=None,
            launch_mode_after=source_state_before,
            launch_status_after=source_status_before,
            next_action="block_progression",
        )

        evidence = _build_evidence(
            result=result,
            correlation_id=correlation_id or "unknown",
            checked_by=checked_by,
            state_file_path=state_path,
            transition_record_path=transition_record_path,
            dry_run_evidence_path=dry_run_evidence_path or Path("missing-dry-run-evidence"),
            resume_evidence_path=resume_evidence_path or Path("missing-resume-evidence"),
        )

        try:
            _atomic_write_json(transition_record_path, evidence)
        except Exception:
            pass

        if output_path is not None:
            try:
                _atomic_write_json(output_path, evidence)
            except Exception:
                pass

        print(json.dumps(evidence, indent=2, sort_keys=True))
        _emit_summary(result, state_path, transition_record_path)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
