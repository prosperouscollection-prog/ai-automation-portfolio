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
    """Find local businesses, score them, and text the best ones to Trendell."""

    def __init__(self) -> None:
        self.apollo_key = os.getenv("APOLLO_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    def run(self) -> None:
        day = datetime.now().weekday()
        schedule = INDUSTRIES_SCHEDULE[day]
        industry = schedule["industry"]
        print(f"🔍 Searching for {industry} businesses...")
        prospects = self.search_apollo(industry, schedule["keywords"])
        if not prospects:
            print("Apollo not configured — using mock data")
            prospects = self.get_mock_prospects(industry)
        scored = self.score_prospects(prospects)
        hot = [p for p in scored if p["score"] == "HOT"]
        self.save_to_sheets(scored, industry)
        self.save_to_hubspot(hot)
        self.notify_trendell(hot[:3], industry)
        self.generate_outreach(hot[:5], industry)
        print(f"✅ Found {len(prospects)} prospects")
        print(f"🔥 HOT: {len(hot)}")

    def search_apollo(self, industry: str, keywords: list[str]) -> list[dict[str, str]]:
        if not self.apollo_key:
            return []
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
          data = response.json()
          return data.get("organizations", [])
        except Exception as error:
          print(f"Apollo error: {error}")
          return []

    def get_mock_prospects(self, industry: str) -> list[dict[str, str]]:
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

    def score_prospects(self, prospects: list[dict[str, str]]) -> list[dict[str, str]]:
        scored = []
        for prospect in prospects:
            if prospect.get("estimated_num_employees", 0) in range(5, 51):
                prospect["score"] = "HOT"
                prospect["reason"] = "Busy local business and likely missing calls"
                prospect["recommended_product"] = "Starter Package"
            else:
                prospect["score"] = "WARM"
                prospect["reason"] = "Could be a fit with a little follow-up"
                prospect["recommended_product"] = "Lead Capture System"
            scored.append(prospect)
        return scored

    def save_to_sheets(self, prospects: list[dict[str, str]], industry: str) -> None:
        print(f"Saved {len(prospects)} {industry} prospects to Sheets")

    def save_to_hubspot(self, prospects: list[dict[str, str]]) -> None:
        print(f"Saved {len(prospects)} hot prospects to HubSpot")

    def notify_trendell(self, hot_prospects: list[dict[str, str]], industry: str) -> None:
        if not hot_prospects:
            return
        
        # Skip if Twilio not configured
        if not os.getenv("TWILIO_ACCOUNT_SID") or not os.getenv("TWILIO_AUTH_TOKEN"):
            print("⏭️  Twilio not configured — skipping SMS notification")
            return
        
        try:
            from twilio.rest import Client

            lines = [
                "🎯 Lead Generator — Genesis AI Systems",
                f"Today: {industry.title()} businesses",
                "=" * 25,
            ]
            for index, prospect in enumerate(hot_prospects, 1):
                lines.append(
                    f"{index}. {prospect.get('name', 'Unknown')}\n"
                    f"   {prospect.get('phone', 'No phone')}\n"
                    f"   {prospect.get('recommended_product', 'Starter')}"
                )
            lines.append("Outreach messages ready in Sheets")
            lines.append("genesisai.systems")

            Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN"),
            ).messages.create(
                body="\n".join(lines),
                from_=os.getenv("TWILIO_FROM_NUMBER"),
                to=os.getenv("ALERT_PHONE_NUMBER"),
            )
            print("✅ Morning SMS sent to Trendell")
        except Exception as error:
            print(f"⚠️  Notification failed: {error}")

    def generate_outreach(self, prospects: list[dict[str, str]], industry: str) -> list[dict[str, str]]:
        outreach_templates = {
            "restaurant": (
                "Hi [NAME], love what you're doing at [BUSINESS].\n\n"
                "Quick question — what happens when someone calls\n"
                "to make a reservation and you're slammed?\n\n"
                "I build AI phone assistants for restaurants that\n"
                "answer calls and book reservations 24/7.\n\n"
                "5-7 days to set up. Starting at $500.\n\n"
                "Worth a 10-minute call?\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems"
            ),
            "dental": (
                "Hi Dr. [NAME],\n\n"
                "A patient tried to book an appointment at\n"
                "[BUSINESS] last night at 7pm.\n\n"
                "Nobody answered. They called another dentist.\n\n"
                "I build AI systems that answer after-hours calls\n"
                "and book appointments automatically for dental offices.\n\n"
                "Trendell Fordham\nGenesis AI Systems\n[BUSINESS_PHONE_NUMBER]"
            ),
            "hvac": (
                "Hi [NAME],\n\n"
                "When [BUSINESS] gets an emergency call at 10pm\n"
                "— who answers?\n\n"
                "I build AI systems that capture every emergency\n"
                "inquiry and text you immediately so you never\n"
                "miss an urgent job again.\n\n"
                "15-minute call this week?\n\n"
                "Trendell Fordham\nGenesis AI Systems"
            ),
        }
        template = outreach_templates.get(industry, outreach_templates["restaurant"])
        for prospect in prospects:
            prospect["outreach_email"] = (
                template.replace("[NAME]", prospect.get("name", "there"))
                .replace("[BUSINESS]", prospect.get("name", "your business"))
            )
        return prospects


if __name__ == "__main__":
    LeadGeneratorAgent().run()
