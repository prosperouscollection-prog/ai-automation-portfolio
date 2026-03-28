"""Subprocess execution wrapper."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int


class CommandRunner:
    """Execute shell commands with consistent result handling."""

    def run(self, command: list[str], cwd: str | None = None) -> CommandResult:
        try:
            process = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(exc),
                returncode=127,
            )
        except OSError as exc:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(exc),
                returncode=1,
            )
        return CommandResult(
            success=process.returncode == 0,
            stdout=process.stdout,
            stderr=process.stderr,
            returncode=process.returncode,
        )
