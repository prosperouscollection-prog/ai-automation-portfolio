"""
Orchestration entrypoint for Project 6.

This module coordinates the full fine-tuning workflow while keeping the other
modules focused on their own responsibilities. It depends on abstractions
defined elsewhere and wires them together at runtime.
"""

from __future__ import annotations

import sys

import openai
from openai import OpenAI

from config import AppConfig
from data_validator import TrainingDataValidator, ValidationError
from fine_tuner import OpenAIFineTuner
from inference import BaseInference, OpenAIInference


SAMPLE_QUESTIONS = (
    "Do you see kids?",
    "Do you accept Cigna insurance?",
    "I have a toothache",
)


def run_pipeline() -> int:
    """Run validation, fine-tuning, and sample inference end to end."""
    try:
        config = AppConfig.from_env()
        client = OpenAI(api_key=config.openai_api_key)

        print("Step 1/3: Validating training data...")
        validator = TrainingDataValidator(minimum_examples=10)
        validator.validate(config.training_file)
        print(f"Validation passed for: {config.training_file}")

        print("Step 2/3: Uploading training data and creating fine-tuning job...")
        fine_tuner = OpenAIFineTuner(
            client=client,
            base_model=config.base_model,
        )
        training_file_id = fine_tuner.upload_data(config.training_file)
        print(f"Uploaded training file. File ID: {training_file_id}")

        job_id = fine_tuner.create_job(training_file_id)
        print(f"Created fine-tuning job. Job ID: {job_id}")

        fine_tuned_model_id = fine_tuner.wait_for_completion(job_id)
        print(f"Fine-tuning completed. Model ID: {fine_tuned_model_id}")

        print("Step 3/3: Running sample inference...")
        inference: BaseInference = OpenAIInference(
            client=client,
            model_id=fine_tuned_model_id,
            system_prompt=config.system_prompt,
        )

        for question in SAMPLE_QUESTIONS:
            answer = inference.ask(question)
            print(f"Q: {question}")
            print(f"A: {answer}")
            print("-" * 60)

        print("Pipeline completed successfully.")
        return 0

    except ValidationError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"File error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except TimeoutError as exc:
        print(f"Timeout error: {exc}", file=sys.stderr)
        return 1
    except openai.APIError as exc:
        print(f"OpenAI API error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run_pipeline())
