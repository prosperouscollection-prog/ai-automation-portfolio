#!/usr/bin/env python3
"""Morning prospect finder for Genesis AI Systems."""

from __future__ import annotations

import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

INDUSTRIES_SCHEDULE = {
    0: {"industry": "restaurant", "keywords": ["restaurant", "cafe", "diner", "bistro"]},
    1: {"industry": "dental", "keywords": ["dental", "dentist", "orthodontist"]},
    2: {"industry": "hvac", "keywords": ["hvac", "heating", "cooling", "air conditioning"]},
    3: {"industry": "salon", "keywords": ["salon", "barbershop", "hair", "beauty"]},
    4: {"industry": "real_estate", "keywords": ["realtor", "real estate", "properties"]},
    5: {"industry": "retail", "keywords": ["boutique", "shop", "store", "retail"]},
    6: {"industry": "mixed", "keywords": ["local business", "small business"]},
}


class LeadGeneratorAgent:
    """Find local businesses, score them, and push hot leads to HubSpot + Sheets."""

    def __init__(self) -> None:
        self.apollo_key = os.getenv("APOLLO_API_KEY", "").strip()
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        self.service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT", "").strip()

    def run(self) -> None:
        day = datetime.now().weekday()
        schedule = INDUSTRIES_SCHEDULE[day]
        industry = schedule["industry"]
        print(f"🔍 Searching for {industry} businesses in Detroit...")

        # --- Apollo search ---
        prospects = []
        if not self.apollo_key:
            print("⚠️  APOLLO_API_KEY is missing or empty — skipping real search")
        else:
            prospects = self.search_apollo(industry, schedule["keywords"])

        if not prospects:
            print("⚠️  No Apollo results — falling back to mock data for testing")
            prospects = self.get_mock_prospects(industry)

        scored = self.score_prospects(prospects)
        hot = [p for p in scored if p["score"] == "HOT"]

        self.save_to_sheets(scored, industry)
        self.save_to_hubspot(hot)
        self.notify_trendell(hot[:3], industry)
        self.generate_outreach(hot[:5], industry)

        print(f"✅ Found {len(prospects)} prospects")
        print(f"🔥 HOT leads: {len(hot)}")

    def search_apollo(self, industry: str, keywords: list[str]) -> list[dict]:
        """Search Apollo.io for Detroit businesses in this industry."""
        try:
            response = requests.post(
                "https://api.apollo.io/v1/mixed_companies/search",
                headers={
                    "Content-Type": "application/json",
                    "X-Api-Key": self.apollo_key,
                },
                json={
                    "q_organization_name": "",
                    "organization_locations": ["Detroit, Michigan, United States"],
                    "organization_keyword_tags": keywords,
                    "page": 1,
                    "per_page": 25,
                },
                timeout=30,
            )
            if response.status_code == 401:
                print(f"❌ Apollo auth failed (401) — check APOLLO_API_KEY secret")
                return []
            if response.status_code == 422:
                print(f"❌ Apollo rejected request (422) — check payload format")
                print(f"   Response: {response.text[:300]}")
                return []
            if not response.ok:
                print(f"❌ Apollo error {response.status_code}: {response.text[:300]}")
                return []
            data = response.json()
            orgs = data.get("organizations", [])
            print(f"✅ Apollo returned {len(orgs)} organizations")
            return orgs
        except Exception as error:
            print(f"❌ Apollo exception: {error}")
            return []

    def get_mock_prospects(self, industry: str) -> list[dict]:
        return [
            {
                "name": f"Sample {industry.title()} Business",
                "primary_domain": "example.com",
                "phone": "(313) 555-0100",
                "estimated_num_employees": 5,
                "city": "Detroit",
                "industry": industry,
            },
            {
                "name": f"Metro {industry.title()} Group",
                "primary_domain": "metro-example.com",
                "phone": "(313) 555-0101",
                "estimated_num_employees": 12,
                "city": "Detroit",
                "industry": industry,
            },
        ]

    def score_prospects(self, prospects: list[dict]) -> list[dict]:
        scored = []
        for prospect in prospects:
            employees = prospect.get("estimated_num_employees", 0) or 0
            if 2 <= employees <= 50:
                prospect["score"] = "HOT"
                prospect["reason"] = "Right-sized local business — likely missing calls"
                prospect["recommended_product"] = "Starter Package — $500 setup, $150/mo"
            else:
                prospect["score"] = "WARM"
                prospect["reason"] = "Could be a fit with follow-up"
                prospect["recommended_product"] = "Lead Capture System"
            scored.append(prospect)
        return scored

    # ------------------------------------------------------------------
    # REAL HubSpot save — creates a Company record for each HOT lead
    # ------------------------------------------------------------------
    def save_to_hubspot(self, prospects: list[dict]) -> None:
        if not self.hubspot_token:
            print("⚠️  HUBSPOT_ACCESS_TOKEN missing — skipping HubSpot save")
            return
        if not prospects:
            print("ℹ️  No HOT prospects to save to HubSpot")
            return

        headers = {
            "Authorization": f"Bearer {self.hubspot_token}",
            "Content-Type": "application/json",
        }
        saved = 0
        for prospect in prospects:
            try:
                payload = {
                    "properties": {
                        "name": prospect.get("name", "Unknown"),
                        "domain": prospect.get("primary_domain", ""),
                        "phone": prospect.get("phone", ""),
                        "city": prospect.get("city", "Detroit"),
                        "industry": prospect.get("industry", ""),
                        "numberofemployees": str(prospect.get("estimated_num_employees", "")),
                        "description": (
                            f"Score: {prospect.get('score','')}\n"
                            f"Reason: {prospect.get('reason','')}\n"
                            f"Product: {prospect.get('recommended_product','')}"
                        ),
                        "hs_lead_status": "NEW",
                    }
                }
                response = requests.post(
                    "https://api.hubapi.com/crm/v3/objects/companies",
                    headers=headers,
                    json=payload,
                    timeout=15,
                )
                if response.status_code in (200, 201):
                    saved += 1
                else:
                    print(f"⚠️  HubSpot {response.status_code} for {prospect.get('name')}: {response.text[:200]}")
            except Exception as e:
                print(f"❌ HubSpot exception for {prospect.get('name')}: {e}")

        print(f"✅ Saved {saved}/{len(prospects)} HOT prospects to HubSpot")

    # ------------------------------------------------------------------
    # REAL Google Sheets save — appends all scored leads as rows
    # ------------------------------------------------------------------
    def save_to_sheets(self, prospects: list[dict], industry: str) -> None:
        if not self.sheet_id:
            print("⚠️  GOOGLE_SHEET_ID missing — skipping Sheets save")
            return
        if not self.service_account_json:
            print("⚠️  GOOGLE_SERVICE_ACCOUNT missing — skipping Sheets save")
            print("   Fix: Add a GOOGLE_SERVICE_ACCOUNT secret with your service account JSON")
            return
        try:
            import google.auth
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds_dict = json.loads(self.service_account_json)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            service = build("sheets", "v4", credentials=creds)
            today = datetime.now().strftime("%Y-%m-%d")
            rows = []
            for p in prospects:
                rows.append([
                    today,
                    industry,
                    p.get("name", ""),
                    p.get("primary_domain", ""),
                    p.get("phone", ""),
                    p.get("city", "Detroit"),
                    str(p.get("estimated_num_employees", "")),
                    p.get("score", ""),
                    p.get("reason", ""),
                    p.get("recommended_product", ""),
                    p.get("outreach_email", ""),
                ])
            service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range="Leads!A1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": rows},
            ).execute()
            print(f"✅ Saved {len(rows)} prospects to Google Sheets")
        except ImportError:
            print("⚠️  google-auth not installed — pip install google-auth google-api-python-client")
        except json.JSONDecodeError:
            print("❌ GOOGLE_SERVICE_ACCOUNT is not valid JSON — check your secret")
        except Exception as e:
            print(f"❌ Google Sheets error: {e}")

    def notify_trendell(self, hot_prospects: list[dict], industry: str) -> None:
        if not hot_prospects:
            print("ℹ️  No HOT leads — skipping notification")
            return

        lines = [
            "🎯 Lead Generator — Genesis AI Systems",
            f"Today: {industry.title()} businesses",
            f"Date: {datetime.now().strftime('%b %d')}",
            "=" * 28,
        ]
        for i, p in enumerate(hot_prospects, 1):
            lines.append(
                f"{i}. {p.get('name', 'Unknown')}\n"
                f"   {p.get('phone', 'No phone listed')}\n"
                f"   → {p.get('recommended_product', 'Starter')}"
            )
        lines.append("\nOutreach messages ready.")
        lines.append("genesisai.systems")
        message = "\n".join(lines)

        # Try Telegram first (working) — fall back to Twilio SMS
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        if telegram_token and telegram_chat:
            try:
                resp = requests.post(
                    f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                    json={"chat_id": telegram_chat, "text": message},
                    timeout=15,
                )
                if resp.ok:
                    print("✅ Morning alert sent via Telegram")
                    return
                else:
                    print(f"⚠️  Telegram failed {resp.status_code} — trying Twilio")
            except Exception as e:
                print(f"⚠️  Telegram exception: {e} — trying Twilio")

        # Twilio SMS fallback
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        twilio_from = os.getenv("TWILIO_FROM_NUMBER", "").strip()
        alert_to = os.getenv("ALERT_PHONE_NUMBER", "").strip()
        if twilio_sid and twilio_token and twilio_from and alert_to:
            try:
                from twilio.rest import Client
                Client(twilio_sid, twilio_token).messages.create(
                    body=message, from_=twilio_from, to=alert_to
                )
                print("✅ Morning alert sent via Twilio SMS")
            except Exception as e:
                print(f"⚠️  Twilio exception: {e}")
        else:
            print("⚠️  No notification method available (Telegram or Twilio)")
            print(f"   HOT leads today:\n{message}")

    def generate_outreach(self, prospects: list[dict], industry: str) -> list[dict]:
        templates = {
            "restaurant": (
                "Hi [NAME], I noticed [BUSINESS] in Detroit.\n\n"
                "Quick question — what happens when someone calls\n"
                "to make a reservation and you're slammed during service?\n\n"
                "I build AI phone assistants for restaurants that\n"
                "answer calls and book tables 24/7 automatically.\n\n"
                "Takes 5-7 days to set up. Starts at $500.\n\n"
                "Worth a 10-minute call this week?\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems\n(586) 636-9550"
            ),
            "dental": (
                "Hi Dr. [NAME],\n\n"
                "A patient tried to book an appointment at [BUSINESS]\n"
                "after hours last week. Nobody answered — they called elsewhere.\n\n"
                "I build AI systems for dental offices that answer after-hours\n"
                "calls and book appointments automatically.\n\n"
                "No staff needed. Works while you sleep.\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems"
            ),
            "hvac": (
                "Hi [NAME],\n\n"
                "When [BUSINESS] gets an emergency call at 10pm — who answers?\n\n"
                "I build AI systems that catch every after-hours inquiry\n"
                "and text you immediately so you never miss an urgent job.\n\n"
                "15-minute call this week?\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems"
            ),
            "salon": (
                "Hi [NAME], love what you're building at [BUSINESS].\n\n"
                "Are you still taking appointment calls manually?\n\n"
                "I set up AI assistants for salons that book appointments,\n"
                "send reminders, and handle questions 24/7 — automatically.\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems"
            ),
        }
        template = templates.get(industry, templates["restaurant"])
        for prospect in prospects:
            name = prospect.get("name", "there")
            prospect["outreach_email"] = (
                template
                .replace("[NAME]", name)
                .replace("[BUSINESS]", name)
            )
        return prospects


if __name__ == "__main__":
    LeadGeneratorAgent().run()
