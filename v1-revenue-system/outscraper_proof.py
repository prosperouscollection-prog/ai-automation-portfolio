#!/usr/bin/env python3
"""Outscraper 10-lead proof-of-concept for Genesis AI Systems.

Goals:
  1. Verify Outscraper returns a real usable website field for Detroit local-business niches
  2. Verify the site field can be normalized to a Hunter-compatible domain
  3. Measure fill rate on a 10-lead proof batch
  4. Estimate cost/usage
  5. Verify Yelp endpoint behavior re: business website vs Yelp listing URL

Run:
  OUTSCRAPER_API_KEY=... python3 v1-revenue-system/outscraper_proof.py
"""

import os
import sys
import json
import re
import requests
from urllib.parse import urlparse

OUTSCRAPER_API_KEY = os.environ.get("OUTSCRAPER_API_KEY", "")
YELP_API_KEY = os.environ.get("YELP_API_KEY", "")

# 10 Detroit businesses across our 3 primary niches
PROOF_QUERIES = [
    "restaurants Detroit MI",
    "dentists Detroit MI",
    "hvac Detroit MI",
]
LIMIT_PER_QUERY = 4  # 4 + 4 + 4 = 12, take first 10 usable


def normalize_domain(raw: str) -> str:
    """Strip protocol, www, and trailing path from a URL to get a bare domain.
    Returns empty string if input is not a real domain.
    """
    if not raw or not raw.strip():
        return ""
    s = raw.strip().lower()
    if not s.startswith("http"):
        s = "https://" + s
    try:
        netloc = urlparse(s).netloc or ""
        domain = netloc.replace("www.", "").strip()
        # Reject Yelp/Google/Facebook/social URLs — not the business's own domain
        blocked = ("yelp.com", "google.com", "facebook.com", "instagram.com",
                   "twitter.com", "linkedin.com", "maps.google")
        if any(b in domain for b in blocked):
            return ""
        # Must look like a real domain: at least one dot, no spaces
        if "." not in domain or " " in domain:
            return ""
        return domain
    except Exception:
        return ""


def run_outscraper_proof():
    print("── OUTSCRAPER PROOF ────────────────────────────────────────────────────")

    if not OUTSCRAPER_API_KEY:
        print("FAIL: OUTSCRAPER_API_KEY not set")
        return

    results = []
    total_records_fetched = 0

    for query in PROOF_QUERIES:
        print(f"\nQuery: {query}")
        resp = requests.get(
            "https://api.app.outscraper.com/maps/search-v2",
            headers={"X-API-KEY": OUTSCRAPER_API_KEY},
            params={
                "query": query,
                "limit": LIMIT_PER_QUERY,
                "async": "false",
            },
            timeout=90,
        )
        print(f"  HTTP {resp.status_code}")
        if not resp.ok:
            print(f"  ERROR: {resp.text[:300]}")
            continue

        data = resp.json()
        # Response is {"data": [[...records...]]} — list of lists
        records = []
        raw_data = data.get("data", [])
        if raw_data and isinstance(raw_data[0], list):
            records = raw_data[0]
        elif raw_data and isinstance(raw_data[0], dict):
            records = raw_data

        print(f"  Records returned: {len(records)}")
        total_records_fetched += len(records)
        if records:
            first = records[0]
            print(f"  RAW FIRST RECORD KEYS: {list(first.keys())}")
            for k, v in first.items():
                if any(x in k.lower() for x in ['site','web','url','domain','link']):
                    print(f"  FIELD {k!r}: {v!r}")

        for biz in records[:LIMIT_PER_QUERY]:
            site_raw = biz.get("website", "")
            domain = normalize_domain(site_raw)
            results.append({
                "name": biz.get("name", ""),
                "address": biz.get("full_address", ""),
                "phone": biz.get("phone", ""),
                "site_raw": site_raw,
                "domain_normalized": domain,
                "category": biz.get("category", ""),
                "rating": biz.get("rating", ""),
                "reviews": biz.get("reviews_count", 0),
            })

    # Take first 10
    results = results[:10]

    print(f"\n── RESULTS ({len(results)} leads) ──────────────────────────────────────────")
    filled = 0
    usable_domains = []
    for i, r in enumerate(results, 1):
        domain = r["domain_normalized"]
        has_domain = bool(domain)
        if has_domain:
            filled += 1
            usable_domains.append(domain)
        flag = "✅" if has_domain else "❌"
        print(f"{i:2}. {flag} {r['name'][:35]:<35} | site_raw: {r['site_raw'][:40] or '(empty)':<40} | domain: {domain or '(none)'}")

    fill_rate = filled / len(results) * 100 if results else 0

    print(f"\n── FILL RATE ───────────────────────────────────────────────────────────")
    print(f"  Leads with usable domain: {filled}/{len(results)} ({fill_rate:.0f}%)")
    print(f"  Usable domains: {usable_domains}")

    print(f"\n── COST ESTIMATE ───────────────────────────────────────────────────────")
    print(f"  Records fetched: {total_records_fetched}")
    print(f"  Free tier: 500 records/month")
    print(f"  Cost for this proof: $0.00 ({total_records_fetched}/500 free credits used)")
    print(f"  Cost at paid rate ($3/1000): ${total_records_fetched * 0.003:.3f}")

    print(f"\n── OUTSCRAPER VERDICT ──────────────────────────────────────────────────")
    if fill_rate >= 60:
        print(f"  PASS — {fill_rate:.0f}% fill rate meets V1 threshold (≥60%)")
    elif fill_rate >= 30:
        print(f"  PARTIAL — {fill_rate:.0f}% fill rate; usable but not dominant source")
    else:
        print(f"  FAIL — {fill_rate:.0f}% fill rate too low for V1 use")

    return fill_rate, usable_domains


