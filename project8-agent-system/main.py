"""CLI entrypoint for the Project 8 multi-agent system."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from agent_system.config import Settings
from agent_system.orchestrator import AgentSystemOrchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Project 8 agent system.")
    parser.add_argument(
        "--source",
        default="local",
        help="Execution source label, e.g. local, schedule, workflow_dispatch, manual-webhook.",
    )
    parser.add_argument(
        "--no-deploy",
        action="store_true",
        help="Skip deployment even if the deploy stage would otherwise run.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print final run summary as JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        settings = Settings.from_env()
        orchestrator = AgentSystemOrchestrator(settings=settings)
        summary = orchestrator.run(
            source=args.source,
            allow_deploy=not args.no_deploy,
        )
    except Exception as exc:  # noqa: BLE001
        if args.json:
            print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        else:
            print(f"Fatal error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(asdict(summary), indent=2, default=str))
    else:
        print(summary.human_summary())

    stage_statuses = [
        summary.security_result.status,
        summary.qa_result.status,
        summary.evolution_result.status,
        summary.deploy_result.status,
    ]
    return 0 if all(status in {"passed", "skipped"} for status in stage_statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
