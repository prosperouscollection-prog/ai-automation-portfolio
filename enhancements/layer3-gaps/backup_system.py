"""Daily backup system for Genesis AI Systems client data.

This module exports Google Sheets data to CSV, stores rolling local backups,
optionally mirrors the backups to S3, and notifies stakeholders of success or
failure. The pipeline is built from abstractions so storage backends can be
extended safely.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv


@dataclass(frozen=True)
class BackupArtifact:
    """A file produced or stored during the backup pipeline."""

    path: Path
    provider_name: str


@dataclass(frozen=True)
class BackupConfig:
    """Environment-backed configuration for backup operations."""

    spreadsheet_id: str
    worksheet_names: list[str]
    service_account_json: str
    local_dir: Path
    log_path: Path
    retention_days: int
    s3_bucket: str | None
    aws_region: str | None
    notify_to: str | None
    smtp_host: str
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from_email: str | None
    smtp_from_name: str

    @classmethod
    def from_env(cls) -> "BackupConfig":
        """Load configuration from environment variables."""
        load_dotenv()
        return cls(
            spreadsheet_id=_require_env("GOOGLE_SHEETS_SPREADSHEET_ID"),
            worksheet_names=[
                item.strip()
                for item in os.getenv("GOOGLE_SHEETS_WORKSHEET_NAMES", "Leads").split(",")
                if item.strip()
            ],
            service_account_json=_require_env("GOOGLE_SERVICE_ACCOUNT_JSON"),
            local_dir=Path(os.getenv("BACKUP_LOCAL_DIR", "./backups")).expanduser(),
            log_path=Path(os.getenv("BACKUP_LOG_PATH", "./backup_operations.log")).expanduser(),
            retention_days=int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
            s3_bucket=os.getenv("AWS_S3_BUCKET") or None,
            aws_region=os.getenv("AWS_REGION") or None,
            notify_to=os.getenv("BACKUP_NOTIFY_TO") or None,
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "465")),
            smtp_username=os.getenv("SMTP_USERNAME") or None,
            smtp_password=os.getenv("SMTP_PASSWORD") or None,
            smtp_from_email=os.getenv("SMTP_FROM_EMAIL") or None,
            smtp_from_name=os.getenv("SMTP_FROM_NAME", "Genesis AI Systems"),
        )


class BackupProvider(ABC):
    """Abstract base for one stage in the backup pipeline."""

    @abstractmethod
    def run(self, artifacts: list[BackupArtifact]) -> list[BackupArtifact]:
        """Process and return backup artifacts."""


class GoogleSheetsBackup(BackupProvider):
    """Exports configured Google Sheets tabs into CSV files."""

    def __init__(self, spreadsheet_id: str, worksheet_names: list[str], service_account_json: str, export_dir: Path) -> None:
        """Store Google Sheets export settings."""
        self._spreadsheet_id = spreadsheet_id
        self._worksheet_names = worksheet_names
        self._service_account_json = service_account_json
        self._export_dir = export_dir

    def run(self, artifacts: list[BackupArtifact]) -> list[BackupArtifact]:
        """Download worksheet data and write each tab to CSV."""
        import gspread

        self._export_dir.mkdir(parents=True, exist_ok=True)
        creds = _load_service_account_credentials(
            self._service_account_json,
            [
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
            ],
        )
        client = gspread.authorize(creds)
        workbook = client.open_by_key(self._spreadsheet_id)
        exported: list[BackupArtifact] = []

        for worksheet_name in self._worksheet_names:
            worksheet = workbook.worksheet(worksheet_name)
            rows = worksheet.get_all_values()
            csv_path = self._export_dir / f"{worksheet_name}.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerows(rows)
            exported.append(BackupArtifact(path=csv_path, provider_name="GoogleSheetsBackup"))

        return artifacts + exported


class LocalFileBackup(BackupProvider):
    """Copies exported files into the rolling local backup directory."""

    def __init__(self, destination_dir: Path, retention_days: int) -> None:
        """Store local backup location and retention policy."""
        self._destination_dir = destination_dir
        self._retention_days = retention_days

    def run(self, artifacts: list[BackupArtifact]) -> list[BackupArtifact]:
        """Copy current artifacts into a timestamped local backup folder."""
        stamped_dir = self._destination_dir / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        stamped_dir.mkdir(parents=True, exist_ok=True)
        stored: list[BackupArtifact] = []
        for artifact in artifacts:
            destination = stamped_dir / artifact.path.name
            shutil.copy2(artifact.path, destination)
            stored.append(BackupArtifact(path=destination, provider_name="LocalFileBackup"))
        self._prune_old_backups()
        return artifacts + stored

    def _prune_old_backups(self) -> None:
        """Delete local backup folders older than the configured retention."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)
        for child in self._destination_dir.iterdir() if self._destination_dir.exists() else []:
            if not child.is_dir():
                continue
            try:
                created = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
            if created < cutoff:
                shutil.rmtree(child, ignore_errors=True)


