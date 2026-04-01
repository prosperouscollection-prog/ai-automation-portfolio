#!/usr/bin/env python3
"""Hunter.io email lookup — OPTIONAL FALLBACK for V1.

STATUS: Demoted from planned primary to optional fallback (2026-03-31).
Outscraper Emails & Contacts is now the proven primary enrichment layer
(90% email fill rate on 10 Detroit domains). Hunter.io is only needed if
Outscraper gaps become a problem at scale.

Do not add Hunter.io to the V1 critical path. Activate only when:
1. Outscraper email fill rate drops below 60% for a niche
2. A specific lead has no Outscraper email and is high-value
3. HUNTER_API_KEY is already in GitHub secrets

Free tier: 25 lookups/month. Paid: $34/mo for 500.

Usage (optional integration in lead_generator_agent.py):
    from hunter_lookup import HunterLookup

    hunter = HunterLookup()
    if hunter.configured:
        result = hunter.find_email("slowsbarbq.com")
"""

from __future__ import annotations

import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class HunterLookup:
    """Hunter.io domain search — finds owner emails for lead outreach."""

    BASE_URL = "https://api.hunter.io/v2"

    # Titles that indicate a decision-maker at a local business
    DECISION_MAKER_TITLES = [
        "owner", "founder", "ceo", "president", "general manager",
        "manager", "director", "partner", "principal", "operator",
    ]

    def __init__(self):
        self.api_key = os.getenv("HUNTER_API_KEY", "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def find_email(self, domain: str) -> Optional[dict]:
        """Search a domain for the best decision-maker email.

        Returns dict with: email, name, position, confidence, source
        Returns None if no email found or API unavailable.
        """
        if not self.api_key:
            print("⚠️  HUNTER_API_KEY not set — email lookup skipped")
            return None

        if not domain or domain in ("", "unknown", "n/a"):
            return None

        # Clean the domain
        domain = domain.strip().lower()
        if domain.startswith("http"):
            from urllib.parse import urlparse
            domain = urlparse(domain).netloc or domain
        domain = domain.replace("www.", "")

        try:
            resp = requests.get(
                f"{self.BASE_URL}/domain-search",
                params={
                    "domain": domain,
                    "api_key": self.api_key,
                    "type": "personal",  # personal emails, not generic
                    "limit": 10,
                },
                timeout=15,
            )

            if resp.status_code == 401:
                print("❌ Hunter.io auth failed — check HUNTER_API_KEY")
                return None
            if resp.status_code == 429:
                print("⚠️  Hunter.io rate limit reached — try again later")
                return None
            if not resp.ok:
                print(f"❌ Hunter.io {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json().get("data", {})
            emails = data.get("emails", [])

            if not emails:
                print(f"ℹ️  No emails found for {domain}")
                return None

            # Find the best decision-maker
            best = self._pick_best_contact(emails)
            if best:
                print(f"✅ Found email for {domain}: {best['email']} ({best.get('position', 'unknown')})")
            return best

        except Exception as e:
            print(f"❌ Hunter.io exception for {domain}: {e}")
            return None

    def find_email_by_name(self, domain: str, first_name: str, last_name: str) -> Optional[dict]:
        """Find a specific person's email at a domain.

        Uses Hunter.io email finder (more precise, uses 1 request).
        """
        if not self.api_key or not domain:
            return None

        try:
            resp = requests.get(
                f"{self.BASE_URL}/email-finder",
                params={
                    "domain": domain,
                    "first_name": first_name,
                    "last_name": last_name,
                    "api_key": self.api_key,
                },
                timeout=15,
            )

            if not resp.ok:
                return None

            data = resp.json().get("data", {})
            email = data.get("email")
            if email:
                return {
                    "email": email,
                    "name": f"{first_name} {last_name}",
                    "position": data.get("position", ""),
                    "confidence": data.get("score", 0),
                    "source": "hunter_finder",
                }
            return None

        except Exception as e:
            print(f"❌ Hunter.io finder exception: {e}")
            return None

    def check_remaining(self) -> Optional[int]:
        """Check how many Hunter.io lookups remain this month."""
        if not self.api_key:
            return None
        try:
            resp = requests.get(
                f"{self.BASE_URL}/account",
                params={"api_key": self.api_key},
                timeout=10,
            )
            if resp.ok:
                data = resp.json().get("data", {})
                requests_info = data.get("requests", {})
                used = requests_info.get("searches", {}).get("used", 0)
                available = requests_info.get("searches", {}).get("available", 0)
                remaining = available - used
                print(f"ℹ️  Hunter.io: {remaining} lookups remaining ({used}/{available} used)")
                return remaining
            return None
        except Exception:
            return None

    def _pick_best_contact(self, emails: list[dict]) -> Optional[dict]:
        """Pick the best decision-maker from Hunter.io results.

        Priority: owner/founder > manager/director > highest confidence.
        """
        scored = []
        for entry in emails:
            email = entry.get("value", "")
            if not email:
                continue

            position = (entry.get("position") or "").lower()
            confidence = entry.get("confidence", 0)

            # Score: decision-maker title bonus + confidence
            title_score = 0
            for i, title in enumerate(self.DECISION_MAKER_TITLES):
                if title in position:
                    title_score = (len(self.DECISION_MAKER_TITLES) - i) * 10
                    break

            scored.append({
                "email": email,
                "name": f"{entry.get('first_name', '')} {entry.get('last_name', '')}".strip(),
                "position": entry.get("position", ""),
                "confidence": confidence,
                "source": "hunter_domain",
                "_sort_score": title_score + confidence,
            })

        if not scored:
            return None

        scored.sort(key=lambda x: x["_sort_score"], reverse=True)
        best = scored[0]
        del best["_sort_score"]
        return best


# --- Convenience ---

_default_hunter: Optional[HunterLookup] = None


def get_hunter() -> HunterLookup:
    global _default_hunter
    if _default_hunter is None:
        _default_hunter = HunterLookup()
    return _default_hunter


def lookup_email(domain: str) -> Optional[dict]:
    """Module-level convenience for quick lookups."""
    return get_hunter().find_email(domain)
