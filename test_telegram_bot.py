#!/usr/bin/env python3
"""Test Telegram bot configuration."""

import os
import sys
import requests

def check(name, condition, error_msg=""):
    """Print a check result."""
    if condition:
        print(f"✓ {name}")
        return True
    else:
        print(f"✗ {name}")
        if error_msg:
            print(f"  → {error_msg}")
        return False

def test_telegram():
    """Test Telegram bot setup."""
    print("\n" + "="*50)
    print("Telegram Bot Diagnostic")
    print("="*50 + "\n")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    
    # Check environment variables
    token_ok = check("TELEGRAM_BOT_TOKEN set", bool(token), 
                    "Set: export TELEGRAM_BOT_TOKEN=your_token")
    chat_ok = check("TELEGRAM_CHAT_ID set", bool(chat_id),
                   "Set: export TELEGRAM_CHAT_ID=your_id")
    
    if not token_ok or not chat_ok:
        print(f"\nCannot proceed without credentials")
        return False
    
    print()
    
    # Test token validity
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=5
        )
        bot_ok = check("Bot token valid", response.ok)
        if response.ok:
            data = response.json()
            bot_name = data.get("result", {}).get("username", "Unknown")
            print(f"  → Bot: @{bot_name}")
    except Exception as e:
        check("Bot token valid", False, str(e))
        return False
    
    print()
    
    # Test webhook
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            data={"url": "https://genesis-ai-systems-demo.onrender.com/telegram/webhook"}
        )
        webhook_ok = check("Webhook set", response.ok)
        if response.ok:
            data = response.json()
            status = "already set" if data.get("description") else "updated"
            print(f"  → Webhook {status}")
    except Exception as e:
        check("Webhook set", False, str(e))
        return False
    
    print()
    
    # Test demo server reachability
    try:
        response = requests.get(
            "https://genesis-ai-systems-demo.onrender.com/",
            timeout=5
        )
        server_ok = check("Demo server reachable", response.ok)
    except Exception as e:
        check("Demo server reachable", False, 
             "Render app may be asleep or down")
        server_ok = False
    
    print()
    
    # Test message sending (won't actually send to wrong ID)
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": "Test"}
        )
        can_send = response.ok or response.status_code == 400
        if response.status_code == 400:
            check("Chat ID valid", False, 
                 f"Invalid chat ID: {response.json().get('description')}")
        else:
            check("Can send messages", response.ok)
    except Exception as e:
        check("Can send messages", False, str(e))
    
    print("\n" + "="*50)
    print("✓ All checks passed!" if all([token_ok, chat_ok, bot_ok, webhook_ok, server_ok]) 
          else "⚠ Some checks failed - see above")
    print("="*50 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        test_telegram()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Cancelled")
        sys.exit(1)
