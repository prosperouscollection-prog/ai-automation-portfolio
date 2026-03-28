#!/usr/bin/env python3
"""
Genesis AI Systems — Notifier Module

Provides notification utilities (Email, SMS, Slack, GitHub) for agent alerting,
following SOLID principles and supporting all required notification priorities.

Trendell Fordham, Founder — genesisai.systems
"""
import os
import sys
import enum
import logging
import datetime
import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

# Optional imports
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
except ImportError:
    SendGridAPIClient = None

try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

try:
    import requests
except ImportError:
    requests = None

# Constants (branding)
BRAND_NAME = "Genesis AI Systems"
BRAND_WEBSITE = "https://genesisai.systems"
BRAND_EMAIL = "info@genesisai.systems"
BRAND_PHONE = "(313) 400-2575"
BRAND_PHONE_INTL = "+13134002575"
NAVY = "#0f172a"
ELECTRIC_BLUE = "#2563eb"
FOUNDER = "Trendell Fordham"
GITHUB_REPO = "prosperouscollection-prog/ai-automation-portfolio"
GITHUB_BASE_URL = f"https://github.com/{GITHUB_REPO}"
ISSUES_URL = f"{GITHUB_BASE_URL}/issues"
ACTIONS_URL = f"{GITHUB_BASE_URL}/actions"

# Logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Priority Enum
class NotificationPriority(enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

# Abstract Base Notifier (SOLID: Single + Open/Closed + Liskov + Interface)
class BaseNotifier(ABC):
    """Abstract base class for all notifiers."""

    @abstractmethod
    def send(self, subject: str, message: str, priority: NotificationPriority, **kwargs) -> bool:
        """Send a notification through the channel."""
        pass

    @staticmethod
    def power_footer() -> Dict[str, str]:
        return {
            "powered_by": BRAND_NAME,
            "website": BRAND_WEBSITE,
            "contact": BRAND_EMAIL
        }

    @staticmethod
    def now() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Email Notifier (SendGrid)
class EmailNotifier(BaseNotifier):
    """Notifier for sending emails using SendGrid."""

    def __init__(self, api_key: Optional[str] = None, from_email: Optional[str] = None, from_name: str = BRAND_NAME):
        self.api_key = api_key or os.environ.get("SENDGRID_API_KEY")
        self.from_email = from_email or os.environ.get("SENDGRID_FROM_EMAIL", BRAND_EMAIL)
        self.from_name = from_name or os.environ.get("SENDGRID_FROM_NAME", BRAND_NAME)

        if not self.api_key:
            logger.warning("SendGrid API key missing. Email notifications will fail.")
        if SendGridAPIClient is None:
            logger.warning("sendgrid package not found. Email notifications will not work.")

    def _render_html(self, subject: str, body: str) -> str:
        """Produce a branded HTML email template."""
        now = self.now()
        template = f'''
        <html>
        <body style="margin:0; font-family:Segoe UI,Arial,sans-serif; background:#f7fafd;">
            <div style="background:{NAVY};padding:32px 8px;">
                <h1 style="color:#fff;margin:0;font-size:2rem;letter-spacing:2px; font-weight:700;">{BRAND_NAME}</h1>
                <p style="color:{ELECTRIC_BLUE};font-size:1rem;margin:0;">Done-for-you AI automation for local businesses</p>
            </div>
            <div style="background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.06);max-width:600px;margin:32px auto;padding:32px 24px 24px;border-top:4px solid {ELECTRIC_BLUE};">
                <h2 style="color:{NAVY};">{subject}</h2>
                <div style="color:#1e293b; font-size:1.05rem; line-height:1.7;">
                    {body}
                </div>
                <div style="margin-top:24px; font-size:0.95rem; color:#64748b;">
                    <hr style="border:none;border-top:1px solid #e2e8f0;"/>
                    <strong style="color:{NAVY};">{BRAND_NAME}</strong> | <a href="mailto:{BRAND_EMAIL}" style="color:{ELECTRIC_BLUE};text-decoration:none;font-weight:500;">{BRAND_EMAIL}</a> | <a href="tel:{BRAND_PHONE_INTL}" style="color:{ELECTRIC_BLUE};text-decoration:none;">{BRAND_PHONE}</a><br/>
                    {now}<br/>
                    <span style="color:#94a3b8;">&copy; 2026 {BRAND_NAME}, Detroit MI</span><br/>
                </div>
            </div>
        </body>
        </html>
        '''
        return template

    def send(self, subject: str, message: str, priority: NotificationPriority, to_email: Optional[str] = None, **kwargs) -> bool:
        """Send an HTML email using SendGrid."""
        if not self.api_key or not SendGridAPIClient:
            logger.error("Missing SendGrid configuration — not sending email.")
            return False
        to_email = to_email or os.environ.get("NOTIFICATION_EMAIL", BRAND_EMAIL)
        html_content = self._render_html(subject, message)
        data_payload = self.power_footer()

        try:
            mail = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=HtmlContent(html_content)
            )
            mail.reply_to = Email(self.from_email, self.from_name)
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(mail)
            logger.info(f"Sent email to {to_email} [{priority.value}]: {subject} (status {response.status_code})")
            return 200 <= response.status_code < 300
        except Exception as e:
            logger.error(f"Failed to send SendGrid email: {e}")
            return False

