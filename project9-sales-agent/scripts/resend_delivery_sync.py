#!/usr/bin/env python3
"""Resend delivery-status sync for the first-10 outbound monitor.

Polls the Resend API for each provider_message_id recorded in the
first-10 send-event feed that holds a real Resend email ID (IDs that start
with "re_" or contain only alphanumeric characters without the synthetic prefix).
Updates delivery_status, bounce_count, and complaint_count in-place, then
writes any newly detected suppression events to the dedicated suppression list.

Preserves fail-closed behaviour: any unreadable state file or unresolvable API
error leaves the feed unchanged.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_EVENTS_FILE = REPO_ROOT / "state" / "outbound_first_10_send_events.ndjson"
DEFAULT_SUPPRESSION_FILE = REPO_ROOT / "state" / "suppression_list.ndjson"

RESEND_BASE = "https://api.resend.com"
RESEND_TIMEOUT = 15

# Resend statuses that map to hard_bounce suppression
BOUNCE_STATUSES = {"bounced"}
# Resend statuses that map to complaint suppression
COMPLAINT_STATUSES = {"complained"}
# Resend statuses considered terminal (no further polling needed)
TERMINAL_STATUSES = {"delivered", "bounced", "complained"}
# Resend statuses that indicate failed delivery (not a suppression event)
DELIVERY_FAIL_STATUSES = {"delivery_delayed"}

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_real_resend_id(provider_message_id: str | None) -> bool:
    """Return True if the ID looks like a real Resend email ID (not synthetic)."""
    if not provider_message_id:
        return False
    pid = str(provider_message_id).strip()
    # Real Resend IDs start with "re_" followed by alphanumerics
    if pid.startswith("re_"):
        return True
    # Synthetic IDs created by this codebase have "resend-synthetic-" or "resend-{run_id}-"
    if "synthetic" in pid or pid.startswith("resend-"):
        return False
    return False


def _hash_email(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _fetch_resend_email_status(resend_id: str, api_key: str) -> dict[str, Any] | None:
    """Call GET /emails/{id} and return the parsed JSON body, or None on error."""
    if requests is None:
        logger.error("requests package is not available; cannot poll Resend API")
        return None
    url = f"{RESEND_BASE}/emails/{resend_id}"
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=RESEND_TIMEOUT,
        )
    except Exception as exc:
        logger.warning("Resend API request failed for %s: %s", resend_id, exc)
        return None
    if resp.status_code == 404:
        logger.info("Resend email ID not found (may have expired): %s", resend_id)
        return None
    if not resp.ok:
        logger.warning("Resend API returned %s for %s: %s", resp.status_code, resend_id, resp.text[:200])
        return None
    try:
        return resp.json()
    except Exception:
        logger.warning("Resend API returned non-JSON for %s", resend_id)
        return None


def _map_resend_status_to_internal(resend_status: str | None) -> str | None:
    """Map a Resend last_event value to our internal delivery_status vocabulary."""
    if not resend_status:
        return None
    s = str(resend_status).strip().lower()
    mapping = {
        "sent": "accepted",
        "delivered": "delivered",
        "delivery_delayed": "delivery_delayed",
        "bounced": "hard_bounce",
        "complained": "complaint",
        "opened": "delivered",
        "clicked": "delivered",
    }
    return mapping.get(s, s)


def _load_events(events_file: Path) -> list[dict[str, Any]]:
    if not events_file.exists():
        return []
    raw = events_file.read_text(encoding="utf-8", errors="replace")
    records = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            logger.warning("Skipping malformed NDJSON line in event feed")
    return records


def _write_events_atomic(events_file: Path, records: list[dict[str, Any]]) -> None:
    """Write records back to the NDJSON file atomically."""
    events_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=events_file.parent, prefix=".resend_sync_tmp_", suffix=".ndjson"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        os.replace(tmp_path, events_file)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _append_suppression_entry(
    suppression_file: Path,
    *,
    recipient_hash: str,
    status: str,
    reason: str,
    resend_id: str,
) -> None:
    """Append a suppression event to the dedicated suppression list."""
    suppression_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "recipient_hash": recipient_hash,
        "status": status,
        "reason": reason,
        "resend_id": resend_id,
        "date_added": _utc_now_iso(),
        "source": "resend_delivery_sync",
    }
    with suppression_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info("Suppression entry written: status=%s resend_id=%s", status, resend_id)


def run(
    events_file: Path,
    suppression_file: Path,
    api_key: str,
    *,
    dry_run: bool = False,
) -> int:
    """Sync delivery status for all actionable first-10 events.

    Returns the number of events updated.
    """
    records = _load_events(events_file)
    if not records:
        logger.info("No first-10 send events found; nothing to sync.")
        return 0

    updated = 0
    for idx, record in enumerate(records):
        pid = record.get("provider_message_id")
        if not _is_real_resend_id(pid):
            continue

        current_status = str(record.get("delivery_status", "")).strip().lower()
        # Skip events that already have a terminal delivery status
        if current_status in ("delivered", "hard_bounce", "complaint"):
            logger.info("Skipping already-terminal event idx=%d status=%s", idx, current_status)
            continue

        email_data = _fetch_resend_email_status(pid, api_key)
        if email_data is None:
            continue

        # Resend returns last_event or sometimes just status depending on SDK version
        raw_status = (
            email_data.get("last_event")
            or email_data.get("status")
        )
        internal_status = _map_resend_status_to_internal(raw_status)
        if not internal_status:
            logger.info("Resend returned no recognisable status for %s", pid)
            continue

        if internal_status == current_status:
            logger.info("Status unchanged for %s: %s", pid, internal_status)
            continue

        logger.info(
            "Updating event idx=%d provider_message_id=%s: %s → %s",
            idx, pid, current_status, internal_status,
        )

        recipient_hash = str(record.get("recipient_hash", "")).strip()

        if not dry_run:
            record["delivery_status"] = internal_status
            record["delivery_sync_updated_at"] = _utc_now_iso()
            record["delivery_sync_raw_status"] = raw_status

            if internal_status == "hard_bounce":
                record["bounce_count"] = 1
                if recipient_hash:
                    _append_suppression_entry(
                        suppression_file,
                        recipient_hash=recipient_hash,
                        status="hard_bounce",
                        reason=f"resend_status={raw_status}",
                        resend_id=pid,
                    )
            elif internal_status == "complaint":
                record["complaint_count"] = 1
                if recipient_hash:
                    _append_suppression_entry(
                        suppression_file,
                        recipient_hash=recipient_hash,
                        status="complaint",
                        reason=f"resend_status={raw_status}",
                        resend_id=pid,
                    )

        updated += 1

    if not dry_run and updated > 0:
        _write_events_atomic(events_file, records)
        logger.info("Event feed updated with %d delivery status change(s).", updated)
    elif dry_run:
        logger.info("[DRY RUN] %d event(s) would have been updated.", updated)
    else:
        logger.info("All events already current; no writes needed.")

    return updated


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Sync Resend delivery signals into first-10 event feed.")
    parser.add_argument(
        "--events-file",
        default=str(DEFAULT_EVENTS_FILE),
        help="Path to outbound_first_10_send_events.ndjson",
    )
    parser.add_argument(
        "--suppression-file",
        default=str(DEFAULT_SUPPRESSION_FILE),
        help="Path to suppression_list.ndjson",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be updated without writing any files.",
    )
    args = parser.parse_args()

    api_key = os.getenv("RESEND_API_KEY", "").strip()
    if not api_key:
        logger.error("RESEND_API_KEY is not set; cannot poll Resend API. Exiting.")
        sys.exit(1)

    events_file = Path(args.events_file)
    suppression_file = Path(args.suppression_file)

    updated = run(events_file, suppression_file, api_key, dry_run=args.dry_run)
    print(f"resend_delivery_sync: {updated} event(s) updated.")


if __name__ == "__main__":
    main()
