#!/usr/bin/env python3
"""Sales Agent — Genesis AI Systems.

Reads HOT leads from Google Sheets Leads tab, enriches emails via Outscraper
(Hunter fallback), drafts personalized outreach via Claude Haiku, sends a
Telegram SEND/SKIP approval prompt to Trendell, delivers via Resend on approval,
and logs every outcome to the Outreach Log tab.

Approval gate: Trendell must reply SEND within 10 minutes. No email sends without it.
Max 3 outreach emails per run to keep the approval burden manageable.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# Shared notification helpers
from notify import telegram_notify, resend_email

# Outreach approval gate — Trendell must reply SEND before any email goes out
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
# A=date, B=industry, C=name, D=primary_domain, E=phone, F=address,
# G=employees, H=yelp_rating, I=yelp_reviews, J=score, K=reason,
# L=recommended_product, M=yelp_url, N=outreach_email_template, O=notified
COL = {
    "date": 0, "industry": 1, "name": 2, "domain": 3, "phone": 4,
    "address": 5, "employees": 6, "yelp_rating": 7, "yelp_reviews": 8,
    "score": 9, "reason": 10, "product": 11, "yelp_url": 12,
    "email_template": 13, "notified": 14,
}

# Industry-specific pain point framing for Claude prompt
INDUSTRY_CONTEXT = {
    "restaurant": "restaurants that miss reservation calls during the dinner rush",
    "dental": "dental offices that lose after-hours appointment requests",
    "hvac": "HVAC contractors that miss emergency calls overnight or on weekends",
    "salon": "salons still taking bookings manually by phone",
    "real_estate": "real estate agents slow to follow up on new leads",
    "retail": "retail stores that miss customer inquiries after hours",
}


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
    email: str = ""


class SalesAgent:
    """Reads HOT leads from Sheets, enriches email, drafts via Claude,
    sends Telegram approval prompt, delivers via Resend, logs result."""

    def __init__(self) -> None:
        self.hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        self.service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT", "").strip()
        self.resend_key = os.getenv("RESEND_API_KEY", "").strip()
        self.outscraper_key = os.getenv("OUTSCRAPER_API_KEY", "").strip()
        self.hunter_key = os.getenv("HUNTER_API_KEY", "").strip()
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.run_id = os.getenv("GITHUB_RUN_ID", f"local-{int(time.time())}")
        self._sheets_service = None
        self._flow = ApprovalFlow()

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------

    def run(self) -> None:
        leads = self.get_hot_leads_from_sheets()
        if not leads:
            print("ℹ️  No HOT leads with domain found in Sheets")
            telegram_notify("Sales Agent", "No HOT leads with domain to process today.", "INFO")
            return

        print(f"📋 Found {len(leads)} HOT leads with domain — processing up to 3")
        sent_count = 0

        for lead in leads:
            if sent_count >= 3:
                print("ℹ️  Reached 3-lead limit for this run")
                break

            # Deduplication: skip if already in Outreach Log
            if self._already_outreached(lead.business):
                print(f"  ⏭️  {lead.business} already in Outreach Log — skipping")
                continue

            # Enrich email via Outscraper (Hunter fallback)
            email = self._enrich_email(lead.domain)
            if not email:
                print(f"  ℹ️  No email found for {lead.business} ({lead.domain}) — skipping")
                continue
            lead.email = email

            # Draft personalized email with Claude Haiku
            try:
                subject, body = self._draft_email(lead)
            except Exception as exc:
                print(f"  ⚠️  Draft failed for {lead.business}: {exc} — skipping")
                continue

            # Send Telegram approval prompt; wait up to 10 min for SEND/SKIP
            req = self._flow.request_approval(
                action_type=ActionType.OUTREACH,
                target_name=lead.business,
                target_email=email,
                preview=f"Subject: {subject}\n\n{body[:250]}",
            )
            status = self._flow.wait_for_approval(
                req.request_id, timeout_seconds=600, poll_interval=15
            )

            if status == ApprovalStatus.APPROVED:
                ok = resend_email(email, subject, body, priority="MEDIUM")
                log_status = "sent" if ok else "failed"
                if ok:
                    print(f"  ✅ Email sent to {lead.business} ({email})")
                    sent_count += 1
                else:
                    print(f"  ⚠️  Resend failed for {lead.business}")
            elif status == ApprovalStatus.SKIPPED:
                log_status = "skipped"
                print(f"  ⏭️  Skipped by founder: {lead.business}")
            else:
                log_status = "timeout"
                print(f"  ⏰ No response in 10 minutes: {lead.business}")

            self._log_outreach(lead.business, email, subject, log_status)
            self._mark_notified(lead.sheet_row)

        print(f"✅ Sales Agent complete — {sent_count} email(s) sent this run")

    # ------------------------------------------------------------------
    # SHEETS — read leads
    # ------------------------------------------------------------------

    def get_hot_leads_from_sheets(self) -> list[Lead]:
        """Read HOT leads that have a primary_domain from the Leads tab."""
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
                range="Leads!A2:O",
            ).execute()
            rows = result.get("values", [])
            leads = []
            for i, row in enumerate(rows):
                if len(row) <= COL["score"]:
                    continue
                score = row[COL["score"]] if len(row) > COL["score"] else ""
                if score != "HOT":
                    continue
                # Skip rows already marked notified (col O)
                if len(row) > COL["notified"] and row[COL["notified"]].strip() == "Y":
                    continue
                domain = row[COL["domain"]].strip() if len(row) > COL["domain"] else ""
                if not domain:
                    continue
                leads.append(Lead(
                    business=row[COL["name"]].strip() if len(row) > COL["name"] else "Local Business",
                    domain=domain,
                    phone=row[COL["phone"]] if len(row) > COL["phone"] else "",
                    address=row[COL["address"]] if len(row) > COL["address"] else "",
                    industry=row[COL["industry"]] if len(row) > COL["industry"] else "retail",
                    score=score,
                    yelp_rating=row[COL["yelp_rating"]] if len(row) > COL["yelp_rating"] else "",
                    sheet_row=i + 2,  # +2: 1-based index + header row
                ))
            print(f"✅ Read {len(leads)} HOT leads with domain from Sheets")
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
            return any(
                row and row[0].strip().lower() == name_lower
                for row in rows
            )
        except Exception as e:
            print(f"⚠️  Outreach Log check failed: {e}")
            return False

    def _log_outreach(
        self, business_name: str, email: str, subject: str, status: str
    ) -> None:
        """Append one row to Outreach Log: timestamp|business|email|subject|status|run_id."""
        if not self._sheets_service or not self.sheet_id:
            print(f"  ⚠️  Cannot log outreach — Sheets not connected")
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self._sheets_service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range="Outreach Log!A1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [[timestamp, business_name, email, subject, status, self.run_id]]},
            ).execute()
            print(f"  📋 Outreach Log: {business_name} → {status}")
        except Exception as e:
            print(f"  ⚠️  Outreach Log write failed: {e}")

    def _mark_notified(self, sheet_row: int) -> None:
        """Write Y to column O of the given Leads row to suppress re-processing."""
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
    # EMAIL ENRICHMENT — Outscraper primary, Hunter fallback
    # ------------------------------------------------------------------

    def _enrich_email(self, domain: str) -> str:
        """Return first valid email address for domain, or empty string."""
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
                                print(f"  📧 Outscraper → {domain}: {val}")
                                return str(val)
                    print(f"  ℹ️  Outscraper: no email for {domain}")
                else:
                    print(f"  ⚠️  Outscraper {resp.status_code} for {domain}")
            except Exception as exc:
                print(f"  ⚠️  Outscraper exception for {domain}: {exc}")
        else:
            print("  ℹ️  OUTSCRAPER_API_KEY not set — skipping Outscraper")

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
                            print(f"  📧 Hunter → {domain}: {val}")
                            return val
                    print(f"  ℹ️  Hunter: no email for {domain}")
            except Exception as exc:
                print(f"  ⚠️  Hunter exception for {domain}: {exc}")

        print(f"  ❌ No email found for {domain}")
        return ""

    # ------------------------------------------------------------------
    # DRAFT — Claude Haiku personalized email
    # ------------------------------------------------------------------

    def _draft_email(self, lead: Lead) -> tuple[str, str]:
        """Draft a short personalized outreach email using Claude Haiku.

        Falls back to a static template if ANTHROPIC_API_KEY is missing.
        """
        if _anthropic is None or not self.anthropic_key:
            subject = f"Quick question about {lead.business}"
            body = (
                f"Hi there,\n\n"
                f"I noticed {lead.business} here in Detroit and wanted to reach out.\n\n"
                "I help local businesses set up simple tools that answer calls, book appointments, "
                "and follow up with customers automatically — so nothing falls through the cracks.\n\n"
                "Would you have 10 minutes this week for a quick call?\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems"
            )
            return subject, body

        context = INDUSTRY_CONTEXT.get(
            lead.industry.lower(),
            "local businesses that miss customer calls and inquiries",
        )
        prompt = (
            f"Write a cold outreach email from Trendell Fordham of Genesis AI Systems "
            f"to the owner of {lead.business}, a {lead.industry} business in Detroit.\n\n"
            f"Context: You help {context}.\n\n"
            "Rules:\n"
            "- Plain English only. No jargon. No phrases like 'AI agents', 'automation pipeline', or 'tech stack'\n"
            "- Sound like one Detroit entrepreneur talking to another — not a tech salesperson\n"
            "- 3 to 5 sentences for the body, no more\n"
            "- One clear, specific pain point relevant to their industry\n"
            "- Soft CTA: ask for a 10-minute call, not a sale\n"
            "- Sign off as: Trendell Fordham, Genesis AI Systems, genesisai.systems\n\n"
            "Return in exactly this format — no extra commentary:\n"
            "SUBJECT: [subject line]\n"
            "BODY:\n"
            "[email body]"
        )

        client = _anthropic.Anthropic(api_key=self.anthropic_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
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
        return subject, body

    # ------------------------------------------------------------------
    # HUBSPOT — create/update company record
    # ------------------------------------------------------------------

    def save_to_hubspot(self, lead: Lead) -> None:
        """Create a Company record in HubSpot for this lead."""
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
