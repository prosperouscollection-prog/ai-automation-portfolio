#!/usr/bin/env python3
"""HoneyBook client for Genesis AI Systems V1.

STATUS: HoneyBook direct REST API access is UNVERIFIED.
HoneyBook does not publish a documented public API for programmatic project creation.
The endpoint https://api.honeybook.com/v1/projects is provisional — not confirmed to exist.

V1 BEHAVIOR (until API is verified):
- This module will attempt the API call if HONEYBOOK_API_KEY is set.
- All callers check the return value. None = failure.
- On None, callers send a HIGH Telegram alert to the founder to send manually
  from the HoneyBook dashboard.
- No Resend fallback. No email bypass. Manual HoneyBook send is the only fallback.

HONEYBOOK IS STILL THE SYSTEM OF RECORD:
- Proposals must exist as HoneyBook projects before advancing HubSpot.
- The demo-done-to-proposal n8n workflow handles this by alerting the founder
  with client details and instructions — it does NOT call this module.

To verify HoneyBook API access:
1. Check app.honeybook.com/app/settings/integrations for API docs or token
2. Test: curl -H "Authorization: Bearer <key>" https://api.honeybook.com/v1/projects
3. Update API_BASE and request schema if endpoint differs

Usage (once verified):
    from honeybook_client import HoneyBookClient

    hb = HoneyBookClient()
    result = hb.send_proposal(client_name="Slows Bar BQ", client_email="owner@slowsbarbq.com", plan="starter")
    if result is None:
        # alert founder — see intake_agent.py for reference pattern
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
class HoneyBookProject:
    """Represents a HoneyBook project/proposal."""
    project_id: str
    client_name: str
    client_email: str
    plan: str
    status: str  # draft, sent, viewed, signed, paid
    url: str = ""


class HoneyBookClient:
    """HoneyBook integration for proposals, contracts, and intake forms.

    HoneyBook is the system of record for proposals, contracts, and intake.
    All sends go through HoneyBook so a project record always exists.

    If the API is unavailable:
    - The caller receives None (failure)
    - The caller (intake_agent, proposal_agent) alerts the founder via Telegram
      to send manually from HoneyBook dashboard
    - A plain Resend email is NOT used as a bypass — that would create a record
      in the client's inbox with no corresponding HoneyBook project
    """

    API_BASE = "https://api.honeybook.com/v1"  # UNVERIFIED — endpoint not confirmed to exist. See module docstring.

    # Template IDs — set these after creating templates in HoneyBook
    TEMPLATES = {
        "starter_proposal": os.getenv("HONEYBOOK_STARTER_TEMPLATE_ID", ""),
        "growth_proposal": os.getenv("HONEYBOOK_GROWTH_TEMPLATE_ID", ""),
        "intake_form": os.getenv("HONEYBOOK_INTAKE_TEMPLATE_ID", ""),
    }

    def __init__(self):
        self.api_key = os.getenv("HONEYBOOK_API_KEY", "").strip()

    @property
    def api_available(self) -> bool:
        """Check if HoneyBook API is configured and accessible."""
        return bool(self.api_key)

    def send_proposal(
        self,
        client_name: str,
        client_email: str,
        plan: str = "starter",
    ) -> Optional[str]:
        """Send a proposal through HoneyBook. Returns HoneyBook project ID or None.

        On failure returns None. The caller must alert the founder to send manually
        from HoneyBook dashboard — do not bypass with a plain email.
        """
        template_key = f"{plan}_proposal"

        if not self.api_available:
            print(f"❌ HoneyBook API not configured — cannot send proposal for {client_name}")
            return None

        template_id = self.TEMPLATES.get(template_key)
        if not template_id:
            print(f"❌ No HoneyBook template ID set for {template_key}")
            return None

        return self._send_via_api(
            template_id=template_id,
            client_name=client_name,
            client_email=client_email,
            subject=f"Genesis AI Systems — {plan.title()} Proposal for {client_name}",
        )

    def send_intake_form(
        self,
        client_name: str,
        client_email: str,
    ) -> Optional[str]:
        """Send onboarding intake form through HoneyBook. Returns project ID or None.

        On failure returns None. The caller must alert the founder to send manually
        from HoneyBook dashboard — do not bypass with a plain email.
        """
        if not self.api_available:
            print(f"❌ HoneyBook API not configured — cannot send intake form for {client_name}")
            return None

        template_id = self.TEMPLATES.get("intake_form")
        if not template_id:
            print(f"❌ No HoneyBook intake form template ID set")
            return None

        return self._send_via_api(
            template_id=template_id,
            client_name=client_name,
            client_email=client_email,
            subject=f"Welcome to Genesis AI Systems — Let's Get Started, {client_name}!",
        )

    def _send_via_api(
        self,
        template_id: str,
        client_name: str,
        client_email: str,
        subject: str,
    ) -> Optional[str]:
        """Send via HoneyBook API (if available)."""
        try:
            resp = requests.post(
                f"{self.API_BASE}/projects",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "template_id": template_id,
                    "client": {
                        "name": client_name,
                        "email": client_email,
                    },
                    "subject": subject,
                    "send_immediately": True,
                },
                timeout=15,
            )

            if resp.ok:
                project_id = resp.json().get("id", "unknown")
                print(f"✅ HoneyBook project created: {project_id} for {client_name}")
                return project_id
            else:
                print(f"❌ HoneyBook API failed: {resp.status_code} — {resp.text[:200]}")
                return None

        except Exception as e:
            print(f"❌ HoneyBook API exception: {e}")
            return None

    @staticmethod
    def parse_webhook(payload: dict) -> Optional[dict]:
        """Parse a HoneyBook webhook payload.

        Returns normalized event dict with: event_type, project_id, client_email, client_name
        """
        event_type = payload.get("event_type", payload.get("type", ""))
        data = payload.get("data", payload)

        if not event_type:
            return None

        return {
            "event_type": event_type,
            "project_id": data.get("project_id", data.get("id", "")),
            "client_email": data.get("client", {}).get("email", data.get("email", "")),
            "client_name": data.get("client", {}).get("name", data.get("name", "")),
            "raw": payload,
        }