# SMS Notifier (Twilio)
class SMSNotifier(BaseNotifier):
    """Notifier for sending SMS via Twilio."""
    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None, from_number: Optional[str] = None):
        self.account_sid = account_sid or os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.environ.get("TWILIO_FROM_NUMBER")
        if not self.account_sid or not self.auth_token or not self.from_number:
            logger.warning("Twilio credentials missing. SMS notifications will fail.")
        if TwilioClient is None:
            logger.warning("twilio package not found. SMS notifications will not work.")

    def send(self, subject: str, message: str, priority: NotificationPriority, to_number: Optional[str] = None, **kwargs) -> bool:
        """Send an SMS message via Twilio."""
        if not self.account_sid or not self.auth_token or not self.from_number or TwilioClient is None:
            logger.error("Twilio not configured or twilio package missing, cannot send SMS.")
            return False
        to_number = to_number or os.environ.get("ALERT_PHONE_NUMBER", BRAND_PHONE_INTL)
        sms_body = message
        try:
            client = TwilioClient(self.account_sid, self.auth_token)
            msg = client.messages.create(
                to=to_number,
                from_=self.from_number,
                body=sms_body
            )
            logger.info(f"Sent SMS to {to_number} [{priority.value}] id={msg.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS via Twilio: {e}")
            return False

