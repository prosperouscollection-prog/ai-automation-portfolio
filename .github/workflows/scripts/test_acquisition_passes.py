#!/usr/bin/env python3
"""CI assertion test — proves EmailAcquisitionEngine passes 2-6 are reachable.

Exit code 0 = all assertions passed.
Exit code 1 = at least one assertion failed.

Rules:
- Pass 1 must produce zero candidates (prospect has no structured email fields).
- All six pass names must appear in passes_ran.
- No API key is required — the test proves code reachability, not delivery.
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

from email_acquisition import EmailAcquisitionEngine  # noqa: E402

EXPECTED_PASSES = ["pass_1", "pass_2", "pass_3", "pass_4", "pass_5", "pass_6"]

# Prospect with a real-looking domain but no structured email fields.
# This forces pass_1 to produce zero candidates so passes 2-6 must run.
PROBE_PROSPECT = {
    "primary_domain": "genesisai.systems",
    "name": "Genesis AI Systems",
    # Intentionally no owner_email, contact_email, or staff_email
}


def run_assertions() -> list[str]:
    failures: list[str] = []

    engine = EmailAcquisitionEngine(logger=lambda msg: None)
    result = engine.acquire(PROBE_PROSPECT)
    data = result.to_dict()

    passes_ran: list[str] = data.get("passes_ran", [])

    # Assertion 1: all six passes must appear in passes_ran
    for pass_name in EXPECTED_PASSES:
        if pass_name not in passes_ran:
            failures.append(f"FAIL: {pass_name} not in passes_ran — got {passes_ran}")

    # Assertion 2: exactly 6 passes must have run
    if len(passes_ran) != 6:
        failures.append(
            f"FAIL: expected 6 passes, got {len(passes_ran)} — passes_ran={passes_ran}"
        )

    # Assertion 3: pass_1 must have produced zero candidates
    # (no owner_email was supplied, so structured provider has nothing to return)
    pass_1_candidates = [
        entry
        for entry in data.get("candidate_history", [])
        if entry.get("pass") == "pass_1" and entry.get("candidate")
    ]
    if pass_1_candidates:
        failures.append(
            f"FAIL: pass_1 found candidates unexpectedly — {pass_1_candidates}"
        )

    return failures


def main() -> int:
    print("=== EmailAcquisitionEngine passes 2-6 reachability test ===")
    failures = run_assertions()

    if failures:
        for msg in failures:
            print(msg)
        print(f"\nRESULT: FAIL — {len(failures)} assertion(s) failed")
        return 1

    print("PASS: all six passes present in passes_ran")
    print("PASS: pass_1 produced zero candidates (no structured email supplied)")
    print("PASS: passes 2-6 are reachable and were attempted")
    print("\nRESULT: PASS — 3/3 assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
