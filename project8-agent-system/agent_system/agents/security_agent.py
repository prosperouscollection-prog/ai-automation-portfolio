"""SecurityAgent implementation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from agent_system.agents.base import BaseStageAgent
from agent_system.config import Settings
from agent_system.models import IssueFinding, StageResult
from agent_system.services.command_runner import CommandRunner


class SecurityAgent(BaseStageAgent):
    """Run security scanners, classify findings, and auto-fix low severity issues."""

    EXCLUDED_DIR_NAMES = {
        ".git",
        ".venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        "node_modules",
    }
    SECRET_PATTERNS = [
        re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
        re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    ]

    def __init__(self, settings: Settings, runner: CommandRunner) -> None:
        self._settings = settings
        self._runner = runner

    def run(self) -> StageResult:
        findings: list[IssueFinding] = []
        details: list[str] = []
        tool_failures = 0

        bandit_findings, bandit_ok = self._run_bandit(details)
        semgrep_findings, semgrep_ok = self._run_semgrep(details)
        findings.extend(bandit_findings)
        findings.extend(semgrep_findings)
        findings.extend(self._scan_exposed_keys(details))
        tool_failures += 0 if bandit_ok else 1
        tool_failures += 0 if semgrep_ok else 1

        autofixed = 0
        if self._settings.allow_auto_fix_low:
            autofixed = self._auto_fix_low(findings)

        unresolved_blockers = [
            item for item in findings if item.severity in {"CRITICAL", "HIGH"} and not item.auto_fixed
        ]
        status = "blocked" if unresolved_blockers or tool_failures else "passed"
        summary = (
            f"{len(findings)} findings detected; {autofixed} low severity issues auto-fixed."
        )
        return StageResult(
            stage="SecurityAgent",
            status=status,
            summary=summary,
            details=details,
            findings=findings,
            metadata={
                "blockers": len(unresolved_blockers),
                "scanner_failures": tool_failures,
            },
        )

    def _run_bandit(self, details: list[str]) -> tuple[list[IssueFinding], bool]:
        excluded_paths = ",".join(
            str(self._settings.target_repo_path / name) for name in self.EXCLUDED_DIR_NAMES
        )
        command = [
            "bandit",
            "-r",
            str(self._settings.target_repo_path),
            "-f",
            "json",
            "-x",
            excluded_paths,
        ]
        result = self._runner.run(command)
        findings: list[IssueFinding] = []
        if not result.success and not result.stdout.strip():
            details.append(f"Bandit unavailable or failed to execute: {result.stderr.strip()}")
            return findings, False

        try:
            payload = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            details.append("Bandit returned non-JSON output.")
            return findings, False

        for issue in payload.get("results", []):
            findings.append(
                IssueFinding(
                    source="bandit",
                    severity=str(issue.get("issue_severity", "LOW")).upper(),
                    title=str(issue.get("test_name", "Bandit issue")),
                    description=str(issue.get("issue_text", "")),
                    file_path=issue.get("filename"),
                    line=issue.get("line_number"),
                    rule_id=issue.get("test_id"),
                    auto_fixable=issue.get("issue_severity", "").upper() == "LOW",
                )
            )
        details.append(f"Bandit completed with {len(findings)} findings.")
        return findings, True

    def _run_semgrep(self, details: list[str]) -> tuple[list[IssueFinding], bool]:
        command = [
            "semgrep",
            "--config",
            self._settings.semgrep_config,
            "--json",
        ]
        for name in self.EXCLUDED_DIR_NAMES:
            command.extend(["--exclude", name])
        command.append(
            str(self._settings.target_repo_path),
        )
        result = self._runner.run(command)
        findings: list[IssueFinding] = []
        if not result.success and not result.stdout.strip():
            details.append(f"Semgrep unavailable or failed to execute: {result.stderr.strip()}")
            return findings, False

        try:
            payload = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            details.append("Semgrep returned non-JSON output.")
            return findings, False

        for issue in payload.get("results", []):
            findings.append(
                IssueFinding(
                    source="semgrep",
                    severity=self._map_semgrep_severity(str(issue.get("extra", {}).get("severity", "LOW"))),
                    title=str(issue.get("check_id", "Semgrep issue")),
                    description=str(issue.get("extra", {}).get("message", "")),
                    file_path=issue.get("path"),
                    line=issue.get("start", {}).get("line"),
                    rule_id=issue.get("check_id"),
                    auto_fixable=str(issue.get("extra", {}).get("severity", "")).upper() in {"INFO", "LOW"},
                )
            )
        details.append(f"Semgrep completed with {len(findings)} findings.")
        return findings, True

    def _scan_exposed_keys(self, details: list[str]) -> list[IssueFinding]:
        findings: list[IssueFinding] = []
        for file_path in self._settings.target_repo_path.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part in self.EXCLUDED_DIR_NAMES for part in file_path.parts):
                continue
            if file_path.suffix.lower() not in {".py", ".js", ".ts", ".json", ".md", ".env", ".html"}:
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pattern in self.SECRET_PATTERNS:
                for match in pattern.finditer(text):
                    findings.append(
                        IssueFinding(
                            source="regex-scan",
                            severity="CRITICAL",
                            title="Potential exposed API key",
                            description=f"Matched secret-like pattern: {match.group(0)[:8]}...",
                            file_path=str(file_path),
                            line=text[: match.start()].count("\n") + 1,
                            auto_fixable=False,
                        )
                    )
        details.append(f"Regex key scan completed with {len(findings)} findings.")
        return findings

    @staticmethod
    def _map_semgrep_severity(value: str) -> str:
        normalized = value.upper()
        if normalized in {"ERROR", "HIGH", "CRITICAL"}:
            return "HIGH"
        if normalized in {"WARNING", "MEDIUM"}:
            return "MEDIUM"
        return "LOW"

    def _auto_fix_low(self, findings: list[IssueFinding]) -> int:
        fixed = 0
        for finding in findings:
            if not finding.auto_fixable or finding.auto_fixed or not finding.file_path:
                continue
            if not finding.file_path.endswith(".py"):
                continue
            path = Path(finding.file_path)
            try:
                original = path.read_text(encoding="utf-8")
            except OSError:
                continue

            updated = original.replace("yaml.load(", "yaml.safe_load(")
            updated = updated.replace("debug=True", "debug=False")
            if updated != original:
                path.write_text(updated, encoding="utf-8")
                finding.auto_fixed = True
                fixed += 1
        return fixed
