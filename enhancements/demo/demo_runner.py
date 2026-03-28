"""Credential-free demo harness for the Genesis AI Systems enhancement stack.

The runner generates presentation-ready outputs for the most visual retention
and operations layers without requiring Google Sheets, Twilio, Anthropic, or
SMTP credentials. It reuses the real uptime and PDF builders where practical
and falls back to HTML previews when optional PDF dependencies are missing.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import types
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from demo_data import DEMO_NOW, build_monthly_rollup, build_sample_leads, build_sample_uptime_snapshots


ROOT = Path("/Users/genesisai/portfolio/enhancements")
OUTPUT_DIR = ROOT / "demo" / "demo-output"


def ensure_import_stubs() -> None:
    """Install lightweight stubs for optional packages used only by live integrations."""
    if importlib.util.find_spec("dotenv") is None and "dotenv" not in sys.modules:
        dotenv_stub = types.ModuleType("dotenv")
        dotenv_stub.load_dotenv = lambda *args, **kwargs: False
        sys.modules["dotenv"] = dotenv_stub

    if importlib.util.find_spec("requests") is None and "requests" not in sys.modules:
        requests_stub = types.ModuleType("requests")

        class RequestException(Exception):
            """Fallback request exception used in the demo harness."""

        def _unsupported_get(*args, **kwargs):
            raise RequestException("requests is not installed in this environment")

        requests_stub.RequestException = RequestException
        requests_stub.get = _unsupported_get
        sys.modules["requests"] = requests_stub


def load_module(name: str, path: Path):
    """Load a Python file from disk as a uniquely named module."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def parse_timestamp(value: str) -> datetime:
    """Parse ISO timestamps from the sample lead feed."""
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def summarize_window(leads: list[dict[str, str]], days: int | None = None) -> dict[str, int]:
    """Count total, HIGH, MEDIUM, and LOW leads inside a date window."""
    now = DEMO_NOW
    selected = []
    for lead in leads:
        timestamp = parse_timestamp(lead["timestamp"])
        if days is None:
            if timestamp.year == now.year and timestamp.month == now.month:
                selected.append(lead)
        else:
            start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
            if start <= timestamp <= now:
                selected.append(lead)
    counts = Counter(item["score"] for item in selected)
    return {
        "total": len(selected),
        "HIGH": counts.get("HIGH", 0),
        "MEDIUM": counts.get("MEDIUM", 0),
        "LOW": counts.get("LOW", 0),
    }


