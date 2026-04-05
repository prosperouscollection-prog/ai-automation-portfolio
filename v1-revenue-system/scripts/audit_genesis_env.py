#!/usr/bin/env python3
"""Fail-fast environment audit for Genesis AI Systems.

Checks the local `.env.local` template/values and the workflow secret
expectations before any operational workflow step runs.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared_env import EXPECTED_SECRET_KEYS, LOCAL_ENV_EXAMPLE_PATH, LOCAL_ENV_PATH, bootstrap_env, getenv  # noqa: E402


WORKFLOW_SECRET_PATTERN = re.compile(r"secrets\.([A-Z0-9_]+)")


def _scan_workflow_secret_refs() -> set[str]:
    refs: set[str] = set()
    workflows_dir = ROOT / ".github" / "workflows"
    for path in workflows_dir.glob("*.yml"):
        refs.update(WORKFLOW_SECRET_PATTERN.findall(path.read_text(encoding="utf-8")))
    return refs


def _format_missing(keys: Iterable[str]) -> str:
    return ", ".join(keys) if keys else "none"


def _env_file_keys(path: Path) -> list[str]:
    if not path.exists():
        return []
    keys: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key:
            keys.append(key)
    return keys


def audit_local_env() -> list[str]:
    missing: list[str] = []
    if not LOCAL_ENV_PATH.exists():
        missing.append(f"missing local env file: {LOCAL_ENV_PATH}")
        return missing

    values = dotenv_values(LOCAL_ENV_PATH)
    for key in EXPECTED_SECRET_KEYS:
        if not str(values.get(key, "") or "").strip():
            missing.append(f"{key} missing from {LOCAL_ENV_PATH.name}")
    return missing


def audit_example_sync() -> list[str]:
    if not LOCAL_ENV_EXAMPLE_PATH.exists():
        return [f"missing template file: {LOCAL_ENV_EXAMPLE_PATH}"]

    example_keys = _env_file_keys(LOCAL_ENV_EXAMPLE_PATH)
    missing = [key for key in EXPECTED_SECRET_KEYS if key not in example_keys]
    extra = [key for key in example_keys if key not in EXPECTED_SECRET_KEYS]
    order_matches = example_keys[: len(EXPECTED_SECRET_KEYS)] == list(EXPECTED_SECRET_KEYS)
    failures: list[str] = []
    if missing:
        failures.append(
            f"{LOCAL_ENV_EXAMPLE_PATH.name} is missing keys: " + _format_missing(missing)
        )
    if extra:
        failures.append(
            f"{LOCAL_ENV_EXAMPLE_PATH.name} has unexpected keys: " + _format_missing(extra)
        )
    if not order_matches:
        failures.append(
            f"{LOCAL_ENV_EXAMPLE_PATH.name} order does not match the registry"
        )
    return failures


def audit_runtime_env() -> list[str]:
    missing: list[str] = []
    for key in EXPECTED_SECRET_KEYS:
        if not getenv(key):
            missing.append(f"{key} missing from current environment")
    return missing


def audit_workflow_secret_refs(workflow_file: Path | None = None) -> list[str]:
    if workflow_file is None:
        refs = _scan_workflow_secret_refs()
        return sorted(refs.difference(EXPECTED_SECRET_KEYS))
    refs = set(WORKFLOW_SECRET_PATTERN.findall(workflow_file.read_text(encoding="utf-8")))
    unknown_refs = sorted(refs.difference(EXPECTED_SECRET_KEYS))
    return unknown_refs


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Genesis env/secrets before workflow execution.")
    parser.add_argument(
        "--mode",
        choices=("auto", "local", "github"),
        default="auto",
        help="Audit the local .env.local file, the current GitHub Actions environment, or auto-detect.",
    )
    parser.add_argument(
        "--skip-workflow-scan",
        action="store_true",
        help="Skip scanning .github/workflows for secret reference expectations.",
    )
    parser.add_argument(
        "--workflow-file",
        type=Path,
        help="Optional workflow file to audit against the registry and current env.",
    )
    args = parser.parse_args()

    bootstrap_env()

    mode = args.mode
    if mode == "auto":
        mode = "github" if getenv("GITHUB_ACTIONS") == "true" else "local"

    failures: list[str] = []
    if mode == "local":
        failures.extend(audit_local_env())
        failures.extend(audit_example_sync())
    else:
        workflow_file = args.workflow_file
        if workflow_file is not None:
            refs = set(WORKFLOW_SECRET_PATTERN.findall(workflow_file.read_text(encoding="utf-8")))
            unknown_refs = sorted(refs.difference(EXPECTED_SECRET_KEYS))
            if unknown_refs:
                failures.append(
                    f"{workflow_file.name} references unknown secrets: " + _format_missing(unknown_refs)
                )
            missing_env = [key for key in sorted(refs) if not getenv(key)]
            if missing_env:
                failures.append(
                    f"{workflow_file.name} missing env values: " + _format_missing(missing_env)
                )
        else:
            failures.extend(audit_runtime_env())

    if not args.skip_workflow_scan:
        if args.workflow_file is None:
            unknown_refs = audit_workflow_secret_refs(None)
            if unknown_refs:
                failures.append(
                    "workflow secret references use unknown secrets: " + _format_missing(unknown_refs)
                )

    print(f"Genesis env audit mode: {mode}")
    print(f"Expected secrets: {', '.join(EXPECTED_SECRET_KEYS)}")
    if args.workflow_file:
        print(f"Workflow file: {args.workflow_file}")
    if not args.skip_workflow_scan:
        print("Workflow secret references: scanned")
    else:
        print("Workflow secret references: skipped")

    if failures:
        print("FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
