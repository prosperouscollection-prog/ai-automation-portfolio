# Weekly AI Report Setup

## Overview

`weekly_report_generator.py` turns lead logs into a polished PDF report that lands in the client inbox every Monday morning. It is a strong retention add-on because it continuously reminds the client that the system is generating business value.

Commercial positioning:

- Monthly retainer add-on: `+$200/month`

## Report Contents

- executive summary
- lead volume chart
- lead score distribution
- top lead messages
- AI performance metrics
- recommended actions
- next week forecast

## Setup

1. Fill in the Google Sheets, SMTP, and Anthropic variables in [`.env.example`](/Users/genesisai/portfolio/enhancements/layer1-sellability/.env.example).
2. Make sure the target worksheet contains `Timestamp`, `Message`, `Response`, and `Score` columns.
3. Run the generator directly:

```bash
cd /Users/genesisai/portfolio/enhancements/layer1-sellability
python weekly_report_generator.py
```

4. Import `weekly_report_n8n.json` into n8n if you want a no-code weekly schedule.

## Cron Option

For a server-based schedule, use:

```cron
0 8 * * 1 cd /Users/genesisai/portfolio/enhancements/layer1-sellability && /usr/bin/python3 weekly_report_generator.py
```

## Sales Positioning

Pitch this as:

- automated account management
- proactive insight delivery
- a weekly proof-of-value document

It is especially strong when paired with the ROI report in Layer 3.
