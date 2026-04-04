#!/usr/bin/env python3
"""Telegram approval module for Genesis AI Systems V1 revenue corridor.

Handles founder approval at HIGH-RISK CONTROL POINTS ONLY.
Not every external action requires approval. Routine automated handoffs
(payment received → intake trigger, intake complete → HubSpot update) run
without approval gates.

HIGH-RISK CONTROL POINTS THAT REQUIRE APPROVAL:
  - Outreach review queue decisions (QUEUE/SKIP)
  - Deployment start after intake complete (DEPLOY/HOLD)

AUTOMATED — NO APPROVAL REQUIRED:
  - Lead Generator finding leads
  - Proposal handoff (auto-triggered after founder marks demo done)
  - Payment → intake form trigger (Stripe webhook → n8n, fully automated)
  - Intake completion → HubSpot update (HoneyBook webhook → n8n)
  - QA runs (triggered by Deploy Agent, results reported via Telegram)
  - Stale deal alerts (CRM Pipeline Agent — informational only)

Usage:
    from approval_flow import ApprovalFlow, ActionType

    flow = ApprovalFlow()
    req = flow.request_approval(ActionType.OUTREACH, "Slows Bar BQ", "owner@slowsbarbq.com", draft)
    status = flow.wait_for_approval(req.request_id)
"""

from __future__ import annotations

import json
import os
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SKIPPED = "skipped"
    EXPIRED = "expired"
    CONFIRMED = "confirmed"


class ActionType(Enum):
    OUTREACH = "outreach"   # Outreach review queue — requires QUEUE/SKIP
    DEPLOY = "deploy"       # Client deployment start — requires DEPLOY/HOLD


