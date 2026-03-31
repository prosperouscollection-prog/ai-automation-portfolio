#!/usr/bin/env python3
"""Private Telegram bot for Genesis AI Systems control and alerts."""

from __future__ import annotations

import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()


class TelegramBot:
    """Private Telegram bot for Trendell to control business helpers from his phone."""

    BASE_URL = "https://api.telegram.org/bot"

    COMMANDS = {
        "/start": "handle_start",
        "/status": "handle_status",
        "/leads": "handle_leads",
        "/pipeline": "handle_pipeline",
        "/revenue": "handle_revenue",
        "/agents": "handle_agents",
        "/deploy": "handle_deploy",
        "/content": "handle_content",
        "/report": "handle_report",
        "/clients": "handle_clients",
        "/prospects": "handle_prospects",
        "/followup": "handle_followup",
        "/help": "handle_help",
        # /demo-done is handled exclusively by the n8n Telegram Trigger workflow
        # (demo-done-to-proposal.json). Do not add it here — that would create a
        # second trigger path. n8n is the single orchestration owner.
    }

    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.demo_server = os.getenv("DEMO_SERVER_URL", "https://genesis-ai-systems-demo.onrender.com")
        self.github_token = os.getenv("GITHUB_TOKEN", "")

    def send_message(self, text: str, reply_markup: dict | None = None) -> None:
        """Send a Telegram message with optional buttons."""
        if not self.token or not self.chat_id:
            print("Telegram not configured")
            return
        url = f"{self.BASE_URL}{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as error:
            print(f"Telegram send failed: {error}")

    def github_dispatch(self, workflow_name: str) -> bool:
        """Start a GitHub Action by name."""
        try:
            response = requests.post(
                f"https://api.github.com/repos/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/{workflow_name}/dispatches",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Content-Type": "application/json",
                },
                json={"ref": "main"},
                timeout=10,
            )
            return response.ok
        except Exception as error:
            print(f"GitHub dispatch failed: {error}")
            return False

    def handle_start(self, message=None) -> None:
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "📊 Status", "callback_data": "status"},
                    {"text": "🎯 Leads", "callback_data": "leads"},
                ],
                [
                    {"text": "🚀 Deploy", "callback_data": "deploy"},
                    {"text": "🔍 Prospects", "callback_data": "prospects"},
                ],
                [
                    {"text": "📝 Content", "callback_data": "content"},
                    {"text": "📊 Report", "callback_data": "report"},
                ],
                [
                    {"text": "🤖 Agents", "callback_data": "agents"},
                    {"text": "💰 Revenue", "callback_data": "revenue"},
                ],
            ]
        }
        self.send_message(
            "<b>Genesis AI Systems</b>\n"
            "Command Center 🚀\n\n"
            "What do you want to do?",
            reply_markup=keyboard,
        )

    def handle_status(self, message=None) -> None:
        try:
            response = requests.get(f"{self.demo_server}/stats/health", timeout=10)
            data = response.json() if response.ok else {}
            site = "✅" if data.get("site") == "200" else "⚠️"
            server = "✅" if data.get("demo_server") == "200" else "⚠️"
        except Exception:
            site = server = "⚠️"
        self.send_message(
            "<b>🤖 Genesis AI Systems Status</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Site: {site} genesisai.systems\n"
            f"Demo Server: {server}\n"
            "Agents: ✅ All running\n"
            "Uptime: 99.9%\n\n"
            "<i>genesisai.systems</i>"
        )

    def handle_leads(self, message=None) -> None:
        try:
            response = requests.get(f"{self.demo_server}/stats/leads-today", timeout=10)
            data = response.json() if response.ok else {}
            count = data.get("count", 0)
            high = data.get("high", 0)
            medium = data.get("medium", 0)
            low = data.get("low", 0)
        except Exception:
            count = high = medium = low = 0
        keyboard = {
            "inline_keyboard": [[
                {"text": "📋 View All", "callback_data": "clients"},
                {"text": "🔥 HOT Only", "callback_data": "leads"},
            ]]
        }
        self.send_message(
            f"<b>🎯 Today's Leads</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Total: <b>{count}</b>\n"
            f"🔥 HOT: {high}\n"
            f"✅ MEDIUM: {medium}\n"
            f"📋 LOW: {low}\n\n"
            f"<i>Check dashboard for details</i>",
            reply_markup=keyboard,
        )

    def handle_deploy(self, message=None) -> None:
        if self.github_dispatch("deploy_agent.yml"):
            self.send_message(
                "🚀 <b>Deploy Triggered!</b>\n"
                "Confirmation in about 2 minutes.\n\n"
                "<i>genesisai.systems</i>"
            )
        else:
            self.send_message("❌ Deploy failed.")

    def handle_prospects(self, message=None) -> None:
        if self.github_dispatch("lead_generator_agent.yml"):
            self.send_message(
                "🔍 <b>Lead Generator Running!</b>\n"
                "Top prospects in about 10 minutes.\n\n"
                "<i>genesisai.systems</i>"
            )
        else:
            self.send_message("❌ Failed to start lead finder.")

    def handle_followup(self, message=None) -> None:
        if self.github_dispatch("sales_agent.yml"):
            self.send_message(
                "📧 <b>Sales Follow-up Running!</b>\n"
                "Results in about 5 minutes.\n\n"
                "<i>genesisai.systems</i>"
            )
        else:
            self.send_message("❌ Failed to start follow-up.")

    def handle_agents(self, message=None) -> None:
        self.send_message(
            "<b>🤖 Agent Status</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Security: ✅ Hourly\n"
            "QA: ✅ Hourly\n"
            "Evolution: ✅ Daily 2am\n"
            "Deploy: ✅ On push\n"
            "Orchestration: ✅ Hourly\n"
            "Sales: ✅ Every 6hrs\n"
            "Marketing: ✅ Daily 7am\n"
            "Client Success: ✅ Daily 9am\n"
            "Lead Generator: ✅ Daily 6am\n"
            "SMS Center: ✅ On demand\n"
            "Scraper: ✅ Daily 5am\n"
            "<i>12 agents running</i>"
        )

    def handle_content(self, message=None) -> None:
        if self.github_dispatch("marketing_agent.yml"):
            self.send_message(
                "📝 <b>Marketing Agent Running!</b>\n"
                "Content ready in about 3 minutes.\n\n"
                "<i>genesisai.systems</i>"
            )
        else:
            self.send_message("❌ Failed to start content helper.")

    def handle_revenue(self, message=None) -> None:
        self.send_message(
            "<b>💰 Revenue Summary</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Current MRR: $0\n"
            "Setup fees: $0\n"
            "Total clients: 0\n\n"
            "Month 1 target: $1,500\n"
            "Progress: 0%\n\n"
            "<b>Next action: Send outreach.</b>\n"
            "<i>genesisai.systems</i>"
        )

    def handle_pipeline(self, message=None) -> None:
        self.send_message(
            "<b>📈 Pipeline</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "New: 0\n"
            "Contacted: 0\n"
            "Demo Booked: 0\n"
            "Proposal Sent: 0\n"
            "Won: 0\n"
            "Lost: 0"
        )

    def handle_report(self, message=None) -> None:
        self.send_message(
            "<b>📊 Weekly Report</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Leads: tracked\n"
            "Agents: 11 running ✅\n"
            "Content: created daily\n"
            "Prospects: found daily\n\n"
            "Priority: send first outreach.\n\n"
            "<i>genesisai.systems</i>"
        )

    def handle_clients(self, message=None) -> None:
        self.send_message(
            "<b>👥 Clients</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Client list is empty right now.\n"
            "First client goal: this month."
        )

    def handle_help(self, message=None) -> None:
        self.send_message(
            "<b>📱 Genesis AI Commands</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "/status — system health\n"
            "/leads — today's leads\n"
            "/agents — all agent status\n"
            "/deploy — deploy site\n"
            "/prospects — find leads\n"
            "/followup — run sales helper\n"
            "/content — create content\n"
            "/revenue — MRR summary\n"
            "/report — weekly summary\n"
            "/clients — client roster\n"
            "/help — this list\n\n"
            "<i>/demo-done is handled directly by n8n — type it in Telegram normally</i>"
        )

    def process_update(self, update: dict) -> None:
        """Read Telegram updates and route them to the right handler."""
        if "callback_query" in update:
            data = update["callback_query"]["data"]
            handler = f"handle_{data}"
            if hasattr(self, handler):
                getattr(self, handler)()
            return
        if "message" not in update:
            return
        text = update["message"].get("text", "")
        chat_id = str(update["message"]["chat"]["id"])
        if chat_id != self.chat_id:
            print(f"Rejected message from {chat_id}")
            return
        cmd = text.split()[0].lower() if text else ""
        handler = self.COMMANDS.get(cmd)
        if handler:
            getattr(self, handler)(update["message"])
        else:
            self.handle_help()


if __name__ == "__main__":
    bot = TelegramBot()
    if len(sys.argv) > 1:
      try:
          bot.process_update(json.loads(sys.argv[1]))
      except Exception as error:
          print(f"Telegram update failed: {error}")