class S3Backup(BackupProvider):
    """Mirrors backup artifacts to S3 when bucket configuration exists."""

    def __init__(self, bucket_name: str, region_name: str | None, retention_days: int) -> None:
        """Store S3 settings for upload and optional cleanup."""
        self._bucket_name = bucket_name
        self._region_name = region_name
        self._retention_days = retention_days

    def run(self, artifacts: list[BackupArtifact]) -> list[BackupArtifact]:
        """Upload current artifacts to S3 and keep the artifact list unchanged."""
        import boto3

        session = boto3.session.Session(region_name=self._region_name)
        client = session.client("s3")
        prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d/%H%M%S")
        for artifact in artifacts:
            key = f"genesis-ai-backups/{prefix}/{artifact.path.name}"
            client.upload_file(str(artifact.path), self._bucket_name, key)
        self._prune_old_objects(client)
        return artifacts

    def _prune_old_objects(self, client) -> None:
        """Delete old backup objects from S3 beyond the retention window."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket_name, Prefix="genesis-ai-backups/"):
            for item in page.get("Contents", []):
                if item["LastModified"] < cutoff:
                    client.delete_object(Bucket=self._bucket_name, Key=item["Key"])


class EmailNotifier:
    """Sends success or failure notifications for the backup job."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        from_email: str | None,
        from_name: str,
        notify_to: str | None,
    ) -> None:
        """Store email settings and support no-op mode when email is not configured."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._from_name = from_name
        self._notify_to = notify_to

    def send(self, subject: str, body: str) -> None:
        """Send an email if notification settings are available."""
        if not all([self._username, self._password, self._from_email, self._notify_to]):
            return
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{self._from_name} <{self._from_email}>"
        message["To"] = self._notify_to
        message.set_content(body)
        with smtplib.SMTP_SSL(self._host, self._port) as smtp:
            smtp.login(self._username, self._password)
            smtp.send_message(message)


class BackupLogger:
    """Simple append-only logger for backup operations."""

    def __init__(self, path: Path) -> None:
        """Store the file path for backup logs."""
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, message: str) -> None:
        """Append a timestamped message to the log file."""
        line = f"{datetime.now(timezone.utc).isoformat()} | {message}\n"
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(line)


class BackupOrchestrator:
    """Coordinates the backup providers into one daily job."""

    def __init__(self, providers: list[BackupProvider], notifier: EmailNotifier, logger: BackupLogger) -> None:
        """Inject backup stages and operational services."""
        self._providers = providers
        self._notifier = notifier
        self._logger = logger

    def run(self) -> list[BackupArtifact]:
        """Run the full backup pipeline and send a final notification."""
        artifacts: list[BackupArtifact] = []
        try:
            for provider in self._providers:
                artifacts = provider.run(artifacts)
                self._logger.write(
                    f"{provider.__class__.__name__} completed with {len(artifacts)} artifacts available."
                )
            self._notifier.send(
                subject="Genesis AI Systems backup succeeded",
                body=f"Backup completed successfully with {len(artifacts)} artifacts.",
            )
            return artifacts
        except Exception as exc:  # noqa: BLE001
            self._logger.write(f"Backup failed: {exc}")
            self._notifier.send(
                subject="Genesis AI Systems backup failed",
                body=f"The backup job failed with error: {exc}",
            )
            raise


def build_backup_orchestrator() -> BackupOrchestrator:
    """Assemble the backup system from environment variables."""
    config = BackupConfig.from_env()
    export_dir = config.local_dir / "_exports"
    providers: list[BackupProvider] = [
        GoogleSheetsBackup(
            spreadsheet_id=config.spreadsheet_id,
            worksheet_names=config.worksheet_names,
            service_account_json=config.service_account_json,
            export_dir=export_dir,
        ),
        LocalFileBackup(config.local_dir, config.retention_days),
    ]
    if config.s3_bucket:
        providers.append(S3Backup(config.s3_bucket, config.aws_region, config.retention_days))

    notifier = EmailNotifier(
        host=config.smtp_host,
        port=config.smtp_port,
        username=config.smtp_username,
        password=config.smtp_password,
        from_email=config.smtp_from_email,
        from_name=config.smtp_from_name,
        notify_to=config.notify_to,
    )
    logger = BackupLogger(config.log_path)
    return BackupOrchestrator(providers, notifier, logger)


def _load_service_account_credentials(raw_json_or_path: str, scopes: Iterable[str]):
    """Load Google service-account credentials from JSON text or a file path."""
    from google.oauth2.service_account import Credentials

    raw = raw_json_or_path.strip()
    if raw.startswith("{"):
        info = json.loads(raw)
    else:
        info = json.loads(Path(raw).read_text(encoding="utf-8"))
    return Credentials.from_service_account_info(info, scopes=list(scopes))


def _require_env(name: str) -> str:
    """Read and validate a required environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


if __name__ == "__main__":
    orchestrator = build_backup_orchestrator()
    result = orchestrator.run()
    print(f"Backup complete: {len(result)} artifacts processed.")
