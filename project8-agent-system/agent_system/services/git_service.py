"""Git and GitHub Actions integration."""

from __future__ import annotations

import os
import time

import requests

from agent_system.config import Settings
from agent_system.services.command_runner import CommandRunner


class GitService:
    """Own git commit/push/rollback actions and GitHub workflow dispatch."""

    DISPATCH_EVENT_TYPE = "manual-agent-run"

    def __init__(self, settings: Settings, runner: CommandRunner) -> None:
        self._settings = settings
        self._runner = runner
        self._repo_path = str(settings.target_repo_path)

    def commit_changes(self, message: str) -> str | None:
        self._runner.run(["git", "add", "-A"], cwd=self._repo_path)
        diff = self._runner.run(["git", "diff", "--cached", "--quiet"], cwd=self._repo_path)
        if diff.success:
            return None
        commit = self._runner.run(["git", "commit", "-m", message], cwd=self._repo_path)
        if not commit.success:
            raise RuntimeError(commit.stderr or commit.stdout or "git commit failed")
        sha = self._runner.run(["git", "rev-parse", "HEAD"], cwd=self._repo_path)
        return sha.stdout.strip()

    def push_changes(self) -> tuple[bool, str]:
        result = self._runner.run(
            ["git", "push", "origin", self._settings.github_default_branch],
            cwd=self._repo_path,
        )
        return result.success, (result.stdout or result.stderr).strip() or "git push completed"

    def rollback_last_commit(self) -> None:
        self._runner.run(["git", "reset", "--hard", "HEAD~1"], cwd=self._repo_path)

    def trigger_actions_pipeline(self, source: str, commit_sha: str) -> tuple[bool, str]:
        if self.is_running_in_github_actions():
            return True, "Already running inside GitHub Actions; no extra trigger required."
        if not self._settings.github_token or not self._settings.github_repository:
            return False, "Missing GITHUB_TOKEN or GITHUB_REPOSITORY."

        url = f"https://api.github.com/repos/{self._settings.github_repository}/dispatches"
        response = requests.post(
            url,
            headers=self._github_headers(),
            json={
                "event_type": self.DISPATCH_EVENT_TYPE,
                "client_payload": {"source": source, "commit_sha": commit_sha},
            },
            timeout=20,
        )
        if response.status_code in {200, 201, 204}:
            return True, "GitHub repository dispatch accepted."
        return False, f"GitHub repository dispatch failed: {response.status_code} {response.text}"

    def should_wait_for_remote_pipeline(self) -> bool:
        return not self.is_running_in_github_actions()

    @staticmethod
    def is_running_in_github_actions() -> bool:
        return os.getenv("GITHUB_ACTIONS", "").lower() == "true"

    def wait_for_workflow_completion(self, commit_sha: str) -> tuple[bool, str]:
        if not self._settings.github_token or not self._settings.github_repository:
            return False, "Missing GITHUB_TOKEN or GITHUB_REPOSITORY."

        timeout_seconds = self._settings.deploy_timeout_minutes * 60
        deadline = time.time() + timeout_seconds
        last_observation = "No matching workflow run found yet."
        workflow_path = f".github/workflows/{self._settings.deploy_workflow_file}"

        while time.time() < deadline:
            response = requests.get(
                f"https://api.github.com/repos/{self._settings.github_repository}/actions/runs",
                headers=self._github_headers(),
                params={"head_sha": commit_sha, "per_page": 20},
                timeout=20,
            )
            if response.status_code != 200:
                return (
                    False,
                    f"Unable to inspect workflow run status: {response.status_code} {response.text}",
                )

            payload = response.json()
            runs = payload.get("workflow_runs", [])
            matching_run = None
            for run in runs:
                path = str(run.get("path", ""))
                if workflow_path in path or path.startswith(workflow_path):
                    matching_run = run
                    break
            if not matching_run and runs:
                matching_run = runs[0]

            if matching_run:
                run_id = matching_run.get("id")
                status = matching_run.get("status", "unknown")
                conclusion = matching_run.get("conclusion")
                html_url = matching_run.get("html_url", "")
                last_observation = (
                    f"run_id={run_id}, status={status}, conclusion={conclusion}, url={html_url}"
                )
                if status == "completed":
                    if conclusion == "success":
                        return True, f"Workflow run succeeded: {last_observation}"
                    return False, f"Workflow run failed: {last_observation}"

            time.sleep(self._settings.deploy_poll_seconds)

        return (
            False,
            "Timed out waiting for the GitHub Actions workflow to finish. "
            f"Last observed state: {last_observation}",
        )

    def rollback_remote_commit(self, commit_sha: str) -> tuple[bool, str]:
        revert = self._runner.run(["git", "revert", "--no-edit", commit_sha], cwd=self._repo_path)
        if not revert.success:
            message = (revert.stderr or revert.stdout).strip() or "git revert failed"
            return False, f"Rollback failed while creating revert commit: {message}"

        push = self._runner.run(
            ["git", "push", "origin", self._settings.github_default_branch],
            cwd=self._repo_path,
        )
        message = (push.stdout or push.stderr).strip() or "git push completed"
        if push.success:
            return True, f"Rollback push succeeded for commit {commit_sha}."
        return False, f"Rollback push failed for commit {commit_sha}: {message}"

    def _github_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._settings.github_token}",
        }
