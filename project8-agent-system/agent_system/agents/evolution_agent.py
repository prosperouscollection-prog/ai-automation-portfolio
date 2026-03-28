"""EvolutionAgent implementation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from agent_system.agents.base import BaseStageAgent
from agent_system.config import Settings
from agent_system.models import EvolutionChange, StageResult, utc_now_iso
from agent_system.services.claude_advisor import ClaudeAdvisor
from agent_system.services.rss_monitor import RSSMonitor


class EvolutionAgent(BaseStageAgent):
    """Monitor changelogs, detect stale models, and propose safe upgrades."""

    EXCLUDED_DIR_NAMES = {
        ".git",
        ".venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        "node_modules",
    }
    MODEL_REGEX = re.compile(
        r"(gpt-[A-Za-z0-9\.-]+|claude-[A-Za-z0-9\.-]+|anthropic/claude-[A-Za-z0-9\.-]+)"
    )

    def __init__(
        self,
        settings: Settings,
        advisor: ClaudeAdvisor,
        rss_monitor: RSSMonitor,
    ) -> None:
        self._settings = settings
        self._advisor = advisor
        self._rss_monitor = rss_monitor

    def run(self) -> StageResult:
        changelog_items = self._rss_monitor.fetch_many(
            {
                "openai": self._settings.openai_changelog_rss_url,
                "anthropic": self._settings.anthropic_changelog_rss_url,
            }
        )
        inventory = self._find_models()
        changes = self._advisor.suggest_model_evolution(changelog_items, inventory)

        applied_files: list[str] = []
        if self._settings.evolution_auto_apply:
            applied_files = self._apply_changes(changes)
            for change in changes:
                change.files_changed = [item for item in applied_files if item in change.files_changed or not change.files_changed]
                change.applied = bool(change.files_changed)

        self._append_changelog(changes, inventory)

        summary = (
            f"Detected {len(inventory)} model references and generated {len(changes)} evolution suggestions."
        )
        return StageResult(
            stage="EvolutionAgent",
            status="passed",
            summary=summary,
            evolution_changes=changes,
            details=[
                f"OpenAI RSS items: {len(changelog_items.get('openai', []))}",
                f"Anthropic RSS items: {len(changelog_items.get('anthropic', []))}",
                f"Applied file updates: {len(applied_files)}",
            ],
        )

    def _find_models(self) -> list[str]:
        models: set[str] = set()
        for file_path in self._settings.target_repo_path.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part in self.EXCLUDED_DIR_NAMES for part in file_path.parts):
                continue
            if file_path.suffix.lower() not in {".py", ".json", ".md", ".yml", ".yaml", ".html"}:
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            models.update(self.MODEL_REGEX.findall(text))
        return sorted(models)

    def _apply_changes(self, changes: list[EvolutionChange]) -> list[str]:
        touched: set[str] = set()
        if not changes:
            return []
        files = [
            path
            for path in self._settings.target_repo_path.rglob("*")
            if path.is_file()
            and not any(part in self.EXCLUDED_DIR_NAMES for part in path.parts)
            and path.suffix.lower() in {".py", ".json", ".md", ".yml", ".yaml", ".html"}
        ]
        for change in changes:
            for path in files:
                original = path.read_text(encoding="utf-8", errors="ignore")
                if change.current_model not in original:
                    continue
                updated = original.replace(change.current_model, change.suggested_model)
                if updated != original:
                    path.write_text(updated, encoding="utf-8")
                    touched.add(str(path))
                    change.files_changed.append(str(path))
                    change.applied = True
        return sorted(touched)

    def _append_changelog(self, changes: list[EvolutionChange], inventory: list[str]) -> None:
        changelog_path = Path(__file__).resolve().parents[2] / "EVOLUTION_CHANGELOG.md"
        if not changelog_path.exists():
            changelog_path.write_text("# Evolution Changelog\n", encoding="utf-8")
        entry_lines = [
            "",
            f"## {utc_now_iso()}",
            "",
            f"- Models detected: {', '.join(inventory) if inventory else 'none'}",
        ]
        if changes:
            for change in changes:
                entry_lines.append(
                    f"- {change.current_model} -> {change.suggested_model} | applied={change.applied} | {change.reason}"
                )
        else:
            entry_lines.append("- No evolution suggestions generated.")
        changelog_path.write_text(
            changelog_path.read_text(encoding="utf-8") + "\n".join(entry_lines) + "\n",
            encoding="utf-8",
        )
