"""Twilio-powered SMS escalation for Genesis AI Systems lead workflows.

This module is intentionally focused on one job: receiving scored lead data,
enforcing opt-out rules, and sending high-priority SMS alerts to a business
owner when the lead deserves immediate attention.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import os


@dataclass(frozen=True)
class LeadData:
    """Lead information required for an SMS escalation decision."""

    message: str
    score: str
    timestamp: datetime


@dataclass(frozen=True)
class TwilioSettings:
    """Environment-backed configuration for Twilio SMS delivery."""

    account_sid: str
    auth_token: str
    from_number: str
    to_number: str
    log_path: Path
    opt_out_path: Path

    @classmethod
    def from_env(cls) -> "TwilioSettings":
        """Build settings from environment variables."""
        load_dotenv()
        return cls(
            account_sid=_require_env("TWILIO_ACCOUNT_SID"),
            auth_token=_require_env("TWILIO_AUTH_TOKEN"),
            from_number=_require_env("TWILIO_FROM_NUMBER"),
            to_number=_require_env("TWILIO_TO_NUMBER"),
            log_path=Path(os.getenv("SMS_LOG_PATH", "./sms_alerts.log")).expanduser(),
            opt_out_path=Path(os.getenv("SMS_OPTOUT_PATH", "./sms_opt_out.txt")).expanduser(),
        )


@dataclass(frozen=True)
class SMSResult:
    """Represents the final delivery outcome for an alert attempt."""

    sent: bool
    reason: str
    message_sid: Optional[str] = None


class SMSGateway(ABC):
    """Abstraction for any SMS delivery provider."""

    @abstractmethod
    def send_message(self, body: str, from_number: str, to_number: str) -> SMSResult:
        """Send an SMS body from one number to another."""


class TwilioGateway(SMSGateway):
    """Twilio implementation of the SMS delivery gateway."""

    def __init__(self, account_sid: str, auth_token: str) -> None:
        """Create a Twilio gateway with authenticated client access."""
        from twilio.base.exceptions import TwilioRestException
        from twilio.rest import Client

        self._client = Client(account_sid, auth_token)
        self._error_type = TwilioRestException

    def send_message(self, body: str, from_number: str, to_number: str) -> SMSResult:
        """Send a message through Twilio and normalize errors."""
        try:
            message = self._client.messages.create(
                body=body,
                from_=from_number,
                to=to_number,
            )
            return SMSResult(sent=True, reason="SMS sent successfully.", message_sid=message.sid)
        except self._error_type as exc:
            return SMSResult(sent=False, reason=f"Twilio rejected the request: {exc}")
        except Exception as exc:  # noqa: BLE001
            return SMSResult(sent=False, reason=f"Unexpected SMS transport error: {exc}")


class OptOutRegistry:
    """Tracks which recipients have opted out of SMS notifications."""

    STOP_WORDS = {"STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"}

    def __init__(self, file_path: Path) -> None:
        """Store opt-out data in a simple newline-delimited text file."""
        self._file_path = file_path
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file_path.touch(exist_ok=True)

    def is_opted_out(self, phone_number: str) -> bool:
        """Return True when the supplied number has opted out."""
        normalized = _normalize_phone(phone_number)
        return normalized in self._read_all()

    def process_inbound_reply(self, phone_number: str, inbound_text: str) -> bool:
        """Persist an opt-out when the inbound text contains a STOP keyword."""
        normalized_text = inbound_text.strip().upper()
        if normalized_text not in self.STOP_WORDS:
            return False

        numbers = self._read_all()
        numbers.add(_normalize_phone(phone_number))
        self._write_all(numbers)
        return True

    def _read_all(self) -> set[str]:
        """Read all opted-out numbers from disk."""
        content = self._file_path.read_text(encoding="utf-8")
        return {line.strip() for line in content.splitlines() if line.strip()}

    def _write_all(self, numbers: set[str]) -> None:
        """Write the opt-out registry to disk in a stable order."""
        self._file_path.write_text("\n".join(sorted(numbers)) + "\n", encoding="utf-8")


class AlertLogger:
    """Structured logging wrapper for audit-friendly SMS send logs."""

    def __init__(self, file_path: Path) -> None:
        """Configure a file-based logger for alert attempts."""
        self._logger = logging.getLogger(f"genesis_ai_sms_{file_path}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        if not self._logger.handlers:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(file_path, encoding="utf-8")
            handler.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            )
            self._logger.addHandler(handler)

    def info(self, message: str) -> None:
        """Log an informational event."""
        self._logger.info(message)

    def error(self, message: str) -> None:
        """Log an error event."""
        self._logger.error(message)


class SMSAlertService:
    """Single service object that enforces policy and sends SMS alerts."""

    def __init__(
        self,
        settings: TwilioSettings,
        gateway: SMSGateway,
        opt_out_registry: OptOutRegistry,
        alert_logger: AlertLogger,
    ) -> None:
        """Inject collaborators so the service depends on abstractions."""
        self._settings = settings
        self._gateway = gateway
        self._opt_out_registry = opt_out_registry
        self._alert_logger = alert_logger

    def send_high_lead_alert(self, lead: LeadData) -> SMSResult:
        """Send an alert when and only when the lead score is HIGH."""
        if lead.score.strip().upper() != "HIGH":
            result = SMSResult(sent=False, reason="Lead score is not HIGH; no SMS sent.")
            self._alert_logger.info(result.reason)
            return result

        if self._opt_out_registry.is_opted_out(self._settings.to_number):
            result = SMSResult(sent=False, reason="Recipient has opted out of SMS alerts.")
            self._alert_logger.info(result.reason)
            return result

        message_body = (
            "🔥 HIGH LEAD - Genesis AI Systems Alert\n"
            f"Message: {lead.message}\n"
            "Score: HIGH\n"
            f"Time: {lead.timestamp.isoformat()}\n"
            "Reply STOP to unsubscribe"
        )
        result = self._gateway.send_message(
            body=message_body,
            from_number=self._settings.from_number,
            to_number=self._settings.to_number,
        )
        log_method = self._alert_logger.info if result.sent else self._alert_logger.error
        log_method(
            f"sent={result.sent} | sid={result.message_sid or 'n/a'} | "
            f"to={self._settings.to_number} | reason={result.reason}"
        )
        return result


def build_sms_service() -> SMSAlertService:
    """Construct a fully configured SMS alert service from environment variables."""
    settings = TwilioSettings.from_env()
    gateway = TwilioGateway(settings.account_sid, settings.auth_token)
    registry = OptOutRegistry(settings.opt_out_path)
    logger = AlertLogger(settings.log_path)
    return SMSAlertService(settings, gateway, registry, logger)


def _require_env(name: str) -> str:
    """Read and validate a required environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _normalize_phone(phone_number: str) -> str:
    """Normalize a phone number to digits and a possible leading plus sign."""
    stripped = phone_number.strip()
    plus = "+" if stripped.startswith("+") else ""
    digits = "".join(char for char in stripped if char.isdigit())
    return f"{plus}{digits}"


def _demo() -> None:
    """Run a simple demonstration alert using environment-backed credentials."""
    service = build_sms_service()
    result = service.send_high_lead_alert(
        LeadData(
            message="I need an emergency dental appointment today.",
            score="HIGH",
            timestamp=datetime.now(timezone.utc),
        )
    )
    print(result)


if __name__ == "__main__":
    _demo()
