"""Weekly PDF reporting for Genesis AI Systems lead workflows.

The service in this module pulls the last seven days of lead data, computes
business-friendly metrics, generates a branded PDF report, and emails it to
the client. Each class has a single concern so the pipeline is easy to extend.
"""

from __future__ import annotations

import os
import re
import smtplib
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv


@dataclass(frozen=True)
class LeadRecord:
    """Normalized lead row used for weekly analytics."""

    timestamp: datetime
    message: str
    response: str
    score: str


@dataclass(frozen=True)
class WeeklyMetrics:
    """Computed metrics for the report body."""

    total_leads: int
    high_count: int
    medium_count: int
    low_count: int
    response_rate: float
    busiest_day: str
    busiest_hour: str
    top_keywords: list[str]
    top_messages: list[LeadRecord]
    next_week_forecast: int


@dataclass(frozen=True)
class WeeklyReportConfig:
    """Environment-backed report configuration."""

    spreadsheet_id: str
    worksheet_name: str
    service_account_json: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    report_to: str
    from_email: str
    from_name: str
    business_name: str
    claude_model: str
    anthropic_api_key: str | None

    @classmethod
    def from_env(cls) -> "WeeklyReportConfig":
        """Load configuration from environment variables."""
        load_dotenv()
        return cls(
            spreadsheet_id=_require_env("GOOGLE_SHEETS_SPREADSHEET_ID"),
            worksheet_name=os.getenv("GOOGLE_SHEETS_WORKSHEET", "Leads"),
            service_account_json=_require_env("GOOGLE_SERVICE_ACCOUNT_JSON"),
            smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "465")),
            smtp_username=_require_env("SMTP_USERNAME"),
            smtp_password=_require_env("SMTP_PASSWORD"),
            report_to=_require_env("WEEKLY_REPORT_TO"),
            from_email=_require_env("SMTP_FROM_EMAIL"),
            from_name=os.getenv("SMTP_FROM_NAME", "Genesis AI Systems"),
            business_name=os.getenv("BUSINESS_NAME", "Genesis AI Systems Client"),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )


class LeadRepository(ABC):
    """Abstract source for retrieving lead data."""

    @abstractmethod
    def fetch_last_days(self, days: int) -> list[LeadRecord]:
        """Return lead records within the requested date window."""


class RecommendationEngine(ABC):
    """Abstract provider for AI-generated report recommendations."""

    @abstractmethod
    def generate(self, metrics: WeeklyMetrics) -> list[str]:
        """Return a short list of recommended actions."""


class ReportDelivery(ABC):
    """Abstract destination for weekly report delivery."""

    @abstractmethod
    def send(self, subject: str, body: str, pdf_path: Path, recipient: str) -> None:
        """Deliver a PDF report to the intended stakeholder."""


