"""A/B testing framework for Genesis AI Systems prompts.

This module manages two prompt variants, splits traffic, stores interactions,
calculates statistical significance, and promotes a winner after enough data
has been collected.
"""

from __future__ import annotations

import json
import math
import os
import random
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class PromptVariant:
    """Represents one prompt version inside a test."""

    variant_id: str
    prompt_text: str
    version_label: str


@dataclass(frozen=True)
class InteractionRecord:
    """One scored interaction for a prompt variant."""

    use_case: str
    variant_id: str
    recorded_at: str
    quality_score: float
    lead_score: str
    follow_up_happened: bool


@dataclass(frozen=True)
class TestOutcome:
    """Summary of an A/B test once enough evidence exists."""

    use_case: str
    total_interactions: int
    winner_variant_id: str | None
    statistical_significance: float
    recommendation: str


class ABTest(ABC):
    """Abstract base for A/B testing workflows."""

    @abstractmethod
    def choose_variant(self) -> PromptVariant:
        """Route the next interaction to a prompt variant."""

    @abstractmethod
    def record_interaction(self, record: InteractionRecord) -> None:
        """Persist one interaction result."""

    @abstractmethod
    def evaluate(self) -> TestOutcome:
        """Evaluate the test and return the current outcome."""


class JSONLInteractionStore:
    """JSONL persistence for prompt test interactions."""

    def __init__(self, path: Path) -> None:
        """Store the log path and ensure the directory exists."""
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, record: InteractionRecord) -> None:
        """Append a new interaction record."""
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record)) + "\n")

    def list_for_use_case(self, use_case: str) -> list[InteractionRecord]:
        """Return all records for one use case."""
        records = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if payload["use_case"] == use_case:
                records.append(InteractionRecord(**payload))
        return records


class ProductionStateStore:
    """Stores the currently promoted production variant."""

    def __init__(self, path: Path) -> None:
        """Store the state file path."""
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text("{}", encoding="utf-8")

    def promote(self, use_case: str, variant_id: str) -> None:
        """Persist the winning production variant for a use case."""
        state = json.loads(self._path.read_text(encoding="utf-8"))
        state[use_case] = {"production_variant": variant_id, "promoted_at": datetime.now(timezone.utc).isoformat()}
        self._path.write_text(json.dumps(state, indent=2), encoding="utf-8")


class PromptABTest(ABTest):
    """Concrete prompt A/B test with automatic winner promotion."""

    SCORE_WEIGHTS = {"HIGH": 1.0, "MEDIUM": 0.55, "LOW": 0.2}

    def __init__(
        self,
        use_case: str,
        variant_a: PromptVariant,
        variant_b: PromptVariant,
        interaction_store: JSONLInteractionStore,
        production_state_store: ProductionStateStore,
        minimum_interactions: int = 100,
    ) -> None:
        """Store variants, persistence, and evaluation threshold."""
        self._use_case = use_case
        self._variant_a = variant_a
        self._variant_b = variant_b
        self._interaction_store = interaction_store
        self._production_state_store = production_state_store
        self._minimum_interactions = minimum_interactions

    def choose_variant(self) -> PromptVariant:
        """Route roughly 50% of requests to each prompt variant."""
        return self._variant_a if random.random() < 0.5 else self._variant_b

    def record_interaction(self, record: InteractionRecord) -> None:
        """Persist a test interaction."""
        self._interaction_store.append(record)

    def evaluate(self) -> TestOutcome:
        """Evaluate composite performance and promote a winner when justified."""
        records = self._interaction_store.list_for_use_case(self._use_case)
        grouped = {
            self._variant_a.variant_id: [item for item in records if item.variant_id == self._variant_a.variant_id],
            self._variant_b.variant_id: [item for item in records if item.variant_id == self._variant_b.variant_id],
        }
        total = len(records)
        if total < self._minimum_interactions:
            return TestOutcome(
                use_case=self._use_case,
                total_interactions=total,
                winner_variant_id=None,
                statistical_significance=0.0,
                recommendation=f"Keep collecting data until at least {self._minimum_interactions} interactions are logged.",
            )

        score_a = self._composite_score(grouped[self._variant_a.variant_id])
        score_b = self._composite_score(grouped[self._variant_b.variant_id])
        p_value = self._two_proportion_p_value(
            grouped[self._variant_a.variant_id],
            grouped[self._variant_b.variant_id],
        )
        significance = round((1 - p_value) * 100, 2)
        winner = self._variant_a.variant_id if score_a >= score_b else self._variant_b.variant_id

        recommendation = (
            f"Promote {winner} to production."
            if p_value <= 0.05
            else "Keep testing. Current difference is not yet statistically strong enough."
        )
        if p_value <= 0.05:
            self._production_state_store.promote(self._use_case, winner)

        return TestOutcome(
            use_case=self._use_case,
            total_interactions=total,
            winner_variant_id=winner if p_value <= 0.05 else None,
            statistical_significance=significance,
            recommendation=recommendation,
        )

    def _composite_score(self, records: list[InteractionRecord]) -> float:
        """Blend quality, lead quality, and follow-up rate into one score."""
        if not records:
            return 0.0
        avg_quality = sum(item.quality_score for item in records) / len(records)
        avg_lead_value = sum(self.SCORE_WEIGHTS.get(item.lead_score.upper(), 0.2) for item in records) / len(records)
        follow_up_rate = sum(1 for item in records if item.follow_up_happened) / len(records)
        return round((avg_quality / 5.0) * 0.4 + avg_lead_value * 0.3 + follow_up_rate * 0.3, 4)

    @staticmethod
    def _two_proportion_p_value(group_a: list[InteractionRecord], group_b: list[InteractionRecord]) -> float:
        """Compute a two-proportion p-value using follow-up rate as the success metric."""
        if not group_a or not group_b:
            return 1.0
        success_a = sum(1 for item in group_a if item.follow_up_happened)
        success_b = sum(1 for item in group_b if item.follow_up_happened)
        n_a = len(group_a)
        n_b = len(group_b)
        pooled = (success_a + success_b) / (n_a + n_b)
        denominator = math.sqrt(pooled * (1 - pooled) * ((1 / n_a) + (1 / n_b)))
        if denominator == 0:
            return 1.0
        z_score = ((success_a / n_a) - (success_b / n_b)) / denominator
        return math.erfc(abs(z_score) / math.sqrt(2))


def build_prompt_ab_test(use_case: str, variant_a: PromptVariant, variant_b: PromptVariant) -> PromptABTest:
    """Create a PromptABTest using environment-backed storage locations."""
    load_dotenv()
    return PromptABTest(
        use_case=use_case,
        variant_a=variant_a,
        variant_b=variant_b,
        interaction_store=JSONLInteractionStore(Path(os.getenv("AB_TEST_RESULTS_PATH", "./ab_test_results.jsonl")).expanduser()),
        production_state_store=ProductionStateStore(Path(os.getenv("AB_TEST_PRODUCTION_STATE_PATH", "./ab_test_state.json")).expanduser()),
    )


if __name__ == "__main__":
    test = build_prompt_ab_test(
        use_case="lead_score_classifier",
        variant_a=PromptVariant("A", "Prompt A", "v1.0"),
        variant_b=PromptVariant("B", "Prompt B", "v1.1"),
    )
    variant = test.choose_variant()
    test.record_interaction(
        InteractionRecord(
            use_case="lead_score_classifier",
            variant_id=variant.variant_id,
            recorded_at=datetime.now(timezone.utc).isoformat(),
            quality_score=4.2,
            lead_score="HIGH",
            follow_up_happened=True,
        )
    )
    print(test.evaluate())
