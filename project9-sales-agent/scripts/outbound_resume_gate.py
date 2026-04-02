#!/usr/bin/env python3
"""Founder-only resume gate for Project 9 outbound launch state."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_STATE_FILE = REPO_ROOT / "state" / "outbound_launch_state.json"
DEFAULT_RESUME_RECORD = REPO_ROOT / "state" / "outbound_resume_authorization.json"
DEFAULT_ENTRY_POINT = "workflow_dispatch"
HOOK_NAME = "outbound_resume_gate"
ALERT_CHANNEL_PLACEHOLDER = "Telegram"
APPROVED_RESUME_REQUEST = "RESUME AUTO"
DEFAULT_APPROVED_GITHUB_ACTOR = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
ELIGIBLE_LAUNCH_STATES = {
    "DRY_RUN",
    "PAUSED",
}
REQUIRED_STATE_FIELDS = (
    "launch_mode",
    "launch_status",
    "verified_by",
    "verified_at",
    "correlation_id",
    "source",
    "notes",
)
REPLAY_WINDOW = timedelta(hours=6)
REPLAY_DETECTION_MODE = "correlation_and_time"


@dataclass(frozen=True)
class GateResult:
    authorization_result: str
    failure_reason: str | None
    launch_mode_before: str | None
    launch_status_before: str | None
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
        return None, f"state file unreadable: {exc.strerror or exc.__class__.__name__}"

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"state file malformed: {exc.msg}"

    if not isinstance(payload, dict):
        return None, "state file malformed: root JSON value must be an object"

    return payload, None


def _parse_iso_timestamp(value: str | None) -> datetime | None:
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


def _validate_launch_state(state: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    missing = [field for field in REQUIRED_STATE_FIELDS if _normalize(state.get(field)) is None]
    launch_mode = _normalize(state.get("launch_mode"))
    launch_status = _normalize(state.get("launch_status"))
    correlation_id = _normalize(state.get("correlation_id"))

    if missing:
        raise ValueError(f"incomplete launch state: missing fields {', '.join(missing)}")

    if launch_mode not in ELIGIBLE_LAUNCH_STATES:
        raise ValueError(f"launch state not eligible for resume: {launch_mode}")

    return launch_mode, launch_status, correlation_id


def _validate_founder_identity(*, requested_by: str, approved_github_actor: str) -> None:
    if not approved_github_actor:
        raise ValueError("missing approved GitHub founder identity")

    if requested_by != approved_github_actor:
        raise ValueError(
            f"unauthorized GitHub identity: {requested_by}; expected {approved_github_actor}"
        )


def _validate_resume_request_text(resume_request: str) -> None:
    if resume_request != APPROVED_RESUME_REQUEST:
        raise ValueError(f"invalid resume request: {resume_request}")


def _validate_entry_point(entry_point: str) -> None:
    if entry_point != DEFAULT_ENTRY_POINT:
        raise ValueError(f"unsupported resume entry point: {entry_point}")


def _validate_replay(
    *,
    current_request: str,
    current_requester: str,
    current_correlation_id: str,
    existing_record: dict[str, Any] | None,
) -> None:
    if existing_record is None:
        return

    previous_request = _normalize(existing_record.get("request_text"))
    previous_requester = _normalize(existing_record.get("requested_by"))
    previous_correlation_id = _normalize(existing_record.get("correlation_id"))
    previous_checked_at = _parse_iso_timestamp(existing_record.get("checked_at"))

    if previous_correlation_id == current_correlation_id:
        raise ValueError("duplicate resume request: correlation id already recorded")

    if previous_request == current_request and previous_requester == current_requester:
        if previous_checked_at is None:
            raise ValueError("resume record corrupted: missing or invalid checked_at")

        if _utc_now() - previous_checked_at < REPLAY_WINDOW:
            raise ValueError("replayed resume request: time-based replay window active")


def _build_evidence(
    *,
    result: GateResult,
    correlation_id: str,
    resume_request: str,
    requested_by: str,
    approved_github_actor: str,
    checked_by: str,
    resume_record_path: Path,
    entry_point: str,
) -> dict[str, Any]:
    return {
        "hook_name": HOOK_NAME,
        "correlation_id": correlation_id,
        "request_text": resume_request,
        "requested_by": requested_by,
        "approved_github_actor": approved_github_actor,
        "authorization_result": result.authorization_result,
        "failure_reason": result.failure_reason,
        "launch_mode_before": result.launch_mode_before,
        "launch_status_before": result.launch_status_before,
        "resume_record_path": str(resume_record_path),
        "checked_at": _utc_now_iso(),
        "checked_by": checked_by,
        "next_action": result.next_action,
        "resume_entry_point": entry_point,
        "replay_detection_mode": REPLAY_DETECTION_MODE,
        "alert_channel_placeholder": ALERT_CHANNEL_PLACEHOLDER
        if result.authorization_result == "FAIL"
        else None,
    }


def _emit_summary(
    result: GateResult,
    state_path: Path,
    resume_record_path: Path,
    evidence_path: Path | None,
) -> None:
    if result.authorization_result == "PASS":
        print(f"[PASS] Founder resume gate authorized: {state_path}")
        print(f"Authorization record written to: {resume_record_path}")
    else:
        print(f"[FAIL] Founder resume gate blocked progression: {result.failure_reason}")

    if evidence_path is not None:
        print(f"Evidence written to: {evidence_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Authorize founder-only RESUME AUTO requests.")
    parser.add_argument(
        "--resume-request",
        default=os.environ.get("OUTBOUND_RESUME_REQUEST"),
        help="Founder resume request text.",
    )
    parser.add_argument(
        "--requested-by",
        default=os.environ.get("OUTBOUND_REQUESTED_BY"),
        help="GitHub actor login for the resume request.",
    )
    parser.add_argument(
        "--approved-github-actor",
        default=os.environ.get("OUTBOUND_APPROVED_GITHUB_ACTOR", DEFAULT_APPROVED_GITHUB_ACTOR),
        help="Approved GitHub founder login.",
    )
    parser.add_argument(
        "--correlation-id",
        default=os.environ.get("OUTBOUND_CORRELATION_ID"),
        help="Launch correlation id.",
    )
    parser.add_argument(
        "--state-file",
        default=os.environ.get("OUTBOUND_LAUNCH_STATE_PATH", str(DEFAULT_STATE_FILE)),
        help="Path to the launch-state JSON.",
    )
    parser.add_argument(
        "--resume-record",
        default=os.environ.get("OUTBOUND_RESUME_RECORD_PATH", str(DEFAULT_RESUME_RECORD)),
        help="Path to the resume authorization record.",
    )
    parser.add_argument(
        "--entry-point",
        default=os.environ.get("OUTBOUND_RESUME_ENTRY_POINT", DEFAULT_ENTRY_POINT),
        help="Founder resume entry point.",
    )
    parser.add_argument(
        "--checked-by",
        default=os.environ.get("OUTBOUND_GUARD_ACTOR", "python"),
        help="Actor label for the verification run.",
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
    resume_record_path = Path(args.resume_record)
    output_path = Path(args.output) if args.output else None
    resume_request = _normalize(args.resume_request)
    requested_by = _normalize(args.requested_by)
    approved_github_actor = _normalize(args.approved_github_actor)
    correlation_id = _normalize(args.correlation_id)
    entry_point = _normalize(args.entry_point) or DEFAULT_ENTRY_POINT
    checked_by = _normalize(args.checked_by) or "python"

    try:
        if resume_request is None:
            raise ValueError("missing resume request")
        if requested_by is None:
            raise ValueError("missing GitHub actor identity")
        if correlation_id is None:
            raise ValueError("missing correlation id")

        _validate_entry_point(entry_point)
        _validate_resume_request_text(resume_request)
        _validate_founder_identity(
            requested_by=requested_by,
            approved_github_actor=approved_github_actor or DEFAULT_APPROVED_GITHUB_ACTOR,
        )

        state, load_error = _load_json_file(state_path)
        if load_error is not None:
            raise ValueError(load_error)

        launch_mode_before, launch_status_before, state_correlation_id = _validate_launch_state(state)

        if state_correlation_id is not None and state_correlation_id != correlation_id:
            raise ValueError(
                f"launch correlation mismatch: state has {state_correlation_id}, request has {correlation_id}"
            )

        existing_record = None
        if resume_record_path.exists():
            existing_record, record_error = _load_json_file(resume_record_path)
            if record_error is not None:
                raise ValueError(f"resume record unreadable: {record_error}")

        _validate_replay(
            current_request=resume_request,
            current_requester=requested_by,
            current_correlation_id=correlation_id,
            existing_record=existing_record,
        )

        result = GateResult(
            authorization_result="PASS",
            failure_reason=None,
            launch_mode_before=launch_mode_before,
            launch_status_before=launch_status_before,
            next_action="advance_to_later_launch_steps",
        )

        evidence = _build_evidence(
            result=result,
            correlation_id=correlation_id,
            resume_request=resume_request,
            requested_by=requested_by,
            approved_github_actor=approved_github_actor or DEFAULT_APPROVED_GITHUB_ACTOR,
            checked_by=checked_by,
            resume_record_path=resume_record_path,
            entry_point=entry_point,
        )

        resume_record_path.parent.mkdir(parents=True, exist_ok=True)
        resume_record_path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        print(json.dumps(evidence, indent=2, sort_keys=True))
        _emit_summary(result, state_path, resume_record_path, output_path)
        return 0

    except ValueError as exc:
        try:
            state, _ = _load_json_file(state_path)
            launch_mode_before = _normalize(state.get("launch_mode")) if state else None
            launch_status_before = _normalize(state.get("launch_status")) if state else None
        except Exception:
            launch_mode_before = None
            launch_status_before = None

        result = GateResult(
            authorization_result="FAIL",
            failure_reason=str(exc),
            launch_mode_before=launch_mode_before,
            launch_status_before=launch_status_before,
            next_action="block_progression",
        )
        evidence = _build_evidence(
            result=result,
            correlation_id=correlation_id or "unknown",
            resume_request=resume_request or APPROVED_RESUME_REQUEST,
            requested_by=requested_by or "unknown",
            approved_github_actor=approved_github_actor or DEFAULT_APPROVED_GITHUB_ACTOR,
            checked_by=checked_by,
            resume_record_path=resume_record_path,
            entry_point=entry_point,
        )

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        print(json.dumps(evidence, indent=2, sort_keys=True))
        _emit_summary(result, state_path, resume_record_path, output_path)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
