#!/usr/bin/env python3
"""Sales Agent — Genesis AI Systems.

Queued no-send autonomy mode.

Reads eligible HOT leads from Google Sheets, drafts personalized outreach via
Claude Haiku using controlled variation, and sends a founder review prompt to
Telegram. No email delivery is allowed in this workflow. Valid leads are queued
for founder review, logged, and capped at 3 per run.
"""

from __future__ import annotations

import json
import hashlib
import os
import sys
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

DETROIT = ZoneInfo("America/Detroit")

import requests
from dotenv import load_dotenv

load_dotenv()

# Shared notification helpers
from notify import telegram_notify
from lead_generator_agent import CHAIN_EXCLUSION_KEYWORDS

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from email_acquisition import EmailAcquisitionEngine, normalize_owner_email  # noqa: E402

# Outreach approval gate
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "v1-revenue-system"))
from approval_flow import ApprovalFlow, ApprovalStatus, ActionType

try:
    import anthropic as _anthropic
except ImportError:
    _anthropic = None

HUBSPOT_INDUSTRY_MAP = {
    "restaurant": "FOOD_BEVERAGES",
    "dental": "HEALTH_WELLNESS_AND_FITNESS",
    "hvac": "CONSTRUCTION",
    "salon": "COSMETICS",
    "real_estate": "REAL_ESTATE",
    "retail": "RETAIL",
}

QUEUE_TAB_NAME = "Founder Review Queue"
OUTREACH_LOG_TAB_NAME = "Outreach Log"
FAILSAFE_TAB_NAME = "FAILSAFE_LOG"
CAP_LIMIT = 3
WORKFLOW_MODE = "QUEUED_NO_SEND_AUTONOMY"

QUEUE_HEADERS = [
    "run_id",
    "queued_at",
    "lead_id",
    "business_name",
    "owner_email",
    "priority",
    "reason_selected",
    "recommended_draft",
    "variant_metadata",
    "pass_metadata",
    "terminal_state",
]

OUTREACH_LOG_HEADERS = [
    "run_id",
    "timestamp",
    "lead_id",
    "business_name",
    "filter_result",
    "priority",
    "queue_result",
    "terminal_state",
    "log_write_result",
    "idempotency_key",
]

FAILSAFE_HEADERS = [
    "run_id",
    "timestamp",
    "lead_id",
    "business_name",
    "failure_reason",
    "serialized_payload",
    "log_write_result",
]

DIGEST_FILENAME_PREFIX = "founder_morning_digest_"
DIGEST_PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
DIGEST_ANOMALY_LABELS = {
    "fail_safe_used": "fail-safe used",
    "summary_integrity_mismatch": "summary_integrity mismatch",
    "callback_ambiguity": "callback ambiguity",
    "queue_corruption_detected": "queue corruption detected",
    "founder_stop_blocked_run": "founder stop blocked run",
    "CAP_BREACH_BLOCKED": "CAP_BREACH_BLOCKED",
    "log_persistence_failure": "log persistence failure",
    "timeout_unresolved": "timeout unresolved count > 0",
    "total_errors": "total_errors > 0",
}

# Sheets column indices (0-based) written by Lead Generator
# A=date B=industry C=name D=primary_domain E=phone F=address
# G=employees H=yelp_rating I=yelp_reviews J=score K=reason
# L=recommended_product M=yelp_url N=outreach_email_template
# O=notified P=owner_email (enriched contact address)
COL = {
    "date": 0, "industry": 1, "name": 2, "domain": 3, "phone": 4,
    "address": 5, "employees": 6, "yelp_rating": 7, "yelp_reviews": 8,
    "score": 9, "reason": 10, "product": 11, "yelp_url": 12,
    "email_template": 13, "notified": 14, "owner_email": 15,
}

# Five opening styles per category — variant = hash(business) % 5
# Each entry is a brief instruction for how to open the email.
HOOK_VARIANTS: dict[str, list[str]] = {
    "restaurant": [
        "Open with a question about what happens when someone tries to book a table during a busy service and nobody picks up the phone.",
        "Open with a quick observation: most Detroit restaurants lose reservations they never knew they missed.",
        "Open with a short scenario — someone drives by, decides to call ahead for a table, gets no answer, and goes somewhere else.",
    ],
    "dental": [
        "Open with a question about what happens when a patient calls to book an appointment after the office closes.",
        "Open with an observation about how dental offices lose new patients not because of their work but because of missed calls.",
        "Open with a short scenario: a new patient searches for a dentist, calls after hours, nobody answers, they call the next one on the list.",
    ],
    "hvac": [
        "Open with a question about what happens when an emergency call comes in late on a Friday night.",
        "Open with a blunt observation: HVAC contractors miss jobs because they miss calls, not because they lack skill.",
        "Open with a short scenario — a homeowner's heat goes out at 10pm, they call three companies, the first one to respond gets the job.",
    ],
    "salon": [
        "Open with a question about how many booking calls they miss when they're in the middle of a cut.",
        "Open with a short observation: most salons still take bookings by phone, which means every unanswered call is a missed appointment.",
        "Open with a scenario — someone tries to book on a Saturday afternoon, calls go unanswered, they book at another salon.",
    ],
    "real_estate": [
        "Open with a question about what happens when a buyer calls at 9pm and nobody follows up until the next morning.",
        "Open with a short observation: in real estate, the first agent to respond usually wins the client.",
        "Open with a scenario — a buyer submits an online inquiry, waits two hours, and signs with whoever called first.",
    ],
    "retail": [
        "Open with a question about what happens when a customer calls after hours to ask if something's in stock.",
        "Open with an observation about how retail shops lose customers over simple unanswered questions.",
        "Open with a scenario — a customer wants to check hours or availability, can't reach anyone, and orders online instead.",
    ],
}

DEFAULT_HOOKS = [
    "Open with a question about what happens when a customer tries to reach them and nobody answers.",
    "Open with a short observation about local businesses that lose customers over missed calls.",
    "Open with a brief scenario showing a customer going elsewhere because they couldn't reach them.",
]

# LEAK — 2 framings (industry-agnostic; prompt provides industry context)
LEAK_VARIANTS = [
    "Gently note that most businesses in this industry don't have a reliable way to catch every incoming inquiry, especially outside peak hours. Be observational, never accusatory.",
    "Observationally note that the leads they lose aren't from bad service — they're from calls and messages that come in when nobody's available to respond.",
]

# OUTCOME — 2 emphases
OUTCOME_VARIANTS = [
    "State one grounded result: responding to every inquiry within minutes means more booked appointments and fewer lost opportunities. No inflated claims.",
    "State one grounded result: catching after-hours calls and texts means booking jobs that competitors miss entirely. Keep it concrete.",
]

# PROOF — 2 framings (truthful only — no fabricated case studies or numbers)
PROOF_VARIANTS = [
    "Briefly mention that you built this for Detroit local businesses specifically, and it handles the exact type of calls their industry gets. Do not fabricate any statistics or client names.",
    "Briefly mention that the system runs in the background — it doesn't replace their team, it just catches what their team can't get to. Do not invent case studies or numbers.",
]

# MICRO-CTA — 2 styles
CTA_VARIANTS = [
    "Ask if they'd have 10 minutes for a quick call this week to see if it even makes sense for their business.",
    "Ask if they'd have 10 minutes to walk through how it works for a business like theirs.",
]

