"""Monthly ROI reporting for Genesis AI Systems retained clients.

This report is designed to keep clients from canceling by translating system
activity into time saved, revenue influenced, and operational leverage.
"""

from __future__ import annotations

import json
import os
import smtplib
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class MonthlyMetrics:
    """All metrics required for the ROI report."""

    total_leads: int
    high_count: int
    medium_count: int
    low_count: int
    ai_responses_sent: int
    voice_calls_handled: int
    emails_sent: int
    estimated_time_saved_hours: float
    estimated_revenue_generated: float
    uptime_percentage: float
    top_keywords: list[str]


@dataclass(frozen=True)
class ROIConfig:
    """Environment-backed ROI reporting configuration."""

    spreadsheet_id: str
    worksheet_name: str
    service_account_json: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str
    report_to: str
    drive_folder_id: str | None
    anthropic_api_key: str | None
    claude_model: str
    business_name: str
    avg_deal_value: float
    vapi_metrics_path: Path
    email_metrics_path: Path
    uptime_log_path: Path

    @classmethod
    def from_env(cls) -> "ROIConfig":
        """Load the report configuration from environment variables."""
        load_dotenv()
        return cls(
            spreadsheet_id=_require_env("GOOGLE_SHEETS_SPREADSHEET_ID"),
            worksheet_name=os.getenv("GOOGLE_SHEETS_WORKSHEET_NAMES", "Leads").split(",")[0].strip(),
            service_account_json=_require_env("GOOGLE_SERVICE_ACCOUNT_JSON"),
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "465")),
            smtp_username=_require_env("SMTP_USERNAME"),
            smtp_password=_require_env("SMTP_PASSWORD"),
            smtp_from_email=_require_env("SMTP_FROM_EMAIL"),
            smtp_from_name=os.getenv("SMTP_FROM_NAME", "Genesis AI Systems"),
            report_to=_require_env("ROI_REPORT_TO"),
            drive_folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID") or None,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
            claude_model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            business_name=os.getenv("BUSINESS_NAME", "Genesis AI Systems Client"),
            avg_deal_value=float(os.getenv("ROI_AVG_DEAL_VALUE", "500")),
            vapi_metrics_path=Path(os.getenv("ROI_VAPI_METRICS_PATH", "./vapi_monthly_metrics.json")).expanduser(),
            email_metrics_path=Path(os.getenv("ROI_EMAIL_METRICS_PATH", "./email_monthly_metrics.json")).expanduser(),
            uptime_log_path=Path(os.getenv("UPTIME_LOG_PATH", "./uptime_logs.jsonl")).expanduser(),
        )


class MetricsSource(ABC):
    """Abstract metrics source for ROI calculations."""

    @abstractmethod
    def collect(self, month_start: datetime, month_end: datetime) -> dict:
        """Return source-specific metrics for the selected month."""


