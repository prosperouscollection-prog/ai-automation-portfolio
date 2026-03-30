#!/usr/bin/env python3
"""Genesis AI Systems auto prompt deployer utilities."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Iterable

import openai
import requests
import tiktoken
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

try:
    import resend
except ImportError:  # pragma: no cover - handled at runtime
    resend = None


@dataclass(frozen=True)
class StructuredFile:
    """Represents one file returned by the structured model response."""

    path: str
    content: str


@dataclass(frozen=True)
class StructuredPromptResponse:
    """Holds the parsed JSON payload returned by the model."""

    files: list[StructuredFile]
    summary: str


@dataclass(frozen=True)
class ManifestFile:
    """Represents one target file requested by a large prompt."""

    path: str
    purpose: str


@dataclass(frozen=True)
class PromptManifest:
    """Holds a file-generation manifest extracted from a large prompt."""

    files: list[ManifestFile]
    summary: str


@dataclass(frozen=True)
class FileWriteRecord:
    """Captures metadata for a single file written to disk."""

    path: Path
    bytes_written: int
    line_count: int


@dataclass(frozen=True)
class FileWriteReport:
    """Summarizes a batch of file writes."""

    records: list[FileWriteRecord]
    skipped_paths: list[str]

    @property
    def written_files(self) -> list[Path]:
        """Return written file paths in order."""
        return [record.path for record in self.records]

    @property
    def file_count(self) -> int:
        """Return the number of files written."""
        return len(self.records)

    @property
    def total_bytes(self) -> int:
        """Return the total number of bytes written."""
        return sum(record.bytes_written for record in self.records)


@dataclass
class PromptUsage:
    """Captures token usage and estimated cost for a single prompt."""

    prompt_name: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    total_tokens: int
    cost_usd: float


class BasePromptRunner(ABC):
    """Defines the contract for prompt runners."""

    @abstractmethod
    def run(self, prompt_path: str) -> dict[str, Any]:
        """Run a prompt file and return a structured result."""

    @abstractmethod
    def estimate_tokens(self, prompt: str) -> int:
        """Estimate token usage for the provided prompt."""

    @abstractmethod
    def verify_output(self, files: list[Path]) -> bool:
        """Verify that model-written files exist and are not empty."""


class TokenCounter:
    """Counts prompt tokens and records estimates for each prompt run."""

    def __init__(self, model: str, log_path: Path) -> None:
        """Initialize the token counter for a specific model."""
        self.model = model
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count(self, prompt: str) -> int:
        """Return the token count for a prompt string."""
        return len(self.encoding.encode(prompt))

    def warn_if_large(self, tokens: int, console: Console) -> None:
        """Warn if the prompt is approaching the configured context limit."""
        if tokens > 900_000:
            console.print(
                f"[bold yellow]Warning:[/bold yellow] estimated prompt size is {tokens:,} "
                "tokens and is approaching the 1M-token target."
            )

    def log_usage(self, prompt_name: str, tokens: int) -> None:
        """Append a token estimate entry to disk."""
        record = {
            "timestamp": _utc_timestamp(),
            "prompt_name": prompt_name,
            "estimated_tokens": tokens,
            "model": self.model,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")


class FileWriter:
    """Validates file paths and writes structured model output atomically."""

    ALLOWED_EMPTY_FILENAMES = {".nojekyll", ".gitkeep", ".keep"}

    def __init__(self, portfolio_dir: Path, log_path: Path, console: Console) -> None:
        """Initialize the writer with workspace boundaries and logging."""
        self.portfolio_dir = portfolio_dir.resolve()
        self.log_path = log_path
        self.console = console
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write_files(self, files: Iterable[StructuredFile]) -> FileWriteReport:
        """Write all structured file payloads to disk and report the result."""
        records: list[FileWriteRecord] = []
        skipped_paths: list[str] = []

        for file_obj in files:
            resolved_path = self._resolve_path(file_obj.path)
            if resolved_path is None:
                skipped_paths.append(file_obj.path)
                self.console.print(
                    f"[yellow]Skipping invalid path:[/yellow] {file_obj.path}"
                )
                self._log_file_skip(file_obj.path)
                continue

            self._atomic_write(resolved_path, file_obj.content)
            if not resolved_path.exists():
                raise OSError(f"Failed to write file: {resolved_path}")

            bytes_written = resolved_path.stat().st_size
            line_count = _count_lines(file_obj.content)
            record = FileWriteRecord(
                path=resolved_path,
                bytes_written=bytes_written,
                line_count=line_count,
            )
            records.append(record)
            self._log_file_write(record)
            self.console.print(f"✅ Created: {resolved_path.name} ({line_count} lines)")

        return FileWriteReport(records=records, skipped_paths=skipped_paths)

    def verify_files(self, files: Iterable[Path]) -> bool:
        """Verify that each file exists and contains content."""
        file_list = list(files)
        return bool(file_list) and all(
            path.exists()
            and (
                path.stat().st_size > 0
                or path.name in self.ALLOWED_EMPTY_FILENAMES
            )
            for path in file_list
        )

    def _resolve_path(self, raw_path: str) -> Path | None:
        """Resolve a model-provided path inside the portfolio workspace."""
        if not raw_path or not os.path.isabs(raw_path):
            return None

        try:
            resolved_path = Path(raw_path).expanduser().resolve()
        except OSError:
            return None

        if self.portfolio_dir not in [resolved_path, *resolved_path.parents]:
            return None
        return resolved_path

    def _atomic_write(self, path: Path, content: str) -> None:
        """Write file contents atomically to avoid partial writes."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
            newline="",
        ) as temp_handle:
            temp_handle.write(content)
            temp_path = Path(temp_handle.name)
        temp_path.replace(path)

    def _log_file_write(self, record: FileWriteRecord) -> None:
        """Append a file write record to disk."""
        payload = {
            "timestamp": _utc_timestamp(),
            "path": str(record.path),
            "bytes": record.bytes_written,
            "lines": record.line_count,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def _log_file_skip(self, raw_path: str) -> None:
        """Append an invalid-path warning to disk."""
        record = {
            "timestamp": _utc_timestamp(),
            "path": raw_path,
            "status": "skipped_invalid_path",
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")


class StructuredResponseParser:
    """Parses and validates the model's structured JSON response."""

    def __init__(self, raw_log_path: Path) -> None:
        """Initialize the parser with a raw-response log destination."""
        self.raw_log_path = raw_log_path
        self.raw_log_path.parent.mkdir(parents=True, exist_ok=True)

    def parse_response(
        self,
        response_text: str,
        prompt_name: str,
    ) -> StructuredPromptResponse:
        """Parse a JSON response and validate the required schema fields."""
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as exc:
            self.log_raw_response(
                prompt_name=prompt_name,
                response_text=response_text,
                error=f"JSON parsing failed: {exc}",
            )
            raise ValueError(f"Failed to parse JSON response for {prompt_name}: {exc}") from exc

        if not isinstance(data, dict):
            self.log_raw_response(
                prompt_name=prompt_name,
                response_text=response_text,
                error="Response root must be a JSON object.",
            )
            raise ValueError(f"Structured response for {prompt_name} was not a JSON object.")

        files_value = data.get("files")
        summary_value = data.get("summary")

        if not isinstance(files_value, list):
            self.log_raw_response(
                prompt_name=prompt_name,
                response_text=response_text,
                error="Response 'files' field was missing or not an array.",
            )
            raise ValueError(f"Structured response for {prompt_name} did not include a valid files array.")

        if not isinstance(summary_value, str):
            self.log_raw_response(
                prompt_name=prompt_name,
                response_text=response_text,
                error="Response 'summary' field was missing or not a string.",
            )
            raise ValueError(f"Structured response for {prompt_name} did not include a valid summary.")

        files: list[StructuredFile] = []
        for index, file_value in enumerate(files_value):
            if not isinstance(file_value, dict):
                error = f"File entry {index} for {prompt_name} was not an object."
                self.log_raw_response(
                    prompt_name=prompt_name,
                    response_text=response_text,
                    error=error,
                )
                raise ValueError(error)

            path_value = file_value.get("path")
            content_value = file_value.get("content")
            if not isinstance(path_value, str) or not isinstance(content_value, str):
                error = (
                    f"File entry {index} for {prompt_name} must include string path and "
                    "content values."
                )
                self.log_raw_response(
                    prompt_name=prompt_name,
                    response_text=response_text,
                    error=error,
                )
                raise ValueError(error)
            files.append(StructuredFile(path=path_value, content=content_value))

        return StructuredPromptResponse(files=files, summary=summary_value)

    def log_raw_response(self, prompt_name: str, response_text: str, error: str) -> None:
        """Persist raw model output for postmortem debugging."""
        record = {
            "timestamp": _utc_timestamp(),
            "prompt_name": prompt_name,
            "error": error,
            "response_length_chars": len(response_text),
            "response_text": response_text,
        }
        with self.raw_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")


class ManifestResponseParser:
    """Parses and validates the model's file manifest response."""

    def __init__(self, raw_log_path: Path) -> None:
        """Initialize the parser with the shared raw-response log."""
        self.raw_log_path = raw_log_path
        self.raw_log_path.parent.mkdir(parents=True, exist_ok=True)

    def parse_response(self, response_text: str, prompt_name: str) -> PromptManifest:
        """Parse a manifest JSON payload and validate the required fields."""
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as exc:
            self._log_raw_response(
                prompt_name=prompt_name,
                response_text=response_text,
                error=f"Manifest JSON parsing failed: {exc}",
            )
            raise ValueError(f"Failed to parse manifest for {prompt_name}: {exc}") from exc

        if not isinstance(data, dict):
            self._log_raw_response(
                prompt_name=prompt_name,
                response_text=response_text,
                error="Manifest root must be a JSON object.",
            )
            raise ValueError(f"Manifest for {prompt_name} was not a JSON object.")

        files_value = data.get("files")
        summary_value = data.get("summary")
        if not isinstance(files_value, list):
            self._log_raw_response(
                prompt_name=prompt_name,
                response_text=response_text,
                error="Manifest 'files' field was missing or not an array.",
            )
            raise ValueError(f"Manifest for {prompt_name} did not include a valid files array.")

        if not isinstance(summary_value, str):
            self._log_raw_response(
                prompt_name=prompt_name,
                response_text=response_text,
                error="Manifest 'summary' field was missing or not a string.",
            )
            raise ValueError(f"Manifest for {prompt_name} did not include a valid summary.")

        manifest_files: list[ManifestFile] = []
        seen_paths: set[str] = set()
        for index, item in enumerate(files_value):
            if not isinstance(item, dict):
                raise ValueError(f"Manifest file entry {index} for {prompt_name} was not an object.")
            path_value = item.get("path")
            purpose_value = item.get("purpose")
            if not isinstance(path_value, str) or not isinstance(purpose_value, str):
                raise ValueError(
                    f"Manifest file entry {index} for {prompt_name} must include string path and purpose values."
                )
            if path_value in seen_paths:
                continue
            seen_paths.add(path_value)
            manifest_files.append(ManifestFile(path=path_value, purpose=purpose_value))

        if not manifest_files:
            self._log_raw_response(
                prompt_name=prompt_name,
                response_text=response_text,
                error="Manifest contained zero files.",
            )
            raise ValueError(f"Manifest for {prompt_name} did not contain any files.")

        return PromptManifest(files=manifest_files, summary=summary_value)

    def _log_raw_response(self, prompt_name: str, response_text: str, error: str) -> None:
        """Persist invalid manifest responses for debugging."""
        record = {
            "timestamp": _utc_timestamp(),
            "prompt_name": prompt_name,
            "error": error,
            "response_length_chars": len(response_text),
            "response_text": response_text,
        }
        with self.raw_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

class CostTracker:
    """Tracks balance, estimated costs, and actual usage for prompt runs."""

    DEFAULT_PRICING = {
        "gpt-4o": {"input": 2.50, "cached_input": 0.625, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "cached_input": 0.0375, "output": 0.60},
    }

    def __init__(
        self,
        api_key: str,
        min_balance: float,
        log_dir: Path,
        console: Console,
        notifier: NotificationSender | None = None,
    ) -> None:
        """Initialize cost tracking with API credentials and thresholds."""
        self.api_key = api_key
        self.min_balance = min_balance
        self.log_dir = log_dir
        self.console = console
        self.notifier = notifier
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.cost_log_path = self.log_dir / "cost_log.jsonl"
        self.balance_log_path = self.log_dir / "balance_log.json"

    def get_balance(self) -> dict[str, Any]:
        """Fetch the available balance or fall back to environment-provided values."""
        env_balance = os.getenv("OPENAI_ACCOUNT_BALANCE")
        if env_balance:
            balance = float(env_balance)
            result = {"balance_usd": balance, "source": "environment"}
            self._log_balance(result)
            return result

        headers = {"Authorization": f"Bearer {self.api_key}"}
        endpoints = [
            "https://api.openai.com/v1/dashboard/billing/credit_grants",
            "https://api.openai.com/dashboard/billing/credit_grants",
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=20)
                response.raise_for_status()
                data = response.json()
                balance = (
                    data.get("total_available")
                    or data.get("total_granted")
                    or data.get("balance")
                )
                if balance is None and "grants" in data:
                    grants = data.get("grants", {}).get("data", [])
                    balance = sum(item.get("grant_amount", 0.0) for item in grants)
                if balance is not None:
                    result = {"balance_usd": float(balance), "source": endpoint}
                    self._log_balance(result)
                    return result
            except requests.RequestException as exc:
                self.console.print(
                    f"[yellow]Balance lookup warning:[/yellow] {exc}"
                )
            except (TypeError, ValueError) as exc:
                self.console.print(
                    f"[yellow]Balance parsing warning:[/yellow] {exc}"
                )

        result = {"balance_usd": None, "source": "unavailable"}
        self._log_balance(result)
        return result

    def ensure_minimum_balance(self) -> dict[str, Any]:
        """Validate that the account has sufficient balance to proceed."""
        result = self.get_balance()
        balance = result.get("balance_usd")
        if balance is not None and balance < self.min_balance:
            raise RuntimeError(
                f"OpenAI balance is ${balance:.2f}, which is below the minimum "
                f"required balance of ${self.min_balance:.2f}."
            )
        return result

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int = 0,
        cached_input_tokens: int = 0,
    ) -> float:
        """Estimate cost using a model pricing table."""
        pricing = self.DEFAULT_PRICING.get(model, self.DEFAULT_PRICING["gpt-4o"])
        return round(
            (input_tokens / 1_000_000) * pricing["input"]
            + (cached_input_tokens / 1_000_000) * pricing["cached_input"]
            + (output_tokens / 1_000_000) * pricing["output"],
            4,
        )

    def log_actual_cost(self, usage: PromptUsage, prompt_path: Path) -> None:
        """Append actual usage and cost data to disk."""
        record = {
            "timestamp": _utc_timestamp(),
            "prompt_path": str(prompt_path),
            "prompt_name": usage.prompt_name,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cached_input_tokens": usage.cached_input_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": usage.cost_usd,
        }
        with self.cost_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def send_monthly_cost_report(self) -> None:
        """Send a monthly cost summary email if notifications are configured."""
        if not self.notifier:
            return

        month_prefix = datetime.now(timezone.utc).strftime("%Y-%m")
        total_cost = 0.0
        total_tokens = 0
        if self.cost_log_path.exists():
            with self.cost_log_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if month_prefix in line:
                        data = json.loads(line)
                        total_cost += float(data.get("cost_usd", 0.0))
                        total_tokens += int(data.get("total_tokens", 0))

        subject = f"Genesis AI Systems — Monthly Prompt Cost Report ({month_prefix})"
        body = (
            f"Month: {month_prefix}\n"
            f"Total token usage: {total_tokens:,}\n"
            f"Estimated API cost: ${total_cost:.2f}\n"
            f"Website: https://genesisai.systems\n"
            f"Contact: info@genesisai.systems\n"
        )
        self.notifier.send_email(subject=subject, message=body, priority="LOW")

    def estimate_remaining_runs(self, balance: float | None, estimated_run_cost: float) -> int | None:
        """Estimate how many full prompt runs remain at the current balance."""
        if balance is None or estimated_run_cost <= 0:
            return None
        return max(int(balance // estimated_run_cost), 0)

    def _log_balance(self, result: dict[str, Any]) -> None:
        """Persist the most recent balance lookup to disk."""
        payload = {"timestamp": _utc_timestamp(), **result}
        with self.balance_log_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)


class NotificationSender:
    """Sends completion and failure notifications without crashing the runner."""

    def __init__(
        self,
        console: Console,
        alert_phone: str | None = None,
        resend_key: str | None = None,
        notification_email: str | None = None,
    ) -> None:
        """Initialize email notification client."""
        self.console = console
        self.alert_phone = alert_phone
        self.notification_email = notification_email or "info@genesisai.systems"
        self.resend_api_key = resend_key or os.getenv("RESEND_API_KEY")

        if self.resend_api_key and resend is not None:
            try:
                resend.api_key = self.resend_api_key
            except Exception as exc:  # pragma: no cover - network auth
                self.console.print(f"[yellow]Resend init warning:[/yellow] {exc}")

    def send(self, subject: str, message: str, priority: str = "INFO") -> None:
        """Send a message over all configured notification channels."""
        self.send_email(subject=subject, message=message, priority=priority)

    def send_email(self, subject: str, message: str, priority: str = "INFO") -> None:
        """Send an email notification via Resend if configured."""
        if not self.resend_api_key or resend is None:
            return

        try:
            resend.Emails.send(
                {
                    "from": "Genesis AI Systems <info@genesisai.systems>",
                    "to": [self.notification_email],
                    "subject": subject,
                    "html": self._wrap_html_email(
                        subject=subject,
                        message=message,
                        priority=priority,
                    ),
                }
            )
        except Exception as exc:  # pragma: no cover - external network
            self.console.print(f"[yellow]Email notification warning:[/yellow] {exc}")

    def send_completion_report(self, summary: dict[str, Any]) -> None:
        """Send a deployment completion summary."""
        message = (
            f"Completed prompt deployment.\n"
            f"Success: {summary.get('success')}\n"
            f"Files created: {summary.get('total_files', 0)}\n"
            f"Tokens used: {summary.get('total_tokens', 0):,}\n"
            f"Estimated cost: ${summary.get('total_cost', 0.0):.2f}\n"
            f"Elapsed time: {summary.get('elapsed_seconds', 0):.1f}s\n"
            f"Website: https://genesisai.systems\n"
            f"Contact: info@genesisai.systems"
        )
        self.send(
            subject="Genesis AI Systems — Auto Prompt Deployer Complete",
            message=message,
            priority="INFO",
        )

    def send_failure_report(self, failed_at: str, error: str) -> None:
        """Send a failure summary without interrupting the caller."""
        message = (
            f"Prompt deployment failed.\n"
            f"Failed at: {failed_at}\n"
            f"Error: {error}\n"
            f"Website: https://genesisai.systems\n"
            f"Contact: info@genesisai.systems"
        )
        self.send(
            subject="Genesis AI Systems — Auto Prompt Deployer Failed",
            message=message,
            priority="HIGH",
        )

    def _wrap_html_email(self, subject: str, message: str, priority: str) -> str:
        """Render a simple branded HTML email."""
        color = {
            "CRITICAL": "#ef4444",
            "HIGH": "#f97316",
            "MEDIUM": "#2563eb",
            "LOW": "#22c55e",
            "INFO": "#94a3b8",
        }.get(priority, "#2563eb")
        safe_message = escape(message)
        return f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: #0f172a; padding: 24px; border-radius: 8px 8px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 20px;">Genesis AI Systems</h1>
            <p style="color: #94a3b8; margin: 4px 0 0;">{escape(subject)}</p>
          </div>
          <div style="background: #f8fafc; padding: 24px; border-left: 4px solid {color};">
            <div style="background: {color}; color: white; padding: 4px 12px; border-radius: 4px; display: inline-block; font-size: 12px; font-weight: bold; margin-bottom: 16px;">
              {priority}
            </div>
            <div style="color: #1e293b; line-height: 1.6; white-space: pre-wrap;">
              {safe_message}
            </div>
          </div>
          <div style="background: #0f172a; padding: 16px 24px; border-radius: 0 0 8px 8px; text-align: center;">
            <p style="color: #475569; font-size: 12px; margin: 0;">
              Trendell Fordham | Genesis AI Systems<br>
              info@genesisai.systems |
              (313) 400-2575 | genesisai.systems
            </p>
          </div>
        </div>
        """


class OpenAIPromptRunner(BasePromptRunner):
    """Runs prompt files against the OpenAI Chat Completions API."""

    RESPONSE_FORMAT = {
        "type": "json_schema",
        "json_schema": {
            "name": "file_output",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Absolute file path",
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Complete file content",
                                },
                            },
                            "required": ["path", "content"],
                            "additionalProperties": False,
                        },
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of what was created",
                    },
                },
                "required": ["files", "summary"],
                "additionalProperties": False,
            },
        },
    }

    MANIFEST_RESPONSE_FORMAT = {
        "type": "json_schema",
        "json_schema": {
            "name": "file_manifest",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Absolute file path inside the portfolio.",
                                },
                                "purpose": {
                                    "type": "string",
                                    "description": "Short note describing what the file must contain.",
                                },
                            },
                            "required": ["path", "purpose"],
                            "additionalProperties": False,
                        },
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of the manifest contents.",
                    },
                },
                "required": ["files", "summary"],
                "additionalProperties": False,
            },
        },
    }

    def __init__(
        self,
        api_key: str,
        model: str,
        portfolio_dir: Path,
        token_counter: TokenCounter,
        file_writer: FileWriter,
        cost_tracker: CostTracker,
        console: Console,
        raw_response_log_path: Path,
        run_log_path: Path,
        max_output_tokens: int = 32_000,
    ) -> None:
        """Initialize the OpenAI-backed prompt runner."""
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.portfolio_dir = portfolio_dir
        self.token_counter = token_counter
        self.file_writer = file_writer
        self.cost_tracker = cost_tracker
        self.console = console
        self.response_parser = StructuredResponseParser(raw_log_path=raw_response_log_path)
        self.manifest_parser = ManifestResponseParser(raw_log_path=raw_response_log_path)
        self.run_log_path = run_log_path
        self.max_output_tokens = max_output_tokens
        self.run_log_path.parent.mkdir(parents=True, exist_ok=True)

    def run(self, prompt_path: str) -> dict[str, Any]:
        """Run a prompt file, write the emitted files, and return a summary."""
        prompt_file = Path(prompt_path)
        prompt_text = prompt_file.read_text(encoding="utf-8")
        system_prompt = self._build_system_prompt()
        estimated_tokens = self.estimate_tokens(system_prompt + "\n" + prompt_text)
        self.token_counter.warn_if_large(estimated_tokens, self.console)
        self.token_counter.log_usage(prompt_file.name, estimated_tokens)
        self.cost_tracker.ensure_minimum_balance()

        estimated_cost = self.cost_tracker.estimate_cost(
            model=self.model,
            input_tokens=estimated_tokens,
            output_tokens=self.max_output_tokens,
        )

        started_at = time.perf_counter()
        use_manifest_mode = self._should_use_manifest_mode(prompt_text, estimated_tokens)
        failure_file_count = 0
        failure_files_created: list[str] = []
        failure_skipped_paths: list[str] = []
        failure_total_bytes = 0

        try:
            if use_manifest_mode:
                result = self._run_manifest_mode(
                    prompt_file=prompt_file,
                    prompt_text=prompt_text,
                    estimated_tokens=estimated_tokens,
                    estimated_cost=estimated_cost,
                    started_at=started_at,
                )
            else:
                result = self._run_single_response_mode(
                    prompt_file=prompt_file,
                    prompt_text=prompt_text,
                    system_prompt=system_prompt,
                    estimated_tokens=estimated_tokens,
                    estimated_cost=estimated_cost,
                    started_at=started_at,
                )
            self._log_run_summary(result)
            return result
        except Exception as exc:
            if not use_manifest_mode and self._should_fallback_to_manifest_mode(exc):
                self.console.print(
                    f"[yellow]Falling back to file-by-file manifest mode for {prompt_file.name}...[/yellow]"
                )
                result = self._run_manifest_mode(
                    prompt_file=prompt_file,
                    prompt_text=prompt_text,
                    estimated_tokens=estimated_tokens,
                    estimated_cost=estimated_cost,
                    started_at=started_at,
                )
                self._log_run_summary(result)
                return result

            elapsed = time.perf_counter() - started_at
            self._log_run_summary(
                {
                    "success": False,
                    "prompt_name": prompt_file.name,
                    "prompt_path": str(prompt_file),
                    "summary": "",
                    "file_count": failure_file_count,
                    "files_created": failure_files_created,
                    "skipped_paths": failure_skipped_paths,
                    "total_bytes": failure_total_bytes,
                    "elapsed_seconds": round(elapsed, 2),
                    "error": str(exc),
                }
            )
            raise

    def estimate_tokens(self, prompt: str) -> int:
        """Estimate token usage for a prompt."""
        return self.token_counter.count(prompt)

    def verify_output(self, files: list[Path]) -> bool:
        """Verify the written output files."""
        return self.file_writer.verify_files(files)

    @staticmethod
    def _should_use_manifest_mode(prompt_text: str, estimated_tokens: int) -> bool:
        """Return True when a prompt is large enough to justify file-by-file generation."""
        section_count = prompt_text.count("\n### ")
        explicit_file_count = prompt_text.count("File:")
        return estimated_tokens > 10_000 or section_count >= 10 or explicit_file_count >= 8

    @staticmethod
    def _should_fallback_to_manifest_mode(exc: Exception) -> bool:
        """Return True when the failure looks like a one-shot JSON truncation problem."""
        message = str(exc).lower()
        return "likely truncated" in message or "failed to parse json response" in message

    def _run_single_response_mode(
        self,
        prompt_file: Path,
        prompt_text: str,
        system_prompt: str,
        estimated_tokens: int,
        estimated_cost: float,
        started_at: float,
    ) -> dict[str, Any]:
        """Run the original all-files-in-one-response mode."""
        write_report = FileWriteReport(records=[], skipped_paths=[])
        response, structured_response, empty_files_retries = self._request_structured_response(
            prompt_name=prompt_file.name,
            system_prompt=system_prompt,
            prompt_text=prompt_text,
        )
        write_report = self.file_writer.write_files(structured_response.files)
        elapsed = time.perf_counter() - started_at

        if not write_report.file_count:
            raise RuntimeError(
                f"No valid files were written for {prompt_file.name}. "
                "Check skipped path warnings and raw response logs."
            )

        if not self.verify_output(write_report.written_files):
            raise RuntimeError(f"Output verification failed for {prompt_file.name}")

        usage = self._extract_usage(
            prompt_name=prompt_file.stem,
            response=response,
            fallback_tokens=estimated_tokens,
        )
        if usage.cost_usd == 0.0:
            usage.cost_usd = estimated_cost
        self.cost_tracker.log_actual_cost(usage=usage, prompt_path=prompt_file)

        return {
            "success": True,
            "prompt_name": prompt_file.name,
            "prompt_path": str(prompt_file),
            "summary": structured_response.summary,
            "estimated_tokens": estimated_tokens,
            "estimated_cost": estimated_cost,
            "elapsed_seconds": round(elapsed, 2),
            "files_created": [str(path) for path in write_report.written_files],
            "file_count": write_report.file_count,
            "skipped_paths": write_report.skipped_paths,
            "total_bytes": write_report.total_bytes,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cached_input_tokens": usage.cached_input_tokens,
            "total_tokens": usage.total_tokens,
            "actual_cost": usage.cost_usd,
            "empty_files_retries": empty_files_retries,
            "execution_mode": "single_response",
        }

    def _run_manifest_mode(
        self,
        prompt_file: Path,
        prompt_text: str,
        estimated_tokens: int,
        estimated_cost: float,
        started_at: float,
    ) -> dict[str, Any]:
        """Run a large prompt by first building a manifest and then generating each file separately."""
        manifest_api_response, manifest_response = self._request_manifest(prompt_file.name, prompt_text)
        written_paths: list[Path] = []
        skipped_paths: list[str] = []
        total_bytes = 0
        manifest_fallback_tokens = self.estimate_tokens(
            self._build_manifest_system_prompt() + "\n" + prompt_text
        )
        manifest_usage = self._extract_usage(
            prompt_name=f"{prompt_file.stem}:manifest",
            response=manifest_api_response,
            fallback_tokens=manifest_fallback_tokens,
        )
        self.cost_tracker.log_actual_cost(usage=manifest_usage, prompt_path=prompt_file)
        total_input_tokens = manifest_usage.input_tokens
        total_output_tokens = manifest_usage.output_tokens
        total_cached_input_tokens = manifest_usage.cached_input_tokens
        total_actual_cost = manifest_usage.cost_usd

        for index, manifest_file in enumerate(manifest_response.files, start=1):
            self.console.print(
                f"[cyan]Manifest file {index}/{len(manifest_response.files)}:[/cyan] {manifest_file.path}"
            )
            response, structured_response = self._request_single_file_from_manifest(
                prompt_name=prompt_file.name,
                prompt_text=prompt_text,
                manifest_file=manifest_file,
            )
            write_report = self.file_writer.write_files(structured_response.files)
            written_paths.extend(write_report.written_files)
            skipped_paths.extend(write_report.skipped_paths)
            total_bytes += write_report.total_bytes

            file_fallback_tokens = self.estimate_tokens(
                self._build_single_file_system_prompt(
                    target_path=manifest_file.path,
                    purpose=manifest_file.purpose,
                )
            )
            usage = self._extract_usage(
                prompt_name=f"{prompt_file.stem}:{Path(manifest_file.path).name}",
                response=response,
                fallback_tokens=file_fallback_tokens,
            )
            self.cost_tracker.log_actual_cost(usage=usage, prompt_path=prompt_file)
            total_input_tokens += usage.input_tokens
            total_output_tokens += usage.output_tokens
            total_cached_input_tokens += usage.cached_input_tokens
            total_actual_cost += usage.cost_usd

        elapsed = time.perf_counter() - started_at
        unique_written_paths = list(dict.fromkeys(written_paths))
        if not unique_written_paths:
            raise RuntimeError(
                f"Manifest mode did not write any files for {prompt_file.name}. "
                "Check raw response logs for details."
            )
        if not self.verify_output(unique_written_paths):
            raise RuntimeError(f"Output verification failed for {prompt_file.name} in manifest mode")

        return {
            "success": True,
            "prompt_name": prompt_file.name,
            "prompt_path": str(prompt_file),
            "summary": manifest_response.summary,
            "estimated_tokens": estimated_tokens,
            "estimated_cost": estimated_cost,
            "elapsed_seconds": round(elapsed, 2),
            "files_created": [str(path) for path in unique_written_paths],
            "file_count": len(unique_written_paths),
            "skipped_paths": skipped_paths,
            "total_bytes": total_bytes,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "cached_input_tokens": total_cached_input_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "actual_cost": round(total_actual_cost, 4),
            "empty_files_retries": 0,
            "execution_mode": "manifest_file_by_file",
        }

    def _build_system_prompt(self) -> str:
        """Build the system instructions used for every prompt run."""
        return (
            "You are a senior developer for Genesis AI Systems founded by "
            "Trendell Fordham in Detroit MI.\n\n"
            "Your ONLY job is to create files as requested.\n\n"
            "You MUST respond with valid JSON in this exact format:\n"
            "{\n"
            '  "files": [\n'
            "    {\n"
            '      "path": "/absolute/path/to/file.ext",\n'
            '      "content": "complete file content here"\n'
            "    }\n"
            "  ],\n"
            '  "summary": "Brief description of what was created"\n'
            "}\n\n"
            "Rules:\n"
            "- Never truncate file content\n"
            f"- Always use absolute paths starting with {self.portfolio_dir}/\n"
            "- Create every file requested\n"
            "- Complete every file fully\n"
            "- Valid JSON only - no markdown, no explanation outside JSON"
        )

    def _build_manifest_system_prompt(self) -> str:
        """Build system instructions for the manifest discovery pass."""
        return (
            "You are a senior developer for Genesis AI Systems.\n\n"
            "Your job is to identify every file the user prompt asks to create or update.\n\n"
            "Return valid JSON only in this exact format:\n"
            "{\n"
            '  "files": [\n'
            "    {\n"
            '      "path": "/absolute/path/to/file.ext",\n'
            '      "purpose": "One sentence describing what must go in the file."\n'
            "    }\n"
            "  ],\n"
            '  "summary": "Brief description of the manifest"\n'
            "}\n\n"
            "Rules:\n"
            f"- Every path must be absolute and start with {self.portfolio_dir}/\n"
            "- Infer full absolute paths from any directory context in the prompt\n"
            "- Deduplicate repeated files\n"
            "- Include only files, not shell commands or prose-only instructions\n"
            "- Valid JSON only"
        )

    def _build_single_file_system_prompt(self, target_path: str, purpose: str) -> str:
        """Build system instructions for generating exactly one file."""
        return (
            "You are a senior developer for Genesis AI Systems.\n\n"
            "Your job is to generate exactly one file.\n\n"
            "Return valid JSON only in this exact format:\n"
            "{\n"
            '  "files": [\n'
            "    {\n"
            f'      "path": "{target_path}",\n'
            '      "content": "complete file content here"\n'
            "    }\n"
            "  ],\n"
            '  "summary": "Brief description of what was created"\n'
            "}\n\n"
            "Rules:\n"
            f"- Generate only this exact file path: {target_path}\n"
            f"- The file purpose is: {purpose}\n"
            "- If updating an existing file, return the full final file contents, not a patch\n"
            "- Never omit required sections from the original prompt that apply to this file\n"
            "- Valid JSON only - no markdown fences and no explanation outside JSON"
        )

    def _request_structured_response(
        self,
        prompt_name: str,
        system_prompt: str,
        prompt_text: str,
    ) -> tuple[Any, StructuredPromptResponse, int]:
        """Request a structured response and retry once if files are empty."""
        last_response_text = ""
        last_parse_error: Exception | None = None
        output_budgets = self._candidate_output_budgets()

        for budget_index, output_budget in enumerate(output_budgets):
            if budget_index > 0:
                self.console.print(
                    "[yellow]Retrying with a larger completion budget...[/yellow] "
                    f"max_output_tokens={output_budget:,}"
                )

            for empty_files_retry in range(2):
                response = self._call_openai(
                    system_prompt=system_prompt,
                    prompt_text=prompt_text,
                    max_output_tokens=output_budget,
                )
                response_text = self._extract_response_text(response)
                last_response_text = response_text

                try:
                    structured_response = self.response_parser.parse_response(
                        response_text=response_text,
                        prompt_name=prompt_name,
                    )
                except ValueError as exc:
                    last_parse_error = exc
                    finish_reason = self._extract_finish_reason(response)
                    if self._is_likely_truncated_response(
                        response_text=response_text,
                        finish_reason=finish_reason,
                    ):
                        self.console.print(
                            "[yellow]Likely truncated model output detected:[/yellow] "
                            f"{prompt_name} returned {len(response_text):,} characters "
                            f"with finish_reason={finish_reason or 'unknown'}."
                        )
                        break
                    raise

                if structured_response.files:
                    return response, structured_response, empty_files_retry

                self.console.print(
                    f"[yellow]Warning:[/yellow] model returned an empty files array for {prompt_name}."
                )
                self.response_parser.log_raw_response(
                    prompt_name=prompt_name,
                    response_text=response_text,
                    error="Model returned an empty files array.",
                )
                if empty_files_retry == 0:
                    self.console.print("[yellow]Retrying once with the same prompt...[/yellow]")
            else:
                raise RuntimeError(
                    f"Model returned an empty files array for {prompt_name} after one retry. "
                    f"See raw response log for details. Last response length: {len(last_response_text)} characters."
                )

        if last_parse_error is not None:
            raise RuntimeError(
                f"Structured response for {prompt_name} was likely truncated before completion. "
                f"Last response length: {len(last_response_text):,} characters. "
                f"Try increasing PROMPT_MAX_OUTPUT_TOKENS or splitting the prompt into smaller batches. "
                f"Parser error: {last_parse_error}"
            ) from last_parse_error

        raise RuntimeError(
            f"Failed to obtain a valid structured response for {prompt_name}. "
            f"Last response length: {len(last_response_text):,} characters."
        )

    def _request_manifest(self, prompt_name: str, prompt_text: str) -> tuple[Any, PromptManifest]:
        """Request a manifest of files for a large prompt."""
        response = self._call_openai(
            system_prompt=self._build_manifest_system_prompt(),
            prompt_text=prompt_text,
            max_output_tokens=8_000,
            response_format=self.MANIFEST_RESPONSE_FORMAT,
        )
        response_text = self._extract_response_text(response)
        manifest = self.manifest_parser.parse_response(
            response_text=response_text,
            prompt_name=f"{prompt_name}:manifest",
        )
        return response, manifest

    def _request_single_file_from_manifest(
        self,
        prompt_name: str,
        prompt_text: str,
        manifest_file: ManifestFile,
    ) -> tuple[Any, StructuredPromptResponse]:
        """Generate one file from a manifest entry."""
        target_path = Path(manifest_file.path).expanduser()
        current_content = ""
        if target_path.exists() and target_path.is_file():
            try:
                current_content = target_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                current_content = ""

        user_prompt = (
            "Original prompt:\n"
            f"{prompt_text}\n\n"
            f"Target file to generate now:\n{manifest_file.path}\n"
            f"Purpose:\n{manifest_file.purpose}\n"
        )
        if current_content:
            user_prompt += (
                "\nCurrent file contents to update:\n"
                f"{current_content}\n"
            )

        response, structured_response, _ = self._request_structured_response(
            prompt_name=f"{prompt_name}:{Path(manifest_file.path).name}",
            system_prompt=self._build_single_file_system_prompt(
                target_path=manifest_file.path,
                purpose=manifest_file.purpose,
            ),
            prompt_text=user_prompt,
        )
        return response, structured_response

    def _call_openai(
        self,
        system_prompt: str,
        prompt_text: str,
        max_output_tokens: int,
        response_format: dict[str, Any] | None = None,
    ) -> Any:
        """Call the OpenAI Chat Completions API with retries."""
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_text},
                    ],
                    response_format=response_format or self.RESPONSE_FORMAT,
                    max_tokens=max_output_tokens,
                )
            except Exception as exc:  # pragma: no cover - network call
                last_error = exc
                backoff = attempt * 3
                self.console.print(
                    f"[yellow]OpenAI request attempt {attempt} failed:[/yellow] {exc}. "
                    f"Retrying in {backoff}s..."
                )
                time.sleep(backoff)
        raise RuntimeError(f"OpenAI request failed after retries: {last_error}")

    def _extract_response_text(self, response: Any) -> str:
        """Extract the JSON text payload from a Chat Completions response."""
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise ValueError("OpenAI response did not include any choices.")

        message = getattr(choices[0], "message", None)
        if message is None:
            raise ValueError("OpenAI response choice did not include a message.")

        refusal = _safe_get(message, "refusal", None)
        if refusal:
            raise ValueError(f"OpenAI returned a refusal: {refusal}")

        content = _safe_get(message, "content", "")
        if isinstance(content, str) and content.strip():
            return content

        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text_value = item.get("text")
                else:
                    text_value = _safe_get(item, "text", None)
                if text_value:
                    chunks.append(text_value)
            if chunks:
                return "".join(chunks)

        raise ValueError("OpenAI response did not include JSON content.")

    def _candidate_output_budgets(self) -> list[int]:
        """Return progressive completion budgets for large structured outputs."""
        budgets = [self.max_output_tokens]
        for candidate in (24_000, 32_000):
            if candidate > budgets[-1]:
                budgets.append(candidate)
        return budgets

    @staticmethod
    def _extract_finish_reason(response: Any) -> str | None:
        """Extract the finish reason from the first response choice when present."""
        choices = getattr(response, "choices", None) or []
        if not choices:
            return None
        return _safe_get(choices[0], "finish_reason", None)

    @staticmethod
    def _is_likely_truncated_response(response_text: str, finish_reason: str | None) -> bool:
        """Return True when the model output appears cut off by token limits."""
        compact_text = response_text.rstrip()
        if finish_reason in {"length", "max_tokens"}:
            return True
        if not compact_text.endswith("}") or '"summary"' not in response_text:
            return True
        return False

    def _extract_usage(self, prompt_name: str, response: Any, fallback_tokens: int) -> PromptUsage:
        """Extract token usage and estimate cost from the response object."""
        usage = getattr(response, "usage", None)
        input_tokens = fallback_tokens
        output_tokens = 0
        cached_input_tokens = 0
        total_tokens = fallback_tokens

        if usage:
            input_tokens = _first_non_none(
                _safe_get(usage, "input_tokens", None),
                _safe_get(usage, "prompt_tokens", None),
                fallback_tokens,
            )
            output_tokens = _first_non_none(
                _safe_get(usage, "output_tokens", None),
                _safe_get(usage, "completion_tokens", None),
                0,
            )
            total_tokens = _first_non_none(
                _safe_get(usage, "total_tokens", None),
                int(input_tokens) + int(output_tokens),
            )
            input_details = _first_non_none(
                _safe_get(usage, "input_tokens_details", None),
                _safe_get(usage, "prompt_tokens_details", None),
                {},
            )
            if isinstance(input_details, dict):
                cached_input_tokens = int(input_details.get("cached_tokens", 0))
            else:
                cached_input_tokens = int(_safe_get(input_details, "cached_tokens", 0))

        cost = self.cost_tracker.estimate_cost(
            model=self.model,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            cached_input_tokens=int(cached_input_tokens),
        )
        return PromptUsage(
            prompt_name=prompt_name,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            cached_input_tokens=int(cached_input_tokens),
            total_tokens=int(total_tokens),
            cost_usd=cost,
        )

    def _log_run_summary(self, result: dict[str, Any]) -> None:
        """Append prompt run metrics to disk."""
        payload = {
            "timestamp": _utc_timestamp(),
            "prompt_name": result.get("prompt_name"),
            "prompt_path": result.get("prompt_path"),
            "success": result.get("success", False),
            "summary": result.get("summary", ""),
            "execution_mode": result.get("execution_mode", "single_response"),
            "files_created_count": result.get("file_count", 0),
            "files_created": result.get("files_created", []),
            "skipped_paths": result.get("skipped_paths", []),
            "total_size_bytes": result.get("total_bytes", 0),
            "elapsed_seconds": result.get("elapsed_seconds", 0.0),
            "error": result.get("error", ""),
        }
        with self.run_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")


class PromptOrchestrator:
    """Coordinates prompt execution, verification, and notifications."""

    TITLE_MAP = {
        "prompt1_production.md": "Production Mode + Live Demos",
        "prompt2_agents.md": "Agents + Setup Guide",
        "prompt3_checklists.md": "Checklists + Summary",
        "prompt4_branding.md": "Branding + Legal Pages",
    }

    def __init__(
        self,
        prompts_dir: Path,
        portfolio_dir: Path,
        openai_api_key: str,
        model: str,
        max_output_tokens: int = 32_000,
        min_balance: float = 2.00,
        alert_phone: str | None = None,
        resend_key: str | None = None,
        notification_email: str | None = None,
    ) -> None:
        """Initialize the prompt orchestrator and its collaborators."""
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY is required to run the prompt deployer.")

        self.console = Console()
        self.prompts_dir = prompts_dir
        self.portfolio_dir = portfolio_dir
        self.log_dir = portfolio_dir / ".github" / "workflows" / "logs"
        self.notifier = NotificationSender(
            console=self.console,
            alert_phone=alert_phone,
            resend_key=resend_key,
            notification_email=notification_email,
        )
        self.cost_tracker = CostTracker(
            api_key=openai_api_key,
            min_balance=min_balance,
            log_dir=self.log_dir,
            console=self.console,
            notifier=self.notifier,
        )
        token_counter = TokenCounter(model=model, log_path=self.log_dir / "token_usage.jsonl")
        file_writer = FileWriter(
            portfolio_dir=portfolio_dir,
            log_path=self.log_dir / "file_write_log.jsonl",
            console=self.console,
        )
        self.runner = OpenAIPromptRunner(
            api_key=openai_api_key,
            model=model,
            portfolio_dir=portfolio_dir,
            token_counter=token_counter,
            file_writer=file_writer,
            cost_tracker=self.cost_tracker,
            console=self.console,
            raw_response_log_path=self.log_dir / "raw_response_log.jsonl",
            run_log_path=self.log_dir / "prompt_run_log.jsonl",
            max_output_tokens=max_output_tokens,
        )

    def run_all(self, selected_prompt: int | None = None) -> dict[str, Any]:
        """Run all prompts in sequence or a single selected prompt."""
        prompt_files = self._load_prompt_files(selected_prompt=selected_prompt)
        start_time = time.perf_counter()
        self._render_header()

        balance_result = self.cost_tracker.ensure_minimum_balance()
        balance = balance_result.get("balance_usd")
        if balance is not None:
            self.console.print(f"[bold green]Balance check:[/bold green] ${balance:.2f} available")
        else:
            self.console.print("[bold yellow]Balance check:[/bold yellow] unavailable, continuing with caution")

        aggregate = {
            "success": True,
            "total_files": 0,
            "total_bytes": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "elapsed_seconds": 0.0,
            "results": [],
        }

        try:
            for index, prompt_path in enumerate(prompt_files, start=1):
                title = self.TITLE_MAP.get(prompt_path.name, prompt_path.stem.replace("_", " ").title())
                prompt_text = prompt_path.read_text(encoding="utf-8")
                estimated_tokens = self.runner.estimate_tokens(prompt_text)
                self.console.print(f"Prompt {index}/{len(prompt_files)}: {title}")
                self.console.print(f"Tokens: {estimated_tokens:,} [green]estimated[/green]")

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(bar_width=32),
                    TextColumn("{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    console=self.console,
                ) as progress:
                    task = progress.add_task("Running prompt...", total=100)
                    progress.update(task, advance=10)
                    result = self.runner.run(str(prompt_path))
                    progress.update(task, completed=100)

                aggregate["results"].append(result)
                aggregate["total_files"] += result["file_count"]
                aggregate["total_bytes"] += result.get("total_bytes", 0)
                aggregate["total_tokens"] += result["total_tokens"]
                aggregate["total_cost"] += result["actual_cost"]
                self.console.print(f"Files created: {result['file_count']} [green]done[/green]\n")

            aggregate["elapsed_seconds"] = round(time.perf_counter() - start_time, 2)
            self._render_footer(aggregate)
            self.notifier.send_completion_report(aggregate)
            return aggregate
        except Exception as exc:
            aggregate["success"] = False
            aggregate["failed_at"] = prompt_files[len(aggregate["results"])].name if len(aggregate["results"]) < len(prompt_files) else "unknown"
            aggregate["error"] = str(exc)
            aggregate["elapsed_seconds"] = round(time.perf_counter() - start_time, 2)
            self.console.print(f"[bold red]Prompt deployment failed:[/bold red] {exc}")
            self.notifier.send_failure_report(
                failed_at=aggregate["failed_at"],
                error=str(exc),
            )
            return aggregate

    def _load_prompt_files(self, selected_prompt: int | None) -> list[Path]:
        """Load prompt files in sequence, optionally filtering to one prompt."""
        files = sorted(self.prompts_dir.glob("prompt*.md"))
        if not files:
            raise FileNotFoundError(f"No prompt files found in {self.prompts_dir}")
        if selected_prompt in (None, 0):
            return files

        selected_name = f"prompt{selected_prompt}_"
        selected_files = [path for path in files if path.name.startswith(selected_name)]
        if not selected_files:
            raise FileNotFoundError(f"Prompt {selected_prompt} was not found in {self.prompts_dir}")
        return selected_files

    def _render_header(self) -> None:
        """Render the branded header."""
        self.console.print("🚀 [bold blue]Genesis AI Systems — Auto Prompt Deployer[/bold blue]")
        self.console.print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    def _render_footer(self, aggregate: dict[str, Any]) -> None:
        """Render the final completion summary."""
        self.console.print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.console.print("[bold green]ALL PROMPTS COMPLETE[/bold green]")
        self.console.print(f"Total files: {aggregate['total_files']}")
        self.console.print(f"Total size: {aggregate.get('total_bytes', 0):,} bytes")
        self.console.print(f"Tokens used: {aggregate['total_tokens']:,}")
        self.console.print(f"API cost: ~${aggregate['total_cost']:.2f}")
        self.console.print(f"Time: {aggregate['elapsed_seconds']} seconds")
        self.console.print("Git syncing: handled by your workflow commit step")
        self.console.print("SMS and email notifications: attempted where configured")

    def create_commit(self, message: str) -> bool:
        """Optionally commit changes locally if the environment requests it."""
        if os.getenv("AUTO_COMMIT_PROMPTS", "false").lower() != "true":
            return False

        commands = [
            ["git", "add", "."],
            ["git", "commit", "-m", message],
            ["git", "push", "origin", "main"],
        ]
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=self.portfolio_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                self.console.print(
                    f"[yellow]Git command warning:[/yellow] {' '.join(command)}\n{completed.stderr}"
                )
                return False
        return True


def _safe_get(container: Any, key: str, default: Any) -> Any:
    """Safely extract a value from objects or dictionaries."""
    if isinstance(container, dict):
        return container.get(key, default)
    return getattr(container, key, default)


def _first_non_none(*values: Any) -> Any:
    """Return the first value that is not None."""
    for value in values:
        if value is not None:
            return value
    return None


def _count_lines(content: str) -> int:
    """Return the number of lines in a text blob."""
    return len(content.splitlines())


def _utc_timestamp() -> str:
    """Return an ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()
