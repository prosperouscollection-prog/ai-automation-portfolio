"""CrewAI role definitions for the four Project 8 agents."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from agent_system.config import Settings
from agent_system.models import RunSummary, StageResult

if TYPE_CHECKING:
    from crewai import Crew


class CrewFactory:
    """Build CrewAI agents and tasks for final executive reasoning."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def build_summary_crew(self, summary: RunSummary) -> "Crew":
        Agent, Crew, Process, Task, llm = self._crewai_components()
        security_agent = Agent(
            role="SecurityAgent",
            goal="Review security scan output, explain risk, and decide if findings block deployment.",
            backstory="You are a senior application security engineer who thinks in concrete severities and remediation priorities.",
            verbose=False,
            allow_delegation=False,
            llm=llm,
        )
        qa_agent = Agent(
            role="QAAgent",
            goal="Review test execution, identify breakage, and explain what must be fixed before release.",
            backstory="You are a pragmatic QA lead focused on fast, reliable validation and actionable debugging output.",
            verbose=False,
            allow_delegation=False,
            llm=llm,
        )
        evolution_agent = Agent(
            role="EvolutionAgent",
            goal="Review changelog signals, identify stale model usage, and summarize safe upgrade opportunities.",
            backstory="You monitor AI platform changes and recommend low-risk, high-value improvements.",
            verbose=False,
            allow_delegation=False,
            llm=llm,
        )
        deploy_agent = Agent(
            role="DeployAgent",
            goal="Make a final go/no-go decision based on the prior stages and produce a deployment summary.",
            backstory="You are a release manager who only ships when the evidence supports it.",
            verbose=False,
            allow_delegation=False,
            llm=llm,
        )

        tasks = [
            Task(
                description=self._stage_prompt("security", summary.security_result),
                expected_output="A concise security risk summary with blocking issues called out.",
                agent=security_agent,
            ),
            Task(
                description=self._stage_prompt("qa", summary.qa_result),
                expected_output="A concise QA summary with failures, likely causes, and next steps.",
                agent=qa_agent,
            ),
            Task(
                description=self._stage_prompt("evolution", summary.evolution_result),
                expected_output="A concise evolution summary including upgrade opportunities and safety notes.",
                agent=evolution_agent,
            ),
            Task(
                description=(
                    "Using the prior stage outputs and the deployment stage result below, "
                    "produce the final release manager summary.\n\n"
                    f"Deployment stage data:\n{self._serialize_stage(summary.deploy_result)}\n\n"
                    "Your output must clearly state GO, NO-GO, or REVIEW REQUIRED."
                ),
                expected_output="A final deployment recommendation with one-paragraph rationale.",
                agent=deploy_agent,
            ),
        ]

        return Crew(
            agents=[security_agent, qa_agent, evolution_agent, deploy_agent],
            tasks=tasks,
            process=Process.sequential,
            verbose=False,
        )

    @staticmethod
    def _serialize_stage(result: StageResult) -> str:
        return json.dumps(
            {
                "stage": result.stage,
                "status": result.status,
                "summary": result.summary,
                "details": result.details,
                "suggestions": result.suggestions,
                "metadata": result.metadata,
            },
            indent=2,
        )

    def _stage_prompt(self, name: str, result: StageResult) -> str:
        return (
            f"You are reviewing the {name} stage of an autonomous engineering system.\n\n"
            "Summarize what matters, identify risks, and explain what a human reviewer should know.\n\n"
            f"Stage data:\n{self._serialize_stage(result)}"
        )

    def _crewai_components(self) -> tuple[Any, Any, Any, Any, Any]:
        from crewai import Agent, Crew, LLM, Process, Task

        llm = LLM(
            model=self._settings.crewai_model,
            api_key=self._settings.anthropic_api_key,
            max_tokens=1800,
            temperature=0.2,
        )
        return Agent, Crew, Process, Task, llm