class GoogleSheetsMetricsSource(MetricsSource):
    """Reads lead and response metrics from Google Sheets."""

    def __init__(self, spreadsheet_id: str, worksheet_name: str, service_account_json: str, avg_deal_value: float) -> None:
        """Store Google Sheets connection details."""
        self._spreadsheet_id = spreadsheet_id
        self._worksheet_name = worksheet_name
        self._service_account_json = service_account_json
        self._avg_deal_value = avg_deal_value

    def collect(self, month_start: datetime, month_end: datetime) -> dict:
        """Collect lead counts, score mix, and estimated revenue."""
        import gspread

        creds = _load_service_account_credentials(
            self._service_account_json,
            [
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
            ],
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(self._spreadsheet_id).worksheet(self._worksheet_name)
        records = sheet.get_all_records()

        leads = []
        keyword_counter = Counter()
        for row in records:
            timestamp = _parse_timestamp(str(row.get("Timestamp") or row.get("timestamp") or ""))
            if not timestamp or timestamp < month_start or timestamp >= month_end:
                continue
            score = str(row.get("Score") or row.get("score") or "LOW").upper()
            message = str(row.get("Message") or row.get("message") or "")
            response = str(row.get("Response") or row.get("response") or "")
            leads.append({"score": score, "message": message, "response": response})
            keyword_counter.update(_extract_keywords(message))

        high = sum(1 for item in leads if item["score"] == "HIGH")
        medium = sum(1 for item in leads if item["score"] == "MEDIUM")
        low = sum(1 for item in leads if item["score"] == "LOW")
        ai_responses_sent = sum(1 for item in leads if item["response"].strip())
        return {
            "total_leads": len(leads),
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
            "ai_responses_sent": ai_responses_sent,
            "estimated_time_saved_hours": round((len(leads) * 15) / 60.0, 2),
            "estimated_revenue_generated": round(high * self._avg_deal_value, 2),
            "top_keywords": [word for word, _ in keyword_counter.most_common(5)],
        }


class JSONMetricsSource(MetricsSource):
    """Reads auxiliary metrics such as Vapi calls or email counts from JSON files."""

    def __init__(self, path: Path, mapping: dict[str, str]) -> None:
        """Store the JSON path and field mapping."""
        self._path = path
        self._mapping = mapping

    def collect(self, month_start: datetime, month_end: datetime) -> dict:
        """Return zeroed metrics when the file is missing and mapped values when present."""
        if not self._path.exists():
            return {target: 0 for target in self._mapping.values()}
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        return {target: payload.get(source, 0) for source, target in self._mapping.items()}


class UptimeMetricsSource(MetricsSource):
    """Calculates monthly uptime percentage from the uptime JSONL log."""

    def __init__(self, path: Path) -> None:
        """Store the uptime log path."""
        self._path = path

    def collect(self, month_start: datetime, month_end: datetime) -> dict:
        """Return the uptime percentage for the selected month."""
        if not self._path.exists():
            return {"uptime_percentage": 100.0}
        relevant = []
        prefix = month_start.strftime("%Y-%m")
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not str(payload.get("checked_at", "")).startswith(prefix):
                continue
            relevant.append(payload)
        if not relevant:
            return {"uptime_percentage": 100.0}
        healthy = sum(1 for row in relevant if all(check["healthy"] for check in row.get("checks", [])))
        return {"uptime_percentage": round((healthy / len(relevant)) * 100, 2)}


class RecommendationEngine(ABC):
    """Abstract next-step recommendation provider."""

    @abstractmethod
    def generate(self, metrics: MonthlyMetrics) -> list[str]:
        """Return concise next-month recommendations."""


class ClaudeROIRecommendationEngine(RecommendationEngine):
    """Anthropic-backed recommendation engine with deterministic fallback."""

    def __init__(self, api_key: str | None, model: str) -> None:
        """Store Anthropic credentials and model details."""
        self._api_key = api_key
        self._model = model

    def generate(self, metrics: MonthlyMetrics) -> list[str]:
        """Generate short conservative recommendations."""
        if not self._api_key:
            return self._fallback(metrics)
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self._api_key)
            prompt = (
                "You are Genesis AI Systems' monthly client strategist. "
                "Given the metrics below, write three concise recommendations for next month. "
                "Keep them conservative and practical.\n\n"
                f"{metrics}"
            )
            response = client.messages.create(
                model=self._model,
                max_tokens=250,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(getattr(block, "text", "") for block in response.content).strip()
            lines = [line.strip("-• ").strip() for line in text.splitlines() if line.strip()]
            return lines[:3] if lines else self._fallback(metrics)
        except Exception:  # noqa: BLE001
            return self._fallback(metrics)

    @staticmethod
    def _fallback(metrics: MonthlyMetrics) -> list[str]:
        """Return deterministic next-step guidance."""
        return [
            f"Double down on follow-up speed around the {metrics.high_count} HIGH leads generated this month.",
            f"Use messaging around {', '.join(metrics.top_keywords[:3]) or 'top customer concerns'} in next month’s scripts and content.",
            f"Review staffing and escalation coverage so the system maintains at least {metrics.uptime_percentage:.1f}% uptime next month.",
        ]


class PDFBuilder:
    """Builds the monthly ROI PDF report."""

    def __init__(self, business_name: str) -> None:
        """Store the business name for report branding."""
        self._business_name = business_name

    def build(self, metrics: MonthlyMetrics, recommendations: list[str], output_path: Path) -> Path:
        """Generate the monthly ROI PDF and return its path."""
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.shapes import Drawing
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Your AI worked this month so you didn't have to", styles["Title"]),
            Spacer(1, 8),
            Paragraph(f"{self._business_name} Monthly ROI Report", styles["Heading2"]),
            Spacer(1, 12),
        ]

        executive = [
            f"{metrics.total_leads} total leads captured",
            f"{metrics.estimated_time_saved_hours:.1f} hours of estimated time saved",
            f"${metrics.estimated_revenue_generated:,.0f} in conservative revenue influence",
        ]
        for line in executive:
            story.append(Paragraph(f"• {line}", styles["BodyText"]))
            story.append(Spacer(1, 4))

        story.append(Spacer(1, 8))
        story.append(Paragraph("Lead Performance", styles["Heading2"]))
        chart = VerticalBarChart()
        chart.x = 40
        chart.y = 20
        chart.height = 120
        chart.width = 300
        chart.data = [[metrics.high_count, metrics.medium_count, metrics.low_count]]
        chart.categoryAxis.categoryNames = ["High", "Medium", "Low"]
        chart.bars[(0, 0)].fillColor = colors.HexColor("#16a34a")
        chart.bars[(0, 1)].fillColor = colors.HexColor("#f59e0b")
        chart.bars[(0, 2)].fillColor = colors.HexColor("#ef4444")
        drawing = Drawing(360, 160)
        drawing.add(chart)
        story.append(drawing)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Before Genesis AI Systems vs After Genesis AI Systems", styles["Heading2"]))
        comparison = Table(
            [
                ["Metric", "Before Genesis AI Systems", "After Genesis AI Systems"],
                ["Lead handling", "Manual and inconsistent", f"{metrics.total_leads} leads tracked automatically"],
                ["Follow-up", "Delayed or forgotten", f"{metrics.ai_responses_sent} AI responses sent"],
                ["After-hours coverage", "Usually none", f"{metrics.voice_calls_handled} calls handled by AI"],
                ["Reporting", "Manual guesswork", "Monthly ROI report with hard numbers"],
            ],
            colWidths=[140, 170, 190],
        )
        comparison.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(comparison)
        story.append(Spacer(1, 12))

        story.append(Paragraph("System Metrics", styles["Heading2"]))
        metrics_table = Table(
            [
                ["Voice calls handled", str(metrics.voice_calls_handled)],
                ["Automated emails sent", str(metrics.emails_sent)],
                ["System uptime", f"{metrics.uptime_percentage:.2f}%"],
                ["Top themes", ", ".join(metrics.top_keywords) or "No data"],
                ["Investment vs return", f"Retainer paid back through time and revenue leverage"],
            ],
            colWidths=[180, 260],
        )
        metrics_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        story.append(metrics_table)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Next Month Recommendations", styles["Heading2"]))
        for item in recommendations:
            story.append(Paragraph(f"• {item}", styles["BodyText"]))
            story.append(Spacer(1, 4))

        doc.build(story)
        return output_path


