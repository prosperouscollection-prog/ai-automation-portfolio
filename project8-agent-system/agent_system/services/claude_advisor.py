"""Claude-powered advisory services for test and evolution suggestions."""

from __future__ import annotations

import json

from anthropic import Anthropic

from agent_system.config import Settings
from agent_system.models import EvolutionChange


class ClaudeAdvisor:
    """Use Claude for structured recommendations without owning orchestration logic."""

    def __init__(self, settings: Settings) -> None:
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model

    def suggest_test_fixes(self, error_text: str) -> list[str]:
        if not error_text.strip():
            return []
        prompt = (
            "You are a senior QA engineer. Read the following failed test output and provide "
            "a concise list of likely fixes. Return JSON as "
            '{"suggestions": ["..."]}.\n\n'
            f"{error_text}"
        )
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            text = self._extract_text(response)
            payload = json.loads(text)
            return [str(item) for item in payload.get("suggestions", [])]
        except Exception as exc:  # noqa: BLE001
            return [f"Claude suggestion generation failed: {exc}"]

    def suggest_model_evolution(
        self,
        changelog_items: dict[str, list[dict[str, str]]],
        model_inventory: list[str],
    ) -> list[EvolutionChange]:
        prompt = (
            "You are an AI platform evolution engineer.\n\n"
            "Given recent OpenAI and Anthropic changelog items plus the current model inventory "
            "found in a codebase, identify outdated or improvable model references.\n"
            "Return strict JSON with the shape "
            '{"changes": [{"current_model": "...", "suggested_model": "...", "reason": "..."}]}.\n\n'
            f"Current inventory: {json.dumps(model_inventory, indent=2)}\n\n"
            f"Changelog items: {json.dumps(changelog_items, indent=2)}"
        )
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=900,
                messages=[{"role": "user", "content": prompt}],
            )
            text = self._extract_text(response)
            payload = json.loads(text)
            changes = []
            for item in payload.get("changes", []):
                current_model = str(item.get("current_model", "")).strip()
                suggested_model = str(item.get("suggested_model", "")).strip()
                reason = str(item.get("reason", "")).strip()
                if current_model and suggested_model and reason:
                    changes.append(
                        EvolutionChange(
                            current_model=current_model,
                            suggested_model=suggested_model,
                            reason=reason,
                        )
                    )
            return changes
        except Exception as exc:  # noqa: BLE001
            return [
                EvolutionChange(
                    current_model="n/a",
                    suggested_model="n/a",
                    reason=f"Claude evolution analysis failed: {exc}",
                )
            ]

    @staticmethod
    def _extract_text(response) -> str:
        chunks = []
        for block in getattr(response, "content", []):
            text = getattr(block, "text", "")
            if text:
                chunks.append(text)
        return "".join(chunks).strip()
