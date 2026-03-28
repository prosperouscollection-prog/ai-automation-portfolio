"""Active uptime monitoring for Genesis AI Systems client deployments.

This module pings client systems, logs uptime, notifies on outages and
recoveries, and renders a lightweight status dashboard for internal ops use.
"""

from __future__ import annotations

import json
import os
import smtplib
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import requests
from dotenv import load_dotenv


@dataclass(frozen=True)
class ClientMonitorConfig:
    """Monitoring inputs for one client."""

    client_id: str
    client_name: str
    webhook_urls: list[str]
    google_sheet_key: str | None = None
    vapi_status_url: str | None = None


@dataclass(frozen=True)
class CheckResult:
    """One system health check result."""

    check_name: str
    healthy: bool
    details: str


@dataclass(frozen=True)
class ClientStatusSnapshot:
    """Combined status for one client at one point in time."""

    client_id: str
    client_name: str
    checked_at: str
    checks: list[CheckResult]

    @property
    def healthy(self) -> bool:
        """Return True when all checks are healthy."""
        return all(check.healthy for check in self.checks)


class SystemCheck(ABC):
    """Abstract base for one health-check type."""

    @abstractmethod
    def run(self, client: ClientMonitorConfig) -> CheckResult:
        """Run the health check for a client."""


class AlertChannel(ABC):
    """Abstract interface for outage notifications."""

    @abstractmethod
    def send(self, subject: str, message: str) -> None:
        """Send an alert message."""


class WebhookCheck(SystemCheck):
    """Checks all configured webhook URLs for a client."""

    def run(self, client: ClientMonitorConfig) -> CheckResult:
        """Return healthy only when all webhooks respond below HTTP 400."""
        if not client.webhook_urls:
            return CheckResult("webhook", True, "No webhook URLs configured.")

        failures = []
        for url in client.webhook_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code >= 400:
                    failures.append(f"{url} returned {response.status_code}")
            except requests.RequestException as exc:
                failures.append(f"{url} failed: {exc}")

        if failures:
            return CheckResult("webhook", False, " | ".join(failures))
        return CheckResult("webhook", True, "All webhook endpoints responded successfully.")


class GoogleSheetsCheck(SystemCheck):
    """Checks Google Sheets connectivity for the client workbook."""

    def __init__(self, service_account_json: str | None) -> None:
        """Store Google credentials for later connectivity checks."""
        self._service_account_json = service_account_json

    def run(self, client: ClientMonitorConfig) -> CheckResult:
        """Confirm the workbook can be opened when a sheet key is provided."""
        if not client.google_sheet_key or not self._service_account_json:
            return CheckResult("google_sheets", True, "Google Sheets check skipped.")
        try:
            import gspread

            creds = _load_service_account_credentials(
                self._service_account_json,
                [
                    "https://www.googleapis.com/auth/spreadsheets.readonly",
                    "https://www.googleapis.com/auth/drive.readonly",
                ],
            )
            client_api = gspread.authorize(creds)
            client_api.open_by_key(client.google_sheet_key)
            return CheckResult("google_sheets", True, "Workbook opened successfully.")
        except Exception as exc:  # noqa: BLE001
            return CheckResult("google_sheets", False, f"Google Sheets check failed: {exc}")


class OpenAIStatusCheck(SystemCheck):
    """Checks the public OpenAI status endpoint."""

    def __init__(self, status_url: str) -> None:
        """Store the status endpoint URL."""
        self._status_url = status_url

    def run(self, client: ClientMonitorConfig) -> CheckResult:
        """Return healthy when OpenAI status does not report a major outage."""
        try:
            response = requests.get(self._status_url, timeout=10)
            response.raise_for_status()
            payload = response.json()
            indicator = (
                payload.get("status", {}).get("indicator")
                or payload.get("page", {}).get("status_indicator")
                or "none"
            )
            healthy = indicator not in {"major", "critical"}
            return CheckResult("openai", healthy, f"OpenAI status indicator: {indicator}")
        except Exception as exc:  # noqa: BLE001
            return CheckResult("openai", False, f"OpenAI status check failed: {exc}")


class VapiStatusCheck(SystemCheck):
    """Checks a Vapi status or health endpoint when configured."""

    def run(self, client: ClientMonitorConfig) -> CheckResult:
        """Return healthy when the Vapi URL responds successfully."""
        if not client.vapi_status_url:
            return CheckResult("vapi", True, "Vapi check skipped.")
        try:
            response = requests.get(client.vapi_status_url, timeout=10)
            healthy = response.status_code < 400
            return CheckResult("vapi", healthy, f"Vapi status HTTP {response.status_code}")
        except requests.RequestException as exc:
            return CheckResult("vapi", False, f"Vapi status check failed: {exc}")


