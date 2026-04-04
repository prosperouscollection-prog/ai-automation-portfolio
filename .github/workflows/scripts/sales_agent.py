#!/usr/bin/env python3
"""Sales Agent — Genesis AI Systems.

Reads HOT leads from Google Sheets (Leads tab), uses owner_email from col P
if Lead Generator already enriched it, falls back to Outscraper + Hunter only
if col P is empty. Drafts personalized outreach via Claude Haiku using
controlled variation (5 patterns per industry). Sends Telegram SEND/SKIP
approval prompt. Delivers via Resend on approval. Logs to Outreach Log tab.

Approval gate: Trendell must reply SEND within 10 minutes. No email sends without it.
Limit: 3 leads processed per run (regardless of send/skip/timeout outcome).
"""

from __future__ import annotations

import json
import hashlib
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DETROIT = ZoneInfo("America/Detroit")

import requests
from dotenv import load_dotenv

load_dotenv()

# Shared notification helpers
from notify import telegram_notify, resend_email

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
VARIANT_OPENERS: dict[str, list[str]] = {
    "restaurant": [
        "Open with a question about what happens when someone tries to book a table during a busy service and nobody picks up the phone.",
        "Open with a quick observation: most Detroit restaurants lose reservations they never knew they missed.",
        "Open with a short, specific scenario — someone drives by, decides to call ahead for a table, gets no answer, and goes somewhere else.",
        "Open direct: tell them what you do in one sentence, then connect it to one problem restaurants specifically deal with.",
        "Open with a blunt question about whether they have someone covering the phone during rush hours.",
    ],
    "dental": [
        "Open with a question about what happens when a patient calls to book an appointment after the office closes.",
        "Open with a short scenario: a new patient searches for a dentist, calls after hours, nobody answers, they call the next one on the list.",
        "Open direct: one sentence on what you do, then tie it to the specific problem dental offices have with after-hours calls.",
        "Open with an observation about how dental offices lose new patients not because of their work but because of missed calls.",
        "Open with a question about whether the front desk can realistically catch every incoming call on a busy day.",
    ],
    "hvac": [
        "Open with a question about what happens when an emergency call comes in late on a Friday night.",
        "Open with a blunt observation: HVAC contractors miss jobs because they miss calls, not because they lack skill.",
        "Open with a short scenario — a homeowner's heat goes out at 10pm, they call three companies, the first one to respond gets the job.",
        "Open direct: one sentence on what you do, then connect it to the specific timing problem HVAC work has.",
        "Open with a question about how many after-hours calls they catch versus how many go to voicemail.",
    ],
    "salon": [
        "Open with a question about how many booking calls they miss when they're in the middle of a cut.",
        "Open with a short observation: most salons still take bookings by phone, which means every unanswered call is a missed appointment.",
        "Open with a scenario — someone tries to book on a Saturday afternoon, calls go unanswered, they book at another salon.",
        "Open direct: one sentence on what you do, then connect it to the booking problem salons deal with.",
        "Open with a question about whether clients ever show up for appointments they thought they booked but didn't confirm.",
    ],
    "real_estate": [
        "Open with a question about what happens when a buyer calls at 9pm and nobody follows up until the next morning.",
        "Open with a short observation: in real estate, the first agent to respond usually wins the client.",
        "Open with a scenario — a buyer submits an online inquiry, waits two hours, and signs with whoever called first.",
        "Open direct: one sentence on what you do, then connect it to lead response time specifically.",
        "Open with a question about their average time to follow up on a new inquiry.",
    ],
    "retail": [
        "Open with a question about what happens when a customer calls after hours to ask if something's in stock.",
        "Open with an observation about how retail shops lose customers over simple unanswered questions.",
        "Open with a scenario — a customer wants to check hours or availability, can't reach anyone, and orders online instead.",
        "Open direct: one sentence on what you do, then connect it to after-hours customer inquiries.",
        "Open with a question about whether they have a way to handle customer questions outside business hours.",
    ],
}

DEFAULT_OPENERS = [
    "Open with a question about what happens when a customer tries to reach them and nobody answers.",
    "Open with a short observation about local businesses that lose customers over missed calls.",
    "Open with a brief scenario showing a customer going elsewhere because they couldn't reach them.",
    "Open direct: one sentence on what you do, then connect it to a specific gap local businesses deal with.",
    "Open with a question about whether they have anyone covering inquiries outside of business hours.",
]

REPO_ROOT = Path(__file__).resolve().parents[3]
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
    email: str = ""          # populated from col P if available, then by enrichment
    email_source: str = ""   # "sheets" or "enrichment"


