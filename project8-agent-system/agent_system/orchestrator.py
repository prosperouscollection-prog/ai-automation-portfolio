"""Top-level orchestration for the four-agent Project 8 pipeline."""

from __future__ import annotations

from agent_system.agents.deploy_agent import DeployAgent
from agent_system.agents.evolution_agent import EvolutionAgent
from agent_system.agents.qa_agent import QAAgent
from agent_system.agents.security_agent import SecurityAgent
from agent_system.config import Settings
from agent_system.crew_factory import CrewFactory
from agent_system.models import RunSummary, utc_now_iso
from agent_system.services.claude_advisor import ClaudeAdvisor
from agent_system.services.command_runner import CommandRunner
from agent_system.services.git_service import GitService
from agent_system.services.gmail_notifier import GmailNotifier
from agent_system.services.google_sheets_logger import GoogleSheetsRunLogger
from agent_system.services.rss_monitor import RSSMonitor


class AgentSystemOrchestrator:
    """Coordinate the end-to-end stage execution and reporting flow."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._runner = CommandRunner()
        self._advisor = ClaudeAdvisor(settings)
        self._rss_monitor = RSSMonitor()
        self._git = GitService(settings, self._runner)
        self._mailer = GmailNotifier(settings)
        self._sheet_logger = GoogleSheetsRunLogger(settings)

    def run(self, source: str, allow_deploy: bool) -> RunSummary:
        started_at = utc_now_iso()
        security = SecurityAgent(
            settings=self._settings,
            runner=self._runner,
        ).run()

        qa = QAAgent(
            settings=self._settings,
            runner=self._runner,
            advisor=self._advisor,
        ).run()

        evolution = EvolutionAgent(
            settings=self._settings,
            advisor=self._advisor,
            rss_monitor=self._rss_monitor,
        ).run()

        deploy = DeployAgent(
            settings=self._settings,
            git_service=self._git,
            notifier=self._mailer,
        ).run(
            prior_results=[security, qa, evolution],
            allow_deploy=allow_deploy,
            source=source,
        )

        summary = RunSummary(
            source=source,
            started_at=started_at,
            security_result=security,
            qa_result=qa,
            evolution_result=evolution,
            deploy_result=deploy,
            crew_summary=self._build_crew_summary(
                source=source,
                security=security,
                qa=qa,
                evolution=evolution,
                deploy=deploy,
            ),
        )
        self._sheet_logger.log_run(summary)
        return summary

    def _build_crew_summary(self, source, security, qa, evolution, deploy) -> str:
        try:
            summary = RunSummary(
                source=source,
                started_at=utc_now_iso(),
                security_result=security,
                qa_result=qa,
                evolution_result=evolution,
                deploy_result=deploy,
                crew_summary="",
            )
            crew = CrewFactory(self._settings).build_summary_crew(summary)
            result = crew.kickoff()
            return str(result)
        except Exception as exc:  # noqa: BLE001
            return f"CrewAI summary unavailable: {exc}"