class EmailDelivery:
    """Emails the generated ROI report to the client."""

    def __init__(self, config: ROIConfig) -> None:
        """Store SMTP configuration for later delivery."""
        self._config = config

    def send(self, pdf_path: Path) -> None:
        """Send the report email with the PDF attached."""
        message = EmailMessage()
        message["Subject"] = f"{self._config.business_name} Monthly ROI Report"
        message["From"] = f"{self._config.smtp_from_name} <{self._config.smtp_from_email}>"
        message["To"] = self._config.report_to
        message.set_content(
            f"Attached is your monthly Genesis AI Systems ROI report for {self._config.business_name}."
        )
        message.add_attachment(pdf_path.read_bytes(), maintype="application", subtype="pdf", filename=pdf_path.name)
        with smtplib.SMTP_SSL(self._config.smtp_host, self._config.smtp_port) as smtp:
            smtp.login(self._config.smtp_username, self._config.smtp_password)
            smtp.send_message(message)


class GoogleDriveUploader:
    """Uploads the finished PDF to a Google Drive folder when configured."""

    def __init__(self, service_account_json: str, folder_id: str | None) -> None:
        """Store Drive credentials and optional destination folder."""
        self._service_account_json = service_account_json
        self._folder_id = folder_id

    def upload(self, file_path: Path) -> str | None:
        """Upload the PDF to Google Drive and return the file ID when enabled."""
        if not self._folder_id:
            return None
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = _load_service_account_credentials(
            self._service_account_json,
            ["https://www.googleapis.com/auth/drive.file"],
        )
        service = build("drive", "v3", credentials=creds)
        metadata = {"name": file_path.name, "parents": [self._folder_id]}
        media = MediaFileUpload(str(file_path), mimetype="application/pdf")
        created = service.files().create(body=metadata, media_body=media, fields="id").execute()
        return created.get("id")


