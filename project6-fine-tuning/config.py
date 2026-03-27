"""
Configuration layer for Project 6.

This module follows SOLID by isolating environment-driven configuration in one
place. The rest of the application depends on the AppConfig abstraction instead
of reading environment variables directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _require_env(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(
            f"Missing required environment variable: {name}. "
            "Add it to your environment or .env file."
        )
    return value


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration loaded from environment variables."""

    openai_api_key: str
    base_model: str
    training_file: Path
    system_prompt: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables and an optional .env file."""
        load_dotenv()

        project_root = Path(__file__).resolve().parent
        training_file_raw = _require_env("TRAINING_FILE")
        training_file = Path(training_file_raw)
        if not training_file.is_absolute():
            training_file = project_root / training_file

        return cls(
            openai_api_key=_require_env("OPENAI_API_KEY"),
            base_model=_require_env("BASE_MODEL"),
            training_file=training_file,
            system_prompt=_require_env("SYSTEM_PROMPT"),
        )
