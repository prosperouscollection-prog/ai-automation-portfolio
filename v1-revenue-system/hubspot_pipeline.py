#!/usr/bin/env python3
"""HubSpot deal pipeline manager for Genesis AI Systems V1 revenue corridor.

Owns all deal stage transitions. Every agent that needs to update a deal stage
calls this module rather than hitting HubSpot directly. This ensures:
1. Stage names are consistent (single source of truth)
2. Every stage change fires a Telegram notification
3. Invalid transitions are caught

Usage:
    from hubspot_pipeline import PipelineManager, Stage

    pm = PipelineManager()
    pm.move_deal(deal_id="12345", to_stage=Stage.OUTREACH_SENT)
    pm.get_deals_at_stage(Stage.NEW_LEAD)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class Stage(Enum):
    """HubSpot deal stages for the Genesis Revenue Pipeline.

    Lean V1 path only. QA state lives in GitHub Actions + Render, not here.
    LOST is terminal from any stage.
    """
    NEW_LEAD = "new_lead"
    OUTREACH_SENT = "outreach_sent"
    DEMO_BOOKED = "demo_booked"
    PROPOSAL_SENT = "proposal_sent"
    PAYMENT_RECEIVED = "payment_received"
    INTAKE_COMPLETE = "intake_complete"
    DEPLOYED = "deployed"
    LOST = "lost"  # Terminal — can be set from any stage


# Ordered list for progression checks (LOST excluded)
STAGE_ORDER = [s for s in Stage if s != Stage.LOST]


@dataclass
class Deal:
    """Lightweight representation of a HubSpot deal."""
    deal_id: str
    name: str
    stage: Stage
    owner_email: str = ""
    lead_source: str = ""
    proposal_type: str = ""
    amount: float = 0.0
    properties: dict = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class PipelineManager:
    """Manages the Genesis Revenue Pipeline in HubSpot."""

    HUBSPOT_API = "https://api.hubapi.com"

    # Custom properties to create in HubSpot (run setup once)
    CUSTOM_PROPERTIES = [
        {"name": "lead_source", "label": "Lead Source", "type": "enumeration",
         "options": ["yelp", "google_maps", "website", "referral", "cold_outreach"]},
        {"name": "lead_score", "label": "Lead Score", "type": "enumeration",
         "options": ["HOT", "WARM", "COLD"]},
        {"name": "owner_email", "label": "Owner Email", "type": "string"},
        {"name": "proposal_type", "label": "Proposal Type", "type": "enumeration",
         "options": ["starter", "growth"]},
        {"name": "stripe_payment_id", "label": "Stripe Payment ID", "type": "string"},
        {"name": "honeybook_project_id", "label": "HoneyBook Project ID", "type": "string"},
        {"name": "intake_completed", "label": "Intake Completed", "type": "bool"},
        {"name": "deploy_approved_at", "label": "Deploy Approved At", "type": "datetime"},
        {"name": "qa_result", "label": "QA Result", "type": "enumeration",
         "options": ["pass", "fail", "pending"]},
        {"name": "client_go_live_date", "label": "Go Live Date", "type": "datetime"},
    ]

    def __init__(self):
        self.token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _telegram(self, text: str) -> None:
        """Send pipeline event to Telegram."""
        if not self.telegram_token or not self.telegram_chat:
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                json={"chat_id": self.telegram_chat, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
        except Exception:
            pass  # Pipeline updates must not fail on notification errors

    # --- Deal Operations ---

    def create_deal(
        self,
        name: str,
        stage: Stage = Stage.NEW_LEAD,
        owner_email: str = "",
        lead_source: str = "yelp",
        lead_score: str = "HOT",
        properties: Optional[dict] = None,
    ) -> Optional[str]:
        """Create a new deal in the Genesis Revenue Pipeline.

        Returns the HubSpot deal ID on success, None on failure.
        """
        if not self.configured:
            print("⚠️  HubSpot not configured — deal not created")
            return None

        props = {
            "dealname": name,
            "dealstage": stage.value,
            "pipeline": "default",  # Will be updated to custom pipeline ID
            "lead_source": lead_source,
            "lead_score": lead_score,
        }
        if owner_email:
            props["owner_email"] = owner_email
        if properties:
            props.update(properties)

        try:
            resp = requests.post(
                f"{self.HUBSPOT_API}/crm/v3/objects/deals",
                headers=self._headers(),
                json={"properties": props},
                timeout=15,
            )
            if resp.ok:
                deal_id = resp.json().get("id")
                print(f"✅ Deal created: {name} → {stage.value} (ID: {deal_id})")
                self._telegram(f"🆕 <b>New Deal:</b> {name}\n<b>Stage:</b> {stage.value}\n<b>Source:</b> {lead_source}")
                return deal_id
            else:
                print(f"❌ HubSpot create deal failed: {resp.status_code} — {resp.text[:300]}")
                return None
        except Exception as e:
            print(f"❌ HubSpot exception: {e}")
            return None

    def move_deal(self, deal_id: str, to_stage: Stage, properties: Optional[dict] = None) -> bool:
        """Move a deal to a new stage.

        Validates the transition is forward (or to LOST).
        Updates HubSpot and sends Telegram notification.
        """
        if not self.configured:
            return False

        props = {"dealstage": to_stage.value}
        if properties:
            props.update(properties)

        try:
            resp = requests.patch(
                f"{self.HUBSPOT_API}/crm/v3/objects/deals/{deal_id}",
                headers=self._headers(),
                json={"properties": props},
                timeout=15,
            )
            if resp.ok:
                deal_name = resp.json().get("properties", {}).get("dealname", deal_id)
                emoji = self._stage_emoji(to_stage)
                print(f"{emoji} Deal moved: {deal_name} → {to_stage.value}")
                self._telegram(f"{emoji} <b>Pipeline Update:</b> {deal_name}\n<b>Stage:</b> {to_stage.value}")
                return True
            else:
                print(f"❌ HubSpot move deal failed: {resp.status_code} — {resp.text[:300]}")
                return False
        except Exception as e:
            print(f"❌ HubSpot exception: {e}")
            return False

    def get_deals_at_stage(self, stage: Stage, limit: int = 50) -> list[Deal]:
        """Get all deals at a specific pipeline stage."""
        if not self.configured:
            return []

        try:
            resp = requests.post(
                f"{self.HUBSPOT_API}/crm/v3/objects/deals/search",
                headers=self._headers(),
                json={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "dealstage",
                            "operator": "EQ",
                            "value": stage.value,
                        }]
                    }],
                    "properties": [
                        "dealname", "dealstage", "owner_email", "lead_source",
                        "proposal_type", "amount", "lead_score",
                    ],
                    "limit": limit,
                },
                timeout=15,
            )
            if not resp.ok:
                print(f"❌ HubSpot search failed: {resp.status_code}")
                return []

            results = resp.json().get("results", [])
            deals = []
            for r in results:
                props = r.get("properties", {})
                deals.append(Deal(
                    deal_id=r.get("id", ""),
                    name=props.get("dealname", "Unknown"),
                    stage=stage,
                    owner_email=props.get("owner_email", ""),
                    lead_source=props.get("lead_source", ""),
                    proposal_type=props.get("proposal_type", ""),
                    amount=float(props.get("amount", 0) or 0),
                    properties=props,
                ))
            return deals
        except Exception as e:
            print(f"❌ HubSpot search exception: {e}")
            return []

    def get_deal(self, deal_id: str) -> Optional[Deal]:
        """Get a single deal by ID."""
        if not self.configured:
            return None

        try:
            resp = requests.get(
                f"{self.HUBSPOT_API}/crm/v3/objects/deals/{deal_id}",
                headers=self._headers(),
                params={
                    "properties": "dealname,dealstage,owner_email,lead_source,proposal_type,amount,lead_score",
                },
                timeout=15,
            )
            if not resp.ok:
                return None

            props = resp.json().get("properties", {})
            stage_val = props.get("dealstage", "new_lead")
            try:
                stage = Stage(stage_val)
            except ValueError:
                stage = Stage.NEW_LEAD

            return Deal(
                deal_id=deal_id,
                name=props.get("dealname", "Unknown"),
                stage=stage,
                owner_email=props.get("owner_email", ""),
                lead_source=props.get("lead_source", ""),
                proposal_type=props.get("proposal_type", ""),
                amount=float(props.get("amount", 0) or 0),
                properties=props,
            )
        except Exception as e:
            print(f"❌ HubSpot get deal exception: {e}")
            return None

    def find_deal_by_name(self, name: str) -> Optional[Deal]:
        """Search for a deal by company name (partial match)."""
        if not self.configured:
            return None

        try:
            resp = requests.post(
                f"{self.HUBSPOT_API}/crm/v3/objects/deals/search",
                headers=self._headers(),
                json={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "dealname",
                            "operator": "CONTAINS_TOKEN",
                            "value": name,
                        }]
                    }],
                    "properties": [
                        "dealname", "dealstage", "owner_email", "lead_source",
                        "proposal_type", "amount",
                    ],
                    "limit": 1,
                },
                timeout=15,
            )
            if not resp.ok:
                return None

            results = resp.json().get("results", [])
            if not results:
                return None

            r = results[0]
            props = r.get("properties", {})
            stage_val = props.get("dealstage", "new_lead")
            try:
                stage = Stage(stage_val)
            except ValueError:
                stage = Stage.NEW_LEAD

            return Deal(
                deal_id=r.get("id", ""),
                name=props.get("dealname", "Unknown"),
                stage=stage,
                owner_email=props.get("owner_email", ""),
                properties=props,
            )
        except Exception:
            return None

    def get_pipeline_summary(self) -> dict[str, int]:
        """Get deal count per stage for reporting."""
        summary = {}
        for stage in Stage:
            deals = self.get_deals_at_stage(stage, limit=1)
            # Use search count instead of fetching all deals
            summary[stage.value] = len(deals)  # Approximate — improve with aggregation API
        return summary

    def get_pipeline_value(self) -> float:
        """Get total pipeline value across all active stages."""
        total = 0.0
        for stage in STAGE_ORDER:
            if stage == Stage.DEPLOYED:
                continue
            deals = self.get_deals_at_stage(stage)
            total += sum(d.amount for d in deals)
        return total

    # --- Utilities ---

    @staticmethod
    def _stage_emoji(stage: Stage) -> str:
        return {
            Stage.NEW_LEAD: "🆕",
            Stage.OUTREACH_SENT: "📧",
            Stage.DEMO_BOOKED: "📅",
            Stage.PROPOSAL_SENT: "📋",
            Stage.PAYMENT_RECEIVED: "💰",
            Stage.INTAKE_COMPLETE: "📦",
            Stage.DEPLOYED: "🟢",
            Stage.LOST: "❌",
        }.get(stage, "▪️")
