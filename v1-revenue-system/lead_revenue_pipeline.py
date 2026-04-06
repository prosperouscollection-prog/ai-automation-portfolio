#!/usr/bin/env python3
"""Safe end-to-end lead revenue path for Genesis AI Systems V1.

This module is intentionally small and explicit. It does not auto-send outbound
messages. It only:
- normalizes a lead payload
- qualifies/scored the lead
- prepares a sales draft
- appends a locked Google Sheets row mapping
- updates local pipeline state
- emits dry-run evidence and failure records

AUTO-SEND REMAINS PAUSED BY DEFAULT.
NO LIVE OUTBOUND IS AUTHORIZED.
ONLY DRAFTING, QA, LOGGING, AND DRY-RUN HARDENING ARE IN SCOPE.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent
STATE_DIR = SCRIPT_DIR / "state"
DEFAULT_STATE_PATH = STATE_DIR / "lead_revenue_state.json"
DEFAULT_EVIDENCE_PATH = STATE_DIR / "lead_revenue_dry_run_evidence.ndjson"
DEFAULT_FAILURE_LOG_PATH = STATE_DIR / "lead_revenue_failures.ndjson"
DEFAULT_SHEETS_CAPTURE_PATH = STATE_DIR / "lead_revenue_sheet_capture.ndjson"
DEFAULT_DRAFT_CAPTURE_PATH = STATE_DIR / "lead_revenue_draft_capture.ndjson"
DEFAULT_SHEET_NAME = "Lead Revenue Proof"
DEFAULT_PROOF_ARTIFACTS_DIR = SCRIPT_DIR / "proof_artifacts"
DEFAULT_MIGRATION_READINESS_ARTIFACT_PATH = (
    DEFAULT_PROOF_ARTIFACTS_DIR / "canonical_sheets_migration_readiness.md"
)
DEFAULT_FINAL_RELEASE_CHECKLIST_PATH = (
    DEFAULT_PROOF_ARTIFACTS_DIR / "final_release_checklist.md"
)
DEFAULT_GOVERNOR_PROOF_SUMMARY_PATH = (
    DEFAULT_PROOF_ARTIFACTS_DIR / "governor_release_gate_summary.md"
)
DEFAULT_LIVE_GOOGLE_SHEET_ID = "1ORElwpEZN23jzPR9v_-Wu_qVG2g8xKGIkw_g41JoAPw"
DEFAULT_LIVE_SERVICE_ACCOUNT_FILE = Path(
    "/Users/genesisai/Downloads/n8n-integration-491503-9e7222cb0016.json"
)
AUTO_SEND_PAUSED_BY_DEFAULT = True
LIVE_SEND_ENV_FLAG = "GENESIS_ALLOW_LIVE_SEND"
FOUNDERS_ONLY_FLAG = "GENESIS_FOUNDERS_LIVE_SEND_APPROVAL"

HOOK_NAME = "lead_revenue_dry_run"
PIPELINE_STAGE_CAPTURED = "CAPTURED"
PIPELINE_STAGE_NORMALIZED = "NORMALIZED"
PIPELINE_STAGE_QUALIFIED = "QUALIFIED"
PIPELINE_STAGE_DRAFT_READY = "DRAFT_READY"
PIPELINE_STAGE_DRY_RUN_LOGGED = "DRY_RUN_LOGGED"


@dataclass(frozen=True)
class SheetColumn:
    key: str
    header: str


SHEETS_SCHEMA: tuple[SheetColumn, ...] = (
    SheetColumn("date_timestamp", "date/timestamp"),
    SheetColumn("source", "source"),
    SheetColumn("business_name", "business name"),
    SheetColumn("domain", "domain"),
    SheetColumn("owner_email", "owner_email"),
    SheetColumn("phone", "phone"),
    SheetColumn("address", "address"),
    SheetColumn("score", "score"),
    SheetColumn("qualification_status", "qualification status"),
    SheetColumn("outreach_subject", "outreach subject"),
    SheetColumn("outreach_body", "outreach body"),
    SheetColumn("variant_id", "variant ID"),
    SheetColumn("pipeline_stage", "pipeline stage"),
    SheetColumn("next_action", "next action"),
    SheetColumn("last_updated", "last updated"),
)

SHEETS_HEADERS = [column.header for column in SHEETS_SCHEMA]
SHEETS_SCHEMA_KEYS = {column.key for column in SHEETS_SCHEMA}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    text = str(value).strip()
    return text or None


def _normalize_email(value: Any) -> str | None:
    text = _normalize_text(value)
    if text is None:
        return None
    lowered = text.lower()
    return lowered if "@" in lowered else None


def _normalize_domain(value: Any) -> str | None:
    text = _normalize_text(value)
    if text is None:
        return None
    lowered = text.lower()
    if lowered.startswith("http://"):
        lowered = lowered[len("http://") :]
    if lowered.startswith("https://"):
        lowered = lowered[len("https://") :]
    if lowered.startswith("www."):
        lowered = lowered[len("www.") :]
    return lowered.strip("/") or None


def _safe_json_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=True)


def _stable_fingerprint(*parts: str | None) -> str:
    digest_input = "||".join(part or "" for part in parts)
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


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


def _append_ndjson(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=True))
        handle.write("\n")


def _render_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_proof_artifact_references() -> dict[str, str]:
    return {
        "client_intake_checklist": str(DEFAULT_PROOF_ARTIFACTS_DIR / "client_intake_checklist.md"),
        "credential_request_template": str(DEFAULT_PROOF_ARTIFACTS_DIR / "credential_request_template.md"),
        "scope_lock_template": str(DEFAULT_PROOF_ARTIFACTS_DIR / "scope_lock_template.md"),
        "deployment_readiness_checklist": str(
            DEFAULT_PROOF_ARTIFACTS_DIR / "deployment_readiness_checklist.md"
        ),
        "governor_evidence_pack": str(DEFAULT_PROOF_ARTIFACTS_DIR / "governor_evidence_pack.md"),
        "canonical_sheets_migration_readiness": str(DEFAULT_MIGRATION_READINESS_ARTIFACT_PATH),
        "final_release_checklist": str(DEFAULT_FINAL_RELEASE_CHECKLIST_PATH),
        "governor_release_gate_summary": str(DEFAULT_GOVERNOR_PROOF_SUMMARY_PATH),
    }


def render_canonical_sheets_migration_readiness_report(
    *,
    current_headers: list[str],
    canonical_headers: list[str] | None = None,
    worksheet_name: str = "Leads",
    proof_worksheet_name: str = DEFAULT_SHEET_NAME,
) -> str:
    canonical = canonical_headers or SHEETS_HEADERS
    current_set = set(current_headers)
    canonical_set = set(canonical)
    missing = [header for header in canonical if header not in current_set]
    extra = [header for header in current_headers if header not in canonical_set]
    order_mismatch = current_headers[: len(canonical)] != canonical

    steps = [
        "Review the current production `Leads` tab headers against the canonical V1 schema.",
        "Do not mutate the production tab unless the explicit `--repair-production-leads-tab` flag is supplied.",
        f"Keep the isolated proof tab `{proof_worksheet_name}` as the active V1 proof path.",
        "If migration is approved later, back up the production tab, write the canonical header row, and re-read the tab to confirm exact placement.",
        "Re-run duplicate protection and one controlled proof lead after any migration action.",
    ]
    risks = [
        "Overwriting the production tab without a backup could disrupt the older 14-column workflow.",
        "Column order drift can silently misplace revenue-critical data if the canonical header row is not enforced.",
        "Any migration of the production tab should be treated as a separate controlled change from the proof tab path.",
    ]

    return "\n".join(
        [
            "# Canonical Sheets Migration Readiness",
            "",
            f"Production worksheet inspected: `{worksheet_name}`",
            f"Proof worksheet preserved: `{proof_worksheet_name}`",
            "",
            "## Current Columns",
            _render_bullets(current_headers),
            "",
            "## Canonical Columns",
            _render_bullets(canonical),
            "",
            "## Mismatches",
            _render_bullets(
                [
                    f"Missing in production: {', '.join(missing) if missing else 'none'}",
                    f"Extra in production: {', '.join(extra) if extra else 'none'}",
                    f"Order matches canonical: {'no' if order_mismatch else 'yes'}",
                ]
            ),
            "",
            "## Exact Migration Steps",
            _render_bullets(steps),
            "",
            "## Risks",
            _render_bullets(risks),
            "",
            "## Safe Flag",
            "The production `Leads` tab is not mutated automatically.",
            "A future explicit migration may use `--repair-production-leads-tab` after operator approval.",
            "",
            "AUTO-SEND MUST REMAIN PAUSED BY DEFAULT.",
            "NO LIVE OUTBOUND IS AUTHORIZED.",
            "ONLY DRAFTING, QA, LOGGING, INTAKE/DEPLOYMENT HANDOFF PROOF, SCHEMA MIGRATION READINESS, AND RELEASE-GATE ARTIFACTS ARE IN SCOPE.",
        ]
    )


def render_final_release_checklist_report(
    *,
    live_sheets_status: str,
    live_draft_status: str,
    duplicate_protection_status: str,
    malformed_payload_status: str,
    intake_ready_status: str,
    deployment_ready_status: str,
    auto_send_paused_status: str,
    remaining_blockers: list[str],
) -> str:
    blockers = remaining_blockers or ["none"]
    return "\n".join(
        [
            "# Final V1 Release Checklist",
            "",
            f"- Live Sheets proof status: {live_sheets_status}",
            f"- Live draft proof status: {live_draft_status}",
            f"- Duplicate protection status: {duplicate_protection_status}",
            f"- Malformed payload handling status: {malformed_payload_status}",
            f"- Intake-ready status: {intake_ready_status}",
            f"- Deployment-ready status: {deployment_ready_status}",
            f"- Auto-send paused status: {auto_send_paused_status}",
            "",
            "## Remaining Blockers",
            _render_bullets(blockers),
            "",
            "AUTO-SEND MUST REMAIN PAUSED BY DEFAULT.",
            "NO LIVE OUTBOUND IS AUTHORIZED.",
            "ONLY DRAFTING, QA, LOGGING, INTAKE/DEPLOYMENT HANDOFF PROOF, SCHEMA MIGRATION READINESS, AND RELEASE-GATE ARTIFACTS ARE IN SCOPE.",
        ]
    )


def read_sheet_headers(
    *,
    spreadsheet_id: str,
    service_account_file: Path,
    worksheet_name: str,
) -> list[str]:
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_file(str(service_account_file), scopes=scopes)
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    response = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{worksheet_name}!A1:O1")
        .execute()
    )
    values = response.get("values", [])
    if not values:
        return []
    return [str(item).strip() for item in values[0]]


def compare_sheet_headers(
    current_headers: list[str],
    canonical_headers: list[str] | None = None,
) -> dict[str, Any]:
    canonical = canonical_headers or SHEETS_HEADERS
    current_set = set(current_headers)
    canonical_set = set(canonical)
    return {
        "current_headers": current_headers,
        "canonical_headers": canonical,
        "missing_headers": [header for header in canonical if header not in current_set],
        "extra_headers": [header for header in current_headers if header not in canonical_set],
        "order_matches": current_headers[: len(canonical)] == canonical,
    }


@dataclass(frozen=True)
class FailureRecord:
    module: str
    reason: str
    lead_identifier: str | None
    timestamp: str
    retry_allowed: bool


@dataclass(frozen=True)
class SalesDraft:
    subject: str
    body: str
    variant_id: str


@dataclass(frozen=True)
class NormalizedLead:
    lead_identifier: str
    date_timestamp: str
    source: str
    business_name: str
    domain: str
    owner_email: str
    phone: str
    address: str
    score: int
    qualification_status: str
    outreach_subject: str
    outreach_body: str
    variant_id: str
    pipeline_stage: str
    next_action: str
    last_updated: str
    processed_count_before: int
    processed_count_after: int
    fingerprint: str

    def to_sheet_row(self) -> list[str]:
        row = {
            "date/timestamp": self.date_timestamp,
            "source": self.source,
            "business name": self.business_name,
            "domain": self.domain,
            "owner_email": self.owner_email,
            "phone": self.phone,
            "address": self.address,
            "score": str(self.score),
            "qualification status": self.qualification_status,
            "outreach subject": self.outreach_subject,
            "outreach body": self.outreach_body,
            "variant ID": self.variant_id,
            "pipeline stage": self.pipeline_stage,
            "next action": self.next_action,
            "last updated": self.last_updated,
        }
        return [row[column.header] for column in SHEETS_SCHEMA]

    def to_sheet_record(self) -> dict[str, Any]:
        return {
            "date/timestamp": self.date_timestamp,
            "source": self.source,
            "business name": self.business_name,
            "domain": self.domain,
            "owner_email": self.owner_email,
            "phone": self.phone,
            "address": self.address,
            "score": self.score,
            "qualification status": self.qualification_status,
            "outreach subject": self.outreach_subject,
            "outreach body": self.outreach_body,
            "variant ID": self.variant_id,
            "pipeline stage": self.pipeline_stage,
            "next action": self.next_action,
            "last updated": self.last_updated,
        }


@dataclass(frozen=True)
class DryRunResult:
    status: str
    lead_identifier: str | None
    fingerprint: str | None
    processed_count_before: int
    processed_count_after: int
    pipeline_stage_before: str | None
    pipeline_stage_after: str | None
    sheet_row: list[str] | None
    draft: SalesDraft | None
    failure: FailureRecord | None
    evidence_path: str
    failure_log_path: str
    auto_send_paused: bool
    live_send_enabled: bool


class SheetsSink(Protocol):
    def append_row(self, row: list[str]) -> None: ...


class FileSheetsSink:
    """Capture would-be Sheets writes in an NDJSON file for dry-run proof."""

    def __init__(self, capture_path: Path) -> None:
        self._capture_path = capture_path

    def append_row(self, row: list[str]) -> None:
        _append_ndjson(
            self._capture_path,
            {
                "hook_name": "google_sheets_append_row",
                "sheet_name": DEFAULT_SHEET_NAME,
                "headers": SHEETS_HEADERS,
                "row": row,
                "checked_at": _utc_now(),
            },
        )


class LiveGoogleSheetsSink:
    """Append rows to the live Genesis operations workbook.

    The sink validates the live header row against the centralized schema before
    appending so column drift fails loudly instead of silently misplacing data.
    """

    def __init__(
        self,
        *,
        spreadsheet_id: str,
        service_account_file: Path,
        worksheet_name: str = DEFAULT_SHEET_NAME,
    ) -> None:
        self._spreadsheet_id = spreadsheet_id
        self._service_account_file = service_account_file
        self._worksheet_name = worksheet_name
        self._service = self._build_service()

    def _build_service(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(
            str(self._service_account_file),
            scopes=scopes,
        )
        return build("sheets", "v4", credentials=credentials, cache_discovery=False)

    def _metadata(self) -> dict[str, Any]:
        return (
            self._service.spreadsheets()
            .get(spreadsheetId=self._spreadsheet_id)
            .execute()
        )

    def _worksheet_exists(self) -> bool:
        meta = self._metadata()
        for sheet in meta.get("sheets", []):
            props = sheet.get("properties", {})
            if props.get("title") == self._worksheet_name:
                return True
        return False

    def _create_worksheet(self) -> None:
        self._service.spreadsheets().batchUpdate(
            spreadsheetId=self._spreadsheet_id,
            body={
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": self._worksheet_name,
                                "gridProperties": {"rowCount": 1000, "columnCount": 15},
                            }
                        }
                    }
                ]
            },
        ).execute()
        self._service.spreadsheets().values().update(
            spreadsheetId=self._spreadsheet_id,
            range=f"{self._worksheet_name}!A1:O1",
            valueInputOption="RAW",
            body={"values": [[column.header for column in SHEETS_SCHEMA]]},
        ).execute()

    def _validate_headers(self) -> list[str]:
        response = (
            self._service.spreadsheets()
            .values()
            .get(
                spreadsheetId=self._spreadsheet_id,
                range=f"{self._worksheet_name}!A1:O1",
            )
            .execute()
        )
        values = response.get("values", [])
        if not values:
            raise RevenuePipelineError(
                "google sheets persistence",
                f"live worksheet {self._worksheet_name} has no header row",
                retry_allowed=True,
            )
        headers = [str(item).strip() for item in values[0]]
        expected = [column.header for column in SHEETS_SCHEMA]
        if headers[: len(expected)] != expected:
            raise RevenuePipelineError(
                "google sheets persistence",
                "live worksheet headers do not match the centralized schema",
                retry_allowed=True,
            )
        return headers

    def append_row(self, row: list[str]) -> None:
        if not self._worksheet_exists():
            self._create_worksheet()
        headers = self._validate_headers()
        response = (
            self._service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self._spreadsheet_id,
                range=f"{self._worksheet_name}!A:O",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [row]},
                includeValuesInResponse=True,
                responseValueRenderOption="UNFORMATTED_VALUE",
            )
            .execute()
        )
        updated_range = response.get("updates", {}).get("updatedRange", "")
        _append_ndjson(
            STATE_DIR / "lead_revenue_live_sheets_evidence.ndjson",
            {
                "hook_name": "google_sheets_live_append",
                "spreadsheet_id": self._spreadsheet_id,
                "worksheet_name": self._worksheet_name,
                "headers": headers,
                "row": row,
                "updated_range": updated_range,
                "checked_at": _utc_now(),
            },
        )


class FailingSheetsSink:
    """Simulate a Sheets auth/write failure."""

    def __init__(self, reason: str, module: str = "google sheets persistence") -> None:
        self.reason = reason
        self.module = module

    def append_row(self, row: list[str]) -> None:  # noqa: ARG002
        raise RevenuePipelineError(self.module, self.reason, retry_allowed=True)


class RevenuePipelineError(Exception):
    def __init__(
        self,
        module: str,
        reason: str,
        lead_identifier: str | None = None,
        retry_allowed: bool = False,
    ) -> None:
        super().__init__(reason)
        self.module = module
        self.reason = reason
        self.lead_identifier = lead_identifier
        self.retry_allowed = retry_allowed


class PipelineStateStore:
    """Persist processed lead fingerprints and processed_count safely."""

    def __init__(self, path: Path = DEFAULT_STATE_PATH) -> None:
        self._path = path

    def load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {
                "processed_count": 0,
                "last_updated": None,
                "seen_fingerprints": [],
                "last_lead_identifier": None,
                "pipeline_stage": None,
            }
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RevenuePipelineError(
                "pipeline state",
                f"state file malformed: {exc.msg}",
                retry_allowed=True,
            ) from exc
        if not isinstance(payload, dict):
            raise RevenuePipelineError(
                "pipeline state",
                "state file malformed: root JSON value must be an object",
                retry_allowed=True,
            )
        payload.setdefault("processed_count", 0)
        payload.setdefault("seen_fingerprints", [])
        payload.setdefault("last_updated", None)
        payload.setdefault("last_lead_identifier", None)
        payload.setdefault("pipeline_stage", None)
        return payload

    def is_duplicate(self, fingerprint: str) -> bool:
        state = self.load()
        return fingerprint in set(state.get("seen_fingerprints", []))

    def update_after_success(self, *, lead_identifier: str, fingerprint: str, pipeline_stage: str) -> dict[str, Any]:
        state = self.load()
        seen = list(state.get("seen_fingerprints", []))
        if fingerprint not in seen:
            seen.append(fingerprint)
        processed_count = int(state.get("processed_count", 0) or 0) + 1
        updated = {
            "processed_count": processed_count,
            "last_updated": _utc_now(),
            "seen_fingerprints": seen,
            "last_lead_identifier": lead_identifier,
            "pipeline_stage": pipeline_stage,
        }
        _atomic_write_json(self._path, updated)
        return updated


def _coerce_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        try:
            loaded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RevenuePipelineError(
                "webhook intake",
                f"payload malformed: {exc.msg}",
                retry_allowed=True,
            ) from exc
        if not isinstance(loaded, dict):
            raise RevenuePipelineError(
                "webhook intake",
                "payload malformed: root JSON value must be an object",
                retry_allowed=True,
            )
        return loaded
    raise RevenuePipelineError(
        "webhook intake",
        f"payload malformed: expected object, got {type(payload).__name__}",
        retry_allowed=True,
    )


def normalize_lead_payload(payload: Any) -> dict[str, Any]:
    """Normalize webhook payloads into a strict internal shape."""

    data = _coerce_payload(payload)
    lead_identifier = (
        _normalize_text(data.get("lead_id"))
        or _normalize_text(data.get("id"))
        or _normalize_text(data.get("email"))
        or _normalize_text(data.get("owner_email"))
        or _normalize_text(data.get("business_name"))
    )
    source = _normalize_text(data.get("source")) or "webhook"
    business_name = (
        _normalize_text(data.get("business_name"))
        or _normalize_text(data.get("business"))
        or _normalize_text(data.get("company_name"))
    )
    domain = _normalize_domain(data.get("domain") or data.get("website"))
    owner_email = _normalize_email(data.get("owner_email") or data.get("email"))
    phone = _normalize_text(data.get("phone") or data.get("phone_number"))
    address = _normalize_text(data.get("address") or data.get("location"))
    message = _normalize_text(data.get("message") or data.get("inquiry") or data.get("details"))
    submitted_at = _normalize_text(data.get("submitted_at") or data.get("timestamp")) or _utc_now()

    fingerprint = _stable_fingerprint(source, business_name, domain, owner_email, phone)
    lead_identifier = lead_identifier or fingerprint[:12]

    return {
        "lead_identifier": lead_identifier,
        "source": source,
        "business_name": business_name,
        "domain": domain,
        "owner_email": owner_email,
        "phone": phone,
        "address": address,
        "message": message,
        "submitted_at": submitted_at,
        "fingerprint": fingerprint,
        "raw": data,
    }


def qualify_lead(normalized: dict[str, Any]) -> tuple[int, str]:
    """Rule-based qualification that avoids model ambiguity for the dry-run path."""

    score = 0
    if normalized.get("business_name"):
        score += 25
    if normalized.get("owner_email"):
        score += 25
    if normalized.get("phone"):
        score += 15
    if normalized.get("address"):
        score += 10
    if normalized.get("domain"):
        score += 10
    if normalized.get("message"):
        score += 15

    if not normalized.get("owner_email") or not normalized.get("business_name"):
        status = "needs_follow_up"
    elif score >= 80:
        status = "qualified"
    elif score >= 55:
        status = "review"
    else:
        status = "unqualified"
    return min(score, 100), status


def _strip_code_fences(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def parse_draft_model_output(model_output: str) -> SalesDraft:
    """Parse model JSON safely. Invalid JSON is a hard failure, not a silent fallback."""

    cleaned = _strip_code_fences(model_output)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RevenuePipelineError(
            "sales draft generation",
            f"model output invalid JSON: {exc.msg}",
            retry_allowed=True,
        ) from exc

    if not isinstance(payload, dict):
        raise RevenuePipelineError(
            "sales draft generation",
            "model output invalid JSON: root value must be an object",
            retry_allowed=True,
        )

    subject = _normalize_text(payload.get("subject"))
    body = _normalize_text(payload.get("body"))
    variant_id = _normalize_text(payload.get("variant_id") or payload.get("variantID")) or "model-variant-1"

    if not subject or not body:
        raise RevenuePipelineError(
            "sales draft generation",
            "model output missing required subject/body fields",
            retry_allowed=True,
        )

    return SalesDraft(subject=subject, body=body, variant_id=variant_id)


def generate_sales_draft(normalized: dict[str, Any], model_output: str | None = None) -> SalesDraft:
    """Create a founder-review draft only.

    No live send code exists in this path. If a live send flag is present, it is
    still ignored by design. This module only returns a draft for review.
    """

    if model_output:
        return parse_draft_model_output(model_output)

    business_name = normalized.get("business_name") or "there"
    owner_email = normalized.get("owner_email") or ""
    subject = "Thanks for reaching out to Genesis AI Systems"
    body = (
        f"Hi {business_name},\n\n"
        "Thanks for contacting Genesis AI Systems!\n\n"
        "I'm Trendell Fordham, founder of Genesis AI Systems.\n"
        "I build done-for-you AI automation systems for local businesses starting at $500.\n\n"
        "Book a free 15-minute demo:\n"
        "calendly.com/genesisai-info-ptmt/free-ai-demo-call\n\n"
        "Or reply with any questions.\n\n"
        "Trendell Fordham\n"
        "Founder, Genesis AI Systems\n"
        "(313) 400-2575\n"
        "info@genesisai.systems\n"
        "genesisai.systems\n"
    )
    if owner_email:
        body += f"\nLead email preserved: {owner_email}\n"
    return SalesDraft(subject=subject, body=body, variant_id="draft-only-template-v1")


def _build_failure_record(error: RevenuePipelineError, lead_identifier: str | None) -> FailureRecord:
    return FailureRecord(
        module=error.module,
        reason=error.reason,
        lead_identifier=lead_identifier or error.lead_identifier,
        timestamp=_utc_now(),
        retry_allowed=error.retry_allowed,
    )


def _append_failure(path: Path, record: FailureRecord) -> None:
    _append_ndjson(path, asdict(record))


class LeadRevenuePipeline:
    """Coordinate the dry-run-safe revenue path end to end."""

    def __init__(
        self,
        *,
        state_store: PipelineStateStore | None = None,
        sheets_sink: SheetsSink | None = None,
        evidence_path: Path = DEFAULT_EVIDENCE_PATH,
        failure_log_path: Path = DEFAULT_FAILURE_LOG_PATH,
        draft_capture_path: Path = DEFAULT_DRAFT_CAPTURE_PATH,
        sheets_capture_path: Path = DEFAULT_SHEETS_CAPTURE_PATH,
    ) -> None:
        self.state_store = state_store or PipelineStateStore()
        self.sheets_sink = sheets_sink or FileSheetsSink(sheets_capture_path)
        self.evidence_path = evidence_path
        self.failure_log_path = failure_log_path
        self.draft_capture_path = draft_capture_path

    @property
    def live_send_enabled(self) -> bool:
        return bool(os.getenv(LIVE_SEND_ENV_FLAG, "").strip()) and bool(
            os.getenv(FOUNDERS_ONLY_FLAG, "").strip()
        )

    def run(
        self,
        payload: Any,
        model_output: str | None = None,
        draft_client: OpenAIDraftClient | None = None,
    ) -> DryRunResult:
        raw_state = self.state_store.load()
        processed_before = int(raw_state.get("processed_count", 0) or 0)
        pipeline_stage_before = _normalize_text(raw_state.get("pipeline_stage"))

        try:
            normalized = normalize_lead_payload(payload)
            lead_identifier = normalized["lead_identifier"]
            fingerprint = normalized["fingerprint"]
            missing_required = [
                field
                for field in ("business_name", "owner_email")
                if not normalized.get(field)
            ]
            if missing_required:
                raise RevenuePipelineError(
                    "qualification/scoring",
                    f"missing required lead fields: {', '.join(missing_required)}",
                    lead_identifier=lead_identifier,
                    retry_allowed=True,
                )
            if self.state_store.is_duplicate(fingerprint):
                result = DryRunResult(
                    status="duplicate",
                    lead_identifier=lead_identifier,
                    fingerprint=fingerprint,
                    processed_count_before=processed_before,
                    processed_count_after=processed_before,
                    pipeline_stage_before=pipeline_stage_before,
                    pipeline_stage_after=pipeline_stage_before,
                    sheet_row=None,
                    draft=None,
                    failure=FailureRecord(
                        module="duplicate lead protection",
                        reason="duplicate lead rerun blocked",
                        lead_identifier=lead_identifier,
                        timestamp=_utc_now(),
                        retry_allowed=False,
                    ),
                    evidence_path=str(self.evidence_path),
                    failure_log_path=str(self.failure_log_path),
                    auto_send_paused=AUTO_SEND_PAUSED_BY_DEFAULT,
                    live_send_enabled=self.live_send_enabled,
                )
                self._write_result(result)
                return result

            score, qualification_status = qualify_lead(normalized)
            if draft_client is not None:
                try:
                    draft = draft_client.generate(normalized)
                except RevenuePipelineError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    raise RevenuePipelineError(
                        "sales draft generation",
                        f"live model request failed: {exc}",
                        lead_identifier=lead_identifier,
                        retry_allowed=True,
                    ) from exc
            else:
                draft = generate_sales_draft(normalized, model_output=model_output)
            sheet_row = self._build_sheet_row(normalized, score, qualification_status, draft)

            self.sheets_sink.append_row(sheet_row)
            _append_ndjson(
                self.draft_capture_path,
                {
                    "hook_name": "sales_draft_generated",
                    "lead_identifier": lead_identifier,
                    "variant_id": draft.variant_id,
                    "subject": draft.subject,
                    "body": draft.body,
                    "checked_at": _utc_now(),
                    "live_send_enabled": self.live_send_enabled,
                    "auto_send_paused": AUTO_SEND_PAUSED_BY_DEFAULT,
                },
            )

            updated_state = self.state_store.update_after_success(
                lead_identifier=lead_identifier,
                fingerprint=fingerprint,
                pipeline_stage=PIPELINE_STAGE_DRY_RUN_LOGGED,
            )
            processed_after = int(updated_state.get("processed_count", processed_before))
            result = DryRunResult(
                status="success",
                lead_identifier=lead_identifier,
                fingerprint=fingerprint,
                processed_count_before=processed_before,
                processed_count_after=processed_after,
                pipeline_stage_before=pipeline_stage_before,
                pipeline_stage_after=PIPELINE_STAGE_DRY_RUN_LOGGED,
                sheet_row=sheet_row,
                draft=draft,
                failure=None,
                evidence_path=str(self.evidence_path),
                failure_log_path=str(self.failure_log_path),
                auto_send_paused=AUTO_SEND_PAUSED_BY_DEFAULT,
                live_send_enabled=self.live_send_enabled,
            )
            self._write_result(result)
            return result
        except RevenuePipelineError as error:
            failure = _build_failure_record(error, locals().get("lead_identifier"))
            _append_failure(self.failure_log_path, failure)
            result = DryRunResult(
                status="failed",
                lead_identifier=failure.lead_identifier,
                fingerprint=locals().get("fingerprint"),
                processed_count_before=processed_before,
                processed_count_after=processed_before,
                pipeline_stage_before=pipeline_stage_before,
                pipeline_stage_after=pipeline_stage_before,
                sheet_row=None,
                draft=None,
                failure=failure,
                evidence_path=str(self.evidence_path),
                failure_log_path=str(self.failure_log_path),
                auto_send_paused=AUTO_SEND_PAUSED_BY_DEFAULT,
                live_send_enabled=self.live_send_enabled,
            )
            self._write_result(result)
            return result

    def _build_sheet_row(
        self,
        normalized: dict[str, Any],
        score: int,
        qualification_status: str,
        draft: SalesDraft,
    ) -> list[str]:
        record = {
            "date/timestamp": normalized.get("submitted_at") or _utc_now(),
            "source": normalized.get("source") or "webhook",
            "business name": normalized.get("business_name") or "",
            "domain": normalized.get("domain") or "",
            "owner_email": normalized.get("owner_email") or "",
            "phone": normalized.get("phone") or "",
            "address": normalized.get("address") or "",
            "score": str(score),
            "qualification status": qualification_status,
            "outreach subject": draft.subject,
            "outreach body": draft.body,
            "variant ID": draft.variant_id,
            "pipeline stage": PIPELINE_STAGE_DRAFT_READY,
            "next action": "founder_review_draft",
            "last updated": _utc_now(),
        }
        return [record[column.header] for column in SHEETS_SCHEMA]

    def _write_result(self, result: DryRunResult) -> None:
        _append_ndjson(
            self.evidence_path,
            {
                "hook_name": HOOK_NAME,
                "checked_at": _utc_now(),
                "status": result.status,
                "lead_identifier": result.lead_identifier,
                "fingerprint": result.fingerprint,
                "processed_count_before": result.processed_count_before,
                "processed_count_after": result.processed_count_after,
                "pipeline_stage_before": result.pipeline_stage_before,
                "pipeline_stage_after": result.pipeline_stage_after,
                "sheet_row": result.sheet_row,
                "draft_present": result.draft is not None,
                "failure": asdict(result.failure) if result.failure else None,
                "auto_send_paused": result.auto_send_paused,
                "live_send_enabled": result.live_send_enabled,
                "next_action": "dry_run_only",
            },
        )


class OpenAIDraftClient:
    """Generate structured outreach drafts through the live OpenAI API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    def generate(self, normalized: dict[str, Any]) -> SalesDraft:
        business_name = normalized.get("business_name") or "there"
        owner_email = normalized.get("owner_email") or ""
        industry = normalized.get("industry") or "retail"
        domain = normalized.get("domain") or ""
        custom_system_prompt = _normalize_text(normalized.get("system_prompt"))
        if custom_system_prompt:
            prompt = (
                "Write one email only.\n"
                "Return subject and body as JSON.\n"
                f"Business name: {business_name}\n"
                f"Owner email: {owner_email}\n"
                f"Industry: {industry}\n"
                f"Domain: {domain}\n"
            )
            system_prompt = custom_system_prompt
        else:
            message = normalized.get("message") or ""
            prompt = (
                "Return only valid JSON with keys subject, body, and variant_id.\n"
                "Draft a founder-reviewed outbound email for Genesis AI Systems.\n"
                "Constraints:\n"
                "- draft only; no send language\n"
                "- preserve the founder-led close tone\n"
                "- include the Calendly link\n"
                "- keep the body concise and professional\n"
                "- variant_id must be a short stable string\n"
                f"Business: {business_name}\n"
                f"Email: {owner_email}\n"
                f"Message: {message}\n"
            )
            system_prompt = "You write safe draft-only sales emails as JSON."
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        return parse_draft_model_output(content)