@dataclass
class ApprovalRequest:
    """One pending approval waiting for founder response."""
    request_id: str
    action_type: ActionType
    target_name: str
    target_email: str
    preview: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = ""
    resolved_at: str = ""
    message_id: Optional[int] = None  # Telegram message ID for tracking

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class ApprovalFlow:
    """Manages Telegram-based approval gates for the V1 revenue corridor."""

    TELEGRAM_API = "https://api.telegram.org/bot"

    # Reply keywords per action type
    APPROVE_KEYWORDS = {
        ActionType.OUTREACH: ["queue", "yes", "approve"],
        ActionType.DEPLOY: ["deploy", "yes", "go"],
    }
    SKIP_KEYWORDS = ["skip", "no", "pass", "hold", "later"]

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.pending: dict[str, ApprovalRequest] = {}

    def _generate_id(self, action_type: str, target_name: str) -> str:
        """Create a short, unique request ID."""
        raw = f"{action_type}-{target_name}-{time.time()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:8]

    def send_telegram(self, text: str, reply_markup: Optional[dict] = None) -> Optional[int]:
        """Send a Telegram message. Returns message_id on success."""
        print(f"  🔍 Telegram send_telegram() called — token={'SET' if os.getenv('TELEGRAM_BOT_TOKEN') else 'MISSING'} chat={'SET' if os.getenv('TELEGRAM_CHAT_ID') else 'MISSING'}")
        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram not configured — approval flow disabled")
            return None

        url = f"{self.TELEGRAM_API}{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)

        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.ok:
                return resp.json().get("result", {}).get("message_id")
            print(f"  ⚠️  Telegram sendMessage failed: {resp.status_code} {resp.text}")
            return None
        except Exception as e:
            print(f"  ⚠️  Telegram sendMessage exception: {e}")
            return None

    def get_recent_replies(self, since_message_id: int) -> list[dict]:
        """Poll for Telegram replies after a specific message ID."""
        if not self.bot_token:
            return []

        url = f"{self.TELEGRAM_API}{self.bot_token}/getUpdates"
        try:
            resp = requests.get(url, params={"timeout": 5, "offset": -20}, timeout=15)
            if not resp.ok:
                return []
            updates = resp.json().get("result", [])
            replies = []
            for update in updates:
                msg = update.get("message", {})
                # Only from founder's chat
                if str(msg.get("chat", {}).get("id")) != str(self.chat_id):
                    continue
                # Only messages after our approval prompt
                if msg.get("message_id", 0) > since_message_id:
                    replies.append({
                        "text": msg.get("text", "").strip().lower(),
                        "message_id": msg.get("message_id"),
                        "date": msg.get("date"),
                    })
            return replies
        except Exception as e:
            print(f"❌ Telegram getUpdates error: {e}")
            return []

    def request_approval(
        self,
        action_type: ActionType,
        target_name: str,
        target_email: str = "",
        preview: str = "",
        metadata: Optional[dict] = None,
    ) -> ApprovalRequest:
        """Send an approval prompt to Telegram and register it as pending.

        Returns the ApprovalRequest. Caller should then poll check_approval()
        or use the synchronous wait_for_approval() method.
        """
        request_id = self._generate_id(action_type.value, target_name)

        req = ApprovalRequest(
            request_id=request_id,
            action_type=action_type,
            target_name=target_name,
            target_email=target_email,
            preview=preview[:500],  # Truncate long previews
        )

        # Format the Telegram message
        approve_word = self.APPROVE_KEYWORDS[action_type][0].upper()
        emoji = {"outreach": "📧", "deploy": "🚀"}.get(action_type.value, "❓")

        msg = (
            f"{emoji} <b>APPROVAL NEEDED — {action_type.value.upper()}</b>\n\n"
            f"<b>Target:</b> {target_name}\n"
        )
        if target_email:
            msg += f"<b>Email:</b> {target_email}\n"
        if preview:
            msg += f"\n<b>Preview:</b>\n<i>{preview[:300]}</i>\n"
        msg += (
            f"\n<b>Reply {approve_word} to queue for review or SKIP to pass.</b>\n"
            f"<code>ID: {request_id}</code>"
        )

        message_id = self.send_telegram(msg)
        req.message_id = message_id
        self.pending[request_id] = req

        print(f"📨 Approval requested: {request_id} ({action_type.value} → {target_name})")
        return req

    def check_approval(self, request_id: str) -> ApprovalStatus:
        """Check if a specific approval request has been answered.

        Polls Telegram for replies and checks keywords against the pending request.
        """
        req = self.pending.get(request_id)
        if not req or req.status != ApprovalStatus.PENDING:
            return req.status if req else ApprovalStatus.EXPIRED

        if not req.message_id:
            return ApprovalStatus.PENDING

        replies = self.get_recent_replies(req.message_id)
        for reply in replies:
            text = reply["text"]

            # Check approve keywords
            approve_words = self.APPROVE_KEYWORDS.get(req.action_type, ["yes"])
            if any(kw in text for kw in approve_words):
                req.status = ApprovalStatus.APPROVED
                req.resolved_at = datetime.now(timezone.utc).isoformat()
                print(f"✅ Approved: {request_id} ({req.target_name})")
                return ApprovalStatus.APPROVED

            # Check skip keywords
            if any(kw in text for kw in self.SKIP_KEYWORDS):
                req.status = ApprovalStatus.SKIPPED
                req.resolved_at = datetime.now(timezone.utc).isoformat()
                print(f"⏭️  Skipped: {request_id} ({req.target_name})")
                return ApprovalStatus.SKIPPED

        return ApprovalStatus.PENDING

    def wait_for_approval(
        self,
        request_id: str,
        timeout_seconds: int = 14400,  # 4 hours default
        poll_interval: int = 30,
    ) -> ApprovalStatus:
        """Block until approval is received, skipped, or timeout.

        For use in GitHub Actions where the agent runs synchronously.
        Default timeout: 4 hours (matching founder operating rules).

        NOTE: In GitHub Actions, max job time is 6 hours. Set timeout accordingly.
        For async flows, use check_approval() with external polling instead.
        """
        start = time.time()
        while time.time() - start < timeout_seconds:
            status = self.check_approval(request_id)
            if status != ApprovalStatus.PENDING:
                return status
            time.sleep(poll_interval)

        # Expired
        req = self.pending.get(request_id)
        if req:
            req.status = ApprovalStatus.EXPIRED
            req.resolved_at = datetime.now(timezone.utc).isoformat()
        print(f"⏰ Expired: {request_id} (no response in {timeout_seconds}s)")
        return ApprovalStatus.EXPIRED

    def get_pending_count(self) -> int:
        """Count of unresolved approval requests."""
        return sum(1 for r in self.pending.values() if r.status == ApprovalStatus.PENDING)

    def get_all_pending(self) -> list[ApprovalRequest]:
        """List all pending approval requests."""
        return [r for r in self.pending.values() if r.status == ApprovalStatus.PENDING]

    def resolve_by_name(self, target_name: str, approve: bool) -> Optional[ApprovalRequest]:
        """Resolve a pending request by target name (for Telegram command handler).

        Used by /queue [name] and /skip [name] commands.
        """
        target_lower = target_name.lower()
        for req in self.pending.values():
            if req.status == ApprovalStatus.PENDING and target_lower in req.target_name.lower():
                req.status = ApprovalStatus.APPROVED if approve else ApprovalStatus.SKIPPED
                req.resolved_at = datetime.now(timezone.utc).isoformat()
                return req
        return None

    def to_json(self) -> str:
        """Serialize all requests for logging."""
        return json.dumps(
            {k: asdict(v) for k, v in self.pending.items()},
            indent=2,
            default=str,
        )


# --- Module-level convenience functions ---

_default_flow: Optional[ApprovalFlow] = None


def get_flow() -> ApprovalFlow:
    """Get or create the singleton ApprovalFlow instance."""
    global _default_flow
    if _default_flow is None:
        _default_flow = ApprovalFlow()
    return _default_flow


def request_outreach_approval(name: str, email: str, draft: str) -> ApprovalRequest:
    """Request founder approval before queuing outreach review for a lead."""
    return get_flow().request_approval(
        action_type=ActionType.OUTREACH,
        target_name=name,
        target_email=email,
        preview=draft,
    )


def request_deploy_approval(client_name: str) -> ApprovalRequest:
    """Request founder approval before starting client deployment."""
    return get_flow().request_approval(
        action_type=ActionType.DEPLOY,
        target_name=client_name,
    )
