"""Environment-driven configuration for the Project 8 agent system."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return int(value.strip())


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    claude_model: str
    crewai_model: str
    target_repo_path: Path
    google_service_account_json: str | None
    google_sheets_spreadsheet_id: str | None
    google_sheets_worksheet: str
    github_token: str | None
    github_repository: str | None
    github_default_branch: str
    deploy_workflow_file: str
    gmail_smtp_username: str | None
    gmail_smtp_password: str | None
    gmail_to: str | None
    webhook_urls: list[str]
    openai_changelog_rss_url: str
    anthropic_changelog_rss_url: str
    semgrep_config: str
    allow_auto_fix_low: bool
    allow_auto_deploy: bool
    evolution_auto_apply: bool
    deploy_poll_seconds: int
    deploy_timeout_minutes: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        webhook_raw = os.getenv("WEBHOOK_URLS", "").strip()
        return cls(
            anthropic_api_key=_require("ANTHROPIC_API_KEY"),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            crewai_model=os.getenv(
                "CREWAI_MODEL", "anthropic/claude-3-5-sonnet-20241022"
            ),
            target_repo_path=Path(_require("TARGET_REPO_PATH")).expanduser().resolve(),
            google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"),
            google_sheets_spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"),
            google_sheets_worksheet=os.getenv(
                "GOOGLE_SHEETS_WORKSHEET", "Project8Runs"
            ),
            github_token=os.getenv("GITHUB_TOKEN"),
            github_repository=os.getenv("GITHUB_REPOSITORY"),
            github_default_branch=os.getenv("GITHUB_DEFAULT_BRANCH", "main"),
            deploy_workflow_file=os.getenv("DEPLOY_WORKFLOW_FILE", "agent_system.yml"),
            gmail_smtp_username=os.getenv("GMAIL_SMTP_USERNAME"),
            gmail_smtp_password=os.getenv("GMAIL_SMTP_PASSWORD"),
            gmail_to=os.getenv("GMAIL_TO"),
            webhook_urls=[item.strip() for item in webhook_raw.split(",") if item.strip()],
            openai_changelog_rss_url=os.getenv(
                "OPENAI_CHANGELOG_RSS_URL", "https://openai.com/news/rss.xml"
            ),
            anthropic_changelog_rss_url=os.getenv(
                "ANTHROPIC_CHANGELOG_RSS_URL", "https://www.anthropic.com/news/rss.xml"
            ),
            semgrep_config=os.getenv("SEMGREP_CONFIG", "auto"),
            allow_auto_fix_low=_bool("ALLOW_AUTO_FIX_LOW", True),
            allow_auto_deploy=_bool("ALLOW_AUTO_DEPLOY", False),
            evolution_auto_apply=_bool("EVOLUTION_AUTO_APPLY", False),
            deploy_poll_seconds=_int("DEPLOY_POLL_SECONDS", 20),
            deploy_timeout_minutes=_int("DEPLOY_TIMEOUT_MINUTES", 20),
        )
