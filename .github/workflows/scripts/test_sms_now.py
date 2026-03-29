#!/usr/bin/env python3
"""Send a one-time text so Trendell can confirm alerts are working."""

import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()


def test_sms() -> bool:
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_FROM_NUMBER")
    to_num = os.getenv("ALERT_PHONE_NUMBER")

    print(f"SID: {sid[:10] if sid else 'MISSING'}...")
    print(f"From: {from_num or 'MISSING'}")
    print(f"To: {to_num or 'MISSING'}")

    if not all([sid, token, from_num, to_num]):
      print("❌ Missing env vars — check .env file")
      return False

    try:
      client = Client(sid, token)
      msg = client.messages.create(
          body=(
              "✅ Genesis AI Systems\n"
              "SMS test successful!\n"
              "Your agents can now reach you.\n"
              "Trendell — genesisai.systems"
          ),
          from_=from_num,
          to=to_num
      )
      print(f"✅ SMS sent: {msg.sid}")
      print(f"Status: {msg.status}")
      return True
    except Exception as error:
      print(f"❌ SMS failed: {error}")
      print("\nCommon fixes:")
      print("1. Verify +13134002575 at twilio.com/console")
      print("2. Check TWILIO_FROM_NUMBER: +1XXXXXXXXXX")
      print("3. Check ALERT_PHONE_NUMBER: +13134002575")
      return False


if __name__ == "__main__":
    raise SystemExit(0 if test_sms() else 1)
