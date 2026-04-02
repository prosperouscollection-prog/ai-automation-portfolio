#!/usr/bin/env python3
"""Dry-run guard verifier for Project 9 outbound launch state."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_STATE_FILE = SCRIPT_DIR.parent / "state" / "outbound_launch_state.json"
HOOK_NAME = "outbound_dry_run_guard"
ALERT_CHANNEL_PLACEHOLDER = "Telegram"
REQUIRED_FIELDS = (
    "launch_mode",
    "launch_status",
    "verified_by",
    "verified_at",
    "correlation_id",
    "source",
    "notes",
)
ALLOWED_DRY_RUN_STATUSES = {
    "READY",
    "PAUSED",
    "PREPARED",
    "VERIFIED",
    "DRY_RUN_READY",
}
BLOCKED_LAUNCH_STATUSES = {
    "LIVE_ALLOWED",
    "LIVE",
    "ACTIVE",
    "SENDING",
    "SEND_ENABLED",
    "ARMED",
    "GO",
    "RESUME_PENDING",
}


@dataclass(frozen=True)
class GuardResult:
    verification_result: str
    failure_reason: str | None
    launch_mode_before: str | None
    launch_status_before: str | None
    next_action: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state(path: Path) -> tuple[dict[str, Any] | None, str | None]:
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


def _normalize(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value).strip() or None


def _validate_state(state: dict[str, Any]) -> GuardResult:
    missing = [field for field in REQUIRED_FIELDS if _normalize(state.get(field)) is None]
    launch_mode = _normalize(state.get("launch_mode"))
    launch_status = _normalize(state.get("launch_status"))

    if missing:
        return GuardResult(
            verification_result="FAIL",
            failure_reason=f"incomplete state: missing fields {', '.join(missing)}",
            launch_mode_before=launch_mode,
            launch_status_before=launch_status,
            next_action="block_progression",
        )

    if launch_mode != "DRY_RUN":
        return GuardResult(
            verification_result="FAIL",
            failure_reason=f"launch_mode must be DRY_RUN, found {launch_mode}",
            launch_mode_before=launch_mode,
            launch_status_before=launch_status,
            next_action="block_progression",
        )

    if launch_status in BLOCKED_LAUNCH_STATUSES:
        return GuardResult(
            verification_result="FAIL",
            failure_reason=f"contradictory launch_status: {launch_status}",
            launch_mode_before=launch_mode,
            launch_status_before=launch_status,
            next_action="block_progression",
        )

    if launch_status not in ALLOWED_DRY_RUN_STATUSES:
        return GuardResult(
            verification_result="FAIL",
            failure_reason=f"unsupported launch_status for DRY_RUN: {launch_status}",
            launch_mode_before=launch_mode,
            launch_status_before=launch_status,
            next_action="block_progression",
        )

    return GuardResult(
        verification_result="PASS",
        failure_reason=None,
        launch_mode_before=launch_mode,
        launch_status_before=launch_status,
        next_action="proceed_to_resume_gate",
    )


def _build_evidence(
    *,
    result: GuardResult,
    correlation_id: str,
    checked_by: str,
    source_of_truth_path: Path,
) -> dict[str, Any]:
    return {
        "hook_name": HOOK_NAME,
        "correlation_id": correlation_id,
        "launch_mode_before": result.launch_mode_before,
        "launch_status_before": result.launch_status_before,
        "verification_result": result.verification_result,
        "failure_reason": result.failure_reason,
        "source_of_truth_path": str(source_of_truth_path),
        "checked_at": _utc_now(),
        "checked_by": checked_by,
        "next_action": result.next_action,
        "alert_channel_placeholder": ALERT_CHANNEL_PLACEHOLDER
        if result.verification_result == "FAIL"
        else None,
    }


def _emit_summary(result: GuardResult, state_path: Path, evidence_path: Path | None) -> None:
    if result.verification_result == "PASS":
        print(f"[PASS] Dry-run guard verified: {state_path}")
    else:
        print(f"[FAIL] Dry-run guard blocked progression: {result.failure_reason}")
    if evidence_path is not None:
        print(f"Evidence written to: {evidence_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify outbound launch is still in DRY-RUN.")
    parser.add_argument(
        "--state-file",
        default=os.environ.get("OUTBOUND_LAUNCH_STATE_PATH", str(DEFAULT_STATE_FILE)),
        help="Path to the launch-state JSON.",
    )
    parser.add_argument(
        "--correlation-id",
        default=os.environ.get("OUTBOUND_CORRELATION_ID"),
        help="Launch correlation id.",
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
    correlation_id = args.correlation_id or state_path.stem
    checked_by = args.checked_by
    output_path = Path(args.output) if args.output else None

    state, load_error = _load_state(state_path)
    if load_error is not None:
        result = GuardResult(
            verification_result="FAIL",
            failure_reason=load_error,
            launch_mode_before=None,
            launch_status_before=None,
            next_action="block_progression",
        )
    else:
        result = _validate_state(state)

    evidence = _build_evidence(
        result=result,
        correlation_id=correlation_id,
        checked_by=checked_by,
        source_of_truth_path=state_path,
    )

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(evidence, indent=2, sort_keys=True))
    _emit_summary(result, state_path, output_path)
    return 0 if result.verification_result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