class EmailAlertChannel(AlertChannel):
    """SMTP email alerts for outages and recoveries."""

    def __init__(self, host: str, port: int, username: str, password: str, from_email: str, from_name: str, to_email: str) -> None:
        """Store SMTP configuration for later delivery."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._from_name = from_name
        self._to_email = to_email

    def send(self, subject: str, message: str) -> None:
        """Send an email alert."""
        email = EmailMessage()
        email["Subject"] = subject
        email["From"] = f"{self._from_name} <{self._from_email}>"
        email["To"] = self._to_email
        email.set_content(message)
        with smtplib.SMTP_SSL(self._host, self._port) as smtp:
            smtp.login(self._username, self._password)
            smtp.send_message(email)


class TwilioAlertChannel(AlertChannel):
    """Twilio SMS alerts for outages and recoveries."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str) -> None:
        """Store Twilio credentials and destination numbers."""
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._from_number = from_number
        self._to_number = to_number

    def send(self, subject: str, message: str) -> None:
        """Send a short SMS alert through Twilio."""
        from twilio.rest import Client

        client = Client(self._account_sid, self._auth_token)
        body = f"{subject}\n{message}"
        client.messages.create(body=body[:1500], from_=self._from_number, to=self._to_number)


class UptimeStateRepository:
    """Persists the last known healthy state so recovery notices are possible."""

    def __init__(self, path: Path) -> None:
        """Store the JSON file path for state data."""
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("{}", encoding="utf-8")

    def load(self) -> dict[str, bool]:
        """Load last known health states."""
        return json.loads(self._path.read_text(encoding="utf-8"))

    def save(self, state: dict[str, bool]) -> None:
        """Persist new health states."""
        self._path.write_text(json.dumps(state, indent=2), encoding="utf-8")


class UptimeLogRepository:
    """Stores uptime snapshots and calculates daily/monthly uptime."""

    def __init__(self, path: Path) -> None:
        """Store the JSONL log path."""
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, snapshot: ClientStatusSnapshot) -> None:
        """Append one snapshot to the uptime log."""
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(snapshot)) + "\n")

    def calculate_monthly_uptime(self, client_id: str, year: int, month: int) -> float:
        """Calculate uptime percentage for a client based on logged snapshots."""
        prefix = f"{year:04d}-{month:02d}"
        rows = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if payload["client_id"] == client_id and payload["checked_at"].startswith(prefix):
                rows.append(payload)
        if not rows:
            return 100.0
        healthy = sum(1 for row in rows if all(check["healthy"] for check in row["checks"]))
        return round((healthy / len(rows)) * 100, 2)


class DashboardRenderer:
    """Renders a simple internal uptime dashboard as HTML."""

    def render(self, snapshots: list[ClientStatusSnapshot], output_path: Path) -> Path:
        """Write a lightweight status dashboard to disk."""
        rows = []
        for snapshot in snapshots:
            status = "Healthy" if snapshot.healthy else "Issue Detected"
            details = "<br>".join(
                f"{check.check_name}: {check.details}" for check in snapshot.checks
            )
            rows.append(
                f"<tr><td>{snapshot.client_name}</td><td>{status}</td>"
                f"<td>{snapshot.checked_at}</td><td>{details}</td></tr>"
            )
        html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Genesis AI Systems Uptime Dashboard</title></head>
<body style="font-family:Arial,sans-serif;background:#0f172a;color:#f8fafc;padding:24px;">
<h1>Genesis AI Systems Uptime Dashboard</h1>
<table style="width:100%;border-collapse:collapse;background:#16213b;">
<thead><tr><th>Client</th><th>Status</th><th>Checked At</th><th>Details</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></body></html>"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        return output_path


