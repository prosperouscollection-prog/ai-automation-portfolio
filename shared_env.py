from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parent
LOCAL_ENV_PATH = REPO_ROOT / ".env.local"
LOCAL_ENV_EXAMPLE_PATH = REPO_ROOT / ".env.local.example"
EXPECTED_SECRET_KEYS = (
    "ALERT_PHONE_NUMBER",
    "ANTHROPIC_API_KEY",
    "APOLLO_API_KEY",
    "BUSINESS_MAILING_ADDRESS",
    "BUSINESS_PHONE_NUMBER",
    "CALENDLY_ORG_URL",
    "CALENDLY_TOKEN",
    "CALENDLY_URL",
    "DEMO_SERVER_URL",
    "GOOGLE_SERVICE_ACCOUNT",
    "GOOGLE_SHEET_ID",
    "HUBSPOT_ACCESS_TOKEN",
    "HUNTER_API_KEY",
    "NOTIFICATION_EMAIL",
    "OPENAI_ACCOUNT_BALANCE",
    "OPENAI_API_KEY",
    "OUTSCRAPER_API_KEY",
    "PROJECT9_BUSINESS_MAILING_ADDRESS",
    "RESEND_API_KEY",
    "SENDGRID_FROM_EMAIL",
    "SENDGRID_FROM_NAME",
    "SITE_URL",
    "STRIPE_DEPOSIT_LINK",
    "STRIPE_FULLSTACK_LINK",
    "STRIPE_GROWTH_LINK",
    "STRIPE_SECRET_KEY",
    "STRIPE_STARTER_LINK",
    "STRIPE_WEBHOOK_SECRET",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "VAPI_PUBLIC_KEY",
    "YELP_API_KEY",
)

_BOOTSTRAPPED = False


def bootstrap_env() -> None:
    """Load local developer secrets without disturbing CI/Actions env vars."""

    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return

    if LOCAL_ENV_PATH.exists():
        load_dotenv(LOCAL_ENV_PATH, override=False)

    fallback_env = REPO_ROOT / ".env"
    if fallback_env.exists():
        load_dotenv(fallback_env, override=False)

    _BOOTSTRAPPED = True


@lru_cache(maxsize=None)
def getenv(key: str, default: Any = "") -> str:
    bootstrap_env()
    value = os.getenv(key, default)
    if value is None:
        return ""
    return str(value).strip()


def require_env(key: str) -> str:
    value = getenv(key)
    if not value:
        raise RuntimeError(f"{key} is required")
    return value
