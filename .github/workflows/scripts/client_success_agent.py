#!/usr/bin/env python3
"""Client care agent — pulls real clients from HubSpot, sends milestone emails via Resend."""

from __future__ import annotations

import os
from datetime import date, datetime

import requests
from dotenv import load_dotenv

load_dotenv()

from notify import telegram_notify, resend_email


class ClientSuccessAgent:
    """Send check-ins, ask for reviews, and keep clients feeling looked after."""

    MILESTONES = {
        7: "first_checkin",
        30: "monthly_report",
        60: "testimonial_request",
        90: "referral_request",
    }

    def __init__(self) -> None:
        self.hubspot_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "").strip()

    def run(self) -> None:
        clients = self.get_active_clients()
        if not clients:
            print("ℹ️  No active clients found in HubSpot")
            return
        actions_taken = 0
        for client in clients:
            days = self.days_since_start(client)
            for milestone, action in self.MILESTONES.items():
                if days == milestone:
                    getattr(self, action)(client)
                    actions_taken += 1
        self.send_weekly_report(clients)
        print(f"✅ Client Success Agent complete — {len(clients)} clients, {actions_taken} actions taken")


    def get_active_clients(self) -> list[dict]:
        """Pull active client companies from HubSpot — filter by lead status WON."""
        if not self.hubspot_token:
            print("⚠️  HUBSPOT_ACCESS_TOKEN missing — cannot pull clients")
            return []
        try:
            resp = requests.post(
                "https://api.hubapi.com/crm/v3/objects/companies/search",
                headers={"Authorization": f"Bearer {self.hubspot_token}", "Content-Type": "application/json"},
                json={
                    "filterGroups": [{"filters": [{"propertyName": "hs_lead_status", "operator": "EQ", "value": "WON"}]}],
                    "properties": ["name", "phone", "hs_email", "createdate", "city", "industry"],
                    "limit": 50,
                },
                timeout=15,
            )
            if not resp.ok:
                print(f"⚠️  HubSpot search {resp.status_code}: {resp.text[:200]}")
                return []
            results = resp.json().get("results", [])
            clients = []
            for r in results:
                props = r.get("properties", {})
                clients.append({
                    "name": props.get("name", "Client"),
                    "email": props.get("hs_email", ""),
                    "phone": props.get("phone", ""),
                    "business": props.get("name", ""),
                    "start_date": (props.get("createdate") or datetime.now().isoformat())[:10],
                    "industry": props.get("industry", ""),
                    "city": props.get("city", "Detroit"),
                })
            print(f"✅ Found {len(clients)} active clients in HubSpot")
            return clients
        except Exception as e:
            print(f"❌ HubSpot client pull error: {e}")
            return []

    def days_since_start(self, client: dict) -> int:
        try:
            started = datetime.fromisoformat(client["start_date"]).date()
            return (date.today() - started).days
        except Exception:
            return 0

    def send_email(self, email: str, subject: str, body: str) -> None:
        """Send via Resend. Skip if no email on file."""
        if not email:
            print(f"ℹ️  No email on file — skipping: {subject}")
            return
        ok = resend_email(email, subject, body, priority="LOW")
        print(f"{'✅' if ok else '⚠️ '} Email {'sent' if ok else 'failed'}: {subject} → {email}")


    def first_checkin(self, client: dict) -> None:
        self.send_email(
            client["email"],
            f"Quick check-in — {client['business']} AI systems",
            f"Hi {client['name']},\n\n"
            f"Checking in on how your AI system is working for {client['business']}.\n\n"
            "This week your system handled inquiries, answered questions, and saved you time every day.\n\n"
            "Anything you would like adjusted?\n\n"
            "Trendell Fordham\nGenesis AI Systems\n(586) 636-9550"
        )

    def monthly_report(self, client: dict) -> None:
        self.send_email(
            client["email"],
            f"Your monthly update — {client['business']}",
            f"Hi {client['name']},\n\n"
            "Here is what your system handled this month and what we can improve next.\n\n"
            "Reply to this email and I will set up a quick call.\n\n"
            "Trendell Fordham\nGenesis AI Systems"
        )

    def testimonial_request(self, client: dict) -> None:
        self.send_email(
            client["email"],
            "Would you share your experience?",
            f"Hi {client['name']},\n\n"
            f"You have been with Genesis AI Systems for 2 months now.\n\n"
            "If you have been happy with the results, would you share a quick testimonial?\n\n"
            "A Google review or LinkedIn recommendation means a lot.\n\n"
            "Thank you,\nTrendell"
        )
        telegram_notify(
            "Testimonial Request Sent",
            f"Sent testimonial request to {client['name']} at {client['business']}",
            "INFO"
        )

    def referral_request(self, client: dict) -> None:
        self.send_email(
            client["email"],
            "Know anyone who could use this?",
            f"Hi {client['name']},\n\n"
            "You have been with us for 3 months.\n\n"
            "If you know any other business owners struggling with missed calls or slow follow-ups, I would love an introduction.\n\n"
            "For every client you refer who signs up, you get one month completely free.\n\n"
            "Just forward my number: (586) 636-9550\n\n"
            "Trendell"
        )

    def send_weekly_report(self, clients: list[dict]) -> None:
        today = date.today().strftime("%B %d, %Y")
        body = (
            f"Client Health — {today}\n\n"
            f"Active clients: {len(clients)}\n\n"
            + "\n".join(f"- {c['name']} ({c['business']})" for c in clients[:10])
            + "\n\ngenesisai.systems"
        )
        trendell_email = os.getenv("NOTIFICATION_EMAIL", "info@genesisai.systems")
        resend_email(trendell_email, f"Client Health Report — {today}", body, "LOW")
        telegram_notify("Client Health Report", f"{len(clients)} active clients tracked.", "INFO")
        print("✅ Weekly client report sent")


if __name__ == "__main__":
    ClientSuccessAgent().run()
