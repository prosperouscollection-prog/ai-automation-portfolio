# Enhancement Demo Harness

This folder generates presentation-ready sample outputs for the most visual and retention-focused Genesis AI Systems enhancements without requiring live credentials.

## What It Creates

- `client_dashboard_demo.html`: static preview of the client dashboard using Smile Dental demo leads
- `weekly_report_demo.html`: browser-friendly weekly report preview
- `weekly_report_demo.pdf`: optional PDF generated from the real weekly report builder when `reportlab` is installed
- `roi_report_demo.html`: browser-friendly monthly ROI preview
- `roi_report_demo.pdf`: optional PDF generated from the real ROI report builder when `reportlab` is installed
- `uptime_dashboard_demo.html`: uptime dashboard rendered with the real monitoring dashboard renderer
- `demo_summary.json`: machine-readable index of generated files and headline metrics

## How To Run

1. Install the enhancement dependencies if you want PDF generation:

```bash
cd /Users/genesisai/portfolio/enhancements
pip install -r requirements.txt
```

2. Generate the demo bundle:

```bash
cd /Users/genesisai/portfolio/enhancements/demo
python3 demo_runner.py
```

3. Open the generated assets from:

`/Users/genesisai/portfolio/enhancements/demo/demo-output/`

## Why This Exists

- Lets you record Loom demos before wiring live APIs
- Gives prospects visual proof of the enhancement stack
- Reuses the real weekly, ROI, and uptime logic where possible
- Falls back gracefully when optional packages like `reportlab` are not installed

## Demo Data Notes

- Uses fixed Smile Dental sample data for repeatable outputs
- Never touches production Google Sheets, SMTP, Twilio, Anthropic, or Vapi accounts
- Produces stable metrics so screenshots and walkthroughs stay consistent over time

