"""
Smoke tests for Project 7 prompt builders.

This module has one responsibility: verify that each prompt function returns a
non-empty string and print the generated prompts for portfolio review or quick
manual QA.
"""

from __future__ import annotations

from prompts import (
    CAPTIONS_PROMPT,
    HASHTAGS_PROMPT,
    SCRIPT_PROMPT,
    THUMBNAIL_PROMPT,
)


TEST_TOPIC = "5 reasons to choose Invisalign"


def _assert_non_empty(name: str, value: str) -> None:
    """Raise a helpful error if a prompt builder returns empty content."""
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{name} returned an empty prompt.")


def main() -> int:
    """Run prompt smoke tests and print generated prompt bodies."""
    prompt_builders = [
        ("SCRIPT_PROMPT", SCRIPT_PROMPT),
        ("CAPTIONS_PROMPT", CAPTIONS_PROMPT),
        ("HASHTAGS_PROMPT", HASHTAGS_PROMPT),
        ("THUMBNAIL_PROMPT", THUMBNAIL_PROMPT),
    ]

    for name, builder in prompt_builders:
        output = builder(TEST_TOPIC)
        _assert_non_empty(name, output)

        print(f"{name} OUTPUT")
        print("-" * 80)
        print(output)
        print("=" * 80)

    print("All prompt checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
