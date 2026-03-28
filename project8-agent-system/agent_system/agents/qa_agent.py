"""QAAgent implementation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import requests

from agent_system.agents.base import BaseStageAgent
from agent_system.config import Settings
from agent_system.models import StageResult, TestCheck
from agent_system.services.claude_advisor import ClaudeAdvisor
from agent_system.services.command_runner import CommandRunner


class QAAgent(BaseStageAgent):
    """Run code smoke tests, workflow validation, and endpoint checks."""

    EXCLUDED_DIR_NAMES = {
        ".git",
        ".venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        "node_modules",
    }

    def __init__(
        self,
        settings: Settings,
        runner: CommandRunner,
        advisor: ClaudeAdvisor,
    ) -> None:
        self._settings = settings
        self._runner = runner
        self._advisor = advisor

    def run(self) -> StageResult:
        checks: list[TestCheck] = []
        suggestions: list[str] = []

        pytest_check = self._run_pytest_smoke()
        checks.append(pytest_check)

        checks.extend(self._validate_workflow_json())
        checks.extend(self._check_webhooks())

        failed = [check for check in checks if check.status == "failed"]
        if failed:
            suggestions = self._advisor.suggest_test_fixes(
                "\n".join(f"{item.name}: {item.details}" for item in failed)
            )

        status = "passed" if not failed else "failed"
        summary = f"{len(checks) - len(failed)}/{len(checks)} QA checks passed."
        return StageResult(
            stage="QAAgent",
            status=status,
            summary=summary,
            checks=checks,
            suggestions=suggestions,
        )

    def _run_pytest_smoke(self) -> TestCheck:
        python_files = [
            str(path)
            for path in self._settings.target_repo_path.rglob("*.py")
            if not any(part in self.EXCLUDED_DIR_NAMES for part in path.parts)
        ]
        if not python_files:
            return TestCheck(
                name="pytest-python-smoke",
                status="skipped",
                details="No Python files found.",
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "test_python_files.py"
            test_path.write_text(
                "import py_compile\n"
                "import pytest\n\n"
                f"PYTHON_FILES = {python_files!r}\n\n"
                "@pytest.mark.parametrize('path', PYTHON_FILES)\n"
                "def test_python_file_compiles(path):\n"
                "    py_compile.compile(path, doraise=True)\n",
                encoding="utf-8",
            )
            result = self._runner.run(["pytest", "-q", str(test_path)])
        return TestCheck(
            name="pytest-python-smoke",
            status="passed" if result.success else "failed",
            details=(result.stdout or result.stderr).strip() or "Pytest completed.",
        )

    def _validate_workflow_json(self) -> list[TestCheck]:
        checks: list[TestCheck] = []
        workflow_files = list(self._settings.target_repo_path.rglob("workflow.json"))
        workflow_files = [
            path
            for path in workflow_files
            if not any(part in self.EXCLUDED_DIR_NAMES for part in path.parts)
        ]
        if not workflow_files:
            return [
                TestCheck(
                    name="workflow-json-validation",
                    status="skipped",
                    details="No workflow.json files found.",
                )
            ]
        for workflow_file in workflow_files:
            try:
                payload = json.loads(workflow_file.read_text(encoding="utf-8"))
                nodes = payload.get("nodes", [])
                connections = payload.get("connections", {})
                valid = bool(nodes) and isinstance(connections, dict)
                checks.append(
                    TestCheck(
                        name=f"workflow-json:{workflow_file.name}",
                        status="passed" if valid else "failed",
                        details=(
                            f"Validated {workflow_file} with {len(nodes)} nodes."
                            if valid
                            else f"Workflow structure invalid: {workflow_file}"
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                checks.append(
                    TestCheck(
                        name=f"workflow-json:{workflow_file.name}",
                        status="failed",
                        details=f"{workflow_file}: {exc}",
                    )
                )
        return checks

    def _check_webhooks(self) -> list[TestCheck]:
        if not self._settings.webhook_urls:
            return [
                TestCheck(
                    name="webhook-health",
                    status="skipped",
                    details="No WEBHOOK_URLS configured.",
                )
            ]

        checks: list[TestCheck] = []
        for url in self._settings.webhook_urls:
            try:
                response = requests.get(url, timeout=10)
                passed = response.status_code < 400
                checks.append(
                    TestCheck(
                        name=f"webhook:{url}",
                        status="passed" if passed else "failed",
                        details=f"HTTP {response.status_code}",
                    )
                )
            except requests.RequestException as exc:
                checks.append(
                    TestCheck(
                        name=f"webhook:{url}",
                        status="failed",
                        details=str(exc),
                    )
                )
        return checks
