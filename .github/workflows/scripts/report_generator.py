#!/usr/bin/env python3
"""
Genesis AI Systems Report Generator
Generates branded HTML email, SMS text, Slack blocks, and GitHub issue markdown for agent reporting.

- Author: Genesis AI Systems (Trendell Fordham, Founder)
- Website: https://genesisai.systems
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

# Brand constants
genesis_brand = {
    "brand_name": "Genesis AI Systems",
    "primary_color": "#0f172a",  # Navy
    "accent_color": "#2563eb",   # Electric Blue
    "founder_name": "Trendell Fordham",
    "founder_email": "info@genesisai.systems",
    "founder_phone": "(313) 400-2575",
    "alert_phone": "+13134002575",
    "website": "https://genesisai.systems",
    "calendly": "https://calendly.com/genesisai-info-ptmt/free-ai-demo-call",
    "footer": "genesisai.systems | info@genesisai.systems | (313) 400-2575",
    "tagline": "Done-for-you AI automation for local businesses"
}

def now_ts() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def email_header(subject_line: str) -> str:
    """Genesis AI Systems branded HTML header"""
    return f'''<table width="100%" cellpadding="0" cellspacing="0" style="background:{genesis_brand['primary_color']};border-radius:8px 8px 0 0;">
  <tr>
    <td align="center" style="padding:30px 0;">
        <span style="font-size:30px;font-family:sans-serif;color:#fff;font-weight:700">{genesis_brand['brand_name']}</span><br/>
        <span style="font-size:16px;letter-spacing:1px;color:{genesis_brand['accent_color']};font-weight:600;">{genesis_brand['tagline']}</span>
    </td>
  </tr>
</table>
'''

def email_footer() -> str:
    return f'''<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f6fa;border-radius:0 0 8px 8px;">
  <tr><td align="center" style="padding:20px 0 10px 0;color:#888;font-family:sans-serif;font-size:13px;">
    <span style="color:{genesis_brand['primary_color']};font-weight:600;">{genesis_brand['footer']}</span><br/>
    <span style="color:#bbb;">&copy; {datetime.now().year} Genesis AI Systems. All rights reserved.</span>
  </td></tr>
</table>'''

def html_report_email(subject: str, summary: str, details: Union[str, List[Dict[str, Any]]], agent: str, status: str,
                     priority: str, extra_lines: Optional[List[str]] = None,
                     timestamp: Optional[str] = None) -> str:
    """
    Generates a branded HTML email for Genesis AI Systems agent reports.
    Args:
        subject: Email subject (without branding part)
        summary: Summary/intro of the issue or report
        details: Table: [{ 'Check': str, 'Status': str, 'Details': str }], or string (if not table)
        agent: Agent name (Security, QA, Evolution, Deploy, etc)
        status: Status ('PASSED', 'FAILED', 'ERROR', etc)
        priority: CRITICAL, HIGH, MEDIUM, LOW, INFO
        extra_lines: Optional lines to display after table
        timestamp: Optional override timestamp
    Returns:
        HTML string (safe for SendGrid emails)
    """
    if not timestamp:
        timestamp = now_ts()
    # If details is list, render table; else, render paragraph
    if isinstance(details, list) and details:
        table_rows = ''.join([f'<tr><td style="padding:8px;border:1px solid #d1d5db;background:#fff;font-family:sans-serif;">{d.get("Check")}<br><span style="color:#2563eb;font-size:12px;">{d.get("Details","&nbsp;")}</span></td><td style="padding:8px;border:1px solid #d1d5db;text-align:center;background:#fafdff;color:{status_color(d.get("Status",""))};font-weight:600">{d.get("Status","?")}</td></tr>' for d in details])
        table_html = f'''
        <table width="98%" align="center" cellpadding="0" cellspacing="0" style="margin:15px auto 20px auto;border-collapse:collapse;border-radius:8px;overflow:hidden;box-shadow:0 2px 10px #e5e5e7;">
          <tr style="background:{genesis_brand['accent_color']};color:#fff;font-family:sans-serif;font-size:15px;"><th style="padding:10px 15px;text-align:left;">Check</th><th style="padding:10px 15px;text-align:center;">Status</th></tr>
          {table_rows}
        </table>
        '''
    else:
        table_html = f'<p style="font-family:sans-serif;font-size:15px;background:#f8fafc;padding:16px 24px;border-radius:6px;margin:24px 0;">{details if details else "-"}</p>'

    # Extra lines shown in main body
    extra_html = '\n'.join([f'<div style="color:#2563eb;font-family:sans-serif;font-size:14px;margin-top:6px;">{line}</div>' for line in (extra_lines or [])])

    return f'''<html>
  <body style="margin:0;padding:0;background:#f3f5fa;">
  <div style="max-width:600px;margin:40px auto;font-family:sans-serif;background:#fff;border-radius:8px;box-shadow:0 4px 24px #e7ebf6;overflow:hidden;">
  {email_header(subject)}
    <div style="padding:38px 36px 16px 36px;">
      <h2 style="font-size:22px;color:{genesis_brand['primary_color']};margin:0 0 18px 0;font-weight:700;letter-spacing:0.01em;">{subject}</h2>
      <div style="font-size:15px;color:#23262f;margin-bottom:6px;">{summary}</div>
      <div style="color:#6b7280;font-size:14px;margin-bottom:8px;">Status: <b style="color:{status_color(status)}">{status.upper()}</b> &nbsp;|&nbsp; Agent: <span style="color:#2563eb;font-weight:500">{agent}</span> &nbsp;|&nbsp; Priority: {badge_html(priority)}</div>
      <div style="color:#8996a6;margin-bottom:16px;font-size:13px;">Time: {timestamp}</div>
      {table_html}
      {extra_html if extra_html else ''}
      <div style="margin-top:22px;">
        <a href="{genesis_brand['website']}" style="background:{genesis_brand['accent_color']};color:#fff;text-decoration:none;padding:11px 32px;border-radius:5px;font-weight:600;">Visit Website</a>
        <a href="{genesis_brand['calendly']}" style="background:#fff;color:{genesis_brand['accent_color']};margin-left:16px;border:2px solid {genesis_brand['accent_color']};padding:10px 31px;border-radius:5px;font-weight:500;text-decoration:none;">Book AI Demo</a>
      </div>
    </div>
  {email_footer()}
  </div>
  </body>
</html>
'''

def status_color(status: str) -> str:
    s = status.strip().upper()
    if s in ["PASSED", "OK", "SUCCESS", "RECOVERED"]:
        return "#16a34a"  # green
    if s in ["FAILED", "CRITICAL", "ERROR", "BLOCKED"]:
        return "#dc2626"  # red
    if s in ["WARNING", "WARN", "HIGH"]:
        return "#f59e42"  # orange
    if s in ["LOW", "INFO"]:
        return "#2563eb"  # blue
    return "#64748b"  # gray

def badge_html(priority: str) -> str:
    pr = priority.strip().upper()
    color = {
        "CRITICAL": "#dc2626",
        "HIGH": "#f59e42",
        "MEDIUM": "#2563eb",
        "LOW": "#64748b",
        "INFO": "#1d4ed8"
    }.get(pr, "#64748b")
    return f'<span style="background:{color};color:#fff;font-size:12px;padding:2px 10px;border-radius:6px;margin-right:4px;font-weight:600;letter-spacing:0.5px;">{pr}</span>'

def sms_alert(agent: str, status: str, description: str, ts: Optional[str]=None, recovery: bool=False) -> str:
    """SMS alert (failure or recovery)"""
    ts = ts or now_ts()
    if recovery:
        return f"""✅ Genesis AI Systems\nAgent: {agent}\nStatus: RECOVERED\nAll systems operational\nTime: {ts}"""
    return f"""🚨 Genesis AI Systems Alert\nAgent: {agent}\nStatus: {status.upper()}\nIssue: {description}\nTime: {ts}\nFix: github.com/prosperouscollection-prog/ai-automation-portfolio/actions"""

def sms_digest(subject: str, summary: str, agents_status: Dict[str, str], ts: Optional[str]=None) -> str:
    ts = ts or now_ts()
    base = f"Genesis AI Systems Health Report\n{subject}\n{summary}\n"
    statuses = '\n'.join([f"{agent}: {status}" for agent, status in agents_status.items()])
    return f"{base}{statuses}\nTime: {ts}"

def slack_report_blocks(subject: str, summary: str, details: Union[str, List[Dict[str, Any]]], agent: str, status: str, priority: str, timestamp: Optional[str]=None) -> List[Dict[str, Any]]:
    """
    Slack message (blocks array).
    """
    ts = timestamp or now_ts()
    status_color_map = {
        "CRITICAL": "#dc2626",
        "HIGH": "#f59e42",
        "MEDIUM": "#2563eb",
        "LOW": "#64748b",
        "INFO": "#1d4ed8"
    }
    color = status_color_map.get(priority.upper(), "#2563eb")
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{genesis_brand['brand_name']} — {subject}", "emoji": True}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Agent:*
{agent}  "},
                {"type": "mrkdwn", "text": f"*Status:*
*{status.upper()}*"},
                {"type": "mrkdwn", "text": f"*Priority:*
{priority.title()}"},
                {"type": "mrkdwn", "text": f"*Time:*
{ts}"}
            ]
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{summary}"}
        }
    ]
    if isinstance(details, list) and details:
        limit = 10
        detail_lines = []
        for d in details[:limit]:
            line = f"• *{d.get('Check','')}:* `{d.get('Status','?')}` — _{d.get('Details','')}_"
            detail_lines.append(line)
        details_text = '\n'.join(detail_lines)
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Details:*\n{details_text}"}
        })
        if len(details) > limit:
            blocks.append({
                "type": "context",
                "elements": [{"type": "plain_text", "text": f" +{len(details)-limit} more checks ...", "emoji": True }]}
            )
    elif isinstance(details, str):
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": details[:4000]}
        })

    blocks.extend([
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "plain_text", "text": f"genesisai.systems | info@genesisai.systems | (313) 400-2575", "emoji": True},
                {"type": "plain_text", "text": f"{genesis_brand['website']}", "emoji": True}
            ]
        }
    ])
    return blocks

def github_issue_markdown(subject: str, summary: str, details: Union[str, List[Dict[str, Any]]], agent: str, status: str,
                         priority: str, author: Optional[str]=None, timestamp: Optional[str]=None) -> str:
    """
    Generate markdown for a GitHub issue.
    """
    author = author or f"{genesis_brand['founder_name']} (@prosperouscollection-prog)"
    ts = timestamp or now_ts()
    md = f"""<!-- Powered by Genesis AI Systems --><!-- DO NOT REMOVE THIS HEADER -->