class GoogleSheetsLeadRepository(LeadRepository):
    """Google Sheets-backed implementation for lead retrieval."""

    def __init__(self, spreadsheet_id: str, worksheet_name: str, service_account_json: str) -> None:
        """Store the spreadsheet connection settings."""
        self._spreadsheet_id = spreadsheet_id
        self._worksheet_name = worksheet_name
        self._service_account_json = service_account_json

    def fetch_last_days(self, days: int) -> list[LeadRecord]:
        """Fetch and normalize lead rows from the configured worksheet."""
        import gspread

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = _load_service_account_credentials(self._service_account_json, scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(self._spreadsheet_id).worksheet(self._worksheet_name)
        records = sheet.get_all_records()

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        results: list[LeadRecord] = []
        for record in records:
            timestamp = _parse_timestamp(
                str(record.get("Timestamp") or record.get("timestamp") or "")
            )
            if not timestamp or timestamp < cutoff:
                continue
            results.append(
                LeadRecord(
                    timestamp=timestamp,
                    message=str(record.get("Message") or record.get("message") or ""),
                    response=str(record.get("Response") or record.get("response") or ""),
                    score=str(record.get("Score") or record.get("score") or "LOW").upper(),
                )
            )
        return results


class ClaudeRecommendationEngine(RecommendationEngine):
    """Anthropic-backed recommendation engine for weekly action items."""

    def __init__(self, model: str, api_key: str | None) -> None:
        """Store model settings for later advisory generation."""
        self._model = model
        self._api_key = api_key

    def generate(self, metrics: WeeklyMetrics) -> list[str]:
        """Generate recommendations or fall back to deterministic guidance."""
        if not self._api_key:
            return self._fallback(metrics)

        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self._api_key)
            prompt = (
                "You are a revenue-focused AI operations strategist. "
                "Given the weekly lead metrics below, produce three short recommended actions "
                "for a local business owner. Return each action on its own line.\n\n"
                f"Total leads: {metrics.total_leads}\n"
                f"High: {metrics.high_count}\n"
                f"Medium: {metrics.medium_count}\n"
                f"Low: {metrics.low_count}\n"
                f"Response rate: {metrics.response_rate:.2%}\n"
                f"Busiest day: {metrics.busiest_day}\n"
                f"Busiest hour: {metrics.busiest_hour}\n"
                f"Top keywords: {', '.join(metrics.top_keywords)}"
            )
            response = client.messages.create(
                model=self._model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(getattr(block, "text", "") for block in response.content).strip()
            lines = [line.strip("-• ").strip() for line in text.splitlines() if line.strip()]
            return lines[:3] if lines else self._fallback(metrics)
        except Exception:  # noqa: BLE001
            return self._fallback(metrics)

    @staticmethod
    def _fallback(metrics: WeeklyMetrics) -> list[str]:
        """Return deterministic recommendations when AI is unavailable."""
        recommendations = [
            f"Follow up with all {metrics.high_count} HIGH leads within five minutes during {metrics.busiest_day}.",
            f"Use FAQ automation around {', '.join(metrics.top_keywords[:3]) or 'common questions'} to lift response rate.",
            f"Staff the inbox or phone line more heavily around {metrics.busiest_hour} when lead volume peaks.",
        ]
        return recommendations


class SMTPReportDelivery(ReportDelivery):
    """SMTP-based report delivery with a PDF attachment."""

    def __init__(self, host: str, port: int, username: str, password: str, from_email: str, from_name: str) -> None:
        """Store SMTP configuration for later use."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._from_name = from_name

    def send(self, subject: str, body: str, pdf_path: Path, recipient: str) -> None:
        """Send a weekly report email with the generated PDF attached."""
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{self._from_name} <{self._from_email}>"
        message["To"] = recipient
        message.set_content(body)
        message.add_attachment(
            pdf_path.read_bytes(),
            maintype="application",
            subtype="pdf",
            filename=pdf_path.name,
        )
        with smtplib.SMTP_SSL(self._host, self._port) as smtp:
            smtp.login(self._username, self._password)
            smtp.send_message(message)


class WeeklyMetricsCalculator:
    """Pure business logic for weekly lead analytics."""

    STOPWORDS = {
        "the", "and", "for", "that", "with", "this", "from", "your", "have",
        "need", "want", "would", "about", "please", "today", "hello", "thanks",
    }

    @classmethod
    def calculate(cls, leads: list[LeadRecord]) -> WeeklyMetrics:
        """Aggregate weekly metrics from lead records."""
        total = len(leads)
        high = sum(1 for lead in leads if lead.score == "HIGH")
        medium = sum(1 for lead in leads if lead.score == "MEDIUM")
        low = sum(1 for lead in leads if lead.score == "LOW")
        responded = sum(1 for lead in leads if lead.response.strip())

        by_day: defaultdict[str, int] = defaultdict(int)
        by_hour: defaultdict[int, int] = defaultdict(int)
        keyword_counts: Counter[str] = Counter()
        for lead in leads:
            by_day[lead.timestamp.strftime("%A")] += 1
            by_hour[lead.timestamp.hour] += 1
            keyword_counts.update(cls._extract_keywords(lead.message))

        top_messages = sorted(leads, key=lambda item: (item.score, item.timestamp.isoformat()), reverse=True)[:5]
        busiest_day = max(by_day, key=by_day.get, default="No data")
        busiest_hour_value = max(by_hour, key=by_hour.get, default=None)
        busiest_hour = (
            datetime(2000, 1, 1, busiest_hour_value or 0).strftime("%I:00 %p")
            if busiest_hour_value is not None
            else "No data"
        )
        next_week_forecast = round(total * 1.08) if total else 0

        return WeeklyMetrics(
            total_leads=total,
            high_count=high,
            medium_count=medium,
            low_count=low,
            response_rate=(responded / total) if total else 0.0,
            busiest_day=busiest_day,
            busiest_hour=busiest_hour,
            top_keywords=[word for word, _ in keyword_counts.most_common(5)],
            top_messages=top_messages,
            next_week_forecast=next_week_forecast,
        )

    @classmethod
    def executive_summary(cls, metrics: WeeklyMetrics) -> list[str]:
        """Generate three deterministic executive bullets."""
        return [
            f"{metrics.total_leads} total leads were handled this week, including {metrics.high_count} high-priority opportunities.",
            f"The AI response rate was {metrics.response_rate:.0%}, with peak activity on {metrics.busiest_day} around {metrics.busiest_hour}.",
            f"Lead intent centered on {', '.join(metrics.top_keywords[:3]) or 'repeat service questions'}, suggesting clear follow-up themes for next week.",
        ]

    @classmethod
    def _extract_keywords(cls, message: str) -> list[str]:
        """Extract simple report-friendly keywords from lead text."""
        candidates = re.findall(r"[A-Za-z']{4,}", message.lower())
        return [item for item in candidates if item not in cls.STOPWORDS]


class WeeklyPDFBuilder:
    """Builds a polished weekly PDF report using ReportLab."""

    def __init__(self, business_name: str) -> None:
        """Store branding text for report headers."""
        self._business_name = business_name

    def build(self, metrics: WeeklyMetrics, recommendations: list[str], output_path: Path) -> Path:
        """Generate the PDF report and return its path."""
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"{self._business_name} Weekly AI Report", styles["Title"]))
        story.append(Spacer(1, 12))

        for bullet in WeeklyMetricsCalculator.executive_summary(metrics):
            story.append(Paragraph(f"• {bullet}", styles["BodyText"]))
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 8))
        story.append(Paragraph("Lead Volume Chart", styles["Heading2"]))
        story.append(self._build_volume_chart(metrics))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Lead Score Distribution", styles["Heading2"]))
        story.append(self._build_score_chart(metrics))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Top Lead Messages", styles["Heading2"]))
        top_message_rows = [["Timestamp", "Score", "Message"]]
        for lead in metrics.top_messages:
            top_message_rows.append(
                [
                    lead.timestamp.strftime("%m/%d %I:%M %p"),
                    lead.score,
                    (lead.message[:80] + "...") if len(lead.message) > 80 else lead.message,
                ]
            )
        top_table = Table(top_message_rows, colWidths=[90, 70, 340])
        top_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(top_table)
        story.append(Spacer(1, 12))

        story.append(Paragraph("AI Performance Metrics", styles["Heading2"]))
        metrics_table = Table(
            [
                ["Response rate", f"{metrics.response_rate:.0%}"],
                ["Busiest day", metrics.busiest_day],
                ["Busiest hour", metrics.busiest_hour],
                ["Top keywords", ", ".join(metrics.top_keywords) or "No data"],
                ["Next week forecast", str(metrics.next_week_forecast)],
            ],
            colWidths=[160, 340],
        )
        metrics_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e2e8f0")),
                ]
            )
        )
        story.append(metrics_table)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Recommended Actions", styles["Heading2"]))
        for item in recommendations:
            story.append(Paragraph(f"• {item}", styles["BodyText"]))
            story.append(Spacer(1, 4))

        doc.build(story)
        return output_path

    def _build_volume_chart(self, metrics: WeeklyMetrics):
        """Create a simple bar chart drawing for the PDF."""
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.shapes import Drawing
        from reportlab.lib import colors

        drawing = Drawing(460, 180)
        chart = VerticalBarChart()
        chart.x = 40
        chart.y = 30
        chart.height = 120
        chart.width = 360
        chart.data = [[metrics.high_count, metrics.medium_count, metrics.low_count]]
        chart.categoryAxis.categoryNames = ["High", "Medium", "Low"]
        chart.bars[0].fillColor = None
        chart.bars[0].strokeColor = None
        chart.bars[(0, 0)].fillColor = colors.HexColor("#16a34a")
        chart.bars[(0, 1)].fillColor = colors.HexColor("#f59e0b")
        chart.bars[(0, 2)].fillColor = colors.HexColor("#ef4444")
        drawing.add(chart)
        return drawing

    def _build_score_chart(self, metrics: WeeklyMetrics):
        """Create a pie chart showing the lead score mix."""
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.lib import colors

        drawing = Drawing(460, 180)
        pie = Pie()
        pie.x = 85
        pie.y = 15
        pie.width = 140
        pie.height = 140
        pie.data = [metrics.high_count or 1, metrics.medium_count or 1, metrics.low_count or 1]
        pie.labels = ["High", "Medium", "Low"]
        pie.slices[0].fillColor = colors.HexColor("#16a34a")
        pie.slices[1].fillColor = colors.HexColor("#f59e0b")
        pie.slices[2].fillColor = colors.HexColor("#ef4444")
        drawing.add(pie)
        drawing.add(String(255, 120, f"Total leads: {metrics.total_leads}", fontSize=12))
        return drawing


class WeeklyReportService:
    """High-level orchestration for building and emailing weekly reports."""

    def __init__(
        self,
        repository: LeadRepository,
        calculator: WeeklyMetricsCalculator,
        recommender: RecommendationEngine,
        pdf_builder: WeeklyPDFBuilder,
        delivery: ReportDelivery,
        config: WeeklyReportConfig,
    ) -> None:
        """Store injected dependencies for end-to-end report generation."""
        self._repository = repository
        self._calculator = calculator
        self._recommender = recommender
        self._pdf_builder = pdf_builder
        self._delivery = delivery
        self._config = config

    def run(self, output_dir: Path | None = None) -> Path:
        """Generate and deliver the weekly report PDF."""
        output_dir = output_dir or Path.cwd() / "reports"
        leads = self._repository.fetch_last_days(days=7)
        metrics = self._calculator.calculate(leads)
        recommendations = self._recommender.generate(metrics)
        output_path = output_dir / f"weekly_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf_path = self._pdf_builder.build(metrics, recommendations, output_path)
        email_body = (
            f"Attached is your weekly Genesis AI Systems report for {self._config.business_name}.\n\n"
            f"This week's headline numbers: {metrics.total_leads} leads, "
            f"{metrics.high_count} high-priority leads, and a {metrics.response_rate:.0%} response rate."
        )
        self._delivery.send(
            subject=f"{self._config.business_name} Weekly AI Report",
            body=email_body,
            pdf_path=pdf_path,
            recipient=self._config.report_to,
        )
        return pdf_path


def build_weekly_report_service() -> WeeklyReportService:
    """Assemble the full report pipeline from environment variables."""
    config = WeeklyReportConfig.from_env()
    repository = GoogleSheetsLeadRepository(
        spreadsheet_id=config.spreadsheet_id,
        worksheet_name=config.worksheet_name,
        service_account_json=config.service_account_json,
    )
    recommender = ClaudeRecommendationEngine(
        model=config.claude_model,
        api_key=config.anthropic_api_key,
    )
    pdf_builder = WeeklyPDFBuilder(config.business_name)
    delivery = SMTPReportDelivery(
        host=config.smtp_host,
        port=config.smtp_port,
        username=config.smtp_username,
        password=config.smtp_password,
        from_email=config.from_email,
        from_name=config.from_name,
    )
    return WeeklyReportService(
        repository=repository,
        calculator=WeeklyMetricsCalculator(),
        recommender=recommender,
        pdf_builder=pdf_builder,
        delivery=delivery,
        config=config,
    )


def _load_service_account_credentials(raw_json_or_path: str, scopes: Iterable[str]):
    """Load service-account credentials from JSON text or a file path."""
    import json
    from google.oauth2.service_account import Credentials

    raw = raw_json_or_path.strip()
    if raw.startswith("{"):
        data = json.loads(raw)
    else:
        data = json.loads(Path(raw).read_text(encoding="utf-8"))
    return Credentials.from_service_account_info(data, scopes=list(scopes))


def _require_env(name: str) -> str:
    """Read and validate a required environment variable."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _parse_timestamp(value: str) -> datetime | None:
    """Parse a timestamp from common worksheet formats."""
    if not value.strip():
        return None

    candidates = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in candidates:
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


if __name__ == "__main__":
    service = build_weekly_report_service()
    report = service.run()
    print(f"Weekly report generated: {report}")
