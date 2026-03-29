#!/usr/bin/env python3
"""Genesis AI Systems notification module with Resend email delivery."""

from __future__ import annotations

import argparse
import datetime as dt
import enum
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from html import escape
from pathlib import Path
from typing import Any, Optional

try:
    import resend
except ImportError:  # pragma: no cover - runtime dependency
    resend = None

try:
    import requests
except ImportError:  # pragma: no cover - runtime dependency
    requests = None

try:
    from twilio.rest import Client as TwilioClient
except ImportError:  # pragma: no cover - runtime dependency
    TwilioClient = None


BRAND_NAME = "Genesis AI Systems"
BRAND_WEBSITE = "https://genesisai.systems"
BRAND_EMAIL = "info@genesisai.systems"
BRAND_PHONE = "(313) 400-2575"
BRAND_PHONE_INTL = "+13134002575"
FOUNDER = "Trendell Fordham"
NAVY = "#0f172a"
ELECTRIC_BLUE = "#2563eb"
REPO_SLUG = "prosperouscollection-prog/ai-automation-portfolio"
ACTIONS_URL = f"https://github.com/{REPO_SLUG}/actions"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class NotificationPriority(enum.Enum):
    """Priority levels supported by the Genesis AI notification system."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


PriorityEnum = NotificationPriority


class BaseNotifier(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    def send(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        **kwargs: Any,
    ) -> bool:
        """Send a notification through this channel."""

    @staticmethod
    def normalize_priority(priority: NotificationPriority | str) -> NotificationPriority:
        """Convert a string or enum into a NotificationPriority."""
        if isinstance(priority, NotificationPriority):
            return priority
        try:
            return NotificationPriority[str(priority).upper()]
        except KeyError as exc:
            raise ValueError(f"Unsupported priority: {priority}") from exc

    @staticmethod
    def now() -> str:
        """Return the current local timestamp string."""
        return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def power_footer() -> dict[str, str]:
        """Return the standard Genesis AI Systems response footer."""
        return {
            "powered_by": BRAND_NAME,
            "website": BRAND_WEBSITE,
            "contact": BRAND_EMAIL,
        }


class EmailNotifier(BaseNotifier):
    """Notifier for sending branded emails with Resend."""

    COLOR_MAP = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MEDIUM": "#2563eb",
        "LOW": "#22c55e",
        "INFO": "#94a3b8",
    }

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the Resend client configuration."""
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        self.to_email = os.getenv("NOTIFICATION_EMAIL", BRAND_EMAIL)
        if self.api_key and resend is not None:
            resend.api_key = self.api_key
        elif not self.api_key:
            logger.warning("RESEND_API_KEY is missing. Email notifications will be skipped.")
        elif resend is None:
            logger.warning("resend package is missing. Email notifications will be skipped.")

    def send(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        to_email: Optional[str] = None,
        **_: Any,
    ) -> bool:
        """Send an HTML email using Resend."""
        if not self.api_key or resend is None:
            logger.error("Resend is not configured. Email was not sent.")
            return False

        normalized = self.normalize_priority(priority)
        recipient = to_email or self.to_email

        try:
            params = {
                "from": "Genesis AI Systems <info@genesisai.systems>",
                "to": [recipient],
                "subject": subject,
                "html": self._build_html(message, normalized.value),
            }
            resend.Emails.send(params)
            logger.info("Resend email sent to %s [%s]: %s", recipient, normalized.value, subject)
            return True
        except Exception as exc:  # pragma: no cover - external network
            logger.error("Email failed: %s", exc)
            return False

    def _build_html(self, message: str, priority: str) -> str:
        """Build the branded HTML email body for Resend."""
        color = self.COLOR_MAP.get(priority, ELECTRIC_BLUE)
        safe_message = escape(message)
        return f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #0f172a; padding: 24px; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 20px;">
                    Genesis AI Systems
                </h1>
                <p style="color: #94a3b8; margin: 4px 0 0;">
                    genesisai.systems
                </p>
            </div>
            <div style="background: #f8fafc; padding: 24px; border-left: 4px solid {color};">
                <div style="background: {color}; color: white; padding: 4px 12px; border-radius: 4px; display: inline-block; font-size: 12px; font-weight: bold; margin-bottom: 16px;">
                    {priority}
                </div>
                <div style="color: #1e293b; line-height: 1.6; white-space: pre-wrap;">
                    {safe_message}
                </div>
            </div>
            <div style="background: #0f172a; padding: 16px 24px; border-radius: 0 0 8px 8px; text-align: center;">
                <p style="color: #475569; font-size: 12px; margin: 0;">
                    Trendell Fordham | Genesis AI Systems<br>
                    info@genesisai.systems |
                    (313) 400-2575 | genesisai.systems
                </p>
            </div>
        </div>
        """


class SMSNotifier(BaseNotifier):
    """Notifier for sending SMS alerts via Twilio."""

    def __init__(self) -> None:
        """Load Twilio settings and create the client when possible."""
        self.to_number = os.getenv("ALERT_PHONE_NUMBER")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.client = None
        if TwilioClient is None:
            logger.warning("twilio package missing. SMS notifications will be skipped.")
            return
        try:
            self.client = TwilioClient(
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN"),
            )
        except Exception as exc:
            logger.warning("Twilio credentials missing or invalid. SMS skipped: %s", exc)

    def send(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        **_: Any,
    ) -> bool:
        """Send an SMS message via Twilio."""
        if self.client is None or not self.from_number or not self.to_number:
            logger.error("Twilio is not configured. SMS was not sent.")
            return False

        normalized = self.normalize_priority(priority)
        body = (
            f"Genesis AI Systems\n"
            f"{'=' * 20}\n"
            f"{normalized.value}: {subject}\n"
            f"{'-' * 20}\n"
            f"{str(message)[:140]}\n"
            f"genesisai.systems"
        )
        try:
            msg = self.client.messages.create(
                body=body,
                from_=self.from_number,
                to=self.to_number,
            )
            logger.info("SMS sent: %s", msg.sid)
            return True
        except Exception as exc:
            logger.error("SMS failed: %s", exc)
            return False


class SlackNotifier(BaseNotifier):
    """Notifier for sending Slack webhook alerts."""

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        """Initialize the Slack webhook."""
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL missing. Slack notifications will be skipped.")
        if requests is None:
            logger.warning("requests package missing. Slack notifications will be skipped.")

    def send(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        **_: Any,
    ) -> bool:
        """Send a Slack webhook notification."""
        if not self.webhook_url or requests is None:
            logger.error("Slack is not configured. Message was not sent.")
            return False

        normalized = self.normalize_priority(priority)
        payload = {
            "text": f"*{subject}*\nPriority: {normalized.value}\n{message}",
            **self.power_footer(),
        }
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Slack notification sent [%s]: %s", normalized.value, subject)
            return True
        except Exception as exc:  # pragma: no cover - external network
            logger.error("Slack notification failed: %s", exc)
            return False


class GitHubNotifier(BaseNotifier):
    """Notifier for creating GitHub issues as alerts."""

    def __init__(self, repo: Optional[str] = None, token: Optional[str] = None) -> None:
        """Initialize the GitHub notifier."""
        self.repo = repo or os.getenv("GITHUB_REPOSITORY", REPO_SLUG)
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.warning("GITHUB_TOKEN missing. GitHub issue alerts will be skipped.")
        if requests is None:
            logger.warning("requests package missing. GitHub issue alerts will be skipped.")

    def send(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        **_: Any,
    ) -> bool:
        """Create a GitHub issue for an alert."""
        if not self.token or requests is None:
            logger.error("GitHub notifications are not configured.")
            return False

        normalized = self.normalize_priority(priority)
        payload = {
            "title": f"[{normalized.value}] {subject}",
            "body": f"{message}\n\nPowered by Genesis AI Systems\n{BRAND_WEBSITE}",
            "labels": ["alert", normalized.value.lower()],
        }
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
        try:
            response = requests.post(
                f"https://api.github.com/repos/{self.repo}/issues",
                headers=headers,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            logger.info("GitHub issue created [%s]: %s", normalized.value, subject)
            return True
        except Exception as exc:  # pragma: no cover - external network
            logger.error("GitHub notification failed: %s", exc)
            return False


class NotificationOrchestrator:
    """Route notifications to the right channels based on severity."""

    def __init__(
        self,
        email_notifier: Optional[EmailNotifier] = None,
        sms_notifier: Optional[SMSNotifier] = None,
        slack_notifier: Optional[SlackNotifier] = None,
        github_notifier: Optional[GitHubNotifier] = None,
    ) -> None:
        """Initialize all supported notification channels."""
        self.email_notifier = email_notifier or EmailNotifier()
        self.sms_notifier = sms_notifier or SMSNotifier()
        self.slack_notifier = slack_notifier or SlackNotifier()
        self.github_notifier = github_notifier or GitHubNotifier()

    def notify(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        **kwargs: Any,
    ) -> dict[str, bool]:
        """Dispatch a notification based on its priority."""
        normalized = BaseNotifier.normalize_priority(priority)
        sent: dict[str, bool] = {}
        if normalized == NotificationPriority.CRITICAL:
            sent["email"] = self.email_notifier.send(subject, message, normalized, **kwargs)
            sent["sms"] = self.sms_notifier.send(subject, message, normalized, **kwargs)
            sent["slack"] = self.slack_notifier.send(subject, message, normalized, **kwargs)
            sent["github"] = self.github_notifier.send(subject, message, normalized, **kwargs)
        elif normalized == NotificationPriority.HIGH:
            sent["email"] = self.email_notifier.send(subject, message, normalized, **kwargs)
            sent["sms"] = self.sms_notifier.send(subject, message, normalized, **kwargs)
        elif normalized == NotificationPriority.MEDIUM:
            sent["email"] = self.email_notifier.send(subject, message, normalized, **kwargs)
        elif normalized == NotificationPriority.LOW:
            sent["email"] = self.email_notifier.send(subject, message, normalized, **kwargs)
        else:
            sent["email"] = self.email_notifier.send(subject, message, normalized, **kwargs)
        return sent

    def send_email_only(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        **kwargs: Any,
    ) -> bool:
        """Send an email without touching other channels."""
        return self.email_notifier.send(subject, message, priority, **kwargs)

    def send_sms_only(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        **kwargs: Any,
    ) -> bool:
        """Send an SMS without touching other channels."""
        return self.sms_notifier.send(subject, message, priority, **kwargs)

    def send_slack_only(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        **kwargs: Any,
    ) -> bool:
        """Send a Slack message without touching other channels."""
        return self.slack_notifier.send(subject, message, priority, **kwargs)

    def send_github_only(
        self,
        subject: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        **kwargs: Any,
    ) -> bool:
        """Create a GitHub issue without touching other channels."""
        return self.github_notifier.send(subject, message, priority, **kwargs)

    def send_daily_digest(self, message: str, to_email: Optional[str] = None) -> bool:
        """Send a daily digest email immediately."""
        subject = f"Genesis AI Systems — Daily Health {dt.date.today().isoformat()}"
        return self.email_notifier.send(subject, message, NotificationPriority.LOW, to_email=to_email)

    def send_weekly_report(self, message: str, to_email: Optional[str] = None) -> bool:
        """Send a weekly report email immediately."""
        today = dt.date.today()
        week_start = today - dt.timedelta(days=today.weekday())
        subject = f"Genesis AI Systems — Weekly Report {week_start} to {today}"
        return self.email_notifier.send(subject, message, NotificationPriority.INFO, to_email=to_email)


def format_sms_failure(agent_name: str, description: str, when: Optional[str] = None) -> str:
    """Format the branded SMS failure body."""
    timestamp = when or BaseNotifier.now()
    return (
        "🚨 Genesis AI Systems Alert\n"
        f"Agent: {agent_name}\n"
        "Status: FAILED\n"
        f"Issue: {description}\n"
        f"Time: {timestamp}\n"
        f"Fix: {ACTIONS_URL}"
    )


def format_sms_recovery(agent_name: str, when: Optional[str] = None) -> str:
    """Format the branded SMS recovery body."""
    timestamp = when or BaseNotifier.now()
    return (
        "✅ Genesis AI Systems\n"
        f"Agent: {agent_name}\n"
        "Status: RECOVERED\n"
        "All systems operational\n"
        f"Time: {timestamp}"
    )


def load_json_report(report_path: str) -> dict[str, Any]:
    """Load a JSON report file if it exists."""
    path = Path(report_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("Could not parse report %s: %s", report_path, exc)
        return {}


def derive_priority_from_report(report: dict[str, Any]) -> NotificationPriority:
    """Infer the highest priority contained in a report object."""
    serialized = json.dumps(report).upper()
    if "CRITICAL" in serialized:
        return NotificationPriority.CRITICAL
    if "HIGH" in serialized or '"FAILED"' in serialized:
        return NotificationPriority.HIGH
    if "MEDIUM" in serialized:
        return NotificationPriority.MEDIUM
    if "LOW" in serialized or "WARNING" in serialized:
        return NotificationPriority.LOW
    return NotificationPriority.INFO


def build_report_message(agent: str, report: dict[str, Any], fallback: str) -> str:
    """Build a concise plain-text message from a report."""
    if not report:
        return fallback

    summary = report.get("summary") or report.get("message") or fallback
    findings = report.get("findings") or report.get("issues") or []
    lines = [f"Agent: {agent}", f"Summary: {summary}"]
    if isinstance(findings, list) and findings:
        lines.append("Key findings:")
        for finding in findings[:5]:
            if isinstance(finding, dict):
                label = finding.get("title") or finding.get("name") or finding.get("message") or str(finding)
            else:
                label = str(finding)
            lines.append(f"- {label}")
    lines.append(f"Website: {BRAND_WEBSITE}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for local tests and workflow usage."""
    parser = argparse.ArgumentParser(description="Genesis AI Systems notification utility")
    parser.add_argument("--subject", default=None, help="Notification subject")
    parser.add_argument("--message", default=None, help="Notification body")
    parser.add_argument("--priority", default="MEDIUM", help="Priority level")
    parser.add_argument("--agent", default=None, help="Agent name")
    parser.add_argument("--status", default=None, help="Agent status")
    parser.add_argument("--desc", default=None, help="Description text")
    parser.add_argument("--report", default=None, help="Report type (daily/weekly) or JSON report path")
    parser.add_argument("--qa-report", default=None, help="QA report path for deploy notifications")
    parser.add_argument("--notify-deploy", action="store_true", help="Send post-deploy notifications")
    parser.add_argument("--on-critical-fail", default="false", help="Send CRITICAL alerts when report is critical")
    parser.add_argument("--on-high-email", default="false", help="Send HIGH email alerts when report is high")
    parser.add_argument("--on-warning-log", default="false", help="Log LOW/MEDIUM report warnings without failing")
    parser.add_argument("--test-sms", action="store_true", help="Test SMS notification")
    parser.add_argument("--test-email", action="store_true", help="Test email notification")
    parser.add_argument("--test-slack", action="store_true", help="Test Slack notification")
    parser.add_argument("--test-all", action="store_true", help="Test all notification channels")
    parser.add_argument("--to-email", default=None, help="Override destination email")
    parser.add_argument("--to-number", default=None, help="Override destination phone")
    return parser.parse_args()


