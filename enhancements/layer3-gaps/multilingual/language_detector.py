"""Language detection and routing for multilingual Genesis AI Systems deployments.

The detector intentionally uses a simple abstract design so you can swap the
heuristic implementation for a model-based detector later without changing the
calling code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionResult:
    """Represents the predicted language and confidence."""

    language: str
    confidence: float


class LanguageDetector(ABC):
    """Abstract interface for language detection."""

    @abstractmethod
    def detect(self, text: str) -> DetectionResult:
        """Detect the language of the supplied text."""


class HeuristicLanguageDetector(LanguageDetector):
    """Keyword and character-based detector for English and Spanish."""

    SPANISH_MARKERS = {
        "hola", "gracias", "cita", "seguro", "precio", "quiero", "necesito",
        "dolor", "calor", "frio", "comida", "casa", "hoy", "mañana",
    }

    def detect(self, text: str) -> DetectionResult:
        """Return Spanish when enough Spanish markers are present."""
        lowered = text.lower()
        hits = sum(1 for marker in self.SPANISH_MARKERS if marker in lowered)
        accent_bonus = 1 if any(char in lowered for char in "áéíóúñ¿¡") else 0
        score = hits + accent_bonus
        if score >= 2:
            confidence = min(0.95, 0.55 + (score * 0.08))
            return DetectionResult(language="es", confidence=confidence)
        if score == 1:
            return DetectionResult(language="es", confidence=0.58)
        return DetectionResult(language="en", confidence=0.82)


class LanguageRoutingService:
    """Routes user input to the correct prompt variant."""

    def __init__(self, detector: LanguageDetector, confidence_threshold: float = 0.65) -> None:
        """Store the detection strategy and fallback threshold."""
        self._detector = detector
        self._confidence_threshold = confidence_threshold

    def route_prompt(self, text: str, english_prompt: str, spanish_prompt: str) -> tuple[str, DetectionResult]:
        """Return the best prompt based on detected language confidence."""
        result = self._detector.detect(text)
        if result.language == "es" and result.confidence >= self._confidence_threshold:
            return spanish_prompt, result
        return english_prompt, DetectionResult(language="en", confidence=max(result.confidence, 0.70))


def default_language_service() -> LanguageRoutingService:
    """Build the recommended language routing service."""
    return LanguageRoutingService(detector=HeuristicLanguageDetector())
