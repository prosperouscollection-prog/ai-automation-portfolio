#!/usr/bin/env python3
"""Outscraper enrichment proof — test whether Outscraper can replace Hunter.io.

Tests Outscraper's email/contact enrichment endpoints against the 10 domains
proven in the Maps proof. Determines if Outscraper can serve as the primary
enrichment layer in V1 (replacing Hunter).

Endpoints tested:
  1. /emails-and-contacts  — scrapes emails, phones, socials from domains
  2. /contacts-and-leads   — richer enrichment with named contacts & titles

Run:
  OUTSCRAPER_API_KEY=... python3 v1-revenue-system/outscraper_enrichment_proof.py
"""

import os
import sys
import json
import requests
from urllib.parse import urlparse

OUTSCRAPER_API_KEY = os.environ.get("OUTSCRAPER_API_KEY", "")

# 10 Detroit businesses across 3 niches — same queries as Maps proof
PROOF_QUERIES = [
    "restaurants Detroit MI",
    "dentists Detroit MI",
    "hvac Detroit MI",
]
LIMIT_PER_QUERY = 4  # 4+4+4=12, take first 10 usable


def normalize_domain(raw: str) -> str:
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


# ── Step 1: Collect domains from Maps ────────────────────────────────────────

def collect_domains_from_maps() -> list[str]:
    """Run Maps queries and return up to 10 usable domains."""
    print("── STEP 1: COLLECTING DOMAINS FROM MAPS ────────────────────────────────")

    if not OUTSCRAPER_API_KEY:
        print("FAIL: OUTSCRAPER_API_KEY not set")
        sys.exit(1)

    domains = []
    for query in PROOF_QUERIES:
        print(f"  Query: {query}")
        resp = requests.get(
            "https://api.app.outscraper.com/maps/search-v2",
            headers={"X-API-KEY": OUTSCRAPER_API_KEY},
            params={"query": query, "limit": LIMIT_PER_QUERY, "async": "false"},
            timeout=90,
        )
        if not resp.ok:
            print(f"    ERROR {resp.status_code}: {resp.text[:200]}")
            continue

        data = resp.json()
        raw = data.get("data", [])
        records = raw[0] if raw and isinstance(raw[0], list) else raw

        for biz in records[:LIMIT_PER_QUERY]:
            d = normalize_domain(biz.get("website", ""))
            if d and d not in domains:
                domains.append(d)
                print(f"    ✅ {biz.get('name','')[:35]} → {d}")
            elif not d:
                print(f"    ❌ {biz.get('name','')[:35]} — no usable domain")

    domains = domains[:10]
    print(f"\n  Collected {len(domains)} usable domains: {domains}\n")
    return domains


# ── Step 2: Emails & Contacts Scraper ────────────────────────────────────────