def bool_arg(value: str) -> bool:
    """Parse a workflow-style boolean string."""
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def handle_tests(args: argparse.Namespace, orchestrator: NotificationOrchestrator) -> int:
    """Run requested test notifications."""
    ran_any = False
    results: list[bool] = []

    if args.test_sms or args.test_all:
        ran_any = True
        message = (
            "✅ Genesis AI Systems\n"
            "Test notification successful!\n"
            "Your agent monitoring is active.\n"
            "- Trendell Fordham\n"
            "  genesisai.systems"
        )
        ok = orchestrator.send_sms_only(
            subject="Genesis AI Systems Test SMS",
            message=message,
            priority=NotificationPriority.INFO,
            to_number=args.to_number,
        )
        print("Test SMS:", "PASS" if ok else "FAIL")
        results.append(ok)

    if args.test_email or args.test_all:
        ran_any = True
        message = (
            "This is a test from Genesis AI Systems agent monitoring system.\n\n"
            "If you received this, notifications work.\n\n"
            f"Monitoring: {BRAND_WEBSITE}\n\n"
            "Trendell Fordham\n"
            "Founder, Genesis AI Systems\n"
            "info@genesisai.systems\n"
            "(313) 400-2575"
        )
        ok = orchestrator.send_email_only(
            subject="✅ Genesis AI Systems — Notification Test",
            message=message,
            priority=NotificationPriority.INFO,
            to_email=args.to_email,
        )
        print("Test Email:", "PASS" if ok else "FAIL")
        results.append(ok)

    if args.test_slack or args.test_all:
        ran_any = True
        ok = orchestrator.send_slack_only(
            subject="Genesis AI Systems — Notification Test",
            message="✅ Genesis AI Systems\nTest notification successful from agent monitoring system.",
            priority=NotificationPriority.INFO,
        )
        print("Test Slack:", "PASS" if ok else "FAIL")
        results.append(ok)

    if not ran_any:
        return -1
    return 0 if all(results) else 1