# {subject}
**Agent:** {agent}
**Status:** `{status.upper()}` | **Priority:** `{priority.title()}`
**Opened by:** {author} 
**Time:** {ts}
---
{summary}
"""
    if isinstance(details, list) and details:
        md += "\n| Check | Status | Details |\n|---|---|---|\n"
        for d in details:
            md += f"| {d.get('Check','')} | `{d.get('Status','?')}` | {d.get('Details','')} |\n"
    elif details:
        md += f"\n**Details:**\n\n{details}\n"
    md += f"\n---\n**:robot: Report generated by [Genesis AI Systems](https://genesisai.systems)**\n"
    return md

def api_powered_by_block() -> Dict[str, Any]:
    """Power-by block for API responses (always include in json)"""
    return {
        "powered_by": "Genesis AI Systems",
        "website": genesis_brand["website"],
        "contact": genesis_brand["founder_email"]
    }

# Example usages (remove/comment out in prod)
if __name__ == "__main__":
    checks = [
        {"Check": "PORTFOLIO_WEBSITE.html for exposed keys", "Status": "PASSED", "Details": "No credentials found."},
        {"Check": "Hardcoded credentials", "Status": "FAILED", "Details": "Found AWS key on line 38."},
    ]
    html = html_report_email(
        subject="Security Agent Failure",
        summary="Critical security issue detected on portfolio website.",
        details=checks,
        agent="Security Agent",
        status="FAILED",
        priority="CRITICAL",
        extra_lines=["Immediate action required.", "See attached logs for details."],
        timestamp=now_ts()
    )
    sms = sms_alert(agent="Security Agent", status="FAILED", description="Hardcoded AWS key found.")
    blocks = slack_report_blocks(
        subject="Security Check Failed",
        summary="Found exposed secret in site.",
        details=checks,
        agent="Security Agent",
        status="FAILED",
        priority="CRITICAL"
    )
    issue = github_issue_markdown(
        subject="Security Breach: Exposed AWS Key",
        summary="Security Agent found hardcoded AWS credentials.",
        details=checks,
        agent="Security Agent",
        status="FAILED",
        priority="CRITICAL"
    )
    import json
    print("----- HTML Email Snippet -----\n", html[:400], '...')
    print("----- SMS Alert -----\n", sms)
    print("----- Slack Blocks -----\n", json.dumps(blocks, indent=2))
    print("----- GitHub Issue Markdown -----\n", issue)
    print("----- API Powered By Block -----\n", api_powered_by_block())
