#!/usr/bin/env python3
"""Stripe payment handling for Genesis AI Systems V1.

Handles:
1. Creating proposal-specific payment links (separate from site buy-now links)
2. Verifying webhook signatures from n8n
3. Extracting payment details for HubSpot updates

The actual webhook endpoint lives in n8n. This module provides helper
functions that n8n calls via HTTP request node or that agents use directly.

Usage:
    from stripe_handler import StripeHandler

    sh = StripeHandler()
    link = sh.create_payment_link(client_name="Slows Bar BQ", amount_cents=50000, plan="starter")
    payment = sh.verify_webhook(payload, signature)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class PaymentEvent:
    """Parsed Stripe payment event."""
    payment_id: str
    customer_email: str
    customer_name: str
    amount_cents: int
    currency: str
    status: str
    metadata: dict

    @property
    def amount_dollars(self) -> float:
        return self.amount_cents / 100.0

    @property
    def client_name(self) -> str:
        return self.metadata.get("client_name", self.customer_name)


class StripeHandler:
    """Stripe integration for proposal payments and webhooks."""

    API_BASE = "https://api.stripe.com/v1"

    # Existing site payment links (do not modify)
    SITE_LINKS = {
        "starter_buy": os.getenv("STRIPE_STARTER_LINK", ""),
        "growth_buy": os.getenv("STRIPE_GROWTH_LINK", ""),
    }

    # Proposal pricing
    PROPOSAL_PRICING = {
        "starter": {
            "setup": 50000,      # $500.00
            "monthly": 15000,    # $150.00
            "name": "Starter — Never Miss a Customer Again",
        },
        "growth": {
            "setup": 350000,     # $3,500.00
            "monthly": 30000,    # $300.00
            "name": "Growth — Full AI Automation Package",
        },
    }

    def __init__(self):
        self.secret_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.secret_key)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def create_payment_link(
        self,
        client_name: str,
        plan: str = "starter",
        client_email: str = "",
    ) -> Optional[str]:
        """Create a one-time Stripe payment link for a proposal.

        Returns the payment URL or None on failure.
        """
        if not self.configured:
            print("⚠️  Stripe not configured — payment link not created")
            return None

        pricing = self.PROPOSAL_PRICING.get(plan)
        if not pricing:
            print(f"❌ Unknown plan: {plan}")
            return None

        try:
            # Create a checkout session instead of payment link for metadata support
            data = {
                "mode": "payment",
                "success_url": "https://genesisai.systems/thank-you.html?session_id={CHECKOUT_SESSION_ID}",
                "cancel_url": "https://genesisai.systems/contact.html",
                "line_items[0][price_data][currency]": "usd",
                "line_items[0][price_data][unit_amount]": str(pricing["setup"]),
                "line_items[0][price_data][product_data][name]": pricing["name"],
                "metadata[client_name]": client_name,
                "metadata[plan]": plan,
                "metadata[source]": "proposal",
            }

            if client_email:
                data["customer_email"] = client_email

            resp = requests.post(
                f"{self.API_BASE}/checkout/sessions",
                headers=self._headers(),
                data=data,
                timeout=15,
            )

            if resp.ok:
                url = resp.json().get("url")
                print(f"✅ Payment link created for {client_name}: {url}")
                return url
            else:
                print(f"❌ Stripe create session failed: {resp.status_code} — {resp.text[:300]}")
                return None

        except Exception as e:
            print(f"❌ Stripe exception: {e}")
            return None

    def parse_webhook_event(self, payload: dict) -> Optional[PaymentEvent]:
        """Parse a Stripe webhook event into a PaymentEvent.

        Called by n8n or by a direct webhook handler.
        Handles: checkout.session.completed, payment_intent.succeeded
        """
        event_type = payload.get("type", "")
        data_obj = payload.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            return PaymentEvent(
                payment_id=data_obj.get("id", ""),
                customer_email=data_obj.get("customer_email", data_obj.get("customer_details", {}).get("email", "")),
                customer_name=data_obj.get("customer_details", {}).get("name", ""),
                amount_cents=data_obj.get("amount_total", 0),
                currency=data_obj.get("currency", "usd"),
                status=data_obj.get("payment_status", ""),
                metadata=data_obj.get("metadata", {}),
            )

        elif event_type == "payment_intent.succeeded":
            return PaymentEvent(
                payment_id=data_obj.get("id", ""),
                customer_email=data_obj.get("receipt_email", ""),
                customer_name=data_obj.get("metadata", {}).get("client_name", ""),
                amount_cents=data_obj.get("amount", 0),
                currency=data_obj.get("currency", "usd"),
                status="succeeded",
                metadata=data_obj.get("metadata", {}),
            )

        return None

    def get_recent_payments(self, limit: int = 10) -> list[dict]:
        """Get recent successful payments for reporting."""
        if not self.configured:
            return []

        try:
            resp = requests.get(
                f"{self.API_BASE}/payment_intents",
                headers=self._headers(),
                params={"limit": limit, "status": "succeeded"},
                timeout=15,
            )
            if resp.ok:
                return resp.json().get("data", [])
            return []
        except Exception:
            return []
