"""
Training data validation for Project 6.

This module has a single responsibility: validate JSONL training data before it
is uploaded. It does not know about APIs, orchestration, or inference.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class ValidationError(ValueError):
    """Raised when the training dataset fails validation."""


class TrainingDataValidator:
    """Validate fine-tuning datasets against expected message structure."""

    REQUIRED_ROLES = ("system", "user", "assistant")

    def __init__(self, minimum_examples: int = 10) -> None:
        self._minimum_examples = minimum_examples

    def validate(self, training_file: Path) -> None:
        """Validate file existence, example count, and message role ordering."""
        if not training_file.exists():
            raise ValidationError(f"Training file not found: {training_file}")

        if training_file.suffix.lower() != ".jsonl":
            raise ValidationError(
                f"Training file must be a .jsonl file, received: {training_file.name}"
            )

        examples = 0
        with training_file.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue

                examples += 1
                payload = self._parse_json_line(line, line_number)
                self._validate_example(payload, line_number)

        if examples < self._minimum_examples:
            raise ValidationError(
                f"Expected at least {self._minimum_examples} training examples, "
                f"found {examples}."
            )

    def _parse_json_line(self, line: str, line_number: int) -> dict[str, Any]:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(
                f"Line {line_number}: invalid JSON - {exc.msg}."
            ) from exc

        if not isinstance(payload, dict):
            raise ValidationError(f"Line {line_number}: each JSONL row must be an object.")

        return payload

    def _validate_example(self, payload: dict[str, Any], line_number: int) -> None:
        messages = payload.get("messages")
        if not isinstance(messages, list):
            raise ValidationError(
                f"Line {line_number}: missing 'messages' list."
            )

        if len(messages) < len(self.REQUIRED_ROLES):
            raise ValidationError(
                f"Line {line_number}: each example must contain at least "
                f"{len(self.REQUIRED_ROLES)} messages."
            )

        roles = []
        for index, expected_role in enumerate(self.REQUIRED_ROLES):
            message = messages[index]
            if not isinstance(message, dict):
                raise ValidationError(
                    f"Line {line_number}: message {index + 1} must be an object."
                )

            role = message.get("role")
            content = message.get("content")
            roles.append(role)

            if role != expected_role:
                raise ValidationError(
                    f"Line {line_number}: expected roles "
                    f"{list(self.REQUIRED_ROLES)}, found {roles}."
                )

            if not isinstance(content, str) or not content.strip():
                raise ValidationError(
                    f"Line {line_number}: message {index + 1} content must be a "
                    "non-empty string."
                )


def _resolve_training_file() -> Path:
    """Resolve the training file path for command-line validation."""
    load_dotenv()
    project_root = Path(__file__).resolve().parent
    training_file = Path(os.getenv("TRAINING_FILE", "training_data.jsonl"))
    if not training_file.is_absolute():
        training_file = project_root / training_file
    return training_file


def main() -> int:
    """Run validation from the command line."""
    try:
        training_file = _resolve_training_file()
        validator = TrainingDataValidator(minimum_examples=10)
        validator.validate(training_file)
        print(f"Validation passed for: {training_file}")
        return 0
    except ValidationError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
