#!/usr/bin/env python3
"""Controlled prospect micro-batch pilot for Genesis AI Systems.

This runner stays tightly bounded:
- only qualified production Leads rows are eligible
- batch size is capped at 5 by default
- founder approval is required before each send
- duplicate protection is preserved through a dedicated pilot state file
- no schedule automation, no loops, no auto-send enablement

GLOBAL AUTO-SEND REMAINS PAUSED.
ONLY FOUNDER-APPROVED MICRO-BATCH PILOT IS AUTHORIZED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPO_ROOT = ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared_env import bootstrap_env, getenv  # noqa: E402

bootstrap_env()

from lead_revenue_pipeline import (  # noqa: E402
    AUTO_SEND_PAUSED_BY_DEFAULT,
    DEFAULT_LIVE_GOOGLE_SHEET_ID,
    DEFAULT_LIVE_SERVICE_ACCOUNT_FILE,
    OpenAIDraftClient,
    SHEETS_HEADERS,
    compare_sheet_headers,
    _safe_json_dumps,
)


SCRIPT_DIR = Path(__file__).resolve().parent
STATE_DIR = SCRIPT_DIR / ".." / "state"
PROOF_DIR = SCRIPT_DIR / ".." / "proof_artifacts"
PILOT_STATE_PATH = STATE_DIR / "prospect_pilot_state.json"
PILOT_EVIDENCE_PATH = STATE_DIR / "prospect_pilot_delivery_log.ndjson"
PILOT_ARTIFACT_PATH = PROOF_DIR / "prospect_pilot_delivery_evidence.md"

PRODUCTION_SHEET_NAME = "Leads"
DEFAULT_BATCH_SIZE = 5
PILOT_ENABLED_FLAG = "GENESIS_FOUNDERS_PILOT_APPROVAL"
INTERNAL_MARKER_PATTERNS = (
    "release-gate",
    "founder-test",
    "verification",
    "proof",
    "internal",
    "test",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_ndjson(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True))
        handle.write("\n")


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


def _sheet_client(service_account_file: Path, scopes: list[str]):
    credentials = Credentials.from_service_account_file(str(service_account_file), scopes=scopes)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def _read_sheet_rows(
    *,
    spreadsheet_id: str,
    service_account_file: Path,
    worksheet_name: str,
) -> list[list[str]]:
    service = _sheet_client(service_account_file, ["https://www.googleapis.com/auth/spreadsheets.readonly"])
    response = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{worksheet_name}!A1:O1000")
        .execute()
    )
    return response.get("values", [])


def _row_to_record(headers: list[str], row: list[str]) -> dict[str, str]:
    record: dict[str, str] = {}
    for index, header in enumerate(headers):
        record[header] = str(row[index]).strip() if index < len(row) else ""
    return record


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _is_internal_row(record: dict[str, str]) -> bool:
    haystack_parts = [
        record.get("business name", ""),
        record.get("owner_email", ""),
        record.get("source", ""),
        record.get("outreach subject", ""),
        record.get("outreach body", ""),
    ]
    haystack = " ".join(part.lower() for part in haystack_parts if part)
    return any(marker in haystack for marker in INTERNAL_MARKER_PATTERNS)


def _lead_fingerprint(record: dict[str, str]) -> str:
    parts = [
        _normalize_text(record.get("business name")),
        _normalize_text(record.get("domain")),
        _normalize_text(record.get("owner_email")),
        _normalize_text(record.get("phone")),
    ]
    digest_input = "||".join(parts).encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"seen_fingerprints": [], "sent": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"seen_fingerprints": [], "sent": []}


def _save_state(path: Path, payload: dict[str, Any]) -> None:
    payload = {
        **payload,
        "updated_at": _utc_now(),
    }
    _atomic_write_json(path, payload)


def _select_candidates(
    rows: list[list[str]],
    *,
    batch_size: int,
    seen_fingerprints: set[str],
) -> tuple[list[dict[str, str]], int]:
    if not rows:
        return [], 0
    headers = [str(item).strip() for item in rows[0]]
    diff = compare_sheet_headers(headers, SHEETS_HEADERS)
    if diff["missing_headers"] or diff["extra_headers"] or not diff["order_matches"]:
        # The canonical production Leads tab should already match the schema exactly.
        raise RuntimeError("production Leads headers do not match canonical schema")

    candidates: list[dict[str, str]] = []
    duplicate_count = 0
    for row in rows[1:]:
        record = _row_to_record(headers, row)
        if _is_internal_row(record):
            continue
        if _normalize_text(record.get("qualification status")).lower() != "qualified":
            continue
        if not _normalize_text(record.get("owner_email")):
            continue
        fingerprint = _lead_fingerprint(record)
        if fingerprint in seen_fingerprints:
            duplicate_count += 1
            continue
        record["_fingerprint"] = fingerprint
        candidates.append(record)
        if len(candidates) >= batch_size:
            break
    return candidates, duplicate_count


def _clean_subject(record: dict[str, str], draft: dict[str, str]) -> str:
    return draft["subject"].strip()


def _clean_body(record: dict[str, str], draft: dict[str, str]) -> str:
    body = draft["body"].strip()
    body = re.sub(r"https?://(?:www\.)?calendly\.com/[^\s)>\]]+", "", body, flags=re.IGNORECASE)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def _render_preview(record: dict[str, str], subject: str, body: str) -> str:
    return "\n".join(
        [
            "## Lead Preview",
            f"- business: {record.get('business name') or 'n/a'}",
            f"- domain: {record.get('domain') or 'n/a'}",
            f"- email: {record.get('owner_email') or 'n/a'}",
            f"- qualification score: {record.get('score') or 'n/a'}",
            f"- qualification status: {record.get('qualification status') or 'n/a'}",
            "",
            "## Generated Subject",
            subject,
            "",
            "## Generated Body",
            body,
            "",
            "## Founder Approval",
            "Type APPROVE to send this lead or SKIP to block it.",
        ]
    )


def _prompt_founder_approval(record: dict[str, str], subject: str, body: str) -> bool:
    preview = _render_preview(record, subject, body)
    print(preview)
    if not sys.stdin.isatty():
        raise RuntimeError("founder approval requires an interactive terminal")
    response = input("Founder approval (APPROVE/SKIP): ").strip().upper()
    return response == "APPROVE"


def _sender_identity() -> tuple[str, str]:
    from_email = getenv("SENDGRID_FROM_EMAIL", "info@genesisai.systems")
    reply_to = from_email
    return from_email, reply_to


def _send_prospect_email(*, recipient: str, subject: str, body: str) -> dict[str, Any]:
    api_key = getenv("RESEND_API_KEY")
    from_email, reply_to = _sender_identity()
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is missing")

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": f"Genesis AI Systems <{from_email}>",
            "to": [recipient],
            "subject": subject,
            "html": body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>"),
            "text": body,
            "reply_to": reply_to,
        },
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(f"prospect send failed for {recipient}: {response.status_code} {response.text[:200]}")

    data = response.json()
    return {
        "recipient": recipient,
        "resend_id": data.get("id"),
        "from_email": from_email,
        "reply_to": reply_to,
        "provider_status": "accepted",
        "provider_response": {
            "status_code": response.status_code,
            "headers": {
                "date": response.headers.get("date"),
                "content_type": response.headers.get("content-type"),
                "request_id": response.headers.get("x-request-id"),
            },
            "body": data,
        },
        "auth_metadata": {
            "gmail_style_auth": "not available",
            "outlook_style_auth": "not available",
            "from_domain": from_email.split("@")[-1] if "@" in from_email else "",
            "reply_to": reply_to,
        },
        "reply_status": "pending",
        "bounce_status": "pending",
        "spam_complaint_status": "pending",
        "follow_up_due": "pending",
        "created_at": _utc_now(),
    }


def _write_artifact(summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    lines = [
        "# Prospect Pilot Delivery Evidence",
        "",
        f"Generated at: {_utc_now()}",
        "",
        "## Pilot Summary",
        f"- total attempted: {summary['total_attempted']}",
        f"- total sent: {summary['total_sent']}",
        f"- blocked by QA: {summary['blocked_by_qa']}",
        f"- duplicate blocked: {summary['duplicate_blocked']}",
        f"- provider accepted: {summary['provider_accepted']}",
        f"- immediate failures: {summary['immediate_failures']}",
        f"- second batch safe: {summary['second_batch_safe']}",
        "",
        "## Placeholder Follow-Up States",
        "- replied: pending",
        "- interested: pending",
        "- not now: pending",
        "- wrong contact: pending",
        "- bounced: pending",
        "- spam complaint: pending",
        "- follow-up due: pending",
        "",
        "## Delivery Records",
    ]
    for record in results:
        lines.append(f"- recipient: {record['recipient']}")
        lines.append(f"  - send timestamp: {record['created_at']}")
        lines.append(f"  - subject: {record['subject']}")
        lines.append(f"  - provider acceptance: {record['provider_status']}")
        lines.append(f"  - from address: {record['from_email']}")
        lines.append(f"  - reply-to: {record['reply_to']}")
        lines.append(f"  - auth metadata: {_safe_json_dumps(record.get('auth_metadata', {}))}")
        lines.append(f"  - reply status: {record['reply_status']}")
        lines.append(f"  - bounce placeholder: {record['bounce_status']}")
        lines.append(f"  - spam complaint placeholder: {record['spam_complaint_status']}")
    lines.extend(
        [
            "",
            "GLOBAL AUTO-SEND REMAINS PAUSED.",
            "ONLY FOUNDER-APPROVED MICRO-BATCH PILOT IS AUTHORIZED.",
        ]
    )
    PILOT_ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PILOT_ARTIFACT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the controlled founder-approved prospect pilot.")
    parser.add_argument(
        "--founder-pilot",
        action="store_true",
        help="Enable the controlled founder-approved micro-batch pilot.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Maximum number of leads to review; hard-capped at 5.",
    )
    parser.add_argument(
        "--spreadsheet-id",
        default=DEFAULT_LIVE_GOOGLE_SHEET_ID,
        help="Genesis operations workbook ID.",
    )
    parser.add_argument(
        "--service-account-file",
        default=str(DEFAULT_LIVE_SERVICE_ACCOUNT_FILE),
        help="Path to the Google service-account JSON file.",
    )
    parser.add_argument(
        "--openai-model",
        default=getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        help="Live OpenAI model for pilot draft generation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.founder_pilot:
        raise SystemExit("Use --founder-pilot to authorize the controlled pilot run.")

    if args.batch_size > DEFAULT_BATCH_SIZE:
        raise SystemExit(f"batch size is capped at {DEFAULT_BATCH_SIZE}")

    service_account_file = Path(args.service_account_file)
    rows = _read_sheet_rows(
        spreadsheet_id=args.spreadsheet_id,
        service_account_file=service_account_file,
        worksheet_name=PRODUCTION_SHEET_NAME,
    )
    if not rows:
        raise SystemExit("production Leads sheet is empty")

    headers = [str(item).strip() for item in rows[0]]
    diff = compare_sheet_headers(headers, SHEETS_HEADERS)
    if diff["missing_headers"] or diff["extra_headers"] or not diff["order_matches"]:
        raise SystemExit("production Leads headers do not match the canonical schema")

    state = _load_state(PILOT_STATE_PATH)
    seen_fingerprints = set(str(item) for item in state.get("seen_fingerprints", []))
    candidates, duplicate_count = _select_candidates(
        rows, batch_size=args.batch_size, seen_fingerprints=seen_fingerprints
    )

    draft_client = OpenAIDraftClient(model=args.openai_model)
    summary = {
        "total_attempted": 0,
        "total_sent": 0,
        "blocked_by_qa": 0,
        "duplicate_blocked": 0,
        "provider_accepted": 0,
        "immediate_failures": 0,
        "second_batch_safe": "NO",
    }
    sent_records: list[dict[str, Any]] = []
    for record in candidates:
        summary["total_attempted"] += 1
        fingerprint = record["_fingerprint"]
        draft = draft_client.generate(
            {
                "business_name": record.get("business name"),
                "owner_email": record.get("owner_email"),
                "industry": record.get("source") or "retail",
                "domain": record.get("domain"),
                "system_prompt": """