class SalesAgent:
    """Reads HOT leads from Sheets, enriches email if needed, drafts via
    Claude with variation, sends Telegram approval, delivers via Resend,
    logs every outcome to Outreach Log tab. Max 3 leads per run."""

    def __init__(self) -> None:
        self.hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        self.service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT", "").strip()
        self.resend_key = os.getenv("RESEND_API_KEY", "").strip()
        self.outscraper_key = os.getenv("OUTSCRAPER_API_KEY", "").strip()
        self.hunter_key = os.getenv("HUNTER_API_KEY", "").strip()
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.run_id = os.getenv("GITHUB_RUN_ID", f"local-{int(time.time())}")
        self.launch_state_path = Path(
            os.getenv(
                "PROJECT9_OUTBOUND_LAUNCH_STATE_PATH",
                str(DEFAULT_PROJECT9_LAUNCH_STATE_PATH),
            )
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
        self._sheets_service = None
        self._flow = ApprovalFlow()

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------

    def run(self) -> None:
        self.resolve_launch_state()
        self._ensure_first_10_event_feed()
        leads = self.get_hot_leads_from_sheets()
        if not leads:
            print("ℹ️  No HOT leads with domain found in Sheets")
            telegram_notify("Sales Agent", "No HOT leads with domain to process today.", "INFO")
            return

        print(f"📋 Found {len(leads)} HOT leads with domain — processing up to 3")
        processed_count = 0  # counts every lead that enters the approval flow

        for lead in leads:
            if processed_count >= 3:
                print("ℹ️  Reached 3-lead limit for this run")
                break

            # Deduplication: skip if already in Outreach Log
            if self._already_outreached(lead.business):
                print(f"  ⏭️  {lead.business} already in Outreach Log — skipping")
                continue

            # Use owner_email from Sheets (col P) if Lead Generator enriched it.
            # Fall back to re-enrichment only if col P is empty.
            if lead.email:
                print(f"  ✉️  Using owner_email from Sheets for {lead.business}: {lead.email}")
                lead.email_source = "sheets"
            elif lead.domain:
                lead.email = self._enrich_email(lead.domain)
                lead.email_source = "enrichment"

            if not lead.email:
                print(f"  ℹ️  No email for {lead.business} — skipping")
                continue

            # Select draft variant (1–5) deterministically per business name
            variant = (hash(lead.business) % 5) + 1

            # Draft personalized email via Claude Haiku
            try:
                subject, body, pass_type = self._draft_email(lead, variant)
            except Exception as exc:
                print(f"  ⚠️  Draft failed for {lead.business}: {exc} — skipping")
                continue

            # Send Telegram approval prompt + attach inline buttons, then wait
            req = self._flow.request_approval(
                action_type=ActionType.OUTREACH,
                target_name=lead.business,
                target_email=lead.email,
                preview=f"Subject: {subject}\n\n{body[:280]}",
            )
            self._attach_approval_buttons(req.message_id)
            status = self._wait_for_callback(req.message_id, timeout_seconds=600)

            # Act on founder decision — full side effects before any UI response
            if status == ApprovalStatus.APPROVED:
                try:
                    self._assert_outbound_launch_allowed(lead.business)
                except RuntimeError as exc:
                    log_status = "blocked_launch_state"
                    print(f"  ⛔ Send blocked for {lead.business}: {exc}")
                    self._log_outreach(
                        lead.business,
                        lead.email,
                        subject,
                        log_status,
                        category=lead.industry,
                        draft_variant=variant,
                        pass_type=pass_type,
                    )
                    self._mark_notified(lead.sheet_row)
                    print(f"  📋 Blocked lead logged and marked: {lead.business}")
                    self._telegram_confirm(
                        f"⛔ Send blocked for {lead.business}.\n\n"
                        f"Reason: {exc}\n"
                        f"Reply /leads to continue."
                    )
                    processed_count += 1
                    continue

                ok = resend_email(lead.email, subject, body, priority="MEDIUM")
                log_status = "sent" if ok else "failed"
                print(f"  {'✅' if ok else '⚠️ '} Resend {'sent' if ok else 'FAILED'}: {lead.business} ({lead.email})")
                self._record_first_10_send_event(
                    lead=lead,
                    subject=subject,
                    body=body,
                    delivery_ok=ok,
                )
            elif status == ApprovalStatus.SKIPPED:
                log_status = "skipped"
                print(f"  ⏭️  Skipped by founder: {lead.business}")
            else:
                log_status = "timeout"
                print(f"  ⏰ No response in 10 minutes: {lead.business}")

            # Side effects first: log row + notified flag
            self._log_outreach(
                lead.business, lead.email, subject, log_status,
                category=lead.industry, draft_variant=variant, pass_type=pass_type,
            )
            self._mark_notified(lead.sheet_row)
            print(f"  📤 approval action complete: {log_status}")

            # Telegram confirmation only after all side effects finish
            if status == ApprovalStatus.APPROVED:
                if log_status == "sent":
                    self._telegram_confirm(
                        f"✅ Email sent to {lead.business} ({lead.email}).\n\n"
                        f"Reply /leads for today's pipeline or /pipeline for deal status."
                    )
                else:
                    self._telegram_confirm(
                        f"⚠️ Email FAILED for {lead.business}. Resend error. "
                        f"Reply /leads to continue."
                    )
            elif status == ApprovalStatus.SKIPPED:
                self._telegram_confirm(
                    f"⏭️ Skipped {lead.business}. No email sent.\n\n"
                    f"Reply /leads for today's pipeline or /pipeline for deal status."
                )
            else:
                self._telegram_confirm(
                    f"⏰ No response for {lead.business} after 10 minutes. Email not sent, logged as timeout."
                )

            processed_count += 1  # increment for every lead that completed the flow

        print(f"✅ Sales Agent complete — {processed_count} lead(s) processed this run")

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
            f"resend-{self.run_id}-{attempt_number}-{self._hash_text(lead.email.lower())[:12]}"
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
            "recipient_hash": self._hash_text(lead.email.strip().lower()),
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
        """Edit the approval message to add inline SEND / SKIP buttons.

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
                            {"text": "✅ SEND", "callback_data": "send"},
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
        timeout_seconds: int = 120,
        poll_interval: int = 15,
    ) -> ApprovalStatus:
        """Poll getUpdates for SEND/SKIP as either callback_query or text reply.

        Answers the callback_query immediately so the Telegram spinner clears
        and the action branch runs before the Command Center can respond.
        Text reply detection is kept as a fallback for non-button responses.
        """
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if not token or not chat:
            return ApprovalStatus.EXPIRED

        start = time.time()
        last_update_id = 0

        def process_updates(resp: requests.Response) -> ApprovalStatus | None:
            nonlocal last_update_id
            if not resp.ok:
                return None
            for update in resp.json().get("result", []):
                last_update_id = max(last_update_id, update.get("update_id", 0))

                # --- inline keyboard callback_query (primary path) ---
                cq = update.get("callback_query", {})
                if cq:
                    cq_chat = str(cq.get("message", {}).get("chat", {}).get("id", ""))
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
                        if any(kw in data for kw in ("send", "yes", "approve")):
                            return ApprovalStatus.APPROVED
                        if any(kw in data for kw in ("skip", "no", "pass")):
                            return ApprovalStatus.SKIPPED

                # --- plain text reply (fallback) ---
                msg = update.get("message", {})
                if msg and str(msg.get("chat", {}).get("id", "")) == chat:
                    if message_id and msg.get("message_id", 0) > message_id:
                        text = msg.get("text", "").strip().lower()
                        if any(kw in text for kw in ("send", "yes", "approve")):
                            return ApprovalStatus.APPROVED
                        if any(kw in text for kw in ("skip", "no", "pass")):
                            return ApprovalStatus.SKIPPED
            return None

        while time.time() - start < timeout_seconds:
            try:
                params = {
                    "timeout": 5,
                    "offset": last_update_id + 1 if last_update_id else -20,
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

        return ApprovalStatus.EXPIRED

    # ------------------------------------------------------------------
    # SHEETS — read leads
    # ------------------------------------------------------------------

    def get_hot_leads_from_sheets(self) -> list[Lead]:
        """Read HOT leads with a domain from the Leads tab.

        Reads through col P (owner_email). If col P is populated by the Lead
        Generator, no re-enrichment is needed. If empty, Sales Agent enriches.
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
                owner_email = row[COL["owner_email"]].strip() if len(row) > COL["owner_email"] else ""
                leads.append(Lead(
                    business=row[COL["name"]].strip() if len(row) > COL["name"] else "Local Business",
                    domain=domain,
                    phone=row[COL["phone"]] if len(row) > COL["phone"] else "",
                    address=row[COL["address"]] if len(row) > COL["address"] else "",
                    industry=row[COL["industry"]] if len(row) > COL["industry"] else "retail",
                    score=score,
                    yelp_rating=row[COL["yelp_rating"]] if len(row) > COL["yelp_rating"] else "",
                    sheet_row=i + 2,
                    email=owner_email,
                ))
            sheets_email_count = sum(1 for l in leads if l.email)
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
    # EMAIL ENRICHMENT — fallback only (Lead Generator is primary owner)
    # ------------------------------------------------------------------

    def _enrich_email(self, domain: str) -> str:
        """Return first valid email address for domain.

        Called only when owner_email is not in Sheets col P.
        Outscraper primary, Hunter fallback.
        """
        if self.outscraper_key:
            try:
                resp = requests.get(
                    "https://api.app.outscraper.com/emails-and-contacts",
                    headers={"X-API-KEY": self.outscraper_key},
                    params={"query": domain, "async": "false"},
                    timeout=30,
                )
                if resp.ok:
                    raw = resp.json().get("data", [])
                    records = raw[0] if raw and isinstance(raw[0], list) else raw
                    if records and isinstance(records, list):
                        emails = records[0].get("emails", []) or []
                        for entry in emails:
                            val = entry.get("value", "") if isinstance(entry, dict) else entry
                            if val and "@" in str(val):
                                print(f"  📧 Outscraper fallback → {domain}: {val}")
                                return str(val)
                    print(f"  ℹ️  Outscraper: no email for {domain}")
                else:
                    print(f"  ⚠️  Outscraper {resp.status_code} for {domain}")
            except Exception as exc:
                print(f"  ⚠️  Outscraper exception for {domain}: {exc}")

        if self.hunter_key:
            try:
                resp = requests.get(
                    "https://api.hunter.io/v2/domain-search",
                    params={"domain": domain, "api_key": self.hunter_key, "limit": 5},
                    timeout=15,
                )
                if resp.ok:
                    emails = resp.json().get("data", {}).get("emails", [])
                    if emails:
                        val = emails[0].get("value", "")
                        if val:
                            print(f"  📧 Hunter fallback → {domain}: {val}")
                            return val
                    print(f"  ℹ️  Hunter: no email for {domain}")
            except Exception as exc:
                print(f"  ⚠️  Hunter exception for {domain}: {exc}")

        print(f"  ❌ No email found for {domain}")
        return ""

    # ------------------------------------------------------------------
    # DRAFT — Claude Haiku with controlled variation + quality check
    # ------------------------------------------------------------------

    def _draft_email(self, lead: Lead, variant: int) -> tuple[str, str, str]:
        """Draft a short personalized email. Returns (subject, body, pass_type).

        Uses one of 5 controlled opening patterns per industry so messages
        don't all read the same. Includes a built-in quality check and rewrite
        instruction inside the prompt.
        """
        if _anthropic is None or not self.anthropic_key:
            # Static fallback — no API key
            subject = f"Quick question about {lead.business}"
            body = (
                f"Hi there,\n\n"
                f"I noticed {lead.business} here in Detroit.\n\n"
                "I help local businesses set up simple tools that handle calls and bookings "
                "automatically so owners aren't tied to the phone all day.\n\n"
                "Have 10 minutes for a quick call this week?\n\n"
                "Trendell\nGenesis AI Systems\ngenesisai.systems"
            )
            return subject, body, "static_fallback"

        openers = VARIANT_OPENERS.get(lead.industry.lower(), DEFAULT_OPENERS)
        opening_instruction = openers[(variant - 1) % len(openers)]

        prompt = f"""Write a cold outreach email from Trendell Fordham of Genesis AI Systems to the owner of {lead.business}, a {lead.industry} business in Detroit.

Opening instruction (follow this for the first sentence or two):
{opening_instruction}

Requirements:
- 3 to 5 sentences for the body. No more.
- Plain English. Write like one Detroit business owner talking to another.
- One specific value statement relevant to this exact type of business.
- Soft CTA: ask for a 10-minute call. Do not pitch a sale.
- Sign off: Trendell, Genesis AI Systems, genesisai.systems
- No em dashes.

Hard rules — never use these words or phrases:
unlock, leverage, revolutionize, streamline, optimize, cutting-edge, game-changer, seamless, robust, end-to-end, solution, workflow, pipeline, platform, ecosystem, tech stack, automation stack, AI agents, digital transformation

Before returning your draft, check it against this list:
1. Does it sound human, not AI-generated?
2. Is it specific to this lead's business type, not generic?
3. Does it avoid all the banned phrases above?
4. Is there one clear value statement?
5. Is the CTA soft and specific?

If your draft fails any check, rewrite it before returning. Do not mention the quality check in your response.

Return in exactly this format:
SUBJECT: [subject line here]
BODY:
[email body here]"""

        client = _anthropic.Anthropic(api_key=self.anthropic_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=450,
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
        return subject, body, "first_pass"

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
                        f"Email: {lead.email}\n"
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
