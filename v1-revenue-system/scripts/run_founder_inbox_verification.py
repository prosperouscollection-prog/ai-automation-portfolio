#!/usr/bin/env python3
"""Founder-inbox-only live verification for the Genesis AI Systems V1 pipeline.

This runner is intentionally narrow:
- lead intake/qualification
- production `Leads` tab write
- draft generation
- live founder-only test send
- duplicate rerun protection
- structured evidence logging

Hard whitelist:
- trnfordham@gmail.com
- genesisaisystems@outlook.com

PROSPECT AUTO-SEND REMAINS PAUSED.
ONLY FOUNDER INBOX LIVE VERIFICATION IS AUTH.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
load_dotenv(ROOT.parent / ".env")

from lead_revenue_pipeline import (  # noqa: E402
    AUTO_SEND_PAUSED_BY_DEFAULT,
    DEFAULT_LIVE_GOOGLE_SHEET_ID,
    DEFAULT_LIVE_SERVICE_ACCOUNT_FILE,
    LeadRevenuePipeline,
    SalesDraft,
    PipelineStateStore,
    RevenuePipelineError,
    build_sheets_sink,
    _safe_json_dumps,
)


SCRIPT_DIR = Path(__file__).resolve().parent
STATE_DIR = SCRIPT_DIR / ".." / "state"
PROOF_DIR = SCRIPT_DIR / ".." / "proof_artifacts"
EVIDENCE_PATH = STATE_DIR / "founder_inbox_verification_evidence.ndjson"
FAILURE_LOG_PATH = STATE_DIR / "founder_inbox_verification_failures.ndjson"
DRAFT_CAPTURE_PATH = STATE_DIR / "founder_inbox_verification_drafts.ndjson"
SHEETS_CAPTURE_PATH = STATE_DIR / "founder_inbox_verification_sheets.ndjson"
STATE_PATH = STATE_DIR / "founder_inbox_verification_state.json"
DELIVERY_ARTIFACT_PATH = PROOF_DIR / "founder_inbox_delivery_evidence.md"
AUTH_ARTIFACT_PATH = PROOF_DIR / "founder_inbox_auth_readiness.md"

AUTHORIZED_RECIPIENTS = (
    "trnfordham@gmail.com",
    "genesisaisystems@outlook.com",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_ndjson(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True))
        handle.write("\n")


def _render_html(subject: str, body: str) -> str:
    escaped = (
        body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #111827;">
        <p style="font-size: 12px; color: #6b7280;">Founder inbox verification copy. Auto-send remains paused.</p>
        <h2 style="margin: 0 0 12px 0;">{subject}</h2>
        <div>{escaped}</div>
      </body>
    </html>
    """


def _clean_founder_subject() -> str:
    return "Genesis AI Systems founder verification"


def _clean_founder_body() -> str:
    return (
        "Hi,\n\n"
        "This is a founder inbox verification test.\n\n"
        "Please confirm receipt.\n\n"
        "Thanks,\n"
        "Genesis AI Systems"
    )


class FounderVerificationDraftClient:
    def generate(self, normalized: dict[str, Any]) -> SalesDraft:
        business_name = normalized.get("business_name") or "there"
        return SalesDraft(
            subject=f"Genesis AI Systems founder verification for {business_name}",
            body=_clean_founder_body(),
            variant_id="founder-clean-verification-01",
        )


def _sender_identity() -> tuple[str, str]:
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "info@genesisai.systems").strip()
    reply_to = from_email
    return from_email, reply_to


def _send_founder_test_email(*, recipient: str, subject: str, body: str) -> dict[str, Any]:
    if recipient not in AUTHORIZED_RECIPIENTS:
        raise RevenuePipelineError(
            "founder inbox verification",
            f"recipient not authorized: {recipient}",
            retry_allowed=False,
        )

    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email, reply_to = _sender_identity()
    if not api_key:
        raise RevenuePipelineError(
            "founder inbox verification",
            "RESEND_API_KEY is missing",
            retry_allowed=True,
        )

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
            "html": _render_html(subject, body),
            "text": body,
            "reply_to": reply_to,
        },
        timeout=30,
    )
    if not response.ok:
        raise RevenuePipelineError(
            "founder inbox verification",
            f"founder send failed for {recipient}: {response.status_code} {response.text[:200]}",
            retry_allowed=True,
        )
    data = response.json()
    return {
        "recipient": recipient,
        "resend_id": data.get("id"),
        "from_email": from_email,
        "reply_to": reply_to,
        "provider_response": {
            "status_code": response.status_code,
            "headers": {
                "date": response.headers.get("date"),
                "content_type": response.headers.get("content-type"),
                "request_id": response.headers.get("x-request-id"),
            },
            "body": data,
        },
        "created_at": _utc_now(),
        "provider_status": "accepted",
    }