def test_emails_and_contacts(domains: list[str]) -> list[dict]:
    """Test /emails-and-contacts on all domains (one request per domain)."""
    print("── STEP 2: EMAILS & CONTACTS SCRAPER (/emails-and-contacts) ────────────")
    print(f"  Domains: {domains}")

    records = []
    for domain in domains:
        resp = requests.get(
            "https://api.app.outscraper.com/emails-and-contacts",
            headers={"X-API-KEY": OUTSCRAPER_API_KEY},
            params={"query": domain, "async": "false"},
            timeout=120,
        )

        print(f"  {domain}: HTTP {resp.status_code}")
        if not resp.ok:
            print(f"    ERROR: {resp.text[:300]}")
            records.append({"query": domain})
            continue

        data = resp.json()
        raw = data.get("data", [])
        # Flatten: may be [[{...}]] or [{...}]
        if raw and isinstance(raw[0], list):
            recs = raw[0]
        elif raw and isinstance(raw[0], dict):
            recs = raw
        else:
            recs = []

        if recs:
            records.append(recs[0])
        else:
            records.append({"query": domain})

    print(f"\n  Total records: {len(records)}")
    if records:
        print(f"  RAW FIRST RECORD KEYS: {sorted(records[0].keys())}")
        print(f"  FULL FIRST RECORD:")
        print(json.dumps(records[0], indent=4, default=str)[:2000])

    results = []
    for i, rec in enumerate(records, 1):
        domain = rec.get("domain", rec.get("query", "unknown"))

        # Extract emails — may be list of dicts or list of strings
        raw_emails = rec.get("emails", []) or []
        if raw_emails and isinstance(raw_emails[0], dict):
            email_list = [e.get("value", "") for e in raw_emails if e.get("value")]
        elif raw_emails and isinstance(raw_emails[0], str):
            email_list = raw_emails
        else:
            email_list = []
        # Also check flat fields email_1..email_5
        for n in range(1, 6):
            e = rec.get(f"email_{n}", "")
            if e and e not in email_list:
                email_list.append(e)

        # Extract phones
        raw_phones = rec.get("phones", []) or []
        if raw_phones and isinstance(raw_phones[0], dict):
            phone_list = [p.get("value", "") for p in raw_phones if p.get("value")]
        elif raw_phones and isinstance(raw_phones[0], str):
            phone_list = raw_phones
        else:
            phone_list = []
        for n in range(1, 4):
            p = rec.get(f"phone_{n}", "")
            if p and p not in phone_list:
                phone_list.append(p)

        # Socials
        socials = {}
        for platform in ("facebook", "instagram", "twitter", "linkedin", "youtube"):
            val = rec.get(platform, "")
            if val:
                socials[platform] = val
        # Also check nested socials dict
        socials_nested = rec.get("socials", rec.get("social_links", {}))
        if isinstance(socials_nested, dict):
            socials.update({k: v for k, v in socials_nested.items() if v})

        # Contact names / titles (if present)
        contacts = rec.get("contacts", []) or []
        contact_names = []
        contact_titles = []
        if contacts and isinstance(contacts[0], dict):
            for c in contacts:
                name = c.get("name", c.get("full_name", ""))
                title = c.get("title", c.get("position", c.get("job_title", "")))
                if name:
                    contact_names.append(name)
                if title:
                    contact_titles.append(title)

        result = {
            "domain": domain,
            "emails": email_list,
            "phones": phone_list,
            "socials": socials,
            "contact_names": contact_names,
            "contact_titles": contact_titles,
            "raw_keys": sorted(rec.keys()),
        }
        results.append(result)

        flag = "✅" if email_list else "❌"
        print(f"\n  {i}. {flag} {domain}")
        print(f"     emails:    {email_list[:5]}")
        print(f"     phones:    {phone_list[:3]}")
        print(f"     contacts:  {contact_names[:3]}")
        print(f"     titles:    {contact_titles[:3]}")
        print(f"     socials:   {list(socials.keys())}")

    return results


# ── Step 3: Contacts & Leads Enrichment ──────────────────────────────────────

