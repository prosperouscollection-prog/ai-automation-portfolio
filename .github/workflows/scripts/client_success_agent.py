#!/usr/bin/env python3
"""Client care helper for Genesis AI Systems."""

from __future__ import annotations

import os
from datetime import date, datetime

from dotenv import load_dotenv

load_dotenv()


class ClientSuccessAgent:
    """Send check-ins, ask for reviews, and keep clients feeling looked after."""

    MILESTONES = {
        7: "first_checkin",
        30: "monthly_report",
        60: "testimonial_request",
        90: "referral_request",
    }

    def run(self) -> None:
        clients = self.get_active_clients()
        for client in clients:
            days = self.days_since_start(client)
            for milestone, action in self.MILESTONES.items():
                if days == milestone:
                    getattr(self, action)(client)
        self.send_weekly_report()

    def get_active_clients(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Alicia Monroe",
                "business": "Motor City Diner",
                "email": "alicia@motorcitydiner.com",
                "start_date": (date.today()).isoformat(),
            },
            {
                "name": "Dana Ross",
                "business": "Bright Smile Dental",
                "email": "dana@brightsmile.com",
                "start_date": (date.today().replace(day=max(1, date.today().day - 60))).isoformat(),
            },
        ]

    def days_since_start(self, client: dict[str, str]) -> int:
        started = datetime.fromisoformat(client["start_date"]).date()
        return (date.today() - started).days

    def send_email(self, email: str, subject: str, body: str) -> None:
        print(f"Email ready for {email}\nSubject: {subject}\n{body}\n")

    def first_checkin(self, client: dict[str, str]) -> None:
        subject = f"Quick check-in — {client['business']} AI systems"
        body = (
            f"Hi {client['name']},\n\n"
            f"Checking in on how your AI system is working for {client['business']}.\n\n"
            "This week your system:\n"
            "✅ Handled inquiries automatically\n"
            "✅ Answered customer questions\n"
            "✅ Saved you time every day\n\n"
            "Anything you would like adjusted?\n\n"
            "Trendell Fordham\n"
            "Genesis AI Systems\n"
            "[BUSINESS_PHONE_NUMBER]"
        )
        self.send_email(client["email"], subject, body)

    def monthly_report(self, client: dict[str, str]) -> None:
        self.send_email(
            client["email"],
            f"Your monthly update — {client['business']}",
            "Here is what your system handled this month and what we can improve next.",
        )

    def testimonial_request(self, client: dict[str, str]) -> None:
        subject = "Would you share your experience?"
        body = (
            f"Hi {client['name']},\n\n"
            "You have been with Genesis AI Systems for 2 months now.\n\n"
            "If you have been happy with the results would you be willing to share a quick testimonial?\n\n"
            "It can be as simple as:\n"
            "Genesis AI Systems helped my business do X.\n\n"
            "A Google review or LinkedIn recommendation would mean a lot to us.\n\n"
            "Thank you,\nTrendell"
        )
        self.send_email(client["email"], subject, body)

    def referral_request(self, client: dict[str, str]) -> None:
        subject = "Know anyone who could use this?"
        body = (
            f"Hi {client['name']},\n\n"
            "You have been with us for 3 months.\n\n"
            "If you know any other business owners struggling with missed calls or slow follow-ups I would love an introduction.\n\n"
            "For every client you refer who signs up you get one month completely free.\n\n"
            "Just forward my number:\n"
            "[BUSINESS_PHONE_NUMBER]\n\n"
            "Trendell"
        )
        self.send_email(client["email"], subject, body)

    def send_weekly_report(self) -> None:
        print("✅ Weekly client health report ready")


if __name__ == "__main__":
    ClientSuccessAgent().run()
