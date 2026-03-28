"""Appointment confirmation email generation for Genesis AI Systems deployments.

This module handles one workflow: take appointment details, render a branded
HTML confirmation email, attach a calendar invite, and deliver the message via
an injected transport.
"""

from __future__ import annotations

import os
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from string import Template

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppointmentDetails:
    """All details required to confirm an appointment."""

    client_name: str
    client_email: str
    appointment_start: datetime
    duration_minutes: int
    service_name: str
    location_name: str
    location_address: str
    business_phone: str


@dataclass(frozen=True)
class BrandingConfig:
    """Brand colors and text injected into the email template."""

    business_name: str
    primary_color: str
    accent_color: str
    cancellation_policy: str
    directions_url: str
    support_email: str


@dataclass(frozen=True)
class SMTPConfig:
    """SMTP delivery settings for confirmation emails."""

    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str


class EmailTransport(ABC):
    """Interface for any email delivery provider."""

    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """Send the prepared email message."""


class SMTPEmailTransport(EmailTransport):
    """SMTP implementation for confirmation email delivery."""

    def __init__(self, config: SMTPConfig) -> None:
        """Store SMTP configuration for later delivery."""
        self._config = config

    def send(self, message: EmailMessage) -> None:
        """Deliver the email over SMTP with SSL transport."""
        with smtplib.SMTP_SSL(self._config.host, self._config.port) as smtp:
            smtp.login(self._config.username, self._config.password)
            smtp.send_message(message)


class ConfirmationTemplateRenderer:
    """Loads and renders the standalone HTML email template."""

    def __init__(self, template_path: Path) -> None:
        """Use a filesystem HTML template for the confirmation email."""
        self._template_path = template_path

    def render(self, appointment: AppointmentDetails, branding: BrandingConfig) -> str:
        """Replace placeholders with appointment and business information."""
        raw_template = self._template_path.read_text(encoding="utf-8")
        template = Template(raw_template)
        end_time = appointment.appointment_start + timedelta(minutes=appointment.duration_minutes)
        return template.safe_substitute(
            business_name=branding.business_name,
            primary_color=branding.primary_color,
            accent_color=branding.accent_color,
            client_name=appointment.client_name,
            appointment_date=appointment.appointment_start.strftime("%A, %B %d, %Y"),
            appointment_time=appointment.appointment_start.strftime("%I:%M %p"),
            appointment_end_time=end_time.strftime("%I:%M %p"),
            service_name=appointment.service_name,
            location_name=appointment.location_name,
            location_address=appointment.location_address,
            business_phone=appointment.business_phone,
            support_email=branding.support_email,
            cancellation_policy=branding.cancellation_policy,
            directions_url=branding.directions_url,
        )


class ICSBuilder:
    """Builds a standards-friendly calendar invite attachment."""

    @staticmethod
    def build(appointment: AppointmentDetails, branding: BrandingConfig) -> str:
        """Render an iCalendar payload for the appointment."""
        start = appointment.appointment_start.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        end = (
            appointment.appointment_start + timedelta(minutes=appointment.duration_minutes)
        ).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        created = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        uid = f"{appointment.client_email}-{start}@genesis-ai"
        summary = f"{branding.business_name}: {appointment.service_name}"

        return "\r\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Genesis AI Systems//Appointment Confirmation//EN",
                "CALSCALE:GREGORIAN",
                "METHOD:REQUEST",
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{created}",
                f"DTSTART:{start}",
                f"DTEND:{end}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:Appointment confirmed with {branding.business_name}",
                f"LOCATION:{appointment.location_address}",
                "END:VEVENT",
                "END:VCALENDAR",
            ]
        )


class AppointmentConfirmationService:
    """Coordinates HTML rendering, .ics generation, and message delivery."""

    def __init__(
        self,
        transport: EmailTransport,
        renderer: ConfirmationTemplateRenderer,
        branding: BrandingConfig,
        from_email: str,
        from_name: str,
    ) -> None:
        """Store injected dependencies for confirmation delivery."""
        self._transport = transport
        self._renderer = renderer
        self._branding = branding
        self._from_email = from_email
        self._from_name = from_name

    def send_confirmation(self, appointment: AppointmentDetails) -> EmailMessage:
        """Build and send a branded confirmation email with calendar attachment."""
        html_body = self._renderer.render(appointment, self._branding)
        ics_payload = ICSBuilder.build(appointment, self._branding)

        message = EmailMessage()
        message["Subject"] = (
            f"{self._branding.business_name} Appointment Confirmation - "
            f"{appointment.appointment_start.strftime('%B %d, %Y')}"
        )
        message["From"] = f"{self._from_name} <{self._from_email}>"
        message["To"] = appointment.client_email
        message.set_content(
            (
                f"Hello {appointment.client_name},\n\n"
                f"Your {appointment.service_name} appointment with {self._branding.business_name} "
                f"is confirmed for {appointment.appointment_start.strftime('%A, %B %d at %I:%M %p')}.\n\n"
                f"Location: {appointment.location_name}\n"
                f"Address: {appointment.location_address}\n"
                f"Phone: {appointment.business_phone}\n\n"
                f"Cancellation policy: {self._branding.cancellation_policy}\n"
            )
        )
        message.add_alternative(html_body, subtype="html")
        message.add_attachment(
            ics_payload.encode("utf-8"),
            maintype="text",
            subtype="calendar",
            filename="appointment.ics",
        )

        self._transport.send(message)
        return message


def load_branding_from_env() -> BrandingConfig:
    """Load email branding values from environment variables."""
    load_dotenv()
    return BrandingConfig(
        business_name=os.getenv("BUSINESS_NAME", "Genesis AI Systems Client"),
        primary_color=os.getenv("BUSINESS_PRIMARY_COLOR", "#2563eb"),
        accent_color=os.getenv("BUSINESS_ACCENT_COLOR", "#0f172a"),
        cancellation_policy=os.getenv(
            "BUSINESS_CANCELLATION_POLICY",
            "Please give at least 24 hours notice if you need to reschedule.",
        ),
        directions_url=os.getenv("BUSINESS_DIRECTIONS_URL", "https://maps.google.com/"),
        support_email=os.getenv("BUSINESS_EMAIL", "support@example.com"),
    )


def load_smtp_from_env() -> SMTPConfig:
    """Load SMTP configuration from environment variables."""
    load_dotenv()
    return SMTPConfig(
        host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        port=int(os.getenv("SMTP_PORT", "465")),
        username=_require_env("SMTP_USERNAME"),
        password=_require_env("SMTP_PASSWORD"),
        from_email=_require_env("SMTP_FROM_EMAIL"),
        from_name=os.getenv("SMTP_FROM_NAME", "Genesis AI Systems"),
    )


def build_confirmation_service() -> AppointmentConfirmationService:
    """Create a ready-to-send confirmation service from environment variables."""
    smtp_config = load_smtp_from_env()
    branding = load_branding_from_env()
    transport = SMTPEmailTransport(smtp_config)
    template_path = Path(__file__).with_name("confirmation_email_template.html")
    renderer = ConfirmationTemplateRenderer(template_path)
    return AppointmentConfirmationService(
        transport=transport,
        renderer=renderer,
        branding=branding,
        from_email=smtp_config.from_email,
        from_name=smtp_config.from_name,
    )


def _require_env(name: str) -> str:
    """Read and validate a required environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value
