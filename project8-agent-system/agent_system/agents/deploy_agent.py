"""DeployAgent implementation."""

from __future__ import annotations

from agent_system.agents.base import BaseStageAgent
from agent_system.config import Settings
from agent_system.models import StageResult
from agent_system.services.git_service import GitService
from agent_system.services.gmail_notifier import GmailNotifier


class DeployAgent(BaseStageAgent):
    """Validate prior stages, commit changes, trigger deployment, and notify stakeholders."""

    def __init__(
        self,
        settings: Settings,
        git_service: GitService,
        notifier: GmailNotifier,
    ) -> None:
        self._settings = settings
        self._git_service = git_service
        self._notifier = notifier

    def run(
        self,
        prior_results: list[StageResult],
        allow_deploy: bool,
        source: str,
    ) -> StageResult:
        blockers = [result for result in prior_results if result.status not in {"passed", "skipped"}]
        if blockers:
            summary = "Deployment blocked because one or more prior stages did not pass."
            result = StageResult(
                stage="DeployAgent",
                status="blocked",
                summary=summary,
                details=[f"{item.stage}: {item.status}" for item in blockers],
            )
            self._notifier.send_summary("Project 8 deployment blocked", summary, result.details)
            return result

        if not allow_deploy or not self._settings.allow_auto_deploy:
            summary = "Deployment skipped because auto-deploy is disabled."
            result = StageResult(
                stage="DeployAgent",
                status="skipped",
                summary=summary,
                details=["Set ALLOW_AUTO_DEPLOY=true and omit --no-deploy to enable deployment."],
            )
            self._notifier.send_summary("Project 8 deployment skipped", summary, result.details)
            return result

        commit_message = "chore(project8): automated security, QA, and evolution updates"
        commit_sha = self._git_service.commit_changes(commit_message)
        if not commit_sha:
            result = StageResult(
                stage="DeployAgent",
                status="passed",
                summary="No deployable changes detected; repository clean.",
            )
            self._notifier.send_summary("Project 8 no-op deploy", result.summary, [])
            return result

        push_ok, push_message = self._git_service.push_changes()
        if not push_ok:
            self._git_service.rollback_last_commit()
            result = StageResult(
                stage="DeployAgent",
                status="failed",
                summary="Deployment failed during git push. Last automated commit was rolled back locally.",
                details=[push_message],
                metadata={"commit_sha": commit_sha},
            )
            self._notifier.send_summary("Project 8 deployment failed", result.summary, result.details)
            return result

        trigger_ok, trigger_message = self._git_service.trigger_actions_pipeline(
            source=source,
            commit_sha=commit_sha,
        )
        if not trigger_ok:
            rollback_ok, rollback_message = self._git_service.rollback_remote_commit(commit_sha)
            result = StageResult(
                stage="DeployAgent",
                status="failed",
                summary="Changes pushed, but the deployment pipeline trigger failed.",
                details=[trigger_message, rollback_message],
                metadata={"commit_sha": commit_sha, "rollback_performed": rollback_ok},
            )
            self._notifier.send_summary("Project 8 deployment trigger failed", result.summary, result.details)
            return result

        if self._git_service.should_wait_for_remote_pipeline():
            pipeline_ok, pipeline_message = self._git_service.wait_for_workflow_completion(
                commit_sha=commit_sha
            )
            if not pipeline_ok:
                rollback_ok, rollback_message = self._git_service.rollback_remote_commit(commit_sha)
                result = StageResult(
                    stage="DeployAgent",
                    status="failed",
                    summary="GitHub Actions completed unsuccessfully. Automated changes were rolled back.",
                    details=[pipeline_message, rollback_message],
                    metadata={"commit_sha": commit_sha, "rollback_performed": rollback_ok},
                )
                self._notifier.send_summary(
                    "Project 8 deployment rolled back",
                    result.summary,
                    result.details,
                )
                return result
            result = StageResult(
                stage="DeployAgent",
                status="passed",
                summary="Deployment committed, pushed, and GitHub Actions completed successfully.",
                details=[push_message, trigger_message, pipeline_message],
                metadata={"commit_sha": commit_sha},
            )
            self._notifier.send_summary("Project 8 deployment succeeded", result.summary, result.details)
            return result

        result = StageResult(
            stage="DeployAgent",
            status="passed",
            summary="Deployment committed, pushed, and GitHub Actions is already handling execution.",
            details=[push_message, trigger_message],
            metadata={"commit_sha": commit_sha},
        )
        self._notifier.send_summary("Project 8 deployment succeeded", result.summary, result.details)
        return result
