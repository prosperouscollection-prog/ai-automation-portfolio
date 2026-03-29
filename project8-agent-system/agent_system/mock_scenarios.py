"""Mock scenario builders for credential-free Project 8 demos.

This module keeps demo data separate from the real orchestration code so the
portfolio can show believable system behavior without requiring external APIs,
GitHub credentials, or live infrastructure.
"""

from __future__ import annotations

from agent_system.models import (
    EvolutionChange,
    IssueFinding,
    RunSummary,
    StageResult,
    TestCheck,
    utc_now_iso,
)


def build_mock_summary(scenario: str, source: str = "mock-demo") -> RunSummary:
    """Return a realistic run summary for the requested demo scenario."""
    builders = {
        "success": _build_success_summary,
        "blocked": _build_blocked_summary,
        "rollback": _build_rollback_summary,
    }
    try:
        builder = builders[scenario]
    except KeyError as exc:
        raise ValueError(f"Unsupported mock scenario: {scenario}") from exc
    return builder(source)


def _build_success_summary(source: str) -> RunSummary:
    return RunSummary(
        source=source,
        started_at=utc_now_iso(),
        security_result=StageResult(
            stage="SecurityAgent",
            status="passed",
            summary="3 findings detected; 2 low severity issues auto-fixed.",
            details=[
                "Bandit completed with 2 findings.",
                "Semgrep completed with 1 finding.",
                "Regex key scan completed with 0 findings.",
            ],
            findings=[
                IssueFinding(
                    source="bandit",
                    severity="LOW",
                    title="Unsafe yaml.load usage",
                    description="Replaced yaml.load(...) with yaml.safe_load(...).",
                    file_path="project6-fine-tuning/prepare_data.py",
                    line=42,
                    rule_id="B506",
                    auto_fixable=True,
                    auto_fixed=True,
                ),
                IssueFinding(
                    source="semgrep",
                    severity="LOW",
                    title="Flask debug mode enabled",
                    description="Set debug=False before deployment.",
                    file_path="project5-chat-widget/app.py",
                    line=18,
                    rule_id="python.flask.security.debug",
                    auto_fixable=True,
                    auto_fixed=True,
                ),
                IssueFinding(
                    source="bandit",
                    severity="MEDIUM",
                    title="Subprocess shell usage reviewed",
                    description="Command execution wrapper is acceptable but should stay monitored.",
                    file_path="project8-agent-system/agent_system/services/command_runner.py",
                    line=17,
                    rule_id="B404",
                ),
            ],
            metadata={"blockers": 0, "scanner_failures": 0},
        ),
        qa_result=StageResult(
            stage="QAAgent",
            status="passed",
            summary="4/4 QA checks passed.",
            checks=[
                TestCheck(
                    name="pytest-python-smoke",
                    status="passed",
                    details="18 Python files compiled successfully.",
                ),
                TestCheck(
                    name="workflow-json:workflow.json",
                    status="passed",
                    details="Validated project7-video-automation/workflow.json with 7 nodes.",
                ),
                TestCheck(
                    name="webhook:http://localhost:5678/webhook/video-automation?topic=test",
                    status="passed",
                    details="HTTP 200",
                ),
                TestCheck(
                    name="webhook:http://localhost:5678/webhook/lead-capture?message=test",
                    status="passed",
                    details="HTTP 200",
                ),
            ],
        ),
        evolution_result=StageResult(
            stage="EvolutionAgent",
            status="passed",
            summary="Detected 5 model references and generated 2 evolution suggestions.",
            details=[
                "OpenAI RSS items: 5",
                "Anthropic RSS items: 4",
                "Applied file updates: 0",
            ],
            evolution_changes=[
                EvolutionChange(
                    current_model="gpt-4o-mini",
                    suggested_model="gpt-4o-mini",
                    reason="Model remains valid; prompt tightening recommended instead of version change.",
                ),
                EvolutionChange(
                    current_model="claude-3-5-sonnet-20241022",
                    suggested_model="claude-3-5-sonnet-20241022",
                    reason="No forced upgrade needed; changelog review suggests keeping prompts shorter and more structured.",
                ),
            ],
        ),
        deploy_result=StageResult(
            stage="DeployAgent",
            status="passed",
            summary="Deployment committed, pushed, and GitHub Actions completed successfully.",
            details=[
                "git push completed",
                "GitHub repository dispatch accepted.",
                "Workflow run succeeded: run_id=812345678, status=completed, conclusion=success, url=https://github.com/example/repo/actions/runs/812345678",
            ],
            metadata={"commit_sha": "abc123def456"},
        ),
        crew_summary=(
            "GO. Security findings were either low-risk and auto-fixed or medium-risk and documented. "
            "QA checks passed, no webhook regressions were detected, and the deployment workflow completed successfully."
        ),
    )


