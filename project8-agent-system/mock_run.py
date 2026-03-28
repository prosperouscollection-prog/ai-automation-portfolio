"""Credential-free CLI demo for Project 8.

This script lets portfolio viewers see realistic output from the four-agent
system without setting API keys, GitHub secrets, or Google credentials.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from agent_system.mock_scenarios import build_mock_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a mock Project 8 demo.")
    parser.add_argument(
        "--scenario",
        choices=["success", "blocked", "rollback"],
        default="success",
        help="Which demo scenario to render.",
    )
    parser.add_argument(
        "--source",
        default="mock-demo",
        help="Execution source label shown in the output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the mock run summary as JSON instead of plain text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_mock_summary(scenario=args.scenario, source=args.source)
    if args.json:
        print(json.dumps(asdict(summary), indent=2, default=str))
    else:
        print(summary.human_summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