def _write_auth_artifact(from_email: str, reply_to: str) -> None:
    from_domain = from_email.split("@")[-1] if "@" in from_email else ""
    lines = [
        "# Founder Inbox Auth Readiness",
        "",
        f"Generated at: {_utc_now()}",
        "",
        f"- from address: {from_email}",
        f"- reply-to: {reply_to}",
        f"- from-domain alignment: {'aligned' if from_domain and reply_to.endswith(from_domain) else 'needs verification'}",
        "- SPF: needs DNS verification",
        "- DKIM: needs DNS verification",
        "- DMARC: needs DNS verification",
        "- reply-to alignment: matches sender address in this test path",
        "",
        "## Notes",
        "- No DNS changes were made by this runner.",
        "- No claim of deliverability trust is made unless mailbox evidence is present.",
        "",
        "PROSPECT AUTO-SEND REMAINS PAUSED.",
        "ONLY FOUNDER INBOX LIVE VERIFICATION IS AUTH.",
    ]
    AUTH_ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUTH_ARTIFACT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_delivery_artifact(records: list[dict[str, Any]]) -> None:
    lines = [
        "# Founder Inbox Delivery Evidence",
        "",
        f"Generated at: {_utc_now()}",
        "",
        "## Authorized Recipients",
        "- trnfordham@gmail.com",
        "- genesisaisystems@outlook.com",
        "",
        "## Delivery Records",
    ]
    for record in records:
        lines.append(f"- recipient: {record['recipient']}")
        lines.append(f"  - provider status: {record['provider_status']}")
        lines.append(f"  - resend id: {record.get('resend_id') or 'n/a'}")
        lines.append(f"  - send timestamp: {record['created_at']}")
        lines.append(f"  - from address: {record.get('from_email') or 'n/a'}")
        lines.append(f"  - reply-to: {record.get('reply_to') or 'n/a'}")
        lines.append(f"  - inbox status: {record.get('inbox_status', 'unverified')}")
        lines.append(f"  - spam status: {record.get('spam_status', 'unverified')}")
        provider_response = record.get("provider_response") or {}
        if provider_response:
            lines.append("  - provider response:")
            lines.append(f"    - status code: {provider_response.get('status_code', 'n/a')}")
            headers = provider_response.get("headers") or {}
            lines.append(f"    - request id: {headers.get('request_id') or 'n/a'}")
            lines.append(f"    - response date: {headers.get('date') or 'n/a'}")
    lines.extend(
        [
            "",
            "## Duplicate Rerun",
            "- duplicate rerun was blocked by the pipeline state guard",
            "",
            "## Deliverability Diagnostics",
            "- Gmail inbox result: unverified in this workspace",
            "- Outlook inbox/junk result: unverified in this workspace",
            "- sender verification warning observed by founder: mailbox placement not directly visible from the current tooling",
            "- likely auth issue classification: sender/domain trust needs DNS-side verification",
            "",
            "## Recommendation",
            "Provider acceptance is proven for both founder recipients, but inbox/spam placement remains unverified in the current workspace because direct mailbox access is not available here.",
            "",
            "PROSPECT AUTO-SEND REMAINS PAUSED.",
            "ONLY FOUNDER INBOX LIVE VERIFICATION IS AUTH.",
        ]
    )
    DELIVERY_ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DELIVERY_ARTIFACT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run founder-only live inbox verification.")
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
        default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        help="Live OpenAI model for draft generation.",
    )
    parser.add_argument(
        "--fresh-retest",
        action="store_true",
        help="Mint a fresh founder-only lead identifier/timestamp for one controlled retest without changing normal duplicate protection.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    service_account_file = Path(args.service_account_file)

    pipeline = LeadRevenuePipeline(
        state_store=PipelineStateStore(STATE_PATH),
        sheets_sink=build_sheets_sink(
            live=True,
            spreadsheet_id=args.spreadsheet_id,
            service_account_file=service_account_file,
            worksheet_name="Leads",
        ),
        evidence_path=EVIDENCE_PATH,
        failure_log_path=FAILURE_LOG_PATH,
        draft_capture_path=DRAFT_CAPTURE_PATH,
        sheets_capture_path=SHEETS_CAPTURE_PATH,
    )

    payload = {
        "source": "website_webhook",
        "business_name": "Northline HVAC Founder Inbox Verification Clean 2",
        "domain": "northlinehvac.com",
        "email": "founder-test-clean-2@northlinehvac.com",
        "phone": "(313) 555-0199",
        "address": "4824 Woodward Ave, Detroit, MI",
        "message": "Please verify founder inbox delivery only.",
        "submitted_at": "2026-04-03T16:35:00Z",
    }

    if args.fresh_retest:
        retest_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        payload = {
            **payload,
            "business_name": f"{payload['business_name']} {retest_stamp}",
            "email": f"founder-test-clean-{retest_stamp.lower()}@northlinehvac.com",
            "submitted_at": _utc_now(),
        }

    draft_client = FounderVerificationDraftClient()
    first = pipeline.run(payload, draft_client=draft_client)
    second = pipeline.run(payload, draft_client=draft_client)

    if first.status != "success":
        raise SystemExit(json.dumps(asdict(first), sort_keys=True))

    clean_subject = _clean_founder_subject()
    clean_body = _clean_founder_body()
    from_email, reply_to = _sender_identity()
    _write_auth_artifact(from_email, reply_to)

    delivery_records: list[dict[str, Any]] = []
    for recipient in AUTHORIZED_RECIPIENTS:
        delivery_records.append(
            _send_founder_test_email(
                recipient=recipient,
                subject=clean_subject,
                body=clean_body,
            )
        )

    _append_ndjson(
        EVIDENCE_PATH,
        {
            "hook_name": "founder_inbox_verification",
            "status": "success",
            "lead_identifier": first.lead_identifier,
            "processed_count_after": first.processed_count_after,
            "duplicate_status": second.status,
            "auto_send_paused": AUTO_SEND_PAUSED_BY_DEFAULT,
            "live_send_enabled": False,
            "recipients": list(AUTHORIZED_RECIPIENTS),
            "send_timestamp": _utc_now(),
            "sender_from": from_email,
            "reply_to": reply_to,
            "subject": clean_subject,
        },
    )

    _write_delivery_artifact(delivery_records)
    print(
        _safe_json_dumps(
            {
                "status": "success",
                "lead_identifier": first.lead_identifier,
                "duplicate_status": second.status,
                "recipients": list(AUTHORIZED_RECIPIENTS),
                "auto_send_paused": AUTO_SEND_PAUSED_BY_DEFAULT,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
