"""Google Sheets run logging."""

from __future__ import annotations

import json
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from agent_system.config import Settings
from agent_system.models import RunSummary


class GoogleSheetsRunLogger:
    """Append run summaries to Google Sheets when configured."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def log_run(self, summary: RunSummary) -> None:
        if not self._settings.google_service_account_json or not self._settings.google_sheets_spreadsheet_id:
            return
        try:
            client = self._build_client()
            workbook = client.open_by_key(self._settings.google_sheets_spreadsheet_id)
            worksheet = workbook.worksheet(self._settings.google_sheets_worksheet)
            worksheet.append_row(
                [
                    summary.started_at,
                    summary.source,
                    summary.security_result.status,
                    summary.qa_result.status,
                    summary.evolution_result.status,
                    summary.deploy_result.status,
                    summary.security_result.summary,
                    summary.qa_result.summary,
                    summary.evolution_result.summary,
                    summary.deploy_result.summary,
                    summary.crew_summary,
                    json.dumps(summary.deploy_result.metadata),
                ]
            )
        except Exception:
            return

    def _build_client(self) -> gspread.Client:
        raw = self._settings.google_service_account_json or ""
        if raw.strip().startswith("{"):
            creds_info = json.loads(raw)
        else:
            creds_info = json.loads(Path(raw).read_text(encoding="utf-8"))
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return gspread.authorize(credentials)