# Slack Notifier
class SlackNotifier(BaseNotifier):
    """Notifier for sending Slack messages using webhooks."""
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            logger.warning("Slack webhook missing. Slack notifications will fail.")
        if requests is None:
            logger.warning("requests package not found. Slack notifications will not work.")

    def send(self, subject: str, message: str, priority: NotificationPriority, **kwargs) -> bool:
        """Send a message to Slack via webhook."""
        if not self.webhook_url or requests is None:
            logger.error("Missing Slack webhook or requests package. Not sending Slack message.")
            return False
        slack_data = {
            "text": f"*{subject}*\n{message}",
            **self.power_footer()
        }
        try:
            resp = requests.post(self.webhook_url, json=slack_data, timeout=8)
            if resp.status_code == 200:
                logger.info(f"Sent Slack notification [{priority.value}]: {subject}")
                return True
            else:
                logger.error(f"Slack webhook error: HTTP {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False

# GitHub Notifier (Issues)
class GitHubNotifier(BaseNotifier):
    """Notifier for creating GitHub Issues as alerts."""
    def __init__(self, repo: Optional[str] = None, token: Optional[str] = None):
        # Requires repo and personal access token with repo:issues scope
        self.repo = repo or os.environ.get("GITHUB_REPOSITORY", GITHUB_REPO)
        self.token = token or os.environ.get("GITHUB_TOKEN")  # Github Actions auto-provides GITHUB_TOKEN
        if requests is None:
            logger.warning("requests package not found. GitHub notifications will not work.")
        if not self.token:
            logger.warning("GITHUB_TOKEN missing. GitHub issue alerts will fail.")

    def send(self, subject: str, message: str, priority: NotificationPriority, **kwargs) -> bool:
        """Create a GitHub Issue with alert details."""
        if not self.token or requests is None:
            logger.error("Cannot send GitHub issue notification (missing token/requests)."); return False
        url = f"https://api.github.com/repos/{self.repo}/issues"
        issue = {
            "title": f"[{BRAND_NAME}][{priority.value}] {subject}",
            "body": message + ("\n\nPowered by Genesis AI Systems."),
            "labels": ["alert", priority.value.lower(), "autobot"]
        }
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json"
        }
        try:
            resp = requests.post(url, headers=headers, json=issue, timeout=10)
            if resp.status_code in (200, 201):
                logger.info(f"GitHub issue created for [{priority.value}]: {subject}")
                return True
            else:
                logger.error(f"GitHub issue failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.error(f"GitHub Issue notification failed: {e}")
            return False

# Notification Orchestrator (SRP + Dependency Inversion + Open/Closed)
class NotificationOrchestrator:
    """
    Orchestrates notifications between channels based on priority.
    - CRITICAL: all channels
    - HIGH: email + SMS
    - MEDIUM: email
    - LOW: batch for daily digest
    - INFO: batch for weekly report
    """
    def __init__(self,
                 email_notifier: Optional[EmailNotifier] = None,
                 sms_notifier: Optional[SMSNotifier] = None,
                 slack_notifier: Optional[SlackNotifier] = None,
                 github_notifier: Optional[GitHubNotifier] = None):
        self.email_notifier = email_notifier or EmailNotifier()
        self.sms_notifier = sms_notifier or SMSNotifier()
        self.slack_notifier = slack_notifier or SlackNotifier()
        self.github_notifier = github_notifier or GitHubNotifier()
        self.low_priority_queue = []  # (subject, message, priority)
        self.info_queue = []

    def notify(self, subject: str, message: str, priority: NotificationPriority, **kwargs):
        """
        Notify all channels based on priority.
        """
        # All messages are HTML-safe for email, plain text for others
        sent = dict()
        if priority == NotificationPriority.CRITICAL:
            sent['email'] = self.email_notifier.send(subject, message, priority, **kwargs)
            sent['sms'] = self.sms_notifier.send(subject, message, priority, **kwargs)
            sent['slack'] = self.slack_notifier.send(subject, message, priority, **kwargs)
            sent['github'] = self.github_notifier.send(subject, message, priority, **kwargs)
            logger.info(f"CRITICAL notification: {sent}")
        elif priority == NotificationPriority.HIGH:
            sent['email'] = self.email_notifier.send(subject, message, priority, **kwargs)
            sent['sms'] = self.sms_notifier.send(subject, message, priority, **kwargs)
            logger.info(f"HIGH notification: {sent}")
        elif priority == NotificationPriority.MEDIUM:
            sent['email'] = self.email_notifier.send(subject, message, priority, **kwargs)
            logger.info(f"MEDIUM notification: {sent}")
        elif priority == NotificationPriority.LOW:
            self.low_priority_queue.append((subject, message, priority, kwargs))
            logger.info(f"LOW notification queued (for digest)")
        elif priority == NotificationPriority.INFO:
            self.info_queue.append((subject, message, priority, kwargs))
            logger.info(f"INFO notification queued (for weekly)")
        else:
            logger.warning(f"Unknown priority: {priority}")
        return sent

    def send_daily_digest(self, to_email: Optional[str] = None) -> bool:
        """Send a single daily digest email for LOW priority messages."""
        if not self.low_priority_queue:
            logger.info("No LOW priority messages to send in daily digest.")
            return False
        subject = f"Genesis AI Systems — Daily Health {datetime.date.today()}"
        html = ""
        for idx, (s, m, p, k) in enumerate(self.low_priority_queue, 1):
            html += f"<h4 style='margin-bottom:2px;color:{ELECTRIC_BLUE};'>{idx}. {s} <span style='color:#64748b;font-size:.95em;'>[{p.value}]</span></h4>"
            html += f"<div style='margin-left:10px;margin-bottom:16px;'>{m}</div>"
        sent = self.email_notifier.send(subject, html, NotificationPriority.LOW, to_email=to_email or BRAND_EMAIL)
        self.low_priority_queue.clear()
        logger.info("Daily digest sent.")
        return sent

    def send_weekly_report(self, to_email: Optional[str] = None) -> bool:
        """Send a single weekly report email for INFO messages."""
        if not self.info_queue:
            logger.info("No INFO messages to send in weekly report.")
            return False
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())
        subject = f"Genesis AI Systems — Weekly Report {week_start} to {today}"
        html = ""
        for idx, (s, m, p, k) in enumerate(self.info_queue, 1):
            html += f"<h4 style='margin-bottom:2px;color:{ELECTRIC_BLUE};'>{idx}. {s} <span style='color:#64748b;font-size:.95em;'>[{p.value}]</span></h4>"
            html += f"<div style='margin-left:10px;margin-bottom:16px;'>{m}</div>"
        sent = self.email_notifier.send(subject, html, NotificationPriority.INFO, to_email=to_email or BRAND_EMAIL)
        self.info_queue.clear()
        logger.info("Weekly report sent.")
        return sent

    def batch_digest(self):
        self.send_daily_digest()
        self.send_weekly_report()