def build_sheets_sink(
    *,
    live: bool,
    spreadsheet_id: str | None = None,
    service_account_file: Path | None = None,
    capture_path: Path = DEFAULT_SHEETS_CAPTURE_PATH,
    worksheet_name: str = DEFAULT_SHEET_NAME,
) -> SheetsSink:
    if live:
        return LiveGoogleSheetsSink(
            spreadsheet_id=spreadsheet_id or DEFAULT_LIVE_GOOGLE_SHEET_ID,
            service_account_file=service_account_file or DEFAULT_LIVE_SERVICE_ACCOUNT_FILE,
            worksheet_name=worksheet_name,
        )
    return FileSheetsSink(capture_path)


def load_payload_from_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RevenuePipelineError(
            "webhook intake",
            f"payload file unreadable: {exc.strerror or exc.__class__.__name__}",
            retry_allowed=True,
        ) from exc


def _default_sample_payload() -> dict[str, Any]:
    return {
        "source": "website_webhook",
        "business_name": "Northline HVAC",
        "domain": "northlinehvac.com",
        "email": "owner@northlinehvac.com",
        "phone": "(313) 555-0199",
        "address": "4824 Woodward Ave, Detroit, MI",
        "message": "We need help responding to website leads faster.",
        "submitted_at": "2026-04-03T14:00:00Z",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a dry-run-safe lead revenue path.")
    parser.add_argument("--payload-file", help="Path to a JSON payload file.")
    parser.add_argument("--payload-json", help="Inline JSON payload.")
    parser.add_argument("--model-output-json", help="Inline model output JSON for draft parsing.")
    parser.add_argument(
        "--use-live-model",
        action="store_true",
        help="Use the live OpenAI draft generation path.",
    )
    parser.add_argument(
        "--use-live-sheets",
        action="store_true",
        help="Append to the live Google Sheets workbook instead of file capture.",
    )
    parser.add_argument(
        "--google-sheet-id",
        default=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", DEFAULT_LIVE_GOOGLE_SHEET_ID),
        help="Live Google Sheets workbook ID.",
    )
    parser.add_argument(
        "--google-service-account-file",
        default=os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_JSON", str(DEFAULT_LIVE_SERVICE_ACCOUNT_FILE)
        ),
        help="Path to the Google service account JSON file.",
    )
    parser.add_argument(
        "--openai-model",
        default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        help="OpenAI model name for live draft generation.",
    )
    parser.add_argument("--state-file", help="Path to the pipeline state JSON.")
    parser.add_argument("--evidence-file", help="Path to the dry-run evidence NDJSON.")
    parser.add_argument("--failure-log-file", help="Path to the failure log NDJSON.")
    parser.add_argument("--sheets-capture-file", help="Path to the Sheets capture NDJSON.")
    parser.add_argument("--draft-capture-file", help="Path to the draft capture NDJSON.")
    parser.add_argument(
        "--simulate-sheets-failure",
        action="store_true",
        help="Simulate a Sheets auth/write failure.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state_path = Path(args.state_file) if args.state_file else DEFAULT_STATE_PATH
    evidence_path = Path(args.evidence_file) if args.evidence_file else DEFAULT_EVIDENCE_PATH
    failure_log_path = Path(args.failure_log_file) if args.failure_log_file else DEFAULT_FAILURE_LOG_PATH
    sheets_capture_path = (
        Path(args.sheets_capture_file) if args.sheets_capture_file else DEFAULT_SHEETS_CAPTURE_PATH
    )
    draft_capture_path = (
        Path(args.draft_capture_file) if args.draft_capture_file else DEFAULT_DRAFT_CAPTURE_PATH
    )

    if args.simulate_sheets_failure:
        sheets_sink: SheetsSink = FailingSheetsSink("simulated Sheets auth/write failure")
    else:
        sheets_sink = build_sheets_sink(
            live=args.use_live_sheets,
            spreadsheet_id=args.google_sheet_id,
            service_account_file=Path(args.google_service_account_file),
            capture_path=sheets_capture_path,
        )

    draft_client = OpenAIDraftClient(model=args.openai_model) if args.use_live_model else None

    pipeline = LeadRevenuePipeline(
        state_store=PipelineStateStore(state_path),
        sheets_sink=sheets_sink,
        evidence_path=evidence_path,
        failure_log_path=failure_log_path,
        draft_capture_path=draft_capture_path,
        sheets_capture_path=sheets_capture_path,
    )

    if args.payload_json:
        payload = args.payload_json
    elif args.payload_file:
        payload = load_payload_from_file(Path(args.payload_file))
    else:
        payload = _default_sample_payload()

    result = pipeline.run(
        payload,
        model_output=args.model_output_json,
        draft_client=draft_client,
    )
    print(_safe_json_dumps(asdict(result)))
    return 0 if result.status in {"success", "duplicate"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
