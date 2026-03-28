"""Gmail SMTP notifications."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from agent_system.config import Settings


class GmailNotifier:
    """Send deployment summaries through Gmail SMTP if configured."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_summary(self, subject: str, summary: str, details: list[str]) -> None:
        if not all(
            [
                self._settings.gmail_smtp_username,
                self._settings.gmail_smtp_password,
                self._settings.gmail_to,
            ]
        ):
            return

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._settings.gmail_smtp_username
        message["To"] = self._settings.gmail_to
        body = summary
        if details:
            body += "\n\nDetails:\n- " + "\n- ".join(details)
        message.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(
                self._settings.gmail_smtp_username,
                self._settings.gmail_smtp_password,
            )
            smtp.send_message(message)