def _build_blocked_summary(source: str) -> RunSummary:
    return RunSummary(
        source=source,
        started_at=utc_now_iso(),
        security_result=StageResult(
            stage="SecurityAgent",
            status="blocked",
            summary="2 findings detected; 0 low severity issues auto-fixed.",
            details=[
                "Bandit completed with 1 finding.",
                "Semgrep completed with 0 findings.",
                "Regex key scan completed with 1 finding.",
            ],
            findings=[
                IssueFinding(
                    source="regex-scan",
                    severity="CRITICAL",
                    title="Potential exposed API key",
                    description="Matched secret-like pattern: sk-proj-...",
                    file_path="project5-chat-widget/index.html",
                    line=119,
                    auto_fixable=False,
                ),
                IssueFinding(
                    source="bandit",
                    severity="HIGH",
                    title="Hardcoded password string",
                    description="Credential-like string should be moved to environment variables.",
                    file_path="project8-agent-system/agent_system/services/gmail_notifier.py",
                    line=23,
                    rule_id="B105",
                ),
            ],
            metadata={"blockers": 2, "scanner_failures": 0},
        ),
        qa_result=StageResult(
            stage="QAAgent",
            status="passed",
            summary="3/3 QA checks passed.",
            checks=[
                TestCheck(
                    name="pytest-python-smoke",
                    status="passed",
                    details="18 Python files compiled successfully.",
                ),
                TestCheck(
                    name="workflow-json:workflow.json",
                    status="passed",
                    details="Validated project7-video-automation/workflow.json with 7 nodes.",
                ),
                TestCheck(
                    name="webhook-health",
                    status="skipped",
                    details="No WEBHOOK_URLS configured.",
                ),
            ],
        ),
        evolution_result=StageResult(
            stage="EvolutionAgent",
            status="passed",
            summary="Detected 4 model references and generated 1 evolution suggestion.",
            details=[
                "OpenAI RSS items: 5",
                "Anthropic RSS items: 4",
                "Applied file updates: 0",
            ],
            evolution_changes=[
                EvolutionChange(
                    current_model="gpt-4",
                    suggested_model="gpt-4o-mini",
                    reason="Project uses a legacy model label in one helper script.",
                )
            ],
        ),
        deploy_result=StageResult(
            stage="DeployAgent",
            status="blocked",
            summary="Deployment blocked because one or more prior stages did not pass.",
            details=["SecurityAgent: blocked"],
        ),
        crew_summary=(
            "NO-GO. QA and evolution checks are acceptable, but SecurityAgent found unresolved CRITICAL/HIGH issues. "
            "Human review is required before any deployment can proceed."
        ),
    )


def _build_rollback_summary(source: str) -> RunSummary:
    return RunSummary(
        source=source,
        started_at=utc_now_iso(),
        security_result=StageResult(
            stage="SecurityAgent",
            status="passed",
            summary="1 finding detected; 1 low severity issue auto-fixed.",
            details=[
                "Bandit completed with 1 finding.",
                "Semgrep completed with 0 findings.",
                "Regex key scan completed with 0 findings.",
            ],
            findings=[
                IssueFinding(
                    source="bandit",
                    severity="LOW",
                    title="Unsafe yaml.load usage",
                    description="Replaced yaml.load(...) with yaml.safe_load(...).",
                    file_path="project6-fine-tuning/prepare_data.py",
                    line=42,
                    rule_id="B506",
                    auto_fixable=True,
                    auto_fixed=True,
                )
            ],
            metadata={"blockers": 0, "scanner_failures": 0},
        ),
        qa_result=StageResult(
            stage="QAAgent",
            status="passed",
            summary="4/4 QA checks passed.",
            checks=[
                TestCheck(
                    name="pytest-python-smoke",
                    status="passed",
                    details="18 Python files compiled successfully.",
                ),
                TestCheck(
                    name="workflow-json:workflow.json",
                    status="passed",
                    details="Validated project7-video-automation/workflow.json with 7 nodes.",
                ),
                TestCheck(
                    name="webhook:http://localhost:5678/webhook/video-automation?topic=test",
                    status="passed",
                    details="HTTP 200",
                ),
                TestCheck(
                    name="webhook:http://localhost:5678/webhook/lead-capture?message=test",
                    status="passed",
                    details="HTTP 200",
                ),
            ],
        ),
        evolution_result=StageResult(
            stage="EvolutionAgent",
            status="passed",
            summary="Detected 6 model references and generated 3 evolution suggestions.",
            details=[
                "OpenAI RSS items: 5",
                "Anthropic RSS items: 4",
                "Applied file updates: 2",
            ],
            evolution_changes=[
                EvolutionChange(
                    current_model="gpt-4",
                    suggested_model="gpt-4o-mini",
                    reason="Lower-cost replacement identified for non-critical completion tasks.",
                    files_changed=[
                        "project5-chat-widget/index.html",
                        "project4-workflow-automation/workflow.json",
                    ],
                    applied=True,
                )
            ],
        ),
        deploy_result=StageResult(
            stage="DeployAgent",
            status="failed",
            summary="GitHub Actions completed unsuccessfully. Automated changes were rolled back.",
            details=[
                "Workflow run failed: run_id=812345999, status=completed, conclusion=failure, url=https://github.com/example/repo/actions/runs/812345999",
                "Rollback push succeeded for commit def789abc012.",
            ],
            metadata={"commit_sha": "def789abc012", "rollback_performed": True},
        ),
        crew_summary=(
            "REVIEW REQUIRED. The system made safe pre-deploy changes and passed QA, but the downstream deployment pipeline failed. "
            "Rollback succeeded, so production safety was preserved."
        ),
    )