def test_contacts_and_leads(domains: list[str]) -> list[dict]:
    """Test /contacts-and-leads on all domains (one request per domain)."""
    print("\n── STEP 3: CONTACTS & LEADS ENRICHMENT (/contacts-and-leads) ────────────")
    print(f"  Domains: {domains}")

    records = []
    for domain in domains:
        resp = requests.get(
            "https://api.app.outscraper.com/contacts-and-leads",
            headers={"X-API-KEY": OUTSCRAPER_API_KEY},
            params={
                "query": domain,
                "async": "false",
                "contacts_per_company": 3,
                "emails_per_contact": 1,
            },
            timeout=180,
        )

        print(f"  {domain}: HTTP {resp.status_code}")
        if not resp.ok:
            print(f"    ERROR: {resp.text[:300]}")
            records.append({"query": domain})
            continue

        data = resp.json()
        raw = data.get("data", [])
        if raw and isinstance(raw[0], list):
            recs = raw[0]
        elif raw and isinstance(raw[0], dict):
            recs = raw
        else:
            recs = []

        if recs:
            records.append(recs[0])
        else:
            records.append({"query": domain})

    print(f"\n  Total records: {len(records)}")
    if records:
        print(f"  RAW FIRST RECORD KEYS: {sorted(records[0].keys())}")
        print(f"  FULL FIRST RECORD:")
        print(json.dumps(records[0], indent=4, default=str)[:3000])

    results = []
    for i, rec in enumerate(records, 1):
        domain = rec.get("domain", rec.get("query", "unknown"))

        # Emails
        raw_emails = rec.get("emails", []) or []
        if raw_emails and isinstance(raw_emails[0], dict):
            email_list = [e.get("value", e.get("email", "")) for e in raw_emails if e.get("value") or e.get("email")]
        elif raw_emails and isinstance(raw_emails[0], str):
            email_list = raw_emails
        else:
            email_list = []

        # Phones
        raw_phones = rec.get("phones", []) or []
        if raw_phones and isinstance(raw_phones[0], dict):
            phone_list = [p.get("value", "") for p in raw_phones if p.get("value")]
        elif raw_phones and isinstance(raw_phones[0], str):
            phone_list = raw_phones
        else:
            phone_list = []

        # Named contacts with titles
        contacts = rec.get("contacts", rec.get("people", [])) or []
        contact_names = []
        contact_titles = []
        contact_emails = []
        if contacts and isinstance(contacts[0], dict):
            for c in contacts:
                name = c.get("name", c.get("full_name", ""))
                title = c.get("title", c.get("position", c.get("job_title", "")))
                email = c.get("email", c.get("email_address", ""))
                if name:
                    contact_names.append(name)
                if title:
                    contact_titles.append(title)
                if email:
                    contact_emails.append(email)

        result = {
            "domain": domain,
            "emails": email_list,
            "phones": phone_list,
            "contact_names": contact_names,
            "contact_titles": contact_titles,
            "contact_emails": contact_emails,
            "raw_keys": sorted(rec.keys()),
        }
        results.append(result)

        flag = "✅" if (email_list or contact_emails) else "❌"
        print(f"\n  {i}. {flag} {domain}")
        print(f"     company emails: {email_list[:5]}")
        print(f"     contact names:  {contact_names[:5]}")
        print(f"     contact titles: {contact_titles[:5]}")
        print(f"     contact emails: {contact_emails[:5]}")
        print(f"     phones:         {phone_list[:3]}")

    return results


# ── Step 4: Summary & Verdict ────────────────────────────────────────────────

