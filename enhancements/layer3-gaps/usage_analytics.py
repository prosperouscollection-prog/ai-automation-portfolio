"""Usage analytics and pricing protection for Genesis AI Systems retainers.

The goal of this module is to track actual client consumption, estimate cost,
flag margin risk, and generate clear overage language before usage turns into
an unprofitable surprise.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class UsageSnapshot:
    """One usage event or daily aggregate for a client."""

    client_id: str
    recorded_at: str
    api_calls: int = 0
    tokens_used: int = 0
    leads_processed: int = 0
    voice_minutes: float = 0.0
    emails_sent: int = 0


@dataclass(frozen=True)
class ClientPlan:
    """Commercial limits and included usage for one client."""

    client_id: str
    monthly_retainer: float
    included_api_calls: int
    included_tokens: int
    included_voice_minutes: float
    included_emails: int
    api_call_overage_rate: float
    token_overage_rate_per_1k: float
    voice_minute_overage_rate: float
    email_overage_rate: float


@dataclass(frozen=True)
class OverageSummary:
    """Calculated usage totals, estimated cost, and overage charges."""

    client_id: str
    total_api_calls: int
    total_tokens: int
    total_voice_minutes: float
    total_emails: int
    estimated_variable_cost: float
    overage_amount: float
    over_limit: bool


class UsageRepository(ABC):
    """Abstract storage for usage snapshots."""

    @abstractmethod
    def append(self, snapshot: UsageSnapshot) -> None:
        """Persist a usage snapshot."""

    @abstractmethod
    def list_for_month(self, client_id: str, year: int, month: int) -> list[UsageSnapshot]:
        """Return snapshots for the given client and month."""


class JSONUsageRepository(UsageRepository):
    """JSON-backed repository for small-agency usage analytics."""

    def __init__(self, path: Path) -> None:
        """Store the JSON file path and initialize it if needed."""
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("[]", encoding="utf-8")

    def append(self, snapshot: UsageSnapshot) -> None:
        """Append a new snapshot to the JSON list."""
        existing = self._read_all()
        existing.append(asdict(snapshot))
        self._path.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    def list_for_month(self, client_id: str, year: int, month: int) -> list[UsageSnapshot]:
        """Filter snapshots for one client and month."""
        prefix = f"{year:04d}-{month:02d}"
        return [
            UsageSnapshot(**row)
            for row in self._read_all()
            if row["client_id"] == client_id and str(row["recorded_at"]).startswith(prefix)
        ]

    def _read_all(self) -> list[dict]:
        """Read raw usage rows from disk."""
        return json.loads(self._path.read_text(encoding="utf-8"))


class UsageCalculator:
    """Pure pricing logic for usage analytics."""

    @staticmethod
    def summarize(plan: ClientPlan, snapshots: list[UsageSnapshot]) -> OverageSummary:
        """Summarize usage totals and compute overage exposure."""
        total_api_calls = sum(item.api_calls for item in snapshots)
        total_tokens = sum(item.tokens_used for item in snapshots)
        total_voice_minutes = round(sum(item.voice_minutes for item in snapshots), 2)
        total_emails = sum(item.emails_sent for item in snapshots)

        overage_amount = 0.0
        if total_api_calls > plan.included_api_calls:
            overage_amount += (total_api_calls - plan.included_api_calls) * plan.api_call_overage_rate
        if total_tokens > plan.included_tokens:
            overage_amount += (
                (total_tokens - plan.included_tokens) / 1000.0
            ) * plan.token_overage_rate_per_1k
        if total_voice_minutes > plan.included_voice_minutes:
            overage_amount += (
                total_voice_minutes - plan.included_voice_minutes
            ) * plan.voice_minute_overage_rate
        if total_emails > plan.included_emails:
            overage_amount += (total_emails - plan.included_emails) * plan.email_overage_rate

        estimated_variable_cost = round(
            (total_tokens / 1000.0) * 0.008 + total_voice_minutes * 0.06 + total_emails * 0.002,
            2,
        )
        return OverageSummary(
            client_id=plan.client_id,
            total_api_calls=total_api_calls,
            total_tokens=total_tokens,
            total_voice_minutes=total_voice_minutes,
            total_emails=total_emails,
            estimated_variable_cost=estimated_variable_cost,
            overage_amount=round(overage_amount, 2),
            over_limit=overage_amount > 0,
        )


class InvoiceAddendumGenerator:
    """Renders a client-facing usage overage summary."""

    @staticmethod
    def render(summary: OverageSummary) -> str:
        """Return markdown-friendly invoice addendum text."""
        return (
            f"# Usage Invoice Addendum - {summary.client_id}\n\n"
            f"- Total API calls: {summary.total_api_calls}\n"
            f"- Total tokens: {summary.total_tokens}\n"
            f"- Total voice minutes: {summary.total_voice_minutes}\n"
            f"- Total automated emails: {summary.total_emails}\n"
            f"- Estimated variable cost: ${summary.estimated_variable_cost:.2f}\n"
            f"- Overage due: ${summary.overage_amount:.2f}\n"
        )


class UsageAnalyticsService:
    """High-level entrypoint for recording usage and checking margins."""

    def __init__(self, repository: UsageRepository) -> None:
        """Store the injected repository implementation."""
        self._repository = repository

    def record_usage(self, snapshot: UsageSnapshot) -> None:
        """Persist one usage snapshot."""
        self._repository.append(snapshot)

    def monthly_summary(self, plan: ClientPlan, year: int, month: int) -> OverageSummary:
        """Return one client's overage summary for the selected month."""
        snapshots = self._repository.list_for_month(plan.client_id, year, month)
        return UsageCalculator.summarize(plan, snapshots)


def build_usage_service() -> UsageAnalyticsService:
    """Build the usage analytics service from environment variables."""
    load_dotenv()
    repository_path = Path(os.getenv("USAGE_REPOSITORY_PATH", "./usage_analytics.json")).expanduser()
    return UsageAnalyticsService(JSONUsageRepository(repository_path))


if __name__ == "__main__":
    service = build_usage_service()
    demo_snapshot = UsageSnapshot(
        client_id="smile-dental",
        recorded_at=datetime.now(timezone.utc).isoformat(),
        api_calls=120,
        tokens_used=42000,
        leads_processed=17,
        voice_minutes=23.5,
        emails_sent=14,
    )
    service.record_usage(demo_snapshot)
    print("Usage snapshot recorded.")
