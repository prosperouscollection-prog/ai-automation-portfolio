#!/usr/bin/env python3
"""Daily content helper for Genesis AI Systems."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

TOPICS = [
    "missed_calls",
    "before_after",
    "industry_tip",
    "behind_scenes",
    "ai_myth_busted",
    "real_result",
    "plain_english_ai",
]

INDUSTRIES = [
    "restaurant",
    "dental",
    "hvac",
    "salon",
    "real_estate",
    "retail",
]


class MarketingAgent:
    """Make daily content and text Trendell a preview."""

    def __init__(self) -> None:
        self.output_dir = Path.cwd() / "marketing_output"
        self.output_dir.mkdir(exist_ok=True)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def run(self) -> None:
        topic = self.get_todays_topic()
        industry = self.get_todays_industry()
        linkedin = self.generate_linkedin_post(topic)
        instagram = self.generate_instagram_captions(topic)
        outreach = self.generate_outreach_email(industry)
        self.save_to_files(linkedin, instagram, outreach)
        self.notify_trendell(linkedin[:200])
        print("✅ Marketing content generated")

    def get_todays_topic(self) -> str:
        return TOPICS[datetime.utcnow().day % len(TOPICS)]

    def get_todays_industry(self) -> str:
        return INDUSTRIES[datetime.utcnow().day % len(INDUSTRIES)]

    def call_claude(self, prompt: str, fallback: str) -> str:
        """Use Claude when ready. Fall back to a safe draft when not."""
        if not self.api_key:
            return fallback
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 800,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=45,
            )
            if not response.ok:
                return fallback
            data = response.json()
            blocks = data.get("content", [])
            if not blocks:
                return fallback
            return blocks[0].get("text", fallback)
        except Exception as error:
            print(f"Claude error: {error}")
            return fallback

    def generate_linkedin_post(self, topic: str) -> str:
        prompt = f"""
You are writing a LinkedIn post for Trendell Fordham
founder of Genesis AI Systems in Detroit MI.

Topic: {topic}

Rules:
- Write in first person as Trendell
- Plain English
- Hook in first line
- 3-5 short paragraphs
- End with call to action to visit genesisai.systems
- Include these hashtags:
  #AIAutomation #DetroitBusiness #LocalBusiness
  #SmallBusiness #GenesisAISystems
"""
        fallback = (
            "Your restaurant lost 3 customers last night.\n\n"
            "Not because your food was bad.\n"
            "Because nobody answered the phone.\n\n"
            "That is the kind of problem I build around.\n"
            "I help local businesses answer calls, capture leads, and follow up fast.\n\n"
            "See what we are building at genesisai.systems\n\n"
            "#AIAutomation #DetroitBusiness #LocalBusiness #SmallBusiness #GenesisAISystems"
        )
        return self.call_claude(prompt, fallback)

    def generate_instagram_captions(self, topic: str) -> str:
        prompt = f"""
Write 3 Instagram captions for Genesis AI Systems.
Topic: {topic}
Each caption: 2-3 sentences max.
Plain English.
Include call to action: Link in bio → genesisai.systems
"""
        fallback = (
            "CAPTION 1: If your phone keeps ringing after hours, your next customer may be calling your competitor. Link in bio → genesisai.systems\n"
            "CAPTION 2: We help local businesses answer faster and book more. Link in bio → genesisai.systems\n"
            "CAPTION 3: Less missed calls. More booked jobs. Link in bio → genesisai.systems"
        )
        return self.call_claude(prompt, fallback)

    def generate_outreach_email(self, industry: str) -> str:
        templates = {
            "restaurant": (
                "Subject: Quick question about [Restaurant Name]\n\n"
                "Hi [Owner Name],\n\n"
                "Love what you're doing at [Restaurant].\n\n"
                "What happens when someone calls to make a reservation and you're slammed?\n\n"
                "I build AI phone assistants for restaurants that answer calls and book reservations 24/7.\n\n"
                "5-7 days to set up. Starting at $500.\n\n"
                "Worth a 10-minute call?\n\n"
                "Trendell Fordham\nGenesis AI Systems\ngenesisai.systems\n[BUSINESS_PHONE_NUMBER]"
            ),
            "dental": (
                "Subject: Patients calling after you close\n\n"
                "Hi Dr. [Name],\n\n"
                "A patient tried to book an appointment last night at 7pm.\n\n"
                "Nobody answered. They called another dentist.\n\n"
                "I build AI systems that answer after-hours calls and book appointments automatically.\n\n"
                "Trendell Fordham\nGenesis AI Systems\n[BUSINESS_PHONE_NUMBER]"
            ),
            "hvac": (
                "Subject: Emergency calls you are missing at night\n\n"
                "Hi [Name],\n\n"
                "When your HVAC company gets an emergency call at 10pm — who answers?\n\n"
                "I build AI systems that capture every emergency inquiry and text you immediately.\n\n"
                "15-minute call this week?\n\n"
                "Trendell Fordham\nGenesis AI Systems"
            ),
        }
        return templates.get(industry, templates["restaurant"])

    def save_to_files(self, linkedin: str, instagram: str, outreach: str) -> None:
        stamp = datetime.utcnow().strftime("%Y-%m-%d")
        (self.output_dir / f"{stamp}_linkedin.txt").write_text(linkedin)
        (self.output_dir / f"{stamp}_instagram.txt").write_text(instagram)
        (self.output_dir / f"{stamp}_outreach.txt").write_text(outreach)

    def notify_trendell(self, preview: str) -> None:
        # Skip if Twilio not configured
        if not os.getenv("TWILIO_ACCOUNT_SID") or not os.getenv("TWILIO_AUTH_TOKEN"):
            print("⏭️  Twilio not configured — skipping SMS notification")
            return
        
        try:
            from twilio.rest import Client

            Client(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN"),
            ).messages.create(
                body=(
                    "📝 Marketing content ready\n"
                    "Genesis AI Systems\n"
                    f"Today's post preview:\n{preview}...\n"
                    "Full content saved to files"
                ),
                from_=os.getenv("TWILIO_FROM_NUMBER"),
                to=os.getenv("ALERT_PHONE_NUMBER"),
            )
        except Exception as error:
            print(f"⚠️  Notification failed: {error}")


if __name__ == "__main__":
    MarketingAgent().run()
