"""
Inference abstractions and OpenAI implementation for Project 6.

This module follows SOLID by exposing a minimal BaseInference interface. The
OpenAI-specific request/response details are contained in one concrete class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from openai import OpenAI


class BaseInference(ABC):
    """Abstract interface for question-answer inference."""

    @abstractmethod
    def ask(self, question: str) -> str:
        """Ask a question and return a clean text answer."""


class OpenAIInference(BaseInference):
    """OpenAI chat-completions inference for a fine-tuned model."""

    def __init__(self, client: OpenAI, model_id: str, system_prompt: str) -> None:
        self._client = client
        self._model_id = model_id
        self._system_prompt = system_prompt

    def ask(self, question: str) -> str:
        """Send a question to the fine-tuned model and return the text response."""
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question must be a non-empty string.")

        completion = self._client.chat.completions.create(
            model=self._model_id,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": cleaned_question},
            ],
        )

        answer = completion.choices[0].message.content
        if not answer:
            raise RuntimeError("Inference completed but no response text was returned.")

        return answer.strip()