EMAIL_SIGNATURE = (
    "Trendell Fordham\n"
    "Founder | Genesis AI Systems\n"
    "genesisai.systems\n"
    "Detroit, MI\n"
    "(586) 636-9550"
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECT9_STATE_DIR = REPO_ROOT / "project9-sales-agent" / "state"
DEFAULT_FOUNDERS_STOP_PATH = PROJECT9_STATE_DIR / "founder_stop.json"
DEFAULT_PROJECT9_LAUNCH_STATE_PATH = (
    REPO_ROOT / "project9-sales-agent" / "state" / "outbound_launch_state.json"
)
ALLOWED_OUTBOUND_LAUNCH_MODES = {"LIVE_ALLOWED"}
LAUNCH_STATE_ARTIFACT_NAME = "outbound-launch-state-current"
FIRST_10_EVENT_FEED_PATH = (
    REPO_ROOT / "project9-sales-agent" / "state" / "outbound_first_10_send_events.ndjson"
)
LAUNCH_STATE_RUNTIME_PATH = (
    REPO_ROOT / "project9-sales-agent" / "state" / "outbound_launch_state_runtime.json"
)


@dataclass
class Lead:
    business: str
    domain: str
    phone: str
    address: str
    industry: str
    score: str
    yelp_rating: str
    sheet_row: int
    owner_email: str = ""    # canonical owner_email from col P if available
    email_source: str = ""   # "sheets" when provided by the Lead Generator
    lead_id: str = ""
    email_confidence: str = ""
    email_source_type: str = ""
    email_source_reference: str = ""
    person_match_basis: str = ""
    verification_notes: str = ""
    rejection_reason: str = ""

    @property
    def email(self) -> str:
        return self.owner_email

    @email.setter
    def email(self, value: str) -> None:
        self.owner_email = value


class SalesAgent:
    """Reads HOT leads from Sheets, drafts via Claude with variation, sends a
    founder review prompt, and writes queue/log evidence. No live send path."""

    def __init__(self) -> None:
        self.hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        self.service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT", "").strip()
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.run_id = os.getenv(
            "PROJECT9_SALES_AGENT_RUN_ID",
            datetime.now(DETROIT).strftime("%Y%m%d_%H%M%S"),
        )
        self.started_at = time.time()
        self.no_send_invoked = False
        self.workflow_mode = WORKFLOW_MODE
        self.launch_state_path = Path(
            os.getenv(
                "PROJECT9_OUTBOUND_LAUNCH_STATE_PATH",
                str(DEFAULT_PROJECT9_LAUNCH_STATE_PATH),
            )
        )
        self.founder_stop_path = Path(
            os.getenv("PROJECT9_FOUNDER_STOP_PATH", str(DEFAULT_FOUNDERS_STOP_PATH))
        )
        self.first_10_event_feed_path = Path(
            os.getenv(
                "OUTBOUND_FIRST_10_EVENT_FEED_PATH",
                os.getenv(
                    "PROJECT9_OUTBOUND_FIRST_10_EVENT_FEED_PATH",
                    str(FIRST_10_EVENT_FEED_PATH),
                ),
            )
        )
        self.morning_digest_path = PROJECT9_STATE_DIR / f"{DIGEST_FILENAME_PREFIX}{self.run_id}.md"
        self.email_engine = EmailAcquisitionEngine()
        self.email_audit_path = PROJECT9_STATE_DIR / "email_acquisition_audit.ndjson"
        self._sheets_service = None
        self._flow = ApprovalFlow()

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------

    def run(self) -> None:
        summary = self._new_run_summary()
        digest_entries: list[dict[str, Any]] = []
        anomaly_categories: set[str] = set()
        self._ensure_first_10_event_feed()
        if self._founder_stop_active():
            anomaly_categories.add("founder_stop_blocked_run")
            timestamp = datetime.now(DETROIT).isoformat()
            reason = self._founder_stop_reason()
            print(
                f"RUN_BLOCKED_BY_FOUNDER_STOP timestamp={timestamp} "
                f"run_id={self.run_id} reason={reason}"
            )
            telegram_notify(
                "Sales Agent blocked by founder stop",
                f"RUN_BLOCKED_BY_FOUNDER_STOP\nrun_id={self.run_id}\ntimestamp={timestamp}\nreason={reason}",
                "CRITICAL",
            )
            summary["cap_status"] = "UNDER_CAP"
            summary["summary_integrity"] = "VERIFIED"
            summary["no_send_integrity"] = "VERIFIED" if not self.no_send_invoked else "BREACH"
            summary["workflow_duration_seconds"] = round(time.time() - self.started_at, 1)
            summary.pop("leads_touched", None)
            self._finalize_run_outputs(summary, digest_entries, anomaly_categories)
            self._emit_run_summary(summary)
            return

        leads = self.get_hot_leads_from_sheets()
        summary["total_candidates_seen"] = len(leads)
        if not leads:
            print("ℹ️  No HOT leads with domain found in Sheets")
            telegram_notify(
                "Sales Agent",
                f"No HOT leads with domain to process today.\nrun_id={self.run_id}",
                "INFO",
            )
            summary["cap_status"] = "UNDER_CAP"
            summary["summary_integrity"] = "VERIFIED"
            summary["no_send_integrity"] = "VERIFIED" if not self.no_send_invoked else "BREACH"
            summary["workflow_duration_seconds"] = round(time.time() - self.started_at, 1)
            summary.pop("leads_touched", None)
            self._finalize_run_outputs(summary, digest_entries, anomaly_categories)
            self._emit_run_summary(summary)
            return

        print(f"📋 Found {len(leads)} HOT leads with domain — processing up to {CAP_LIMIT}")

        queue_index = self._load_queue_index()
        lead_ids_this_run: dict[str, str] = {}
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

        total_terminal_states_assigned = (
            summary["total_queued"]
            + summary["total_filtered_out_chain"]
            + summary["total_filtered_out_corporate"]
            + summary["total_filtered_out_duplicate"]
            + summary["total_filtered_out_incomplete"]
            + summary["total_skipped"]
            + summary["total_timeout_unresolved"]
            + summary["total_errors"]
        )
        summary["summary_integrity"] = (
            "VERIFIED"
            if total_terminal_states_assigned == summary["total_leads_evaluated_for_this_run"]
            else "SUMMARY_INTEGRITY_FAIL"
        )
        summary["no_send_integrity"] = "VERIFIED" if not self.no_send_invoked else "BREACH"
        summary["workflow_duration_seconds"] = round(time.time() - self.started_at, 1)
        if summary["cap_status"] == "UNDER_CAP" and summary["leads_touched"] >= CAP_LIMIT:
            summary["cap_status"] = "AT_CAP"
        summary.pop("leads_touched", None)
        if summary["fail_safe_usage_status"] == "USED":
            anomaly_categories.add("fail_safe_used")
        if summary["summary_integrity"] == "SUMMARY_INTEGRITY_FAIL":
            anomaly_categories.add("summary_integrity_mismatch")
        if summary["total_timeout_unresolved"] > 0:
            anomaly_categories.add("timeout_unresolved")
        if summary["total_errors"] > 0:
            anomaly_categories.add("total_errors")
        if summary["cap_status"] == "CAP_BREACH_BLOCKED":
            anomaly_categories.add("CAP_BREACH_BLOCKED")
        if summary["log_write_status"] == "PERSISTENCE_FAILURE":
            anomaly_categories.add("log_persistence_failure")
        self._finalize_run_outputs(summary, digest_entries, anomaly_categories)
        self._emit_run_summary(summary)

    # ------------------------------------------------------------------
    # TELEGRAM CONFIRMATION
    # ------------------------------------------------------------------

    def _ensure_first_10_event_feed(self) -> None:
        self.first_10_event_feed_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.first_10_event_feed_path.exists():
            self.first_10_event_feed_path.touch()

    def _read_launch_state_payload(self) -> dict[str, Any]:
        payload = json.loads(self.launch_state_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("launch state root JSON value must be an object")
        return payload

    def _load_first_10_event_records(self) -> list[dict[str, Any]]:
        if not self.first_10_event_feed_path.exists():
            return []
        records: list[dict[str, Any]] = []
        raw = self.first_10_event_feed_path.read_text(encoding="utf-8", errors="replace")
        if not raw.strip():
            return []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                records.append(payload)
        return records

    def _append_first_10_event(self, record: dict[str, Any]) -> None:
        self.first_10_event_feed_path.parent.mkdir(parents=True, exist_ok=True)
        with self.first_10_event_feed_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    @staticmethod
    def _hash_text(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _new_run_summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "leads_touched": 0,
            "total_candidates_seen": 0,
            "total_leads_evaluated_for_this_run": 0,
            "total_filtered_out_chain": 0,
            "total_filtered_out_corporate": 0,
            "total_filtered_out_duplicate": 0,
            "total_filtered_out_incomplete": 0,
            "total_queued": 0,
            "total_skipped": 0,
            "total_timeout_unresolved": 0,
            "total_errors": 0,
            "cap_status": "UNDER_CAP",
            "log_write_status": "ALL_WRITTEN",
            "fail_safe_usage_status": "NOT_USED",
            "no_send_integrity": "VERIFIED",
            "summary_integrity": "VERIFIED",
            "workflow_duration_seconds": 0.0,
        }

    def _load_founder_stop_payload(self) -> dict[str, Any] | None:
        env_flag = os.getenv("PROJECT9_FOUNDER_STOP_ACTIVE", "").strip().lower()
        if env_flag in {"1", "true", "yes", "on"}:
            return {
                "stop_active": True,
                "reason": os.getenv("PROJECT9_FOUNDER_STOP_REASON", "founder stop active"),
                "source": "environment",
            }
        if not self.founder_stop_path.exists():
            return None
        try:
            payload = json.loads(self.founder_stop_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {
                "stop_active": True,
                "reason": f"invalid founder stop file: {exc}",
                "source": str(self.founder_stop_path),
            }
        if isinstance(payload, dict) and bool(payload.get("stop_active")):
            return payload
        return None

    def _founder_stop_active(self) -> bool:
        return self._load_founder_stop_payload() is not None

    def _founder_stop_reason(self) -> str:
        payload = self._load_founder_stop_payload() or {}
        reason = str(payload.get("reason", "")).strip()
        return reason or "founder stop active"

    def _get_sheets_service(self):
        if self._sheets_service is not None:
            return self._sheets_service
        if not self.sheet_id or not self.service_account_json:
            raise RuntimeError("Sheets not configured")
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds = service_account.Credentials.from_service_account_info(
            json.loads(self.service_account_json),
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        self._sheets_service = build("sheets", "v4", credentials=creds)
        return self._sheets_service

    def _worksheet_exists(self, worksheet_name: str) -> bool:
        service = self._get_sheets_service()
        meta = service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        for sheet in meta.get("sheets", []):
            props = sheet.get("properties", {})
            if props.get("title") == worksheet_name:
                return True
        return False

    def _ensure_worksheet(self, worksheet_name: str, headers: list[str]) -> None:
        service = self._get_sheets_service()
        if self._worksheet_exists(worksheet_name):
            return
        service.spreadsheets().batchUpdate(
            spreadsheetId=self.sheet_id,
            body={
                "requests": [
                    {
                        "addSheet": {
                            "properties": {
                                "title": worksheet_name,
                                "gridProperties": {
                                    "rowCount": 1000,
                                    "columnCount": max(20, len(headers) + 2),
                                },
                            }
                        }
                    }
                ]
            },
        ).execute()
        service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=f"{worksheet_name}!A1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()

    def _append_row(self, worksheet_name: str, row: list[str]) -> None:
        service = self._get_sheets_service()
        service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range=f"{worksheet_name}!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()

    def _read_rows(self, worksheet_name: str, range_spec: str) -> list[list[str]]:
        service = self._get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id,
            range=range_spec,
        ).execute()
        return result.get("values", [])

    def _load_queue_index(self) -> set[str]:
        if not self.sheet_id:
            return set()
        try:
            rows = self._read_rows(QUEUE_TAB_NAME, f"{QUEUE_TAB_NAME}!C2:C")
        except Exception:
            return set()
        return {str(row[0]).strip() for row in rows if row and str(row[0]).strip()}

    def _outreach_log_has_key(self, idempotency_key: str) -> bool:
        if not self.sheet_id:
            return False
        try:
            rows = self._read_rows(OUTREACH_LOG_TAB_NAME, f"{OUTREACH_LOG_TAB_NAME}!J2:J")
        except Exception:
            return False
        return any(row and str(row[0]).strip() == idempotency_key for row in rows)

    def _build_lead_id(self, lead: Lead) -> str:
        source = "|".join(
            [
                (lead.business or "").strip().lower(),
                (lead.domain or "").strip().lower(),
                (lead.owner_email or "").strip().lower(),
                (lead.phone or "").strip(),
            ]
        )
        return f"lead-{self._hash_text(source)[:12]}"

    def _is_chain_filtered(self, lead_name: str) -> bool:
        return bool(
            any(kw in lead_name for kw in CHAIN_EXCLUSION_KEYWORDS)
            or re.search(r"\b(?:inc|llc|corp|holdings|enterprises)\b", lead_name)
        )

    def _is_corporate_filtered(self, lead_name: str) -> bool:
        return bool(re.search(r"\b(?:inc|llc|corp|holdings|enterprises)\b", lead_name))

    def _is_non_smb_filtered(self, lead: Lead) -> bool:
        lead_name = (lead.business or "").lower()
        return bool(
            re.search(r"\b(?:corporate|headquarters|franchise|enterprise|national|regional)\b", lead_name)
        )

    def _is_incomplete(self, lead: Lead) -> bool:
        return not all(
            [
                (lead.business or "").strip(),
                (lead.owner_email or "").strip(),
                (lead.phone or "").strip(),
            ]
        )

    def _append_email_audit(self, payload: dict[str, Any]) -> None:
        try:
            self.email_audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.email_audit_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n")
        except Exception as exc:
            print(f"  ⚠️  Email acquisition audit write failed: {exc}")

    def _recover_owner_email(self, lead: Lead) -> dict[str, Any]:
        prospect = {
            "business_name": lead.business,
            "name": lead.business,
            "primary_domain": lead.domain,
            "domain": lead.domain,
            "website": lead.domain,
            "owner_email": lead.owner_email,
            "email": lead.owner_email,
            "contact_name": "",
            "title": "",
            "source": "sales_agent_reprocess",
        }
        acquisition = self.email_engine.acquire(prospect).to_dict()
        canonical_email = normalize_owner_email(
            acquisition.get("final_email") or lead.owner_email or lead.email
        ) or ""
        if canonical_email:
            lead.owner_email = canonical_email
            lead.lead_id = self._build_lead_id(lead)
        lead.email_confidence = acquisition.get("email_confidence", "")
        lead.email_source_type = acquisition.get("email_source_type", "")
        lead.email_source_reference = acquisition.get("email_source_reference", "")
        lead.person_match_basis = acquisition.get("person_match_basis", "")
        lead.verification_notes = acquisition.get("verification_notes", "")
        lead.rejection_reason = acquisition.get("rejection_reason", "")
        lead.email_source = "acquisition_reprocess" if canonical_email else lead.email_source
        acquisition["final_email"] = canonical_email
        acquisition["owner_email"] = canonical_email
        self._append_email_audit(
            {
                "run_id": self.run_id,
                "business_name": lead.business,
                "lead_id": lead.lead_id,
                "reprocess": True,
                **acquisition,
            }
        )
        return acquisition

    def _assign_priority(self, lead: Lead) -> str:
        industry = (lead.industry or "").strip().lower()
        if industry in {"restaurant", "dental", "hvac"}:
            return "HIGH"
        if industry in {"salon", "real_estate"}:
            return "MEDIUM"
        return "LOW"

    def _build_reason_selected(self, lead: Lead, priority: str, pass_type: str) -> str:
        return (
            f"{lead.business} passed suppression filters and is ready for founder review "
            f"(priority={priority}, pass={pass_type})"
        )

    def _serialize_payload(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)

    def _preview_recommended_draft(self, recommended_draft: str) -> list[str]:
        if not recommended_draft:
            return []
        try:
            payload = json.loads(recommended_draft)
        except Exception:
            snippet = [line.strip() for line in recommended_draft.splitlines() if line.strip()]
            return snippet[:2] if snippet else [recommended_draft[:160]]

        preview_lines: list[str] = []
        subject = str(payload.get("subject", "")).strip()
        body = str(payload.get("body", "")).strip()
        if subject:
            preview_lines.append(f"Subject: {subject}")
        body_lines = [line.strip() for line in body.splitlines() if line.strip()]
        for line in body_lines:
            preview_lines.append(f"Body: {line}")
            if len(preview_lines) >= 2:
                break
        return preview_lines[:2]

    def _build_digest_entry(
        self,
        *,
        lead: Lead,
        result: dict[str, Any],
        sequence: int,
    ) -> dict[str, Any]:
        return {
            "sequence": sequence,
            "business_name": lead.business,
            "priority": result.get("priority", ""),
            "reason_selected": result.get("reason_selected", ""),
            "owner_email": lead.owner_email,
            "recommended_draft_preview": self._preview_recommended_draft(
                str(result.get("recommended_draft", ""))
            ),
            "lead_id": result.get("lead_id", lead.lead_id),
            "terminal_state": result.get("terminal_state", ""),
        }

    def _prune_old_digest_files(self) -> None:
        self.morning_digest_path.parent.mkdir(parents=True, exist_ok=True)
        for path in self.morning_digest_path.parent.glob(f"{DIGEST_FILENAME_PREFIX}*.md"):
            if path == self.morning_digest_path:
                continue
            try:
                path.unlink()
            except FileNotFoundError:
                pass

    def _digest_anomaly_labels(self, anomaly_categories: set[str]) -> list[str]:
        labels = [DIGEST_ANOMALY_LABELS.get(item, item) for item in anomaly_categories]
        order = {value: index for index, value in enumerate(DIGEST_ANOMALY_LABELS.values())}
        return sorted(labels, key=lambda item: order.get(item, 999))

    def _build_morning_digest(
        self,
        summary: dict[str, Any],
        digest_entries: list[dict[str, Any]],
        anomaly_categories: set[str],
    ) -> str:
        ordered_entries = sorted(
            digest_entries,
            key=lambda item: (
                DIGEST_PRIORITY_ORDER.get(str(item.get("priority", "")).upper(), 99),
                int(item.get("sequence", 0)),
            ),
        )
        anomaly_labels = self._digest_anomaly_labels(anomaly_categories)
        lines = [
            "# Founder Morning Digest",
            "",
            "## Top Line",
            f"- run_id: {summary.get('run_id', self.run_id)}",
            f"- workflow_duration_seconds: {summary.get('workflow_duration_seconds', 0.0)}",
            f"- cap_status: {summary.get('cap_status', 'UNDER_CAP')}",
            f"- total_queued: {summary.get('total_queued', 0)}",
            f"- anomaly_count: {len(anomaly_labels)}",
            f"- fail_safe_usage_status: {summary.get('fail_safe_usage_status', 'NOT_USED')}",
            f"- no_send_integrity: {summary.get('no_send_integrity', 'VERIFIED')}",
            f"- summary_integrity: {summary.get('summary_integrity', 'VERIFIED')}",
            "",
            "## Immediate Decisions",
        ]
        if ordered_entries:
            current_priority = None
            for entry in ordered_entries:
                priority = str(entry.get("priority", "")).upper() or "LOW"
                if priority != current_priority:
                    lines.extend(["", f"### {priority}"])
                    current_priority = priority
                lines.extend(
                    [
                        f"- business_name: {entry.get('business_name', '')}",
                        f"  - priority: {priority}",
                        f"  - reason_selected: {entry.get('reason_selected', '')}",
                        f"  - owner_email: {entry.get('owner_email', '')}",
                        f"  - lead_id: {entry.get('lead_id', '')}",
                        f"  - terminal_state: {entry.get('terminal_state', '')}",
                        "  - recommended_draft_preview:",
                    ]
                )
                preview = entry.get("recommended_draft_preview", [])
                if preview:
                    lines.extend([f"    - {line}" for line in preview])
                else:
                    lines.append("    - none")
        else:
            lines.append("- none queued")

        lines.extend(
            [
                "",
                "## Filtered Summary",
                f"- total_filtered_out_chain: {summary.get('total_filtered_out_chain', 0)}",
                f"- total_filtered_out_corporate: {summary.get('total_filtered_out_corporate', 0)}",
                f"- total_filtered_out_duplicate: {summary.get('total_filtered_out_duplicate', 0)}",
                f"- total_filtered_out_incomplete: {summary.get('total_filtered_out_incomplete', 0)}",
                "",
                "## Anomalies",
            ]
        )
        if anomaly_labels:
            lines.extend(f"- {label}" for label in anomaly_labels)
        else:
            lines.append("- anomalies: none")

        lines.extend(
            [
                "",
                "## Human-Locked Reminders",
                "- live send still paused",
                "- founder approval required for every queued lead",
                "- no gate changes occurred in this run",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _write_morning_digest(
        self,
        summary: dict[str, Any],
        digest_entries: list[dict[str, Any]],
        anomaly_categories: set[str],
    ) -> Path:
        self._prune_old_digest_files()
        digest_text = self._build_morning_digest(summary, digest_entries, anomaly_categories)
        self.morning_digest_path.write_text(digest_text, encoding="utf-8")
        print(f"✅ Founder morning digest written → {self.morning_digest_path}")
        print(
            "📦 Founder morning digest metrics: "
            f"run_id={summary.get('run_id', self.run_id)} "
            f"queued_leads={len(digest_entries)} "
            f"anomaly_count={len(anomaly_categories)} "
            f"no_send_integrity={summary.get('no_send_integrity', 'VERIFIED')} "
            f"summary_integrity={summary.get('summary_integrity', 'VERIFIED')}"
        )
        return self.morning_digest_path

    def _finalize_run_outputs(
        self,
        summary: dict[str, Any],
        digest_entries: list[dict[str, Any]],
        anomaly_categories: set[str],
    ) -> None:
        self._write_morning_digest(summary, digest_entries, anomaly_categories)

    def _sheet_write_with_retry(self, worksheet_name: str, row: list[str]) -> None:
        delays = (2, 4, 8)
        last_exc: Exception | None = None
        for attempt, delay in enumerate(delays, start=1):
            try:
                self._append_row(worksheet_name, row)
                return
            except Exception as exc:
                last_exc = exc
                print(f"  ⚠️  {worksheet_name} write failed (attempt {attempt}/3): {exc}")
                if attempt < len(delays):
                    time.sleep(delay)
        raise RuntimeError(f"{worksheet_name} write failed after 3 attempts: {last_exc}")

    def _alert_with_payload(self, subject: str, payload: dict[str, Any], priority: str = "CRITICAL") -> bool:
        text = self._serialize_payload(payload)
        return telegram_notify(subject, text, priority)

    def _persist_with_failsafe(
        self,
        *,
        worksheet_name: str,
        headers: list[str],
        row: list[str],
        failsafe_payload: dict[str, Any],
        summary: dict[str, Any],
    ) -> str:
        self._ensure_worksheet(worksheet_name, headers)
        try:
            self._sheet_write_with_retry(worksheet_name, row)
            return "WRITTEN"
        except Exception as primary_exc:
            print(f"  ⚠️  {worksheet_name} primary write failed: {primary_exc}")
            if worksheet_name == FAILSAFE_TAB_NAME:
                if self._alert_with_payload(
                    f"{worksheet_name} unreachable",
                    failsafe_payload,
                    "CRITICAL",
                ):
                    summary["fail_safe_usage_status"] = "USED"
                    return "FAILSAFE_USED"
                summary["fail_safe_usage_status"] = "FAILED"
                summary["log_write_status"] = "PERSISTENCE_FAILURE"
                raise RuntimeError("LOG_PERSISTENCE_FAILURE") from primary_exc

            failsafe_row = [
                str(failsafe_payload.get("run_id", self.run_id)),
                str(failsafe_payload.get("timestamp", datetime.now(DETROIT).isoformat())),
                str(failsafe_payload.get("lead_id", "")),
                str(failsafe_payload.get("business_name", "")),
                str(failsafe_payload.get("failure_reason", "")),
                self._serialize_payload(failsafe_payload),
                "FAILSAFE_WRITTEN",
            ]
            failsafe_status = self._persist_with_failsafe(
                worksheet_name=FAILSAFE_TAB_NAME,
                headers=FAILSAFE_HEADERS,
                row=failsafe_row,
                failsafe_payload=failsafe_payload,
                summary=summary,
            )
            if failsafe_status in {"WRITTEN", "FAILSAFE_USED"}:
                summary["fail_safe_usage_status"] = "USED"
                return "FAILSAFE_USED"

            if self._alert_with_payload(
                f"{worksheet_name} fail-safe fallback",
                failsafe_payload,
                "CRITICAL",
            ):
                summary["fail_safe_usage_status"] = "USED"
                return "FAILSAFE_USED"

            summary["fail_safe_usage_status"] = "FAILED"
            summary["log_write_status"] = "PERSISTENCE_FAILURE"
            raise RuntimeError("LOG_PERSISTENCE_FAILURE") from primary_exc

    def _queue_entry_exists(self, lead_id: str) -> list[tuple[str, str]]:
        if not self.sheet_id:
            return []
        try:
            rows = self._read_rows(QUEUE_TAB_NAME, f"{QUEUE_TAB_NAME}!C2:K")
        except Exception:
            return []
        existing: list[tuple[str, str]] = []
        for row in rows:
            if len(row) < 9:
                continue
            if str(row[0]).strip() == lead_id:
                existing.append((str(row[1]).strip(), str(row[8]).strip()))
        return existing

    def _process_candidate(
        self,
        lead: Lead,
        *,
        summary: dict[str, Any],
        queue_index: set[str],
        lead_ids_this_run: dict[str, str],
    ) -> dict[str, Any]:
        lead_name = (lead.business or "").strip().lower()
        if not normalize_owner_email(lead.owner_email):
            self._recover_owner_email(lead)

        lead_id = self._build_lead_id(lead)
        lead.lead_id = lead_id

        if self._is_incomplete(lead):
            return {
                "selected": False,
                "filter_summary_key": "total_filtered_out_incomplete",
                "terminal_state": "FILTERED_OUT_INCOMPLETE",
                "lead_id": lead_id,
            }
        if self._is_chain_filtered(lead_name):
            return {
                "selected": False,
                "filter_summary_key": "total_filtered_out_chain",
                "terminal_state": "FILTERED_OUT_CHAIN",
                "lead_id": lead_id,
            }
        if self._is_corporate_filtered(lead_name) or self._is_non_smb_filtered(lead):
            return {
                "selected": False,
                "filter_summary_key": "total_filtered_out_corporate",
                "terminal_state": "FILTERED_OUT_CORPORATE",
                "lead_id": lead_id,
            }
        if lead_id in queue_index:
            return {
                "selected": False,
                "filter_summary_key": "total_filtered_out_duplicate",
                "terminal_state": "FILTERED_OUT_DUPLICATE",
                "lead_id": lead_id,
            }

        if lead_id in lead_ids_this_run and lead_ids_this_run[lead_id] != "QUEUED_FOR_REVIEW":
            print(
                f"⛔ QUEUE_CORRUPTION_DETECTED lead_id={lead_id} "
                f"run_id={self.run_id} previous_state={lead_ids_this_run[lead_id]}"
            )
            telegram_notify(
                "Sales Agent queue corruption",
                f"QUEUE_CORRUPTION_DETECTED\nrun_id={self.run_id}\nlead_id={lead_id}\nbusiness={lead.business}",
                "CRITICAL",
            )
            summary["total_leads_evaluated_for_this_run"] += 1
            lead_ids_this_run[lead_id] = "ERROR_RETRY_LOGGED"
            return {
                "selected": True,
                "terminal_state": "ERROR_RETRY_LOGGED",
                "queue_result": "ERROR_RETRY_LOGGED",
                "priority": self._assign_priority(lead),
                "reason_selected": self._build_reason_selected(lead, self._assign_priority(lead), "first_pass"),
                "queue_status": "PERSISTENCE_FAILURE",
                "log_write_status": "PERSISTENCE_FAILURE",
                "fail_safe_usage_status": summary.get("fail_safe_usage_status", "NOT_USED"),
                "anomaly_category": "queue_corruption_detected",
                "halt_run": True,
                "halt_reason": "QUEUE_CORRUPTION_DETECTED",
            }

        if len(lead_ids_this_run) >= CAP_LIMIT:
            print(
                f"⛔ CAP_BREACH_BLOCKED run_id={self.run_id} lead_id={lead_id} business={lead.business}"
            )
            telegram_notify(
                "Sales Agent cap breach blocked",
                f"CAP_BREACH_BLOCKED\nrun_id={self.run_id}\nlead_id={lead_id}\nbusiness={lead.business}",
                "CRITICAL",
            )
            return {
                "selected": False,
                "terminal_state": "CAP_BREACH_BLOCKED",
                "anomaly_category": "CAP_BREACH_BLOCKED",
                "halt_run": True,
                "halt_reason": "CAP_BREACH_BLOCKED",
                "lead_id": lead_id,
            }

        if summary["leads_touched"] >= CAP_LIMIT:
            print(
                f"⛔ CAP_BREACH_BLOCKED run_id={self.run_id} lead_id={lead_id} business={lead.business}"
            )
            telegram_notify(
                "Sales Agent cap breach blocked",
                f"CAP_BREACH_BLOCKED\nrun_id={self.run_id}\nlead_id={lead_id}\nbusiness={lead.business}",
                "CRITICAL",
            )
            return {
                "selected": False,
                "terminal_state": "CAP_BREACH_BLOCKED",
                "anomaly_category": "CAP_BREACH_BLOCKED",
                "halt_run": True,
                "halt_reason": "CAP_BREACH_BLOCKED",
                "lead_id": lead_id,
            }

        summary["total_leads_evaluated_for_this_run"] += 1

        queue_index.add(lead_id)
        lead_ids_this_run[lead_id] = "PROCESSING"
        variant = (hash(lead.business) % 5) + 1
        priority = self._assign_priority(lead)
        try:
            subject, body, pass_type = self._draft_email(lead, variant)
            recommended_draft = self._serialize_payload(
                {
                    "subject": subject,
                    "body": body,
                    "variant": variant,
                    "pass_type": pass_type,
                }
            )
            reason_selected = self._build_reason_selected(lead, priority, pass_type)
            request = self._flow.request_approval(
                action_type=ActionType.OUTREACH,
                target_name=lead.business,
                target_email=lead.owner_email,
                preview=f"Subject: {subject}\n\n{body[:280]}",
            )
            if not request.message_id:
                raise RuntimeError("approval prompt missing message_id")
            self._attach_approval_buttons(request.message_id)
            status = self._wait_for_callback(request.message_id, timeout_seconds=600)
            if status == ApprovalStatus.APPROVED:
                terminal_state = "QUEUED_FOR_REVIEW"
                queue_result = "QUEUED_FOR_REVIEW"
                confirmation = f"🗂️ Queued for review: {lead.business}. No email was sent."
            elif status == ApprovalStatus.SKIPPED:
                terminal_state = "SKIPPED"
                queue_result = "SKIPPED"
                confirmation = f"⏭️ Skipped by founder: {lead.business}. No email was sent."
            elif status == ApprovalStatus.EXPIRED:
                terminal_state = "TIMEOUT_UNRESOLVED"
                queue_result = "TIMEOUT_UNRESOLVED"
                confirmation = f"⏰ No response for {lead.business}; marked TIMEOUT_UNRESOLVED."
            else:
                raise RuntimeError(f"unresolved callback ambiguity: {status}")
        except Exception as exc:
            terminal_state = "ERROR_RETRY_LOGGED"
            queue_result = "ERROR_RETRY_LOGGED"
            reason_selected = reason_selected if "reason_selected" in locals() else self._build_reason_selected(lead, priority, "first_pass")
            recommended_draft = recommended_draft if "recommended_draft" in locals() else self._serialize_payload(
                {
                    "subject": f"Quick question about {lead.business}",
                    "body": f"Draft unavailable: {exc}",
                    "variant": variant,
                    "pass_type": "first_pass",
                }
            )
            confirmation = f"⚠️ Error logged for {lead.business}: {exc}"
            if "QUEUE_CORRUPTION_DETECTED" in str(exc):
                raise
            anomaly_category = "callback_ambiguity" if "unresolved callback ambiguity" in str(exc) else None
            if "LOG_PERSISTENCE_FAILURE" in str(exc):
                anomaly_category = "log_persistence_failure"
            if "CAP_BREACH_BLOCKED" in str(exc):
                anomaly_category = "CAP_BREACH_BLOCKED"
            if anomaly_category:
                current_log_status = summary.get("log_write_status", "ALL_WRITTEN")
                current_fail_safe_status = summary.get("fail_safe_usage_status", "NOT_USED")
                if anomaly_category == "log_persistence_failure":
                    current_log_status = "PERSISTENCE_FAILURE"
                self._telegram_confirm(confirmation)
                return {
                    "selected": True,
                    "terminal_state": terminal_state,
                    "queue_result": queue_result,
                    "priority": priority,
                    "reason_selected": reason_selected,
                    "queue_status": current_log_status,
                    "log_write_status": current_log_status,
                    "fail_safe_usage_status": current_fail_safe_status,
                    "lead_id": lead_id,
                    "recommended_draft": recommended_draft,
                    "anomaly_category": anomaly_category,
                    "halt_run": True,
                    "halt_reason": (
                        "LOG_PERSISTENCE_FAILURE"
                        if anomaly_category == "log_persistence_failure"
                        else ("CAP_BREACH_BLOCKED" if anomaly_category == "CAP_BREACH_BLOCKED" else "CALLBACK_AMBIGUITY")
                    ),
                }
        lead_ids_this_run[lead_id] = terminal_state
        queued_at = datetime.now(DETROIT).isoformat()
        timestamp = queued_at
        variant_metadata = self._serialize_payload(
            {
                "variant": variant,
                "industry": lead.industry,
                "lead_id": lead_id,
            }
        )
        pass_metadata = self._serialize_payload(
            {
                "pass_type": locals().get("pass_type", "first_pass"),
                "lead_id": lead_id,
                "email_confidence": lead.email_confidence or "NONE",
                "email_source_type": lead.email_source_type or "unknown",
                "email_source_reference": lead.email_source_reference or "",
            }
        )
        queue_row = [
            self.run_id,
            queued_at,
            lead_id,
            lead.business,
            lead.owner_email,
            priority,
            reason_selected,
            recommended_draft,
            variant_metadata,
            pass_metadata,
            terminal_state,
        ]
        log_row = [
            self.run_id,
            timestamp,
            lead_id,
            lead.business,
            "PASSED_SUPPRESSION_FILTERS",
            priority,
            queue_result,
            terminal_state,
            "WRITTEN",
            f"{lead_id}{self.run_id}{terminal_state}",
        ]
        try:
            queue_status = self._persist_with_failsafe(
                worksheet_name=QUEUE_TAB_NAME,
                headers=QUEUE_HEADERS,
                row=queue_row,
                failsafe_payload={
                    "run_id": self.run_id,
                    "timestamp": timestamp,
                    "lead_id": lead_id,
                    "business_name": lead.business,
                    "failure_reason": f"queue persistence failed for terminal_state={terminal_state}",
                    "serialized_payload": self._serialize_payload(
                        {
                            "queue_row": queue_row,
                            "terminal_state": terminal_state,
                            "reason_selected": reason_selected,
                        }
                    ),
                },
                summary=summary,
            )
            log_idempotency_key = f"{lead_id}{self.run_id}{terminal_state}"
            if self._outreach_log_has_key(log_idempotency_key):
                print(
                    f"  DUPLICATE_WRITE_BLOCKED lead_id={lead_id} run_id={self.run_id} "
                    f"terminal_state={terminal_state}"
                )
                log_status = "DUPLICATE_WRITE_BLOCKED"
            else:
                log_status = self._persist_with_failsafe(
                    worksheet_name=OUTREACH_LOG_TAB_NAME,
                    headers=OUTREACH_LOG_HEADERS,
                    row=log_row,
                    failsafe_payload={
                        "run_id": self.run_id,
                        "timestamp": timestamp,
                        "lead_id": lead_id,
                        "business_name": lead.business,
                        "failure_reason": f"outreach log persistence failed for terminal_state={terminal_state}",
                        "serialized_payload": self._serialize_payload(
                            {
                                "log_row": log_row,
                                "terminal_state": terminal_state,
                                "queue_result": queue_result,
                            }
                        ),
                    },
                    summary=summary,
                )
        except RuntimeError as exc:
            terminal_state = "ERROR_RETRY_LOGGED"
            queue_result = "ERROR_RETRY_LOGGED"
            queue_status = "PERSISTENCE_FAILURE"
            log_status = "PERSISTENCE_FAILURE"
            confirmation = f"⚠️ Error logged for {lead.business}: {exc}"
            lead_ids_this_run[lead_id] = terminal_state
            self._telegram_confirm(confirmation)
            return {
                "selected": True,
                "terminal_state": terminal_state,
                "queue_result": queue_result,
                "priority": priority,
                "reason_selected": reason_selected,
                "queue_status": queue_status,
                "log_write_status": log_status,
                "fail_safe_usage_status": summary.get("fail_safe_usage_status", "NOT_USED"),
                "halt_run": True,
                "halt_reason": "LOG_PERSISTENCE_FAILURE",
            }

        if queue_status == "FAILSAFE_USED" or log_status == "FAILSAFE_USED":
            summary["log_write_status"] = "FAILSAFE_USED"
            summary["fail_safe_usage_status"] = "USED"
        elif queue_status == "WRITTEN" and log_status == "WRITTEN":
            summary["log_write_status"] = "ALL_WRITTEN"
        self._mark_notified(lead.sheet_row)
        print(f"  📋 Founder review queue: {lead.business} → {terminal_state} (run_id={self.run_id})")
        print(f"  📤 queue action complete: {queue_result}")
        self._telegram_confirm(confirmation)
        return {
            "selected": True,
            "terminal_state": terminal_state,
            "queue_result": queue_result,
            "priority": priority,
            "reason_selected": reason_selected,
            "queue_status": queue_status,
            "log_write_status": log_status,
            "fail_safe_usage_status": summary.get("fail_safe_usage_status", "NOT_USED"),
            "lead_id": lead_id,
            "recommended_draft": recommended_draft,
        }

    def _emit_run_summary(self, summary: dict[str, Any]) -> None:
        print("RUN SUMMARY:")
        print(json.dumps(summary, indent=2, sort_keys=True))

    def _record_first_10_send_event(
        self,
        *,
        lead: Lead,
        subject: str,
        body: str,
        delivery_ok: bool,
    ) -> None:
        try:
            launch_state = self._read_launch_state_payload()
        except Exception as exc:
            print(f"⚠️  First-10 event feed skipped: {exc}")
            return

        launch_correlation_id = str(launch_state.get("correlation_id", "")).strip() or "unknown"
        campaign_id = str(launch_state.get("campaign_id", "")).strip() or launch_correlation_id
        existing_records = self._load_first_10_event_records()
        accepted_send_number = sum(
            1 for item in existing_records if bool(item.get("provider_accepted"))
        ) + (1 if delivery_ok else 0)
        attempt_number = len(existing_records) + 1
        provider_message_id = (
            f"queue-{self.run_id}-{attempt_number}-{self._hash_text(lead.owner_email.lower())[:12]}"
            if delivery_ok
            else None
        )
        record = {
            "hook_name": "outbound_first_10_send_event",
            "verification_result": "PASS" if delivery_ok else "FAIL",
            "launch_correlation_id": launch_correlation_id,
            "campaign_id": campaign_id,
            "window_name": "first_10",
            "attempt_number": attempt_number,
            "send_number": attempt_number,
            "accepted_send_number": accepted_send_number if delivery_ok else None,
            "recipient_hash": self._hash_text(lead.owner_email.strip().lower()),
            "message_hash": self._hash_text(f"{subject}\n\n{body}"),
            "provider_message_id": provider_message_id,
            "provider_accepted": bool(delivery_ok),
            "delivery_status": "accepted" if delivery_ok else "delivery_failed",
            "bounce_count": 0,
            "complaint_count": 0,
            "wrong_recipient_count": 0,
            "wrong_copy_count": 0,
            "authentication_failure_count": 0,
            "threshold_breached": False,
            "failure_reason": None if delivery_ok else "provider rejected or send failed",
            "next_action": "continue_monitoring",
            "checked_at": datetime.now(DETROIT).astimezone(DETROIT).isoformat(),
            "checked_by": "sales_agent",
            "source_of_truth_path": str(self.launch_state_path),
        }
        self._append_first_10_event(record)

    def _assert_outbound_launch_allowed(self, business: str) -> None:
        """Fail closed unless Project 9 launch state explicitly allows send."""
        try:
            payload = self._read_launch_state_payload()
        except OSError as exc:
            reason = f"outbound launch state unreadable: {exc.strerror or exc.__class__.__name__}"
            print(f"  ⛔ Blocking send for {business}: {reason}")
            raise RuntimeError(reason) from exc
        except json.JSONDecodeError as exc:
            reason = f"outbound launch state malformed: {exc.msg}"
            print(f"  ⛔ Blocking send for {business}: {reason}")
            raise RuntimeError(reason) from exc
        except ValueError as exc:
            reason = f"outbound launch state malformed: {exc}"
            print(f"  ⛔ Blocking send for {business}: {reason}")
            raise RuntimeError(reason) from exc

        if not isinstance(payload, dict):
            reason = "outbound launch state malformed: root JSON value must be an object"
            print(f"  ⛔ Blocking send for {business}: {reason}")
            raise RuntimeError(reason)

        launch_mode = str(payload.get("launch_mode", "")).strip()
        launch_status = str(payload.get("launch_status", "")).strip()
        if launch_mode not in ALLOWED_OUTBOUND_LAUNCH_MODES:
            reason = (
                "outbound send blocked: launch_mode must be LIVE_ALLOWED, "
                f"found {launch_mode or 'missing'}"
            )
            print(f"  ⛔ Blocking send for {business}: {reason} "
                  f"(status={launch_status or 'missing'}, state={self.launch_state_path})")
            raise RuntimeError(reason)

        if launch_status != "READY":
            reason = f"outbound send blocked: launch_status must be READY, found {launch_status or 'missing'}"
            print(f"  ⛔ Blocking send for {business}: {reason} (state={self.launch_state_path})")
            raise RuntimeError(reason)

    def resolve_launch_state(self) -> None:
        """Prefer the latest durable launch-state artifact, with repo fallback."""
        artifact_state = self._download_latest_launch_state_artifact()
        if artifact_state is not None:
            self.launch_state_path = artifact_state

    def _download_latest_launch_state_artifact(self) -> Path | None:
        """Resolve the latest durable Project 9 launch-state artifact if available."""
        token = os.getenv("GITHUB_TOKEN", "").strip()
        repository = os.getenv("GITHUB_REPOSITORY", "").strip()
        api_url = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
        if not token or not repository:
            return None
        try:
            resp = requests.get(
                f"{api_url}/repos/{repository}/actions/artifacts",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"per_page": 100},
                timeout=30,
            )
            if not resp.ok:
                print(f"⚠️  Launch state artifact lookup failed: {resp.status_code}")
                return None
            artifacts = [
                artifact for artifact in resp.json().get("artifacts", [])
                if artifact.get("name") == LAUNCH_STATE_ARTIFACT_NAME and not artifact.get("expired")
            ]
            if not artifacts:
                print("ℹ️  No durable launch-state artifact found; using repo state file")
                return None
            artifact = max(artifacts, key=lambda item: item.get("created_at", ""))
            archive_url = artifact.get("archive_download_url")
            if not archive_url:
                print("⚠️  Durable launch-state artifact missing archive URL")
                return None
            archive = requests.get(
                archive_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30,
            )
            if not archive.ok:
                print(f"⚠️  Durable launch-state artifact download failed: {archive.status_code}")
                return None
            import zipfile
            from io import BytesIO

            LAUNCH_STATE_RUNTIME_PATH.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(BytesIO(archive.content)) as zf:
                members = zf.namelist()
                candidate = next((name for name in members if name.endswith("outbound_launch_state.json")), None)
                if candidate is None:
                    print("⚠️  Durable launch-state artifact missing state JSON")
                    return None
                LAUNCH_STATE_RUNTIME_PATH.write_bytes(zf.read(candidate))
            print(f"✅ Loaded durable launch-state artifact → {LAUNCH_STATE_RUNTIME_PATH}")
            return LAUNCH_STATE_RUNTIME_PATH
        except Exception as exc:
            print(f"⚠️  Durable launch-state artifact resolution failed: {exc}")
            return None

    def _telegram_confirm(self, text: str) -> None:
        """Send a follow-up Telegram message after an approval decision."""
        try:
            token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
            chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
            if token and chat:
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat, "text": text},
                    timeout=10,
                )
        except Exception:
            pass

    def _attach_approval_buttons(self, message_id: int | None) -> None:
        """Edit the approval message to add inline QUEUE / SKIP buttons.

        This lets the founder tap a button instead of typing a reply.
        The callback_query from the button is what _wait_for_callback detects.
        """
        if not message_id:
            return
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat:
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/editMessageReplyMarkup",
                json={
                    "chat_id": chat,
                    "message_id": message_id,
                    "reply_markup": {
                        "inline_keyboard": [[
                            {"text": "🗂️ QUEUE", "callback_data": "queue"},
                            {"text": "⏭️ SKIP", "callback_data": "skip"},
                        ]]
                    },
                },
                timeout=10,
            )
        except Exception:
            pass

    def _wait_for_callback(
        self,
        message_id: int | None,
        timeout_seconds: int = 60,
        poll_interval: int = 3,
    ) -> ApprovalStatus:
        """Poll getUpdates for QUEUE/SKIP as either callback_query or text reply.

        Answers the callback_query immediately so the Telegram spinner clears
        and the action branch runs before the Command Center can respond.
        Text reply detection is kept as a fallback for non-button responses.
        """
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat:
            return ApprovalStatus.EXPIRED

        start = time.time()
        print(f"  🔍 _wait_for_callback() started — timeout={timeout_seconds}s message_id={message_id}")
        last_update_id = 0

        def process_updates(resp: requests.Response) -> ApprovalStatus | None:
            nonlocal last_update_id
            if not resp.ok:
                return None
            print(f"  🔍 process_updates() — updates={len(resp.json().get('result', []))}")
            for update in resp.json().get("result", []):
                last_update_id = max(last_update_id, update.get("update_id", 0))

                # --- inline keyboard callback_query (primary path) ---
                cq = update.get("callback_query", {})
                if cq:
                    cq_chat = str(cq.get("message", {}).get("chat", {}).get("id", ""))
                    print(f"  🔍 cq_chat='{cq_chat}' vs chat='{chat}' match={cq_chat == chat}")
                    if cq_chat == chat:
                        data = cq.get("data", "").strip().lower()
                        # Answer immediately to clear Telegram spinner
                        # before the action branch runs
                        try:
                            requests.post(
                                f"https://api.telegram.org/bot{token}/answerCallbackQuery",
                                json={"callback_query_id": cq.get("id", "")},
                                timeout=5,
                            )
                        except Exception:
                            pass
                        if any(kw in data for kw in ("queue", "yes", "approve")):
                            return ApprovalStatus.APPROVED
                        if any(kw in data for kw in ("skip", "no", "pass")):
                            return ApprovalStatus.SKIPPED

                # --- plain text reply (fallback) ---
                msg = update.get("message", {})
                if msg and str(msg.get("chat", {}).get("id", "")) == chat:
                    if message_id and msg.get("message_id", 0) > message_id:
                        text = msg.get("text", "").strip().lower()
                        if any(kw in text for kw in ("queue", "yes", "approve")):
                            return ApprovalStatus.APPROVED
                        if any(kw in text for kw in ("skip", "no", "pass")):
                            return ApprovalStatus.SKIPPED
            return None

        while time.time() - start < timeout_seconds:
            print(f"  🔍 poll loop tick — elapsed={time.time()-start:.1f}s")
            try:
                params = {
                    "timeout": 5,
                    "offset": last_update_id + 1 if last_update_id else 0,
                }
                resp = requests.get(
                    f"https://api.telegram.org/bot{token}/getUpdates",
                    params=params,
                    timeout=20,
                )
                status = process_updates(resp)
                if status is not None:
                    return status
            except Exception as exc:
                print(f"  ⚠️  getUpdates error: {exc}")

            time.sleep(poll_interval)

        try:
            resp = requests.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={
                    "timeout": 5,
                    "offset": last_update_id + 1 if last_update_id else -20,
                },
                timeout=20,
            )
            status = process_updates(resp)
            if status is not None:
                return status
        except Exception as exc:
            print(f"  ⚠️  getUpdates error: {exc}")

        print(f"  🔍 _wait_for_callback() returning EXPIRED — elapsed={time.time()-start:.1f}s")
        return ApprovalStatus.EXPIRED

    # ------------------------------------------------------------------
    # SHEETS — read leads
    # ------------------------------------------------------------------

    def get_hot_leads_from_sheets(self) -> list[Lead]:
        """Read HOT leads with a domain from the Leads tab.

        Reads through col P (owner_email). If col P is populated by the Lead
        Generator, the row is eligible for founder review. Missing owner_email
        rows are rejected later by the incomplete-record filter.
        """
        if not self.sheet_id or not self.service_account_json:
            print("⚠️  Sheets not configured — no leads to process")
            return []
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds = service_account.Credentials.from_service_account_info(
                json.loads(self.service_account_json),
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            service = build("sheets", "v4", credentials=creds)
            self._sheets_service = service

            result = service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Leads!A2:P",
            ).execute()
            rows = result.get("values", [])
            leads = []
            for i, row in enumerate(rows):
                if len(row) <= COL["score"]:
                    continue
                score = row[COL["score"]] if len(row) > COL["score"] else ""
                if score != "HOT":
                    continue
                # Skip rows already processed by Sales Agent (col O)
                if len(row) > COL["notified"] and row[COL["notified"]].strip() == "Y":
                    continue
                domain = row[COL["domain"]].strip() if len(row) > COL["domain"] else ""
                if not domain:
                    continue
                # Read owner_email from col P if Lead Generator populated it
                owner_email = normalize_owner_email(
                    row[COL["owner_email"]].strip() if len(row) > COL["owner_email"] else ""
                ) or ""
                lead = Lead(
                    business=row[COL["name"]].strip() if len(row) > COL["name"] else "Local Business",
                    domain=domain,
                    phone=row[COL["phone"]] if len(row) > COL["phone"] else "",
                    address=row[COL["address"]] if len(row) > COL["address"] else "",
                    industry=row[COL["industry"]] if len(row) > COL["industry"] else "retail",
                    score=score,
                    yelp_rating=row[COL["yelp_rating"]] if len(row) > COL["yelp_rating"] else "",
                    sheet_row=i + 2,
                    owner_email=owner_email,
                    email_source="sheets" if owner_email else "",
                    email_confidence="HIGH" if owner_email else "NONE",
                )
                lead.lead_id = self._build_lead_id(lead)
                leads.append(lead)
            sheets_email_count = sum(1 for l in leads if l.owner_email)
            print(
                f"✅ Read {len(leads)} HOT leads with domain from Sheets "
                f"({sheets_email_count} already have owner_email in col P)"
            )
            return leads
        except Exception as e:
            print(f"❌ Sheets read error: {e}")
            return []

    # ------------------------------------------------------------------
    # OUTREACH LOG — deduplication + write
    # ------------------------------------------------------------------

    def _already_outreached(self, business_name: str) -> bool:
        """Return True if this business already has a row in Outreach Log."""
        if not self._sheets_service or not self.sheet_id:
            return False
        try:
            result = self._sheets_service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Outreach Log!B2:B",
            ).execute()
            rows = result.get("values", [])
            name_lower = business_name.strip().lower()
            return any(row and row[0].strip().lower() == name_lower for row in rows)
        except Exception as e:
            print(f"⚠️  Outreach Log check failed: {e}")
            return False

    def _log_outreach(
        self,
        business_name: str,
        email: str,
        subject: str,
        status: str,
        category: str = "",
        draft_variant: int = 0,
        pass_type: str = "first_pass",
    ) -> None:
        """Append one row to Outreach Log tab.

        Columns: timestamp | business_name | email | subject | status |
                 run_id | category | draft_variant | pass_type
        """
        if not self._sheets_service or not self.sheet_id:
            print("  ⚠️  Cannot log outreach — Sheets not connected")
            return
        timestamp = datetime.now(DETROIT).strftime("%Y-%m-%d %H:%M:%S %Z")
        delays = (2, 4, 8)
        last_exc: Exception | None = None
        for attempt, delay in enumerate(delays, start=1):
            try:
                self._sheets_service.spreadsheets().values().append(
                    spreadsheetId=self.sheet_id,
                    range="Outreach Log!A1",
                    valueInputOption="RAW",
                    insertDataOption="INSERT_ROWS",
                    body={"values": [[
                        timestamp, business_name, email, subject, status,
                        self.run_id, category, str(draft_variant), pass_type,
                    ]]},
                ).execute()
                print(f"  📋 Outreach Log: {business_name} → {status} (variant {draft_variant}, {pass_type})")
                return
            except Exception as exc:
                last_exc = exc
                print(f"  ⚠️  Outreach Log write failed (attempt {attempt}/3): {exc}")
                if attempt < len(delays):
                    time.sleep(delay)

        raise RuntimeError(f"Outreach Log write failed after 3 attempts: {last_exc}")

    def _mark_notified(self, sheet_row: int) -> None:
        """Write Y to column O of the given Leads row."""
        if not self._sheets_service or not self.sheet_id:
            return
        try:
            self._sheets_service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=f"Leads!O{sheet_row}",
                valueInputOption="RAW",
                body={"values": [["Y"]]},
            ).execute()
        except Exception as e:
            print(f"⚠️  _mark_notified failed for row {sheet_row}: {e}")

    # ------------------------------------------------------------------
    # DRAFT — H.O.O.K. framework with deterministic multi-axis variants
    # ------------------------------------------------------------------

    @staticmethod
    def _select_framework_variants(business: str, industry: str) -> tuple[dict[str, str], str]:
        """Select one instruction per framework section, deterministically.

        Returns (instructions_dict, variant_label).
        Variant label format: H{x}L{y}O{z}P{w}C{v} — traceable and loggable.
        """
        hooks = HOOK_VARIANTS.get(industry.lower(), DEFAULT_HOOKS)
        h = hash(business) % len(hooks)
        l = hash(business + "leak") % len(LEAK_VARIANTS)
        o = hash(business + "outcome") % len(OUTCOME_VARIANTS)
        p = hash(business + "proof") % len(PROOF_VARIANTS)
        c = hash(business + "cta") % len(CTA_VARIANTS)

        instructions = {
            "hook": hooks[h],
            "leak": LEAK_VARIANTS[l],
            "outcome": OUTCOME_VARIANTS[o],
            "proof": PROOF_VARIANTS[p],
            "cta": CTA_VARIANTS[c],
        }
        label = f"H{h}L{l}O{o}P{p}C{c}"
        return instructions, label

    def _draft_email(self, lead: Lead, variant: int) -> tuple[str, str, str]:
        """Draft a personalized email using the H.O.O.K. framework.

        Returns (subject, body, pass_type).
        pass_type encodes the framework version and variant trace:
        "hook_v1:H{x}L{y}O{z}P{w}C{v}" for Claude-generated,
        "static_fallback" when no API key is available.
        """
        if _anthropic is None or not self.anthropic_key:
            # Static fallback — no API key
            subject = f"Quick question about {lead.business}"
            body = (
                f"Hi there,\n\n"
                f"I noticed {lead.business} here in Detroit.\n\n"
                "I help local businesses set up simple tools that handle calls and bookings "
                "automatically so owners aren't tied to the phone all day.\n\n"
                "Have 10 minutes for a quick call this week?"
            )
            return subject, f"{body}\n\n{EMAIL_SIGNATURE}", "static_fallback"

        fw, label = self._select_framework_variants(lead.business, lead.industry)

        prompt = f"""Write a cold outreach email from Trendell Fordham of Genesis AI Systems to the owner of {lead.business}, a {lead.industry} business in Detroit.

Follow this exact 5-part structure. Each part should be 1 to 2 sentences. The full email body should be 5 to 8 sentences total.

1. HOOK — {fw['hook']}

2. LEAK — {fw['leak']}

3. OUTCOME — {fw['outcome']}

4. PROOF — {fw['proof']}

5. MICRO-CTA — {fw['cta']}

Greeting rule:
- Always begin the email with exactly: Hi there,
- Do NOT use the owner's personal name. You do not know it.
- Do NOT write "Dear [anything]" or "Hello [anything]".

Voice rules:
- Plain English. Write like one Detroit business owner talking to another.
- First-person singular only. Always use "I", never "we", "our", or "our team". This email is from one founder, not a company.
- Natural sentence variation. Mix short and medium sentences.
- No em dashes.
- Do NOT include a sign-off or signature. The signature block is appended automatically.
- Do NOT use section labels or numbers in the email. It should read as one natural flowing message.
- When referencing the business, use the actual business name "{lead.business}" — never a placeholder.

Hard sentence stop:
- Maximum 5 sentences before the signature. STOP at sentence 5.
- Do not add proof or extra reinforcement after sentence 5.
- An incomplete framework is acceptable. Hook + Leak + CTA are highest priority.
- If you cannot fit all 5 framework parts in 5 sentences, drop PROOF first, then OUTCOME.
- Do not add filler, extra explanation, or transition sentences.

Scenario hook constraint:
- If using a cinematic scene opening (e.g. "A customer's furnace stops working..."), the opening scene must be a maximum of 2 sentences total.
- Never use 3 or more sentences to set up the scenario.
- After the scene, move directly into the leak observation, then CTA.
- The full email must still stop at 5 sentences.

Paragraph format:
- Write in paragraphs of 2 to 3 sentences each.
- Never put every sentence on its own line.
- The email should visually read like a real business email, not a text thread.

Repetition control:
- Do NOT default to the same "after-hours / heat dies / three companies" scenario every time.
- Vary your entry point. Use a different angle, question, or observation than you would for the previous business.
- Each email should feel individually written, not batch-templated.

Placeholder ban:
- NEVER output square bracket placeholders like [Name], [Owner], [Business], [Phone], [Restaurant Name], [BUSINESS_PHONE_NUMBER], or any other [TOKEN].
- If you do not know a specific detail, omit it entirely. Do not insert a placeholder.

Phone ban:
- NEVER include a phone number anywhere in the email body.
- No callback numbers, no "call me at", no digits resembling a phone number.

Plain language lock:
- Use only words an HVAC owner or tech would actually say.
- Prefer: missed calls, booked jobs, after-hours calls, texts that come in at night.
- Do NOT use: overflow inquiries, qualified leads, missed moments, flagged inquiries, lead flow.

CTA time lock:
- Always ask for exactly "10 minutes". Never 15, never 20, never "a few minutes".

Hard rules — never use these words or phrases:
unlock, leverage, revolutionize, streamline, optimize, cutting-edge, game-changer, seamless, robust, end-to-end, solution, workflow, pipeline, platform, ecosystem, tech stack, automation stack, AI agents, digital transformation, I couldn't help but notice, I wanted to reach out, best-in-class, state-of-the-art, next-level, synergy

Banned trust-cliche phrases — never use any variation of:
without changing how you work, without changing how you operate, without forcing you to change, without changing how you run things, without asking you to change anything
Instead, build trust by being specific about what the system actually does.

Banned filler phrases — never use any variation of:
slips through the cracks, falls through the cracks, nothing slips through, nothing falls through
Use plain operational wording instead, like "so you don't miss anything" or "so nothing gets lost".

Quality check — before returning, verify:
1. Does it sound like a real person wrote it, not AI?
2. Is it specific to this business type, not generic?
3. Does it avoid all banned phrases above?
4. Is the LEAK observational and non-accusatory?
5. Is the PROOF truthful with no fabricated numbers or case studies?
6. Is the CTA soft and conversational, not a hard close?
7. Does the email flow naturally without visible section breaks?
8. Does it start with "Hi there," and NOT use any personal name?
9. Are there ZERO square bracket placeholders anywhere in the text?
10. Is there NO phone number anywhere in the body?
11. Is it first-person singular only (no "we", "our", "our team")?
12. Is it 5 sentences or fewer before the signature?
13. Does the opening feel distinct, not a copy of a batch template?
14. Does it avoid ALL banned trust-cliche phrases ("without changing how you...")?
15. Does it use plain spoken language only (no "overflow inquiries", "qualified leads", etc.)?
16. Does the CTA ask for exactly "10 minutes"?
17. Does it avoid "slips/falls through the cracks" and all variations?
18. Is it written in paragraphs (2-3 sentences each), not one-sentence-per-line?
19. If using a scenario/scene opening, is the scene 2 sentences or fewer?

If any check fails, rewrite before returning. Do not mention the checks.

Return in exactly this format:
SUBJECT: [subject line here]
BODY:
[email body here]"""

        client = _anthropic.Anthropic(api_key=self.anthropic_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        subject = f"Quick question about {lead.business}"
        body_lines: list[str] = []
        in_body = False
        for line in text.split("\n"):
            if line.startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
            elif line.strip() == "BODY:":
                in_body = True
            elif in_body:
                body_lines.append(line)

        body = "\n".join(body_lines).strip() or text
        return subject, f"{body}\n\n{EMAIL_SIGNATURE}", f"hook_v1:{label}"

    # ------------------------------------------------------------------
    # HUBSPOT — optional company record update
    # ------------------------------------------------------------------

    def save_to_hubspot(self, lead: Lead) -> None:
        if not self.hubspot_token:
            return
        try:
            resp = requests.post(
                "https://api.hubapi.com/crm/v3/objects/companies",
                headers={
                    "Authorization": f"Bearer {self.hubspot_token}",
                    "Content-Type": "application/json",
                },
                json={"properties": {
                    "name": lead.business,
                    "phone": lead.phone,
                    "city": "Detroit",
                    "state": "Michigan",
                    "industry": HUBSPOT_INDUSTRY_MAP.get(lead.industry.lower(), "OTHER"),
                    "description": (
                        f"Score: {lead.score}\n"
                        f"Domain: {lead.domain}\n"
                        f"Email: {lead.owner_email}\n"
                        f"Address: {lead.address}\n"
                        f"Yelp: {lead.yelp_rating} stars"
                    ),
                    "hs_lead_status": "IN_PROGRESS",
                }},
                timeout=15,
            )
            if resp.status_code in (200, 201):
                print(f"✅ {lead.business} saved to HubSpot")
            else:
                print(f"⚠️  HubSpot {resp.status_code} for {lead.business}: {resp.text[:200]}")
        except Exception as e:
            print(f"❌ HubSpot error for {lead.business}: {e}")


if __name__ == "__main__":
    SalesAgent().run()
