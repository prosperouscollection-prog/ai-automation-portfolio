#!/usr/bin/env python3
"""Find local businesses, score them, and text the best ones to Trendell."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

from notify import telegram_notify

INDUSTRY_SEARCHES = {
    "restaurant": [
        "restaurants in {city}",
        "best restaurants {city}",
        "local restaurants {city}",
    ],
    "dental": [
        "dental offices {city}",
        "dentist {city}",
        "family dentist {city}",
    ],
    "hvac": [
        "hvac companies {city}",
        "heating cooling {city}",
        "air conditioning repair {city}",
    ],
    "salon": [
        "hair salon {city}",
        "barbershop {city}",
        "beauty salon {city}",
    ],
    "real_estate": [
        "real estate agents {city}",
        "realtor {city}",
        "property management {city}",
    ],
    "retail": [
        "retail stores {city}",
        "local boutique {city}",
        "small business {city}",
    ],
    "plumbing": [
        "plumbers {city}",
        "plumbing company {city}",
        "emergency plumber {city}",
    ],
    "landscaping": [
        "landscaping {city}",
        "lawn care {city}",
        "landscape company {city}",
    ],
}


class GoogleMapsScaper:
    """Search Google Maps or Google Places and return business candidates."""

    def __init__(self) -> None:
        self.places_key = os.getenv("GOOGLE_PLACES_API_KEY")

    def search(self, query: str, max_results: int = 50) -> list[dict]:
        if self.places_key:
            return self.search_places_api(query, max_results)
        return self.search_google_maps(query, max_results)

    def search_places_api(self, query: str, max_results: int) -> list[dict]:
        results = []
        try:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/place/textsearch/json",
                params={
                    "query": query,
                    "key": self.places_key,
                    "type": "establishment",
                },
                timeout=15,
            )
            data = response.json()
            for place in data.get("results", [])[:max_results]:
                results.append({
                    "name": place.get("name"),
                    "address": place.get("formatted_address"),
                    "rating": place.get("rating", 0),
                    "reviews": place.get("user_ratings_total", 0),
                    "place_id": place.get("place_id"),
                    "types": place.get("types", []),
                    "phone": None,
                    "website": None,
                })
            print(f"Found {len(results)} via Places API")
        except Exception as error:
            print(f"Places API error: {error}")
        return results

    def search_google_maps(self, query: str, max_results: int) -> list[dict]:
        results = []
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(
                    f"https://www.google.com/maps/search/{query.replace(' ', '+')}",
                    timeout=30000,
                )
                page.wait_for_timeout(3000)
                listings = page.query_selector_all("[data-result-index]")
                for listing in listings[:max_results]:
                    try:
                        name_el = listing.query_selector(".qBF1Pd")
                        rating_el = listing.query_selector(".MW4etd")
                        reviews_el = listing.query_selector(".UY7F9")
                        address_el = listing.query_selector(".W4Efsd:last-child")
                        results.append({
                            "name": name_el.inner_text() if name_el else "Unknown",
                            "address": address_el.inner_text() if address_el else "",
                            "rating": float(rating_el.inner_text()) if rating_el else 0,
                            "reviews": int(
                                (reviews_el.inner_text() if reviews_el else "0")
                                .replace("(", "")
                                .replace(")", "")
                                .replace(",", "")
                            ),
                            "phone": None,
                            "website": None,
                            "source": "google_maps",
                        })
                    except Exception:
                        continue
                browser.close()
            print(f"Scraped {len(results)} from Google Maps")
        except Exception as error:
            print(f"Scraper error: {error}")
            results = self.get_mock_results(query)
        return results

    def get_mock_results(self, query: str) -> list[dict]:
        return [{
            "name": f"Sample Business from {query}",
            "address": "Detroit, MI",
            "rating": 4.2,
            "reviews": 47,
            "phone": None,
            "website": None,
            "source": "mock",
        }]


class ProspectScorer:
    """Score prospects with simple rules and optional Claude support later."""

    def score(self, prospect: dict, industry: str) -> dict:
        try:
            rating = float(prospect.get("rating", 0))
            reviews = int(prospect.get("reviews", 0))
            if 3.5 <= rating <= 4.8 and reviews >= 20:
                return {
                    "score": "HOT",
                    "reason": "Busy local business and likely missing calls",
                    "product": "Starter Package",
                    "estimated_value": 500,
                }
            return {
                "score": "WARM",
                "reason": "Could benefit from a faster lead process",
                "product": "Lead Capture System",
                "estimated_value": 500,
            }
        except Exception as error:
            print(f"Scoring error: {error}")
            return {
                "score": "WARM",
                "reason": "Could not score — default WARM",
                "product": "Starter Package",
                "estimated_value": 500,
            }


class OutreachGenerator:
    """Create short outreach drafts for prospects."""

    TEMPLATES = {
        "restaurant": (
            "Subject: Quick question about {name}\n\n"
            "Hi there,\n\n"
            "Love what you're doing at {name}.\n\n"
            "Quick question — what happens when someone calls to make a reservation and you're slammed?\n\n"
            "I build AI phone assistants for restaurants that answer calls and book reservations 24/7.\n\n"
            "Worth a 10-minute call?\n\n"
            "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems\n(586) 636-9550"
        ),
        "dental": (
            "Subject: Patients calling after you close\n\n"
            "Hi there,\n\n"
            "A patient tried to book at {name} last night at 7pm.\n\n"
            "Nobody answered. They called another dentist.\n\n"
            "I build AI systems that answer after-hours calls and book appointments automatically.\n\n"
            "Trendell Fordham\nGenesis AI Systems\n(586) 636-9550"
        ),
        "default": (
            "Subject: Quick question about {name}\n\n"
            "Hi there,\n\n"
            "I noticed {name} and wanted to reach out.\n\n"
            "I build done-for-you AI systems for local businesses that want to capture more customers without working more hours.\n\n"
            "Starting at $500. Set up in 5-7 days.\n\n"
            "Worth a quick 10-minute call?\n\n"
            "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems"
        ),
    }

    def generate(self, prospect: dict, industry: str) -> str:
        template = self.TEMPLATES.get(industry, self.TEMPLATES["default"])
        return template.format(name=prospect.get("name", "your business"))


class ScraperAgent:
    """Search, score, save, and notify."""

    def __init__(self) -> None:
        self.scraper = GoogleMapsScaper()
        self.scorer = ProspectScorer()
        self.outreach_gen = OutreachGenerator()
        self.city = os.getenv("TARGET_CITY", "Detroit MI")
        self.industry = os.getenv("INDUSTRY", "restaurant")
        self.max_results = int(os.getenv("MAX_RESULTS", "50"))

    def run(self) -> None:
        print(f"🔍 Scraping {self.industry} in {self.city}")
        searches = INDUSTRY_SEARCHES.get(self.industry, [f"{self.industry} {self.city}"])
        all_prospects = []
        for search_query in searches[:2]:
            query = search_query.format(city=self.city)
            all_prospects.extend(self.scraper.search(query, self.max_results // 2))
            time.sleep(1)
        unique = self.deduplicate(all_prospects)
        scored = []
        for prospect in unique[:30]:
            score_data = self.scorer.score(prospect, self.industry)
            prospect.update(score_data)
            prospect["outreach"] = self.outreach_gen.generate(prospect, self.industry)
            prospect["scraped_at"] = datetime.now().isoformat()
            prospect["city"] = self.city
            prospect["industry"] = self.industry
            scored.append(prospect)
        hot = [prospect for prospect in scored if prospect["score"] == "HOT"]
        warm = [prospect for prospect in scored if prospect["score"] == "WARM"]
        print(f"🔥 HOT: {len(hot)}")
        print(f"✅ WARM: {len(warm)}")
        self.save_to_sheets(scored)
        self.save_to_hubspot(hot[:10])
        self.notify_trendell(hot[:3])
        print("✅ Scraper Agent complete")

    def deduplicate(self, prospects: list[dict]) -> list[dict]:
        seen = set()
        unique = []
        for prospect in prospects:
            name = prospect.get("name", "").lower().strip()
            if name and name not in seen:
                seen.add(name)
                unique.append(prospect)
        return unique

    def save_to_sheets(self, prospects: list[dict]) -> None:
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT", "{}")
            creds_dict = json.loads(creds_json)
            if not creds_dict:
                print("Google Sheets not configured")
                return
            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            service = build("sheets", "v4", credentials=creds)
            sheet_id = os.getenv("GOOGLE_SHEET_ID")
            if not sheet_id:
                print("No Sheet ID")
                return
            rows = [[
                prospect.get("scraped_at", ""),
                prospect.get("name", ""),
                prospect.get("industry", ""),
                prospect.get("city", ""),
                prospect.get("address", ""),
                str(prospect.get("rating", 0)),
                str(prospect.get("reviews", 0)),
                prospect.get("score", ""),
                prospect.get("reason", ""),
                prospect.get("product", ""),
                str(prospect.get("estimated_value", 0)),
                prospect.get("phone", ""),
                prospect.get("website", ""),
                prospect.get("outreach", "")[:500],
                "New",
            ] for prospect in prospects]
            service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range="Leads!A1",
                valueInputOption="RAW",
                body={"values": rows},
            ).execute()
            print(f"✅ Saved {len(rows)} to Google Sheets")
        except Exception as error:
            print(f"Sheets error: {error}")

    def save_to_hubspot(self, prospects: list[dict]) -> None:
        token = os.getenv("HUBSPOT_ACCESS_TOKEN")
        if not token:
            print("HubSpot not configured")
            return
        for prospect in prospects:
            try:
                requests.post(
                    "https://api.hubapi.com/crm/v3/objects/contacts",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "properties": {
                            "company": prospect.get("name", ""),
                            "city": prospect.get("city", ""),
                            "industry": prospect.get("industry", ""),
                            "hs_lead_status": "NEW",
                            "message": (
                                f"Scraped prospect. Score: {prospect.get('score')}. "
                                f"Rating: {prospect.get('rating')}/5. Reviews: {prospect.get('reviews')}"
                            ),
                        }
                    },
                    timeout=10,
                )
            except Exception as error:
                print(f"HubSpot error for {prospect.get('name')}: {error}")

    def notify_trendell(self, hot_prospects: list[dict]) -> None:
        if not hot_prospects:
            self.send_sms(
                f"🔍 Scraper Agent — Genesis AI Systems\n"
                f"Industry: {self.industry}\n"
                f"City: {self.city}\n"
                f"No HOT prospects found today.\n"
                f"WARM leads saved to Sheets."
            )
            return
        lines = [
            "🔥 Scraper Agent Results",
            "Genesis AI Systems",
            "=" * 25,
            f"Industry: {self.industry.title()}",
            f"City: {self.city}",
            f"HOT prospects: {len(hot_prospects)}",
            "=" * 25,
        ]
        for index, prospect in enumerate(hot_prospects, 1):
            lines.append(
                f"{index}. {prospect.get('name', 'Unknown')}\n"
                f"   ⭐ {prospect.get('rating', 0)} ({prospect.get('reviews', 0)} reviews)\n"
                f"   {prospect.get('address', '')[:40]}\n"
                f"   → {prospect.get('product', 'Starter')}"
            )
        lines.append("Outreach ready in Google Sheets")
        lines.append("genesisai.systems")
        self.send_sms("\n".join(lines))

    def send_sms(self, message: str) -> None:
        """Send alert via Telegram (primary) then Twilio SMS (fallback)."""
        # Telegram first — always working
        subject = "Scraper Agent Results"
        if telegram_notify(subject, message, "MEDIUM"):
            print("✅ Scraper alert sent via Telegram")
            return
        # Twilio fallback
        if not os.getenv("TWILIO_ACCOUNT_SID") or not os.getenv("TWILIO_AUTH_TOKEN"):
            print("⚠️  No notification method available — printing results:")
            print(message)
            return
        try:
            from twilio.rest import Client
            Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN"),
            ).messages.create(
                body=message[:1600],
                from_=os.getenv("TWILIO_FROM_NUMBER"),
                to=os.getenv("ALERT_PHONE_NUMBER"),
            )
            print("✅ Scraper alert sent via Twilio SMS")
        except Exception as error:
            print(f"⚠️  All notification methods failed: {error}")


if __name__ == "__main__":
    ScraperAgent().run()