# Utility for formatting SMS for agent failure and recovery

def format_sms_failure(agent_name, description, when=None):
    when = when or BaseNotifier.now()
    text = f"""
🚨 Genesis AI Systems Alert
Agent: {agent_name}\nStatus: FAILED\nIssue: {description}\nTime: {when}\nFix: {ACTIONS_URL}
"""
    return text.strip()

def format_sms_recovery(agent_name, when=None):
    when = when or BaseNotifier.now()
    text = f"""
✅ Genesis AI Systems
Agent: {agent_name}\nStatus: RECOVERED\nAll systems operational\nTime: {when}
"""
    return text.strip()

# === Commandline for Local Testing ===
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Genesis AI Systems Notification Utility")
    parser.add_argument('--test-sms', action='store_true', help="Test SMS notification")
    parser.add_argument('--test-email', action='store_true', help="Test email notification")
    parser.add_argument('--test-slack', action='store_true', help="Test Slack notification")
    parser.add_argument('--test-all', action='store_true', help="Test all notification channels")
    parser.add_argument('--to-email', default=None, help="Override destination email for test")
    parser.add_argument('--to-number', default=None, help="Override destination phone number for test")
    args = parser.parse_args()

    results = {}

    if args.test_sms or args.test_all:
        sms_body = """\n✅ Genesis AI Systems\nTest notification successful!\nYour agent monitoring is active.\n- Trendell Fordham\n  genesisai.systems\n""".strip()
        sms = SMSNotifier()
        ok = sms.send("Genesis AI Systems Test SMS", sms_body, NotificationPriority.INFO, to_number=args.to_number)
        print("Test SMS:", "PASS" if ok else "FAIL")
        results['sms'] = ok

    if args.test_email or args.test_all:
        subject = "✅ Genesis AI Systems — Notification Test"
        body = """
This is a test from Genesis AI Systems agent monitoring system.<br><br>
If you received this, notifications work.<br><br>
Monitoring: <a href=\"https://genesisai.systems\">https://genesisai.systems</a><br><br>
Trendell Fordham<br>
Founder, Genesis AI Systems<br>
info@genesisai.systems<br>
(313) 400-2575
""".strip()
        email = EmailNotifier()
        ok = email.send(subject, body, NotificationPriority.INFO, to_email=args.to_email)
        print("Test Email:", "PASS" if ok else "FAIL")
        results['email'] = ok

    if args.test_slack or args.test_all:
        slack_msg = "✅ Genesis AI Systems\nTest notification successful from agent monitoring system."
        slack = SlackNotifier()
        ok = slack.send("Genesis AI Systems — Notification Test", slack_msg, NotificationPriority.INFO)
        print("Test Slack:", "PASS" if ok else "FAIL")
        results['slack'] = ok

    if not (args.test_sms or args.test_email or args.test_slack or args.test_all):
        parser.print_help()

    exit_code = 0 if all(results.values()) else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
