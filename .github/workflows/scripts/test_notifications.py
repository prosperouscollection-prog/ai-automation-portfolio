# Genesis AI Systems — Notification Test Script
# ---------------------------------------------------------
# Author: Trendell Fordham
# https://genesisai.systems | info@genesisai.systems | (313) 400-2575
"""
Test notification script that sends SMS, email, and Slack agent verification messages using the SOLID notification module.
Usage:
    python test_notifications.py
"""

import os
import sys
from dotenv import load_dotenv
from notify import NotificationOrchestrator, PriorityEnum


def print_colored(message: str, status: str = "success"):
    """
    Prints colored status messages to terminal.
    """
    if status == "success":
        print(f"\033[92m{message}\033[0m")  # Green
    else:
        print(f"\033[91m{message}\033[0m")  # Red


def main():
    """
    Executes test notifications for SMS, email, and Slack if available.
    """
    load_dotenv()
    
    results = {
        'sms': False,
        'email': False,
        'slack': None  # None means not attempted (missing secret)
    }
    
    orchestrator = NotificationOrchestrator()

    # SMS Test
    sms_message = (
        "\u2705 Genesis AI Systems\n"
        "Test notification successful!\n"
        "Your agent monitoring is active.\n"
        "- Trendell Fordham\n  genesisai.systems"
    )
    try:
        orchestrator.send_sms_only(
            subject="Genesis AI Systems Test SMS",
            message=sms_message,
            priority=PriorityEnum.CRITICAL  # Forces SMS channel
        )
        results['sms'] = True
        print_colored("[PASS] SMS delivered to (313) 400-2575.")
    except Exception as e:
        results['sms'] = False
        print_colored(f"[FAIL] SMS delivery failed: {e}", status="fail")

    # Email Test
    email_subject = "\u2705 Genesis AI Systems d Notification Test"
    email_body = (
        "This is a test from Genesis AI Systems agent monitoring system.\n\n"
        "If you received this, notifications work.\n\n"
        "Monitoring: https://genesisai.systems\n\n"
        "Trendell Fordham\n"
        "Founder, Genesis AI Systems\n"
        "info@genesisai.systems\n"
        "(313) 400-2575"
    )
    try:
        orchestrator.send_email_only(
            subject=email_subject,
            message=email_body,
            priority=PriorityEnum.CRITICAL
        )
        results['email'] = True
        print_colored("[PASS] Email delivered to info@genesisai.systems.")
    except Exception as e:
        results['email'] = False
        print_colored(f"[FAIL] Email delivery failed: {e}", status="fail")
        
    # Slack Test (optional)
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    if slack_webhook:
        slack_message = (
            "*\u2705 Genesis AI Systems*\n"
            "Test notification successful!\n"
            "Agent monitoring is active :rocket:"
        )
        try:
            orchestrator.send_slack_only(
                subject="Genesis AI Systems: Notification Test",
                message=slack_message,
                priority=PriorityEnum.INFO
            )
            results['slack'] = True
            print_colored("[PASS] Slack notification delivered.")
        except Exception as e:
            results['slack'] = False
            print_colored(f"[FAIL] Slack delivery failed: {e}", status="fail")
    else:
        results['slack'] = None
        print("[SKIP] Slack Webhook not set; skipping Slack notification test.")

    print("\n----------------------------------------")
    print("Genesis AI Systems — Notification Test Report")
    print("----------------------------------------")
    print(f"SMS : {'PASS' if results['sms'] else 'FAIL'}")
    print(f"Email : {'PASS' if results['email'] else 'FAIL'}")
    print(f"Slack : {'PASS' if results['slack'] else 'SKIP' if results['slack'] is None else 'FAIL'}")
    print("----------------------------------------")
    all_pass = all(res is True or res is None for res in results.values())
    if all_pass:
        print_colored("All enabled notification channels operational! [MONITORING ACTIVE]")
        sys.exit(0)
    else:
        print_colored("Some notification channels failed. Please check setup.", status="fail")
        sys.exit(1)

if __name__ == "__main__":
    main()
