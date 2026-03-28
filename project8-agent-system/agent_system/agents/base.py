"""Base class for deterministic stage agents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent_system.models import StageResult


class BaseStageAgent(ABC):
    """Shared interface for stage agents."""

    @abstractmethod
    def run(self) -> StageResult:
        """Execute the stage and return a structured result."""