def handle_report_mode(args: argparse.Namespace, orchestrator: NotificationOrchestrator) -> int:
    """Handle daily, weekly, or JSON report notifications."""
    if args.report == "daily":
        message = args.desc or "Genesis AI Systems — Daily Health Digest"
        return 0 if orchestrator.send_daily_digest(message) else 1

    if args.report == "weekly":
        message = args.desc or "Genesis AI Systems — Weekly Report"
        return 0 if orchestrator.send_weekly_report(message) else 1

    report = load_json_report(args.report)
    priority = derive_priority_from_report(report)
    agent_name = args.agent or "Genesis AI Systems Agent"
    message = build_report_message(
        agent=agent_name,
        report=report,
        fallback=args.desc or f"{agent_name} report requires review.",
    )

    if priority == NotificationPriority.CRITICAL and bool_arg(args.on_critical_fail):
        results = orchestrator.notify(
            subject=f"{agent_name} report requires immediate attention",
            message=message,
            priority=NotificationPriority.CRITICAL,
        )
        return 0 if any(results.values()) else 1

    if priority == NotificationPriority.HIGH and bool_arg(args.on_high_email):
        ok = orchestrator.send_email_only(
            subject=f"{agent_name} high-priority report",
            message=message,
            priority=NotificationPriority.HIGH,
        )
        return 0 if ok else 1

    if bool_arg(args.on_warning_log):
        logger.warning("%s", message)
        return 0

    ok = orchestrator.send_email_only(
        subject=f"{agent_name} report",
        message=message,
        priority=priority,
    )
    return 0 if ok else 1