def summarize(domains, ec_results, cl_results):
    """Print summary comparing both endpoints and deliver final ruling."""
    n = len(domains)

    print("\n" + "=" * 78)
    print("  OUTSCRAPER ENRICHMENT PROOF — SUMMARY")
    print("=" * 78)

    # Emails & Contacts fill rate
    ec_email_hits = sum(1 for r in ec_results if r["emails"])
    ec_phone_hits = sum(1 for r in ec_results if r["phones"])
    ec_contact_hits = sum(1 for r in ec_results if r["contact_names"])
    ec_title_hits = sum(1 for r in ec_results if r["contact_titles"])
    ec_rate = ec_email_hits / n * 100 if n else 0

    print(f"\n  SERVICE 1: /emails-and-contacts")
    print(f"    Email hit rate:   {ec_email_hits}/{n} ({ec_rate:.0f}%)")
    print(f"    Phone hit rate:   {ec_phone_hits}/{n}")
    print(f"    Contact names:    {ec_contact_hits}/{n}")
    print(f"    Contact titles:   {ec_title_hits}/{n}")

    # Contacts & Leads fill rate
    if cl_results:
        cl_email_hits = sum(1 for r in cl_results if r["emails"] or r.get("contact_emails"))
        cl_phone_hits = sum(1 for r in cl_results if r["phones"])
        cl_name_hits = sum(1 for r in cl_results if r["contact_names"])
        cl_title_hits = sum(1 for r in cl_results if r["contact_titles"])
        cl_personal_email_hits = sum(1 for r in cl_results if r.get("contact_emails"))
        cl_rate = cl_email_hits / n * 100 if n else 0

        print(f"\n  SERVICE 2: /contacts-and-leads")
        print(f"    Email hit rate:        {cl_email_hits}/{n} ({cl_rate:.0f}%)")
        print(f"    Phone hit rate:        {cl_phone_hits}/{n}")
        print(f"    Contact names:         {cl_name_hits}/{n}")
        print(f"    Contact titles:        {cl_title_hits}/{n}")
        print(f"    Personal emails:       {cl_personal_email_hits}/{n}")
    else:
        cl_rate = 0
        print(f"\n  SERVICE 2: /contacts-and-leads — NOT TESTED (endpoint error)")

    best_rate = max(ec_rate, cl_rate)

    # Cost estimate
    print(f"\n  COST ESTIMATE")
    print(f"    /emails-and-contacts: {n} domains × $0.003 = ${n * 0.003:.3f}")
    print(f"    /contacts-and-leads:  {n} domains (pricing TBD — check Outscraper dashboard)")
    print(f"    Free tier: 500 domains/month for emails-and-contacts")

    # Per-domain comparison
    print(f"\n  PER-DOMAIN RESULTS")
    print(f"  {'Domain':<30} {'EC-Email':>10} {'EC-Phone':>10} {'CL-Email':>10} {'CL-Names':>10}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
    for i, domain in enumerate(domains):
        ec = ec_results[i] if i < len(ec_results) else {}
        cl = cl_results[i] if i < len(cl_results) else {}
        print(f"  {domain[:30]:<30} "
              f"{'✅' if ec.get('emails') else '❌':>10} "
              f"{'✅' if ec.get('phones') else '❌':>10} "
              f"{'✅' if cl.get('emails') or cl.get('contact_emails') else '❌':>10} "
              f"{'✅' if cl.get('contact_names') else '❌':>10}")

    # Final ruling
    print(f"\n  {'=' * 74}")
    print(f"  FINAL RULING")
    print(f"  {'=' * 74}")

    if best_rate >= 60:
        winner = "/emails-and-contacts" if ec_rate >= cl_rate else "/contacts-and-leads"
        print(f"  VERDICT: OUTSCRAPER REPLACES HUNTER AS PRIMARY ENRICHMENT")
        print(f"  Best endpoint: {winner} ({best_rate:.0f}% email fill rate)")
        print(f"  Architecture: Outscraper Maps → Outscraper {winner} → HubSpot")
        print(f"  Hunter.io: DEMOTED to optional fallback (not needed in V1 core)")
        ruling = "outscraper_primary"
    elif best_rate >= 30:
        print(f"  VERDICT: HYBRID — Outscraper primary, Hunter fallback")
        print(f"  Best email fill rate: {best_rate:.0f}%")
        print(f"  Architecture: Outscraper Maps → Outscraper Emails → Hunter fallback → HubSpot")
        ruling = "hybrid"
    else:
        print(f"  VERDICT: HUNTER STAYS PRIMARY")
        print(f"  Best email fill rate: {best_rate:.0f}%")
        print(f"  Architecture: Outscraper Maps → Hunter.io → HubSpot")
        ruling = "hunter_primary"

    return ruling, best_rate


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not OUTSCRAPER_API_KEY:
        print("Set OUTSCRAPER_API_KEY to run this proof")
        sys.exit(1)

    # Step 1: Get domains from Maps
    domains = collect_domains_from_maps()
    if len(domains) < 5:
        print(f"FAIL: Only {len(domains)} usable domains found — need at least 5")
        sys.exit(1)

    # Step 2: Test /emails-and-contacts
    ec_results = test_emails_and_contacts(domains)

    # Step 3: Test /contacts-and-leads
    cl_results = test_contacts_and_leads(domains)

    # Step 4: Summary & verdict
    ruling, rate = summarize(domains, ec_results, cl_results)

    print(f"\nDONE — ruling={ruling}, best_rate={rate:.0f}%")
