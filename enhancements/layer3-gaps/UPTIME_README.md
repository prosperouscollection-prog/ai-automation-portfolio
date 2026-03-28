# Uptime Monitoring

## Overview

`uptime_monitoring.py` is the operational safety layer for Genesis AI Systems. It actively checks client webhooks, Google Sheets connectivity, OpenAI status, and Vapi status, then alerts on failure and recovery.

This is included in all retainers because it protects brand trust and supports your uptime promise.

## What It Monitors

- client webhook endpoints
- Google Sheets workbook access
- OpenAI status
- Vapi status

## What It Produces

- outage alerts
- recovery alerts
- uptime logs
- internal HTML dashboard
- monthly uptime percentage per client

## Setup

1. Fill in [`.env.example`](/Users/genesisai/portfolio/enhancements/layer3-gaps/.env.example).
2. Configure email and/or Twilio alerting.
3. Provide client webhook URLs and sheet keys to the service.
4. Run the monitor directly or schedule it:

```bash
cd /Users/genesisai/portfolio/enhancements/layer3-gaps
python uptime_monitoring.py
```

## Scheduling

- run every `5 minutes`
- import `uptime_n8n.json` for a no-code scheduler

## Target

Genesis AI Systems internal target: `99.9%` observed uptime
