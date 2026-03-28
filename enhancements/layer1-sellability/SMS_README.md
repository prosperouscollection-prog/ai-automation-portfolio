# SMS Alerts Setup

## Overview

`sms_alerts.py` sends an immediate text message to the business owner when a lead is scored `HIGH`. This is one of the easiest upsells because the client understands the value instantly.

Commercial positioning:

- Setup fee: `+$200`
- Monthly retainer: `+$50/month`
- Twilio usage: billed through to the client

## Environment Variables

Use the shared [`.env.example`](/Users/genesisai/portfolio/enhancements/layer1-sellability/.env.example) and fill in:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`
- `TWILIO_TO_NUMBER`
- `SMS_LOG_PATH`
- `SMS_OPTOUT_PATH`

## How the Module Works

1. Your lead workflow scores a lead as `HIGH`.
2. It calls `SMSAlertService.send_high_lead_alert(...)`.
3. The service checks whether the destination number has opted out.
4. If the number is eligible, Twilio sends the alert and the action is written to the audit log.

## TCPA / Opt-Out Handling

The module respects opt-outs by:

- including `Reply STOP to unsubscribe` in every alert
- storing opted-out numbers in `SMS_OPTOUT_PATH`
- blocking new sends to opted-out recipients

If you receive inbound SMS replies through Twilio webhooks, wire those replies into `OptOutRegistry.process_inbound_reply(...)`.

## n8n Option

Use `sms_alerts_n8n_node.json` when you want a no-code alert path directly inside an existing n8n workflow.

Recommended trigger condition:

- only continue to the Twilio node if `score === "HIGH"`

## Example Python Usage

```python
from datetime import datetime, timezone
from sms_alerts import LeadData, build_sms_service

service = build_sms_service()
service.send_high_lead_alert(
    LeadData(
        message="I need to book an emergency cleaning today.",
        score="HIGH",
        timestamp=datetime.now(timezone.utc),
    )
)
```

## Pricing Guidance

- bundle this aggressively with lead capture systems
- sell it as a speed-to-lead enhancement, not as "just texting"
- pass Twilio costs straight through so margins stay predictable
