"""Referral tracking and commission automation for Genesis AI Systems.

This module treats referrals as a small operating system: it stores referral
records, calculates commissions, generates tracking links, sends thank-you
emails, and produces monthly reports.
"""

from __future__ import annotations

import csv
import os
import smtplib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

from dotenv import load_dotenv


@dataclass(frozen=True)
class ReferralRecord:
    """Represents one referral tracked by Genesis AI Systems."""

    referral_id: str
    referrer_name: str
    referrer_email: str
    referred_business_name: str
    referred_contact_email: str
    created_at: str
    status: str
    utm_link: str
    setup_fee: float = 0.0
    commission_due: float = 0.0
    converted_at: str = ""


class ReferralRepository(ABC):
    """Abstract persistence layer for referral records."""

    @abstractmethod
    def add(self, record: ReferralRecord) -> None:
        """Persist a new referral record."""

    @abstractmethod
    def update(self, record: ReferralRecord) -> None:
        """Update an existing referral record."""

    @abstractmethod
    def list_all(self) -> list[ReferralRecord]:
        """Return all referral records."""


class CSVReferralRepository(ReferralRepository):
    """CSV-backed referral repository for low-friction operations."""

    FIELDNAMES = [
        "referral_id",
        "referrer_name",
        "referrer_email",
        "referred_business_name",
        "referred_contact_email",
        "created_at",
        "status",
        "utm_link",
        "setup_fee",
        "commission_due",
        "converted_at",
    ]

    def __init__(self, file_path: Path) -> None:
        """Store the CSV path and initialize the file if needed."""
        self._file_path = file_path
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            with self._file_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=self.FIELDNAMES)
                writer.writeheader()

    def add(self, record: ReferralRecord) -> None:
        """Append a new referral record to the CSV file."""
        with self._file_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.FIELDNAMES)
            writer.writerow(record.__dict__)

    def update(self, record: ReferralRecord) -> None:
        """Replace one referral record in the CSV file."""
        records = self.list_all()
        with self._file_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            for existing in records:
                writer.writerow((record if existing.referral_id == record.referral_id else existing).__dict__)

    def list_all(self) -> list[ReferralRecord]:
        """Return all CSV referral records as dataclasses."""
        with self._file_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return [
                ReferralRecord(
                    referral_id=row["referral_id"],
                    referrer_name=row["referrer_name"],
                    referrer_email=row["referrer_email"],
                    referred_business_name=row["referred_business_name"],
                    referred_contact_email=row["referred_contact_email"],
                    created_at=row["created_at"],
                    status=row["status"],
                    utm_link=row["utm_link"],
                    setup_fee=float(row["setup_fee"] or 0),
                    commission_due=float(row["commission_due"] or 0),
                    converted_at=row["converted_at"],
                )
                for row in reader
            ]


class EmailTransport(ABC):
    """Interface for sending referral-related emails."""

    @abstractmethod
    def send(self, to_email: str, subject: str, body: str) -> None:
        """Deliver an email message."""


