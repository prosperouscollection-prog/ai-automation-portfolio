#!/usr/bin/env python3
"""Intake / Onboarding Agent for Genesis AI Systems V1.

Scope (V1 only):
1. Trigger HoneyBook intake form after PAYMENT_RECEIVED
2. Track whether intake was completed (update HubSpot to INTAKE_COMPLETE)

HoneyBook is the system of record for intake.
No Sheets writes. No deployment prompting (that belongs to Deploy Agent).
"""

from __future__ import annotations

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "v1-revenue-system"))

from notify import telegram_notify

HUBSPOT_API = "https://api.hubapi.com"


class IntakeAgent:
    """Manages client onboarding from payment to deployment readiness."""

    def __init__(self) -> None:
        self.hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
        self.honeybook_key = os.getenv("HONEYBOOK_API_KEY", "").strip()

    def run(self) -> None:
        print("📦 Intake Agent starting...")

        # Find deals at PAYMENT_RECEIVED that haven't had intake form sent yet
        needs_intake = self.get_deals_needing_intake()
        for deal in needs_intake:
            self.send_intake_form(deal)

        if needs_intake:
            print(f"✅ Intake Agent sent {len(needs_intake)} intake forms")
        else:
            print("ℹ️  No intake actions needed")

    def get_deals_needing_intake(self) -> list[dict]:
        """Find deals at PAYMENT_RECEIVED where intake_completed is false."""
        return self._search_deals("payment_received", intake_completed=False)

    def _search_deals(self, stage: str, intake_completed: bool = False) -> list[dict]:
        """Search HubSpot for deals at a specific stage."""
        if not self.hubspot_token:
            return []

        filters = [{"propertyName": "dealstage", "operator": "EQ", "value": stage}]

        try:
            resp = requests.post(
                f"{HUBSPOT_API}/crm/v3/objects/deals/search",
                headers={
                    "Authorization": f"Bearer {self.hubspot_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "filterGroups": [{"filters": filters}],
                    "properties": [
                        "dealname", "dealstage", "owner_email", "proposal_type",
                        "intake_completed", "stripe_payment_id",
                    ],
                    "limit": 20,
                },
                timeout=15,
            )
            if resp.ok:
                results = resp.json().get("results", [])
                # Filter by intake_completed status
                filtered = []
                for r in results:
                    props = r.get("properties", {})
                    is_complete = props.get("intake_completed", "false").lower() == "true"
                    if is_complete == intake_completed:
                        filtered.append(r)
                return filtered
            return []
        except Exception as e:
            print(f"❌ HubSpot search error: {e}")
            return []

    def send_intake_form(self, deal: dict) -> None:
        """Send HoneyBook intake form to client. HoneyBook is the system of record.

        If HoneyBook send fails, alerts founder via Telegram to send manually.
        Does NOT fall back to a plain email — that would bypass HoneyBook records.
        """
        props = deal.get("properties", {})
        deal_id = deal.get("id", "")
        client_name = props.get("dealname", "Unknown")
        client_email = props.get("owner_email", "")

        if not client_email:
            print(f"⚠️  No email for {client_name} — cannot send intake form")
            telegram_notify(
                "Intake Agent",
                f"⚠️ Cannot send intake form to <b>{client_name}</b> — no email on file.\n"
                f"Add owner_email to HubSpot deal {deal_id} and resend manually.",
                "HIGH",
            )
            return

        print(f"📋 Sending HoneyBook intake form to {client_name} ({client_email})")

        from honeybook_client import HoneyBookClient
        hb = HoneyBookClient()
        result = hb.send_intake_form(client_name, client_email)

        if result:
            print(f"✅ Intake form sent via HoneyBook")
            telegram_notify(
                "Intake Agent",
                f"📋 <b>Intake form sent</b>\n{client_name} ({client_email})\n"
                f"HoneyBook project: {result}\nWaiting for client to complete.",
                "MEDIUM",
            )
        else:
            # HoneyBook failed — do not bypass with a plain email
            print(f"❌ HoneyBook intake send failed for {client_name}")
            telegram_notify(
                "Intake Agent",
                f"❌ <b>Intake form FAILED</b> for {client_name}\n"
                f"Send manually from HoneyBook dashboard to {client_email}.\n"
                f"Deal ID: {deal_id}",
                "HIGH",
            )

    def record_intake_completion(self, deal_id: str) -> None:
        """Called by n8n webhook when HoneyBook intake form is completed.

        Updates HubSpot deal to INTAKE_COMPLETE. HoneyBook holds the form data.
        """
        if not self.hubspot_token:
            return

        try:
            requests.patch(
                f"{HUBSPOT_API}/crm/v3/objects/deals/{deal_id}",
                headers={
                    "Authorization": f"Bearer {self.hubspot_token}",
                    "Content-Type": "application/json",
                },
                json={"properties": {"dealstage": "intake_complete", "intake_completed": "true"}},
                timeout=15,
            )
            print(f"✅ HubSpot updated: {deal_id} → intake_complete")
            telegram_notify(
                "Intake Agent",
                f"📦 <b>Intake complete</b> for deal {deal_id}\n"
                f"HubSpot updated to INTAKE_COMPLETE.\n"
                f"Trendell: reply <code>/deploy [client name]</code> when ready.",
                "HIGH",
            )
        except Exception as e:
            print(f"❌ HubSpot update error: {e}")
            telegram_notify(
                "Intake Agent",
                f"❌ <b>HubSpot update FAILED</b> for deal <code>{deal_id}</code>\n"
                f"Error: {e}\n\n"
                f"Manually update HubSpot deal {deal_id} to stage <b>INTAKE_COMPLETE</b> "
                f"and set intake_completed = true.",
                "HIGH",
            )


def main() -> None:
    agent = IntakeAgent()
    agent.run()


if __name__ == "__main__":
    main()