class ROIReportService:
    """Coordinates metric collection, PDF generation, email delivery, and Drive upload."""

    def __init__(
        self,
        config: ROIConfig,
        sources: list[MetricsSource],
        recommender: RecommendationEngine,
        pdf_builder: PDFBuilder,
        email_delivery: EmailDelivery,
        drive_uploader: GoogleDriveUploader,
    ) -> None:
        """Store injected dependencies for the monthly reporting pipeline."""
        self._config = config
        self._sources = sources
        self._recommender = recommender
        self._pdf_builder = pdf_builder
        self._email_delivery = email_delivery
        self._drive_uploader = drive_uploader

    def run(self, output_dir: Path | None = None) -> Path:
        """Generate, email, and archive the monthly ROI report."""
        output_dir = output_dir or Path.cwd() / "roi_reports"
        month_start, month_end = _previous_month_window()
        merged = {}
        for source in self._sources:
            merged.update(source.collect(month_start, month_end))

        metrics = MonthlyMetrics(
            total_leads=int(merged.get("total_leads", 0)),
            high_count=int(merged.get("high_count", 0)),
            medium_count=int(merged.get("medium_count", 0)),
            low_count=int(merged.get("low_count", 0)),
            ai_responses_sent=int(merged.get("ai_responses_sent", 0)),
            voice_calls_handled=int(merged.get("voice_calls_handled", 0)),
            emails_sent=int(merged.get("emails_sent", 0)),
            estimated_time_saved_hours=float(merged.get("estimated_time_saved_hours", 0.0)),
            estimated_revenue_generated=float(merged.get("estimated_revenue_generated", 0.0)),
            uptime_percentage=float(merged.get("uptime_percentage", 100.0)),
            top_keywords=list(merged.get("top_keywords", [])),
        )
        recommendations = self._recommender.generate(metrics)
        output_path = output_dir / f"roi_report_{month_start.strftime('%Y_%m')}.pdf"
        pdf_path = self._pdf_builder.build(metrics, recommendations, output_path)
        self._email_delivery.send(pdf_path)
        self._drive_uploader.upload(pdf_path)
        return pdf_path


def build_roi_report_service() -> ROIReportService:
    """Build the monthly ROI report service from environment variables."""
    config = ROIConfig.from_env()
    sources = [
        GoogleSheetsMetricsSource(
            spreadsheet_id=config.spreadsheet_id,
            worksheet_name=config.worksheet_name,
            service_account_json=config.service_account_json,
            avg_deal_value=config.avg_deal_value,
        ),
        JSONMetricsSource(config.vapi_metrics_path, {"voice_calls_handled": "voice_calls_handled"}),
        JSONMetricsSource(config.email_metrics_path, {"emails_sent": "emails_sent"}),
        UptimeMetricsSource(config.uptime_log_path),
    ]
    return ROIReportService(
        config=config,
        sources=sources,
        recommender=ClaudeROIRecommendationEngine(config.anthropic_api_key, config.claude_model),
        pdf_builder=PDFBuilder(config.business_name),
        email_delivery=EmailDelivery(config),
        drive_uploader=GoogleDriveUploader(config.service_account_json, config.drive_folder_id),
    )


def _previous_month_window() -> tuple[datetime, datetime]:
    """Return the previous full calendar month window in UTC."""
    now = datetime.now(timezone.utc)
    first_this_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    month_end = first_this_month
    last_day_previous = first_this_month - timedelta(days=1)
    month_start = datetime(last_day_previous.year, last_day_previous.month, 1, tzinfo=timezone.utc)
    return month_start, month_end


def _load_service_account_credentials(raw_json_or_path: str, scopes: list[str]):
    """Load service-account credentials from JSON text or a file path."""
    from google.oauth2.service_account import Credentials

    raw = raw_json_or_path.strip()
    if raw.startswith("{"):
        info = json.loads(raw)
    else:
        info = json.loads(Path(raw).read_text(encoding="utf-8"))
    return Credentials.from_service_account_info(info, scopes=scopes)


def _require_env(name: str) -> str:
    """Read and validate a required environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _parse_timestamp(value: str) -> datetime | None:
    """Parse common timestamp formats from lead sheets."""
    if not value.strip():
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _extract_keywords(message: str) -> list[str]:
    """Extract lightweight keyword candidates from lead messages."""
    words = [word.strip(".,!?").lower() for word in message.split()]
    return [word for word in words if len(word) > 3 and word.isalpha()]


if __name__ == "__main__":
    report = build_roi_report_service().run()
    print(f"ROI report generated: {report}")
