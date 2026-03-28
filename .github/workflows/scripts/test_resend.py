#!/usr/bin/env python3
"""Send a Resend test email for Genesis AI Systems."""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from notify import EmailNotifier, NotificationPriority


def main() -> int:
    """Send a single Resend verification email and print the result."""
    load_dotenv()
    notifier = EmailNotifier()
    ok = notifier.send(
        subject="✅ Genesis AI Systems — Resend Test",
        message=(
            "Resend email is working correctly.\n"
            "Genesis AI Systems notifications are active.\n"
            "genesisai.systems"
        ),
        priority=NotificationPriority.INFO,
        to_email="info@genesisai.systems",
    )
    if ok:
        print("✅ Email sent successfully")
        return 0

    print("❌ Email failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