def handle_deploy_mode(args: argparse.Namespace, orchestrator: NotificationOrchestrator) -> int:
    """Handle post-deployment notifications."""
    report = load_json_report(args.qa_report) if args.qa_report else {}
    priority = derive_priority_from_report(report) if report else NotificationPriority.INFO
    summary = build_report_message(
        agent="Deploy Agent",
        report=report,
        fallback="Deployment completed. Review post-deploy QA report for details.",
    )
    results = orchestrator.notify(
        subject="Genesis AI Systems deployment update",
        message=summary,
        priority=priority,
    )
    return 0 if any(results.values()) else 1


def handle_direct_mode(args: argparse.Namespace, orchestrator: NotificationOrchestrator) -> int:
    """Handle direct subject/message or agent/status alerts."""
    priority = BaseNotifier.normalize_priority(args.priority)

    if args.subject and args.message:
        results = orchestrator.notify(args.subject, args.message, priority, to_email=args.to_email)
        return 0 if any(results.values()) else 1

    if args.agent and args.status:
        subject = f"{args.agent}: {args.status}"
        description = args.desc or "No additional details provided."
        message = (
            f"Agent: {args.agent}\n"
            f"Status: {args.status}\n"
            f"Detail: {description}\n"
            f"Time: {BaseNotifier.now()}\n"
            f"Fix: {ACTIONS_URL}"
        )
        results = orchestrator.notify(subject, message, priority)
        return 0 if any(results.values()) else 1

    return -1


def main() -> int:
    """Entry point for workflow and local CLI notification handling."""
    args = parse_args()
    orchestrator = NotificationOrchestrator()

    for handler in (
        lambda: handle_tests(args, orchestrator),
        lambda: handle_deploy_mode(args, orchestrator) if args.notify_deploy else -1,
        lambda: handle_report_mode(args, orchestrator) if args.report else -1,
        lambda: handle_direct_mode(args, orchestrator),
    ):
        result = handler()
        if result != -1:
            return result

    print("No action requested. Use --help for options.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
