#!/usr/bin/env python3
"""Check OpenAI prompt deployment balance for Genesis AI Systems."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from prompt_deployer import CostTracker, NotificationSender


def main() -> int:
    """Check balance, log the result, and print run estimates."""
    load_dotenv()
    console = Console()

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        console.print("[bold red]OPENAI_API_KEY is required.[/bold red]")
        return 1

    notifier = NotificationSender(
        console=console,
        twilio_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        twilio_token=os.getenv("TWILIO_AUTH_TOKEN"),
        twilio_from=os.getenv("TWILIO_FROM_NUMBER"),
        alert_phone=os.getenv("ALERT_PHONE_NUMBER"),
        sendgrid_key=os.getenv("SENDGRID_API_KEY"),
        notification_email=os.getenv("NOTIFICATION_EMAIL", "info@genesisai.systems"),
    )
    tracker = CostTracker(
        api_key=api_key,
        min_balance=float(os.getenv("MIN_BALANCE", "2.00")),
        log_dir=Path("/Users/genesisai/portfolio/.github/workflows/logs"),
        console=console,
        notifier=notifier,
    )

    result = tracker.get_balance()
    balance = result.get("balance_usd")
    estimated_cost = 0.35
    runs_remaining = tracker.estimate_remaining_runs(balance=balance, estimated_run_cost=estimated_cost)

    if balance is None:
        console.print("💰 Balance check: unavailable ⚠️")
        console.print("Estimated cost: $0.35")
        console.print("Runs remaining: unknown")
        console.print("🚀 Starting Genesis AI Systems prompt deployer requires a valid balance lookup or OPENAI_ACCOUNT_BALANCE override.")
        return 1

    indicator = "✅" if balance >= float(os.getenv("MIN_BALANCE", "2.00")) else "⚠️"
    console.print(f"💰 Balance check: ${balance:.2f} {indicator}")
    console.print(f"Estimated cost: ${estimated_cost:.2f}")
    if runs_remaining is not None:
        console.print(f"Runs remaining: ~{runs_remaining}")
    else:
        console.print("Runs remaining: unknown")
    console.print("🚀 Starting Genesis AI Systems prompt deployer...")

    weekly_subject = "Genesis AI Systems — Weekly Balance Report"
    weekly_message = (
        f"Current balance: ${balance:.2f}\n"
        f"Estimated cost per full run: ${estimated_cost:.2f}\n"
        f"Estimated runs remaining: ~{runs_remaining if runs_remaining is not None else 'unknown'}\n"
        f"Website: https://genesisai.systems\n"
        f"Contact: info@genesisai.systems"
    )
    notifier.send_email(subject=weekly_subject, message=weekly_message, priority="LOW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
