"""Shared data models for Project 8."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class IssueFinding:
    source: str
    severity: str
    title: str
    description: str
    file_path: str | None = None
    line: int | None = None
    rule_id: str | None = None
    auto_fixable: bool = False
    auto_fixed: bool = False


@dataclass
class TestCheck:
    name: str
    status: str
    details: str


@dataclass
class EvolutionChange:
    current_model: str
    suggested_model: str
    reason: str
    files_changed: list[str] = field(default_factory=list)
    applied: bool = False


@dataclass
class StageResult:
    stage: str
    status: str
    summary: str
    details: list[str] = field(default_factory=list)
    findings: list[IssueFinding] = field(default_factory=list)
    checks: list[TestCheck] = field(default_factory=list)
    evolution_changes: list[EvolutionChange] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class RunSummary:
    source: str
    started_at: str
    security_result: StageResult
    qa_result: StageResult
    evolution_result: StageResult
    deploy_result: StageResult
    crew_summary: str

    def human_summary(self) -> str:
        return (
            f"Run source: {self.source}\n"
            f"Started at: {self.started_at}\n"
            f"Security: {self.security_result.status} - {self.security_result.summary}\n"
            f"QA: {self.qa_result.status} - {self.qa_result.summary}\n"
            f"Evolution: {self.evolution_result.status} - {self.evolution_result.summary}\n"
            f"Deploy: {self.deploy_result.status} - {self.deploy_result.summary}\n"
            f"Crew summary:\n{self.crew_summary}"
        )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
