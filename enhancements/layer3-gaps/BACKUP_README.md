# Backup System

## Overview

`backup_system.py` protects Genesis AI Systems and the client by exporting Google Sheets data to CSV every day, storing rolling local backups, and optionally mirroring the backup to S3.

This enhancement is included in all retainers because it protects your reputation as much as the client’s data.

## What It Does

- exports configured worksheet tabs to CSV
- stores timestamped local backups
- keeps `30` days of backups by default
- optionally uploads backups to AWS S3
- emails success or failure notifications

## Setup

1. Fill in [`.env.example`](/Users/genesisai/portfolio/enhancements/layer3-gaps/.env.example).
2. Set `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SHEETS_WORKSHEET_NAMES`, and `GOOGLE_SERVICE_ACCOUNT_JSON`.
3. Set `BACKUP_LOCAL_DIR`.
4. Add S3 variables if you want off-site storage.
5. Run:

```bash
cd /Users/genesisai/portfolio/enhancements/layer3-gaps
python backup_system.py
```

## Scheduling

- Python / cron: daily at `2:00 AM`
- n8n: import `backup_n8n.json`

## Recommended Policy

- always keep local backups
- use S3 for off-site redundancy
- email yourself on every failure
