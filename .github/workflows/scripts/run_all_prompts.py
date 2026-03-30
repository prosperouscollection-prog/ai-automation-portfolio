#!/usr/bin/env python3
"""Genesis AI Systems — Auto Prompt Deployer."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from prompt_deployer import PromptOrchestrator


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for selecting prompts."""
    parser = argparse.ArgumentParser(
        description="Run Genesis AI Systems prompt deployment jobs."
    )
    parser.add_argument(
        "--prompt",
        type=int,
        choices=[0, 1, 2, 3, 4],
        default=int(os.getenv("PROMPT_NUMBER", "0")),
        help="Run a specific prompt (1-4) or 0 for all prompts.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the requested prompts and print a concise outcome summary."""
    load_dotenv()
    args = parse_args()

    orchestrator = PromptOrchestrator(
        prompts_dir=Path("/Users/genesisai/portfolio/.github/workflows/prompts"),
        portfolio_dir=Path("/Users/genesisai/portfolio"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("PROMPT_MODEL", "gpt-4o"),
        max_output_tokens=int(os.getenv("PROMPT_MAX_OUTPUT_TOKENS", "32000")),
        alert_phone=os.getenv("ALERT_PHONE_NUMBER"),
        resend_key=os.getenv("RESEND_API_KEY"),
        notification_email=os.getenv("NOTIFICATION_EMAIL"),
        min_balance=float(os.getenv("MIN_BALANCE", "2.00")),
    )

    results = orchestrator.run_all(selected_prompt=args.prompt)

    if results["success"]:
        print("✅ All prompts completed successfully")
        print(f"Files created: {results['total_files']}")
        print(f"API cost: ${results['total_cost']:.2f}")
        return 0

    print(f"❌ Failed at prompt {results['failed_at']}")
    print(f"Error: {results['error']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
