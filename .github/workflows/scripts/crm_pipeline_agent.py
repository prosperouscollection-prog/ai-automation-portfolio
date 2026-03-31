#!/usr/bin/env python3
"""CRM / Pipeline Agent for Genesis AI Systems V1.

Runs every 2 hours. Responsibilities:
1. Detect stale deals (>48hrs in any pre-outreach stage)
2. Report pipeline summary to Telegram

HubSpot is the system of record. This agent reads HubSpot and alerts.
It does NOT sync to Sheets. Sheets is not part of V1 CRM logic.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

# Add v1-revenue-system to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "v1-revenue-system"))

from notify import telegram_notify

HUBSPOT_API = "https://api.hubapi.com"

# Stages where stale detection applies (pre-demo in lean V1 pipeline)
STALE_STAGES = ["new_lead", "outreach_sent"]
STALE_THRESHOLD_HOURS = 48


class CRMPipelineAgent:
    """Reads HubSpot pipeline, flags stale deals, reports to Telegram.

    HubSpot is the system of record. No Sheets sync in V1.
    """

    def __init__(self) -> None:
        self.hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()

    def run(self) -> None:
        print("🔄 CRM Pipeline Agent starting...")

        # 1. Pull all active deals from HubSpot
        deals = self.get_hubspot_deals()
        if not deals:
            print("ℹ️  No active deals in HubSpot")
            return

        # 2. Check for stale deals
        stale = self.find_stale_deals(deals)

        # 3. Send summary to Telegram
        self.send_summary(deals, stale)

        print(f"✅ CRM Pipeline Agent complete — {len(deals)} deals checked, {len(stale)} stale")

    def get_hubspot_deals(self) -> list[dict]:
        """Fetch all non-LOST, non-LIVE deals from HubSpot."""
        if not self.hubspot_token:
            print("⚠️  HubSpot not configured")
            return []

        headers = {
            "Authorization": f"Bearer {self.hubspot_token}",
            "Content-Type": "application/json",
        }

        all_deals = []
        # Exclude terminal stages (lean V1 pipeline)
        exclude_stages = ["deployed", "lost"]

        try:
            # Use search to get deals with properties
            resp = requests.post(
                f"{HUBSPOT_API}/crm/v3/objects/deals/search",
                headers=headers,
                json={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "dealstage",
                            "operator": "NOT_IN",
                            "values": exclude_stages,
                        }]
                    }],
                    "properties": [
                        "dealname", "dealstage", "owner_email", "lead_source",
                        "lead_score", "amount", "createdate", "hs_lastmodifieddate",
                        "proposal_type", "qa_result",
                    ],
                    "limit": 100,
                    "sorts": [{"propertyName": "createdate", "direction": "DESCENDING"}],
                },
                timeout=15,
            )

            if resp.ok:
                all_deals = resp.json().get("results", [])
                print(f"📊 Fetched {len(all_deals)} active deals from HubSpot")
            else:
                print(f"❌ HubSpot search failed: {resp.status_code} — {resp.text[:300]}")

        except Exception as e:
            print(f"❌ HubSpot exception: {e}")

        return all_deals

    def find_stale_deals(self, deals: list[dict]) -> list[dict]:
        """Find deals stuck in pre-demo stages for >48 hours."""
        stale = []
        now = datetime.now(timezone.utc)

        for deal in deals:
            props = deal.get("properties", {})
            stage = props.get("dealstage", "")

            if stage not in STALE_STAGES:
                continue

            # Check last modified date
            modified_str = props.get("hs_lastmodifieddate", "")
            if not modified_str:
                continue

            try:
                # HubSpot returns ISO format
                modified = datetime.fromisoformat(modified_str.replace("Z", "+00:00"))
                hours_since = (now - modified).total_seconds() / 3600

                if hours_since > STALE_THRESHOLD_HOURS:
                    stale.append({
                        "name": props.get("dealname", "Unknown"),
                        "stage": stage,
                        "hours_stale": round(hours_since),
                        "deal_id": deal.get("id"),
                    })
            except (ValueError, TypeError):
                continue

        if stale:
            # Alert on stale deals
            msg = "⚠️ <b>STALE DEALS ALERT</b>\n\n"
            for s in stale:
                msg += f"• <b>{s['name']}</b> — stuck at {s['stage']} for {s['hours_stale']}hrs\n"
            msg += "\nReply /send [name] to approve outreach or /skip [name] to pass."
            telegram_notify("CRM Pipeline", msg, "HIGH")
            print(f"⚠️  {len(stale)} stale deals flagged")

        return stale

    def send_summary(self, deals: list[dict], stale: list[dict]) -> None:
        """Send pipeline summary to Telegram."""
        # Count by stage
        stage_counts: dict[str, int] = {}
        total_value = 0.0

        for deal in deals:
            props = deal.get("properties", {})
            stage = props.get("dealstage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            try:
                total_value += float(props.get("amount", 0) or 0)
            except (ValueError, TypeError):
                pass

        msg = "📊 <b>Pipeline Sync Complete</b>\n\n"
        for stage, count in sorted(stage_counts.items()):
            msg += f"• {stage}: <b>{count}</b>\n"
        msg += f"\n💰 Pipeline value: <b>${total_value:,.0f}</b>"
        if stale:
            msg += f"\n⚠️ Stale deals: <b>{len(stale)}</b>"

        telegram_notify("CRM Pipeline", msg, "INFO")


def main() -> None:
    agent = CRMPipelineAgent()
    agent.run()


if __name__ == "__main__":
    main()