class SMTPEmailTransport(EmailTransport):
    """SMTP implementation used for referral emails."""

    def __init__(self, host: str, port: int, username: str, password: str, from_email: str, from_name: str) -> None:
        """Store SMTP settings for later email delivery."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._from_name = from_name

    def send(self, to_email: str, subject: str, body: str) -> None:
        """Send a plain-text email via SMTP SSL."""
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{self._from_name} <{self._from_email}>"
        message["To"] = to_email
        message.set_content(body)
        with smtplib.SMTP_SSL(self._host, self._port) as smtp:
            smtp.login(self._username, self._password)
            smtp.send_message(message)


class CommissionCalculator:
    """Owns commission calculation rules."""

    @staticmethod
    def calculate_first_month_setup_commission(setup_fee: float) -> float:
        """Return a 10 percent commission on the setup fee."""
        return round(setup_fee * 0.10, 2)


class ReferralLinkGenerator:
    """Generates trackable UTM links for referrers."""

    def __init__(self, base_url: str) -> None:
        """Store the landing URL used for referral tracking."""
        self._base_url = base_url

    def build(self, referrer_name: str, referral_id: str) -> str:
        """Create a UTM-tagged link tied to the referral source."""
        parsed = urlparse(self._base_url)
        query = dict(parse_qsl(parsed.query))
        query.update(
            {
                "utm_source": "client_referral",
                "utm_medium": "referral",
                "utm_campaign": _slugify(referrer_name),
                "ref": referral_id,
            }
        )
        return urlunparse(parsed._replace(query=urlencode(query)))


class ReferralService:
    """High-level operations for referral creation, conversion, and reporting."""

    def __init__(
        self,
        repository: ReferralRepository,
        link_generator: ReferralLinkGenerator,
        commission_calculator: CommissionCalculator,
        email_transport: EmailTransport | None = None,
    ) -> None:
        """Inject dependencies behind interfaces for testability."""
        self._repository = repository
        self._link_generator = link_generator
        self._commission_calculator = commission_calculator
        self._email_transport = email_transport

    def create_referral(
        self,
        referrer_name: str,
        referrer_email: str,
        referred_business_name: str,
        referred_contact_email: str,
    ) -> ReferralRecord:
        """Create and persist a new referral record with a tracking link."""
        referral_id = str(uuid.uuid4())
        utm_link = self._link_generator.build(referrer_name, referral_id)
        record = ReferralRecord(
            referral_id=referral_id,
            referrer_name=referrer_name,
            referrer_email=referrer_email,
            referred_business_name=referred_business_name,
            referred_contact_email=referred_contact_email,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="referred",
            utm_link=utm_link,
        )
        self._repository.add(record)
        return record

    def convert_referral(self, referral_id: str, setup_fee: float) -> ReferralRecord:
        """Mark a referral as converted, calculate commission, and send a thank-you email."""
        records = self._repository.list_all()
        record = next((item for item in records if item.referral_id == referral_id), None)
        if record is None:
            raise ValueError(f"Referral not found: {referral_id}")

        converted = ReferralRecord(
            referral_id=record.referral_id,
            referrer_name=record.referrer_name,
            referrer_email=record.referrer_email,
            referred_business_name=record.referred_business_name,
            referred_contact_email=record.referred_contact_email,
            created_at=record.created_at,
            status="converted",
            utm_link=record.utm_link,
            setup_fee=setup_fee,
            commission_due=self._commission_calculator.calculate_first_month_setup_commission(setup_fee),
            converted_at=datetime.now(timezone.utc).isoformat(),
        )
        self._repository.update(converted)

        if self._email_transport is not None:
            self._email_transport.send(
                to_email=converted.referrer_email,
                subject="Your Genesis AI Systems referral converted",
                body=(
                    f"Hi {converted.referrer_name},\n\n"
                    f"Thank you for referring {converted.referred_business_name}. "
                    f"They are now an active Genesis AI Systems client.\n\n"
                    f"Your referral reward is ${converted.commission_due:.2f}.\n"
                ),
            )
        return converted

    def monthly_report(self, year: int, month: int) -> str:
        """Generate a lightweight monthly referral report."""
        records = self._repository.list_all()
        matching = [
            record
            for record in records
            if record.created_at.startswith(f"{year:04d}-{month:02d}")
            or record.converted_at.startswith(f"{year:04d}-{month:02d}")
        ]
        converted = [record for record in matching if record.status == "converted"]
        total_commission = sum(record.commission_due for record in converted)
        return (
            f"Referral report for {year:04d}-{month:02d}\n"
            f"Total referrals touched: {len(matching)}\n"
            f"Converted referrals: {len(converted)}\n"
            f"Commission due: ${total_commission:.2f}\n"
        )


def build_referral_service() -> ReferralService:
    """Create a referral service from environment variables."""
    load_dotenv()
    repository = CSVReferralRepository(
        Path(os.getenv("REFERRAL_CSV_PATH", "./referrals.csv")).expanduser()
    )
    link_generator = ReferralLinkGenerator(_require_env("REFERRAL_BASE_URL"))
    email_transport = None

    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    if smtp_username and smtp_password and smtp_from_email:
        email_transport = SMTPEmailTransport(
            host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            port=int(os.getenv("SMTP_PORT", "465")),
            username=smtp_username,
            password=smtp_password,
            from_email=smtp_from_email,
            from_name=os.getenv("SMTP_FROM_NAME", "Genesis AI Systems"),
        )

    return ReferralService(
        repository=repository,
        link_generator=link_generator,
        commission_calculator=CommissionCalculator(),
        email_transport=email_transport,
    )


def _require_env(name: str) -> str:
    """Read and validate a required environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _slugify(value: str) -> str:
    """Convert user-facing text into a URL-safe campaign slug."""
    lowered = value.lower().strip()
    return "".join(char if char.isalnum() else "-" for char in lowered).strip("-")