def run_yelp_website_check():
    print("\n── YELP WEBSITE FIELD AUDIT ────────────────────────────────────────────")

    if not YELP_API_KEY:
        print("  YELP_API_KEY not set — skipping")
        return

    resp = requests.get(
        "https://api.yelp.com/v3/businesses/search",
        headers={"Authorization": f"Bearer {YELP_API_KEY}"},
        params={"location": "Detroit, MI", "categories": "restaurants", "limit": 3},
        timeout=15,
    )
    if not resp.ok:
        print(f"  Yelp error {resp.status_code}: {resp.text[:200]}")
        return

    businesses = resp.json().get("businesses", [])
    print(f"  Checking top 3 Yelp results for website/url fields:")
    for biz in businesses[:3]:
        name = biz.get("name", "")
        url_field = biz.get("url", "")          # This is the Yelp listing URL
        website_field = biz.get("website", "")  # Does this exist?
        all_keys = list(biz.keys())
        print(f"\n  Business: {name}")
        print(f"    url field:     {url_field[:60] if url_field else '(empty)'}")
        print(f"    website field: {website_field if website_field else '(not present)'}")
        print(f"    all keys: {all_keys}")

    # Fetch one business detail to check if website appears there
    if businesses:
        biz_id = businesses[0].get("id", "")
        detail_resp = requests.get(
            f"https://api.yelp.com/v3/businesses/{biz_id}",
            headers={"Authorization": f"Bearer {YELP_API_KEY}"},
            timeout=15,
        )
        if detail_resp.ok:
            detail = detail_resp.json()
            print(f"\n  Business detail endpoint keys: {list(detail.keys())}")
            print(f"  website field in detail: {detail.get('website', '(not present)')}")
            print(f"  url field in detail:     {detail.get('url', '(empty)')[:60]}")

    print("\n── YELP VERDICT ────────────────────────────────────────────────────────")
    print("  url field = Yelp listing URL only (yelp.com/biz/...)")
    print("  website field = check output above for presence/absence")


if __name__ == "__main__":
    if not OUTSCRAPER_API_KEY and not YELP_API_KEY:
        print("Set OUTSCRAPER_API_KEY and/or YELP_API_KEY to run proof")
        sys.exit(1)

    run_outscraper_proof()
    run_yelp_website_check()
    print("\nDONE")