class UptimeMonitorService:
    """Coordinates checks, logging, alerting, and dashboard rendering."""

    def __init__(
        self,
        checks: list[SystemCheck],
        alert_channels: list[AlertChannel],
        state_repository: UptimeStateRepository,
        log_repository: UptimeLogRepository,
        dashboard_renderer: DashboardRenderer,
        dashboard_path: Path,
    ) -> None:
        """Inject collaborators for the monitoring workflow."""
        self._checks = checks
        self._alert_channels = alert_channels
        self._state_repository = state_repository
        self._log_repository = log_repository
        self._dashboard_renderer = dashboard_renderer
        self._dashboard_path = dashboard_path

    def run_once(self, clients: list[ClientMonitorConfig]) -> list[ClientStatusSnapshot]:
        """Run checks for all clients and send alerts on status changes."""
        prior_state = self._state_repository.load()
        new_state: dict[str, bool] = {}
        snapshots: list[ClientStatusSnapshot] = []

        for client in clients:
            results = [check.run(client) for check in self._checks]
            snapshot = ClientStatusSnapshot(
                client_id=client.client_id,
                client_name=client.client_name,
                checked_at=datetime.now(timezone.utc).isoformat(),
                checks=results,
            )
            snapshots.append(snapshot)
            self._log_repository.append(snapshot)
            new_state[client.client_id] = snapshot.healthy

            was_healthy = prior_state.get(client.client_id, True)
            if was_healthy and not snapshot.healthy:
                self._send_alert(
                    f"Genesis AI Systems outage detected - {client.client_name}",
                    self._format_snapshot(snapshot),
                )
            if not was_healthy and snapshot.healthy:
                self._send_alert(
                    f"Genesis AI Systems all clear - {client.client_name}",
                    self._format_snapshot(snapshot),
                )

        self._state_repository.save(new_state)
        self._dashboard_renderer.render(snapshots, self._dashboard_path)
        return snapshots

    def _send_alert(self, subject: str, message: str) -> None:
        """Send an alert through each configured channel."""
        for channel in self._alert_channels:
            try:
                channel.send(subject, message)
            except Exception:  # noqa: BLE001
                continue

    @staticmethod
    def _format_snapshot(snapshot: ClientStatusSnapshot) -> str:
        """Convert a snapshot into a human-readable alert body."""
        lines = [
            f"Client: {snapshot.client_name}",
            f"Checked at: {snapshot.checked_at}",
            f"Overall healthy: {snapshot.healthy}",
        ]
        lines.extend(f"- {check.check_name}: {check.details}" for check in snapshot.checks)
        return "\n".join(lines)


def build_default_service() -> UptimeMonitorService:
    """Build the monitoring service from environment variables."""
    load_dotenv()
    alert_channels: list[AlertChannel] = []
    if all(os.getenv(name, "").strip() for name in ["SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL", "UPTIME_ALERT_TO_EMAIL"]):
        alert_channels.append(
            EmailAlertChannel(
                host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
                port=int(os.getenv("SMTP_PORT", "465")),
                username=os.getenv("SMTP_USERNAME", ""),
                password=os.getenv("SMTP_PASSWORD", ""),
                from_email=os.getenv("SMTP_FROM_EMAIL", ""),
                from_name=os.getenv("SMTP_FROM_NAME", "Genesis AI Systems"),
                to_email=os.getenv("UPTIME_ALERT_TO_EMAIL", ""),
            )
        )
    if all(os.getenv(name, "").strip() for name in ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER", "UPTIME_ALERT_TO_NUMBER"]):
        alert_channels.append(
            TwilioAlertChannel(
                account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
                auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
                from_number=os.getenv("TWILIO_FROM_NUMBER", ""),
                to_number=os.getenv("UPTIME_ALERT_TO_NUMBER", ""),
            )
        )

    checks = [
        WebhookCheck(),
        GoogleSheetsCheck(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")),
        OpenAIStatusCheck(os.getenv("OPENAI_STATUS_URL", "https://status.openai.com/api/v2/status.json")),
        VapiStatusCheck(),
    ]
    return UptimeMonitorService(
        checks=checks,
        alert_channels=alert_channels,
        state_repository=UptimeStateRepository(Path(os.getenv("UPTIME_STATE_PATH", "./uptime_state.json"))),
        log_repository=UptimeLogRepository(Path(os.getenv("UPTIME_LOG_PATH", "./uptime_logs.jsonl"))),
        dashboard_renderer=DashboardRenderer(),
        dashboard_path=Path(os.getenv("UPTIME_DASHBOARD_PATH", "./uptime_dashboard.html")),
    )


def _load_service_account_credentials(raw_json_or_path: str, scopes: list[str]):
    """Load service-account credentials from JSON text or a file path."""
    from google.oauth2.service_account import Credentials

    raw = raw_json_or_path.strip()
    if raw.startswith("{"):
        info = json.loads(raw)
    else:
        info = json.loads(Path(raw).read_text(encoding="utf-8"))
    return Credentials.from_service_account_info(info, scopes=scopes)


if __name__ == "__main__":
    service = build_default_service()
    demo_clients = [
        ClientMonitorConfig(
            client_id="smile-dental",
            client_name="Smile Dental",
            webhook_urls=["https://example.com/webhook/lead-capture"],
            google_sheet_key=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"),
            vapi_status_url=os.getenv("VAPI_STATUS_URL") or None,
        )
    ]
    snapshots = service.run_once(demo_clients)
    print(f"Completed uptime checks for {len(snapshots)} client(s).")
