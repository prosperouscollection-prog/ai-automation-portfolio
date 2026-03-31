#!/usr/bin/env python3
"""One-time webhook registration script for Genesis AI Systems V1.

Registers:
  1. Calendly webhook → n8n.genesisai.systems/webhook/calendly-booked
  2. Verifies Stripe webhook endpoint is active

Required env vars:
  CALENDLY_TOKEN     — Calendly Personal Access Token
  CALENDLY_ORG_URL   — e.g. https://api.calendly.com/organizations/XXXX
  STRIPE_SECRET_KEY  — sk_live_... or sk_test_...
"""

import os
import sys
import json
import traceback

print("register_webhooks.py: starting", flush=True)

try:
    import requests
    print("requests imported OK", flush=True)

    N8N_CALENDLY_WEBHOOK = "https://n8n.genesisai.systems/webhook/calendly-booked"
    N8N_STRIPE_WEBHOOK   = "https://n8n.genesisai.systems/webhook/stripe-payment"

    CALENDLY_TOKEN   = os.environ.get("CALENDLY_TOKEN", "")
    CALENDLY_ORG_URL = os.environ.get("CALENDLY_ORG_URL", "")
    STRIPE_SECRET    = os.environ.get("STRIPE_SECRET_KEY", "")

    print(f"CALENDLY_TOKEN set:   {'YES' if CALENDLY_TOKEN else 'NO'}", flush=True)
    print(f"CALENDLY_ORG_URL set: {'YES' if CALENDLY_ORG_URL else 'NO'}", flush=True)
    print(f"STRIPE_SECRET_KEY set: {'YES' if STRIPE_SECRET else 'NO'}", flush=True)

    errors = []
    if not CALENDLY_TOKEN:
        errors.append("CALENDLY_TOKEN is not set")
    if not CALENDLY_ORG_URL:
        errors.append("CALENDLY_ORG_URL is not set")
    if not STRIPE_SECRET:
        errors.append("STRIPE_SECRET_KEY is not set")

    if errors:
        for e in errors:
            print(f"  MISSING: {e}", flush=True)
        sys.exit(1)


    # ── 1. Calendly webhook registration ────────────────────────────────────────
    print("\n── 1. Calendly webhook ─────────────────────────────────────────────────", flush=True)

    payload = {
        "url": N8N_CALENDLY_WEBHOOK,
        "events": ["invitee.created"],
        "organization": CALENDLY_ORG_URL,
        "scope": "organization",
    }

    resp = requests.post(
        "https://api.calendly.com/webhook_subscriptions",
        headers={
            "Authorization": f"Bearer {CALENDLY_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )

    print(f"Status: {resp.status_code}", flush=True)
    try:
        body = resp.json()
        print(json.dumps(body, indent=2), flush=True)
    except Exception:
        print(resp.text, flush=True)

    if resp.status_code in (200, 201):
        print("\nCALENDLY: PASS", flush=True)
    elif resp.status_code == 409:
        print("\nCALENDLY: PASS (already registered — 409 Conflict means webhook exists)", flush=True)
    else:
        print("\nCALENDLY: FAIL", flush=True)


    # ── 2. Stripe webhook verification ──────────────────────────────────────────
    print("\n── 2. Stripe webhook ───────────────────────────────────────────────────", flush=True)

    resp2 = requests.get(
        "https://api.stripe.com/v1/webhook_endpoints",
        headers={"Authorization": f"Bearer {STRIPE_SECRET}"},
        timeout=15,
    )

    print(f"Status: {resp2.status_code}", flush=True)
    try:
        body2 = resp2.json()
        print(json.dumps(body2, indent=2), flush=True)
    except Exception:
        print(resp2.text, flush=True)

    stripe_pass = False
    if resp2.status_code == 200:
        endpoints = body2.get("data", [])
        for ep in endpoints:
            url = ep.get("url", "")
            status = ep.get("status", "")
            print(f"\n  endpoint: {url}", flush=True)
            print(f"  status:   {status}", flush=True)
            if N8N_STRIPE_WEBHOOK in url and status == "enabled":
                stripe_pass = True

    if stripe_pass:
        print("\nSTRIPE: PASS", flush=True)
    else:
        print(f"\nSTRIPE: FAIL — no active endpoint found for {N8N_STRIPE_WEBHOOK}", flush=True)
        print("  Action: Stripe → Developers → Webhooks → Add endpoint", flush=True)
        print(f"  URL: {N8N_STRIPE_WEBHOOK}", flush=True)
        print("  Events: checkout.session.completed, payment_intent.succeeded", flush=True)

except Exception:
    print("\n── UNHANDLED EXCEPTION ─────────────────────────────────────────────────", flush=True)
    traceback.print_exc()
    sys.exit(1)

print("\nDONE", flush=True)
