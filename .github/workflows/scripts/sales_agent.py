#!/usr/bin/env python3
"""Sales helper that follows up on new leads and alerts Trendell on hot ones."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Lead:
    """Simple lead record used by the sales helper."""

    name: str
    business: str
    email: str
    phone: str
    business_type: str
    pain_point: str
    score: str


class SalesAgent:
    """Reads new leads, follows up, and pushes hot ones to Trendell fast."""

    STAGES = {
        "New": 1,
        "Contacted": 2,
        "Demo Booked": 3,
        "Proposal Sent": 4,
        "Won": 5,
        "Lost": 6,
    }

    def __init__(self) -> None:
        self.demo_server = os.getenv("DEMO_SERVER_URL", "https://genesis-ai-systems-demo.onrender.com")

    def run(self) -> None:
        leads = self.get_new_leads()
        for lead in leads:
            self.process_lead(lead)
        self.send_pipeline_report()

    def get_new_leads(self) -> list[Lead]:
        """Read recent leads from the demo server or fall back to sample data."""
        try:
            response = requests.get(f"{self.demo_server}/stats/leads", timeout=15)
            items = response.json().get("items", []) if response.ok else []
            leads: list[Lead] = []
            for item in items:
                leads.append(
                    Lead(
                        name=item.get("name", "Unknown"),
                        business=item.get("business", "Unknown Business"),
                        email=item.get("email", ""),
                        phone=item.get("phone", ""),
                        business_type=item.get("business_type", "Other"),
                        pain_point=item.get("pain_point", item.get("message", "")),
                        score=item.get("score", "MEDIUM"),
                    )
                )
            return leads[:5]
        except Exception as error:
            print(f"Lead read failed: {error}")
            return [
                Lead(
                    name="Alicia Monroe",
                    business="Motor City Diner",
                    email="alicia@motorcitydiner.com",
                    phone="(313) 555-0110",
                    business_type="Restaurant",
                    pain_point="We miss dinner calls at night",
                    score="HIGH",
                )
            ]

    def process_lead(self, lead: Lead) -> None:
        """Handle one lead based on how ready they sound."""
        if lead.score == "HIGH":
            self.alert_trendell(lead)
            self.trigger_lindy_sequence(lead, "hot")
        elif lead.score == "MEDIUM":
            self.trigger_lindy_sequence(lead, "warm")
        else:
            self.trigger_lindy_sequence(lead, "cold")
        self.update_hubspot(lead)
        self.mark_contacted(lead)

    def trigger_lindy_sequence(self, lead: Lead, sequence_type: str) -> None:
        """Ask Lindy to handle the follow-up. Fall back to a direct email."""
        key = os.getenv("LINDY_API_KEY")
        if not key:
            print("Lindy not configured — using direct email")
            self.send_direct_email(lead)
            return
        try:
            requests.post(
                "https://api.lindy.ai/v1/sequences/trigger",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "sequence_id": f"genesis_ai_{sequence_type}",
                    "contact": {
                        "email": lead.email,
                        "name": lead.name,
                        "company": lead.business,
                        "custom": {
                            "business_type": lead.business_type,
                            "pain_point": lead.pain_point,
                        },
                    },
                },
                timeout=20,
            )
            print(f"✅ Lindy sequence triggered for {lead.name}")
        except Exception as error:
            print(f"Lindy error: {error} — falling back to direct email")
            self.send_direct_email(lead)

    def send_direct_email(self, lead: Lead) -> None:
        """Fallback email if Lindy is not ready yet."""
        body = self.get_email_body(lead)
        print(f"Direct email ready for {lead.email}:\n{body}\n")

    def get_email_body(self, lead: Lead) -> str:
        """Choose a short email that feels right for that business."""
        templates = {
            "Restaurant": (
                f"Hi {lead.name},\n\n"
                f"I saw your inquiry about {lead.business}.\n\n"
                "I build AI systems that answer calls and book\n"
                "reservations 24/7 for restaurants.\n\n"
                "Worth a 15-minute call?\n\n"
                "Trendell Fordham\n"
                "Genesis AI Systems\n"
                "genesisai.systems"
            ),
            "HVAC": (
                f"Hi {lead.name},\n\n"
                "When someone needs emergency HVAC at 10pm\n"
                "and calls you — who answers?\n\n"
                "I build AI systems that capture every\n"
                "emergency inquiry and text you immediately.\n\n"
                "15-minute call this week?\n\n"
                "Trendell Fordham\n"
                "Genesis AI Systems"
            ),
        }
        return templates.get(
            lead.business_type,
            (
                f"Hi {lead.name},\n\n"
                f"I saw your inquiry about {lead.business}.\n\n"
                "I build done-for-you AI systems for local\n"
                "businesses starting at $500.\n\n"
                "Worth a quick 15-minute call?\n\n"
                "Trendell Fordham\n"
                "Genesis AI Systems\n"
                "genesisai.systems"
            ),
        )

    def alert_trendell(self, lead: Lead) -> None:
        """Text Trendell when a lead sounds ready now."""
        try:
            from twilio.rest import Client

            Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN"),
            ).messages.create(
                body=(
                    "🔥 HOT Lead Alert\n"
                    "Genesis AI Systems\n"
                    f"Name: {lead.name}\n"
                    f"Business: {lead.business}\n"
                    f"Phone: {lead.phone}\n"
                    f"Need: {lead.pain_point}\n"
                    "Call them NOW!"
                ),
                from_=os.getenv("TWILIO_FROM_NUMBER"),
                to=os.getenv("ALERT_PHONE_NUMBER"),
            )
        except Exception as error:
            print(f"HOT lead SMS failed: {error}")

    def update_hubspot(self, lead: Lead) -> None:
        """Print what would be sent to HubSpot."""
        print(f"HubSpot update ready for {lead.name} ({lead.score})")

    def mark_contacted(self, lead: Lead) -> None:
        """Print a marker so the lead is not contacted twice."""
        print(f"Lead marked contacted: {lead.email}")

    def send_pipeline_report(self) -> None:
        """Print a simple pipeline report."""
        print("✅ Weekly pipeline report ready")


if __name__ == "__main__":
    SalesAgent().run()
