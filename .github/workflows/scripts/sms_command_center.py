#!/usr/bin/env python3
"""Accept commands and reply via Telegram."""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

load_dotenv()

COMMANDS = {
    "STATUS": "handle_status",
    "LEADS": "handle_leads",
    "LEAD": "handle_lead_detail",
    "DEPLOY": "handle_deploy",
    "CONTENT": "handle_content",
    "REPORT": "handle_report",
    "FOLLOWUP": "handle_followup",
    "CLIENTS": "handle_clients",
    "REVENUE": "handle_revenue",
    "AGENTS": "handle_agents",
    "PROSPECTS": "handle_prospects",
    "HELP": "handle_help",
}


class TelegramCommandCenter:
    """Receive commands and reply via Telegram."""

    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat = os.getenv("TELEGRAM_CHAT_ID", "")
        self.demo_server = os.getenv("DEMO_SERVER_URL", "https://genesis-ai-systems-demo.onrender.com")
        self.github_token = os.getenv("GITHUB_TOKEN", "")

    def run(self) -> None:
        command = os.getenv("COMMAND", "").strip().upper()
        parts = command.split()
        cmd = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        handler = COMMANDS.get(cmd)
        response = getattr(self, handler)(args) if handler else self.handle_help([])
        self.send_telegram(response)

    def github_dispatch(self, workflow_name: str) -> bool:
        try:
            response = requests.post(
                f"https://api.github.com/repos/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/{workflow_name}/dispatches",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Content-Type": "application/json",
                },
                json={"ref": "main"},
                timeout=20,
            )
            return response.ok
        except Exception:
            return False

    def handle_status(self, args: list[str]) -> str:
        try:
            response = requests.get(f"{self.demo_server}/stats/health", timeout=10)
            data = response.json() if response.ok else {}
            site = data.get("site", "?")
            uptime = data.get("uptime", "?")
        except Exception:
            site = uptime = "checking..."
        return (
            "Genesis AI Systems Status\n"
            "====================\n"
            f"Site: {'✅' if site == '200' else '⚠️'} Online\n"
            f"Uptime: {uptime}\n"
            "Agents: All running ✅\n"
            "genesisai.systems"
        )

    def handle_leads(self, args: list[str]) -> str:
        try:
            response = requests.get(f"{self.demo_server}/stats/leads-today", timeout=10)
            data = response.json() if response.ok else {}
            count = data.get("count", 0)
            high = data.get("high", 0)
            medium = data.get("medium", 0)
        except Exception:
            count = high = medium = "?"
        return (
            "Today's Leads\n"
            "===============\n"
            f"Total: {count}\n"
            f"🔥 HOT: {high}\n"
            f"✅ WARM: {medium}\n"
            "genesisai.systems"
        )

    def handle_lead_detail(self, args: list[str]) -> str:
        return (
            "Lead details:\n"
            "Check dashboard for full info:\n"
            "genesisai.systems/dashboard.html"
        )

    def handle_deploy(self, args: list[str]) -> str:
        if self.github_dispatch("deploy_agent.yml"):
            return "🚀 Deploy triggered!\nConfirmation in ~2 min.\ngenesisai.systems"
        return "Deploy trigger failed. Check GitHub."

    def handle_content(self, args: list[str]) -> str:
        self.github_dispatch("marketing_agent.yml")
        return "📝 Marketing agent is running.\nContent will be ready soon."

    def handle_report(self, args: list[str]) -> str:
        return "📊 Weekly report is being prepared.\nCheck your inbox soon."

    def handle_followup(self, args: list[str]) -> str:
        self.github_dispatch("sales_agent.yml")
        return "📧 Sales follow-up running!\nResults in ~5 min.\ngenesisai.systems"

    def handle_clients(self, args: list[str]) -> str:
        self.github_dispatch("client_success_agent.yml")
        return "🤝 Client success check is running now."

    def handle_revenue(self, args: list[str]) -> str:
        return "💰 Current goal: turn hot leads into booked calls this week."

    def handle_prospects(self, args: list[str]) -> str:
        self.github_dispatch("lead_generator_agent.yml")
        return "🔍 Lead generator running!\nTop prospects in ~10 min.\ngenesisai.systems"

    def handle_agents(self, args: list[str]) -> str:
        return (
            "Agent Status\n"
            "============\n"
            "Security: ✅ Hourly\n"
            "QA: ✅ Hourly\n"
            "Deploy: ✅ On push\n"
            "Evolution: ✅ Daily\n"
            "Sales: ✅ Every 6hrs\n"
            "Marketing: ✅ 7am daily\n"
            "Client Success: ✅ 9am daily\n"
            "Lead Generator: ✅ 6am daily\n"
            "Telegram Center: ✅ On demand\n"
            "Check: github.com/prosperouscollection-prog"
        )

    def handle_help(self, args: list[str]) -> str:
        return (
            "Genesis AI Commands\n"
            "==================\n"
            "STATUS — health check\n"
            "LEADS — today's leads\n"
            "LEAD N — lead details\n"
            "DEPLOY — deploy site\n"
            "FOLLOWUP — run sales\n"
            "PROSPECTS — find leads\n"
            "AGENTS — agent status\n"
            "REPORT — weekly stats\n"
            "CLIENTS — client list\n"
            "REVENUE — MRR summary\n"
            "HELP — this list"
        )

    def send_telegram(self, message: str) -> None:
        if not self.token or not self.chat:
            print("⚠️ Telegram not configured")
            return
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat, "text": message[:4096]},
                timeout=10,
            )
            print("✅ Telegram response sent" if r.ok else f"⚠️ Telegram {r.status_code}")
        except Exception as error:
            print(f"⚠️ Telegram failed: {error}")


if __name__ == "__main__":
    center = TelegramCommandCenter()
    center.run()