def build_dashboard_html(leads: list[dict[str, str]], output_path: Path) -> Path:
    """Render a static, browser-ready client dashboard preview."""
    counts = Counter(lead["score"] for lead in leads)
    total = len(leads)
    high = counts.get("HIGH", 0)
    medium = counts.get("MEDIUM", 0)
    low = counts.get("LOW", 0)

    today = summarize_window(leads, days=1)
    week = summarize_window(leads, days=7)
    month = summarize_window(leads, days=None)
    recent = sorted(leads, key=lambda item: item["timestamp"], reverse=True)[:10]

    high_pct = round((high / total) * 100, 1) if total else 0
    medium_pct = round((medium / total) * 100, 1) if total else 0
    low_pct = round((low / total) * 100, 1) if total else 0

    def render_summary_row(label: str, metrics: dict[str, int]) -> str:
        return (
            f"<tr><th scope='row'>{label}</th><td>{metrics['total']}</td><td>{metrics['HIGH']}</td>"
            f"<td>{metrics['MEDIUM']}</td><td>{metrics['LOW']}</td></tr>"
        )

    def render_log_row(lead: dict[str, str]) -> str:
        timestamp = parse_timestamp(lead["timestamp"]).strftime("%b %d, %Y %I:%M %p UTC")
        score = lead["score"].lower()
        return (
            f"<tr><td>{timestamp}</td><td class='log-message'>{lead['message']}</td>"
            f"<td class='log-response'>{lead['response']}</td>"
            f"<td><span class='score-pill {score}'>{lead['score']}</span></td></tr>"
        )

    pie_style = (
        f"--high:{high_pct};--medium:{medium_pct};--low:{low_pct};"
        f"--high-stop:{high_pct};--medium-stop:{high_pct + medium_pct};"
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Genesis AI Systems Dashboard Demo</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #16213b;
      --panel-border: #2f4774;
      --text: #f8fafc;
      --muted: #cbd5e1;
      --blue: #2563eb;
      --green: #16a34a;
      --amber: #f59e0b;
      --red: #ef4444;
      --shadow: 0 16px 32px rgba(2, 6, 23, 0.32);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background:
        radial-gradient(circle at top right, rgba(37, 99, 235, 0.18), transparent 28%),
        linear-gradient(180deg, #0b1222 0%, var(--bg) 100%);
      color: var(--text);
      line-height: 1.5;
    }}
    .page {{ width: min(1180px, calc(100% - 2rem)); margin: 0 auto; padding: 2rem 0 3rem; }}
    .hero, .panel-header {{ display: flex; justify-content: space-between; gap: 1rem; }}
    .hero {{ align-items: flex-end; margin-bottom: 1.5rem; }}
    h1 {{ margin: 0; font-size: clamp(2rem, 4vw, 3rem); line-height: 1.05; }}
    p {{ margin: 0.5rem 0 0; }}
    .muted {{ color: var(--muted); }}
    .status-chip {{
      display: inline-flex; align-items: center; padding: 0.65rem 0.9rem; border-radius: 999px;
      background: rgba(37, 99, 235, 0.16); border: 1px solid rgba(96, 165, 250, 0.42); color: #dbeafe;
    }}
    .grid {{ display: grid; gap: 1rem; }}
    .stats-grid {{ grid-template-columns: repeat(4, minmax(0, 1fr)); margin-bottom: 1rem; }}
    .secondary-grid {{ grid-template-columns: 1.2fr 0.8fr; margin-bottom: 1rem; }}
    .panel {{
      background: linear-gradient(180deg, rgba(22, 33, 59, 0.96), rgba(14, 24, 44, 0.96));
      border: 1px solid var(--panel-border); border-radius: 1.25rem; box-shadow: var(--shadow); padding: 1.2rem;
    }}
    .metric-card h2 {{ margin: 0 0 0.35rem; font-size: 0.95rem; color: var(--muted); }}
    .metric-value {{ margin: 0; font-size: 2rem; font-weight: 700; }}
    .score-high {{ color: #86efac; }}
    .score-medium {{ color: #fcd34d; }}
    .score-low {{ color: #fda4af; }}
    .metrics-table {{ width: 100%; border-collapse: collapse; }}
    .metrics-table th, .metrics-table td {{
      padding: 0.8rem 0.65rem; border-bottom: 1px solid rgba(203, 213, 225, 0.12); text-align: left; vertical-align: top;
    }}
    .table-scroll {{ overflow-x: auto; }}
    .score-pill {{
      display: inline-flex; align-items: center; justify-content: center; min-width: 5.5rem;
      border-radius: 999px; padding: 0.3rem 0.75rem; font-size: 0.84rem; font-weight: 700;
    }}
    .score-pill.high {{ background: rgba(22, 163, 74, 0.2); color: #bbf7d0; }}
    .score-pill.medium {{ background: rgba(245, 158, 11, 0.2); color: #fde68a; }}
    .score-pill.low {{ background: rgba(239, 68, 68, 0.2); color: #fecdd3; }}
    .pie-wrap {{ display: grid; place-items: center; gap: 1rem; padding-top: 0.6rem; }}
    .pie-chart {{
      width: min(260px, 70vw); aspect-ratio: 1 / 1; border-radius: 50%;
      background:
        conic-gradient(
          var(--green) 0 calc(var(--high-stop) * 1%),
          var(--amber) calc(var(--high-stop) * 1%) calc(var(--medium-stop) * 1%),
          var(--red) calc(var(--medium-stop) * 1%) 100%
        );
      border: 10px solid rgba(15, 23, 42, 0.8);
      box-shadow: inset 0 0 0 1px rgba(203, 213, 225, 0.12);
    }}
    .legend {{ display: grid; gap: 0.55rem; width: 100%; }}
    .legend-row {{ display: flex; justify-content: space-between; align-items: center; gap: 1rem; }}
    .legend-label {{ display: inline-flex; align-items: center; gap: 0.55rem; }}
    .dot {{ width: 0.85rem; height: 0.85rem; border-radius: 50%; }}
    .dot.high {{ background: var(--green); }}
    .dot.medium {{ background: var(--amber); }}
    .dot.low {{ background: var(--red); }}
    .log-message, .log-response {{ max-width: 28rem; }}
    @media (max-width: 920px) {{
      .stats-grid, .secondary-grid {{ grid-template-columns: 1fr; }}
      .hero {{ align-items: flex-start; flex-direction: column; }}
    }}
    @media (max-width: 640px) {{
      .page {{ width: min(100% - 1rem, 1180px); padding-top: 1rem; }}
      .panel {{ padding: 1rem; }}
      .metric-value {{ font-size: 1.6rem; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero" aria-labelledby="dashboard-title">
      <div>
        <h1 id="dashboard-title">Genesis AI Systems Lead Dashboard Demo</h1>
        <p class="muted">Static portfolio preview using Smile Dental demo data. The live client version refreshes from Google Sheets every 60 seconds and is typically sold for <strong>+$500-$1,000 setup</strong> and <strong>+$100/month</strong>.</p>
      </div>
      <div class="status-chip">Last updated: {DEMO_NOW.strftime("%B %d, %Y %I:%M %p UTC")}</div>
    </section>

    <section class="grid stats-grid" aria-label="Lead score summary">
      <article class="panel metric-card"><h2>Total Leads</h2><p class="metric-value">{total}</p><p class="muted">All captured leads in the demo month.</p></article>
      <article class="panel metric-card"><h2>High Priority</h2><p class="metric-value score-high">{high}</p><p class="muted">Best leads for immediate follow-up.</p></article>
      <article class="panel metric-card"><h2>Medium Priority</h2><p class="metric-value score-medium">{medium}</p><p class="muted">Qualified leads that still need same-day attention.</p></article>
      <article class="panel metric-card"><h2>Low Priority</h2><p class="metric-value score-low">{low}</p><p class="muted">Lower urgency leads for nurture sequences.</p></article>
    </section>

    <section class="grid secondary-grid" aria-label="Lead metrics and chart">
      <article class="panel">
        <div class="panel-header"><div><h2>Lead Volume Snapshot</h2><p class="muted">Today, this week, and this month using the demo lead feed.</p></div></div>
        <div class="table-scroll">
          <table class="metrics-table">
            <thead><tr><th scope="col">Window</th><th scope="col">Total</th><th scope="col">High</th><th scope="col">Medium</th><th scope="col">Low</th></tr></thead>
            <tbody>
              {render_summary_row("Today", today)}
              {render_summary_row("This Week", week)}
              {render_summary_row("This Month", month)}
            </tbody>
          </table>
        </div>
      </article>
      <article class="panel">
        <div class="panel-header"><div><h2>Lead Score Distribution</h2><p class="muted">Generated from the same lead feed used in the ROI demo.</p></div></div>
        <div class="pie-wrap">
          <div class="pie-chart" style="{pie_style}" aria-label="Lead score distribution chart"></div>
          <div class="legend">
            <div class="legend-row"><span class="legend-label"><span class="dot high"></span>High</span><strong>{high_pct}%</strong></div>
            <div class="legend-row"><span class="legend-label"><span class="dot medium"></span>Medium</span><strong>{medium_pct}%</strong></div>
            <div class="legend-row"><span class="legend-label"><span class="dot low"></span>Low</span><strong>{low_pct}%</strong></div>
          </div>
        </div>
      </article>
    </section>

    <section class="panel" aria-labelledby="response-log-title">
      <div class="panel-header">
        <div>
          <h2 id="response-log-title">AI Response Log</h2>
          <p class="muted">Last 10 demo leads showing the exact client-facing narrative this enhancement makes visible.</p>
        </div>
      </div>
      <div class="table-scroll">
        <table class="metrics-table">
          <thead><tr><th scope="col">Timestamp</th><th scope="col">Lead Message</th><th scope="col">AI Response</th><th scope="col">Score</th></tr></thead>
          <tbody>{''.join(render_log_row(lead) for lead in recent)}</tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>"""
    output_path.write_text(html, encoding="utf-8")
    return output_path


def build_weekly_preview_html(metrics, recommendations: list[str], output_path: Path) -> Path:
    """Write a browser-friendly weekly report preview."""
    top_rows = "".join(
        "<tr>"
        f"<td>{lead.timestamp.strftime('%b %d %I:%M %p')}</td>"
        f"<td>{lead.score}</td>"
        f"<td>{lead.message}</td>"
        "</tr>"
        for lead in metrics.top_messages
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Weekly Report Demo</title>
  <style>
    body {{ font-family: "Segoe UI", Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
    .wrap {{ max-width: 960px; margin: 0 auto; }}
    .panel {{ background: #16213b; border: 1px solid #2f4774; border-radius: 20px; padding: 1.5rem; margin-bottom: 1rem; }}
    h1, h2 {{ margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 0.75rem; border-bottom: 1px solid rgba(203, 213, 225, 0.16); text-align: left; vertical-align: top; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 0.75rem; }}
    .chip {{ background: rgba(37, 99, 235, 0.15); border: 1px solid #2563eb; border-radius: 999px; padding: 0.55rem 0.8rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <h1>Smile Dental Weekly AI Report</h1>
      <p>Demo preview for the sellability layer. When ReportLab is installed, this same data can also be rendered as a PDF automatically every Monday at 8am.</p>
    </div>
    <div class="panel">
      <h2>Executive Summary</h2>
      <ul>
        <li>{metrics.total_leads} leads were handled this week, including {metrics.high_count} high-priority opportunities.</li>
        <li>The AI response rate was {metrics.response_rate:.0%}, with peak activity on {metrics.busiest_day} around {metrics.busiest_hour}.</li>
        <li>Top lead themes centered on {', '.join(metrics.top_keywords[:3]) or 'repeat service questions'}.</li>
      </ul>
    </div>
    <div class="panel">
      <h2>Weekly Metrics</h2>
      <div class="chips">
        <div class="chip">High: {metrics.high_count}</div>
        <div class="chip">Medium: {metrics.medium_count}</div>
        <div class="chip">Low: {metrics.low_count}</div>
        <div class="chip">Forecast Next Week: {metrics.next_week_forecast}</div>
      </div>
    </div>
    <div class="panel">
      <h2>Top Lead Messages</h2>
      <table>
        <thead><tr><th>Timestamp</th><th>Score</th><th>Message</th></tr></thead>
        <tbody>{top_rows}</tbody>
      </table>
    </div>
    <div class="panel">
      <h2>Recommended Actions</h2>
      <ul>{''.join(f'<li>{item}</li>' for item in recommendations)}</ul>
    </div>
  </div>
</body>
</html>"""
    output_path.write_text(html, encoding="utf-8")
    return output_path


def build_roi_preview_html(metrics, recommendations: list[str], output_path: Path) -> Path:
    """Write a browser-friendly monthly ROI report preview."""
    before_after_rows = [
        ("Lead handling", "Manual and inconsistent", f"{metrics.total_leads} leads tracked automatically"),
        ("Follow-up", "Delayed or forgotten", f"{metrics.ai_responses_sent} AI responses sent"),
        ("After-hours coverage", "Usually none", f"{metrics.voice_calls_handled} calls handled by AI"),
        ("Reporting", "Manual guesswork", "Monthly ROI report with hard numbers"),
    ]
    comparison_rows = "".join(
        f"<tr><td>{label}</td><td>{before}</td><td>{after}</td></tr>"
        for label, before, after in before_after_rows
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ROI Report Demo</title>
  <style>
    body {{ font-family: "Segoe UI", Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
    .wrap {{ max-width: 980px; margin: 0 auto; }}
    .panel {{ background: #16213b; border: 1px solid #2f4774; border-radius: 20px; padding: 1.5rem; margin-bottom: 1rem; }}
    .hero-number {{ font-size: 2rem; font-weight: 700; color: #93c5fd; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 0.75rem; border-bottom: 1px solid rgba(203, 213, 225, 0.16); text-align: left; vertical-align: top; }}
    .grid {{ display: grid; gap: 1rem; grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    @media (max-width: 800px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <h1>Your AI worked {metrics.estimated_time_saved_hours:.1f} hours this month so you didn't have to</h1>
      <p>Demo ROI preview. When ReportLab is available, this dataset also exports as a client-ready monthly PDF.</p>
    </div>
    <div class="grid">
      <div class="panel"><div class="hero-number">{metrics.total_leads}</div><div>Total leads captured</div></div>
      <div class="panel"><div class="hero-number">${metrics.estimated_revenue_generated:,.0f}</div><div>Estimated revenue influenced</div></div>
      <div class="panel"><div class="hero-number">{metrics.uptime_percentage:.2f}%</div><div>System uptime</div></div>
    </div>
    <div class="panel">
      <h2>Before Genesis AI Systems vs After Genesis AI Systems</h2>
      <table>
        <thead><tr><th>Metric</th><th>Before Genesis AI Systems</th><th>After Genesis AI Systems</th></tr></thead>
        <tbody>{comparison_rows}</tbody>
      </table>
    </div>
    <div class="panel">
      <h2>System Metrics</h2>
      <ul>
        <li>Lead score mix: {metrics.high_count} HIGH, {metrics.medium_count} MEDIUM, {metrics.low_count} LOW</li>
        <li>Voice calls handled: {metrics.voice_calls_handled}</li>
        <li>Automated emails sent: {metrics.emails_sent}</li>
        <li>Top themes: {', '.join(metrics.top_keywords) or 'No data'}</li>
      </ul>
    </div>
    <div class="panel">
      <h2>Next Month Recommendations</h2>
      <ul>{''.join(f'<li>{item}</li>' for item in recommendations)}</ul>
    </div>
  </div>
</body>
</html>"""
    output_path.write_text(html, encoding="utf-8")
    return output_path


def generate_weekly_assets(weekly_module, leads: list[dict[str, str]], output_dir: Path) -> dict[str, str]:
    """Generate weekly report demo assets from the real analytics module."""
    weekly_leads = []
    for lead in leads:
        timestamp = parse_timestamp(lead["timestamp"])
        if timestamp >= DEMO_NOW - timedelta(days=7):
            weekly_leads.append(
                weekly_module.LeadRecord(
                    timestamp=timestamp,
                    message=lead["message"],
                    response=lead["response"],
                    score=lead["score"],
                )
            )
    metrics = weekly_module.WeeklyMetricsCalculator.calculate(weekly_leads)
    recommendations = weekly_module.ClaudeRecommendationEngine(model="demo", api_key=None).generate(metrics)

    preview_path = build_weekly_preview_html(
        metrics,
        recommendations,
        output_dir / "weekly_report_demo.html",
    )
    results = {"weekly_preview": str(preview_path)}

    if importlib.util.find_spec("reportlab") is not None:
        pdf_path = weekly_module.WeeklyPDFBuilder("Smile Dental").build(
            metrics,
            recommendations,
            output_dir / "weekly_report_demo.pdf",
        )
        results["weekly_pdf"] = str(pdf_path)
    return results


def generate_roi_assets(roi_module, leads: list[dict[str, str]], output_dir: Path) -> dict[str, str]:
    """Generate monthly ROI demo assets from the real report builder."""
    rollup = build_monthly_rollup(leads)
    metrics = roi_module.MonthlyMetrics(
        total_leads=int(rollup["total_leads"]),
        high_count=int(rollup["high_count"]),
        medium_count=int(rollup["medium_count"]),
        low_count=int(rollup["low_count"]),
        ai_responses_sent=int(rollup["ai_responses_sent"]),
        voice_calls_handled=int(rollup["voice_calls_handled"]),
        emails_sent=int(rollup["emails_sent"]),
        estimated_time_saved_hours=float(rollup["estimated_time_saved_hours"]),
        estimated_revenue_generated=float(rollup["estimated_revenue_generated"]),
        uptime_percentage=float(rollup["uptime_percentage"]),
        top_keywords=list(rollup["top_keywords"]),
    )
    recommendations = roi_module.ClaudeROIRecommendationEngine(api_key=None, model="demo").generate(metrics)

    preview_path = build_roi_preview_html(
        metrics,
        recommendations,
        output_dir / "roi_report_demo.html",
    )
    results = {"roi_preview": str(preview_path)}

    if importlib.util.find_spec("reportlab") is not None:
        pdf_path = roi_module.PDFBuilder("Smile Dental").build(
            metrics,
            recommendations,
            output_dir / "roi_report_demo.pdf",
        )
        results["roi_pdf"] = str(pdf_path)
    return results


def generate_uptime_assets(uptime_module, output_dir: Path) -> dict[str, str]:
    """Generate an internal uptime dashboard from the real renderer."""
    snapshots = []
    for raw_snapshot in build_sample_uptime_snapshots():
        checks = [
            uptime_module.CheckResult(
                check_name=item["check_name"],
                healthy=bool(item["healthy"]),
                details=str(item["details"]),
            )
            for item in raw_snapshot["checks"]
        ]
        snapshots.append(
            uptime_module.ClientStatusSnapshot(
                client_id=str(raw_snapshot["client_id"]),
                client_name=str(raw_snapshot["client_name"]),
                checked_at=str(raw_snapshot["checked_at"]),
                checks=checks,
            )
        )
    dashboard_path = uptime_module.DashboardRenderer().render(
        snapshots,
        output_dir / "uptime_dashboard_demo.html",
    )
    return {"uptime_dashboard": str(dashboard_path)}


def write_summary(leads: list[dict[str, str]], generated_files: dict[str, str], output_dir: Path) -> Path:
    """Persist a machine-readable summary of the demo bundle."""
    score_counts = Counter(lead["score"] for lead in leads)
    summary = {
        "generated_at": DEMO_NOW.isoformat(),
        "business_name": "Smile Dental",
        "lead_count": len(leads),
        "high_count": score_counts.get("HIGH", 0),
        "medium_count": score_counts.get("MEDIUM", 0),
        "low_count": score_counts.get("LOW", 0),
        "files": generated_files,
    }
    summary_path = output_dir / "demo_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary_path


def main() -> int:
    """Generate the enhancement demo bundle and print the created files."""
    parser = argparse.ArgumentParser(description="Generate demo assets for the Genesis AI Systems enhancement stack.")
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory where the demo assets should be written.",
    )
    args = parser.parse_args()

    ensure_import_stubs()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    weekly_module = load_module(
        "genesis_weekly_report_demo",
        ROOT / "layer1-sellability" / "weekly_report_generator.py",
    )
    roi_module = load_module(
        "genesis_roi_report_demo",
        ROOT / "layer3-gaps" / "roi_report_generator.py",
    )
    uptime_module = load_module(
        "genesis_uptime_monitor_demo",
        ROOT / "layer3-gaps" / "uptime_monitoring.py",
    )

    leads = build_sample_leads()
    generated_files: dict[str, str] = {}
    generated_files["client_dashboard"] = str(
        build_dashboard_html(leads, output_dir / "client_dashboard_demo.html")
    )
    generated_files.update(generate_weekly_assets(weekly_module, leads, output_dir))
    generated_files.update(generate_roi_assets(roi_module, leads, output_dir))
    generated_files.update(generate_uptime_assets(uptime_module, output_dir))
    generated_files["summary"] = str(write_summary(leads, generated_files, output_dir))

    print("Genesis AI Systems enhancement demo bundle created:")
    for label, file_path in generated_files.items():
        print(f"- {label}: {file_path}")
    if "weekly_pdf" not in generated_files or "roi_pdf" not in generated_files:
        print("- note: PDF files were skipped because reportlab is not installed in the active Python environment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
