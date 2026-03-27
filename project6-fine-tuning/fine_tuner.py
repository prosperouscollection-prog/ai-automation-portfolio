"""
Fine-tuning abstractions and OpenAI implementation for Project 6.

This module applies SOLID by exposing a narrow BaseFineTuner interface while
encapsulating OpenAI-specific behavior in a concrete implementation. The rest
of the application depends on the abstraction, not the vendor details.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path

from openai import OpenAI


class BaseFineTuner(ABC):
    """Abstract interface for fine-tuning providers."""

    @abstractmethod
    def upload_data(self, training_file: Path) -> str:
        """Upload a training file and return its provider-specific file ID."""

    @abstractmethod
    def create_job(self, training_file_id: str) -> str:
        """Create a fine-tuning job and return the provider-specific job ID."""

    @abstractmethod
    def get_status(self, job_id: str) -> str:
        """Return the current status for a fine-tuning job."""


class OpenAIFineTuner(BaseFineTuner):
    """OpenAI-backed fine-tuner implementation."""

    TERMINAL_STATES = {"succeeded", "failed", "cancelled"}

    def __init__(
        self,
        client: OpenAI,
        base_model: str,
        poll_interval_seconds: int = 30,
        timeout_seconds: int = 3600,
    ) -> None:
        self._client = client
        self._base_model = base_model
        self._poll_interval_seconds = poll_interval_seconds
        self._timeout_seconds = timeout_seconds

    def upload_data(self, training_file: Path) -> str:
        """Upload training data to OpenAI and return the resulting file ID."""
        with training_file.open("rb") as training_handle:
            uploaded_file = self._client.files.create(
                file=training_handle,
                purpose="fine-tune",
            )
        return uploaded_file.id

    def create_job(self, training_file_id: str) -> str:
        """Create a supervised fine-tuning job and return the job ID."""
        job = self._client.fine_tuning.jobs.create(
            model=self._base_model,
            training_file=training_file_id,
        )
        return job.id

    def get_status(self, job_id: str) -> str:
        """Retrieve the latest fine-tuning job status."""
        job = self._client.fine_tuning.jobs.retrieve(job_id)
        return job.status

    def wait_for_completion(self, job_id: str) -> str:
        """
        Poll the job until a terminal state is reached.

        Returns the fine-tuned model ID on success.
        """
        deadline = time.monotonic() + self._timeout_seconds

        while time.monotonic() < deadline:
            job = self._client.fine_tuning.jobs.retrieve(job_id)
            status = job.status

            if status == "succeeded":
                fine_tuned_model = getattr(job, "fine_tuned_model", None)
                if not fine_tuned_model:
                    raise RuntimeError(
                        "Fine-tuning succeeded but no fine-tuned model ID was returned."
                    )
                return fine_tuned_model

            if status in self.TERMINAL_STATES:
                error = getattr(job, "error", None)
                error_message = getattr(error, "message", None) or "No error details provided."
                raise RuntimeError(
                    f"Fine-tuning job {job_id} ended with status '{status}': {error_message}"
                )

            print(f"Fine-tuning job {job_id} status: {status}")
            time.sleep(self._poll_interval_seconds)

        raise TimeoutError(
            f"Fine-tuning job {job_id} did not complete within "
            f"{self._timeout_seconds} seconds."
        )
