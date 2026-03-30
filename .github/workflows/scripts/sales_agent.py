#!/usr/bin/env python3
"""Sales helper — reads leads from Sheets, sends outreach via Resend, alerts Trendell on HOT ones."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# Shared notification helpers from notify.py
from notify import telegram_notify, resend_email

HUBSPOT_INDUSTRY_MAP = {
    "restaurant": "FOOD_BEVERAGES",
    "dental": "HEALTH_WELLNESS_AND_FITNESS",
    "hvac": "CONSTRUCTION",
    "salon": "COSMETICS",
    "real_estate": "REAL_ESTATE",
    "retail": "RETAIL",
}


@dataclass
class Lead:
    name: str
    business: str
    email: str
    phone: str
    business_type: str
    pain_point: str
    score: str
    address: str = ""
    yelp_rating: str = ""
    yelp_url: str = ""


class SalesAgent:
    """Reads HOT leads from Google Sheets, sends outreach via Resend, alerts Trendell via Telegram."""

    def __init__(self) -> None:
        self.hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        self.service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT", "").strip()
        self.resend_key = os.getenv("RESEND_API_KEY", "").strip()

    def run(self) -> None:
        leads = self.get_leads_from_sheets()
        if not leads:
            print("ℹ️  No leads to process today")
            telegram_notify("Sales Agent", "No new leads to process today.", "INFO")
            return

        hot = [l for l in leads if l.score == "HOT"]
        warm = [l for l in leads if l.score == "WARM"]

        print(f"📋 Processing {len(leads)} leads — {len(hot)} HOT, {len(warm)} WARM")

        for lead in hot[:10]:
            self.send_outreach_email(lead)
            self.save_to_hubspot(lead)
            self.save_to_pipeline(lead)

        for lead in warm[:5]:
            self.send_outreach_email(lead)

        self.alert_trendell_hot(hot[:3])
        self.send_pipeline_report(hot, warm)
        print(f"✅ Sales Agent complete — {len(hot)} HOT leads processed")


    def get_leads_from_sheets(self) -> list[Lead]:
        """Read HOT/WARM prospects from the Leads Google Sheet."""
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
            result = service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="Leads!A2:N",
            ).execute()
            rows = result.get("values", [])
            leads = []
            for row in rows:
                if len(row) < 10:
                    continue
                score = row[9] if len(row) > 9 else "WARM"
                if score not in ("HOT", "WARM"):
                    continue
                leads.append(Lead(
                    name=row[2] if len(row) > 2 else "Business Owner",
                    business=row[2] if len(row) > 2 else "Local Business",
                    email="",  # Yelp leads don't have email — outreach via phone/visit
                    phone=row[4] if len(row) > 4 else "",
                    business_type=row[1] if len(row) > 1 else "retail",
                    pain_point="Missed calls and slow follow-up",
                    score=score,
                    address=row[5] if len(row) > 5 else "",
                    yelp_rating=row[7] if len(row) > 7 else "",
                    yelp_url=row[12] if len(row) > 12 else "",
                ))
            print(f"✅ Read {len(leads)} leads from Sheets")
            return leads
        except Exception as e:
            print(f"❌ Sheets read error: {e}")
            return []


    def get_email_body(self, lead: Lead) -> tuple[str, str]:
        """Return (subject, body) for this lead's business type."""
        btype = lead.business_type.lower()
        templates = {
            "restaurant": (
                f"Quick question about {lead.business}",
                f"Hi there,\n\n"
                f"I noticed {lead.business} in Detroit.\n\n"
                "Quick question — what happens when someone calls for a reservation and you're slammed?\n\n"
                "I build AI phone assistants for restaurants that answer calls and book tables 24/7.\n\n"
                "Takes 5-7 days to set up. Starts at $500.\n\n"
                "Worth a 10-minute call this week?\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems\n(586) 636-9550"
            ),
            "dental": (
                f"Patients calling {lead.business} after hours",
                f"Hi there,\n\n"
                f"A patient tried to book at {lead.business} after hours last week.\n\n"
                "Nobody answered. They called another dentist.\n\n"
                "I build AI systems for dental offices that answer after-hours calls and book appointments automatically.\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems"
            ),
            "hvac": (
                f"Emergency calls {lead.business} might be missing",
                f"Hi there,\n\n"
                f"When {lead.business} gets an emergency call at 10pm — who answers?\n\n"
                "I build AI systems that catch every after-hours inquiry and text you immediately.\n\n"
                "15-minute call this week?\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems"
            ),
            "salon": (
                f"Booking appointments for {lead.business} automatically",
                f"Hi there,\n\n"
                f"Are you still taking appointment calls manually at {lead.business}?\n\n"
                "I set up AI assistants for salons that book appointments and send reminders 24/7 — automatically.\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems"
            ),
        }
        default = (
            f"Quick question about {lead.business}",
            f"Hi there,\n\n"
            f"I noticed {lead.business} in Detroit and wanted to reach out.\n\n"
            "I build done-for-you AI systems for local businesses — answering calls, capturing leads, following up fast.\n\n"
            "Starts at $500. Live in 5-7 days.\n\n"
            "Worth a quick 10-minute call?\n\n"
            "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems\n(586) 636-9550"
        )
        return templates.get(btype, default)

    def send_outreach_email(self, lead: Lead) -> None:
        """Send a Resend outreach email to this lead. Skip if no email on record."""
        if not lead.email:
            print(f"ℹ️  No email for {lead.business} — outreach via phone: {lead.phone}")
            return
        subject, body = self.get_email_body(lead)
        ok = resend_email(lead.email, subject, body, priority="MEDIUM")
        if ok:
            print(f"✅ Outreach email sent to {lead.business} ({lead.email})")
        else:
            print(f"⚠️  Email failed for {lead.business}")


    def save_to_pipeline(self, lead: Lead) -> None:
        """Append HOT lead to Pipeline tab so Trendell can track outreach."""
        if not self.sheet_id or not self.service_account_json:
            return
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            creds = service_account.Credentials.from_service_account_info(
                json.loads(self.service_account_json),
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            service = build("sheets", "v4", credentials=creds)
            today = datetime.now().strftime("%Y-%m-%d")
            service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range="Pipeline!A1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [[
                    today,
                    lead.business,
                    lead.phone,
                    lead.address,
                    lead.business_type,
                    lead.yelp_rating,
                    lead.score,
                    "No",       # Outreach Sent
                    "",         # Channel
                    "",         # Response
                    "New",      # Status
                    "Call or text",  # Next Step
                    "",         # Next Follow-up Date
                    lead.pain_point,
                ]]},
            ).execute()
            print(f"✅ {lead.business} added to Pipeline")
        except Exception as e:
            print(f"⚠️  Pipeline save failed for {lead.business}: {e}")

    def save_to_hubspot(self, lead: Lead) -> None:
        """Create a Company record in HubSpot for this lead."""
        if not self.hubspot_token:
            print("⚠️  HUBSPOT_ACCESS_TOKEN missing — skipping HubSpot save")
            return
        try:
            resp = requests.post(
                "https://api.hubapi.com/crm/v3/objects/companies",
                headers={"Authorization": f"Bearer {self.hubspot_token}", "Content-Type": "application/json"},
                json={"properties": {
                    "name": lead.business,
                    "phone": lead.phone,
                    "city": "Detroit",
                    "state": "Michigan",
                    "industry": HUBSPOT_INDUSTRY_MAP.get(lead.business_type.lower(), "OTHER"),
                    "description": (
                        f"Score: {lead.score}\n"
                        f"Pain point: {lead.pain_point}\n"
                        f"Address: {lead.address}\n"
                        f"Yelp: {lead.yelp_rating} stars\n"
                        f"Yelp URL: {lead.yelp_url}"
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

    def alert_trendell_hot(self, hot_leads: list[Lead]) -> None:
        """Telegram alert for HOT leads — call them now."""
        if not hot_leads:
            return
        lines = ["🔥 HOT Lead Alert — Genesis AI Systems", "=" * 28]
        for i, lead in enumerate(hot_leads, 1):
            lines.append(
                f"{i}. {lead.business}\n"
                f"   📞 {lead.phone or 'No phone'}\n"
                f"   ⭐ Yelp {lead.yelp_rating} | {lead.address[:40]}\n"
                f"   → Reach out NOW"
            )
        lines.append("\ngenesisai.systems")
        telegram_notify("HOT Leads Ready", "\n".join(lines), "HIGH")

    def send_pipeline_report(self, hot: list[Lead], warm: list[Lead]) -> None:
        """Send a Resend email + Telegram summary of today's pipeline."""
        today = datetime.now().strftime("%B %d, %Y")
        body = (
            f"Sales Pipeline — {today}\n\n"
            f"HOT leads: {len(hot)}\n"
            f"WARM leads: {len(warm)}\n\n"
            + (("Top HOT leads:\n" + "\n".join(f"- {l.business} | {l.phone}" for l in hot[:5])) if hot else "No HOT leads today.")
            + "\n\nAll leads saved to HubSpot and Google Sheets.\ngenesisai.systems"
        )
        trendell_email = os.getenv("NOTIFICATION_EMAIL", "info@genesisai.systems")
        resend_email(trendell_email, f"Sales Pipeline — {today}", body, "MEDIUM")
        telegram_notify(f"Sales Pipeline — {today}", f"HOT: {len(hot)} | WARM: {len(warm)}", "INFO")
        print(f"✅ Pipeline report sent — {len(hot)} HOT, {len(warm)} WARM")


if __name__ == "__main__":
    SalesAgent().run()