You write short cold outreach emails for Genesis AI Systems, a Detroit-based AI automation
company run by founder Trendell Fordham.

The audience is local Detroit small business owners.
Write like a real person, not a consultant.

Email rules:
- Subject line: specific to the business, under 8 words, no buzzwords
- Opening line: one sentence about a real problem their type of business faces
  (missed calls, after-hours inquiries, booking gaps, slow response times)
- Body: 2-3 short sentences max. What we do. What it means for them specifically.
- CTA: ask for 10 minutes this week. Nothing else.
- Sign off: Trendell Fordham, Genesis AI Systems, genesisai.systems, (586) 636-9550
- No Calendly links
- No placeholders like [Name] or [Business]
- No "synergies", "strategic partnership", "collaboration", "solutions"
- Plain English only

Write one email only. Return subject and body as JSON:
{"subject": "...", "body": "..."}
""".strip(),
            }
        )
        subject = _clean_subject(record, asdict(draft))
        body = _clean_body(record, asdict(draft))

        approved = _prompt_founder_approval(record, subject, body)
        if not approved:
            summary["blocked_by_qa"] += 1
            _append_ndjson(
                PILOT_EVIDENCE_PATH,
                {
                    "hook_name": "prospect_pilot_lead",
                    "status": "blocked_by_qa",
                    "lead_identifier": record.get("owner_email") or fingerprint,
                    "fingerprint": fingerprint,
                    "business_name": record.get("business name"),
                    "domain": record.get("domain"),
                    "qualification_score": record.get("score"),
                    "approval": "SKIP",
                    "reply_status": "pending",
                    "bounce_status": "pending",
                    "spam_complaint_status": "pending",
                    "follow_up_due": "pending",
                    "timestamp": _utc_now(),
                },
            )
            continue

        try:
            result = _send_prospect_email(
                recipient=record.get("owner_email", ""),
                subject=subject,
                body=body,
            )
        except Exception as exc:  # noqa: BLE001
            summary["immediate_failures"] += 1
            _append_ndjson(
                PILOT_EVIDENCE_PATH,
                {
                    "hook_name": "prospect_pilot_lead",
                    "status": "failed",
                    "lead_identifier": record.get("owner_email") or fingerprint,
                    "fingerprint": fingerprint,
                    "business_name": record.get("business name"),
                    "domain": record.get("domain"),
                    "qualification_score": record.get("score"),
                    "approval": "APPROVE",
                    "failure": str(exc),
                    "reply_status": "pending",
                    "bounce_status": "pending",
                    "spam_complaint_status": "pending",
                    "follow_up_due": "pending",
                    "timestamp": _utc_now(),
                },
            )
            continue

        summary["total_sent"] += 1
        summary["provider_accepted"] += 1
        state.setdefault("seen_fingerprints", []).append(fingerprint)
        state.setdefault("sent", []).append(
            {
                "fingerprint": fingerprint,
                "recipient": record.get("owner_email"),
                "resend_id": result.get("resend_id"),
                "sent_at": result.get("created_at"),
            }
        )
        _append_ndjson(
            PILOT_EVIDENCE_PATH,
            {
                "hook_name": "prospect_pilot_lead",
                "status": "sent",
                "lead_identifier": record.get("owner_email") or fingerprint,
                "fingerprint": fingerprint,
                "recipient": record.get("owner_email"),
                "business_name": record.get("business name"),
                "domain": record.get("domain"),
                "qualification_score": record.get("score"),
                "subject": subject,
                "provider_acceptance": result.get("provider_status"),
                "auth_metadata": result.get("auth_metadata"),
                "reply_status": result.get("reply_status"),
                "bounce_status": result.get("bounce_status"),
                "spam_complaint_status": result.get("spam_complaint_status"),
                "follow_up_due": result.get("follow_up_due"),
                "timestamp": _utc_now(),
            },
        )
        sent_records.append(
            {
                **result,
                "subject": subject,
                "recipient": record.get("owner_email"),
            }
        )

    summary["duplicate_blocked"] = duplicate_count
    summary["total_attempted"] = (
        summary["total_sent"]
        + summary["blocked_by_qa"]
        + summary["duplicate_blocked"]
        + summary["immediate_failures"]
    )
    summary["second_batch_safe"] = "YES" if summary["immediate_failures"] == 0 else "NO"

    _save_state(PILOT_STATE_PATH, state)
    _write_artifact(summary, sent_records)
    print(
        _safe_json_dumps(
            {
                "status": "success",
                "batch_size_cap": DEFAULT_BATCH_SIZE,
                "total_attempted": summary["total_attempted"],
                "total_sent": summary["total_sent"],
                "blocked_by_qa": summary["blocked_by_qa"],
                "duplicate_blocked": summary["duplicate_blocked"],
                "provider_accepted": summary["provider_accepted"],
                "immediate_failures": summary["immediate_failures"],
                "second_batch_safe": summary["second_batch_safe"],
                "artifact": str(PILOT_ARTIFACT_PATH),
                "auto_send_paused": AUTO_SEND_PAUSED_BY_DEFAULT,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
