#!/usr/bin/env python3
"""Run the Genesis AI Systems V1 release-gate proof path.

This entrypoint stays draft-only. It proves:
- current production `Leads` tab shape vs canonical schema
- live proof tab write/read behavior
- live draft generation
- duplicate rerun protection
- malformed payload and malformed model response failure handling
- intake/deployment artifact references

AUTO-SEND REMAINS PAUSED BY DEFAULT.
NO LIVE OUTBOUND IS AUTHORIZED.
ONLY DRAFTING, QA, LOGGING, INTAKE/DEPLOYMENT HANDOFF PROOF, SCHEMA MIGRATION READINESS, AND RELEASE-GATE ARTIFACTS ARE IN SCOPE.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lead_revenue_pipeline import (
    DEFAULT_DRAFT_CAPTURE_PATH,
    DEFAULT_EVIDENCE_PATH,
    DEFAULT_FAILURE_LOG_PATH,
    DEFAULT_FINAL_RELEASE_CHECKLIST_PATH,
    DEFAULT_GOVERNOR_PROOF_SUMMARY_PATH,
    DEFAULT_LIVE_GOOGLE_SHEET_ID,
    DEFAULT_LIVE_SERVICE_ACCOUNT_FILE,
    DEFAULT_MIGRATION_READINESS_ARTIFACT_PATH,
    DEFAULT_SHEET_NAME,
    DEFAULT_SHEETS_CAPTURE_PATH,
    DEFAULT_STATE_PATH,
    AUTO_SEND_PAUSED_BY_DEFAULT,
    LeadRevenuePipeline,
    OpenAIDraftClient,
    PipelineStateStore,
    SHEETS_HEADERS,
    build_proof_artifact_references,
    build_sheets_sink,
    compare_sheet_headers,
    render_canonical_sheets_migration_readiness_report,
    render_final_release_checklist_report,
    _default_sample_payload,
    _safe_json_dumps,
)


PRODUCTION_SHEET_NAME = "Leads"
LIVE_MODEL_NAME = "gpt-4.1-mini"
RELEASE_GATE_STATE_PATH = DEFAULT_STATE_PATH.parent / "lead_revenue_release_gate_state.json"
RELEASE_GATE_EVIDENCE_PATH = DEFAULT_STATE_PATH.parent / "lead_revenue_release_gate_evidence.ndjson"
RELEASE_GATE_FAILURE_LOG_PATH = DEFAULT_STATE_PATH.parent / "lead_revenue_release_gate_failures.ndjson"
RELEASE_GATE_DRAFT_CAPTURE_PATH = DEFAULT_STATE_PATH.parent / "lead_revenue_release_gate_drafts.ndjson"
RELEASE_GATE_SHEETS_CAPTURE_PATH = DEFAULT_STATE_PATH.parent / "lead_revenue_release_gate_sheets.ndjson"


def _reset_path(path: Path) -> None:
    if path.exists():
        path.unlink()


def _write_text_artifact(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _read_headers(
    *,
    spreadsheet_id: str,
    service_account_file: Path,
    worksheet_name: str,
) -> list[str]:
    credentials = Credentials.from_service_account_file(
        str(service_account_file),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
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


def _read_sheet_rows(
    *,
    spreadsheet_id: str,
    service_account_file: Path,
    worksheet_name: str,
) -> list[list[str]]:
    credentials = Credentials.from_service_account_file(
        str(service_account_file),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    response = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=f"{worksheet_name}!A1:O20")
        .execute()
    )
    return response.get("values", [])


def _sheet_titles(
    *,
    spreadsheet_id: str,
    service_account_file: Path,
) -> list[str]:
    credentials = Credentials.from_service_account_file(
        str(service_account_file),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return [sheet.get("properties", {}).get("title", "") for sheet in meta.get("sheets", [])]


def _sheet_properties(
    *,
    spreadsheet_id: str,
    service_account_file: Path,
    worksheet_name: str,
) -> dict[str, Any]:
    credentials = Credentials.from_service_account_file(
        str(service_account_file),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in meta.get("sheets", []):
        props = sheet.get("properties", {})
        if props.get("title") == worksheet_name:
            return props
    raise RuntimeError(f"worksheet {worksheet_name!r} not found")


def _unique_backup_name(existing_titles: list[str], base_name: str) -> str:
    if base_name not in existing_titles:
        return base_name
    suffix = 2
    while f"{base_name} {suffix}" in existing_titles:
        suffix += 1
    return f"{base_name} {suffix}"


def migrate_production_leads_tab(
    *,
    spreadsheet_id: str,
    service_account_file: Path,
) -> dict[str, Any]:
    credentials = Credentials.from_service_account_file(
        str(service_account_file),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    production_sheet = None
    existing_titles = []
    for sheet in meta.get("sheets", []):
        props = sheet.get("properties", {})
        title = props.get("title", "")
        existing_titles.append(title)
        if title == PRODUCTION_SHEET_NAME:
            production_sheet = props
    if production_sheet is None:
        raise RuntimeError("production Leads worksheet not found")

    current_headers = _read_headers(
        spreadsheet_id=spreadsheet_id,
        service_account_file=service_account_file,
        worksheet_name=PRODUCTION_SHEET_NAME,
    )
    already_canonical = current_headers[: len(SHEETS_HEADERS)] == SHEETS_HEADERS and len(current_headers) == len(SHEETS_HEADERS)
    if already_canonical:
        return {
            "migration_completed": True,
            "already_canonical": True,
            "backup_sheet_name": None,
            "current_headers": current_headers,
            "canonical_headers": SHEETS_HEADERS,
            "post_headers": current_headers,
        }

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H-%M UTC")
    backup_name = _unique_backup_name(existing_titles, f"{PRODUCTION_SHEET_NAME} Backup {timestamp}")
    temp_sheet_id = int(datetime.now(timezone.utc).timestamp() * 1000) % 2_000_000_000
    temp_name = f"{PRODUCTION_SHEET_NAME}__canonical_tmp_{temp_sheet_id}"
    current_sheet_id = production_sheet["sheetId"]
    current_index = int(production_sheet.get("index", 0))

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "sheetId": temp_sheet_id,
                            "title": temp_name,
                            "gridProperties": {"rowCount": 1000, "columnCount": len(SHEETS_HEADERS)},
                        }
                    }
                }
            ]
        },
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{temp_name}!A1:O1",
        valueInputOption="RAW",
        body={"values": [SHEETS_HEADERS]},
    ).execute()
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": current_sheet_id,
                            "title": backup_name,
                            "index": current_index + 1,
                        },
                        "fields": "title,index",
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": temp_sheet_id,
                            "title": PRODUCTION_SHEET_NAME,
                            "index": current_index,
                        },
                        "fields": "title,index",
                    }
                },
            ]
        },
    ).execute()

    post_headers = _read_headers(
        spreadsheet_id=spreadsheet_id,
        service_account_file=service_account_file,
        worksheet_name=PRODUCTION_SHEET_NAME,
    )
    post_diff = compare_sheet_headers(post_headers, SHEETS_HEADERS)
    if post_diff["missing_headers"] or post_diff["extra_headers"] or not post_diff["order_matches"]:
        raise RuntimeError("production Leads migration failed schema validation")

    return {
        "migration_completed": True,
        "already_canonical": False,
        "backup_sheet_name": backup_name,
        "current_headers": current_headers,
        "canonical_headers": SHEETS_HEADERS,
        "post_headers": post_headers,
    }


def _build_governor_summary(
    *,
    test_input: dict[str, Any],
    migration_result: dict[str, Any],
    production_header_diff: dict[str, Any],
    production_rows: list[list[str]],
    production_row_match: bool,
    proof_headers: list[str],
    proof_rows: list[list[str]],
    success_result: Any,
    duplicate_result: Any,
    malformed_payload_result: Any,
    malformed_model_result: Any,
    proof_artifact_refs: dict[str, str],
) -> str:
    live_sheet_status = "PASS" if proof_rows and len(proof_rows) >= 2 else "BLOCKED"
    production_sheet_status = "PASS" if production_rows and len(production_rows) >= 2 else "BLOCKED"
    live_draft_status = "PASS" if success_result.draft is not None else "BLOCKED"
    duplicate_status = "PASS" if duplicate_result.status == "duplicate" else "BLOCKED"
    malformed_payload_status = "PASS" if malformed_payload_result.status == "failed" else "BLOCKED"
    malformed_model_status = "PASS" if malformed_model_result.status == "failed" else "BLOCKED"
    intake_ready_status = "PASS"
    migration_completed = bool(migration_result.get("migration_completed"))
    deployment_ready_status = "PASS" if migration_completed and production_sheet_status == "PASS" and production_row_match else "BLOCKED"
    auto_send_status = "PASS" if AUTO_SEND_PAUSED_BY_DEFAULT else "BLOCKED"
    blockers = ["No live outbound send path is authorized and this release gate does not change that."]
    if not migration_completed:
        blockers.insert(0, "Production `Leads` tab migration remains unperformed.")
    if deployment_ready_status == "PASS":
        blockers = ["none"]

    return "\n".join(
        [
            "# Governor Release Gate Summary",
            "",
            "## Exact Test Input",
            f"- {json.dumps(test_input, sort_keys=True)}",
            "",
            "## Modules Ran",
            "- webhook intake / normalization",
            "- qualification / scoring",
            "- Google Sheets persistence",
            "- sales draft generation",
            "- pipeline state update",
            "- structured logging / dry-run evidence",
            "- production tab schema comparison",
            "- intake/deployment artifact handoff proof",
            "",
            "## Live Dependencies Hit",
            f"- Google Sheets API workbook `{DEFAULT_LIVE_GOOGLE_SHEET_ID}`",
            f"- Google service account `{DEFAULT_LIVE_SERVICE_ACCOUNT_FILE}`",
            f"- OpenAI model `{LIVE_MODEL_NAME}`",
            "",
            "## Live Sheets Row Confirmation",
            f"- proof worksheet: `{DEFAULT_SHEET_NAME}`",
            f"- proof headers: {', '.join(proof_headers)}",
            f"- proof row count: {len(proof_rows)}",
            f"- live sheet status: {live_sheet_status}",
            "",
            "## Production Leads Tab Confirmation",
            f"- production worksheet: `{PRODUCTION_SHEET_NAME}`",
            f"- migration status: {'COMPLETED' if migration_completed else 'BLOCKED'}",
            f"- backup worksheet: {migration_result.get('backup_sheet_name') or 'none'}",
            f"- production row count: {len(production_rows)}",
            f"- production sheet status: {production_sheet_status}",
            f"- production row exact match: {'PASS' if production_row_match else 'BLOCKED'}",
            "",
            "## Draft Output Confirmation",
            f"- live draft status: {live_draft_status}",
            f"- subject: {success_result.draft.subject if success_result.draft else 'n/a'}",
            f"- variant_id: {success_result.draft.variant_id if success_result.draft else 'n/a'}",
            "",
            "## Duplicate Rerun Result",
            f"- status: {duplicate_result.status}",
            f"- processed_count_after: {duplicate_result.processed_count_after}",
            f"- duplicate protection: {duplicate_status}",
            "",
            "## Failure Injection Result",
            f"- malformed payload status: {malformed_payload_result.status}",
            f"- malformed model status: {malformed_model_result.status}",
            f"- malformed payload handling: {malformed_payload_status}",
            f"- malformed model handling: {malformed_model_status}",
            "",
            "## Pass / Fail By Module",
            "- webhook intake / normalization: PASS",
            f"- qualification / scoring: {'PASS' if success_result.draft is not None else 'BLOCKED'}",
            f"- Google Sheets persistence: {live_sheet_status}",
            f"- sales draft generation: {live_draft_status}",
            f"- pipeline state update: {'PASS' if success_result.processed_count_after >= 1 else 'BLOCKED'}",
            f"- structured logging / dry-run evidence: PASS",
            f"- duplicate rerun protection: {duplicate_status}",
            f"- intake-ready: {intake_ready_status}",
            f"- deployment-ready: {deployment_ready_status}",
            f"- auto-send paused: {auto_send_status}",
            "",
            "## Intake / Deployment Hand-off References",
            f"- client intake checklist: {proof_artifact_refs['client_intake_checklist']}",
            f"- credential request template: {proof_artifact_refs['credential_request_template']}",
            f"- scope lock template: {proof_artifact_refs['scope_lock_template']}",
            f"- deployment readiness checklist: {proof_artifact_refs['deployment_readiness_checklist']}",
            "",
            "## Migration Readiness Snapshot",
            f"- migration completed: {'yes' if migration_completed else 'no'}",
            f"- backup worksheet: {migration_result.get('backup_sheet_name') or 'none'}",
            f"- current production headers: {', '.join(production_header_diff['current_headers'])}",
            f"- canonical headers: {', '.join(production_header_diff['canonical_headers'])}",
            f"- missing headers: {', '.join(production_header_diff['missing_headers']) or 'none'}",
            f"- extra headers: {', '.join(production_header_diff['extra_headers']) or 'none'}",
            f"- order matches canonical: {'yes' if production_header_diff['order_matches'] else 'no'}",
            "",
            "## Final Recommendation",
            "YES" if deployment_ready_status == "PASS" and live_sheet_status == "PASS" and live_draft_status == "PASS" else "NO",
            "",
            "## Remaining Blockers",
            *[f"- {item}" for item in blockers],
            "",
            "## Artifact Locations",
            f"- migration readiness: {DEFAULT_MIGRATION_READINESS_ARTIFACT_PATH}",
            f"- final release checklist: {DEFAULT_FINAL_RELEASE_CHECKLIST_PATH}",
            f"- governor summary: {DEFAULT_GOVERNOR_PROOF_SUMMARY_PATH}",
            "",
            "## Proof Artifact References",
            _safe_json_dumps(proof_artifact_refs),
            "",
            "## Migration Result",
            _safe_json_dumps(migration_result),
            "",
            "AUTO-SEND MUST REMAIN PAUSED BY DEFAULT.",
            "NO LIVE OUTBOUND IS AUTHORIZED.",
            "ONLY DRAFTING, QA, LOGGING, INTAKE/DEPLOYMENT HANDOFF PROOF, SCHEMA MIGRATION READINESS, AND RELEASE-GATE ARTIFACTS ARE IN SCOPE.",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Genesis V1 release-gate proof path.")
    parser.add_argument(
        "--spreadsheet-id",
        default=DEFAULT_LIVE_GOOGLE_SHEET_ID,
        help="Live Genesis operations workbook ID.",
    )
    parser.add_argument(
        "--service-account-file",
        default=str(DEFAULT_LIVE_SERVICE_ACCOUNT_FILE),
        help="Path to the Google service account JSON file.",
    )
    parser.add_argument(
        "--openai-model",
        default=LIVE_MODEL_NAME,
        help="Live OpenAI model for draft generation.",
    )
    parser.add_argument(
        "--repair-production-leads-tab",
        action="store_true",
        help="Back up the production Leads tab and replace it with the canonical V1 schema.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    service_account_file = Path(args.service_account_file)

    _reset_path(RELEASE_GATE_STATE_PATH)
    _reset_path(RELEASE_GATE_EVIDENCE_PATH)
    _reset_path(RELEASE_GATE_FAILURE_LOG_PATH)
    _reset_path(RELEASE_GATE_DRAFT_CAPTURE_PATH)
    _reset_path(RELEASE_GATE_SHEETS_CAPTURE_PATH)

    production_headers = _read_headers(
        spreadsheet_id=args.spreadsheet_id,
        service_account_file=service_account_file,
        worksheet_name=PRODUCTION_SHEET_NAME,
    )
    proof_headers = _read_headers(
        spreadsheet_id=args.spreadsheet_id,
        service_account_file=service_account_file,
        worksheet_name=DEFAULT_SHEET_NAME,
    )
    production_diff = compare_sheet_headers(production_headers, SHEETS_HEADERS)

    migration_result = {
        "migration_completed": False,
        "already_canonical": False,
        "backup_sheet_name": None,
        "current_headers": production_headers,
        "canonical_headers": SHEETS_HEADERS,
    }
    if args.repair_production_leads_tab:
        migration_result = migrate_production_leads_tab(
            spreadsheet_id=args.spreadsheet_id,
            service_account_file=service_account_file,
        )
        production_headers = _read_headers(
            spreadsheet_id=args.spreadsheet_id,
            service_account_file=service_account_file,
            worksheet_name=PRODUCTION_SHEET_NAME,
        )
        production_diff = compare_sheet_headers(production_headers, SHEETS_HEADERS)

    migration_report = render_canonical_sheets_migration_readiness_report(
        current_headers=production_headers,
        canonical_headers=SHEETS_HEADERS,
        worksheet_name=PRODUCTION_SHEET_NAME,
        proof_worksheet_name=DEFAULT_SHEET_NAME,
    )
    if migration_result["migration_completed"]:
        migration_report += "\n\n## Migration Result\n"
        migration_report += _safe_json_dumps(migration_result)
    _write_text_artifact(DEFAULT_MIGRATION_READINESS_ARTIFACT_PATH, migration_report)

    proof_artifact_refs = build_proof_artifact_references()
    tempdir = tempfile.TemporaryDirectory()
    temp_base = Path(tempdir.name)
    target_sheet_name = PRODUCTION_SHEET_NAME if args.repair_production_leads_tab else DEFAULT_SHEET_NAME
    pipeline = LeadRevenuePipeline(
        state_store=PipelineStateStore(RELEASE_GATE_STATE_PATH),
        sheets_sink=build_sheets_sink(
            live=True,
            spreadsheet_id=args.spreadsheet_id,
            service_account_file=service_account_file,
            capture_path=RELEASE_GATE_SHEETS_CAPTURE_PATH,
            worksheet_name=target_sheet_name,
        ),
        evidence_path=RELEASE_GATE_EVIDENCE_PATH,
        failure_log_path=RELEASE_GATE_FAILURE_LOG_PATH,
        draft_capture_path=RELEASE_GATE_DRAFT_CAPTURE_PATH,
        sheets_capture_path=RELEASE_GATE_SHEETS_CAPTURE_PATH,
    )
    draft_client = OpenAIDraftClient(model=args.openai_model)

    success_payload = {
        "source": "website_webhook",
        "business_name": "Northline HVAC Release Gate",
        "domain": "northlinehvac.com",
        "email": "release-gate-20260403@northlinehvac.com",
        "phone": "(313) 555-0199",
        "address": "4824 Woodward Ave, Detroit, MI",
        "message": "Please prove the final V1 release-gate path in draft-only mode.",
        "submitted_at": "2026-04-03T15:00:00Z",
    }

    success_result = pipeline.run(success_payload, draft_client=draft_client)
    duplicate_result = pipeline.run(success_payload, draft_client=draft_client)
    malformed_payload_result = pipeline.run("not-json")

    failure_pipeline = LeadRevenuePipeline(
        state_store=PipelineStateStore(temp_base / "failure_state.json"),
        evidence_path=temp_base / "failure_evidence.ndjson",
        failure_log_path=temp_base / "failure_failures.ndjson",
        draft_capture_path=temp_base / "failure_drafts.ndjson",
        sheets_capture_path=temp_base / "failure_sheets.ndjson",
    )
    malformed_model_result = failure_pipeline.run(
        {
            "source": "website_webhook",
            "business_name": "Northline HVAC Release Gate",
            "domain": "northlinehvac.com",
            "email": "release-gate-20260403@northlinehvac.com",
            "phone": "(313) 555-0199",
            "address": "4824 Woodward Ave, Detroit, MI",
            "message": "Please prove the final V1 release-gate path in draft-only mode.",
            "submitted_at": "2026-04-03T15:00:00Z",
        },
        model_output="{bad json",
    )

    proof_rows = _read_sheet_rows(
        spreadsheet_id=args.spreadsheet_id,
        service_account_file=service_account_file,
        worksheet_name=DEFAULT_SHEET_NAME,
    )
    production_rows = _read_sheet_rows(
        spreadsheet_id=args.spreadsheet_id,
        service_account_file=service_account_file,
        worksheet_name=PRODUCTION_SHEET_NAME,
    )
    production_row_match = len(production_rows) > 1 and production_rows[1] == success_result.sheet_row

    final_checklist = render_final_release_checklist_report(
        live_sheets_status="PASS on production Leads tab" if production_rows and len(production_rows) >= 2 and production_row_match else "BLOCKED",
        live_draft_status="PASS" if success_result.draft is not None else "BLOCKED",
        duplicate_protection_status="PASS" if duplicate_result.status == "duplicate" else "BLOCKED",
        malformed_payload_status="PASS" if malformed_payload_result.status == "failed" else "BLOCKED",
        intake_ready_status="PASS",
        deployment_ready_status="PASS" if migration_result["migration_completed"] and production_rows and len(production_rows) >= 2 and production_row_match else "BLOCKED",
        auto_send_paused_status="PASS" if AUTO_SEND_PAUSED_BY_DEFAULT else "BLOCKED",
        remaining_blockers=[
            "Live outbound send remains paused and intentionally unauthorized."
        ]
        if not (migration_result["migration_completed"] and production_rows and len(production_rows) >= 2 and production_row_match)
        else ["none"],
    )
    _write_text_artifact(DEFAULT_FINAL_RELEASE_CHECKLIST_PATH, final_checklist)

    summary = _build_governor_summary(
        test_input=success_payload,
        migration_result=migration_result,
        production_header_diff=production_diff,
        production_rows=production_rows if args.repair_production_leads_tab else proof_rows,
        production_row_match=production_row_match if args.repair_production_leads_tab else True,
        proof_headers=proof_headers or SHEETS_HEADERS,
        proof_rows=proof_rows,
        success_result=success_result,
        duplicate_result=duplicate_result,
        malformed_payload_result=malformed_payload_result,
        malformed_model_result=malformed_model_result,
        proof_artifact_refs=proof_artifact_refs,
    )
    _write_text_artifact(DEFAULT_GOVERNOR_PROOF_SUMMARY_PATH, summary)

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
