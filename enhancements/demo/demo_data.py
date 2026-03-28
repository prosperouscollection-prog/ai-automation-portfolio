"""Sample data for the Genesis AI Systems enhancement demo harness.

This module provides stable, portfolio-safe demo data so the enhancement
stack can be shown without live vendor credentials or production client
records. The values are intentionally realistic for a local service business
and are fixed to a known demo window for repeatable output.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone


DEMO_NOW = datetime(2026, 3, 28, 16, 30, tzinfo=timezone.utc)


def build_sample_leads() -> list[dict[str, str]]:
    """Return a deterministic month of Smile Dental lead activity."""
    patterns = [
        (
            "I have a toothache and need to come in today if possible.",
            "We can help with that. Our team can prioritize same-day emergency visits when availability opens up.",
            "HIGH",
            0,
            8,
        ),
        (
            "Do you accept Delta Dental for Invisalign consults?",
            "Yes, we can review Delta Dental benefits during your Invisalign consultation and explain your options clearly.",
            "HIGH",
            0,
            13,
        ),
        (
            "How much is a cleaning without insurance?",
            "Our team can quote current self-pay pricing and help you schedule a cleaning at the location closest to you.",
            "MEDIUM",
            1,
            10,
        ),
        (
            "Can I book whitening for next Friday afternoon?",
            "Absolutely. We can help you find a whitening appointment that fits your Friday schedule.",
            "MEDIUM",
            1,
            15,
        ),
        (
            "Do you see kids for first dental visits?",
            "Yes, we welcome pediatric patients and can help you choose the best first-visit time for your child.",
            "HIGH",
            2,
            9,
        ),
        (
            "What time do you open on Saturdays?",
            "Saturday availability can vary by location, and we can confirm the soonest opening for you right away.",
            "LOW",
            2,
            12,
        ),
        (
            "I chipped a crown and want to know if you take emergencies.",
            "Yes, emergency dental concerns like chipped crowns can be prioritized. We can collect a few details and get you routed correctly.",
            "HIGH",
            3,
            11,
        ),
        (
            "Can someone call me back about implants?",
            "Absolutely. We can have the office follow up with implant information and next-step scheduling options.",
            "MEDIUM",
            3,
            16,
        ),
        (
            "Do you offer payment plans for braces?",
            "Yes, we can review financing and payment plan options for orthodontic treatment.",
            "MEDIUM",
            4,
            14,
        ),
        (
            "Need to reschedule my hygiene appointment.",
            "No problem. We can help you move your hygiene visit to a better time.",
            "LOW",
            4,
            17,
        ),
        (
            "Is Invisalign better than braces for adults?",
            "For many adults Invisalign is a great option, and our doctor can recommend the right plan after an evaluation.",
            "HIGH",
            5,
            9,
        ),
        (
            "Do you take Cigna insurance?",
            "We can verify Cigna benefits before your visit and explain what is typically covered.",
            "MEDIUM",
            5,
            13,
        ),
        (
            "I want veneers before my wedding in June.",
            "That is a great timeline to discuss. We can schedule a cosmetic consult and map out the best veneer plan.",
            "HIGH",
            6,
            10,
        ),
        (
            "What is your address in Southfield?",
            "We can send you the Southfield office address, parking details, and directions.",
            "LOW",
            6,
            15,
        ),
    ]

    leads: list[dict[str, str]] = []
    for index in range(42):
        message, response, score, day_offset, hour = patterns[index % len(patterns)]
        timestamp = DEMO_NOW - timedelta(days=day_offset + (index // len(patterns)) * 7)
        timestamp = timestamp.replace(hour=hour, minute=(index * 7) % 60, second=0, microsecond=0)
        leads.append(
            {
                "timestamp": timestamp.isoformat(),
                "message": message,
                "response": response,
                "score": score,
            }
        )
    leads.sort(key=lambda item: item["timestamp"])
    return leads


def build_sample_uptime_snapshots() -> list[dict[str, object]]:
    """Return deterministic uptime snapshots for three demo clients."""
    return [
        {
            "client_id": "smile-dental",
            "client_name": "Smile Dental",
            "checked_at": DEMO_NOW.isoformat(),
            "checks": [
                {"check_name": "webhook", "healthy": True, "details": "Lead webhook responded in 214ms."},
                {"check_name": "google_sheets", "healthy": True, "details": "Workbook opened successfully."},
                {"check_name": "openai", "healthy": True, "details": "OpenAI status indicator: none"},
                {"check_name": "vapi", "healthy": True, "details": "Vapi status HTTP 200"},
            ],
        },
        {
            "client_id": "bright-smiles-ortho",
            "client_name": "Bright Smiles Ortho",
            "checked_at": DEMO_NOW.isoformat(),
            "checks": [
                {"check_name": "webhook", "healthy": False, "details": "Webhook timeout after 10s on /lead-intake."},
                {"check_name": "google_sheets", "healthy": True, "details": "Workbook opened successfully."},
                {"check_name": "openai", "healthy": True, "details": "OpenAI status indicator: none"},
                {"check_name": "vapi", "healthy": True, "details": "Vapi status HTTP 200"},
            ],
        },
        {
            "client_id": "southfield-family-dental",
            "client_name": "Southfield Family Dental",
            "checked_at": DEMO_NOW.isoformat(),
            "checks": [
                {"check_name": "webhook", "healthy": True, "details": "Lead webhook responded in 301ms."},
                {"check_name": "google_sheets", "healthy": True, "details": "Workbook opened successfully."},
                {"check_name": "openai", "healthy": True, "details": "OpenAI status indicator: none"},
                {"check_name": "vapi", "healthy": False, "details": "Vapi status HTTP 503"},
            ],
        },
    ]


def build_monthly_rollup(leads: list[dict[str, str]]) -> dict[str, object]:
    """Calculate realistic monthly demo metrics from the sample lead set."""
    counts = Counter(lead["score"] for lead in leads)
    keywords = Counter()
    for lead in leads:
        for word in lead["message"].lower().replace("?", "").replace(".", "").split():
            cleaned = word.strip(",!:")
            if cleaned.isalpha() and len(cleaned) >= 5:
                keywords[cleaned] += 1

    total = len(leads)
    high_count = counts.get("HIGH", 0)
    return {
        "total_leads": total,
        "high_count": high_count,
        "medium_count": counts.get("MEDIUM", 0),
        "low_count": counts.get("LOW", 0),
        "ai_responses_sent": total,
        "voice_calls_handled": 29,
        "emails_sent": 37,
        "estimated_time_saved_hours": round((total * 15) / 60.0, 1),
        "estimated_revenue_generated": float(high_count * 450),
        "uptime_percentage": 99.57,
        "top_keywords": [word for word, _ in keywords.most_common(5)],
    }

