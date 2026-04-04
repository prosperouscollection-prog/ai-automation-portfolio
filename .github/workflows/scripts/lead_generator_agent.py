#!/usr/bin/env python3
"""Morning prospect finder for Genesis AI Systems."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

DETROIT = ZoneInfo("America/Detroit")
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

INDUSTRIES_SCHEDULE = {
    0: {"industry": "restaurant", "keywords": ["restaurant", "cafe", "diner", "bistro"], "yelp_categories": "restaurants"},
    1: {"industry": "dental", "keywords": ["dental", "dentist", "orthodontist"], "yelp_categories": "dentists,orthodontists"},
    2: {"industry": "hvac", "keywords": ["hvac", "heating", "cooling", "air conditioning"], "yelp_categories": "hvac"},
    3: {"industry": "salon", "keywords": ["salon", "barbershop", "hair", "beauty"], "yelp_categories": "hair,barbers,beautysvc"},
    4: {"industry": "real_estate", "keywords": ["realtor", "real estate", "properties"], "yelp_categories": "realestate"},
    5: {"industry": "retail", "keywords": ["boutique", "shop", "store", "retail"], "yelp_categories": "shopping"},
    6: {"industry": "mixed", "keywords": ["local business", "small business"], "yelp_categories": "localservices"},
}

CHAIN_EXCLUSION_KEYWORDS = [
    "mcdonald",
    "subway",
    "starbucks",
    "walmart",
    "target",
    "cvs",
    "walgreens",
    "autozone",
    "jiffy lube",
    "great clips",
    "supercuts",
    "domino",
    "pizza hut",
    "little caesar",
    "jersey mike",
    "firehouse",
    "anytime fitness",
    "planet fitness",
    "h&r block",
    "h&m",
    "zara",
    "forever 21",
    "old navy",
    "gap",
    "tj maxx",
    "marshalls",
    "ross",
    "burlington",
    "lululemon",
    "nike",
    "adidas",
    "under armour",
    "foot locker",
    "finish line",
    "dick's sporting",
    "urban outfitters",
    "anthropologie",
    "free people",
    "the ups store",
    "ace hardware",
    "7-eleven",
    "dollar general",
    "family dollar",
    "five guys",
]


class LeadGeneratorAgent:
    """Find local businesses, score them, and push hot leads to HubSpot + Sheets."""

    def __init__(self) -> None:
        self.apollo_key = os.getenv("APOLLO_API_KEY", "").strip()
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        self.hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
        self.service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT", "").strip()
        self.outscraper_key = os.getenv("OUTSCRAPER_API_KEY", "").strip()
        self.hunter_key = os.getenv("HUNTER_API_KEY", "").strip()

    def run(self) -> None:
        day = datetime.now(DETROIT).weekday()
        schedule = INDUSTRIES_SCHEDULE[day]
        industry = schedule["industry"]
        print(f"🔍 Searching for {industry} businesses in Detroit...")

        # --- Outscraper Maps discovery (primary source) ---
        prospects = []
        if not self.outscraper_key:
            print("⚠️  OUTSCRAPER_API_KEY missing — falling back to mock data")
        else:
            prospects = self.search_outscraper_maps(industry)

        if not prospects:
            print("⚠️  No results from any source — falling back to mock data for testing")
            prospects = self.get_mock_prospects(industry)

        scored = self.score_prospects(prospects)
        hot = [p for p in scored if p["score"] == "HOT"]

        # --- Email enrichment for HOT leads with a known domain ---
        for p in hot:
            domain = p.get("primary_domain", "").strip()
            if domain and not p.get("email"):
                p["email"] = self.enrich_email(domain)

        self.generate_outreach(hot[:5], industry)  # must run before save_to_sheets
        self.save_to_sheets(scored, industry)
        self.save_to_hubspot(hot)
        self.notify_trendell(hot[:3], industry)

        print(f"✅ Found {len(prospects)} prospects")
        print(f"🔥 HOT leads: {len(hot)}")

    # Maps query for each day's industry — Detroit-scoped
    MAPS_QUERY = {
        "restaurant":  "restaurants Detroit MI",
        "dental":      "dentists Detroit MI",
        "hvac":        "hvac contractors Detroit MI",
        "salon":       "hair salons Detroit MI",
        "real_estate": "real estate agents Detroit MI",
        "retail":      "retail stores Detroit MI",
        "mixed":       "local businesses Detroit MI",
    }

    def _normalize_domain(self, raw: str) -> str:
        """Strip protocol/www/path. Reject social & aggregator domains. Return bare domain or ''."""
        if not raw or not raw.strip():
            return ""
        s = raw.strip().lower()
        if not s.startswith("http"):
            s = "https://" + s
        try:
            netloc = urlparse(s).netloc or ""
            domain = netloc.replace("www.", "").strip()
            blocked = ("yelp.com", "google.com", "facebook.com", "instagram.com",
                       "twitter.com", "linkedin.com", "maps.google")
            if any(b in domain for b in blocked):
                return ""
            if "." not in domain or " " in domain:
                return ""
            return domain
        except Exception:
            return ""

    def search_outscraper_maps(self, industry: str) -> list[dict]:
        """Search Outscraper Maps for Detroit businesses in today's niche.

        Maps each result into the standard lead dict with primary_domain
        populated from the `website` field — enabling enrich_email() to fire.
        """
        query = self.MAPS_QUERY.get(industry, f"{industry} Detroit MI")
        print(f"  Maps query: {query!r}")
        try:
            resp = requests.get(
                "https://api.app.outscraper.com/maps/search-v2",
                headers={"X-API-KEY": self.outscraper_key},
                params={"query": query, "limit": 25, "async": "false"},
                timeout=90,
            )
            if not resp.ok:
                print(f"❌ Outscraper Maps {resp.status_code}: {resp.text[:300]}")
                return []
            raw = resp.json().get("data", [])
            records = raw[0] if raw and isinstance(raw[0], list) else raw
            if not isinstance(records, list):
                records = []
            print(f"✅ Outscraper Maps returned {len(records)} businesses")
            results = []
            for biz in records:
                domain = self._normalize_domain(biz.get("website", ""))
                results.append({
                    "name": biz.get("name", "Unknown"),
                    "primary_domain": domain,
                    "phone": biz.get("phone", ""),
                    "email": "",
                    "contact_name": "",
                    "title": "",
                    "estimated_num_employees": 0,
                    "city": "Detroit",
                    "address": biz.get("full_address", "Detroit, MI"),
                    "industry": industry,
                    "yelp_rating": biz.get("rating", ""),
                    "yelp_reviews": biz.get("reviews", 0) or 0,  # Maps field is `reviews`, not `reviews_count`
                    "yelp_url": "",
                    "linkedin_url": "",
                    "source": "outscraper_maps",
                })
            return results
        except Exception as exc:
            print(f"❌ Outscraper Maps exception: {exc}")
            return []

    def search_yelp(self, industry: str, categories: str) -> list[dict]:
        """Search Yelp Fusion for Detroit businesses — free, 500 calls/day."""
        try:
            response = requests.get(
                "https://api.yelp.com/v3/businesses/search",
                headers={"Authorization": f"Bearer {self.yelp_key}"},
                params={
                    "location": "Detroit, MI",
                    "categories": categories,
                    "limit": 25,
                    "sort_by": "review_count",  # busiest businesses first
                },
                timeout=30,
            )
            if response.status_code == 401:
                print("❌ Yelp auth failed (401) — check YELP_API_KEY secret")
                return []
            if not response.ok:
                print(f"❌ Yelp {response.status_code}: {response.text[:300]}")
                return []
            businesses = response.json().get("businesses", [])
            print(f"✅ Yelp returned {len(businesses)} businesses")
            results = []
            for biz in businesses:
                location = biz.get("location", {})
                results.append({
                    "name": biz.get("name", "Unknown"),
                    "primary_domain": "",
                    "phone": biz.get("display_phone", biz.get("phone", "")),
                    "email": "",
                    "contact_name": "",
                    "title": "",
                    "estimated_num_employees": 0,  # Yelp doesn't provide this — 0 so scoring uses reviews only
                    "city": location.get("city", "Detroit"),
                    "address": ", ".join(filter(None, [
                        location.get("address1", ""),
                        location.get("city", ""),
                        location.get("state", ""),
                    ])),
                    "industry": industry,
                    "yelp_rating": biz.get("rating", ""),
                    "yelp_reviews": biz.get("review_count", 0),
                    "yelp_url": biz.get("url", ""),
                    "linkedin_url": "",
                })
            return results
        except Exception as error:
            print(f"❌ Yelp exception: {error}")
            return []

    def search_apollo(self, industry: str, keywords: list[str]) -> list[dict]:
        """Search Apollo.io for Detroit business contacts in this industry.
        Uses /v1/people/search — available on free plan.
        Returns org-shaped dicts so downstream code stays unchanged.
        """
        try:
            response = requests.post(
                "https://api.apollo.io/v1/people/search",
                headers={
                    "Content-Type": "application/json",
                    "X-Api-Key": self.apollo_key,
                },
                json={
                    "person_titles": ["owner", "manager", "operator", "founder", "general manager"],
                    "organization_locations": ["Detroit, Michigan, United States"],
                    "organization_keyword_tags": keywords,
                    "contact_email_status": ["verified", "likely to engage"],
                    "page": 1,
                    "per_page": 25,
                },
                timeout=30,
            )
            if response.status_code == 401:
                print("❌ Apollo auth failed (401) — check APOLLO_API_KEY secret")
                return []
            if response.status_code == 403:
                print("❌ Apollo 403 — endpoint not accessible on this plan")
                print(f"   {response.text[:300]}")
                return []
            if response.status_code == 422:
                print(f"❌ Apollo 422 — bad request: {response.text[:300]}")
                return []
            if not response.ok:
                print(f"❌ Apollo {response.status_code}: {response.text[:300]}")
                return []
            data = response.json()
            people = data.get("people", [])
            print(f"✅ Apollo returned {len(people)} contacts")
            # Log first result's domain field for verification
            if people:
                first_org = (people[0].get("organization") or {})
                print(f"ℹ️  Apollo domain field sample — primary_domain: '{first_org.get('primary_domain', 'NOT RETURNED')}'")
            # Normalize people records to org-shaped dicts
            results = []
            for person in people:
                org = person.get("organization") or {}
                results.append({
                    "name": org.get("name") or person.get("name", "Unknown"),
                    "primary_domain": org.get("primary_domain", ""),
                    "phone": (
                        person.get("phone_numbers", [{}])[0].get("raw_number", "")
                        if person.get("phone_numbers") else ""
                    ),
                    "email": person.get("email", ""),
                    "contact_name": person.get("name", ""),
                    "title": person.get("title", ""),
                    "estimated_num_employees": org.get("estimated_num_employees", 0),
                    "city": "Detroit",
                    "industry": industry,
                    "linkedin_url": person.get("linkedin_url", ""),
                })
            return results
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
            name = (prospect.get("name", "") or "").lower()
            if any(keyword in name for keyword in CHAIN_EXCLUSION_KEYWORDS) or re.search(r"\b(?:inc|llc|corp|holdings|enterprises)\b", name):
                prospect["score"] = 0
                prospect["reason"] = "Corporate chain or entity excluded"
                prospect["recommended_product"] = ""
                scored.append(prospect)
                continue
            reviews = prospect.get("yelp_reviews", 0) or 0
            rating = prospect.get("yelp_rating", 0) or 0
            employees = prospect.get("estimated_num_employees", 0) or 0
            # HOT: active business with any reviews (Maps) or right employee count
            # Threshold lowered from 20→5 — Maps returns local service businesses
            # with far fewer reviews than Yelp's popularity-sorted results
            if reviews >= 5 or (2 <= employees <= 50):
                prospect["score"] = "HOT"
                prospect["reason"] = "Active local business — likely missing calls and leads"
                prospect["recommended_product"] = "Starter Package — $500 setup, $150/mo"
            elif reviews > 5 or employees > 0:
                prospect["score"] = "WARM"
                prospect["reason"] = "Established business — worth a follow-up"
                prospect["recommended_product"] = "Lead Capture System"
            else:
                prospect["score"] = "COLD"
                prospect["reason"] = "New or low-activity listing"
                prospect["recommended_product"] = "Check back in 30 days"
            scored.append(prospect)
        return scored

    # HubSpot requires specific enum values for the industry field
    HUBSPOT_INDUSTRY_MAP = {
        "restaurant": "FOOD_BEVERAGES",
        "dental": "HEALTH_WELLNESS_AND_FITNESS",
        "hvac": "CONSTRUCTION",
        "salon": "COSMETICS",
        "real_estate": "REAL_ESTATE",
        "retail": "RETAIL",
        "mixed": "OTHER",
    }

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
                        "state": "Michigan",
                        "country": "United States",
                        "industry": self.HUBSPOT_INDUSTRY_MAP.get(
                            prospect.get("industry", ""), "OTHER"
                        ),
                        "numberofemployees": str(prospect.get("estimated_num_employees", "") or ""),
                        "description": (
                            f"Score: {prospect.get('score','')}\n"
                            f"Reason: {prospect.get('reason','')}\n"
                            f"Product: {prospect.get('recommended_product','')}\n"
                            f"Address: {prospect.get('address','')}\n"
                            f"Yelp: {prospect.get('yelp_rating','')} stars, {prospect.get('yelp_reviews','')} reviews\n"
                            f"Contact: {prospect.get('contact_name','')}, {prospect.get('title','')}\n"
                            f"Email: {prospect.get('email','')}\n"
                            f"LinkedIn: {prospect.get('linkedin_url','')}"
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
            today = datetime.now(DETROIT).strftime("%Y-%m-%d")
            rows = []
            for p in prospects:
                rows.append([
                    today,
                    industry,
                    p.get("name", ""),
                    p.get("primary_domain", ""),
                    p.get("phone", ""),
                    p.get("address", p.get("city", "Detroit")),
                    str(p.get("estimated_num_employees", "")),
                    str(p.get("yelp_rating", "")),
                    str(p.get("yelp_reviews", "")),
                    p.get("score", ""),
                    p.get("reason", ""),
                    p.get("recommended_product", ""),
                    p.get("yelp_url", ""),
                    p.get("outreach_email", ""),
                    "",                   # col O: placeholder
                    p.get("email", ""),   # col P: owner_email — enriched contact address
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
            f"Date: {datetime.now(DETROIT).strftime('%b %d')}",
            "=" * 28,
        ]
        for i, p in enumerate(hot_prospects, 1):
            email_line = f"\n   📧 {p['email']}" if p.get("email") else ""
            lines.append(
                f"{i}. {p.get('name', 'Unknown')}\n"
                f"   {p.get('phone', 'No phone listed')}"
                f"{email_line}\n"
                f"   → {p.get('recommended_product', 'Starter')}"
            )
        lines.append("\nOutreach messages ready.")
        lines.append("genesisai.systems")
        message = "\n".join(lines)

        # Send via Telegram
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
                else:
                    print(f"⚠️  Telegram failed {resp.status_code}")
            except Exception as e:
                print(f"⚠️  Telegram exception: {e}")
        else:
            print("⚠️  Telegram not configured — TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing")
            print(f"   HOT leads today:\n{message}")

    def enrich_email(self, domain: str) -> str:
        """Return first valid email for domain. Outscraper primary, Hunter fallback.

        Logs result clearly. Never raises — returns '' on any failure so the
        caller can continue processing the rest of the batch.
        """
        # 1. Outscraper /emails-and-contacts
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
                    print(f"  ⚠️  Outscraper {resp.status_code} for {domain} — trying Hunter")
            except Exception as exc:
                print(f"  ⚠️  Outscraper exception for {domain}: {exc} — trying Hunter")
        else:
            print("  ℹ️  OUTSCRAPER_API_KEY not set — skipping Outscraper enrichment")

        # 2. Hunter fallback
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
                else:
                    print(f"  ⚠️  Hunter {resp.status_code} for {domain}")
            except Exception as exc:
                print(f"  ⚠️  Hunter exception for {domain}: {exc}")
        else:
            print("  ℹ️  HUNTER_API_KEY not set — Hunter fallback skipped")

        print(f"  ❌ No email found for {domain}")
        return ""

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
